from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DewPointCalculator(View):
    """
    Dew Point Calculator — Magnus Formula.

    Calc types
        • dew_point          → Td from T + RH
        • relative_humidity  → RH from T + Td
        • temperature        → T from Td + RH
        • convert            → °C ↔ °F ↔ K

    Magnus constants: A = 17.27, B = 237.7 °C
    Formula:  α = (A·T)/(B+T) + ln(RH/100)
              Td = (B·α) / (A − α)
    """
    template_name = 'other_calculators/dew_point_calculator.html'

    # Magnus constants
    A = 17.27
    B = 237.7  # °C

    UNIT_SYM = {'celsius': '°C', 'fahrenheit': '°F', 'kelvin': 'K'}

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Dew Point Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'dew_point')
            dispatch = {
                'dew_point':         self._calc_dew_point,
                'relative_humidity': self._calc_rh,
                'temperature':       self._calc_temperature,
                'convert':           self._calc_convert,
            }
            handler = dispatch.get(calc)
            if not handler:
                return self._err(_('Invalid calculation type.'))
            return handler(data)
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(e))
        except Exception:
            return self._err(_('An error occurred during calculation.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    def _fnum(self, v, dp=1):
        if v is None:
            return '0'
        return f'{v:,.{dp}f}'

    def _sym(self, u):
        return self.UNIT_SYM.get(u, '°C')

    def _req_float(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        return float(v)

    # ── temperature conversions ──────────────────────────────────────
    @staticmethod
    def _to_c(val, unit):
        if unit == 'fahrenheit':
            return float(np.multiply(np.subtract(val, 32.0), 5.0 / 9.0))
        if unit == 'kelvin':
            return float(np.subtract(val, 273.15))
        return float(val)

    @staticmethod
    def _from_c(c, unit):
        if unit == 'fahrenheit':
            return float(np.add(np.multiply(c, 1.8), 32.0))
        if unit == 'kelvin':
            return float(np.add(c, 273.15))
        return float(c)

    # ── Magnus core ──────────────────────────────────────────────────
    def _alpha(self, t_c, rh):
        """α = (A·T)/(B+T) + ln(RH/100)"""
        return float(
            np.add(
                np.divide(np.multiply(self.A, t_c), np.add(self.B, t_c)),
                np.log(np.divide(max(rh, 0.01), 100.0))
            )
        )

    def _dew_point_c(self, t_c, rh):
        """Td = (B·α) / (A − α)"""
        a = self._alpha(t_c, rh)
        denom = self.A - a
        if abs(denom) < 1e-12:
            raise ValueError(str(_('Cannot compute dew point for these inputs.')))
        return float(np.divide(np.multiply(self.B, a), denom))

    def _rh_from_t_td(self, t_c, td_c):
        """RH = 100 × exp( (A·Td)/(B+Td) − (A·T)/(B+T) )"""
        diff = (self.A * td_c) / (self.B + td_c) - (self.A * t_c) / (self.B + t_c)
        return float(np.clip(np.multiply(100.0, np.exp(diff)), 0, 100))

    def _temp_from_td_rh(self, td_c, rh):
        """Rearranged Magnus: T = (B·β)/(A−β), β = (A·Td)/(B+Td) − ln(RH/100)"""
        beta = (self.A * td_c) / (self.B + td_c) - float(np.log(max(rh, 0.01) / 100.0))
        denom = self.A - beta
        if abs(denom) < 1e-12:
            raise ValueError(str(_('Cannot compute temperature for these inputs.')))
        return float(np.divide(np.multiply(self.B, beta), denom))

    # ── comfort category ─────────────────────────────────────────────
    @staticmethod
    def _comfort(td_c):
        if td_c < 10:
            return str(_('Dry')), '#22c55e'
        elif td_c < 16:
            return str(_('Comfortable')), '#3b82f6'
        elif td_c < 18:
            return str(_('Slightly Humid')), '#eab308'
        elif td_c < 21:
            return str(_('Humid')), '#f97316'
        elif td_c < 24:
            return str(_('Very Humid')), '#ef4444'
        else:
            return str(_('Extremely Humid')), '#991b1b'

    # ── 1) CALCULATE DEW POINT ───────────────────────────────────────
    def _calc_dew_point(self, d):
        temp = self._req_float(d, 'temperature', str(_('Temperature')))
        rh = self._req_float(d, 'relative_humidity', str(_('Relative Humidity')))
        t_unit = d.get('temp_unit', 'celsius')
        r_unit = d.get('result_unit', 'celsius')

        if rh < 0 or rh > 100:
            raise ValueError(str(_('Relative humidity must be between 0 and 100 %.')))

        t_c = self._to_c(temp, t_unit)
        td_c = self._dew_point_c(t_c, rh)
        td_out = self._from_c(td_c, r_unit)
        comfort, color = self._comfort(td_c)

        ts = self._sym(t_unit)
        rs = self._sym(r_unit)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Temperature")} = {self._fnum(temp)} {ts}',
            f'  • {_("Relative Humidity")} = {self._fnum(rh)} %',
        ]
        if t_unit != 'celsius':
            steps += ['', str(_('Step 2: Convert temperature to °C')),
                       f'  T = {self._fnum(t_c)} °C']
        steps += [
            '', str(_('Step 3: Apply Magnus formula')),
            f'  α = (A×T)/(B+T) + ln(RH/100)',
            f'  α = ({self.A}×{self._fnum(t_c)})/({self.B}+{self._fnum(t_c)}) + ln({self._fnum(rh)}/100)',
            f'  α = {self._fnum(self._alpha(t_c, rh), 4)}',
            '',
            f'  Td = (B×α)/(A−α) = {self._fnum(td_c)} °C',
        ]
        if r_unit != 'celsius':
            steps += ['', str(_('Step 4: Convert result')),
                       f'  Td = {self._fnum(td_out)} {rs}']
        steps += ['', str(_('Step 5: Comfort level')),
                   f'  {comfort}']

        chart = self._dp_chart(t_c, td_c, rh, comfort, color)

        return JsonResponse({
            'success': True, 'calc_type': 'dew_point',
            'result': round(td_out, 1),
            'result_label': str(_('Dew Point')),
            'result_unit_symbol': rs,
            'result_c': round(td_c, 1),
            'comfort': comfort,
            'comfort_color': color,
            'formula': f'Td = {self._fnum(td_out)} {rs}',
            'step_by_step': steps,
            'chart_data': {'dp_chart': chart},
        })

    # ── 2) RELATIVE HUMIDITY ─────────────────────────────────────────
    def _calc_rh(self, d):
        temp = self._req_float(d, 'temperature', str(_('Temperature')))
        dp = self._req_float(d, 'dew_point', str(_('Dew Point')))
        t_unit = d.get('temp_unit', 'celsius')
        dp_unit = d.get('dew_point_unit', 'celsius')

        t_c = self._to_c(temp, t_unit)
        td_c = self._to_c(dp, dp_unit)

        if td_c > t_c:
            raise ValueError(str(_('Dew point cannot be greater than temperature.')))

        rh = self._rh_from_t_td(t_c, td_c)

        ts = self._sym(t_unit)
        ds = self._sym(dp_unit)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Temperature")} = {self._fnum(temp)} {ts}',
            f'  • {_("Dew Point")} = {self._fnum(dp)} {ds}',
        ]
        if t_unit != 'celsius' or dp_unit != 'celsius':
            steps += ['', str(_('Step 2: Convert to °C')),
                       f'  T = {self._fnum(t_c)} °C,  Td = {self._fnum(td_c)} °C']
        steps += [
            '', str(_('Step 3: Apply Magnus formula (rearranged for RH)')),
            f'  RH = 100 × exp( (A×Td)/(B+Td) − (A×T)/(B+T) )',
            f'  RH = 100 × exp( ({self.A}×{self._fnum(td_c)})/({self.B}+{self._fnum(td_c)}) − ({self.A}×{self._fnum(t_c)})/({self.B}+{self._fnum(t_c)}) )',
            f'  RH = {self._fnum(rh)} %',
        ]

        chart = self._bar_chart(
            [str(_('Temperature (°C)')), str(_('Dew Point (°C)')), str(_('Relative Humidity (%)'))],
            [t_c, td_c, rh],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(139,92,246,0.8)'],
            str(_('Relative Humidity Calculation'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'relative_humidity',
            'result': round(rh, 1),
            'result_label': str(_('Relative Humidity')),
            'result_unit_symbol': '%',
            'formula': f'RH = {self._fnum(rh)} %',
            'step_by_step': steps,
            'chart_data': {'dp_chart': chart},
        })

    # ── 3) TEMPERATURE FROM DEW POINT + RH ──────────────────────────
    def _calc_temperature(self, d):
        dp = self._req_float(d, 'dew_point', str(_('Dew Point')))
        rh = self._req_float(d, 'relative_humidity', str(_('Relative Humidity')))
        dp_unit = d.get('dew_point_unit', 'celsius')
        r_unit = d.get('result_unit', 'celsius')

        if rh <= 0 or rh > 100:
            raise ValueError(str(_('Relative humidity must be between 0 and 100 %.')))

        td_c = self._to_c(dp, dp_unit)
        t_c = self._temp_from_td_rh(td_c, rh)
        t_out = self._from_c(t_c, r_unit)
        rs = self._sym(r_unit)
        ds = self._sym(dp_unit)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Dew Point")} = {self._fnum(dp)} {ds}',
            f'  • {_("Relative Humidity")} = {self._fnum(rh)} %',
        ]
        if dp_unit != 'celsius':
            steps += ['', str(_('Step 2: Convert dew point to °C')),
                       f'  Td = {self._fnum(td_c)} °C']
        steps += [
            '', str(_('Step 3: Apply rearranged Magnus formula')),
            f'  β = (A×Td)/(B+Td) − ln(RH/100)',
            f'  T = (B×β)/(A−β) = {self._fnum(t_c)} °C',
        ]
        if r_unit != 'celsius':
            steps += ['', str(_('Step 4: Convert result')),
                       f'  T = {self._fnum(t_out)} {rs}']

        chart = self._bar_chart(
            [str(_('Dew Point (°C)')), str(_('Humidity (%)')), str(_('Temperature (°C)'))],
            [td_c, rh, t_c],
            ['rgba(16,185,129,0.8)', 'rgba(139,92,246,0.8)', 'rgba(59,130,246,0.8)'],
            str(_('Temperature from Dew Point'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'temperature',
            'result': round(t_out, 1),
            'result_label': str(_('Temperature')),
            'result_unit_symbol': rs,
            'result_c': round(t_c, 1),
            'formula': f'T = {self._fnum(t_out)} {rs}',
            'step_by_step': steps,
            'chart_data': {'dp_chart': chart},
        })

    # ── 4) CONVERT TEMPERATURE ───────────────────────────────────────
    def _calc_convert(self, d):
        value = self._req_float(d, 'value', str(_('Temperature')))
        fu = d.get('from_unit', 'celsius')
        tu = d.get('to_unit', 'celsius')

        c_val = self._to_c(value, fu)
        result = self._from_c(c_val, tu)
        fs = self._sym(fu)
        ts_sym = self._sym(tu)

        steps = [
            str(_('Step 1: Given value')),
            f'  • {self._fnum(value)} {fs}',
        ]
        if fu != tu:
            steps += [
                '', str(_('Step 2: Convert')),
                f'  → {self._fnum(c_val)} °C' if fu != 'celsius' else '',
                f'  → {self._fnum(result)} {ts_sym}',
            ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': round(result, 1),
            'result_label': str(_('Converted Temperature')),
            'result_unit_symbol': ts_sym,
            'formula': f'{self._fnum(value)} {fs} = {self._fnum(result)} {ts_sym}',
            'step_by_step': [s for s in steps if s],
            'chart_data': None,
        })

    # ── chart helpers ────────────────────────────────────────────────
    def _bar_chart(self, labels, data, colors, title):
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': [round(v, 1) for v in data],
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
                    'y': {'beginAtZero': True},
                },
            },
        }

    def _dp_chart(self, t_c, td_c, rh, comfort, color):
        """Horizontal bar comparing T, Td, and comfort thresholds."""
        labels = [
            str(_('Air Temp')),
            str(_('Dew Point')),
            str(_('Dry (<10°C)')),
            str(_('Comfortable')),
            str(_('Humid (18°C)')),
            str(_('Very Humid')),
        ]
        data = [t_c, td_c, 10, 16, 18, 24]
        colors = [
            'rgba(59,130,246,0.85)',
            f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.85)' if color.startswith('#') else 'rgba(34,197,94,0.85)',
            'rgba(34,197,94,0.5)',
            'rgba(59,130,246,0.5)',
            'rgba(249,115,22,0.5)',
            'rgba(239,68,68,0.5)',
        ]
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': '°C',
                    'data': [round(v, 1) for v in data],
                    'backgroundColor': colors,
                    'borderWidth': 0,
                    'borderRadius': 6,
                }]
            },
            'options': {
                'indexAxis': 'y',
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': f'{comfort} — Td = {self._fnum(td_c)} °C'},
                },
                'scales': {
                    'x': {'title': {'display': True, 'text': '°C'}},
                },
            },
        }
