from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class AmortizationCalculator(View):
    """
    Class-based view for Amortization Calculator
    Generates complete loan amortization schedules with payment breakdowns.
    """
    template_name = 'financial_calculators/amortization_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Amortization Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            loan_term = int(data.get('loan_term', 0))
            start_month = int(data.get('start_month', 1))
            start_year = int(data.get('start_year', 2025))
            extra_payment = float(str(data.get('extra_payment', 0)).replace(',', ''))
            
            # Validation
            if loan_amount <= 0 or loan_amount > 100000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid loan amount (up to $100,000,000).'}, status=400)
            
            if interest_rate <= 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0.01% and 50%.'}, status=400)
            
            if loan_term <= 0 or loan_term > 50:
                return JsonResponse({'success': False, 'error': 'Loan term must be between 1 and 50 years.'}, status=400)
            
            if extra_payment < 0:
                return JsonResponse({'success': False, 'error': 'Extra payment cannot be negative.'}, status=400)
            
            # Calculate monthly rate and number of payments
            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term * 12
            
            # Calculate standard monthly payment (without extra)
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments
            
            total_payment_with_extra = monthly_payment + extra_payment
            
            # Generate amortization schedule
            schedule = []
            balance = loan_amount
            total_interest = 0
            total_principal = 0
            month_count = 0
            current_year = start_year
            current_month = start_month
            
            year_summary = {}
            
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            
            while balance > 0.01 and month_count < num_payments * 2:  # Safety limit
                month_count += 1
                interest_payment = balance * monthly_rate
                
                # Calculate principal payment
                principal_payment = min(monthly_payment - interest_payment + extra_payment, balance)
                actual_payment = principal_payment + interest_payment
                
                balance = max(0, balance - principal_payment)
                
                total_interest += interest_payment
                total_principal += principal_payment
                
                # Track yearly summary
                if current_year not in year_summary:
                    year_summary[current_year] = {
                        'year': current_year,
                        'principal': 0,
                        'interest': 0,
                        'total_payment': 0,
                        'ending_balance': 0
                    }
                
                year_summary[current_year]['principal'] += principal_payment
                year_summary[current_year]['interest'] += interest_payment
                year_summary[current_year]['total_payment'] += actual_payment
                year_summary[current_year]['ending_balance'] = balance
                
                schedule.append({
                    'payment_number': month_count,
                    'month': months[current_month - 1],
                    'year': current_year,
                    'date': f"{months[current_month - 1]} {current_year}",
                    'payment': round(actual_payment, 2),
                    'principal': round(principal_payment, 2),
                    'interest': round(interest_payment, 2),
                    'balance': round(balance, 2)
                })
                
                # Move to next month
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            
            # Calculate savings with extra payments
            original_total_interest = 0
            if extra_payment > 0 and monthly_rate > 0:
                # Calculate original total interest without extra payments
                original_balance = loan_amount
                for _ in range(num_payments):
                    int_pmt = original_balance * monthly_rate
                    prin_pmt = monthly_payment - int_pmt
                    original_total_interest += int_pmt
                    original_balance -= prin_pmt
            
            interest_savings = original_total_interest - total_interest if extra_payment > 0 else 0
            time_savings_months = num_payments - month_count if extra_payment > 0 else 0
            
            # Prepare yearly summary list
            yearly_data = list(year_summary.values())
            for item in yearly_data:
                item['principal'] = round(item['principal'], 2)
                item['interest'] = round(item['interest'], 2)
                item['total_payment'] = round(item['total_payment'], 2)
                item['ending_balance'] = round(item['ending_balance'], 2)
            
            # Chart data
            chart_data = {
                'principal_interest': {
                    'principal': round(total_principal, 2),
                    'interest': round(total_interest, 2)
                },
                'balance_over_time': {
                    'labels': [f"Yr {i+1}" for i in range(len(yearly_data))],
                    'balances': [y['ending_balance'] for y in yearly_data]
                }
            }
            
            result = {
                'success': True,
                'summary': {
                    'loan_amount': round(loan_amount, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payment': round(total_principal + total_interest, 2),
                    'total_interest': round(total_interest, 2),
                    'total_payments': month_count,
                    'payoff_date': f"{months[current_month - 2 if current_month > 1 else 11]} {current_year if current_month > 1 else current_year - 1}",
                    'interest_savings': round(interest_savings, 2),
                    'time_savings_months': time_savings_months,
                    'extra_payment': round(extra_payment, 2)
                },
                'schedule': schedule[:120],  # First 10 years for display
                'yearly_summary': yearly_data,
                'full_schedule_length': len(schedule),
                'chart_data': chart_data
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
