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
class TimeCardCalculator(View):
    """
    Professional Time Card Calculator with Comprehensive Features
    
    This calculator provides time card calculations with:
    - Calculate hours worked from clock in/out times
    - Account for break times
    - Calculate overtime hours
    - Calculate pay (regular and overtime)
    - Weekly totals
    - Multiple day entries
    
    Features:
    - Supports multiple calculation modes
    - Handles various time formats
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/time_card_calculator.html'
    
    # Standard work week hours
    STANDARD_WEEK_HOURS = 40.0
    OVERTIME_THRESHOLD = 8.0  # Hours per day for overtime
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Time Card Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'daily')
            
            if calc_type == 'daily':
                return self._calculate_daily(data)
            elif calc_type == 'weekly':
                return self._calculate_weekly(data)
            elif calc_type == 'pay':
                return self._calculate_pay(data)
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
    
    def _seconds_to_hours(self, seconds):
        """Convert seconds to decimal hours"""
        return float(seconds / 3600.0)
    
    def _format_time(self, seconds):
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _calculate_daily(self, data):
        """Calculate daily hours worked"""
        try:
            if 'clock_in' not in data or not data.get('clock_in'):
                return JsonResponse({
                    'success': False,
                    'error': _('Clock in time is required.')
                }, status=400)
            
            if 'clock_out' not in data or not data.get('clock_out'):
                return JsonResponse({
                    'success': False,
                    'error': _('Clock out time is required.')
                }, status=400)
            
            clock_in_str = data.get('clock_in', '')
            clock_out_str = data.get('clock_out', '')
            break_minutes = float(data.get('break_minutes', 0))
            
            # Parse times
            clock_in_seconds = self._parse_time(clock_in_str)
            clock_out_seconds = self._parse_time(clock_out_str)
            
            if clock_in_seconds is None or clock_out_seconds is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time format. Use HH:MM or HH:MM:SS format.')
                }, status=400)
            
            # Handle next day (clock out is after midnight)
            if clock_out_seconds < clock_in_seconds:
                clock_out_seconds += 86400  # Add 24 hours
            
            # Calculate total time
            total_seconds = clock_out_seconds - clock_in_seconds
            
            # Subtract break time
            break_seconds = break_minutes * 60
            worked_seconds = total_seconds - break_seconds
            
            if worked_seconds < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Break time cannot exceed total time.')
                }, status=400)
            
            # Calculate hours
            total_hours = self._seconds_to_hours(total_seconds)
            break_hours = self._seconds_to_hours(break_seconds)
            worked_hours = self._seconds_to_hours(worked_seconds)
            
            # Calculate overtime
            regular_hours = min(worked_hours, self.OVERTIME_THRESHOLD)
            overtime_hours = max(0, worked_hours - self.OVERTIME_THRESHOLD)
            
            steps = self._prepare_daily_steps(clock_in_str, clock_out_str, clock_in_seconds, clock_out_seconds, total_seconds, break_minutes, break_seconds, worked_seconds, total_hours, break_hours, worked_hours, regular_hours, overtime_hours)
            chart_data = self._prepare_daily_chart_data(regular_hours, overtime_hours, break_hours)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating daily hours: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_weekly(self, data):
        """Calculate weekly hours from multiple days"""
        try:
            if 'days' not in data or not data.get('days'):
                return JsonResponse({
                    'success': False,
                    'error': _('At least one day is required.')
                }, status=400)
            
            days = data.get('days', [])
            
            if len(days) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('At least one day is required.')
                }, status=400)
            
            total_worked_hours = 0.0
            total_regular_hours = 0.0
            total_overtime_hours = 0.0
            daily_breakdown = []
            
            for day_data in days:
                clock_in_str = day_data.get('clock_in', '')
                clock_out_str = day_data.get('clock_out', '')
                break_minutes = float(day_data.get('break_minutes', 0))
                
                # Parse times
                clock_in_seconds = self._parse_time(clock_in_str)
                clock_out_seconds = self._parse_time(clock_out_str)
                
                if clock_in_seconds is None or clock_out_seconds is None:
                    continue
                
                # Handle next day
                if clock_out_seconds < clock_in_seconds:
                    clock_out_seconds += 86400
                
                # Calculate hours
                total_seconds = clock_out_seconds - clock_in_seconds
                break_seconds = break_minutes * 60
                worked_seconds = total_seconds - break_seconds
                
                if worked_seconds < 0:
                    continue
                
                worked_hours = self._seconds_to_hours(worked_seconds)
                regular_hours = min(worked_hours, self.OVERTIME_THRESHOLD)
                overtime_hours = max(0, worked_hours - self.OVERTIME_THRESHOLD)
                
                total_worked_hours += worked_hours
                total_regular_hours += regular_hours
                total_overtime_hours += overtime_hours
                
                daily_breakdown.append({
                    'day': day_data.get('day', ''),
                    'worked_hours': round(worked_hours, 2),
                    'regular_hours': round(regular_hours, 2),
                    'overtime_hours': round(overtime_hours, 2),
                })
            
            # Calculate weekly overtime (over 40 hours)
            weekly_regular = min(total_worked_hours, self.STANDARD_WEEK_HOURS)
            weekly_overtime = max(0, total_worked_hours - self.STANDARD_WEEK_HOURS)
            
            steps = self._prepare_weekly_steps(days, daily_breakdown, total_worked_hours, total_regular_hours, total_overtime_hours, weekly_regular, weekly_overtime)
            chart_data = self._prepare_weekly_chart_data(daily_breakdown, total_worked_hours, weekly_regular, weekly_overtime)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating weekly hours: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_pay(self, data):
        """Calculate pay from hours worked"""
        try:
            if 'regular_hours' not in data or data.get('regular_hours') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Regular hours is required.')
                }, status=400)
            
            try:
                regular_hours = float(data.get('regular_hours', 0))
                overtime_hours = float(data.get('overtime_hours', 0))
                hourly_rate = float(data.get('hourly_rate', 0))
                overtime_multiplier = float(data.get('overtime_multiplier', 1.5))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            currency = data.get('currency', 'usd')
            
            # Validate
            if regular_hours < 0 or overtime_hours < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Hours must be non-negative.')
                }, status=400)
            
            if hourly_rate < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Hourly rate must be non-negative.')
                }, status=400)
            
            # Calculate pay
            regular_pay = float(np.multiply(regular_hours, hourly_rate))
            overtime_rate = float(np.multiply(hourly_rate, overtime_multiplier))
            overtime_pay = float(np.multiply(overtime_hours, overtime_rate))
            total_pay = float(np.add(regular_pay, overtime_pay))
            
            steps = self._prepare_pay_steps(regular_hours, overtime_hours, hourly_rate, overtime_multiplier, regular_pay, overtime_rate, overtime_pay, total_pay, currency)
            chart_data = self._prepare_pay_chart_data(regular_pay, overtime_pay, total_pay)
            
            return JsonResponse({
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
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating pay: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_daily_steps(self, clock_in_str, clock_out_str, clock_in_seconds, clock_out_seconds, total_seconds, break_minutes, break_seconds, worked_seconds, total_hours, break_hours, worked_hours, regular_hours, overtime_hours):
        """Prepare step-by-step solution for daily calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Clock In: {time}').format(time=clock_in_str))
        steps.append(_('Clock Out: {time}').format(time=clock_out_str))
        steps.append(_('Break Time: {break_time} minutes').format(break_time=break_minutes))
        steps.append('')
        steps.append(_('Step 2: Convert to seconds'))
        steps.append(_('Clock In: {time} = {seconds} seconds').format(time=clock_in_str, seconds=clock_in_seconds))
        steps.append(_('Clock Out: {time} = {seconds} seconds').format(time=clock_out_str, seconds=clock_out_seconds))
        steps.append('')
        steps.append(_('Step 3: Calculate total time'))
        steps.append(_('Total Time = Clock Out - Clock In'))
        steps.append(_('Total Time = {out} - {clock_in} = {total} seconds').format(out=clock_out_seconds, clock_in=clock_in_seconds, total=total_seconds))
        steps.append(_('Total Time = {hours} hours').format(hours=round(total_hours, 2)))
        steps.append('')
        steps.append(_('Step 4: Subtract break time'))
        steps.append(_('Break Time = {break_time} minutes = {seconds} seconds = {hours} hours').format(break_time=break_minutes, seconds=break_seconds, hours=round(break_hours, 2)))
        steps.append(_('Worked Time = Total Time - Break Time'))
        steps.append(_('Worked Time = {total} - {break_time} = {worked} hours').format(total=round(total_hours, 2), break_time=round(break_hours, 2), worked=round(worked_hours, 2)))
        steps.append('')
        steps.append(_('Step 5: Calculate regular and overtime'))
        steps.append(_('Regular Hours = min(Worked Hours, {threshold}) = {regular} hours').format(threshold=self.OVERTIME_THRESHOLD, regular=round(regular_hours, 2)))
        steps.append(_('Overtime Hours = max(0, Worked Hours - {threshold}) = {overtime} hours').format(threshold=self.OVERTIME_THRESHOLD, overtime=round(overtime_hours, 2)))
        return steps
    
    def _prepare_weekly_steps(self, days, daily_breakdown, total_worked_hours, total_regular_hours, total_overtime_hours, weekly_regular, weekly_overtime):
        """Prepare step-by-step solution for weekly calculation"""
        steps = []
        steps.append(_('Step 1: Calculate hours for each day'))
        for i, breakdown in enumerate(daily_breakdown):
            steps.append(_('{day}: {hours} hours ({regular} regular, {overtime} overtime)').format(
                day=breakdown['day'],
                hours=breakdown['worked_hours'],
                regular=breakdown['regular_hours'],
                overtime=breakdown['overtime_hours']
            ))
        steps.append('')
        steps.append(_('Step 2: Sum daily hours'))
        steps.append(_('Total Worked Hours = {total} hours').format(total=round(total_worked_hours, 2)))
        steps.append(_('Total Regular Hours = {regular} hours').format(regular=round(total_regular_hours, 2)))
        steps.append(_('Total Overtime Hours = {overtime} hours').format(overtime=round(total_overtime_hours, 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate weekly overtime'))
        steps.append(_('Weekly Regular = min(Total Hours, {threshold}) = {regular} hours').format(threshold=self.STANDARD_WEEK_HOURS, regular=round(weekly_regular, 2)))
        steps.append(_('Weekly Overtime = max(0, Total Hours - {threshold}) = {overtime} hours').format(threshold=self.STANDARD_WEEK_HOURS, overtime=round(weekly_overtime, 2)))
        return steps
    
    def _prepare_pay_steps(self, regular_hours, overtime_hours, hourly_rate, overtime_multiplier, regular_pay, overtime_rate, overtime_pay, total_pay, currency):
        """Prepare step-by-step solution for pay calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Regular Hours: {hours}').format(hours=regular_hours))
        steps.append(_('Overtime Hours: {hours}').format(hours=overtime_hours))
        steps.append(_('Hourly Rate: {rate} {currency}').format(rate=hourly_rate, currency=currency.upper()))
        steps.append(_('Overtime Multiplier: {mult}').format(mult=overtime_multiplier))
        steps.append('')
        steps.append(_('Step 2: Calculate regular pay'))
        steps.append(_('Regular Pay = Regular Hours × Hourly Rate'))
        steps.append(_('Regular Pay = {hours} × {rate} = {pay} {currency}').format(hours=regular_hours, rate=hourly_rate, pay=round(regular_pay, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 3: Calculate overtime rate'))
        steps.append(_('Overtime Rate = Hourly Rate × Multiplier'))
        steps.append(_('Overtime Rate = {rate} × {mult} = {overtime_rate} {currency}').format(rate=hourly_rate, mult=overtime_multiplier, overtime_rate=round(overtime_rate, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 4: Calculate overtime pay'))
        steps.append(_('Overtime Pay = Overtime Hours × Overtime Rate'))
        steps.append(_('Overtime Pay = {hours} × {rate} = {pay} {currency}').format(hours=overtime_hours, rate=round(overtime_rate, 2), pay=round(overtime_pay, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 5: Calculate total pay'))
        steps.append(_('Total Pay = Regular Pay + Overtime Pay'))
        steps.append(_('Total Pay = {regular} + {overtime} = {total} {currency}').format(regular=round(regular_pay, 2), overtime=round(overtime_pay, 2), total=round(total_pay, 2), currency=currency.upper()))
        return steps
    
    # Chart data preparation methods
    def _prepare_daily_chart_data(self, regular_hours, overtime_hours, break_hours):
        """Prepare chart data for daily hours visualization"""
        try:
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': [_('Regular Hours'), _('Overtime Hours'), _('Break Time')],
                    'datasets': [{
                        'data': [regular_hours, overtime_hours, break_hours],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(234, 179, 8, 0.8)',
                            'rgba(156, 163, 175, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#eab308',
                            '#9ca3af'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Daily Hours Breakdown')
                        }
                    }
                }
            }
            return {'daily_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_weekly_chart_data(self, daily_breakdown, total_worked_hours, weekly_regular, weekly_overtime):
        """Prepare chart data for weekly hours visualization"""
        try:
            days = [d['day'] for d in daily_breakdown]
            hours = [d['worked_hours'] for d in daily_breakdown]
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': days + [_('Total')],
                    'datasets': [{
                        'label': _('Hours Worked'),
                        'data': hours + [total_worked_hours],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in days
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in days
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
                            'text': _('Weekly Hours Worked')
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
            return {'weekly_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_pay_chart_data(self, regular_pay, overtime_pay, total_pay):
        """Prepare chart data for pay visualization"""
        try:
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': [_('Regular Pay'), _('Overtime Pay')],
                    'datasets': [{
                        'data': [regular_pay, overtime_pay],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(234, 179, 8, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
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
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Pay Breakdown (Total: {total})').format(total=total_pay)
                        }
                    }
                }
            }
            return {'pay_chart': chart_config}
        except Exception as e:
            return None
