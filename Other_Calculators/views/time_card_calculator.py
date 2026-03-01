from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TimeCardCalculator(View):
    """
    Time Card Calculator — 4 calculation types.

    Calculation types
        • weekly       → full week timecard (up to 7 days) with overtime
        • daily        → single day with breaks and overtime
        • payroll      → calculate pay from hours + rate
        • overtime     → overtime analysis with thresholds
    """
    template_name = 'other_calculators/time_card_calculator.html'

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Time Card Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'weekly')
            dispatch = {
                'weekly':   self._calc_weekly,
                'daily':    self._calc_daily,
                'payroll':  self._calc_payroll,
                'overtime': self._calc_overtime,
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
        """Parse HH:MM → minutes from midnight. Returns None on failure."""
        if not val:
            return None
        s = str(val).strip()
        if ':' not in s:
            return None
        parts = s.split(':')
        try:
            h, m = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return None
        if not (0 <= h <= 23 and 0 <= m <= 59):
            return None
        return h * 60 + m

    @staticmethod
    def _fmt_hm(minutes):
        """Format minutes → Xh Ym string."""
        if minutes < 0:
            minutes = 0
        h = int(minutes) // 60
        m = int(minutes) % 60
        if h == 0:
            return f'{m}m'
        if m == 0:
            return f'{h}h'
        return f'{h}h {m}m'

    @staticmethod
    def _minutes_to_hours(minutes):
        """Minutes → decimal hours, rounded to 2 places."""
        return round(minutes / 60, 2)

    @staticmethod
    def _duration_minutes(start_min, end_min):
        """Calculate duration in minutes, handling midnight crossing."""
        if end_min < start_min:
            return (1440 - start_min) + end_min
        return end_min - start_min

    DAYS = [
        str(_('Monday')), str(_('Tuesday')), str(_('Wednesday')),
        str(_('Thursday')), str(_('Friday')), str(_('Saturday')), str(_('Sunday')),
    ]

    # ── 1) WEEKLY ────────────────────────────────────────────────────
    def _calc_weekly(self, data):
        entries = data.get('entries', [])
        ot_threshold = float(data.get('overtime_threshold', 40))
        ot_rate = float(data.get('overtime_rate', 1.5))
        hourly_rate = float(data.get('hourly_rate', 0))

        if not entries or len(entries) == 0:
            return self._err(_('At least one day entry is required.'))
        if len(entries) > 7:
            return self._err(_('Maximum 7 day entries allowed.'))

        daily_results = []
        total_minutes = 0
        labels = []
        hours_data = []

        for i, entry in enumerate(entries):
            clock_in = self._parse_time(entry.get('clock_in'))
            clock_out = self._parse_time(entry.get('clock_out'))
            break_min = float(entry.get('break_minutes', 0))
            day_name = entry.get('day', self.DAYS[i] if i < 7 else f'Day {i+1}')

            if clock_in is None or clock_out is None:
                daily_results.append({
                    'day': day_name, 'clock_in': '-', 'clock_out': '-',
                    'break': 0, 'gross': '0h', 'net': '0h',
                    'net_minutes': 0, 'net_hours': 0,
                })
                labels.append(day_name)
                hours_data.append(0)
                continue

            gross = self._duration_minutes(clock_in, clock_out)
            net = max(0, gross - break_min)
            total_minutes += net

            daily_results.append({
                'day': day_name,
                'clock_in': entry.get('clock_in', '-'),
                'clock_out': entry.get('clock_out', '-'),
                'break': int(break_min),
                'gross': self._fmt_hm(gross),
                'net': self._fmt_hm(net),
                'net_minutes': int(net),
                'net_hours': self._minutes_to_hours(net),
            })
            labels.append(day_name)
            hours_data.append(self._minutes_to_hours(net))

        total_hours = self._minutes_to_hours(total_minutes)
        regular_hours = min(total_hours, ot_threshold)
        overtime_hours = max(0, total_hours - ot_threshold)

        regular_pay = round(regular_hours * hourly_rate, 2) if hourly_rate > 0 else 0
        overtime_pay = round(overtime_hours * hourly_rate * ot_rate, 2) if hourly_rate > 0 else 0
        total_pay = round(regular_pay + overtime_pay, 2)

        steps = [
            str(_('Step 1: Daily hours')),
        ]
        for dr in daily_results:
            steps.append(f'  • {dr["day"]}: {dr["clock_in"]} → {dr["clock_out"]} − {dr["break"]}m break = {dr["net"]}')
        steps += [
            '',
            str(_('Step 2: Total hours')),
            f'  {_("Total")} = {total_hours}h ({self._fmt_hm(total_minutes)})',
            '',
            str(_('Step 3: Overtime calculation')),
            f'  {_("Threshold")} = {ot_threshold}h',
            f'  {_("Regular")} = {regular_hours}h',
            f'  {_("Overtime")} = {overtime_hours}h (×{ot_rate})',
        ]
        if hourly_rate > 0:
            steps += [
                '',
                str(_('Step 4: Pay calculation')),
                f'  {_("Rate")} = ${hourly_rate}/hr',
                f'  {_("Regular pay")} = {regular_hours} × ${hourly_rate} = ${regular_pay}',
                f'  {_("Overtime pay")} = {overtime_hours} × ${hourly_rate} × {ot_rate} = ${overtime_pay}',
                f'  {_("Total pay")} = ${total_pay}',
            ]
        steps += ['', str(_('Result: {h}h total, {ot}h overtime').format(h=total_hours, ot=overtime_hours))]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Hours')),
                    'data': hours_data,
                    'backgroundColor': 'rgba(99,102,241,0.7)',
                    'borderColor': '#6366f1',
                    'borderWidth': 2, 'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Hours by Day'))}},
                'scales': {'y': {'beginAtZero': True,
                                 'title': {'display': True, 'text': str(_('Hours'))}}},
            },
        }}

        detail_cards = [
            {'label': str(_('Total')), 'value': f'{total_hours}h', 'color': 'indigo'},
            {'label': str(_('Regular')), 'value': f'{regular_hours}h', 'color': 'green'},
            {'label': str(_('Overtime')), 'value': f'{overtime_hours}h', 'color': 'red'},
            {'label': str(_('Days')), 'value': str(len(entries)), 'color': 'blue'},
        ]
        if hourly_rate > 0:
            detail_cards.append({'label': str(_('Total Pay')), 'value': f'${total_pay}', 'color': 'purple'})

        return JsonResponse({
            'success': True, 'calc_type': 'weekly',
            'result': f'{total_hours}h',
            'result_label': str(_('Weekly Total Hours')),
            'daily_results': daily_results,
            'total_hours': total_hours,
            'regular_hours': regular_hours,
            'overtime_hours': overtime_hours,
            'total_pay': total_pay if hourly_rate > 0 else None,
            'formula': f'{len(entries)} days → {total_hours}h ({overtime_hours}h OT)',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': detail_cards,
        })

    # ── 2) DAILY ─────────────────────────────────────────────────────
    def _calc_daily(self, data):
        ci = data.get('clock_in', '')
        co = data.get('clock_out', '')
        brk = float(data.get('break_minutes', 0))
        ot_after = float(data.get('overtime_after', 8))

        if not ci or not co:
            return self._err(_('Clock in and clock out times are required.'))

        ci_min = self._parse_time(ci)
        co_min = self._parse_time(co)
        if ci_min is None or co_min is None:
            return self._err(_('Invalid time format. Use HH:MM (24-hour).'))

        gross = self._duration_minutes(ci_min, co_min)
        net = max(0, gross - brk)

        net_hours = self._minutes_to_hours(net)
        regular = min(net_hours, ot_after)
        overtime = max(0, net_hours - ot_after)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Clock In")} = {ci}',
            f'  • {_("Clock Out")} = {co}',
            f'  • {_("Break")} = {int(brk)} {_("minutes")}',
            '',
            str(_('Step 2: Calculate gross hours')),
            f'  {co} − {ci} = {self._fmt_hm(gross)} ({self._minutes_to_hours(gross)}h)',
            '',
            str(_('Step 3: Subtract break')),
            f'  {self._fmt_hm(gross)} − {int(brk)}m = {self._fmt_hm(net)} ({net_hours}h)',
            '',
            str(_('Step 4: Overtime (after {t}h)').format(t=ot_after)),
            f'  {_("Regular")} = {regular}h',
            f'  {_("Overtime")} = {overtime}h',
            '',
            str(_('Result: {h} net hours').format(h=net_hours)),
        ]

        chart = {'main_chart': {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Work')), str(_('Break'))],
                'datasets': [{
                    'data': [int(net), int(brk)],
                    'backgroundColor': ['rgba(99,102,241,0.8)', 'rgba(239,68,68,0.6)'],
                    'borderWidth': 2, 'borderColor': '#fff',
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'position': 'bottom'},
                            'title': {'display': True, 'text': str(_('Work vs Break'))}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'daily',
            'result': self._fmt_hm(net),
            'result_label': str(_('Net Working Time')),
            'gross_hours': self._minutes_to_hours(gross),
            'net_hours': net_hours,
            'regular_hours': regular,
            'overtime_hours': overtime,
            'formula': f'{ci} → {co} − {int(brk)}m = {self._fmt_hm(net)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Gross')), 'value': self._fmt_hm(gross), 'color': 'blue'},
                {'label': str(_('Net')), 'value': self._fmt_hm(net), 'color': 'indigo'},
                {'label': str(_('Regular')), 'value': f'{regular}h', 'color': 'green'},
                {'label': str(_('Overtime')), 'value': f'{overtime}h', 'color': 'red'},
            ],
        })

    # ── 3) PAYROLL ───────────────────────────────────────────────────
    def _calc_payroll(self, data):
        reg_hours = float(data.get('regular_hours', 0))
        ot_hours = float(data.get('overtime_hours', 0))
        hourly_rate = float(data.get('hourly_rate', 0))
        ot_rate = float(data.get('overtime_rate', 1.5))

        if hourly_rate <= 0:
            return self._err(_('Hourly rate must be greater than zero.'))
        if reg_hours < 0 or ot_hours < 0:
            return self._err(_('Hours must be non-negative.'))

        reg_pay = round(reg_hours * hourly_rate, 2)
        ot_pay = round(ot_hours * hourly_rate * ot_rate, 2)
        gross_pay = round(reg_pay + ot_pay, 2)
        total_hours = round(reg_hours + ot_hours, 2)

        # Common deduction estimates
        fed_tax = round(gross_pay * 0.22, 2)     # ~22% federal
        state_tax = round(gross_pay * 0.05, 2)   # ~5% state
        fica = round(gross_pay * 0.0765, 2)      # 7.65% FICA
        total_deductions = round(fed_tax + state_tax + fica, 2)
        net_pay = round(gross_pay - total_deductions, 2)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Regular hours")} = {reg_hours}h',
            f'  • {_("Overtime hours")} = {ot_hours}h',
            f'  • {_("Hourly rate")} = ${hourly_rate}',
            f'  • {_("OT multiplier")} = {ot_rate}×',
            '',
            str(_('Step 2: Calculate pay')),
            f'  {_("Regular pay")} = {reg_hours} × ${hourly_rate} = ${reg_pay}',
            f'  {_("OT pay")} = {ot_hours} × ${hourly_rate} × {ot_rate} = ${ot_pay}',
            f'  {_("Gross pay")} = ${reg_pay} + ${ot_pay} = ${gross_pay}',
            '',
            str(_('Step 3: Estimated deductions')),
            f'  {_("Federal tax")} (~22%) = ${fed_tax}',
            f'  {_("State tax")} (~5%) = ${state_tax}',
            f'  FICA (7.65%) = ${fica}',
            f'  {_("Total deductions")} = ${total_deductions}',
            '',
            str(_('Step 4: Net pay')),
            f'  ${gross_pay} − ${total_deductions} = ${net_pay}',
            '',
            str(_('Result: Gross ${g}, Net ${n}').format(g=gross_pay, n=net_pay)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Regular')), str(_('Overtime')), str(_('Gross')),
                           str(_('Deductions')), str(_('Net'))],
                'datasets': [{
                    'label': '$',
                    'data': [reg_pay, ot_pay, gross_pay, total_deductions, net_pay],
                    'backgroundColor': [
                        'rgba(16,185,129,0.7)', 'rgba(245,158,11,0.7)',
                        'rgba(99,102,241,0.7)', 'rgba(239,68,68,0.7)',
                        'rgba(59,130,246,0.7)'],
                    'borderRadius': 6, 'borderWidth': 2,
                    'borderColor': ['#10b981', '#f59e0b', '#6366f1', '#ef4444', '#3b82f6'],
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Pay Breakdown'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'payroll',
            'result': f'${gross_pay}',
            'result_label': str(_('Gross Pay')),
            'regular_pay': reg_pay, 'overtime_pay': ot_pay,
            'gross_pay': gross_pay, 'net_pay': net_pay,
            'deductions': total_deductions,
            'formula': f'{reg_hours}h + {ot_hours}h OT @ ${hourly_rate}/hr = ${gross_pay}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Gross')), 'value': f'${gross_pay}', 'color': 'indigo'},
                {'label': str(_('Regular')), 'value': f'${reg_pay}', 'color': 'green'},
                {'label': str(_('OT Pay')), 'value': f'${ot_pay}', 'color': 'yellow'},
                {'label': str(_('Net')), 'value': f'${net_pay}', 'color': 'blue'},
            ],
        })

    # ── 4) OVERTIME ANALYSIS ─────────────────────────────────────────
    def _calc_overtime(self, data):
        total_hours = float(data.get('total_hours', 0))
        threshold = float(data.get('threshold', 40))
        ot_rate = float(data.get('overtime_rate', 1.5))
        double_threshold = float(data.get('double_threshold', 60))
        double_rate = float(data.get('double_rate', 2.0))
        hourly_rate = float(data.get('hourly_rate', 0))

        if total_hours < 0:
            return self._err(_('Total hours must be non-negative.'))
        if threshold <= 0:
            return self._err(_('Overtime threshold must be positive.'))

        regular = min(total_hours, threshold)

        if total_hours > double_threshold:
            time_and_half = double_threshold - threshold if double_threshold > threshold else 0
            double_time = total_hours - double_threshold
        else:
            time_and_half = max(0, total_hours - threshold)
            double_time = 0

        total_ot = round(time_and_half + double_time, 2)

        if hourly_rate > 0:
            reg_pay = round(regular * hourly_rate, 2)
            ot_pay = round(time_and_half * hourly_rate * ot_rate, 2)
            dt_pay = round(double_time * hourly_rate * double_rate, 2)
            total_pay = round(reg_pay + ot_pay + dt_pay, 2)
        else:
            reg_pay = ot_pay = dt_pay = total_pay = 0

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Total hours")} = {total_hours}h',
            f'  • {_("OT threshold")} = {threshold}h (×{ot_rate})',
            f'  • {_("Double-time threshold")} = {double_threshold}h (×{double_rate})',
            '',
            str(_('Step 2: Break down hours')),
            f'  {_("Regular")} = min({total_hours}, {threshold}) = {regular}h',
            f'  {_("Time-and-half")} = {round(time_and_half, 2)}h',
            f'  {_("Double-time")} = {round(double_time, 2)}h',
            f'  {_("Total overtime")} = {total_ot}h',
        ]

        if hourly_rate > 0:
            steps += [
                '',
                str(_('Step 3: Pay calculation')),
                f'  {_("Rate")} = ${hourly_rate}/hr',
                f'  {_("Regular")} = {regular} × ${hourly_rate} = ${reg_pay}',
                f'  {_("OT")} = {round(time_and_half, 2)} × ${hourly_rate} × {ot_rate} = ${ot_pay}',
                f'  {_("Double")} = {round(double_time, 2)} × ${hourly_rate} × {double_rate} = ${dt_pay}',
                f'  {_("Total")} = ${total_pay}',
            ]

        pct_ot = round((total_ot / total_hours * 100), 1) if total_hours > 0 else 0
        steps += ['', str(_('Result: {r}h regular, {ot}h overtime ({pct}%)').format(
            r=regular, ot=total_ot, pct=pct_ot))]

        chart = {'main_chart': {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Regular')), str(_('Time-and-half')), str(_('Double-time'))],
                'datasets': [{
                    'data': [regular, round(time_and_half, 2), round(double_time, 2)],
                    'backgroundColor': ['rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)',
                                        'rgba(239,68,68,0.8)'],
                    'borderWidth': 2, 'borderColor': '#fff',
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'position': 'bottom'},
                            'title': {'display': True, 'text': str(_('Hours Breakdown'))}},
            },
        }}

        detail_cards = [
            {'label': str(_('Regular')), 'value': f'{regular}h', 'color': 'green'},
            {'label': str(_('OT (1.5×)')), 'value': f'{round(time_and_half, 2)}h', 'color': 'yellow'},
            {'label': str(_('DT (2×)')), 'value': f'{round(double_time, 2)}h', 'color': 'red'},
            {'label': str(_('OT %')), 'value': f'{pct_ot}%', 'color': 'purple'},
        ]
        if hourly_rate > 0:
            detail_cards.append({'label': str(_('Total Pay')), 'value': f'${total_pay}', 'color': 'indigo'})

        return JsonResponse({
            'success': True, 'calc_type': 'overtime',
            'result': f'{total_ot}h OT',
            'result_label': str(_('Overtime Analysis')),
            'regular_hours': regular,
            'time_and_half': round(time_and_half, 2),
            'double_time': round(double_time, 2),
            'total_overtime': total_ot,
            'overtime_pct': pct_ot,
            'total_pay': total_pay if hourly_rate > 0 else None,
            'formula': f'{total_hours}h → {regular}h reg + {total_ot}h OT',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': detail_cards,
        })
