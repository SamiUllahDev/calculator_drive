from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SalesTaxCalculator(View):
    """
    Class-based view for Sales Tax Calculator.
    Add tax to price, extract tax from total, or find tax rate.
    Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/sales_tax_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': str(_('Sales Tax Calculator')),
        }
        return render(request, self.template_name, context)

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        # Fallback: try body as JSON (e.g. if Content-Type was not set correctly)
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

    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'add_tax')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'add_tax'

            price = self._get_float(data, 'price', 0)
            tax_rate = self._get_float(data, 'tax_rate', 0)

            if price < 0:
                return JsonResponse({'success': False, 'error': str(_('Price cannot be negative.'))}, status=400)
            if tax_rate < 0 or tax_rate > 100:
                return JsonResponse({'success': False, 'error': str(_('Tax rate must be between 0 and 100.'))}, status=400)

            if calc_type == 'add_tax':
                tax_amount = round(price * (tax_rate / 100), 2)
                total = round(price + tax_amount, 2)
                result = {
                    'success': True,
                    'calc_type': 'add_tax',
                    'before_tax': round(price, 2),
                    'tax_rate': tax_rate,
                    'tax_amount': tax_amount,
                    'total': total
                }
            elif calc_type == 'extract_tax':
                divisor = 1 + (tax_rate / 100)
                before_tax = round(price / divisor, 2)
                tax_amount = round(price - before_tax, 2)
                result = {
                    'success': True,
                    'calc_type': 'extract_tax',
                    'total': round(price, 2),
                    'tax_rate': tax_rate,
                    'tax_amount': tax_amount,
                    'before_tax': before_tax
                }
            elif calc_type == 'find_rate':
                before_tax = self._get_float(data, 'before_tax', 100)
                total = self._get_float(data, 'total', 110)
                if before_tax <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Before-tax price must be greater than zero.'))}, status=400)
                tax_amount = round(total - before_tax, 2)
                calculated_rate = round((tax_amount / before_tax) * 100, 4)
                result = {
                    'success': True,
                    'calc_type': 'find_rate',
                    'before_tax': round(before_tax, 2),
                    'total': round(total, 2),
                    'tax_amount': tax_amount,
                    'tax_rate': calculated_rate
                }
            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            result['chart_data'] = self._prepare_chart_data(result)
            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, result):
        """Build Chart.js doughnut: Before tax + Sales tax."""
        calc_type = result.get('calc_type', 'add_tax')
        before = result.get('before_tax', 0)
        tax = result.get('tax_amount', 0)
        if before <= 0 and tax <= 0:
            return {}
        labels = [str(_('Before Tax')), str(_('Sales Tax'))]
        values = [round(before, 2), round(tax, 2)]
        return {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': ['#3b82f6', '#ef4444'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom'}}
                }
            }
        }
