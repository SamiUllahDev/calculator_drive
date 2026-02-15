from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import symbols, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FhaLoanCalculator(View):
    """
    Class-based view for FHA Loan Calculator.
    Calculates FHA mortgage payments including upfront and annual MIP.
    Uses NumPy for validation and SymPy for precise payment formula.
    """
    template_name = 'financial_calculators/fha_loan_calculator.html'

    # FHA MIP rates (2024)
    UPFRONT_MIP_RATE = Float('1.75')  # 1.75% of base loan amount

    # Annual MIP rates: (term_years, ltv_threshold): rate
    ANNUAL_MIP_RATES = {
        (30, 95): 0.55,
        (30, 90): 0.50,
        (30, 0): 0.50,
        (15, 90): 0.40,
        (15, 0): 0.15,
    }

    MIN_DOWN_PERCENT = 3.5

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'FHA Loan Calculator',
            'page_title': 'FHA Loan Calculator - Calculate Payments & MIP',
        }
        return render(request, self.template_name, context)

    def _parse_number(self, val):
        """Parse string with commas/dollars to float."""
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        return float(str(val).replace(',', '').replace('$', '').strip() or 0)

    def post(self, request):
        """Handle POST request for FHA loan calculations (JSON or form)."""
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = {}
                for k in request.POST:
                    v = request.POST.getlist(k)
                    data[k] = v[0] if len(v) == 1 else v

            # Property details
            home_price = self._parse_number(data.get('home_price', 0))
            down_payment = self._parse_number(data.get('down_payment', 0))
            down_payment_type = (data.get('down_payment_type') or 'percent').strip().lower()

            # Loan details
            interest_rate = self._parse_number(data.get('interest_rate', 0))
            loan_term_raw = data.get('loan_term', 360)
            loan_term = int(float(loan_term_raw)) if loan_term_raw else 360

            # Additional costs
            property_tax_annual = self._parse_number(data.get('property_tax', 0))
            home_insurance_annual = self._parse_number(data.get('home_insurance', 0))
            hoa_monthly = self._parse_number(data.get('hoa', 0))

            # Validation using NumPy
            if np.any(np.array([home_price]) <= 0):
                return JsonResponse({'success': False, 'error': 'Home price must be greater than zero.'}, status=400)
            if interest_rate < 0:
                return JsonResponse({'success': False, 'error': 'Interest rate cannot be negative.'}, status=400)
            if loan_term <= 0 or loan_term > 600:
                return JsonResponse({'success': False, 'error': 'Loan term must be between 1 and 600 months.'}, status=400)
            if down_payment_type not in ('percent', 'amount'):
                return JsonResponse({'success': False, 'error': 'Down payment type must be percent or amount.'}, status=400)

            # Calculate down payment
            if down_payment_type == 'percent':
                down_payment_percent = down_payment
                down_payment_amount = home_price * (down_payment / 100)
            else:
                down_payment_amount = down_payment
                down_payment_percent = (down_payment / home_price * 100) if home_price > 0 else 0

            if down_payment_amount > home_price:
                return JsonResponse({'success': False, 'error': 'Down payment cannot exceed home price.'}, status=400)

            # FHA minimum down payment
            if down_payment_percent < self.MIN_DOWN_PERCENT:
                return JsonResponse({
                    'success': False,
                    'error': f'FHA requires minimum {self.MIN_DOWN_PERCENT}% down payment. Your down payment is {down_payment_percent:.1f}%.'
                }, status=400)

            # Base loan amount
            base_loan_amount = home_price - down_payment_amount

            # Upfront MIP (SymPy for consistency)
            upfront_mip = float(N(base_loan_amount * (self.UPFRONT_MIP_RATE / 100), 10))
            total_loan_amount = base_loan_amount + upfront_mip

            # LTV
            ltv = (base_loan_amount / home_price) * 100 if home_price > 0 else 0

            # Annual MIP rate
            term_years = loan_term // 12
            term_key = 30 if term_years > 15 else 15
            if ltv > 95:
                annual_mip_rate = self.ANNUAL_MIP_RATES.get((term_key, 95), 0.55)
            elif ltv > 90:
                annual_mip_rate = self.ANNUAL_MIP_RATES.get((term_key, 90), 0.50)
            else:
                annual_mip_rate = self.ANNUAL_MIP_RATES.get((term_key, 0), 0.50)

            monthly_mip = (base_loan_amount * (annual_mip_rate / 100)) / 12

            if ltv > 90:
                mip_duration_months = loan_term
                mip_duration_note = 'MIP required for life of loan (LTV > 90%)'
            else:
                mip_duration_months = 132
                mip_duration_note = 'MIP required for 11 years (LTV ≤ 90%)'

            # Monthly P&I: PMT = P * (r(1+r)^n) / ((1+r)^n - 1)
            monthly_rate = interest_rate / 100 / 12
            if monthly_rate > 0:
                P, r, n = symbols('P r n', real=True, positive=True)
                # SymPy evaluation for consistency with other calculators
                factor = (r * (1 + r)**n) / ((1 + r)**n - 1)
                factor_val = float(N(factor.subs({r: Float(monthly_rate, 15), n: Float(loan_term, 15)}), 10))
                monthly_pi = float(N(total_loan_amount * factor_val, 10))
            else:
                monthly_pi = total_loan_amount / loan_term

            monthly_taxes = property_tax_annual / 12
            monthly_insurance = home_insurance_annual / 12
            total_monthly_payment = monthly_pi + monthly_taxes + monthly_insurance + monthly_mip + hoa_monthly

            # Totals over life of loan
            total_pi_payments = monthly_pi * loan_term
            total_interest = total_pi_payments - total_loan_amount
            total_mip = monthly_mip * min(mip_duration_months, loan_term)
            total_taxes = property_tax_annual * (loan_term / 12)
            total_insurance = home_insurance_annual * (loan_term / 12)
            total_hoa = hoa_monthly * loan_term
            total_cost = total_pi_payments + total_mip + total_taxes + total_insurance + total_hoa

            # Amortization schedule (first 12 months, yearly, last month)
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

            # Backend-prepared chart data (BMI-style)
            chart_data = self._prepare_chart_data(
                monthly_pi=monthly_pi,
                monthly_mip=monthly_mip,
                monthly_taxes=monthly_taxes,
                monthly_insurance=monthly_insurance,
                hoa_monthly=hoa_monthly,
                total_loan_amount=total_loan_amount,
                total_interest=total_interest,
                total_mip=total_mip,
                total_taxes=total_taxes,
                total_insurance=total_insurance,
                total_hoa=total_hoa,
                total_cost=total_cost,
            )

            fha_info = {
                'min_down_payment': f'{self.MIN_DOWN_PERCENT}%',
                'min_credit_score': '500-579 (10% down) or 580+ (3.5% down)',
                'max_dti': '43% (may go up to 50% with compensating factors)',
                'upfront_mip_rate': f'{float(self.UPFRONT_MIP_RATE)}%',
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
                    'upfront_mip_rate': float(self.UPFRONT_MIP_RATE),
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
                'chart_data': chart_data,
            }

            return JsonResponse(result)

        except (ValueError, TypeError, KeyError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)

    def _prepare_chart_data(self, monthly_pi, monthly_mip, monthly_taxes, monthly_insurance, hoa_monthly,
                            total_loan_amount, total_interest, total_mip, total_taxes, total_insurance, total_hoa, total_cost):
        """Build Chart.js-ready data on the backend (BMI-style)."""
        # Monthly payment breakdown (doughnut)
        monthly_labels = ['Principal & Interest', 'Monthly MIP', 'Property Tax', 'Home Insurance']
        monthly_values = [round(monthly_pi, 2), round(monthly_mip, 2), round(monthly_taxes, 2), round(monthly_insurance, 2)]
        monthly_colors = ['#2563eb', '#9333ea', '#ef4444', '#22c55e']
        if hoa_monthly and float(hoa_monthly) > 0:
            monthly_labels.append('HOA')
            monthly_values.append(round(float(hoa_monthly), 2))
            monthly_colors.append('#f59e0b')

        payment_breakdown_chart = {
            'type': 'doughnut',
            'data': {
                'labels': monthly_labels,
                'datasets': [{
                    'data': monthly_values,
                    'backgroundColor': monthly_colors,
                    'borderWidth': 0,
                    'hoverOffset': 4
                }]
            },
            'options': {
                'cutout': '70%',
                'plugins': {'legend': {'position': 'right', 'labels': {'boxWidth': 12}}}
            }
        }

        # Total cost breakdown over life of loan (doughnut)
        life_labels = ['Principal', 'Interest', 'MIP', 'Taxes & Insurance']
        life_values = [
            round(total_loan_amount, 2),
            round(total_interest, 2),
            round(total_mip, 2),
            round(total_taxes + total_insurance + total_hoa, 2)
        ]
        life_colors = ['#2563eb', '#f59e0b', '#9333ea', '#22c55e']
        if total_hoa > 0:
            life_labels = ['Principal', 'Interest', 'MIP', 'Taxes & Ins.', 'HOA']
            life_values = [
                round(total_loan_amount, 2),
                round(total_interest, 2),
                round(total_mip, 2),
                round(total_taxes + total_insurance, 2),
                round(total_hoa, 2)
            ]
            life_colors = ['#2563eb', '#f59e0b', '#9333ea', '#22c55e', '#ec4899']

        total_cost_chart = {
            'type': 'doughnut',
            'data': {
                'labels': life_labels,
                'datasets': [{
                    'data': life_values,
                    'backgroundColor': life_colors,
                    'borderWidth': 0,
                    'hoverOffset': 4
                }]
            },
            'options': {
                'cutout': '65%',
                'plugins': {'legend': {'position': 'right', 'labels': {'boxWidth': 12}}}
            }
        }

        return {
            'payment_breakdown_chart': payment_breakdown_chart,
            'total_cost_chart': total_cost_chart,
        }
