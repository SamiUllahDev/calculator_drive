from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class LeaseCalculator(View):
    """
    Class-based view for General Lease Calculator
    Calculates equipment/property lease payments with buy vs lease analysis.
    """
    template_name = 'financial_calculators/lease_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Lease Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for lease calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'equipment_lease')

            if calc_type == 'equipment_lease':
                # Equipment lease calculation
                equipment_cost = float(str(data.get('equipment_cost', 0)).replace(',', ''))
                lease_term = int(data.get('lease_term', 36))  # months
                residual_value = float(str(data.get('residual_value', 0)).replace(',', ''))
                residual_type = data.get('residual_type', 'amount')  # 'amount' or 'percent'
                interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
                advance_payments = int(data.get('advance_payments', 1))  # Usually 1-2 months
                security_deposit = float(str(data.get('security_deposit', 0)).replace(',', ''))
                lease_type = data.get('lease_type', 'fmv')  # 'fmv' (Fair Market Value) or 'dollar_buyout'

                if equipment_cost <= 0:
                    return JsonResponse({'success': False, 'error': 'Equipment cost must be greater than zero.'}, status=400)
                if lease_term <= 0:
                    return JsonResponse({'success': False, 'error': 'Lease term must be greater than zero.'}, status=400)

                # Calculate residual value
                if residual_type == 'percent':
                    residual_amount = equipment_cost * (residual_value / 100)
                else:
                    residual_amount = residual_value

                # For $1 buyout leases
                if lease_type == 'dollar_buyout':
                    residual_amount = 1

                # Amount to finance (depreciation)
                amount_to_finance = equipment_cost - residual_amount

                # Calculate monthly payment using PMT formula
                monthly_rate = interest_rate / 100 / 12
                
                if monthly_rate > 0:
                    # Present value of payments needed
                    pv_factor = (1 - np.power(1 + monthly_rate, -lease_term)) / monthly_rate
                    monthly_payment = amount_to_finance / pv_factor
                else:
                    monthly_payment = amount_to_finance / lease_term

                # Total of all payments
                total_payments = monthly_payment * lease_term
                total_interest = total_payments - amount_to_finance

                # Due at signing
                due_at_signing = (monthly_payment * advance_payments) + security_deposit

                # Generate payment schedule
                schedule = []
                for month in range(1, lease_term + 1):
                    if month <= 12 or month % 12 == 0 or month == lease_term:
                        schedule.append({
                            'month': month,
                            'payment': round(monthly_payment, 2),
                            'cumulative': round(monthly_payment * month, 2)
                        })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'lease_type': 'Fair Market Value (FMV)' if lease_type == 'fmv' else '$1 Buyout',
                    'equipment_cost': round(equipment_cost, 2),
                    'residual_value': round(residual_amount, 2),
                    'residual_percent': round(residual_amount / equipment_cost * 100, 1) if equipment_cost > 0 else 0,
                    'amount_financed': round(amount_to_finance, 2),
                    'interest_rate': interest_rate,
                    'lease_term': lease_term,
                    'lease_term_years': round(lease_term / 12, 1),
                    'monthly_payment': round(monthly_payment, 2),
                    'total_payments': round(total_payments, 2),
                    'total_interest': round(total_interest, 2),
                    'advance_payments': advance_payments,
                    'security_deposit': round(security_deposit, 2),
                    'due_at_signing': round(due_at_signing, 2),
                    'buyout_at_end': round(residual_amount, 2),
                    'schedule': schedule
                }

            elif calc_type == 'property_lease':
                # Commercial property lease
                monthly_rent = float(str(data.get('monthly_rent', 0)).replace(',', ''))
                lease_term = int(data.get('lease_term', 12))  # months
                annual_increase = float(str(data.get('annual_increase', 0)).replace(',', ''))
                security_deposit_months = int(data.get('security_deposit_months', 2))
                cam_charges = float(str(data.get('cam_charges', 0)).replace(',', ''))  # Common Area Maintenance
                utilities = float(str(data.get('utilities', 0)).replace(',', ''))
                lease_structure = data.get('lease_structure', 'gross')  # 'gross', 'net', 'triple_net'

                if monthly_rent <= 0:
                    return JsonResponse({'success': False, 'error': 'Monthly rent must be greater than zero.'}, status=400)

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
                # Lease vs Buy analysis for equipment
                equipment_cost = float(str(data.get('equipment_cost', 0)).replace(',', ''))
                useful_life = int(data.get('useful_life', 60))  # months
                
                # Lease option
                lease_payment = float(str(data.get('lease_payment', 0)).replace(',', ''))
                lease_term = int(data.get('lease_term', 36))
                lease_residual = float(str(data.get('lease_residual', 0)).replace(',', ''))
                
                # Buy option
                loan_rate = float(str(data.get('loan_rate', 0)).replace(',', ''))
                down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
                salvage_value = float(str(data.get('salvage_value', 0)).replace(',', ''))
                tax_rate = float(str(data.get('tax_rate', 0)).replace(',', ''))  # For depreciation benefits

                if equipment_cost <= 0:
                    return JsonResponse({'success': False, 'error': 'Equipment cost must be greater than zero.'}, status=400)

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
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
