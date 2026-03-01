from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SpeedCalculator(View):
    """
    Speed Calculator — speed, distance, time, unit conversion.

    Calc types
        • speed    → v = d / t
        • distance → d = v × t
        • time     → t = d / v
        • convert  → speed unit conversion

    Base units: m/s (speed), metres (distance), seconds (time).
    """
    template_name = 'other_calculators/speed_calculator.html'

    # ── conversion factors ────────────────────────────────────────────
    # speed → m/s
    SPD = {
        'm_s': 1.0, 'km_h': 0.277778, 'mph': 0.44704,
        'knots': 0.514444, 'ft_s': 0.3048,
    }
    SPD_LBL = {'m_s': 'm/s', 'km_h': 'km/h', 'mph': 'mph', 'knots': 'knots', 'ft_s': 'ft/s'}

    # distance → metres
    DIST = {
        'meters': 1.0, 'kilometers': 1000.0, 'miles': 1609.34,
        'feet': 0.3048, 'yards': 0.9144,
    }
    DIST_LBL = {'meters': 'm', 'kilometers': 'km', 'miles': 'mi', 'feet': 'ft', 'yards': 'yd'}

    # time → seconds
    TIME = {'seconds': 1.0, 'minutes': 60.0, 'hours': 3600.0}
    TIME_LBL = {'seconds': 's', 'minutes': 'min', 'hours': 'h'}

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Speed Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'speed')
            dispatch = {
                'speed':    self._calc_speed,
                'distance': self._calc_distance,
                'time':     self._calc_time,
                'convert':  self._calc_convert,
            }
            handler = dispatch.get(ct)
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

    def _f(self, v, dp=4):
        return f'{v:,.{dp}f}'

    def _sl(self, u): return self.SPD_LBL.get(u, u)
    def _dl(self, u): return self.DIST_LBL.get(u, u)
    def _tl(self, u): return self.TIME_LBL.get(u, u)

    def _req_pos(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        f = float(v)
        if f <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        return f

    def _req_nn(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        f = float(v)
        if f < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        return f

    def _safe(self, v):
        if math.isinf(v) or math.isnan(v):
            raise ValueError(str(_('Invalid calculation result.')))
        return v

    # ── 1) SPEED ─────────────────────────────────────────────────────
    def _calc_speed(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        time = self._req_pos(d, 'time', str(_('Time')))
        du = d.get('distance_unit', 'kilometers')
        tu = d.get('time_unit', 'hours')
        ru = d.get('result_unit', 'km_h')

        dist_m = dist * self.DIST[du]
        time_s = time * self.TIME[tu]
        spd_ms = self._safe(dist_m / time_s)
        result = self._safe(spd_ms / self.SPD[ru])

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist, 2)} {self._dl(du)}',
            f'  • {_("Time")} = {self._f(time, 2)} {self._tl(tu)}',
            '', str(_('Step 2: Convert to base units')),
            f'  {_("Distance")} = {self._f(dist_m, 2)} m',
            f'  {_("Time")} = {self._f(time_s, 2)} s',
            '', str(_('Step 3: Calculate speed')),
            f'  v = d / t = {self._f(dist_m, 2)} / {self._f(time_s, 2)} = {self._f(spd_ms)} m/s',
        ]
        if ru != 'm_s':
            steps += ['', str(_('Step 4: Convert to desired unit')),
                       f'  v = {self._f(result)} {self._sl(ru)}']

        # Multi-unit chart
        chart = self._speed_chart(spd_ms)

        return JsonResponse({
            'success': True, 'calc_type': 'speed',
            'result': round(result, 4),
            'result_label': str(_('Speed')),
            'result_unit_symbol': self._sl(ru),
            'formula': f'v = {self._f(dist, 2)} {self._dl(du)} / {self._f(time, 2)} {self._tl(tu)} = {self._f(result)} {self._sl(ru)}',
            'speed_m_s': round(spd_ms, 4),
            'step_by_step': steps,
            'chart_data': {'spd_chart': chart},
        })

    # ── 2) DISTANCE ──────────────────────────────────────────────────
    def _calc_distance(self, d):
        spd = self._req_pos(d, 'speed', str(_('Speed')))
        time = self._req_pos(d, 'time', str(_('Time')))
        su = d.get('speed_unit', 'km_h')
        tu = d.get('time_unit', 'hours')
        ru = d.get('result_unit', 'kilometers')

        spd_ms = spd * self.SPD[su]
        time_s = time * self.TIME[tu]
        dist_m = self._safe(spd_ms * time_s)
        result = self._safe(dist_m / self.DIST[ru])

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Speed")} = {self._f(spd, 2)} {self._sl(su)}',
            f'  • {_("Time")} = {self._f(time, 2)} {self._tl(tu)}',
            '', str(_('Step 2: Convert to base units')),
            f'  {_("Speed")} = {self._f(spd_ms)} m/s',
            f'  {_("Time")} = {self._f(time_s, 2)} s',
            '', str(_('Step 3: Calculate distance')),
            f'  d = v × t = {self._f(spd_ms)} × {self._f(time_s, 2)} = {self._f(dist_m, 2)} m',
        ]
        if ru != 'meters':
            steps += ['', str(_('Step 4: Convert to desired unit')),
                       f'  d = {self._f(result)} {self._dl(ru)}']

        chart = self._bar(
            [str(_('Distance'))], [result],
            ['rgba(16,185,129,0.8)'],
            f'{_("Distance")} ({self._dl(ru)})')

        return JsonResponse({
            'success': True, 'calc_type': 'distance',
            'result': round(result, 4),
            'result_label': str(_('Distance')),
            'result_unit_symbol': self._dl(ru),
            'formula': f'd = {self._f(spd, 2)} {self._sl(su)} × {self._f(time, 2)} {self._tl(tu)} = {self._f(result)} {self._dl(ru)}',
            'distance_m': round(dist_m, 4),
            'step_by_step': steps,
            'chart_data': {'spd_chart': chart},
        })

    # ── 3) TIME ──────────────────────────────────────────────────────
    def _calc_time(self, d):
        spd = self._req_pos(d, 'speed', str(_('Speed')))
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        su = d.get('speed_unit', 'km_h')
        du = d.get('distance_unit', 'kilometers')
        ru = d.get('result_unit', 'hours')

        spd_ms = spd * self.SPD[su]
        dist_m = dist * self.DIST[du]
        time_s = self._safe(dist_m / spd_ms)
        result = self._safe(time_s / self.TIME[ru])

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Speed")} = {self._f(spd, 2)} {self._sl(su)}',
            f'  • {_("Distance")} = {self._f(dist, 2)} {self._dl(du)}',
            '', str(_('Step 2: Convert to base units')),
            f'  {_("Speed")} = {self._f(spd_ms)} m/s',
            f'  {_("Distance")} = {self._f(dist_m, 2)} m',
            '', str(_('Step 3: Calculate time')),
            f'  t = d / v = {self._f(dist_m, 2)} / {self._f(spd_ms)} = {self._f(time_s, 2)} s',
        ]
        if ru != 'seconds':
            steps += ['', str(_('Step 4: Convert to desired unit')),
                       f'  t = {self._f(result)} {self._tl(ru)}']

        chart = self._bar(
            [str(_('Time'))], [result],
            ['rgba(234,179,8,0.8)'],
            f'{_("Time")} ({self._tl(ru)})')

        return JsonResponse({
            'success': True, 'calc_type': 'time',
            'result': round(result, 4),
            'result_label': str(_('Time')),
            'result_unit_symbol': self._tl(ru),
            'formula': f't = {self._f(dist, 2)} {self._dl(du)} / {self._f(spd, 2)} {self._sl(su)} = {self._f(result)} {self._tl(ru)}',
            'time_s': round(time_s, 4),
            'step_by_step': steps,
            'chart_data': {'spd_chart': chart},
        })

    # ── 4) CONVERT ───────────────────────────────────────────────────
    def _calc_convert(self, d):
        spd = self._req_nn(d, 'speed', str(_('Speed')))
        fu = d.get('from_unit', 'km_h')
        tu = d.get('to_unit', 'mph')

        spd_ms = spd * self.SPD[fu]
        result = self._safe(spd_ms / self.SPD[tu])

        steps = [
            str(_('Step 1: Given value')),
            f'  • {self._f(spd)} {self._sl(fu)}',
            '', str(_('Step 2: Convert to m/s')),
            f'  {self._f(spd)} × {self.SPD[fu]} = {self._f(spd_ms)} m/s',
            '', str(_('Step 3: Convert to {unit}').format(unit=self._sl(tu))),
            f'  {self._f(spd_ms)} / {self.SPD[tu]} = {self._f(result)} {self._sl(tu)}',
        ]

        # Show all conversions
        chart = self._speed_chart(spd_ms)

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': round(result, 4),
            'result_label': str(_('Converted Speed')),
            'result_unit_symbol': self._sl(tu),
            'formula': f'{self._f(spd)} {self._sl(fu)} = {self._f(result)} {self._sl(tu)}',
            'step_by_step': steps,
            'chart_data': {'spd_chart': chart},
        })

    # ── chart helpers ────────────────────────────────────────────────
    def _speed_chart(self, spd_ms):
        """Bar chart showing speed in all units."""
        labels = []
        data = []
        colors = [
            'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)',
            'rgba(234,179,8,0.8)', 'rgba(139,92,246,0.8)', 'rgba(239,68,68,0.8)',
        ]
        for i, (key, factor) in enumerate(self.SPD.items()):
            labels.append(self.SPD_LBL[key])
            data.append(round(spd_ms / factor, 2))
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Speed')),
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.8', '1') for c in colors],
                    'borderWidth': 2, 'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Speed in All Units'))}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }

    def _bar(self, labels, data, colors, title):
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': [round(v, 2) for v in data],
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.8', '1') for c in colors],
                    'borderWidth': 2, 'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': title}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }
