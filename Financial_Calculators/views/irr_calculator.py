from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class IrrCalculator(View):
    """
    Class-based view for IRR (Internal Rate of Return) Calculator
    Calculates IRR, NPV, and payback period for investment analysis.
    """
    template_name = 'financial_calculators/irr_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'IRR Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for IRR calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'irr')

            if calc_type == 'irr':
                # Calculate IRR from cash flows
                initial_investment = float(str(data.get('initial_investment', 0)).replace(',', ''))
                cash_flows = data.get('cash_flows', [])
                discount_rate = float(str(data.get('discount_rate', 10)).replace(',', ''))

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': 'Initial investment must be greater than zero.'}, status=400)
                if not cash_flows or len(cash_flows) == 0:
                    return JsonResponse({'success': False, 'error': 'Please provide at least one cash flow.'}, status=400)

                # Convert cash flows to floats
                try:
                    cash_flow_values = [float(str(cf).replace(',', '')) for cf in cash_flows]
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid cash flow values.'}, status=400)

                # All cash flows including initial investment (negative)
                all_cash_flows = [-initial_investment] + cash_flow_values

                # Calculate IRR using Newton-Raphson method
                irr = self._calculate_irr(all_cash_flows)

                # Calculate NPV at given discount rate
                npv = self._calculate_npv(all_cash_flows, discount_rate / 100)

                # Calculate payback period
                payback_period, discounted_payback = self._calculate_payback(initial_investment, cash_flow_values, discount_rate / 100)

                # Profitability Index
                pv_cash_flows = sum([cf / np.power(1 + discount_rate/100, i+1) for i, cf in enumerate(cash_flow_values)])
                profitability_index = pv_cash_flows / initial_investment if initial_investment > 0 else 0

                # Total return
                total_cash_inflows = sum(cash_flow_values)
                total_return = ((total_cash_inflows - initial_investment) / initial_investment * 100) if initial_investment > 0 else 0

                # Cash flow analysis
                cash_flow_analysis = []
                cumulative = -initial_investment
                cumulative_discounted = -initial_investment
                
                for i, cf in enumerate(cash_flow_values):
                    cumulative += cf
                    discounted_cf = cf / np.power(1 + discount_rate/100, i+1)
                    cumulative_discounted += discounted_cf
                    
                    cash_flow_analysis.append({
                        'period': i + 1,
                        'cash_flow': round(cf, 2),
                        'discounted_cf': round(discounted_cf, 2),
                        'cumulative': round(cumulative, 2),
                        'cumulative_discounted': round(cumulative_discounted, 2)
                    })

                # Investment decision
                if irr is not None:
                    if irr > discount_rate:
                        decision = "Accept - IRR exceeds required return"
                        decision_class = "positive"
                    elif irr == discount_rate:
                        decision = "Indifferent - IRR equals required return"
                        decision_class = "neutral"
                    else:
                        decision = "Reject - IRR below required return"
                        decision_class = "negative"
                else:
                    decision = "Unable to calculate IRR"
                    decision_class = "neutral"

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'num_periods': len(cash_flow_values),
                    'discount_rate': discount_rate,
                    'irr': round(irr, 2) if irr is not None else None,
                    'npv': round(npv, 2),
                    'payback_period': round(payback_period, 2) if payback_period else None,
                    'discounted_payback': round(discounted_payback, 2) if discounted_payback else None,
                    'profitability_index': round(profitability_index, 2),
                    'total_cash_inflows': round(total_cash_inflows, 2),
                    'total_return_percent': round(total_return, 2),
                    'decision': decision,
                    'decision_class': decision_class,
                    'cash_flow_analysis': cash_flow_analysis
                }

            elif calc_type == 'npv_sensitivity':
                # NPV Sensitivity Analysis at different discount rates
                initial_investment = float(str(data.get('initial_investment', 0)).replace(',', ''))
                cash_flows = data.get('cash_flows', [])

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': 'Initial investment must be greater than zero.'}, status=400)

                try:
                    cash_flow_values = [float(str(cf).replace(',', '')) for cf in cash_flows]
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid cash flow values.'}, status=400)

                all_cash_flows = [-initial_investment] + cash_flow_values

                # Calculate NPV at various rates
                sensitivity = []
                rates = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30]
                
                for rate in rates:
                    npv = self._calculate_npv(all_cash_flows, rate / 100)
                    sensitivity.append({
                        'rate': rate,
                        'npv': round(npv, 2)
                    })

                # Calculate IRR (where NPV = 0)
                irr = self._calculate_irr(all_cash_flows)

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'irr': round(irr, 2) if irr is not None else None,
                    'sensitivity': sensitivity,
                    'break_even_rate': round(irr, 2) if irr is not None else None
                }

            elif calc_type == 'compare_projects':
                # Compare multiple investment projects
                projects = data.get('projects', [])
                discount_rate = float(str(data.get('discount_rate', 10)).replace(',', ''))

                if not projects or len(projects) < 2:
                    return JsonResponse({'success': False, 'error': 'Please provide at least 2 projects to compare.'}, status=400)

                comparisons = []
                for i, project in enumerate(projects):
                    name = project.get('name', f'Project {i+1}')
                    initial = float(str(project.get('initial_investment', 0)).replace(',', ''))
                    cfs = [float(str(cf).replace(',', '')) for cf in project.get('cash_flows', [])]
                    
                    all_cfs = [-initial] + cfs
                    
                    irr = self._calculate_irr(all_cfs)
                    npv = self._calculate_npv(all_cfs, discount_rate / 100)
                    payback, _ = self._calculate_payback(initial, cfs, discount_rate / 100)
                    pi = sum([cf / np.power(1 + discount_rate/100, j+1) for j, cf in enumerate(cfs)]) / initial if initial > 0 else 0
                    
                    comparisons.append({
                        'name': name,
                        'initial_investment': round(initial, 2),
                        'irr': round(irr, 2) if irr is not None else None,
                        'npv': round(npv, 2),
                        'payback': round(payback, 2) if payback else None,
                        'profitability_index': round(pi, 2)
                    })

                # Rank by NPV
                ranked = sorted([c for c in comparisons if c['npv'] is not None], key=lambda x: x['npv'], reverse=True)
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'discount_rate': discount_rate,
                    'comparisons': comparisons,
                    'ranked_by_npv': [c['name'] for c in ranked],
                    'best_project': ranked[0]['name'] if ranked else None
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)

    def _calculate_irr(self, cash_flows, max_iterations=100, tolerance=0.0001):
        """Calculate IRR using Newton-Raphson method"""
        if len(cash_flows) < 2:
            return None

        # Initial guess
        rate = 0.1

        for _ in range(max_iterations):
            npv = sum([cf / np.power(1 + rate, i) for i, cf in enumerate(cash_flows)])
            
            # Derivative of NPV
            npv_derivative = sum([-i * cf / np.power(1 + rate, i + 1) for i, cf in enumerate(cash_flows)])
            
            if abs(npv_derivative) < 1e-10:
                break
                
            new_rate = rate - npv / npv_derivative
            
            if abs(new_rate - rate) < tolerance:
                return new_rate * 100
            
            rate = new_rate
            
            # Keep rate in reasonable bounds
            if rate < -0.99:
                rate = -0.99
            if rate > 10:
                rate = 10

        # Return last calculated rate if convergence not achieved
        return rate * 100 if abs(sum([cf / np.power(1 + rate, i) for i, cf in enumerate(cash_flows)])) < 1 else None

    def _calculate_npv(self, cash_flows, rate):
        """Calculate Net Present Value"""
        if rate == 0:
            return sum(cash_flows)
        return sum([cf / np.power(1 + rate, i) for i, cf in enumerate(cash_flows)])

    def _calculate_payback(self, initial_investment, cash_flows, rate):
        """Calculate payback period and discounted payback period"""
        # Simple payback
        cumulative = 0
        payback = None
        for i, cf in enumerate(cash_flows):
            cumulative += cf
            if cumulative >= initial_investment and payback is None:
                # Interpolate
                prev_cumulative = cumulative - cf
                fraction = (initial_investment - prev_cumulative) / cf if cf != 0 else 0
                payback = i + fraction

        # Discounted payback
        cumulative_discounted = 0
        discounted_payback = None
        for i, cf in enumerate(cash_flows):
            discounted_cf = cf / np.power(1 + rate, i + 1) if rate > 0 else cf
            cumulative_discounted += discounted_cf
            if cumulative_discounted >= initial_investment and discounted_payback is None:
                prev_cumulative = cumulative_discounted - discounted_cf
                fraction = (initial_investment - prev_cumulative) / discounted_cf if discounted_cf != 0 else 0
                discounted_payback = i + fraction

        return payback, discounted_payback
