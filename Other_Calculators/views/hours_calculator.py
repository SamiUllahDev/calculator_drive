from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import math
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
class HoursCalculator(View):
    """
    Hours Calculator: time difference, add/subtract hours, convert units,
    total hours from periods, hours worked. BMI-style upgrade.
    """
    template_name = 'other_calculators/hours_calculator.html'

    HOURS_TO_MINUTES = 60.0
    MINUTES_TO_HOURS = 1.0 / 60.0
    HOURS_TO_SECONDS = 3600.0
    SECONDS_TO_HOURS = 1.0 / 3600.0
    HOURS_TO_DAYS = 1.0 / 24.0
    DAYS_TO_HOURS = 24.0

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
        context = {'calculator_name': str(_('Hours Calculator'))}
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
            calc_type = self._val(data, 'calc_type', 'time_difference')
            if calc_type == 'time_difference':
                result = self._calculate_time_difference(data)
            elif calc_type == 'add_subtract':
                result = self._add_subtract_hours(data)
            elif calc_type == 'convert':
                result = self._convert_time_units(data)
            elif calc_type == 'total_hours':
                result = self._calculate_total_hours(data)
            elif calc_type == 'hours_worked':
                result = self._calculate_hours_worked(data)
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
            logger.exception("Hours calculator failed: %s", e)
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
            parts = str(time_str).split(':')
            if len(parts) == 2:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), 0
            elif len(parts) == 3:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                raise ValueError(str(_('Invalid time format')))
            if hours < 0 or hours >= 24 or minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
                raise ValueError(str(_('Invalid time values')))
            return hours, minutes, seconds
        except (ValueError, IndexError, TypeError):
            raise ValueError(str(_('Invalid time format')) + ': ' + str(time_str))

    def _time_to_hours(self, hours, minutes, seconds):
        return float(hours) + minutes * self.MINUTES_TO_HOURS + seconds * self.SECONDS_TO_HOURS

    def _hours_to_time(self, decimal_hours):
        hours = int(decimal_hours)
        remaining = decimal_hours - hours
        minutes_decimal = remaining * self.HOURS_TO_MINUTES
        minutes = int(minutes_decimal)
        seconds_decimal = minutes_decimal - minutes
        seconds = int(round(seconds_decimal * self.HOURS_TO_MINUTES))
        if seconds >= 60:
            seconds = 0
            minutes += 1
        if minutes >= 60:
            minutes = 0
            hours += 1
        return hours, minutes, seconds

    def _calculate_time_difference(self, data):
        start_time_str = self._val(data, 'start_time', '').strip() or ''
        end_time_str = self._val(data, 'end_time', '').strip() or ''
        if not start_time_str:
            return {'success': False, 'error': str(_('Start time is required.'))}
        if not end_time_str:
            return {'success': False, 'error': str(_('End time is required.'))}
        try:
            start_h, start_m, start_s = self._parse_time(start_time_str)
            end_h, end_m, end_s = self._parse_time(end_time_str)
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        next_day = data.get('next_day') in (True, 'true', 'True', 1, '1')
        start_hours = self._time_to_hours(start_h, start_m, start_s)
        end_hours = self._time_to_hours(end_h, end_m, end_s)
        if end_hours < start_hours and not next_day:
            next_day = True
        if next_day:
            end_hours += 24.0
        difference_hours = end_hours - start_hours
        if difference_hours < 0:
            return {'success': False, 'error': str(_('End time must be after start time.'))}
        if difference_hours > 48:
            return {'success': False, 'error': str(_('Time difference exceeds 48 hours. Please check your inputs.'))}
        difference_minutes = difference_hours * self.HOURS_TO_MINUTES
        difference_seconds = difference_hours * self.HOURS_TO_SECONDS
        difference_days = difference_hours * self.HOURS_TO_DAYS
        diff_h, diff_m, diff_s = self._hours_to_time(difference_hours)
        steps = self._prepare_time_difference_steps(
            start_time_str, end_time_str, next_day, start_hours, end_hours, difference_hours,
            diff_h, diff_m, diff_s, difference_minutes, difference_seconds, difference_days
        )
        chart_data = self._prepare_time_difference_chart_data(start_hours, end_hours, difference_hours)
        return {
            'success': True,
            'calc_type': 'time_difference',
            'start_time': start_time_str,
            'end_time': end_time_str,
            'next_day': next_day,
            'difference_hours': round(difference_hours, 2),
            'difference_minutes': round(difference_minutes, 1),
            'difference_seconds': round(difference_seconds, 0),
            'difference_days': round(difference_days, 4),
            'difference_time': f'{diff_h:02d}:{diff_m:02d}:{diff_s:02d}',
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _add_subtract_hours(self, data):
        time_str = self._val(data, 'time', '').strip() or ''
        if not time_str:
            return {'success': False, 'error': str(_('Time is required.'))}
        hours_raw = self._val(data, 'hours')
        if hours_raw is None or hours_raw == '':
            return {'success': False, 'error': str(_('Hours to add/subtract is required.'))}
        try:
            hours_to_add = float(hours_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid hours value. Please enter a numeric value.'))}
        operation = self._val(data, 'operation', 'add')
        try:
            time_h, time_m, time_s = self._parse_time(time_str)
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        time_hours = self._time_to_hours(time_h, time_m, time_s)
        if operation == 'add':
            result_hours = time_hours + hours_to_add
        else:
            result_hours = time_hours - hours_to_add
        days = 0
        while result_hours >= 24:
            result_hours -= 24.0
            days += 1
        while result_hours < 0:
            result_hours += 24.0
            days -= 1
        result_h, result_m, result_s = self._hours_to_time(result_hours)
        steps = self._prepare_add_subtract_steps(
            time_str, hours_to_add, operation, time_hours, result_hours,
            result_h, result_m, result_s, days
        )
        return {
            'success': True,
            'calc_type': 'add_subtract',
            'time': time_str,
            'hours': hours_to_add,
            'operation': operation,
            'result_time': f'{result_h:02d}:{result_m:02d}:{result_s:02d}',
            'result_hours': round(result_hours, 2),
            'days': days,
            'step_by_step': steps,
        }

    def _convert_time_units(self, data):
        value_raw = self._val(data, 'value')
        if value_raw is None or value_raw == '':
            return {'success': False, 'error': str(_('Time value is required.'))}
        try:
            value = float(value_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter a numeric value.'))}
        from_unit = self._val(data, 'from_unit', 'hours') or 'hours'
        to_unit = self._val(data, 'to_unit', 'minutes') or 'minutes'
        if from_unit not in ('hours', 'minutes', 'seconds', 'days') or to_unit not in ('hours', 'minutes', 'seconds', 'days'):
            return {'success': False, 'error': str(_('Invalid unit.'))}
        if value < 0:
            return {'success': False, 'error': str(_('Time must be non-negative.'))}
        if from_unit == 'hours':
            hours_value = value
        elif from_unit == 'minutes':
            hours_value = value * self.MINUTES_TO_HOURS
        elif from_unit == 'seconds':
            hours_value = value * self.SECONDS_TO_HOURS
        else:
            hours_value = value * self.DAYS_TO_HOURS
        if to_unit == 'hours':
            result = hours_value
        elif to_unit == 'minutes':
            result = hours_value * self.HOURS_TO_MINUTES
        elif to_unit == 'seconds':
            result = hours_value * self.HOURS_TO_SECONDS
        else:
            result = hours_value * self.HOURS_TO_DAYS
        if math.isinf(result) or math.isnan(result):
            return {'success': False, 'error': str(_('Invalid conversion result.'))}
        steps = self._prepare_convert_steps(value, from_unit, to_unit, result, hours_value)
        return {
            'success': True,
            'calc_type': 'convert',
            'value': value,
            'from_unit': from_unit,
            'to_unit': to_unit,
            'result': round(result, 2),
            'step_by_step': steps,
        }

    def _calculate_total_hours(self, data):
        time_periods_raw = data.get('time_periods')
        if not isinstance(time_periods_raw, list):
            return {'success': False, 'error': str(_('Time periods are required as a list.'))}
        time_periods = time_periods_raw
        if len(time_periods) == 0:
            return {'success': False, 'error': str(_('At least one time period is required.'))}
        if len(time_periods) > 50:
            return {'success': False, 'error': str(_('Maximum 50 time periods allowed.'))}
        total_hours = 0.0
        processed_periods = []
        for i, period in enumerate(time_periods):
            if not isinstance(period, dict):
                return {'success': False, 'error': str(_('Invalid time period data format.'))}
            start_time = (period.get('start_time') or '').strip()
            end_time = (period.get('end_time') or '').strip()
            next_day = period.get('next_day') in (True, 'true', 'True', 1, '1')
            if not start_time or not end_time:
                continue
            try:
                start_h, start_m, start_s = self._parse_time(start_time)
                end_h, end_m, end_s = self._parse_time(end_time)
            except ValueError as e:
                return {'success': False, 'error': str(_('Invalid time format in period')) + ' ' + str(i + 1) + ': ' + str(e)}
            start_hours = self._time_to_hours(start_h, start_m, start_s)
            end_hours = self._time_to_hours(end_h, end_m, end_s)
            if end_hours < start_hours and not next_day:
                next_day = True
            if next_day:
                end_hours += 24.0
            period_hours = end_hours - start_hours
            if period_hours < 0:
                return {'success': False, 'error': str(_('Invalid time period')) + ' ' + str(i + 1) + ': ' + str(_('end time must be after start time.'))}
            processed_periods.append({'start_time': start_time, 'end_time': end_time, 'hours': round(period_hours, 2)})
            total_hours += period_hours
        total_minutes = total_hours * self.HOURS_TO_MINUTES
        total_seconds = total_hours * self.HOURS_TO_SECONDS
        total_days = total_hours * self.HOURS_TO_DAYS
        total_h, total_m, total_s = self._hours_to_time(total_hours)
        steps = self._prepare_total_hours_steps(
            processed_periods, total_hours, total_h, total_m, total_s,
            total_minutes, total_seconds, total_days
        )
        chart_data = self._prepare_total_hours_chart_data(processed_periods, total_hours)
        return {
            'success': True,
            'calc_type': 'total_hours',
            'time_periods': processed_periods,
            'total_hours': round(total_hours, 2),
            'total_minutes': round(total_minutes, 1),
            'total_seconds': round(total_seconds, 0),
            'total_days': round(total_days, 4),
            'total_time': f'{total_h:02d}:{total_m:02d}:{total_s:02d}',
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _calculate_hours_worked(self, data):
        start_time_str = self._val(data, 'start_time', '').strip() or ''
        end_time_str = self._val(data, 'end_time', '').strip() or ''
        if not start_time_str:
            return {'success': False, 'error': str(_('Start time is required.'))}
        if not end_time_str:
            return {'success': False, 'error': str(_('End time is required.'))}
        try:
            break_minutes = float(self._val(data, 'break_minutes') or 0)
        except (ValueError, TypeError):
            break_minutes = 0.0
        next_day = data.get('next_day') in (True, 'true', 'True', 1, '1')
        try:
            start_h, start_m, start_s = self._parse_time(start_time_str)
            end_h, end_m, end_s = self._parse_time(end_time_str)
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        if break_minutes < 0:
            return {'success': False, 'error': str(_('Break time must be non-negative.'))}
        start_hours = self._time_to_hours(start_h, start_m, start_s)
        end_hours = self._time_to_hours(end_h, end_m, end_s)
        if end_hours < start_hours and not next_day:
            next_day = True
        if next_day:
            end_hours += 24.0
        total_hours = end_hours - start_hours
        break_hours = break_minutes * self.MINUTES_TO_HOURS
        hours_worked = total_hours - break_hours
        if hours_worked < 0:
            return {'success': False, 'error': str(_('Break time cannot exceed total time.'))}
        hours_worked_minutes = hours_worked * self.HOURS_TO_MINUTES
        worked_h, worked_m, worked_s = self._hours_to_time(hours_worked)
        steps = self._prepare_hours_worked_steps(
            start_time_str, end_time_str, next_day, break_minutes,
            start_hours, end_hours, total_hours, break_hours, hours_worked,
            worked_h, worked_m, worked_s
        )
        chart_data = self._prepare_hours_worked_chart_data(total_hours, break_hours, hours_worked)
        return {
            'success': True,
            'calc_type': 'hours_worked',
            'start_time': start_time_str,
            'end_time': end_time_str,
            'break_minutes': break_minutes,
            'next_day': next_day,
            'total_hours': round(total_hours, 2),
            'break_hours': round(break_hours, 2),
            'hours_worked': round(hours_worked, 2),
            'hours_worked_minutes': round(hours_worked_minutes, 1),
            'hours_worked_time': f'{worked_h:02d}:{worked_m:02d}:{worked_s:02d}',
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _prepare_time_difference_steps(self, start_time, end_time, next_day, start_hours, end_hours, difference_hours, diff_h, diff_m, diff_s, diff_minutes, diff_seconds, diff_days):
        steps = []
        steps.append(str(_('Step 1: Identify the given times')))
        steps.append(str(_('Start Time')) + ': ' + str(start_time))
        steps.append(str(_('End Time')) + ': ' + str(end_time))
        if next_day:
            steps.append(str(_('Note: End time is on the next day')))
        steps.append('')
        steps.append(str(_('Step 2: Convert to decimal hours')))
        steps.append(str(_('Start Time')) + ': ' + str(start_hours) + ' ' + str(_('hours')))
        steps.append(str(_('End Time')) + ': ' + str(end_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 3: Calculate difference')))
        steps.append(str(_('Difference')) + ' = ' + str(_('End Time')) + ' - ' + str(_('Start Time')))
        steps.append(str(_('Difference')) + ' = ' + str(end_hours) + ' - ' + str(start_hours) + ' = ' + str(difference_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 4: Convert to other units')))
        steps.append(str(_('Time Format')) + ': ' + f'{diff_h:02d}:{diff_m:02d}:{diff_s:02d}')
        steps.append(str(_('Minutes')) + ': ' + str(diff_minutes) + ' ' + str(_('minutes')))
        steps.append(str(_('Seconds')) + ': ' + str(diff_seconds) + ' ' + str(_('seconds')))
        steps.append(str(_('Days')) + ': ' + str(diff_days) + ' ' + str(_('days')))
        return steps

    def _prepare_add_subtract_steps(self, time_str, hours_to_add, operation, time_hours, result_hours, result_h, result_m, result_s, days):
        op_label = str(_('add')) if operation == 'add' else str(_('subtract'))
        op_label_cap = str(_('Add')) if operation == 'add' else str(_('Subtract'))
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Time')) + ': ' + str(time_str))
        steps.append(str(_('Hours to')) + ' ' + op_label + ': ' + str(hours_to_add))
        steps.append('')
        steps.append(str(_('Step 2: Convert time to decimal hours')))
        steps.append(str(_('Time')) + ' = ' + str(time_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 3')) + ': ' + op_label_cap + ' ' + str(_('hours')))
        if operation == 'add':
            steps.append(str(_('Result')) + ' = ' + str(time_hours) + ' + ' + str(hours_to_add) + ' = ' + str(result_hours) + ' ' + str(_('hours')))
        else:
            steps.append(str(_('Result')) + ' = ' + str(time_hours) + ' - ' + str(hours_to_add) + ' = ' + str(result_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 4: Convert to time format')))
        result_time_str = f'{result_h:02d}:{result_m:02d}:{result_s:02d}'
        if days != 0:
            day_label = str(_('later')) if days > 0 else str(_('earlier'))
            steps.append(str(_('Result')) + ': ' + result_time_str + ' (' + str(abs(days)) + ' ' + str(_('day(s)')) + ' ' + day_label + ')')
        else:
            steps.append(str(_('Result')) + ': ' + result_time_str)
        return steps

    def _prepare_convert_steps(self, value, from_unit, to_unit, result, hours_value):
        steps = []
        unit_names = {'hours': str(_('hours')), 'minutes': str(_('minutes')), 'seconds': str(_('seconds')), 'days': str(_('days'))}
        steps.append(str(_('Step 1: Identify the given value')))
        steps.append(str(_('Time')) + ': ' + str(value) + ' ' + unit_names.get(from_unit, from_unit))
        steps.append('')
        if from_unit != 'hours':
            steps.append(str(_('Step 2: Convert to hours')))
            if from_unit == 'minutes':
                steps.append(str(_('Hours')) + ' = ' + str(_('Minutes')) + ' / 60')
                steps.append(str(_('Hours')) + ' = ' + str(value) + ' / 60 = ' + str(hours_value) + ' ' + str(_('hours')))
            elif from_unit == 'seconds':
                steps.append(str(_('Hours')) + ' = ' + str(_('Seconds')) + ' / 3600')
                steps.append(str(_('Hours')) + ' = ' + str(value) + ' / 3600 = ' + str(hours_value) + ' ' + str(_('hours')))
            elif from_unit == 'days':
                steps.append(str(_('Hours')) + ' = ' + str(_('Days')) + ' × 24')
                steps.append(str(_('Hours')) + ' = ' + str(value) + ' × 24 = ' + str(hours_value) + ' ' + str(_('hours')))
            steps.append('')
        if to_unit != 'hours':
            steps.append(str(_('Step 3: Convert from hours to')) + ' ' + unit_names.get(to_unit, to_unit))
            if to_unit == 'minutes':
                steps.append(str(_('Minutes')) + ' = ' + str(_('Hours')) + ' × 60')
                steps.append(str(_('Minutes')) + ' = ' + str(hours_value) + ' × 60 = ' + str(result) + ' ' + str(_('minutes')))
            elif to_unit == 'seconds':
                steps.append(str(_('Seconds')) + ' = ' + str(_('Hours')) + ' × 3600')
                steps.append(str(_('Seconds')) + ' = ' + str(hours_value) + ' × 3600 = ' + str(result) + ' ' + str(_('seconds')))
            elif to_unit == 'days':
                steps.append(str(_('Days')) + ' = ' + str(_('Hours')) + ' / 24')
                steps.append(str(_('Days')) + ' = ' + str(hours_value) + ' / 24 = ' + str(result) + ' ' + str(_('days')))
        else:
            steps.append(str(_('Step 2: Result')))
            steps.append(str(_('Time')) + ' = ' + str(result) + ' ' + str(_('hours')))
        return steps

    def _prepare_total_hours_steps(self, processed_periods, total_hours, total_h, total_m, total_s, total_minutes, total_seconds, total_days):
        steps = []
        steps.append(str(_('Step 1: Identify all time periods')))
        for i, period in enumerate(processed_periods, 1):
            steps.append(str(_('Period')) + ' ' + str(i) + ': ' + str(period['start_time']) + ' ' + str(_('to')) + ' ' + str(period['end_time']) + ' = ' + str(period['hours']) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 2: Calculate total hours')))
        hours_list = [str(p['hours']) for p in processed_periods]
        steps.append(str(_('Total')) + ' = ' + ' + '.join(hours_list))
        steps.append(str(_('Total')) + ' = ' + str(total_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 3: Convert to other units')))
        steps.append(str(_('Time Format')) + ': ' + f'{total_h:02d}:{total_m:02d}:{total_s:02d}')
        steps.append(str(_('Minutes')) + ': ' + str(total_minutes) + ' ' + str(_('minutes')))
        steps.append(str(_('Seconds')) + ': ' + str(total_seconds) + ' ' + str(_('seconds')))
        steps.append(str(_('Days')) + ': ' + str(total_days) + ' ' + str(_('days')))
        return steps

    def _prepare_hours_worked_steps(self, start_time, end_time, next_day, break_minutes, start_hours, end_hours, total_hours, break_hours, hours_worked, worked_h, worked_m, worked_s):
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Start Time')) + ': ' + str(start_time))
        steps.append(str(_('End Time')) + ': ' + str(end_time))
        if next_day:
            steps.append(str(_('Note: End time is on the next day')))
        steps.append(str(_('Break Time')) + ': ' + str(break_minutes) + ' ' + str(_('minutes')))
        steps.append('')
        steps.append(str(_('Step 2: Calculate total time')))
        steps.append(str(_('Total Time')) + ' = ' + str(_('End Time')) + ' - ' + str(_('Start Time')))
        steps.append(str(_('Total Time')) + ' = ' + str(end_hours) + ' - ' + str(start_hours) + ' = ' + str(total_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 3: Convert break time to hours')))
        steps.append(str(_('Break Time')) + ' = ' + str(break_minutes) + ' ' + str(_('minutes')) + ' / 60 = ' + str(break_hours) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 4: Calculate hours worked')))
        steps.append(str(_('Hours Worked')) + ' = ' + str(_('Total Time')) + ' - ' + str(_('Break Time')))
        steps.append(str(_('Hours Worked')) + ' = ' + str(total_hours) + ' - ' + str(break_hours) + ' = ' + str(hours_worked) + ' ' + str(_('hours')))
        steps.append('')
        steps.append(str(_('Step 5: Convert to time format')))
        steps.append(str(_('Hours Worked')) + ': ' + f'{worked_h:02d}:{worked_m:02d}:{worked_s:02d}')
        return steps

    def _prepare_time_difference_chart_data(self, start_hours, end_hours, difference_hours):
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Start Time')), str(_('End Time')), str(_('Difference'))],
                'datasets': [{
                    'label': str(_('Hours')),
                    'data': [start_hours, end_hours, difference_hours],
                    'backgroundColor': ['#6366f1', '#8b5cf6', '#e5e7eb'],
                    'borderColor': ['#4f46e5', '#7c3aed', '#d1d5db'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('Time Difference Calculation'))}},
                'scales': {'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Hours'))}}}
            }
        }
        return {'time_difference_chart': chart_config}

    def _prepare_total_hours_chart_data(self, processed_periods, total_hours):
        labels = [str(_('Period')) + ' ' + str(i + 1) for i in range(len(processed_periods))] + [str(_('Total'))]
        data_values = [p['hours'] for p in processed_periods] + [total_hours]
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Hours')),
                    'data': data_values,
                    'backgroundColor': ['#6366f1'] * len(processed_periods) + ['#8b5cf6'],
                    'borderColor': ['#4f46e5'] * len(processed_periods) + ['#7c3aed'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('Total Hours Calculation'))}},
                'scales': {'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Hours'))}}}
            }
        }
        return {'total_hours_chart': chart_config}

    def _prepare_hours_worked_chart_data(self, total_hours, break_hours, hours_worked):
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Total Time')), str(_('Break Time')), str(_('Hours Worked'))],
                'datasets': [{
                    'label': str(_('Hours')),
                    'data': [total_hours, break_hours, hours_worked],
                    'backgroundColor': ['#6366f1', '#8b5cf6', '#e5e7eb'],
                    'borderColor': ['#4f46e5', '#7c3aed', '#d1d5db'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('Hours Worked Calculation'))}},
                'scales': {'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Hours'))}}}
            }
        }
        return {'hours_worked_chart': chart_config}
