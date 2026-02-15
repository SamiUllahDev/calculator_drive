from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PensionCalculator(View):
    """
    Class-based view for Pension Calculator.
    Calculates pension benefits for defined benefit plans, lump sum vs annuity, and service credits.
    Returns backend-controlled chart_data and color_info (BMI/RMD-style).
    """
    template_name = 'financial_calculators/pension_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Pension Calculator'),
            'page_title': _('Pension Calculator - Calculate Retirement Benefits'),
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

    def get_color_info(self, key):
        """Return color info for UI (backend-controlled, BMI-style)."""
        color_map = {
            'lump_sum': {
                'tailwind_classes': 'bg-green-100 border-2 border-green-300 text-green-800',
                'hex': '#059669',
            },
            'annuity': {
                'tailwind_classes': 'bg-blue-100 border-2 border-blue-300 text-blue-800',
                'hex': '#2563eb',
            },
        }
        return color_map.get(key, color_map['annuity'])

    def post(self, request):
        """Handle POST request for pension calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': _('Invalid request data.')}, status=400)
            
            calc_type = data.get('calc_type', 'defined_benefit')
            
            if calc_type == 'defined_benefit':
                final_salary = self._get_float(data, 'final_salary', 80000)
                years_of_service = int(self._get_float(data, 'years_of_service', 25))
                benefit_multiplier = self._get_float(data, 'benefit_multiplier', 2)
                retirement_age = int(self._get_float(data, 'retirement_age', 65))
                current_age = int(self._get_float(data, 'current_age', 55))
                cola_rate = self._get_float(data, 'cola_rate', 2)

                if final_salary <= 0:
                    return JsonResponse({'success': False, 'error': _('Final salary must be greater than zero.')}, status=400)
                if years_of_service <= 0 or years_of_service > 50:
                    return JsonResponse({'success': False, 'error': _('Years of service must be between 1 and 50.')}, status=400)
                if retirement_age <= current_age:
                    return JsonResponse({'success': False, 'error': _('Retirement age must be greater than current age.')}, status=400)

                annual_pension = final_salary * years_of_service * (benefit_multiplier / 100)
                monthly_pension = annual_pension / 12
                replacement_ratio = (annual_pension / final_salary) * 100

                years_in_retirement = 30
                yearly_benefits = []
                cumulative = 0.0
                labels_list = []
                annual_benefits_list = []

                for year in range(years_in_retirement):
                    age = retirement_age + year
                    adjusted_annual = annual_pension * np.power(1 + cola_rate / 100, year)
                    cumulative += adjusted_annual
                    labels_list.append(str(age))
                    annual_benefits_list.append(round(adjusted_annual, 2))
                    yearly_benefits.append({
                        'year': year + 1,
                        'age': age,
                        'annual_benefit': round(adjusted_annual, 2),
                        'monthly_benefit': round(adjusted_annual / 12, 2),
                        'cumulative': round(cumulative, 2)
                    })

                discount_rate = 0.04
                present_value = sum(
                    annual_pension * np.power(1 + cola_rate / 100, y) / np.power(1 + discount_rate, y)
                    for y in range(years_in_retirement)
                )

                chart_data = self._prepare_defined_benefit_chart_data(labels_list, annual_benefits_list)

                result = {
                    'success': True,
                    'calc_type': 'defined_benefit',
                    'inputs': {
                        'final_salary': round(final_salary, 2),
                        'years_of_service': years_of_service,
                        'benefit_multiplier': benefit_multiplier,
                        'retirement_age': retirement_age,
                        'cola_rate': cola_rate
                    },
                    'pension': {
                        'annual': round(annual_pension, 2),
                        'monthly': round(monthly_pension, 2),
                        'replacement_ratio': round(replacement_ratio, 1)
                    },
                    'projection': {
                        'years_in_retirement': years_in_retirement,
                        'total_benefits': round(cumulative, 2),
                        'present_value': round(present_value, 2),
                        'yearly_breakdown': yearly_benefits[:20]
                    },
                    'formula': f'Annual Pension = ${final_salary:,.0f} × {years_of_service} years × {benefit_multiplier}% = ${annual_pension:,.0f}',
                    'chart_data': chart_data
                }
                
            elif calc_type == 'lump_sum_vs_annuity':
                monthly_annuity = self._get_float(data, 'monthly_annuity', 3000)
                lump_sum_offer = self._get_float(data, 'lump_sum_offer', 500000)
                life_expectancy = int(self._get_float(data, 'life_expectancy', 85))
                retirement_age = int(self._get_float(data, 'ls_retirement_age', self._get_float(data, 'retirement_age', 65)))
                expected_return = self._get_float(data, 'expected_return', 5)

                if monthly_annuity <= 0 or lump_sum_offer <= 0:
                    return JsonResponse({'success': False, 'error': _('Both values must be greater than zero.')}, status=400)

                years_in_retirement = max(1, life_expectancy - retirement_age)
                annual_annuity = monthly_annuity * 12
                total_annuity = annual_annuity * years_in_retirement

                balance = lump_sum_offer
                lump_sum_projection = []
                annual_withdrawal = annual_annuity
                monthly_return = expected_return / 100 / 12
                labels_list = []
                end_balances_list = []

                for year in range(years_in_retirement):
                    year_start = balance
                    for month in range(12):
                        balance = balance * (1 + monthly_return) - (annual_withdrawal / 12)
                    end_bal = max(0.0, balance)
                    labels_list.append(str(retirement_age + year))
                    end_balances_list.append(round(end_bal, 2))
                    lump_sum_projection.append({
                        'year': year + 1,
                        'age': retirement_age + year,
                        'start_balance': round(year_start, 2),
                        'end_balance': round(end_bal, 2)
                    })
                    if balance <= 0:
                        break

                implied_rate = (total_annuity / lump_sum_offer) ** (1 / years_in_retirement) - 1 if lump_sum_offer else 0

                if balance > 0:
                    recommendation = 'lump_sum'
                    reason = _('Lump sum would have %(amount)s remaining after %(years)s years.') % {
                        'amount': f'${balance:,.0f}', 'years': years_in_retirement
                    }
                else:
                    years_lasted = len([p for p in lump_sum_projection if p['end_balance'] > 0])
                    recommendation = 'annuity'
                    reason = _('Lump sum would run out in %(years)s years. Annuity provides lifetime income.') % {'years': years_lasted}

                chart_data = self._prepare_lump_sum_chart_data(labels_list, end_balances_list)
                recommendation_info = {
                    'recommendation': recommendation,
                    'reason': reason,
                    'color_info': self.get_color_info(recommendation)
                }

                result = {
                    'success': True,
                    'calc_type': 'lump_sum_vs_annuity',
                    'annuity': {
                        'monthly': round(monthly_annuity, 2),
                        'annual': round(annual_annuity, 2),
                        'total_lifetime': round(total_annuity, 2)
                    },
                    'lump_sum': {
                        'offer': round(lump_sum_offer, 2),
                        'expected_return': expected_return,
                        'final_balance': round(max(0, balance), 2),
                        'projection': lump_sum_projection[:20]
                    },
                    'comparison': {
                        'years_in_retirement': years_in_retirement,
                        'implied_rate': round(implied_rate * 100, 2),
                        'recommendation': recommendation,
                        'reason': reason
                    },
                    'recommendation_info': recommendation_info,
                    'chart_data': chart_data
                }
                
            elif calc_type == 'service_credit':
                current_salary = self._get_float(data, 'current_salary', 0)
                years_to_purchase = self._get_float(data, 'years_to_purchase', 0)
                cost_percentage = self._get_float(data, 'cost_percentage', 10)
                benefit_multiplier = self._get_float(data, 'benefit_multiplier', 2)
                years_until_retirement = int(self._get_float(data, 'years_until_retirement', 10))

                if current_salary <= 0 or years_to_purchase <= 0:
                    return JsonResponse({'success': False, 'error': _('Invalid input values.')}, status=400)

                purchase_cost = current_salary * years_to_purchase * (cost_percentage / 100)
                additional_benefit = current_salary * years_to_purchase * (benefit_multiplier / 100)
                payback_years = purchase_cost / additional_benefit if additional_benefit > 0 else 0
                total_additional = additional_benefit * 20
                roi = ((total_additional - purchase_cost) / purchase_cost * 100) if purchase_cost > 0 else 0

                result = {
                    'success': True,
                    'calc_type': 'service_credit',
                    'inputs': {
                        'current_salary': round(current_salary, 2),
                        'years_to_purchase': years_to_purchase,
                        'cost_percentage': cost_percentage
                    },
                    'purchase': {
                        'total_cost': round(purchase_cost, 2),
                        'additional_annual_benefit': round(additional_benefit, 2),
                        'additional_monthly_benefit': round(additional_benefit / 12, 2)
                    },
                    'analysis': {
                        'payback_years': round(payback_years, 1),
                        'total_benefit_20_years': round(total_additional, 2),
                        'roi_20_years': round(roi, 1),
                        'worth_it': payback_years < 10
                    },
                    'chart_data': None
                }
            else:
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('Invalid request data.')}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)

    def _prepare_defined_benefit_chart_data(self, labels, annual_benefits):
        """Build Chart.js-ready config for benefits over time (backend-controlled)."""
        if not labels or not annual_benefits:
            return None
        return {
            'benefits_chart': {
                'type': 'line',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': 'Annual Benefit',
                        'data': annual_benefits,
                        'borderColor': '#10b981',
                        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                        'fill': True,
                        'tension': 0.4
                    }]
                }
            }
        }

    def _prepare_lump_sum_chart_data(self, labels, end_balances):
        """Build Chart.js-ready config for lump sum balance over time (backend-controlled)."""
        if not labels or not end_balances:
            return None
        return {
            'balance_chart': {
                'type': 'line',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': 'Balance',
                        'data': end_balances,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'fill': True,
                        'tension': 0.4
                    }]
                }
            }
        }
