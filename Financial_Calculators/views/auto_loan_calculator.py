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
class AutoLoanCalculator(View):
    """
    Professional Auto Loan Calculator with comprehensive features.
    
    Features:
    - Vehicle price with trade-in value
    - Sales tax calculation
    - Registration and dealer fees
    - Multiple loan term options
    - Amortization schedule
    - Total cost of ownership analysis
    """
    template_name = 'financial_calculators/auto_loan_calculator.html'
    
    # Validation limits
    MIN_PRICE = 1000
    MAX_PRICE = 10000000
    MIN_RATE = 0
    MAX_RATE = 30
    MIN_TERM = 12
    MAX_TERM = 96
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Auto Loan Calculator',
            'page_title': 'Auto Loan Calculator - Car Payment Calculator',
        }
        return render(request, self.template_name, context)

    def _get_data(self, request):
        """Parse JSON or form POST into a flat dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)
            
            # Get inputs
            vehicle_price = self._get_float(data, 'vehicle_price', 0)
            down_payment = self._get_float(data, 'down_payment', 0)
            trade_in_value = self._get_float(data, 'trade_in_value', 0)
            amount_owed = self._get_float(data, 'amount_owed', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            loan_term = self._get_int(data, 'loan_term', 60)
            sales_tax_rate = self._get_float(data, 'sales_tax_rate', 0)
            fees = self._get_float(data, 'fees', 0)
            include_tax_in_loan = str(data.get('include_tax_in_loan', 'true')).lower() in ('true', '1', 'on', 'yes')
            
            # Validation
            errors = []
            
            if vehicle_price < self.MIN_PRICE:
                errors.append(f'Vehicle price must be at least ${self.MIN_PRICE:,}.')
            elif vehicle_price > self.MAX_PRICE:
                errors.append(f'Vehicle price cannot exceed ${self.MAX_PRICE:,}.')
            
            if down_payment < 0:
                errors.append('Down payment cannot be negative.')
            elif down_payment >= vehicle_price:
                errors.append('Down payment must be less than vehicle price.')
            
            if trade_in_value < 0:
                errors.append('Trade-in value cannot be negative.')
            
            if amount_owed < 0:
                errors.append('Amount owed on trade cannot be negative.')
            elif amount_owed > trade_in_value:
                errors.append('Amount owed cannot exceed trade-in value (negative equity will be added to loan).')
            
            if interest_rate < self.MIN_RATE:
                errors.append('Interest rate cannot be negative.')
            elif interest_rate > self.MAX_RATE:
                errors.append(f'Interest rate cannot exceed {self.MAX_RATE}%.')
            
            if loan_term < self.MIN_TERM:
                errors.append(f'Loan term must be at least {self.MIN_TERM} months.')
            elif loan_term > self.MAX_TERM:
                errors.append(f'Loan term cannot exceed {self.MAX_TERM} months.')
            
            if sales_tax_rate < 0 or sales_tax_rate > 20:
                errors.append('Sales tax rate must be between 0% and 20%.')
            
            if fees < 0:
                errors.append('Fees cannot be negative.')
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate loan details
            result = self._calculate_auto_loan(
                vehicle_price,
                down_payment,
                trade_in_value,
                amount_owed,
                interest_rate,
                loan_term,
                sales_tax_rate,
                fees,
                include_tax_in_loan
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
    
    def _calculate_auto_loan(self, vehicle_price, down_payment, trade_in_value, 
                              amount_owed, interest_rate, loan_term, sales_tax_rate,
                              fees, include_tax_in_loan):
        """Calculate auto loan details"""
        
        # Calculate trade-in equity
        trade_in_equity = trade_in_value - amount_owed
        
        # Calculate taxable amount (varies by state - simplified)
        # Some states tax the difference after trade-in
        taxable_amount = vehicle_price - trade_in_value if trade_in_value > 0 else vehicle_price
        taxable_amount = max(0, taxable_amount)
        
        # Calculate sales tax
        sales_tax = taxable_amount * (sales_tax_rate / 100)
        
        # Calculate total price
        total_price = vehicle_price + sales_tax + fees
        
        # Calculate upfront costs and loan amount
        upfront_payment = down_payment + trade_in_equity
        
        if include_tax_in_loan:
            loan_amount = total_price - upfront_payment
        else:
            loan_amount = vehicle_price + fees - upfront_payment
        
        loan_amount = max(0, loan_amount)
        
        # Calculate monthly payment
        monthly_rate = (interest_rate / 100) / 12
        
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, loan_term)
            monthly_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            monthly_payment = loan_amount / loan_term if loan_term > 0 else 0
        
        # Generate amortization schedule
        schedule = []
        balance = loan_amount
        total_interest = 0
        total_principal = 0
        
        yearly_summary = []
        current_year = datetime.now().year
        year_principal = 0
        year_interest = 0
        
        chart_labels = ['Start']
        chart_balance = [round(loan_amount, 2)]
        
        for month in range(1, loan_term + 1):
            current_date = add_months(datetime.now(), month - 1)
            
            interest = balance * monthly_rate
            principal = monthly_payment - interest
            
            # Last payment adjustment
            if month == loan_term or principal > balance:
                principal = balance
                payment = principal + interest
            else:
                payment = monthly_payment
            
            balance = max(0, balance - principal)
            total_interest += interest
            total_principal += principal
            year_principal += principal
            year_interest += interest
            
            schedule.append({
                'month': month,
                'date': current_date.strftime('%b %Y'),
                'payment': round(payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(balance, 2),
            })
            
            # Year end summary
            if month % 12 == 0 or month == loan_term:
                year_num = (month - 1) // 12 + 1
                yearly_summary.append({
                    'year': current_year + year_num - 1,
                    'year_num': year_num,
                    'principal': round(year_principal, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(balance, 2),
                })
                chart_labels.append(f'Year {year_num}')
                chart_balance.append(round(balance, 2))
                year_principal = 0
                year_interest = 0
        
        # Total costs
        total_of_payments = monthly_payment * loan_term
        total_cost = total_of_payments + down_payment + trade_in_equity
        
        if not include_tax_in_loan:
            total_cost += sales_tax
        
        # Payoff date
        payoff_date = add_months(datetime.now(), loan_term)
        
        # Compare different terms
        term_comparison = []
        for term in [36, 48, 60, 72, 84]:
            if term != loan_term:
                comp_payment, comp_total = self._quick_calc(loan_amount, interest_rate, term)
                term_comparison.append({
                    'term': term,
                    'monthly': round(comp_payment, 2),
                    'total_interest': round(comp_total - loan_amount, 2),
                })
        
        return {
            'loan_details': {
                'vehicle_price': round(vehicle_price, 2),
                'down_payment': round(down_payment, 2),
                'trade_in_value': round(trade_in_value, 2),
                'trade_in_equity': round(trade_in_equity, 2),
                'sales_tax': round(sales_tax, 2),
                'fees': round(fees, 2),
                'loan_amount': round(loan_amount, 2),
            },
            'payment': {
                'monthly': round(monthly_payment, 2),
                'total_interest': round(total_interest, 2),
                'total_of_payments': round(total_of_payments, 2),
                'total_cost': round(total_cost, 2),
            },
            'schedule': schedule[:60],  # First 5 years
            'yearly_summary': yearly_summary,
            'term_comparison': term_comparison,
            'payoff_date': payoff_date.strftime('%B %Y'),
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
                'breakdown': {
                    'principal': round(loan_amount, 2),
                    'interest': round(total_interest, 2),
                }
            }
        }
    
    def _quick_calc(self, loan_amount, interest_rate, term):
        """Quick calculation for comparison"""
        monthly_rate = (interest_rate / 100) / 12
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, term)
            payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            payment = loan_amount / term if term > 0 else 0
        total = payment * term
        return payment, total
