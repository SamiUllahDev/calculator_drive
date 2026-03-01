from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GolfHandicapCalculator(View):
    """
    Golf Handicap Calculator — WHS-compliant.

    Calc types
        • handicap_index     → best differentials × 0.96  (WHS)
        • course_handicap    → HI × (SR / 113) + (CR − Par)
        • score_differential → (AGS − CR) × (113 / SR)
        • net_score          → Gross − Course Handicap
        • playing_handicap   → CH × (Allowance / 100)
    """
    template_name = 'other_calculators/golf_handicap_calculator.html'
    STANDARD_SLOPE = 113

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Golf Handicap Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'handicap_index')
            dispatch = {
                'handicap_index':     self._calc_handicap_index,
                'course_handicap':    self._calc_course_handicap,
                'score_differential': self._calc_score_differential,
                'net_score':          self._calc_net_score,
                'playing_handicap':   self._calc_playing_handicap,
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

    def _f(self, v, dp=1):
        return f'{v:,.{dp}f}'

    def _pos(self, data, key, label):
        v = data.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{label} is required.').format(label=label)))
        f = float(v)
        if f <= 0:
            raise ValueError(str(_('{label} must be greater than zero.').format(label=label)))
        return f

    def _ranged(self, data, key, label, lo, hi):
        v = data.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{label} is required.').format(label=label)))
        f = float(v)
        if f < lo or f > hi:
            raise ValueError(str(_('{label} must be between {lo} and {hi}.').format(label=label, lo=lo, hi=hi)))
        return f

    def _chart_bar(self, labels, values, title):
        colors = ['rgba(34,197,94,0.8)', 'rgba(59,130,246,0.8)', 'rgba(139,92,246,0.8)',
                  'rgba(245,158,11,0.8)', 'rgba(236,72,153,0.8)']
        borders = ['#22c55e', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899']
        n = len(labels)
        return {'main_chart': {
            'type': 'bar',
            'data': {'labels': labels, 'datasets': [{
                'label': str(_('Values')), 'data': values,
                'backgroundColor': colors[:n], 'borderColor': borders[:n],
                'borderWidth': 2, 'borderRadius': 6,
            }]},
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(title)}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

    # How many best differentials to use based on count (WHS table)
    @staticmethod
    def _best_count(n):
        if n >= 20: return 8
        if n >= 17: return 7
        if n >= 14: return 6
        if n >= 11: return 5
        if n >= 9:  return 4
        if n >= 7:  return 3
        if n >= 5:  return 2
        if n >= 3:  return 1
        return 1

    # ── 1) HANDICAP INDEX (WHS) ──────────────────────────────────────
    def _calc_handicap_index(self, data):
        raw = data.get('differentials')
        if not raw or not isinstance(raw, list):
            raise ValueError(str(_('Score differentials are required as a comma-separated list.')))
        diffs = []
        for i, d in enumerate(raw):
            try:
                f = float(d)
            except (ValueError, TypeError):
                raise ValueError(str(_('Differential #{n} is not a valid number.').format(n=i + 1)))
            if f < 0 or f > 200:
                raise ValueError(str(_('Differential #{n} must be between 0 and 200.').format(n=i + 1)))
            diffs.append(f)
        if len(diffs) < 3:
            raise ValueError(str(_('At least 3 score differentials are required.')))
        if len(diffs) > 20:
            raise ValueError(str(_('Maximum 20 score differentials allowed.')))

        n = len(diffs)
        sorted_d = sorted(diffs)
        use = self._best_count(n)
        best = sorted_d[:use]
        avg = sum(best) / len(best)
        hi = round(avg * 0.96, 1)

        steps = [
            str(_('Step 1: Given differentials ({n} rounds)').format(n=n)),
            f'  • {", ".join(self._f(d) for d in diffs)}',
            '', str(_('Step 2: Sort ascending')),
            f'  {", ".join(self._f(d) for d in sorted_d)}',
            '', str(_('Step 3: Select best {use} of {n}').format(use=use, n=n)),
            f'  {", ".join(self._f(d) for d in best)}',
            '', str(_('Step 4: Calculate average')),
            f'  ({" + ".join(self._f(d) for d in best)}) / {use} = {self._f(avg, 2)}',
            '', str(_('Step 5: Multiply by 0.96 (WHS adjustment)')),
            f'  {self._f(avg, 2)} × 0.96 = {self._f(hi)}',
            '', str(_('Result: Handicap Index = {hi}').format(hi=self._f(hi))),
        ]

        chart_labels = [f'R{i+1}' for i in range(n)]
        chart_values = sorted_d
        chart_data = self._chart_bar(chart_labels, chart_values, str(_('Score Differentials (sorted)')))

        return JsonResponse({
            'success': True, 'calc_type': 'handicap_index',
            'result': hi,
            'result_label': str(_('Handicap Index')),
            'num_differentials': n,
            'best_count': use,
            'best_differentials': best,
            'average_differential': round(avg, 2),
            'handicap_index': hi,
            'formula': f'{_("Avg")} {self._f(avg, 2)} × 0.96 = {self._f(hi)}',
            'step_by_step': steps,
            'chart_data': chart_data,
        })

    # ── 2) COURSE HANDICAP ──────────────────────────────────────────
    def _calc_course_handicap(self, data):
        hi = self._ranged(data, 'handicap_index', str(_('Handicap Index')), 0, 54)
        sr = self._ranged(data, 'slope_rating', str(_('Slope Rating')), 55, 155)
        cr = self._ranged(data, 'course_rating', str(_('Course Rating')), 60, 80)
        par = self._ranged(data, 'par', str(_('Par')), 60, 80)

        # CH = HI × (SR / 113) + (CR − Par)
        sf = sr / self.STANDARD_SLOPE
        ch = round(hi * sf + (cr - par))

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Handicap Index")} = {self._f(hi)}',
            f'  • {_("Slope Rating")} = {self._f(sr, 0)}',
            f'  • {_("Course Rating")} = {self._f(cr)}',
            f'  • {_("Par")} = {self._f(par, 0)}',
            '', str(_('Step 2: Slope factor = SR / 113')),
            f'  {self._f(sr, 0)} / 113 = {self._f(sf, 4)}',
            '', str(_('Step 3: Course Handicap = HI × SF + (CR − Par)')),
            f'  {self._f(hi)} × {self._f(sf, 4)} + ({self._f(cr)} − {self._f(par, 0)})',
            f'  = {self._f(hi * sf, 2)} + {self._f(cr - par, 1)}',
            f'  = {ch}',
            '', str(_('Result: Course Handicap = {ch}').format(ch=ch)),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'course_handicap',
            'result': ch,
            'result_label': str(_('Course Handicap')),
            'handicap_index': hi, 'slope_rating': sr, 'course_rating': cr, 'par': par,
            'course_handicap': ch,
            'formula': f'HI {self._f(hi)} × ({self._f(sr,0)}/113) + ({self._f(cr)}−{self._f(par,0)}) = {ch}',
            'step_by_step': steps,
            'chart_data': self._chart_bar(
                [str(_('Handicap Index')), str(_('Course Handicap'))],
                [hi, ch], str(_('Course Handicap Calc'))),
        })

    # ── 3) SCORE DIFFERENTIAL ────────────────────────────────────────
    def _calc_score_differential(self, data):
        ags = self._ranged(data, 'adjusted_gross_score', str(_('Adjusted Gross Score')), 50, 200)
        cr = self._ranged(data, 'course_rating', str(_('Course Rating')), 60, 80)
        sr = self._ranged(data, 'slope_rating', str(_('Slope Rating')), 55, 155)

        # SD = (AGS − CR) × (113 / SR)
        sd = round((ags - cr) * (self.STANDARD_SLOPE / sr), 1)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Adjusted Gross Score")} = {self._f(ags, 0)}',
            f'  • {_("Course Rating")} = {self._f(cr)}',
            f'  • {_("Slope Rating")} = {self._f(sr, 0)}',
            '', str(_('Step 2: Score Differential = (AGS − CR) × (113 / SR)')),
            f'  ({self._f(ags, 0)} − {self._f(cr)}) × (113 / {self._f(sr, 0)})',
            f'  = {self._f(ags - cr)} × {self._f(113 / sr, 4)}',
            f'  = {self._f(sd)}',
            '', str(_('Result: Score Differential = {sd}').format(sd=self._f(sd))),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'score_differential',
            'result': sd,
            'result_label': str(_('Score Differential')),
            'adjusted_gross_score': ags, 'course_rating': cr, 'slope_rating': sr,
            'score_differential': sd,
            'formula': f'({self._f(ags,0)} − {self._f(cr)}) × (113/{self._f(sr,0)}) = {self._f(sd)}',
            'step_by_step': steps,
            'chart_data': self._chart_bar(
                [str(_('Gross Score')), str(_('Course Rating')), str(_('Differential'))],
                [ags, cr, sd], str(_('Score Differential'))),
        })

    # ── 4) NET SCORE ─────────────────────────────────────────────────
    def _calc_net_score(self, data):
        gross = self._ranged(data, 'gross_score', str(_('Gross Score')), 50, 200)
        ch_val = data.get('course_handicap')
        if ch_val is None or ch_val == '':
            raise ValueError(str(_('Course Handicap is required.')))
        ch = float(ch_val)
        if ch < -10 or ch > 54:
            raise ValueError(str(_('Course Handicap must be between -10 and 54.')))

        net = round(gross - ch)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Gross Score")} = {self._f(gross, 0)}',
            f'  • {_("Course Handicap")} = {self._f(ch, 0)}',
            '', str(_('Step 2: Net Score = Gross − Course Handicap')),
            f'  {self._f(gross, 0)} − {self._f(ch, 0)} = {net}',
            '', str(_('Result: Net Score = {net}').format(net=net)),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'net_score',
            'result': net,
            'result_label': str(_('Net Score')),
            'gross_score': gross, 'course_handicap': ch,
            'net_score': net,
            'formula': f'{self._f(gross,0)} − {self._f(ch,0)} = {net}',
            'step_by_step': steps,
            'chart_data': self._chart_bar(
                [str(_('Gross')), str(_('Handicap')), str(_('Net'))],
                [gross, ch, net], str(_('Net Score Calc'))),
        })

    # ── 5) PLAYING HANDICAP ─────────────────────────────────────────
    def _calc_playing_handicap(self, data):
        ch_val = data.get('course_handicap')
        if ch_val is None or ch_val == '':
            raise ValueError(str(_('Course Handicap is required.')))
        ch = float(ch_val)
        if ch < -10 or ch > 54:
            raise ValueError(str(_('Course Handicap must be between -10 and 54.')))

        allow = float(data.get('handicap_allowance', 100))
        if allow < 0 or allow > 200:
            raise ValueError(str(_('Handicap Allowance must be between 0% and 200%.')))

        ph = round(ch * allow / 100)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Course Handicap")} = {self._f(ch, 0)}',
            f'  • {_("Handicap Allowance")} = {self._f(allow, 0)}%',
            '', str(_('Step 2: Playing Handicap = CH × (Allowance / 100)')),
            f'  {self._f(ch, 0)} × ({self._f(allow, 0)} / 100) = {ph}',
            '', str(_('Result: Playing Handicap = {ph}').format(ph=ph)),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'playing_handicap',
            'result': ph,
            'result_label': str(_('Playing Handicap')),
            'course_handicap': ch, 'handicap_allowance': allow,
            'playing_handicap': ph,
            'formula': f'{self._f(ch,0)} × {self._f(allow,0)}% = {ph}',
            'step_by_step': steps,
            'chart_data': self._chart_bar(
                [str(_('Course HC')), str(_('Playing HC'))],
                [ch, ph], str(_('Playing Handicap'))),
        })
