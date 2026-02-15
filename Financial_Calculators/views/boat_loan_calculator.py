from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BoatLoanCalculator(View):
    """
    Class-based view for Boat Loan Calculator
    Calculates boat loan payments including insurance, maintenance, and storage costs.
    """
    template_name = 'financial_calculators/boat_loan_calculator.html'

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
            'calculator_name': 'Boat Loan Calculator',
            'page_title': 'Boat Loan Calculator - Calculate Marine Financing Payments',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for boat loan calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            boat_price = self._get_float(data, 'boat_price', 0)
            down_payment = self._get_float(data, 'down_payment', 0)
            down_payment_type = data.get('down_payment_type', 'amount')
            if isinstance(down_payment_type, list):
                down_payment_type = down_payment_type[0] if down_payment_type else 'amount'
            interest_rate = self._get_float(data, 'interest_rate', 0)
            loan_term = self._get_int(data, 'loan_term', 60)

            sales_tax_rate = self._get_float(data, 'sales_tax_rate', 0)
            registration_fees = self._get_float(data, 'registration_fees', 0)
            documentation_fees = self._get_float(data, 'documentation_fees', 0)

            trade_in_value = self._get_float(data, 'trade_in_value', 0)
            trade_in_payoff = self._get_float(data, 'trade_in_payoff', 0)

            annual_insurance = self._get_float(data, 'annual_insurance', 0)
            annual_maintenance = self._get_float(data, 'annual_maintenance', 0)
            annual_storage = self._get_float(data, 'annual_storage', 0)
            annual_fuel = self._get_float(data, 'annual_fuel', 0)

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
