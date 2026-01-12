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
    """Add months to a date (fallback if dateutil not available)"""
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
class MortgageAmortizationCalculator(View):
    """
    Professional Mortgage Amortization Calculator
    
    Features:
    - Full amortization schedule generation
    - Monthly and yearly view options
    - Extra payment analysis
    - Interest savings calculation
    - Exportable schedule data
    - Visual charts showing payment breakdown
    - Comparison with and without extra payments
    """
    template_name = 'financial_calculators/mortgage_amortization_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        current_month = datetime.now().month
        current_year = datetime.now().year
        years = list(range(current_year, current_year + 31))
        
        context = {
            'calculator_name': 'Mortgage Amortization Calculator',
            'page_title': 'Mortgage Amortization Calculator - View Your Complete Payment Schedule',
            'months': months,
            'years': years,
            'current_month': current_month,
            'current_year': current_year,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            loan_amount = self._get_float(data, 'loan_amount', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            loan_term = self._get_int(data, 'loan_term', 30)
            start_month = self._get_int(data, 'start_month', datetime.now().month)
            start_year = self._get_int(data, 'start_year', datetime.now().year)
            
            # Extra payments
            extra_monthly = self._get_float(data, 'extra_monthly', 0)
            extra_yearly = self._get_float(data, 'extra_yearly', 0)
            extra_yearly_month = self._get_int(data, 'extra_yearly_month', 1)
            
            # Validation
            if loan_amount <= 0:
                return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)
            
            if interest_rate <= 0 or interest_rate > 30:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0.01% and 30%.'}, status=400)
            
            if loan_term <= 0 or loan_term > 50:
                return JsonResponse({'success': False, 'error': 'Loan term must be between 1 and 50 years.'}, status=400)
            
            # Calculate monthly rate and payment
            monthly_rate = (interest_rate / 100) / 12
            total_payments = loan_term * 12
            
            # Standard monthly payment (without extra)
            if monthly_rate > 0:
                rate_factor = np.power(1 + monthly_rate, total_payments)
                monthly_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
            else:
                monthly_payment = loan_amount / total_payments
            
            # Generate standard amortization (without extra payments)
            standard_schedule = self._generate_schedule(
                loan_amount=loan_amount,
                monthly_rate=monthly_rate,
                monthly_payment=monthly_payment,
                total_payments=total_payments,
                start_month=start_month,
                start_year=start_year,
                extra_monthly=0,
                extra_yearly=0,
                extra_yearly_month=1
            )
            
            # Generate schedule with extra payments
            has_extra = extra_monthly > 0 or extra_yearly > 0
            extra_schedule = None
            savings = None
            
            if has_extra:
                extra_schedule = self._generate_schedule(
                    loan_amount=loan_amount,
                    monthly_rate=monthly_rate,
                    monthly_payment=monthly_payment,
                    total_payments=total_payments,
                    start_month=start_month,
                    start_year=start_year,
                    extra_monthly=extra_monthly,
                    extra_yearly=extra_yearly,
                    extra_yearly_month=extra_yearly_month
                )
                
                # Calculate savings
                standard_interest = sum(p['interest'] for p in standard_schedule['schedule'])
                extra_interest = sum(p['interest'] for p in extra_schedule['schedule'])
                
                savings = {
                    'interest_saved': round(standard_interest - extra_interest, 2),
                    'months_saved': len(standard_schedule['schedule']) - len(extra_schedule['schedule']),
                    'original_months': len(standard_schedule['schedule']),
                    'new_months': len(extra_schedule['schedule']),
                    'total_extra_paid': round(sum(p['extra'] for p in extra_schedule['schedule']), 2),
                }
            
            # Calculate totals for standard schedule
            total_interest = sum(p['interest'] for p in standard_schedule['schedule'])
            total_paid = loan_amount + total_interest
            
            # Last payment info
            last_payment = standard_schedule['schedule'][-1] if standard_schedule['schedule'] else None
            payoff_date = last_payment['date'] if last_payment else 'N/A'
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(
                standard_schedule,
                extra_schedule if has_extra else None
            )
            
            response_data = {
                'success': True,
                'loan_details': {
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'loan_term_years': loan_term,
                    'loan_term_months': total_payments,
                    'monthly_payment': round(monthly_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'total_paid': round(total_paid, 2),
                    'payoff_date': payoff_date,
                },
                'schedule': standard_schedule['schedule'],
                'yearly_summary': standard_schedule['yearly_summary'],
                'chart_data': chart_data,
            }
            
            if has_extra:
                response_data['extra_schedule'] = extra_schedule['schedule']
                response_data['extra_yearly_summary'] = extra_schedule['yearly_summary']
                response_data['savings'] = savings
                
                extra_last = extra_schedule['schedule'][-1] if extra_schedule['schedule'] else None
                response_data['extra_payoff_date'] = extra_last['date'] if extra_last else 'N/A'
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Calculation error. Please check your inputs.'
            }, status=400)
    
    def _get_float(self, data, key, default=0):
        """Safely get float value from data"""
        try:
            value = data.get(key, default)
            return float(value) if value not in (None, '', 'null') else default
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely get int value from data"""
        try:
            value = data.get(key, default)
            return int(float(value)) if value not in (None, '', 'null') else default
        except (ValueError, TypeError):
            return default
    
    def _generate_schedule(self, loan_amount, monthly_rate, monthly_payment, total_payments,
                           start_month, start_year, extra_monthly, extra_yearly, extra_yearly_month):
        """Generate amortization schedule"""
        schedule = []
        yearly_summary = []
        
        balance = loan_amount
        current_date = datetime(start_year, start_month, 1)
        
        # Yearly tracking
        year_interest = 0
        year_principal = 0
        current_year = start_year
        year_start_balance = balance
        
        month_num = 0
        cumulative_interest = 0
        cumulative_principal = 0
        
        while balance > 0.01 and month_num < total_payments + 120:
            month_num += 1
            
            # Calculate interest
            interest_payment = balance * monthly_rate
            
            # Calculate principal
            scheduled_principal = monthly_payment - interest_payment
            
            # Extra payments
            extra_this_month = extra_monthly
            if current_date.month == extra_yearly_month and extra_yearly > 0:
                extra_this_month += extra_yearly
            
            total_principal = scheduled_principal + extra_this_month
            
            # Don't overpay
            if total_principal > balance:
                total_principal = balance
                extra_this_month = max(0, total_principal - scheduled_principal)
                scheduled_principal = min(scheduled_principal, balance)
            
            # Update balance
            balance = max(0, balance - total_principal)
            
            # Update cumulative totals
            cumulative_interest += interest_payment
            cumulative_principal += total_principal
            
            # Calculate percentage of loan paid
            percent_paid = ((loan_amount - balance) / loan_amount) * 100
            
            # Add to schedule
            schedule.append({
                'month': month_num,
                'date': current_date.strftime('%b %Y'),
                'payment': round(monthly_payment + extra_this_month, 2),
                'principal': round(scheduled_principal, 2),
                'extra': round(extra_this_month, 2),
                'total_principal': round(scheduled_principal + extra_this_month, 2),
                'interest': round(interest_payment, 2),
                'balance': round(balance, 2),
                'cumulative_interest': round(cumulative_interest, 2),
                'cumulative_principal': round(cumulative_principal, 2),
                'percent_paid': round(percent_paid, 1),
            })
            
            # Track yearly totals
            year_interest += interest_payment
            year_principal += total_principal
            
            # Year end summary
            if current_date.month == 12 or balance <= 0.01:
                yearly_summary.append({
                    'year': current_year,
                    'principal': round(year_principal, 2),
                    'interest': round(year_interest, 2),
                    'total_paid': round(year_principal + year_interest, 2),
                    'start_balance': round(year_start_balance, 2),
                    'end_balance': round(balance, 2),
                    'percent_paid': round(((loan_amount - balance) / loan_amount) * 100, 1),
                })
                year_interest = 0
                year_principal = 0
                current_year += 1
                year_start_balance = balance
            
            # Move to next month
            current_date = add_months(current_date, 1)
            
            if balance <= 0.01:
                break
        
        return {
            'schedule': schedule,
            'yearly_summary': yearly_summary,
        }
    
    def _prepare_chart_data(self, standard_schedule, extra_schedule=None):
        """Prepare chart data for visualization"""
        
        # Balance over time
        balance_data = {
            'labels': [],
            'standard_balance': [],
            'standard_interest': [],
            'standard_principal': [],
        }
        
        cumulative_interest = 0
        cumulative_principal = 0
        
        for year in standard_schedule['yearly_summary']:
            balance_data['labels'].append(str(year['year']))
            balance_data['standard_balance'].append(year['end_balance'])
            cumulative_interest += year['interest']
            cumulative_principal += year['principal']
            balance_data['standard_interest'].append(round(cumulative_interest, 2))
            balance_data['standard_principal'].append(round(cumulative_principal, 2))
        
        # Add extra payment data if available
        if extra_schedule:
            balance_data['extra_balance'] = []
            cumulative_interest_extra = 0
            
            for i, year in enumerate(extra_schedule['yearly_summary']):
                if i < len(balance_data['labels']):
                    balance_data['extra_balance'].append(year['end_balance'])
                cumulative_interest_extra += year['interest']
            
            # Pad with zeros if paid off early
            while len(balance_data['extra_balance']) < len(balance_data['labels']):
                balance_data['extra_balance'].append(0)
        
        # Payment breakdown for first year
        if standard_schedule['schedule']:
            first_payment = standard_schedule['schedule'][0]
            payment_breakdown = {
                'principal': first_payment['principal'],
                'interest': first_payment['interest'],
            }
        else:
            payment_breakdown = {'principal': 0, 'interest': 0}
        
        # Interest vs Principal over time (monthly for first 2 years)
        monthly_breakdown = {
            'labels': [],
            'principal': [],
            'interest': [],
        }
        
        for payment in standard_schedule['schedule'][:24]:  # First 2 years
            monthly_breakdown['labels'].append(payment['date'])
            monthly_breakdown['principal'].append(payment['principal'])
            monthly_breakdown['interest'].append(payment['interest'])
        
        return {
            'balance_data': balance_data,
            'payment_breakdown': payment_breakdown,
            'monthly_breakdown': monthly_breakdown,
        }
