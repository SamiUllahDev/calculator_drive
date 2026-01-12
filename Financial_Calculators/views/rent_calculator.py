from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class RentCalculator(View):
    """
    Class-based view for Rent Affordability Calculator
    Calculates how much rent you can afford based on income.
    """
    template_name = 'financial_calculators/rent_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rent Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for rent calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'affordability')

            if calc_type == 'affordability':
                # Calculate affordable rent based on income
                gross_income = float(str(data.get('gross_income', 0)).replace(',', ''))
                income_period = data.get('income_period', 'annual')  # annual, monthly
                
                # Other monthly expenses
                car_payment = float(str(data.get('car_payment', 0)).replace(',', ''))
                student_loans = float(str(data.get('student_loans', 0)).replace(',', ''))
                credit_card_payments = float(str(data.get('credit_card_payments', 0)).replace(',', ''))
                other_debt = float(str(data.get('other_debt', 0)).replace(',', ''))
                utilities = float(str(data.get('utilities', 0)).replace(',', ''))
                
                # Preferred rent percentage (default 30%)
                preferred_rent_percent = float(str(data.get('rent_percent', 30)).replace(',', ''))

                if gross_income <= 0:
                    return JsonResponse({'success': False, 'error': 'Gross income must be greater than zero.'}, status=400)

                # Convert to monthly income
                if income_period == 'annual':
                    monthly_income = gross_income / 12
                    annual_income = gross_income
                else:
                    monthly_income = gross_income
                    annual_income = gross_income * 12

                # Estimated taxes and take-home (simplified)
                estimated_tax_rate = 22  # Rough estimate
                net_monthly_income = monthly_income * (1 - estimated_tax_rate / 100)

                # Total monthly debt payments
                total_monthly_debt = car_payment + student_loans + credit_card_payments + other_debt

                # Rent affordability calculations
                # 30% Rule
                rent_30_percent = monthly_income * 0.30
                
                # 28/36 Rule (28% for housing, 36% total debt)
                rent_28_percent = monthly_income * 0.28
                max_total_debt_36 = monthly_income * 0.36
                available_for_rent_36 = max_total_debt_36 - total_monthly_debt
                
                # 50/30/20 Rule (50% needs, 30% wants, 20% savings)
                # Rent should be part of 50% needs
                needs_budget = net_monthly_income * 0.50
                rent_50_30_20 = needs_budget - utilities  # Subtract utilities from needs

                # Custom percentage
                rent_custom = monthly_income * (preferred_rent_percent / 100)

                # Conservative and aggressive estimates
                rent_conservative = monthly_income * 0.25
                rent_aggressive = monthly_income * 0.35

                # After rent budget analysis (at recommended 30% level)
                recommended_rent = rent_30_percent
                after_rent = net_monthly_income - recommended_rent - total_monthly_debt - utilities
                
                budget_breakdown = {
                    'rent': round(recommended_rent, 2),
                    'utilities': round(utilities, 2),
                    'debt_payments': round(total_monthly_debt, 2),
                    'estimated_taxes': round(monthly_income * (estimated_tax_rate / 100), 2),
                    'remaining': round(after_rent, 2)
                }

                # Rent ranges by percentage
                rent_ranges = [
                    {'percent': 25, 'monthly': round(monthly_income * 0.25, 2), 'label': 'Conservative'},
                    {'percent': 28, 'monthly': round(monthly_income * 0.28, 2), 'label': '28% Rule'},
                    {'percent': 30, 'monthly': round(monthly_income * 0.30, 2), 'label': 'Standard (30%)'},
                    {'percent': 33, 'monthly': round(monthly_income * 0.33, 2), 'label': 'Moderate'},
                    {'percent': 35, 'monthly': round(monthly_income * 0.35, 2), 'label': 'Maximum'},
                ]

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'income': {
                        'gross_annual': round(annual_income, 2),
                        'gross_monthly': round(monthly_income, 2),
                        'net_monthly_estimate': round(net_monthly_income, 2),
                        'estimated_tax_rate': estimated_tax_rate
                    },
                    'monthly_obligations': {
                        'car_payment': round(car_payment, 2),
                        'student_loans': round(student_loans, 2),
                        'credit_cards': round(credit_card_payments, 2),
                        'other_debt': round(other_debt, 2),
                        'utilities': round(utilities, 2),
                        'total_debt': round(total_monthly_debt, 2)
                    },
                    'affordability': {
                        'rent_30_rule': round(rent_30_percent, 2),
                        'rent_28_rule': round(rent_28_percent, 2),
                        'rent_36_rule_available': round(max(0, available_for_rent_36), 2),
                        'rent_50_30_20': round(max(0, rent_50_30_20), 2),
                        'rent_custom': round(rent_custom, 2),
                        'custom_percent': preferred_rent_percent,
                        'rent_conservative': round(rent_conservative, 2),
                        'rent_aggressive': round(rent_aggressive, 2)
                    },
                    'recommended': {
                        'monthly_rent': round(rent_30_percent, 2),
                        'including_utilities': round(rent_30_percent + utilities, 2),
                        'annual_rent': round(rent_30_percent * 12, 2)
                    },
                    'budget_breakdown': budget_breakdown,
                    'rent_ranges': rent_ranges,
                    'required_annual_income_for_rent': {
                        '1000': round(1000 * 12 / 0.30, 2),
                        '1500': round(1500 * 12 / 0.30, 2),
                        '2000': round(2000 * 12 / 0.30, 2),
                        '2500': round(2500 * 12 / 0.30, 2),
                        '3000': round(3000 * 12 / 0.30, 2),
                    }
                }

            elif calc_type == 'split_rent':
                # Calculate rent split between roommates
                total_rent = float(str(data.get('total_rent', 0)).replace(',', ''))
                num_roommates = int(data.get('num_roommates', 2))
                split_method = data.get('split_method', 'equal')  # equal, by_room, by_income
                
                # Room sizes (for by_room split)
                room_sizes = data.get('room_sizes', [])
                
                # Incomes (for by_income split)
                incomes = data.get('incomes', [])
                
                # Utilities
                total_utilities = float(str(data.get('total_utilities', 0)).replace(',', ''))

                if total_rent <= 0:
                    return JsonResponse({'success': False, 'error': 'Total rent must be greater than zero.'}, status=400)
                if num_roommates < 1:
                    return JsonResponse({'success': False, 'error': 'Must have at least 1 person.'}, status=400)

                splits = []
                
                if split_method == 'equal':
                    per_person_rent = total_rent / num_roommates
                    per_person_utilities = total_utilities / num_roommates
                    
                    for i in range(num_roommates):
                        splits.append({
                            'person': f'Person {i+1}',
                            'rent': round(per_person_rent, 2),
                            'utilities': round(per_person_utilities, 2),
                            'total': round(per_person_rent + per_person_utilities, 2),
                            'percent_of_total': round(100 / num_roommates, 1)
                        })

                elif split_method == 'by_room':
                    if not room_sizes or len(room_sizes) != num_roommates:
                        # Default to equal if room sizes not provided
                        room_sizes = [100] * num_roommates
                    
                    try:
                        sizes = [float(str(s).replace(',', '')) for s in room_sizes]
                    except:
                        sizes = [100] * num_roommates
                    
                    total_size = sum(sizes)
                    
                    for i in range(num_roommates):
                        size_percent = sizes[i] / total_size if total_size > 0 else 1 / num_roommates
                        person_rent = total_rent * size_percent
                        person_utilities = total_utilities / num_roommates  # Utilities split equally
                        
                        splits.append({
                            'person': f'Person {i+1}',
                            'room_size': sizes[i],
                            'rent': round(person_rent, 2),
                            'utilities': round(person_utilities, 2),
                            'total': round(person_rent + person_utilities, 2),
                            'percent_of_total': round(size_percent * 100, 1)
                        })

                elif split_method == 'by_income':
                    if not incomes or len(incomes) != num_roommates:
                        # Default to equal if incomes not provided
                        incomes = [50000] * num_roommates
                    
                    try:
                        income_values = [float(str(i).replace(',', '')) for i in incomes]
                    except:
                        income_values = [50000] * num_roommates
                    
                    total_income = sum(income_values)
                    
                    for i in range(num_roommates):
                        income_percent = income_values[i] / total_income if total_income > 0 else 1 / num_roommates
                        person_rent = total_rent * income_percent
                        person_utilities = total_utilities * income_percent
                        
                        splits.append({
                            'person': f'Person {i+1}',
                            'income': income_values[i],
                            'rent': round(person_rent, 2),
                            'utilities': round(person_utilities, 2),
                            'total': round(person_rent + person_utilities, 2),
                            'percent_of_total': round(income_percent * 100, 1)
                        })

                total_monthly = total_rent + total_utilities

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'total_rent': round(total_rent, 2),
                    'total_utilities': round(total_utilities, 2),
                    'total_monthly': round(total_monthly, 2),
                    'num_roommates': num_roommates,
                    'split_method': split_method,
                    'splits': splits
                }

            elif calc_type == 'rent_increase':
                # Analyze rent increase
                current_rent = float(str(data.get('current_rent', 0)).replace(',', ''))
                new_rent = float(str(data.get('new_rent', 0)).replace(',', ''))
                monthly_income = float(str(data.get('monthly_income', 0)).replace(',', ''))

                if current_rent <= 0:
                    return JsonResponse({'success': False, 'error': 'Current rent must be greater than zero.'}, status=400)

                increase_amount = new_rent - current_rent
                increase_percent = (increase_amount / current_rent * 100) if current_rent > 0 else 0
                annual_increase = increase_amount * 12

                # Impact analysis
                current_percent_income = (current_rent / monthly_income * 100) if monthly_income > 0 else 0
                new_percent_income = (new_rent / monthly_income * 100) if monthly_income > 0 else 0

                affordable = new_percent_income <= 30

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'current_rent': round(current_rent, 2),
                    'new_rent': round(new_rent, 2),
                    'increase_amount': round(increase_amount, 2),
                    'increase_percent': round(increase_percent, 1),
                    'annual_increase': round(annual_increase, 2),
                    'current_percent_of_income': round(current_percent_income, 1),
                    'new_percent_of_income': round(new_percent_income, 1),
                    'affordable': affordable,
                    'recommendation': 'Rent remains affordable (under 30% of income)' if affordable else 'Consider negotiating or finding alternatives (over 30% of income)'
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
