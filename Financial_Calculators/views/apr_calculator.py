from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AprCalculator(View):
    """
    Class-based view for APR Calculator.
    Calculates Annual Percentage Rate including fees; returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/apr_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('APR Calculator'))}
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

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            loan_amount = self._get_float(data, 'loan_amount', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            loan_term = self._get_int(data, 'loan_term', 30)
            origination_fee = self._get_float(data, 'origination_fee', 0)
            discount_points = self._get_float(data, 'discount_points', 0)
            other_fees = self._get_float(data, 'other_fees', 0)

            if loan_amount <= 0 or loan_amount > 100000000:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid loan amount (up to $100,000,000).'))}, status=400)
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': str(_('Interest rate must be between 0%% and 50%%.'))}, status=400)
            if loan_term <= 0 or loan_term > 50:
                return JsonResponse({'success': False, 'error': str(_('Loan term must be between 1 and 50 years.'))}, status=400)

            points_cost = loan_amount * (discount_points / 100)
            total_fees = origination_fee + points_cost + other_fees
            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term * 12

            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments

            net_loan = loan_amount - total_fees
            apr_monthly = monthly_rate if monthly_rate > 0 else 0.001

            for _ in range(100):
                if apr_monthly <= 0:
                    apr_monthly = 0.001
                pv = 0
                dpv = 0
                for i in range(1, num_payments + 1):
                    discount = (1 + apr_monthly) ** i
                    pv += monthly_payment / discount
                    dpv -= i * monthly_payment / ((1 + apr_monthly) ** (i + 1))
                f = pv - net_loan
                if abs(f) < 0.01:
                    break
                if dpv != 0:
                    apr_monthly = apr_monthly - f / dpv

            apr_annual = apr_monthly * 12 * 100
            apr_annual = max(interest_rate, min(apr_annual, 99.99))

            total_interest = (monthly_payment * num_payments) - loan_amount
            total_cost = total_interest + total_fees
            rate_difference = apr_annual - interest_rate

            result = {
                'success': True,
                'summary': {
                    'apr': round(apr_annual, 3),
                    'stated_rate': round(interest_rate, 3),
                    'rate_difference': round(rate_difference, 3),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'total_fees': round(total_fees, 2),
                    'total_cost': round(total_cost, 2),
                    'points_cost': round(points_cost, 2),
                    'net_loan': round(net_loan, 2)
                },
                'fee_breakdown': {
                    'origination': round(origination_fee, 2),
                    'points': round(points_cost, 2),
                    'other': round(other_fees, 2),
                    'total': round(total_fees, 2)
                },
            }
            result['chart_data'] = self._prepare_chart_data(
                round(loan_amount, 2),
                round(total_interest, 2),
                round(total_fees, 2)
            )
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, principal, total_interest, total_fees):
        if principal <= 0 and total_interest <= 0 and total_fees <= 0:
            return {}
        return {
            'cost_breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Principal')), str(_('Interest')), str(_('Fees'))],
                    'datasets': [{
                        'data': [principal, total_interest, total_fees],
                        'backgroundColor': ['#3b82f6', '#ef4444', '#f59e0b'],
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
