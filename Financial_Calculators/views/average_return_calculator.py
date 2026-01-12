from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class AverageReturnCalculator(View):
    """
    Class-based view for Average Return Calculator
    Calculates arithmetic mean, geometric mean, CAGR, and other return metrics.
    """
    template_name = 'financial_calculators/average_return_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Average Return Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for average return calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'returns')

            if calc_type == 'returns':
                # Calculate average returns from periodic returns
                returns = data.get('returns', [])
                
                if not returns or len(returns) < 2:
                    return JsonResponse({'success': False, 'error': 'Please provide at least 2 return values.'}, status=400)

                try:
                    return_values = [float(str(r).replace(',', '').replace('%', '')) for r in returns]
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid return values.'}, status=400)

                # Convert percentages to decimals for calculations
                return_decimals = [r / 100 for r in return_values]

                # Arithmetic Mean
                arithmetic_mean = np.mean(return_values)

                # Geometric Mean (compound annual growth rate for single period returns)
                # Formula: ((1+r1)*(1+r2)*...*(1+rn))^(1/n) - 1
                product = np.prod([1 + r for r in return_decimals])
                if product > 0:
                    geometric_mean = (np.power(product, 1/len(return_decimals)) - 1) * 100
                else:
                    geometric_mean = None

                # Standard Deviation
                std_dev = np.std(return_values, ddof=1)  # Sample std dev

                # Variance
                variance = np.var(return_values, ddof=1)

                # Coefficient of Variation
                cv = (std_dev / arithmetic_mean * 100) if arithmetic_mean != 0 else None

                # Min and Max returns
                min_return = min(return_values)
                max_return = max(return_values)
                range_return = max_return - min_return

                # Growth of $10,000
                initial_value = 10000
                growth_values = [initial_value]
                current_value = initial_value
                for r in return_decimals:
                    current_value *= (1 + r)
                    growth_values.append(round(current_value, 2))

                final_value = growth_values[-1]
                total_return = ((final_value - initial_value) / initial_value) * 100

                # Period-by-period analysis
                period_analysis = []
                cumulative_value = initial_value
                for i, r in enumerate(return_values):
                    previous_value = cumulative_value
                    cumulative_value *= (1 + r/100)
                    gain_loss = cumulative_value - previous_value
                    
                    period_analysis.append({
                        'period': i + 1,
                        'return_percent': round(r, 2),
                        'starting_value': round(previous_value, 2),
                        'gain_loss': round(gain_loss, 2),
                        'ending_value': round(cumulative_value, 2)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'num_periods': len(return_values),
                    'returns': [round(r, 2) for r in return_values],
                    'arithmetic_mean': round(arithmetic_mean, 2),
                    'geometric_mean': round(geometric_mean, 2) if geometric_mean is not None else None,
                    'standard_deviation': round(std_dev, 2),
                    'variance': round(variance, 2),
                    'coefficient_of_variation': round(cv, 2) if cv is not None else None,
                    'min_return': round(min_return, 2),
                    'max_return': round(max_return, 2),
                    'range': round(range_return, 2),
                    'growth_of_10000': {
                        'initial': initial_value,
                        'final': round(final_value, 2),
                        'total_return_percent': round(total_return, 2),
                        'values': growth_values
                    },
                    'period_analysis': period_analysis
                }

            elif calc_type == 'cagr':
                # Calculate CAGR from beginning and ending values
                beginning_value = float(str(data.get('beginning_value', 0)).replace(',', ''))
                ending_value = float(str(data.get('ending_value', 0)).replace(',', ''))
                num_years = float(str(data.get('num_years', 0)).replace(',', ''))

                if beginning_value <= 0:
                    return JsonResponse({'success': False, 'error': 'Beginning value must be greater than zero.'}, status=400)
                if ending_value < 0:
                    return JsonResponse({'success': False, 'error': 'Ending value cannot be negative.'}, status=400)
                if num_years <= 0:
                    return JsonResponse({'success': False, 'error': 'Number of years must be greater than zero.'}, status=400)

                # CAGR = (Ending/Beginning)^(1/n) - 1
                if ending_value > 0:
                    cagr = (np.power(ending_value / beginning_value, 1/num_years) - 1) * 100
                else:
                    cagr = -100  # Total loss

                # Total return
                total_return = ((ending_value - beginning_value) / beginning_value) * 100

                # Absolute change
                absolute_change = ending_value - beginning_value

                # Multiple
                multiple = ending_value / beginning_value

                # Project future values
                projections = []
                for year in [5, 10, 15, 20, 25, 30]:
                    if year > num_years:
                        future_value = ending_value * np.power(1 + cagr/100, year - num_years)
                        projections.append({
                            'year': year,
                            'value': round(future_value, 2)
                        })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'beginning_value': round(beginning_value, 2),
                    'ending_value': round(ending_value, 2),
                    'num_years': num_years,
                    'cagr': round(cagr, 2),
                    'total_return_percent': round(total_return, 2),
                    'absolute_change': round(absolute_change, 2),
                    'multiple': round(multiple, 2),
                    'projections': projections
                }

            elif calc_type == 'required_return':
                # Calculate required return to reach a goal
                current_value = float(str(data.get('current_value', 0)).replace(',', ''))
                target_value = float(str(data.get('target_value', 0)).replace(',', ''))
                years = float(str(data.get('years', 0)).replace(',', ''))

                if current_value <= 0:
                    return JsonResponse({'success': False, 'error': 'Current value must be greater than zero.'}, status=400)
                if target_value <= 0:
                    return JsonResponse({'success': False, 'error': 'Target value must be greater than zero.'}, status=400)
                if years <= 0:
                    return JsonResponse({'success': False, 'error': 'Years must be greater than zero.'}, status=400)

                # Required return = (Target/Current)^(1/years) - 1
                required_return = (np.power(target_value / current_value, 1/years) - 1) * 100

                # Total growth needed
                total_growth = ((target_value - current_value) / current_value) * 100

                # Multiple needed
                multiple_needed = target_value / current_value

                # Alternative scenarios (different time periods)
                scenarios = []
                for y in [3, 5, 7, 10, 15, 20]:
                    req_return = (np.power(target_value / current_value, 1/y) - 1) * 100
                    scenarios.append({
                        'years': y,
                        'required_return': round(req_return, 2)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'current_value': round(current_value, 2),
                    'target_value': round(target_value, 2),
                    'years': years,
                    'required_return': round(required_return, 2),
                    'total_growth_percent': round(total_growth, 2),
                    'multiple_needed': round(multiple_needed, 2),
                    'scenarios': scenarios
                }

            elif calc_type == 'time_weighted':
                # Time-weighted return calculation
                portfolio_values = data.get('portfolio_values', [])
                cash_flows = data.get('cash_flows', [])  # External flows (deposits/withdrawals)

                if not portfolio_values or len(portfolio_values) < 2:
                    return JsonResponse({'success': False, 'error': 'Please provide at least 2 portfolio values.'}, status=400)

                try:
                    values = [float(str(v).replace(',', '')) for v in portfolio_values]
                    flows = [float(str(f).replace(',', '')) if f else 0 for f in cash_flows] if cash_flows else [0] * (len(values) - 1)
                except:
                    return JsonResponse({'success': False, 'error': 'Invalid values.'}, status=400)

                # Ensure flows array is correct length
                while len(flows) < len(values) - 1:
                    flows.append(0)

                # Calculate sub-period returns
                sub_period_returns = []
                for i in range(1, len(values)):
                    # Return = (End Value - Cash Flow) / (Beginning Value + Cash Flow) - 1
                    begin_value = values[i-1]
                    end_value = values[i]
                    flow = flows[i-1] if i-1 < len(flows) else 0
                    
                    # Assuming flow happens at start of period
                    adjusted_begin = begin_value + flow
                    if adjusted_begin > 0:
                        period_return = (end_value / adjusted_begin - 1) * 100
                    else:
                        period_return = 0
                    
                    sub_period_returns.append({
                        'period': i,
                        'beginning_value': round(begin_value, 2),
                        'cash_flow': round(flow, 2),
                        'ending_value': round(end_value, 2),
                        'return_percent': round(period_return, 2)
                    })

                # Time-weighted return = product of (1 + sub-period returns) - 1
                twr_product = np.prod([1 + r['return_percent']/100 for r in sub_period_returns])
                time_weighted_return = (twr_product - 1) * 100

                # Annualized TWR (assuming periods are years, adjust if needed)
                num_periods = len(sub_period_returns)
                if num_periods > 0 and twr_product > 0:
                    annualized_twr = (np.power(twr_product, 1/num_periods) - 1) * 100
                else:
                    annualized_twr = 0

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'num_periods': num_periods,
                    'beginning_value': round(values[0], 2),
                    'ending_value': round(values[-1], 2),
                    'total_cash_flows': round(sum(flows), 2),
                    'time_weighted_return': round(time_weighted_return, 2),
                    'annualized_twr': round(annualized_twr, 2),
                    'sub_period_returns': sub_period_returns
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
