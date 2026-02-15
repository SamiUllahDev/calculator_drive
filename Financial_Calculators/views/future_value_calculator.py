from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FutureValueCalculator(View):
    """
    Class-based view for Future Value Calculator.
    Calculates future value of investments with regular contributions.
    """
    template_name = 'financial_calculators/future_value_calculator.html'

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
            'calculator_name': _('Future Value Calculator'),
            'page_title': _('Future Value Calculator - Calculate Investment Growth'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            present_value = self._get_float(data, 'present_value', 0)
            periodic_payment = self._get_float(data, 'periodic_payment', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            years = self._get_int(data, 'years', 0)
            payment_frequency = self._unwrap(data.get('payment_frequency')) or 'monthly'
            compound_frequency = self._unwrap(data.get('compound_frequency')) or 'monthly'
            payment_timing = self._unwrap(data.get('payment_timing')) or 'end'

            if present_value < 0 or present_value > 1000000000:
                return JsonResponse({'success': False, 'error': _('Please enter a valid present value.')}, status=400)
            if periodic_payment < 0:
                return JsonResponse({'success': False, 'error': _('Periodic payment cannot be negative.')}, status=400)
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': _('Interest rate must be between 0%% and 50%%.')}, status=400)
            if years <= 0 or years > 100:
                return JsonResponse({'success': False, 'error': _('Years must be between 1 and 100.')}, status=400)

            freq_map = {'annually': 1, 'semi-annually': 2, 'quarterly': 4, 'monthly': 12, 'biweekly': 26, 'weekly': 52}
            payment_freq = freq_map.get(payment_frequency, 12)
            compound_freq = freq_map.get(compound_frequency, 12)

            rate = interest_rate / 100
            period_rate = rate / compound_freq
            total_periods = compound_freq * years

            fv_pv = present_value * ((1 + period_rate) ** total_periods)
            if rate > 0:
                pmt_per_compound = periodic_payment * (payment_freq / compound_freq)
                if payment_timing == 'beginning':
                    fv_annuity = pmt_per_compound * (((1 + period_rate) ** total_periods - 1) / period_rate) * (1 + period_rate)
                else:
                    fv_annuity = pmt_per_compound * (((1 + period_rate) ** total_periods - 1) / period_rate)
            else:
                fv_annuity = periodic_payment * payment_freq * years

            future_value = fv_pv + fv_annuity
            total_contributions = present_value + (periodic_payment * payment_freq * years)
            total_interest = future_value - total_contributions

            yearly_data = []
            running_balance = present_value
            running_contributions = present_value
            for year in range(1, years + 1):
                year_periods = compound_freq
                annual_contribution = periodic_payment * payment_freq
                if rate > 0:
                    year_end_balance = running_balance * ((1 + period_rate) ** year_periods)
                    if payment_timing == 'beginning':
                        year_end_balance += (annual_contribution / year_periods) * (((1 + period_rate) ** year_periods - 1) / period_rate) * (1 + period_rate)
                    else:
                        year_end_balance += (annual_contribution / year_periods) * (((1 + period_rate) ** year_periods - 1) / period_rate)
                else:
                    year_end_balance = running_balance + annual_contribution
                running_contributions += annual_contribution
                year_interest = year_end_balance - running_contributions
                yearly_data.append({
                    'year': year,
                    'contributions': round(running_contributions, 2),
                    'interest': round(year_interest, 2),
                    'balance': round(year_end_balance, 2)
                })
                running_balance = year_end_balance

            scenarios = []
            for pmt in [0, 100, 200, 500, 1000]:
                if rate > 0:
                    pmt_per_c = pmt * (12 / compound_freq)
                    fv_a = pmt_per_c * (((1 + period_rate) ** total_periods - 1) / period_rate)
                else:
                    fv_a = pmt * 12 * years
                total_fv = fv_pv + fv_a
                scenarios.append({
                    'payment': pmt,
                    'future_value': round(total_fv, 2),
                    'total_contributed': round(present_value + (pmt * 12 * years), 2)
                })

            result = {
                'success': True,
                'summary': {
                    'present_value': round(present_value, 2),
                    'periodic_payment': round(periodic_payment, 2),
                    'interest_rate': round(interest_rate, 3),
                    'years': years,
                    'future_value': round(future_value, 2),
                    'total_contributions': round(total_contributions, 2),
                    'total_interest': round(total_interest, 2),
                    'fv_from_pv': round(fv_pv, 2),
                    'fv_from_payments': round(fv_annuity, 2)
                },
                'yearly_data': yearly_data,
                'scenarios': scenarios,
                'chart_data': {
                    'breakdown': {
                        'contributions': round(total_contributions, 2),
                        'interest': round(total_interest, 2)
                    },
                    'growth': {
                        'labels': [f"Year {d['year']}" for d in yearly_data[:20]],
                        'contributions': [d['contributions'] for d in yearly_data[:20]],
                        'balances': [d['balance'] for d in yearly_data[:20]]
                    }
                }
            }
            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except json.JSONDecodeError as e:
            return JsonResponse({'success': False, 'error': _('Invalid request data.')}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
