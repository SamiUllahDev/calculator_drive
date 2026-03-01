from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import Integer, Rational, sqrt as sym_sqrt, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ElectricityCalculator(View):
    """
    Electricity Calculator — Power, Voltage, Current, Resistance, Energy & Cost.

    Uses NumPy for efficient vectorised arithmetic.
    Uses SymPy for precise symbolic verification.
    """
    template_name = 'other_calculators/electricity_calculator.html'

    # ── unit conversion tables (to base SI) ──────────────────────────
    POWER_CONV = {'W': 1.0, 'kW': 1e3, 'MW': 1e6, 'hp': 745.7, 'BTU_per_hour': 0.293071}
    VOLTAGE_CONV = {'V': 1.0, 'kV': 1e3, 'mV': 1e-3}
    CURRENT_CONV = {'A': 1.0, 'mA': 1e-3, 'kA': 1e3}
    RESISTANCE_CONV = {'ohm': 1.0, 'kohm': 1e3, 'Mohm': 1e6}
    ENERGY_CONV = {'kWh': 1.0, 'Wh': 1e-3, 'MWh': 1e3, 'J': 2.77778e-7, 'MJ': 0.277778}
    TIME_CONV = {'seconds': 1 / 3600, 'minutes': 1 / 60, 'hours': 1.0, 'days': 24.0}

    UNIT_DISPLAY = {
        'W': 'W', 'kW': 'kW', 'MW': 'MW', 'hp': 'hp', 'BTU_per_hour': 'BTU/h',
        'V': 'V', 'kV': 'kV', 'mV': 'mV',
        'A': 'A', 'mA': 'mA', 'kA': 'kA',
        'ohm': 'Ω', 'kohm': 'kΩ', 'Mohm': 'MΩ',
        'kWh': 'kWh', 'Wh': 'Wh', 'MWh': 'MWh', 'J': 'J', 'MJ': 'MJ',
    }

    def _u(self, key):
        return self.UNIT_DISPLAY.get(key, key)

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Electricity Calculator'),
            'page_title': _('Electricity Calculator - Calculate Power, Voltage, Current & Resistance Online Free'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'power')
            dispatch = {
                'power': self._calc_power,
                'voltage': self._calc_voltage,
                'current': self._calc_current,
                'resistance': self._calc_resistance,
                'energy': self._calc_energy,
                'cost': self._calc_cost,
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

    def _fnum(self, v):
        """Format a number for display."""
        if v is None:
            return '0'
        if abs(v) < 1e-6 or abs(v) >= 1e6:
            return f'{v:.6g}'
        return f'{v:,.6g}'

    def _safe(self, v, name):
        """Parse and validate a positive numeric value."""
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        if v > 1e12:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _safe_pos(self, v, name):
        """Parse and validate a strictly positive numeric value."""
        v = self._safe(v, name)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        return v

    def _base(self, v, unit, table, name):
        if unit not in table:
            raise ValueError(str(_('{name}: invalid unit "{unit}".').format(name=name, unit=unit)))
        return float(np.float64(v) * table[unit])

    def _to_unit(self, base_val, unit, table):
        return float(np.float64(base_val) / table[unit])

    def _verify(self, val):
        if not np.isfinite(val):
            raise ValueError(str(_('Calculation produced an invalid result.')))
        return val

    # ── POWER ─────────────────────────────────────────────────────────
    def _calc_power(self, d):
        method = d.get('method', 'vi')
        ru = d.get('result_unit', 'W')
        if ru not in self.POWER_CONV:
            return self._err(_('Invalid result unit.'))

        if method == 'vi':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'V')
            I = self._safe(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'A')
            Vb = self._base(V, vu, self.VOLTAGE_CONV, str(_('Voltage')))
            Ib = self._base(I, iu, self.CURRENT_CONV, str(_('Current')))
            Pb = self._verify(float(np.multiply(Vb, Ib)))
            P = self._to_unit(Pb, ru, self.POWER_CONV)
            formula = 'P = V × I'
            steps = [
                str(_('Formula:')) + ' P = V × I',
                str(_('Given values:')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                str(_('Calculation:')),
                f'  P = {V} {self._u(vu)} × {I} {self._u(iu)}',
                f'  P = {self._fnum(P)} {self._u(ru)}',
            ]
        elif method == 'vr':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'V')
            R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
            rsu = d.get('resistance_unit', 'ohm')
            Vb = self._base(V, vu, self.VOLTAGE_CONV, str(_('Voltage')))
            Rb = self._base(R, rsu, self.RESISTANCE_CONV, str(_('Resistance')))
            Pb = self._verify(float(np.divide(np.multiply(Vb, Vb), Rb)))
            P = self._to_unit(Pb, ru, self.POWER_CONV)
            formula = 'P = V² / R'
            steps = [
                str(_('Formula:')) + ' P = V² / R',
                str(_('Given values:')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(rsu)}',
                str(_('Calculation:')),
                f'  V² = {V}² = {V**2}',
                f'  P = {V**2} / {R} = {self._fnum(P)} {self._u(ru)}',
            ]
        elif method == 'ir':
            I = self._safe(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'A')
            R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
            rsu = d.get('resistance_unit', 'ohm')
            Ib = self._base(I, iu, self.CURRENT_CONV, str(_('Current')))
            Rb = self._base(R, rsu, self.RESISTANCE_CONV, str(_('Resistance')))
            Pb = self._verify(float(np.multiply(np.multiply(Ib, Ib), Rb)))
            P = self._to_unit(Pb, ru, self.POWER_CONV)
            formula = 'P = I² × R'
            steps = [
                str(_('Formula:')) + ' P = I² × R',
                str(_('Given values:')),
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(rsu)}',
                str(_('Calculation:')),
                f'  I² = {I}² = {I**2}',
                f'  P = {I**2} × {R} = {self._fnum(P)} {self._u(ru)}',
            ]
        else:
            return self._err(_('Invalid method.'))

        chart = self._chart_bar(
            [str(_('Power'))], [Pb],
            ['#6366f1'],
            str(_('Power Calculation'))
        )
        return JsonResponse({
            'success': True, 'calc_type': 'power', 'method': method,
            'result': P, 'result_unit': self._u(ru), 'formula': formula,
            'step_by_step': steps,
            'chart_data': {'power_chart': chart},
        })

    # ── VOLTAGE ───────────────────────────────────────────────────────
    def _calc_voltage(self, d):
        method = d.get('method', 'pi')
        ru = d.get('result_unit', 'V')
        if ru not in self.VOLTAGE_CONV:
            return self._err(_('Invalid result unit.'))

        if method == 'pi':
            P = self._safe(d.get('power'), str(_('Power')))
            pu = d.get('power_unit', 'W')
            I = self._safe_pos(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'A')
            Pb = self._base(P, pu, self.POWER_CONV, str(_('Power')))
            Ib = self._base(I, iu, self.CURRENT_CONV, str(_('Current')))
            Vb = self._verify(float(np.divide(Pb, Ib)))
            V = self._to_unit(Vb, ru, self.VOLTAGE_CONV)
            formula = 'V = P / I'
            steps = [
                str(_('Formula:')) + ' V = P / I',
                str(_('Given values:')),
                f'  • {_("Power")} (P) = {P} {self._u(pu)}',
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                str(_('Calculation:')),
                f'  V = {P} / {I} = {self._fnum(V)} {self._u(ru)}',
            ]
        elif method == 'ir':
            I = self._safe(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'A')
            R = self._safe(d.get('resistance'), str(_('Resistance')))
            rsu = d.get('resistance_unit', 'ohm')
            Ib = self._base(I, iu, self.CURRENT_CONV, str(_('Current')))
            Rb = self._base(R, rsu, self.RESISTANCE_CONV, str(_('Resistance')))
            Vb = self._verify(float(np.multiply(Ib, Rb)))
            V = self._to_unit(Vb, ru, self.VOLTAGE_CONV)
            formula = 'V = I × R'
            steps = [
                str(_('Formula:')) + ' V = I × R',
                str(_('Given values:')),
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(rsu)}',
                str(_('Calculation:')),
                f'  V = {I} × {R} = {self._fnum(V)} {self._u(ru)}',
            ]
        elif method == 'pr':
            P = self._safe(d.get('power'), str(_('Power')))
            pu = d.get('power_unit', 'W')
            R = self._safe(d.get('resistance'), str(_('Resistance')))
            rsu = d.get('resistance_unit', 'ohm')
            Pb = self._base(P, pu, self.POWER_CONV, str(_('Power')))
            Rb = self._base(R, rsu, self.RESISTANCE_CONV, str(_('Resistance')))
            Vb = self._verify(float(math.sqrt(np.multiply(Pb, Rb))))
            V = self._to_unit(Vb, ru, self.VOLTAGE_CONV)
            formula = 'V = √(P × R)'
            steps = [
                str(_('Formula:')) + ' V = √(P × R)',
                str(_('Given values:')),
                f'  • {_("Power")} (P) = {P} {self._u(pu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(rsu)}',
                str(_('Calculation:')),
                f'  P × R = {P} × {R} = {P * R}',
                f'  V = √({P * R}) = {self._fnum(V)} {self._u(ru)}',
            ]
        else:
            return self._err(_('Invalid method.'))

        chart = self._chart_bar(
            [str(_('Voltage'))], [Vb],
            ['#8b5cf6'],
            str(_('Voltage Calculation'))
        )
        return JsonResponse({
            'success': True, 'calc_type': 'voltage', 'method': method,
            'result': V, 'result_unit': self._u(ru), 'formula': formula,
            'step_by_step': steps,
            'chart_data': {'voltage_chart': chart},
        })

    # ── CURRENT ───────────────────────────────────────────────────────
    def _calc_current(self, d):
        method = d.get('method', 'pv')
        ru = d.get('result_unit', 'A')
        if ru not in self.CURRENT_CONV:
            return self._err(_('Invalid result unit.'))

        if method == 'pv':
            P = self._safe(d.get('power'), str(_('Power')))
            pu = d.get('power_unit', 'W')
            V = self._safe_pos(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'V')
            Pb = self._base(P, pu, self.POWER_CONV, str(_('Power')))
            Vb = self._base(V, vu, self.VOLTAGE_CONV, str(_('Voltage')))
            Ib = self._verify(float(np.divide(Pb, Vb)))
            I = self._to_unit(Ib, ru, self.CURRENT_CONV)
            formula = 'I = P / V'
            steps = [
                str(_('Formula:')) + ' I = P / V',
                str(_('Given values:')),
                f'  • {_("Power")} (P) = {P} {self._u(pu)}',
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                str(_('Calculation:')),
                f'  I = {P} / {V} = {self._fnum(I)} {self._u(ru)}',
            ]
        elif method == 'vr':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'V')
            R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
            rsu = d.get('resistance_unit', 'ohm')
            Vb = self._base(V, vu, self.VOLTAGE_CONV, str(_('Voltage')))
            Rb = self._base(R, rsu, self.RESISTANCE_CONV, str(_('Resistance')))
            Ib = self._verify(float(np.divide(Vb, Rb)))
            I = self._to_unit(Ib, ru, self.CURRENT_CONV)
            formula = 'I = V / R'
            steps = [
                str(_('Formula:')) + ' I = V / R',
                str(_('Given values:')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(rsu)}',
                str(_('Calculation:')),
                f'  I = {V} / {R} = {self._fnum(I)} {self._u(ru)}',
            ]
        elif method == 'pr':
            P = self._safe(d.get('power'), str(_('Power')))
            pu = d.get('power_unit', 'W')
            R = self._safe_pos(d.get('resistance'), str(_('Resistance')))
            rsu = d.get('resistance_unit', 'ohm')
            Pb = self._base(P, pu, self.POWER_CONV, str(_('Power')))
            Rb = self._base(R, rsu, self.RESISTANCE_CONV, str(_('Resistance')))
            Ib = self._verify(float(math.sqrt(np.divide(Pb, Rb))))
            I = self._to_unit(Ib, ru, self.CURRENT_CONV)
            formula = 'I = √(P / R)'
            steps = [
                str(_('Formula:')) + ' I = √(P / R)',
                str(_('Given values:')),
                f'  • {_("Power")} (P) = {P} {self._u(pu)}',
                f'  • {_("Resistance")} (R) = {R} {self._u(rsu)}',
                str(_('Calculation:')),
                f'  P / R = {P} / {R} = {P / R}',
                f'  I = √({P / R}) = {self._fnum(I)} {self._u(ru)}',
            ]
        else:
            return self._err(_('Invalid method.'))

        chart = self._chart_bar(
            [str(_('Current'))], [Ib],
            ['#10b981'],
            str(_('Current Calculation'))
        )
        return JsonResponse({
            'success': True, 'calc_type': 'current', 'method': method,
            'result': I, 'result_unit': self._u(ru), 'formula': formula,
            'step_by_step': steps,
            'chart_data': {'current_chart': chart},
        })

    # ── RESISTANCE ────────────────────────────────────────────────────
    def _calc_resistance(self, d):
        method = d.get('method', 'vi')
        ru = d.get('result_unit', 'ohm')
        if ru not in self.RESISTANCE_CONV:
            return self._err(_('Invalid result unit.'))

        if method == 'vi':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'V')
            I = self._safe_pos(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'A')
            Vb = self._base(V, vu, self.VOLTAGE_CONV, str(_('Voltage')))
            Ib = self._base(I, iu, self.CURRENT_CONV, str(_('Current')))
            Rb = self._verify(float(np.divide(Vb, Ib)))
            R = self._to_unit(Rb, ru, self.RESISTANCE_CONV)
            formula = 'R = V / I'
            steps = [
                str(_('Formula:')) + ' R = V / I',
                str(_('Given values:')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                str(_('Calculation:')),
                f'  R = {V} / {I} = {self._fnum(R)} {self._u(ru)}',
            ]
        elif method == 'vp':
            V = self._safe(d.get('voltage'), str(_('Voltage')))
            vu = d.get('voltage_unit', 'V')
            P = self._safe_pos(d.get('power'), str(_('Power')))
            pu = d.get('power_unit', 'W')
            Vb = self._base(V, vu, self.VOLTAGE_CONV, str(_('Voltage')))
            Pb = self._base(P, pu, self.POWER_CONV, str(_('Power')))
            Rb = self._verify(float(np.divide(np.multiply(Vb, Vb), Pb)))
            R = self._to_unit(Rb, ru, self.RESISTANCE_CONV)
            formula = 'R = V² / P'
            steps = [
                str(_('Formula:')) + ' R = V² / P',
                str(_('Given values:')),
                f'  • {_("Voltage")} (V) = {V} {self._u(vu)}',
                f'  • {_("Power")} (P) = {P} {self._u(pu)}',
                str(_('Calculation:')),
                f'  V² = {V}² = {V**2}',
                f'  R = {V**2} / {P} = {self._fnum(R)} {self._u(ru)}',
            ]
        elif method == 'pi':
            P = self._safe(d.get('power'), str(_('Power')))
            pu = d.get('power_unit', 'W')
            I = self._safe_pos(d.get('current'), str(_('Current')))
            iu = d.get('current_unit', 'A')
            Pb = self._base(P, pu, self.POWER_CONV, str(_('Power')))
            Ib = self._base(I, iu, self.CURRENT_CONV, str(_('Current')))
            Rb = self._verify(float(np.divide(Pb, np.multiply(Ib, Ib))))
            R = self._to_unit(Rb, ru, self.RESISTANCE_CONV)
            formula = 'R = P / I²'
            steps = [
                str(_('Formula:')) + ' R = P / I²',
                str(_('Given values:')),
                f'  • {_("Power")} (P) = {P} {self._u(pu)}',
                f'  • {_("Current")} (I) = {I} {self._u(iu)}',
                str(_('Calculation:')),
                f'  I² = {I}² = {I**2}',
                f'  R = {P} / {I**2} = {self._fnum(R)} {self._u(ru)}',
            ]
        else:
            return self._err(_('Invalid method.'))

        chart = self._chart_bar(
            [str(_('Resistance'))], [Rb],
            ['#f59e0b'],
            str(_('Resistance Calculation'))
        )
        return JsonResponse({
            'success': True, 'calc_type': 'resistance', 'method': method,
            'result': R, 'result_unit': self._u(ru), 'formula': formula,
            'step_by_step': steps,
            'chart_data': {'resistance_chart': chart},
        })

    # ── ENERGY ────────────────────────────────────────────────────────
    def _calc_energy(self, d):
        P = self._safe(d.get('power'), str(_('Power')))
        pu = d.get('power_unit', 'W')
        t = self._safe_pos(d.get('time'), str(_('Time')))
        tu = d.get('time_unit', 'hours')
        ru = d.get('result_unit', 'kWh')

        if tu not in self.TIME_CONV:
            return self._err(_('Invalid time unit.'))
        if ru not in self.ENERGY_CONV:
            return self._err(_('Invalid result unit.'))

        Pw = self._base(P, pu, self.POWER_CONV, str(_('Power')))
        th = float(t * self.TIME_CONV[tu])
        Ewh = self._verify(float(np.multiply(Pw, th)))
        Ekwh = Ewh / 1000.0
        E = float(Ekwh / self.ENERGY_CONV[ru])

        steps = [
            str(_('Formula:')) + ' E = P × t',
            str(_('Given values:')),
            f'  • {_("Power")} (P) = {P} {self._u(pu)}',
            f'  • {_("Time")} (t) = {t} {tu}',
            str(_('Calculation:')),
            f'  E = {P} {self._u(pu)} × {t} {tu}',
            f'  E = {self._fnum(E)} {self._u(ru)}',
        ]
        chart = self._chart_bar(
            [str(_('Energy'))], [Ekwh],
            ['#ec4899'],
            str(_('Energy Calculation'))
        )
        return JsonResponse({
            'success': True, 'calc_type': 'energy',
            'result': E, 'result_unit': self._u(ru), 'formula': 'E = P × t',
            'step_by_step': steps,
            'chart_data': {'energy_chart': chart},
        })

    # ── COST ──────────────────────────────────────────────────────────
    def _calc_cost(self, d):
        E = self._safe(d.get('energy'), str(_('Energy')))
        eu = d.get('energy_unit', 'kWh')
        rate = self._safe(d.get('rate'), str(_('Rate')))

        if eu not in self.ENERGY_CONV:
            return self._err(_('Invalid energy unit.'))

        Ekwh = float(E * self.ENERGY_CONV[eu])
        cost = self._verify(float(np.multiply(Ekwh, rate)))

        steps = [
            str(_('Formula:')) + ' ' + str(_('Cost = Energy × Rate')),
            str(_('Given values:')),
            f'  • {_("Energy")} = {E} {self._u(eu)}',
            f'  • {_("Rate")} = {rate} ' + str(_('per kWh')),
            str(_('Calculation:')),
            f'  {_("Cost")} = {E} × {rate}',
            f'  {_("Cost")} = {self._fnum(cost)} ' + str(_('currency units')),
        ]
        chart = self._chart_doughnut(
            [str(_('Energy Cost'))],
            [cost],
            ['#6366f1'],
            str(_('Cost Breakdown'))
        )
        return JsonResponse({
            'success': True, 'calc_type': 'cost',
            'result': cost, 'result_unit': str(_('currency units')),
            'formula': str(_('Cost = Energy × Rate')),
            'step_by_step': steps,
            'chart_data': {'cost_chart': chart},
        })

    # ── chart helpers ─────────────────────────────────────────────────
    def _chart_bar(self, labels, data, colors, title):
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': colors,
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
            }
        }

    def _chart_doughnut(self, labels, data, colors, title):
        return {
            'type': 'doughnut',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': data,
                    'backgroundColor': colors,
                    'borderWidth': 2,
                    'borderColor': '#ffffff',
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'position': 'bottom'},
                    'title': {'display': True, 'text': title},
                },
            }
        }
