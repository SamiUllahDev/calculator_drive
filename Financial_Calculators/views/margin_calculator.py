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
class MarginCalculator(View):
    """
    Class-based view for Margin Calculator.
    Calculates profit margin, markup, cost, and revenue. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/margin_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Margin Calculator'))}
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

    def _prepare_chart_data(self, result, comparison_table):
        """Backend-controlled: cost/profit doughnut (when applicable) + margin vs markup bar chart."""
        out = {}
        cost = result.get('cost')
        profit = result.get('profit')
        if cost is not None and profit is not None and (cost > 0 or profit > 0):
            cost_val = max(0, float(cost))
            profit_val = max(0, float(profit))
            if cost_val + profit_val > 0:
                out['breakdown_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': [str(_('Cost')), str(_('Profit'))],
                        'datasets': [{
                            'data': [cost_val, profit_val],
                            'backgroundColor': ['#6b7280', '#10b981'],
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
        if comparison_table:
            labels = [str(r['margin']) + '%' for r in comparison_table]
            markup_values = [float(r['markup']) for r in comparison_table]
            out['comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Equivalent markup (%)')),
                        'data': markup_values,
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

            calc_type = data.get('calc_type', 'margin_from_cost_price')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'margin_from_cost_price'

            if calc_type == 'margin_from_cost_price':
                cost = self._get_float(data, 'cost', 0)
                price = self._get_float(data, 'price', 0)
                if cost < 0 or price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Values cannot be negative.'))}, status=400)
                if price == 0:
                    return JsonResponse({'success': False, 'error': str(_('Selling price cannot be zero.'))}, status=400)
                profit = price - cost
                margin = (profit / price) * 100
                markup = (profit / cost) * 100 if cost > 0 else 0
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'cost': round(cost, 2),
                    'price': round(price, 2),
                    'profit': round(profit, 2),
                    'margin': round(margin, 2),
                    'markup': round(markup, 2),
                    'formulas': {
                        'profit': str(_('Profit = Price - Cost = %(price)s - %(cost)s = %(profit)s')) % {
                            'price': f'${price:,.2f}', 'cost': f'${cost:,.2f}', 'profit': f'${profit:,.2f}'
                        },
                        'margin': str(_('Margin = (Profit / Price) × 100 = (%(profit)s / %(price)s) × 100 = %(margin)s%%')) % {
                            'profit': f'{profit:,.2f}', 'price': f'{price:,.2f}', 'margin': f'{margin:.2f}'
                        },
                        'markup': str(_('Markup = (Profit / Cost) × 100 = (%(profit)s / %(cost)s) × 100 = %(markup)s%%')) % {
                            'profit': f'{profit:,.2f}', 'cost': f'{cost:,.2f}', 'markup': f'{markup:.2f}'
                        }
                    }
                }
            elif calc_type == 'price_from_cost_margin':
                cost = self._get_float(data, 'cost', 0)
                margin = self._get_float(data, 'margin', 0)
                if cost < 0:
                    return JsonResponse({'success': False, 'error': str(_('Cost cannot be negative.'))}, status=400)
                if margin >= 100:
                    return JsonResponse({'success': False, 'error': str(_('Margin must be less than 100%%.'))}, status=400)
                price = cost / (1 - margin / 100) if margin < 100 else 0
                profit = price - cost
                markup = (profit / cost) * 100 if cost > 0 else 0
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'cost': round(cost, 2),
                    'margin': round(margin, 2),
                    'price': round(price, 2),
                    'profit': round(profit, 2),
                    'markup': round(markup, 2),
                    'formulas': {
                        'price': str(_('Price = Cost / (1 - Margin%%) = %(cost)s / (1 - %(margin)s%%) = %(price)s')) % {
                            'cost': f'${cost:,.2f}', 'margin': margin, 'price': f'${price:,.2f}'
                        },
                        'profit': str(_('Profit = %(profit)s')) % {'profit': f'${profit:,.2f}'},
                        'markup': str(_('Markup = %(markup)s%%')) % {'markup': f'{markup:.2f}'}
                    }
                }
            elif calc_type == 'price_from_cost_markup':
                cost = self._get_float(data, 'cost', 0)
                markup = self._get_float(data, 'markup', 0)
                if cost < 0:
                    return JsonResponse({'success': False, 'error': str(_('Cost cannot be negative.'))}, status=400)
                price = cost * (1 + markup / 100)
                profit = price - cost
                margin = (profit / price) * 100 if price > 0 else 0
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'cost': round(cost, 2),
                    'markup': round(markup, 2),
                    'price': round(price, 2),
                    'profit': round(profit, 2),
                    'margin': round(margin, 2),
                    'formulas': {
                        'price': str(_('Price = Cost × (1 + Markup%%) = %(cost)s × (1 + %(markup)s%%) = %(price)s')) % {
                            'cost': f'${cost:,.2f}', 'markup': markup, 'price': f'${price:,.2f}'
                        },
                        'profit': str(_('Profit = %(profit)s')) % {'profit': f'${profit:,.2f}'},
                        'margin': str(_('Margin = %(margin)s%%')) % {'margin': f'{margin:.2f}'}
                    }
                }
            elif calc_type == 'cost_from_price_margin':
                price = self._get_float(data, 'price', 0)
                margin = self._get_float(data, 'margin', 0)
                if price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Price cannot be negative.'))}, status=400)
                if margin >= 100:
                    return JsonResponse({'success': False, 'error': str(_('Margin must be less than 100%%.'))}, status=400)
                cost = price * (1 - margin / 100)
                profit = price - cost
                markup = (profit / cost) * 100 if cost > 0 else 0
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'price': round(price, 2),
                    'margin': round(margin, 2),
                    'cost': round(cost, 2),
                    'profit': round(profit, 2),
                    'markup': round(markup, 2),
                    'formulas': {
                        'cost': str(_('Cost = Price × (1 - Margin%%) = %(price)s × (1 - %(margin)s%%) = %(cost)s')) % {
                            'price': f'${price:,.2f}', 'margin': margin, 'cost': f'${cost:,.2f}'
                        },
                        'profit': str(_('Profit = %(profit)s')) % {'profit': f'${profit:,.2f}'},
                        'markup': str(_('Markup = %(markup)s%%')) % {'markup': f'{markup:.2f}'}
                    }
                }
            elif calc_type == 'margin_markup_convert':
                value = self._get_float(data, 'value', 0)
                convert_from = data.get('convert_from', 'margin')
                if isinstance(convert_from, list):
                    convert_from = convert_from[0] if convert_from else 'margin'
                if value < 0:
                    return JsonResponse({'success': False, 'error': str(_('Value cannot be negative.'))}, status=400)
                if convert_from == 'margin':
                    if value >= 100:
                        return JsonResponse({'success': False, 'error': str(_('Margin must be less than 100%%.'))}, status=400)
                    markup = (value / (100 - value)) * 100 if value < 100 else 0
                    result = {
                        'success': True,
                        'calc_type': calc_type,
                        'margin': round(value, 2),
                        'markup': round(markup, 2),
                        'cost': None,
                        'price': None,
                        'profit': None,
                        'formula': str(_('Markup = Margin / (100 - Margin) × 100 = %(value)s / (100 - %(value)s) × 100 = %(markup)s%%')) % {
                            'value': value, 'markup': f'{markup:.2f}'
                        }
                    }
                else:
                    margin = (value / (100 + value)) * 100
                    result = {
                        'success': True,
                        'calc_type': calc_type,
                        'markup': round(value, 2),
                        'margin': round(margin, 2),
                        'cost': None,
                        'price': None,
                        'profit': None,
                        'formula': str(_('Margin = Markup / (100 + Markup) × 100 = %(value)s / (100 + %(value)s) × 100 = %(margin)s%%')) % {
                            'value': value, 'margin': f'{margin:.2f}'
                        }
                    }
            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            comparison_table = []
            for m in [10, 15, 20, 25, 30, 35, 40, 45, 50]:
                markup_equiv = (m / (100 - m)) * 100
                comparison_table.append({'margin': m, 'markup': round(markup_equiv, 1)})
            result['comparison_table'] = comparison_table
            result['chart_data'] = self._prepare_chart_data(result, comparison_table)

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Margin JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Margin calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
