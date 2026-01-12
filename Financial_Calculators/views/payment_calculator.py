from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class PaymentCalculator(View):
    """
    Class-based view for Payment Calculator
    Calculates monthly loan payments with detailed breakdowns.
    """
    template_name = 'financial_calculators/payment_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Payment Calculator',
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
            term_unit = data.get('term_unit', 'years')
            
            # Validation
            if loan_amount <= 0 or loan_amount > 100000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid loan amount.'}, status=400)
            
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0% and 50%.'}, status=400)
            
            if loan_term <= 0:
                return JsonResponse({'success': False, 'error': 'Loan term must be greater than 0.'}, status=400)
            
            # Convert term to months
            if term_unit == 'years':
                num_payments = loan_term * 12
            else:
                num_payments = loan_term
            
            monthly_rate = (interest_rate / 100) / 12
            
            # Calculate monthly payment
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments
            
            total_payment = monthly_payment * num_payments
            total_interest = total_payment - loan_amount
            
            # Calculate different payment scenarios
            scenarios = []
            for term in [12, 24, 36, 48, 60, 72]:
                if monthly_rate > 0:
                    pmt = loan_amount * (monthly_rate * (1 + monthly_rate) ** term) / ((1 + monthly_rate) ** term - 1)
                else:
                    pmt = loan_amount / term
                total = pmt * term
                scenarios.append({
                    'term_months': term,
                    'term_years': term / 12,
                    'monthly_payment': round(pmt, 2),
                    'total_payment': round(total, 2),
                    'total_interest': round(total - loan_amount, 2)
                })
            
            # Generate first 12 months of schedule
            schedule = []
            balance = loan_amount
            for month in range(1, min(13, num_payments + 1)):
                interest_pmt = balance * monthly_rate
                principal_pmt = monthly_payment - interest_pmt
                balance = max(0, balance - principal_pmt)
                schedule.append({
                    'month': month,
                    'payment': round(monthly_payment, 2),
                    'principal': round(principal_pmt, 2),
                    'interest': round(interest_pmt, 2),
                    'balance': round(balance, 2)
                })
            
            result = {
                'success': True,
                'summary': {
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'loan_term': loan_term,
                    'term_unit': term_unit,
                    'num_payments': num_payments,
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payment': round(total_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'biweekly_payment': round(monthly_payment / 2, 2),
                    'weekly_payment': round(monthly_payment / 4.33, 2)
                },
                'scenarios': scenarios,
                'schedule': schedule,
                'chart_data': {
                    'breakdown': {
                        'principal': round(loan_amount, 2),
                        'interest': round(total_interest, 2)
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
