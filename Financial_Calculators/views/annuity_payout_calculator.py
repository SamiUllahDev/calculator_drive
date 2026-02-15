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
class AnnuityPayoutCalculator(View):
    """
    Class-based view for Annuity Payout Calculator.
    Calculates annuity payouts, present value, and future value using NumPy.
    Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/annuity_payout_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Annuity Payout Calculator'),
            'page_title': _('Annuity Payout Calculator - Calculate Periodic Payments'),
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

            calc_type = data.get('calc_type', 'payout')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'payout'
            payment_frequency = data.get('payment_frequency', 'monthly')
            if isinstance(payment_frequency, list):
                payment_frequency = payment_frequency[0] if payment_frequency else 'monthly'
            annuity_type = data.get('annuity_type', 'ordinary')
            if isinstance(annuity_type, list):
                annuity_type = annuity_type[0] if annuity_type else 'ordinary'

            principal = self._get_float(data, 'principal', 100000)
            annual_rate = self._get_float(data, 'annual_rate', 5)
            years = int(self._get_float(data, 'years', 20))
            periodic_payment_input = self._get_float(data, 'periodic_payment', 1000)

            if principal <= 0 and calc_type == 'payout':
                return JsonResponse({'success': False, 'error': str(_('Principal must be greater than zero.'))}, status=400)
            if annual_rate < 0 or annual_rate > 50:
                return JsonResponse({'success': False, 'error': str(_('Interest rate must be between 0 and 50%%.'))}, status=400)
            if years < 1 or years > 100:
                return JsonResponse({'success': False, 'error': str(_('Years must be between 1 and 100.'))}, status=400)
            
            # Calculate periods and periodic rate
            periods_per_year = {'monthly': 12, 'quarterly': 4, 'annually': 1}
            n_per_year = periods_per_year.get(payment_frequency, 12)
            n_total = years * n_per_year
            periodic_rate = (annual_rate / 100) / n_per_year
            
            # Using NumPy for calculations
            if periodic_rate > 0:
                # Present Value of Ordinary Annuity factor
                pvifa = (1 - np.power(1 + periodic_rate, -n_total)) / periodic_rate
                
                # Future Value of Ordinary Annuity factor
                fvifa = (np.power(1 + periodic_rate, n_total) - 1) / periodic_rate
                
                # Adjustment for annuity due (payments at beginning)
                if annuity_type == 'due':
                    pvifa *= (1 + periodic_rate)
                    fvifa *= (1 + periodic_rate)
                
                # Calculate periodic payment (given present value)
                if calc_type == 'payout':
                    periodic_payment = principal / pvifa
                    total_received = periodic_payment * n_total
                    total_interest = total_received - principal
                    
                    result = {
                        'success': True,
                        'calc_type': 'payout',
                        'periodic_payment': round(periodic_payment, 2),
                        'total_received': round(total_received, 2),
                        'total_interest': round(total_interest, 2),
                        'principal': round(principal, 2)
                    }
                
                elif calc_type == 'present_value':
                    periodic_payment = periodic_payment_input
                    present_value = periodic_payment * pvifa
                    total_payments = periodic_payment * n_total
                    
                    result = {
                        'success': True,
                        'calc_type': 'present_value',
                        'present_value': round(present_value, 2),
                        'periodic_payment': round(periodic_payment, 2),
                        'total_payments': round(total_payments, 2)
                    }
                
                elif calc_type == 'future_value':
                    periodic_payment = periodic_payment_input
                    future_value = periodic_payment * fvifa
                    total_contributions = periodic_payment * n_total
                    total_interest = future_value - total_contributions
                    
                    result = {
                        'success': True,
                        'calc_type': 'future_value',
                        'future_value': round(future_value, 2),
                        'periodic_payment': round(periodic_payment, 2),
                        'total_contributions': round(total_contributions, 2),
                        'total_interest': round(total_interest, 2)
                    }
                else:
                    return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)
            else:
                # Zero interest rate case
                if calc_type == 'payout':
                    periodic_payment = principal / n_total
                    result = {
                        'success': True,
                        'calc_type': 'payout',
                        'periodic_payment': round(periodic_payment, 2),
                        'total_received': round(principal, 2),
                        'total_interest': 0,
                        'principal': round(principal, 2)
                    }
                else:
                    return JsonResponse({'success': False, 'error': str(_('Zero interest not supported for this calculation.'))}, status=400)
            
            # Add common fields
            result.update({
                'annual_rate': annual_rate,
                'years': years,
                'payment_frequency': payment_frequency,
                'annuity_type': annuity_type,
                'periods_per_year': n_per_year,
                'total_periods': n_total,
                'periodic_rate': round(periodic_rate * 100, 4)
            })
            
            # Generate payment schedule (first 12 periods or all if less)
            schedule = []
            remaining = principal
            for i in range(min(12, n_total)):
                if calc_type == 'payout':
                    interest = remaining * periodic_rate
                    principal_portion = periodic_payment - interest if periodic_payment > interest else remaining
                    remaining -= principal_portion
                    schedule.append({
                        'period': i + 1,
                        'payment': round(periodic_payment, 2),
                        'interest': round(interest, 2),
                        'principal': round(principal_portion, 2),
                        'remaining': round(max(0, remaining), 2)
                    })
            
            result['schedule'] = schedule
            result['chart_data'] = self._prepare_chart_data(result)
            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, result):
        """Build Chart.js-ready chart_data (breakdown doughnut) based on calc_type."""
        calc_type = result.get('calc_type', 'payout')
        principal_label = str(_('Principal'))
        interest_label = str(_('Interest'))
        contributions_label = str(_('Contributions'))
        present_value_label = str(_('Present Value'))

        if calc_type == 'payout':
            principal_val = round(float(result.get('principal', 0)), 2)
            interest_val = round(float(result.get('total_received', 0)) - principal_val, 2)
            interest_val = round(max(0, interest_val), 2)
            labels = [principal_label, interest_label]
            values = [principal_val, interest_val]
        elif calc_type == 'present_value':
            pv_val = round(float(result.get('present_value', 0)), 2)
            total_val = round(float(result.get('total_payments', 0)), 2)
            extra = round(max(0, total_val - pv_val), 2)
            labels = [present_value_label, interest_label]
            values = [pv_val, extra]
        else:
            # future_value
            contrib = round(float(result.get('total_contributions', 0)), 2)
            interest_val = round(float(result.get('total_interest', 0)), 2)
            labels = [contributions_label, interest_label]
            values = [contrib, interest_val]

        breakdown = {
            'type': 'doughnut',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': values,
                    'backgroundColor': ['#3b82f6', '#10b981'],
                    'borderWidth': 0,
                }],
            },
            'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
        }
        return {'breakdown_chart': breakdown}
