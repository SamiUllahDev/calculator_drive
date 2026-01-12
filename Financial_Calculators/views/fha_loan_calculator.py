from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class FhaLoanCalculator(View):
    """
    Class-based view for FHA Loan Calculator
    Calculates FHA mortgage payments including upfront and annual MIP.
    """
    template_name = 'financial_calculators/fha_loan_calculator.html'

    # FHA MIP rates (2024)
    UPFRONT_MIP_RATE = 1.75  # 1.75% of base loan amount
    
    # Annual MIP rates based on loan term and LTV
    ANNUAL_MIP_RATES = {
        # (term_years, ltv_threshold): rate
        (30, 95): 0.55,   # >95% LTV, 30 year term
        (30, 90): 0.50,   # 90-95% LTV
        (30, 0): 0.50,    # <=90% LTV
        (15, 90): 0.40,   # >90% LTV, 15 year term
        (15, 0): 0.15,    # <=90% LTV
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'FHA Loan Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for FHA loan calculations"""
        try:
            data = json.loads(request.body)

            # Property details
            home_price = float(str(data.get('home_price', 0)).replace(',', ''))
            down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
            down_payment_type = data.get('down_payment_type', 'percent')  # 'percent' or 'amount'
            
            # Loan details
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            loan_term = int(data.get('loan_term', 360))  # months
            
            # Additional costs
            property_tax_annual = float(str(data.get('property_tax', 0)).replace(',', ''))
            home_insurance_annual = float(str(data.get('home_insurance', 0)).replace(',', ''))
            hoa_monthly = float(str(data.get('hoa', 0)).replace(',', ''))

            # Validation
            if home_price <= 0:
                return JsonResponse({'success': False, 'error': 'Home price must be greater than zero.'}, status=400)
            if interest_rate < 0:
                return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)
            if loan_term <= 0:
                return JsonResponse({'success': False, 'error': 'Loan term must be greater than zero.'}, status=400)

            # Calculate down payment
            if down_payment_type == 'percent':
                down_payment_percent = down_payment
                down_payment_amount = home_price * (down_payment / 100)
            else:
                down_payment_amount = down_payment
                down_payment_percent = (down_payment / home_price * 100) if home_price > 0 else 0

            # FHA minimum down payment check
            min_down_payment_percent = 3.5
            if down_payment_percent < min_down_payment_percent:
                return JsonResponse({
                    'success': False, 
                    'error': f'FHA requires minimum {min_down_payment_percent}% down payment. Your down payment is {down_payment_percent:.1f}%.'
                }, status=400)

            # Base loan amount
            base_loan_amount = home_price - down_payment_amount

            # Calculate Upfront MIP
            upfront_mip = base_loan_amount * (self.UPFRONT_MIP_RATE / 100)

            # Total loan amount (including financed UFMIP)
            total_loan_amount = base_loan_amount + upfront_mip

            # Calculate LTV
            ltv = (base_loan_amount / home_price) * 100

            # Determine Annual MIP rate
            term_years = loan_term // 12
            if term_years > 15:
                term_key = 30
            else:
                term_key = 15

            if ltv > 95:
                annual_mip_rate = self.ANNUAL_MIP_RATES.get((term_key, 95), 0.55)
            elif ltv > 90:
                annual_mip_rate = self.ANNUAL_MIP_RATES.get((term_key, 90), 0.50)
            else:
                annual_mip_rate = self.ANNUAL_MIP_RATES.get((term_key, 0), 0.50)

            # Monthly MIP
            monthly_mip = (base_loan_amount * (annual_mip_rate / 100)) / 12

            # MIP duration (for loans with LTV > 90%, MIP is for life of loan)
            if ltv > 90:
                mip_duration_months = loan_term
                mip_duration_note = "MIP required for life of loan (LTV > 90%)"
            else:
                mip_duration_months = 132  # 11 years
                mip_duration_note = "MIP required for 11 years (LTV ≤ 90%)"

            # Calculate monthly P&I payment
            monthly_rate = interest_rate / 100 / 12
            
            if monthly_rate > 0:
                monthly_pi = total_loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
            else:
                monthly_pi = total_loan_amount / loan_term

            # Monthly escrow (taxes + insurance)
            monthly_taxes = property_tax_annual / 12
            monthly_insurance = home_insurance_annual / 12

            # Total monthly payment (PITI + MIP + HOA)
            total_monthly_payment = monthly_pi + monthly_taxes + monthly_insurance + monthly_mip + hoa_monthly

            # Total costs
            total_pi_payments = monthly_pi * loan_term
            total_interest = total_pi_payments - total_loan_amount
            total_mip = monthly_mip * min(mip_duration_months, loan_term)
            total_taxes = property_tax_annual * (loan_term / 12)
            total_insurance = home_insurance_annual * (loan_term / 12)
            total_hoa = hoa_monthly * loan_term

            total_cost = total_pi_payments + total_mip + total_taxes + total_insurance + total_hoa

            # Generate amortization schedule
            schedule = []
            balance = total_loan_amount
            total_interest_paid = 0
            total_principal_paid = 0
            total_mip_paid = 0

            for month in range(1, loan_term + 1):
                interest_payment = balance * monthly_rate
                principal_payment = monthly_pi - interest_payment
                
                if principal_payment > balance:
                    principal_payment = balance
                
                balance = max(0, balance - principal_payment)
                total_interest_paid += interest_payment
                total_principal_paid += principal_payment
                
                # MIP payment (if within duration)
                mip_payment = monthly_mip if month <= mip_duration_months else 0
                total_mip_paid += mip_payment

                if month <= 12 or month % 12 == 0 or month == loan_term:
                    schedule.append({
                        'month': month,
                        'payment': round(monthly_pi + mip_payment, 2),
                        'principal': round(principal_payment, 2),
                        'interest': round(interest_payment, 2),
                        'mip': round(mip_payment, 2),
                        'balance': round(balance, 2),
                        'total_interest': round(total_interest_paid, 2)
                    })

            # FHA loan limits info
            fha_info = {
                'min_down_payment': f'{min_down_payment_percent}%',
                'min_credit_score': '500-579 (10% down) or 580+ (3.5% down)',
                'max_dti': '43% (may go up to 50% with compensating factors)',
                'upfront_mip_rate': f'{self.UPFRONT_MIP_RATE}%',
                'annual_mip_rate': f'{annual_mip_rate}%'
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
                    'upfront_mip': round(upfront_mip, 2),
                    'total_loan_amount': round(total_loan_amount, 2),
                    'interest_rate': interest_rate,
                    'term_months': loan_term,
                    'term_years': round(loan_term / 12, 1)
                },
                'mip_details': {
                    'upfront_mip': round(upfront_mip, 2),
                    'upfront_mip_rate': self.UPFRONT_MIP_RATE,
                    'annual_mip_rate': annual_mip_rate,
                    'monthly_mip': round(monthly_mip, 2),
                    'mip_duration_months': mip_duration_months,
                    'mip_duration_years': round(mip_duration_months / 12, 1),
                    'mip_duration_note': mip_duration_note,
                    'total_mip': round(total_mip, 2)
                },
                'monthly_payment': {
                    'principal_interest': round(monthly_pi, 2),
                    'mip': round(monthly_mip, 2),
                    'property_tax': round(monthly_taxes, 2),
                    'home_insurance': round(monthly_insurance, 2),
                    'hoa': round(hoa_monthly, 2),
                    'total': round(total_monthly_payment, 2)
                },
                'totals': {
                    'total_payments': round(total_pi_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'total_mip': round(total_mip, 2),
                    'total_taxes': round(total_taxes, 2),
                    'total_insurance': round(total_insurance, 2),
                    'total_hoa': round(total_hoa, 2),
                    'total_cost': round(total_cost, 2)
                },
                'fha_info': fha_info,
                'schedule': schedule,
                'chart_data': {
                    'principal': round(total_loan_amount, 2),
                    'interest': round(total_interest, 2),
                    'mip': round(total_mip, 2),
                    'taxes_insurance': round(total_taxes + total_insurance, 2)
                }
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
