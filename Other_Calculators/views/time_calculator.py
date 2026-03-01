from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TimeCalculator(View):
    """
    Time Calculator — 4 calculation types.

    Calculation types
        • difference   → time between two clock times
        • add_subtract → add/subtract duration to/from a time
        • convert      → convert between time units
        • duration     → duration from start to end (midnight-aware)
    """
    template_name = 'other_calculators/time_calculator.html'

    UNITS = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours':   3600.0,
        'days':    86400.0,
        'weeks':   604800.0,
    }
    UNIT_SHORT = {
        'seconds': 's', 'minutes': 'min',
        'hours': 'h', 'days': 'days', 'weeks': 'weeks',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Time Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'difference')
            dispatch = {
                'difference':   self._calc_difference,
                'add_subtract': self._calc_add_subtract,
                'convert':      self._calc_convert,
                'duration':     self._calc_duration,
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

    def _parse_time(self, val):
        """Parse HH:MM or HH:MM:SS → total seconds. Returns None on failure."""
        if not val:
            return None
        s = str(val).strip()
        if ':' in s:
            parts = s.split(':')
            try:
                if len(parts) == 2:
                    h, m, sec = int(parts[0]), int(parts[1]), 0
                elif len(parts) == 3:
                    h, m, sec = int(parts[0]), int(parts[1]), int(parts[2])
                else:
                    return None
            except ValueError:
                return None
            if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= sec <= 59):
                return None
            return h * 3600 + m * 60 + sec
        try:
            return float(s)
        except ValueError:
            return None

    @staticmethod
    def _fmt_hms(total_sec):
        """Format seconds → HH:MM:SS string."""
        total_sec = int(total_sec) % 86400
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        return f'{h:02d}:{m:02d}:{s:02d}'

    @staticmethod
    def _breakdown(total_sec):
        """Return h, m, s ints from total seconds."""
        ts = int(abs(total_sec))
        return ts // 3600, (ts % 3600) // 60, ts % 60

    # ── 1) DIFFERENCE ────────────────────────────────────────────────
    def _calc_difference(self, data):
        t1s = data.get('time1', '')
        t2s = data.get('time2', '')
        if not t1s or not t2s:
            return self._err(_('Both times are required.'))

        s1 = self._parse_time(t1s)
        s2 = self._parse_time(t2s)
        if s1 is None or s2 is None:
            return self._err(_('Invalid time format. Use HH:MM or HH:MM:SS (24-hour).'))

        diff = abs(s2 - s1)
        h, m, s = self._breakdown(diff)
        fmt = self._fmt_hms(diff)

        steps = [
            str(_('Step 1: Given times')),
            f'  • Time 1 = {t1s}',
            f'  • Time 2 = {t2s}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  Time 1 = {int(s1)} {_("seconds")}',
            f'  Time 2 = {int(s2)} {_("seconds")}',
            '',
            str(_('Step 3: Calculate difference')),
            f'  |{int(s2)} − {int(s1)}| = {int(diff)} {_("seconds")}',
            '',
            str(_('Step 4: Convert to HH:MM:SS')),
            f'  {_("Hours")} = {int(diff)} ÷ 3600 = {h}',
            f'  {_("Minutes")} = ({int(diff)} mod 3600) ÷ 60 = {m}',
            f'  {_("Seconds")} = {int(diff)} mod 60 = {s}',
            '',
            str(_('Result: {r}').format(r=fmt)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Time 1')), str(_('Time 2')), str(_('Difference'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [int(s1), int(s2), int(diff)],
                    'backgroundColor': ['rgba(99,102,241,0.7)', 'rgba(139,92,246,0.7)',
                                        'rgba(167,139,250,0.7)'],
                    'borderColor': ['#6366f1', '#8b5cf6', '#a78bfa'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Time Comparison'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'difference',
            'result': fmt, 'result_label': str(_('Time Difference')),
            'formula': f'|{t2s} − {t1s}| = {fmt}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Hours')), 'value': str(h), 'color': 'indigo'},
                {'label': str(_('Minutes')), 'value': str(m), 'color': 'purple'},
                {'label': str(_('Seconds')), 'value': str(s), 'color': 'violet'},
                {'label': str(_('Total sec')), 'value': str(int(diff)), 'color': 'blue'},
            ],
        })

    # ── 2) ADD / SUBTRACT ────────────────────────────────────────────
    def _calc_add_subtract(self, data):
        ts = data.get('time', '')
        op = data.get('operation', 'add')
        amt_raw = data.get('amount')
        amt_unit = data.get('amount_unit', 'hours')

        if not ts:
            return self._err(_('Time is required.'))
        if amt_raw is None or amt_raw == '':
            return self._err(_('Amount is required.'))

        base = self._parse_time(ts)
        if base is None:
            return self._err(_('Invalid time format. Use HH:MM or HH:MM:SS (24-hour).'))

        try:
            amt = float(amt_raw)
        except (ValueError, TypeError):
            return self._err(_('Amount must be a number.'))
        if amt < 0:
            return self._err(_('Amount must be non-negative.'))

        factor = self.UNITS.get(amt_unit, 3600)
        amt_sec = amt * factor

        if op == 'add':
            result_sec = base + amt_sec
        else:
            result_sec = base - amt_sec
            if result_sec < 0:
                result_sec += 86400

        fmt = self._fmt_hms(result_sec)
        h, m, s = self._breakdown(result_sec)
        op_sym = '+' if op == 'add' else '−'
        u_short = self.UNIT_SHORT.get(amt_unit, amt_unit)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Time")} = {ts}',
            f'  • {_("Operation")} = {op.title()}',
            f'  • {_("Amount")} = {amt} {u_short}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  {_("Time")} = {int(base)} {_("seconds")}',
            f'  {_("Amount")} = {amt} × {factor:.0f} = {amt_sec:.0f} {_("seconds")}',
            '',
            str(_('Step 3: Calculate')),
            f'  {int(base)} {op_sym} {amt_sec:.0f} = {int(result_sec % 86400)} {_("seconds")}',
            '',
            str(_('Step 4: Convert to HH:MM:SS')),
            f'  {fmt}',
            '',
            str(_('Result: {r}').format(r=fmt)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Start')), str(_('Amount')), str(_('Result'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [int(base), int(amt_sec), int(result_sec % 86400)],
                    'backgroundColor': ['rgba(99,102,241,0.7)', 'rgba(139,92,246,0.7)',
                                        'rgba(167,139,250,0.7)'],
                    'borderColor': ['#6366f1', '#8b5cf6', '#a78bfa'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Add/Subtract Time'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'add_subtract',
            'result': fmt, 'result_label': str(_('Result Time')),
            'formula': f'{ts} {op_sym} {amt} {u_short} = {fmt}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Start')), 'value': ts, 'color': 'indigo'},
                {'label': str(_('Operation')), 'value': f'{op_sym} {amt} {u_short}', 'color': 'purple'},
                {'label': str(_('Result')), 'value': fmt, 'color': 'green'},
                {'label': str(_('Total sec')), 'value': str(int(result_sec % 86400)), 'color': 'blue'},
            ],
        })

    # ── 3) CONVERT ───────────────────────────────────────────────────
    def _calc_convert(self, data):
        val_raw = data.get('time')
        from_u = data.get('from_unit', 'hours')
        to_u = data.get('to_unit', 'minutes')

        if val_raw is None or val_raw == '':
            return self._err(_('Time value is required.'))
        try:
            val = float(val_raw)
        except (ValueError, TypeError):
            return self._err(_('Time must be a number.'))
        if val < 0:
            return self._err(_('Time must be non-negative.'))

        from_f = self.UNITS.get(from_u)
        to_f = self.UNITS.get(to_u)
        if not from_f or not to_f:
            return self._err(_('Unknown time unit.'))

        sec = val * from_f
        result = round(sec / to_f, 6)
        fu = self.UNIT_SHORT.get(from_u, from_u)
        tu = self.UNIT_SHORT.get(to_u, to_u)

        # Also show all conversions
        all_conv = {k: round(sec / v, 6) for k, v in self.UNITS.items()}

        steps = [
            str(_('Step 1: Given value')),
            f'  {val} {fu}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  {val} × {from_f:.0f} = {sec:.2f} {_("seconds")}',
            '',
            str(_('Step 3: Convert to {u}').format(u=tu)),
            f'  {sec:.2f} ÷ {to_f:.0f} = {result} {tu}',
            '',
            str(_('Step 4: All conversions')),
        ]
        for k, v in all_conv.items():
            steps.append(f'  • {self.UNIT_SHORT[k]} = {v}')
        steps += ['', str(_('Result: {v} {u}').format(v=result, u=tu))]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [f'{val} {fu}', f'{result} {tu}'],
                'datasets': [{
                    'label': str(_('Value (seconds)')),
                    'data': [sec, sec],
                    'backgroundColor': ['rgba(99,102,241,0.7)', 'rgba(139,92,246,0.7)'],
                    'borderColor': ['#6366f1', '#8b5cf6'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Unit Conversion'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': f'{result} {tu}',
            'result_label': str(_('Conversion Result')),
            'all_conversions': all_conv,
            'formula': f'{val} {fu} = {result} {tu}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Seconds')), 'value': str(all_conv['seconds']), 'color': 'indigo'},
                {'label': str(_('Minutes')), 'value': str(all_conv['minutes']), 'color': 'purple'},
                {'label': str(_('Hours')), 'value': str(all_conv['hours']), 'color': 'blue'},
                {'label': str(_('Days')), 'value': str(all_conv['days']), 'color': 'green'},
            ],
        })

    # ── 4) DURATION ──────────────────────────────────────────────────
    def _calc_duration(self, data):
        st = data.get('start_time', '')
        et = data.get('end_time', '')
        if not st or not et:
            return self._err(_('Start and end times are required.'))

        ss = self._parse_time(st)
        es = self._parse_time(et)
        if ss is None or es is None:
            return self._err(_('Invalid time format. Use HH:MM or HH:MM:SS (24-hour).'))

        # Handle crossing midnight
        if es < ss:
            dur = (86400 - ss) + es
            crosses = True
        else:
            dur = es - ss
            crosses = False

        h, m, s = self._breakdown(dur)
        fmt = self._fmt_hms(dur)

        steps = [
            str(_('Step 1: Given times')),
            f'  • {_("Start")} = {st}',
            f'  • {_("End")} = {et}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  {_("Start")} = {int(ss)} {_("seconds")}',
            f'  {_("End")} = {int(es)} {_("seconds")}',
            '',
        ]
        if crosses:
            steps += [
                str(_('Step 3: Calculate duration (crosses midnight)')),
                f'  (86400 − {int(ss)}) + {int(es)} = {int(dur)} {_("seconds")}',
            ]
        else:
            steps += [
                str(_('Step 3: Calculate duration')),
                f'  {int(es)} − {int(ss)} = {int(dur)} {_("seconds")}',
            ]
        steps += [
            '',
            str(_('Step 4: Convert to HH:MM:SS')),
            f'  {_("Hours")} = {h},  {_("Minutes")} = {m},  {_("Seconds")} = {s}',
            '',
            str(_('Result: {r}').format(r=fmt)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Start')), str(_('End')), str(_('Duration'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [int(ss), int(es), int(dur)],
                    'backgroundColor': ['rgba(99,102,241,0.7)', 'rgba(139,92,246,0.7)',
                                        'rgba(16,185,129,0.7)'],
                    'borderColor': ['#6366f1', '#8b5cf6', '#10b981'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Duration'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'duration',
            'result': fmt, 'result_label': str(_('Duration')),
            'crosses_midnight': crosses,
            'formula': f'{st} → {et} = {fmt}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Hours')), 'value': str(h), 'color': 'indigo'},
                {'label': str(_('Minutes')), 'value': str(m), 'color': 'purple'},
                {'label': str(_('Seconds')), 'value': str(s), 'color': 'violet'},
                {'label': str(_('Total sec')), 'value': str(int(dur)), 'color': 'green'},
            ],
        })
