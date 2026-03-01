from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EngineHorsepowerCalculator(View):
    """
    Engine Horsepower Calculator — HP ↔ Torque ↔ RPM with extended units.

    Calc types:
        • Calculate Horsepower   → HP = (T × RPM) / 5252
        • Calculate Torque       → T  = (HP × 5252) / RPM
        • Calculate RPM          → RPM = (HP × 5252) / T
        • Convert Power Units    → HP ↔ kW ↔ PS ↔ BHP
        • Convert Torque Units   → lb·ft ↔ N·m ↔ kg·m

    Supports multiple power units (HP, kW, PS, BHP) and torque units
    (lb·ft, N·m, kg·m) commonly used in the automotive industry.

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/engine_horsepower_calculator.html'

    # ── conversion factors (to HP / to lb·ft) ────────────────────────
    HP_CONSTANT = 5252.0

    POWER_UNITS = {
        'hp':  {'to_hp': 1.0,              'sym': 'HP',  'label': _('Horsepower (HP)')},
        'kW':  {'to_hp': 1.0 / 0.7457,     'sym': 'kW',  'label': _('Kilowatts (kW)')},
        'PS':  {'to_hp': 0.9863,            'sym': 'PS',  'label': _('Metric HP (PS)')},
        'bhp': {'to_hp': 1.0,              'sym': 'BHP', 'label': _('Brake HP (BHP)')},
    }

    TORQUE_UNITS = {
        'lb_ft': {'to_lbft': 1.0,           'sym': 'lb·ft', 'label': _('Pound-Feet (lb·ft)')},
        'nm':    {'to_lbft': 0.737562,       'sym': 'N·m',   'label': _('Newton-Meters (N·m)')},
        'kg_m':  {'to_lbft': 7.233,          'sym': 'kg·m',  'label': _('Kilogram-Meters (kg·m)')},
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Engine Horsepower Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'horsepower')
            dispatch = {
                'horsepower':     self._calc_horsepower,
                'torque':         self._calc_torque,
                'rpm':            self._calc_rpm,
                'convert_power':  self._calc_convert_power,
                'convert_torque': self._calc_convert_torque,
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

    def _safe_pos(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        if v > 1e12:
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

    def _p_sym(self, key):
        return self.POWER_UNITS.get(key, self.POWER_UNITS['hp'])['sym']

    def _t_sym(self, key):
        return self.TORQUE_UNITS.get(key, self.TORQUE_UNITS['lb_ft'])['sym']

    def _to_hp(self, val, unit):
        return float(np.multiply(val, self.POWER_UNITS.get(unit, self.POWER_UNITS['hp'])['to_hp']))

    def _from_hp(self, hp, unit):
        factor = self.POWER_UNITS.get(unit, self.POWER_UNITS['hp'])['to_hp']
        return float(np.divide(hp, factor))

    def _to_lbft(self, val, unit):
        return float(np.multiply(val, self.TORQUE_UNITS.get(unit, self.TORQUE_UNITS['lb_ft'])['to_lbft']))

    def _from_lbft(self, lbft, unit):
        factor = self.TORQUE_UNITS.get(unit, self.TORQUE_UNITS['lb_ft'])['to_lbft']
        return float(np.divide(lbft, factor))

    # ── CALCULATE HORSEPOWER ─────────────────────────────────────────
    def _calc_horsepower(self, d):
        torque = self._safe_pos(d.get('torque'), str(_('Torque')))
        rpm = self._safe_pos(d.get('rpm'), str(_('RPM')))
        tu = d.get('torque_unit', 'lb_ft')
        ru = d.get('result_unit', 'hp')

        t_lbft = self._to_lbft(torque, tu)
        hp = self._verify(float(np.divide(np.multiply(t_lbft, rpm), self.HP_CONSTANT)))
        result = self._from_hp(hp, ru) if ru != 'hp' else hp
        kw = self._from_hp(hp, 'kW')
        ps = self._from_hp(hp, 'PS')

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Torque")} = {torque} {self._t_sym(tu)}',
            f'  • {_("RPM")} = {rpm}',
        ]
        if tu != 'lb_ft':
            steps += [
                '', str(_('Step 2: Convert torque to lb·ft')),
                f'  {_("Torque")} = {torque} × {self.TORQUE_UNITS[tu]["to_lbft"]} = {self._fnum(t_lbft)} lb·ft',
            ]
        steps += [
            '', str(_('Step 3: Apply the horsepower formula')),
            f'  {_("Formula")}: HP = (Torque × RPM) / 5252',
            f'  HP = ({self._fnum(t_lbft)} × {rpm}) / 5252',
            f'  HP = {self._fnum(hp)}',
        ]
        if ru != 'hp':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._p_sym(ru))),
                f'  {_("Result")} = {self._fnum(result)} {self._p_sym(ru)}',
            ]
        steps += [
            '', str(_('Step 5: Other power units')),
            f'  • {self._fnum(hp)} HP',
            f'  • {self._fnum(kw)} kW',
            f'  • {self._fnum(ps)} PS',
        ]

        chart = self._bar_chart(
            [str(_('Torque (lb·ft)')), str(_('RPM')), str(_('HP'))],
            [t_lbft, rpm, hp],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Engine Horsepower Breakdown'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'horsepower',
            'result': round(result, 4),
            'result_label': str(_('Engine Horsepower')),
            'result_unit_symbol': self._p_sym(ru),
            'formula': f'HP = ({self._fnum(t_lbft)} × {rpm}) / 5252',
            'hp': round(hp, 4), 'kw': round(kw, 4), 'ps': round(ps, 4),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── CALCULATE TORQUE ─────────────────────────────────────────────
    def _calc_torque(self, d):
        hp_in = self._safe_pos(d.get('horsepower'), str(_('Horsepower')))
        rpm = self._safe_pos(d.get('rpm'), str(_('RPM')))
        pu = d.get('power_unit', 'hp')
        ru = d.get('result_unit', 'lb_ft')

        hp = self._to_hp(hp_in, pu)
        t_lbft = self._verify(float(np.divide(np.multiply(hp, self.HP_CONSTANT), rpm)))
        result = self._from_lbft(t_lbft, ru) if ru != 'lb_ft' else t_lbft

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Horsepower")} = {hp_in} {self._p_sym(pu)}',
            f'  • {_("RPM")} = {rpm}',
        ]
        if pu != 'hp':
            steps += [
                '', str(_('Step 2: Convert power to HP')),
                f'  HP = {hp_in} × {self.POWER_UNITS[pu]["to_hp"]:.6g} = {self._fnum(hp)} HP',
            ]
        steps += [
            '', str(_('Step 3: Apply the torque formula')),
            f'  {_("Formula")}: Torque = (HP × 5252) / RPM',
            f'  Torque = ({self._fnum(hp)} × 5252) / {rpm}',
            f'  Torque = {self._fnum(t_lbft)} lb·ft',
        ]
        if ru != 'lb_ft':
            steps += [
                '', str(_('Step 4: Convert to {unit}').format(unit=self._t_sym(ru))),
                f'  {_("Result")} = {self._fnum(result)} {self._t_sym(ru)}',
            ]

        chart = self._bar_chart(
            [str(_('HP')), str(_('RPM')), str(_('Torque (lb·ft)'))],
            [hp, rpm, t_lbft],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Torque Calculation Breakdown'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'torque',
            'result': round(result, 4),
            'result_label': str(_('Engine Torque')),
            'result_unit_symbol': self._t_sym(ru),
            'formula': f'T = ({self._fnum(hp)} × 5252) / {rpm}',
            'torque_lbft': round(t_lbft, 4),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── CALCULATE RPM ────────────────────────────────────────────────
    def _calc_rpm(self, d):
        hp_in = self._safe_pos(d.get('horsepower'), str(_('Horsepower')))
        torque = self._safe_pos(d.get('torque'), str(_('Torque')))
        pu = d.get('power_unit', 'hp')
        tu = d.get('torque_unit', 'lb_ft')

        hp = self._to_hp(hp_in, pu)
        t_lbft = self._to_lbft(torque, tu)
        rpm = self._verify(float(np.divide(np.multiply(hp, self.HP_CONSTANT), t_lbft)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Horsepower")} = {hp_in} {self._p_sym(pu)}',
            f'  • {_("Torque")} = {torque} {self._t_sym(tu)}',
        ]
        if pu != 'hp':
            steps += [
                '', str(_('Step 2: Convert power to HP')),
                f'  HP = {self._fnum(hp)} HP',
            ]
        if tu != 'lb_ft':
            steps += [
                '', str(_('Step 3: Convert torque to lb·ft')),
                f'  {_("Torque")} = {self._fnum(t_lbft)} lb·ft',
            ]
        steps += [
            '', str(_('Step 4: Apply the RPM formula')),
            f'  {_("Formula")}: RPM = (HP × 5252) / Torque',
            f'  RPM = ({self._fnum(hp)} × 5252) / {self._fnum(t_lbft)}',
            f'  RPM = {self._fnum(rpm)}',
        ]

        chart = self._bar_chart(
            [str(_('HP')), str(_('Torque (lb·ft)')), str(_('RPM'))],
            [hp, t_lbft, rpm],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('RPM Calculation Breakdown'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'rpm',
            'result': round(rpm, 2),
            'result_label': str(_('Engine RPM')),
            'result_unit_symbol': 'RPM',
            'formula': f'RPM = ({self._fnum(hp)} × 5252) / {self._fnum(t_lbft)}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── CONVERT POWER UNITS ──────────────────────────────────────────
    def _calc_convert_power(self, d):
        value = self._safe_nn(d.get('value'), str(_('Power Value')))
        from_u = d.get('from_unit', 'hp')
        to_u = d.get('to_unit', 'kW')

        if from_u not in self.POWER_UNITS:
            return self._err(_('Invalid source unit.'))
        if to_u not in self.POWER_UNITS:
            return self._err(_('Invalid target unit.'))

        hp = self._to_hp(value, from_u)
        result = self._verify(self._from_hp(hp, to_u))
        f_sym = self._p_sym(from_u)
        t_sym = self._p_sym(to_u)

        steps = [
            str(_('Step 1: Identify the given value')),
            f'  • {_("Power")} = {value} {f_sym}',
        ]
        if from_u != 'hp':
            steps += [
                '', str(_('Step 2: Convert to HP')),
                f'  HP = {value} × {self.POWER_UNITS[from_u]["to_hp"]:.6g} = {self._fnum(hp)} HP',
            ]
        steps += [
            '', str(_('Step 3: Convert to {unit}').format(unit=t_sym)),
            f'  {_("Result")} = {self._fnum(result)} {t_sym}',
        ]

        chart = self._bar_chart(
            [f_sym, 'HP', t_sym],
            [value, hp, result],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Power Conversion'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'convert_power',
            'result': round(result, 6),
            'result_label': str(_('{from_u} to {to_u}').format(from_u=f_sym, to_u=t_sym)),
            'result_unit_symbol': t_sym,
            'formula': f'{value} {f_sym} → {self._fnum(result)} {t_sym}',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── CONVERT TORQUE UNITS ─────────────────────────────────────────
    def _calc_convert_torque(self, d):
        value = self._safe_nn(d.get('value'), str(_('Torque Value')))
        from_u = d.get('from_unit', 'lb_ft')
        to_u = d.get('to_unit', 'nm')

        if from_u not in self.TORQUE_UNITS:
            return self._err(_('Invalid source unit.'))
        if to_u not in self.TORQUE_UNITS:
            return self._err(_('Invalid target unit.'))

        lbft = self._to_lbft(value, from_u)
        result = self._verify(self._from_lbft(lbft, to_u))
        f_sym = self._t_sym(from_u)
        t_sym = self._t_sym(to_u)

        steps = [
            str(_('Step 1: Identify the given value')),
            f'  • {_("Torque")} = {value} {f_sym}',
        ]
        if from_u != 'lb_ft':
            steps += [
                '', str(_('Step 2: Convert to lb·ft')),
                f'  lb·ft = {value} × {self.TORQUE_UNITS[from_u]["to_lbft"]:.6g} = {self._fnum(lbft)} lb·ft',
            ]
        steps += [
            '', str(_('Step 3: Convert to {unit}').format(unit=t_sym)),
            f'  {_("Result")} = {self._fnum(result)} {t_sym}',
        ]

        chart = self._bar_chart(
            [f_sym, 'lb·ft', t_sym],
            [value, lbft, result],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Torque Conversion'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'convert_torque',
            'result': round(result, 6),
            'result_label': str(_('{from_u} to {to_u}').format(from_u=f_sym, to_u=t_sym)),
            'result_unit_symbol': t_sym,
            'formula': f'{value} {f_sym} → {self._fnum(result)} {t_sym}',
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
