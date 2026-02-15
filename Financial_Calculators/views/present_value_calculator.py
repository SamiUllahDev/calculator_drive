from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PresentValueCalculator(View):
    """
    Class-based view for Present Value Calculator.
    Calculates present value of future cash flows.
    """
    template_name = 'financial_calculators/present_value_calculator.html'

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
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float (handles list, strips % and commas)."""
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
        """Safely get int (handles list)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def _unwrap(self, value):
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Present Value Calculator'),
            'page_title': _('Present Value Calculator - Calculate PV of Future Cash'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            future_value = self._get_float(data, 'future_value', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            years = self._get_int(data, 'years', 0)
            compound_frequency = self._unwrap(data.get('compound_frequency')) or 'monthly'

            if future_value <= 0 or future_value > 1000000000:
                return JsonResponse({'success': False, 'error': _('Please enter a valid future value.')}, status=400)
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': _('Interest rate must be between 0%% and 50%%.')}, status=400)
            if years <= 0 or years > 100:
                return JsonResponse({'success': False, 'error': _('Years must be between 1 and 100.')}, status=400)

            freq_map = {'annually': 1, 'semi-annually': 2, 'quarterly': 4, 'monthly': 12, 'daily': 365}
            n = freq_map.get(compound_frequency, 12)
            rate = interest_rate / 100
            present_value = future_value / ((1 + rate/n) ** (n * years))
            discount = future_value - present_value
            effective_rate = ((1 + rate/n) ** n - 1) * 100

            yearly_data = []
            for year in range(1, years + 1):
                pv_at_year = future_value / ((1 + rate/n) ** (n * (years - year + 1)))
                yearly_data.append({
                    'year': year,
                    'years_from_now': years - year + 1,
                    'present_value': round(pv_at_year, 2),
                    'discount_factor': round(1 / ((1 + rate/n) ** (n * (years - year + 1))), 4)
                })

            comparison = []
            for r in [3, 5, 7, 10, 12, 15]:
                rate_dec = r / 100
                pv = future_value / ((1 + rate_dec/n) ** (n * years))
                comparison.append({
                    'rate': r,
                    'present_value': round(pv, 2),
                    'discount': round(future_value - pv, 2)
                })

            result = {
                'success': True,
                'summary': {
                    'future_value': round(future_value, 2),
                    'present_value': round(present_value, 2),
                    'discount': round(discount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'effective_rate': round(effective_rate, 3),
                    'years': years,
                    'discount_factor': round(present_value / future_value, 4)
                },
                'yearly_data': yearly_data,
                'comparison': comparison,
                'chart_data': {
                    'breakdown': {
                        'present_value': round(present_value, 2),
                        'discount': round(discount, 2)
                    }
                }
            }
            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('Invalid request data.')}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
