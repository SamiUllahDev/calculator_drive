from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ResistorCalculator(View):
    """
    Resistor Calculator — Color Code, Series, Parallel & Power.

    Features:
        • Decode resistance from 4-band, 5-band, or 6-band color codes
        • Calculate total series resistance  (R = R1 + R2 + …)
        • Calculate total parallel resistance (1/R = 1/R1 + 1/R2 + …)
        • Calculate power dissipation        (P = V² / R)

    Uses NumPy for vectorised arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/resistor_calculator.html'

    # ── color-code lookup ────────────────────────────────────────────
    COLOR_CODES = {
        'black':  {'value': 0, 'multiplier': 1,           'tolerance': None, 'temp_coeff': 250},
        'brown':  {'value': 1, 'multiplier': 10,          'tolerance': 1,    'temp_coeff': 100},
        'red':    {'value': 2, 'multiplier': 100,         'tolerance': 2,    'temp_coeff': 50},
        'orange': {'value': 3, 'multiplier': 1000,        'tolerance': None, 'temp_coeff': 15},
        'yellow': {'value': 4, 'multiplier': 10000,       'tolerance': None, 'temp_coeff': 25},
        'green':  {'value': 5, 'multiplier': 100000,      'tolerance': 0.5,  'temp_coeff': 20},
        'blue':   {'value': 6, 'multiplier': 1000000,     'tolerance': 0.25, 'temp_coeff': 10},
        'violet': {'value': 7, 'multiplier': 10000000,    'tolerance': 0.1,  'temp_coeff': 5},
        'gray':   {'value': 8, 'multiplier': 100000000,   'tolerance': 0.05, 'temp_coeff': 1},
        'white':  {'value': 9, 'multiplier': 1000000000,  'tolerance': None, 'temp_coeff': None},
        'gold':   {'value': None, 'multiplier': 0.1,      'tolerance': 5,    'temp_coeff': None},
        'silver': {'value': None, 'multiplier': 0.01,     'tolerance': 10,   'temp_coeff': None},
    }

    # ── resistance unit conversion (to Ω) ────────────────────────────
    R_CONV = {'ohms': 1.0, 'milliohms': 1e-3, 'kiloohms': 1e3, 'megaohms': 1e6}

    UNIT_SYM = {
        'ohms': 'Ω', 'milliohms': 'mΩ', 'kiloohms': 'kΩ', 'megaohms': 'MΩ',
    }

    def _u(self, key):
        return self.UNIT_SYM.get(key, key)

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Resistor Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'color_code')
            dispatch = {
                'color_code': self._calc_color_code,
                'series': self._calc_series,
                'parallel': self._calc_parallel,
                'power': self._calc_power,
            }
            handler = dispatch.get(calc)
            if not handler:
                return self._err(_('Invalid calculation type.'))
            return handler(data)
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(_('Invalid input:')) + ' ' + str(e))
        except Exception:
            return self._err(_('An error occurred during calculation.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    def _fnum(self, v, dp=6):
        if v is None:
            return '0'
        if abs(v) < 1e-6 or abs(v) >= 1e9:
            return f'{v:.6g}'
        return f'{v:,.{dp}g}'

    def _format_resistance(self, ohms):
        """Return a human-friendly string like '4.7 kΩ'."""
        if ohms >= 1e6:
            return f'{ohms / 1e6:.2f} MΩ'
        if ohms >= 1e3:
            return f'{ohms / 1e3:.2f} kΩ'
        if ohms < 1:
            return f'{ohms * 1e3:.2f} mΩ'
        return f'{ohms:.2f} Ω'

    def _safe_pos(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        if v > 1e15:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _safe(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        if v > 1e15:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _to_ohms(self, v, unit, name):
        if unit not in self.R_CONV:
            raise ValueError(str(_('{name}: invalid unit "{unit}".').format(name=name, unit=unit)))
        return float(np.float64(v) * self.R_CONV[unit])

    def _from_ohms(self, ohms, unit):
        return float(np.float64(ohms) / self.R_CONV[unit])

    def _verify(self, val):
        if not np.isfinite(val):
            raise ValueError(str(_('Calculation produced an invalid result.')))
        return val

    # ── COLOR CODE ───────────────────────────────────────────────────
    def _calc_color_code(self, d):
        band_type = d.get('band_type', '4_band')

        if band_type == '4_band':
            colors = [d.get('band1'), d.get('band2'), d.get('multiplier'), d.get('tolerance')]
            if not all(colors):
                return self._err(_('All color bands are required.'))
            for c in colors:
                if c not in self.COLOR_CODES:
                    return self._err(_('Invalid color: {color}').format(color=c))
            d1 = self.COLOR_CODES[colors[0]]['value']
            d2 = self.COLOR_CODES[colors[1]]['value']
            mult = self.COLOR_CODES[colors[2]]['multiplier']
            tol = self.COLOR_CODES[colors[3]]['tolerance']
            if d1 is None or d2 is None:
                return self._err(_('Invalid color for digit bands.'))
            if tol is None:
                return self._err(_('Invalid tolerance color.'))
            resistance = float(np.multiply(d1 * 10 + d2, mult))
            steps = [
                str(_('Step 1: Identify the color bands')),
                f'  • {_("Band 1 (1st digit)")}: {colors[0]} = {d1}',
                f'  • {_("Band 2 (2nd digit)")}: {colors[1]} = {d2}',
                f'  • {_("Multiplier")}: {colors[2]} = ×{mult}',
                f'  • {_("Tolerance")}: {colors[3]} = ±{tol}%',
                '',
                str(_('Step 2: Calculate resistance')),
                f'  {_("Formula")}: R = (D1×10 + D2) × Multiplier',
                f'  R = ({d1}×10 + {d2}) × {mult}',
                f'  R = {self._fnum(resistance)} Ω',
            ]

        elif band_type == '5_band':
            colors = [d.get('band1'), d.get('band2'), d.get('band3'), d.get('multiplier'), d.get('tolerance')]
            if not all(colors):
                return self._err(_('All color bands are required.'))
            for c in colors:
                if c not in self.COLOR_CODES:
                    return self._err(_('Invalid color: {color}').format(color=c))
            d1 = self.COLOR_CODES[colors[0]]['value']
            d2 = self.COLOR_CODES[colors[1]]['value']
            d3 = self.COLOR_CODES[colors[2]]['value']
            mult = self.COLOR_CODES[colors[3]]['multiplier']
            tol = self.COLOR_CODES[colors[4]]['tolerance']
            if any(x is None for x in [d1, d2, d3]):
                return self._err(_('Invalid color for digit bands.'))
            if tol is None:
                return self._err(_('Invalid tolerance color.'))
            resistance = float(np.multiply(d1 * 100 + d2 * 10 + d3, mult))
            steps = [
                str(_('Step 1: Identify the color bands')),
                f'  • {_("Band 1 (1st digit)")}: {colors[0]} = {d1}',
                f'  • {_("Band 2 (2nd digit)")}: {colors[1]} = {d2}',
                f'  • {_("Band 3 (3rd digit)")}: {colors[2]} = {d3}',
                f'  • {_("Multiplier")}: {colors[3]} = ×{mult}',
                f'  • {_("Tolerance")}: {colors[4]} = ±{tol}%',
                '',
                str(_('Step 2: Calculate resistance')),
                f'  {_("Formula")}: R = (D1×100 + D2×10 + D3) × Multiplier',
                f'  R = ({d1}×100 + {d2}×10 + {d3}) × {mult}',
                f'  R = {self._fnum(resistance)} Ω',
            ]

        elif band_type == '6_band':
            colors = [d.get('band1'), d.get('band2'), d.get('band3'),
                      d.get('multiplier'), d.get('tolerance'), d.get('temp_coeff')]
            if not all(colors):
                return self._err(_('All color bands are required.'))
            for c in colors:
                if c not in self.COLOR_CODES:
                    return self._err(_('Invalid color: {color}').format(color=c))
            d1 = self.COLOR_CODES[colors[0]]['value']
            d2 = self.COLOR_CODES[colors[1]]['value']
            d3 = self.COLOR_CODES[colors[2]]['value']
            mult = self.COLOR_CODES[colors[3]]['multiplier']
            tol = self.COLOR_CODES[colors[4]]['tolerance']
            temp = self.COLOR_CODES[colors[5]]['temp_coeff']
            if any(x is None for x in [d1, d2, d3]):
                return self._err(_('Invalid color for digit bands.'))
            if tol is None:
                return self._err(_('Invalid tolerance color.'))
            if temp is None:
                return self._err(_('Invalid temperature coefficient color.'))
            resistance = float(np.multiply(d1 * 100 + d2 * 10 + d3, mult))
            steps = [
                str(_('Step 1: Identify the color bands')),
                f'  • {_("Band 1 (1st digit)")}: {colors[0]} = {d1}',
                f'  • {_("Band 2 (2nd digit)")}: {colors[1]} = {d2}',
                f'  • {_("Band 3 (3rd digit)")}: {colors[2]} = {d3}',
                f'  • {_("Multiplier")}: {colors[3]} = ×{mult}',
                f'  • {_("Tolerance")}: {colors[4]} = ±{tol}%',
                f'  • {_("Temp Coeff")}: {colors[5]} = {temp} ppm/°C',
                '',
                str(_('Step 2: Calculate resistance')),
                f'  {_("Formula")}: R = (D1×100 + D2×10 + D3) × Multiplier',
                f'  R = ({d1}×100 + {d2}×10 + {d3}) × {mult}',
                f'  R = {self._fnum(resistance)} Ω',
            ]
        else:
            return self._err(_('Invalid band type.'))

        tol_val = tol if isinstance(tol, (int, float)) else 0
        min_r = float(np.multiply(resistance, 1 - tol_val / 100))
        max_r = float(np.multiply(resistance, 1 + tol_val / 100))
        formatted = self._format_resistance(resistance)

        steps += [
            '',
            str(_('Step 3: Tolerance range')),
            f'  {_("Min")} = {self._fnum(min_r)} Ω',
            f'  {_("Max")} = {self._fnum(max_r)} Ω',
            '',
            str(_('Step 4: Result')),
            f'  {_("Resistance")} = {formatted} ± {tol_val}%',
        ]

        chart = self._bar_chart(
            [str(_('Min')), str(_('Nominal')), str(_('Max'))],
            [min_r, resistance, max_r],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Resistance Tolerance Range'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'color_code',
            'band_type': band_type,
            'resistance': round(resistance, 2),
            'tolerance': tol_val,
            'min_resistance': round(min_r, 2),
            'max_resistance': round(max_r, 2),
            'formatted_value': formatted,
            'result_label': str(_('Resistance')),
            'step_by_step': steps,
            'chart_data': {'resistor_chart': chart},
        })

    # ── SERIES: R_total = R1 + R2 + … ───────────────────────────────
    def _calc_series(self, d):
        resistors = d.get('resistors', [])
        if not resistors or len(resistors) < 2:
            return self._err(_('At least two resistors are required.'))

        values, units = [], []
        for i, r in enumerate(resistors):
            val = self._safe_pos(r.get('value'), f'R{i+1}')
            unit = r.get('unit', 'ohms')
            if unit not in self.R_CONV:
                return self._err(_('Invalid unit for resistor {index}.').format(index=i+1))
            values.append(val)
            units.append(unit)

        ohms = [self._to_ohms(v, u, f'R{i+1}') for i, (v, u) in enumerate(zip(values, units))]
        total = self._verify(float(np.sum(ohms)))

        res_u = d.get('result_unit', 'ohms')
        if res_u not in self.R_CONV:
            res_u = 'ohms'
        result = self._from_ohms(total, res_u)

        steps = [
            str(_('Step 1: Identify the resistor values')),
        ]
        for i, (v, u) in enumerate(zip(values, units)):
            steps.append(f'  • R{i+1} = {v} {self._u(u)}')
        steps += ['', str(_('Step 2: Convert all to ohms'))]
        for i, r in enumerate(ohms):
            steps.append(f'  R{i+1} = {self._fnum(r)} Ω')
        steps += [
            '',
            str(_('Step 3: Apply series formula')),
            f'  {_("Formula")}: R_total = R1 + R2 + …',
            f'  R_total = {" + ".join(self._fnum(r) for r in ohms)}',
            f'  R_total = {self._fnum(total)} Ω',
            '',
            str(_('Step 4: Result')),
            f'  {_("Total Resistance")} = {self._fnum(result)} {self._u(res_u)}',
        ]

        labels = [f'R{i+1}' for i in range(len(ohms))] + [str(_('Total'))]
        data = list(ohms) + [total]
        colors = ['rgba(59,130,246,0.8)'] * len(ohms) + ['rgba(16,185,129,0.8)']
        chart = self._bar_chart(labels, data, colors, str(_('Series Resistance')))

        return JsonResponse({
            'success': True, 'calc_type': 'series',
            'result': round(result, 6), 'result_unit': res_u,
            'result_unit_symbol': self._u(res_u),
            'result_label': str(_('Total Resistance')),
            'total_resistance_ohms': round(total, 6),
            'formula': 'R_total = R1 + R2 + …',
            'step_by_step': steps,
            'chart_data': {'resistor_chart': chart},
        })

    # ── PARALLEL: 1/R_total = 1/R1 + 1/R2 + … ──────────────────────
    def _calc_parallel(self, d):
        resistors = d.get('resistors', [])
        if not resistors or len(resistors) < 2:
            return self._err(_('At least two resistors are required.'))

        values, units = [], []
        for i, r in enumerate(resistors):
            val = self._safe_pos(r.get('value'), f'R{i+1}')
            unit = r.get('unit', 'ohms')
            if unit not in self.R_CONV:
                return self._err(_('Invalid unit for resistor {index}.').format(index=i+1))
            values.append(val)
            units.append(unit)

        ohms = [self._to_ohms(v, u, f'R{i+1}') for i, (v, u) in enumerate(zip(values, units))]
        reciprocals = [float(np.divide(1.0, r)) for r in ohms]
        total_recip = float(np.sum(reciprocals))
        total = self._verify(float(np.divide(1.0, total_recip)))

        res_u = d.get('result_unit', 'ohms')
        if res_u not in self.R_CONV:
            res_u = 'ohms'
        result = self._from_ohms(total, res_u)

        steps = [
            str(_('Step 1: Identify the resistor values')),
        ]
        for i, (v, u) in enumerate(zip(values, units)):
            steps.append(f'  • R{i+1} = {v} {self._u(u)}')
        steps += ['', str(_('Step 2: Convert all to ohms'))]
        for i, r in enumerate(ohms):
            steps.append(f'  R{i+1} = {self._fnum(r)} Ω')
        steps += ['', str(_('Step 3: Calculate reciprocals'))]
        for i, rec in enumerate(reciprocals):
            steps.append(f'  1/R{i+1} = 1/{self._fnum(ohms[i])} = {self._fnum(rec)}')
        steps += [
            '',
            str(_('Step 4: Apply parallel formula')),
            f'  {_("Formula")}: 1/R_total = 1/R1 + 1/R2 + …',
            f'  1/R_total = {" + ".join(self._fnum(r) for r in reciprocals)}',
            f'  1/R_total = {self._fnum(total_recip)}',
            f'  R_total = 1 / {self._fnum(total_recip)} = {self._fnum(total)} Ω',
            '',
            str(_('Step 5: Result')),
            f'  {_("Total Resistance")} = {self._fnum(result)} {self._u(res_u)}',
        ]

        labels = [f'R{i+1}' for i in range(len(ohms))] + [str(_('Total'))]
        data = list(ohms) + [total]
        colors = ['rgba(59,130,246,0.8)'] * len(ohms) + ['rgba(16,185,129,0.8)']
        chart = self._bar_chart(labels, data, colors, str(_('Parallel Resistance')))

        return JsonResponse({
            'success': True, 'calc_type': 'parallel',
            'result': round(result, 6), 'result_unit': res_u,
            'result_unit_symbol': self._u(res_u),
            'result_label': str(_('Total Resistance')),
            'total_resistance_ohms': round(total, 6),
            'formula': '1/R_total = 1/R1 + 1/R2 + …',
            'step_by_step': steps,
            'chart_data': {'resistor_chart': chart},
        })

    # ── POWER: P = V² / R ────────────────────────────────────────────
    def _calc_power(self, d):
        V = self._safe(d.get('voltage'), str(_('Voltage')))
        R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
        ru = d.get('resistance_unit', 'ohms')

        R_ohms = self._to_ohms(R, ru, str(_('Resistance')))
        P = self._verify(float(np.divide(np.multiply(V, V), R_ohms)))
        I = self._verify(float(np.divide(V, R_ohms)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Voltage")} (V) = {V} V',
            f'  • {_("Resistance")} (R) = {R} {self._u(ru)}',
            '',
            str(_('Step 2: Convert resistance to ohms')),
            f'  R = {self._fnum(R_ohms)} Ω',
            '',
            str(_('Step 3: Calculate current')),
            f'  {_("Formula")}: I = V / R',
            f'  I = {V} / {self._fnum(R_ohms)}',
            f'  I = {self._fnum(I)} A',
            '',
            str(_('Step 4: Calculate power')),
            f'  {_("Formula")}: P = V² / R',
            f'  P = ({V})² / {self._fnum(R_ohms)}',
            f'  P = {self._fnum(P)} W',
            '',
            str(_('Step 5: Result')),
            f'  {_("Power")} = {self._fnum(P)} W',
            f'  {_("Current")} = {self._fnum(I)} A',
        ]

        chart = self._bar_chart(
            [str(_('Voltage (V)')), str(_('Resistance (Ω)')), str(_('Current (A)')), str(_('Power (W)'))],
            [V, R_ohms, I, P],
            ['rgba(251,191,36,0.8)', 'rgba(16,185,129,0.8)', 'rgba(59,130,246,0.8)', 'rgba(239,68,68,0.8)'],
            str(_('Power Dissipation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'power',
            'result': round(P, 6),
            'result_unit': 'watts',
            'result_unit_symbol': 'W',
            'result_label': str(_('Power')),
            'current': round(I, 6),
            'voltage': V,
            'resistance': R,
            'resistance_unit': ru,
            'formula': 'P = V² / R',
            'step_by_step': steps,
            'chart_data': {'resistor_chart': chart},
        })

    # ── chart helper ─────────────────────────────────────────────────
    def _bar_chart(self, labels, data, colors, title):
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.8', '1') for c in colors],
                    'borderWidth': 2,
                    'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': title},
                },
                'scales': {
                    'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Value'))}},
                },
            },
        }
