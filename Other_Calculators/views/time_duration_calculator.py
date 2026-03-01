from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TimeDurationCalculator(View):
    """
    Time Duration Calculator — 4 calculation types.

    Calculation types
        • between_times → duration between two clock times (midnight-aware)
        • add_subtract  → add/subtract a duration to/from a clock time
        • convert       → convert between time-duration units
        • elapsed       → start time + elapsed duration → end time
    """
    template_name = 'other_calculators/time_duration_calculator.html'

    UNITS = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours':   3600.0,
        'days':    86400.0,
        'weeks':   604800.0,
        'months':  2592000.0,   # 30 days
        'years':   31536000.0,  # 365 days
    }
    UNIT_SHORT = {
        'seconds': 's', 'minutes': 'min', 'hours': 'h',
        'days': 'days', 'weeks': 'weeks', 'months': 'months', 'years': 'years',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Time Duration Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'between_times')
            dispatch = {
                'between_times': self._calc_between,
                'add_subtract':  self._calc_add_subtract,
                'convert':       self._calc_convert,
                'elapsed':       self._calc_elapsed,
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

    @staticmethod
    def _parse_time(val):
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
    def _fmt_duration(total_sec):
        """Format seconds → human-readable duration string."""
        total_sec = int(abs(total_sec))
        if total_sec == 0:
            return '0 seconds'
        d = total_sec // 86400
        h = (total_sec % 86400) // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        parts = []
        if d > 0:
            parts.append(f'{d} day{"s" if d != 1 else ""}')
        if h > 0:
            parts.append(f'{h} hour{"s" if h != 1 else ""}')
        if m > 0:
            parts.append(f'{m} minute{"s" if m != 1 else ""}')
        if s > 0:
            parts.append(f'{s} second{"s" if s != 1 else ""}')
        return ' '.join(parts)

    @staticmethod
    def _breakdown(total_sec):
        """Return h, m, s ints from total seconds."""
        ts = int(abs(total_sec))
        return ts // 3600, (ts % 3600) // 60, ts % 60

    # ── 1) BETWEEN TIMES ─────────────────────────────────────────────
    def _calc_between(self, data):
        st = data.get('start_time', '')
        et = data.get('end_time', '')
        if not st:
            return self._err(_('Start time is required.'))
        if not et:
            return self._err(_('End time is required.'))

        ss = self._parse_time(st)
        es = self._parse_time(et)
        if ss is None or es is None:
            return self._err(_('Invalid time format. Use HH:MM or HH:MM:SS (24-hour).'))

        # Handle midnight crossing
        if es < ss:
            dur = (86400 - ss) + es
            crosses = True
        else:
            dur = es - ss
            crosses = False

        h, m, s = self._breakdown(dur)
        dur_min = round(dur / 60, 2)
        dur_hrs = round(dur / 3600, 2)
        dur_days = round(dur / 86400, 4)
        dur_fmt = self._fmt_duration(dur)

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
            str(_('Step 4: Convert to other units')),
            f'  {_("Minutes")} = {dur_min}',
            f'  {_("Hours")} = {dur_hrs}',
            f'  {_("Days")} = {dur_days}',
            '',
            str(_('Result: {d}').format(d=dur_fmt)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Start')), str(_('End')), str(_('Duration'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [int(ss), int(es), int(dur)],
                    'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(99,102,241,0.7)',
                                        'rgba(139,92,246,0.7)'],
                    'borderColor': ['#3b82f6', '#6366f1', '#8b5cf6'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Time Duration'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'between_times',
            'result': dur_fmt, 'result_label': str(_('Duration Between Times')),
            'crosses_midnight': crosses,
            'duration_seconds': int(dur), 'duration_minutes': dur_min,
            'duration_hours': dur_hrs, 'duration_days': dur_days,
            'duration_formatted': dur_fmt,
            'formula': f'{st} → {et} = {dur_fmt}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Seconds')), 'value': str(int(dur)), 'color': 'blue'},
                {'label': str(_('Minutes')), 'value': str(dur_min), 'color': 'indigo'},
                {'label': str(_('Hours')), 'value': str(dur_hrs), 'color': 'purple'},
                {'label': str(_('Days')), 'value': str(dur_days), 'color': 'violet'},
            ],
        })

    # ── 2) ADD / SUBTRACT ────────────────────────────────────────────
    def _calc_add_subtract(self, data):
        ts = data.get('time', '')
        op = data.get('operation', 'add')
        dur_raw = data.get('duration')
        dur_unit = data.get('duration_unit', 'hours')

        if not ts:
            return self._err(_('Time is required.'))
        if dur_raw is None or dur_raw == '':
            return self._err(_('Duration is required.'))

        base = self._parse_time(ts)
        if base is None:
            return self._err(_('Invalid time format. Use HH:MM or HH:MM:SS (24-hour).'))

        try:
            dur_val = float(dur_raw)
        except (ValueError, TypeError):
            return self._err(_('Duration must be a number.'))
        if dur_val < 0:
            return self._err(_('Duration must be non-negative.'))
        if dur_unit not in self.UNITS:
            return self._err(_('Invalid duration unit.'))

        dur_sec = dur_val * self.UNITS[dur_unit]
        u_short = self.UNIT_SHORT.get(dur_unit, dur_unit)

        if op == 'add':
            result_sec = base + dur_sec
        else:
            result_sec = base - dur_sec
            if result_sec < 0:
                result_sec += 86400

        fmt = self._fmt_hms(result_sec)
        h, m, s = self._breakdown(result_sec)
        op_sym = '+' if op == 'add' else '−'

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Time")} = {ts}',
            f'  • {_("Operation")} = {op.title()}',
            f'  • {_("Duration")} = {dur_val} {u_short}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  {_("Time")} = {int(base)} {_("seconds")}',
            f'  {_("Duration")} = {dur_val} × {self.UNITS[dur_unit]:.0f} = {dur_sec:.0f} {_("seconds")}',
            '',
            str(_('Step 3: Calculate')),
            f'  {int(base)} {op_sym} {dur_sec:.0f} = {int(result_sec % 86400)} {_("seconds")}',
            '',
            str(_('Step 4: Convert to HH:MM:SS')),
            f'  {_("Hours")} = {h},  {_("Minutes")} = {m},  {_("Seconds")} = {s}',
            '',
            str(_('Result: {r}').format(r=fmt)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Original')), str(_('Duration')), str(_('Result'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [int(base), int(dur_sec), int(result_sec % 86400)],
                    'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(99,102,241,0.7)',
                                        'rgba(16,185,129,0.7)'],
                    'borderColor': ['#3b82f6', '#6366f1', '#10b981'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Add/Subtract Duration'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'add_subtract',
            'result': fmt, 'result_label': str(_('Result Time')),
            'formula': f'{ts} {op_sym} {dur_val} {u_short} = {fmt}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Original')), 'value': ts, 'color': 'blue'},
                {'label': str(_('Operation')), 'value': f'{op_sym} {dur_val} {u_short}', 'color': 'indigo'},
                {'label': str(_('Result')), 'value': fmt, 'color': 'green'},
                {'label': str(_('Total sec')), 'value': str(int(result_sec % 86400)), 'color': 'purple'},
            ],
        })

    # ── 3) CONVERT ───────────────────────────────────────────────────
    def _calc_convert(self, data):
        dur_raw = data.get('duration')
        from_u = data.get('from_unit', 'hours')
        to_u = data.get('to_unit', 'minutes')

        if dur_raw is None or dur_raw == '':
            return self._err(_('Duration is required.'))
        try:
            dur_val = float(dur_raw)
        except (ValueError, TypeError):
            return self._err(_('Duration must be a number.'))
        if dur_val < 0:
            return self._err(_('Duration must be non-negative.'))
        if from_u not in self.UNITS or to_u not in self.UNITS:
            return self._err(_('Invalid unit.'))

        dur_sec = dur_val * self.UNITS[from_u]
        result = round(dur_sec / self.UNITS[to_u], 6)
        fu = self.UNIT_SHORT.get(from_u, from_u)
        tu = self.UNIT_SHORT.get(to_u, to_u)

        # All conversions
        all_conv = {k: round(dur_sec / v, 6) for k, v in self.UNITS.items()}

        steps = [
            str(_('Step 1: Given value')),
            f'  {dur_val} {fu}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  {dur_val} × {self.UNITS[from_u]:.0f} = {dur_sec:.2f} {_("seconds")}',
            '',
            str(_('Step 3: Convert to {u}').format(u=tu)),
            f'  {dur_sec:.2f} ÷ {self.UNITS[to_u]:.0f} = {result} {tu}',
            '',
            str(_('Step 4: All conversions')),
        ]
        for k, v in all_conv.items():
            steps.append(f'  • {self.UNIT_SHORT[k]} = {v}')
        steps += ['', str(_('Result: {v} {u}').format(v=result, u=tu))]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [f'{dur_val} {fu}', f'{result} {tu}'],
                'datasets': [{
                    'label': str(_('Seconds equivalent')),
                    'data': [dur_sec, dur_sec],
                    'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(139,92,246,0.7)'],
                    'borderColor': ['#3b82f6', '#8b5cf6'],
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
            'formula': f'{dur_val} {fu} = {result} {tu}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Seconds')), 'value': str(all_conv['seconds']), 'color': 'blue'},
                {'label': str(_('Minutes')), 'value': str(all_conv['minutes']), 'color': 'indigo'},
                {'label': str(_('Hours')), 'value': str(all_conv['hours']), 'color': 'purple'},
                {'label': str(_('Days')), 'value': str(all_conv['days']), 'color': 'green'},
            ],
        })

    # ── 4) ELAPSED ───────────────────────────────────────────────────
    def _calc_elapsed(self, data):
        st = data.get('start_time', '')
        dur_raw = data.get('elapsed_duration')
        dur_unit = data.get('elapsed_unit', 'hours')

        if not st:
            return self._err(_('Start time is required.'))
        if dur_raw is None or dur_raw == '':
            return self._err(_('Elapsed duration is required.'))

        ss = self._parse_time(st)
        if ss is None:
            return self._err(_('Invalid time format. Use HH:MM or HH:MM:SS (24-hour).'))

        try:
            dur_val = float(dur_raw)
        except (ValueError, TypeError):
            return self._err(_('Duration must be a number.'))
        if dur_val < 0:
            return self._err(_('Duration must be non-negative.'))
        if dur_unit not in self.UNITS:
            return self._err(_('Invalid duration unit.'))

        dur_sec = dur_val * self.UNITS[dur_unit]
        end_sec = ss + dur_sec
        u_short = self.UNIT_SHORT.get(dur_unit, dur_unit)

        fmt = self._fmt_hms(end_sec)
        h, m, s = self._breakdown(end_sec % 86400)
        crosses = end_sec >= 86400
        days_elapsed = int(end_sec // 86400)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Start")} = {st}',
            f'  • {_("Elapsed")} = {dur_val} {u_short}',
            '',
            str(_('Step 2: Convert to seconds')),
            f'  {_("Start")} = {int(ss)} {_("seconds")}',
            f'  {_("Elapsed")} = {dur_val} × {self.UNITS[dur_unit]:.0f} = {dur_sec:.0f} {_("seconds")}',
            '',
            str(_('Step 3: Calculate end time')),
            f'  {int(ss)} + {dur_sec:.0f} = {int(end_sec)} {_("seconds")}',
        ]
        if crosses:
            steps.append(f'  ({days_elapsed} day{"s" if days_elapsed != 1 else ""} later)')
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
                'labels': [str(_('Start')), str(_('Elapsed')), str(_('End'))],
                'datasets': [{
                    'label': str(_('Seconds')),
                    'data': [int(ss), int(dur_sec), int(end_sec % 86400)],
                    'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(245,158,11,0.7)',
                                        'rgba(16,185,129,0.7)'],
                    'borderColor': ['#3b82f6', '#f59e0b', '#10b981'],
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Elapsed Time'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        detail_cards = [
            {'label': str(_('Start')), 'value': st, 'color': 'blue'},
            {'label': str(_('Elapsed')), 'value': f'{dur_val} {u_short}', 'color': 'yellow'},
            {'label': str(_('End')), 'value': fmt, 'color': 'green'},
            {'label': str(_('Total sec')), 'value': str(int(end_sec)), 'color': 'purple'},
        ]
        if crosses:
            detail_cards.append({'label': str(_('Days')), 'value': f'+{days_elapsed}', 'color': 'red'})

        return JsonResponse({
            'success': True, 'calc_type': 'elapsed',
            'result': fmt, 'result_label': str(_('End Time')),
            'crosses_midnight': crosses, 'days_elapsed': days_elapsed,
            'end_time_formatted': fmt,
            'formula': f'{st} + {dur_val} {u_short} = {fmt}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': detail_cards,
        })
