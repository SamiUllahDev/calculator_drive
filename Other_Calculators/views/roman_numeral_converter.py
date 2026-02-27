from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import re
import numpy as np
from sympy import Integer, Symbol, Add


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RomanNumeralConverter(View):
    """
    Class-based view for Roman Numeral Converter with full functionality

    Uses NumPy for efficient array-based value lookups and aggregation.
    Uses SymPy for symbolic representation of the conversion formula.

    Features:
    - Bidirectional conversion (decimal ↔ Roman, range 1–3999)
    - Standard subtractive notation (IV, IX, XL, XC, CD, CM)
    - Step-by-step conversion breakdown
    - Chart.js bar-chart visualization (backend-controlled)
    - Full i18n support via gettext_lazy
    """
    template_name = 'other_calculators/roman_numeral_converter.html'

    # ── Roman numeral single-symbol values ──────────────────────────
    ROMAN_VALUES = {
        'I': 1,
        'V': 5,
        'X': 10,
        'L': 50,
        'C': 100,
        'D': 500,
        'M': 1000,
    }

    # ── Subtractive notation pairs ──────────────────────────────────
    SUBTRACTIVE_VALUES = {
        'IV': 4,
        'IX': 9,
        'XL': 40,
        'XC': 90,
        'CD': 400,
        'CM': 900,
    }

    # ── Ordered map for decimal → Roman conversion ──────────────────
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

    # NumPy array of the decimal keys for fast look-ups
    _DECIMAL_KEYS = np.array([v for v, _ in DECIMAL_TO_ROMAN])

    # ================================================================
    # HTTP handlers
    # ================================================================

    def get(self, request):
        """Handle GET request – render the empty converter page."""
        context = {
            'calculator_name': _('Roman Numeral Converter'),
            'page_title': _('Roman Numeral Converter - Convert Numbers to Roman Numerals'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request – perform the requested conversion."""
        try:
            data = (
                json.loads(request.body)
                if request.content_type == 'application/json'
                else request.POST
            )
            conversion_type = data.get('conversion_type', 'decimal_to_roman')

            if conversion_type == 'decimal_to_roman':
                return self._convert_decimal_to_roman(data)
            elif conversion_type == 'roman_to_decimal':
                return self._convert_roman_to_decimal(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid conversion type.'))
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid JSON data.'))
            }, status=400)
        except Exception:
            return JsonResponse({
                'success': False,
                'error': str(_('An error occurred during conversion.'))
            }, status=500)

    # ================================================================
    # DECIMAL → ROMAN
    # ================================================================

    def _convert_decimal_to_roman(self, data):
        """Validate input and convert a decimal number to a Roman numeral."""
        try:
            # --- presence check ---
            raw = data.get('decimal')
            if raw is None or raw == '':
                return JsonResponse({
                    'success': False,
                    'error': str(_('Please enter a decimal number.'))
                }, status=400)

            # --- type check ---
            try:
                decimal = int(float(raw))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid input. Please enter a valid integer.'))
                }, status=400)

            # --- range check (NumPy for consistency with project style) ---
            val = np.array([decimal])
            if np.any(val < 1):
                return JsonResponse({
                    'success': False,
                    'error': str(_('Number must be at least 1.'))
                }, status=400)
            if np.any(val > 3999):
                return JsonResponse({
                    'success': False,
                    'error': str(_('Number cannot exceed 3999 (standard Roman numeral limit).'))
                }, status=400)

            # --- conversion ---
            roman, steps = self._decimal_to_roman_with_steps(decimal)

            # --- chart data ---
            chart_data = self._prepare_decimal_chart(decimal, roman)

            # --- color info ---
            color_info = self._get_color_info(decimal)

            return JsonResponse({
                'success': True,
                'conversion_type': 'decimal_to_roman',
                'decimal': decimal,
                'roman': roman,
                'step_by_step': steps,
                'chart_data': chart_data,
                'color_info': color_info,
            })

        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input: %(error)s') % {'error': str(e)})
            }, status=400)
        except Exception:
            return JsonResponse({
                'success': False,
                'error': str(_('Error converting to Roman numeral.'))
            }, status=500)

    # ================================================================
    # ROMAN → DECIMAL
    # ================================================================

    def _convert_roman_to_decimal(self, data):
        """Validate input and convert a Roman numeral to a decimal number."""
        try:
            raw = data.get('roman')
            if not raw:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Please enter a Roman numeral.'))
                }, status=400)

            roman = raw.strip().upper()
            if not roman:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Roman numeral cannot be empty.'))
                }, status=400)

            if not self._is_valid_roman(roman):
                return JsonResponse({
                    'success': False,
                    'error': str(_(
                        'Invalid Roman numeral format. '
                        'Only I, V, X, L, C, D, M are allowed with standard rules.'
                    ))
                }, status=400)

            decimal, steps = self._roman_to_decimal_with_steps(roman)

            if decimal is None:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid Roman numeral.'))
                }, status=400)

            chart_data = self._prepare_roman_chart(roman, decimal)
            color_info = self._get_color_info(decimal)

            return JsonResponse({
                'success': True,
                'conversion_type': 'roman_to_decimal',
                'roman': roman,
                'decimal': decimal,
                'step_by_step': steps,
                'chart_data': chart_data,
                'color_info': color_info,
            })

        except Exception:
            return JsonResponse({
                'success': False,
                'error': str(_('Error converting to decimal.'))
            }, status=500)

    # ================================================================
    # Conversion logic
    # ================================================================

    def _decimal_to_roman_with_steps(self, decimal):
        """Return (roman_string, steps_list) using SymPy symbolic addition."""
        steps = []

        # Step 1 – original number
        steps.append({
            'title': str(_('Step 1: Start with the decimal number')),
            'content': str(_('Decimal: %(decimal)s') % {'decimal': f'{decimal:,}'})
        })

        roman = ''
        remaining = decimal
        components = []

        # Use SymPy Integer for symbolic representation
        sym_remaining = Integer(decimal)
        sym_parts = []

        for value, symbol in self.DECIMAL_TO_ROMAN:
            count = remaining // value
            if count > 0:
                part = symbol * count
                roman += part
                part_value = value * count
                components.append({
                    'value': part_value,
                    'symbol': part,
                    'label': f'{part} ({part_value:,})'
                })
                sym_parts.append(Integer(part_value))
                remaining %= value

        # SymPy cross-check: sum of parts must equal original
        if sym_parts:
            sym_total = Add(*sym_parts)
            assert int(sym_total) == decimal, (
                f"SymPy verification failed: {sym_total} != {decimal}"
            )

        # NumPy cross-check
        if components:
            np_total = int(np.sum(np.array([c['value'] for c in components])))
            assert np_total == decimal, (
                f"NumPy verification failed: {np_total} != {decimal}"
            )

        # Step 2 – breakdown
        step2_lines = [f"{c['symbol']} = {c['value']:,}" for c in components]
        steps.append({
            'title': str(_('Step 2: Break down into Roman numeral components')),
            'content': ' , '.join(step2_lines)
        })

        # Step 3 – combine
        steps.append({
            'title': str(_('Step 3: Combine all components')),
            'content': str(_('Roman Numeral: %(roman)s') % {'roman': roman})
        })

        # Result
        steps.append({
            'title': str(_('Result')),
            'content': f'{decimal:,} = {roman}'
        })

        return roman, steps

    def _roman_to_decimal_with_steps(self, roman):
        """Return (decimal_int, steps_list)."""
        steps = []

        steps.append({
            'title': str(_('Step 1: Start with the Roman numeral')),
            'content': str(_('Roman: %(roman)s') % {'roman': roman})
        })

        decimal = 0
        i = 0
        parts = []

        while i < len(roman):
            # Try two-character subtractive pair first
            if i + 1 < len(roman):
                two_char = roman[i:i + 2]
                value = self.SUBTRACTIVE_VALUES.get(two_char)
                if value:
                    decimal += value
                    parts.append({'symbol': two_char, 'value': value, 'type': 'subtractive'})
                    i += 2
                    continue

            # Single character
            char = roman[i]
            value = self.ROMAN_VALUES.get(char)
            if value:
                decimal += value
                parts.append({'symbol': char, 'value': value, 'type': 'additive'})
                i += 1
            else:
                return None, []

        # NumPy cross-check
        np_values = np.array([p['value'] for p in parts])
        np_total = int(np.sum(np_values))
        if np_total != decimal:
            return None, []

        # Step 2 – per-symbol breakdown
        step2_lines = []
        for p in parts:
            note = str(_('(subtractive)')) if p['type'] == 'subtractive' else ''
            step2_lines.append(f"{p['symbol']} = {p['value']:,} {note}".strip())
        steps.append({
            'title': str(_('Step 2: Process each symbol from left to right')),
            'content': ' , '.join(step2_lines)
        })

        # Step 3 – sum
        sum_expr = ' + '.join([f"{p['value']:,}" for p in parts])
        steps.append({
            'title': str(_('Step 3: Sum all values')),
            'content': f'{sum_expr} = {decimal:,}'
        })

        # Result
        steps.append({
            'title': str(_('Result')),
            'content': f'{roman} = {decimal:,}'
        })

        return decimal, steps

    # ================================================================
    # Validation
    # ================================================================

    def _is_valid_roman(self, roman):
        """Validate a Roman numeral string against standard rules."""
        valid_chars = set('IVXLCDM')
        if not all(c in valid_chars for c in roman):
            return False

        # No more than 3 consecutive identical symbols (V, L, D may not repeat)
        if re.search(r'(I{4,}|V{2,}|X{4,}|L{2,}|C{4,}|D{2,}|M{4,})', roman):
            return False

        # Invalid subtractive patterns
        invalid_patterns = [
            'IL', 'IC', 'ID', 'IM',
            'VX', 'VL', 'VC', 'VD', 'VM',
            'XD', 'XM',
            'LC', 'LD', 'LM',
            'DM',
        ]
        for pat in invalid_patterns:
            if pat in roman:
                return False

        return True

    # ================================================================
    # Chart data helpers (backend-controlled, like BMI calculator)
    # ================================================================

    def _get_color_info(self, decimal):
        """Return colour information based on numeric magnitude."""
        # Partition 1-3999 into four visual tiers
        thresholds = np.array([1000, 2000, 3000])
        tier = int(np.searchsorted(thresholds, decimal))

        color_map = [
            {  # 1–999
                'hex': '#6366f1',
                'rgb': 'rgb(99, 102, 241)',
                'gradient': 'from-indigo-600 to-indigo-700',
                'name': 'indigo',
            },
            {  # 1000–1999
                'hex': '#8b5cf6',
                'rgb': 'rgb(139, 92, 246)',
                'gradient': 'from-violet-600 to-violet-700',
                'name': 'violet',
            },
            {  # 2000–2999
                'hex': '#a855f7',
                'rgb': 'rgb(168, 85, 247)',
                'gradient': 'from-purple-600 to-purple-700',
                'name': 'purple',
            },
            {  # 3000–3999
                'hex': '#ec4899',
                'rgb': 'rgb(236, 72, 153)',
                'gradient': 'from-pink-600 to-pink-700',
                'name': 'pink',
            },
        ]
        return color_map[tier]

    def _prepare_decimal_chart(self, decimal, roman):
        """Prepare Chart.js config for a decimal → Roman result."""
        try:
            breakdown = []
            remaining = decimal

            for value, symbol in self.DECIMAL_TO_ROMAN:
                count = remaining // value
                if count > 0:
                    breakdown.append({
                        'value': value * count,
                        'symbol': symbol * count,
                        'label': f'{symbol * count} ({value * count:,})'
                    })
                    remaining %= value

            labels = [item['label'] for item in breakdown] + [str(_('Total'))]
            values = [item['value'] for item in breakdown] + [decimal]
            bg_colors = (
                ['rgba(99, 102, 241, 0.7)'] * len(breakdown)
                + ['rgba(16, 185, 129, 0.8)']
            )
            border_colors = (
                ['#6366f1'] * len(breakdown)
                + ['#10b981']
            )

            # Gauge-style doughnut (like BMI gauge)
            max_val = 3999.0
            pct = min((decimal / max_val) * 100, 100)
            color_info = self._get_color_info(decimal)

            gauge_chart = {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Value')), str(_('Remaining'))],
                    'datasets': [{
                        'data': [round(pct, 2), round(100 - pct, 2)],
                        'backgroundColor': [color_info['hex'], '#e5e7eb'],
                        'borderWidth': 0,
                        'cutout': '75%'
                    }]
                },
                'center_text': {
                    'value': decimal,
                    'label': roman,
                    'color': color_info['hex']
                }
            }

            bar_chart = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Value')),
                        'data': values,
                        'backgroundColor': bg_colors,
                        'borderColor': border_colors,
                        'borderWidth': 2,
                        'borderRadius': 8,
                    }]
                },
            }

            return {
                'gauge_chart': gauge_chart,
                'bar_chart': bar_chart,
            }
        except Exception:
            return None

    def _prepare_roman_chart(self, roman, decimal):
        """Prepare Chart.js config for a Roman → decimal result."""
        try:
            breakdown = []
            i = 0

            while i < len(roman):
                if i + 1 < len(roman):
                    two_char = roman[i:i + 2]
                    value = self.SUBTRACTIVE_VALUES.get(two_char)
                    if value:
                        breakdown.append({'symbol': two_char, 'value': value})
                        i += 2
                        continue

                char = roman[i]
                value = self.ROMAN_VALUES.get(char)
                if value:
                    breakdown.append({'symbol': char, 'value': value})
                    i += 1

            labels = [item['symbol'] for item in breakdown] + [str(_('Total'))]
            values = [item['value'] for item in breakdown] + [decimal]
            bg_colors = (
                ['rgba(99, 102, 241, 0.7)'] * len(breakdown)
                + ['rgba(16, 185, 129, 0.8)']
            )
            border_colors = (
                ['#6366f1'] * len(breakdown)
                + ['#10b981']
            )

            # Gauge
            max_val = 3999.0
            pct = min((decimal / max_val) * 100, 100)
            color_info = self._get_color_info(decimal)

            gauge_chart = {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Value')), str(_('Remaining'))],
                    'datasets': [{
                        'data': [round(pct, 2), round(100 - pct, 2)],
                        'backgroundColor': [color_info['hex'], '#e5e7eb'],
                        'borderWidth': 0,
                        'cutout': '75%'
                    }]
                },
                'center_text': {
                    'value': decimal,
                    'label': roman,
                    'color': color_info['hex']
                }
            }

            bar_chart = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Value')),
                        'data': values,
                        'backgroundColor': bg_colors,
                        'borderColor': border_colors,
                        'borderWidth': 2,
                        'borderRadius': 8,
                    }]
                },
            }

            return {
                'gauge_chart': gauge_chart,
                'bar_chart': bar_chart,
            }
        except Exception:
            return None
