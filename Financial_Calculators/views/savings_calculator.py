from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from datetime import datetime

try:
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


def add_months(source_date, months):
    """Add months to a date"""
    if HAS_DATEUTIL:
        return source_date + relativedelta(months=months)
    else:
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return datetime(year, month, day)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SavingsCalculator(View):
    """
    Professional Savings Calculator with comprehensive features.
    
    Features:
    - Savings goal tracking
    - Regular deposit calculations
    - Interest earnings projection
    - Growth visualization
    - Multiple scenarios
    """
    template_name = 'financial_calculators/savings_calculator.html'
    
    # Validation limits
    MIN_AMOUNT = 0
    MAX_AMOUNT = 1000000000
    MIN_RATE = 0
    MAX_RATE = 50
    MIN_YEARS = 1
    MAX_YEARS = 50
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Savings Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get calculation mode
            calc_mode = data.get('calc_mode', 'future_value')  # future_value, monthly_deposit, or time_to_goal
            
            # Get inputs
            initial_savings = self._get_float(data, 'initial_savings', 0)
            monthly_deposit = self._get_float(data, 'monthly_deposit', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            years = self._get_float(data, 'years', 0)
            savings_goal = self._get_float(data, 'savings_goal', 0)
            compound_frequency = data.get('compound_frequency', 'monthly')
            
            # Validation
            errors = []
            
            if initial_savings < self.MIN_AMOUNT:
                errors.append('Initial savings cannot be negative.')
            elif initial_savings > self.MAX_AMOUNT:
                errors.append(f'Initial savings cannot exceed ${self.MAX_AMOUNT:,}.')
            
            if monthly_deposit < self.MIN_AMOUNT:
                errors.append('Monthly deposit cannot be negative.')
            elif monthly_deposit > self.MAX_AMOUNT / 12:
                errors.append('Monthly deposit is too large.')
            
            if interest_rate < self.MIN_RATE:
                errors.append('Interest rate cannot be negative.')
            elif interest_rate > self.MAX_RATE:
                errors.append(f'Interest rate cannot exceed {self.MAX_RATE}%.')
            
            if calc_mode != 'time_to_goal':
                if years < self.MIN_YEARS:
                    errors.append(f'Time period must be at least {self.MIN_YEARS} year.')
                elif years > self.MAX_YEARS:
                    errors.append(f'Time period cannot exceed {self.MAX_YEARS} years.')
            
            if calc_mode == 'time_to_goal' or savings_goal > 0:
                if savings_goal <= 0:
                    errors.append('Please enter a valid savings goal.')
                elif savings_goal > self.MAX_AMOUNT:
                    errors.append(f'Savings goal cannot exceed ${self.MAX_AMOUNT:,}.')
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Get compound frequency
            compound_map = {
                'annually': 1,
                'semiannually': 2,
                'quarterly': 4,
                'monthly': 12,
                'daily': 365,
            }
            n = compound_map.get(compound_frequency, 12)
            r = interest_rate / 100
            
            # Perform calculations based on mode
            if calc_mode == 'future_value':
                result = self._calculate_future_value(
                    initial_savings, monthly_deposit, r, n, years
                )
            elif calc_mode == 'monthly_deposit':
                result = self._calculate_required_deposit(
                    initial_savings, savings_goal, r, n, years
                )
            elif calc_mode == 'time_to_goal':
                result = self._calculate_time_to_goal(
                    initial_savings, monthly_deposit, savings_goal, r, n
                )
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation mode.'}, status=400)
            
            # Check for goal achievement
            if savings_goal > 0 and result.get('final_balance', 0) >= savings_goal:
                result['goal_achieved'] = True
                result['goal_surplus'] = round(result['final_balance'] - savings_goal, 2)
            else:
                result['goal_achieved'] = False
            
            return JsonResponse({
                'success': True,
                **result
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Calculation error. Please check your inputs and try again.'
            }, status=400)
    
    def _get_float(self, data, key, default=0):
        """Safely get float value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            return float(str(value).replace(',', '').replace('$', ''))
        except (ValueError, TypeError):
            return default
    
    def _calculate_future_value(self, initial, monthly, rate, n, years):
        """Calculate future value of savings"""
        months = int(years * 12)
        monthly_rate = rate / 12
        
        balance = initial
        total_deposits = initial
        total_interest = 0
        
        yearly_breakdown = []
        chart_labels = ['Start']
        chart_balance = [initial]
        chart_deposits = [initial]
        
        current_year = datetime.now().year
        year_start_balance = initial
        year_deposits = 0
        year_interest = 0
        
        for month in range(1, months + 1):
            # Add monthly deposit
            balance += monthly
            total_deposits += monthly
            year_deposits += monthly
            
            # Calculate interest
            interest = balance * monthly_rate
            balance += interest
            total_interest += interest
            year_interest += interest
            
            # Year end summary
            if month % 12 == 0:
                year_num = month // 12
                yearly_breakdown.append({
                    'year': current_year + year_num,
                    'year_num': year_num,
                    'deposits': round(year_deposits, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(balance, 2),
                })
                chart_labels.append(f'Year {year_num}')
                chart_balance.append(round(balance, 2))
                chart_deposits.append(round(total_deposits, 2))
                
                year_start_balance = balance
                year_deposits = 0
                year_interest = 0
        
        # Handle partial year
        remaining_months = months % 12
        if remaining_months > 0:
            year_num = (months // 12) + 1
            yearly_breakdown.append({
                'year': current_year + year_num,
                'year_num': f'{year_num} (partial)',
                'deposits': round(year_deposits, 2),
                'interest': round(year_interest, 2),
                'end_balance': round(balance, 2),
            })
        
        # Calculate payoff date
        end_date = add_months(datetime.now(), months)
        
        return {
            'calc_mode': 'future_value',
            'final_balance': round(balance, 2),
            'total_deposits': round(total_deposits, 2),
            'total_interest': round(total_interest, 2),
            'initial_savings': round(initial, 2),
            'monthly_contribution': round(monthly * months, 2),
            'years': years,
            'end_date': end_date.strftime('%B %Y'),
            'yearly_breakdown': yearly_breakdown,
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
                'deposits': chart_deposits,
            }
        }
    
    def _calculate_required_deposit(self, initial, goal, rate, n, years):
        """Calculate required monthly deposit to reach goal"""
        months = int(years * 12)
        monthly_rate = rate / 12
        
        if monthly_rate > 0:
            # Future value of initial deposit
            fv_initial = initial * np.power(1 + monthly_rate, months)
            
            # Remaining amount needed
            remaining = goal - fv_initial
            
            # Calculate required monthly deposit using annuity formula
            if remaining <= 0:
                monthly_deposit = 0
            else:
                # PMT = FV * r / [(1+r)^n - 1]
                rate_factor = np.power(1 + monthly_rate, months) - 1
                monthly_deposit = remaining * monthly_rate / rate_factor
        else:
            remaining = goal - initial
            monthly_deposit = remaining / months if months > 0 else remaining
        
        monthly_deposit = max(0, monthly_deposit)
        
        # Now calculate the actual growth with this deposit
        result = self._calculate_future_value(initial, monthly_deposit, rate, n, years)
        result['calc_mode'] = 'monthly_deposit'
        result['required_monthly_deposit'] = round(monthly_deposit, 2)
        result['savings_goal'] = round(goal, 2)
        
        return result
    
    def _calculate_time_to_goal(self, initial, monthly, goal, rate, n):
        """Calculate time needed to reach savings goal"""
        monthly_rate = rate / 12
        
        if goal <= initial:
            return {
                'calc_mode': 'time_to_goal',
                'months_to_goal': 0,
                'years_to_goal': 0,
                'final_balance': round(initial, 2),
                'savings_goal': round(goal, 2),
                'message': 'You have already reached your goal!',
                'yearly_breakdown': [],
                'chart_data': {'labels': [], 'balance': [], 'deposits': []}
            }
        
        # Simulate month by month
        balance = initial
        total_deposits = initial
        months = 0
        max_months = self.MAX_YEARS * 12
        
        yearly_breakdown = []
        chart_labels = ['Start']
        chart_balance = [initial]
        chart_deposits = [initial]
        
        current_year = datetime.now().year
        year_deposits = 0
        year_interest = 0
        total_interest = 0
        
        while balance < goal and months < max_months:
            months += 1
            
            # Add monthly deposit
            balance += monthly
            total_deposits += monthly
            year_deposits += monthly
            
            # Calculate interest
            interest = balance * monthly_rate
            balance += interest
            total_interest += interest
            year_interest += interest
            
            # Year end summary
            if months % 12 == 0:
                year_num = months // 12
                yearly_breakdown.append({
                    'year': current_year + year_num,
                    'year_num': year_num,
                    'deposits': round(year_deposits, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(balance, 2),
                })
                chart_labels.append(f'Year {year_num}')
                chart_balance.append(round(balance, 2))
                chart_deposits.append(round(total_deposits, 2))
                
                year_deposits = 0
                year_interest = 0
        
        if months >= max_months:
            return {
                'calc_mode': 'time_to_goal',
                'error': 'Goal cannot be reached within reasonable time frame. Consider increasing your monthly deposit.',
                'months_to_goal': None,
                'yearly_breakdown': yearly_breakdown[:10],
                'chart_data': {
                    'labels': chart_labels[:11],
                    'balance': chart_balance[:11],
                    'deposits': chart_deposits[:11],
                }
            }
        
        years = months / 12
        end_date = add_months(datetime.now(), months)
        
        return {
            'calc_mode': 'time_to_goal',
            'months_to_goal': months,
            'years_to_goal': round(years, 1),
            'final_balance': round(balance, 2),
            'total_deposits': round(total_deposits, 2),
            'total_interest': round(total_interest, 2),
            'savings_goal': round(goal, 2),
            'end_date': end_date.strftime('%B %Y'),
            'yearly_breakdown': yearly_breakdown,
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
                'deposits': chart_deposits,
            }
        }
