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
class RentCalculator(View):
    """
    Class-based view for Rent Affordability Calculator.
    Calculates how much rent you can afford based on income and debt.
    Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/rent_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Rent Affordability Calculator'))}
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

            # Support both gross_income+income_period and monthly_income+additional_income
            gross_income = self._get_float(data, 'gross_income', 0)
            income_period = data.get('income_period', 'monthly')
            if isinstance(income_period, list):
                income_period = income_period[0] if income_period else 'monthly'
            monthly_income = self._get_float(data, 'monthly_income', 0)
            additional_income = self._get_float(data, 'additional_income', 0)
            if gross_income <= 0 and (monthly_income > 0 or additional_income > 0):
                gross_income = monthly_income + additional_income
                income_period = 'monthly'

            car_payment = self._get_float(data, 'car_payment', 0)
            student_loans = self._get_float(data, 'student_loans', 0)
            credit_card_payments = self._get_float(data, 'credit_card_payments', 0)
            if credit_card_payments == 0:
                credit_card_payments = self._get_float(data, 'credit_cards', 0)
            other_debt = self._get_float(data, 'other_debt', 0)
            if other_debt == 0:
                other_debt = self._get_float(data, 'other_debts', 0)
            utilities = self._get_float(data, 'utilities', 0)
            preferred_rent_percent = self._get_float(data, 'rent_percent', 30)
            if preferred_rent_percent <= 0:
                preferred_rent_percent = self._get_float(data, 'budget_rule', 30)

            if gross_income <= 0:
                return JsonResponse({'success': False, 'error': str(_('Gross income must be greater than zero.'))}, status=400)

            if income_period == 'annual':
                monthly_income = gross_income / 12
                annual_income = gross_income
            else:
                monthly_income = gross_income
                annual_income = gross_income * 12

            estimated_tax_rate = 22
            net_monthly_income = monthly_income * (1 - estimated_tax_rate / 100)
            total_monthly_debt = car_payment + student_loans + credit_card_payments + other_debt

            rent_30_percent = monthly_income * 0.30
            rent_28_percent = monthly_income * 0.28
            max_total_debt_36 = monthly_income * 0.36
            available_for_rent_36 = max(0, max_total_debt_36 - total_monthly_debt)
            needs_budget = net_monthly_income * 0.50
            rent_50_30_20 = max(0, needs_budget - utilities)
            rent_custom = monthly_income * (preferred_rent_percent / 100)
            rent_conservative = monthly_income * 0.25
            rent_aggressive = monthly_income * 0.35

            recommended_rent = rent_30_percent
            after_rent = net_monthly_income - recommended_rent - total_monthly_debt - utilities

            budget_breakdown = {
                'rent': round(recommended_rent, 2),
                'utilities': round(utilities, 2),
                'debt_payments': round(total_monthly_debt, 2),
                'estimated_taxes': round(monthly_income * (estimated_tax_rate / 100), 2),
                'remaining': round(after_rent, 2)
            }

            rent_ranges = [
                {'percent': 25, 'monthly': round(monthly_income * 0.25, 2), 'label': str(_('Conservative'))},
                {'percent': 28, 'monthly': round(monthly_income * 0.28, 2), 'label': str(_('28% Rule'))},
                {'percent': 30, 'monthly': round(monthly_income * 0.30, 2), 'label': str(_('Standard (30%)'))},
                {'percent': 33, 'monthly': round(monthly_income * 0.33, 2), 'label': str(_('Moderate'))},
                {'percent': 35, 'monthly': round(monthly_income * 0.35, 2), 'label': str(_('Maximum'))},
            ]

            summary = {
                'gross_annual': round(annual_income, 2),
                'gross_monthly': round(monthly_income, 2),
                'net_monthly_estimate': round(net_monthly_income, 2),
                'recommended_rent': round(recommended_rent, 2),
                'rent_30_rule': round(rent_30_percent, 2),
                'rent_28_rule': round(rent_28_percent, 2),
                'rent_36_available': round(available_for_rent_36, 2),
                'rent_50_30_20': round(rent_50_30_20, 2),
                'rent_custom': round(rent_custom, 2),
                'custom_percent': preferred_rent_percent,
                'total_debt': round(total_monthly_debt, 2),
                'utilities': round(utilities, 2),
                'after_rent': round(after_rent, 2),
                'rent_conservative': round(rent_conservative, 2),
                'rent_aggressive': round(rent_aggressive, 2),
            }

            result = {
                'success': True,
                'summary': summary,
                'budget_breakdown': budget_breakdown,
                'rent_ranges': rent_ranges,
            }
            result['chart_data'] = self._prepare_chart_data(
                budget_breakdown, rent_ranges
            )
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Rent JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Rent calculation failed: %s", e)
            from django.conf import settings
            err_msg = "An error occurred during calculation."
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )

    def _prepare_chart_data(self, budget_breakdown, rent_ranges):
        """Backend-controlled: budget doughnut + rent ranges bar chart."""
        out = {}
        rent = float(budget_breakdown.get('rent', 0))
        utilities = float(budget_breakdown.get('utilities', 0))
        debt = float(budget_breakdown.get('debt_payments', 0))
        remaining = float(budget_breakdown.get('remaining', 0))
        if rent <= 0 and utilities <= 0 and debt <= 0 and remaining <= 0:
            return out
        out['breakdown_chart'] = {
            'type': 'doughnut',
            'data': {
                'labels': [
                    str(_('Rent')),
                    str(_('Utilities')),
                    str(_('Debt payments')),
                    str(_('Remaining'))
                ],
                'datasets': [{
                    'data': [rent, utilities, debt, max(0, remaining)],
                    'backgroundColor': ['#ec4899', '#f59e0b', '#ef4444', '#22c55e'],
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
        if rent_ranges:
            labels = [str(r.get('percent', 0)) + '%' for r in rent_ranges]
            values = [float(r.get('monthly', 0)) for r in rent_ranges]
            out['ranges_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Monthly rent')),
                        'data': values,
                        'backgroundColor': '#ec4899',
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
