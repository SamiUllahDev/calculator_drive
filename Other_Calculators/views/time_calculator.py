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
        context = {
            'calculator_name': _('Time Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'difference')
            
            if calc_type == 'difference':
                return self._calculate_difference(data)
            elif calc_type == 'add_subtract':
                return self._calculate_add_subtract(data)
            elif calc_type == 'convert':
                return self._convert_time(data)
            elif calc_type == 'duration':
                return self._calculate_duration(data)
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
            # Try HH:MM:SS format
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
                # Try numeric value
                return float(time_str)
        except Exception:
            return None
    
    def _calculate_difference(self, data):
        """Calculate time difference between two times"""
        try:
            if 'time1' not in data or not data.get('time1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First time is required.')
                }, status=400)
            
            if 'time2' not in data or not data.get('time2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second time is required.')
                }, status=400)
            
            time1_str = data.get('time1', '')
            time2_str = data.get('time2', '')
            
            # Parse times
            time1_seconds = self._parse_time(time1_str)
            time2_seconds = self._parse_time(time2_str)
            
            if time1_seconds is None or time2_seconds is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time format. Use HH:MM or HH:MM:SS format.')
                }, status=400)
            
            # Calculate difference
            difference_seconds = abs(time2_seconds - time1_seconds)
            
            # Convert to hours, minutes, seconds
            hours = int(difference_seconds // 3600)
            minutes = int((difference_seconds % 3600) // 60)
            seconds = int(difference_seconds % 60)
            
            # Format result
            result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            steps = self._prepare_difference_steps(time1_str, time2_str, time1_seconds, time2_seconds, difference_seconds, hours, minutes, seconds, result_formatted)
            chart_data = self._prepare_difference_chart_data(time1_seconds, time2_seconds, difference_seconds)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating time difference: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_add_subtract(self, data):
        """Add or subtract time"""
        try:
            if 'time' not in data or not data.get('time'):
                return JsonResponse({
                    'success': False,
                    'error': _('Time is required.')
                }, status=400)
            
            if 'amount' not in data or data.get('amount') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Amount is required.')
                }, status=400)
            
            try:
                amount = float(data.get('amount', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            time_str = data.get('time', '')
            operation = data.get('operation', 'add')  # 'add' or 'subtract'
            amount_unit = data.get('amount_unit', 'hours')
            
            # Parse time
            time_seconds = self._parse_time(time_str)
            
            if time_seconds is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time format. Use HH:MM or HH:MM:SS format.')
                }, status=400)
            
            # Validate
            if amount < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Amount must be non-negative.')
                }, status=400)
            
            # Convert amount to seconds
            amount_seconds = float(amount * self.TIME_CONVERSIONS[amount_unit])
            
            # Perform operation
            if operation == 'add':
                result_seconds = time_seconds + amount_seconds
            else:  # subtract
                result_seconds = time_seconds - amount_seconds
                if result_seconds < 0:
                    # Handle negative result (previous day)
                    result_seconds += 86400  # Add 24 hours
            
            # Convert to hours, minutes, seconds
            total_seconds = int(result_seconds % 86400)  # Keep within 24 hours
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            seconds = int(total_seconds % 60)
            
            result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            steps = self._prepare_add_subtract_steps(time_str, operation, amount, amount_unit, time_seconds, amount_seconds, result_seconds, hours, minutes, seconds, result_formatted)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating add/subtract: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_time(self, data):
        """Convert time between units"""
        try:
            if 'time' not in data or data.get('time') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Time is required.')
                }, status=400)
            
            try:
                time_value = float(data.get('time', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'hours')
            to_unit = data.get('to_unit', 'minutes')
            
            # Validate
            if time_value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Time must be non-negative.')
                }, status=400)
            
            # Convert to seconds
            time_seconds = float(time_value * self.TIME_CONVERSIONS[from_unit])
            
            # Convert to target unit
            result = float(np.divide(time_seconds, self.TIME_CONVERSIONS[to_unit]))
            
            steps = self._prepare_convert_steps(time_value, from_unit, time_seconds, result, to_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'time': time_value,
                'from_unit': from_unit,
                'result': round(result, 6),
                'to_unit': to_unit,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting time: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_duration(self, data):
        """Calculate duration from start and end times"""
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
            
            # Convert to hours, minutes, seconds
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)
            
            result_formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            steps = self._prepare_duration_steps(start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, hours, minutes, seconds, result_formatted)
            chart_data = self._prepare_duration_chart_data(start_seconds, end_seconds, duration_seconds)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating duration: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_difference_steps(self, time1_str, time2_str, time1_seconds, time2_seconds, difference_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for time difference"""
        steps = []
        steps.append(_('Step 1: Identify the given times'))
        steps.append(_('Time 1: {time1}').format(time1=time1_str))
        steps.append(_('Time 2: {time2}').format(time2=time2_str))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Time 1: {time1} = {seconds1} seconds').format(time1=time1_str, seconds1=time1_seconds))
        steps.append(_('Time 2: {time2} = {seconds2} seconds').format(time2=time2_str, seconds2=time2_seconds))
        steps.append('')
        steps.append(_('Step 3: Calculate difference'))
        steps.append(_('Difference = |Time 2 - Time 1|'))
        steps.append(_('Difference = |{time2} - {time1}|').format(time2=time2_seconds, time1=time1_seconds))
        steps.append(_('Difference = {diff} seconds').format(diff=difference_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_('Hours = {diff} ÷ 3600 = {hours}').format(diff=difference_seconds, hours=hours))
        steps.append(_('Minutes = ({diff} % 3600) ÷ 60 = {minutes}').format(diff=difference_seconds, minutes=minutes))
        steps.append(_('Seconds = {diff} % 60 = {seconds}').format(diff=difference_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_('Difference = {result}').format(result=result_formatted))
        return steps
    
    def _prepare_add_subtract_steps(self, time_str, operation, amount, amount_unit, time_seconds, amount_seconds, result_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for add/subtract"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Time: {time}').format(time=time_str))
        steps.append(_('Amount: {amount} {unit}').format(amount=amount, unit=self._format_unit(amount_unit)))
        steps.append(_('Operation: {op}').format(op=operation.title()))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Time: {time} = {seconds} seconds').format(time=time_str, seconds=time_seconds))
        steps.append(_('Amount: {amount} {unit} = {seconds} seconds').format(amount=amount, unit=self._format_unit(amount_unit), seconds=amount_seconds))
        steps.append('')
        steps.append(_('Step 3: Perform {op}').format(op=operation))
        if operation == 'add':
            steps.append(_('Result = Time + Amount'))
            steps.append(_('Result = {time} + {amount} = {result} seconds').format(time=time_seconds, amount=amount_seconds, result=result_seconds))
        else:
            steps.append(_('Result = Time - Amount'))
            steps.append(_('Result = {time} - {amount} = {result} seconds').format(time=time_seconds, amount=amount_seconds, result=result_seconds))
        steps.append('')
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_('Hours = {result} ÷ 3600 = {hours}').format(result=result_seconds, hours=hours))
        steps.append(_('Minutes = ({result} % 3600) ÷ 60 = {minutes}').format(result=result_seconds, minutes=minutes))
        steps.append(_('Seconds = {result} % 60 = {seconds}').format(result=result_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_('Result = {result}').format(result=result_formatted))
        return steps
    
    def _prepare_convert_steps(self, time_value, from_unit, time_seconds, result, to_unit):
        """Prepare step-by-step solution for time conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Time: {time} {unit}').format(time=time_value, unit=self._format_unit(from_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base unit (seconds)'))
        steps.append(_('Time in seconds = {time} × {factor} = {seconds} seconds').format(time=time_value, factor=self.TIME_CONVERSIONS[from_unit], seconds=time_seconds))
        steps.append('')
        steps.append(_('Step 3: Convert to target unit'))
        steps.append(_('Time in {unit} = {seconds} ÷ {factor} = {result} {unit}').format(unit=self._format_unit(to_unit), seconds=time_seconds, factor=self.TIME_CONVERSIONS[to_unit], result=round(result, 6)))
        return steps
    
    def _prepare_duration_steps(self, start_time_str, end_time_str, start_seconds, end_seconds, duration_seconds, hours, minutes, seconds, result_formatted):
        """Prepare step-by-step solution for duration calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given times'))
        steps.append(_('Start Time: {start}').format(start=start_time_str))
        steps.append(_('End Time: {end}').format(end=end_time_str))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Start Time: {start} = {seconds} seconds').format(start=start_time_str, seconds=start_seconds))
        steps.append(_('End Time: {end} = {seconds} seconds').format(end=end_time_str, seconds=end_seconds))
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
        steps.append(_('Step 4: Convert to hours, minutes, seconds'))
        steps.append(_('Hours = {duration} ÷ 3600 = {hours}').format(duration=duration_seconds, hours=hours))
        steps.append(_('Minutes = ({duration} % 3600) ÷ 60 = {minutes}').format(duration=duration_seconds, minutes=minutes))
        steps.append(_('Seconds = {duration} % 60 = {seconds}').format(duration=duration_seconds, seconds=seconds))
        steps.append('')
        steps.append(_('Step 5: Result'))
        steps.append(_('Duration = {result}').format(result=result_formatted))
        return steps
    
    # Chart data preparation methods
    def _prepare_difference_chart_data(self, time1_seconds, time2_seconds, difference_seconds):
        """Prepare chart data for time difference visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Time 1'), _('Time 2'), _('Difference')],
                    'datasets': [{
                        'label': _('Time (seconds)'),
                        'data': [time1_seconds, time2_seconds, difference_seconds],
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
                            'text': _('Time Difference')
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
            return {'difference_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_duration_chart_data(self, start_seconds, end_seconds, duration_seconds):
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
