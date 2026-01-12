from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class AutoLeaseCalculator(View):
    """
    Class-based view for Auto Lease Calculator
    Calculates monthly lease payments using money factor and residual value.
    """
    template_name = 'financial_calculators/auto_lease_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Auto Lease Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for auto lease calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'calculate_payment')

            if calc_type == 'calculate_payment':
                # Calculate monthly lease payment
                msrp = float(str(data.get('msrp', 0)).replace(',', ''))
                negotiated_price = float(str(data.get('negotiated_price', 0)).replace(',', ''))
                down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
                trade_in_value = float(str(data.get('trade_in_value', 0)).replace(',', ''))
                trade_in_payoff = float(str(data.get('trade_in_payoff', 0)).replace(',', ''))
                lease_term = int(data.get('lease_term', 36))  # months
                residual_percent = float(str(data.get('residual_percent', 0)).replace(',', ''))
                money_factor = float(str(data.get('money_factor', 0)).replace(',', ''))
                sales_tax_rate = float(str(data.get('sales_tax_rate', 0)).replace(',', ''))
                acquisition_fee = float(str(data.get('acquisition_fee', 0)).replace(',', ''))
                doc_fee = float(str(data.get('doc_fee', 0)).replace(',', ''))
                rebates = float(str(data.get('rebates', 0)).replace(',', ''))

                if msrp <= 0:
                    return JsonResponse({'success': False, 'error': 'MSRP must be greater than zero.'}, status=400)
                if negotiated_price <= 0:
                    negotiated_price = msrp
                if lease_term <= 0:
                    return JsonResponse({'success': False, 'error': 'Lease term must be greater than zero.'}, status=400)
                if residual_percent <= 0 or residual_percent > 100:
                    return JsonResponse({'success': False, 'error': 'Residual value must be between 0 and 100%.'}, status=400)

                # Calculate residual value
                residual_value = msrp * (residual_percent / 100)

                # Calculate trade-in equity
                trade_in_equity = max(0, trade_in_value - trade_in_payoff)
                trade_in_negative = max(0, trade_in_payoff - trade_in_value)

                # Calculate capitalized cost
                gross_cap_cost = negotiated_price + acquisition_fee + doc_fee + trade_in_negative
                cap_cost_reduction = down_payment + trade_in_equity + rebates
                adjusted_cap_cost = gross_cap_cost - cap_cost_reduction

                # Depreciation fee (monthly)
                depreciation = (adjusted_cap_cost - residual_value) / lease_term

                # Finance charge (rent charge) - monthly
                finance_charge = (adjusted_cap_cost + residual_value) * money_factor

                # Base monthly payment (before tax)
                base_payment = depreciation + finance_charge

                # Monthly sales tax
                monthly_tax = base_payment * (sales_tax_rate / 100)

                # Total monthly payment
                monthly_payment = base_payment + monthly_tax

                # Convert money factor to APR equivalent
                apr_equivalent = money_factor * 2400

                # Total lease cost
                total_lease_cost = (monthly_payment * lease_term) + down_payment + acquisition_fee
                total_depreciation = adjusted_cap_cost - residual_value
                total_finance_charges = finance_charge * lease_term
                total_taxes = monthly_tax * lease_term

                # Cost per mile (assuming 12,000 miles/year)
                miles_per_year = 12000
                total_miles = miles_per_year * (lease_term / 12)
                cost_per_mile = total_lease_cost / total_miles if total_miles > 0 else 0

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input': {
                        'msrp': round(msrp, 2),
                        'negotiated_price': round(negotiated_price, 2),
                        'discount': round(msrp - negotiated_price, 2),
                        'discount_percent': round((msrp - negotiated_price) / msrp * 100, 1) if msrp > 0 else 0,
                        'down_payment': round(down_payment, 2),
                        'lease_term': lease_term,
                        'residual_percent': residual_percent,
                        'money_factor': money_factor,
                        'apr_equivalent': round(apr_equivalent, 2)
                    },
                    'capitalized_cost': {
                        'gross_cap_cost': round(gross_cap_cost, 2),
                        'cap_reduction': round(cap_cost_reduction, 2),
                        'adjusted_cap_cost': round(adjusted_cap_cost, 2),
                        'residual_value': round(residual_value, 2)
                    },
                    'monthly_breakdown': {
                        'depreciation': round(depreciation, 2),
                        'finance_charge': round(finance_charge, 2),
                        'base_payment': round(base_payment, 2),
                        'sales_tax': round(monthly_tax, 2),
                        'total_payment': round(monthly_payment, 2)
                    },
                    'totals': {
                        'total_payments': round(monthly_payment * lease_term, 2),
                        'total_depreciation': round(total_depreciation, 2),
                        'total_finance_charges': round(total_finance_charges, 2),
                        'total_taxes': round(total_taxes, 2),
                        'total_lease_cost': round(total_lease_cost, 2),
                        'cost_per_mile': round(cost_per_mile, 4)
                    },
                    'drive_off': {
                        'first_payment': round(monthly_payment, 2),
                        'down_payment': round(down_payment, 2),
                        'acquisition_fee': round(acquisition_fee, 2),
                        'doc_fee': round(doc_fee, 2),
                        'total_due_at_signing': round(monthly_payment + down_payment + acquisition_fee + doc_fee, 2)
                    }
                }

            elif calc_type == 'lease_vs_buy':
                # Compare lease vs buy
                msrp = float(str(data.get('msrp', 0)).replace(',', ''))
                negotiated_price = float(str(data.get('negotiated_price', 0)).replace(',', ''))
                down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
                
                # Lease terms
                lease_term = int(data.get('lease_term', 36))
                residual_percent = float(str(data.get('residual_percent', 55)).replace(',', ''))
                money_factor = float(str(data.get('money_factor', 0.00125)).replace(',', ''))
                
                # Buy terms
                loan_term = int(data.get('loan_term', 60))
                loan_rate = float(str(data.get('loan_rate', 6)).replace(',', ''))
                
                # Ownership period for comparison
                ownership_years = int(data.get('ownership_years', 5))

                if msrp <= 0:
                    return JsonResponse({'success': False, 'error': 'MSRP must be greater than zero.'}, status=400)
                if negotiated_price <= 0:
                    negotiated_price = msrp

                # LEASE CALCULATION
                residual_value = msrp * (residual_percent / 100)
                adjusted_cap_cost = negotiated_price - down_payment
                depreciation = (adjusted_cap_cost - residual_value) / lease_term
                finance_charge = (adjusted_cap_cost + residual_value) * money_factor
                lease_payment = depreciation + finance_charge
                
                # Number of leases in ownership period
                num_leases = ownership_years * 12 / lease_term
                total_lease_cost = (lease_payment * lease_term + down_payment) * num_leases
                lease_end_value = 0  # You don't own anything at the end

                # BUY CALCULATION
                loan_amount = negotiated_price - down_payment
                monthly_rate = loan_rate / 100 / 12
                
                if monthly_rate > 0:
                    buy_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    buy_payment = loan_amount / loan_term

                total_buy_payments = buy_payment * loan_term + down_payment
                
                # Estimated value after ownership period (simple depreciation)
                annual_depreciation_rate = 0.15  # 15% per year
                end_value = negotiated_price * np.power(1 - annual_depreciation_rate, ownership_years)
                
                total_buy_cost = total_buy_payments
                net_buy_cost = total_buy_cost - end_value

                # Comparison
                savings = total_lease_cost - net_buy_cost

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'ownership_years': ownership_years,
                    'lease': {
                        'monthly_payment': round(lease_payment, 2),
                        'term_months': lease_term,
                        'number_of_leases': round(num_leases, 1),
                        'total_cost': round(total_lease_cost, 2),
                        'end_value': 0
                    },
                    'buy': {
                        'monthly_payment': round(buy_payment, 2),
                        'term_months': loan_term,
                        'total_payments': round(total_buy_payments, 2),
                        'estimated_end_value': round(end_value, 2),
                        'net_cost': round(net_buy_cost, 2)
                    },
                    'comparison': {
                        'lease_total': round(total_lease_cost, 2),
                        'buy_net_total': round(net_buy_cost, 2),
                        'difference': round(abs(savings), 2),
                        'recommendation': 'Buying is cheaper' if savings > 0 else 'Leasing is cheaper'
                    }
                }

            elif calc_type == 'money_factor_convert':
                # Convert between money factor and APR
                input_value = float(str(data.get('input_value', 0)).replace(',', ''))
                convert_from = data.get('convert_from', 'money_factor')  # 'money_factor' or 'apr'

                if convert_from == 'money_factor':
                    money_factor = input_value
                    apr = money_factor * 2400
                else:
                    apr = input_value
                    money_factor = apr / 2400

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'money_factor': round(money_factor, 6),
                    'apr': round(apr, 2),
                    'formula': 'APR = Money Factor × 2400'
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
