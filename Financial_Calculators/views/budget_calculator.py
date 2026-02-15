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
class BudgetCalculator(View):
    """
    Class-based view for Budget Calculator.
    Helps users create and analyze their monthly budget. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/budget_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Budget Calculator'))}
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

    def _prepare_chart_data(self, categories, recommended, category_order, category_labels):
        """Backend-controlled: breakdown doughnut + actual vs recommended bar chart."""
        out = {}
        amounts = [float(categories.get(k, {}).get('amount', 0)) for k in category_order]
        labels = [str(category_labels.get(k, k)) for k in category_order]
        colors = ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#6b7280']
        if any(amounts):
            out['breakdown_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': amounts,
                        'backgroundColor': colors[: len(labels)],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'cutout': '55%',
                    'plugins': {'legend': {'position': 'bottom'}}
                }
            }
        rec_values = [float(recommended.get(k, 0)) for k in category_order]
        if any(amounts) or any(rec_values):
            out['comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': str(_('Actual')),
                            'data': amounts,
                            'backgroundColor': '#3b82f6',
                            'borderRadius': 4,
                            'borderWidth': 0
                        },
                        {
                            'label': str(_('Recommended')),
                            'data': rec_values,
                            'backgroundColor': '#d1d5db',
                            'borderRadius': 4,
                            'borderWidth': 0
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom'}},
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True}
                    }
                }
            }
        return out

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            salary = self._get_float(data, 'salary', 0)
            other_income = self._get_float(data, 'other_income', 0)
            total_income = salary + other_income

            rent_mortgage = self._get_float(data, 'rent_mortgage', 0)
            utilities = self._get_float(data, 'utilities', 0)
            insurance_home = self._get_float(data, 'insurance_home', 0)
            car_payment = self._get_float(data, 'car_payment', 0)
            gas = self._get_float(data, 'gas', 0)
            car_insurance = self._get_float(data, 'car_insurance', 0)
            groceries = self._get_float(data, 'groceries', 0)
            dining = self._get_float(data, 'dining', 0)
            entertainment = self._get_float(data, 'entertainment', 0)
            credit_cards = self._get_float(data, 'credit_cards', 0)
            student_loans = self._get_float(data, 'student_loans', 0)
            other_debt = self._get_float(data, 'other_debt', 0)
            savings = self._get_float(data, 'savings', 0)
            retirement = self._get_float(data, 'retirement', 0)
            healthcare = self._get_float(data, 'healthcare', 0)
            other_expenses = self._get_float(data, 'other_expenses', 0)

            if total_income <= 0:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid income.'))}, status=400)

            housing = rent_mortgage + utilities + insurance_home
            transportation = car_payment + gas + car_insurance
            living = groceries + dining + entertainment
            debt = credit_cards + student_loans + other_debt
            savings_total = savings + retirement
            other = healthcare + other_expenses

            total_expenses = housing + transportation + living + debt + savings_total + other
            remaining = total_income - total_expenses

            def pct(val):
                return round((val / total_income) * 100, 1) if total_income > 0 else 0

            housing_pct = pct(housing)
            savings_pct = pct(savings_total)
            debt_pct = pct(debt)

            status = 'healthy'
            recommendations = []

            if remaining < 0:
                status = 'deficit'
                recommendations.append(str(_('You are spending more than you earn. Review expenses to reduce spending.')))
            elif housing_pct > 30:
                status = 'warning'
                recommendations.append(
                    str(_('Housing costs (%(pct)s%%) exceed the recommended 30%% of income.')) % {'pct': housing_pct}
                )
            if savings_pct < 20:
                recommendations.append(
                    str(_('Try to save at least 20%% of income. Currently saving %(pct)s%%.')) % {'pct': savings_pct}
                )
            if debt_pct > 20:
                recommendations.append(
                    str(_('Debt payments (%(pct)s%%) are high. Consider debt reduction strategies.')) % {'pct': debt_pct}
                )
            if remaining > 0 and savings_pct < 20:
                recommendations.append(
                    str(_('Consider allocating %(amount)s to savings or debt payoff.')) % {'amount': f'${remaining:,.0f}'}
                )
            if savings_pct >= 20 and housing_pct <= 30 and debt_pct <= 20 and remaining >= 0:
                recommendations.append(str(_('Great job! Your budget follows healthy financial guidelines.')))

            categories = {
                'housing': {'amount': round(housing, 2), 'percentage': pct(housing)},
                'transportation': {'amount': round(transportation, 2), 'percentage': pct(transportation)},
                'living': {'amount': round(living, 2), 'percentage': pct(living)},
                'debt': {'amount': round(debt, 2), 'percentage': pct(debt)},
                'savings': {'amount': round(savings_total, 2), 'percentage': pct(savings_total)},
                'other': {'amount': round(other, 2), 'percentage': pct(other)}
            }
            recommended = {
                'housing': round(total_income * 0.30, 2),
                'transportation': round(total_income * 0.15, 2),
                'living': round(total_income * 0.15, 2),
                'debt': round(total_income * 0.10, 2),
                'savings': round(total_income * 0.20, 2),
                'other': round(total_income * 0.10, 2)
            }
            category_order = ['housing', 'transportation', 'living', 'debt', 'savings', 'other']
            category_labels = {
                'housing': str(_('Housing')),
                'transportation': str(_('Transportation')),
                'living': str(_('Living')),
                'debt': str(_('Debt')),
                'savings': str(_('Savings')),
                'other': str(_('Other'))
            }

            summary = {
                'total_income': round(total_income, 2),
                'total_expenses': round(total_expenses, 2),
                'remaining': round(remaining, 2),
                'status': status,
                'recommendations': recommendations
            }

            result = {
                'success': True,
                'summary': summary,
                'categories': categories,
                'recommended': recommended,
            }
            result['chart_data'] = self._prepare_chart_data(
                categories, recommended, category_order, category_labels
            )

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Budget JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Budget calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
