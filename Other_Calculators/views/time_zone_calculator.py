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
class TimeZoneCalculator(View):
    """
    Time Zone Calculator: convert time between zones, timezone difference,
    current time in multiple zones. BMI-style upgrade.
    """
    template_name = 'other_calculators/time_zone_calculator.html'

    TIME_ZONES = {
        'UTC': 0, 'EST': -5, 'EDT': -4, 'CST': -6, 'CDT': -5,
        'MST': -7, 'MDT': -6, 'PST': -8, 'PDT': -7, 'GMT': 0,
        'CET': 1, 'CEST': 2, 'EET': 2, 'EEST': 3, 'JST': 9,
        'IST': 5.5, 'AEST': 10, 'AEDT': 11, 'NZST': 12, 'NZDT': 13,
    }

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
        context = {'calculator_name': str(_('Time Zone Calculator'))}
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
            calc_type = self._val(data, 'calc_type', 'convert')
            if calc_type == 'convert':
                result = self._convert_timezone(data)
            elif calc_type == 'difference':
                result = self._calculate_timezone_difference(data)
            elif calc_type == 'current':
                result = self._get_current_time(data)
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
            logger.exception("Time zone calculator failed: %s", e)
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

    def _format_time(self, seconds):
        total_seconds = int(seconds % 86400)
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        secs = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_utc_offset(self, timezone):
        return self.TIME_ZONES.get(timezone, 0)

    def _convert_timezone(self, data):
        time_str = self._val(data, 'time', '')
        if not time_str:
            return {'success': False, 'error': str(_('Time is required.'))}
        from_timezone = self._val(data, 'from_timezone', 'UTC')
        to_timezone = self._val(data, 'to_timezone', 'UTC')
        time_seconds = self._parse_time(time_str)
        if time_seconds is None:
            return {'success': False, 'error': str(_('Invalid time format. Use HH:MM or HH:MM:SS format.'))}
        from_offset = self._get_utc_offset(from_timezone)
        to_offset = self._get_utc_offset(to_timezone)
        utc_seconds = time_seconds - (from_offset * 3600)
        if utc_seconds < 0:
            utc_seconds += 86400
        elif utc_seconds >= 86400:
            utc_seconds -= 86400
        result_seconds = utc_seconds + (to_offset * 3600)
        if result_seconds < 0:
            result_seconds += 86400
        elif result_seconds >= 86400:
            result_seconds -= 86400
        result_formatted = self._format_time(result_seconds)
        time_diff_hours = to_offset - from_offset
        steps = self._prepare_convert_steps(
            time_str, from_timezone, to_timezone, from_offset, to_offset,
            time_seconds, utc_seconds, result_seconds, time_diff_hours, result_formatted
        )
        chart_data = self._prepare_convert_chart_data(time_seconds, result_seconds, from_timezone, to_timezone)
        return {
            'success': True,
            'calc_type': 'convert',
            'time': time_str,
            'from_timezone': from_timezone,
            'to_timezone': to_timezone,
            'result_time': result_formatted,
            'time_diff_hours': time_diff_hours,
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _calculate_timezone_difference(self, data):
        timezone1 = self._val(data, 'timezone1', 'UTC')
        timezone2 = self._val(data, 'timezone2', 'UTC')
        if not timezone1:
            return {'success': False, 'error': str(_('First timezone is required.'))}
        if not timezone2:
            return {'success': False, 'error': str(_('Second timezone is required.'))}
        offset1 = self._get_utc_offset(timezone1)
        offset2 = self._get_utc_offset(timezone2)
        difference_hours = offset2 - offset1
        difference_minutes = difference_hours * 60
        difference_seconds = difference_hours * 3600
        diff_formatted = f"+{difference_hours} hours" if difference_hours >= 0 else f"{difference_hours} hours"
        steps = self._prepare_difference_steps(
            timezone1, timezone2, offset1, offset2,
            difference_hours, difference_minutes, difference_seconds, diff_formatted
        )
        return {
            'success': True,
            'calc_type': 'difference',
            'timezone1': timezone1,
            'timezone2': timezone2,
            'difference_hours': difference_hours,
            'difference_minutes': difference_minutes,
            'difference_seconds': difference_seconds,
            'difference_formatted': diff_formatted,
            'step_by_step': steps,
        }

    def _get_current_time(self, data):
        timezones_raw = data.get('timezones', ['UTC'])
        timezones = timezones_raw if isinstance(timezones_raw, list) else ['UTC']
        if not timezones:
            timezones = ['UTC']
        now = datetime.utcnow()
        base_time_seconds = now.hour * 3600 + now.minute * 60 + now.second
        current_times = []
        for tz in timezones:
            offset = self._get_utc_offset(tz)
            tz_time_seconds = base_time_seconds + (offset * 3600)
            if tz_time_seconds < 0:
                tz_time_seconds += 86400
            elif tz_time_seconds >= 86400:
                tz_time_seconds -= 86400
            tz_time_formatted = self._format_time(tz_time_seconds)
            current_times.append({
                'timezone': tz,
                'time': tz_time_formatted,
                'offset': offset,
            })
        steps = self._prepare_current_steps(current_times)
        chart_data = self._prepare_current_chart_data(current_times)
        return {
            'success': True,
            'calc_type': 'current',
            'current_times': current_times,
            'step_by_step': steps,
            'chart_data': chart_data,
        }

    def _prepare_convert_steps(self, time_str, from_timezone, to_timezone, from_offset, to_offset, time_seconds, utc_seconds, result_seconds, time_diff_hours, result_formatted):
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Time: {time}')).format(time=time_str))
        steps.append(str(_('From Timezone: {tz} (UTC{offset:+d})')).format(tz=from_timezone, offset=int(from_offset)))
        steps.append(str(_('To Timezone: {tz} (UTC{offset:+d})')).format(tz=to_timezone, offset=int(to_offset)))
        steps.append('')
        steps.append(str(_('Step 2: Convert to seconds')))
        steps.append(str(_('Time: {time} = {seconds} seconds')).format(time=time_str, seconds=time_seconds))
        steps.append('')
        steps.append(str(_('Step 3: Convert to UTC')))
        steps.append(str(_('UTC Time = Source Time - Source Offset')))
        steps.append(str(_('UTC Time = {time} - ({offset} × 3600)')).format(time=time_seconds, offset=int(from_offset)))
        steps.append(str(_('UTC Time = {utc} seconds = {utc_formatted}')).format(utc=utc_seconds, utc_formatted=self._format_time(utc_seconds)))
        steps.append('')
        steps.append(str(_('Step 4: Convert from UTC to target timezone')))
        steps.append(str(_('Target Time = UTC Time + Target Offset')))
        steps.append(str(_('Target Time = {utc} + ({offset} × 3600)')).format(utc=utc_seconds, offset=int(to_offset)))
        steps.append(str(_('Target Time = {result} seconds = {result_formatted}')).format(result=result_seconds, result_formatted=result_formatted))
        steps.append('')
        steps.append(str(_('Step 5: Time difference')))
        steps.append(str(_('Time Difference = {diff} hours')).format(diff=time_diff_hours))
        return steps

    def _prepare_difference_steps(self, timezone1, timezone2, offset1, offset2, difference_hours, difference_minutes, difference_seconds, diff_formatted):
        steps = []
        steps.append(str(_('Step 1: Identify the given timezones')))
        steps.append(str(_('Timezone 1: {tz1} (UTC{offset1:+d})')).format(tz1=timezone1, offset1=int(offset1)))
        steps.append(str(_('Timezone 2: {tz2} (UTC{offset2:+d})')).format(tz2=timezone2, offset2=int(offset2)))
        steps.append('')
        steps.append(str(_('Step 2: Calculate difference')))
        steps.append(str(_('Difference = Offset 2 - Offset 1')))
        steps.append(str(_('Difference = {offset2} - {offset1} = {diff} hours')).format(offset2=int(offset2), offset1=int(offset1), diff=difference_hours))
        steps.append('')
        steps.append(str(_('Step 3: Convert to different units')))
        steps.append(str(_('Difference = {hours} hours')).format(hours=difference_hours))
        steps.append(str(_('Difference = {minutes} minutes')).format(minutes=difference_minutes))
        steps.append(str(_('Difference = {seconds} seconds')).format(seconds=difference_seconds))
        return steps

    def _prepare_current_steps(self, current_times):
        steps = []
        steps.append(str(_('Step 1: Current time in different timezones')))
        for tz_info in current_times:
            steps.append(str(_('{tz}: {time} (UTC{offset:+d})')).format(
                tz=tz_info['timezone'],
                time=tz_info['time'],
                offset=int(tz_info['offset'])
            ))
        return steps

    def _prepare_convert_chart_data(self, time_seconds, result_seconds, from_timezone, to_timezone):
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [from_timezone, to_timezone],
                'datasets': [{
                    'label': str(_('Time (seconds)')),
                    'data': [time_seconds, result_seconds],
                    'backgroundColor': ['#6366f1', '#8b5cf6'],
                    'borderColor': ['#4f46e5', '#7c3aed'],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': str(_('Time Zone Conversion'))}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {'display': True, 'text': str(_('Time (seconds)'))}
                    }
                }
            }
        }
        return {'convert_chart': chart_config}

    def _prepare_current_chart_data(self, current_times):
        timezones = [tz['timezone'] for tz in current_times]
        times_seconds = []
        for tz in current_times:
            s = self._parse_time(tz['time'])
            times_seconds.append(s if s is not None else 0)
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': timezones,
                'datasets': [{
                    'label': str(_('Current Time')),
                    'data': times_seconds,
                    'backgroundColor': '#6366f1',
                    'borderColor': '#4f46e5',
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': str(_('Current Time in Different Time Zones'))}
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {'display': True, 'text': str(_('Time (seconds)'))}
                    }
                }
            }
        }
        return {'current_chart': chart_config}
