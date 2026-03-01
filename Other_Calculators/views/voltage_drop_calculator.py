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
class VoltageDropCalculator(View):
    """
    Voltage Drop Calculator — voltage drop, wire size, max current, max length.

    Supports DC, single-phase AC, and three-phase AC circuits.
    Uses NumPy for vectorised arithmetic.
    """
    template_name = 'other_calculators/voltage_drop_calculator.html'

    # Wire resistivity (Ω-cmil/ft) at 75 °C
    WIRE_RESISTIVITY = {
        'copper': 12.9,
        'aluminum': 21.2,
    }

    # Standard AWG sizes → circular mils
    AWG_SIZES = {
        '14': 4107, '12': 6530, '10': 10380, '8': 16510,
        '6': 26240, '4': 41740, '3': 52620, '2': 66360,
        '1': 83690, '1/0': 105600, '2/0': 133100,
        '3/0': 167800, '4/0': 211600,
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Voltage Drop Calculator'),
            'page_title': _('Voltage Drop Calculator - Calculate Wire Voltage Loss Online Free'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'voltage_drop')
            dispatch = {
                'voltage_drop': self._calc_voltage_drop,
                'wire_size': self._calc_wire_size,
                'max_current': self._calc_max_current,
                'max_length': self._calc_max_length,
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

    def _fnum(self, v, dp=2):
        if v is None:
            return '0'
        return f'{v:,.{dp}f}'

    def _safe_pos(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        if v > 1e9:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _safe(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        return v

    def _validate_material(self, m):
        if m not in self.WIRE_RESISTIVITY:
            raise ValueError(str(_('Invalid wire material.')))
        return m

    def _validate_awg(self, s):
        if s not in self.AWG_SIZES:
            raise ValueError(str(_('Invalid wire size.')))
        return s

    def _circuit_factor(self, ct, pf):
        """Return the multiplier for the circuit type."""
        if ct == 'dc':
            return 2.0
        elif ct == 'single_phase':
            return 2.0 * pf
        elif ct == 'three_phase':
            return 1.732 * pf
        else:
            return 2.0

    def _resistance(self, material, awg, length):
        rho = self.WIRE_RESISTIVITY[material]
        cmils = self.AWG_SIZES[awg]
        return float(np.divide(np.multiply(rho, length), cmils))

    # ── VOLTAGE DROP ──────────────────────────────────────────────────
    def _calc_voltage_drop(self, d):
        current = self._safe_pos(d.get('current'), str(_('Current')))
        voltage = self._safe_pos(d.get('voltage'), str(_('Voltage')))
        length = self._safe_pos(d.get('length'), str(_('Length')))
        awg = self._validate_awg(d.get('wire_size', '12'))
        mat = self._validate_material(d.get('wire_material', 'copper'))
        ct = d.get('circuit_type', 'single_phase')
        pf = float(d.get('power_factor', 1.0))

        R = self._resistance(mat, awg, length)
        factor = self._circuit_factor(ct, pf)
        vd = float(np.multiply(np.multiply(current, R), factor))
        vd_pct = float(np.divide(vd, voltage) * 100)
        v_load = float(np.subtract(voltage, vd))
        p_loss = float(np.multiply(current, vd))

        rho = self.WIRE_RESISTIVITY[mat]
        cmils = self.AWG_SIZES[awg]

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Current")}: {current} A',
            f'  • {_("Voltage")}: {voltage} V',
            f'  • {_("Wire Length")}: {length} ft',
            f'  • {_("Wire Size")}: {awg} AWG ({mat})',
            f'  • {_("Circuit Type")}: {ct}' + (f', PF = {pf}' if ct != 'dc' else ''),
            '',
            str(_('Step 2: Calculate wire resistance')),
            f'  R = (ρ × L) / A = ({rho} × {length}) / {cmils}',
            f'  R = {self._fnum(R, 4)} Ω',
            '',
            str(_('Step 3: Calculate voltage drop')),
            f'  VD = I × R × {self._fnum(factor, 3)}',
            f'  VD = {current} × {self._fnum(R, 4)} × {self._fnum(factor, 3)}',
            f'  VD = {self._fnum(vd)} V ({self._fnum(vd_pct)}%)',
            '',
            str(_('Step 4: Voltage at load')),
            f'  V_load = {voltage} − {self._fnum(vd)} = {self._fnum(v_load)} V',
            '',
            str(_('Step 5: Power loss')),
            f'  P_loss = {current} × {self._fnum(vd)} = {self._fnum(p_loss)} W',
        ]

        chart = {
            'voltage_drop_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Source Voltage')), str(_('Voltage Drop')), str(_('Voltage at Load'))],
                    'datasets': [{
                        'label': str(_('Voltage (V)')),
                        'data': [voltage, round(vd, 2), round(v_load, 2)],
                        'backgroundColor': ['rgba(59,130,246,0.8)', 'rgba(239,68,68,0.8)', 'rgba(16,185,129,0.8)'],
                        'borderColor': ['#3b82f6', '#ef4444', '#10b981'],
                        'borderWidth': 2, 'borderRadius': 8,
                    }]
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('Voltage Distribution'))}},
                    'scales': {'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Voltage (V)'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'voltage_drop',
            'voltage_drop': round(vd, 2),
            'voltage_drop_percent': round(vd_pct, 2),
            'voltage_at_load': round(v_load, 2),
            'power_loss': round(p_loss, 2),
            'resistance': round(R, 4),
            'step_by_step': steps,
            'chart_data': chart,
        })

    # ── WIRE SIZE ─────────────────────────────────────────────────────
    def _calc_wire_size(self, d):
        current = self._safe_pos(d.get('current'), str(_('Current')))
        voltage = self._safe_pos(d.get('voltage'), str(_('Voltage')))
        length = self._safe_pos(d.get('length'), str(_('Length')))
        max_vd = self._safe_pos(d.get('max_voltage_drop'), str(_('Max Voltage Drop')))
        vd_type = d.get('max_voltage_drop_type', 'volts')
        mat = self._validate_material(d.get('wire_material', 'copper'))
        ct = d.get('circuit_type', 'single_phase')
        pf = float(d.get('power_factor', 1.0))

        max_vd_v = (max_vd / 100) * voltage if vd_type == 'percent' else max_vd
        factor = self._circuit_factor(ct, pf)
        max_R = float(np.divide(max_vd_v, np.multiply(current, factor)))
        rho = self.WIRE_RESISTIVITY[mat]
        req_cmils = float(np.divide(np.multiply(rho, length), max_R))

        recommended = '4/0'
        for size, cmils in sorted(self.AWG_SIZES.items(), key=lambda x: x[1], reverse=True):
            if cmils >= req_cmils:
                recommended = size

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Current")}: {current} A',
            f'  • {_("Voltage")}: {voltage} V',
            f'  • {_("Wire Length")}: {length} ft',
            f'  • {_("Max Voltage Drop")}: {max_vd} {vd_type}',
            f'  • {_("Wire Material")}: {mat}',
            '',
            str(_('Step 2: Convert max voltage drop to volts')),
            f'  {_("Max VD")} = {self._fnum(max_vd_v)} V',
            '',
            str(_('Step 3: Calculate maximum resistance')),
            f'  R_max = VD_max / (I × factor)',
            f'  R_max = {self._fnum(max_vd_v)} / ({current} × {self._fnum(factor, 3)})',
            f'  R_max = {self._fnum(max_R, 4)} Ω',
            '',
            str(_('Step 4: Calculate required circular mils')),
            f'  CM = (ρ × L) / R_max = ({rho} × {length}) / {self._fnum(max_R, 4)}',
            f'  CM = {self._fnum(req_cmils, 0)} cmil',
            '',
            str(_('Step 5: Select wire size')),
            f'  {_("Recommended")}: {recommended} AWG',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'wire_size',
            'recommended_wire_size': recommended,
            'required_circular_mils': round(req_cmils),
            'step_by_step': steps,
        })

    # ── MAX CURRENT ───────────────────────────────────────────────────
    def _calc_max_current(self, d):
        vd = self._safe_pos(d.get('voltage_drop'), str(_('Voltage Drop')))
        voltage = self._safe_pos(d.get('voltage'), str(_('Voltage')))
        length = self._safe_pos(d.get('length'), str(_('Length')))
        awg = self._validate_awg(d.get('wire_size', '12'))
        mat = self._validate_material(d.get('wire_material', 'copper'))
        ct = d.get('circuit_type', 'single_phase')
        pf = float(d.get('power_factor', 1.0))

        R = self._resistance(mat, awg, length)
        factor = self._circuit_factor(ct, pf)
        max_I = float(np.divide(vd, np.multiply(R, factor)))
        vd_pct = float(np.divide(vd, voltage) * 100)

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Voltage Drop")}: {vd} V',
            f'  • {_("Voltage")}: {voltage} V',
            f'  • {_("Wire Length")}: {length} ft',
            f'  • {_("Wire Size")}: {awg} AWG ({mat})',
            '',
            str(_('Step 2: Calculate wire resistance')),
            f'  R = {self._fnum(R, 4)} Ω',
            '',
            str(_('Step 3: Calculate maximum current')),
            f'  I_max = VD / (R × factor)',
            f'  I_max = {vd} / ({self._fnum(R, 4)} × {self._fnum(factor, 3)})',
            f'  I_max = {self._fnum(max_I)} A',
            '',
            str(_('Step 4: Voltage drop percentage')),
            f'  VD% = ({vd} / {voltage}) × 100 = {self._fnum(vd_pct)}%',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'max_current',
            'max_current': round(max_I, 2),
            'voltage_drop': round(vd, 2),
            'voltage_drop_percent': round(vd_pct, 2),
            'step_by_step': steps,
        })

    # ── MAX LENGTH ────────────────────────────────────────────────────
    def _calc_max_length(self, d):
        vd = self._safe_pos(d.get('voltage_drop'), str(_('Voltage Drop')))
        voltage = self._safe_pos(d.get('voltage'), str(_('Voltage')))
        current = self._safe_pos(d.get('current'), str(_('Current')))
        awg = self._validate_awg(d.get('wire_size', '12'))
        mat = self._validate_material(d.get('wire_material', 'copper'))
        ct = d.get('circuit_type', 'single_phase')
        pf = float(d.get('power_factor', 1.0))

        rho = self.WIRE_RESISTIVITY[mat]
        cmils = self.AWG_SIZES[awg]
        factor = self._circuit_factor(ct, pf)
        max_L = float(np.divide(np.multiply(vd, cmils), np.multiply(np.multiply(current, rho), factor)))
        vd_pct = float(np.divide(vd, voltage) * 100)

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Voltage Drop")}: {vd} V',
            f'  • {_("Voltage")}: {voltage} V',
            f'  • {_("Current")}: {current} A',
            f'  • {_("Wire Size")}: {awg} AWG ({mat})',
            '',
            str(_('Step 2: Calculate maximum length')),
            f'  L_max = (VD × CM) / (I × ρ × factor)',
            f'  L_max = ({vd} × {cmils}) / ({current} × {rho} × {self._fnum(factor, 3)})',
            f'  L_max = {self._fnum(max_L)} ft',
            '',
            str(_('Step 3: Voltage drop percentage')),
            f'  VD% = ({vd} / {voltage}) × 100 = {self._fnum(vd_pct)}%',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'max_length',
            'max_length': round(max_L, 2),
            'voltage_drop': round(vd, 2),
            'voltage_drop_percent': round(vd_pct, 2),
            'step_by_step': steps,
        })
