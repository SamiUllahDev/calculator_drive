from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class K401Calculator(View):
    """
    Class-based view for 401(k) Retirement Calculator
    Calculates projected 401(k) balance at retirement with employer matching,
    catch-up contributions, and salary growth projections.
    """
    template_name = 'financial_calculators/401k_calculator.html'
    
    # 2024 IRS Contribution Limits
    CONTRIBUTION_LIMIT_2024 = 23000
    CATCH_UP_LIMIT_2024 = 7500  # For age 50+
    CATCH_UP_LIMIT_60_63 = 11250  # New higher limit for ages 60-63 (starting 2025)
    
    def get(self, request):
        """Handle GET request - render the calculator form"""
        context = {
            'calculator_name': '401(k) Calculator',
            'contribution_limit': self.CONTRIBUTION_LIMIT_2024,
            'catch_up_limit': self.CATCH_UP_LIMIT_2024,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Get input values
            current_age = self._get_int(data, 'current_age', 30)
            retirement_age = self._get_int(data, 'retirement_age', 65)
            current_salary = self._get_float(data, 'current_salary', 60000)
            salary_increase = self._get_float(data, 'salary_increase', 2.5) / 100
            current_balance = self._get_float(data, 'current_balance', 0)
            contribution_percent = self._get_float(data, 'contribution_percent', 6) / 100
            employer_match_percent = self._get_float(data, 'employer_match_percent', 50) / 100
            employer_match_limit = self._get_float(data, 'employer_match_limit', 6) / 100
            annual_return = self._get_float(data, 'annual_return', 7) / 100
            include_catch_up = data.get('include_catch_up', True)
            
            # Validate inputs
            errors = self._validate_inputs(
                current_age, retirement_age, current_salary,
                contribution_percent, annual_return
            )
            if errors:
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            # Calculate projections
            result = self._calculate_401k_projection(
                current_age=current_age,
                retirement_age=retirement_age,
                current_salary=current_salary,
                salary_increase=salary_increase,
                current_balance=current_balance,
                contribution_percent=contribution_percent,
                employer_match_percent=employer_match_percent,
                employer_match_limit=employer_match_limit,
                annual_return=annual_return,
                include_catch_up=include_catch_up
            )
            
            return JsonResponse({'success': True, **result})
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'errors': ['Invalid JSON data']
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            }, status=500)
    
    def _get_float(self, data, key, default=0.0):
        """Safely extract float value from data"""
        try:
            value = data.get(key, default)
            return float(value) if value not in [None, ''] else default
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely extract integer value from data"""
        try:
            value = data.get(key, default)
            return int(float(value)) if value not in [None, ''] else default
        except (ValueError, TypeError):
            return default
    
    def _validate_inputs(self, current_age, retirement_age, current_salary,
                         contribution_percent, annual_return):
        """Validate calculator inputs"""
        errors = []
        
        if current_age < 18 or current_age > 100:
            errors.append('Current age must be between 18 and 100')
        if retirement_age < current_age:
            errors.append('Retirement age must be greater than current age')
        if retirement_age > 100:
            errors.append('Retirement age must be 100 or less')
        if current_salary <= 0:
            errors.append('Salary must be greater than 0')
        if contribution_percent < 0 or contribution_percent > 1:
            errors.append('Contribution percentage must be between 0% and 100%')
        if annual_return < -0.5 or annual_return > 0.5:
            errors.append('Annual return must be between -50% and 50%')
        
        return errors
    
    def _calculate_401k_projection(self, current_age, retirement_age, current_salary,
                                   salary_increase, current_balance, contribution_percent,
                                   employer_match_percent, employer_match_limit,
                                   annual_return, include_catch_up):
        """Calculate 401(k) projections year by year"""
        
        years_to_retirement = retirement_age - current_age
        balance = current_balance
        salary = current_salary
        
        # Track totals
        total_employee_contributions = 0
        total_employer_contributions = 0
        total_investment_gains = 0
        
        # Year-by-year breakdown
        yearly_breakdown = []
        chart_data = {
            'labels': [],
            'employee_contributions': [],
            'employer_contributions': [],
            'investment_gains': [],
            'balances': []
        }
        
        for year in range(1, years_to_retirement + 1):
            age = current_age + year
            year_start_balance = balance
            
            # Calculate contribution limit with catch-up
            contribution_limit = self.CONTRIBUTION_LIMIT_2024
            if include_catch_up and age >= 50:
                if age >= 60 and age <= 63:
                    contribution_limit += self.CATCH_UP_LIMIT_60_63
                else:
                    contribution_limit += self.CATCH_UP_LIMIT_2024
            
            # Calculate employee contribution (capped at IRS limit)
            employee_contribution = min(
                salary * contribution_percent,
                contribution_limit
            )
            
            # Calculate employer match
            # Employer matches X% of employee contribution up to Y% of salary
            matchable_contribution = min(
                employee_contribution,
                salary * employer_match_limit
            )
            employer_contribution = matchable_contribution * employer_match_percent
            
            # Add contributions to balance
            balance += employee_contribution + employer_contribution
            
            # Calculate investment gains (on average balance during year)
            mid_year_balance = year_start_balance + (employee_contribution + employer_contribution) / 2
            investment_gain = mid_year_balance * annual_return
            balance += investment_gain
            
            # Update totals
            total_employee_contributions += employee_contribution
            total_employer_contributions += employer_contribution
            total_investment_gains += investment_gain
            
            # Store yearly data
            yearly_breakdown.append({
                'year': year,
                'age': age,
                'salary': round(salary, 2),
                'employee_contribution': round(employee_contribution, 2),
                'employer_contribution': round(employer_contribution, 2),
                'investment_gain': round(investment_gain, 2),
                'year_end_balance': round(balance, 2)
            })
            
            # Chart data
            chart_data['labels'].append(f'Age {age}')
            chart_data['employee_contributions'].append(round(total_employee_contributions, 2))
            chart_data['employer_contributions'].append(round(total_employer_contributions, 2))
            chart_data['investment_gains'].append(round(total_investment_gains, 2))
            chart_data['balances'].append(round(balance, 2))
            
            # Increase salary for next year
            salary *= (1 + salary_increase)
        
        # Calculate effective match rate
        if total_employee_contributions > 0:
            effective_match_rate = (total_employer_contributions / total_employee_contributions) * 100
        else:
            effective_match_rate = 0
        
        # Calculate monthly retirement income (4% rule)
        monthly_income_4_percent = (balance * 0.04) / 12
        
        # Calculate what percentage of final salary this represents
        if salary > 0:
            income_replacement_rate = (monthly_income_4_percent * 12 / salary) * 100
        else:
            income_replacement_rate = 0
        
        return {
            'projected_balance': round(balance, 2),
            'total_employee_contributions': round(total_employee_contributions, 2),
            'total_employer_contributions': round(total_employer_contributions, 2),
            'total_contributions': round(total_employee_contributions + total_employer_contributions, 2),
            'total_investment_gains': round(total_investment_gains, 2),
            'effective_match_rate': round(effective_match_rate, 2),
            'years_to_retirement': years_to_retirement,
            'monthly_income_4_percent': round(monthly_income_4_percent, 2),
            'income_replacement_rate': round(income_replacement_rate, 2),
            'final_salary': round(salary, 2),
            'chart_data': chart_data,
            'yearly_breakdown': yearly_breakdown[:10] + yearly_breakdown[-5:] if len(yearly_breakdown) > 15 else yearly_breakdown,
            'full_breakdown_available': len(yearly_breakdown) > 15
        }
