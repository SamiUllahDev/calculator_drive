from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AnnuityCalculator(View):
    """
    Class-based view for Annuity Calculator.
    Calculates present value, future value, and payments for annuities.
    Uses NumPy for efficient financial calculations. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/annuity_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Annuity Calculator'),
            'page_title': _('Annuity Calculator - Present & Future Value'),
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

            calc_type = data.get('calc_type', 'pv')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'pv'
            annuity_type = data.get('annuity_type', 'ordinary')
            if isinstance(annuity_type, list):
                annuity_type = annuity_type[0] if annuity_type else 'ordinary'

            payment = self._get_float(data, 'payment', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            periods = int(self._get_float(data, 'periods', 0))
            present_value = self._get_float(data, 'present_value', 0)
            future_value = self._get_float(data, 'future_value', 0)

            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': str(_('Interest rate must be between 0%% and 50%%.'))}, status=400)
            if periods <= 0 or periods > 600:
                return JsonResponse({'success': False, 'error': str(_('Periods must be between 1 and 600.'))}, status=400)
            
            rate = interest_rate / 100
            
            # Using NumPy for financial calculations
            if calc_type == 'pv':
                # Calculate Present Value of Annuity
                if payment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Payment must be greater than 0.'))}, status=400)
                
                if rate > 0:
                    # PV = PMT * [(1 - (1 + r)^-n) / r]
                    pv_factor = (1 - np.power(1 + rate, -periods)) / rate
                    result = payment * pv_factor
                    
                    if annuity_type == 'due':
                        result = result * (1 + rate)
                else:
                    result = payment * periods
                
                result_label = 'Present Value'
                
            elif calc_type == 'fv':
                # Calculate Future Value of Annuity
                if payment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Payment must be greater than 0.'))}, status=400)
                
                if rate > 0:
                    # FV = PMT * [((1 + r)^n - 1) / r]
                    fv_factor = (np.power(1 + rate, periods) - 1) / rate
                    result = payment * fv_factor
                    
                    if annuity_type == 'due':
                        result = result * (1 + rate)
                else:
                    result = payment * periods
                
                result_label = 'Future Value'
                
            else:  # Calculate Payment
                if calc_type == 'pmt_pv':
                    # Payment from Present Value
                    if present_value <= 0:
                        return JsonResponse({'success': False, 'error': str(_('Present value must be greater than 0.'))}, status=400)
                    
                    if rate > 0:
                        pv_factor = (1 - np.power(1 + rate, -periods)) / rate
                        if annuity_type == 'due':
                            pv_factor = pv_factor * (1 + rate)
                        result = present_value / pv_factor
                    else:
                        result = present_value / periods
                else:
                    # Payment from Future Value
                    if future_value <= 0:
                        return JsonResponse({'success': False, 'error': str(_('Future value must be greater than 0.'))}, status=400)
                    
                    if rate > 0:
                        fv_factor = (np.power(1 + rate, periods) - 1) / rate
                        if annuity_type == 'due':
                            fv_factor = fv_factor * (1 + rate)
                        result = future_value / fv_factor
                    else:
                        result = future_value / periods
                
                result_label = 'Payment Required'
            
            # Calculate total payments and interest
            if calc_type in ['pv', 'pmt_pv']:
                total_payments = payment * periods if calc_type == 'pv' else result * periods
                total_interest = total_payments - (result if calc_type == 'pv' else present_value)
            else:
                total_payments = payment * periods if calc_type == 'fv' else result * periods
                total_interest = (result if calc_type == 'fv' else future_value) - total_payments
            
            # Generate payment schedule for first 24 periods
            schedule = []
            if calc_type in ['pv', 'pmt_pv']:
                pmt = payment if calc_type == 'pv' else result
                balance = result if calc_type == 'pv' else present_value
                
                for period in range(1, min(25, periods + 1)):
                    if annuity_type == 'due' and period == 1:
                        interest = 0
                    else:
                        interest = balance * rate
                    
                    principal = pmt - interest if rate > 0 else pmt
                    balance = max(0, balance - principal)
                    
                    schedule.append({
                        'period': period,
                        'payment': round(pmt, 2),
                        'principal': round(principal, 2),
                        'interest': round(interest, 2),
                        'balance': round(balance, 2)
                    })
            
            # Compare different periods
            comparison = []
            base_pmt = payment if calc_type in ['pv', 'fv'] else result
            for n in [12, 24, 36, 60, 120, 240]:
                if rate > 0:
                    pv_f = (1 - np.power(1 + rate, -n)) / rate
                    fv_f = (np.power(1 + rate, n) - 1) / rate
                else:
                    pv_f = n
                    fv_f = n
                
                comparison.append({
                    'periods': n,
                    'pv': round(base_pmt * pv_f, 2),
                    'fv': round(base_pmt * fv_f, 2)
                })
            
            principal_val = round(abs(total_payments - total_interest), 2)
            interest_val = round(abs(total_interest), 2)
            chart_data = self._prepare_chart_data(principal_val, interest_val)

            response_data = {
                'success': True,
                'result': round(result, 2),
                'result_label': result_label,
                'summary': {
                    'calc_type': calc_type,
                    'annuity_type': annuity_type,
                    'payment': round(payment if calc_type in ['pv', 'fv'] else result, 2),
                    'interest_rate': interest_rate,
                    'periods': periods,
                    'total_payments': round(abs(total_payments), 2),
                    'total_interest': round(abs(total_interest), 2)
                },
                'schedule': schedule,
                'comparison': comparison,
                'chart_data': chart_data,
            }
            return JsonResponse(response_data, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, principal_val, interest_val):
        """Build Chart.js-ready chart_data (breakdown doughnut)."""
        principal_label = str(_('Principal'))
        interest_label = str(_('Interest'))
        breakdown = {
            'type': 'doughnut',
            'data': {
                'labels': [principal_label, interest_label],
                'datasets': [{
                    'data': [principal_val, interest_val],
                    'backgroundColor': ['#3b82f6', '#10b981'],
                    'borderWidth': 0,
                }],
            },
            'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
        }
        return {'breakdown_chart': breakdown}
