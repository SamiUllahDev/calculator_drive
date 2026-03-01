from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MassCalculator(View):
    """
    Mass Calculator — Convert, Calculate Mass / Density / Volume.

    Calc types:
        • convert           → mass unit conversion
        • mass_from_density  → m = ρ × V
        • density_from_mass  → ρ = m / V
        • volume_from_mass   → V = m / ρ

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/mass_calculator.html'

    # ── unit conversion factors ──────────────────────────────────────
    MASS_UNITS = {
        'kilograms':   {'to_kg': 1.0,        'sym': 'kg',         'label': _('Kilograms (kg)')},
        'grams':       {'to_kg': 0.001,      'sym': 'g',          'label': _('Grams (g)')},
        'milligrams':  {'to_kg': 1e-6,       'sym': 'mg',         'label': _('Milligrams (mg)')},
        'pounds':      {'to_kg': 0.453592,   'sym': 'lb',         'label': _('Pounds (lb)')},
        'ounces':      {'to_kg': 0.0283495,  'sym': 'oz',         'label': _('Ounces (oz)')},
        'tons':        {'to_kg': 1000.0,     'sym': 't',          'label': _('Metric Tons (t)')},
        'stone':       {'to_kg': 6.35029,    'sym': 'st',         'label': _('Stone (st)')},
        'us_tons':     {'to_kg': 907.185,    'sym': 'US ton',     'label': _('US Tons')},
    }

    VOL_UNITS = {
        'cubic_meters':      {'to_m3': 1.0,           'sym': 'm³',   'label': _('Cubic Meters (m³)')},
        'liters':            {'to_m3': 0.001,         'sym': 'L',    'label': _('Liters (L)')},
        'milliliters':       {'to_m3': 1e-6,          'sym': 'mL',   'label': _('Milliliters (mL)')},
        'cubic_centimeters': {'to_m3': 1e-6,          'sym': 'cm³',  'label': _('Cubic Centimeters (cm³)')},
        'cubic_feet':        {'to_m3': 0.0283168,     'sym': 'ft³',  'label': _('Cubic Feet (ft³)')},
        'cubic_inches':      {'to_m3': 1.6387e-5,     'sym': 'in³',  'label': _('Cubic Inches (in³)')},
        'gallons_us':        {'to_m3': 0.00378541,    'sym': 'gal (US)', 'label': _('US Gallons')},
    }

    DENS_UNITS = {
        'kg_per_m3':   {'to_base': 1.0,        'sym': 'kg/m³',  'label': _('kg/m³')},
        'g_per_cm3':   {'to_base': 1000.0,     'sym': 'g/cm³',  'label': _('g/cm³')},
        'g_per_ml':    {'to_base': 1000.0,     'sym': 'g/mL',   'label': _('g/mL')},
        'lb_per_ft3':  {'to_base': 16.018463,  'sym': 'lb/ft³', 'label': _('lb/ft³')},
        'lb_per_in3':  {'to_base': 27679.9,    'sym': 'lb/in³', 'label': _('lb/in³')},
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Mass Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'convert')
            dispatch = {
                'convert':           self._calc_convert,
                'mass_from_density': self._calc_mass_from_density,
                'density_from_mass': self._calc_density_from_mass,
                'volume_from_mass':  self._calc_volume_from_mass,
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

    def _safe_nn(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        return v

    def _verify(self, val):
        if not np.isfinite(val):
            raise ValueError(str(_('Calculation produced an invalid result.')))
        return val

    def _ms(self, k):
        return self.MASS_UNITS.get(k, self.MASS_UNITS['kilograms'])['sym']

    def _vs(self, k):
        return self.VOL_UNITS.get(k, self.VOL_UNITS['cubic_meters'])['sym']

    def _ds(self, k):
        return self.DENS_UNITS.get(k, self.DENS_UNITS['kg_per_m3'])['sym']

    def _to_kg(self, val, u):
        return float(np.multiply(val, self.MASS_UNITS.get(u, self.MASS_UNITS['kilograms'])['to_kg']))

    def _from_kg(self, kg, u):
        return float(np.divide(kg, self.MASS_UNITS.get(u, self.MASS_UNITS['kilograms'])['to_kg']))

    def _to_m3(self, val, u):
        return float(np.multiply(val, self.VOL_UNITS.get(u, self.VOL_UNITS['cubic_meters'])['to_m3']))

    def _from_m3(self, m3, u):
        return float(np.divide(m3, self.VOL_UNITS.get(u, self.VOL_UNITS['cubic_meters'])['to_m3']))

    def _to_base_d(self, val, u):
        return float(np.multiply(val, self.DENS_UNITS.get(u, self.DENS_UNITS['kg_per_m3'])['to_base']))

    def _from_base_d(self, base, u):
        return float(np.divide(base, self.DENS_UNITS.get(u, self.DENS_UNITS['kg_per_m3'])['to_base']))

    # ── 1) CONVERT MASS UNITS ────────────────────────────────────────
    def _calc_convert(self, d):
        value = self._safe_nn(d.get('value'), str(_('Mass value')))
        fu = d.get('from_unit', 'kilograms')
        tu = d.get('to_unit', 'pounds')

        kg = self._to_kg(value, fu)
        result = self._verify(self._from_kg(kg, tu))

        steps = [
            str(_('Step 1: Identify the given value')),
            f'  • {value} {self._ms(fu)}',
        ]
        if fu != 'kilograms':
            steps += [
                '', str(_('Step 2: Convert to kilograms (base unit)')),
                f'  {value} × {self.MASS_UNITS[fu]["to_kg"]} = {self._fnum(kg)} kg',
            ]
        if tu != 'kilograms':
            steps += [
                '', str(_('Step 3: Convert to {unit}').format(unit=self._ms(tu))),
                f'  {self._fnum(kg)} / {self.MASS_UNITS[tu]["to_kg"]} = {self._fnum(result)} {self._ms(tu)}',
            ]
        steps += [
            '', str(_('Result')),
            f'  {value} {self._ms(fu)} = {self._fnum(result)} {self._ms(tu)}',
        ]

        chart = self._bar_chart(
            [self._ms(fu), 'kg', self._ms(tu)],
            [value, kg, result],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Mass Conversion'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': round(result, 6),
            'result_label': str(_('Converted Mass')),
            'result_unit_symbol': self._ms(tu),
            'formula': f'{value} {self._ms(fu)} = {self._fnum(result)} {self._ms(tu)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 2) MASS FROM DENSITY & VOLUME ────────────────────────────────
    def _calc_mass_from_density(self, d):
        density = self._safe_pos(d.get('density'), str(_('Density')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        du = d.get('density_unit', 'kg_per_m3')
        vu = d.get('volume_unit', 'cubic_meters')
        ru = d.get('result_unit', 'kilograms')

        dens_base = self._to_base_d(density, du)
        vol_m3 = self._to_m3(volume, vu)
        mass_kg = self._verify(float(np.multiply(dens_base, vol_m3)))
        result = self._from_kg(mass_kg, ru) if ru != 'kilograms' else mass_kg

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Density")} = {density} {self._ds(du)}',
            f'  • {_("Volume")} = {volume} {self._vs(vu)}',
        ]
        if du != 'kg_per_m3' or vu != 'cubic_meters':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if du != 'kg_per_m3':
                steps.append(f'  {_("Density")} = {self._fnum(dens_base)} kg/m³')
            if vu != 'cubic_meters':
                steps.append(f'  {_("Volume")} = {self._fnum(vol_m3)} m³')
        steps += [
            '', str(_('Step 3: Apply the mass formula')),
            f'  {_("Formula")}: m = ρ × V',
            f'  m = {self._fnum(dens_base)} × {self._fnum(vol_m3)}',
            f'  m = {self._fnum(mass_kg)} kg',
        ]
        if ru != 'kilograms':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._ms(ru))),
                f'  m = {self._fnum(result)} {self._ms(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Density (kg/m³)')), str(_('Volume (m³)')), str(_('Mass (kg)'))],
            [dens_base, vol_m3, mass_kg],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Mass from Density'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'mass_from_density',
            'result': round(result, 6),
            'result_label': str(_('Mass')),
            'result_unit_symbol': self._ms(ru),
            'formula': f'm = {self._fnum(dens_base)} × {self._fnum(vol_m3)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 3) DENSITY FROM MASS & VOLUME ────────────────────────────────
    def _calc_density_from_mass(self, d):
        mass = self._safe_pos(d.get('mass'), str(_('Mass')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        mu = d.get('mass_unit', 'kilograms')
        vu = d.get('volume_unit', 'cubic_meters')
        ru = d.get('result_unit', 'kg_per_m3')

        mass_kg = self._to_kg(mass, mu)
        vol_m3 = self._to_m3(volume, vu)
        dens_base = self._verify(float(np.divide(mass_kg, vol_m3)))
        result = self._from_base_d(dens_base, ru) if ru != 'kg_per_m3' else dens_base

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Mass")} = {mass} {self._ms(mu)}',
            f'  • {_("Volume")} = {volume} {self._vs(vu)}',
        ]
        if mu != 'kilograms' or vu != 'cubic_meters':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if mu != 'kilograms':
                steps.append(f'  {_("Mass")} = {self._fnum(mass_kg)} kg')
            if vu != 'cubic_meters':
                steps.append(f'  {_("Volume")} = {self._fnum(vol_m3)} m³')
        steps += [
            '', str(_('Step 3: Apply the density formula')),
            f'  {_("Formula")}: ρ = m / V',
            f'  ρ = {self._fnum(mass_kg)} / {self._fnum(vol_m3)}',
            f'  ρ = {self._fnum(dens_base)} kg/m³',
        ]
        if ru != 'kg_per_m3':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._ds(ru))),
                f'  ρ = {self._fnum(result)} {self._ds(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Mass (kg)')), str(_('Volume (m³)')), str(_('Density (kg/m³)'))],
            [mass_kg, vol_m3, dens_base],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Density from Mass'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'density_from_mass',
            'result': round(result, 6),
            'result_label': str(_('Density')),
            'result_unit_symbol': self._ds(ru),
            'formula': f'ρ = {self._fnum(mass_kg)} / {self._fnum(vol_m3)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 4) VOLUME FROM MASS & DENSITY ────────────────────────────────
    def _calc_volume_from_mass(self, d):
        mass = self._safe_pos(d.get('mass'), str(_('Mass')))
        density = self._safe_pos(d.get('density'), str(_('Density')))
        mu = d.get('mass_unit', 'kilograms')
        du = d.get('density_unit', 'kg_per_m3')
        ru = d.get('result_unit', 'cubic_meters')

        mass_kg = self._to_kg(mass, mu)
        dens_base = self._to_base_d(density, du)
        vol_m3 = self._verify(float(np.divide(mass_kg, dens_base)))
        result = self._from_m3(vol_m3, ru) if ru != 'cubic_meters' else vol_m3

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Mass")} = {mass} {self._ms(mu)}',
            f'  • {_("Density")} = {density} {self._ds(du)}',
        ]
        if mu != 'kilograms' or du != 'kg_per_m3':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if mu != 'kilograms':
                steps.append(f'  {_("Mass")} = {self._fnum(mass_kg)} kg')
            if du != 'kg_per_m3':
                steps.append(f'  {_("Density")} = {self._fnum(dens_base)} kg/m³')
        steps += [
            '', str(_('Step 3: Apply the volume formula')),
            f'  {_("Formula")}: V = m / ρ',
            f'  V = {self._fnum(mass_kg)} / {self._fnum(dens_base)}',
            f'  V = {self._fnum(vol_m3)} m³',
        ]
        if ru != 'cubic_meters':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._vs(ru))),
                f'  V = {self._fnum(result)} {self._vs(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Mass (kg)')), str(_('Density (kg/m³)')), str(_('Volume (m³)'))],
            [mass_kg, dens_base, vol_m3],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Volume from Mass'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'volume_from_mass',
            'result': round(result, 6),
            'result_label': str(_('Volume')),
            'result_unit_symbol': self._vs(ru),
            'formula': f'V = {self._fnum(mass_kg)} / {self._fnum(dens_base)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
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
