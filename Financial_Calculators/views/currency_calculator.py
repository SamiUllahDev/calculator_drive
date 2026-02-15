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
class CurrencyCalculator(View):
    """
    Class-based view for Currency Calculator.
    Converts between currencies using exchange rates. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/currency_calculator.html'

    DEFAULT_RATES = {
        'USD': 1.0, 'EUR': 0.92, 'GBP': 0.79, 'JPY': 149.50, 'CAD': 1.36, 'AUD': 1.53,
        'CHF': 0.88, 'CNY': 7.24, 'INR': 83.12, 'MXN': 17.15, 'BRL': 4.97, 'KRW': 1298.50,
        'SGD': 1.34, 'HKD': 7.82, 'NOK': 10.65, 'SEK': 10.42, 'DKK': 6.87, 'NZD': 1.64,
        'ZAR': 18.65, 'RUB': 92.50, 'TRY': 28.85, 'PLN': 4.02, 'THB': 35.45, 'IDR': 15650.00,
        'MYR': 4.72, 'PHP': 55.85, 'CZK': 22.75, 'ILS': 3.72, 'AED': 3.67, 'SAR': 3.75,
    }

    CURRENCY_NAMES = {
        'USD': 'US Dollar', 'EUR': 'Euro', 'GBP': 'British Pound', 'JPY': 'Japanese Yen',
        'CAD': 'Canadian Dollar', 'AUD': 'Australian Dollar', 'CHF': 'Swiss Franc',
        'CNY': 'Chinese Yuan', 'INR': 'Indian Rupee', 'MXN': 'Mexican Peso', 'BRL': 'Brazilian Real',
        'KRW': 'South Korean Won', 'SGD': 'Singapore Dollar', 'HKD': 'Hong Kong Dollar',
        'NOK': 'Norwegian Krone', 'SEK': 'Swedish Krona', 'DKK': 'Danish Krone',
        'NZD': 'New Zealand Dollar', 'ZAR': 'South African Rand', 'RUB': 'Russian Ruble',
        'TRY': 'Turkish Lira', 'PLN': 'Polish Zloty', 'THB': 'Thai Baht', 'IDR': 'Indonesian Rupiah',
        'MYR': 'Malaysian Ringgit', 'PHP': 'Philippine Peso', 'CZK': 'Czech Koruna',
        'ILS': 'Israeli Shekel', 'AED': 'UAE Dirham', 'SAR': 'Saudi Riyal',
    }

    CURRENCY_SYMBOLS = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF',
        'CNY': '¥', 'INR': '₹', 'MXN': '$', 'BRL': 'R$', 'KRW': '₩', 'SGD': 'S$', 'HKD': 'HK$',
        'NOK': 'kr', 'SEK': 'kr', 'DKK': 'kr', 'NZD': 'NZ$', 'ZAR': 'R', 'RUB': '₽', 'TRY': '₺',
        'PLN': 'zł', 'THB': '฿', 'IDR': 'Rp', 'MYR': 'RM', 'PHP': '₱', 'CZK': 'Kč', 'ILS': '₪',
        'AED': 'د.إ', 'SAR': '﷼',
    }

    def get(self, request):
        currencies = [
            {'code': code, 'name': self.CURRENCY_NAMES.get(code, code), 'symbol': self.CURRENCY_SYMBOLS.get(code, '')}
            for code in self.DEFAULT_RATES.keys()
        ]
        context = {
            'calculator_name': str(_('Currency Calculator')),
            'currencies': currencies,
        }
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

            amount = self._get_float(data, 'amount', 0)
            from_currency = data.get('from_currency', 'USD')
            to_currency = data.get('to_currency', 'EUR')
            if isinstance(from_currency, list):
                from_currency = from_currency[0] if from_currency else 'USD'
            if isinstance(to_currency, list):
                to_currency = to_currency[0] if to_currency else 'EUR'
            from_currency = str(from_currency).upper()[:3]
            to_currency = str(to_currency).upper()[:3]

            if amount < 0:
                return JsonResponse({'success': False, 'error': str(_('Amount cannot be negative.'))}, status=400)
            if from_currency not in self.DEFAULT_RATES:
                return JsonResponse({'success': False, 'error': str(_('Unsupported currency: %s')) % from_currency}, status=400)
            if to_currency not in self.DEFAULT_RATES:
                return JsonResponse({'success': False, 'error': str(_('Unsupported currency: %s')) % to_currency}, status=400)

            from_rate = self.DEFAULT_RATES[from_currency]
            to_rate = self.DEFAULT_RATES[to_currency]
            amount_usd = amount / from_rate
            converted_amount = amount_usd * to_rate
            exchange_rate = to_rate / from_rate
            inverse_rate = from_rate / to_rate

            from_symbol = self.CURRENCY_SYMBOLS.get(from_currency, '')
            to_symbol = self.CURRENCY_SYMBOLS.get(to_currency, '')

            summary = {
                'amount': round(amount, 2),
                'from_currency': from_currency,
                'from_currency_name': self.CURRENCY_NAMES.get(from_currency, from_currency),
                'from_symbol': from_symbol,
                'to_currency': to_currency,
                'to_currency_name': self.CURRENCY_NAMES.get(to_currency, to_currency),
                'to_symbol': to_symbol,
                'converted_amount': round(converted_amount, 2),
                'exchange_rate': round(exchange_rate, 6),
                'inverse_rate': round(inverse_rate, 6),
            }
            formatted = {
                'from': f'{from_symbol}{amount:,.2f} {from_currency}',
                'to': f'{to_symbol}{converted_amount:,.2f} {to_currency}',
                'rate': f'1 {from_currency} = {exchange_rate:.4f} {to_currency}',
                'inverse': f'1 {to_currency} = {inverse_rate:.4f} {from_currency}'
            }

            common_amounts = [1, 5, 10, 25, 50, 100, 500, 1000]
            conversion_table = []
            for amt in common_amounts:
                converted = (amt / from_rate) * to_rate
                conversion_table.append({
                    'from_amount': amt,
                    'to_amount': round(converted, 2),
                    'from_formatted': f'{from_symbol}{amt:,.0f}',
                    'to_formatted': f'{to_symbol}{converted:,.2f}'
                })

            major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
            cross_rates = []
            for curr in major_currencies:
                if curr != from_currency:
                    rate = self.DEFAULT_RATES[curr] / from_rate
                    conv = amount * rate
                    cross_rates.append({
                        'currency': curr,
                        'name': self.CURRENCY_NAMES.get(curr, curr),
                        'symbol': self.CURRENCY_SYMBOLS.get(curr, ''),
                        'rate': round(rate, 6),
                        'converted': round(conv, 2)
                    })

            result = {
                'success': True,
                'summary': summary,
                'formatted': formatted,
                'conversion_table': conversion_table,
                'cross_rates': cross_rates,
            }
            result['chart_data'] = self._prepare_chart_data(amount, from_currency, from_symbol, cross_rates)

            try:
                body = json.dumps(result, cls=SafeJSONEncoder)
            except (TypeError, ValueError) as ser_err:
                logger.exception("Currency JSON serialization failed: %s", ser_err)
                return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
            return HttpResponse(body, content_type='application/json')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception as e:
            logger.exception("Currency calculation failed: %s", e)
            from django.conf import settings
            err_msg = "An error occurred during calculation."
            if getattr(settings, 'DEBUG', False):
                err_msg += " [" + str(e).replace('"', "'") + "]"
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}),
                content_type='application/json',
                status=500
            )

    def _prepare_chart_data(self, amount, from_currency, from_symbol, cross_rates):
        """Bar chart: same amount converted to major currencies."""
        if not cross_rates:
            return {}
        labels = [r['currency'] for r in cross_rates]
        values = [float(r['converted']) for r in cross_rates]
        return {
            'cross_chart': {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Converted amount')),
                        'data': values,
                        'backgroundColor': '#3b82f6',
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
        }
