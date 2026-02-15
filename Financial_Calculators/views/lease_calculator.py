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
class LeaseCalculator(View):
    """
    Class-based view for General Lease Calculator.
    Calculates equipment/property lease payments; uses NumPy for finance math; returns Chart.js chart_data (BMI-style).
    """
    template_name = 'financial_calculators/lease_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Lease Calculator'))}
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

            calc_type = data.get('calc_type', 'equipment_lease')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'equipment_lease'

            if calc_type == 'equipment_lease':
                equipment_cost = self._get_float(data, 'equipment_cost', 0)
                lease_term = self._get_int(data, 'lease_term', 36)
                residual_value = self._get_float(data, 'residual_value', 0)
                residual_type = data.get('residual_type', 'amount')
                if isinstance(residual_type, list):
                    residual_type = residual_type[0] if residual_type else 'amount'
                interest_rate = self._get_float(data, 'interest_rate', 0)
                advance_payments = self._get_int(data, 'advance_payments', 1)
                security_deposit = self._get_float(data, 'security_deposit', 0)
                lease_type = data.get('lease_type', 'fmv')
                if isinstance(lease_type, list):
                    lease_type = lease_type[0] if lease_type else 'fmv'

                if equipment_cost <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Equipment cost must be greater than zero.'))}, status=400)
                if lease_term <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Lease term must be greater than zero.'))}, status=400)

                residual_amount = (equipment_cost * (residual_value / 100.0) if residual_type == 'percent' else residual_value)
                if lease_type == 'dollar_buyout':
                    residual_amount = 1.0

                amount_to_finance = equipment_cost - residual_amount
                monthly_rate = interest_rate / 100.0 / 12.0

                if monthly_rate > 0:
                    pv_factor = (1.0 - np.power(1.0 + monthly_rate, -lease_term)) / monthly_rate
                    monthly_payment = float(amount_to_finance / pv_factor)
                else:
                    monthly_payment = amount_to_finance / lease_term

                total_payments = monthly_payment * lease_term
                total_interest = total_payments - amount_to_finance
                due_at_signing = (monthly_payment * advance_payments) + security_deposit

                # Amortization for first 12 months (NumPy-friendly) for chart
                schedule_12 = []
                balance = amount_to_finance
                for month in range(1, min(13, lease_term + 1)):
                    interest_pmt = balance * monthly_rate
                    principal_pmt = monthly_payment - interest_pmt
                    balance = max(0.0, balance - principal_pmt)
                    schedule_12.append({
                        'month': month,
                        'payment': round(monthly_payment, 2),
                        'principal': round(principal_pmt, 2),
                        'interest': round(interest_pmt, 2),
                        'balance': round(balance, 2),
                        'cumulative': round(monthly_payment * month, 2)
                    })

                schedule = []
                for month in range(1, lease_term + 1):
                    if month <= 12 or month % 12 == 0 or month == lease_term:
                        schedule.append({
                            'month': month,
                            'payment': round(monthly_payment, 2),
                            'cumulative': round(monthly_payment * month, 2)
                        })

                interest_pct = (total_interest / total_payments * 100) if total_payments > 0 else 0
                summary = {
                    'equipment_cost': round(equipment_cost, 2),
                    'residual_value': round(residual_amount, 2),
                    'residual_percent': round(residual_amount / equipment_cost * 100, 1) if equipment_cost > 0 else 0,
                    'amount_financed': round(amount_to_finance, 2),
                    'interest_rate': round(interest_rate, 2),
                    'lease_term': lease_term,
                    'lease_term_years': round(lease_term / 12, 1),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'interest_pct': round(interest_pct, 1),
                    'advance_payments': advance_payments,
                    'security_deposit': round(security_deposit, 2),
                    'due_at_signing': round(due_at_signing, 2),
                    'buyout_at_end': round(residual_amount, 2)
                }
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'lease_type': str(_('Fair Market Value (FMV)')) if lease_type == 'fmv' else str(_('$1 Buyout')),
                    'summary': summary,
                    'schedule': schedule,
                    'schedule_12': schedule_12
                }
                result['chart_data'] = self._prepare_chart_data(
                    amount_to_finance, total_interest, schedule_12
                )
                return JsonResponse(result, encoder=DjangoJSONEncoder)

            elif calc_type == 'property_lease':
                monthly_rent = self._get_float(data, 'monthly_rent', 0)
                lease_term = self._get_int(data, 'lease_term', 12)
                annual_increase = self._get_float(data, 'annual_increase', 0)
                security_deposit_months = self._get_int(data, 'security_deposit_months', 2)
                cam_charges = self._get_float(data, 'cam_charges', 0)
                utilities = self._get_float(data, 'utilities', 0)
                lease_structure = data.get('lease_structure', 'gross')
                if isinstance(lease_structure, list):
                    lease_structure = lease_structure[0] if lease_structure else 'gross'

                if monthly_rent <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Monthly rent must be greater than zero.'))}, status=400)

                security_deposit = monthly_rent * security_deposit_months

                # Calculate total rent over lease term with annual increases
                total_rent = 0
                current_rent = monthly_rent
                rent_schedule = []
                
                for year in range(1, int(np.ceil(lease_term / 12)) + 1):
                    months_in_year = min(12, lease_term - (year - 1) * 12)
                    if months_in_year <= 0:
                        break
                    
                    yearly_rent = current_rent * months_in_year
                    total_rent += yearly_rent
                    
                    rent_schedule.append({
                        'year': year,
                        'monthly_rent': round(current_rent, 2),
                        'annual_rent': round(current_rent * 12, 2),
                        'months': months_in_year
                    })
                    
                    current_rent *= (1 + annual_increase / 100)

                # Total monthly costs
                if lease_structure == 'gross':
                    total_monthly = monthly_rent
                    additional_costs = 0
                elif lease_structure == 'net':
                    total_monthly = monthly_rent + cam_charges
                    additional_costs = cam_charges
                else:  # triple_net
                    total_monthly = monthly_rent + cam_charges + utilities
                    additional_costs = cam_charges + utilities

                total_additional = additional_costs * lease_term
                total_cost = total_rent + total_additional

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'lease_structure': lease_structure.replace('_', ' ').title(),
                    'base_monthly_rent': round(monthly_rent, 2),
                    'annual_base_rent': round(monthly_rent * 12, 2),
                    'lease_term_months': lease_term,
                    'lease_term_years': round(lease_term / 12, 1),
                    'annual_increase': annual_increase,
                    'security_deposit': round(security_deposit, 2),
                    'cam_charges': round(cam_charges, 2),
                    'utilities': round(utilities, 2),
                    'total_monthly_cost': round(total_monthly, 2),
                    'total_rent': round(total_rent, 2),
                    'total_additional_costs': round(total_additional, 2),
                    'total_lease_cost': round(total_cost, 2),
                    'due_at_signing': round(monthly_rent + security_deposit, 2),
                    'rent_schedule': rent_schedule
                }

            elif calc_type == 'lease_vs_buy':
                equipment_cost = self._get_float(data, 'equipment_cost', 0)
                useful_life = self._get_int(data, 'useful_life', 60)
                lease_payment = self._get_float(data, 'lease_payment', 0)
                lease_term = self._get_int(data, 'lease_term', 36)
                lease_residual = self._get_float(data, 'lease_residual', 0)
                loan_rate = self._get_float(data, 'loan_rate', 0)
                down_payment = self._get_float(data, 'down_payment', 0)
                salvage_value = self._get_float(data, 'salvage_value', 0)
                tax_rate = self._get_float(data, 'tax_rate', 0)

                if equipment_cost <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Equipment cost must be greater than zero.'))}, status=400)

                # LEASE ANALYSIS
                total_lease_payments = lease_payment * lease_term
                lease_buyout = lease_residual if lease_residual > 0 else 0
                total_lease_cost = total_lease_payments + lease_buyout
                
                # Tax benefit of lease payments (fully deductible)
                lease_tax_benefit = total_lease_payments * (tax_rate / 100)
                net_lease_cost = total_lease_cost - lease_tax_benefit

                # BUY ANALYSIS
                loan_amount = equipment_cost - down_payment
                monthly_rate = loan_rate / 100 / 12
                loan_term = useful_life
                
                if monthly_rate > 0 and loan_amount > 0:
                    loan_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    loan_payment = loan_amount / loan_term if loan_term > 0 else 0

                total_loan_payments = loan_payment * loan_term
                total_interest = total_loan_payments - loan_amount
                
                # Depreciation tax benefit (straight-line over useful life)
                annual_depreciation = (equipment_cost - salvage_value) / (useful_life / 12)
                total_depreciation_benefit = annual_depreciation * (useful_life / 12) * (tax_rate / 100)
                
                total_buy_cost = down_payment + total_loan_payments - salvage_value
                net_buy_cost = total_buy_cost - total_depreciation_benefit

                # Comparison
                savings = net_lease_cost - net_buy_cost

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'equipment_cost': round(equipment_cost, 2),
                    'analysis_period_months': useful_life,
                    'lease_option': {
                        'monthly_payment': round(lease_payment, 2),
                        'term_months': lease_term,
                        'total_payments': round(total_lease_payments, 2),
                        'buyout': round(lease_buyout, 2),
                        'total_cost': round(total_lease_cost, 2),
                        'tax_benefit': round(lease_tax_benefit, 2),
                        'net_cost': round(net_lease_cost, 2)
                    },
                    'buy_option': {
                        'down_payment': round(down_payment, 2),
                        'loan_amount': round(loan_amount, 2),
                        'monthly_payment': round(loan_payment, 2),
                        'total_interest': round(total_interest, 2),
                        'salvage_value': round(salvage_value, 2),
                        'depreciation_benefit': round(total_depreciation_benefit, 2),
                        'total_cost': round(total_buy_cost, 2),
                        'net_cost': round(net_buy_cost, 2)
                    },
                    'comparison': {
                        'lease_net_cost': round(net_lease_cost, 2),
                        'buy_net_cost': round(net_buy_cost, 2),
                        'difference': round(abs(savings), 2),
                        'recommendation': 'Buying is better' if savings > 0 else 'Leasing is better'
                    }
                }

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, amount_financed, total_interest, schedule_12=None):
        """Backend-controlled chart data (BMI-style): breakdown doughnut + schedule stacked bar (NumPy)."""
        if amount_financed <= 0 and total_interest <= 0:
            return {}
        out = {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Amount Financed')), str(_('Interest'))],
                    'datasets': [{
                        'data': [round(amount_financed, 2), round(total_interest, 2)],
                        'backgroundColor': ['#0d9488', '#ef4444'],
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
            principals = [r['principal'] for r in schedule_12]
            interests = [r['interest'] for r in schedule_12]
            out['schedule_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': months,
                    'datasets': [
                        {
                            'label': str(_('Principal')),
                            'data': principals,
                            'backgroundColor': '#0d9488',
                            'borderRadius': 4,
                            'borderWidth': 0
                        },
                        {
                            'label': str(_('Interest')),
                            'data': interests,
                            'backgroundColor': '#ef4444',
                            'borderRadius': 4,
                            'borderWidth': 0
                        }
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
