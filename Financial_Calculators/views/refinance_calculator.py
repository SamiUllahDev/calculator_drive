from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
import math

logger = logging.getLogger(__name__)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RefinanceCalculator(View):
    """
    Class-based view for Mortgage Refinance Calculator.
    Calculates refinance savings, break-even point, and compares current vs new loan.
    Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/refinance_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Refinance Calculator'))}
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

    def _get_bool(self, data, key, default=False):
        value = data.get(key, default)
        if isinstance(value, list):
            value = value[0] if value else default
        if value in (True, 'true', 'True', '1', 1):
            return True
        return bool(value) if value is not None else default

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            current_balance = self._get_float(data, 'current_balance', 0)
            current_rate = self._get_float(data, 'current_rate', 0)
            current_payment = self._get_float(data, 'current_payment', 0)
            months_remaining = self._get_int(data, 'months_remaining', 0)
            new_rate = self._get_float(data, 'new_rate', 0)
            new_term = self._get_int(data, 'new_term', 360)
            closing_costs = self._get_float(data, 'closing_costs', 0)
            points = self._get_float(data, 'points', 0)
            roll_costs_into_loan = self._get_bool(data, 'roll_costs_into_loan', False)
            cash_out = self._get_float(data, 'cash_out', 0)

            if current_balance <= 0:
                return JsonResponse({'success': False, 'error': str(_('Current balance must be greater than zero.'))}, status=400)
            if months_remaining <= 0:
                return JsonResponse({'success': False, 'error': str(_('Months remaining must be greater than zero.'))}, status=400)
            if new_term <= 0:
                return JsonResponse({'success': False, 'error': str(_('New loan term must be greater than zero.'))}, status=400)
            # Cap terms to avoid overflow in (1+r)^n
            months_remaining = min(months_remaining, 600)
            new_term = min(new_term, 600)

            points_cost = current_balance * (points / 100)
            total_closing_costs = closing_costs + points_cost
            if roll_costs_into_loan:
                new_loan_amount = current_balance + total_closing_costs + cash_out
            else:
                new_loan_amount = current_balance + cash_out

            current_monthly_rate = current_rate / 100 / 12
            current_total_remaining = current_payment * months_remaining

            balance = current_balance
            current_remaining_interest = 0
            for _ in range(months_remaining):
                interest = balance * current_monthly_rate
                principal = current_payment - interest
                if principal > balance:
                    principal = balance
                current_remaining_interest += interest
                balance -= principal
                if balance <= 0:
                    break

            new_monthly_rate = new_rate / 100 / 12
            if new_monthly_rate > 0:
                factor = (1 + new_monthly_rate) ** new_term
                new_payment = new_loan_amount * (new_monthly_rate * factor) / (factor - 1)
            else:
                new_payment = new_loan_amount / new_term

            new_total_payments = new_payment * new_term
            new_total_interest = new_total_payments - new_loan_amount
            monthly_savings = current_payment - new_payment

            if monthly_savings > 0:
                if roll_costs_into_loan:
                    break_even_months = 0
                else:
                    break_even_months = int(math.ceil(total_closing_costs / monthly_savings))
            else:
                break_even_months = -1

            current_total_cost = current_total_remaining
            new_total_cost = new_total_payments + (0 if roll_costs_into_loan else total_closing_costs)
            lifetime_savings = current_total_cost - new_total_cost
            interest_savings = current_remaining_interest - new_total_interest

            current_schedule = []
            new_schedule = []
            current_balance_by_year = [round(current_balance, 2)]
            new_balance_by_year = [round(new_loan_amount, 2)]

            bal_cur = current_balance
            for month in range(1, min(months_remaining + 1, 361)):
                interest = bal_cur * current_monthly_rate
                principal = current_payment - interest
                if principal > bal_cur:
                    principal = bal_cur
                bal_cur = max(0, bal_cur - principal)
                if month <= 12 or month % 12 == 0:
                    current_schedule.append({
                        'month': month,
                        'payment': round(current_payment, 2),
                        'principal': round(principal, 2),
                        'interest': round(interest, 2),
                        'balance': round(bal_cur, 2)
                    })
                if month % 12 == 0:
                    current_balance_by_year.append(round(bal_cur, 2))

            bal_new = new_loan_amount
            for month in range(1, min(new_term + 1, 361)):
                interest = bal_new * new_monthly_rate
                principal = new_payment - interest
                if principal > bal_new:
                    principal = bal_new
                bal_new = max(0, bal_new - principal)
                if month <= 12 or month % 12 == 0:
                    new_schedule.append({
                        'month': month,
                        'payment': round(new_payment, 2),
                        'principal': round(principal, 2),
                        'interest': round(interest, 2),
                        'balance': round(bal_new, 2)
                    })
                if month % 12 == 0:
                    new_balance_by_year.append(round(bal_new, 2))

            if lifetime_savings > 0 and break_even_months >= 0:
                if break_even_months <= 24:
                    recommendation = str(_("Strongly recommended - quick break-even and significant savings"))
                elif break_even_months <= 48:
                    recommendation = str(_("Recommended if you plan to stay in home 4+ years"))
                else:
                    recommendation = str(_("Consider carefully - long break-even period"))
            elif lifetime_savings > 0:
                recommendation = str(_("May be worth it for lower payments despite higher total cost"))
            else:
                recommendation = str(_("Not recommended - refinancing would cost more overall"))

            result = {
                'success': True,
                'current_loan': {
                    'balance': round(current_balance, 2),
                    'rate': current_rate,
                    'payment': round(current_payment, 2),
                    'months_remaining': months_remaining,
                    'years_remaining': round(months_remaining / 12, 1),
                    'total_remaining': round(current_total_remaining, 2),
                    'remaining_interest': round(current_remaining_interest, 2)
                },
                'new_loan': {
                    'amount': round(new_loan_amount, 2),
                    'rate': new_rate,
                    'term_months': new_term,
                    'term_years': round(new_term / 12, 1),
                    'payment': round(new_payment, 2),
                    'total_payments': round(new_total_payments, 2),
                    'total_interest': round(new_total_interest, 2)
                },
                'costs': {
                    'closing_costs': round(closing_costs, 2),
                    'points': points,
                    'points_cost': round(points_cost, 2),
                    'total_closing_costs': round(total_closing_costs, 2),
                    'cash_out': round(cash_out, 2),
                    'rolled_into_loan': roll_costs_into_loan
                },
                'savings': {
                    'monthly_savings': round(monthly_savings, 2),
                    'break_even_months': break_even_months,
                    'break_even_years': round(break_even_months / 12, 1) if break_even_months > 0 else 0,
                    'lifetime_savings': round(lifetime_savings, 2),
                    'interest_savings': round(interest_savings, 2)
                },
                'comparison': {
                    'rate_reduction': round(current_rate - new_rate, 2),
                    'payment_change': round(new_payment - current_payment, 2),
                    'term_change_months': new_term - months_remaining
                },
                'recommendation': recommendation,
                'current_schedule': current_schedule[:24],
                'new_schedule': new_schedule[:24]
            }
            result['chart_data'] = self._prepare_chart_data(
                new_loan_amount, new_total_interest, total_closing_costs, roll_costs_into_loan,
                current_balance_by_year, new_balance_by_year
            )
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Refinance JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Refinance calculation failed: %s", e)
            from django.conf import settings
            err_msg = "An error occurred during calculation."
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )

    def _prepare_chart_data(self, new_loan_amount, new_total_interest, total_closing_costs, roll_costs_into_loan,
                            current_balance_by_year, new_balance_by_year):
        """Backend-controlled chart data: breakdown doughnut + balance-over-time line chart."""
        out = {}
        breakdown_labels = [str(_('New principal')), str(_('Interest (new loan)'))]
        breakdown_values = [float(round(new_loan_amount, 2)), float(round(new_total_interest, 2))]
        if total_closing_costs > 0 and not roll_costs_into_loan:
            breakdown_labels.append(str(_('Closing costs')))
            breakdown_values.append(float(round(total_closing_costs, 2)))
        out['breakdown_chart'] = {
            'type': 'doughnut',
            'data': {
                'labels': breakdown_labels,
                'datasets': [{
                    'data': breakdown_values,
                    'backgroundColor': ['#6366f1', '#ef4444', '#f59e0b'],
                    'borderWidth': 0
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'cutout': '60%',
                'plugins': {'legend': {'position': 'bottom'}}
            }
        }
        max_years = max(len(current_balance_by_year), len(new_balance_by_year))
        years_labels = [str(_('Year')) + ' ' + str(i) for i in range(max_years)]
        cur_data = current_balance_by_year + [0] * (max_years - len(current_balance_by_year))
        new_data = new_balance_by_year + [0] * (max_years - len(new_balance_by_year))
        out['balance_chart'] = {
            'type': 'line',
            'data': {
                'labels': years_labels,
                'datasets': [
                    {
                        'label': str(_('Current loan balance')),
                        'data': cur_data[:max_years],
                        'borderColor': '#ef4444',
                        'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                        'fill': True,
                        'tension': 0.2
                    },
                    {
                        'label': str(_('New loan balance')),
                        'data': new_data,
                        'borderColor': '#22c55e',
                        'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                        'fill': True,
                        'tension': 0.2
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'scales': {
                    'x': {'grid': {'display': False}},
                    'y': {'beginAtZero': True}
                },
                'plugins': {'legend': {'position': 'top'}}
            }
        }
        return out
