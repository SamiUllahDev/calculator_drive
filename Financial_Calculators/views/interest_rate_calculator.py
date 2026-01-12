from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class InterestRateCalculator(View):
    """
    Class-based view for Interest Rate Calculator
    Calculates interest rate from loan terms or converts between rates.
    """
    template_name = 'financial_calculators/interest_rate_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Interest Rate Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for interest rate calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'find_rate')

            if calc_type == 'find_rate':
                # Find interest rate from loan amount, payment, and term
                loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
                monthly_payment = float(str(data.get('monthly_payment', 0)).replace(',', ''))
                loan_term = int(data.get('loan_term', 60))  # months

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)
                if monthly_payment <= 0:
                    return JsonResponse({'success': False, 'error': 'Monthly payment must be greater than zero.'}, status=400)
                if loan_term <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan term must be greater than zero.'}, status=400)

                # Newton-Raphson method to find rate
                rate = 0.05 / 12  # Initial guess (5% annual)
                
                for _ in range(100):
                    # PMT formula: P * r(1+r)^n / ((1+r)^n - 1) = payment
                    if rate > 0:
                        term = np.power(1 + rate, loan_term)
                        payment_calc = loan_amount * rate * term / (term - 1)
                        
                        # Derivative of PMT with respect to r
                        dpmt_dr = loan_amount * (term * (term - 1 - loan_term * rate) / 
                                                np.power(term - 1, 2))
                    else:
                        payment_calc = loan_amount / loan_term
                        dpmt_dr = 0
                    
                    diff = payment_calc - monthly_payment
                    
                    if abs(diff) < 0.0001:
                        break
                    
                    if dpmt_dr != 0:
                        rate = rate - diff / dpmt_dr
                    
                    # Keep rate in bounds
                    rate = max(0.0001, min(rate, 0.5))

                annual_rate = rate * 12 * 100
                
                # Calculate totals at found rate
                total_payments = monthly_payment * loan_term
                total_interest = total_payments - loan_amount

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_amount': round(loan_amount, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'loan_term_months': loan_term,
                    'loan_term_years': round(loan_term / 12, 1),
                    'monthly_rate': round(rate * 100, 4),
                    'annual_rate': round(annual_rate, 2),
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2)
                }

            elif calc_type == 'apr_to_apy':
                # Convert APR to APY (and vice versa)
                input_rate = float(str(data.get('rate', 0)).replace(',', ''))
                compounding_frequency = int(data.get('compounding_frequency', 12))  # times per year
                direction = data.get('direction', 'apr_to_apy')  # apr_to_apy or apy_to_apr

                if input_rate < 0:
                    return JsonResponse({'success': False, 'error': 'Rate cannot be negative.'}, status=400)
                if compounding_frequency <= 0:
                    return JsonResponse({'success': False, 'error': 'Compounding frequency must be greater than zero.'}, status=400)

                if direction == 'apr_to_apy':
                    apr = input_rate
                    # APY = (1 + APR/n)^n - 1
                    apy = (np.power(1 + apr/100/compounding_frequency, compounding_frequency) - 1) * 100
                    
                    result = {
                        'success': True,
                        'calc_type': calc_type,
                        'direction': 'APR to APY',
                        'apr': round(apr, 4),
                        'apy': round(apy, 4),
                        'compounding_frequency': compounding_frequency,
                        'formula': 'APY = (1 + APR/n)^n - 1',
                        'difference': round(apy - apr, 4)
                    }
                else:
                    apy = input_rate
                    # APR = n * ((1 + APY)^(1/n) - 1)
                    apr = compounding_frequency * (np.power(1 + apy/100, 1/compounding_frequency) - 1) * 100
                    
                    result = {
                        'success': True,
                        'calc_type': calc_type,
                        'direction': 'APY to APR',
                        'apy': round(apy, 4),
                        'apr': round(apr, 4),
                        'compounding_frequency': compounding_frequency,
                        'formula': 'APR = n × ((1 + APY)^(1/n) - 1)',
                        'difference': round(apy - apr, 4)
                    }

            elif calc_type == 'effective_rate':
                # Calculate effective interest rate with fees
                nominal_rate = float(str(data.get('nominal_rate', 0)).replace(',', ''))
                loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
                loan_term = int(data.get('loan_term', 60))  # months
                origination_fee = float(str(data.get('origination_fee', 0)).replace(',', ''))
                points = float(str(data.get('points', 0)).replace(',', ''))  # percentage
                other_fees = float(str(data.get('other_fees', 0)).replace(',', ''))

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)

                # Calculate total fees
                points_cost = loan_amount * (points / 100)
                total_fees = origination_fee + points_cost + other_fees
                
                # Net loan proceeds
                net_proceeds = loan_amount - total_fees

                # Calculate monthly payment based on nominal rate
                monthly_rate = nominal_rate / 100 / 12
                if monthly_rate > 0:
                    monthly_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    monthly_payment = loan_amount / loan_term

                # Find effective rate (rate that gives same payment with net proceeds)
                eff_rate = monthly_rate
                
                for _ in range(100):
                    if eff_rate > 0:
                        term = np.power(1 + eff_rate, loan_term)
                        payment_calc = net_proceeds * eff_rate * term / (term - 1)
                        dpmt_dr = net_proceeds * (term * (term - 1 - loan_term * eff_rate) / np.power(term - 1, 2))
                    else:
                        payment_calc = net_proceeds / loan_term
                        dpmt_dr = 0
                    
                    diff = payment_calc - monthly_payment
                    
                    if abs(diff) < 0.0001:
                        break
                    
                    if dpmt_dr != 0:
                        eff_rate = eff_rate - diff / dpmt_dr
                    
                    eff_rate = max(0.0001, min(eff_rate, 0.5))

                effective_annual_rate = eff_rate * 12 * 100

                # Total cost analysis
                total_payments = monthly_payment * loan_term
                total_interest_nominal = total_payments - loan_amount
                total_cost = total_payments + total_fees

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_amount': round(loan_amount, 2),
                    'nominal_rate': round(nominal_rate, 2),
                    'fees': {
                        'origination': round(origination_fee, 2),
                        'points': round(points_cost, 2),
                        'points_percent': points,
                        'other': round(other_fees, 2),
                        'total': round(total_fees, 2)
                    },
                    'net_proceeds': round(net_proceeds, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'effective_rate': round(effective_annual_rate, 2),
                    'rate_difference': round(effective_annual_rate - nominal_rate, 2),
                    'total_interest': round(total_interest_nominal, 2),
                    'total_cost': round(total_cost, 2)
                }

            elif calc_type == 'compare_rates':
                # Compare different interest rates
                loan_amount = float(str(data.get('loan_amount', 0)).replace(',', ''))
                loan_term = int(data.get('loan_term', 60))
                rates = data.get('rates', [5, 6, 7, 8, 9])

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': 'Loan amount must be greater than zero.'}, status=400)

                try:
                    rate_list = [float(str(r).replace(',', '')) for r in rates]
                except:
                    rate_list = [5, 6, 7, 8, 9]

                comparisons = []
                for rate in rate_list:
                    monthly_rate = rate / 100 / 12
                    
                    if monthly_rate > 0:
                        monthly_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                    else:
                        monthly_payment = loan_amount / loan_term
                    
                    total_payments = monthly_payment * loan_term
                    total_interest = total_payments - loan_amount
                    
                    comparisons.append({
                        'rate': rate,
                        'monthly_payment': round(monthly_payment, 2),
                        'total_interest': round(total_interest, 2),
                        'total_cost': round(total_payments, 2)
                    })

                # Calculate savings between lowest and highest rate
                if len(comparisons) >= 2:
                    lowest = min(comparisons, key=lambda x: x['rate'])
                    highest = max(comparisons, key=lambda x: x['rate'])
                    savings = {
                        'monthly': round(highest['monthly_payment'] - lowest['monthly_payment'], 2),
                        'total_interest': round(highest['total_interest'] - lowest['total_interest'], 2),
                        'rate_spread': round(highest['rate'] - lowest['rate'], 2)
                    }
                else:
                    savings = None

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'loan_amount': round(loan_amount, 2),
                    'loan_term_months': loan_term,
                    'loan_term_years': round(loan_term / 12, 1),
                    'comparisons': comparisons,
                    'savings': savings
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
