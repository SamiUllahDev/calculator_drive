from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DebtToIncomeCalculator(View):
    """
    Class-based view for Debt-to-Income (DTI) Ratio Calculator
    Calculates front-end and back-end DTI ratios for mortgage qualification.
    """
    template_name = 'financial_calculators/debt_to_income_calculator.html'

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float from data."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Debt-to-Income Calculator'),
            'page_title': _('Debt-to-Income (DTI) Calculator - Check Mortgage Qualification'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for DTI calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            gross_monthly_income = self._get_float(data, 'gross_monthly_income', 0)
            other_income = self._get_float(data, 'other_income', 0)
            mortgage_payment = self._get_float(data, 'mortgage_payment', 0)
            property_tax = self._get_float(data, 'property_tax', 0)
            home_insurance = self._get_float(data, 'home_insurance', 0)
            hoa_fees = self._get_float(data, 'hoa_fees', 0)
            car_payment = self._get_float(data, 'car_payment', 0)
            student_loans = self._get_float(data, 'student_loans', 0)
            credit_cards = self._get_float(data, 'credit_cards', 0)
            personal_loans = self._get_float(data, 'personal_loans', 0)
            other_debts = self._get_float(data, 'other_debts', 0)
            child_support = self._get_float(data, 'child_support', 0)

            total_income = gross_monthly_income + other_income
            if total_income <= 0:
                return JsonResponse({'success': False, 'error': _('Total income must be greater than zero.')}, status=400)

            total_housing = mortgage_payment + property_tax + home_insurance + hoa_fees
            total_other_debts = car_payment + student_loans + credit_cards + personal_loans + other_debts + child_support
            total_debts = total_housing + total_other_debts

            front_end_ratio = (total_housing / total_income) * 100
            back_end_ratio = (total_debts / total_income) * 100

            def get_status(ratio, front=False):
                if front:
                    if ratio <= 28:
                        return {'status': 'excellent', 'message': _('Excellent - Well within lender guidelines')}
                    elif ratio <= 31:
                        return {'status': 'good', 'message': _('Good - Meets conventional loan requirements')}
                    elif ratio <= 36:
                        return {'status': 'fair', 'message': _('Fair - May qualify with compensating factors')}
                    else:
                        return {'status': 'poor', 'message': _('High - May have difficulty qualifying')}
                else:
                    if ratio <= 36:
                        return {'status': 'excellent', 'message': _('Excellent - Strong qualification position')}
                    elif ratio <= 43:
                        return {'status': 'good', 'message': _('Good - Meets qualified mortgage (QM) standards')}
                    elif ratio <= 50:
                        return {'status': 'fair', 'message': _('Fair - May qualify for FHA or VA loans')}
                    else:
                        return {'status': 'poor', 'message': _('High - Significant barrier to mortgage approval')}

            front_end_status = get_status(front_end_ratio, front=True)
            back_end_status = get_status(back_end_ratio, front=False)

            max_housing_28 = total_income * 0.28
            max_housing_31 = total_income * 0.31
            max_housing_36 = total_income * 0.36
            max_debt_36 = total_income * 0.36
            max_debt_43 = total_income * 0.43
            max_debt_50 = total_income * 0.50
            room_to_43 = max(0, max_debt_43 - total_debts)
            room_to_36 = max(0, max_debt_36 - total_debts)

            result = {
                'success': True,
                'income': {
                    'gross_monthly': round(gross_monthly_income, 2),
                    'other': round(other_income, 2),
                    'total': round(total_income, 2),
                    'annual': round(total_income * 12, 2)
                },
                'housing_costs': {
                    'mortgage': round(mortgage_payment, 2),
                    'property_tax': round(property_tax, 2),
                    'insurance': round(home_insurance, 2),
                    'hoa': round(hoa_fees, 2),
                    'total': round(total_housing, 2)
                },
                'other_debts': {
                    'car': round(car_payment, 2),
                    'student_loans': round(student_loans, 2),
                    'credit_cards': round(credit_cards, 2),
                    'personal_loans': round(personal_loans, 2),
                    'child_support': round(child_support, 2),
                    'other': round(other_debts, 2),
                    'total': round(total_other_debts, 2)
                },
                'dti_ratios': {
                    'front_end': round(front_end_ratio, 2),
                    'back_end': round(back_end_ratio, 2),
                    'front_end_status': front_end_status,
                    'back_end_status': back_end_status
                },
                'total_debts': round(total_debts, 2),
                'affordability': {
                    'max_housing_28': round(max_housing_28, 2),
                    'max_housing_31': round(max_housing_31, 2),
                    'max_housing_36': round(max_housing_36, 2),
                    'max_debt_36': round(max_debt_36, 2),
                    'max_debt_43': round(max_debt_43, 2),
                    'max_debt_50': round(max_debt_50, 2),
                    'room_to_36': round(room_to_36, 2),
                    'room_to_43': round(room_to_43, 2)
                },
                'guidelines': {
                    'conventional': {'front_end': _('28% or less'), 'back_end': _('36% or less')},
                    'fha': {'front_end': _('31% or less'), 'back_end': _('43% or less (up to 50%% with compensating factors)')},
                    'va': {'front_end': _('No limit'), 'back_end': _('41% or less (flexible)')}
                }
            }

            recommendations = []
            if back_end_ratio > 43:
                recommendations.append(_('Your DTI of %(ratio)s%% exceeds the QM limit of 43%%. Consider paying down debt to improve qualification.') % {'ratio': f'{back_end_ratio:.1f}'})
            if front_end_ratio > 28:
                recommendations.append(_('Your housing ratio of %(ratio)s%% is above the ideal 28%%. Consider a less expensive home or increasing your income.') % {'ratio': f'{front_end_ratio:.1f}'})
            if back_end_ratio <= 36:
                recommendations.append(_('Your DTI is excellent for conventional mortgage qualification.'))
            if credit_cards > 0:
                cc_impact = credit_cards / total_income * 100
                if cc_impact > 5:
                    recommendations.append(_('Credit card payments represent %(pct)s%% of your income. Paying these off could significantly improve your DTI.') % {'pct': f'{cc_impact:.1f}'})

            result['recommendations'] = recommendations

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
