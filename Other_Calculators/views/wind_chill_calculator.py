from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class WindChillCalculator(View):
    """
    Wind Chill Calculator — NWS Wind Chill Index.

    Calc types
        • wind_chill       → WC from temperature + wind speed
        • from_wind_chill  → T from WC + wind speed (algebraic)
        • wind_speed       → V from WC + T (binary-search)

    NWS formula (°F, mph):
        WC = 35.74 + 0.6215·T − 35.75·V^0.16 + 0.4275·T·V^0.16

    Valid when T ≤ 50 °F and V ≥ 3 mph.
    """
    template_name = 'other_calculators/wind_chill_calculator.html'

    WIND_SYM = {'mph': 'mph', 'kmh': 'km/h', 'ms': 'm/s'}

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Wind Chill Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'wind_chill')
            dispatch = {
                'wind_chill':      self._calc_wind_chill,
                'from_wind_chill': self._calc_from_wind_chill,
                'wind_speed':      self._calc_wind_speed,
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

    # ── unit conversions ─────────────────────────────────────────────
    @staticmethod
    def _to_f(c):
        return float(np.add(np.multiply(c, 1.8), 32.0))

    @staticmethod
    def _to_c(f):
        return float(np.multiply(np.subtract(f, 32.0), 5.0 / 9.0))

    @staticmethod
    def _to_mph(val, unit):
        if unit == 'kmh':
            return val / 1.60934
        if unit == 'ms':
            return val / 0.44704
        return val

    @staticmethod
    def _from_mph(mph, unit):
        if unit == 'kmh':
            return mph * 1.60934
        if unit == 'ms':
            return mph * 0.44704
        return mph

    # ── NWS Wind Chill Index (°F, mph) ───────────────────────────────
    def _wci(self, T, V):
        """WC = 35.74 + 0.6215·T − 35.75·V^0.16 + 0.4275·T·V^0.16"""
        if V < 3 or T > 50:
            return T
        vp = V ** 0.16
        return 35.74 + 0.6215 * T - 35.75 * vp + 0.4275 * T * vp

    # ── risk category ────────────────────────────────────────────────
    @staticmethod
    def _category(wc_f):
        if wc_f >= 32:
            return str(_('Little Danger')), str(_('Low')), '#22c55e', str(_('Properly clothed persons are in little danger.'))
        elif wc_f >= 0:
            return str(_('Caution')), str(_('Moderate')), '#eab308', str(_('Risk of hypothermia with prolonged exposure.'))
        elif wc_f >= -20:
            return str(_('Danger')), str(_('High')), '#f97316', str(_('Exposed skin can freeze in 10 minutes.'))
        elif wc_f >= -40:
            return str(_('High Danger')), str(_('Very High')), '#ef4444', str(_('Exposed skin can freeze in 5 minutes.'))
        else:
            return str(_('Extreme Danger')), str(_('Extreme')), '#991b1b', str(_('Exposed skin can freeze in under 2 minutes.'))

    # ── 1) WIND CHILL ────────────────────────────────────────────────
    def _calc_wind_chill(self, d):
        temp = self._req_float(d, 'temperature', str(_('Temperature')))
        wspd = self._req_float(d, 'wind_speed', str(_('Wind Speed')))
        tu = d.get('temp_unit', 'F')
        wu = d.get('wind_unit', 'mph')

        temp_f = temp if tu == 'F' else self._to_f(temp)
        wind_mph = self._to_mph(wspd, wu)

        if wind_mph < 0:
            raise ValueError(str(_('Wind speed must be non-negative.')))

        wc_f = self._wci(temp_f, wind_mph)
        wc_out = wc_f if tu == 'F' else self._to_c(wc_f)
        cat_name, risk, color, desc = self._category(wc_f)

        tsym = '°F' if tu == 'F' else '°C'
        wsym = self.WIND_SYM.get(wu, wu)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Temperature")} = {self._fnum(temp)} {tsym}',
            f'  • {_("Wind Speed")} = {self._fnum(wspd)} {wsym}',
        ]
        if tu == 'C':
            steps += ['', str(_('Step 2: Convert to °F and mph')),
                       f'  T = {self._fnum(temp_f)} °F']
        if wu != 'mph':
            steps.append(f'  V = {self._fnum(wind_mph)} mph')

        vp = wind_mph ** 0.16 if wind_mph >= 3 else 0
        steps += [
            '', str(_('Step 3: Apply NWS Wind Chill formula')),
            '  WC = 35.74 + 0.6215×T − 35.75×V^0.16 + 0.4275×T×V^0.16',
            f'  T = {self._fnum(temp_f)} °F,  V = {self._fnum(wind_mph)} mph',
        ]
        if wind_mph >= 3 and temp_f <= 50:
            steps.append(f'  V^0.16 = {self._fnum(vp, 4)}')
            steps.append(f'  WC = {self._fnum(wc_f)} °F  ({self._fnum(self._to_c(wc_f))} °C)')
        else:
            steps.append(f'  {_("Wind chill equals air temperature (outside valid range)")}')

        steps += [
            '', str(_('Step 4: Risk category')),
            f'  {cat_name} — {desc}',
        ]

        chart = self._wc_line_chart(temp_f, tu)

        return JsonResponse({
            'success': True, 'calc_type': 'wind_chill',
            'result': round(wc_out, 1),
            'result_label': str(_('Wind Chill')),
            'result_unit_symbol': tsym,
            'result_f': round(wc_f, 1),
            'category': cat_name,
            'risk_level': risk,
            'category_color': color,
            'category_desc': desc,
            'formula': f'WC = {self._fnum(wc_out)} {tsym}',
            'step_by_step': steps,
            'chart_data': {'wc_chart': chart},
        })

    # ── 2) TEMPERATURE FROM WIND CHILL ───────────────────────────────
    def _calc_from_wind_chill(self, d):
        wc_in = self._req_float(d, 'wind_chill', str(_('Wind Chill')))
        wspd = self._req_float(d, 'wind_speed', str(_('Wind Speed')))
        tu = d.get('temp_unit', 'F')
        wu = d.get('wind_unit', 'mph')

        wc_f = wc_in if tu == 'F' else self._to_f(wc_in)
        wind_mph = self._to_mph(wspd, wu)

        if wind_mph < 3:
            raise ValueError(str(_('Wind speed must be ≥ 3 mph for wind chill.')))

        # Algebraic: T = (WC − 35.74 + 35.75·V^0.16) / (0.6215 + 0.4275·V^0.16)
        vp = wind_mph ** 0.16
        temp_f = (wc_f - 35.74 + 35.75 * vp) / (0.6215 + 0.4275 * vp)
        temp_out = temp_f if tu == 'F' else self._to_c(temp_f)

        tsym = '°F' if tu == 'F' else '°C'
        wsym = self.WIND_SYM.get(wu, wu)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Wind Chill")} = {self._fnum(wc_in)} {tsym}',
            f'  • {_("Wind Speed")} = {self._fnum(wspd)} {wsym}',
        ]
        if tu == 'C':
            steps += ['', str(_('Step 2: Convert WC to °F')),
                       f'  WC = {self._fnum(wc_f)} °F']
        if wu != 'mph':
            steps.append(f'  V = {self._fnum(wind_mph)} mph')
        steps += [
            '', str(_('Step 3: Solve for T')),
            '  T = (WC − 35.74 + 35.75·V^0.16) / (0.6215 + 0.4275·V^0.16)',
            f'  V^0.16 = {self._fnum(vp, 4)}',
            f'  T = {self._fnum(temp_f)} °F  ({self._fnum(self._to_c(temp_f))} °C)',
        ]

        chart = self._bar_chart(
            [str(_('Wind Chill (°F)')), str(_('Wind Speed (mph)')), str(_('Temperature (°F)'))],
            [wc_f, wind_mph, temp_f],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(239,68,68,0.8)'],
            str(_('Temperature from Wind Chill'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'from_wind_chill',
            'result': round(temp_out, 1),
            'result_label': str(_('Temperature')),
            'result_unit_symbol': tsym,
            'formula': f'T = {self._fnum(temp_out)} {tsym}',
            'step_by_step': steps,
            'chart_data': {'wc_chart': chart},
        })

    # ── 3) WIND SPEED FROM WIND CHILL ────────────────────────────────
    def _calc_wind_speed(self, d):
        wc_in = self._req_float(d, 'wind_chill', str(_('Wind Chill')))
        temp = self._req_float(d, 'temperature', str(_('Temperature')))
        tu = d.get('temp_unit', 'F')
        wu = d.get('wind_unit', 'mph')

        wc_f = wc_in if tu == 'F' else self._to_f(wc_in)
        temp_f = temp if tu == 'F' else self._to_f(temp)

        if temp_f > 50:
            raise ValueError(str(_('Temperature must be ≤ 50 °F (10 °C) for wind chill.')))

        # Binary search for V
        lo, hi = 3.0, 200.0
        for _i in range(200):
            mid = (lo + hi) / 2.0
            calc_wc = self._wci(temp_f, mid)
            if abs(calc_wc - wc_f) < 0.01:
                break
            if calc_wc > wc_f:
                lo = mid
            else:
                hi = mid
        wind_mph = (lo + hi) / 2.0
        wind_out = self._from_mph(wind_mph, wu)

        tsym = '°F' if tu == 'F' else '°C'
        wsym = self.WIND_SYM.get(wu, wu)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Wind Chill")} = {self._fnum(wc_in)} {tsym}',
            f'  • {_("Temperature")} = {self._fnum(temp)} {tsym}',
        ]
        if tu == 'C':
            steps += ['', str(_('Step 2: Convert to °F')),
                       f'  WC = {self._fnum(wc_f)} °F,  T = {self._fnum(temp_f)} °F']
        steps += [
            '', str(_('Step 3: Solve for V (iterative)')),
            f'  V = {self._fnum(wind_mph)} mph',
        ]
        if wu != 'mph':
            steps.append(f'  V = {self._fnum(wind_out)} {wsym}')

        chart = self._bar_chart(
            [str(_('Wind Chill (°F)')), str(_('Temperature (°F)')), str(_('Wind Speed (mph)'))],
            [wc_f, temp_f, wind_mph],
            ['rgba(59,130,246,0.8)', 'rgba(239,68,68,0.8)', 'rgba(16,185,129,0.8)'],
            str(_('Wind Speed from Wind Chill'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'wind_speed',
            'result': round(wind_out, 1),
            'result_label': str(_('Wind Speed')),
            'result_unit_symbol': wsym,
            'formula': f'V = {self._fnum(wind_out)} {wsym}',
            'step_by_step': steps,
            'chart_data': {'wc_chart': chart},
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
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': title}},
                'scales': {'y': {'beginAtZero': False}},
            },
        }

    def _wc_line_chart(self, temp_f, tu):
        """Line chart: wind chill vs wind speed at the given temperature."""
        speeds = list(range(3, 61, 3))
        wcs = [self._wci(temp_f, s) for s in speeds]
        if tu == 'C':
            wcs = [self._to_c(w) for w in wcs]
        tsym = '°F' if tu == 'F' else '°C'
        return {
            'type': 'line',
            'data': {
                'labels': [f'{s} mph' for s in speeds],
                'datasets': [{
                    'label': f'{_("Wind Chill")} ({tsym})',
                    'data': [round(w, 1) for w in wcs],
                    'borderColor': 'rgba(59,130,246,1)',
                    'backgroundColor': 'rgba(59,130,246,0.1)',
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 3,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True, 'position': 'top'},
                    'title': {'display': True, 'text': f'{_("Wind Chill at")} {self._fnum(temp_f)} °F'},
                },
                'scales': {
                    'x': {'title': {'display': True, 'text': str(_('Wind Speed (mph)'))}},
                    'y': {'title': {'display': True, 'text': f'{_("Wind Chill")} ({tsym})'}},
                },
            },
        }
