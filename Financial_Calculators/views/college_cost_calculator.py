from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class CollegeCostCalculator(View):
    """
    Class-based view for College Cost Calculator
    Projects future college costs and calculates savings needed.
    """
    template_name = 'financial_calculators/college_cost_calculator.html'

    # Average college costs (2024)
    COLLEGE_COSTS = {
        'public_in_state': {
            'tuition': 10940,
            'room_board': 12310,
            'books': 1240,
            'other': 2350
        },
        'public_out_state': {
            'tuition': 23630,
            'room_board': 12310,
            'books': 1240,
            'other': 2350
        },
        'private': {
            'tuition': 39400,
            'room_board': 14650,
            'books': 1240,
            'other': 2860
        },
        'community': {
            'tuition': 3900,
            'room_board': 9500,
            'books': 1460,
            'other': 2000
        }
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'College Cost Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for college cost calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'project_cost')

            if calc_type == 'project_cost':
                # Project future college costs
                child_age = int(data.get('child_age', 10))
                college_type = data.get('college_type', 'public_in_state')
                years_in_college = int(data.get('years_in_college', 4))
                inflation_rate = float(str(data.get('inflation_rate', 5)).replace(',', ''))
                
                # Custom costs override (optional)
                custom_annual_cost = data.get('custom_annual_cost')

                if child_age < 0 or child_age > 18:
                    return JsonResponse({'success': False, 'error': 'Child age must be between 0 and 18.'}, status=400)

                years_until_college = max(0, 18 - child_age)

                # Get base costs
                if custom_annual_cost:
                    current_annual_cost = float(str(custom_annual_cost).replace(',', ''))
                    cost_breakdown = {
                        'tuition': current_annual_cost * 0.55,
                        'room_board': current_annual_cost * 0.30,
                        'books': current_annual_cost * 0.05,
                        'other': current_annual_cost * 0.10
                    }
                else:
                    base_costs = self.COLLEGE_COSTS.get(college_type, self.COLLEGE_COSTS['public_in_state'])
                    current_annual_cost = sum(base_costs.values())
                    cost_breakdown = base_costs.copy()

                # Project costs for each year of college
                yearly_costs = []
                total_projected_cost = 0
                
                for year in range(years_in_college):
                    years_from_now = years_until_college + year
                    projected_cost = current_annual_cost * np.power(1 + inflation_rate/100, years_from_now)
                    total_projected_cost += projected_cost
                    
                    yearly_costs.append({
                        'college_year': year + 1,
                        'calendar_year': 2024 + years_from_now,
                        'child_age': child_age + years_from_now,
                        'projected_cost': round(projected_cost, 2)
                    })

                # Project cost breakdown at start of college
                projected_breakdown = {
                    k: round(v * np.power(1 + inflation_rate/100, years_until_college), 2) 
                    for k, v in cost_breakdown.items()
                }

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input': {
                        'child_age': child_age,
                        'years_until_college': years_until_college,
                        'college_type': college_type.replace('_', ' ').title(),
                        'years_in_college': years_in_college,
                        'inflation_rate': inflation_rate
                    },
                    'current_costs': {
                        'annual': round(current_annual_cost, 2),
                        'breakdown': {k: round(v, 2) for k, v in cost_breakdown.items()}
                    },
                    'projected_costs': {
                        'first_year': round(yearly_costs[0]['projected_cost'], 2) if yearly_costs else 0,
                        'total_4_year': round(total_projected_cost, 2),
                        'breakdown_at_start': projected_breakdown
                    },
                    'yearly_costs': yearly_costs
                }

            elif calc_type == 'savings_needed':
                # Calculate savings needed to cover costs
                target_amount = float(str(data.get('target_amount', 0)).replace(',', ''))
                current_savings = float(str(data.get('current_savings', 0)).replace(',', ''))
                years_to_save = int(data.get('years_to_save', 10))
                expected_return = float(str(data.get('expected_return', 6)).replace(',', ''))
                
                # Percentage of costs to cover
                coverage_percent = float(str(data.get('coverage_percent', 100)).replace(',', ''))

                if target_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Target amount must be greater than zero.'}, status=400)
                if years_to_save <= 0:
                    return JsonResponse({'success': False, 'error': 'Years to save must be greater than zero.'}, status=400)

                # Adjusted target based on coverage percentage
                adjusted_target = target_amount * (coverage_percent / 100)
                amount_needed = adjusted_target - current_savings

                # Future value of current savings
                monthly_rate = expected_return / 100 / 12
                months = years_to_save * 12
                
                fv_current_savings = current_savings * np.power(1 + monthly_rate, months)

                # Remaining amount needed after current savings grow
                remaining_needed = max(0, adjusted_target - fv_current_savings)

                # Monthly savings needed (PMT formula)
                if monthly_rate > 0 and remaining_needed > 0:
                    monthly_savings = remaining_needed * monthly_rate / (np.power(1 + monthly_rate, months) - 1)
                else:
                    monthly_savings = remaining_needed / months if months > 0 else 0

                annual_savings = monthly_savings * 12

                # Generate savings projection
                projection = []
                balance = current_savings
                total_contributions = 0
                
                for year in range(1, years_to_save + 1):
                    yearly_contribution = annual_savings
                    yearly_growth = balance * (expected_return / 100)
                    balance = balance + yearly_growth + yearly_contribution
                    total_contributions += yearly_contribution
                    
                    projection.append({
                        'year': year,
                        'contribution': round(yearly_contribution, 2),
                        'growth': round(yearly_growth, 2),
                        'balance': round(balance, 2),
                        'total_contributions': round(total_contributions + current_savings, 2)
                    })

                # Alternative scenarios
                scenarios = []
                for coverage in [50, 75, 100]:
                    adj_target = target_amount * (coverage / 100)
                    remaining = max(0, adj_target - fv_current_savings)
                    if monthly_rate > 0 and remaining > 0:
                        monthly = remaining * monthly_rate / (np.power(1 + monthly_rate, months) - 1)
                    else:
                        monthly = remaining / months if months > 0 else 0
                    
                    scenarios.append({
                        'coverage': coverage,
                        'target': round(adj_target, 2),
                        'monthly_savings': round(monthly, 2),
                        'annual_savings': round(monthly * 12, 2)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input': {
                        'target_amount': round(target_amount, 2),
                        'current_savings': round(current_savings, 2),
                        'years_to_save': years_to_save,
                        'expected_return': expected_return,
                        'coverage_percent': coverage_percent
                    },
                    'adjusted_target': round(adjusted_target, 2),
                    'fv_current_savings': round(fv_current_savings, 2),
                    'amount_still_needed': round(remaining_needed, 2),
                    'monthly_savings_needed': round(monthly_savings, 2),
                    'annual_savings_needed': round(annual_savings, 2),
                    'total_contributions': round(monthly_savings * months + current_savings, 2),
                    'total_growth': round(adjusted_target - (monthly_savings * months + current_savings), 2),
                    'projection': projection,
                    'scenarios': scenarios
                }

            elif calc_type == 'compare_529':
                # Compare 529 savings plan scenarios
                monthly_contribution = float(str(data.get('monthly_contribution', 0)).replace(',', ''))
                years = int(data.get('years', 18))
                initial_deposit = float(str(data.get('initial_deposit', 0)).replace(',', ''))
                state_tax_rate = float(str(data.get('state_tax_rate', 0)).replace(',', ''))

                if monthly_contribution < 0:
                    return JsonResponse({'success': False, 'error': 'Monthly contribution cannot be negative.'}, status=400)

                # Different return scenarios
                scenarios = [
                    {'name': 'Conservative', 'return': 4},
                    {'name': 'Moderate', 'return': 6},
                    {'name': 'Aggressive', 'return': 8},
                ]

                comparisons = []
                for scenario in scenarios:
                    monthly_rate = scenario['return'] / 100 / 12
                    months = years * 12
                    
                    # FV of initial deposit
                    fv_initial = initial_deposit * np.power(1 + monthly_rate, months)
                    
                    # FV of monthly contributions
                    if monthly_rate > 0:
                        fv_contributions = monthly_contribution * ((np.power(1 + monthly_rate, months) - 1) / monthly_rate)
                    else:
                        fv_contributions = monthly_contribution * months
                    
                    total_value = fv_initial + fv_contributions
                    total_contributions = initial_deposit + (monthly_contribution * months)
                    total_earnings = total_value - total_contributions
                    
                    # State tax deduction benefit (if applicable)
                    annual_contribution = monthly_contribution * 12
                    annual_tax_benefit = annual_contribution * (state_tax_rate / 100)
                    total_tax_benefit = annual_tax_benefit * years
                    
                    comparisons.append({
                        'scenario': scenario['name'],
                        'return_rate': scenario['return'],
                        'total_value': round(total_value, 2),
                        'total_contributions': round(total_contributions, 2),
                        'total_earnings': round(total_earnings, 2),
                        'annual_tax_benefit': round(annual_tax_benefit, 2),
                        'total_tax_benefit': round(total_tax_benefit, 2),
                        'effective_value': round(total_value + total_tax_benefit, 2)
                    })

                # 529 Benefits
                benefits = [
                    "Tax-free growth",
                    "Tax-free withdrawals for qualified education expenses",
                    "State tax deduction (varies by state)",
                    "High contribution limits",
                    "Flexible beneficiary changes",
                    "Can be used for K-12 tuition (up to $10,000/year)",
                    "No income limits"
                ]

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input': {
                        'monthly_contribution': round(monthly_contribution, 2),
                        'initial_deposit': round(initial_deposit, 2),
                        'years': years,
                        'state_tax_rate': state_tax_rate
                    },
                    'comparisons': comparisons,
                    'benefits': benefits
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
