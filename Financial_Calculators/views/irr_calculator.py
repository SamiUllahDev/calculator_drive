from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IrrCalculator(View):
    """
    Class-based view for IRR (Internal Rate of Return) Calculator
    Calculates IRR, NPV, and payback period for investment analysis.
    """
    template_name = 'financial_calculators/irr_calculator.html'

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
            'calculator_name': _('IRR Calculator'),
            'page_title': _('IRR Calculator - Internal Rate of Return'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for IRR calculations"""
        try:
            data = self._get_data(request)
            calc_type = self._unwrap(data.get('calc_type')) or 'irr'

            if calc_type == 'irr':
                initial_investment = self._get_float(data, 'initial_investment', 0)
                cash_flows_raw = data.get('cash_flows', [])
                discount_rate = self._get_float(data, 'discount_rate', 10)

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Initial investment must be greater than zero.'))}, status=400)
                if not cash_flows_raw or (isinstance(cash_flows_raw, list) and len(cash_flows_raw) == 0):
                    return JsonResponse({'success': False, 'error': str(_('Please provide at least one cash flow.'))}, status=400)

                if not isinstance(cash_flows_raw, list):
                    cash_flows_raw = [cash_flows_raw]
                try:
                    cash_flow_values = [self._get_float({'x': cf}, 'x', 0) for cf in cash_flows_raw]
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': str(_('Invalid cash flow values.'))}, status=400)

                all_cash_flows = [-initial_investment] + cash_flow_values
                irr = self._calculate_irr(all_cash_flows)
                npv = self._calculate_npv(all_cash_flows, discount_rate / 100)
                payback_period, discounted_payback = self._calculate_payback(initial_investment, cash_flow_values, discount_rate / 100)

                pv_cash_flows = sum([cf / np.power(1 + discount_rate/100, i+1) for i, cf in enumerate(cash_flow_values)])
                profitability_index = pv_cash_flows / initial_investment if initial_investment > 0 else 0

                total_cash_inflows = sum(cash_flow_values)
                total_return = ((total_cash_inflows - initial_investment) / initial_investment * 100) if initial_investment > 0 else 0

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

                if irr is not None:
                    if irr > discount_rate:
                        decision = _("Accept - IRR exceeds required return")
                        decision_class = "positive"
                    elif irr == discount_rate:
                        decision = _("Indifferent - IRR equals required return")
                        decision_class = "neutral"
                    else:
                        decision = _("Reject - IRR below required return")
                        decision_class = "negative"
                else:
                    decision = _("Unable to calculate IRR")
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
                initial_investment = self._get_float(data, 'initial_investment', 0)
                cash_flows_raw = data.get('cash_flows', [])

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Initial investment must be greater than zero.'))}, status=400)

                if not isinstance(cash_flows_raw, list):
                    cash_flows_raw = [cash_flows_raw]
                try:
                    cash_flow_values = [self._get_float({'x': cf}, 'x', 0) for cf in cash_flows_raw]
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': str(_('Invalid cash flow values.'))}, status=400)

                all_cash_flows = [-initial_investment] + cash_flow_values
                sensitivity = []
                for rate in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 25, 30]:
                    npv = self._calculate_npv(all_cash_flows, rate / 100)
                    sensitivity.append({'rate': rate, 'npv': round(npv, 2)})
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
                projects = data.get('projects', [])
                discount_rate = self._get_float(data, 'discount_rate', 10)

                if not projects or len(projects) < 2:
                    return JsonResponse({'success': False, 'error': str(_('Please provide at least 2 projects to compare.'))}, status=400)

                comparisons = []
                for i, project in enumerate(projects):
                    if not isinstance(project, dict):
                        project = {}
                    name = project.get('name') or str(_('Project %(n)s') % {'n': i + 1})
                    initial = self._get_float(project, 'initial_investment', 0)
                    cfs_raw = project.get('cash_flows', [])
                    if not isinstance(cfs_raw, list):
                        cfs_raw = [cfs_raw]
                    cfs = [self._get_float({'x': cf}, 'x', 0) for cf in cfs_raw]
                    all_cfs = [-initial] + cfs
                    irr = self._calculate_irr(all_cfs)
                    npv = self._calculate_npv(all_cfs, discount_rate / 100)
                    payback, _disc_payback = self._calculate_payback(initial, cfs, discount_rate / 100)
                    pi = sum([cf / np.power(1 + discount_rate/100, j+1) for j, cf in enumerate(cfs)]) / initial if initial > 0 else 0
                    comparisons.append({
                        'name': str(name),
                        'initial_investment': round(initial, 2),
                        'irr': round(irr, 2) if irr is not None else None,
                        'npv': round(npv, 2),
                        'payback': round(payback, 2) if payback else None,
                        'profitability_index': round(pi, 2)
                    })

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
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': str(_('Invalid input: %(detail)s') % {'detail': str(e)})}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _calculate_irr(self, cash_flows, max_iterations=100, tolerance=0.0001):
        """Calculate IRR using Newton-Raphson method"""
        if len(cash_flows) < 2:
            return None
        rate = 0.1
        for _ in range(max_iterations):
            npv = sum([cf / np.power(1 + rate, i) for i, cf in enumerate(cash_flows)])
            npv_derivative = sum([-i * cf / np.power(1 + rate, i + 1) for i, cf in enumerate(cash_flows)])
            if abs(npv_derivative) < 1e-10:
                break
            new_rate = rate - npv / npv_derivative
            if abs(new_rate - rate) < tolerance:
                return new_rate * 100
            rate = new_rate
            if rate < -0.99:
                rate = -0.99
            if rate > 10:
                rate = 10
        return rate * 100 if abs(sum([cf / np.power(1 + rate, i) for i, cf in enumerate(cash_flows)])) < 1 else None

    def _calculate_npv(self, cash_flows, rate):
        """Calculate Net Present Value"""
        if rate == 0:
            return sum(cash_flows)
        return sum([cf / np.power(1 + rate, i) for i, cf in enumerate(cash_flows)])

    def _calculate_payback(self, initial_investment, cash_flows, rate):
        """Calculate payback period and discounted payback period"""
        cumulative = 0
        payback = None
        for i, cf in enumerate(cash_flows):
            cumulative += cf
            if cumulative >= initial_investment and payback is None:
                prev_cumulative = cumulative - cf
                fraction = (initial_investment - prev_cumulative) / cf if cf != 0 else 0
                payback = i + fraction

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
