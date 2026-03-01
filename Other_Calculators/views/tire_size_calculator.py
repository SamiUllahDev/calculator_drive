from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TireSizeCalculator(View):
    """
    Tire Size Calculator — dimensions, conversion, comparison, speedometer.

    Calc types
        • dimensions   → full tire specs from metric or imperial size
        • convert      → metric ↔ imperial
        • compare      → side-by-side two tires
        • speedometer  → actual vs indicated speed after tire swap

    Metric format:  205/55R16  (width mm / aspect-ratio R rim-inches)
    Imperial format: 31x10.5R15 (overall-dia x width R rim-inches)
    """
    template_name = 'other_calculators/tire_size_calculator.html'

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Tire Size Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'dimensions')
            dispatch = {
                'dimensions':  self._calc_dimensions,
                'convert':     self._calc_convert,
                'compare':     self._calc_compare,
                'speedometer': self._calc_speedometer,
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

    def _f(self, v, dp=2):
        return f'{v:,.{dp}f}'

    # ── tire parsing ─────────────────────────────────────────────────
    def _parse(self, raw):
        """Parse metric (205/55R16) or imperial (31x10.5R15) tire string."""
        s = raw.strip().upper().replace(' ', '')
        if s.startswith('P'):
            s = s[1:]

        # Try metric first
        m = re.match(r'^(\d+)/(\d+)R?(\d+)$', s)
        if m:
            return {
                'fmt': 'metric',
                'width_mm': int(m.group(1)),
                'aspect': int(m.group(2)),
                'rim': int(m.group(3)),
            }

        # Try imperial
        m = re.match(r'^(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)R?(\d+)$', s)
        if m:
            return {
                'fmt': 'imperial',
                'od_in': float(m.group(1)),
                'width_in': float(m.group(2)),
                'rim': int(m.group(3)),
            }
        return None

    def _dims(self, t):
        """Return full dimension dict from parsed tire."""
        if t['fmt'] == 'metric':
            w_mm = t['width_mm']
            ar = t['aspect']
            rim = t['rim']
            w_in = w_mm / 25.4
            sw = (w_mm * ar / 100) / 25.4  # sidewall in
            od = rim + 2 * sw
        else:
            od = t['od_in']
            w_in = t['width_in']
            w_mm = w_in * 25.4
            rim = t['rim']
            sw = (od - rim) / 2
            ar = (sw / w_in) * 100

        circ = math.pi * od
        rpm = 63360 / circ            # revolutions per mile  (63360 in/mi)
        rpk = 1000000 / (circ * 25.4) # revolutions per km    (10^6 mm/km)

        return {
            'width_mm': round(w_mm, 2),
            'width_in': round(w_in, 2),
            'aspect': round(ar, 1),
            'rim': rim,
            'sidewall': round(sw, 2),
            'diameter': round(od, 2),
            'circumference': round(circ, 2),
            'rpm': round(rpm, 0),
            'rpk': round(rpk, 0),
        }

    def _require_tire(self, data, key):
        raw = data.get(key, '').strip()
        if not raw:
            raise ValueError(str(_('Tire size is required.')))
        t = self._parse(raw)
        if not t:
            raise ValueError(str(_(
                'Invalid tire size format. Use metric (e.g., 205/55R16) or imperial (e.g., 31x10.5R15).'
            )))
        return raw, t

    # ── 1) DIMENSIONS ────────────────────────────────────────────────
    def _calc_dimensions(self, data):
        raw, t = self._require_tire(data, 'tire_size')
        d = self._dims(t)

        steps = [
            str(_('Step 1: Parse tire size')),
            f'  • {raw} ({t["fmt"]})',
        ]
        if t['fmt'] == 'metric':
            steps += [
                f'  • {_("Width")} = {t["width_mm"]} mm',
                f'  • {_("Aspect Ratio")} = {t["aspect"]}%',
                f'  • {_("Rim")} = {t["rim"]}"',
                '', str(_('Step 2: Calculate sidewall height')),
                f'  SW = ({t["width_mm"]} × {t["aspect"]} / 100) / 25.4 = {d["sidewall"]}"',
                '', str(_('Step 3: Calculate overall diameter')),
                f'  OD = {t["rim"]} + 2 × {d["sidewall"]} = {d["diameter"]}"',
            ]
        else:
            steps += [
                f'  • {_("Overall Diameter")} = {t["od_in"]}"',
                f'  • {_("Width")} = {t["width_in"]}"',
                f'  • {_("Rim")} = {t["rim"]}"',
                '', str(_('Step 2: Calculate sidewall height')),
                f'  SW = ({t["od_in"]} − {t["rim"]}) / 2 = {d["sidewall"]}"',
            ]
        steps += [
            '', str(_('Step 4: Calculate circumference')),
            f'  C = π × {d["diameter"]} = {d["circumference"]}"',
            '', str(_('Step 5: Revolutions')),
            f'  Rev/mile = 63360 / {d["circumference"]} ≈ {d["rpm"]:.0f}',
            f'  Rev/km   ≈ {d["rpk"]:.0f}',
        ]

        chart = self._dim_chart(d)

        return JsonResponse({
            'success': True, 'calc_type': 'dimensions',
            'tire_size': raw,
            'result': d['diameter'],
            'result_label': str(_('Overall Diameter')),
            'result_unit_symbol': '"',
            'dimensions': d,
            'step_by_step': steps,
            'chart_data': {'ts_chart': chart},
        })

    # ── 2) CONVERT ───────────────────────────────────────────────────
    def _calc_convert(self, data):
        raw, t = self._require_tire(data, 'tire_size')
        target = data.get('target_format', 'imperial')
        d = self._dims(t)

        if target == 'imperial' and t['fmt'] == 'metric':
            conv = f'{d["diameter"]:.1f}x{d["width_in"]:.1f}R{d["rim"]}'
        elif target == 'metric' and t['fmt'] == 'imperial':
            w5 = round(d['width_mm'] / 5) * 5
            a5 = round(d['aspect'] / 5) * 5
            conv = f'{int(w5)}/{int(a5)}R{d["rim"]}'
        else:
            conv = raw  # already in target format

        steps = [
            str(_('Step 1: Parse original tire')),
            f'  {raw} → {t["fmt"]}',
            '', str(_('Step 2: Calculate dimensions')),
            f'  OD = {d["diameter"]}"  |  W = {d["width_in"]}" ({d["width_mm"]} mm)  |  AR = {d["aspect"]}%',
            '', str(_('Step 3: Convert to {fmt}').format(fmt=target)),
            f'  → {conv}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': conv,
            'result_label': str(_('Converted Size')),
            'result_unit_symbol': '',
            'original_size': raw, 'converted_size': conv,
            'original_format': t['fmt'], 'target_format': target,
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── 3) COMPARE ───────────────────────────────────────────────────
    def _calc_compare(self, data):
        r1, t1 = self._require_tire(data, 'tire1')
        r2, t2 = self._require_tire(data, 'tire2')
        d1 = self._dims(t1)
        d2 = self._dims(t2)

        dia_diff = d2['diameter'] - d1['diameter']
        dia_pct = (dia_diff / d1['diameter']) * 100 if d1['diameter'] else 0
        circ_diff = d2['circumference'] - d1['circumference']
        spd_pct = dia_pct  # speedometer error %

        steps = [
            str(_('Step 1: Tire 1 dimensions')),
            f'  {r1} → OD {d1["diameter"]}\"  C {d1["circumference"]}\"  W {d1["width_in"]}\"',
            '', str(_('Step 2: Tire 2 dimensions')),
            f'  {r2} → OD {d2["diameter"]}\"  C {d2["circumference"]}\"  W {d2["width_in"]}\"',
            '', str(_('Step 3: Differences')),
            f'  Δ Diameter = {self._f(dia_diff)}\" ({self._f(dia_pct)}%)',
            f'  Δ Circumference = {self._f(circ_diff)}\"',
            '', str(_('Step 4: Speedometer impact')),
            f'  {_("At 60 mph indicated, actual")} ≈ {self._f(60 * (1 + spd_pct/100))} mph',
        ]

        chart = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Diameter')), str(_('Circumference')), str(_('Width'))],
                'datasets': [
                    {'label': r1, 'data': [d1['diameter'], d1['circumference'], d1['width_in']],
                     'backgroundColor': 'rgba(59,130,246,0.8)', 'borderColor': '#3b82f6', 'borderWidth': 2, 'borderRadius': 6},
                    {'label': r2, 'data': [d2['diameter'], d2['circumference'], d2['width_in']],
                     'backgroundColor': 'rgba(16,185,129,0.8)', 'borderColor': '#10b981', 'borderWidth': 2, 'borderRadius': 6},
                ]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'title': {'display': True, 'text': str(_('Tire Comparison'))}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'compare',
            'result': round(dia_diff, 2),
            'result_label': str(_('Diameter Difference')),
            'result_unit_symbol': '"',
            'tire1': {'size': r1, 'dimensions': d1},
            'tire2': {'size': r2, 'dimensions': d2},
            'differences': {
                'diameter_diff': round(dia_diff, 2),
                'diameter_diff_percent': round(dia_pct, 2),
                'circumference_diff': round(circ_diff, 2),
                'speed_diff': round(spd_pct, 2),
            },
            'step_by_step': steps,
            'chart_data': {'ts_chart': chart},
        })

    # ── 4) SPEEDOMETER ───────────────────────────────────────────────
    def _calc_speedometer(self, data):
        r_orig, t_orig = self._require_tire(data, 'original_tire')
        r_new, t_new = self._require_tire(data, 'new_tire')
        speed = float(data.get('speed', 60))
        speed_unit = data.get('speed_unit', 'mph')
        if speed <= 0:
            raise ValueError(str(_('Speed must be greater than zero.')))

        d_orig = self._dims(t_orig)
        d_new = self._dims(t_new)

        ratio = d_new['diameter'] / d_orig['diameter']
        actual = speed * ratio
        diff = actual - speed
        diff_pct = ((actual - speed) / speed) * 100

        su = 'mph' if speed_unit == 'mph' else 'km/h'

        steps = [
            str(_('Step 1: Original tire')),
            f'  {r_orig} → OD {d_orig["diameter"]}"',
            '', str(_('Step 2: New tire')),
            f'  {r_new} → OD {d_new["diameter"]}"',
            '', str(_('Step 3: Diameter ratio')),
            f'  {_("Ratio")} = {d_new["diameter"]} / {d_orig["diameter"]} = {self._f(ratio, 4)}',
            '', str(_('Step 4: Calculate actual speed')),
            f'  {_("Actual")} = {self._f(speed)} × {self._f(ratio, 4)} = {self._f(actual)} {su}',
            '', str(_('Step 5: Speed difference')),
            f'  Δ = {self._f(diff)} {su} ({self._f(diff_pct)}%)',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'speedometer',
            'result': round(actual, 2),
            'result_label': str(_('Actual Speed')),
            'result_unit_symbol': su,
            'indicated_speed': speed,
            'actual_speed': round(actual, 2),
            'speed_difference': round(diff, 2),
            'speed_difference_percent': round(diff_pct, 2),
            'speed_unit': speed_unit,
            'diameter_ratio': round(ratio, 4),
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── chart helpers ────────────────────────────────────────────────
    def _dim_chart(self, d):
        labels = [str(_('Width (in)')), str(_('Sidewall (in)')), str(_('Diameter (in)')), str(_('Circumference (in)'))]
        data = [d['width_in'], d['sidewall'], d['diameter'], d['circumference']]
        colors = ['rgba(99,102,241,0.8)', 'rgba(16,185,129,0.8)', 'rgba(59,130,246,0.8)', 'rgba(251,191,36,0.8)']
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Inches')),
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.8', '1') for c in colors],
                    'borderWidth': 2, 'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('Tire Dimensions'))}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }
