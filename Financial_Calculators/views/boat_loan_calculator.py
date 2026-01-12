from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class BoatLoanCalculator(View):
    """
    Class-based view for Boat Loan Calculator
    Calculates boat loan payments including insurance, maintenance, and storage costs.
    """
    template_name = 'financial_calculators/boat_loan_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Boat Loan Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for boat loan calculations"""
        try:
            data = json.loads(request.body)

            # Core loan inputs
            boat_price = float(str(data.get('boat_price', 0)).replace(',', ''))
            down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
            down_payment_type = data.get('down_payment_type', 'amount')  # 'amount' or 'percent'
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            loan_term = int(data.get('loan_term', 60))  # months
            
            # Additional costs
            sales_tax_rate = float(str(data.get('sales_tax_rate', 0)).replace(',', ''))
            registration_fees = float(str(data.get('registration_fees', 0)).replace(',', ''))
            documentation_fees = float(str(data.get('documentation_fees', 0)).replace(',', ''))
            
            # Trade-in
            trade_in_value = float(str(data.get('trade_in_value', 0)).replace(',', ''))
            trade_in_payoff = float(str(data.get('trade_in_payoff', 0)).replace(',', ''))
            
            # Ownership costs (annual)
            annual_insurance = float(str(data.get('annual_insurance', 0)).replace(',', ''))
            annual_maintenance = float(str(data.get('annual_maintenance', 0)).replace(',', ''))
            annual_storage = float(str(data.get('annual_storage', 0)).replace(',', ''))
            annual_fuel = float(str(data.get('annual_fuel', 0)).replace(',', ''))

            # Validation
            if boat_price <= 0:
                return JsonResponse({'success': False, 'error': 'Boat price must be greater than zero.'}, status=400)
            if interest_rate < 0:
                return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)
            if loan_term <= 0:
                return JsonResponse({'success': False, 'error': 'Loan term must be greater than zero.'}, status=400)

            # Calculate down payment
            if down_payment_type == 'percent':
                down_payment_amount = boat_price * (down_payment / 100)
                down_payment_percent = down_payment
            else:
                down_payment_amount = down_payment
                down_payment_percent = (down_payment / boat_price * 100) if boat_price > 0 else 0

            # Calculate sales tax
            sales_tax = boat_price * (sales_tax_rate / 100)

            # Calculate trade-in equity
            trade_in_equity = max(0, trade_in_value - trade_in_payoff)

            # Calculate loan amount
            total_fees = registration_fees + documentation_fees
            loan_amount = boat_price + sales_tax + total_fees - down_payment_amount - trade_in_equity

            if loan_amount <= 0:
                return JsonResponse({
                    'success': True,
                    'message': 'No loan needed - your down payment and trade-in cover the purchase.',
                    'loan_amount': 0,
                    'monthly_payment': 0
                })

            # Calculate monthly payment
            monthly_rate = interest_rate / 100 / 12
            
            if monthly_rate > 0:
                monthly_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
            else:
                monthly_payment = loan_amount / loan_term

            total_payments = monthly_payment * loan_term
            total_interest = total_payments - loan_amount

            # Monthly ownership costs
            monthly_insurance = annual_insurance / 12
            monthly_maintenance = annual_maintenance / 12
            monthly_storage = annual_storage / 12
            monthly_fuel = annual_fuel / 12
            total_monthly_ownership = monthly_insurance + monthly_maintenance + monthly_storage + monthly_fuel
            total_monthly_cost = monthly_payment + total_monthly_ownership

            # Generate amortization schedule
            schedule = []
            balance = loan_amount
            total_interest_paid = 0
            total_principal_paid = 0

            for month in range(1, loan_term + 1):
                interest_payment = balance * monthly_rate
                principal_payment = monthly_payment - interest_payment
                
                if principal_payment > balance:
                    principal_payment = balance
                    interest_payment = balance * monthly_rate
                
                balance -= principal_payment
                total_interest_paid += interest_payment
                total_principal_paid += principal_payment

                if month <= 60 or month % 12 == 0 or month == loan_term:
                    schedule.append({
                        'month': month,
                        'payment': round(monthly_payment, 2),
                        'principal': round(principal_payment, 2),
                        'interest': round(interest_payment, 2),
                        'balance': round(max(0, balance), 2),
                        'total_interest': round(total_interest_paid, 2)
                    })

            # Total cost of ownership over loan term
            years = loan_term / 12
            total_ownership_costs = (annual_insurance + annual_maintenance + annual_storage + annual_fuel) * years
            total_cost_of_ownership = boat_price + sales_tax + total_fees + total_interest + total_ownership_costs

            # Loan comparison for different terms
            comparisons = []
            for term in [36, 48, 60, 72, 84, 120, 180, 240]:
                if term == loan_term:
                    continue
                if monthly_rate > 0:
                    comp_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, term)) / (np.power(1 + monthly_rate, term) - 1)
                else:
                    comp_payment = loan_amount / term
                comp_total = comp_payment * term
                comp_interest = comp_total - loan_amount
                
                comparisons.append({
                    'term_months': term,
                    'term_years': round(term / 12, 1),
                    'monthly_payment': round(comp_payment, 2),
                    'total_interest': round(comp_interest, 2),
                    'total_cost': round(comp_total, 2)
                })

            result = {
                'success': True,
                'input': {
                    'boat_price': round(boat_price, 2),
                    'down_payment': round(down_payment_amount, 2),
                    'down_payment_percent': round(down_payment_percent, 1),
                    'interest_rate': interest_rate,
                    'loan_term': loan_term,
                    'loan_term_years': round(loan_term / 12, 1)
                },
                'loan_details': {
                    'boat_price': round(boat_price, 2),
                    'sales_tax': round(sales_tax, 2),
                    'fees': round(total_fees, 2),
                    'down_payment': round(down_payment_amount, 2),
                    'trade_in_equity': round(trade_in_equity, 2),
                    'loan_amount': round(loan_amount, 2)
                },
                'payment_summary': {
                    'monthly_loan_payment': round(monthly_payment, 2),
                    'monthly_insurance': round(monthly_insurance, 2),
                    'monthly_maintenance': round(monthly_maintenance, 2),
                    'monthly_storage': round(monthly_storage, 2),
                    'monthly_fuel': round(monthly_fuel, 2),
                    'total_monthly_ownership': round(total_monthly_ownership, 2),
                    'total_monthly_cost': round(total_monthly_cost, 2)
                },
                'totals': {
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'total_ownership_costs': round(total_ownership_costs, 2),
                    'total_cost_of_ownership': round(total_cost_of_ownership, 2)
                },
                'schedule': schedule,
                'comparisons': comparisons,
                'chart_data': {
                    'principal': round(loan_amount, 2),
                    'interest': round(total_interest, 2),
                    'taxes_fees': round(sales_tax + total_fees, 2),
                    'ownership': round(total_ownership_costs, 2)
                }
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
