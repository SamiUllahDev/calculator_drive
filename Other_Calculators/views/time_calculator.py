from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
import re

logger = logging.getLogger(__name__)


def _safe_format(msg_id, **kwargs):
    """
    Safely format a translatable string.
    
    Translators sometimes translate the {placeholder} names inside format
    strings (e.g. {time1} → {heure1} in French, {hours} → {ساعات} in Arabic).
    When .format() is called, Python raises KeyError because the translated
    placeholder name doesn't match the keyword argument.
    
    This helper tries the translated string first; on any KeyError / IndexError
    it falls back to formatting the original English msgid so the calculator
    still works in every language.
    """
    translated = _(msg_id)
    try:
        return str(translated).format(**kwargs)
    except (KeyError, IndexError, ValueError):
        try:
            return msg_id.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return str(translated)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TimeCalculator(View):
    """
    Professional Time Calculator with Comprehensive Features
    
    This calculator provides time calculations with:
    - Calculate time difference
    - Add/subtract time
    - Convert time units
    - Calculate duration
    - Time arithmetic
    
    Features:
    - Supports multiple calculation modes
    - Handles various time formats
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/time_calculator.html'
    
    # Time conversion factors (to seconds)
    TIME_CONVERSIONS = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': 86400.0,
        'weeks': 604800.0,
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'seconds': 's',
            'minutes': 'min',
            'hours': 'h',
            'days': 'days',
            'weeks': 'weeks',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {'calculator_name': str(_('Time Calculator'))}
        return render(request, self.template_name, context)

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

    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid request data.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            calc_type = data.get('calc_type', 'difference')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'difference'
            if calc_type == 'difference':
                result = self._calculate_difference(data)
            elif calc_type == 'add_subtract':
                result = self._calculate_add_subtract(data)
            elif calc_type == 'convert':
                result = self._convert_time(data)
            elif calc_type == 'duration':
                result = self._calculate_duration(data)
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
            logger.exception("Time calculator failed: %s", e)
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
        """Parse time string in various formats. Validates 24h: hours 0-23, minutes/seconds 0-59."""
        if not time_str:
            return None
        time_str = str(time_str).strip()
        try:
            if ':' in time_str:
                parts = time_str.split(':')
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
                if not (0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
                    return None
                return hours * 3600 + minutes * 60 + seconds
            return float(time_str)
        except (ValueError, TypeError):
            return None
    
    def _calculate_difference(self, data):
        """Calculate time difference between two times"""
        time1_str = (data.get('time1') or [None])[0] if isinstance(data.get('time1'), list) else data.get('time1', '')
        time2_str = (data.get('time2') or [None])[0] if isinstance(data.get('time2'), list) else data.get('time2', '')
        if not time1_str:
            return {'success': False, 'error': str(_('First time is required.'))}
        if not time2_str:
            return {'success': False, 'error': str(_('Second time is required.'))}
        time1_seconds = self._parse_time(time1_str)
        time2_seconds = self._parse_time(time2_str)
        if time1_seconds is None or time2_seconds is None:
            return {'success': False, 'error': str(_('Invalid time. Use HH:MM or HH:MM:SS (hours 0–23, minutes and seconds 0–59).'))}
        difference_seconds = abs(time2_seconds - time1_seconds)
        hours = int(difference_seconds // 3600)
        minutes = int((difference_seconds % 3600) // 60)
        seconds = int(difference_seconds % 60)
        result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        steps = self._prepare_difference_steps(time1_str, time2_str, time1_seconds, time2_seconds, difference_seconds, hours, minutes, seconds, result_formatted)
        chart_data = self._prepare_difference_chart_data(time1_seconds, time2_seconds, difference_seconds)
        return {
            'success': True,
            'calc_type': 'difference',
            'time1': time1_str,
            'time2': time2_str,
            'difference_seconds': difference_seconds,
            'difference_formatted': result_formatted,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'step_by_step': steps,
            'chart_data': chart_data,
        }
    
    def _calculate_add_subtract(self, data):
        """Add or subtract time. Returns a dict (same as other calc methods)."""
        try:
            time_str = (data.get('time') or [None])[0] if isinstance(data.get('time'), list) else data.get('time', '')
            operation = (data.get('operation') or ['add'])[0] if isinstance(data.get('operation'), list) else data.get('operation', 'add')
            amount_raw = (data.get('amount') or [None])[0] if isinstance(data.get('amount'), list) else data.get('amount')
            amount_unit = (data.get('amount_unit') or ['hours'])[0] if isinstance(data.get('amount_unit'), list) else data.get('amount_unit', 'hours')

            if not time_str:
                return {'success': False, 'error': str(_('Time is required.'))}
            if amount_raw is None or amount_raw == '':
                return {'success': False, 'error': str(_('Amount is required.'))}
            try:
                amount = float(amount_raw)
            except (ValueError, TypeError):
                return {'success': False, 'error': str(_('Invalid input type. Please enter numeric values.'))}

            time_seconds = self._parse_time(time_str)
            if time_seconds is None:
                return {'success': False, 'error': str(_('Invalid time. Use HH:MM or HH:MM:SS (hours 0–23, minutes and seconds 0–59).'))}
            if amount < 0:
                return {'success': False, 'error': str(_('Amount must be non-negative.'))}

            amount_seconds = float(amount * self.TIME_CONVERSIONS.get(amount_unit, 3600))
            if operation == 'add':
                result_seconds = time_seconds + amount_seconds
            else:
                result_seconds = time_seconds - amount_seconds
                if result_seconds < 0:
                    result_seconds += 86400

            total_seconds = int(result_seconds % 86400)
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            steps = self._prepare_add_subtract_steps(time_str, operation, amount, amount_unit, time_seconds, amount_seconds, result_seconds, hours, minutes, seconds, result_formatted)
            chart_data = self._prepare_add_subtract_chart_data(time_seconds, amount_seconds, result_seconds)

            return {
                'success': True,
                'calc_type': 'add_subtract',
                'time': time_str,
                'operation': operation,
                'amount': amount,
                'amount_unit': amount_unit,
                'result_seconds': result_seconds,
                'result_formatted': result_formatted,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds,
                'step_by_step': steps,
                'chart_data': chart_data,
            }
        except Exception as e:
            logger.exception("Time calculator add_subtract failed: %s", e)
            return {'success': False, 'error': _safe_format('Error calculating add/subtract: {error}', error=str(e))}
    
    def _convert_time(self, data):
        """Convert time between units"""
        time_raw = data.get('time')
        if time_raw is None or time_raw == '':
            return {'success': False, 'error': str(_('Time is required.'))}
        try:
            time_value = float(time_raw)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Invalid input type. Please enter numeric values.'))}
        from_unit = data.get('from_unit', 'hours')
        to_unit = data.get('to_unit', 'minutes')
        if isinstance(from_unit, list):
            from_unit = from_unit[0] if from_unit else 'hours'
        if isinstance(to_unit, list):
            to_unit = to_unit[0] if to_unit else 'minutes'
        if time_value < 0:
            return {'success': False, 'error': str(_('Time must be non-negative.'))}
        time_seconds = float(time_value * self.TIME_CONVERSIONS.get(from_unit, 3600))
        to_factor = self.TIME_CONVERSIONS.get(to_unit, 60)
        result = time_seconds / to_factor if to_factor else 0
        result = round(result, 6)
        steps = self._prepare_convert_steps(time_value, from_unit, time_seconds, result, to_unit)
        chart_data = self._prepare_convert_chart_data(time_value, from_unit, result, to_unit)
        return {
            'success': True,
            'calc_type': 'convert',
            'time': time_value,
            'from_unit': from_unit,
            'result': result,
            'to_unit': to_unit,
            'step_by_step': steps,
            'chart_data': chart_data,
        }
    
    def _calculate_duration(self, data):
        """Calculate duration from start and end times"""
        start_time_str = (data.get('start_time') or [None])[0] if isinstance(data.get('start_time'), list) else data.get('start_time', '')
        end_time_str = (data.get('end_time') or [None])[0] if isinstance(data.get('end_time'), list) else data.get('end_time', '')
        if not start_time_str:
            return {'success': False, 'error': str(_('Start time is required.'))}
        if not end_time_str:
            return {'success': False, 'error': str(_('End time is required.'))}
        start_seconds = self._parse_time(start_time_str)
        end_seconds = self._parse_time(end_time_str)
        if start_seconds is None or end_seconds is None:
            return {'success': False, 'error': str(_('Invalid time. Use HH:MM or HH:MM:SS (hours 0–23, minutes and seconds 0–59).'))}
        if end_seconds < start_seconds:
            duration_seconds = (86400 - start_seconds) + end_seconds
        else:
            duration_seconds = end_seconds - start_seconds
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        steps = self._prepare_duration_steps(start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, hours, minutes, seconds, result_formatted)
        chart_data = self._prepare_duration_chart_data(start_seconds, end_seconds, duration_seconds)
        return {
            'success': True,
            'calc_type': 'duration',
            'start_time': start_time_str,
            'end_time': end_time_str,
            'duration_seconds': duration_seconds,
            'duration_formatted': result_formatted,
            'hours': hours,
            'minutes': minutes,
            'seconds': seconds,
            'step_by_step': steps,
            'chart_data': chart_data,
        }
    
    # Step-by-step solution preparation methods
    def _prepare_difference_steps(self, time1_str, time2_str, time1_seconds, time2_seconds, difference_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for time difference"""
        steps = []
        steps.append(_('Step 1: Identify the given times'))
        steps.append(_safe_format('Time 1: {time1}', time1=time1_str))
        steps.append(_safe_format('Time 2: {time2}', time2=time2_str))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_safe_format('Time 1: {time1} = {seconds1} seconds', time1=time1_str, seconds1=time1_seconds))
        steps.append(_safe_format('Time 2: {time2} = {seconds2} seconds', time2=time2_str, seconds2=time2_seconds))
        steps.append('')
        steps.append(_('Step 3: Calculate difference'))
        steps.append(_('Difference = |Time 2 - Time 1|'))
        steps.append(_safe_format('Difference = |{time2} - {time1}|', time2=time2_seconds, time1=time1_seconds))
        steps.append(_safe_format('Difference = {diff} seconds', diff=difference_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_safe_format('Hours = {diff} ÷ 3600 = {hours}', diff=difference_seconds, hours=hours))
        steps.append(_safe_format('Minutes = ({diff} % 3600) ÷ 60 = {minutes}', diff=difference_seconds, minutes=minutes))
        steps.append(_safe_format('Seconds = {diff} % 60 = {seconds}', diff=difference_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_safe_format('Difference = {result}', result=result_formatted))
        return steps
    
    def _prepare_add_subtract_steps(self, time_str, operation, amount, amount_unit, time_seconds, amount_seconds, result_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for add/subtract"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_safe_format('Time: {time}', time=time_str))
        steps.append(_safe_format('Amount: {amount} {unit}', amount=amount, unit=self._format_unit(amount_unit)))
        steps.append(_safe_format('Operation: {op}', op=operation.title()))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_safe_format('Time: {time} = {seconds} seconds', time=time_str, seconds=time_seconds))
        steps.append(_safe_format('Amount: {amount} {unit} = {seconds} seconds', amount=amount, unit=self._format_unit(amount_unit), seconds=amount_seconds))
        steps.append('')
        steps.append(_safe_format('Step 3: Perform {op}', op=operation))
        if operation == 'add':
            steps.append(_('Result = Time + Amount'))
            steps.append(_safe_format('Result = {time} + {amount} = {result} seconds', time=time_seconds, amount=amount_seconds, result=result_seconds))
        else:
            steps.append(_('Result = Time - Amount'))
            steps.append(_safe_format('Result = {time} - {amount} = {result} seconds', time=time_seconds, amount=amount_seconds, result=result_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_safe_format('Hours = {result} ÷ 3600 = {hours}', result=result_seconds, hours=hours))
        steps.append(_safe_format('Minutes = ({result} % 3600) ÷ 60 = {minutes}', result=result_seconds, minutes=minutes))
        steps.append(_safe_format('Seconds = {result} % 60 = {seconds}', result=result_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_safe_format('Result = {result}', result=result_formatted))
        return steps
    
    def _prepare_convert_steps(self, time_value, from_unit, time_seconds, result, to_unit):
        """Prepare step-by-step solution for time conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_safe_format('Time: {time} {unit}', time=time_value, unit=self._format_unit(from_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base unit (seconds)'))
        steps.append(_safe_format('Time in seconds = {time} × {factor} = {seconds} seconds', time=time_value, factor=self.TIME_CONVERSIONS[from_unit], seconds=time_seconds))
        steps.append('')
        steps.append(_('Step 3: Convert to target unit'))
        steps.append(_safe_format('Time in {unit} = {seconds} ÷ {factor} = {result} {unit}', unit=self._format_unit(to_unit), seconds=time_seconds, factor=self.TIME_CONVERSIONS[to_unit], result=round(result, 6)))
        return steps
    
    def _prepare_duration_steps(self, start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for duration calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given times'))
        steps.append(_safe_format('Start Time: {start}', start=start_time_str))
        steps.append(_safe_format('End Time: {end}', end=end_time_str))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_safe_format('Start Time: {start} = {seconds} seconds', start=start_time_str, seconds=start_seconds))
        steps.append(_safe_format('End Time: {end} = {seconds} seconds', end=end_time_str, seconds=end_seconds))
        steps.append('')
        if end_seconds < start_seconds:
            steps.append(_('Step 3: Calculate duration (crosses midnight)'))
            steps.append(_('Duration = (86400 - Start) + End'))
            steps.append(_safe_format('Duration = (86400 - {start}) + {end} = {duration} seconds', start=start_seconds, end=end_seconds, duration=duration_seconds))
        else:
            steps.append(_('Step 3: Calculate duration'))
            steps.append(_('Duration = End - Start'))
            steps.append(_safe_format('Duration = {end} - {start} = {duration} seconds', end=end_seconds, start=start_seconds, duration=duration_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_safe_format('Hours = {duration} ÷ 3600 = {hours}', duration=duration_seconds, hours=hours))
        steps.append(_safe_format('Minutes = ({duration} % 3600) ÷ 60 = {minutes}', duration=duration_seconds, minutes=minutes))
        steps.append(_safe_format('Seconds = {duration} % 60 = {seconds}', duration=duration_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_safe_format('Duration = {result}', result=result_formatted))
        return steps
    
    # Chart data preparation methods
    def _prepare_difference_chart_data(self, time1_seconds, time2_seconds, difference_seconds):
        """Prepare chart data for time difference visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Time 1')), str(_('Time 2')), str(_('Difference'))],
                    'datasets': [{
                        'label': str(_('Time (seconds)')),
                        'data': [time1_seconds, time2_seconds, difference_seconds],
                        'backgroundColor': ['#6366f1', '#8b5cf6', '#a78bfa'],
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}},
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True, 'ticks': {'precision': 0}}
                    }
                }
            }
            return {'difference_chart': chart_config}
        except Exception:
            return None
    
    def _prepare_duration_chart_data(self, start_seconds, end_seconds, duration_seconds):
        """Prepare chart data for duration visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Start')), str(_('End')), str(_('Duration'))],
                    'datasets': [{
                        'label': str(_('Time (seconds)')),
                        'data': [start_seconds, end_seconds, duration_seconds],
                        'backgroundColor': ['#6366f1', '#8b5cf6', '#a78bfa'],
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}},
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True, 'ticks': {'precision': 0}}
                    }
                }
            }
            return {'duration_chart': chart_config}
        except Exception:
            return None

    def _prepare_add_subtract_chart_data(self, time_seconds, amount_seconds, result_seconds):
        """Prepare chart data for add/subtract visualization (all in seconds)."""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Start time')), str(_('Amount')), str(_('Result'))],
                    'datasets': [{
                        'label': str(_('Time (seconds)')),
                        'data': [time_seconds, amount_seconds, result_seconds],
                        'backgroundColor': ['#6366f1', '#8b5cf6', '#a78bfa'],
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}},
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True, 'ticks': {'precision': 0}}
                    }
                }
            }
            return {'add_subtract_chart': chart_config}
        except Exception:
            return None

    def _prepare_convert_chart_data(self, time_value, from_unit, result, to_unit):
        """Prepare chart data for unit conversion (from and to values in seconds for comparison)."""
        try:
            time_sec = time_value * self.TIME_CONVERSIONS.get(from_unit, 3600)
            result_sec = result * self.TIME_CONVERSIONS.get(to_unit, 60)
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [str(_('From')) + ' (' + self._format_unit(from_unit) + ')', str(_('To')) + ' (' + self._format_unit(to_unit) + ')'],
                    'datasets': [{
                        'label': str(_('Time (seconds)')),
                        'data': [time_sec, result_sec],
                        'backgroundColor': ['#6366f1', '#8b5cf6'],
                        'borderRadius': 4,
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}},
                    'scales': {
                        'x': {'grid': {'display': False}},
                        'y': {'beginAtZero': True, 'ticks': {'precision': 0}}
                    }
                }
            }
            return {'convert_chart': chart_config}
        except Exception:
            return None
