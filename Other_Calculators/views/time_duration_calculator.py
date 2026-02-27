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
class TimeDurationCalculator(View):
    """
    Time Duration Calculator: duration between times, add/subtract duration,
    convert units, elapsed time. BMI-style upgrade.
    """
    template_name = 'other_calculators/time_duration_calculator.html'

    TIME_CONVERSIONS = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': 86400.0,
        'weeks': 604800.0,
        'months': 2592000.0,
        'years': 31536000.0,
    }

    def _format_unit(self, unit):
        unit_map = {
            'seconds': 's', 'minutes': 'min', 'hours': 'h', 'days': 'days',
            'weeks': 'weeks', 'months': 'months', 'years': 'years',
        }
        return unit_map.get(unit, unit)

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
        context = {'calculator_name': str(_('Time Duration Calculator'))}
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
            calc_type = self._val(data, 'calc_type', 'between_times')
            if calc_type == 'between_times':
                result = self._calculate_between_times(data)
            elif calc_type == 'add_subtract':
                result = self._calculate_add_subtract(data)
            elif calc_type == 'convert':
                result = self._convert_duration(data)
            elif calc_type == 'elapsed':
                result = self._calculate_elapsed(data)
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
            logger.exception("Time duration calculator failed: %s", e)
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

    def _format_duration(self, total_seconds):
        if total_seconds < 60:
            return f"{int(total_seconds)} seconds"
        elif total_seconds < 3600:
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            if seconds == 0:
                return f"{minutes} minute{'s' if minutes != 1 else ''}"
            return f"{minutes} minute{'s' if minutes != 1 else ''} {seconds} second{'s' if seconds != 1 else ''}"
        elif total_seconds < 86400:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            if minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            return f"{hours} hour{'s' if hours != 1 else ''} {minutes} minute{'s' if minutes != 1 else ''}"
        else:
            days = int(total_seconds // 86400)
            hours = int((total_seconds % 86400) // 3600)
            if hours == 0:
                return f"{days} day{'s' if days != 1 else ''}"
            return f"{days} day{'s' if days != 1 else ''} {hours} hour{'s' if hours != 1 else ''}"

    def _calculate_between_times(self, data):
        start_time_str = self._val(data, 'start_time', '')
        end_time_str = self._val(data, 'end_time', '')
        if not start_time_str:
            return {'success': False, 'error': str(_('Start time is required.'))}
        if not end_time_str:
            return {'success': False, 'error': str(_('End time is required.'))}
        start_seconds = self._parse_time(start_time_str)
        end_seconds = self._parse_time(end_time_str)
        if start_seconds is None or end_seconds is None:
            return {'success': False, 'error': str(_('Invalid time format. Use HH:MM or HH:MM:SS format.'))}
        if end_seconds < start_seconds:
            duration_seconds = (86400 - start_seconds) + end_seconds
        else:
            duration_seconds = end_seconds - start_seconds
        duration_minutes = float(duration_seconds / 60.0)
        duration_hours = float(duration_seconds / 3600.0)
        duration_days = float(duration_seconds / 86400.0)
        duration_formatted = self._format_duration(duration_seconds)
        steps = self._prepare_between_times_steps(
            start_time_str, end_time_str, start_seconds, end_seconds,
            duration_seconds, duration_minutes, duration_hours, duration_days, duration_formatted
        )
        chart_data = self._prepare_between_times_chart_data(start_seconds, end_seconds, duration_seconds)
        return {
            'success': True,
            'calc_type': 'between_times',
            'start_time': start_time_str,
            'end_time': end_time_str,
            'duration_seconds': duration_seconds,
            'duration_minutes': round(duration_minutes, 2),
            'duration_hours': round(duration_hours, 2),
            'duration_days': round(duration_days, 4),
            'duration_formatted': duration_formatted,
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _calculate_add_subtract(self, data):
        time_str = self._val(data, 'time', '')
        if not time_str:
            return {'success': False, 'error': str(_('Time is required.'))}
        duration_raw = self._val(data, 'duration')
        if duration_raw is None or duration_raw == '':
            return {'success': False, 'error': str(_('Duration is required.'))}
        try:
            duration = float(duration_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter numeric values.'))}
        operation = self._val(data, 'operation', 'add')
        duration_unit = self._val(data, 'duration_unit', 'hours')
        time_seconds = self._parse_time(time_str)
        if time_seconds is None:
            return {'success': False, 'error': str(_('Invalid time format. Use HH:MM or HH:MM:SS format.'))}
        if duration < 0:
            return {'success': False, 'error': str(_('Duration must be non-negative.'))}
        if duration_unit not in self.TIME_CONVERSIONS:
            return {'success': False, 'error': str(_('Invalid duration unit.'))}
        duration_seconds = float(duration * self.TIME_CONVERSIONS[duration_unit])
        if operation == 'add':
            result_seconds = time_seconds + duration_seconds
        else:
            result_seconds = time_seconds - duration_seconds
            if result_seconds < 0:
                result_seconds += 86400
        total_seconds = int(result_seconds % 86400)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        steps = self._prepare_add_subtract_steps(
            time_str, operation, duration, duration_unit, time_seconds, duration_seconds,
            result_seconds, hours, minutes, seconds, result_formatted
        )
        return {
            'success': True,
            'calc_type': 'add_subtract',
            'time': time_str,
            'operation': operation,
            'duration': duration,
            'duration_unit': duration_unit,
            'result_seconds': result_seconds,
            'result_formatted': result_formatted,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'step_by_step': steps,
        }

    def _convert_duration(self, data):
        duration_raw = self._val(data, 'duration')
        if duration_raw is None or duration_raw == '':
            return {'success': False, 'error': str(_('Duration is required.'))}
        try:
            duration = float(duration_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter numeric values.'))}
        from_unit = self._val(data, 'from_unit', 'hours')
        to_unit = self._val(data, 'to_unit', 'minutes')
        if duration < 0:
            return {'success': False, 'error': str(_('Duration must be non-negative.'))}
        if from_unit not in self.TIME_CONVERSIONS or to_unit not in self.TIME_CONVERSIONS:
            return {'success': False, 'error': str(_('Invalid unit.'))}
        duration_seconds = float(duration * self.TIME_CONVERSIONS[from_unit])
        result = duration_seconds / self.TIME_CONVERSIONS[to_unit]
        steps = self._prepare_convert_steps(duration, from_unit, duration_seconds, result, to_unit)
        return {
            'success': True,
            'calc_type': 'convert',
            'duration': duration,
            'from_unit': from_unit,
            'result': round(result, 6),
            'to_unit': to_unit,
            'step_by_step': steps,
        }

    def _calculate_elapsed(self, data):
        start_time_str = self._val(data, 'start_time', '')
        if not start_time_str:
            return {'success': False, 'error': str(_('Start time is required.'))}
        elapsed_raw = self._val(data, 'elapsed_duration')
        if elapsed_raw is None or elapsed_raw == '':
            return {'success': False, 'error': str(_('Elapsed duration is required.'))}
        try:
            elapsed_duration = float(elapsed_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter numeric values.'))}
        elapsed_unit = self._val(data, 'elapsed_unit', 'hours')
        start_seconds = self._parse_time(start_time_str)
        if start_seconds is None:
            return {'success': False, 'error': str(_('Invalid time format. Use HH:MM or HH:MM:SS format.'))}
        if elapsed_duration < 0:
            return {'success': False, 'error': str(_('Elapsed duration must be non-negative.'))}
        if elapsed_unit not in self.TIME_CONVERSIONS:
            return {'success': False, 'error': str(_('Invalid elapsed unit.'))}
        elapsed_seconds = float(elapsed_duration * self.TIME_CONVERSIONS[elapsed_unit])
        end_seconds = start_seconds + elapsed_seconds
        total_seconds = int(end_seconds % 86400)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        end_time_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        steps = self._prepare_elapsed_steps(
            start_time_str, elapsed_duration, elapsed_unit, start_seconds, elapsed_seconds,
            end_seconds, hours, minutes, seconds, end_time_formatted
        )
        return {
            'success': True,
            'calc_type': 'elapsed',
            'start_time': start_time_str,
            'elapsed_duration': elapsed_duration,
            'elapsed_unit': elapsed_unit,
            'end_time_seconds': end_seconds,
            'end_time_formatted': end_time_formatted,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'step_by_step': steps,
        }

    def _prepare_between_times_steps(self, start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, duration_minutes, duration_hours, duration_days, duration_formatted):
        steps = []
        steps.append(str(_('Step 1: Identify the given times')))
        steps.append(str(_('Start Time')) + ': ' + str(start_time_str))
        steps.append(str(_('End Time')) + ': ' + str(end_time_str))
        steps.append('')
        steps.append(str(_('Step 2: Convert to seconds')))
        steps.append(str(_('Start Time')) + ': ' + str(start_time_str) + ' = ' + str(start_seconds) + ' ' + str(_('seconds')))
        steps.append(str(_('End Time')) + ': ' + str(end_time_str) + ' = ' + str(end_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        if end_seconds < start_seconds:
            steps.append(str(_('Step 3: Calculate duration (crosses midnight)')))
            steps.append(str(_('Duration')) + ' = (86400 - ' + str(_('Start')) + ') + ' + str(_('End')))
            steps.append(str(_('Duration')) + ' = (86400 - ' + str(start_seconds) + ') + ' + str(end_seconds) + ' = ' + str(duration_seconds) + ' ' + str(_('seconds')))
        else:
            steps.append(str(_('Step 3: Calculate duration')))
            steps.append(str(_('Duration')) + ' = ' + str(_('End')) + ' - ' + str(_('Start')))
            steps.append(str(_('Duration')) + ' = ' + str(end_seconds) + ' - ' + str(start_seconds) + ' = ' + str(duration_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        steps.append(str(_('Step 4: Convert to different units')))
        steps.append(str(_('Duration')) + ' = ' + str(duration_seconds) + ' ' + str(_('seconds')))
        steps.append(str(_('Duration')) + ' = ' + str(round(duration_minutes, 2)) + ' ' + str(_('minutes')))
        steps.append(str(_('Duration')) + ' = ' + str(round(duration_hours, 2)) + ' ' + str(_('hours')))
        steps.append(str(_('Duration')) + ' = ' + str(round(duration_days, 4)) + ' ' + str(_('days')))
        steps.append('')
        steps.append(str(_('Step 5: Result')))
        steps.append(str(_('Duration')) + ' = ' + str(duration_formatted))
        return steps

    def _prepare_add_subtract_steps(self, time_str, operation, duration, duration_unit, time_seconds, duration_seconds, result_seconds, hours, minutes, seconds, result_formatted):
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Time')) + ': ' + str(time_str))
        steps.append(str(_('Duration')) + ': ' + str(duration) + ' ' + self._format_unit(duration_unit))
        steps.append(str(_('Operation')) + ': ' + operation.title())
        steps.append('')
        steps.append(str(_('Step 2: Convert to seconds')))
        steps.append(str(_('Time')) + ': ' + str(time_str) + ' = ' + str(time_seconds) + ' ' + str(_('seconds')))
        steps.append(str(_('Duration')) + ': ' + str(duration) + ' ' + self._format_unit(duration_unit) + ' = ' + str(duration_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        steps.append(str(_('Step 3: Perform')) + ' ' + operation)
        if operation == 'add':
            steps.append(str(_('Result')) + ' = ' + str(_('Time')) + ' + ' + str(_('Duration')))
            steps.append(str(_('Result')) + ' = ' + str(time_seconds) + ' + ' + str(duration_seconds) + ' = ' + str(result_seconds) + ' ' + str(_('seconds')))
        else:
            steps.append(str(_('Result')) + ' = ' + str(_('Time')) + ' - ' + str(_('Duration')))
            steps.append(str(_('Result')) + ' = ' + str(time_seconds) + ' - ' + str(duration_seconds) + ' = ' + str(result_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        steps.append(str(_('Step 4: Convert to hours, minutes, seconds')))
        steps.append(str(_('Hours')) + ' = ' + str(result_seconds) + ' ÷ 3600 = ' + str(hours))
        steps.append(str(_('Minutes')) + ' = (' + str(result_seconds) + ' % 3600) ÷ 60 = ' + str(minutes))
        steps.append(str(_('Seconds')) + ' = ' + str(result_seconds) + ' % 60 = ' + str(seconds))
        steps.append('')
        steps.append(str(_('Step 5: Result')))
        steps.append(str(_('Result')) + ' = ' + str(result_formatted))
        return steps

    def _prepare_convert_steps(self, duration, from_unit, duration_seconds, result, to_unit):
        steps = []
        steps.append(str(_('Step 1: Identify the given value')))
        steps.append(str(_('Duration')) + ': ' + str(duration) + ' ' + self._format_unit(from_unit))
        steps.append('')
        steps.append(str(_('Step 2: Convert to base unit (seconds)')))
        steps.append(str(_('Duration in seconds')) + ' = ' + str(duration) + ' × ' + str(self.TIME_CONVERSIONS[from_unit]) + ' = ' + str(duration_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        steps.append(str(_('Step 3: Convert to target unit')))
        steps.append(str(_('Duration in')) + ' ' + self._format_unit(to_unit) + ' = ' + str(duration_seconds) + ' ÷ ' + str(self.TIME_CONVERSIONS[to_unit]) + ' = ' + str(round(result, 6)) + ' ' + self._format_unit(to_unit))
        return steps

    def _prepare_elapsed_steps(self, start_time_str, elapsed_duration, elapsed_unit, start_seconds, elapsed_seconds, end_seconds, hours, minutes, seconds, end_time_formatted):
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Start Time')) + ': ' + str(start_time_str))
        steps.append(str(_('Elapsed Duration')) + ': ' + str(elapsed_duration) + ' ' + self._format_unit(elapsed_unit))
        steps.append('')
        steps.append(str(_('Step 2: Convert to seconds')))
        steps.append(str(_('Start Time')) + ': ' + str(start_time_str) + ' = ' + str(start_seconds) + ' ' + str(_('seconds')))
        steps.append(str(_('Elapsed Duration')) + ': ' + str(elapsed_duration) + ' ' + self._format_unit(elapsed_unit) + ' = ' + str(elapsed_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        steps.append(str(_('Step 3: Calculate end time')))
        steps.append(str(_('End Time')) + ' = ' + str(_('Start Time')) + ' + ' + str(_('Elapsed Duration')))
        steps.append(str(_('End Time')) + ' = ' + str(start_seconds) + ' + ' + str(elapsed_seconds) + ' = ' + str(end_seconds) + ' ' + str(_('seconds')))
        steps.append('')
        steps.append(str(_('Step 4: Convert to hours, minutes, seconds')))
        steps.append(str(_('Hours')) + ' = ' + str(end_seconds) + ' ÷ 3600 = ' + str(hours))
        steps.append(str(_('Minutes')) + ' = (' + str(end_seconds) + ' % 3600) ÷ 60 = ' + str(minutes))
        steps.append(str(_('Seconds')) + ' = ' + str(end_seconds) + ' % 60 = ' + str(seconds))
        steps.append('')
        steps.append(str(_('Step 5: Result')))
        steps.append(str(_('End Time')) + ' = ' + str(end_time_formatted))
        return steps

    def _prepare_between_times_chart_data(self, start_seconds, end_seconds, duration_seconds):
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Start')), str(_('End')), str(_('Duration'))],
                'datasets': [{
                    'label': str(_('Time (seconds)')),
                    'data': [start_seconds, end_seconds, duration_seconds],
                    'backgroundColor': ['#6366f1', '#8b5cf6', '#e5e7eb'],
                    'borderColor': ['#4f46e5', '#7c3aed', '#d1d5db'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': str(_('Time Duration'))}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {'display': True, 'text': str(_('Time (seconds)'))}
                    }
                }
            }
        }
        return {'duration_chart': chart_config}
