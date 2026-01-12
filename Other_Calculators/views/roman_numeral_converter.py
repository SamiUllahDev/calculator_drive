from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RomanNumeralConverter(View):
    """
    Professional Roman Numeral Converter with Comprehensive Features
    
    This converter provides Roman numeral conversions with:
    - Convert decimal numbers to Roman numerals
    - Convert Roman numerals to decimal numbers
    - Validate Roman numeral format
    - Provide step-by-step conversion process
    
    Features:
    - Supports bidirectional conversion
    - Handles standard Roman numeral rules
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/roman_numeral_converter.html'
    
    # Roman numeral values
    ROMAN_VALUES = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000,
    }
    
    # Decimal to Roman conversion map (ordered from largest to smallest)
    DECIMAL_TO_ROMAN = [
        (1000, 'M'),
        (900, 'CM'),
        (500, 'D'),
        (400, 'CD'),
        (100, 'C'),
        (90, 'XC'),
        (50, 'L'),
        (40, 'XL'),
        (10, 'X'),
        (9, 'IX'),
        (5, 'V'),
        (4, 'IV'),
        (1, 'I'),
    ]
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Roman Numeral Converter'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for conversions"""
        try:
            data = json.loads(request.body)
            conversion_type = data.get('conversion_type', 'decimal_to_roman')
            
            if conversion_type == 'decimal_to_roman':
                return self._convert_decimal_to_roman(data)
            elif conversion_type == 'roman_to_decimal':
                return self._convert_roman_to_decimal(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_decimal_to_roman(self, data):
        """Convert decimal number to Roman numeral"""
        try:
            if 'decimal' not in data or data.get('decimal') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Decimal number is required.')
                }, status=400)
            
            try:
                decimal = int(float(data.get('decimal', 0)))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a valid integer.')
                }, status=400)
            
            # Validate range
            if decimal < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('Decimal number must be at least 1.')
                }, status=400)
            
            if decimal > 3999:
                return JsonResponse({
                    'success': False,
                    'error': _('Decimal number cannot exceed 3999 (standard Roman numeral limit).')
                }, status=400)
            
            # Convert to Roman numeral
            roman, steps = self._decimal_to_roman_with_steps(decimal)
            
            chart_data = self._prepare_decimal_to_roman_chart_data(decimal, roman)
            
            return JsonResponse({
                'success': True,
                'conversion_type': 'decimal_to_roman',
                'decimal': decimal,
                'roman': roman,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting to Roman numeral: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_roman_to_decimal(self, data):
        """Convert Roman numeral to decimal number"""
        try:
            if 'roman' not in data or not data.get('roman'):
                return JsonResponse({
                    'success': False,
                    'error': _('Roman numeral is required.')
                }, status=400)
            
            roman = data.get('roman', '').strip().upper()
            
            if not roman:
                return JsonResponse({
                    'success': False,
                    'error': _('Roman numeral cannot be empty.')
                }, status=400)
            
            # Validate Roman numeral format
            if not self._is_valid_roman(roman):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid Roman numeral format.')
                }, status=400)
            
            # Convert to decimal
            decimal, steps = self._roman_to_decimal_with_steps(roman)
            
            # Validate result
            if decimal is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid Roman numeral.')
                }, status=400)
            
            chart_data = self._prepare_roman_to_decimal_chart_data(roman, decimal)
            
            return JsonResponse({
                'success': True,
                'conversion_type': 'roman_to_decimal',
                'roman': roman,
                'decimal': decimal,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting to decimal: {error}').format(error=str(e))
            }, status=500)
    
    def _decimal_to_roman_with_steps(self, decimal):
        """Convert decimal to Roman with step-by-step process"""
        steps = []
        steps.append(_('Step 1: Start with the decimal number'))
        steps.append(_('Decimal: {decimal}').format(decimal=decimal))
        steps.append('')
        steps.append(_('Step 2: Break down into Roman numeral components'))
        
        roman = ''
        remaining = decimal
        step_details = []
        
        for value, symbol in self.DECIMAL_TO_ROMAN:
            count = remaining // value
            if count > 0:
                roman += symbol * count
                step_details.append((value, symbol, count, remaining))
                remaining %= value
                steps.append(_('{count} × {value} = {symbol} × {count} = {symbols}').format(
                    count=count,
                    value=value,
                    symbol=symbol,
                    symbols=symbol * count
                ))
        
        steps.append('')
        steps.append(_('Step 3: Combine all components'))
        steps.append(_('Roman Numeral: {roman}').format(roman=roman))
        
        return roman, steps
    
    def _roman_to_decimal_with_steps(self, roman):
        """Convert Roman to decimal with step-by-step process"""
        steps = []
        steps.append(_('Step 1: Start with the Roman numeral'))
        steps.append(_('Roman: {roman}').format(roman=roman))
        steps.append('')
        steps.append(_('Step 2: Process each symbol from left to right'))
        
        decimal = 0
        i = 0
        step_details = []
        
        while i < len(roman):
            # Check for subtractive notation (two characters)
            if i + 1 < len(roman):
                two_char = roman[i:i+2]
                if two_char in ['IV', 'IX', 'XL', 'XC', 'CD', 'CM']:
                    value = self._get_roman_value(two_char)
                    if value:
                        decimal += value
                        step_details.append((two_char, value, 'subtractive'))
                        steps.append(_('{symbol} = {value} (subtractive notation)').format(symbol=two_char, value=value))
                        i += 2
                        continue
            
            # Single character
            char = roman[i]
            value = self.ROMAN_VALUES.get(char)
            if value:
                decimal += value
                step_details.append((char, value, 'additive'))
                steps.append(_('{symbol} = {value}').format(symbol=char, value=value))
                i += 1
            else:
                return None, []
        
        steps.append('')
        steps.append(_('Step 3: Sum all values'))
        sum_parts = ' + '.join([_('{value}').format(value=v) for _, v, _ in step_details])
        steps.append(_('Decimal = {sum}').format(sum=sum_parts))
        steps.append(_('Decimal = {decimal}').format(decimal=decimal))
        
        return decimal, steps
    
    def _get_roman_value(self, roman_pair):
        """Get value for subtractive notation pairs"""
        subtractive_values = {
            'IV': 4,
            'IX': 9,
            'XL': 40,
            'XC': 90,
            'CD': 400,
            'CM': 900,
        }
        return subtractive_values.get(roman_pair)
    
    def _is_valid_roman(self, roman):
        """Validate Roman numeral format"""
        # Check for invalid characters
        valid_chars = set('IVXLCDM')
        if not all(c in valid_chars for c in roman):
            return False
        
        # Check for invalid patterns
        # No more than 3 consecutive identical symbols (except M)
        pattern = r'(I{4,}|X{4,}|C{4,}|V{2,}|L{2,}|D{2,})'
        if re.search(pattern, roman):
            return False
        
        # Check for invalid subtractive patterns
        invalid_patterns = [
            'IL', 'IC', 'ID', 'IM',  # I can only subtract from V and X
            'VX', 'VL', 'VC', 'VD', 'VM',  # V cannot be subtracted
            'XD', 'XM',  # X can only subtract from L and C
            'LC', 'LD', 'LM',  # L cannot be subtracted
            'DM',  # D cannot be subtracted
        ]
        for pattern in invalid_patterns:
            if pattern in roman:
                return False
        
        return True
    
    def _prepare_decimal_to_roman_chart_data(self, decimal, roman):
        """Prepare chart data for decimal to Roman conversion"""
        try:
            # Break down the conversion
            breakdown = []
            remaining = decimal
            
            for value, symbol in self.DECIMAL_TO_ROMAN:
                count = remaining // value
                if count > 0:
                    breakdown.append({
                        'value': value * count,
                        'symbol': symbol * count,
                        'label': f'{symbol * count} ({value * count})'
                    })
                    remaining %= value
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [item['label'] for item in breakdown] + [_('Total')],
                    'datasets': [{
                        'label': _('Value'),
                        'data': [item['value'] for item in breakdown] + [decimal],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in breakdown
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in breakdown
                        ] + ['#10b981'],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Decimal to Roman Numeral Conversion')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'decimal_to_roman_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_roman_to_decimal_chart_data(self, roman, decimal):
        """Prepare chart data for Roman to decimal conversion"""
        try:
            # Break down the conversion
            breakdown = []
            i = 0
            
            while i < len(roman):
                if i + 1 < len(roman):
                    two_char = roman[i:i+2]
                    value = self._get_roman_value(two_char)
                    if value:
                        breakdown.append({
                            'symbol': two_char,
                            'value': value
                        })
                        i += 2
                        continue
                
                char = roman[i]
                value = self.ROMAN_VALUES.get(char)
                if value:
                    breakdown.append({
                        'symbol': char,
                        'value': value
                    })
                    i += 1
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [item['symbol'] for item in breakdown] + [_('Total')],
                    'datasets': [{
                        'label': _('Value'),
                        'data': [item['value'] for item in breakdown] + [decimal],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in breakdown
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in breakdown
                        ] + ['#10b981'],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Roman Numeral to Decimal Conversion')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'roman_to_decimal_chart': chart_config}
        except Exception as e:
            return None
