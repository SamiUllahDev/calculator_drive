from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HorsepowerCalculator(View):
    """
    Horsepower Calculator — HP ↔ Torque ↔ RPM & Power Conversion.

    Calc types:
        • HP from Torque & RPM    → HP = (T × RPM) / 5252
        • Torque from HP & RPM    → T  = (HP × 5252) / RPM
        • RPM from HP & Torque    → RPM = (HP × 5252) / T
        • Power unit conversion   → HP ↔ kW ↔ W

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/horsepower_calculator.html'

    # ── conversion constants ─────────────────────────────────────────
    HP_TO_KW = 0.7457
    HP_TO_W = 745.7
    FT_LB_TO_NM = 1.35582
    NM_TO_FT_LB = 0.737562

    POWER_UNITS = {
        'hp':    {'to_hp': 1.0,             'sym': 'HP',  'label': _('Horsepower (HP)')},
        'kw':    {'to_hp': 1.0 / 0.7457,    'sym': 'kW',  'label': _('Kilowatts (kW)')},
        'watts': {'to_hp': 1.0 / 745.7,     'sym': 'W',   'label': _('Watts (W)')},
    }

    TORQUE_UNITS = {
        'ft_lb': {'to_ftlb': 1.0,       'sym': 'ft-lb', 'label': _('Foot-Pounds (ft-lb)')},
        'nm':    {'to_ftlb': 0.737562,   'sym': 'N·m',   'label': _('Newton-Meters (N·m)')},
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Horsepower Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'hp_from_torque')
            dispatch = {
                'hp_from_torque':    self._calc_hp_from_torque,
                'torque_from_hp':    self._calc_torque_from_hp,
                'rpm_from_hp':       self._calc_rpm_from_hp,
                'convert_power':     self._calc_convert_power,
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

    def _torque_sym(self, key):
        return self.TORQUE_UNITS.get(key, self.TORQUE_UNITS['ft_lb'])['sym']

    def _to_ftlb(self, val, unit):
        return float(np.multiply(val, self.TORQUE_UNITS.get(unit, self.TORQUE_UNITS['ft_lb'])['to_ftlb']))

    def _from_ftlb(self, val, unit):
        factor = self.TORQUE_UNITS.get(unit, self.TORQUE_UNITS['ft_lb'])['to_ftlb']
        return float(np.divide(val, factor))

    def _hp_to(self, hp, unit):
        if unit == 'kw':
            return float(np.multiply(hp, self.HP_TO_KW))
        if unit == 'watts':
            return float(np.multiply(hp, self.HP_TO_W))
        return hp

    # ── HP FROM TORQUE & RPM ─────────────────────────────────────────
    def _calc_hp_from_torque(self, d):
        torque = self._safe_pos(d.get('torque'), str(_('Torque')))
        rpm = self._safe_pos(d.get('rpm'), str(_('RPM')))
        tu = d.get('torque_unit', 'ft_lb')

        t_ftlb = self._to_ftlb(torque, tu)
        hp = self._verify(float(np.divide(np.multiply(t_ftlb, rpm), 5252.0)))
        kw = self._hp_to(hp, 'kw')
        watts = self._hp_to(hp, 'watts')

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Torque")} = {torque} {self._torque_sym(tu)}',
            f'  • {_("RPM")} = {rpm}',
        ]
        if tu == 'nm':
            steps += [
                '', str(_('Step 2: Convert torque to ft-lb')),
                f'  {_("Formula")}: ft-lb = N·m × 0.737562',
                f'  {_("Torque")} = {torque} × 0.737562 = {self._fnum(t_ftlb)} ft-lb',
            ]
        steps += [
            '', str(_('Step 3: Apply the horsepower formula')),
            f'  {_("Formula")}: HP = (Torque × RPM) / 5252',
            f'  HP = ({self._fnum(t_ftlb)} × {rpm}) / 5252',
            f'  HP = {self._fnum(hp)}',
            '', str(_('Step 4: Convert to other units')),
            f'  • {self._fnum(kw)} kW',
            f'  • {self._fnum(watts)} W',
        ]

        chart = self._bar_chart(
            [str(_('Torque (ft-lb)')), str(_('RPM')), str(_('HP'))],
            [t_ftlb, rpm, hp],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Horsepower Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'hp_from_torque',
            'result': round(hp, 4),
            'result_label': str(_('Horsepower')),
            'result_unit_symbol': 'HP',
            'formula': f'HP = ({self._fnum(t_ftlb)} × {rpm}) / 5252',
            'kilowatts': round(kw, 4),
            'watts': round(watts, 2),
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── TORQUE FROM HP & RPM ─────────────────────────────────────────
    def _calc_torque_from_hp(self, d):
        hp = self._safe_pos(d.get('horsepower'), str(_('Horsepower')))
        rpm = self._safe_pos(d.get('rpm'), str(_('RPM')))
        tu = d.get('torque_unit', 'ft_lb')

        t_ftlb = self._verify(float(np.divide(np.multiply(hp, 5252.0), rpm)))
        torque = self._from_ftlb(t_ftlb, tu) if tu == 'nm' else t_ftlb

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Horsepower")} = {hp} HP',
            f'  • {_("RPM")} = {rpm}',
            '', str(_('Step 2: Apply the torque formula')),
            f'  {_("Formula")}: Torque = (HP × 5252) / RPM',
            f'  Torque = ({hp} × 5252) / {rpm}',
            f'  Torque = {self._fnum(t_ftlb)} ft-lb',
        ]
        if tu == 'nm':
            nm = float(np.multiply(t_ftlb, self.FT_LB_TO_NM))
            steps += [
                '', str(_('Step 3: Convert to Newton-meters')),
                f'  {_("Formula")}: N·m = ft-lb × 1.35582',
                f'  {_("Torque")} = {self._fnum(t_ftlb)} × 1.35582 = {self._fnum(nm)} N·m',
            ]
            torque = nm

        steps += [
            '', str(_('Step 4: Result')),
            f'  {_("Torque")} = {self._fnum(torque)} {self._torque_sym(tu)}',
        ]

        chart = self._bar_chart(
            [str(_('HP')), str(_('RPM')), str(_('Torque (ft-lb)'))],
            [hp, rpm, t_ftlb],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Torque Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'torque_from_hp',
            'result': round(torque, 4),
            'result_label': str(_('Torque')),
            'result_unit_symbol': self._torque_sym(tu),
            'formula': f'T = ({hp} × 5252) / {rpm}',
            'horsepower': hp,
            'rpm': rpm,
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── RPM FROM HP & TORQUE ─────────────────────────────────────────
    def _calc_rpm_from_hp(self, d):
        hp = self._safe_pos(d.get('horsepower'), str(_('Horsepower')))
        torque = self._safe_pos(d.get('torque'), str(_('Torque')))
        tu = d.get('torque_unit', 'ft_lb')

        t_ftlb = self._to_ftlb(torque, tu)
        rpm = self._verify(float(np.divide(np.multiply(hp, 5252.0), t_ftlb)))

        steps = [
            str(_('Step 1: Identify the given values')),
            f'  • {_("Horsepower")} = {hp} HP',
            f'  • {_("Torque")} = {torque} {self._torque_sym(tu)}',
        ]
        if tu == 'nm':
            steps += [
                '', str(_('Step 2: Convert torque to ft-lb')),
                f'  {_("Torque")} = {torque} × 0.737562 = {self._fnum(t_ftlb)} ft-lb',
            ]
        steps += [
            '', str(_('Step 3: Apply the RPM formula')),
            f'  {_("Formula")}: RPM = (HP × 5252) / Torque',
            f'  RPM = ({hp} × 5252) / {self._fnum(t_ftlb)}',
            f'  RPM = {self._fnum(rpm)}',
            '', str(_('Step 4: Result')),
            f'  {_("RPM")} = {self._fnum(rpm)}',
        ]

        chart = self._bar_chart(
            [str(_('HP')), str(_('Torque (ft-lb)')), str(_('RPM'))],
            [hp, t_ftlb, rpm],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('RPM Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'rpm_from_hp',
            'result': round(rpm, 2),
            'result_label': str(_('RPM')),
            'result_unit_symbol': 'RPM',
            'formula': f'RPM = ({hp} × 5252) / {self._fnum(t_ftlb)}',
            'horsepower': hp,
            'torque': torque,
            'torque_unit': tu,
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── CONVERT POWER UNITS ──────────────────────────────────────────
    def _calc_convert_power(self, d):
        value = self._safe_nn(d.get('value'), str(_('Power Value')))
        from_u = d.get('from_unit', 'hp')
        to_u = d.get('to_unit', 'kw')

        if from_u not in self.POWER_UNITS:
            return self._err(_('Invalid source unit.'))
        if to_u not in self.POWER_UNITS:
            return self._err(_('Invalid target unit.'))

        from_sym = self.POWER_UNITS[from_u]['sym']
        to_sym = self.POWER_UNITS[to_u]['sym']

        # convert to HP first
        hp = float(np.multiply(value, self.POWER_UNITS[from_u]['to_hp']))

        # convert from HP to target
        result = self._hp_to(hp, to_u)
        result = self._verify(result)

        steps = [
            str(_('Step 1: Identify the given value')),
            f'  • {_("Power")} = {value} {from_sym}',
        ]
        if from_u != 'hp':
            steps += [
                '', str(_('Step 2: Convert to horsepower')),
                f'  HP = {value} {from_sym} × {self.POWER_UNITS[from_u]["to_hp"]:.6g}',
                f'  HP = {self._fnum(hp)}',
            ]
        steps += [
            '', str(_('Step 3: Convert to {unit}').format(unit=to_sym)),
            f'  {_("Result")} = {self._fnum(result)} {to_sym}',
        ]

        chart = self._bar_chart(
            [from_sym, 'HP', to_sym],
            [value, hp, result],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Power Conversion'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'convert_power',
            'result': round(result, 6),
            'result_label': str(_('{from_u} to {to_u}').format(from_u=from_sym, to_u=to_sym)),
            'result_unit_symbol': to_sym,
            'formula': f'{value} {from_sym} → {self._fnum(result)} {to_sym}',
            'hp_equivalent': round(hp, 4),
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
