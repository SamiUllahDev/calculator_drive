from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AverageReturnCalculator(View):
    """
    Class-based view for Average Return Calculator.
    Calculates arithmetic mean, geometric mean, CAGR, and other return metrics.
    """
    template_name = 'financial_calculators/average_return_calculator.html'

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float (handles list, strips % and commas)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def _unwrap(self, value):
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Average Return Calculator'),
            'page_title': _('Average Return Calculator - CAGR & Investment Performance'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for average return calculations (JSON or form)."""
        try:
            data = self._get_data(request)
            calc_type = self._unwrap(data.get('calc_type')) or 'returns'

            # Map frontend 'simple' / 'periodic' to backend 'cagr' / 'returns'
            if calc_type == 'simple':
                calc_type = 'cagr'
                beginning_value = self._get_float(data, 'initial_value', 0) or self._get_float(data, 'beginning_value', 0)
                ending_value = self._get_float(data, 'final_value', 0) or self._get_float(data, 'ending_value', 0)
                num_years = self._get_float(data, 'years', 0) or self._get_float(data, 'num_years', 0)
            elif calc_type == 'periodic':
                calc_type = 'returns'

            if calc_type == 'returns':
                returns_raw = data.get('returns', [])
                if not isinstance(returns_raw, list):
                    returns_raw = [returns_raw] if returns_raw not in (None, '', 'null') else []
                if len(returns_raw) < 2:
                    return JsonResponse({'success': False, 'error': _('Please provide at least 2 return values.')}, status=400)
                try:
                    return_values = [self._get_float({'x': r}, 'x', 0) for r in returns_raw]
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': _('Invalid return values.')}, status=400)

                return_decimals = [r / 100 for r in return_values]
                arithmetic_mean = float(np.mean(return_values))
                product = np.prod([1 + r for r in return_decimals])
                geometric_mean = (np.power(product, 1/len(return_decimals)) - 1) * 100 if product > 0 else None
                std_dev = float(np.std(return_values, ddof=1)) if len(return_values) > 1 else 0
                variance = float(np.var(return_values, ddof=1)) if len(return_values) > 1 else 0
                cv = (std_dev / arithmetic_mean * 100) if arithmetic_mean != 0 else None
                min_return = min(return_values)
                max_return = max(return_values)
                range_return = max_return - min_return
                positive_count = sum(1 for r in return_values if r > 0)

                initial_value = 10000
                growth_values = [initial_value]
                current_value = initial_value
                for r in return_decimals:
                    current_value *= (1 + r)
                    growth_values.append(round(current_value, 2))
                final_value = growth_values[-1]
                total_return = ((final_value - initial_value) / initial_value) * 100

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

                growth_data = [{'year': i, 'value': growth_values[i]} for i in range(len(growth_values))]
                result = {
                    'success': True,
                    'calc_type': 'returns',
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
                    'period_analysis': period_analysis,
                    'cagr': round(geometric_mean, 2) if geometric_mean is not None else None,
                    'total_return': round(total_return, 2),
                    'absolute_gain': round(final_value - initial_value, 2),
                    'years': len(return_values),
                    'num_years': len(return_values),
                    'growth_data': growth_data,
                    'std_dev': round(std_dev, 2),
                    'best_year': round(max_return, 2),
                    'worst_year': round(min_return, 2),
                    'positive_years': positive_count,
                    'initial_value': initial_value,
                    'final_value': round(final_value, 2),
                }

            elif calc_type == 'cagr':
                beginning_value = self._get_float(data, 'initial_value', 0) or self._get_float(data, 'beginning_value', 0)
                ending_value = self._get_float(data, 'final_value', 0) or self._get_float(data, 'ending_value', 0)
                num_years = self._get_float(data, 'years', 0) or self._get_float(data, 'num_years', 0)
                if beginning_value <= 0:
                    return JsonResponse({'success': False, 'error': _('Beginning value must be greater than zero.')}, status=400)
                if ending_value < 0:
                    return JsonResponse({'success': False, 'error': _('Ending value cannot be negative.')}, status=400)
                if num_years <= 0:
                    return JsonResponse({'success': False, 'error': _('Number of years must be greater than zero.')}, status=400)

                if ending_value > 0:
                    cagr = (np.power(ending_value / beginning_value, 1/num_years) - 1) * 100
                else:
                    cagr = -100
                total_return = ((ending_value - beginning_value) / beginning_value) * 100
                absolute_change = ending_value - beginning_value
                multiple = ending_value / beginning_value

                growth_data = []
                for i in range(int(num_years) + 1):
                    val = beginning_value * np.power(ending_value / beginning_value, i / num_years)
                    growth_data.append({'year': i, 'value': round(val, 2)})

                projections = []
                for year in [5, 10, 15, 20, 25, 30]:
                    if year > num_years:
                        future_value = ending_value * np.power(1 + cagr/100, year - num_years)
                        projections.append({'year': year, 'value': round(future_value, 2)})

                result = {
                    'success': True,
                    'calc_type': 'cagr',
                    'beginning_value': round(beginning_value, 2),
                    'ending_value': round(ending_value, 2),
                    'num_years': num_years,
                    'cagr': round(cagr, 2),
                    'total_return_percent': round(total_return, 2),
                    'absolute_change': round(absolute_change, 2),
                    'multiple': round(multiple, 2),
                    'projections': projections,
                    'initial_value': round(beginning_value, 2),
                    'final_value': round(ending_value, 2),
                    'years': num_years,
                    'total_return': round(total_return, 2),
                    'absolute_gain': round(absolute_change, 2),
                    'growth_data': growth_data,
                }

            elif calc_type == 'required_return':
                current_value = self._get_float(data, 'current_value', 0)
                target_value = self._get_float(data, 'target_value', 0)
                years = self._get_float(data, 'years', 0)
                if current_value <= 0:
                    return JsonResponse({'success': False, 'error': _('Current value must be greater than zero.')}, status=400)
                if target_value <= 0:
                    return JsonResponse({'success': False, 'error': _('Target value must be greater than zero.')}, status=400)
                if years <= 0:
                    return JsonResponse({'success': False, 'error': _('Years must be greater than zero.')}, status=400)
                required_return = (np.power(target_value / current_value, 1/years) - 1) * 100
                total_growth = ((target_value - current_value) / current_value) * 100
                multiple_needed = target_value / current_value
                scenarios = []
                for y in [3, 5, 7, 10, 15, 20]:
                    req_return = (np.power(target_value / current_value, 1/y) - 1) * 100
                    scenarios.append({'years': y, 'required_return': round(req_return, 2)})
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
                portfolio_values = data.get('portfolio_values', [])
                cash_flows = data.get('cash_flows', [])
                if not portfolio_values or len(portfolio_values) < 2:
                    return JsonResponse({'success': False, 'error': _('Please provide at least 2 portfolio values.')}, status=400)
                try:
                    values = [self._get_float({'v': v}, 'v', 0) for v in (portfolio_values if isinstance(portfolio_values, list) else [portfolio_values])]
                    flows = [self._get_float({'f': f}, 'f', 0) for f in (cash_flows if isinstance(cash_flows, list) else [])] if cash_flows else [0] * (len(values) - 1)
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': _('Invalid values.')}, status=400)
                while len(flows) < len(values) - 1:
                    flows.append(0)
                sub_period_returns = []
                for i in range(1, len(values)):
                    begin_value = values[i-1]
                    end_value = values[i]
                    flow = flows[i-1] if i-1 < len(flows) else 0
                    adjusted_begin = begin_value + flow
                    period_return = (end_value / adjusted_begin - 1) * 100 if adjusted_begin > 0 else 0
                    sub_period_returns.append({
                        'period': i,
                        'beginning_value': round(begin_value, 2),
                        'cash_flow': round(flow, 2),
                        'ending_value': round(end_value, 2),
                        'return_percent': round(period_return, 2)
                    })
                twr_product = np.prod([1 + r['return_percent']/100 for r in sub_period_returns])
                time_weighted_return = (twr_product - 1) * 100
                num_periods = len(sub_period_returns)
                annualized_twr = (np.power(twr_product, 1/num_periods) - 1) * 100 if num_periods > 0 and twr_product > 0 else 0
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
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('Invalid request data.')}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
