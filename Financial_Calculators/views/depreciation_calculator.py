from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DepreciationCalculator(View):
    """
    Class-based view for Depreciation Calculator.
    Calculates asset depreciation using various methods. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/depreciation_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Depreciation Calculator'))}
        return render(request, self.template_name, context)

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0.0):
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def _get_int(self, data, key, default=0):
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def _prepare_chart_data(self, schedule, asset_cost, salvage_value, total_depreciation):
        """Backend-controlled: book value over time line chart + total dep vs salvage doughnut."""
        out = {}
        if schedule:
            years = [str(_('Year')) + ' ' + str(s['year']) for s in schedule]
            book_vals = [float(s.get('ending_book_value', 0)) for s in schedule]
            acc_vals = [float(s.get('accumulated_depreciation', 0)) for s in schedule]
            out['value_chart'] = {
                'type': 'line',
                'data': {
                    'labels': years,
                    'datasets': [
                        {
                            'label': str(_('Ending book value')),
                            'data': book_vals,
                            'borderColor': '#6366f1',
                            'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                            'fill': True,
                            'tension': 0.3
                        },
                        {
                            'label': str(_('Accumulated depreciation')),
                            'data': acc_vals,
                            'borderColor': '#ef4444',
                            'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                            'fill': True,
                            'tension': 0.3
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom'}},
                    'scales': {'x': {'grid': {'display': False}}, 'y': {'beginAtZero': True}}
                }
            }
        remaining = max(0, asset_cost - total_depreciation)
        if asset_cost > 0 and (total_depreciation > 0 or remaining > 0):
            out['breakdown_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Total depreciation')), str(_('Remaining value'))],
                    'datasets': [{
                        'data': [round(total_depreciation, 2), round(remaining, 2)],
                        'backgroundColor': ['#6366f1', '#10b981'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'cutout': '55%',
                    'plugins': {'legend': {'position': 'bottom'}}
                }
            }
        return out

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            asset_cost = self._get_float(data, 'asset_cost', 0)
            salvage_value = self._get_float(data, 'salvage_value', 0)
            useful_life = self._get_int(data, 'useful_life', 5)
            depreciation_method = data.get('method', 'straight_line')
            if isinstance(depreciation_method, list):
                depreciation_method = depreciation_method[0] if depreciation_method else 'straight_line'
            db_rate = self._get_float(data, 'db_rate', 200)
            total_units = self._get_int(data, 'total_units', 0)
            units_per_year = data.get('units_per_year', [])

            if asset_cost <= 0:
                return JsonResponse({'success': False, 'error': str(_('Asset cost must be greater than zero.'))}, status=400)
            if useful_life <= 0:
                return JsonResponse({'success': False, 'error': str(_('Useful life must be greater than zero.'))}, status=400)
            if salvage_value < 0:
                return JsonResponse({'success': False, 'error': str(_('Salvage value cannot be negative.'))}, status=400)
            if salvage_value >= asset_cost and depreciation_method != 'macrs':
                return JsonResponse({'success': False, 'error': str(_('Salvage value must be less than asset cost.'))}, status=400)

            depreciable_amount = asset_cost - salvage_value
            schedule = []

            if depreciation_method == 'straight_line':
                # Straight-Line Depreciation
                annual_depreciation = depreciable_amount / useful_life
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    depreciation = annual_depreciation
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })

                result = {
                    'success': True,
                    'method': 'Straight-Line',
                    'formula': 'Depreciation = (Cost - Salvage) / Useful Life',
                    'annual_depreciation': round(annual_depreciation, 2),
                    'monthly_depreciation': round(annual_depreciation / 12, 2)
                }

            elif depreciation_method == 'declining_balance':
                # Declining Balance Depreciation
                rate = db_rate / 100 / useful_life  # e.g., 200% / 5 years = 40%
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    # Cannot depreciate below salvage value
                    depreciation = book_value * rate
                    
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'depreciation_rate': round(rate * 100, 2),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })
                    
                    if book_value <= salvage_value:
                        break

                result = {
                    'success': True,
                    'method': str(_('%(pct)s%% Declining Balance')) % {'pct': int(db_rate)},
                    'formula': str(_('Depreciation = Book Value × Rate')),
                    'depreciation_rate': round(rate * 100, 2),
                    'first_year_depreciation': round(schedule[0]['depreciation'], 2) if schedule else 0
                }

            elif depreciation_method == 'double_declining':
                # Double Declining Balance (DDB)
                rate = 2 / useful_life
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    depreciation = book_value * rate
                    
                    # Cannot depreciate below salvage value
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'depreciation_rate': round(rate * 100, 2),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })
                    
                    if book_value <= salvage_value:
                        break

                result = {
                    'success': True,
                    'method': str(_('Double Declining Balance (DDB)')),
                    'formula': str(_('Depreciation = Book Value × (2 / Useful Life)')),
                    'depreciation_rate': round(rate * 100, 2),
                    'first_year_depreciation': round(schedule[0]['depreciation'], 2) if schedule else 0
                }

            elif depreciation_method == 'sum_of_years':
                # Sum of Years' Digits (SYD)
                sum_of_years = sum(range(1, useful_life + 1))
                
                book_value = asset_cost
                accumulated = 0
                
                for year in range(1, useful_life + 1):
                    remaining_life = useful_life - year + 1
                    fraction = remaining_life / sum_of_years
                    depreciation = depreciable_amount * fraction
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'remaining_life': remaining_life,
                        'fraction': f'{remaining_life}/{sum_of_years}',
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2)
                    })

                result = {
                    'success': True,
                    'method': str(_("Sum of Years' Digits (SYD)")),
                    'formula': str(_('Depreciation = (Remaining Life / Sum of Years) × Depreciable Amount')),
                    'sum_of_years': sum_of_years,
                    'first_year_depreciation': round(schedule[0]['depreciation'], 2) if schedule else 0
                }

            elif depreciation_method == 'units_of_production':
                # Units of Production
                if total_units <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Total units must be greater than zero for this method.'))}, status=400)
                
                depreciation_per_unit = depreciable_amount / total_units
                
                book_value = asset_cost
                accumulated = 0
                total_units_produced = 0
                
                # If units_per_year not provided, assume equal distribution
                if not units_per_year:
                    units_per_year = [total_units / useful_life] * useful_life
                
                try:
                    if isinstance(units_per_year, list):
                        units_list = [self._get_float({'x': u}, 'x', total_units / useful_life) for u in units_per_year[:useful_life]]
                    else:
                        units_list = [total_units / useful_life] * useful_life
                    if len(units_list) < useful_life:
                        units_list.extend([total_units / useful_life] * (useful_life - len(units_list)))
                except (ValueError, TypeError, ZeroDivisionError):
                    units_list = [total_units / useful_life] * useful_life if useful_life else []
                
                for year, units in enumerate(units_list, 1):
                    depreciation = units * depreciation_per_unit
                    
                    # Cannot depreciate below salvage value
                    if book_value - depreciation < salvage_value:
                        depreciation = book_value - salvage_value
                    
                    accumulated += depreciation
                    book_value -= depreciation
                    total_units_produced += units
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'units_produced': int(units),
                        'depreciation_per_unit': round(depreciation_per_unit, 4),
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(book_value, 2),
                        'total_units_to_date': int(total_units_produced)
                    })
                    
                    if book_value <= salvage_value:
                        break

                result = {
                    'success': True,
                    'method': str(_('Units of Production')),
                    'formula': str(_('Depreciation = Units Produced × Depreciation per Unit')),
                    'total_units': total_units,
                    'depreciation_per_unit': round(depreciation_per_unit, 4)
                }

            elif depreciation_method == 'macrs':
                # MACRS (Modified Accelerated Cost Recovery System)
                # Common MACRS rates for different property classes
                macrs_rates = {
                    3: [33.33, 44.45, 14.81, 7.41],
                    5: [20.00, 32.00, 19.20, 11.52, 11.52, 5.76],
                    7: [14.29, 24.49, 17.49, 12.49, 8.93, 8.92, 8.93, 4.46],
                    10: [10.00, 18.00, 14.40, 11.52, 9.22, 7.37, 6.55, 6.55, 6.56, 6.55, 3.28],
                    15: [5.00, 9.50, 8.55, 7.70, 6.93, 6.23, 5.90, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 5.90, 5.91, 2.95],
                }
                
                if useful_life not in macrs_rates:
                    return JsonResponse({'success': False, 'error': str(_('MACRS requires property class of 3, 5, 7, 10, or 15 years.'))}, status=400)
                
                rates = macrs_rates[useful_life]
                book_value = asset_cost
                accumulated = 0
                
                # MACRS doesn't use salvage value
                for year, rate in enumerate(rates, 1):
                    depreciation = asset_cost * (rate / 100)
                    accumulated += depreciation
                    book_value -= depreciation
                    
                    schedule.append({
                        'year': year,
                        'beginning_book_value': round(book_value + depreciation, 2),
                        'macrs_rate': rate,
                        'depreciation': round(depreciation, 2),
                        'accumulated_depreciation': round(accumulated, 2),
                        'ending_book_value': round(max(0, book_value), 2)
                    })

                result = {
                    'success': True,
                    'method': str(_('MACRS (%(years)s-Year Property)')) % {'years': useful_life},
                    'formula': str(_('Depreciation = Cost × MACRS Rate')),
                    'property_class': str(_('%(years)s-Year')) % {'years': useful_life},
                    'note': str(_('MACRS does not consider salvage value'))
                }

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid depreciation method.'))}, status=400)

            total_depreciation = round(sum([s['depreciation'] for s in schedule]), 2)
            result.update({
                'asset_cost': round(asset_cost, 2),
                'salvage_value': round(salvage_value, 2),
                'depreciable_amount': round(depreciable_amount, 2),
                'useful_life': useful_life,
                'total_depreciation': total_depreciation,
                'schedule': schedule
            })
            ending_book_value = schedule[-1]['ending_book_value'] if schedule else salvage_value
            result['summary'] = {
                'method': result.get('method', ''),
                'formula': result.get('formula', ''),
                'asset_cost': result['asset_cost'],
                'salvage_value': result['salvage_value'],
                'depreciable_amount': result['depreciable_amount'],
                'useful_life': useful_life,
                'total_depreciation': total_depreciation,
                'ending_book_value': ending_book_value,
                'first_year_depreciation': result.get('first_year_depreciation') or result.get('annual_depreciation') or (schedule[0]['depreciation'] if schedule else 0),
                'rate_percent': result.get('depreciation_rate')
            }
            result['chart_data'] = self._prepare_chart_data(schedule, asset_cost, salvage_value, total_depreciation)
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Depreciation JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Depreciation calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
