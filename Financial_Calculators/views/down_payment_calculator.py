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
class DownPaymentCalculator(View):
    """
    Professional Down Payment Calculator with comprehensive features.
    
    Features:
    - Down payment amount calculation
    - Savings goal planning
    - PMI impact analysis
    - Closing costs estimation
    - Multiple down payment scenarios
    - Monthly savings needed
    """
    template_name = 'financial_calculators/down_payment_calculator.html'
    
    # Validation limits
    MIN_PRICE = 10000
    MAX_PRICE = 100000000
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Down Payment Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            home_price = self._get_float(data, 'home_price', 0)
            down_payment_percent = self._get_float(data, 'down_payment_percent', 20)
            current_savings = self._get_float(data, 'current_savings', 0)
            monthly_savings = self._get_float(data, 'monthly_savings', 0)
            savings_rate = self._get_float(data, 'savings_rate', 4)
            closing_cost_percent = self._get_float(data, 'closing_cost_percent', 3)
            interest_rate = self._get_float(data, 'interest_rate', 6.5)
            loan_term = self._get_int(data, 'loan_term', 30)
            
            # Validation
            errors = []
            
            if home_price < self.MIN_PRICE:
                errors.append(f'Home price must be at least ${self.MIN_PRICE:,}.')
            elif home_price > self.MAX_PRICE:
                errors.append(f'Home price cannot exceed ${self.MAX_PRICE:,}.')
            
            if down_payment_percent < 0 or down_payment_percent > 100:
                errors.append('Down payment percentage must be between 0% and 100%.')
            
            if current_savings < 0:
                errors.append('Current savings cannot be negative.')
            
            if monthly_savings < 0:
                errors.append('Monthly savings cannot be negative.')
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate
            result = self._calculate_down_payment(
                home_price, down_payment_percent, current_savings,
                monthly_savings, savings_rate, closing_cost_percent,
                interest_rate, loan_term
            )
            
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
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely get int value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default
    
    def _calculate_down_payment(self, home_price, down_pct, current_savings,
                                monthly_savings, savings_rate, closing_pct,
                                interest_rate, loan_term):
        """Calculate down payment and savings timeline"""
        
        # Basic calculations
        down_payment = home_price * (down_pct / 100)
        closing_costs = home_price * (closing_pct / 100)
        total_needed = down_payment + closing_costs
        loan_amount = home_price - down_payment
        
        # PMI calculation (if down payment < 20%)
        pmi_required = down_pct < 20
        monthly_pmi = 0
        total_pmi = 0
        
        if pmi_required:
            # Estimate PMI at 0.5-1% of loan amount annually
            annual_pmi_rate = 0.007  # 0.7% average
            annual_pmi = loan_amount * annual_pmi_rate
            monthly_pmi = annual_pmi / 12
            
            # Calculate PMI duration (until 20% equity)
            pmi_months = self._calculate_pmi_duration(
                loan_amount, interest_rate, loan_term, home_price
            )
            total_pmi = monthly_pmi * pmi_months
        
        # Calculate monthly mortgage payment
        monthly_rate = (interest_rate / 100) / 12
        months = loan_term * 12
        
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, months)
            monthly_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            monthly_payment = loan_amount / months
        
        total_monthly_with_pmi = monthly_payment + monthly_pmi
        
        # Calculate savings timeline
        amount_still_needed = max(0, total_needed - current_savings)
        
        if amount_still_needed > 0 and monthly_savings > 0:
            months_to_goal = self._calculate_months_to_save(
                amount_still_needed, monthly_savings, savings_rate
            )
            target_date = add_months(datetime.now(), months_to_goal)
            goal_date = target_date.strftime('%B %Y')
        else:
            months_to_goal = 0
            goal_date = 'Already saved!' if amount_still_needed <= 0 else 'N/A'
        
        # Generate savings projection
        savings_projection = self._generate_savings_projection(
            current_savings, monthly_savings, savings_rate, total_needed
        )
        
        # Compare different down payment scenarios
        scenarios = self._compare_scenarios(home_price, interest_rate, loan_term, closing_pct)
        
        return {
            'home_price': round(home_price, 2),
            'down_payment': {
                'percent': down_pct,
                'amount': round(down_payment, 2),
            },
            'closing_costs': round(closing_costs, 2),
            'total_needed': round(total_needed, 2),
            'loan_amount': round(loan_amount, 2),
            'monthly_payment': round(monthly_payment, 2),
            'pmi': {
                'required': pmi_required,
                'monthly': round(monthly_pmi, 2),
                'total': round(total_pmi, 2),
            },
            'total_monthly_with_pmi': round(total_monthly_with_pmi, 2),
            'savings_goal': {
                'current_savings': round(current_savings, 2),
                'amount_needed': round(amount_still_needed, 2),
                'months_to_goal': months_to_goal,
                'goal_date': goal_date,
            },
            'savings_projection': savings_projection,
            'scenarios': scenarios,
        }
    
    def _calculate_pmi_duration(self, loan_amount, rate, term, home_price):
        """Calculate how many months until PMI can be removed (20% equity)"""
        monthly_rate = (rate / 100) / 12
        months = term * 12
        
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, months)
            payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            payment = loan_amount / months
        
        balance = loan_amount
        target_balance = home_price * 0.80  # 20% equity
        month = 0
        
        while balance > target_balance and month < months:
            month += 1
            interest = balance * monthly_rate
            principal = payment - interest
            balance = max(0, balance - principal)
        
        return month
    
    def _calculate_months_to_save(self, target, monthly, rate):
        """Calculate months needed to reach savings goal"""
        monthly_rate = (rate / 100) / 12
        
        if monthly <= 0:
            return 999  # Can't reach goal
        
        balance = 0
        month = 0
        max_months = 600
        
        while balance < target and month < max_months:
            month += 1
            balance += monthly
            balance *= (1 + monthly_rate)
        
        return month
    
    def _generate_savings_projection(self, current, monthly, rate, target):
        """Generate savings growth projection"""
        monthly_rate = (rate / 100) / 12
        projection = []
        
        balance = current
        chart_labels = ['Now']
        chart_balance = [round(current, 2)]
        
        year = 0
        max_years = 15
        
        while balance < target and year < max_years:
            year += 1
            year_start = balance
            
            for month in range(12):
                balance += monthly
                balance *= (1 + monthly_rate)
            
            projection.append({
                'year': year,
                'balance': round(balance, 2),
                'added': round(monthly * 12, 2),
            })
            
            chart_labels.append(f'Year {year}')
            chart_balance.append(round(balance, 2))
            
            if balance >= target:
                break
        
        return {
            'yearly': projection,
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
                'target': target,
            }
        }
    
    def _compare_scenarios(self, home_price, rate, term, closing_pct):
        """Compare different down payment scenarios"""
        scenarios = []
        
        for pct in [3, 5, 10, 15, 20]:
            down_payment = home_price * (pct / 100)
            closing = home_price * (closing_pct / 100)
            loan = home_price - down_payment
            
            # Calculate payment
            monthly_rate = (rate / 100) / 12
            months = term * 12
            
            if monthly_rate > 0:
                rate_factor = np.power(1 + monthly_rate, months)
                payment = loan * (monthly_rate * rate_factor) / (rate_factor - 1)
            else:
                payment = loan / months
            
            # PMI
            pmi = 0
            if pct < 20:
                pmi = (loan * 0.007) / 12
            
            total_monthly = payment + pmi
            
            scenarios.append({
                'percent': pct,
                'down_payment': round(down_payment, 2),
                'total_upfront': round(down_payment + closing, 2),
                'loan_amount': round(loan, 2),
                'monthly_payment': round(payment, 2),
                'pmi': round(pmi, 2),
                'total_monthly': round(total_monthly, 2),
            })
        
        return scenarios
