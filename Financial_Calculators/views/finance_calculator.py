from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FinanceCalculator(View):
    """
    Class-based view for Finance Calculator (compound interest / future value).
    Calculates future value and total interest; returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/finance_calculator.html'

    def get(self, request):
        context = {'calculator_name': str(_('Finance Calculator'))}
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

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            amount = self._get_float(data, 'amount_', 0)
            rate = self._get_float(data, 'rate_', 0)
            time_years = self._get_float(data, 'time_years', 0)

            if amount <= 0 or amount > 1e12:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid amount.'))}, status=400)
            if rate < 0 or rate > 100:
                return JsonResponse({'success': False, 'error': str(_('Rate must be between 0 and 100%%.'))}, status=400)
            if time_years <= 0 or time_years > 100:
                return JsonResponse({'success': False, 'error': str(_('Time must be between 0 and 100 years.'))}, status=400)

            r = rate / 100.0
            future_value = amount * ((1 + r) ** time_years)
            total_interest = future_value - amount
            interest_pct = (total_interest / future_value * 100) if future_value > 0 else 0

            # Year-by-year growth for chart
            growth_schedule = []
            balance = amount
            for year in range(0, int(time_years) + 1):
                if year == 0:
                    balance = amount
                else:
                    balance = amount * ((1 + r) ** year)
                growth_schedule.append({
                    'year': year,
                    'balance': round(balance, 2),
                    'interest_earned': round(balance - amount, 2) if year > 0 else 0
                })

            # Scenarios: different time horizons
            scenario_years = [1, 2, 5, 10, 15, 20, 25, 30]
            scenarios = []
            for t in scenario_years:
                if t <= time_years + 20:
                    fv = amount * ((1 + r) ** t)
                    scenarios.append({
                        'years': t,
                        'future_value': round(fv, 2),
                        'total_interest': round(fv - amount, 2)
                    })

            result = {
                'success': True,
                'summary': {
                    'principal': round(amount, 2),
                    'rate': round(rate, 2),
                    'time_years': round(time_years, 2),
                    'future_value': round(future_value, 2),
                    'total_interest': round(total_interest, 2),
                    'interest_pct': round(interest_pct, 1)
                },
                'growth_schedule': growth_schedule,
                'scenarios': scenarios
            }
            result['chart_data'] = self._prepare_chart_data(amount, total_interest, future_value, growth_schedule)
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, principal, total_interest, future_value, growth_schedule):
        """Backend-controlled chart data (BMI-style): breakdown doughnut + growth line/bar chart."""
        if principal <= 0 and total_interest <= 0:
            return {}
        out = {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Principal')), str(_('Interest'))],
                    'datasets': [{
                        'data': [round(principal, 2), round(total_interest, 2)],
                        'backgroundColor': ['#3b82f6', '#10b981'],
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
        if growth_schedule:
            years = [str(r['year']) for r in growth_schedule]
            balances = [r['balance'] for r in growth_schedule]
            out['growth_chart'] = {
                'type': 'line',
                'data': {
                    'labels': years,
                    'datasets': [{
                        'label': str(_('Balance')),
                        'data': balances,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'fill': True,
                        'tension': 0.2,
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True}
                    },
                    'plugins': {'legend': {'position': 'top'}}
                }
            }
        return out
