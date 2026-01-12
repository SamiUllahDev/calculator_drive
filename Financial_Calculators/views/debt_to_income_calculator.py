from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class DebtToIncomeCalculator(View):
    """
    Class-based view for Debt-to-Income (DTI) Ratio Calculator
    Calculates front-end and back-end DTI ratios for mortgage qualification.
    """
    template_name = 'financial_calculators/debt_to_income_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Debt-to-Income Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for DTI calculations"""
        try:
            data = json.loads(request.body)
            
            # Income
            gross_monthly_income = float(str(data.get('gross_monthly_income', 0)).replace(',', ''))
            other_income = float(str(data.get('other_income', 0)).replace(',', ''))
            
            # Housing costs (for front-end ratio)
            mortgage_payment = float(str(data.get('mortgage_payment', 0)).replace(',', ''))
            property_tax = float(str(data.get('property_tax', 0)).replace(',', ''))
            home_insurance = float(str(data.get('home_insurance', 0)).replace(',', ''))
            hoa_fees = float(str(data.get('hoa_fees', 0)).replace(',', ''))
            
            # Other debts (for back-end ratio)
            car_payment = float(str(data.get('car_payment', 0)).replace(',', ''))
            student_loans = float(str(data.get('student_loans', 0)).replace(',', ''))
            credit_cards = float(str(data.get('credit_cards', 0)).replace(',', ''))
            personal_loans = float(str(data.get('personal_loans', 0)).replace(',', ''))
            other_debts = float(str(data.get('other_debts', 0)).replace(',', ''))
            child_support = float(str(data.get('child_support', 0)).replace(',', ''))
            
            # Validation
            total_income = gross_monthly_income + other_income
            if total_income <= 0:
                return JsonResponse({'success': False, 'error': 'Total income must be greater than zero.'}, status=400)
            
            # Calculate housing costs (PITI)
            total_housing = mortgage_payment + property_tax + home_insurance + hoa_fees
            
            # Calculate total monthly debts
            total_other_debts = car_payment + student_loans + credit_cards + personal_loans + other_debts + child_support
            total_debts = total_housing + total_other_debts
            
            # Calculate DTI ratios
            front_end_ratio = (total_housing / total_income) * 100
            back_end_ratio = (total_debts / total_income) * 100
            
            # Determine qualification status
            def get_status(ratio, front=False):
                if front:
                    if ratio <= 28:
                        return {'status': 'excellent', 'message': 'Excellent - Well within lender guidelines'}
                    elif ratio <= 31:
                        return {'status': 'good', 'message': 'Good - Meets conventional loan requirements'}
                    elif ratio <= 36:
                        return {'status': 'fair', 'message': 'Fair - May qualify with compensating factors'}
                    else:
                        return {'status': 'poor', 'message': 'High - May have difficulty qualifying'}
                else:
                    if ratio <= 36:
                        return {'status': 'excellent', 'message': 'Excellent - Strong qualification position'}
                    elif ratio <= 43:
                        return {'status': 'good', 'message': 'Good - Meets qualified mortgage (QM) standards'}
                    elif ratio <= 50:
                        return {'status': 'fair', 'message': 'Fair - May qualify for FHA or VA loans'}
                    else:
                        return {'status': 'poor', 'message': 'High - Significant barrier to mortgage approval'}
            
            front_end_status = get_status(front_end_ratio, front=True)
            back_end_status = get_status(back_end_ratio, front=False)
            
            # Calculate maximum affordable housing payment based on income
            max_housing_28 = total_income * 0.28  # Conservative
            max_housing_31 = total_income * 0.31  # Conventional
            max_housing_36 = total_income * 0.36  # FHA
            
            # Calculate maximum total debt based on income
            max_debt_36 = total_income * 0.36  # Conservative
            max_debt_43 = total_income * 0.43  # QM limit
            max_debt_50 = total_income * 0.50  # FHA limit
            
            # Room for additional debt
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
                    'conventional': {
                        'front_end': '28% or less',
                        'back_end': '36% or less'
                    },
                    'fha': {
                        'front_end': '31% or less',
                        'back_end': '43% or less (up to 50% with compensating factors)'
                    },
                    'va': {
                        'front_end': 'No limit',
                        'back_end': '41% or less (flexible)'
                    }
                }
            }
            
            # Recommendations
            recommendations = []
            if back_end_ratio > 43:
                recommendations.append(f'Your DTI of {back_end_ratio:.1f}% exceeds the QM limit of 43%. Consider paying down ${total_debts - max_debt_43:,.0f} in monthly debts.')
            if front_end_ratio > 28:
                recommendations.append(f'Your housing ratio of {front_end_ratio:.1f}% is above the ideal 28%. Consider a less expensive home or increasing your income.')
            if back_end_ratio <= 36:
                recommendations.append('Your DTI is excellent for conventional mortgage qualification.')
            if credit_cards > 0:
                cc_impact = credit_cards / total_income * 100
                if cc_impact > 5:
                    recommendations.append(f'Credit card payments represent {cc_impact:.1f}% of your income. Paying these off could significantly improve your DTI.')
            
            result['recommendations'] = recommendations
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
