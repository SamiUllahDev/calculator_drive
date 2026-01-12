from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class AprCalculator(View):
    """
    Class-based view for APR Calculator
    Calculates Annual Percentage Rate including fees and costs.
    """
    template_name = 'financial_calculators/apr_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'APR Calculator',
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
            
            # Fee inputs
            origination_fee = float(str(data.get('origination_fee', 0)).replace(',', ''))
            discount_points = float(str(data.get('discount_points', 0)).replace(',', ''))
            other_fees = float(str(data.get('other_fees', 0)).replace(',', ''))
            
            # Validation
            if loan_amount <= 0 or loan_amount > 100000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid loan amount (up to $100,000,000).'}, status=400)
            
            if interest_rate <= 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0.01% and 50%.'}, status=400)
            
            if loan_term <= 0 or loan_term > 50:
                return JsonResponse({'success': False, 'error': 'Loan term must be between 1 and 50 years.'}, status=400)
            
            # Calculate total fees
            points_cost = loan_amount * (discount_points / 100)
            total_fees = origination_fee + points_cost + other_fees
            
            # Calculate monthly rate and number of payments
            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term * 12
            
            # Calculate monthly payment based on stated interest rate
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_payment = loan_amount / num_payments
            
            # Calculate APR using Newton-Raphson method
            # Net loan amount = Loan Amount - Total Fees
            net_loan = loan_amount - total_fees
            
            # Initial guess for APR monthly rate
            apr_monthly = monthly_rate
            
            # Newton-Raphson iteration to find APR
            for _ in range(100):
                if apr_monthly <= 0:
                    apr_monthly = 0.001
                
                # Calculate present value of payments at current APR guess
                pv = 0
                dpv = 0  # Derivative
                for i in range(1, num_payments + 1):
                    discount = (1 + apr_monthly) ** i
                    pv += monthly_payment / discount
                    dpv -= i * monthly_payment / ((1 + apr_monthly) ** (i + 1))
                
                # f(apr) = PV - net_loan
                f = pv - net_loan
                
                if abs(f) < 0.01:
                    break
                
                # Newton-Raphson update
                if dpv != 0:
                    apr_monthly = apr_monthly - f / dpv
            
            apr_annual = apr_monthly * 12 * 100
            
            # Ensure APR is reasonable
            apr_annual = max(interest_rate, min(apr_annual, 99.99))
            
            # Calculate total costs
            total_interest = (monthly_payment * num_payments) - loan_amount
            total_cost = total_interest + total_fees
            
            # Cost comparison
            rate_difference = apr_annual - interest_rate
            
            result = {
                'success': True,
                'summary': {
                    'apr': round(apr_annual, 3),
                    'stated_rate': round(interest_rate, 3),
                    'rate_difference': round(rate_difference, 3),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'total_fees': round(total_fees, 2),
                    'total_cost': round(total_cost, 2),
                    'points_cost': round(points_cost, 2),
                    'net_loan': round(net_loan, 2)
                },
                'fee_breakdown': {
                    'origination': round(origination_fee, 2),
                    'points': round(points_cost, 2),
                    'other': round(other_fees, 2),
                    'total': round(total_fees, 2)
                },
                'chart_data': {
                    'cost_breakdown': {
                        'principal': round(loan_amount, 2),
                        'interest': round(total_interest, 2),
                        'fees': round(total_fees, 2)
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
