from django.views import View
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class InflationCalculator(View):
    """
    Class-based view for Inflation Calculator.
    Calculates the effect of inflation on purchasing power. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/inflation_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Inflation Calculator'))}
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

            amount = self._get_float(data, 'amount', 0)
            inflation_rate = self._get_float(data, 'inflation_rate', 0)
            years = self._get_int(data, 'years', 0)
            calc_type = data.get('calc_type', 'future')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'future'

            if amount <= 0 or amount > 1000000000:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid amount.'))}, status=400)
            if inflation_rate < -20 or inflation_rate > 50:
                return JsonResponse({'success': False, 'error': str(_('Inflation rate must be between -20%% and 50%%.'))}, status=400)
            if years <= 0 or years > 100:
                return JsonResponse({'success': False, 'error': str(_('Years must be between 1 and 100.'))}, status=400)

            rate = inflation_rate / 100

            if calc_type == 'future':
                future_value = amount * ((1 + rate) ** years)
                purchasing_power_lost = future_value - amount
                real_value = amount
            else:
                future_value = amount
                real_value = amount / ((1 + rate) ** years)
                purchasing_power_lost = amount - real_value

            cumulative_inflation = (((1 + rate) ** years) - 1) * 100

            yearly_data = []
            for year in range(1, years + 1):
                if calc_type == 'future':
                    value = amount * ((1 + rate) ** year)
                    power = amount / ((1 + rate) ** year)
                else:
                    value = amount
                    power = amount / ((1 + rate) ** year)
                yearly_data.append({
                    'year': year,
                    'value': round(value, 2),
                    'purchasing_power': round(power, 2),
                    'inflation_factor': round((1 + rate) ** year, 4)
                })

            comparison = []
            for rate_pct in [2, 3, 4, 5, 7, 10]:
                r = rate_pct / 100
                fv = amount * ((1 + r) ** years)
                comparison.append({
                    'rate': rate_pct,
                    'future_value': round(fv, 2),
                    'purchasing_power': round(amount / ((1 + r) ** years), 2)
                })

            summary = {
                'original_amount': round(amount, 2),
                'inflation_rate': round(inflation_rate, 2),
                'years': years,
                'calc_type': calc_type,
                'future_value': round(future_value, 2),
                'real_value': round(real_value, 2),
                'purchasing_power_change': round(purchasing_power_lost, 2),
                'cumulative_inflation': round(cumulative_inflation, 2)
            }

            result = {
                'success': True,
                'summary': summary,
                'yearly_data': yearly_data[:50],
                'comparison': comparison,
            }
            result['chart_data'] = self._prepare_chart_data(yearly_data[:30], comparison, calc_type)

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Inflation JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Inflation calculation failed: %s", e)
            from django.conf import settings
            err_msg = "An error occurred during calculation."
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )

    def _prepare_chart_data(self, yearly_data, comparison, calc_type):
        """Backend-controlled: value-over-time line chart + rate comparison bar chart."""
        out = {}
        if yearly_data:
            labels = [str(_('Year')) + ' ' + str(d['year']) for d in yearly_data]
            values = [float(d['value']) for d in yearly_data]
            power = [float(d['purchasing_power']) for d in yearly_data]
            out['value_chart'] = {
                'type': 'line',
                'data': {
                    'labels': labels,
                    'datasets': [
                        {
                            'label': str(_('Nominal value')),
                            'data': values,
                            'borderColor': '#3b82f6',
                            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                            'fill': True,
                            'tension': 0.3
                        },
                        {
                            'label': str(_('Real value (purchasing power)')),
                            'data': power,
                            'borderColor': '#ef4444',
                            'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                            'fill': True,
                            'tension': 0.3
                        }
                    ]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom'}},
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True}
                    }
                }
            }
        if comparison:
            rate_labels = [str(r['rate']) + '%' for r in comparison]
            fv_values = [float(r['future_value']) for r in comparison]
            out['comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': rate_labels,
                    'datasets': [{
                        'label': str(_('Future cost')),
                        'data': fv_values,
                        'backgroundColor': '#8b5cf6',
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True}
                    },
                    'plugins': {'legend': {'display': False}}
                }
            }
        return out
