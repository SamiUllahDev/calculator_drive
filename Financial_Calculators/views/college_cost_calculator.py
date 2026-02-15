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


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CollegeCostCalculator(View):
    """
    Class-based view for College Cost Calculator.
    Projects future college costs and optional savings needed.
    Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/college_cost_calculator.html'

    COLLEGE_COSTS = {
        'public_in_state': {'tuition': 10940, 'room_board': 12310, 'books': 1240, 'other': 2350},
        'public_out_state': {'tuition': 23630, 'room_board': 12310, 'books': 1240, 'other': 2350},
        'private': {'tuition': 39400, 'room_board': 14650, 'books': 1240, 'other': 2860},
        'community': {'tuition': 3900, 'room_board': 9500, 'books': 1460, 'other': 2000}
    }

    def get(self, request):
        context = {'calculator_name': str(_('College Cost Calculator'))}
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

            child_age = self._get_int(data, 'child_age', 10)
            college_type = data.get('college_type', 'public_in_state')
            if isinstance(college_type, list):
                college_type = college_type[0] if college_type else 'public_in_state'
            years_in_college = self._get_int(data, 'years_in_college', 4)
            if years_in_college <= 0:
                years_in_college = self._get_int(data, 'years_of_college', 4)
            inflation_rate = self._get_float(data, 'inflation_rate', 5)
            custom_annual_cost = data.get('custom_annual_cost')
            current_savings = self._get_float(data, 'current_savings', 0)
            expected_return = self._get_float(data, 'expected_return', 6)
            if expected_return == 0:
                expected_return = self._get_float(data, 'return_rate', 6)

            if child_age < 0 or child_age > 18:
                return JsonResponse({'success': False, 'error': str(_('Child age must be between 0 and 18.'))}, status=400)

            years_until_college = max(0, 18 - child_age)

            if custom_annual_cost:
                try:
                    current_annual_cost = self._get_float(data, 'custom_annual_cost', 0)
                except Exception:
                    current_annual_cost = 0
                if current_annual_cost <= 0:
                    current_annual_cost = 25000
                cost_breakdown = {
                    'tuition': current_annual_cost * 0.55,
                    'room_board': current_annual_cost * 0.30,
                    'books': current_annual_cost * 0.05,
                    'other': current_annual_cost * 0.10
                }
            else:
                base_costs = self.COLLEGE_COSTS.get(college_type, self.COLLEGE_COSTS['public_in_state'])
                current_annual_cost = sum(base_costs.values())
                cost_breakdown = dict(base_costs)

            yearly_costs = []
            total_projected_cost = 0
            for year in range(years_in_college):
                years_from_now = years_until_college + year
                factor = (1 + inflation_rate / 100) ** years_from_now
                projected_cost = current_annual_cost * factor
                total_projected_cost += projected_cost
                yearly_costs.append({
                    'college_year': year + 1,
                    'years_from_now': years_from_now,
                    'projected_cost': round(projected_cost, 2)
                })

            projected_breakdown = {
                k: round(v * (1 + inflation_rate / 100) ** years_until_college, 2)
                for k, v in cost_breakdown.items()
            }
            first_year_cost = round(yearly_costs[0]['projected_cost'], 2) if yearly_costs else 0

            summary = {
                'child_age': child_age,
                'years_until_college': years_until_college,
                'college_type': college_type,
                'college_type_display': college_type.replace('_', ' ').title(),
                'years_in_college': years_in_college,
                'inflation_rate': inflation_rate,
                'current_annual_cost': round(current_annual_cost, 2),
                'total_projected_cost': round(total_projected_cost, 2),
                'first_year_cost': first_year_cost,
                'projected_breakdown': projected_breakdown,
            }

            savings_result = None
            if current_savings >= 0 and years_until_college > 0:
                target_amount = total_projected_cost
                monthly_rate = expected_return / 100 / 12
                months = years_until_college * 12
                fv_current_savings = current_savings * (1 + monthly_rate) ** months
                remaining_needed = max(0, target_amount - fv_current_savings)
                if monthly_rate > 0 and remaining_needed > 0:
                    monthly_savings = remaining_needed * monthly_rate / ((1 + monthly_rate) ** months - 1)
                else:
                    monthly_savings = remaining_needed / months if months > 0 else 0
                annual_savings = monthly_savings * 12

                projection = []
                balance = current_savings
                total_contributions = 0
                for year in range(1, min(years_until_college + 1, 31)):
                    yearly_growth = balance * (expected_return / 100)
                    yearly_contribution = annual_savings
                    balance = balance + yearly_growth + yearly_contribution
                    total_contributions += yearly_contribution
                    projection.append({
                        'year': year,
                        'balance': round(balance, 2),
                        'contribution': round(yearly_contribution, 2),
                        'growth': round(yearly_growth, 2)
                    })

                savings_result = {
                    'current_savings': round(current_savings, 2),
                    'expected_return': expected_return,
                    'target_amount': round(target_amount, 2),
                    'fv_current_savings': round(fv_current_savings, 2),
                    'remaining_needed': round(remaining_needed, 2),
                    'monthly_savings_needed': round(monthly_savings, 2),
                    'annual_savings_needed': round(annual_savings, 2),
                    'projection': projection
                }
                summary['monthly_savings_needed'] = round(monthly_savings, 2)
                summary['annual_savings_needed'] = round(annual_savings, 2)
                summary['funding_gap'] = round(remaining_needed, 2)
                summary['projected_savings_at_start'] = round(fv_current_savings, 2)

            result = {
                'success': True,
                'summary': summary,
                'yearly_costs': yearly_costs,
                'projected_breakdown': projected_breakdown,
            }
            if savings_result:
                result['savings'] = savings_result
            result['chart_data'] = self._prepare_chart_data(
                projected_breakdown, yearly_costs, savings_result
            )
            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("College cost JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("College cost calculation failed: %s", e)
            from django.conf import settings
            err_msg = "An error occurred during calculation."
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )

    def _prepare_chart_data(self, projected_breakdown, yearly_costs, savings_result=None):
        """Backend-controlled: cost breakdown doughnut + yearly cost bar + optional savings line."""
        out = {}
        labels = [
            str(_('Tuition')),
            str(_('Room & board')),
            str(_('Books')),
            str(_('Other'))
        ]
        values = [
            float(projected_breakdown.get('tuition', 0)),
            float(projected_breakdown.get('room_board', 0)),
            float(projected_breakdown.get('books', 0)),
            float(projected_breakdown.get('other', 0))
        ]
        out['breakdown_chart'] = {
            'type': 'doughnut',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': values,
                    'backgroundColor': ['#3b82f6', '#8b5cf6', '#06b6d4', '#f59e0b'],
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
        if yearly_costs:
            year_labels = [str(_('Year')) + ' ' + str(r['college_year']) for r in yearly_costs]
            cost_values = [float(r['projected_cost']) for r in yearly_costs]
            out['yearly_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': year_labels,
                    'datasets': [{
                        'label': str(_('Projected cost')),
                        'data': cost_values,
                        'backgroundColor': '#3b82f6',
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
        if savings_result and savings_result.get('projection'):
            proj = savings_result['projection']
            out['savings_chart'] = {
                'type': 'line',
                'data': {
                    'labels': [str(_('Year')) + ' ' + str(p['year']) for p in proj],
                    'datasets': [{
                        'label': str(_('Savings balance')),
                        'data': [float(p['balance']) for p in proj],
                        'borderColor': '#22c55e',
                        'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                        'fill': True,
                        'tension': 0.2
                    }]
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
