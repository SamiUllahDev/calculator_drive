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
class LoanCalculator(View):
    """
    Professional Loan Calculator with comprehensive features.
    
    Features:
    - Monthly payment calculation
    - Total interest calculation
    - Amortization schedule
    - Extra payment analysis
    - Multiple loan term options
    - Visual charts
    """
    template_name = 'financial_calculators/loan_calculator.html'
    
    # Validation limits
    MIN_LOAN_AMOUNT = 100
    MAX_LOAN_AMOUNT = 100000000
    MIN_INTEREST_RATE = 0.01
    MAX_INTEREST_RATE = 50
    MIN_LOAN_TERM = 1
    MAX_LOAN_TERM = 50
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Loan Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get and validate inputs
            loan_amount = self._get_float(data, 'loan_amount', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            loan_term = self._get_int(data, 'loan_term', 0)
            term_type = data.get('term_type', 'years')  # years or months
            extra_payment = self._get_float(data, 'extra_payment', 0)
            
            # Validation
            errors = []
            
            if loan_amount < self.MIN_LOAN_AMOUNT:
                errors.append(f'Loan amount must be at least ${self.MIN_LOAN_AMOUNT:,}.')
            elif loan_amount > self.MAX_LOAN_AMOUNT:
                errors.append(f'Loan amount cannot exceed ${self.MAX_LOAN_AMOUNT:,}.')
            
            if interest_rate < self.MIN_INTEREST_RATE:
                errors.append(f'Interest rate must be at least {self.MIN_INTEREST_RATE}%.')
            elif interest_rate > self.MAX_INTEREST_RATE:
                errors.append(f'Interest rate cannot exceed {self.MAX_INTEREST_RATE}%.')
            
            if term_type == 'years':
                if loan_term < self.MIN_LOAN_TERM or loan_term > self.MAX_LOAN_TERM:
                    errors.append(f'Loan term must be between {self.MIN_LOAN_TERM} and {self.MAX_LOAN_TERM} years.')
                total_months = loan_term * 12
            else:
                if loan_term < 1 or loan_term > self.MAX_LOAN_TERM * 12:
                    errors.append(f'Loan term must be between 1 and {self.MAX_LOAN_TERM * 12} months.')
                total_months = loan_term
            
            if extra_payment < 0:
                errors.append('Extra payment cannot be negative.')
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate monthly rate
            monthly_rate = (interest_rate / 100) / 12
            
            # Calculate monthly payment using standard loan formula
            if monthly_rate > 0:
                rate_factor = np.power(1 + monthly_rate, total_months)
                monthly_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
            else:
                monthly_payment = loan_amount / total_months
            
            # Validate payment covers interest
            first_month_interest = loan_amount * monthly_rate
            if monthly_payment <= first_month_interest:
                return JsonResponse({
                    'success': False,
                    'error': f'The calculated payment (${monthly_payment:,.2f}) does not cover the first month interest (${first_month_interest:,.2f}). Please adjust your inputs.'
                }, status=400)
            
            # Generate standard amortization schedule
            standard_schedule = self._generate_schedule(
                loan_amount, monthly_rate, monthly_payment, total_months, 0
            )
            
            # Generate schedule with extra payments if applicable
            extra_schedule = None
            savings = None
            
            if extra_payment > 0:
                extra_schedule = self._generate_schedule(
                    loan_amount, monthly_rate, monthly_payment, total_months, extra_payment
                )
                
                standard_interest = sum(p['interest'] for p in standard_schedule['schedule'])
                extra_interest = sum(p['interest'] for p in extra_schedule['schedule'])
                
                savings = {
                    'interest_saved': round(standard_interest - extra_interest, 2),
                    'months_saved': len(standard_schedule['schedule']) - len(extra_schedule['schedule']),
                    'new_payoff_months': len(extra_schedule['schedule']),
                }
            
            # Calculate totals
            total_interest = sum(p['interest'] for p in standard_schedule['schedule'])
            total_paid = loan_amount + total_interest
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(standard_schedule, extra_schedule)
            
            # Last payment info
            last_payment = standard_schedule['schedule'][-1] if standard_schedule['schedule'] else None
            payoff_date = last_payment['date'] if last_payment else 'N/A'
            
            response_data = {
                'success': True,
                'loan_details': {
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'loan_term_months': total_months,
                    'loan_term_years': round(total_months / 12, 1),
                },
                'payment': {
                    'monthly': round(monthly_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'total_paid': round(total_paid, 2),
                    'payoff_date': payoff_date,
                },
                'schedule': standard_schedule['schedule'][:120],  # First 10 years
                'yearly_summary': standard_schedule['yearly_summary'],
                'chart_data': chart_data,
            }
            
            if savings:
                response_data['savings'] = savings
                response_data['extra_schedule'] = extra_schedule['schedule'][:120]
            
            return JsonResponse(response_data)
            
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
    
    def _get_int(self, data, key, default=0):
        """Safely get int value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default
    
    def _generate_schedule(self, loan_amount, monthly_rate, monthly_payment, total_months, extra_payment):
        """Generate amortization schedule"""
        schedule = []
        yearly_summary = []
        
        balance = loan_amount
        start_date = datetime.now()
        
        year_interest = 0
        year_principal = 0
        current_year = start_date.year
        year_start_balance = balance
        
        month_num = 0
        
        while balance > 0.01 and month_num < total_months + 240:
            month_num += 1
            current_date = add_months(start_date, month_num - 1)
            
            # Calculate interest
            interest = balance * monthly_rate
            
            # Calculate principal
            principal = monthly_payment - interest
            
            # Add extra payment
            total_principal = principal + extra_payment
            
            # Don't overpay
            if total_principal > balance:
                total_principal = balance
                extra_this_month = max(0, balance - principal)
            else:
                extra_this_month = extra_payment
            
            # Update balance
            balance = max(0, balance - total_principal)
            
            schedule.append({
                'month': month_num,
                'date': current_date.strftime('%b %Y'),
                'payment': round(monthly_payment + extra_this_month, 2),
                'principal': round(principal, 2),
                'extra': round(extra_this_month, 2),
                'interest': round(interest, 2),
                'balance': round(balance, 2),
            })
            
            # Track yearly totals
            year_interest += interest
            year_principal += total_principal
            
            # Year end summary
            if current_date.month == 12 or balance <= 0.01:
                yearly_summary.append({
                    'year': current_year,
                    'principal': round(year_principal, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(balance, 2),
                })
                year_interest = 0
                year_principal = 0
                current_year += 1
                year_start_balance = balance
            
            if balance <= 0.01:
                break
        
        return {
            'schedule': schedule,
            'yearly_summary': yearly_summary,
        }
    
    def _prepare_chart_data(self, standard_schedule, extra_schedule=None):
        """Prepare chart data"""
        # Balance over time (yearly)
        labels = []
        standard_balance = []
        
        for year in standard_schedule['yearly_summary']:
            labels.append(str(year['year']))
            standard_balance.append(year['end_balance'])
        
        chart_data = {
            'balance': {
                'labels': labels,
                'standard': standard_balance,
            }
        }
        
        if extra_schedule:
            extra_balance = []
            for i, year in enumerate(extra_schedule['yearly_summary']):
                if i < len(labels):
                    extra_balance.append(year['end_balance'])
            # Pad with zeros
            while len(extra_balance) < len(labels):
                extra_balance.append(0)
            chart_data['balance']['extra'] = extra_balance
        
        # Payment breakdown (first payment)
        if standard_schedule['schedule']:
            first = standard_schedule['schedule'][0]
            total_interest = sum(p['interest'] for p in standard_schedule['schedule'])
            chart_data['breakdown'] = {
                'principal': round(standard_schedule['schedule'][0]['principal'], 2),
                'interest': round(standard_schedule['schedule'][0]['interest'], 2),
                'total_principal': round(sum(p['principal'] for p in standard_schedule['schedule']), 2),
                'total_interest': round(total_interest, 2),
            }
        
        return chart_data
