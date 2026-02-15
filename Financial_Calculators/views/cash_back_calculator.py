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
class CashBackCalculator(View):
    """
    Class-based view for Cash Back Calculator.
    Calculates cash back rewards from purchase amount and rate. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/cash_back_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Cash Back Calculator'))}
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

    def _prepare_chart_data(self, purchase_amount, cash_back, rate):
        """Backend-controlled: spend vs cash back doughnut + cash back at different rates bar chart."""
        out = {}
        if purchase_amount > 0 and cash_back >= 0:
            net_spend = max(0, purchase_amount - cash_back)
            if purchase_amount + cash_back > 0:
                out['breakdown_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': [str(_('Net spend')), str(_('Cash back'))],
                        'datasets': [{
                            'data': [round(net_spend, 2), round(cash_back, 2)],
                            'backgroundColor': ['#6366f1', '#10b981'],
                            'borderWidth': 0
                        }]
                    },
                    'options': {
                        'responsive': True,
                        'maintainAspectRatio': False,
                        'cutout': '55%',
                        'plugins': {'legend': {'position': 'bottom'}}
                    }
                }
        if purchase_amount > 0:
            rates = [1, 2, 3, 5, 10]
            labels = [str(r) + '%' for r in rates]
            values = [round(purchase_amount * (r / 100), 2) for r in rates]
            out['comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Cash back')),
                        'data': values,
                        'backgroundColor': '#10b981',
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

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            purchase_amount = self._get_float(data, 'purchase_amount', 0)
            cash_back_rate = self._get_float(data, 'cash_back_rate', 0)

            if purchase_amount < 0:
                return JsonResponse({'success': False, 'error': str(_('Purchase amount cannot be negative.'))}, status=400)
            if cash_back_rate < 0 or cash_back_rate > 100:
                return JsonResponse({'success': False, 'error': str(_('Cash back rate must be between 0 and 100%%.'))}, status=400)

            cash_back = purchase_amount * (cash_back_rate / 100)
            net_cost = purchase_amount - cash_back

            summary = {
                'purchase_amount': round(purchase_amount, 2),
                'cash_back_rate': round(cash_back_rate, 2),
                'cash_back': round(cash_back, 2),
                'net_cost': round(net_cost, 2)
            }

            comparison = []
            for r in [1, 2, 3, 5, 10]:
                comparison.append({
                    'rate': r,
                    'cash_back': round(purchase_amount * (r / 100), 2),
                    'net_cost': round(purchase_amount - purchase_amount * (r / 100), 2)
                })
            result = {
                'success': True,
                'summary': summary,
                'comparison': comparison,
                'chart_data': self._prepare_chart_data(purchase_amount, cash_back, cash_back_rate)
            }

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Cash-back JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Cash-back calculation failed: %s", e)
            from django.conf import settings
            err_msg = str(_("An error occurred during calculation."))
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )
