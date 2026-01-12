from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class PensionCalculator(View):
    """
    Class-based view for Pension Calculator
    Calculates pension benefits for defined benefit plans.
    """
    template_name = 'financial_calculators/pension_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Pension Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for pension calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'defined_benefit')
            
            if calc_type == 'defined_benefit':
                # Defined Benefit Pension calculation
                final_salary = float(str(data.get('final_salary', 0)).replace(',', ''))
                years_of_service = int(data.get('years_of_service', 20))
                benefit_multiplier = float(str(data.get('benefit_multiplier', 2)).replace(',', ''))  # % per year
                retirement_age = int(data.get('retirement_age', 65))
                current_age = int(data.get('current_age', 55))
                cola_rate = float(str(data.get('cola_rate', 2)).replace(',', ''))  # Annual COLA
                
                # Validation
                if final_salary <= 0:
                    return JsonResponse({'success': False, 'error': 'Final salary must be greater than zero.'}, status=400)
                if years_of_service <= 0 or years_of_service > 50:
                    return JsonResponse({'success': False, 'error': 'Years of service must be between 1 and 50.'}, status=400)
                if retirement_age <= current_age:
                    return JsonResponse({'success': False, 'error': 'Retirement age must be greater than current age.'}, status=400)
                
                # Calculate pension benefit
                # Formula: Final Salary × Years of Service × Benefit Multiplier
                annual_pension = final_salary * years_of_service * (benefit_multiplier / 100)
                monthly_pension = annual_pension / 12
                
                # Calculate replacement ratio
                replacement_ratio = (annual_pension / final_salary) * 100
                
                # Project pension with COLA over retirement years
                years_in_retirement = 30  # Assume 30 years in retirement
                yearly_benefits = []
                cumulative = 0
                
                for year in range(years_in_retirement):
                    age = retirement_age + year
                    adjusted_annual = annual_pension * np.power(1 + cola_rate/100, year)
                    cumulative += adjusted_annual
                    yearly_benefits.append({
                        'year': year + 1,
                        'age': age,
                        'annual_benefit': round(adjusted_annual, 2),
                        'monthly_benefit': round(adjusted_annual / 12, 2),
                        'cumulative': round(cumulative, 2)
                    })
                
                # Calculate present value of pension (at 4% discount rate)
                discount_rate = 0.04
                present_value = sum([
                    annual_pension * np.power(1 + cola_rate/100, year) / np.power(1 + discount_rate, year)
                    for year in range(years_in_retirement)
                ])
                
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
                        'yearly_breakdown': yearly_benefits[:20]  # First 20 years
                    },
                    'formula': f'Annual Pension = ${final_salary:,.0f} × {years_of_service} years × {benefit_multiplier}% = ${annual_pension:,.0f}'
                }
                
            elif calc_type == 'lump_sum_vs_annuity':
                # Compare lump sum vs annuity option
                monthly_annuity = float(str(data.get('monthly_annuity', 0)).replace(',', ''))
                lump_sum_offer = float(str(data.get('lump_sum_offer', 0)).replace(',', ''))
                life_expectancy = int(data.get('life_expectancy', 85))
                retirement_age = int(data.get('retirement_age', 65))
                expected_return = float(str(data.get('expected_return', 5)).replace(',', ''))  # If invested
                
                if monthly_annuity <= 0 or lump_sum_offer <= 0:
                    return JsonResponse({'success': False, 'error': 'Both values must be greater than zero.'}, status=400)
                
                years_in_retirement = life_expectancy - retirement_age
                annual_annuity = monthly_annuity * 12
                
                # Total annuity payments
                total_annuity = annual_annuity * years_in_retirement
                
                # Lump sum invested and withdrawn
                balance = lump_sum_offer
                lump_sum_projection = []
                annual_withdrawal = annual_annuity  # Withdraw same as annuity
                monthly_return = expected_return / 100 / 12
                
                for year in range(years_in_retirement):
                    year_start = balance
                    for month in range(12):
                        balance = balance * (1 + monthly_return) - (annual_withdrawal / 12)
                    
                    lump_sum_projection.append({
                        'year': year + 1,
                        'age': retirement_age + year,
                        'start_balance': round(year_start, 2),
                        'end_balance': round(max(0, balance), 2)
                    })
                    
                    if balance <= 0:
                        break
                
                # Calculate breakeven
                # At what return rate does lump sum = annuity?
                # Simple breakeven: lump_sum * rate^n = total_annuity
                implied_rate = (total_annuity / lump_sum_offer) ** (1/years_in_retirement) - 1
                
                # Determine recommendation
                if balance > 0:
                    recommendation = 'lump_sum'
                    reason = f'Lump sum would have ${balance:,.0f} remaining after {years_in_retirement} years.'
                else:
                    years_lasted = len([p for p in lump_sum_projection if p['end_balance'] > 0])
                    recommendation = 'annuity'
                    reason = f'Lump sum would run out in {years_lasted} years. Annuity provides lifetime income.'
                
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
                    }
                }
                
            elif calc_type == 'service_credit':
                # Calculate cost of purchasing service credits
                current_salary = float(str(data.get('current_salary', 0)).replace(',', ''))
                years_to_purchase = float(str(data.get('years_to_purchase', 0)).replace(',', ''))
                cost_percentage = float(str(data.get('cost_percentage', 10)).replace(',', ''))  # % of salary per year
                benefit_multiplier = float(str(data.get('benefit_multiplier', 2)).replace(',', ''))
                years_until_retirement = int(data.get('years_until_retirement', 10))
                
                if current_salary <= 0 or years_to_purchase <= 0:
                    return JsonResponse({'success': False, 'error': 'Invalid input values.'}, status=400)
                
                # Cost to purchase
                purchase_cost = current_salary * years_to_purchase * (cost_percentage / 100)
                
                # Additional annual benefit
                additional_benefit = current_salary * years_to_purchase * (benefit_multiplier / 100)
                
                # Payback period
                payback_years = purchase_cost / additional_benefit if additional_benefit > 0 else 0
                
                # ROI over 20 years retirement
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
                    }
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
