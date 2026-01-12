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
from sympy import symbols, Eq, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HoursCalculator(View):
    """
    Professional Hours Calculator with Comprehensive Features
    
    This calculator provides hours calculations with:
    - Calculate hours between two times
    - Add/subtract hours from a time
    - Convert between hours, minutes, seconds, days
    - Calculate total hours from multiple time periods
    - Calculate hours worked (time tracking)
    
    Features:
    - Supports multiple calculation modes
    - Handles various time formats
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/hours_calculator.html'
    
    # Conversion factors
    HOURS_TO_MINUTES = 60.0
    MINUTES_TO_HOURS = 1.0 / 60.0
    HOURS_TO_SECONDS = 3600.0
    SECONDS_TO_HOURS = 1.0 / 3600.0
    HOURS_TO_DAYS = 1.0 / 24.0
    DAYS_TO_HOURS = 24.0
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Hours Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'time_difference')
            
            if calc_type == 'time_difference':
                return self._calculate_time_difference(data)
            elif calc_type == 'add_subtract':
                return self._add_subtract_hours(data)
            elif calc_type == 'convert':
                return self._convert_time_units(data)
            elif calc_type == 'total_hours':
                return self._calculate_total_hours(data)
            elif calc_type == 'hours_worked':
                return self._calculate_hours_worked(data)
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
        """Parse time string in HH:MM or HH:MM:SS format"""
        try:
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
                raise ValueError('Invalid time format')
            
            if hours < 0 or hours >= 24 or minutes < 0 or minutes >= 60 or seconds < 0 or seconds >= 60:
                raise ValueError('Invalid time values')
            
            return hours, minutes, seconds
        except (ValueError, IndexError) as e:
            raise ValueError(f'Invalid time format: {time_str}')
    
    def _time_to_hours(self, hours, minutes, seconds):
        """Convert time to decimal hours"""
        return float(np.add(
            float(hours),
            np.add(
                np.multiply(minutes, self.MINUTES_TO_HOURS),
                np.multiply(seconds, self.SECONDS_TO_HOURS)
            )
        ))
    
    def _hours_to_time(self, decimal_hours):
        """Convert decimal hours to hours, minutes, seconds"""
        hours = int(np.floor(decimal_hours))
        remaining = float(np.subtract(decimal_hours, hours))
        minutes_decimal = float(np.multiply(remaining, self.HOURS_TO_MINUTES))
        minutes = int(np.floor(minutes_decimal))
        seconds_decimal = float(np.subtract(minutes_decimal, minutes))
        seconds = int(np.round(np.multiply(seconds_decimal, self.HOURS_TO_MINUTES)))
        
        if seconds >= 60:
            seconds = 0
            minutes += 1
        if minutes >= 60:
            minutes = 0
            hours += 1
        
        return hours, minutes, seconds
    
    def _calculate_time_difference(self, data):
        """Calculate hours between two times"""
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
            
            start_time_str = data.get('start_time', '').strip()
            end_time_str = data.get('end_time', '').strip()
            next_day = data.get('next_day', False)
            
            try:
                start_h, start_m, start_s = self._parse_time(start_time_str)
                end_h, end_m, end_s = self._parse_time(end_time_str)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            # Convert to decimal hours
            start_hours = self._time_to_hours(start_h, start_m, start_s)
            end_hours = self._time_to_hours(end_h, end_m, end_s)
            
            # If end time is before start time, assume next day
            if end_hours < start_hours and not next_day:
                next_day = True
            
            if next_day:
                end_hours = float(np.add(end_hours, 24.0))
            
            # Calculate difference
            difference_hours = float(np.subtract(end_hours, start_hours))
            
            # Validate result
            if difference_hours < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('End time must be after start time.')
                }, status=400)
            
            if difference_hours > 48:
                return JsonResponse({
                    'success': False,
                    'error': _('Time difference exceeds 48 hours. Please check your inputs.')
                }, status=400)
            
            # Convert to other units
            difference_minutes = float(np.multiply(difference_hours, self.HOURS_TO_MINUTES))
            difference_seconds = float(np.multiply(difference_hours, self.HOURS_TO_HOURS))
            difference_days = float(np.multiply(difference_hours, self.HOURS_TO_DAYS))
            
            # Convert to time format
            diff_h, diff_m, diff_s = self._hours_to_time(difference_hours)
            
            steps = self._prepare_time_difference_steps(start_time_str, end_time_str, next_day, start_hours, end_hours, difference_hours, diff_h, diff_m, diff_s, difference_minutes, difference_seconds, difference_days)
            
            chart_data = self._prepare_time_difference_chart_data(start_hours, end_hours, difference_hours)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating time difference: {error}').format(error=str(e))
            }, status=500)
    
    def _add_subtract_hours(self, data):
        """Add or subtract hours from a time"""
        try:
            if 'time' not in data or not data.get('time'):
                return JsonResponse({
                    'success': False,
                    'error': _('Time is required.')
                }, status=400)
            
            if 'hours' not in data or data.get('hours') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Hours to add/subtract is required.')
                }, status=400)
            
            time_str = data.get('time', '').strip()
            operation = data.get('operation', 'add')
            
            try:
                hours_to_add = float(data.get('hours', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid hours value. Please enter a numeric value.')
                }, status=400)
            
            try:
                time_h, time_m, time_s = self._parse_time(time_str)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            # Convert to decimal hours
            time_hours = self._time_to_hours(time_h, time_m, time_s)
            
            # Add or subtract
            if operation == 'add':
                result_hours = float(np.add(time_hours, hours_to_add))
            else:
                result_hours = float(np.subtract(time_hours, hours_to_add))
            
            # Handle day overflow/underflow
            days = 0
            while result_hours >= 24:
                result_hours = float(np.subtract(result_hours, 24.0))
                days += 1
            while result_hours < 0:
                result_hours = float(np.add(result_hours, 24.0))
                days -= 1
            
            # Convert to time format
            result_h, result_m, result_s = self._hours_to_time(result_hours)
            
            steps = self._prepare_add_subtract_steps(time_str, hours_to_add, operation, time_hours, result_hours, result_h, result_m, result_s, days)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'add_subtract',
                'time': time_str,
                'hours': hours_to_add,
                'operation': operation,
                'result_time': f'{result_h:02d}:{result_m:02d}:{result_s:02d}',
                'result_hours': round(result_hours, 2),
                'days': days,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error adding/subtracting hours: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_time_units(self, data):
        """Convert between time units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Time value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'hours')
            to_unit = data.get('to_unit', 'minutes')
            
            # Validate units
            if from_unit not in ['hours', 'minutes', 'seconds', 'days'] or to_unit not in ['hours', 'minutes', 'seconds', 'days']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Time must be non-negative.')
                }, status=400)
            
            # Convert to hours first
            if from_unit == 'hours':
                hours_value = value
            elif from_unit == 'minutes':
                hours_value = float(np.multiply(value, self.MINUTES_TO_HOURS))
            elif from_unit == 'seconds':
                hours_value = float(np.multiply(value, self.SECONDS_TO_HOURS))
            elif from_unit == 'days':
                hours_value = float(np.multiply(value, self.DAYS_TO_HOURS))
            
            # Convert to target unit
            if to_unit == 'hours':
                result = hours_value
            elif to_unit == 'minutes':
                result = float(np.multiply(hours_value, self.HOURS_TO_MINUTES))
            elif to_unit == 'seconds':
                result = float(np.multiply(hours_value, self.HOURS_TO_SECONDS))
            elif to_unit == 'days':
                result = float(np.multiply(hours_value, self.HOURS_TO_DAYS))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_steps(value, from_unit, to_unit, result, hours_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': round(result, 2),
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _calculate_total_hours(self, data):
        """Calculate total hours from multiple time periods"""
        try:
            if 'time_periods' not in data or not isinstance(data.get('time_periods'), list):
                return JsonResponse({
                    'success': False,
                    'error': _('Time periods are required as a list.')
                }, status=400)
            
            time_periods = data.get('time_periods', [])
            
            if len(time_periods) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('At least one time period is required.')
                }, status=400)
            
            if len(time_periods) > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Maximum 50 time periods allowed.')
                }, status=400)
            
            total_hours = 0.0
            processed_periods = []
            
            for i, period in enumerate(time_periods):
                if not isinstance(period, dict):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid time period data format.')
                    }, status=400)
                
                start_time = period.get('start_time', '').strip()
                end_time = period.get('end_time', '').strip()
                next_day = period.get('next_day', False)
                
                if not start_time or not end_time:
                    continue
                
                try:
                    start_h, start_m, start_s = self._parse_time(start_time)
                    end_h, end_m, end_s = self._parse_time(end_time)
                except ValueError as e:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid time format in period {num}: {error}').format(num=i+1, error=str(e))
                    }, status=400)
                
                start_hours = self._time_to_hours(start_h, start_m, start_s)
                end_hours = self._time_to_hours(end_h, end_m, end_s)
                
                if end_hours < start_hours and not next_day:
                    next_day = True
                
                if next_day:
                    end_hours = float(np.add(end_hours, 24.0))
                
                period_hours = float(np.subtract(end_hours, start_hours))
                
                if period_hours < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid time period {num}: end time must be after start time.').format(num=i+1)
                    }, status=400)
                
                processed_periods.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'hours': round(period_hours, 2)
                })
                
                total_hours = float(np.add(total_hours, period_hours))
            
            # Convert to other units
            total_minutes = float(np.multiply(total_hours, self.HOURS_TO_MINUTES))
            total_seconds = float(np.multiply(total_hours, self.HOURS_TO_SECONDS))
            total_days = float(np.multiply(total_hours, self.HOURS_TO_DAYS))
            
            # Convert to time format
            total_h, total_m, total_s = self._hours_to_time(total_hours)
            
            steps = self._prepare_total_hours_steps(processed_periods, total_hours, total_h, total_m, total_s, total_minutes, total_seconds, total_days)
            
            chart_data = self._prepare_total_hours_chart_data(processed_periods, total_hours)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating total hours: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_hours_worked(self, data):
        """Calculate hours worked (time tracking)"""
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
            
            start_time_str = data.get('start_time', '').strip()
            end_time_str = data.get('end_time', '').strip()
            break_minutes = float(data.get('break_minutes', 0) or 0)
            next_day = data.get('next_day', False)
            
            try:
                start_h, start_m, start_s = self._parse_time(start_time_str)
                end_h, end_m, end_s = self._parse_time(end_time_str)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            if break_minutes < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Break time must be non-negative.')
                }, status=400)
            
            # Convert to decimal hours
            start_hours = self._time_to_hours(start_h, start_m, start_s)
            end_hours = self._time_to_hours(end_h, end_m, end_s)
            
            if end_hours < start_hours and not next_day:
                next_day = True
            
            if next_day:
                end_hours = float(np.add(end_hours, 24.0))
            
            # Calculate total time
            total_hours = float(np.subtract(end_hours, start_hours))
            
            # Subtract break time
            break_hours = float(np.multiply(break_minutes, self.MINUTES_TO_HOURS))
            hours_worked = float(np.subtract(total_hours, break_hours))
            
            if hours_worked < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Break time cannot exceed total time.')
                }, status=400)
            
            # Convert to other units
            hours_worked_minutes = float(np.multiply(hours_worked, self.HOURS_TO_MINUTES))
            
            # Convert to time format
            worked_h, worked_m, worked_s = self._hours_to_time(hours_worked)
            
            steps = self._prepare_hours_worked_steps(start_time_str, end_time_str, next_day, break_minutes, start_hours, end_hours, total_hours, break_hours, hours_worked, worked_h, worked_m, worked_s)
            
            chart_data = self._prepare_hours_worked_chart_data(total_hours, break_hours, hours_worked)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating hours worked: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_time_difference_steps(self, start_time, end_time, next_day, start_hours, end_hours, difference_hours, diff_h, diff_m, diff_s, diff_minutes, diff_seconds, diff_days):
        """Prepare step-by-step solution for time difference calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given times'))
        steps.append(_('Start Time: {time}').format(time=start_time))
        steps.append(_('End Time: {time}').format(time=end_time))
        if next_day:
            steps.append(_('Note: End time is on the next day'))
        steps.append('')
        steps.append(_('Step 2: Convert to decimal hours'))
        steps.append(_('Start Time: {hours} hours').format(hours=start_hours))
        steps.append(_('End Time: {hours} hours').format(hours=end_hours))
        steps.append('')
        steps.append(_('Step 3: Calculate difference'))
        steps.append(_('Difference = End Time - Start Time'))
        steps.append(_('Difference = {end} - {start} = {diff} hours').format(end=end_hours, start=start_hours, diff=difference_hours))
        steps.append('')
        steps.append(_('Step 4: Convert to other units'))
        steps.append(_('Time Format: {h:02d}:{m:02d}:{s:02d}').format(h=diff_h, m=diff_m, s=diff_s))
        steps.append(_('Minutes: {min} minutes').format(min=diff_minutes))
        steps.append(_('Seconds: {sec} seconds').format(sec=diff_seconds))
        steps.append(_('Days: {days} days').format(days=diff_days))
        return steps
    
    def _prepare_add_subtract_steps(self, time_str, hours_to_add, operation, time_hours, result_hours, result_h, result_m, result_s, days):
        """Prepare step-by-step solution for add/subtract hours calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Time: {time}').format(time=time_str))
        steps.append(_('Hours to {op}: {hours}').format(op=_('add') if operation == 'add' else _('subtract'), hours=hours_to_add))
        steps.append('')
        steps.append(_('Step 2: Convert time to decimal hours'))
        steps.append(_('Time = {hours} hours').format(hours=time_hours))
        steps.append('')
        steps.append(_('Step 3: {op} hours').format(op=_('Add') if operation == 'add' else _('Subtract')))
        if operation == 'add':
            steps.append(_('Result = {time} + {hours} = {result} hours').format(time=time_hours, hours=hours_to_add, result=result_hours))
        else:
            steps.append(_('Result = {time} - {hours} = {result} hours').format(time=time_hours, hours=hours_to_add, result=result_hours))
        steps.append('')
        steps.append(_('Step 4: Convert to time format'))
        if days != 0:
            steps.append(_('Result: {h:02d}:{m:02d}:{s:02d} ({days} day(s) {op})').format(h=result_h, m=result_m, s=result_s, days=abs(days), op=_('later') if days > 0 else _('earlier')))
        else:
            steps.append(_('Result: {h:02d}:{m:02d}:{s:02d}').format(h=result_h, m=result_m, s=result_s))
        return steps
    
    def _prepare_convert_steps(self, value, from_unit, to_unit, result, hours_value):
        """Prepare step-by-step solution for time unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        unit_names = {'hours': _('hours'), 'minutes': _('minutes'), 'seconds': _('seconds'), 'days': _('days')}
        steps.append(_('Time: {value} {unit}').format(value=value, unit=unit_names[from_unit]))
        steps.append('')
        if from_unit != 'hours':
            steps.append(_('Step 2: Convert to hours'))
            if from_unit == 'minutes':
                steps.append(_('Hours = Minutes / 60'))
                steps.append(_('Hours = {min} / 60 = {hours} hours').format(min=value, hours=hours_value))
            elif from_unit == 'seconds':
                steps.append(_('Hours = Seconds / 3600'))
                steps.append(_('Hours = {sec} / 3600 = {hours} hours').format(sec=value, hours=hours_value))
            elif from_unit == 'days':
                steps.append(_('Hours = Days × 24'))
                steps.append(_('Hours = {days} × 24 = {hours} hours').format(days=value, hours=hours_value))
            steps.append('')
        if to_unit != 'hours':
            steps.append(_('Step 3: Convert from hours to {unit}').format(unit=unit_names[to_unit]))
            if to_unit == 'minutes':
                steps.append(_('Minutes = Hours × 60'))
                steps.append(_('Minutes = {hours} × 60 = {result} minutes').format(hours=hours_value, result=result))
            elif to_unit == 'seconds':
                steps.append(_('Seconds = Hours × 3600'))
                steps.append(_('Seconds = {hours} × 3600 = {result} seconds').format(hours=hours_value, result=result))
            elif to_unit == 'days':
                steps.append(_('Days = Hours / 24'))
                steps.append(_('Days = {hours} / 24 = {result} days').format(hours=hours_value, result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Time = {result} hours').format(result=result))
        return steps
    
    def _prepare_total_hours_steps(self, processed_periods, total_hours, total_h, total_m, total_s, total_minutes, total_seconds, total_days):
        """Prepare step-by-step solution for total hours calculation"""
        steps = []
        steps.append(_('Step 1: Identify all time periods'))
        for i, period in enumerate(processed_periods, 1):
            steps.append(_('Period {num}: {start} to {end} = {hours} hours').format(
                num=i, start=period['start_time'], end=period['end_time'], hours=period['hours']
            ))
        steps.append('')
        steps.append(_('Step 2: Calculate total hours'))
        hours_list = [str(p['hours']) for p in processed_periods]
        steps.append(_('Total = {hours}').format(hours=' + '.join(hours_list)))
        steps.append(_('Total = {total} hours').format(total=total_hours))
        steps.append('')
        steps.append(_('Step 3: Convert to other units'))
        steps.append(_('Time Format: {h:02d}:{m:02d}:{s:02d}').format(h=total_h, m=total_m, s=total_s))
        steps.append(_('Minutes: {min} minutes').format(min=total_minutes))
        steps.append(_('Seconds: {sec} seconds').format(sec=total_seconds))
        steps.append(_('Days: {days} days').format(days=total_days))
        return steps
    
    def _prepare_hours_worked_steps(self, start_time, end_time, next_day, break_minutes, start_hours, end_hours, total_hours, break_hours, hours_worked, worked_h, worked_m, worked_s):
        """Prepare step-by-step solution for hours worked calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Start Time: {time}').format(time=start_time))
        steps.append(_('End Time: {time}').format(time=end_time))
        if next_day:
            steps.append(_('Note: End time is on the next day'))
        steps.append(_('Break Time: {min} minutes').format(min=break_minutes))
        steps.append('')
        steps.append(_('Step 2: Calculate total time'))
        steps.append(_('Total Time = End Time - Start Time'))
        steps.append(_('Total Time = {end} - {start} = {total} hours').format(end=end_hours, start=start_hours, total=total_hours))
        steps.append('')
        steps.append(_('Step 3: Convert break time to hours'))
        steps.append(_('Break Time = {min} minutes / 60 = {hours} hours').format(min=break_minutes, hours=break_hours))
        steps.append('')
        steps.append(_('Step 4: Calculate hours worked'))
        steps.append(_('Hours Worked = Total Time - Break Time'))
        steps.append(_('Hours Worked = {total} - {break_time} = {worked} hours').format(total=total_hours, break_time=break_hours, worked=hours_worked))
        steps.append('')
        steps.append(_('Step 5: Convert to time format'))
        steps.append(_('Hours Worked: {h:02d}:{m:02d}:{s:02d}').format(h=worked_h, m=worked_m, s=worked_s))
        return steps
    
    # Chart data preparation methods
    def _prepare_time_difference_chart_data(self, start_hours, end_hours, difference_hours):
        """Prepare chart data for time difference calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Start Time'), _('End Time'), _('Difference')],
                    'datasets': [{
                        'label': _('Hours'),
                        'data': [start_hours, end_hours, difference_hours],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24'
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
                            'text': _('Time Difference Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Hours')
                            }
                        }
                    }
                }
            }
            return {'time_difference_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_total_hours_chart_data(self, processed_periods, total_hours):
        """Prepare chart data for total hours calculation"""
        try:
            labels = [f"Period {i+1}" for i in range(len(processed_periods))] + [_('Total')]
            data_values = [p['hours'] for p in processed_periods] + [total_hours]
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': _('Hours'),
                        'data': data_values,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in processed_periods
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in processed_periods
                        ] + ['#10b981'],
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
                            'text': _('Total Hours Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Hours')
                            }
                        }
                    }
                }
            }
            return {'total_hours_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_hours_worked_chart_data(self, total_hours, break_hours, hours_worked):
        """Prepare chart data for hours worked calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Total Time'), _('Break Time'), _('Hours Worked')],
                    'datasets': [{
                        'label': _('Hours'),
                        'data': [total_hours, break_hours, hours_worked],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#fbbf24',
                            '#10b981'
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
                            'text': _('Hours Worked Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Hours')
                            }
                        }
                    }
                }
            }
            return {'hours_worked_chart': chart_config}
        except Exception as e:
            return None
