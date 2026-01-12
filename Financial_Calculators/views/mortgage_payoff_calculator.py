from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from datetime import datetime
import re

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
class MortgagePayoffCalculator(View):
    """
    Professional Mortgage Payoff Calculator
    
    Features:
    - Two calculation modes (know remaining term / don't know)
    - Extra payment analysis (monthly, yearly, one-time)
    - Biweekly payment option
    - Interest and time savings calculation
    - Side-by-side comparison
    - Amortization schedule generation
    - Comprehensive input validation
    """
    template_name = 'financial_calculators/mortgage_payoff_calculator.html'
    
    # Validation limits
    MIN_LOAN_AMOUNT = 1000
    MAX_LOAN_AMOUNT = 100000000  # $100 million
    MIN_INTEREST_RATE = 0.01
    MAX_INTEREST_RATE = 30
    MIN_LOAN_TERM = 1
    MAX_LOAN_TERM = 50
    MAX_EXTRA_PAYMENT = 10000000  # $10 million
    MAX_ONE_TIME_PAYMENT = 100000000  # $100 million
    
    def get(self, request):
        """Handle GET request"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        current_month = datetime.now().month
        current_year = datetime.now().year
        years = list(range(current_year, current_year + 5))
        
        context = {
            'calculator_name': 'Mortgage Payoff Calculator',
            'page_title': 'Mortgage Payoff Calculator - Calculate Your Payoff Date & Savings',
            'months': months,
            'years': years,
            'current_month': current_month,
            'current_year': current_year,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            # Parse request data
            if request.content_type == 'application/json':
                try:
                    data = json.loads(request.body)
                except json.JSONDecodeError:
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid request format. Please try again.'
                    }, status=400)
            else:
                data = request.POST
            
            # Validate calculation mode
            calc_mode = data.get('calc_mode', 'mode2')
            if calc_mode not in ['mode1', 'mode2']:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid calculation mode selected.'
                }, status=400)
            
            # Validate repayment option
            repayment_option = data.get('repayment_option', 'normal')
            valid_options = ['normal', 'payoff_all', 'extra', 'biweekly']
            if repayment_option not in valid_options:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid repayment option selected.'
                }, status=400)
            
            if calc_mode == 'mode1':
                return self._calculate_mode1(data)
            else:
                return self._calculate_mode2(data)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid request format. Please refresh and try again.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An unexpected error occurred. Please check your inputs and try again.'
            }, status=400)
    
    def _sanitize_number(self, value):
        """Remove common formatting characters from number inputs"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r'[$,\s]', '', str(value))
        return cleaned if cleaned else None
    
    def _validate_positive_number(self, value, field_name, min_val=None, max_val=None, required=True):
        """Validate a positive number with optional range"""
        if value is None or value == '':
            if required:
                return None, f'{field_name} is required.'
            return 0, None
        
        try:
            num = float(value)
        except (ValueError, TypeError):
            return None, f'{field_name} must be a valid number.'
        
        if num < 0:
            return None, f'{field_name} cannot be negative.'
        
        if required and num <= 0:
            return None, f'{field_name} must be greater than zero.'
        
        if min_val is not None and num < min_val:
            return None, f'{field_name} must be at least {min_val:,.2f}.'
        
        if max_val is not None and num > max_val:
            return None, f'{field_name} cannot exceed {max_val:,.0f}.'
        
        return num, None
    
    def _calculate_mode1(self, data):
        """Calculate when remaining loan term is known"""
        errors = []
        
        # Validate and sanitize Original Loan Amount
        original_amount_raw = self._sanitize_number(data.get('original_amount'))
        original_amount, error = self._validate_positive_number(
            original_amount_raw, 
            'Original loan amount',
            min_val=self.MIN_LOAN_AMOUNT,
            max_val=self.MAX_LOAN_AMOUNT
        )
        if error:
            errors.append(error)
        
        # Validate Original Loan Term
        original_term_years = self._get_int(data, 'original_term', 0)
        if original_term_years < self.MIN_LOAN_TERM or original_term_years > self.MAX_LOAN_TERM:
            errors.append(f'Original loan term must be between {self.MIN_LOAN_TERM} and {self.MAX_LOAN_TERM} years.')
        
        # Validate Interest Rate
        interest_rate_raw = self._sanitize_number(data.get('interest_rate'))
        interest_rate, error = self._validate_positive_number(
            interest_rate_raw,
            'Interest rate',
            min_val=self.MIN_INTEREST_RATE,
            max_val=self.MAX_INTEREST_RATE
        )
        if error:
            errors.append(error)
        
        # Validate Remaining Term
        remaining_years = self._get_int(data, 'remaining_years', 0)
        remaining_months_input = self._get_int(data, 'remaining_months', 0)
        
        if remaining_years < 0:
            errors.append('Remaining years cannot be negative.')
        if remaining_months_input < 0 or remaining_months_input > 11:
            errors.append('Remaining months must be between 0 and 11.')
        
        remaining_total_months = remaining_years * 12 + remaining_months_input
        
        if remaining_total_months <= 0:
            errors.append('Remaining term must be greater than 0 months.')
        
        # Check remaining term doesn't exceed original term
        if original_term_years and remaining_total_months > original_term_years * 12:
            errors.append(f'Remaining term ({remaining_years} years, {remaining_months_input} months) cannot exceed original term ({original_term_years} years).')
        
        # Validate Extra Payments
        repayment_option = data.get('repayment_option', 'normal')
        extra_monthly = 0
        extra_yearly = 0
        one_time_payment = 0
        
        if repayment_option == 'extra':
            extra_monthly_raw = self._sanitize_number(data.get('extra_monthly'))
            extra_monthly, error = self._validate_positive_number(
                extra_monthly_raw,
                'Extra monthly payment',
                max_val=self.MAX_EXTRA_PAYMENT,
                required=False
            )
            if error:
                errors.append(error)
            
            extra_yearly_raw = self._sanitize_number(data.get('extra_yearly'))
            extra_yearly, error = self._validate_positive_number(
                extra_yearly_raw,
                'Extra yearly payment',
                max_val=self.MAX_EXTRA_PAYMENT,
                required=False
            )
            if error:
                errors.append(error)
            
            one_time_raw = self._sanitize_number(data.get('one_time_payment'))
            one_time_payment, error = self._validate_positive_number(
                one_time_raw,
                'One-time payment',
                max_val=self.MAX_ONE_TIME_PAYMENT,
                required=False
            )
            if error:
                errors.append(error)
            
            # Check if at least one extra payment is provided
            if extra_monthly == 0 and extra_yearly == 0 and one_time_payment == 0:
                errors.append('Please enter at least one extra payment amount when using extra payments option.')
        
        # Return all errors if any
        if errors:
            return JsonResponse({
                'success': False,
                'error': errors[0] if len(errors) == 1 else 'Please fix the following errors: ' + ' | '.join(errors)
            }, status=400)
        
        # Calculate monthly rate and original payment
        monthly_rate = (interest_rate / 100) / 12
        original_term_months = original_term_years * 12
        
        # Calculate original monthly payment
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, original_term_months)
            monthly_payment = original_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            monthly_payment = original_amount / original_term_months
        
        # Validate monthly payment is reasonable
        if monthly_payment <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Could not calculate a valid monthly payment. Please check your inputs.'
            }, status=400)
        
        # Calculate remaining balance
        months_paid = original_term_months - remaining_total_months
        if months_paid < 0:
            return JsonResponse({
                'success': False,
                'error': 'Remaining term cannot be longer than original term.'
            }, status=400)
        
        remaining_balance = self._calculate_remaining_balance(
            original_amount, monthly_rate, monthly_payment, months_paid
        )
        
        # Validate remaining balance
        if remaining_balance <= 0:
            return JsonResponse({
                'success': False,
                'error': 'The loan appears to be already paid off based on your inputs.'
            }, status=400)
        
        # Validate extra payments don't exceed balance
        total_extra = extra_monthly + extra_yearly + one_time_payment
        if total_extra > remaining_balance:
            return JsonResponse({
                'success': False,
                'error': f'Total extra payments (${total_extra:,.2f}) exceed the remaining balance (${remaining_balance:,.2f}).'
            }, status=400)
        
        return self._process_calculation(
            remaining_balance=remaining_balance,
            monthly_payment=monthly_payment,
            monthly_rate=monthly_rate,
            interest_rate=interest_rate,
            repayment_option=repayment_option,
            extra_monthly=extra_monthly or 0,
            extra_yearly=extra_yearly or 0,
            one_time_payment=one_time_payment or 0,
            original_amount=original_amount,
            original_term_months=original_term_months,
            remaining_months=remaining_total_months
        )
    
    def _calculate_mode2(self, data):
        """Calculate when remaining loan term is unknown"""
        errors = []
        
        # Validate and sanitize Remaining Balance
        remaining_balance_raw = self._sanitize_number(data.get('remaining_balance'))
        remaining_balance, error = self._validate_positive_number(
            remaining_balance_raw,
            'Unpaid principal balance',
            min_val=self.MIN_LOAN_AMOUNT,
            max_val=self.MAX_LOAN_AMOUNT
        )
        if error:
            errors.append(error)
        
        # Validate Monthly Payment
        monthly_payment_raw = self._sanitize_number(data.get('monthly_payment'))
        monthly_payment, error = self._validate_positive_number(
            monthly_payment_raw,
            'Monthly payment',
            min_val=1
        )
        if error:
            errors.append(error)
        
        # Validate Interest Rate
        interest_rate_raw = self._sanitize_number(data.get('interest_rate'))
        interest_rate, error = self._validate_positive_number(
            interest_rate_raw,
            'Interest rate',
            min_val=self.MIN_INTEREST_RATE,
            max_val=self.MAX_INTEREST_RATE
        )
        if error:
            errors.append(error)
        
        # Validate Extra Payments
        repayment_option = data.get('repayment_option', 'normal')
        extra_monthly = 0
        extra_yearly = 0
        one_time_payment = 0
        
        if repayment_option == 'extra':
            extra_monthly_raw = self._sanitize_number(data.get('extra_monthly'))
            extra_monthly, error = self._validate_positive_number(
                extra_monthly_raw,
                'Extra monthly payment',
                max_val=self.MAX_EXTRA_PAYMENT,
                required=False
            )
            if error:
                errors.append(error)
            
            extra_yearly_raw = self._sanitize_number(data.get('extra_yearly'))
            extra_yearly, error = self._validate_positive_number(
                extra_yearly_raw,
                'Extra yearly payment',
                max_val=self.MAX_EXTRA_PAYMENT,
                required=False
            )
            if error:
                errors.append(error)
            
            one_time_raw = self._sanitize_number(data.get('one_time_payment'))
            one_time_payment, error = self._validate_positive_number(
                one_time_raw,
                'One-time payment',
                max_val=self.MAX_ONE_TIME_PAYMENT,
                required=False
            )
            if error:
                errors.append(error)
            
            # Check if at least one extra payment is provided
            if extra_monthly == 0 and extra_yearly == 0 and one_time_payment == 0:
                errors.append('Please enter at least one extra payment amount when using extra payments option.')
        
        # Return all errors if any
        if errors:
            return JsonResponse({
                'success': False,
                'error': errors[0] if len(errors) == 1 else 'Please fix the following errors: ' + ' | '.join(errors)
            }, status=400)
        
        monthly_rate = (interest_rate / 100) / 12
        
        # Check if payment covers interest
        first_month_interest = remaining_balance * monthly_rate
        if monthly_payment <= first_month_interest:
            min_required = first_month_interest * 1.01  # At least 1% more than interest
            return JsonResponse({
                'success': False, 
                'error': f'Monthly payment (${monthly_payment:,.2f}) must be greater than the monthly interest charge (${first_month_interest:,.2f}). Minimum payment should be at least ${min_required:,.2f}.'
            }, status=400)
        
        # Validate payment is reasonable for the balance
        max_reasonable_payment = remaining_balance * 0.5  # No more than 50% of balance per month
        if monthly_payment > max_reasonable_payment and monthly_payment > remaining_balance:
            return JsonResponse({
                'success': False,
                'error': f'Monthly payment (${monthly_payment:,.2f}) exceeds the remaining balance (${remaining_balance:,.2f}). Please verify your inputs.'
            }, status=400)
        
        # Validate extra payments don't exceed balance
        total_extra = (extra_monthly or 0) + (extra_yearly or 0) + (one_time_payment or 0)
        if total_extra > remaining_balance:
            return JsonResponse({
                'success': False,
                'error': f'Total extra payments (${total_extra:,.2f}) exceed the remaining balance (${remaining_balance:,.2f}).'
            }, status=400)
        
        return self._process_calculation(
            remaining_balance=remaining_balance,
            monthly_payment=monthly_payment,
            monthly_rate=monthly_rate,
            interest_rate=interest_rate,
            repayment_option=repayment_option,
            extra_monthly=extra_monthly or 0,
            extra_yearly=extra_yearly or 0,
            one_time_payment=one_time_payment or 0,
            original_amount=None,
            original_term_months=None,
            remaining_months=None
        )
    
    def _process_calculation(self, remaining_balance, monthly_payment, monthly_rate, interest_rate,
                             repayment_option, extra_monthly, extra_yearly, one_time_payment,
                             original_amount, original_term_months, remaining_months):
        """Process the main calculation"""
        
        # Original scenario (normal repayment)
        original_result = self._calculate_payoff(
            balance=remaining_balance,
            monthly_rate=monthly_rate,
            monthly_payment=monthly_payment,
            extra_monthly=0,
            extra_yearly=0,
            one_time_payment=0,
            biweekly=False
        )
        
        # Payoff scenario based on option
        if repayment_option == 'payoff_all':
            # Pay off everything now
            payoff_result = {
                'total_months': 0,
                'total_interest': 0,
                'total_paid': remaining_balance,
                'schedule': [],
                'payoff_date': datetime.now().strftime('%b %Y'),
                'new_payment': remaining_balance,
            }
        elif repayment_option == 'biweekly':
            payoff_result = self._calculate_payoff(
                balance=remaining_balance,
                monthly_rate=monthly_rate,
                monthly_payment=monthly_payment,
                extra_monthly=0,
                extra_yearly=0,
                one_time_payment=0,
                biweekly=True
            )
            payoff_result['new_payment'] = monthly_payment / 2
        elif repayment_option == 'extra':
            payoff_result = self._calculate_payoff(
                balance=remaining_balance,
                monthly_rate=monthly_rate,
                monthly_payment=monthly_payment,
                extra_monthly=extra_monthly,
                extra_yearly=extra_yearly,
                one_time_payment=one_time_payment,
                biweekly=False
            )
            payoff_result['new_payment'] = monthly_payment + extra_monthly
        else:
            # Normal repayment
            payoff_result = original_result.copy()
            payoff_result['new_payment'] = monthly_payment
        
        # Calculate savings
        interest_saved = original_result['total_interest'] - payoff_result['total_interest']
        months_saved = original_result['total_months'] - payoff_result['total_months']
        
        # Format time
        original_years = original_result['total_months'] // 12
        original_mos = original_result['total_months'] % 12
        payoff_years = payoff_result['total_months'] // 12
        payoff_mos = payoff_result['total_months'] % 12
        
        # Percentage savings
        interest_pct = (interest_saved / original_result['total_interest'] * 100) if original_result['total_interest'] > 0 else 0
        time_pct = (months_saved / original_result['total_months'] * 100) if original_result['total_months'] > 0 else 0
        
        # Build response
        response_data = {
            'success': True,
            'remaining_balance': round(remaining_balance, 2),
            'original': {
                'monthly_payment': round(monthly_payment, 2),
                'total_months': original_result['total_months'],
                'years': original_years,
                'months': original_mos,
                'time_string': self._format_time(original_result['total_months']),
                'total_payments': round(remaining_balance + original_result['total_interest'], 2),
                'total_interest': round(original_result['total_interest'], 2),
                'payoff_date': original_result['payoff_date'],
            },
            'payoff': {
                'monthly_payment': round(payoff_result.get('new_payment', monthly_payment), 2),
                'total_months': payoff_result['total_months'],
                'years': payoff_years,
                'months': payoff_mos,
                'time_string': self._format_time(payoff_result['total_months']),
                'total_payments': round(remaining_balance + payoff_result['total_interest'], 2),
                'total_interest': round(payoff_result['total_interest'], 2),
                'payoff_date': payoff_result['payoff_date'],
            },
            'savings': {
                'interest_saved': round(interest_saved, 2),
                'interest_pct': round(interest_pct, 0),
                'months_saved': months_saved,
                'time_saved_string': self._format_time(months_saved),
                'time_pct': round(time_pct, 0),
            },
            'schedule': payoff_result['schedule'][:120],  # First 10 years
        }
        
        # Generate quick comparison scenarios
        scenarios = self._generate_scenarios(remaining_balance, monthly_rate, monthly_payment)
        response_data['scenarios'] = scenarios
        
        return JsonResponse(response_data)
    
    def _calculate_remaining_balance(self, principal, monthly_rate, monthly_payment, months_paid):
        """Calculate remaining balance after N months"""
        if monthly_rate == 0:
            return max(0, principal - (monthly_payment * months_paid))
        
        balance = principal
        for _ in range(months_paid):
            interest = balance * monthly_rate
            principal_paid = monthly_payment - interest
            if principal_paid <= 0:
                # Payment doesn't cover interest - this shouldn't happen with valid inputs
                break
            balance = max(0, balance - principal_paid)
        
        return balance
    
    def _calculate_payoff(self, balance, monthly_rate, monthly_payment, extra_monthly,
                          extra_yearly, one_time_payment, biweekly=False):
        """Calculate payoff schedule"""
        schedule = []
        current_balance = balance
        start_date = datetime.now()
        
        total_interest = 0
        month_num = 0
        one_time_applied = False
        
        # Biweekly payment adjustment (26 half-payments = 13 monthly payments)
        if biweekly:
            # Effective monthly payment with biweekly is 13/12 * normal payment
            effective_monthly = monthly_payment * 13 / 12
            extra_from_biweekly = effective_monthly - monthly_payment
        else:
            extra_from_biweekly = 0
        
        while current_balance > 0.01 and month_num < 600:
            month_num += 1
            current_date = add_months(start_date, month_num - 1)
            
            # Calculate interest
            interest = current_balance * monthly_rate
            
            # Base principal
            principal = monthly_payment - interest
            
            # Extra payments
            extra_this_month = extra_monthly + extra_from_biweekly
            
            # Yearly extra (applied in January)
            if current_date.month == 1 and extra_yearly > 0:
                extra_this_month += extra_yearly
            
            # One-time payment (applied first month)
            if not one_time_applied and one_time_payment > 0:
                extra_this_month += one_time_payment
                one_time_applied = True
            
            total_principal = principal + extra_this_month
            
            # Don't overpay
            if total_principal > current_balance:
                total_principal = current_balance
                extra_this_month = max(0, current_balance - principal)
                principal = min(principal, current_balance)
            
            # Update balance
            current_balance = max(0, current_balance - total_principal)
            total_interest += interest
            
            schedule.append({
                'month': month_num,
                'date': current_date.strftime('%b %Y'),
                'payment': round(monthly_payment + extra_this_month, 2),
                'principal': round(principal, 2),
                'extra': round(extra_this_month, 2),
                'interest': round(interest, 2),
                'total_interest': round(total_interest, 2),
                'balance': round(current_balance, 2),
            })
            
            if current_balance <= 0.01:
                break
        
        payoff_date = add_months(start_date, month_num - 1).strftime('%b %Y')
        
        return {
            'total_months': month_num,
            'total_interest': total_interest,
            'total_paid': balance + total_interest,
            'payoff_date': payoff_date,
            'schedule': schedule,
        }
    
    def _generate_scenarios(self, balance, monthly_rate, monthly_payment):
        """Generate comparison scenarios"""
        scenarios = []
        extra_amounts = [100, 200, 500, 1000]
        
        baseline = self._calculate_payoff(balance, monthly_rate, monthly_payment, 0, 0, 0, False)
        
        for extra in extra_amounts:
            result = self._calculate_payoff(balance, monthly_rate, monthly_payment, extra, 0, 0, False)
            months_saved = baseline['total_months'] - result['total_months']
            interest_saved = baseline['total_interest'] - result['total_interest']
            
            scenarios.append({
                'extra': extra,
                'payoff_time': self._format_time(result['total_months']),
                'months_saved': months_saved,
                'time_saved': self._format_time(months_saved),
                'interest_saved': round(interest_saved, 2),
            })
        
        # Add biweekly scenario
        biweekly_result = self._calculate_payoff(balance, monthly_rate, monthly_payment, 0, 0, 0, True)
        scenarios.append({
            'extra': 'biweekly',
            'payoff_time': self._format_time(biweekly_result['total_months']),
            'months_saved': baseline['total_months'] - biweekly_result['total_months'],
            'time_saved': self._format_time(baseline['total_months'] - biweekly_result['total_months']),
            'interest_saved': round(baseline['total_interest'] - biweekly_result['total_interest'], 2),
        })
        
        return scenarios
    
    def _format_time(self, total_months):
        """Format months into years and months string"""
        if total_months <= 0:
            return "0 months"
        years = total_months // 12
        months = total_months % 12
        
        parts = []
        if years > 0:
            parts.append(f"{years} {'year' if years == 1 else 'years'}")
        if months > 0:
            parts.append(f"{months} {'month' if months == 1 else 'months'}")
        
        return ' and '.join(parts) if parts else "0 months"
    
    def _get_float(self, data, key, default=0):
        """Safely get float value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            # Clean the value
            cleaned = self._sanitize_number(value)
            return float(cleaned) if cleaned else default
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely get int value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            # Clean the value
            cleaned = self._sanitize_number(value)
            return int(float(cleaned)) if cleaned else default
        except (ValueError, TypeError):
            return default
