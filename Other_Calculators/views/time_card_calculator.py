from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TimeCardCalculator(View):
    """
    Time Card Calculator: daily hours, weekly hours, pay from hours.
    BMI-style upgrade.
    """
    template_name = 'other_calculators/time_card_calculator.html'

    STANDARD_WEEK_HOURS = 40.0
    OVERTIME_THRESHOLD = 8.0

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _val(self, data, key, default=None):
        v = data.get(key, default)
        return (v[0] if isinstance(v, list) and v else v) if v is not None else default

    def get(self, request):
        context = {'calculator_name': str(_('Time Card Calculator'))}
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid request data.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            calc_type = self._val(data, 'calc_type', 'daily')
            if calc_type == 'daily':
                result = self._calculate_daily(data)
            elif calc_type == 'weekly':
                result = self._calculate_weekly(data)
            elif calc_type == 'pay':
                result = self._calculate_pay(data)
            else:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid calculation type.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            if isinstance(result, dict) and not result.get('success'):
                return HttpResponse(
                    json.dumps(result, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            return HttpResponse(json.dumps(result, cls=SafeJSONEncoder), content_type='application/json')
        except Exception as e:
            logger.exception("Time card calculator failed: %s", e)
            from django.conf import settings
            err_msg = str(_('An error occurred during calculation.'))
            if getattr(settings, 'DEBUG', False):
                err_msg += ' [' + str(e).replace('"', "'") + ']'
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}, cls=SafeJSONEncoder),
                content_type='application/json',
                status=500
            )

    def _parse_time(self, time_str):
        try:
            if ':' in str(time_str):
                parts = str(time_str).split(':')
                if len(parts) == 2:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = 0
                elif len(parts) == 3:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = int(parts[2])
                else:
                    return None
                return hours * 3600 + minutes * 60 + seconds
            return float(time_str)
        except Exception:
            return None

    def _seconds_to_hours(self, seconds):
        return float(seconds / 3600.0)

    def _format_time(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _calculate_daily(self, data):
        clock_in_str = self._val(data, 'clock_in', '')
        clock_out_str = self._val(data, 'clock_out', '')
        if not clock_in_str:
            return {'success': False, 'error': str(_('Clock in time is required.'))}
        if not clock_out_str:
            return {'success': False, 'error': str(_('Clock out time is required.'))}
        try:
            break_minutes = float(self._val(data, 'break_minutes', 0) or 0)
        except (ValueError, TypeError):
            break_minutes = 0.0
        clock_in_seconds = self._parse_time(clock_in_str)
        clock_out_seconds = self._parse_time(clock_out_str)
        if clock_in_seconds is None or clock_out_seconds is None:
            return {'success': False, 'error': str(_('Invalid time format. Use HH:MM or HH:MM:SS format.'))}
        if clock_out_seconds < clock_in_seconds:
            clock_out_seconds += 86400
        total_seconds = clock_out_seconds - clock_in_seconds
        break_seconds = break_minutes * 60
        worked_seconds = total_seconds - break_seconds
        if worked_seconds < 0:
            return {'success': False, 'error': str(_('Break time cannot exceed total time.'))}
        total_hours = self._seconds_to_hours(total_seconds)
        break_hours = self._seconds_to_hours(break_seconds)
        worked_hours = self._seconds_to_hours(worked_seconds)
        regular_hours = min(worked_hours, self.OVERTIME_THRESHOLD)
        overtime_hours = max(0.0, worked_hours - self.OVERTIME_THRESHOLD)
        steps = self._prepare_daily_steps(
            clock_in_str, clock_out_str, clock_in_seconds, clock_out_seconds, total_seconds,
            break_minutes, break_seconds, worked_seconds, total_hours, break_hours, worked_hours,
            regular_hours, overtime_hours
        )
        chart_data = self._prepare_daily_chart_data(regular_hours, overtime_hours, break_hours)
        return {
            'success': True,
            'calc_type': 'daily',
            'clock_in': clock_in_str,
            'clock_out': clock_out_str,
            'break_minutes': break_minutes,
            'total_hours': round(total_hours, 2),
            'break_hours': round(break_hours, 2),
            'worked_hours': round(worked_hours, 2),
            'regular_hours': round(regular_hours, 2),
            'overtime_hours': round(overtime_hours, 2),
            'total_formatted': self._format_time(total_seconds),
            'worked_formatted': self._format_time(worked_seconds),
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _calculate_weekly(self, data):
        days_raw = data.get('days')
        if not days_raw:
            return {'success': False, 'error': str(_('At least one day is required.'))}
        days = days_raw if isinstance(days_raw, list) else []
        if len(days) == 0:
            return {'success': False, 'error': str(_('At least one day is required.'))}
        total_worked_hours = 0.0
        total_regular_hours = 0.0
        total_overtime_hours = 0.0
        daily_breakdown = []
        for day_data in days:
            clock_in_str = day_data.get('clock_in', '') if isinstance(day_data, dict) else ''
            clock_out_str = day_data.get('clock_out', '') if isinstance(day_data, dict) else ''
            try:
                break_minutes = float(day_data.get('break_minutes', 0) or 0) if isinstance(day_data, dict) else 0
            except (ValueError, TypeError):
                break_minutes = 0
            clock_in_seconds = self._parse_time(clock_in_str)
            clock_out_seconds = self._parse_time(clock_out_str)
            if clock_in_seconds is None or clock_out_seconds is None:
                continue
            if clock_out_seconds < clock_in_seconds:
                clock_out_seconds += 86400
            total_seconds = clock_out_seconds - clock_in_seconds
            break_seconds = break_minutes * 60
            worked_seconds = total_seconds - break_seconds
            if worked_seconds < 0:
                continue
            worked_hours = self._seconds_to_hours(worked_seconds)
            regular_hours = min(worked_hours, self.OVERTIME_THRESHOLD)
            overtime_hours = max(0.0, worked_hours - self.OVERTIME_THRESHOLD)
            total_worked_hours += worked_hours
            total_regular_hours += regular_hours
            total_overtime_hours += overtime_hours
            daily_breakdown.append({
                'day': day_data.get('day', '') if isinstance(day_data, dict) else '',
                'worked_hours': round(worked_hours, 2),
                'regular_hours': round(regular_hours, 2),
                'overtime_hours': round(overtime_hours, 2),
            })
        if not daily_breakdown:
            return {'success': False, 'error': str(_('At least one day with valid clock in/out is required.'))}
        weekly_regular = min(total_worked_hours, self.STANDARD_WEEK_HOURS)
        weekly_overtime = max(0.0, total_worked_hours - self.STANDARD_WEEK_HOURS)
        steps = self._prepare_weekly_steps(daily_breakdown, total_worked_hours, total_regular_hours, total_overtime_hours, weekly_regular, weekly_overtime)
        chart_data = self._prepare_weekly_chart_data(daily_breakdown, total_worked_hours, weekly_regular, weekly_overtime)
        return {
            'success': True,
            'calc_type': 'weekly',
            'total_worked_hours': round(total_worked_hours, 2),
            'total_regular_hours': round(total_regular_hours, 2),
            'total_overtime_hours': round(total_overtime_hours, 2),
            'weekly_regular': round(weekly_regular, 2),
            'weekly_overtime': round(weekly_overtime, 2),
            'daily_breakdown': daily_breakdown,
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _calculate_pay(self, data):
        regular_raw = self._val(data, 'regular_hours')
        if regular_raw is None or regular_raw == '':
            return {'success': False, 'error': str(_('Regular hours is required.'))}
        try:
            regular_hours = float(regular_raw)
            overtime_hours = float(self._val(data, 'overtime_hours') or 0)
            hourly_rate = float(self._val(data, 'hourly_rate') or 0)
            overtime_multiplier = float(self._val(data, 'overtime_multiplier') or 1.5)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter numeric values.'))}
        currency = self._val(data, 'currency', 'usd') or 'usd'
        if regular_hours < 0 or overtime_hours < 0:
            return {'success': False, 'error': str(_('Hours must be non-negative.'))}
        if hourly_rate < 0:
            return {'success': False, 'error': str(_('Hourly rate must be non-negative.'))}
        regular_pay = regular_hours * hourly_rate
        overtime_rate = hourly_rate * overtime_multiplier
        overtime_pay = overtime_hours * overtime_rate
        total_pay = regular_pay + overtime_pay
        steps = self._prepare_pay_steps(regular_hours, overtime_hours, hourly_rate, overtime_multiplier, regular_pay, overtime_rate, overtime_pay, total_pay, currency)
        chart_data = self._prepare_pay_chart_data(regular_pay, overtime_pay, total_pay)
        return {
            'success': True,
            'calc_type': 'pay',
            'regular_hours': regular_hours,
            'overtime_hours': overtime_hours,
            'hourly_rate': hourly_rate,
            'overtime_multiplier': overtime_multiplier,
            'regular_pay': round(regular_pay, 2),
            'overtime_pay': round(overtime_pay, 2),
            'total_pay': round(total_pay, 2),
            'currency': currency,
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _prepare_daily_steps(self, clock_in_str, clock_out_str, clock_in_seconds, clock_out_seconds, total_seconds, break_minutes, break_seconds, worked_seconds, total_hours, break_hours, worked_hours, regular_hours, overtime_hours):
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Clock In: {time}')).format(time=clock_in_str))
        steps.append(str(_('Clock Out: {time}')).format(time=clock_out_str))
        steps.append(str(_('Break Time: {break_time} minutes')).format(break_time=break_minutes))
        steps.append('')
        steps.append(str(_('Step 2: Convert to seconds')))
        steps.append(str(_('Clock In: {time} = {seconds} seconds')).format(time=clock_in_str, seconds=clock_in_seconds))
        steps.append(str(_('Clock Out: {time} = {seconds} seconds')).format(time=clock_out_str, seconds=clock_out_seconds))
        steps.append('')
        steps.append(str(_('Step 3: Calculate total time')))
        steps.append(str(_('Total Time = Clock Out - Clock In')))
        steps.append(str(_('Total Time = {out} - {clock_in} = {total} seconds')).format(out=clock_out_seconds, clock_in=clock_in_seconds, total=total_seconds))
        steps.append(str(_('Total Time = {hours} hours')).format(hours=round(total_hours, 2)))
        steps.append('')
        steps.append(str(_('Step 4: Subtract break time')))
        steps.append(str(_('Break Time = {break_time} minutes = {seconds} seconds = {hours} hours')).format(break_time=break_minutes, seconds=break_seconds, hours=round(break_hours, 2)))
        steps.append(str(_('Worked Time = Total Time - Break Time')))
        steps.append(str(_('Worked Time = {total} - {break_time} = {worked} hours')).format(total=round(total_hours, 2), break_time=round(break_hours, 2), worked=round(worked_hours, 2)))
        steps.append('')
        steps.append(str(_('Step 5: Calculate regular and overtime')))
        steps.append(str(_('Regular Hours = min(Worked Hours, {threshold}) = {regular} hours')).format(threshold=self.OVERTIME_THRESHOLD, regular=round(regular_hours, 2)))
        steps.append(str(_('Overtime Hours = max(0, Worked Hours - {threshold}) = {overtime} hours')).format(threshold=self.OVERTIME_THRESHOLD, overtime=round(overtime_hours, 2)))
        return steps

    def _prepare_weekly_steps(self, daily_breakdown, total_worked_hours, total_regular_hours, total_overtime_hours, weekly_regular, weekly_overtime):
        steps = []
        steps.append(str(_('Step 1: Calculate hours for each day')))
        for breakdown in daily_breakdown:
            steps.append(str(_('{day}: {hours} hours ({regular} regular, {overtime} overtime)')).format(
                day=breakdown['day'],
                hours=breakdown['worked_hours'],
                regular=breakdown['regular_hours'],
                overtime=breakdown['overtime_hours']
            ))
        steps.append('')
        steps.append(str(_('Step 2: Sum daily hours')))
        steps.append(str(_('Total Worked Hours = {total} hours')).format(total=round(total_worked_hours, 2)))
        steps.append(str(_('Total Regular Hours = {regular} hours')).format(regular=round(total_regular_hours, 2)))
        steps.append(str(_('Total Overtime Hours = {overtime} hours')).format(overtime=round(total_overtime_hours, 2)))
        steps.append('')
        steps.append(str(_('Step 3: Calculate weekly overtime')))
        steps.append(str(_('Weekly Regular = min(Total Hours, {threshold}) = {regular} hours')).format(threshold=self.STANDARD_WEEK_HOURS, regular=round(weekly_regular, 2)))
        steps.append(str(_('Weekly Overtime = max(0, Total Hours - {threshold}) = {overtime} hours')).format(threshold=self.STANDARD_WEEK_HOURS, overtime=round(weekly_overtime, 2)))
        return steps

    def _prepare_pay_steps(self, regular_hours, overtime_hours, hourly_rate, overtime_multiplier, regular_pay, overtime_rate, overtime_pay, total_pay, currency):
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Regular Hours: {hours}')).format(hours=regular_hours))
        steps.append(str(_('Overtime Hours: {hours}')).format(hours=overtime_hours))
        steps.append(str(_('Hourly Rate: {rate} {currency}')).format(rate=hourly_rate, currency=(currency or 'usd').upper()))
        steps.append(str(_('Overtime Multiplier: {mult}')).format(mult=overtime_multiplier))
        steps.append('')
        steps.append(str(_('Step 2: Calculate regular pay')))
        steps.append(str(_('Regular Pay = Regular Hours × Hourly Rate')))
        steps.append(str(_('Regular Pay = {hours} × {rate} = {pay} {currency}')).format(hours=regular_hours, rate=hourly_rate, pay=round(regular_pay, 2), currency=(currency or 'usd').upper()))
        steps.append('')
        steps.append(str(_('Step 3: Calculate overtime rate')))
        steps.append(str(_('Overtime Rate = Hourly Rate × Multiplier')))
        steps.append(str(_('Overtime Rate = {rate} × {mult} = {overtime_rate} {currency}')).format(rate=hourly_rate, mult=overtime_multiplier, overtime_rate=round(overtime_rate, 2), currency=(currency or 'usd').upper()))
        steps.append('')
        steps.append(str(_('Step 4: Calculate overtime pay')))
        steps.append(str(_('Overtime Pay = Overtime Hours × Overtime Rate')))
        steps.append(str(_('Overtime Pay = {hours} × {rate} = {pay} {currency}')).format(hours=overtime_hours, rate=round(overtime_rate, 2), pay=round(overtime_pay, 2), currency=(currency or 'usd').upper()))
        steps.append('')
        steps.append(str(_('Step 5: Calculate total pay')))
        steps.append(str(_('Total Pay = Regular Pay + Overtime Pay')))
        steps.append(str(_('Total Pay = {regular} + {overtime} = {total} {currency}')).format(regular=round(regular_pay, 2), overtime=round(overtime_pay, 2), total=round(total_pay, 2), currency=(currency or 'usd').upper()))
        return steps

    def _prepare_daily_chart_data(self, regular_hours, overtime_hours, break_hours):
        chart_config = {
            'type': 'pie',
            'data': {
                'labels': [str(_('Regular Hours')), str(_('Overtime Hours')), str(_('Break Time'))],
                'datasets': [{
                    'data': [max(0.01, regular_hours), max(0.01, overtime_hours), max(0.01, break_hours)],
                    'backgroundColor': ['#6366f1', '#8b5cf6', '#e5e7eb'],
                    'borderColor': ['#4f46e5', '#7c3aed', '#d1d5db'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True, 'position': 'bottom'},
                    'title': {'display': True, 'text': str(_('Daily Hours Breakdown'))}
                }
            }
        }
        return {'daily_chart': chart_config}

    def _prepare_weekly_chart_data(self, daily_breakdown, total_worked_hours, weekly_regular, weekly_overtime):
        days = [d['day'] for d in daily_breakdown]
        hours = [d['worked_hours'] for d in daily_breakdown]
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': days + [str(_('Total'))],
                'datasets': [{
                    'label': str(_('Hours Worked')),
                    'data': hours + [total_worked_hours],
                    'backgroundColor': ['#6366f1'] * len(days) + ['#8b5cf6'],
                    'borderColor': ['#4f46e5'] * len(days) + ['#7c3aed'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': str(_('Weekly Hours Worked'))}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {'display': True, 'text': str(_('Hours'))}
                    }
                }
            }
        }
        return {'weekly_chart': chart_config}

    def _prepare_pay_chart_data(self, regular_pay, overtime_pay, total_pay):
        chart_config = {
            'type': 'pie',
            'data': {
                'labels': [str(_('Regular Pay')), str(_('Overtime Pay'))],
                'datasets': [{
                    'data': [max(0.01, regular_pay), max(0.01, overtime_pay)],
                    'backgroundColor': ['#6366f1', '#8b5cf6'],
                    'borderColor': ['#4f46e5', '#7c3aed'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True, 'position': 'bottom'},
                    'title': {'display': True, 'text': str(_('Pay Breakdown (Total: {total})')).format(total=total_pay)}
                }
            }
        }
        return {'pay_chart': chart_config}
