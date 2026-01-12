from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from datetime import datetime, timedelta
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TimeDurationCalculator(View):
    """
    Professional Time Duration Calculator with Comprehensive Features
    
    This calculator provides time duration calculations with:
    - Calculate duration between two times
    - Add/subtract duration from a time
    - Convert duration between units
    - Calculate elapsed time
    
    Features:
    - Supports multiple calculation modes
    - Handles various time formats
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/time_duration_calculator.html'
    
    # Time conversion factors (to seconds)
    TIME_CONVERSIONS = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': 86400.0,
        'weeks': 604800.0,
        'months': 2592000.0,  # Approximate: 30 days
        'years': 31536000.0,  # Approximate: 365 days
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'seconds': 's',
            'minutes': 'min',
            'hours': 'h',
            'days': 'days',
            'weeks': 'weeks',
            'months': 'months',
            'years': 'years',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Time Duration Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'between_times')
            
            if calc_type == 'between_times':
                return self._calculate_between_times(data)
            elif calc_type == 'add_subtract':
                return self._calculate_add_subtract(data)
            elif calc_type == 'convert':
                return self._convert_duration(data)
            elif calc_type == 'elapsed':
                return self._calculate_elapsed(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _parse_time(self, time_str):
        """Parse time string in various formats"""
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
                return hours * 3600 + minutes * 60 + seconds
            else:
                return float(time_str)
        except Exception:
            return None
    
    def _format_duration(self, total_seconds):
        """Format duration in human-readable format"""
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
        """Calculate duration between two times"""
        try:
            if 'start_time' not in data or not data.get('start_time'):
                return JsonResponse({
                    'success': False,
                    'error': _('Start time is required.')
                }, status=400)
            
            if 'end_time' not in data or not data.get('end_time'):
                return JsonResponse({
                    'success': False,
                    'error': _('End time is required.')
                }, status=400)
            
            start_time_str = data.get('start_time', '')
            end_time_str = data.get('end_time', '')
            
            # Parse times
            start_seconds = self._parse_time(start_time_str)
            end_seconds = self._parse_time(end_time_str)
            
            if start_seconds is None or end_seconds is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time format. Use HH:MM or HH:MM:SS format.')
                }, status=400)
            
            # Calculate duration
            if end_seconds < start_seconds:
                # End time is next day
                duration_seconds = (86400 - start_seconds) + end_seconds
            else:
                duration_seconds = end_seconds - start_seconds
            
            # Convert to different units
            duration_minutes = float(duration_seconds / 60.0)
            duration_hours = float(duration_seconds / 3600.0)
            duration_days = float(duration_seconds / 86400.0)
            
            # Format duration
            duration_formatted = self._format_duration(duration_seconds)
            
            steps = self._prepare_between_times_steps(start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, duration_minutes, duration_hours, duration_days, duration_formatted)
            chart_data = self._prepare_between_times_chart_data(start_seconds, end_seconds, duration_seconds)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating duration: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_add_subtract(self, data):
        """Add or subtract duration from a time"""
        try:
            if 'time' not in data or not data.get('time'):
                return JsonResponse({
                    'success': False,
                    'error': _('Time is required.')
                }, status=400)
            
            if 'duration' not in data or data.get('duration') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Duration is required.')
                }, status=400)
            
            try:
                duration = float(data.get('duration', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            time_str = data.get('time', '')
            operation = data.get('operation', 'add')
            duration_unit = data.get('duration_unit', 'hours')
            
            # Parse time
            time_seconds = self._parse_time(time_str)
            
            if time_seconds is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time format. Use HH:MM or HH:MM:SS format.')
                }, status=400)
            
            # Validate
            if duration < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Duration must be non-negative.')
                }, status=400)
            
            # Convert duration to seconds
            duration_seconds = float(duration * self.TIME_CONVERSIONS[duration_unit])
            
            # Perform operation
            if operation == 'add':
                result_seconds = time_seconds + duration_seconds
            else:  # subtract
                result_seconds = time_seconds - duration_seconds
                if result_seconds < 0:
                    # Handle negative result (previous day)
                    result_seconds += 86400
            
            # Convert to hours, minutes, seconds
            total_seconds = int(result_seconds % 86400)  # Keep within 24 hours
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            steps = self._prepare_add_subtract_steps(time_str, operation, duration, duration_unit, time_seconds, duration_seconds, result_seconds, hours, minutes, seconds, result_formatted)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating add/subtract: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_duration(self, data):
        """Convert duration between units"""
        try:
            if 'duration' not in data or data.get('duration') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Duration is required.')
                }, status=400)
            
            try:
                duration = float(data.get('duration', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'hours')
            to_unit = data.get('to_unit', 'minutes')
            
            # Validate
            if duration < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Duration must be non-negative.')
                }, status=400)
            
            # Convert to seconds
            duration_seconds = float(duration * self.TIME_CONVERSIONS[from_unit])
            
            # Convert to target unit
            result = float(np.divide(duration_seconds, self.TIME_CONVERSIONS[to_unit]))
            
            steps = self._prepare_convert_steps(duration, from_unit, duration_seconds, result, to_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'duration': duration,
                'from_unit': from_unit,
                'result': round(result, 6),
                'to_unit': to_unit,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting duration: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_elapsed(self, data):
        """Calculate elapsed time from a start time"""
        try:
            if 'start_time' not in data or not data.get('start_time'):
                return JsonResponse({
                    'success': False,
                    'error': _('Start time is required.')
                }, status=400)
            
            if 'elapsed_duration' not in data or data.get('elapsed_duration') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Elapsed duration is required.')
                }, status=400)
            
            try:
                elapsed_duration = float(data.get('elapsed_duration', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            start_time_str = data.get('start_time', '')
            elapsed_unit = data.get('elapsed_unit', 'hours')
            
            # Parse start time
            start_seconds = self._parse_time(start_time_str)
            
            if start_seconds is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time format. Use HH:MM or HH:MM:SS format.')
                }, status=400)
            
            # Validate
            if elapsed_duration < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Elapsed duration must be non-negative.')
                }, status=400)
            
            # Convert elapsed duration to seconds
            elapsed_seconds = float(elapsed_duration * self.TIME_CONVERSIONS[elapsed_unit])
            
            # Calculate end time
            end_seconds = start_seconds + elapsed_seconds
            
            # Convert to hours, minutes, seconds
            total_seconds = int(end_seconds % 86400)
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            end_time_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            steps = self._prepare_elapsed_steps(start_time_str, elapsed_duration, elapsed_unit, start_seconds, elapsed_seconds, end_seconds, hours, minutes, seconds, end_time_formatted)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating elapsed time: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_between_times_steps(self, start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, duration_minutes, duration_hours, duration_days, duration_formatted):
        """Prepare step-by-step solution for between times calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given times'))
        steps.append(_('Start Time: {time}').format(time=start_time_str))
        steps.append(_('End Time: {time}').format(time=end_time_str))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Start Time: {time} = {seconds} seconds').format(time=start_time_str, seconds=start_seconds))
        steps.append(_('End Time: {time} = {seconds} seconds').format(time=end_time_str, seconds=end_seconds))
        steps.append('')
        if end_seconds < start_seconds:
            steps.append(_('Step 3: Calculate duration (crosses midnight)'))
            steps.append(_('Duration = (86400 - Start) + End'))
            steps.append(_('Duration = (86400 - {start}) + {end} = {duration} seconds').format(start=start_seconds, end=end_seconds, duration=duration_seconds))
        else:
            steps.append(_('Step 3: Calculate duration'))
            steps.append(_('Duration = End - Start'))
            steps.append(_('Duration = {end} - {start} = {duration} seconds').format(end=end_seconds, start=start_seconds, duration=duration_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to different units'))
        steps.append(_('Duration = {seconds} seconds').format(seconds=duration_seconds))
        steps.append(_('Duration = {minutes} minutes').format(minutes=round(duration_minutes, 2)))
        steps.append(_('Duration = {hours} hours').format(hours=round(duration_hours, 2)))
        steps.append(_('Duration = {days} days').format(days=round(duration_days, 4)))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_('Duration = {formatted}').format(formatted=duration_formatted))
        return steps
    
    def _prepare_add_subtract_steps(self, time_str, operation, duration, duration_unit, time_seconds, duration_seconds, result_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for add/subtract calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Time: {time}').format(time=time_str))
        steps.append(_('Duration: {duration} {unit}').format(duration=duration, unit=self._format_unit(duration_unit)))
        steps.append(_('Operation: {op}').format(op=operation.title()))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Time: {time} = {seconds} seconds').format(time=time_str, seconds=time_seconds))
        steps.append(_('Duration: {duration} {unit} = {seconds} seconds').format(duration=duration, unit=self._format_unit(duration_unit), seconds=duration_seconds))
        steps.append('')
        steps.append(_('Step 3: Perform {op}').format(op=operation))
        if operation == 'add':
            steps.append(_('Result = Time + Duration'))
            steps.append(_('Result = {time} + {duration} = {result} seconds').format(time=time_seconds, duration=duration_seconds, result=result_seconds))
        else:
            steps.append(_('Result = Time - Duration'))
            steps.append(_('Result = {time} - {duration} = {result} seconds').format(time=time_seconds, duration=duration_seconds, result=result_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_('Hours = {result} ÷ 3600 = {hours}').format(result=result_seconds, hours=hours))
        steps.append(_('Minutes = ({result} % 3600) ÷ 60 = {minutes}').format(result=result_seconds, minutes=minutes))
        steps.append(_('Seconds = {result} % 60 = {seconds}').format(result=result_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_('Result = {result}').format(result=result_formatted))
        return steps
    
    def _prepare_convert_steps(self, duration, from_unit, duration_seconds, result, to_unit):
        """Prepare step-by-step solution for duration conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Duration: {duration} {unit}').format(duration=duration, unit=self._format_unit(from_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base unit (seconds)'))
        steps.append(_('Duration in seconds = {duration} × {factor} = {seconds} seconds').format(duration=duration, factor=self.TIME_CONVERSIONS[from_unit], seconds=duration_seconds))
        steps.append('')
        steps.append(_('Step 3: Convert to target unit'))
        steps.append(_('Duration in {unit} = {seconds} ÷ {factor} = {result} {unit}').format(unit=self._format_unit(to_unit), seconds=duration_seconds, factor=self.TIME_CONVERSIONS[to_unit], result=round(result, 6)))
        return steps
    
    def _prepare_elapsed_steps(self, start_time_str, elapsed_duration, elapsed_unit, start_seconds, elapsed_seconds, end_seconds, hours, minutes, seconds, end_time_formatted):
        """Prepare step-by-step solution for elapsed time calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Start Time: {time}').format(time=start_time_str))
        steps.append(_('Elapsed Duration: {duration} {unit}').format(duration=elapsed_duration, unit=self._format_unit(elapsed_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Start Time: {time} = {seconds} seconds').format(time=start_time_str, seconds=start_seconds))
        steps.append(_('Elapsed Duration: {duration} {unit} = {seconds} seconds').format(duration=elapsed_duration, unit=self._format_unit(elapsed_unit), seconds=elapsed_seconds))
        steps.append('')
        steps.append(_('Step 3: Calculate end time'))
        steps.append(_('End Time = Start Time + Elapsed Duration'))
        steps.append(_('End Time = {start} + {elapsed} = {end} seconds').format(start=start_seconds, elapsed=elapsed_seconds, end=end_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_('Hours = {end} ÷ 3600 = {hours}').format(end=end_seconds, hours=hours))
        steps.append(_('Minutes = ({end} % 3600) ÷ 60 = {minutes}').format(end=end_seconds, minutes=minutes))
        steps.append(_('Seconds = {end} % 60 = {seconds}').format(end=end_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_('End Time = {result}').format(result=end_time_formatted))
        return steps
    
    # Chart data preparation methods
    def _prepare_between_times_chart_data(self, start_seconds, end_seconds, duration_seconds):
        """Prepare chart data for duration visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Start'), _('End'), _('Duration')],
                    'datasets': [{
                        'label': _('Time (seconds)'),
                        'data': [start_seconds, end_seconds, duration_seconds],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(234, 179, 8, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#eab308'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Time Duration')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Time (seconds)')
                            }
                        }
                    }
                }
            }
            return {'duration_chart': chart_config}
        except Exception as e:
            return None
