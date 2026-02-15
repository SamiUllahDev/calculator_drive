from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CdCalculator(View):
    """
    Class-based view for CD (Certificate of Deposit) Calculator.
    Calculates CD returns with different compounding options.
    Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/cd_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('CD Calculator'),
            'page_title': _('CD Calculator - Certificate of Deposit Calculator'),
        }
        return render(request, self.template_name, context)

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
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            deposit = self._get_float(data, 'deposit', 0)
            apy = self._get_float(data, 'apy', 0)
            term_months = int(self._get_float(data, 'term_months', 12))
            compound_frequency = data.get('compound_frequency', 'daily')
            if isinstance(compound_frequency, list):
                compound_frequency = compound_frequency[0] if compound_frequency else 'daily'

            if deposit <= 0 or deposit > 10000000:
                return JsonResponse({'success': False, 'error': str(_('Please enter a valid deposit amount (1 to 10,000,000).'))}, status=400)
            if apy < 0 or apy > 25:
                return JsonResponse({'success': False, 'error': str(_('APY must be between 0%% and 25%%.'))}, status=400)
            if term_months <= 0 or term_months > 120:
                return JsonResponse({'success': False, 'error': str(_('CD term must be between 1 and 120 months.'))}, status=400)

            years = term_months / 12
            rate = apy / 100
            frequency_map = {
                'annually': 1,
                'semi-annually': 2,
                'quarterly': 4,
                'monthly': 12,
                'daily': 365
            }
            n = frequency_map.get(compound_frequency, 365)

            final_amount = deposit * ((1 + rate / n) ** (n * years))
            interest_earned = final_amount - deposit
            effective_apy = ((1 + rate / n) ** n - 1) * 100

            monthly_data = []
            for month in range(1, term_months + 1):
                month_years = month / 12
                balance = deposit * ((1 + rate / n) ** (n * month_years))
                monthly_data.append({
                    'month': month,
                    'balance': round(balance, 2),
                    'interest': round(balance - deposit, 2)
                })

            comparison = []
            for months in [3, 6, 12, 24, 36, 60]:
                yrs = months / 12
                amt = deposit * ((1 + rate / n) ** (n * yrs))
                comparison.append({
                    'term': f'{months} mo' if months < 12 else f'{months // 12} yr',
                    'months': months,
                    'final_amount': round(amt, 2),
                    'interest': round(amt - deposit, 2)
                })

            deposit_round = round(deposit, 2)
            interest_round = round(interest_earned, 2)
            chart_data = self._prepare_chart_data(
                deposit_round, interest_round,
                monthly_data, term_months
            )

            result = {
                'success': True,
                'summary': {
                    'deposit': deposit_round,
                    'apy': round(apy, 3),
                    'effective_apy': round(effective_apy, 3),
                    'term_months': term_months,
                    'final_amount': round(final_amount, 2),
                    'interest_earned': interest_round,
                    'compound_frequency': compound_frequency
                },
                'monthly_data': monthly_data[:24],
                'comparison': comparison,
                'chart_data': chart_data,
            }
            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, deposit_val, interest_val, monthly_data, term_months):
        """Build Chart.js-ready chart_data: breakdown doughnut and growth line."""
        deposit_label = str(_('Deposit'))
        interest_label = str(_('Interest'))
        breakdown_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [deposit_label, interest_label],
                'datasets': [{
                    'data': [deposit_val, interest_val],
                    'backgroundColor': ['#3b82f6', '#10b981'],
                    'borderWidth': 0,
                }],
            },
            'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
        }

        step = max(1, term_months // 12)
        sampled = monthly_data[::step]
        growth_labels = [str(_('Mo')) + ' ' + str(d['month']) for d in sampled]
        growth_values = [d['balance'] for d in sampled]
        balance_label = str(_('Balance'))
        growth_chart = {
            'type': 'line',
            'data': {
                'labels': growth_labels,
                'datasets': [{
                    'label': balance_label,
                    'data': growth_values,
                    'borderColor': '#3b82f6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'fill': True,
                    'tension': 0.3,
                }],
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}},
            },
        }
        return {'breakdown_chart': breakdown_chart, 'growth_chart': growth_chart}
