from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from datetime import datetime

# Try to import dateutil, fallback to manual calculation if not available
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
class MortgageCalculator(View):
    """
    Professional Mortgage Calculator with comprehensive features.
    
    Features:
    - Monthly payment calculation with PITI (Principal, Interest, Taxes, Insurance)
    - Property taxes, home insurance, PMI, HOA fees
    - Annual cost increase calculations
    - Extra payments (monthly, yearly, one-time)
    - Biweekly payment option
    - Full amortization schedule with dates
    - Chart data for visualization
    
    Formula used: M = P * [r(1+r)^n] / [(1+r)^n - 1]
    Where:
    - M = Monthly payment
    - P = Principal loan amount
    - r = Monthly interest rate (annual rate / 12)
    - n = Total number of payments
    """
    template_name = 'financial_calculators/mortgage_calculator.html'
    
    def get(self, request):
        """Handle GET request - render the calculator form"""
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        current_month = datetime.now().month
        current_year = datetime.now().year
        years = list(range(current_year, current_year + 31))
        
        context = {
            'calculator_name': 'Mortgage Calculator',
            'page_title': 'Free Mortgage Calculator | Calculate Monthly Payments & Amortization',
            'meta_description': 'Free online mortgage calculator. Calculate monthly mortgage payments, total interest, and view amortization schedule. Includes property tax, insurance, PMI, and extra payment options.',
            'months': months,
            'years': years,
            'current_month': current_month,
            'current_year': current_year,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for mortgage calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Basic inputs with validation
            home_price = self._get_float(data, 'home_price', 0)
            down_payment = self._get_float(data, 'down_payment', 0)
            down_payment_type = data.get('down_payment_type', 'percentage')
            loan_term = self._get_int(data, 'loan_term', 30)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            start_month = self._get_int(data, 'start_month', datetime.now().month)
            start_year = self._get_int(data, 'start_year', datetime.now().year)
            
            # Taxes & Costs
            property_tax = self._get_float(data, 'property_tax', 0)
            property_tax_type = data.get('property_tax_type', 'yearly')
            home_insurance = self._get_float(data, 'home_insurance', 0)
            home_insurance_type = data.get('home_insurance_type', 'yearly')
            pmi_rate = self._get_float(data, 'pmi_rate', 0)
            hoa_fee = self._get_float(data, 'hoa_fee', 0)
            other_costs = self._get_float(data, 'other_costs', 0)
            
            # Annual increases
            property_tax_increase = self._get_float(data, 'property_tax_increase', 0)
            insurance_increase = self._get_float(data, 'insurance_increase', 0)
            hoa_increase = self._get_float(data, 'hoa_increase', 0)
            other_costs_increase = self._get_float(data, 'other_costs_increase', 0)
            
            # Extra payments
            extra_monthly = self._get_float(data, 'extra_monthly', 0)
            extra_yearly = self._get_float(data, 'extra_yearly', 0)
            extra_yearly_month = self._get_int(data, 'extra_yearly_month', 1)
            extra_onetime = self._get_float(data, 'extra_onetime', 0)
            extra_onetime_month = self._get_int(data, 'extra_onetime_month', 1)
            extra_onetime_year = self._get_int(data, 'extra_onetime_year', start_year)
            
            # Show biweekly option
            show_biweekly = data.get('show_biweekly', False)
            if isinstance(show_biweekly, str):
                show_biweekly = show_biweekly.lower() in ('true', '1', 'yes')
            
            # Validation
            errors = self._validate_inputs(home_price, interest_rate, loan_term, down_payment, down_payment_type)
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate down payment amount
            if down_payment_type == 'percentage':
                down_payment_percent = min(down_payment, 99.9)  # Cap at 99.9%
                down_payment_amount = home_price * (down_payment_percent / 100)
            else:
                down_payment_amount = min(down_payment, home_price * 0.999)  # Cap at 99.9% of home price
                down_payment_percent = (down_payment_amount / home_price) * 100 if home_price > 0 else 0
            
            # Calculate loan amount
            loan_amount = home_price - down_payment_amount
            
            if loan_amount <= 0:
                return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)
            
            # Monthly interest rate
            monthly_rate = (interest_rate / 100) / 12
            total_payments = loan_term * 12
            
            # Calculate monthly P&I payment using standard mortgage formula
            if monthly_rate > 0:
                rate_factor = np.power(1 + monthly_rate, total_payments)
                monthly_pi = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
            else:
                monthly_pi = loan_amount / total_payments
            
            # Calculate monthly property tax
            if property_tax_type == 'percentage':
                monthly_property_tax = (home_price * (property_tax / 100)) / 12
            else:
                monthly_property_tax = property_tax / 12
            
            # Calculate monthly insurance
            if home_insurance_type == 'percentage':
                monthly_insurance = (home_price * (home_insurance / 100)) / 12
            else:
                monthly_insurance = home_insurance / 12
            
            # Calculate PMI (if down payment < 20%)
            pmi_monthly = 0
            if down_payment_percent < 20 and pmi_rate > 0:
                pmi_monthly = (loan_amount * (pmi_rate / 100)) / 12
            
            # Total monthly payment (PITI + extras)
            total_monthly = monthly_pi + monthly_property_tax + monthly_insurance + pmi_monthly + hoa_fee + other_costs
            
            # Generate amortization schedule
            amortization = self._generate_amortization_schedule(
                loan_amount=loan_amount,
                monthly_rate=monthly_rate,
                monthly_payment=monthly_pi,
                total_payments=total_payments,
                start_month=start_month,
                start_year=start_year,
                extra_monthly=extra_monthly,
                extra_yearly=extra_yearly,
                extra_yearly_month=extra_yearly_month,
                extra_onetime=extra_onetime,
                extra_onetime_month=extra_onetime_month,
                extra_onetime_year=extra_onetime_year,
                home_price=home_price,
                pmi_rate=pmi_rate,
                down_payment_percent=down_payment_percent,
                monthly_property_tax=monthly_property_tax,
                monthly_insurance=monthly_insurance,
                hoa_fee=hoa_fee,
                other_costs=other_costs,
                property_tax_increase=property_tax_increase,
                insurance_increase=insurance_increase,
                hoa_increase=hoa_increase,
                other_costs_increase=other_costs_increase
            )
            
            # Calculate totals from schedule
            total_interest = sum(p['interest'] for p in amortization['schedule'])
            total_property_tax = sum(p['property_tax'] for p in amortization['schedule'])
            total_insurance = sum(p['insurance'] for p in amortization['schedule'])
            total_pmi = sum(p['pmi'] for p in amortization['schedule'])
            total_hoa = sum(p['hoa'] for p in amortization['schedule'])
            total_other = sum(p['other'] for p in amortization['schedule'])
            total_mortgage_payments = loan_amount + total_interest
            total_all_payments = total_mortgage_payments + total_property_tax + total_insurance + total_pmi + total_hoa + total_other
            
            # Calculate biweekly payments if requested
            biweekly_data = None
            if show_biweekly:
                biweekly_data = self._calculate_biweekly(loan_amount, monthly_rate, monthly_pi, total_payments)
            
            # Payoff date
            last_payment = amortization['schedule'][-1] if amortization['schedule'] else None
            payoff_date = last_payment['date'] if last_payment else 'N/A'
            
            # Chart data
            chart_data = self._prepare_chart_data(amortization['schedule'], amortization['yearly_summary'])
            
            return JsonResponse({
                'success': True,
                'loan_details': {
                    'home_price': round(home_price, 2),
                    'down_payment_amount': round(down_payment_amount, 2),
                    'down_payment_percent': round(down_payment_percent, 2),
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'loan_term_years': loan_term,
                    'total_payments': len(amortization['schedule']),
                    'payoff_date': payoff_date,
                },
                'monthly_payment': {
                    'principal_interest': round(monthly_pi, 2),
                    'property_tax': round(monthly_property_tax, 2),
                    'home_insurance': round(monthly_insurance, 2),
                    'pmi': round(pmi_monthly, 2),
                    'hoa': round(hoa_fee, 2),
                    'other': round(other_costs, 2),
                    'total': round(total_monthly, 2),
                },
                'totals': {
                    'mortgage_payments': round(total_mortgage_payments, 2),
                    'interest': round(total_interest, 2),
                    'property_tax': round(total_property_tax, 2),
                    'insurance': round(total_insurance, 2),
                    'pmi': round(total_pmi, 2),
                    'hoa': round(total_hoa, 2),
                    'other': round(total_other, 2),
                    'all_payments': round(total_all_payments, 2),
                },
                'biweekly': biweekly_data,
                'amortization_schedule': amortization['schedule'],
                'yearly_summary': amortization['yearly_summary'],
                'chart_data': chart_data,
            })
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid input value: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Calculation error. Please check your inputs and try again.'
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
    
    def _validate_inputs(self, home_price, interest_rate, loan_term, down_payment, down_payment_type):
        """Validate input values and return list of errors"""
        errors = []
        
        if home_price <= 0:
            errors.append('Home price must be greater than zero.')
        elif home_price > 100000000:
            errors.append('Home price cannot exceed $100,000,000.')
        
        if interest_rate <= 0:
            errors.append('Interest rate must be greater than zero.')
        elif interest_rate > 30:
            errors.append('Interest rate cannot exceed 30%.')
        
        if loan_term <= 0:
            errors.append('Loan term must be at least 1 year.')
        elif loan_term > 50:
            errors.append('Loan term cannot exceed 50 years.')
        
        if down_payment < 0:
            errors.append('Down payment cannot be negative.')
        
        if down_payment_type == 'percentage' and down_payment >= 100:
            errors.append('Down payment percentage must be less than 100%.')
        
        return errors
    
    def _generate_amortization_schedule(self, loan_amount, monthly_rate, monthly_payment, total_payments,
                                         start_month, start_year, extra_monthly, extra_yearly, extra_yearly_month,
                                         extra_onetime, extra_onetime_month, extra_onetime_year, home_price,
                                         pmi_rate, down_payment_percent, monthly_property_tax, monthly_insurance,
                                         hoa_fee, other_costs, property_tax_increase, insurance_increase,
                                         hoa_increase, other_costs_increase):
        """Generate complete amortization schedule with all costs"""
        schedule = []
        yearly_summary = []
        
        balance = loan_amount
        current_date = datetime(start_year, start_month, 1)
        
        # Track yearly totals
        year_interest = 0
        year_principal = 0
        year_pmi = 0
        year_tax = 0
        year_insurance = 0
        year_hoa = 0
        year_other = 0
        current_year = start_year
        year_start_balance = balance
        
        # Current costs (will increase annually)
        current_property_tax = monthly_property_tax
        current_insurance = monthly_insurance
        current_hoa = hoa_fee
        current_other = other_costs
        
        month_num = 0
        one_time_paid = False
        max_iterations = total_payments + 120  # Safety limit
        
        while balance > 0.01 and month_num < max_iterations:
            month_num += 1
            
            # Apply annual cost increases at start of each new calendar year
            if current_date.month == 1 and month_num > 1:
                current_property_tax *= (1 + property_tax_increase / 100)
                current_insurance *= (1 + insurance_increase / 100)
                current_hoa *= (1 + hoa_increase / 100)
                current_other *= (1 + other_costs_increase / 100)
            
            # Calculate interest for this month
            interest_payment = balance * monthly_rate
            
            # Calculate scheduled principal
            scheduled_principal = monthly_payment - interest_payment
            
            # Add extra payments
            extra_this_month = extra_monthly
            
            # Extra yearly payment
            if current_date.month == extra_yearly_month and extra_yearly > 0:
                extra_this_month += extra_yearly
            
            # One-time payment
            if not one_time_paid and current_date.month == extra_onetime_month and current_date.year == extra_onetime_year and extra_onetime > 0:
                extra_this_month += extra_onetime
                one_time_paid = True
            
            total_principal = scheduled_principal + extra_this_month
            
            # Ensure we don't overpay
            if total_principal > balance:
                total_principal = balance
                extra_this_month = max(0, total_principal - scheduled_principal)
            
            # Update balance
            balance = max(0, balance - total_principal)
            
            # Calculate PMI (drops when LTV reaches 78%)
            current_ltv = (balance / home_price) * 100 if home_price > 0 else 0
            pmi_this_month = 0
            if down_payment_percent < 20 and pmi_rate > 0 and current_ltv > 78:
                pmi_this_month = (loan_amount * (pmi_rate / 100)) / 12
            
            # Add to schedule
            schedule.append({
                'month': month_num,
                'date': current_date.strftime('%b %Y'),
                'payment': round(monthly_payment + extra_this_month, 2),
                'principal': round(scheduled_principal, 2),
                'extra': round(extra_this_month, 2),
                'interest': round(interest_payment, 2),
                'balance': round(balance, 2),
                'property_tax': round(current_property_tax, 2),
                'insurance': round(current_insurance, 2),
                'pmi': round(pmi_this_month, 2),
                'hoa': round(current_hoa, 2),
                'other': round(current_other, 2),
            })
            
            # Track yearly totals
            year_interest += interest_payment
            year_principal += total_principal
            year_pmi += pmi_this_month
            year_tax += current_property_tax
            year_insurance += current_insurance
            year_hoa += current_hoa
            year_other += current_other
            
            # Year end summary (December or final payment)
            if current_date.month == 12 or balance <= 0.01:
                yearly_summary.append({
                    'year': current_year,
                    'principal': round(year_principal, 2),
                    'interest': round(year_interest, 2),
                    'pmi': round(year_pmi, 2),
                    'tax': round(year_tax, 2),
                    'insurance': round(year_insurance, 2),
                    'hoa': round(year_hoa, 2),
                    'other': round(year_other, 2),
                    'start_balance': round(year_start_balance, 2),
                    'end_balance': round(balance, 2),
                })
                # Reset yearly counters
                year_interest = 0
                year_principal = 0
                year_pmi = 0
                year_tax = 0
                year_insurance = 0
                year_hoa = 0
                year_other = 0
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
    
    def _calculate_biweekly(self, loan_amount, monthly_rate, monthly_payment, total_payments):
        """Calculate biweekly payment schedule and savings"""
        biweekly_payment = monthly_payment / 2
        # Biweekly rate approximation
        biweekly_rate = monthly_rate * 12 / 26
        
        balance = loan_amount
        total_interest = 0
        payment_count = 0
        max_payments = total_payments * 3  # Safety limit
        
        while balance > 0.01 and payment_count < max_payments:
            payment_count += 1
            interest = balance * biweekly_rate
            principal = biweekly_payment - interest
            
            if principal > balance:
                principal = balance
            
            balance -= principal
            total_interest += interest
        
        years = payment_count / 26
        months_with_biweekly = int(years * 12)
        months_saved = total_payments - months_with_biweekly
        
        # Calculate interest saved compared to monthly
        monthly_total_interest = (monthly_payment * total_payments) - loan_amount
        interest_saved = monthly_total_interest - total_interest
        
        return {
            'payment': round(biweekly_payment, 2),
            'total_payments': payment_count,
            'total_interest': round(total_interest, 2),
            'interest_saved': round(max(0, interest_saved), 2),
            'time_saved_months': max(0, months_saved),
            'payoff_years': round(years, 1),
        }
    
    def _prepare_chart_data(self, schedule, yearly_summary):
        """Prepare chart data for visualization"""
        balance_data = {
            'labels': [],
            'balance': [],
            'interest': [],
            'principal': [],
        }
        
        cumulative_interest = 0
        cumulative_principal = 0
        
        for year in yearly_summary:
            balance_data['labels'].append(str(year['year']))
            balance_data['balance'].append(year['end_balance'])
            cumulative_interest += year['interest']
            cumulative_principal += year['principal']
            balance_data['interest'].append(round(cumulative_interest, 2))
            balance_data['principal'].append(round(cumulative_principal, 2))
        
        return {
            'balance_data': balance_data,
        }
