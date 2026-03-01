from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HeatIndexCalculator(View):
    """
    Heat Index Calculator — Feels-Like Temperature.

    Calc types:
        • heat_index          → HI from temperature + humidity (Rothfusz)
        • temperature         → T from HI + humidity (Newton iteration)
        • humidity            → RH from HI + temperature (Newton iteration)
        • convert_temperature → °F ↔ °C

    Uses NumPy for arithmetic.  All user-facing strings wrapped with gettext_lazy.
    """
    template_name = 'other_calculators/heat_index_calculator.html'

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Heat Index Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'heat_index')
            dispatch = {
                'heat_index':          self._calc_heat_index,
                'temperature':         self._calc_temperature,
                'humidity':            self._calc_humidity,
                'convert_temperature': self._calc_convert,
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

    def _req_float(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        return float(v)

    @staticmethod
    def _to_f(c):
        return float(np.add(np.multiply(c, 1.8), 32.0))

    @staticmethod
    def _to_c(f):
        return float(np.multiply(np.subtract(f, 32.0), 5.0 / 9.0))

    # ── Rothfusz regression ──────────────────────────────────────────
    def _rothfusz(self, T, RH):
        """Return heat index in °F using the NWS Rothfusz equation + adjustments."""
        hi = (
            -42.379
            + 2.04901523 * T
            + 10.14333127 * RH
            - 0.22475541 * T * RH
            - 6.83783e-3 * T ** 2
            - 5.481717e-2 * RH ** 2
            + 1.22874e-3 * T ** 2 * RH
            + 8.5282e-4 * T * RH ** 2
            - 1.99e-6 * T ** 2 * RH ** 2
        )
        # Low-humidity adjustment
        if RH < 13 and 80 <= T <= 112:
            adj = ((13 - RH) / 4.0) * np.sqrt((17 - abs(T - 95)) / 17.0)
            hi -= float(adj)
        # High-humidity adjustment
        if RH > 85 and 80 <= T <= 87:
            adj = ((RH - 85) / 10.0) * ((87 - T) / 5.0)
            hi += float(adj)
        return float(hi)

    # ── category ─────────────────────────────────────────────────────
    @staticmethod
    def _category(hi_f):
        if hi_f < 80:
            return str(_('Safe')), str(_('Low')), '#22c55e'
        elif hi_f < 90:
            return str(_('Caution')), str(_('Moderate')), '#eab308'
        elif hi_f < 103:
            return str(_('Extreme Caution')), str(_('High')), '#f97316'
        elif hi_f < 125:
            return str(_('Danger')), str(_('Very High')), '#ef4444'
        else:
            return str(_('Extreme Danger')), str(_('Extreme')), '#991b1b'

    # ── 1) CALCULATE HEAT INDEX ──────────────────────────────────────
    def _calc_heat_index(self, d):
        temp = self._req_float(d, 'temperature', str(_('Temperature')))
        hum = self._req_float(d, 'humidity', str(_('Relative Humidity')))
        unit = d.get('temp_unit', 'fahrenheit')

        temp_f = temp if unit == 'fahrenheit' else self._to_f(temp)
        if temp_f < 80:
            raise ValueError(str(_('Temperature must be ≥ 80 °F (27 °C) for heat index.')))
        if hum < 0 or hum > 100:
            raise ValueError(str(_('Relative humidity must be between 0 and 100 %.')))
        if hum < 40:
            raise ValueError(str(_('Relative humidity must be ≥ 40 % for heat index.')))

        hi_f = self._rothfusz(temp_f, hum)
        hi_c = self._to_c(hi_f)
        cat_name, risk, cat_color = self._category(hi_f)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Temperature")} = {temp} °{"F" if unit == "fahrenheit" else "C"}',
            f'  • {_("Relative Humidity")} = {hum} %',
        ]
        if unit == 'celsius':
            steps += [
                '', str(_('Step 2: Convert to Fahrenheit')),
                f'  °F = ({temp} × 9/5) + 32 = {self._fnum(temp_f)} °F',
            ]
        steps += [
            '', str(_('Step 3: Apply Rothfusz equation')),
            '  HI = −42.379 + 2.049×T + 10.143×RH − 0.2248×T×RH …',
            f'  T = {self._fnum(temp_f)} °F,  RH = {hum} %',
            f'  HI = {self._fnum(hi_f)} °F  ({self._fnum(hi_c)} °C)',
            '', str(_('Step 4: Risk category')),
            f'  {cat_name} — {risk} {_("risk")}',
        ]

        chart = self._hi_gauge_chart(hi_f, cat_name, cat_color)

        return JsonResponse({
            'success': True, 'calc_type': 'heat_index',
            'result': round(hi_f, 1),
            'result_c': round(hi_c, 1),
            'result_label': str(_('Heat Index')),
            'result_unit_symbol': '°F',
            'category': cat_name,
            'risk_level': risk,
            'category_color': cat_color,
            'formula': f'HI({self._fnum(temp_f)}°F, {hum}%) = {self._fnum(hi_f)}°F',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 2) TEMPERATURE FROM HEAT INDEX ───────────────────────────────
    def _calc_temperature(self, d):
        hi_input = self._req_float(d, 'heat_index', str(_('Heat Index')))
        hum = self._req_float(d, 'humidity', str(_('Relative Humidity')))
        unit = d.get('temp_unit', 'fahrenheit')

        hi_f = hi_input if unit == 'fahrenheit' else self._to_f(hi_input)
        if hi_f < 80:
            raise ValueError(str(_('Heat index must be ≥ 80 °F (27 °C).')))
        if hum < 40 or hum > 100:
            raise ValueError(str(_('Relative humidity must be between 40 and 100 %.')))

        # Newton iteration
        T = 90.0
        for _i in range(200):
            f_val = self._rothfusz(T, hum) - hi_f
            dT = 0.05
            f_prime = (self._rothfusz(T + dT, hum) - self._rothfusz(T - dT, hum)) / (2 * dT)
            if abs(f_prime) < 1e-12:
                break
            T -= f_val / f_prime
            T = max(80, min(T, 200))
            if abs(f_val) < 0.01:
                break

        temp_f = round(T, 1)
        temp_c = round(self._to_c(temp_f), 1)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Heat Index")} = {hi_input} °{"F" if unit=="fahrenheit" else "C"}',
            f'  • {_("Relative Humidity")} = {hum} %',
        ]
        if unit == 'celsius':
            steps += ['', str(_('Step 2: Convert HI to Fahrenheit')),
                       f'  HI = {self._fnum(hi_f)} °F']
        steps += [
            '', str(_('Step 3: Solve Rothfusz equation for T (iterative)')),
            f'  {_("Temperature")} = {temp_f} °F  ({temp_c} °C)',
        ]

        chart = self._bar_chart(
            [str(_('Heat Index (°F)')), str(_('Humidity (%)')), str(_('Temperature (°F)'))],
            [hi_f, hum, temp_f],
            ['rgba(239,68,68,0.8)', 'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)'],
            str(_('Temperature from Heat Index'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'temperature',
            'result': temp_f,
            'result_c': temp_c,
            'result_label': str(_('Temperature')),
            'result_unit_symbol': '°F',
            'formula': f'T = {temp_f} °F  ({temp_c} °C)',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 3) HUMIDITY FROM HEAT INDEX ──────────────────────────────────
    def _calc_humidity(self, d):
        hi_input = self._req_float(d, 'heat_index', str(_('Heat Index')))
        temp = self._req_float(d, 'temperature', str(_('Temperature')))
        unit = d.get('temp_unit', 'fahrenheit')

        hi_f = hi_input if unit == 'fahrenheit' else self._to_f(hi_input)
        temp_f = temp if unit == 'fahrenheit' else self._to_f(temp)
        if hi_f < 80:
            raise ValueError(str(_('Heat index must be ≥ 80 °F (27 °C).')))
        if temp_f < 80:
            raise ValueError(str(_('Temperature must be ≥ 80 °F (27 °C).')))

        # Newton iteration
        RH = 60.0
        for _i in range(200):
            f_val = self._rothfusz(temp_f, RH) - hi_f
            dRH = 0.05
            f_prime = (self._rothfusz(temp_f, RH + dRH) - self._rothfusz(temp_f, RH - dRH)) / (2 * dRH)
            if abs(f_prime) < 1e-12:
                break
            RH -= f_val / f_prime
            RH = max(0, min(RH, 100))
            if abs(f_val) < 0.01:
                break

        humidity = round(RH, 1)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Heat Index")} = {hi_input} °{"F" if unit=="fahrenheit" else "C"}',
            f'  • {_("Temperature")} = {temp} °{"F" if unit=="fahrenheit" else "C"}',
        ]
        if unit == 'celsius':
            steps += ['', str(_('Step 2: Convert to Fahrenheit')),
                       f'  HI = {self._fnum(hi_f)} °F,  T = {self._fnum(temp_f)} °F']
        steps += [
            '', str(_('Step 3: Solve Rothfusz equation for RH (iterative)')),
            f'  {_("Relative Humidity")} = {humidity} %',
        ]

        chart = self._bar_chart(
            [str(_('Heat Index (°F)')), str(_('Temperature (°F)')), str(_('Humidity (%)'))],
            [hi_f, temp_f, humidity],
            ['rgba(239,68,68,0.8)', 'rgba(16,185,129,0.8)', 'rgba(59,130,246,0.8)'],
            str(_('Humidity from Heat Index'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'humidity',
            'result': humidity,
            'result_label': str(_('Relative Humidity')),
            'result_unit_symbol': '%',
            'formula': f'RH = {humidity} %',
            'step_by_step': steps,
            'chart_data': {'hp_chart': chart},
        })

    # ── 4) CONVERT TEMPERATURE ───────────────────────────────────────
    def _calc_convert(self, d):
        value = self._req_float(d, 'value', str(_('Temperature')))
        fu = d.get('from_unit', 'fahrenheit')
        tu = d.get('to_unit', 'celsius')

        if fu == 'fahrenheit' and tu == 'celsius':
            result = self._to_c(value)
        elif fu == 'celsius' and tu == 'fahrenheit':
            result = self._to_f(value)
        else:
            result = value

        from_sym = '°F' if fu == 'fahrenheit' else '°C'
        to_sym = '°F' if tu == 'fahrenheit' else '°C'

        steps = [
            str(_('Step 1: Given value')),
            f'  • {self._fnum(value)} {from_sym}',
        ]
        if fu != tu:
            formula = '°C = (°F − 32) × 5/9' if tu == 'celsius' else '°F = (°C × 9/5) + 32'
            steps += [
                '', str(_('Step 2: Apply formula')),
                f'  {formula}',
                f'  = {self._fnum(result)} {to_sym}',
            ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert_temperature',
            'result': round(result, 1),
            'result_label': str(_('Converted Temperature')),
            'result_unit_symbol': to_sym,
            'formula': f'{self._fnum(value)} {from_sym} = {self._fnum(result)} {to_sym}',
            'step_by_step': steps,
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
                    'y': {'beginAtZero': True},
                },
            },
        }

    def _hi_gauge_chart(self, hi_f, cat_name, cat_color):
        """Horizontal bar chart comparing HI to category thresholds."""
        labels = [
            str(_('Caution (80)')),
            str(_('Ext. Caution (90)')),
            str(_('Danger (103)')),
            str(_('Ext. Danger (125)')),
            str(_('Your Result')),
        ]
        data = [80, 90, 103, 125, hi_f]
        colors = [
            'rgba(234,179,8,0.7)', 'rgba(249,115,22,0.7)',
            'rgba(239,68,68,0.7)', 'rgba(153,27,27,0.7)',
            cat_color.replace('#', 'rgba(') and f'rgba({int(cat_color[1:3],16)},{int(cat_color[3:5],16)},{int(cat_color[5:7],16)},0.9)',
        ]
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Heat Index (°F)')),
                    'data': data,
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
                    'title': {'display': True, 'text': f'{cat_name} — {self._fnum(hi_f)} °F'},
                },
                'scales': {
                    'x': {'beginAtZero': True, 'title': {'display': True, 'text': '°F'}},
                },
            },
        }
