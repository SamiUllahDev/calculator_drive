from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StairCalculator(View):
    """
    Stair Calculator — design, riser/tread, stringer.

    Calc types
        • design       → total rise → # risers, riser height, tread, run, stringer, angle
        • riser_tread  → given R, T, n → total rise, run, stringer, angle
        • stringer     → rise + run → stringer length, angle
    """
    template_name = 'other_calculators/stair_calculator.html'

    # Length → inches
    LEN = {'inches': 1.0, 'feet': 12.0, 'meters': 39.3701, 'centimeters': 0.393701}

    UNIT_SYM = {'inches': 'in', 'feet': 'ft', 'meters': 'm', 'centimeters': 'cm'}

    # Building code limits (inches)
    MIN_RISER = 4.0
    MAX_RISER = 7.75
    MIN_TREAD = 10.0
    MAX_TREAD = 14.0
    IDEAL_2R_T = 24.5   # 2R + T ≈ 24–25 in

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Stair Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'design')
            dispatch = {
                'design':      self._calc_design,
                'riser_tread': self._calc_riser_tread,
                'stringer':    self._calc_stringer,
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

    def _sym(self, u):
        return self.UNIT_SYM.get(u, u)

    def _pos(self, data, key, label):
        v = data.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{label} is required.').format(label=label)))
        f = float(v)
        if f <= 0:
            raise ValueError(str(_('{label} must be greater than zero.').format(label=label)))
        return f

    def _to_in(self, val, unit):
        if unit not in self.LEN:
            raise ValueError(str(_('Invalid length unit.')))
        return val * self.LEN[unit]

    def _compliance(self, riser, tread):
        riser_ok = self.MIN_RISER <= riser <= self.MAX_RISER
        tread_ok = self.MIN_TREAD <= tread <= self.MAX_TREAD
        sum_2rt = round(2 * riser + tread, 2)
        formula_ok = 24.0 <= sum_2rt <= 25.0
        return {
            'riser_ok': riser_ok, 'tread_ok': tread_ok,
            'formula_ok': formula_ok, 'riser_tread_sum': sum_2rt,
            'overall': riser_ok and tread_ok and formula_ok,
        }

    def _chart(self, labels, values, title):
        colors = ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(139,92,246,0.8)']
        borders = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
        n = len(labels)
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Values')),
                    'data': values,
                    'backgroundColor': colors[:n],
                    'borderColor': borders[:n],
                    'borderWidth': 2, 'borderRadius': 6,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(title)}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }

    # ── 1) DESIGN FROM TOTAL RISE ────────────────────────────────────
    def _calc_design(self, data):
        tr = self._pos(data, 'total_rise', str(_('Total Rise')))
        lu = data.get('length_unit', 'inches')
        pref = float(data.get('preferred_riser', 7.0))

        tr_in = self._to_in(tr, lu)

        # Number of risers
        n = math.ceil(tr_in / pref)
        if n < 1:
            n = 1

        # Actual riser height
        riser = tr_in / n

        # Tread depth: 2R + T = 24.5 → T = 24.5 - 2R
        tread = self.IDEAL_2R_T - 2 * riser
        tread = max(self.MIN_TREAD, min(self.MAX_TREAD, tread))

        # Total run (n-1 treads for n risers)
        total_run = tread * (n - 1) if n > 1 else 0
        # Stringer length
        stringer = math.sqrt(tr_in ** 2 + total_run ** 2)
        # Angle
        angle = math.degrees(math.atan2(tr_in, total_run)) if total_run > 0 else 90.0

        comp = self._compliance(riser, tread)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Total Rise")} = {self._f(tr)} {self._sym(lu)}',
            f'  • {_("Preferred Riser")} = {self._f(pref)} in',
            '', str(_('Step 2: Convert to inches')),
            f'  Total Rise = {self._f(tr_in)} in',
            '', str(_('Step 3: Number of risers')),
            f'  ⌈{self._f(tr_in)} / {self._f(pref)}⌉ = {n} risers',
            '', str(_('Step 4: Actual riser height')),
            f'  {self._f(tr_in)} / {n} = {self._f(riser, 3)} in',
            '', str(_('Step 5: Tread depth (2R + T = 24.5)')),
            f'  T = 24.5 − 2 × {self._f(riser, 3)} = {self._f(tread, 3)} in',
            '', str(_('Step 6: Total run')),
            f'  {self._f(tread, 3)} × ({n} − 1) = {self._f(total_run, 3)} in',
            '', str(_('Step 7: Stringer length')),
            f'  √({self._f(tr_in)}² + {self._f(total_run, 3)}²) = {self._f(stringer, 3)} in',
            '', str(_('Step 8: Angle')),
            f'  arctan({self._f(tr_in)} / {self._f(total_run, 3)}) = {self._f(angle)}°',
            '', str(_('Step 9: Code compliance')),
            f'  • {_("Riser")} {self._f(riser, 3)} in: {"✓" if comp["riser_ok"] else "✗"} (4–7.75)',
            f'  • {_("Tread")} {self._f(tread, 3)} in: {"✓" if comp["tread_ok"] else "✗"} (10–14)',
            f'  • 2R + T = {comp["riser_tread_sum"]}: {"✓" if comp["formula_ok"] else "✗"} (24–25)',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'design',
            'result': n,
            'result_label': str(_('Number of Risers')),
            'result_unit_symbol': str(_('risers')),
            'num_risers': n,
            'riser_height': round(riser, 3),
            'tread_depth': round(tread, 3),
            'total_rise_in': round(tr_in, 3),
            'total_run': round(total_run, 3),
            'stringer_length': round(stringer, 3),
            'angle': round(angle, 2),
            'compliance': comp,
            'formula': f'{self._f(tr)} {self._sym(lu)} → {n} risers × {self._f(riser, 3)}" + {self._f(tread, 3)}" tread',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Riser (in)')), str(_('Tread (in)')), str(_('Angle (°)'))],
                [round(riser, 2), round(tread, 2), round(angle, 2)],
                str(_('Stair Dimensions'))
            )},
        })

    # ── 2) RISER & TREAD ─────────────────────────────────────────────
    def _calc_riser_tread(self, data):
        rh = self._pos(data, 'riser_height', str(_('Riser Height')))
        td = self._pos(data, 'tread_depth', str(_('Tread Depth')))
        ns = int(self._pos(data, 'num_steps', str(_('Number of Steps'))))
        lu = data.get('length_unit', 'inches')

        rh_in = self._to_in(rh, lu)
        td_in = self._to_in(td, lu)

        total_rise = rh_in * ns
        total_run = td_in * (ns - 1) if ns > 1 else 0
        stringer = math.sqrt(total_rise ** 2 + total_run ** 2)
        angle = math.degrees(math.atan2(total_rise, total_run)) if total_run > 0 else 90.0

        comp = self._compliance(rh_in, td_in)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Riser")} = {self._f(rh)} {self._sym(lu)}',
            f'  • {_("Tread")} = {self._f(td)} {self._sym(lu)}',
            f'  • {_("Steps")} = {ns}',
            '', str(_('Step 2: Convert to inches')),
            f'  Riser = {self._f(rh_in, 3)} in, Tread = {self._f(td_in, 3)} in',
            '', str(_('Step 3: Total rise')),
            f'  {self._f(rh_in, 3)} × {ns} = {self._f(total_rise, 3)} in',
            '', str(_('Step 4: Total run')),
            f'  {self._f(td_in, 3)} × ({ns} − 1) = {self._f(total_run, 3)} in',
            '', str(_('Step 5: Stringer length')),
            f'  √({self._f(total_rise, 3)}² + {self._f(total_run, 3)}²) = {self._f(stringer, 3)} in',
            '', str(_('Step 6: Angle')),
            f'  arctan({self._f(total_rise, 3)} / {self._f(total_run, 3)}) = {self._f(angle)}°',
            '', str(_('Step 7: Code compliance')),
            f'  • {_("Riser")} {self._f(rh_in, 3)} in: {"✓" if comp["riser_ok"] else "✗"} (4–7.75)',
            f'  • {_("Tread")} {self._f(td_in, 3)} in: {"✓" if comp["tread_ok"] else "✗"} (10–14)',
            f'  • 2R + T = {comp["riser_tread_sum"]}: {"✓" if comp["formula_ok"] else "✗"} (24–25)',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'riser_tread',
            'result': round(stringer, 3),
            'result_label': str(_('Stringer Length')),
            'result_unit_symbol': 'in',
            'num_steps': ns,
            'riser_height_in': round(rh_in, 3),
            'tread_depth_in': round(td_in, 3),
            'total_rise': round(total_rise, 3),
            'total_run': round(total_run, 3),
            'stringer_length': round(stringer, 3),
            'angle': round(angle, 2),
            'compliance': comp,
            'formula': f'{ns} steps × {self._f(rh_in, 3)}" riser → stringer = {self._f(stringer, 3)}"',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Rise (in)')), str(_('Run (in)')), str(_('Stringer (in)')), str(_('Angle (°)'))],
                [round(total_rise, 1), round(total_run, 1), round(stringer, 1), round(angle, 1)],
                str(_('Stair Overview'))
            )},
        })

    # ── 3) STRINGER ──────────────────────────────────────────────────
    def _calc_stringer(self, data):
        tr = self._pos(data, 'total_rise', str(_('Total Rise')))
        trun = self._pos(data, 'total_run', str(_('Total Run')))
        lu = data.get('length_unit', 'inches')

        tr_in = self._to_in(tr, lu)
        trun_in = self._to_in(trun, lu)

        stringer = math.sqrt(tr_in ** 2 + trun_in ** 2)
        angle = math.degrees(math.atan2(tr_in, trun_in))

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Total Rise")} = {self._f(tr)} {self._sym(lu)}',
            f'  • {_("Total Run")} = {self._f(trun)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to inches')),
            f'  Rise = {self._f(tr_in, 3)} in, Run = {self._f(trun_in, 3)} in',
            '', str(_('Step 3: Stringer length')),
            f'  √({self._f(tr_in, 3)}² + {self._f(trun_in, 3)}²) = {self._f(stringer, 3)} in',
            '', str(_('Step 4: Angle')),
            f'  arctan({self._f(tr_in, 3)} / {self._f(trun_in, 3)}) = {self._f(angle)}°',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'stringer',
            'result': round(stringer, 3),
            'result_label': str(_('Stringer Length')),
            'result_unit_symbol': 'in',
            'total_rise_in': round(tr_in, 3),
            'total_run_in': round(trun_in, 3),
            'stringer_length': round(stringer, 3),
            'angle': round(angle, 2),
            'formula': f'√({self._f(tr_in, 3)}² + {self._f(trun_in, 3)}²) = {self._f(stringer, 3)} in ({self._f(angle)}°)',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Rise (in)')), str(_('Run (in)')), str(_('Stringer (in)'))],
                [round(tr_in, 1), round(trun_in, 1), round(stringer, 1)],
                str(_('Stringer Calculation'))
            )},
        })
