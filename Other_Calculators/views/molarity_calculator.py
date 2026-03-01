from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MolarityCalculator(View):
    """
    Molarity Calculator — Concentration, Moles, Mass & Dilution.

    Calc types:
        • molarity_from_moles  → M = n / V
        • moles_from_molarity  → n = M × V
        • volume_from_molarity → V = n / M
        • molarity_from_mass   → M = (m / MW) / V
        • mass_from_molarity   → m = M × V × MW
        • dilution             → M1V1 = M2V2  (find V2 or M2)

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/molarity_calculator.html'

    # ── unit conversion factors ──────────────────────────────────────
    VOL_UNITS = {
        'liters':            {'to_L': 1.0,       'sym': 'L',   'label': _('Liters (L)')},
        'milliliters':       {'to_L': 0.001,     'sym': 'mL',  'label': _('Milliliters (mL)')},
        'microliters':       {'to_L': 1e-6,      'sym': 'µL',  'label': _('Microliters (µL)')},
        'cubic_centimeters': {'to_L': 0.001,     'sym': 'cm³', 'label': _('Cubic Centimeters (cm³)')},
        'cubic_meters':      {'to_L': 1000.0,    'sym': 'm³',  'label': _('Cubic Meters (m³)')},
    }

    MASS_UNITS = {
        'grams':      {'to_g': 1.0,      'sym': 'g',  'label': _('Grams (g)')},
        'milligrams': {'to_g': 0.001,    'sym': 'mg', 'label': _('Milligrams (mg)')},
        'micrograms': {'to_g': 1e-6,     'sym': 'µg', 'label': _('Micrograms (µg)')},
        'kilograms':  {'to_g': 1000.0,   'sym': 'kg', 'label': _('Kilograms (kg)')},
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Molarity Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'molarity_from_moles')
            dispatch = {
                'molarity_from_moles':  self._calc_molarity_from_moles,
                'moles_from_molarity':  self._calc_moles_from_molarity,
                'volume_from_molarity': self._calc_volume_from_molarity,
                'molarity_from_mass':   self._calc_molarity_from_mass,
                'mass_from_molarity':   self._calc_mass_from_molarity,
                'dilution':             self._calc_dilution,
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

    def _v_sym(self, key):
        return self.VOL_UNITS.get(key, self.VOL_UNITS['liters'])['sym']

    def _m_sym(self, key):
        return self.MASS_UNITS.get(key, self.MASS_UNITS['grams'])['sym']

    def _to_L(self, val, unit):
        return float(np.multiply(val, self.VOL_UNITS.get(unit, self.VOL_UNITS['liters'])['to_L']))

    def _from_L(self, liters, unit):
        factor = self.VOL_UNITS.get(unit, self.VOL_UNITS['liters'])['to_L']
        return float(np.divide(liters, factor))

    def _to_g(self, val, unit):
        return float(np.multiply(val, self.MASS_UNITS.get(unit, self.MASS_UNITS['grams'])['to_g']))

    def _from_g(self, grams, unit):
        factor = self.MASS_UNITS.get(unit, self.MASS_UNITS['grams'])['to_g']
        return float(np.divide(grams, factor))

    # ── 1) MOLARITY FROM MOLES & VOLUME ──────────────────────────────
    def _calc_molarity_from_moles(self, d):
        moles = self._safe_nn(d.get('moles'), str(_('Moles')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        vu = d.get('volume_unit', 'liters')

        v_L = self._to_L(volume, vu)
        molarity = self._verify(float(np.divide(moles, v_L)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Moles")} (n) = {moles} mol',
            f'  • {_("Volume")} = {volume} {self._v_sym(vu)}',
        ]
        if vu != 'liters':
            steps += [
                '', str(_('Step 2: Convert volume to liters')),
                f'  {_("Volume")} = {volume} × {self.VOL_UNITS[vu]["to_L"]} = {self._fnum(v_L)} L',
            ]
        steps += [
            '', str(_('Step 3: Apply the molarity formula')),
            f'  {_("Formula")}: M = n / V',
            f'  M = {moles} / {self._fnum(v_L)}',
            f'  M = {self._fnum(molarity)} mol/L',
        ]

        chart = self._bar_chart(
            [str(_('Moles (mol)')), str(_('Volume (L)')), str(_('Molarity (M)'))],
            [moles, v_L, molarity],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Molarity Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'molarity_from_moles',
            'result': round(molarity, 6),
            'result_label': str(_('Molarity')),
            'result_unit_symbol': 'M (mol/L)',
            'formula': f'M = {moles} / {self._fnum(v_L)}',
            'moles': moles, 'volume_L': round(v_L, 6),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 2) MOLES FROM MOLARITY & VOLUME ──────────────────────────────
    def _calc_moles_from_molarity(self, d):
        molarity = self._safe_nn(d.get('molarity'), str(_('Molarity')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        vu = d.get('volume_unit', 'liters')

        v_L = self._to_L(volume, vu)
        moles = self._verify(float(np.multiply(molarity, v_L)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Molarity")} (M) = {molarity} mol/L',
            f'  • {_("Volume")} = {volume} {self._v_sym(vu)}',
        ]
        if vu != 'liters':
            steps += [
                '', str(_('Step 2: Convert volume to liters')),
                f'  {_("Volume")} = {self._fnum(v_L)} L',
            ]
        steps += [
            '', str(_('Step 3: Apply the moles formula')),
            f'  {_("Formula")}: n = M × V',
            f'  n = {molarity} × {self._fnum(v_L)}',
            f'  n = {self._fnum(moles)} mol',
        ]

        chart = self._bar_chart(
            [str(_('Molarity (M)')), str(_('Volume (L)')), str(_('Moles (mol)'))],
            [molarity, v_L, moles],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Moles Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'moles_from_molarity',
            'result': round(moles, 6),
            'result_label': str(_('Moles')),
            'result_unit_symbol': 'mol',
            'formula': f'n = {molarity} × {self._fnum(v_L)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 3) VOLUME FROM MOLARITY & MOLES ──────────────────────────────
    def _calc_volume_from_molarity(self, d):
        molarity = self._safe_pos(d.get('molarity'), str(_('Molarity')))
        moles = self._safe_nn(d.get('moles'), str(_('Moles')))
        ru = d.get('result_unit', 'liters')

        v_L = self._verify(float(np.divide(moles, molarity)))
        result = self._from_L(v_L, ru) if ru != 'liters' else v_L

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Molarity")} (M) = {molarity} mol/L',
            f'  • {_("Moles")} (n) = {moles} mol',
            '', str(_('Step 2: Apply the volume formula')),
            f'  {_("Formula")}: V = n / M',
            f'  V = {moles} / {molarity}',
            f'  V = {self._fnum(v_L)} L',
        ]
        if ru != 'liters':
            steps += [
                '', str(_('Step 3: Convert to {unit}').format(unit=self._v_sym(ru))),
                f'  {_("Volume")} = {self._fnum(result)} {self._v_sym(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Molarity (M)')), str(_('Moles (mol)')), str(_('Volume (L)'))],
            [molarity, moles, v_L],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Volume Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'volume_from_molarity',
            'result': round(result, 6),
            'result_label': str(_('Volume')),
            'result_unit_symbol': self._v_sym(ru),
            'formula': f'V = {moles} / {molarity}',
            'volume_L': round(v_L, 6),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 4) MOLARITY FROM MASS, MW & VOLUME ───────────────────────────
    def _calc_molarity_from_mass(self, d):
        mass = self._safe_pos(d.get('mass'), str(_('Mass')))
        mw = self._safe_pos(d.get('molecular_weight'), str(_('Molecular Weight')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        mu = d.get('mass_unit', 'grams')
        vu = d.get('volume_unit', 'liters')

        m_g = self._to_g(mass, mu)
        v_L = self._to_L(volume, vu)
        moles = self._verify(float(np.divide(m_g, mw)))
        molarity = self._verify(float(np.divide(moles, v_L)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Mass")} = {mass} {self._m_sym(mu)}',
            f'  • {_("Molecular Weight")} = {mw} g/mol',
            f'  • {_("Volume")} = {volume} {self._v_sym(vu)}',
        ]
        if mu != 'grams' or vu != 'liters':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if mu != 'grams':
                steps.append(f'  {_("Mass")} = {self._fnum(m_g)} g')
            if vu != 'liters':
                steps.append(f'  {_("Volume")} = {self._fnum(v_L)} L')
        steps += [
            '', str(_('Step 3: Calculate moles')),
            f'  {_("Formula")}: n = m / MW',
            f'  n = {self._fnum(m_g)} / {mw}',
            f'  n = {self._fnum(moles)} mol',
            '', str(_('Step 4: Calculate molarity')),
            f'  {_("Formula")}: M = n / V',
            f'  M = {self._fnum(moles)} / {self._fnum(v_L)}',
            f'  M = {self._fnum(molarity)} mol/L',
        ]

        chart = self._bar_chart(
            [str(_('Mass (g)')), str(_('MW (g/mol)')), str(_('Moles (mol)')), str(_('Molarity (M)'))],
            [m_g, mw, moles, molarity],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)', 'rgba(139,92,246,0.8)'],
            str(_('Molarity from Mass'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'molarity_from_mass',
            'result': round(molarity, 6),
            'result_label': str(_('Molarity')),
            'result_unit_symbol': 'M (mol/L)',
            'formula': f'M = ({self._fnum(m_g)} / {mw}) / {self._fnum(v_L)}',
            'moles': round(moles, 6),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 5) MASS FROM MOLARITY, MW & VOLUME ───────────────────────────
    def _calc_mass_from_molarity(self, d):
        molarity = self._safe_nn(d.get('molarity'), str(_('Molarity')))
        mw = self._safe_pos(d.get('molecular_weight'), str(_('Molecular Weight')))
        volume = self._safe_pos(d.get('volume'), str(_('Volume')))
        vu = d.get('volume_unit', 'liters')
        ru = d.get('result_unit', 'grams')

        v_L = self._to_L(volume, vu)
        moles = self._verify(float(np.multiply(molarity, v_L)))
        m_g = self._verify(float(np.multiply(moles, mw)))
        result = self._from_g(m_g, ru) if ru != 'grams' else m_g

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Molarity")} = {molarity} mol/L',
            f'  • {_("Molecular Weight")} = {mw} g/mol',
            f'  • {_("Volume")} = {volume} {self._v_sym(vu)}',
        ]
        if vu != 'liters':
            steps += [
                '', str(_('Step 2: Convert volume to liters')),
                f'  {_("Volume")} = {self._fnum(v_L)} L',
            ]
        steps += [
            '', str(_('Step 3: Calculate moles')),
            f'  {_("Formula")}: n = M × V',
            f'  n = {molarity} × {self._fnum(v_L)} = {self._fnum(moles)} mol',
            '', str(_('Step 4: Calculate mass')),
            f'  {_("Formula")}: m = n × MW',
            f'  m = {self._fnum(moles)} × {mw} = {self._fnum(m_g)} g',
        ]
        if ru != 'grams':
            steps += [
                '', str(_('Step 5: Convert to {unit}').format(unit=self._m_sym(ru))),
                f'  {_("Mass")} = {self._fnum(result)} {self._m_sym(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('Molarity (M)')), str(_('Volume (L)')), str(_('Moles (mol)')), str(_('Mass (g)'))],
            [molarity, v_L, moles, m_g],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)', 'rgba(139,92,246,0.8)'],
            str(_('Mass from Molarity'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'mass_from_molarity',
            'result': round(result, 6),
            'result_label': str(_('Mass')),
            'result_unit_symbol': self._m_sym(ru),
            'formula': f'm = {molarity} × {self._fnum(v_L)} × {mw}',
            'moles': round(moles, 6), 'mass_g': round(m_g, 6),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 6) DILUTION  (M1V1 = M2V2) ──────────────────────────────────
    def _calc_dilution(self, d):
        mode = d.get('dilution_mode', 'find_v2')

        if mode == 'find_v2':
            return self._dilution_find_v2(d)
        elif mode == 'find_m2':
            return self._dilution_find_m2(d)
        else:
            return self._err(_('Invalid dilution mode.'))

    def _dilution_find_v2(self, d):
        m1 = self._safe_pos(d.get('m1'), 'M1')
        v1 = self._safe_pos(d.get('v1'), 'V1')
        m2 = self._safe_pos(d.get('m2'), 'M2')
        v1u = d.get('v1_unit', 'liters')
        ru = d.get('result_unit', 'liters')

        if m2 > m1:
            return self._err(_('Final molarity (M2) cannot be greater than initial molarity (M1) in a dilution.'))

        v1_L = self._to_L(v1, v1u)
        v2_L = self._verify(float(np.divide(np.multiply(m1, v1_L), m2)))
        result = self._from_L(v2_L, ru) if ru != 'liters' else v2_L

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • M1 = {m1} M',
            f'  • V1 = {v1} {self._v_sym(v1u)}',
            f'  • M2 = {m2} M',
        ]
        if v1u != 'liters':
            steps += [
                '', str(_('Step 2: Convert V1 to liters')),
                f'  V1 = {self._fnum(v1_L)} L',
            ]
        steps += [
            '', str(_('Step 3: Apply the dilution formula')),
            f'  {_("Formula")}: M1 × V1 = M2 × V2',
            f'  V2 = (M1 × V1) / M2',
            f'  V2 = ({m1} × {self._fnum(v1_L)}) / {m2}',
            f'  V2 = {self._fnum(v2_L)} L',
        ]
        if ru != 'liters':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._v_sym(ru))),
                f'  V2 = {self._fnum(result)} {self._v_sym(ru)}',
            ]
        steps += [
            '', str(_('Step 5: Solvent to add')),
            f'  {_("Add")} = V2 − V1 = {self._fnum(v2_L)} − {self._fnum(v1_L)} = {self._fnum(v2_L - v1_L)} L',
        ]

        chart = self._bar_chart(
            ['M1 (M)', 'V1 (L)', 'M2 (M)', 'V2 (L)'],
            [m1, v1_L, m2, v2_L],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)', 'rgba(239,68,68,0.8)'],
            str(_('Dilution (M1V1 = M2V2)'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'dilution', 'dilution_mode': 'find_v2',
            'result': round(result, 6),
            'result_label': str(_('Final Volume (V2)')),
            'result_unit_symbol': self._v_sym(ru),
            'formula': f'V2 = ({m1} × {self._fnum(v1_L)}) / {m2}',
            'solvent_to_add_L': round(v2_L - v1_L, 6),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    def _dilution_find_m2(self, d):
        m1 = self._safe_pos(d.get('m1'), 'M1')
        v1 = self._safe_pos(d.get('v1'), 'V1')
        v2 = self._safe_pos(d.get('v2'), 'V2')
        v1u = d.get('v1_unit', 'liters')
        v2u = d.get('v2_unit', 'liters')

        v1_L = self._to_L(v1, v1u)
        v2_L = self._to_L(v2, v2u)
        m2 = self._verify(float(np.divide(np.multiply(m1, v1_L), v2_L)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • M1 = {m1} M',
            f'  • V1 = {v1} {self._v_sym(v1u)}',
            f'  • V2 = {v2} {self._v_sym(v2u)}',
        ]
        if v1u != 'liters' or v2u != 'liters':
            steps += ['', str(_('Step 2: Convert volumes to liters'))]
            if v1u != 'liters':
                steps.append(f'  V1 = {self._fnum(v1_L)} L')
            if v2u != 'liters':
                steps.append(f'  V2 = {self._fnum(v2_L)} L')
        steps += [
            '', str(_('Step 3: Apply the dilution formula')),
            f'  {_("Formula")}: M1 × V1 = M2 × V2',
            f'  M2 = (M1 × V1) / V2',
            f'  M2 = ({m1} × {self._fnum(v1_L)}) / {self._fnum(v2_L)}',
            f'  M2 = {self._fnum(m2)} M',
        ]

        chart = self._bar_chart(
            ['M1 (M)', 'V1 (L)', 'V2 (L)', 'M2 (M)'],
            [m1, v1_L, v2_L, m2],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)', 'rgba(239,68,68,0.8)'],
            str(_('Dilution (M1V1 = M2V2)'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'dilution', 'dilution_mode': 'find_m2',
            'result': round(m2, 6),
            'result_label': str(_('Final Molarity (M2)')),
            'result_unit_symbol': 'M (mol/L)',
            'formula': f'M2 = ({m1} × {self._fnum(v1_L)}) / {self._fnum(v2_L)}',
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
