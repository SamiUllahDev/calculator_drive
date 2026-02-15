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
class PercentOffCalculator(View):
    """
    Class-based view for Percent Off Calculator.
    Calculates discounted prices, percent off, stacked discounts, and buy-X-get-Y deals. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/percent_off_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Percent Off Calculator'))}
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

    def _prepare_chart_data(self, result):
        """Backend-controlled: pay vs save doughnut + sale price at different % off bar chart when applicable."""
        out = {}
        calc_type = result.get('calc_type', '')
        # Pay vs save doughnut
        sale_price = result.get('sale_price') or result.get('final_price') or result.get('deal_price')
        savings = result.get('savings') or result.get('total_savings')
        if sale_price is not None and savings is not None:
            pay = max(0, float(sale_price))
            save = max(0, float(savings))
            if pay + save > 0:
                out['breakdown_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': [str(_('You pay')), str(_('You save'))],
                        'datasets': [{
                            'data': [pay, save],
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
        # Comparison bar: sale price at 10,15,20,25,30,40,50% off
        original = result.get('original_price')
        if original is not None and float(original) > 0:
            orig = float(original)
            percents = [10, 15, 20, 25, 30, 40, 50]
            labels = [str(p) + '% ' + str(_('off')) for p in percents]
            values = [round(orig * (1 - p / 100), 2) for p in percents]
            out['comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Sale price')),
                        'data': values,
                        'backgroundColor': '#6366f1',
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True}
                    },
                    'plugins': {'legend': {'display': False}}
                }
            }
        return out

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'calculate_sale_price')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'calculate_sale_price'

            if calc_type == 'calculate_sale_price':
                original_price = self._get_float(data, 'original_price', 0)
                percent_off = self._get_float(data, 'percent_off', 0)
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Original price cannot be negative.'))}, status=400)
                if percent_off < 0 or percent_off > 100:
                    return JsonResponse({'success': False, 'error': str(_('Percent off must be between 0 and 100.'))}, status=400)
                savings = original_price * (percent_off / 100)
                sale_price = original_price - savings
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'percent_off': percent_off,
                    'savings': round(savings, 2),
                    'sale_price': round(sale_price, 2),
                    'formula': str(_('Sale Price = %(orig)s - (%(pct)s%% of %(orig)s) = %(sale)s')) % {
                        'orig': f'${original_price:,.2f}', 'pct': percent_off, 'sale': f'${sale_price:,.2f}'
                    }
                }
                discounts = [10, 15, 20, 25, 30, 40, 50, 60, 70]
                result['comparison'] = [
                    {'percent': d, 'savings': round(original_price * (d / 100), 2), 'final_price': round(original_price * (1 - d / 100), 2)}
                    for d in discounts
                ]

            elif calc_type == 'calculate_percent_off':
                original_price = self._get_float(data, 'original_price', 0)
                sale_price = self._get_float(data, 'sale_price', 0)
                if original_price <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Original price must be greater than zero.'))}, status=400)
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Sale price cannot be negative.'))}, status=400)
                if sale_price > original_price:
                    return JsonResponse({'success': False, 'error': str(_('Sale price cannot be higher than original price.'))}, status=400)
                savings = original_price - sale_price
                percent_off = (savings / original_price) * 100
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'sale_price': round(sale_price, 2),
                    'savings': round(savings, 2),
                    'percent_off': round(percent_off, 2),
                    'formula': str(_('Percent Off = ((%(orig)s - %(sale)s) / %(orig)s) × 100 = %(pct)s%%')) % {
                        'orig': f'${original_price:,.2f}', 'sale': f'${sale_price:,.2f}', 'pct': f'{percent_off:.2f}'
                    }
                }

            elif calc_type == 'calculate_original':
                sale_price = self._get_float(data, 'sale_price', 0)
                percent_off = self._get_float(data, 'percent_off', 0)
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Sale price cannot be negative.'))}, status=400)
                if percent_off < 0 or percent_off >= 100:
                    return JsonResponse({'success': False, 'error': str(_('Percent off must be between 0 and 99.'))}, status=400)
                original_price = sale_price / (1 - percent_off / 100)
                savings = original_price - sale_price
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'sale_price': round(sale_price, 2),
                    'percent_off': percent_off,
                    'original_price': round(original_price, 2),
                    'savings': round(savings, 2),
                    'formula': str(_('Original = %(sale)s / (1 - %(pct)s%%) = %(orig)s')) % {
                        'sale': f'${sale_price:,.2f}', 'pct': percent_off, 'orig': f'${original_price:,.2f}'
                    }
                }

            elif calc_type == 'stacked_discounts':
                original_price = self._get_float(data, 'original_price', 0)
                discounts_raw = data.get('discounts', [])
                if isinstance(discounts_raw, str):
                    discounts_raw = [x.strip() for x in discounts_raw.replace(',', ' ').split() if x.strip()]
                if not isinstance(discounts_raw, list):
                    discounts_raw = [20, 10]
                discounts = []
                for d in discounts_raw[:10]:
                    try:
                        val = float(str(d).replace(',', '').replace('%', ''))
                        if 0 <= val <= 100:
                            discounts.append(val)
                    except (ValueError, TypeError):
                        pass
                if not discounts:
                    discounts = [20, 10]
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Original price cannot be negative.'))}, status=400)
                current_price = original_price
                breakdown = []
                for i, discount in enumerate(discounts):
                    savings = current_price * (discount / 100)
                    new_price = current_price - savings
                    breakdown.append({
                        'step': i + 1,
                        'discount': discount,
                        'price_before': round(current_price, 2),
                        'savings': round(savings, 2),
                        'price_after': round(new_price, 2)
                    })
                    current_price = new_price
                total_savings = original_price - current_price
                effective_discount = (total_savings / original_price) * 100 if original_price > 0 else 0
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'discounts': discounts,
                    'final_price': round(current_price, 2),
                    'total_savings': round(total_savings, 2),
                    'effective_discount': round(effective_discount, 2),
                    'breakdown': breakdown,
                    'note': str(_('Stacking %(n)s discounts equals a single %(pct)s%% discount')) % {'n': len(discounts), 'pct': f'{effective_discount:.2f}'}
                }

            elif calc_type == 'buy_x_get_y':
                original_price = self._get_float(data, 'original_price', 0)
                buy_quantity = max(1, self._get_int(data, 'buy_quantity', 2))
                get_quantity = max(1, self._get_int(data, 'get_quantity', 1))
                get_discount = self._get_float(data, 'get_discount', 100)
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Price cannot be negative.'))}, status=400)
                total_items = buy_quantity + get_quantity
                regular_total = original_price * total_items
                deal_price = (original_price * buy_quantity) + (original_price * get_quantity * (1 - get_discount / 100))
                savings = regular_total - deal_price
                effective_per_item = deal_price / total_items if total_items > 0 else 0
                effective_discount = (savings / regular_total) * 100 if regular_total > 0 else 0
                deal_label = str(_('Buy %(buy)s Get %(get)s Free')) % {'buy': buy_quantity, 'get': get_quantity} if get_discount == 100 else str(_('Buy %(buy)s Get %(get)s %(pct)s%% Off')) % {'buy': buy_quantity, 'get': get_quantity, 'pct': get_discount}
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'deal': deal_label,
                    'buy_quantity': buy_quantity,
                    'get_quantity': get_quantity,
                    'get_discount': get_discount,
                    'total_items': total_items,
                    'regular_total': round(regular_total, 2),
                    'deal_price': round(deal_price, 2),
                    'savings': round(savings, 2),
                    'effective_per_item': round(effective_per_item, 2),
                    'effective_discount': round(effective_discount, 2)
                }

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            result['chart_data'] = self._prepare_chart_data(result)
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Percent-off JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Percent-off calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
