from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta


class DebtPayoffCalculator(View):
    """
    Class-based view for Debt Payoff Calculator
    Calculates time and interest to pay off debt with various strategies.
    """
    template_name = 'financial_calculators/debt_payoff_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Debt Payoff Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            debt_amount = float(str(data.get('debt_amount', 0)).replace(',', ''))
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            monthly_payment = float(str(data.get('monthly_payment', 0)).replace(',', ''))
            extra_payment = float(str(data.get('extra_payment', 0)).replace(',', ''))
            
            # Validation
            if debt_amount <= 0 or debt_amount > 10000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid debt amount.'}, status=400)
            
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0% and 50%.'}, status=400)
            
            if monthly_payment <= 0:
                return JsonResponse({'success': False, 'error': 'Monthly payment must be greater than 0.'}, status=400)
            
            monthly_rate = (interest_rate / 100) / 12
            
            # Check if payment covers interest
            first_month_interest = debt_amount * monthly_rate
            if monthly_payment <= first_month_interest:
                return JsonResponse({
                    'success': False, 
                    'error': f'Payment (${monthly_payment:,.2f}) must exceed monthly interest (${first_month_interest:,.2f}).'
                }, status=400)
            
            # Calculate without extra payment
            def calculate_payoff(balance, payment, rate):
                months = 0
                total_interest = 0
                schedule = []
                start_date = datetime.now()
                
                while balance > 0.01 and months < 600:  # Max 50 years
                    months += 1
                    interest = balance * rate
                    principal = min(payment - interest, balance)
                    balance = max(0, balance - principal)
                    total_interest += interest
                    
                    if months <= 60:  # First 5 years for schedule
                        current_date = start_date + relativedelta(months=months)
                        schedule.append({
                            'month': months,
                            'date': current_date.strftime('%b %Y'),
                            'payment': round(principal + interest, 2),
                            'principal': round(principal, 2),
                            'interest': round(interest, 2),
                            'balance': round(balance, 2)
                        })
                
                return months, total_interest, schedule
            
            # Standard payoff
            std_months, std_interest, std_schedule = calculate_payoff(
                debt_amount, monthly_payment, monthly_rate
            )
            
            # Accelerated payoff with extra payment
            total_payment = monthly_payment + extra_payment
            acc_months, acc_interest, acc_schedule = calculate_payoff(
                debt_amount, total_payment, monthly_rate
            )
            
            # Calculate savings
            time_saved = std_months - acc_months
            interest_saved = std_interest - acc_interest
            
            # Different payment scenarios
            scenarios = []
            for extra in [0, 50, 100, 200, 300, 500]:
                m, i, _ = calculate_payoff(debt_amount, monthly_payment + extra, monthly_rate)
                scenarios.append({
                    'extra': extra,
                    'total_payment': monthly_payment + extra,
                    'months': m,
                    'years': round(m / 12, 1),
                    'total_interest': round(i, 2),
                    'interest_saved': round(std_interest - i, 2)
                })
            
            # Payoff date
            payoff_date = datetime.now() + relativedelta(months=acc_months)
            
            result = {
                'success': True,
                'summary': {
                    'debt_amount': round(debt_amount, 2),
                    'interest_rate': round(interest_rate, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'extra_payment': round(extra_payment, 2),
                    'total_payment': round(total_payment, 2),
                    'payoff_months': acc_months,
                    'payoff_years': round(acc_months / 12, 1),
                    'payoff_date': payoff_date.strftime('%B %Y'),
                    'total_interest': round(acc_interest, 2),
                    'total_paid': round(debt_amount + acc_interest, 2),
                    'time_saved': time_saved,
                    'interest_saved': round(interest_saved, 2)
                },
                'comparison': {
                    'standard': {
                        'months': std_months,
                        'interest': round(std_interest, 2)
                    },
                    'accelerated': {
                        'months': acc_months,
                        'interest': round(acc_interest, 2)
                    }
                },
                'scenarios': scenarios,
                'schedule': acc_schedule[:36],
                'chart_data': {
                    'breakdown': {
                        'principal': round(debt_amount, 2),
                        'interest': round(acc_interest, 2)
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
