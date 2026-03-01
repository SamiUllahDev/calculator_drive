from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np
from sympy import Integer, Symbol, simplify, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RomanNumeralConverter(View):
    """
    Class-based view for Roman Numeral Converter with full functionality

    Uses NumPy for efficient array-based operations and batch processing.
    Uses SymPy for precise integer arithmetic and symbolic validation.
    """
    template_name = 'other_calculators/roman_numeral_converter.html'

    # Roman numeral mapping (descending order for greedy algorithm)
    ROMAN_VALUES = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]

    # Valid Roman numeral characters and their values
    ROMAN_CHAR_VALUES = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }

    # Subtractive pairs for validation
    VALID_SUBTRACTIVE = {'IV', 'IX', 'XL', 'XC', 'CD', 'CM'}

    # Max repetitions allowed for each character
    MAX_REPETITIONS = {
        'I': 3, 'V': 1, 'X': 3, 'L': 1,
        'C': 3, 'D': 1, 'M': 3
    }

    # Standard range for Roman numerals
    MIN_VALUE = Integer(1)
    MAX_VALUE = Integer(3999)

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Roman Numeral Converter'),
            'page_title': _('Roman Numeral Converter - Convert Between Roman and Arabic Numbers'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for conversions using NumPy and SymPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

            conversion_type = data.get('conversion_type', 'to_roman')  # 'to_roman' or 'to_arabic'
            input_value = data.get('input_value', '').strip()

            if not input_value:
                return JsonResponse({
                    'error': str(_('Please enter a value to convert.')),
                    'success': False
                }, status=400)

            if conversion_type == 'to_roman':
                return self._convert_to_roman(input_value)
            elif conversion_type == 'to_arabic':
                return self._convert_to_arabic(input_value)
            else:
                return JsonResponse({
                    'error': str(_('Invalid conversion type.')),
                    'success': False
                }, status=400)

        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input:')) + ' ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('An error occurred during conversion.'))
            }, status=500)

    def _convert_to_roman(self, input_value):
        """Convert Arabic number to Roman numeral using SymPy and NumPy"""
        try:
            number = int(input_value)
        except ValueError:
            return JsonResponse({
                'error': str(_('Please enter a valid integer number.')),
                'success': False
            }, status=400)

        # Validate range using SymPy Integer for precision
        sym_number = Integer(number)
        if sym_number < self.MIN_VALUE or sym_number > self.MAX_VALUE:
            return JsonResponse({
                'error': str(_('Number must be between')) + f' {self.MIN_VALUE} ' + str(_('and')) + f' {self.MAX_VALUE}.',
                'success': False
            }, status=400)

        # Convert to Roman using greedy algorithm
        roman_result = self._int_to_roman(number)

        # Cross-verify with NumPy-based reverse conversion
        verify_value = self._roman_to_int_numpy(roman_result)
        if verify_value != number:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Conversion discrepancy: input={number}, roman={roman_result}, verify={verify_value}")

        # Build breakdown of how the number is composed
        breakdown = self._get_conversion_breakdown(number)

        # Calculate place values using NumPy
        place_values = self._get_place_values(number)

        # Prepare chart data (backend-controlled)
        chart_data = self._prepare_chart_data(number, breakdown)

        # Get numeral analysis
        analysis = self._analyze_roman_numeral(roman_result, number)

        return JsonResponse({
            'success': True,
            'input_value': number,
            'result': roman_result,
            'conversion_type': 'to_roman',
            'breakdown': breakdown,
            'place_values': place_values,
            'chart_data': chart_data,
            'analysis': analysis,
            'fun_facts': self._get_fun_facts(number),
        })

    def _convert_to_arabic(self, input_value):
        """Convert Roman numeral to Arabic number using SymPy and NumPy"""
        roman_input = input_value.upper().strip()

        # Validate Roman numeral string
        validation_error = self._validate_roman_numeral(roman_input)
        if validation_error:
            return JsonResponse({
                'error': validation_error,
                'success': False
            }, status=400)

        # Convert using NumPy-based approach
        arabic_result = self._roman_to_int_numpy(roman_input)

        # Verify with SymPy by converting back
        sym_result = Integer(arabic_result)
        verify_roman = self._int_to_roman(int(sym_result))

        if verify_roman != roman_input:
            # The input is a valid but non-standard form
            is_standard = False
            standard_form = verify_roman
        else:
            is_standard = True
            standard_form = roman_input

        # Build breakdown
        breakdown = self._get_roman_breakdown(roman_input)

        # Place values
        place_values = self._get_place_values(arabic_result)

        # Chart data
        chart_data = self._prepare_chart_data(arabic_result, self._get_conversion_breakdown(arabic_result))

        # Analysis
        analysis = self._analyze_roman_numeral(roman_input, arabic_result)

        return JsonResponse({
            'success': True,
            'input_value': roman_input,
            'result': arabic_result,
            'conversion_type': 'to_arabic',
            'is_standard_form': is_standard,
            'standard_form': standard_form,
            'breakdown': breakdown,
            'place_values': place_values,
            'chart_data': chart_data,
            'analysis': analysis,
            'fun_facts': self._get_fun_facts(arabic_result),
        })

    def _int_to_roman(self, number):
        """Convert integer to Roman numeral string using greedy algorithm"""
        result = []
        remaining = number
        for value, numeral in self.ROMAN_VALUES:
            while remaining >= value:
                result.append(numeral)
                remaining -= value
        return ''.join(result)

    def _roman_to_int_numpy(self, roman):
        """Convert Roman numeral to integer using NumPy for efficient computation"""
        if not roman:
            return 0

        # Create NumPy array of values
        values = np.array([self.ROMAN_CHAR_VALUES.get(c, 0) for c in roman])

        if len(values) == 0:
            return 0

        # Use NumPy vectorized operations for subtractive notation
        # If a value is less than the next value, subtract it; otherwise add it
        shifted = np.roll(values, -1)
        shifted[-1] = 0  # Last element has nothing after it

        # Where current < next, subtract (subtractive notation)
        signs = np.where(values < shifted, -1, 1)

        # Total = sum of signed values
        total = int(np.sum(values * signs))

        return total

    def _validate_roman_numeral(self, roman):
        """Validate a Roman numeral string and return error message or None"""
        if not roman:
            return str(_('Please enter a Roman numeral.'))

        # Check for invalid characters
        for char in roman:
            if char not in self.ROMAN_CHAR_VALUES:
                return str(_('Invalid character')) + f' "{char}". ' + str(_('Valid Roman numerals are: I, V, X, L, C, D, M.'))

        # Check for too many consecutive repetitions
        count = 1
        for i in range(1, len(roman)):
            if roman[i] == roman[i - 1]:
                count += 1
                max_allowed = self.MAX_REPETITIONS.get(roman[i], 1)
                if count > max_allowed:
                    return str(_('Character')) + f' "{roman[i]}" ' + str(_('cannot be repeated more than')) + f' {max_allowed} ' + str(_('time(s).'))
            else:
                count = 1

        # Check that value is within range
        value = self._roman_to_int_numpy(roman)
        if value < int(self.MIN_VALUE) or value > int(self.MAX_VALUE):
            return str(_('Roman numeral must represent a value between')) + f' {self.MIN_VALUE} ' + str(_('and')) + f' {self.MAX_VALUE}.'

        return None

    def _get_conversion_breakdown(self, number):
        """Get step-by-step breakdown of integer to Roman conversion"""
        breakdown = []
        remaining = number
        for value, numeral in self.ROMAN_VALUES:
            if remaining >= value:
                count = remaining // value
                breakdown.append({
                    'value': value,
                    'numeral': numeral,
                    'count': count,
                    'subtotal': value * count,
                    'description': f'{numeral} × {count} = {value * count}'
                })
                remaining -= value * count
        return breakdown

    def _get_roman_breakdown(self, roman):
        """Get step-by-step breakdown of Roman to integer conversion"""
        breakdown = []
        values = [self.ROMAN_CHAR_VALUES[c] for c in roman]

        i = 0
        while i < len(roman):
            if i + 1 < len(roman) and values[i] < values[i + 1]:
                # Subtractive pair
                pair = roman[i:i + 2]
                pair_value = values[i + 1] - values[i]
                breakdown.append({
                    'numeral': pair,
                    'value': pair_value,
                    'type': 'subtractive',
                    'description': f'{pair} = {values[i + 1]} - {values[i]} = {pair_value}'
                })
                i += 2
            else:
                # Additive
                breakdown.append({
                    'numeral': roman[i],
                    'value': values[i],
                    'type': 'additive',
                    'description': f'{roman[i]} = {values[i]}'
                })
                i += 1
        return breakdown

    def _get_place_values(self, number):
        """Decompose number into place values using NumPy"""
        if number == 0:
            return []

        num_array = np.array([number])

        # Extract thousands, hundreds, tens, ones
        thousands = int((num_array // 1000)[0])
        hundreds = int(((num_array % 1000) // 100)[0])
        tens = int(((num_array % 100) // 10)[0])
        ones = int((num_array % 10)[0])

        place_values = []
        if thousands > 0:
            place_values.append({
                'place': str(_('Thousands')),
                'digit': thousands,
                'value': thousands * 1000,
                'roman': self._int_to_roman(thousands * 1000)
            })
        if hundreds > 0:
            place_values.append({
                'place': str(_('Hundreds')),
                'digit': hundreds,
                'value': hundreds * 100,
                'roman': self._int_to_roman(hundreds * 100)
            })
        if tens > 0:
            place_values.append({
                'place': str(_('Tens')),
                'digit': tens,
                'value': tens * 10,
                'roman': self._int_to_roman(tens * 10)
            })
        if ones > 0:
            place_values.append({
                'place': str(_('Ones')),
                'digit': ones,
                'value': ones,
                'roman': self._int_to_roman(ones)
            })

        return place_values

    def _analyze_roman_numeral(self, roman, arabic):
        """Analyze properties of the numeral"""
        # Character frequency using NumPy
        chars = list(roman)
        unique_chars = list(set(chars))
        char_counts = {c: chars.count(c) for c in unique_chars}

        # Numeral length
        length = len(roman)

        # Is it a palindrome?
        is_palindrome = roman == roman[::-1]

        # Uses subtractive notation?
        uses_subtractive = any(pair in roman for pair in self.VALID_SUBTRACTIVE)

        # Number properties using SymPy
        sym_num = Integer(arabic)
        is_even = bool(sym_num % 2 == 0)
        is_prime = bool(sym_num.is_prime) if arabic > 1 else False

        # Nearest round numbers
        nearest_hundred = int(round(arabic / 100) * 100) if arabic >= 50 else arabic
        nearest_ten = int(round(arabic / 10) * 10)

        return {
            'length': length,
            'unique_characters': len(unique_chars),
            'character_frequency': char_counts,
            'is_palindrome': is_palindrome,
            'uses_subtractive': uses_subtractive,
            'is_even': is_even,
            'is_prime': is_prime,
            'nearest_ten': nearest_ten,
            'nearest_hundred': nearest_hundred,
            'roman_nearest_ten': self._int_to_roman(nearest_ten) if 1 <= nearest_ten <= 3999 else str(_('N/A')),
            'roman_nearest_hundred': self._int_to_roman(nearest_hundred) if 1 <= nearest_hundred <= 3999 else str(_('N/A')),
        }

    def _get_fun_facts(self, number):
        """Get interesting facts about the number"""
        facts = []

        if number == 1:
            facts.append(str(_('I is the simplest Roman numeral.')))
        if number == 4:
            facts.append(str(_('IV uses subtractive notation (5 - 1) instead of IIII.')))
        if number == 9:
            facts.append(str(_('IX uses subtractive notation (10 - 1) instead of VIIII.')))
        if number == 42:
            facts.append(str(_('XLII — "The Answer to the Ultimate Question of Life, the Universe, and Everything."')))
        if number == 100:
            facts.append(str(_('C stands for "centum," the Latin word for 100.')))
        if number == 500:
            facts.append(str(_('D stands for the right half of the symbol Φ (phi), which was used for 1000.')))
        if number == 1000:
            facts.append(str(_('M stands for "mille," the Latin word for 1000.')))
        if number == 666:
            facts.append(str(_('DCLXVI uses each of D, C, L, X, V, I exactly once in descending order.')))
        if number == 1776:
            facts.append(str(_('MDCCLXXVI — The year of the United States Declaration of Independence.')))
        if number == 2024:
            facts.append(str(_('MMXXIV — The current year in Roman numerals.')))
        if number == 3999:
            facts.append(str(_('MMMCMXCIX is the largest standard Roman numeral (3999).')))

        # General facts
        sym_num = Integer(number)
        if number > 1 and sym_num.is_prime:
            facts.append(str(number) + ' ' + str(_('is a prime number.')))
        if number > 0 and int(number ** 0.5) ** 2 == number:
            facts.append(str(number) + ' ' + str(_('is a perfect square')) + f' ({int(number ** 0.5)}²).')

        roman = self._int_to_roman(number)
        if len(roman) == 1:
            facts.append(roman + ' ' + str(_('is one of the 7 basic Roman numeral symbols.')))
        if len(roman) >= 10:
            facts.append(str(_('This number requires')) + f' {len(roman)} ' + str(_('Roman numeral characters — quite long!')))

        return facts

    def _prepare_chart_data(self, number, breakdown):
        """Prepare chart data for visualization (backend-controlled)"""
        # Place value distribution chart
        place_colors = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd']
        place_labels = []
        place_data = []

        thousands = number // 1000
        hundreds = (number % 1000) // 100
        tens = (number % 100) // 10
        ones = number % 10

        if thousands > 0:
            place_labels.append(str(_('Thousands')))
            place_data.append(thousands * 1000)
        if hundreds > 0:
            place_labels.append(str(_('Hundreds')))
            place_data.append(hundreds * 100)
        if tens > 0:
            place_labels.append(str(_('Tens')))
            place_data.append(tens * 10)
        if ones > 0:
            place_labels.append(str(_('Ones')))
            place_data.append(ones)

        place_value_chart = {
            'type': 'doughnut',
            'data': {
                'labels': place_labels,
                'datasets': [{
                    'data': place_data,
                    'backgroundColor': place_colors[:len(place_data)],
                    'borderWidth': 2,
                    'borderColor': '#ffffff',
                    'cutout': '60%'
                }]
            },
            'center_text': {
                'value': number,
                'label': self._int_to_roman(number),
                'color': '#6366f1'
            }
        }

        # Breakdown bar chart
        breakdown_labels = [item['numeral'] for item in breakdown]
        breakdown_data = [item['subtotal'] for item in breakdown]
        bar_colors = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe',
                      '#ede9fe', '#f5f3ff', '#6366f1', '#8b5cf6', '#a78bfa']

        breakdown_chart = {
            'type': 'bar',
            'data': {
                'labels': breakdown_labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': breakdown_data,
                    'backgroundColor': bar_colors[:len(breakdown_data)],
                    'borderColor': '#6366f1',
                    'borderWidth': 1,
                    'borderRadius': 8
                }]
            }
        }

        # Comparison chart: show nearby numbers
        nearby_numbers = []
        nearby_labels = []
        nearby_roman = []
        for offset in [-5, -2, -1, 0, 1, 2, 5]:
            n = number + offset
            if 1 <= n <= 3999:
                nearby_numbers.append(n)
                nearby_labels.append(self._int_to_roman(n))
                nearby_roman.append(self._int_to_roman(n))

        # Color the current number differently
        nearby_colors = []
        for n in nearby_numbers:
            if n == number:
                nearby_colors.append('#6366f1')
            else:
                nearby_colors.append('#e0e7ff')

        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': nearby_labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': nearby_numbers,
                    'backgroundColor': nearby_colors,
                    'borderColor': '#6366f1',
                    'borderWidth': 1,
                    'borderRadius': 6
                }]
            },
            'nearby_roman': nearby_roman
        }

        return {
            'place_value_chart': place_value_chart,
            'breakdown_chart': breakdown_chart,
            'comparison_chart': comparison_chart,
        }
