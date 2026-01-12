from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class CanadianMortgageCalculator(View):
    """
    Class-based view for Canadian Mortgage Calculator
    Calculates mortgage payments using Canadian semi-annual compounding.
    """
    template_name = 'financial_calculators/canadian_mortgage_calculator.html'

    # CMHC Insurance rates (for down payments less than 20%)
    CMHC_RATES = {
        5: 4.00,    # 5-9.99% down
        10: 3.10,   # 10-14.99% down
        15: 2.80,   # 15-19.99% down
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Canadian Mortgage Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for Canadian mortgage calculations"""
        try:
            data = json.loads(request.body)

            # Property details
            home_price = float(str(data.get('home_price', 0)).replace(',', ''))
            down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
            down_payment_type = data.get('down_payment_type', 'percent')
            
            # Loan details
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            amortization_period = int(data.get('amortization_period', 25))  # years
            mortgage_term = int(data.get('mortgage_term', 5))  # years (renewal period)
            payment_frequency = data.get('payment_frequency', 'monthly')
            
            # Additional costs
            property_tax_annual = float(str(data.get('property_tax', 0)).replace(',', ''))
            home_insurance_annual = float(str(data.get('home_insurance', 0)).replace(',', ''))
            condo_fees_monthly = float(str(data.get('condo_fees', 0)).replace(',', ''))

            # Validation
            if home_price <= 0:
                return JsonResponse({'success': False, 'error': 'Home price must be greater than zero.'}, status=400)
            if interest_rate < 0:
                return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)
            if amortization_period <= 0 or amortization_period > 30:
                return JsonResponse({'success': False, 'error': 'Amortization must be between 1 and 30 years.'}, status=400)

            # Calculate down payment
            if down_payment_type == 'percent':
                down_payment_percent = down_payment
                down_payment_amount = home_price * (down_payment / 100)
            else:
                down_payment_amount = down_payment
                down_payment_percent = (down_payment / home_price * 100) if home_price > 0 else 0

            # Canadian minimum down payment rules
            # First $500,000: 5% minimum
            # Above $500,000 to $1M: 10% minimum
            # Above $1M: 20% minimum
            if home_price <= 500000:
                min_down_payment = home_price * 0.05
                min_down_percent = 5
            elif home_price <= 1000000:
                min_down_payment = 500000 * 0.05 + (home_price - 500000) * 0.10
                min_down_percent = min_down_payment / home_price * 100
            else:
                min_down_payment = home_price * 0.20
                min_down_percent = 20

            if down_payment_amount < min_down_payment:
                return JsonResponse({
                    'success': False,
                    'error': f'Minimum down payment required: ${min_down_payment:,.2f} ({min_down_percent:.1f}%)'
                }, status=400)

            # Base mortgage amount
            base_mortgage = home_price - down_payment_amount

            # Calculate CMHC Insurance (if down payment < 20%)
            cmhc_premium = 0
            cmhc_rate = 0
            if down_payment_percent < 20:
                if down_payment_percent >= 15:
                    cmhc_rate = self.CMHC_RATES[15]
                elif down_payment_percent >= 10:
                    cmhc_rate = self.CMHC_RATES[10]
                else:
                    cmhc_rate = self.CMHC_RATES[5]
                
                cmhc_premium = base_mortgage * (cmhc_rate / 100)
                
                # High-ratio mortgages require insurance and max 25-year amortization
                if amortization_period > 25:
                    return JsonResponse({
                        'success': False,
                        'error': 'Insured mortgages (down payment < 20%) are limited to 25-year amortization in Canada.'
                    }, status=400)

            # Total mortgage amount
            total_mortgage = base_mortgage + cmhc_premium

            # Canadian semi-annual compounding
            # Convert annual rate to semi-annual effective rate, then to payment period rate
            semi_annual_rate = interest_rate / 100 / 2
            effective_annual_rate = np.power(1 + semi_annual_rate, 2) - 1

            # Payment frequency calculations
            if payment_frequency == 'monthly':
                payments_per_year = 12
            elif payment_frequency == 'semi_monthly':
                payments_per_year = 24
            elif payment_frequency == 'biweekly':
                payments_per_year = 26
            elif payment_frequency == 'accelerated_biweekly':
                payments_per_year = 26
            elif payment_frequency == 'weekly':
                payments_per_year = 52
            elif payment_frequency == 'accelerated_weekly':
                payments_per_year = 52
            else:
                payments_per_year = 12

            # Periodic rate from effective annual rate
            periodic_rate = np.power(1 + effective_annual_rate, 1/payments_per_year) - 1

            total_payments = amortization_period * payments_per_year

            # Calculate regular payment
            if periodic_rate > 0:
                regular_payment = total_mortgage * (periodic_rate * np.power(1 + periodic_rate, total_payments)) / (np.power(1 + periodic_rate, total_payments) - 1)
            else:
                regular_payment = total_mortgage / total_payments

            # For accelerated payments, calculate as monthly payment / 2 or / 4
            if payment_frequency == 'accelerated_biweekly':
                # Monthly payment divided by 2
                monthly_rate = np.power(1 + effective_annual_rate, 1/12) - 1
                monthly_payment = total_mortgage * (monthly_rate * np.power(1 + monthly_rate, amortization_period * 12)) / (np.power(1 + monthly_rate, amortization_period * 12) - 1)
                regular_payment = monthly_payment / 2
            elif payment_frequency == 'accelerated_weekly':
                # Monthly payment divided by 4
                monthly_rate = np.power(1 + effective_annual_rate, 1/12) - 1
                monthly_payment = total_mortgage * (monthly_rate * np.power(1 + monthly_rate, amortization_period * 12)) / (np.power(1 + monthly_rate, amortization_period * 12) - 1)
                regular_payment = monthly_payment / 4

            # Calculate totals
            # For term period
            term_payments = mortgage_term * payments_per_year
            balance_at_term_end = total_mortgage

            # Simulate payments to get balance at term end
            balance = total_mortgage
            total_interest_term = 0
            total_principal_term = 0
            
            for i in range(int(term_payments)):
                interest_payment = balance * periodic_rate
                principal_payment = regular_payment - interest_payment
                if principal_payment > balance:
                    principal_payment = balance
                balance -= principal_payment
                total_interest_term += interest_payment
                total_principal_term += principal_payment
                if balance <= 0:
                    break

            balance_at_term_end = max(0, balance)

            # Full amortization totals
            total_paid = regular_payment * total_payments
            total_interest = total_paid - total_mortgage

            # Calculate actual amortization for accelerated payments
            if 'accelerated' in payment_frequency:
                balance = total_mortgage
                actual_payments = 0
                while balance > 0 and actual_payments < total_payments * 2:
                    interest_payment = balance * periodic_rate
                    principal_payment = regular_payment - interest_payment
                    if principal_payment > balance:
                        principal_payment = balance
                    balance -= principal_payment
                    actual_payments += 1
                
                actual_years = actual_payments / payments_per_year
                time_saved_years = amortization_period - actual_years
                interest_saved = total_interest - (regular_payment * actual_payments - total_mortgage)
            else:
                actual_years = amortization_period
                time_saved_years = 0
                interest_saved = 0

            # Monthly equivalent costs
            monthly_taxes = property_tax_annual / 12
            monthly_insurance = home_insurance_annual / 12
            
            # Calculate monthly equivalent payment
            if payment_frequency == 'monthly':
                monthly_equivalent = regular_payment
            elif payment_frequency in ['semi_monthly']:
                monthly_equivalent = regular_payment * 2
            elif payment_frequency in ['biweekly', 'accelerated_biweekly']:
                monthly_equivalent = regular_payment * 26 / 12
            else:
                monthly_equivalent = regular_payment * 52 / 12

            total_monthly = monthly_equivalent + monthly_taxes + monthly_insurance + condo_fees_monthly

            # Generate payment schedule
            schedule = []
            balance = total_mortgage
            total_int_paid = 0
            total_prin_paid = 0

            for period in range(1, int(min(term_payments, 60)) + 1):
                interest_payment = balance * periodic_rate
                principal_payment = regular_payment - interest_payment
                if principal_payment > balance:
                    principal_payment = balance
                balance = max(0, balance - principal_payment)
                total_int_paid += interest_payment
                total_prin_paid += principal_payment

                if period <= 12 or period % 12 == 0:
                    schedule.append({
                        'period': period,
                        'payment': round(regular_payment, 2),
                        'principal': round(principal_payment, 2),
                        'interest': round(interest_payment, 2),
                        'balance': round(balance, 2),
                        'total_interest': round(total_int_paid, 2)
                    })

            result = {
                'success': True,
                'property': {
                    'home_price': round(home_price, 2),
                    'down_payment': round(down_payment_amount, 2),
                    'down_payment_percent': round(down_payment_percent, 2),
                    'min_down_payment': round(min_down_payment, 2)
                },
                'mortgage_details': {
                    'base_mortgage': round(base_mortgage, 2),
                    'cmhc_premium': round(cmhc_premium, 2),
                    'cmhc_rate': cmhc_rate,
                    'total_mortgage': round(total_mortgage, 2),
                    'interest_rate': interest_rate,
                    'amortization_years': amortization_period,
                    'term_years': mortgage_term,
                    'payment_frequency': payment_frequency.replace('_', ' ').title()
                },
                'payment_details': {
                    'regular_payment': round(regular_payment, 2),
                    'payment_frequency': payment_frequency.replace('_', ' ').title(),
                    'payments_per_year': payments_per_year,
                    'monthly_equivalent': round(monthly_equivalent, 2)
                },
                'monthly_costs': {
                    'mortgage_payment': round(monthly_equivalent, 2),
                    'property_tax': round(monthly_taxes, 2),
                    'home_insurance': round(monthly_insurance, 2),
                    'condo_fees': round(condo_fees_monthly, 2),
                    'total': round(total_monthly, 2)
                },
                'term_summary': {
                    'term_years': mortgage_term,
                    'total_payments_term': round(regular_payment * term_payments, 2),
                    'principal_paid_term': round(total_principal_term, 2),
                    'interest_paid_term': round(total_interest_term, 2),
                    'balance_at_renewal': round(balance_at_term_end, 2)
                },
                'amortization_summary': {
                    'total_payments': round(total_paid, 2),
                    'total_interest': round(total_interest, 2),
                    'actual_amortization_years': round(actual_years, 1),
                    'time_saved_years': round(time_saved_years, 1),
                    'interest_saved': round(interest_saved, 2)
                },
                'schedule': schedule,
                'canadian_notes': [
                    'Canadian mortgages use semi-annual compounding',
                    'CMHC insurance required for down payments under 20%',
                    'Maximum amortization: 25 years (insured) or 30 years (uninsured)',
                    'Mortgage terms typically 1-5 years, requiring renewal'
                ]
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
