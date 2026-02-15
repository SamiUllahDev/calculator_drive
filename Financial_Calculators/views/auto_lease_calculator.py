from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AutoLeaseCalculator(View):
    """
    Class-based view for Auto Lease Calculator.
    Calculates monthly car lease payments using money factor and residual; uses NumPy; returns Chart.js chart_data (BMI-style).
    """
    template_name = 'financial_calculators/auto_lease_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Auto Lease Calculator'))}
        return render(request, self.template_name, context)

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        return {}

    def _get_float(self, data, key, default=0.0):
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
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'calculate_payment')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'calculate_payment'

            if calc_type == 'calculate_payment':
                msrp = self._get_float(data, 'msrp', 0)
                negotiated_price = self._get_float(data, 'negotiated_price', 0)
                down_payment = self._get_float(data, 'down_payment', 0)
                trade_in_value = self._get_float(data, 'trade_in_value', 0)
                trade_in_payoff = self._get_float(data, 'trade_in_payoff', 0)
                lease_term = self._get_int(data, 'lease_term', 36)
                residual_percent = self._get_float(data, 'residual_percent', 0)
                money_factor = self._get_float(data, 'money_factor', 0)
                sales_tax_rate = self._get_float(data, 'sales_tax_rate', 0)
                acquisition_fee = self._get_float(data, 'acquisition_fee', 0)
                doc_fee = self._get_float(data, 'doc_fee', 0)
                rebates = self._get_float(data, 'rebates', 0)

                if msrp <= 0:
                    return JsonResponse({'success': False, 'error': str(_('MSRP must be greater than zero.'))}, status=400)
                if negotiated_price <= 0:
                    negotiated_price = msrp
                if lease_term <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Lease term must be greater than zero.'))}, status=400)
                if residual_percent <= 0 or residual_percent > 100:
                    return JsonResponse({'success': False, 'error': str(_('Residual value must be between 0 and 100%%.'))}, status=400)

                residual_value = msrp * (residual_percent / 100)
                trade_in_equity = max(0.0, trade_in_value - trade_in_payoff)
                trade_in_negative = max(0.0, trade_in_payoff - trade_in_value)

                gross_cap_cost = negotiated_price + acquisition_fee + doc_fee + trade_in_negative
                cap_cost_reduction = down_payment + trade_in_equity + rebates
                adjusted_cap_cost = gross_cap_cost - cap_cost_reduction

                depreciation = (adjusted_cap_cost - residual_value) / lease_term
                finance_charge = (adjusted_cap_cost + residual_value) * money_factor
                base_payment = depreciation + finance_charge
                monthly_tax = base_payment * (sales_tax_rate / 100)
                monthly_payment = base_payment + monthly_tax

                apr_equivalent = money_factor * 2400

                total_payments_arr = np.array([monthly_payment * lease_term])
                total_lease_cost = float(total_payments_arr[0]) + down_payment + acquisition_fee
                total_depreciation = adjusted_cap_cost - residual_value
                total_finance_charges = finance_charge * lease_term
                total_taxes = monthly_tax * lease_term

                miles_per_year = 12000
                total_miles = miles_per_year * (lease_term / 12.0)
                cost_per_mile = total_lease_cost / total_miles if total_miles > 0 else 0.0

                due_at_signing = monthly_payment + down_payment + acquisition_fee + doc_fee

                schedule_12 = []
                for month in range(1, min(13, lease_term + 1)):
                    schedule_12.append({
                        'month': month,
                        'depreciation': round(depreciation, 2),
                        'finance_charge': round(finance_charge, 2),
                        'sales_tax': round(monthly_tax, 2),
                        'total': round(monthly_payment, 2)
                    })

                summary = {
                    'monthly_payment': round(monthly_payment, 2),
                    'total_lease_cost': round(total_lease_cost, 2),
                    'total_due_at_signing': round(due_at_signing, 2),
                    'cost_per_mile': round(cost_per_mile, 4),
                    'lease_term': lease_term,
                    'down_payment': round(down_payment, 2),
                    'acquisition_fee': round(acquisition_fee, 2),
                    'doc_fee': round(doc_fee, 2),
                    'first_payment': round(monthly_payment, 2),
                    'gross_cap_cost': round(gross_cap_cost, 2),
                    'cap_reduction': round(cap_cost_reduction, 2),
                    'adjusted_cap_cost': round(adjusted_cap_cost, 2),
                    'residual_value': round(residual_value, 2),
                    'depreciation': round(depreciation, 2),
                    'finance_charge': round(finance_charge, 2),
                    'monthly_tax': round(monthly_tax, 2),
                    'total_depreciation': round(total_depreciation, 2),
                    'total_finance_charges': round(total_finance_charges, 2),
                    'total_taxes': round(total_taxes, 2),
                    'apr_equivalent': round(apr_equivalent, 2)
                }

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'summary': summary,
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
                        'total_due_at_signing': round(due_at_signing, 2)
                    },
                    'schedule_12': schedule_12
                }
                result['chart_data'] = self._prepare_chart_data(
                    total_depreciation, total_finance_charges, total_taxes, schedule_12
                )
                return JsonResponse(result, encoder=DjangoJSONEncoder)

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
                input_value = self._get_float(data, 'input_value', 0)
                convert_from = data.get('convert_from', 'money_factor')
                if isinstance(convert_from, list):
                    convert_from = convert_from[0] if convert_from else 'money_factor'

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
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, total_depreciation, total_finance_charges, total_taxes, schedule_12=None):
        """Backend-controlled chart data (BMI-style): cost breakdown doughnut + monthly breakdown stacked bar (NumPy)."""
        total = total_depreciation + total_finance_charges + total_taxes
        if total <= 0:
            return {}
        out = {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Depreciation')), str(_('Finance Charge')), str(_('Tax'))],
                    'datasets': [{
                        'data': [
                            round(total_depreciation, 2),
                            round(total_finance_charges, 2),
                            round(total_taxes, 2)
                        ],
                        'backgroundColor': ['#7c3aed', '#0d9488', '#f59e0b'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'cutout': '60%',
                    'plugins': {'legend': {'position': 'bottom'}}
                }
            }
        }
        if schedule_12:
            months = [str(_('Month')) + ' ' + str(r['month']) for r in schedule_12]
            dep_vals = [r['depreciation'] for r in schedule_12]
            fin_vals = [r['finance_charge'] for r in schedule_12]
            tax_vals = [r['sales_tax'] for r in schedule_12]
            out['schedule_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': months,
                    'datasets': [
                        {'label': str(_('Depreciation')), 'data': dep_vals, 'backgroundColor': '#7c3aed', 'borderRadius': 4, 'borderWidth': 0},
                        {'label': str(_('Finance Charge')), 'data': fin_vals, 'backgroundColor': '#0d9488', 'borderRadius': 4, 'borderWidth': 0},
                        {'label': str(_('Tax')), 'data': tax_vals, 'backgroundColor': '#f59e0b', 'borderRadius': 4, 'borderWidth': 0}
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {'stacked': True, 'grid': {'display': False}},
                        'y': {'stacked': True, 'beginAtZero': True}
                    },
                    'plugins': {'legend': {'position': 'top'}}
                }
            }
        return out
