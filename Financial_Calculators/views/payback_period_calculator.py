from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class PaybackPeriodCalculator(View):
    """
    Class-based view for Payback Period Calculator
    Calculates simple and discounted payback period for investments.
    """
    template_name = 'financial_calculators/payback_period_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Payback Period Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for payback period calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'simple')

            if calc_type == 'simple':
                # Simple payback with uniform cash flows
                initial_investment = float(str(data.get('initial_investment', 0)).replace(',', ''))
                annual_cash_flow = float(str(data.get('annual_cash_flow', 0)).replace(',', ''))

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': 'Initial investment must be greater than zero.'}, status=400)
                if annual_cash_flow <= 0:
                    return JsonResponse({'success': False, 'error': 'Annual cash flow must be greater than zero.'}, status=400)

                # Simple payback period
                payback_years = initial_investment / annual_cash_flow
                payback_months = (payback_years % 1) * 12

                # Generate yearly breakdown
                breakdown = []
                cumulative = 0
                year = 0
                
                while cumulative < initial_investment and year < 50:
                    year += 1
                    cumulative += annual_cash_flow
                    remaining = max(0, initial_investment - cumulative)
                    recovered = min(cumulative, initial_investment)
                    
                    breakdown.append({
                        'year': year,
                        'cash_flow': round(annual_cash_flow, 2),
                        'cumulative': round(cumulative, 2),
                        'remaining': round(remaining, 2),
                        'recovered_percent': round(recovered / initial_investment * 100, 1)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'annual_cash_flow': round(annual_cash_flow, 2),
                    'payback_years': round(payback_years, 2),
                    'payback_years_int': int(payback_years),
                    'payback_months': round(payback_months, 1),
                    'total_return': round(annual_cash_flow * int(np.ceil(payback_years)) - initial_investment, 2),
                    'breakdown': breakdown
                }

            elif calc_type == 'uneven':
                # Payback with uneven cash flows
                initial_investment = float(str(data.get('initial_investment', 0)).replace(',', ''))
                cash_flows = data.get('cash_flows', [])
                discount_rate = float(str(data.get('discount_rate', 0)).replace(',', ''))

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': 'Initial investment must be greater than zero.'}, status=400)
                if not cash_flows:
                    return JsonResponse({'success': False, 'error': 'Please provide cash flows.'}, status=400)

                try:
                    cash_flow_values = [float(str(cf).replace(',', '')) for cf in cash_flows]
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid cash flow values.'}, status=400)

                # Calculate simple payback
                cumulative = 0
                simple_payback = None
                breakdown = []
                
                for i, cf in enumerate(cash_flow_values):
                    cumulative += cf
                    recovered_percent = min(100, cumulative / initial_investment * 100)
                    remaining = max(0, initial_investment - cumulative)
                    
                    breakdown.append({
                        'year': i + 1,
                        'cash_flow': round(cf, 2),
                        'cumulative': round(cumulative, 2),
                        'remaining': round(remaining, 2),
                        'recovered_percent': round(recovered_percent, 1)
                    })
                    
                    if simple_payback is None and cumulative >= initial_investment:
                        # Calculate fractional year
                        prev_cumulative = cumulative - cf
                        if cf > 0:
                            fraction = (initial_investment - prev_cumulative) / cf
                            simple_payback = i + fraction
                        else:
                            simple_payback = i + 1

                # Calculate discounted payback
                discounted_payback = None
                cumulative_discounted = 0
                discounted_breakdown = []
                
                for i, cf in enumerate(cash_flow_values):
                    if discount_rate > 0:
                        discounted_cf = cf / np.power(1 + discount_rate/100, i + 1)
                    else:
                        discounted_cf = cf
                    
                    cumulative_discounted += discounted_cf
                    recovered_percent = min(100, cumulative_discounted / initial_investment * 100)
                    
                    discounted_breakdown.append({
                        'year': i + 1,
                        'cash_flow': round(cf, 2),
                        'discounted_cf': round(discounted_cf, 2),
                        'cumulative': round(cumulative_discounted, 2),
                        'recovered_percent': round(recovered_percent, 1)
                    })
                    
                    if discounted_payback is None and cumulative_discounted >= initial_investment:
                        prev_cumulative = cumulative_discounted - discounted_cf
                        if discounted_cf > 0:
                            fraction = (initial_investment - prev_cumulative) / discounted_cf
                            discounted_payback = i + fraction
                        else:
                            discounted_payback = i + 1

                total_cash_flows = sum(cash_flow_values)
                total_discounted = cumulative_discounted

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'discount_rate': discount_rate,
                    'num_periods': len(cash_flow_values),
                    'simple_payback': round(simple_payback, 2) if simple_payback else None,
                    'simple_payback_years': int(simple_payback) if simple_payback else None,
                    'simple_payback_months': round((simple_payback % 1) * 12, 1) if simple_payback else None,
                    'discounted_payback': round(discounted_payback, 2) if discounted_payback else None,
                    'discounted_payback_years': int(discounted_payback) if discounted_payback else None,
                    'discounted_payback_months': round((discounted_payback % 1) * 12, 1) if discounted_payback else None,
                    'total_cash_flows': round(total_cash_flows, 2),
                    'total_discounted': round(total_discounted, 2),
                    'net_return': round(total_cash_flows - initial_investment, 2),
                    'npv': round(total_discounted - initial_investment, 2),
                    'recovered': cumulative >= initial_investment,
                    'breakdown': breakdown,
                    'discounted_breakdown': discounted_breakdown
                }

            elif calc_type == 'target':
                # Calculate required annual cash flow for target payback
                initial_investment = float(str(data.get('initial_investment', 0)).replace(',', ''))
                target_payback = float(str(data.get('target_payback', 0)).replace(',', ''))
                discount_rate = float(str(data.get('discount_rate', 0)).replace(',', ''))

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': 'Initial investment must be greater than zero.'}, status=400)
                if target_payback <= 0:
                    return JsonResponse({'success': False, 'error': 'Target payback period must be greater than zero.'}, status=400)

                # Simple payback required cash flow
                required_annual = initial_investment / target_payback

                # Discounted payback required cash flow
                if discount_rate > 0:
                    # Calculate present value factor
                    r = discount_rate / 100
                    n = target_payback
                    pv_factor = (1 - np.power(1 + r, -n)) / r
                    required_annual_discounted = initial_investment / pv_factor
                else:
                    required_annual_discounted = required_annual

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'target_payback_years': target_payback,
                    'discount_rate': discount_rate,
                    'required_annual_simple': round(required_annual, 2),
                    'required_monthly_simple': round(required_annual / 12, 2),
                    'required_annual_discounted': round(required_annual_discounted, 2),
                    'required_monthly_discounted': round(required_annual_discounted / 12, 2)
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
