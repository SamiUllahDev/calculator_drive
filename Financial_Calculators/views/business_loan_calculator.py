from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class BusinessLoanCalculator(View):
    """
    Class-based view for Business Loan Calculator
    Calculates business loan payments with support for different loan types (term, SBA, line of credit).
    """
    template_name = 'financial_calculators/business_loan_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Business Loan Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for business loan calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'term_loan')

            if calc_type == 'term_loan':
                # Standard term loan calculation
                loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
                interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
                loan_term = int(data.get('loan_term', 60))  # months
                origination_fee_percent = float(str(data.get('origination_fee', 0)).replace(',', ''))
                payment_frequency = data.get('payment_frequency', 'monthly')

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)
                if interest_rate < 0:
                    return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)
                if loan_term <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan term must be greater than zero.'}, status=400)

                # Calculate origination fee
                origination_fee = loan_amount * (origination_fee_percent / 100)
                net_loan_proceeds = loan_amount - origination_fee

                # Calculate payment based on frequency
                if payment_frequency == 'weekly':
                    periods_per_year = 52
                elif payment_frequency == 'biweekly':
                    periods_per_year = 26
                else:  # monthly
                    periods_per_year = 12

                total_periods = int(loan_term * periods_per_year / 12)
                periodic_rate = interest_rate / 100 / periods_per_year

                if periodic_rate > 0:
                    periodic_payment = loan_amount * (periodic_rate * np.power(1 + periodic_rate, total_periods)) / (np.power(1 + periodic_rate, total_periods) - 1)
                else:
                    periodic_payment = loan_amount / total_periods

                total_payments = periodic_payment * total_periods
                total_interest = total_payments - loan_amount
                total_cost = total_payments + origination_fee

                # Calculate APR including fees
                apr = interest_rate
                if origination_fee > 0:
                    # Simplified APR calculation
                    apr = (total_interest + origination_fee) / loan_amount / (loan_term / 12) * 100

                # Generate amortization schedule (monthly view)
                schedule = []
                balance = loan_amount
                monthly_rate = interest_rate / 100 / 12
                monthly_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1) if monthly_rate > 0 else loan_amount / loan_term
                
                total_interest_paid = 0
                for month in range(1, loan_term + 1):
                    interest_payment = balance * monthly_rate
                    principal_payment = monthly_payment - interest_payment
                    balance = max(0, balance - principal_payment)
                    total_interest_paid += interest_payment

                    if month <= 24 or month % 12 == 0 or month == loan_term:
                        schedule.append({
                            'month': month,
                            'payment': round(monthly_payment, 2),
                            'principal': round(principal_payment, 2),
                            'interest': round(interest_payment, 2),
                            'balance': round(balance, 2),
                            'total_interest': round(total_interest_paid, 2)
                        })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': interest_rate,
                    'loan_term_months': loan_term,
                    'loan_term_years': round(loan_term / 12, 1),
                    'payment_frequency': payment_frequency,
                    'origination_fee': round(origination_fee, 2),
                    'origination_fee_percent': origination_fee_percent,
                    'net_loan_proceeds': round(net_loan_proceeds, 2),
                    'periodic_payment': round(periodic_payment, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'total_cost': round(total_cost, 2),
                    'apr': round(apr, 2),
                    'schedule': schedule
                }

            elif calc_type == 'sba_loan':
                # SBA Loan calculation (7(a) loan)
                loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
                interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
                loan_term = int(data.get('loan_term', 120))  # months (SBA loans can go up to 25 years)
                guarantee_fee_percent = float(str(data.get('guarantee_fee', 2.0)).replace(',', ''))
                
                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)

                # SBA guarantee fee structure (simplified)
                if loan_amount <= 150000:
                    guarantee_fee_percent = 2.0
                elif loan_amount <= 700000:
                    guarantee_fee_percent = 3.0
                else:
                    guarantee_fee_percent = 3.5

                guarantee_fee = loan_amount * 0.75 * (guarantee_fee_percent / 100)  # SBA guarantees up to 75%

                monthly_rate = interest_rate / 100 / 12
                if monthly_rate > 0:
                    monthly_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    monthly_payment = loan_amount / loan_term

                total_payments = monthly_payment * loan_term
                total_interest = total_payments - loan_amount
                total_cost = total_payments + guarantee_fee

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_type': 'SBA 7(a) Loan',
                    'loan_amount': round(loan_amount, 2),
                    'interest_rate': interest_rate,
                    'loan_term_months': loan_term,
                    'loan_term_years': round(loan_term / 12, 1),
                    'guarantee_fee_percent': guarantee_fee_percent,
                    'guarantee_fee': round(guarantee_fee, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'total_cost': round(total_cost, 2),
                    'sba_guarantee': '75%',
                    'notes': [
                        'SBA 7(a) loans are partially guaranteed by the SBA.',
                        'Maximum loan amount is $5 million.',
                        'Terms up to 25 years for real estate, 10 years for equipment.'
                    ]
                }

            elif calc_type == 'line_of_credit':
                # Business line of credit
                credit_limit = float(str(data.get('credit_limit', 0)).replace(',', ''))
                current_balance = float(str(data.get('current_balance', 0)).replace(',', ''))
                interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
                monthly_payment = float(str(data.get('monthly_payment', 0)).replace(',', ''))
                annual_fee = float(str(data.get('annual_fee', 0)).replace(',', ''))
                draw_fee_percent = float(str(data.get('draw_fee', 0)).replace(',', ''))

                if credit_limit <= 0:
                    return JsonResponse({'success': False, 'error': 'Credit limit must be greater than zero.'}, status=400)
                if current_balance < 0:
                    return JsonResponse({'success': False, 'error': 'Balance cannot be negative.'}, status=400)
                if monthly_payment <= 0:
                    return JsonResponse({'success': False, 'error': 'Monthly payment must be greater than zero.'}, status=400)

                available_credit = credit_limit - current_balance
                utilization = (current_balance / credit_limit * 100) if credit_limit > 0 else 0

                # Calculate payoff time
                monthly_rate = interest_rate / 100 / 12
                months_to_payoff = 0
                total_interest = 0
                balance = current_balance

                while balance > 0 and months_to_payoff < 360:
                    interest = balance * monthly_rate
                    principal = monthly_payment - interest
                    if principal <= 0:
                        return JsonResponse({'success': False, 'error': 'Payment too low to cover interest.'}, status=400)
                    balance -= principal
                    total_interest += interest
                    months_to_payoff += 1

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'credit_limit': round(credit_limit, 2),
                    'current_balance': round(current_balance, 2),
                    'available_credit': round(available_credit, 2),
                    'utilization': round(utilization, 1),
                    'interest_rate': interest_rate,
                    'monthly_payment': round(monthly_payment, 2),
                    'months_to_payoff': months_to_payoff,
                    'years_to_payoff': round(months_to_payoff / 12, 1),
                    'total_interest': round(total_interest, 2),
                    'total_cost': round(current_balance + total_interest, 2),
                    'annual_fee': round(annual_fee, 2),
                    'draw_fee_percent': draw_fee_percent
                }

            elif calc_type == 'compare_options':
                # Compare multiple loan options
                loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
                
                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)

                # Define common loan scenarios
                scenarios = [
                    {'name': 'Bank Term Loan (5 yr)', 'rate': 8.0, 'term': 60, 'fee': 1.0},
                    {'name': 'Bank Term Loan (7 yr)', 'rate': 8.5, 'term': 84, 'fee': 1.0},
                    {'name': 'SBA 7(a) Loan (10 yr)', 'rate': 7.5, 'term': 120, 'fee': 2.5},
                    {'name': 'Online Lender (3 yr)', 'rate': 15.0, 'term': 36, 'fee': 3.0},
                    {'name': 'Equipment Financing (5 yr)', 'rate': 9.0, 'term': 60, 'fee': 0.5},
                ]

                comparisons = []
                for scenario in scenarios:
                    rate = scenario['rate']
                    term = scenario['term']
                    fee_percent = scenario['fee']
                    
                    monthly_rate = rate / 100 / 12
                    if monthly_rate > 0:
                        payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, term)) / (np.power(1 + monthly_rate, term) - 1)
                    else:
                        payment = loan_amount / term
                    
                    total = payment * term
                    interest = total - loan_amount
                    fee = loan_amount * (fee_percent / 100)
                    
                    comparisons.append({
                        'name': scenario['name'],
                        'rate': rate,
                        'term_months': term,
                        'term_years': round(term / 12, 1),
                        'monthly_payment': round(payment, 2),
                        'total_interest': round(interest, 2),
                        'fees': round(fee, 2),
                        'total_cost': round(total + fee, 2)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_amount': round(loan_amount, 2),
                    'comparisons': comparisons
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
