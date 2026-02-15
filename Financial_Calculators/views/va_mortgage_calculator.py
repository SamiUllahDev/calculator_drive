from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import symbols, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class VaMortgageCalculator(View):
    """
    Class-based view for VA Mortgage Calculator.
    Calculates VA loan payments including funding fee for veterans.
    Uses NumPy for validation and SymPy for precise payment formula.
    """
    template_name = 'financial_calculators/va_mortgage_calculator.html'

    # VA Funding Fee rates (2024)
    FUNDING_FEE_RATES = {
        'first_use': {0: 2.15, 5: 1.5, 10: 1.25},
        'subsequent_use': {0: 3.3, 5: 1.5, 10: 1.25},
        'reserves_guard_first': {0: 2.15, 5: 1.5, 10: 1.25},
        'reserves_guard_subsequent': {0: 3.3, 5: 1.5, 10: 1.25},
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'VA Mortgage Calculator',
            'page_title': 'VA Mortgage Calculator - Calculate VA Loan Payments',
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
        """Handle POST request for VA loan calculations (JSON or form)."""
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
            down_payment_type = (data.get('down_payment_type') or 'amount').strip().lower()

            # Loan details
            interest_rate = self._parse_number(data.get('interest_rate', 0))
            loan_term_raw = data.get('loan_term', 360)
            loan_term = int(float(loan_term_raw)) if loan_term_raw else 360

            # VA specific
            first_time_use = data.get('first_time_use') in (True, 'true', 'True', '1', 1)
            service_type = (data.get('service_type') or 'regular').strip().lower()
            disability_exempt = data.get('disability_exempt') in (True, 'true', 'True', '1', 1)
            finance_funding_fee = data.get('finance_funding_fee') in (True, 'true', 'True', '1', 1)

            # Additional costs
            property_tax_annual = self._parse_number(data.get('property_tax', 0))
            home_insurance_annual = self._parse_number(data.get('home_insurance', 0))
            hoa_monthly = self._parse_number(data.get('hoa', 0))

            # Validation
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

            # Base loan amount
            base_loan_amount = home_price - down_payment_amount

            # VA Funding Fee
            if disability_exempt:
                funding_fee = 0.0
                funding_fee_rate = 0
                funding_fee_note = 'Exempt due to service-connected disability'
            else:
                if service_type == 'reserves_guard':
                    rate_category = 'reserves_guard_first' if first_time_use else 'reserves_guard_subsequent'
                else:
                    rate_category = 'first_use' if first_time_use else 'subsequent_use'

                if down_payment_percent >= 10:
                    funding_fee_rate = self.FUNDING_FEE_RATES[rate_category][10]
                elif down_payment_percent >= 5:
                    funding_fee_rate = self.FUNDING_FEE_RATES[rate_category][5]
                else:
                    funding_fee_rate = self.FUNDING_FEE_RATES[rate_category][0]

                funding_fee = float(N(Float(base_loan_amount) * (Float(funding_fee_rate) / 100), 10))
                funding_fee_note = f'{funding_fee_rate}% funding fee applied'

            if finance_funding_fee and not disability_exempt:
                total_loan_amount = base_loan_amount + funding_fee
            else:
                total_loan_amount = base_loan_amount

            ltv = (base_loan_amount / home_price) * 100 if home_price > 0 else 0

            # Monthly P&I (SymPy)
            monthly_rate = interest_rate / 100 / 12
            if monthly_rate > 0:
                P, r, n = symbols('P r n', real=True, positive=True)
                factor = (r * (1 + r)**n) / ((1 + r)**n - 1)
                factor_val = float(N(factor.subs({r: Float(monthly_rate, 15), n: Float(loan_term, 15)}), 10))
                monthly_pi = float(N(total_loan_amount * factor_val, 10))
            else:
                monthly_pi = total_loan_amount / loan_term

            monthly_taxes = property_tax_annual / 12
            monthly_insurance = home_insurance_annual / 12
            total_monthly_payment = monthly_pi + monthly_taxes + monthly_insurance + hoa_monthly

            total_pi_payments = monthly_pi * loan_term
            total_interest = total_pi_payments - total_loan_amount
            total_taxes = property_tax_annual * (loan_term / 12)
            total_insurance = home_insurance_annual * (loan_term / 12)
            total_hoa = hoa_monthly * loan_term
            total_cost = total_pi_payments + total_taxes + total_insurance + total_hoa
            if not finance_funding_fee and not disability_exempt:
                total_cost += funding_fee

            # Amortization schedule
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

            va_benefits = [
                'No down payment required (100% financing)',
                'No Private Mortgage Insurance (PMI)',
                'Competitive interest rates',
                'Limited closing costs',
                'No prepayment penalties',
                'Assumable loans',
                'VA assistance if you have trouble paying',
            ]
            va_eligibility = {
                'active_duty': '90 continuous days during wartime, 181 days during peacetime',
                'national_guard': '6 years in Guard/Reserves or 90 days active duty',
                'surviving_spouse': 'Unremarried spouse of veteran who died in service or from service-connected disability',
            }

            # Backend-prepared chart data
            chart_data = self._prepare_chart_data(
                monthly_pi=monthly_pi,
                monthly_taxes=monthly_taxes,
                monthly_insurance=monthly_insurance,
                hoa_monthly=hoa_monthly,
                total_loan_amount=total_loan_amount,
                total_interest=total_interest,
                funding_fee=funding_fee if not disability_exempt else 0,
                total_taxes=total_taxes,
                total_insurance=total_insurance,
                total_hoa=total_hoa,
            )

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
                'chart_data': chart_data,
            }

            return JsonResponse(result)

        except (ValueError, TypeError, KeyError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)

    def _prepare_chart_data(self, monthly_pi, monthly_taxes, monthly_insurance, hoa_monthly,
                            total_loan_amount, total_interest, funding_fee,
                            total_taxes, total_insurance, total_hoa):
        """Build Chart.js-ready data on the backend."""
        monthly_labels = ['Principal & Interest', 'Property Tax', 'Home Insurance']
        monthly_values = [round(monthly_pi, 2), round(monthly_taxes, 2), round(monthly_insurance, 2)]
        monthly_colors = ['#2563eb', '#ef4444', '#22c55e']
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

        life_labels = ['Principal', 'Interest', 'Funding Fee', 'Taxes & Insurance']
        life_values = [
            round(total_loan_amount, 2),
            round(total_interest, 2),
            round(funding_fee, 2),
            round(total_taxes + total_insurance + total_hoa, 2)
        ]
        life_colors = ['#2563eb', '#f59e0b', '#9333ea', '#22c55e']
        if total_hoa > 0:
            life_labels = ['Principal', 'Interest', 'Funding Fee', 'Taxes & Ins.', 'HOA']
            life_values = [
                round(total_loan_amount, 2),
                round(total_interest, 2),
                round(funding_fee, 2),
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
