from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class VaMortgageCalculator(View):
    """
    Class-based view for VA Mortgage Calculator
    Calculates VA loan payments including funding fee for veterans.
    """
    template_name = 'financial_calculators/va_mortgage_calculator.html'

    # VA Funding Fee rates (2024)
    # First-time use, regular military
    FUNDING_FEE_RATES = {
        'first_use': {
            0: 2.15,      # 0% down
            5: 1.5,       # 5-9.99% down
            10: 1.25,     # 10%+ down
        },
        'subsequent_use': {
            0: 3.3,       # 0% down
            5: 1.5,       # 5-9.99% down
            10: 1.25,     # 10%+ down
        },
        'reserves_guard_first': {
            0: 2.15,
            5: 1.5,
            10: 1.25,
        },
        'reserves_guard_subsequent': {
            0: 3.3,
            5: 1.5,
            10: 1.25,
        }
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'VA Mortgage Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for VA loan calculations"""
        try:
            data = json.loads(request.body)

            # Property details
            home_price = float(str(data.get('home_price', 0)).replace(',', ''))
            down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
            down_payment_type = data.get('down_payment_type', 'amount')
            
            # Loan details
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            loan_term = int(data.get('loan_term', 360))  # months
            
            # VA specific
            first_time_use = data.get('first_time_use', True)
            service_type = data.get('service_type', 'regular')  # 'regular' or 'reserves_guard'
            disability_exempt = data.get('disability_exempt', False)  # Exempt from funding fee
            
            # Additional costs
            property_tax_annual = float(str(data.get('property_tax', 0)).replace(',', ''))
            home_insurance_annual = float(str(data.get('home_insurance', 0)).replace(',', ''))
            hoa_monthly = float(str(data.get('hoa', 0)).replace(',', ''))

            # Validation
            if home_price <= 0:
                return JsonResponse({'success': False, 'error': 'Home price must be greater than zero.'}, status=400)
            if interest_rate < 0:
                return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)

            # Calculate down payment
            if down_payment_type == 'percent':
                down_payment_percent = down_payment
                down_payment_amount = home_price * (down_payment / 100)
            else:
                down_payment_amount = down_payment
                down_payment_percent = (down_payment / home_price * 100) if home_price > 0 else 0

            # Base loan amount
            base_loan_amount = home_price - down_payment_amount

            # Calculate VA Funding Fee
            if disability_exempt:
                funding_fee = 0
                funding_fee_rate = 0
                funding_fee_note = "Exempt due to service-connected disability"
            else:
                # Determine rate category
                if service_type == 'reserves_guard':
                    if first_time_use:
                        rate_category = 'reserves_guard_first'
                    else:
                        rate_category = 'reserves_guard_subsequent'
                else:
                    if first_time_use:
                        rate_category = 'first_use'
                    else:
                        rate_category = 'subsequent_use'

                # Determine rate based on down payment
                if down_payment_percent >= 10:
                    funding_fee_rate = self.FUNDING_FEE_RATES[rate_category][10]
                elif down_payment_percent >= 5:
                    funding_fee_rate = self.FUNDING_FEE_RATES[rate_category][5]
                else:
                    funding_fee_rate = self.FUNDING_FEE_RATES[rate_category][0]

                funding_fee = base_loan_amount * (funding_fee_rate / 100)
                funding_fee_note = f"{funding_fee_rate}% funding fee applied"

            # Total loan amount (can finance funding fee)
            finance_funding_fee = data.get('finance_funding_fee', True)
            if finance_funding_fee and not disability_exempt:
                total_loan_amount = base_loan_amount + funding_fee
            else:
                total_loan_amount = base_loan_amount

            # LTV calculation
            ltv = (base_loan_amount / home_price) * 100

            # Calculate monthly P&I payment
            monthly_rate = interest_rate / 100 / 12
            
            if monthly_rate > 0:
                monthly_pi = total_loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
            else:
                monthly_pi = total_loan_amount / loan_term

            # Monthly escrow
            monthly_taxes = property_tax_annual / 12
            monthly_insurance = home_insurance_annual / 12

            # Total monthly payment (PITI + HOA) - NO PMI for VA loans!
            total_monthly_payment = monthly_pi + monthly_taxes + monthly_insurance + hoa_monthly

            # Total costs
            total_pi_payments = monthly_pi * loan_term
            total_interest = total_pi_payments - total_loan_amount
            total_taxes = property_tax_annual * (loan_term / 12)
            total_insurance = home_insurance_annual * (loan_term / 12)
            total_hoa = hoa_monthly * loan_term

            total_cost = total_pi_payments + total_taxes + total_insurance + total_hoa
            if not finance_funding_fee:
                total_cost += funding_fee

            # Generate amortization schedule
            schedule = []
            balance = total_loan_amount
            total_interest_paid = 0
            total_principal_paid = 0

            for month in range(1, loan_term + 1):
                interest_payment = balance * monthly_rate
                principal_payment = monthly_pi - interest_payment
                
                if principal_payment > balance:
                    principal_payment = balance
                
                balance = max(0, balance - principal_payment)
                total_interest_paid += interest_payment
                total_principal_paid += principal_payment

                if month <= 12 or month % 12 == 0 or month == loan_term:
                    schedule.append({
                        'month': month,
                        'payment': round(monthly_pi, 2),
                        'principal': round(principal_payment, 2),
                        'interest': round(interest_payment, 2),
                        'balance': round(balance, 2),
                        'total_interest': round(total_interest_paid, 2)
                    })

            # VA loan benefits summary
            va_benefits = [
                "No down payment required (100% financing)",
                "No Private Mortgage Insurance (PMI)",
                "Competitive interest rates",
                "Limited closing costs",
                "No prepayment penalties",
                "Assumable loans",
                "VA assistance if you have trouble paying"
            ]

            # VA eligibility requirements
            va_eligibility = {
                'active_duty': '90 continuous days during wartime, 181 days during peacetime',
                'national_guard': '6 years in Guard/Reserves or 90 days active duty',
                'surviving_spouse': 'Unremarried spouse of veteran who died in service or from service-connected disability'
            }

            result = {
                'success': True,
                'property': {
                    'home_price': round(home_price, 2),
                    'down_payment': round(down_payment_amount, 2),
                    'down_payment_percent': round(down_payment_percent, 2),
                    'ltv': round(ltv, 2)
                },
                'loan_details': {
                    'base_loan_amount': round(base_loan_amount, 2),
                    'funding_fee': round(funding_fee, 2),
                    'funding_fee_rate': funding_fee_rate if not disability_exempt else 0,
                    'funding_fee_financed': finance_funding_fee,
                    'funding_fee_note': funding_fee_note,
                    'total_loan_amount': round(total_loan_amount, 2),
                    'interest_rate': interest_rate,
                    'term_months': loan_term,
                    'term_years': round(loan_term / 12, 1)
                },
                'borrower': {
                    'service_type': 'Regular Military' if service_type == 'regular' else 'Reserves/National Guard',
                    'first_time_va_use': first_time_use,
                    'disability_exempt': disability_exempt
                },
                'monthly_payment': {
                    'principal_interest': round(monthly_pi, 2),
                    'property_tax': round(monthly_taxes, 2),
                    'home_insurance': round(monthly_insurance, 2),
                    'pmi': 0,
                    'pmi_note': 'VA loans do not require PMI!',
                    'hoa': round(hoa_monthly, 2),
                    'total': round(total_monthly_payment, 2)
                },
                'totals': {
                    'total_payments': round(total_pi_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'funding_fee': round(funding_fee, 2),
                    'total_taxes': round(total_taxes, 2),
                    'total_insurance': round(total_insurance, 2),
                    'total_hoa': round(total_hoa, 2),
                    'total_cost': round(total_cost, 2)
                },
                'va_benefits': va_benefits,
                'va_eligibility': va_eligibility,
                'schedule': schedule,
                'chart_data': {
                    'principal': round(total_loan_amount, 2),
                    'interest': round(total_interest, 2),
                    'funding_fee': round(funding_fee, 2),
                    'taxes_insurance': round(total_taxes + total_insurance, 2)
                }
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
