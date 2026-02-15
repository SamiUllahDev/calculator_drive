from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SalaryCalculator(View):
    """
    Class-based view for Salary Calculator.
    Converts between pay periods, calculates raises, compares offers, and overtime.
    Returns Chart.js-ready chart_data where applicable (BMI-style).
    """
    template_name = 'financial_calculators/salary_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Salary Calculator'),
            'page_title': _('Salary Calculator - Convert Hourly, Monthly, Annual Pay'),
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

    def _to_annual(self, amount, period, hours_per_week=40):
        if period == 'hourly':
            return amount * hours_per_week * 52
        if period == 'daily':
            return amount * 5 * 52
        if period == 'weekly':
            return amount * 52
        if period == 'biweekly':
            return amount * 26
        if period == 'semimonthly':
            return amount * 24
        if period == 'monthly':
            return amount * 12
        return amount  # annual

    def post(self, request):
        """Handle POST request for salary calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'convert')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'convert'

            if calc_type == 'convert':
                amount = self._get_float(data, 'amount', 0)
                period = data.get('period', 'annual')
                if isinstance(period, list):
                    period = period[0] if period else 'annual'
                hours_per_week = self._get_float(data, 'hours_per_week', 40)
                weeks_per_year = self._get_float(data, 'weeks_per_year', 52)

                if amount < 0:
                    return JsonResponse({'success': False, 'error': str(_('Salary cannot be negative.'))}, status=400)
                if hours_per_week <= 0 or hours_per_week > 168:
                    return JsonResponse({'success': False, 'error': str(_('Hours per week must be between 1 and 168.'))}, status=400)
                if weeks_per_year <= 0 or weeks_per_year > 52:
                    return JsonResponse({'success': False, 'error': str(_('Weeks per year must be between 1 and 52.'))}, status=400)

                if period == 'hourly':
                    annual = amount * hours_per_week * weeks_per_year
                elif period == 'daily':
                    annual = amount * 5 * weeks_per_year
                elif period == 'weekly':
                    annual = amount * weeks_per_year
                elif period == 'biweekly':
                    annual = amount * (weeks_per_year / 2)
                elif period == 'semimonthly':
                    annual = amount * 24
                elif period == 'monthly':
                    annual = amount * 12
                else:
                    annual = amount

                hourly = annual / (hours_per_week * weeks_per_year) if (hours_per_week * weeks_per_year) > 0 else 0
                daily = annual / (5 * weeks_per_year) if weeks_per_year > 0 else 0
                weekly = annual / weeks_per_year if weeks_per_year > 0 else 0
                biweekly = annual / (weeks_per_year / 2) if weeks_per_year > 0 else 0
                semimonthly = annual / 24
                monthly = annual / 12

                result = {
                    'success': True,
                    'calc_type': 'convert',
                    'input': {
                        'amount': round(amount, 2),
                        'period': period,
                        'hours_per_week': hours_per_week,
                        'weeks_per_year': weeks_per_year
                    },
                    'conversions': {
                        'hourly': round(hourly, 2),
                        'daily': round(daily, 2),
                        'weekly': round(weekly, 2),
                        'biweekly': round(biweekly, 2),
                        'semimonthly': round(semimonthly, 2),
                        'monthly': round(monthly, 2),
                        'annual': round(annual, 2)
                    },
                    'formatted': {
                        'hourly': f'${hourly:,.2f}/hour',
                        'daily': f'${daily:,.2f}/day',
                        'weekly': f'${weekly:,.2f}/week',
                        'biweekly': f'${biweekly:,.2f}/2 weeks',
                        'semimonthly': f'${semimonthly:,.2f}/semi-month',
                        'monthly': f'${monthly:,.2f}/month',
                        'annual': f'${annual:,.2f}/year'
                    }
                }
                result['chart_data'] = self._prepare_chart_data('convert', result)

            elif calc_type == 'raise':
                current_salary = self._get_float(data, 'current_salary', 0)
                raise_type = data.get('raise_type', 'percentage')
                if isinstance(raise_type, list):
                    raise_type = raise_type[0] if raise_type else 'percentage'
                raise_value = self._get_float(data, 'raise_value', 0)

                if current_salary < 0:
                    return JsonResponse({'success': False, 'error': str(_('Current salary cannot be negative.'))}, status=400)

                if raise_type == 'percentage':
                    raise_amount = current_salary * (raise_value / 100)
                else:
                    raise_amount = raise_value

                new_salary = current_salary + raise_amount
                percentage_increase = (raise_amount / current_salary * 100) if current_salary > 0 else 0

                result = {
                    'success': True,
                    'calc_type': 'raise',
                    'current_salary': round(current_salary, 2),
                    'raise_amount': round(raise_amount, 2),
                    'new_salary': round(new_salary, 2),
                    'percentage_increase': round(percentage_increase, 2),
                    'monthly_increase': round(raise_amount / 12, 2),
                    'biweekly_increase': round(raise_amount / 26, 2)
                }
                result['chart_data'] = self._prepare_chart_data('raise', result)

            elif calc_type == 'compare':
                offer1_salary = self._get_float(data, 'offer1_salary', 0)
                offer1_period = data.get('offer1_period', 'annual')
                if isinstance(offer1_period, list):
                    offer1_period = offer1_period[0] if offer1_period else 'annual'
                offer2_salary = self._get_float(data, 'offer2_salary', 0)
                offer2_period = data.get('offer2_period', 'annual')
                if isinstance(offer2_period, list):
                    offer2_period = offer2_period[0] if offer2_period else 'annual'
                hours_per_week = self._get_float(data, 'hours_per_week', 40)

                offer1_annual = self._to_annual(offer1_salary, offer1_period, hours_per_week)
                offer2_annual = self._to_annual(offer2_salary, offer2_period, hours_per_week)
                difference = offer1_annual - offer2_annual
                percentage_diff = (difference / offer2_annual * 100) if offer2_annual > 0 else 0

                result = {
                    'success': True,
                    'calc_type': 'compare',
                    'offer1': {
                        'salary': round(offer1_salary, 2),
                        'period': offer1_period,
                        'annual': round(offer1_annual, 2),
                        'monthly': round(offer1_annual / 12, 2),
                        'hourly': round(offer1_annual / (hours_per_week * 52), 2) if hours_per_week > 0 else 0
                    },
                    'offer2': {
                        'salary': round(offer2_salary, 2),
                        'period': offer2_period,
                        'annual': round(offer2_annual, 2),
                        'monthly': round(offer2_annual / 12, 2),
                        'hourly': round(offer2_annual / (hours_per_week * 52), 2) if hours_per_week > 0 else 0
                    },
                    'comparison': {
                        'difference': round(difference, 2),
                        'percentage_difference': round(percentage_diff, 2),
                        'monthly_difference': round(difference / 12, 2),
                        'better_offer': 'Offer 1' if difference > 0 else ('Offer 2' if difference < 0 else 'Equal')
                    }
                }
                result['chart_data'] = self._prepare_chart_data('compare', result)

            elif calc_type == 'overtime':
                hourly_rate = self._get_float(data, 'hourly_rate', 0)
                regular_hours = self._get_float(data, 'regular_hours', 40)
                overtime_hours = self._get_float(data, 'overtime_hours', 0)
                overtime_multiplier = self._get_float(data, 'overtime_multiplier', 1.5)

                if hourly_rate < 0:
                    return JsonResponse({'success': False, 'error': str(_('Hourly rate cannot be negative.'))}, status=400)

                regular_pay = hourly_rate * regular_hours
                overtime_rate = hourly_rate * overtime_multiplier
                overtime_pay = overtime_rate * overtime_hours
                total_pay = regular_pay + overtime_pay
                monthly_with_ot = total_pay * 4.33
                annual_with_ot = total_pay * 52

                result = {
                    'success': True,
                    'calc_type': 'overtime',
                    'hourly_rate': round(hourly_rate, 2),
                    'overtime_rate': round(overtime_rate, 2),
                    'regular_hours': regular_hours,
                    'overtime_hours': overtime_hours,
                    'regular_pay': round(regular_pay, 2),
                    'overtime_pay': round(overtime_pay, 2),
                    'total_weekly_pay': round(total_pay, 2),
                    'projections': {
                        'monthly': round(monthly_with_ot, 2),
                        'annual': round(annual_with_ot, 2)
                    }
                }
                result['chart_data'] = self._prepare_chart_data('overtime', result)

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            if 'chart_data' not in result:
                result['chart_data'] = {}
            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, calc_type, result):
        """Build Chart.js-ready chart_data (doughnut or bar) where applicable."""
        if calc_type == 'convert' and result.get('conversions'):
            conv = result['conversions']
            labels = [
                str(_('Hourly')), str(_('Daily')), str(_('Weekly')),
                str(_('Bi-weekly')), str(_('Semi-monthly')), str(_('Monthly')), str(_('Annual'))
            ]
            values = [
                conv.get('hourly', 0), conv.get('daily', 0), conv.get('weekly', 0),
                conv.get('biweekly', 0), conv.get('semimonthly', 0), conv.get('monthly', 0), conv.get('annual', 0)
            ]
            return {
                'breakdown_chart': {
                    'type': 'bar',
                    'data': {
                        'labels': labels,
                        'datasets': [{
                            'label': str(_('Amount')),
                            'data': values,
                            'backgroundColor': ['#3b82f6', '#60a5fa', '#93c5fd', '#6366f1', '#8b5cf6', '#a78bfa', '#10b981'],
                            'borderWidth': 0
                        }]
                    },
                    'options': {
                        'responsive': True,
                        'maintainAspectRatio': False,
                        'plugins': {'legend': {'display': False}},
                        'scales': {'y': {'beginAtZero': True}}
                    }
                }
            }
        if calc_type == 'raise':
            current = float(result.get('current_salary', 0))
            raise_amt = float(result.get('raise_amount', 0))
            if current <= 0 and raise_amt <= 0:
                return {}
            return {
                'breakdown_chart': {
                    'type': 'doughnut',
                    'data': {
                        'labels': [str(_('Current')), str(_('Raise'))],
                        'datasets': [{'data': [round(current, 2), round(raise_amt, 2)], 'backgroundColor': ['#6b7280', '#10b981'], 'borderWidth': 0}]
                    },
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}}
                }
            }
        if calc_type == 'compare' and result.get('offer1') and result.get('offer2'):
            o1 = result['offer1']['annual']
            o2 = result['offer2']['annual']
            return {
                'breakdown_chart': {
                    'type': 'bar',
                    'data': {
                        'labels': [str(_('Offer 1')), str(_('Offer 2'))],
                        'datasets': [{'label': str(_('Annual')), 'data': [o1, o2], 'backgroundColor': ['#3b82f6', '#10b981'], 'borderWidth': 0}]
                    },
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'display': False}}, 'scales': {'y': {'beginAtZero': True}}}
                }
            }
        if calc_type == 'overtime':
            reg = float(result.get('regular_pay', 0))
            ot = float(result.get('overtime_pay', 0))
            if reg <= 0 and ot <= 0:
                return {}
            return {
                'breakdown_chart': {
                    'type': 'doughnut',
                    'data': {
                        'labels': [str(_('Regular')), str(_('Overtime'))],
                        'datasets': [{'data': [round(reg, 2), round(ot, 2)], 'backgroundColor': ['#3b82f6', '#f59e0b'], 'borderWidth': 0}]
                    },
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}}
                }
            }
        return {}
