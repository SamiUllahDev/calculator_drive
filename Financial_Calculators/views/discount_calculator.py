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
class DiscountCalculator(View):
    """
    Class-based view for Discount Calculator.
    Calculates discounts, sale prices, and savings. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/discount_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Discount Calculator'))}
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

    def _prepare_chart_data(self, result):
        """Backend-controlled: pay vs save doughnut + sale price at different discount % bar chart."""
        out = {}
        calc_type = result.get('calc_type', '')
        sale_price = result.get('sale_price') or result.get('final_price')
        discount_amount = result.get('discount_amount') or result.get('total_savings')
        if sale_price is not None and discount_amount is not None:
            pay = max(0, float(sale_price))
            save = max(0, float(discount_amount))
            if pay + save > 0:
                out['breakdown_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': [str(_('You pay')), str(_('You save'))],
                        'datasets': [{
                            'data': [pay, save],
                            'backgroundColor': ['#8b5cf6', '#10b981'],
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
                        'backgroundColor': '#a855f7',
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

            calc_type = data.get('calc_type', 'find_sale_price')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'find_sale_price'

            if calc_type == 'find_sale_price':
                original_price = self._get_float(data, 'original_price', 100)
                discount_percent = self._get_float(data, 'discount_percent', 20)
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Price cannot be negative.'))}, status=400)
                if discount_percent < 0 or discount_percent > 100:
                    return JsonResponse({'success': False, 'error': str(_('Discount must be between 0 and 100%%.'))}, status=400)
                discount_amount = original_price * (discount_percent / 100)
                sale_price = original_price - discount_amount
                result = {
                    'success': True,
                    'calc_type': 'find_sale_price',
                    'original_price': round(original_price, 2),
                    'discount_percent': discount_percent,
                    'discount_amount': round(discount_amount, 2),
                    'sale_price': round(sale_price, 2)
                }
            elif calc_type == 'find_discount':
                original_price = self._get_float(data, 'original_price', 100)
                sale_price = self._get_float(data, 'sale_price', 80)
                if original_price <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Original price must be greater than zero.'))}, status=400)
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Sale price cannot be negative.'))}, status=400)
                discount_amount = original_price - sale_price
                discount_percent = (discount_amount / original_price) * 100
                result = {
                    'success': True,
                    'calc_type': 'find_discount',
                    'original_price': round(original_price, 2),
                    'sale_price': round(sale_price, 2),
                    'discount_amount': round(discount_amount, 2),
                    'discount_percent': round(discount_percent, 2)
                }
            elif calc_type == 'find_original':
                sale_price = self._get_float(data, 'sale_price', 80)
                discount_percent = self._get_float(data, 'discount_percent', 20)
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Sale price cannot be negative.'))}, status=400)
                if discount_percent < 0 or discount_percent >= 100:
                    return JsonResponse({'success': False, 'error': str(_('Discount must be between 0 and 99%%.'))}, status=400)
                original_price = sale_price / (1 - discount_percent / 100)
                discount_amount = original_price - sale_price
                result = {
                    'success': True,
                    'calc_type': 'find_original',
                    'sale_price': round(sale_price, 2),
                    'discount_percent': discount_percent,
                    'original_price': round(original_price, 2),
                    'discount_amount': round(discount_amount, 2)
                }
            elif calc_type == 'double_discount':
                original_price = self._get_float(data, 'original_price', 100)
                discount1 = self._get_float(data, 'discount1', 20)
                discount2 = self._get_float(data, 'discount2', 10)
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': str(_('Price cannot be negative.'))}, status=400)
                price_after_first = original_price * (1 - discount1 / 100)
                final_price = price_after_first * (1 - discount2 / 100)
                total_savings = original_price - final_price
                effective_discount = (total_savings / original_price) * 100 if original_price > 0 else 0
                result = {
                    'success': True,
                    'calc_type': 'double_discount',
                    'original_price': round(original_price, 2),
                    'discount1': discount1,
                    'discount2': discount2,
                    'price_after_first': round(price_after_first, 2),
                    'final_price': round(final_price, 2),
                    'total_savings': round(total_savings, 2),
                    'effective_discount': round(effective_discount, 2)
                }
            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            result['chart_data'] = self._prepare_chart_data(result)
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Discount JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Discount calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
