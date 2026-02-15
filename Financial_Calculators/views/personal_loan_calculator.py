from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from datetime import datetime


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PersonalLoanCalculator(View):
    """
    Class-based view for Personal Loan Calculator
    Calculates monthly payments, total interest, and amortization for personal loans.
    """
    template_name = 'financial_calculators/personal_loan_calculator.html'

    def _get_data(self, request):
        """Parse JSON or form POST into a flat dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float from data."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def _get_int(self, data, key, default=0):
        """Safely get int from data."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Personal Loan Calculator',
            'page_title': 'Personal Loan Calculator - Calculate Monthly Payments',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for personal loan calculations (JSON or form)."""
        try:
            data = self._get_data(request)
            
            calc_type = data.get('calc_type', 'calculate_payment')
            
            if calc_type == 'calculate_payment':
                loan_amount = self._get_float(data, 'loan_amount', 0)
                interest_rate = self._get_float(data, 'interest_rate', 0)
                loan_term = self._get_int(data, 'loan_term', 36)
                origination_fee = self._get_float(data, 'origination_fee', 0)
                
                # Validation
                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)
                if interest_rate < 0:
                    return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)
                if loan_term < 1 or loan_term > 120:
                    return JsonResponse({'success': False, 'error': 'Loan term must be between 1 and 120 months.'}, status=400)
                
                # Calculate origination fee
                fee_amount = loan_amount * (origination_fee / 100)
                net_loan_amount = loan_amount - fee_amount
                
                # Calculate monthly payment
                monthly_rate = interest_rate / 100 / 12
                
                if monthly_rate > 0:
                    rate_factor = np.power(1 + monthly_rate, loan_term)
                    monthly_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
                else:
                    monthly_payment = loan_amount / loan_term
                
                # Calculate totals
                total_payments = monthly_payment * loan_term
                total_interest = total_payments - loan_amount
                total_cost = total_interest + fee_amount
                
                # Calculate APR (including origination fee)
                if fee_amount > 0:
                    # Approximate APR calculation
                    apr = ((total_cost / net_loan_amount) / (loan_term / 12)) * 100
                else:
                    apr = interest_rate
                
                # Generate amortization schedule
                schedule = []
                balance = loan_amount
                total_principal_paid = 0
                total_interest_paid = 0
                
                for month in range(1, min(loan_term + 1, 61)):  # First 60 months
                    interest_payment = balance * monthly_rate
                    principal_payment = monthly_payment - interest_payment
                    
                    if principal_payment > balance:
                        principal_payment = balance
                    
                    balance = max(0, balance - principal_payment)
                    total_principal_paid += principal_payment
                    total_interest_paid += interest_payment
                    
                    schedule.append({
                        'month': month,
                        'payment': round(monthly_payment, 2),
                        'principal': round(principal_payment, 2),
                        'interest': round(interest_payment, 2),
                        'balance': round(balance, 2),
                        'total_interest': round(total_interest_paid, 2)
                    })
                
                # Yearly summary
                yearly_summary = []
                for year in range(1, (loan_term // 12) + 2):
                    start_idx = (year - 1) * 12
                    end_idx = min(year * 12, loan_term)
                    if start_idx >= loan_term:
                        break
                    
                    year_payments = schedule[start_idx:end_idx] if end_idx <= len(schedule) else schedule[start_idx:]
                    if year_payments:
                        year_principal = sum(p['principal'] for p in year_payments)
                        year_interest = sum(p['interest'] for p in year_payments)
                        yearly_summary.append({
                            'year': year,
                            'principal': round(year_principal, 2),
                            'interest': round(year_interest, 2),
                            'end_balance': round(year_payments[-1]['balance'], 2) if year_payments else 0
                        })
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_details': {
                        'loan_amount': round(loan_amount, 2),
                        'interest_rate': interest_rate,
                        'loan_term': loan_term,
                        'origination_fee_percent': origination_fee,
                        'origination_fee_amount': round(fee_amount, 2),
                        'net_proceeds': round(net_loan_amount, 2)
                    },
                    'payment': {
                        'monthly': round(monthly_payment, 2),
                        'total_payments': round(total_payments, 2),
                        'total_interest': round(total_interest, 2),
                        'total_cost': round(total_cost, 2),
                        'apr': round(apr, 2)
                    },
                    'schedule': schedule,
                    'yearly_summary': yearly_summary
                }
                
            elif calc_type == 'calculate_affordability':
                desired_payment = self._get_float(data, 'desired_payment', 0)
                interest_rate = self._get_float(data, 'interest_rate', 0)
                loan_term = self._get_int(data, 'loan_term', 36)
                
                if desired_payment <= 0:
                    return JsonResponse({'success': False, 'error': 'Desired payment must be greater than zero.'}, status=400)
                
                monthly_rate = interest_rate / 100 / 12
                
                if monthly_rate > 0:
                    rate_factor = np.power(1 + monthly_rate, loan_term)
                    max_loan = desired_payment * (rate_factor - 1) / (monthly_rate * rate_factor)
                else:
                    max_loan = desired_payment * loan_term
                
                total_payments = desired_payment * loan_term
                total_interest = total_payments - max_loan
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'desired_payment': round(desired_payment, 2),
                    'interest_rate': interest_rate,
                    'loan_term': loan_term,
                    'max_loan_amount': round(max_loan, 2),
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2)
                }
                
            elif calc_type == 'compare_terms':
                loan_amount = self._get_float(data, 'loan_amount', 0)
                interest_rate = self._get_float(data, 'interest_rate', 0)
                
                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)
                
                monthly_rate = interest_rate / 100 / 12
                terms = [12, 24, 36, 48, 60, 72, 84]
                
                comparisons = []
                for term in terms:
                    if monthly_rate > 0:
                        rate_factor = np.power(1 + monthly_rate, term)
                        payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
                    else:
                        payment = loan_amount / term
                    
                    total = payment * term
                    interest = total - loan_amount
                    
                    comparisons.append({
                        'term_months': term,
                        'term_years': round(term / 12, 1),
                        'monthly_payment': round(payment, 2),
                        'total_payments': round(total, 2),
                        'total_interest': round(interest, 2)
                    })
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': interest_rate,
                    'comparisons': comparisons
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
