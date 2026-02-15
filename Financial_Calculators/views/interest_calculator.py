from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class InterestCalculator(View):
    """
    Class-based view for Interest Calculator.
    Calculates simple and compound interest with detailed breakdowns.
    """
    template_name = 'financial_calculators/interest_calculator.html'

    MIN_PRINCIPAL = 0
    MAX_PRINCIPAL = 1000000000
    MIN_RATE = 0
    MAX_RATE = 100
    MIN_TIME = 0.001
    MAX_TIME = 100

    FREQUENCY_MAP = {
        'annually': 1,
        'semi-annually': 2,
        'semiannually': 2,
        'quarterly': 4,
        'monthly': 12,
        'daily': 365,
    }

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float value from data (handles list from form POST, strips %)."""
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
        """Return first element if list, else value."""
        if isinstance(value, list):
            return value[0] if value else None
        return value

    def get(self, request):
        """Handle GET request."""
        context = {
            'calculator_name': _('Interest Calculator'),
            'page_title': _('Interest Calculator - Simple & Compound Interest'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            principal = self._get_float(data, 'principal', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            time_period = self._get_float(data, 'time_period', 0)
            time_unit = self._unwrap(data.get('time_unit')) or 'years'
            interest_type = self._unwrap(data.get('interest_type')) or 'simple'
            compound_frequency = self._unwrap(data.get('compound_frequency')) or 'monthly'

            errors = []

            if principal <= self.MIN_PRINCIPAL:
                errors.append(_('Please enter a valid principal amount.'))
            elif principal > self.MAX_PRINCIPAL:
                errors.append(_('Principal cannot exceed %(max)s.') % {'max': f'${self.MAX_PRINCIPAL:,}'})

            if interest_rate <= self.MIN_RATE or interest_rate > self.MAX_RATE:
                errors.append(_('Interest rate must be between 0.01%% and 100%%.'))

            if time_period <= 0 or time_period > self.MAX_TIME:
                errors.append(_('Time period must be between 1 and 100.'))

            if time_unit not in ('years', 'months', 'days'):
                errors.append(_('Invalid time unit.'))

            if interest_type not in ('simple', 'compound'):
                errors.append(_('Invalid interest type.'))

            if interest_type == 'compound' and compound_frequency not in self.FREQUENCY_MAP:
                errors.append(_('Invalid compound frequency.'))

            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)

            # Normalize compound_frequency key (semi-annually vs semiannually)
            freq_key = compound_frequency if compound_frequency in self.FREQUENCY_MAP else 'monthly'
            if compound_frequency == 'semi-annually':
                freq_key = 'semi-annually'

            # Convert time to years
            if time_unit == 'months':
                years = time_period / 12
            elif time_unit == 'days':
                years = time_period / 365
            else:
                years = time_period

            rate = interest_rate / 100

            if interest_type == 'simple':
                interest = principal * rate * years
                final_amount = principal + interest
                effective_rate = interest_rate

                yearly_data = []
                for year in range(1, int(years) + 2):
                    if year <= years:
                        yr_interest = principal * rate * min(year, years)
                        yearly_data.append({
                            'year': year,
                            'interest': round(principal * rate, 2),
                            'total_interest': round(yr_interest, 2),
                            'balance': round(principal + yr_interest, 2)
                        })
            else:
                n = self.FREQUENCY_MAP.get(compound_frequency, 12)
                final_amount = principal * ((1 + rate / n) ** (n * years))
                interest = final_amount - principal
                effective_rate = ((1 + rate / n) ** n - 1) * 100

                yearly_data = []
                for year in range(1, int(years) + 2):
                    if year <= years:
                        balance = principal * ((1 + rate / n) ** (n * year))
                        prev_balance = principal * ((1 + rate / n) ** (n * (year - 1))) if year > 1 else principal
                        yr_interest = balance - prev_balance
                        yearly_data.append({
                            'year': year,
                            'interest': round(yr_interest, 2),
                            'total_interest': round(balance - principal, 2),
                            'balance': round(balance, 2)
                        })

            simple_interest = principal * rate * years
            compound_interest = principal * ((1 + rate / 12) ** (12 * years)) - principal

            result = {
                'success': True,
                'summary': {
                    'principal': round(principal, 2),
                    'interest_rate': round(interest_rate, 3),
                    'time_period': time_period,
                    'time_unit': time_unit,
                    'interest_type': interest_type,
                    'interest_earned': round(interest, 2),
                    'final_amount': round(final_amount, 2),
                    'effective_rate': round(effective_rate, 3),
                    'years': round(years, 2)
                },
                'comparison': {
                    'simple': round(simple_interest, 2),
                    'compound': round(compound_interest, 2),
                    'difference': round(compound_interest - simple_interest, 2)
                },
                'yearly_data': yearly_data[:30],
                'chart_data': {
                    'breakdown': {
                        'principal': round(principal, 2),
                        'interest': round(interest, 2)
                    },
                    'growth': {
                        'labels': [f"Year {d['year']}" for d in yearly_data[:10]],
                        'balances': [d['balance'] for d in yearly_data[:10]]
                    }
                }
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
