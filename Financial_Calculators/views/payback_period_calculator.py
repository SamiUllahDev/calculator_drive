from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import math
import logging

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PaybackPeriodCalculator(View):
    """
    Class-based view for Payback Period Calculator.
    Calculates simple and discounted payback period for investments. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/payback_period_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Payback Period Calculator'))}
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
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

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

    def _prepare_chart_data(self, breakdown, initial_investment, cumulative_label=True):
        """Backend-controlled: cumulative recovery line chart + cash flow by year bar chart."""
        out = {}
        if not breakdown:
            return out
        years = [str(_('Year')) + ' ' + str(b['year']) for b in breakdown]
        cumulatives = [float(b.get('cumulative', 0)) for b in breakdown]
        cash_flows = [float(b.get('cash_flow', 0)) for b in breakdown]
        # Line: cumulative cash flow over years
        out['value_chart'] = {
            'type': 'line',
            'data': {
                'labels': years,
                'datasets': [
                    {
                        'label': str(_('Cumulative cash flow')),
                        'data': cumulatives,
                        'borderColor': '#6366f1',
                        'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                        'fill': True,
                        'tension': 0.3
                    },
                    {
                        'label': str(_('Initial investment')),
                        'data': [float(initial_investment)] * len(years),
                        'borderColor': '#ef4444',
                        'borderDash': [5, 5],
                        'fill': False
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'position': 'bottom'}},
                'scales': {'x': {'grid': {'display': False}}, 'y': {'beginAtZero': True}}
            }
        }
        # Bar: cash flow by year
        out['breakdown_chart'] = {
            'type': 'bar',
            'data': {
                'labels': years,
                'datasets': [{
                    'label': str(_('Cash flow')),
                    'data': cash_flows,
                    'backgroundColor': '#10b981',
                    'borderRadius': 4,
                    'borderWidth': 0
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'scales': {'x': {'grid': {'display': False}}, 'y': {'beginAtZero': True}},
                'plugins': {'legend': {'display': False}}
            }
        }
        return out

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'simple')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'simple'

            if calc_type == 'simple':
                initial_investment = self._get_float(data, 'initial_investment', 0)
                annual_cash_flow = self._get_float(data, 'annual_cash_flow', 0)

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Initial investment must be greater than zero.'))}, status=400)
                if annual_cash_flow <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Annual cash flow must be greater than zero.'))}, status=400)

                payback_years = initial_investment / annual_cash_flow
                payback_months = (payback_years % 1) * 12

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

                years_to_payback = int(math.ceil(payback_years))
                total_return = round(annual_cash_flow * years_to_payback - initial_investment, 2)

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'annual_cash_flow': round(annual_cash_flow, 2),
                    'payback_years': round(payback_years, 2),
                    'payback_years_int': int(payback_years),
                    'payback_months': round(payback_months, 1),
                    'total_return': total_return,
                    'breakdown': breakdown,
                    'summary': {
                        'payback_years': round(payback_years, 2),
                        'total_return': total_return,
                        'initial_investment': round(initial_investment, 2),
                        'annual_cash_flow': round(annual_cash_flow, 2)
                    }
                }
                result['chart_data'] = self._prepare_chart_data(breakdown, initial_investment)

            elif calc_type == 'uneven':
                initial_investment = self._get_float(data, 'initial_investment', 0)
                cash_flows_raw = data.get('cash_flows', [])
                discount_rate = self._get_float(data, 'discount_rate', 0)

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Initial investment must be greater than zero.'))}, status=400)
                if not cash_flows_raw:
                    return JsonResponse({'success': False, 'error': str(_('Please provide cash flows.'))}, status=400)

                try:
                    cash_flow_values = [self._get_float({'x': cf}, 'x', 0) for cf in (cash_flows_raw if isinstance(cash_flows_raw, list) else [cash_flows_raw])]
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': str(_('Invalid cash flow values.'))}, status=400)

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
                        prev_cumulative = cumulative - cf
                        if cf > 0:
                            fraction = (initial_investment - prev_cumulative) / cf
                            simple_payback = i + fraction
                        else:
                            simple_payback = i + 1

                discounted_payback = None
                cumulative_discounted = 0
                discounted_breakdown = []
                for i, cf in enumerate(cash_flow_values):
                    if discount_rate > 0:
                        discounted_cf = cf / ((1 + discount_rate / 100) ** (i + 1))
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
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'initial_investment': round(initial_investment, 2),
                    'discount_rate': discount_rate,
                    'num_periods': len(cash_flow_values),
                    'simple_payback': round(simple_payback, 2) if simple_payback is not None else None,
                    'simple_payback_years': int(simple_payback) if simple_payback is not None else None,
                    'simple_payback_months': round((simple_payback % 1) * 12, 1) if simple_payback is not None else None,
                    'discounted_payback': round(discounted_payback, 2) if discounted_payback is not None else None,
                    'discounted_payback_years': int(discounted_payback) if discounted_payback is not None else None,
                    'discounted_payback_months': round((discounted_payback % 1) * 12, 1) if discounted_payback is not None else None,
                    'total_cash_flows': round(total_cash_flows, 2),
                    'total_discounted': round(cumulative_discounted, 2),
                    'net_return': round(total_cash_flows - initial_investment, 2),
                    'npv': round(cumulative_discounted - initial_investment, 2),
                    'recovered': cumulative >= initial_investment,
                    'breakdown': breakdown,
                    'discounted_breakdown': discounted_breakdown,
                    'summary': {
                        'simple_payback': round(simple_payback, 2) if simple_payback is not None else None,
                        'discounted_payback': round(discounted_payback, 2) if discounted_payback is not None else None,
                        'initial_investment': round(initial_investment, 2),
                        'total_cash_flows': round(total_cash_flows, 2),
                        'net_return': round(total_cash_flows - initial_investment, 2)
                    }
                }
                result['chart_data'] = self._prepare_chart_data(breakdown, initial_investment)

            elif calc_type == 'target':
                initial_investment = self._get_float(data, 'initial_investment', 0)
                target_payback = self._get_float(data, 'target_payback', 0)
                discount_rate = self._get_float(data, 'discount_rate', 0)

                if initial_investment <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Initial investment must be greater than zero.'))}, status=400)
                if target_payback <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Target payback period must be greater than zero.'))}, status=400)

                required_annual = initial_investment / target_payback
                if discount_rate > 0:
                    r = discount_rate / 100
                    n = target_payback
                    pv_factor = (1 - (1 + r) ** (-n)) / r
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
                    'required_monthly_discounted': round(required_annual_discounted / 12, 2),
                    'summary': {
                        'required_annual_simple': round(required_annual, 2),
                        'required_annual_discounted': round(required_annual_discounted, 2),
                        'target_payback_years': target_payback
                    }
                }
                result['chart_data'] = {}

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Payback JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Payback period calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
