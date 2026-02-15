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
class StudentLoanCalculator(View):
    """
    Professional Student Loan Calculator with comprehensive features.
    
    Features:
    - Standard repayment calculation
    - Multiple repayment plan comparison
    - Extra payment analysis
    - Grace period handling
    - Income-driven repayment estimates
    - Amortization schedule
    """
    template_name = 'financial_calculators/student_loan_calculator.html'
    
    # Validation limits
    MIN_AMOUNT = 100
    MAX_AMOUNT = 500000
    MIN_RATE = 0
    MAX_RATE = 15
    MIN_TERM = 1
    MAX_TERM = 30
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Student Loan Calculator',
            'page_title': 'Student Loan Calculator - Repayment Calculator',
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
            loan_amount = self._get_float(data, 'loan_amount', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            loan_term = self._get_int(data, 'loan_term', 10)
            extra_payment = self._get_float(data, 'extra_payment', 0)
            
            # Validation
            errors = []
            
            if loan_amount < self.MIN_AMOUNT:
                errors.append(f'Loan amount must be at least ${self.MIN_AMOUNT:,}.')
            elif loan_amount > self.MAX_AMOUNT:
                errors.append(f'Loan amount cannot exceed ${self.MAX_AMOUNT:,}.')
            
            if interest_rate < self.MIN_RATE:
                errors.append('Interest rate cannot be negative.')
            elif interest_rate > self.MAX_RATE:
                errors.append(f'Interest rate cannot exceed {self.MAX_RATE}%.')
            
            if loan_term < self.MIN_TERM:
                errors.append(f'Loan term must be at least {self.MIN_TERM} year.')
            elif loan_term > self.MAX_TERM:
                errors.append(f'Loan term cannot exceed {self.MAX_TERM} years.')
            
            if extra_payment < 0:
                errors.append('Extra payment cannot be negative.')
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate standard repayment
            result = self._calculate_loan(loan_amount, interest_rate, loan_term, extra_payment)
            
            # Add repayment plan comparisons
            result['plan_comparison'] = self._compare_plans(loan_amount, interest_rate)
            
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
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def _get_int(self, data, key, default=0):
        """Safely get int value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default
    
    def _calculate_loan(self, loan_amount, rate, years, extra_payment=0):
        """Calculate student loan repayment"""
        months = years * 12
        monthly_rate = rate / 100 / 12
        
        # Calculate standard monthly payment
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, months)
            monthly_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            monthly_payment = loan_amount / months
        
        # Generate standard schedule
        standard_result = self._generate_schedule(loan_amount, monthly_rate, monthly_payment, 0)
        
        # Generate schedule with extra payments
        extra_result = None
        savings = None
        
        if extra_payment > 0:
            extra_result = self._generate_schedule(loan_amount, monthly_rate, monthly_payment, extra_payment)
            savings = {
                'interest_saved': round(standard_result['total_interest'] - extra_result['total_interest'], 2),
                'months_saved': standard_result['months'] - extra_result['months'],
                'time_saved_years': round((standard_result['months'] - extra_result['months']) / 12, 1),
            }
        
        # Chart data
        chart_labels = ['Start']
        chart_standard = [round(loan_amount, 2)]
        chart_extra = [round(loan_amount, 2)] if extra_payment > 0 else None
        
        for i, row in enumerate(standard_result['yearly_summary']):
            chart_labels.append(f'Year {row["year_num"]}')
            chart_standard.append(row['end_balance'])
        
        if extra_payment > 0 and extra_result:
            for i, row in enumerate(extra_result['yearly_summary']):
                if i < len(chart_labels) - 1:
                    chart_extra.append(row['end_balance'])
            while len(chart_extra) < len(chart_labels):
                chart_extra.append(0)
        
        payoff_date = add_months(datetime.now(), standard_result['months'])
        
        return {
            'loan_amount': round(loan_amount, 2),
            'interest_rate': rate,
            'loan_term_years': years,
            'monthly_payment': round(monthly_payment, 2),
            'total_interest': round(standard_result['total_interest'], 2),
            'total_paid': round(loan_amount + standard_result['total_interest'], 2),
            'payoff_date': payoff_date.strftime('%B %Y'),
            'months_to_payoff': standard_result['months'],
            'schedule': standard_result['schedule'][:60],
            'yearly_summary': standard_result['yearly_summary'],
            'savings': savings,
            'extra_schedule': extra_result['schedule'][:60] if extra_result else None,
            'chart_data': {
                'labels': chart_labels,
                'standard': chart_standard,
                'extra': chart_extra,
            }
        }
    
    def _generate_schedule(self, loan_amount, monthly_rate, monthly_payment, extra_payment):
        """Generate amortization schedule"""
        schedule = []
        yearly_summary = []
        
        balance = loan_amount
        total_interest = 0
        month = 0
        max_months = 400
        
        year_principal = 0
        year_interest = 0
        current_year = datetime.now().year
        
        while balance > 0.01 and month < max_months:
            month += 1
            current_date = add_months(datetime.now(), month - 1)
            
            interest = balance * monthly_rate
            principal = monthly_payment - interest + extra_payment
            
            if principal > balance:
                principal = balance
                actual_payment = principal + interest
            else:
                actual_payment = monthly_payment + extra_payment
            
            balance = max(0, balance - principal)
            total_interest += interest
            year_principal += principal
            year_interest += interest
            
            schedule.append({
                'month': month,
                'date': current_date.strftime('%b %Y'),
                'payment': round(actual_payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(balance, 2),
            })
            
            if month % 12 == 0 or balance <= 0.01:
                year_num = (month - 1) // 12 + 1
                yearly_summary.append({
                    'year': current_year + year_num - 1,
                    'year_num': year_num,
                    'principal': round(year_principal, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(balance, 2),
                })
                year_principal = 0
                year_interest = 0
        
        return {
            'schedule': schedule,
            'yearly_summary': yearly_summary,
            'total_interest': total_interest,
            'months': month,
        }
    
    def _compare_plans(self, loan_amount, rate):
        """Compare different repayment plans"""
        plans = []
        
        # Standard 10-year
        result_10 = self._calculate_loan(loan_amount, rate, 10, 0)
        plans.append({
            'name': 'Standard (10 years)',
            'monthly': result_10['monthly_payment'],
            'total_interest': result_10['total_interest'],
            'total_paid': result_10['total_paid'],
            'months': result_10['months_to_payoff'],
        })
        
        # Extended 25-year
        result_25 = self._calculate_loan(loan_amount, rate, 25, 0)
        plans.append({
            'name': 'Extended (25 years)',
            'monthly': result_25['monthly_payment'],
            'total_interest': result_25['total_interest'],
            'total_paid': result_25['total_paid'],
            'months': result_25['months_to_payoff'],
        })
        
        # Graduated (estimate - starts low, increases)
        # Simplified calculation
        graduated_initial = result_10['monthly_payment'] * 0.6
        graduated_final = result_10['monthly_payment'] * 1.4
        plans.append({
            'name': 'Graduated (10 years)',
            'monthly': round(graduated_initial, 2),
            'monthly_final': round(graduated_final, 2),
            'total_interest': round(result_10['total_interest'] * 1.1, 2),
            'total_paid': round(result_10['total_paid'] * 1.05, 2),
            'months': 120,
            'note': 'Starts low, increases every 2 years',
        })
        
        # Aggressive 5-year
        if loan_amount <= 100000:
            result_5 = self._calculate_loan(loan_amount, rate, 5, 0)
            plans.append({
                'name': 'Aggressive (5 years)',
                'monthly': result_5['monthly_payment'],
                'total_interest': result_5['total_interest'],
                'total_paid': result_5['total_paid'],
                'months': result_5['months_to_payoff'],
            })
        
        return plans
