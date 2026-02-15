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
    """Encode lazy translations and other non-standard types to strings for JSON."""

    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PaymentCalculator(View):
    """
    Class-based view for Payment Calculator.
    Calculates monthly loan payments; returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/payment_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Payment Calculator'))}
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
            loan_term = self._get_int(data, 'loan_term', 0)
            term_unit = data.get('term_unit', 'years')
            if isinstance(term_unit, list):
                term_unit = term_unit[0] if term_unit else 'years'

            if loan_amount <= 0 or loan_amount > 100000000:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid loan amount.'))}, status=400)
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': str(_('Interest rate must be between 0%% and 50%%.'))}, status=400)
            if loan_term <= 0:
                return JsonResponse({'success': False, 'error': str(_('Loan term must be greater than 0.'))}, status=400)

            num_payments = loan_term * 12 if term_unit == 'years' else loan_term
            num_payments = min(num_payments, 600)  # Cap to avoid overflow in (1+r)^n
            monthly_rate = (interest_rate / 100) / 12

            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments

            total_payment = monthly_payment * num_payments
            total_interest = total_payment - loan_amount

            scenarios = []
            for term in [12, 24, 36, 48, 60, 72]:
                if monthly_rate > 0:
                    pmt = loan_amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
                else:
                    pmt = loan_amount / term
                total = pmt * term
                scenarios.append({
                    'term_months': term,
                    'term_years': term / 12,
                    'monthly_payment': round(pmt, 2),
                    'total_payment': round(total, 2),
                    'total_interest': round(total - loan_amount, 2)
                })

            schedule = []
            balance = loan_amount
            for month in range(1, min(13, num_payments + 1)):
                interest_pmt = balance * monthly_rate
                principal_pmt = monthly_payment - interest_pmt
                balance = max(0, balance - principal_pmt)
                schedule.append({
                    'month': month,
                    'payment': round(monthly_payment, 2),
                    'principal': round(principal_pmt, 2),
                    'interest': round(interest_pmt, 2),
                    'balance': round(balance, 2)
                })

            interest_pct = (total_interest / total_payment * 100) if total_payment > 0 else 0

            result = {
                'success': True,
                'summary': {
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'loan_term': loan_term,
                    'term_unit': term_unit,
                    'num_payments': num_payments,
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payment': round(total_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'interest_pct': round(interest_pct, 1),
                    'biweekly_payment': round(monthly_payment / 2, 2),
                    'weekly_payment': round(monthly_payment / 4.33, 2)
                },
                'scenarios': scenarios,
                'schedule': schedule,
            }
            result['chart_data'] = self._prepare_chart_data(
                loan_amount, total_interest, schedule
            )
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Payment JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Payment calculation failed: %s", e)
            from django.conf import settings
            err_msg = "An error occurred during calculation."
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )

    def _prepare_chart_data(self, principal, total_interest, schedule=None):
        """Backend-controlled chart data (BMI-style): breakdown doughnut + schedule stacked bar."""
        if principal <= 0 and total_interest <= 0:
            return {}
        out = {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Principal')), str(_('Interest'))],
                    'datasets': [{
                        'data': [round(principal, 2), round(total_interest, 2)],
                        'backgroundColor': ['#3b82f6', '#ef4444'],
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
        }
        if schedule:
            months = [str(_('Month')) + ' ' + str(r['month']) for r in schedule]
            principals = [r['principal'] for r in schedule]
            interests = [r['interest'] for r in schedule]
            out['schedule_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': months,
                    'datasets': [
                        {
                            'label': str(_('Principal')),
                            'data': principals,
                            'backgroundColor': '#3b82f6',
                            'borderRadius': 4,
                            'borderWidth': 0
                        },
                        {
                            'label': str(_('Interest')),
                            'data': interests,
                            'backgroundColor': '#ef4444',
                            'borderRadius': 4,
                            'borderWidth': 0
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {'stacked': True, 'grid': {'display': False}},
                        'y': {'stacked': True, 'beginAtZero': True}
                    },
                    'plugins': {'legend': {'position': 'top'}}
                }
            }
        return out
