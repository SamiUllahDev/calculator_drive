from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AmortizationCalculator(View):
    """
    Class-based view for Amortization Calculator.
    Generates complete loan amortization schedules; returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/amortization_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Amortization Calculator'))}
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
            start_month = self._get_int(data, 'start_month', 1)
            start_year = self._get_int(data, 'start_year', 2025)
            extra_payment = self._get_float(data, 'extra_payment', 0)

            if loan_amount <= 0 or loan_amount > 100000000:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid loan amount (up to $100,000,000).'))}, status=400)
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': str(_('Interest rate must be between 0%% and 50%%.'))}, status=400)
            if loan_term <= 0 or loan_term > 50:
                return JsonResponse({'success': False, 'error': str(_('Loan term must be between 1 and 50 years.'))}, status=400)
            if extra_payment < 0:
                return JsonResponse({'success': False, 'error': str(_('Extra payment cannot be negative.'))}, status=400)

            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term * 12

            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments

            schedule = []
            balance = loan_amount
            total_interest = 0
            total_principal = 0
            month_count = 0
            current_year = start_year
            current_month = start_month
            year_summary = {}
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

            while balance > 0.01 and month_count < num_payments * 2:
                month_count += 1
                interest_payment = balance * monthly_rate
                principal_payment = min(monthly_payment - interest_payment + extra_payment, balance)
                actual_payment = principal_payment + interest_payment
                balance = max(0, balance - principal_payment)
                total_interest += interest_payment
                total_principal += principal_payment

                if current_year not in year_summary:
                    year_summary[current_year] = {
                        'year': current_year,
                        'principal': 0,
                        'interest': 0,
                        'total_payment': 0,
                        'ending_balance': 0
                    }
                year_summary[current_year]['principal'] += principal_payment
                year_summary[current_year]['interest'] += interest_payment
                year_summary[current_year]['total_payment'] += actual_payment
                year_summary[current_year]['ending_balance'] = balance

                schedule.append({
                    'payment_number': month_count,
                    'month': months[current_month - 1],
                    'year': current_year,
                    'date': f"{months[current_month - 1]} {current_year}",
                    'payment': round(actual_payment, 2),
                    'principal': round(principal_payment, 2),
                    'interest': round(interest_payment, 2),
                    'balance': round(balance, 2)
                })
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1

            original_total_interest = 0
            if extra_payment > 0 and monthly_rate > 0:
                original_balance = loan_amount
                for _ in range(num_payments):
                    int_pmt = original_balance * monthly_rate
                    prin_pmt = monthly_payment - int_pmt
                    original_total_interest += int_pmt
                    original_balance -= prin_pmt
            interest_savings = original_total_interest - total_interest if extra_payment > 0 else 0
            time_savings_months = num_payments - month_count if extra_payment > 0 else 0

            yearly_data = list(year_summary.values())
            for item in yearly_data:
                item['principal'] = round(item['principal'], 2)
                item['interest'] = round(item['interest'], 2)
                item['total_payment'] = round(item['total_payment'], 2)
                item['ending_balance'] = round(item['ending_balance'], 2)

            payoff_display = f"{months[current_month - 2 if current_month > 1 else 11]} {current_year if current_month > 1 else current_year - 1}" if schedule else "-"

            result = {
                'success': True,
                'summary': {
                    'loan_amount': round(loan_amount, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payment': round(total_principal + total_interest, 2),
                    'total_interest': round(total_interest, 2),
                    'total_payments': month_count,
                    'payoff_date': payoff_display,
                    'interest_savings': round(interest_savings, 2),
                    'time_savings_months': time_savings_months,
                    'extra_payment': round(extra_payment, 2)
                },
                'schedule': schedule[:120],
                'yearly_summary': yearly_data,
                'full_schedule_length': len(schedule),
            }
            result['chart_data'] = self._prepare_chart_data(
                round(total_principal, 2),
                round(total_interest, 2),
                yearly_data
            )
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, total_principal, total_interest, yearly_data):
        out = {}
        if total_principal > 0 or total_interest > 0:
            out['breakdown_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Principal')), str(_('Interest'))],
                    'datasets': [{
                        'data': [total_principal, total_interest],
                        'backgroundColor': ['#10b981', '#ef4444'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom'}}
                }
            }
        if yearly_data:
            labels = [str(_('Year')) + " " + str(y['year']) for y in yearly_data]
            balances = [y['ending_balance'] for y in yearly_data]
            out['balance_chart'] = {
                'type': 'line',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Balance')),
                        'data': balances,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'fill': True,
                        'tension': 0.1
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}},
                    'scales': {'y': {'beginAtZero': True}}
                }
            }
        return out
