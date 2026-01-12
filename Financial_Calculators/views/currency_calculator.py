from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class CurrencyCalculator(View):
    """
    Class-based view for Currency Calculator
    Converts between different currencies using exchange rates.
    """
    template_name = 'financial_calculators/currency_calculator.html'
    
    # Default exchange rates (base: USD)
    # These would typically be fetched from an API in production
    DEFAULT_RATES = {
        'USD': 1.0,
        'EUR': 0.92,
        'GBP': 0.79,
        'JPY': 149.50,
        'CAD': 1.36,
        'AUD': 1.53,
        'CHF': 0.88,
        'CNY': 7.24,
        'INR': 83.12,
        'MXN': 17.15,
        'BRL': 4.97,
        'KRW': 1298.50,
        'SGD': 1.34,
        'HKD': 7.82,
        'NOK': 10.65,
        'SEK': 10.42,
        'DKK': 6.87,
        'NZD': 1.64,
        'ZAR': 18.65,
        'RUB': 92.50,
        'TRY': 28.85,
        'PLN': 4.02,
        'THB': 35.45,
        'IDR': 15650.00,
        'MYR': 4.72,
        'PHP': 55.85,
        'CZK': 22.75,
        'ILS': 3.72,
        'AED': 3.67,
        'SAR': 3.75,
    }
    
    CURRENCY_NAMES = {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'GBP': 'British Pound',
        'JPY': 'Japanese Yen',
        'CAD': 'Canadian Dollar',
        'AUD': 'Australian Dollar',
        'CHF': 'Swiss Franc',
        'CNY': 'Chinese Yuan',
        'INR': 'Indian Rupee',
        'MXN': 'Mexican Peso',
        'BRL': 'Brazilian Real',
        'KRW': 'South Korean Won',
        'SGD': 'Singapore Dollar',
        'HKD': 'Hong Kong Dollar',
        'NOK': 'Norwegian Krone',
        'SEK': 'Swedish Krona',
        'DKK': 'Danish Krone',
        'NZD': 'New Zealand Dollar',
        'ZAR': 'South African Rand',
        'RUB': 'Russian Ruble',
        'TRY': 'Turkish Lira',
        'PLN': 'Polish Zloty',
        'THB': 'Thai Baht',
        'IDR': 'Indonesian Rupiah',
        'MYR': 'Malaysian Ringgit',
        'PHP': 'Philippine Peso',
        'CZK': 'Czech Koruna',
        'ILS': 'Israeli Shekel',
        'AED': 'UAE Dirham',
        'SAR': 'Saudi Riyal',
    }
    
    CURRENCY_SYMBOLS = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'CAD': 'C$',
        'AUD': 'A$',
        'CHF': 'CHF',
        'CNY': '¥',
        'INR': '₹',
        'MXN': '$',
        'BRL': 'R$',
        'KRW': '₩',
        'SGD': 'S$',
        'HKD': 'HK$',
        'NOK': 'kr',
        'SEK': 'kr',
        'DKK': 'kr',
        'NZD': 'NZ$',
        'ZAR': 'R',
        'RUB': '₽',
        'TRY': '₺',
        'PLN': 'zł',
        'THB': '฿',
        'IDR': 'Rp',
        'MYR': 'RM',
        'PHP': '₱',
        'CZK': 'Kč',
        'ILS': '₪',
        'AED': 'د.إ',
        'SAR': '﷼',
    }
    
    def get(self, request):
        """Handle GET request"""
        currencies = [
            {'code': code, 'name': self.CURRENCY_NAMES.get(code, code), 'symbol': self.CURRENCY_SYMBOLS.get(code, '')}
            for code in self.DEFAULT_RATES.keys()
        ]
        context = {
            'calculator_name': 'Currency Calculator',
            'currencies': currencies,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for currency conversion"""
        try:
            data = json.loads(request.body)
            
            amount = float(str(data.get('amount', 0)).replace(',', ''))
            from_currency = data.get('from_currency', 'USD').upper()
            to_currency = data.get('to_currency', 'EUR').upper()
            
            # Validation
            if amount < 0:
                return JsonResponse({'success': False, 'error': 'Amount cannot be negative.'}, status=400)
            
            if from_currency not in self.DEFAULT_RATES:
                return JsonResponse({'success': False, 'error': f'Unsupported currency: {from_currency}'}, status=400)
            
            if to_currency not in self.DEFAULT_RATES:
                return JsonResponse({'success': False, 'error': f'Unsupported currency: {to_currency}'}, status=400)
            
            # Convert through USD as base
            from_rate = self.DEFAULT_RATES[from_currency]
            to_rate = self.DEFAULT_RATES[to_currency]
            
            # Amount in USD
            amount_usd = amount / from_rate
            
            # Convert to target currency
            converted_amount = amount_usd * to_rate
            
            # Exchange rate
            exchange_rate = to_rate / from_rate
            inverse_rate = from_rate / to_rate
            
            # Format with symbols
            from_symbol = self.CURRENCY_SYMBOLS.get(from_currency, '')
            to_symbol = self.CURRENCY_SYMBOLS.get(to_currency, '')
            
            result = {
                'success': True,
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
                'formatted': {
                    'from': f'{from_symbol}{amount:,.2f} {from_currency}',
                    'to': f'{to_symbol}{converted_amount:,.2f} {to_currency}',
                    'rate': f'1 {from_currency} = {exchange_rate:.4f} {to_currency}',
                    'inverse': f'1 {to_currency} = {inverse_rate:.4f} {from_currency}'
                }
            }
            
            # Add conversion table for common amounts
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
            result['conversion_table'] = conversion_table
            
            # Add cross rates for major currencies
            major_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF']
            cross_rates = []
            for curr in major_currencies:
                if curr != from_currency:
                    rate = self.DEFAULT_RATES[curr] / from_rate
                    converted = amount * rate
                    cross_rates.append({
                        'currency': curr,
                        'name': self.CURRENCY_NAMES.get(curr, curr),
                        'symbol': self.CURRENCY_SYMBOLS.get(curr, ''),
                        'rate': round(rate, 6),
                        'converted': round(converted, 2)
                    })
            result['cross_rates'] = cross_rates
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
