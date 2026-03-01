from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DensityCalculator(View):
    """
    Density Calculator — Density, Mass & Volume.

    Calc types:
        • density  → ρ = m / V
        • mass     → m = ρ × V
        • volume   → V = m / ρ
        • convert  → density unit conversion

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/density_calculator.html'

    # ── unit conversion factors ──────────────────────────────────────
    MASS_UNITS = {
        'kg':  {'to_kg': 1.0,        'sym': 'kg',  'label': _('Kilograms (kg)')},
        'g':   {'to_kg': 0.001,      'sym': 'g',   'label': _('Grams (g)')},
        'mg':  {'to_kg': 1e-6,       'sym': 'mg',  'label': _('Milligrams (mg)')},
        'lb':  {'to_kg': 0.453592,   'sym': 'lb',  'label': _('Pounds (lb)')},
        'oz':  {'to_kg': 0.0283495,  'sym': 'oz',  'label': _('Ounces (oz)')},
        'ton': {'to_kg': 1000.0,     'sym': 't',   'label': _('Metric Tons (t)')},
    }

    VOL_UNITS = {
        'm3':    {'to_m3': 1.0,           'sym': 'm³',   'label': _('Cubic Meters (m³)')},
        'cm3':   {'to_m3': 1e-6,          'sym': 'cm³',  'label': _('Cubic Centimeters (cm³)')},
        'liter': {'to_m3': 0.001,         'sym': 'L',    'label': _('Liters (L)')},
        'ml':    {'to_m3': 1e-6,          'sym': 'mL',   'label': _('Milliliters (mL)')},
        'ft3':   {'to_m3': 0.0283168,     'sym': 'ft³',  'label': _('Cubic Feet (ft³)')},
        'in3':   {'to_m3': 1.6387e-5,     'sym': 'in³',  'label': _('Cubic Inches (in³)')},
    }

    DENS_UNITS = {
        'kg_per_m3':  {'to_base': 1.0,        'sym': 'kg/m³',  'label': _('kg/m³')},
        'g_per_cm3':  {'to_base': 1000.0,     'sym': 'g/cm³',  'label': _('g/cm³')},
        'g_per_liter': {'to_base': 1.0,       'sym': 'g/L',    'label': _('g/L')},
        'lb_per_ft3': {'to_base': 16.018463,  'sym': 'lb/ft³', 'label': _('lb/ft³')},
        'lb_per_in3': {'to_base': 27679.9,    'sym': 'lb/in³', 'label': _('lb/in³')},
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Density Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'density')
            dispatch = {
                'density': self._calc_density,
                'mass':    self._calc_mass,
                'volume':  self._calc_volume,
                'convert': self._calc_convert,
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
        if abs(v) < 1e-9 or abs(v) >= 1e9:
            return f'{v:.6g}'
        return f'{v:,.{dp}g}'

    def _safe_pos(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        if v > 1e15:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _verify(self, val):
        if not np.isfinite(val):
            raise ValueError(str(_('Calculation produced an invalid result.')))
        return val

    def _m_sym(self, k):
        return self.MASS_UNITS.get(k, self.MASS_UNITS['kg'])['sym']

    def _v_sym(self, k):
        return self.VOL_UNITS.get(k, self.VOL_UNITS['m3'])['sym']

    def _d_sym(self, k):
        return self.DENS_UNITS.get(k, self.DENS_UNITS['kg_per_m3'])['sym']

    def _to_kg(self, val, unit):
        return float(np.multiply(val, self.MASS_UNITS.get(unit, self.MASS_UNITS['kg'])['to_kg']))

    def _from_kg(self, kg, unit):
        return float(np.divide(kg, self.MASS_UNITS.get(unit, self.MASS_UNITS['kg'])['to_kg']))

    def _to_m3(self, val, unit):
        return float(np.multiply(val, self.VOL_UNITS.get(unit, self.VOL_UNITS['m3'])['to_m3']))

    def _from_m3(self, m3, unit):
        return float(np.divide(m3, self.VOL_UNITS.get(unit, self.VOL_UNITS['m3'])['to_m3']))

    def _to_base_d(self, val, unit):
        return float(np.multiply(val, self.DENS_UNITS.get(unit, self.DENS_UNITS['kg_per_m3'])['to_base']))

    def _from_base_d(self, base, unit):
        return float(np.divide(base, self.DENS_UNITS.get(unit, self.DENS_UNITS['kg_per_m3'])['to_base']))

    # ── 1) CALCULATE DENSITY ─────────────────────────────────────────
    def _calc_density(self, d):
        mass = self._safe_pos(d.get('mass'), str(_('Mass')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        mu = d.get('mass_unit', 'kg')
        vu = d.get('volume_unit', 'm3')
        ru = d.get('result_unit', 'kg_per_m3')

        mass_kg = self._to_kg(mass, mu)
        vol_m3 = self._to_m3(volume, vu)
        dens_base = self._verify(float(np.divide(mass_kg, vol_m3)))
        result = self._from_base_d(dens_base, ru)

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Mass")} = {mass} {self._m_sym(mu)}',
            f'  • {_("Volume")} = {volume} {self._v_sym(vu)}',
        ]
        if mu != 'kg' or vu != 'm3':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if mu != 'kg':
                steps.append(f'  {_("Mass")} = {self._fnum(mass_kg)} kg')
            if vu != 'm3':
                steps.append(f'  {_("Volume")} = {self._fnum(vol_m3)} m³')
        steps += [
            '', str(_('Step 3: Apply the density formula')),
            f'  {_("Formula")}: ρ = m / V',
            f'  ρ = {self._fnum(mass_kg)} / {self._fnum(vol_m3)}',
            f'  ρ = {self._fnum(dens_base)} kg/m³',
        ]
        if ru != 'kg_per_m3':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._d_sym(ru))),
                f'  ρ = {self._fnum(result)} {self._d_sym(ru)}',
            ]

        chart = self._comparison_chart(dens_base)

        return JsonResponse({
            'success': True, 'calc_type': 'density',
            'result': round(result, 6),
            'result_label': str(_('Density')),
            'result_unit_symbol': self._d_sym(ru),
            'formula': f'ρ = {self._fnum(mass_kg)} / {self._fnum(vol_m3)}',
            'mass_kg': round(mass_kg, 6),
            'volume_m3': round(vol_m3, 6),
            'density_base': round(dens_base, 6),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 2) CALCULATE MASS ────────────────────────────────────────────
    def _calc_mass(self, d):
        density = self._safe_pos(d.get('density'), str(_('Density')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        du = d.get('density_unit', 'kg_per_m3')
        vu = d.get('volume_unit', 'm3')
        ru = d.get('result_unit', 'kg')

        dens_base = self._to_base_d(density, du)
        vol_m3 = self._to_m3(volume, vu)
        mass_kg = self._verify(float(np.multiply(dens_base, vol_m3)))
        result = self._from_kg(mass_kg, ru) if ru != 'kg' else mass_kg

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Density")} = {density} {self._d_sym(du)}',
            f'  • {_("Volume")} = {volume} {self._v_sym(vu)}',
        ]
        if du != 'kg_per_m3' or vu != 'm3':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if du != 'kg_per_m3':
                steps.append(f'  {_("Density")} = {self._fnum(dens_base)} kg/m³')
            if vu != 'm3':
                steps.append(f'  {_("Volume")} = {self._fnum(vol_m3)} m³')
        steps += [
            '', str(_('Step 3: Apply the mass formula')),
            f'  {_("Formula")}: m = ρ × V',
            f'  m = {self._fnum(dens_base)} × {self._fnum(vol_m3)}',
            f'  m = {self._fnum(mass_kg)} kg',
        ]
        if ru != 'kg':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._m_sym(ru))),
                f'  m = {self._fnum(result)} {self._m_sym(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Density (kg/m³)')), str(_('Volume (m³)')), str(_('Mass (kg)'))],
            [dens_base, vol_m3, mass_kg],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Mass Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'mass',
            'result': round(result, 6),
            'result_label': str(_('Mass')),
            'result_unit_symbol': self._m_sym(ru),
            'formula': f'm = {self._fnum(dens_base)} × {self._fnum(vol_m3)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 3) CALCULATE VOLUME ──────────────────────────────────────────
    def _calc_volume(self, d):
        density = self._safe_pos(d.get('density'), str(_('Density')))
        mass = self._safe_pos(d.get('mass'), str(_('Mass')))
        du = d.get('density_unit', 'kg_per_m3')
        mu = d.get('mass_unit', 'kg')
        ru = d.get('result_unit', 'm3')

        dens_base = self._to_base_d(density, du)
        mass_kg = self._to_kg(mass, mu)
        vol_m3 = self._verify(float(np.divide(mass_kg, dens_base)))
        result = self._from_m3(vol_m3, ru) if ru != 'm3' else vol_m3

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Density")} = {density} {self._d_sym(du)}',
            f'  • {_("Mass")} = {mass} {self._m_sym(mu)}',
        ]
        if du != 'kg_per_m3' or mu != 'kg':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if du != 'kg_per_m3':
                steps.append(f'  {_("Density")} = {self._fnum(dens_base)} kg/m³')
            if mu != 'kg':
                steps.append(f'  {_("Mass")} = {self._fnum(mass_kg)} kg')
        steps += [
            '', str(_('Step 3: Apply the volume formula')),
            f'  {_("Formula")}: V = m / ρ',
            f'  V = {self._fnum(mass_kg)} / {self._fnum(dens_base)}',
            f'  V = {self._fnum(vol_m3)} m³',
        ]
        if ru != 'm3':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._v_sym(ru))),
                f'  V = {self._fnum(result)} {self._v_sym(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Mass (kg)')), str(_('Density (kg/m³)')), str(_('Volume (m³)'))],
            [mass_kg, dens_base, vol_m3],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Volume Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'volume',
            'result': round(result, 6),
            'result_label': str(_('Volume')),
            'result_unit_symbol': self._v_sym(ru),
            'formula': f'V = {self._fnum(mass_kg)} / {self._fnum(dens_base)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 4) CONVERT DENSITY UNITS ─────────────────────────────────────
    def _calc_convert(self, d):
        value = self._safe_pos(d.get('value'), str(_('Value')))
        fu = d.get('from_unit', 'kg_per_m3')
        tu = d.get('to_unit', 'g_per_cm3')

        base = self._to_base_d(value, fu)
        result = self._verify(self._from_base_d(base, tu))

        steps = [
            str(_('Step 1: Identify the given value')),
            f'  • {value} {self._d_sym(fu)}',
            '', str(_('Step 2: Convert to base unit (kg/m³)')),
            f'  {value} × {self.DENS_UNITS[fu]["to_base"]} = {self._fnum(base)} kg/m³',
            '', str(_('Step 3: Convert to target unit ({unit})').format(unit=self._d_sym(tu))),
            f'  {self._fnum(base)} / {self.DENS_UNITS[tu]["to_base"]} = {self._fnum(result)} {self._d_sym(tu)}',
        ]

        chart = self._bar_chart(
            [self._d_sym(fu), 'kg/m³', self._d_sym(tu)],
            [value, base, result],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Unit Conversion'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': round(result, 6),
            'result_label': str(_('Converted Density')),
            'result_unit_symbol': self._d_sym(tu),
            'formula': f'{value} {self._d_sym(fu)} = {self._fnum(result)} {self._d_sym(tu)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── chart helpers ────────────────────────────────────────────────
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

    def _comparison_chart(self, density_kg_m3):
        """Bar chart comparing calculated density with common materials."""
        labels = [
            str(_('Air')), str(_('Water')), str(_('Aluminum')),
            str(_('Iron')), str(_('Gold')), str(_('Your Result'))
        ]
        data = [1.225, 1000, 2700, 7870, 19300, density_kg_m3]
        colors = [
            'rgba(156,163,175,0.8)', 'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)',
            'rgba(251,191,36,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)',
        ]
        return self._bar_chart(labels, data, colors, str(_('Density Comparison (kg/m³)')))
