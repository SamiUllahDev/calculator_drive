from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class RefinanceCalculator(View):
    """
    Class-based view for Mortgage Refinance Calculator
    Calculates refinance savings, break-even point, and compares current vs new loan.
    """
    template_name = 'financial_calculators/refinance_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Refinance Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for refinance calculations"""
        try:
            data = json.loads(request.body)

            # Current loan details
            current_balance = float(str(data.get('current_balance', 0)).replace(',', ''))
            current_rate = float(str(data.get('current_rate', 0)).replace(',', ''))
            current_payment = float(str(data.get('current_payment', 0)).replace(',', ''))
            months_remaining = int(data.get('months_remaining', 0))
            
            # New loan details
            new_rate = float(str(data.get('new_rate', 0)).replace(',', ''))
            new_term = int(data.get('new_term', 360))  # months
            
            # Closing costs
            closing_costs = float(str(data.get('closing_costs', 0)).replace(',', ''))
            points = float(str(data.get('points', 0)).replace(',', ''))  # percentage
            roll_costs_into_loan = data.get('roll_costs_into_loan', False)
            
            # Cash out option
            cash_out = float(str(data.get('cash_out', 0)).replace(',', ''))

            # Validation
            if current_balance <= 0:
                return JsonResponse({'success': False, 'error': 'Current balance must be greater than zero.'}, status=400)
            if months_remaining <= 0:
                return JsonResponse({'success': False, 'error': 'Months remaining must be greater than zero.'}, status=400)
            if new_term <= 0:
                return JsonResponse({'success': False, 'error': 'New loan term must be greater than zero.'}, status=400)

            # Calculate points cost
            points_cost = current_balance * (points / 100)
            total_closing_costs = closing_costs + points_cost

            # New loan amount
            if roll_costs_into_loan:
                new_loan_amount = current_balance + total_closing_costs + cash_out
            else:
                new_loan_amount = current_balance + cash_out

            # Current loan calculations
            current_monthly_rate = current_rate / 100 / 12
            current_total_remaining = current_payment * months_remaining
            
            # Calculate remaining interest on current loan
            balance = current_balance
            current_remaining_interest = 0
            for _ in range(months_remaining):
                interest = balance * current_monthly_rate
                principal = current_payment - interest
                if principal > balance:
                    interest = balance * current_monthly_rate
                    principal = balance
                current_remaining_interest += interest
                balance -= principal
                if balance <= 0:
                    break

            # New loan calculations
            new_monthly_rate = new_rate / 100 / 12
            
            if new_monthly_rate > 0:
                new_payment = new_loan_amount * (new_monthly_rate * np.power(1 + new_monthly_rate, new_term)) / (np.power(1 + new_monthly_rate, new_term) - 1)
            else:
                new_payment = new_loan_amount / new_term

            new_total_payments = new_payment * new_term
            new_total_interest = new_total_payments - new_loan_amount

            # Monthly savings
            monthly_savings = current_payment - new_payment

            # Break-even calculation (months)
            if monthly_savings > 0:
                if roll_costs_into_loan:
                    break_even_months = 0  # No upfront costs
                else:
                    break_even_months = int(np.ceil(total_closing_costs / monthly_savings))
            else:
                break_even_months = -1  # Never breaks even (payment increased)

            # Lifetime savings calculation
            # Compare: remaining cost on current loan vs total cost of new loan + closing costs
            current_total_cost = current_total_remaining
            new_total_cost = new_total_payments + (0 if roll_costs_into_loan else total_closing_costs)
            
            lifetime_savings = current_total_cost - new_total_cost

            # Interest savings
            interest_savings = current_remaining_interest - new_total_interest

            # Generate amortization comparison (first 12 months and yearly)
            current_schedule = []
            new_schedule = []
            
            # Current loan schedule
            balance = current_balance
            for month in range(1, min(months_remaining + 1, 361)):
                interest = balance * current_monthly_rate
                principal = current_payment - interest
                if principal > balance:
                    principal = balance
                balance = max(0, balance - principal)
                
                if month <= 12 or month % 12 == 0:
                    current_schedule.append({
                        'month': month,
                        'payment': round(current_payment, 2),
                        'principal': round(principal, 2),
                        'interest': round(interest, 2),
                        'balance': round(balance, 2)
                    })
            
            # New loan schedule
            balance = new_loan_amount
            for month in range(1, min(new_term + 1, 361)):
                interest = balance * new_monthly_rate
                principal = new_payment - interest
                if principal > balance:
                    principal = balance
                balance = max(0, balance - principal)
                
                if month <= 12 or month % 12 == 0:
                    new_schedule.append({
                        'month': month,
                        'payment': round(new_payment, 2),
                        'principal': round(principal, 2),
                        'interest': round(interest, 2),
                        'balance': round(balance, 2)
                    })

            # Recommendation
            if lifetime_savings > 0 and break_even_months >= 0:
                if break_even_months <= 24:
                    recommendation = "Strongly recommended - quick break-even and significant savings"
                elif break_even_months <= 48:
                    recommendation = "Recommended if you plan to stay in home 4+ years"
                else:
                    recommendation = "Consider carefully - long break-even period"
            elif lifetime_savings > 0:
                recommendation = "May be worth it for lower payments despite higher total cost"
            else:
                recommendation = "Not recommended - refinancing would cost more overall"

            result = {
                'success': True,
                'current_loan': {
                    'balance': round(current_balance, 2),
                    'rate': current_rate,
                    'payment': round(current_payment, 2),
                    'months_remaining': months_remaining,
                    'years_remaining': round(months_remaining / 12, 1),
                    'total_remaining': round(current_total_remaining, 2),
                    'remaining_interest': round(current_remaining_interest, 2)
                },
                'new_loan': {
                    'amount': round(new_loan_amount, 2),
                    'rate': new_rate,
                    'term_months': new_term,
                    'term_years': round(new_term / 12, 1),
                    'payment': round(new_payment, 2),
                    'total_payments': round(new_total_payments, 2),
                    'total_interest': round(new_total_interest, 2)
                },
                'costs': {
                    'closing_costs': round(closing_costs, 2),
                    'points': points,
                    'points_cost': round(points_cost, 2),
                    'total_closing_costs': round(total_closing_costs, 2),
                    'cash_out': round(cash_out, 2),
                    'rolled_into_loan': roll_costs_into_loan
                },
                'savings': {
                    'monthly_savings': round(monthly_savings, 2),
                    'break_even_months': break_even_months,
                    'break_even_years': round(break_even_months / 12, 1) if break_even_months > 0 else 0,
                    'lifetime_savings': round(lifetime_savings, 2),
                    'interest_savings': round(interest_savings, 2)
                },
                'comparison': {
                    'rate_reduction': round(current_rate - new_rate, 2),
                    'payment_change': round(new_payment - current_payment, 2),
                    'term_change_months': new_term - months_remaining
                },
                'recommendation': recommendation,
                'current_schedule': current_schedule[:24],
                'new_schedule': new_schedule[:24]
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
