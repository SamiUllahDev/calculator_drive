from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class InterestRateCalculator(View):
    """
    Class-based view for Interest Rate Calculator.
    Calculates interest rate from loan terms, converts APR/APY, effective rate with fees, compares rates.
    """
    template_name = 'financial_calculators/interest_rate_calculator.html'

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float from data (handles list, strips % and commas)."""
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
        """Safely get int from data (handles list)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def _unwrap(self, value):
        """Return first element if list, else value."""
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get(self, request):
        """Handle GET request."""
        context = {
            'calculator_name': _('Interest Rate Calculator'),
            'page_title': _('Interest Rate Calculator - Find APR, APY & Effective Rates'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            calc_type = self._unwrap(data.get('calc_type')) or 'find_rate'

            if calc_type == 'find_rate':
                loan_amount = self._get_float(data, 'loan_amount', 0)
                monthly_payment = self._get_float(data, 'monthly_payment', 0)
                loan_term = self._get_int(data, 'loan_term', 60)

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': _('Loan amount must be greater than zero.')}, status=400)
                if monthly_payment <= 0:
                    return JsonResponse({'success': False, 'error': _('Monthly payment must be greater than zero.')}, status=400)
                if loan_term <= 0:
                    return JsonResponse({'success': False, 'error': _('Loan term must be greater than zero.')}, status=400)

                rate = 0.05 / 12
                for _ in range(100):
                    if rate > 0:
                        term = np.power(1 + rate, loan_term)
                        payment_calc = loan_amount * rate * term / (term - 1)
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
                    rate = max(0.0001, min(rate, 0.5))

                annual_rate = rate * 12 * 100
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
                direction = self._unwrap(data.get('direction')) or 'apr_to_apy'
                input_rate = self._get_float(data, 'rate', 0)
                compounding_frequency = self._get_int(data, 'compounding_frequency', 12)

                if input_rate < 0:
                    return JsonResponse({'success': False, 'error': _('Rate cannot be negative.')}, status=400)
                if compounding_frequency <= 0:
                    return JsonResponse({'success': False, 'error': _('Compounding frequency must be greater than zero.')}, status=400)

                if direction == 'apr_to_apy':
                    apr = input_rate
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
                nominal_rate = self._get_float(data, 'nominal_rate', 0)
                loan_amount = self._get_float(data, 'loan_amount', 0)
                loan_term = self._get_int(data, 'loan_term', 60)
                origination_fee = self._get_float(data, 'origination_fee', 0)
                points = self._get_float(data, 'points', 0)
                other_fees = self._get_float(data, 'other_fees', 0)

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': _('Loan amount must be greater than zero.')}, status=400)

                points_cost = loan_amount * (points / 100)
                total_fees = origination_fee + points_cost + other_fees
                net_proceeds = loan_amount - total_fees

                monthly_rate = nominal_rate / 100 / 12
                if monthly_rate > 0:
                    monthly_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    monthly_payment = loan_amount / loan_term

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
                loan_amount = self._get_float(data, 'loan_amount', 0)
                loan_term = self._get_int(data, 'loan_term', 60)
                rates_raw = data.get('rates', [5, 6, 7, 8, 9])
                if not isinstance(rates_raw, list):
                    rates_raw = [rates_raw] if rates_raw not in (None, '', 'null') else [5, 6, 7, 8, 9]
                try:
                    rate_list = [self._get_float({'r': r}, 'r', 0) for r in rates_raw]
                    rate_list = [r for r in rate_list if r >= 0][:10] or [5, 6, 7, 8, 9]
                except (ValueError, TypeError):
                    rate_list = [5, 6, 7, 8, 9]

                if loan_amount <= 0:
                    return JsonResponse({'success': False, 'error': _('Loan amount must be greater than zero.')}, status=400)

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

                savings = None
                if len(comparisons) >= 2:
                    lowest = min(comparisons, key=lambda x: x['rate'])
                    highest = max(comparisons, key=lambda x: x['rate'])
                    savings = {
                        'monthly': round(highest['monthly_payment'] - lowest['monthly_payment'], 2),
                        'total_interest': round(highest['total_interest'] - lowest['total_interest'], 2),
                        'rate_spread': round(highest['rate'] - lowest['rate'], 2)
                    }

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
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
