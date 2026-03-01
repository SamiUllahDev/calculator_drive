from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OhmsLawCalculator(View):
    """
    Ohm's Law Calculator — Voltage, Current, Resistance & Power.

    Formulas:
        V = I × R   |   I = V / R   |   R = V / I
        P = V × I   |   P = I² × R  |   P = V² / R

    Uses NumPy for vectorised arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/ohms_law_calculator.html'

    # ── unit conversion tables (to base SI) ──────────────────────────
    V_CONV = {'volts': 1.0, 'millivolts': 1e-3, 'kilovolts': 1e3}
    I_CONV = {'amperes': 1.0, 'milliamperes': 1e-3, 'microamperes': 1e-6}
    R_CONV = {'ohms': 1.0, 'milliohms': 1e-3, 'kiloohms': 1e3, 'megaohms': 1e6}
    P_CONV = {'watts': 1.0, 'milliwatts': 1e-3, 'kilowatts': 1e3, 'megawatts': 1e6}

    UNIT_SYM = {
        'volts': 'V', 'millivolts': 'mV', 'kilovolts': 'kV',
        'amperes': 'A', 'milliamperes': 'mA', 'microamperes': 'µA',
        'ohms': 'Ω', 'milliohms': 'mΩ', 'kiloohms': 'kΩ', 'megaohms': 'MΩ',
        'watts': 'W', 'milliwatts': 'mW', 'kilowatts': 'kW', 'megawatts': 'MW',
    }

    def _u(self, key):
        return self.UNIT_SYM.get(key, key)

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _("Ohm's Law Calculator"),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'voltage')
            dispatch = {
                'voltage': self._calc_voltage,
                'current': self._calc_current,
                'resistance': self._calc_resistance,
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
        if abs(v) < 1e-6 or abs(v) >= 1e6:
            return f'{v:.6g}'
        return f'{v:,.{dp}g}'

    def _safe(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        if v > 1e12:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _safe_pos(self, v, name):
        v = self._safe(v, name)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        return v

    def _to_base(self, v, unit, table, name):
        if unit not in table:
            raise ValueError(str(_('{name}: invalid unit "{unit}".').format(name=name, unit=unit)))
        return float(np.float64(v) * table[unit])

    def _from_base(self, base_val, unit, table):
        return float(np.float64(base_val) / table[unit])

    def _verify(self, val):
        if not np.isfinite(val):
            raise ValueError(str(_('Calculation produced an invalid result.')))
        return val

    # ── VOLTAGE: V = I × R ───────────────────────────────────────────
    def _calc_voltage(self, d):
        I = self._safe(d.get('current'), str(_('Current')))
        iu = d.get('current_unit', 'amperes')
        R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
        ru = d.get('resistance_unit', 'ohms')
        res_u = d.get('result_unit', 'volts')
        if res_u not in self.V_CONV:
            return self._err(_('Invalid result unit.'))

        Ib = self._to_base(I, iu, self.I_CONV, str(_('Current')))
        Rb = self._to_base(R, ru, self.R_CONV, str(_('Resistance')))
        Vb = self._verify(float(np.multiply(Ib, Rb)))
        result = self._from_base(Vb, res_u, self.V_CONV)

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Current")} (I) = {I} {self._u(iu)}',
            f'  • {_("Resistance")} (R) = {R} {self._u(ru)}',
            '',
            str(_('Step 2: Convert to base units')),
            f'  I = {self._fnum(Ib)} A',
            f'  R = {self._fnum(Rb)} Ω',
            '',
            str(_("Step 3: Apply Ohm's Law")),
            f'  {_("Formula")}: V = I × R',
            f'  V = {self._fnum(Ib)} × {self._fnum(Rb)}',
            f'  V = {self._fnum(Vb)} V',
            '',
            str(_('Step 4: Result')),
            f'  {_("Voltage")} = {self._fnum(result)} {self._u(res_u)}',
        ]

        chart = self._bar_chart(
            [str(_('Current (A)')), str(_('Resistance (Ω)')), str(_('Voltage (V)'))],
            [Ib, Rb, Vb],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_("Ohm's Law: Voltage Calculation"))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'voltage',
            'result': round(result, 6), 'result_unit': res_u,
            'result_unit_symbol': self._u(res_u),
            'result_label': str(_('Voltage')),
            'formula': 'V = I × R',
            'step_by_step': steps,
            'chart_data': {'ohm_chart': chart},
        })

    # ── CURRENT: I = V / R ───────────────────────────────────────────
    def _calc_current(self, d):
        V = self._safe(d.get('voltage'), str(_('Voltage')))
        vu = d.get('voltage_unit', 'volts')
        R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
        ru = d.get('resistance_unit', 'ohms')
        res_u = d.get('result_unit', 'amperes')
        if res_u not in self.I_CONV:
            return self._err(_('Invalid result unit.'))

        Vb = self._to_base(V, vu, self.V_CONV, str(_('Voltage')))
        Rb = self._to_base(R, ru, self.R_CONV, str(_('Resistance')))
        Ib = self._verify(float(np.divide(Vb, Rb)))
        result = self._from_base(Ib, res_u, self.I_CONV)

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
            f'  • {_("Resistance")} (R) = {R} {self._u(ru)}',
            '',
            str(_('Step 2: Convert to base units')),
            f'  V = {self._fnum(Vb)} V',
            f'  R = {self._fnum(Rb)} Ω',
            '',
            str(_("Step 3: Apply Ohm's Law")),
            f'  {_("Formula")}: I = V / R',
            f'  I = {self._fnum(Vb)} / {self._fnum(Rb)}',
            f'  I = {self._fnum(Ib)} A',
            '',
            str(_('Step 4: Result')),
            f'  {_("Current")} = {self._fnum(result)} {self._u(res_u)}',
        ]

        chart = self._bar_chart(
            [str(_('Voltage (V)')), str(_('Resistance (Ω)')), str(_('Current (A)'))],
            [Vb, Rb, Ib],
            ['rgba(251,191,36,0.8)', 'rgba(16,185,129,0.8)', 'rgba(59,130,246,0.8)'],
            str(_("Ohm's Law: Current Calculation"))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'current',
            'result': round(result, 6), 'result_unit': res_u,
            'result_unit_symbol': self._u(res_u),
            'result_label': str(_('Current')),
            'formula': 'I = V / R',
            'step_by_step': steps,
            'chart_data': {'ohm_chart': chart},
        })

    # ── RESISTANCE: R = V / I ────────────────────────────────────────
    def _calc_resistance(self, d):
        V = self._safe(d.get('voltage'), str(_('Voltage')))
        vu = d.get('voltage_unit', 'volts')
        I = self._safe_pos(d.get('current'), str(_('Current')))
        iu = d.get('current_unit', 'amperes')
        res_u = d.get('result_unit', 'ohms')
        if res_u not in self.R_CONV:
            return self._err(_('Invalid result unit.'))

        Vb = self._to_base(V, vu, self.V_CONV, str(_('Voltage')))
        Ib = self._to_base(I, iu, self.I_CONV, str(_('Current')))
        Rb = self._verify(float(np.divide(Vb, Ib)))
        result = self._from_base(Rb, res_u, self.R_CONV)

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
            f'  • {_("Current")} (I) = {I} {self._u(iu)}',
            '',
            str(_('Step 2: Convert to base units')),
            f'  V = {self._fnum(Vb)} V',
            f'  I = {self._fnum(Ib)} A',
            '',
            str(_("Step 3: Apply Ohm's Law")),
            f'  {_("Formula")}: R = V / I',
            f'  R = {self._fnum(Vb)} / {self._fnum(Ib)}',
            f'  R = {self._fnum(Rb)} Ω',
            '',
            str(_('Step 4: Result')),
            f'  {_("Resistance")} = {self._fnum(result)} {self._u(res_u)}',
        ]

        chart = self._bar_chart(
            [str(_('Voltage (V)')), str(_('Current (A)')), str(_('Resistance (Ω)'))],
            [Vb, Ib, Rb],
            ['rgba(251,191,36,0.8)', 'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)'],
            str(_("Ohm's Law: Resistance Calculation"))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'resistance',
            'result': round(result, 6), 'result_unit': res_u,
            'result_unit_symbol': self._u(res_u),
            'result_label': str(_('Resistance')),
            'formula': 'R = V / I',
            'step_by_step': steps,
            'chart_data': {'ohm_chart': chart},
        })

    # ── POWER ────────────────────────────────────────────────────────
    def _calc_power(self, d):
        mode = d.get('power_mode', 'from_voltage_current')
        res_u = d.get('result_unit', 'watts')
        if res_u not in self.P_CONV:
            return self._err(_('Invalid result unit.'))

        if mode == 'from_voltage_current':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'volts')
            I = self._safe(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'amperes')
            Vb = self._to_base(V, vu, self.V_CONV, str(_('Voltage')))
            Ib = self._to_base(I, iu, self.I_CONV, str(_('Current')))
            Pw = self._verify(float(np.multiply(Vb, Ib)))
            formula = 'P = V × I'
            steps = [
                str(_('Step 1: Identify the given values')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                '',
                str(_('Step 2: Convert to base units')),
                f'  V = {self._fnum(Vb)} V',
                f'  I = {self._fnum(Ib)} A',
                '',
                str(_('Step 3: Apply power formula')),
                f'  {_("Formula")}: P = V × I',
                f'  P = {self._fnum(Vb)} × {self._fnum(Ib)}',
                f'  P = {self._fnum(Pw)} W',
            ]

        elif mode == 'from_current_resistance':
            I = self._safe(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'amperes')
            R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
            ru = d.get('resistance_unit', 'ohms')
            Ib = self._to_base(I, iu, self.I_CONV, str(_('Current')))
            Rb = self._to_base(R, ru, self.R_CONV, str(_('Resistance')))
            Pw = self._verify(float(np.multiply(np.multiply(Ib, Ib), Rb)))
            formula = 'P = I² × R'
            steps = [
                str(_('Step 1: Identify the given values')),
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(ru)}',
                '',
                str(_('Step 2: Convert to base units')),
                f'  I = {self._fnum(Ib)} A',
                f'  R = {self._fnum(Rb)} Ω',
                '',
                str(_('Step 3: Apply power formula')),
                f'  {_("Formula")}: P = I² × R',
                f'  P = ({self._fnum(Ib)})² × {self._fnum(Rb)}',
                f'  P = {self._fnum(Pw)} W',
            ]

        elif mode == 'from_voltage_resistance':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'volts')
            R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
            ru = d.get('resistance_unit', 'ohms')
            Vb = self._to_base(V, vu, self.V_CONV, str(_('Voltage')))
            Rb = self._to_base(R, ru, self.R_CONV, str(_('Resistance')))
            Pw = self._verify(float(np.divide(np.multiply(Vb, Vb), Rb)))
            formula = 'P = V² / R'
            steps = [
                str(_('Step 1: Identify the given values')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(ru)}',
                '',
                str(_('Step 2: Convert to base units')),
                f'  V = {self._fnum(Vb)} V',
                f'  R = {self._fnum(Rb)} Ω',
                '',
                str(_('Step 3: Apply power formula')),
                f'  {_("Formula")}: P = V² / R',
                f'  P = ({self._fnum(Vb)})² / {self._fnum(Rb)}',
                f'  P = {self._fnum(Pw)} W',
            ]
        else:
            return self._err(_('Invalid power mode.'))

        result = self._from_base(Pw, res_u, self.P_CONV)
        steps += [
            '',
            str(_('Step 4: Result')),
            f'  {_("Power")} = {self._fnum(result)} {self._u(res_u)}',
        ]

        chart = self._bar_chart(
            [str(_('Power (W)'))], [Pw],
            ['rgba(239,68,68,0.8)'],
            str(_('Power Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'power',
            'power_mode': mode,
            'result': round(result, 6), 'result_unit': res_u,
            'result_unit_symbol': self._u(res_u),
            'result_label': str(_('Power')),
            'formula': formula,
            'step_by_step': steps,
            'chart_data': {'ohm_chart': chart},
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
