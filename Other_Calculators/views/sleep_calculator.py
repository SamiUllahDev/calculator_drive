from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
from datetime import datetime, timedelta
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SleepCalculator(View):
    """
    Professional Sleep Calculator with Comprehensive Features
    
    This calculator provides sleep cycle calculations with:
    - Calculate optimal wake times based on bedtime
    - Calculate optimal bed times based on wake time
    - Calculate wake times if sleeping now
    - Sleep cycle optimization (90-minute cycles)
    
    Features:
    - Supports multiple calculation modes
    - Accounts for time to fall asleep
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/sleep_calculator.html'
    
    # Average sleep cycle duration in minutes
    SLEEP_CYCLE = 90
    FALL_ASLEEP_TIME = 15  # Average time to fall asleep
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Sleep Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'wake_time')
            
            if calc_type == 'wake_time':
                return self._calculate_wake_time(data)
            elif calc_type == 'bed_time':
                return self._calculate_bed_time(data)
            elif calc_type == 'sleep_now':
                return self._calculate_sleep_now(data)
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
    
    def _calculate_wake_time(self, data):
        """Calculate when to wake up based on bedtime"""
        try:
            if 'bed_hour' not in data or data.get('bed_hour') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Bedtime hour is required.')
                }, status=400)
            
            if 'bed_minute' not in data or data.get('bed_minute') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Bedtime minute is required.')
                }, status=400)
            
            try:
                bed_hour = int(data.get('bed_hour', 22))
                bed_minute = int(data.get('bed_minute', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter valid numbers.')
                }, status=400)
            
            # Validate time range
            if not (0 <= bed_hour <= 23) or not (0 <= bed_minute <= 59):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time. Hour must be 0-23 and minute must be 0-59.')
                }, status=400)
            
            # Create datetime for bedtime (using today as base)
            now = datetime.now()
            bed_time = now.replace(hour=bed_hour, minute=bed_minute, second=0, microsecond=0)
            
            # If bedtime is before current time, assume next day
            if bed_time < now:
                bed_time += timedelta(days=1)
            
            # Calculate fall asleep time
            fall_asleep_time = bed_time + timedelta(minutes=self.FALL_ASLEEP_TIME)
            
            # Calculate optimal wake times (4, 5, 6 cycles)
            wake_times = []
            for cycles in range(4, 7):
                sleep_duration = cycles * self.SLEEP_CYCLE
                wake_time = fall_asleep_time + timedelta(minutes=sleep_duration)
                total_hours = sleep_duration / 60
                
                wake_times.append({
                    'cycles': cycles,
                    'time': wake_time.strftime('%I:%M %p'),
                    'time_24': wake_time.strftime('%H:%M'),
                    'sleep_hours': round(total_hours, 1),
                    'quality': self.get_sleep_quality(cycles)
                })
            
            steps = self._prepare_wake_time_steps(bed_time, fall_asleep_time, wake_times)
            chart_data = self._prepare_wake_time_chart_data(wake_times)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'wake_time',
                'bed_time': bed_time.strftime('%I:%M %p'),
                'bed_time_24': bed_time.strftime('%H:%M'),
                'fall_asleep_time': fall_asleep_time.strftime('%I:%M %p'),
                'wake_times': wake_times,
                'recommended': wake_times[1] if len(wake_times) > 1 else wake_times[0],
                'step_by_step': steps,
                'chart_data': chart_data,
                'tips': self._get_sleep_tips()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating wake time: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_bed_time(self, data):
        """Calculate when to go to bed based on desired wake time"""
        try:
            if 'wake_hour' not in data or data.get('wake_hour') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wake time hour is required.')
                }, status=400)
            
            if 'wake_minute' not in data or data.get('wake_minute') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wake time minute is required.')
                }, status=400)
            
            try:
                wake_hour = int(data.get('wake_hour', 7))
                wake_minute = int(data.get('wake_minute', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter valid numbers.')
                }, status=400)
            
            # Validate time range
            if not (0 <= wake_hour <= 23) or not (0 <= wake_minute <= 59):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time. Hour must be 0-23 and minute must be 0-59.')
                }, status=400)
            
            now = datetime.now()
            wake_time = now.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
            
            # If wake time is before current time, assume next day
            if wake_time < now:
                wake_time += timedelta(days=1)
            
            # Calculate bed times (4, 5, 6 cycles)
            bed_times = []
            for cycles in range(4, 7):
                sleep_duration = cycles * self.SLEEP_CYCLE + self.FALL_ASLEEP_TIME
                bed_time = wake_time - timedelta(minutes=sleep_duration)
                total_hours = (cycles * self.SLEEP_CYCLE) / 60
                
                bed_times.append({
                    'cycles': cycles,
                    'time': bed_time.strftime('%I:%M %p'),
                    'time_24': bed_time.strftime('%H:%M'),
                    'sleep_hours': round(total_hours, 1),
                    'quality': self.get_sleep_quality(cycles)
                })
            
            steps = self._prepare_bed_time_steps(wake_time, bed_times)
            chart_data = self._prepare_bed_time_chart_data(bed_times)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'bed_time',
                'wake_time': wake_time.strftime('%I:%M %p'),
                'wake_time_24': wake_time.strftime('%H:%M'),
                'bed_times': bed_times,
                'recommended': bed_times[1] if len(bed_times) > 1 else bed_times[0],
                'step_by_step': steps,
                'chart_data': chart_data,
                'tips': self._get_sleep_tips()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating bed time: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_sleep_now(self, data):
        """Calculate wake times if going to sleep now"""
        try:
            now = datetime.now()
            fall_asleep_time = now + timedelta(minutes=self.FALL_ASLEEP_TIME)
            
            wake_times = []
            for cycles in range(4, 7):
                sleep_duration = cycles * self.SLEEP_CYCLE
                wake_time = fall_asleep_time + timedelta(minutes=sleep_duration)
                total_hours = sleep_duration / 60
                
                wake_times.append({
                    'cycles': cycles,
                    'time': wake_time.strftime('%I:%M %p'),
                    'time_24': wake_time.strftime('%H:%M'),
                    'sleep_hours': round(total_hours, 1),
                    'quality': self.get_sleep_quality(cycles)
                })
            
            steps = self._prepare_sleep_now_steps(now, fall_asleep_time, wake_times)
            chart_data = self._prepare_wake_time_chart_data(wake_times)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'sleep_now',
                'current_time': now.strftime('%I:%M %p'),
                'current_time_24': now.strftime('%H:%M'),
                'fall_asleep_time': fall_asleep_time.strftime('%I:%M %p'),
                'wake_times': wake_times,
                'recommended': wake_times[1] if len(wake_times) > 1 else wake_times[0],
                'step_by_step': steps,
                'chart_data': chart_data,
                'tips': self._get_sleep_tips()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating sleep now: {error}').format(error=str(e))
            }, status=500)
    
    def get_sleep_quality(self, cycles):
        """Get sleep quality rating based on number of cycles"""
        if cycles == 6:
            return {'rating': _('Excellent'), 'color': 'green'}
        elif cycles == 5:
            return {'rating': _('Good'), 'color': 'blue'}
        elif cycles == 4:
            return {'rating': _('Fair'), 'color': 'yellow'}
        else:
            return {'rating': _('Poor'), 'color': 'red'}
    
    def _get_sleep_tips(self):
        """Get sleep tips"""
        return [
            _('Maintain a consistent sleep schedule'),
            _('Avoid screens 1 hour before bed'),
            _('Keep your room cool (65-68°F / 18-20°C)'),
            _('Avoid caffeine 6 hours before sleep'),
            _('Exercise regularly, but not before bed'),
            _('Create a relaxing bedtime routine'),
            _('Keep your bedroom dark and quiet'),
            _('Avoid large meals before bedtime')
        ]
    
    def _prepare_wake_time_steps(self, bed_time, fall_asleep_time, wake_times):
        """Prepare step-by-step solution for wake time calculation"""
        steps = []
        steps.append(_('Step 1: Identify bedtime'))
        steps.append(_('Bedtime: {time}').format(time=bed_time.strftime('%I:%M %p')))
        steps.append('')
        steps.append(_('Step 2: Account for time to fall asleep'))
        steps.append(_('Average time to fall asleep: {minutes} minutes').format(minutes=self.FALL_ASLEEP_TIME))
        steps.append(_('Fall asleep time: {time}').format(time=fall_asleep_time.strftime('%I:%M %p')))
        steps.append('')
        steps.append(_('Step 3: Calculate wake times based on sleep cycles'))
        steps.append(_('Each sleep cycle lasts approximately {minutes} minutes').format(minutes=self.SLEEP_CYCLE))
        for wake_time in wake_times:
            steps.append(_('{cycles} cycles = {hours} hours → Wake at {time} ({quality})').format(
                cycles=wake_time['cycles'],
                hours=wake_time['sleep_hours'],
                time=wake_time['time'],
                quality=wake_time['quality']['rating']
            ))
        steps.append('')
        steps.append(_('Step 4: Recommended wake time'))
        recommended = wake_times[1] if len(wake_times) > 1 else wake_times[0]
        steps.append(_('Recommended: {time} ({cycles} cycles, {hours} hours)').format(
            time=recommended['time'],
            cycles=recommended['cycles'],
            hours=recommended['sleep_hours']
        ))
        return steps
    
    def _prepare_bed_time_steps(self, wake_time, bed_times):
        """Prepare step-by-step solution for bed time calculation"""
        steps = []
        steps.append(_('Step 1: Identify desired wake time'))
        steps.append(_('Wake time: {time}').format(time=wake_time.strftime('%I:%M %p')))
        steps.append('')
        steps.append(_('Step 2: Calculate bed times based on sleep cycles'))
        steps.append(_('Each sleep cycle lasts approximately {minutes} minutes').format(minutes=self.SLEEP_CYCLE))
        steps.append(_('Time to fall asleep: {minutes} minutes').format(minutes=self.FALL_ASLEEP_TIME))
        for bed_time in bed_times:
            total_minutes = bed_time['cycles'] * self.SLEEP_CYCLE + self.FALL_ASLEEP_TIME
            steps.append(_('{cycles} cycles = {hours} hours sleep + {fall} min fall asleep = {total} min total → Bed at {time} ({quality})').format(
                cycles=bed_time['cycles'],
                hours=bed_time['sleep_hours'],
                fall=self.FALL_ASLEEP_TIME,
                total=total_minutes,
                time=bed_time['time'],
                quality=bed_time['quality']['rating']
            ))
        steps.append('')
        steps.append(_('Step 3: Recommended bed time'))
        recommended = bed_times[1] if len(bed_times) > 1 else bed_times[0]
        steps.append(_('Recommended: {time} ({cycles} cycles, {hours} hours sleep)').format(
            time=recommended['time'],
            cycles=recommended['cycles'],
            hours=recommended['sleep_hours']
        ))
        return steps
    
    def _prepare_sleep_now_steps(self, now, fall_asleep_time, wake_times):
        """Prepare step-by-step solution for sleep now calculation"""
        steps = []
        steps.append(_('Step 1: Current time'))
        steps.append(_('Current time: {time}').format(time=now.strftime('%I:%M %p')))
        steps.append('')
        steps.append(_('Step 2: Account for time to fall asleep'))
        steps.append(_('Average time to fall asleep: {minutes} minutes').format(minutes=self.FALL_ASLEEP_TIME))
        steps.append(_('Fall asleep time: {time}').format(time=fall_asleep_time.strftime('%I:%M %p')))
        steps.append('')
        steps.append(_('Step 3: Calculate wake times based on sleep cycles'))
        steps.append(_('Each sleep cycle lasts approximately {minutes} minutes').format(minutes=self.SLEEP_CYCLE))
        for wake_time in wake_times:
            steps.append(_('{cycles} cycles = {hours} hours → Wake at {time} ({quality})').format(
                cycles=wake_time['cycles'],
                hours=wake_time['sleep_hours'],
                time=wake_time['time'],
                quality=wake_time['quality']['rating']
            ))
        steps.append('')
        steps.append(_('Step 4: Recommended wake time'))
        recommended = wake_times[1] if len(wake_times) > 1 else wake_times[0]
        steps.append(_('Recommended: {time} ({cycles} cycles, {hours} hours)').format(
            time=recommended['time'],
            cycles=recommended['cycles'],
            hours=recommended['sleep_hours']
        ))
        return steps
    
    def _prepare_wake_time_chart_data(self, wake_times):
        """Prepare chart data for wake time visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [f"{wt['cycles']} {_('cycles')}" for wt in wake_times],
                    'datasets': [{
                        'label': _('Sleep Hours'),
                        'data': [wt['sleep_hours'] for wt in wake_times],
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.8)' if wt['quality']['color'] == 'green'
                            else 'rgba(59, 130, 246, 0.8)' if wt['quality']['color'] == 'blue'
                            else 'rgba(234, 179, 8, 0.8)'
                            for wt in wake_times
                        ],
                        'borderColor': [
                            '#10b981' if wt['quality']['color'] == 'green'
                            else '#3b82f6' if wt['quality']['color'] == 'blue'
                            else '#eab308'
                            for wt in wake_times
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
                            'text': _('Sleep Duration by Cycle Count')
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
            return {'wake_time_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_bed_time_chart_data(self, bed_times):
        """Prepare chart data for bed time visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [f"{bt['cycles']} {_('cycles')}" for bt in bed_times],
                    'datasets': [{
                        'label': _('Sleep Hours'),
                        'data': [bt['sleep_hours'] for bt in bed_times],
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.8)' if bt['quality']['color'] == 'green'
                            else 'rgba(59, 130, 246, 0.8)' if bt['quality']['color'] == 'blue'
                            else 'rgba(234, 179, 8, 0.8)'
                            for bt in bed_times
                        ],
                        'borderColor': [
                            '#10b981' if bt['quality']['color'] == 'green'
                            else '#3b82f6' if bt['quality']['color'] == 'blue'
                            else '#eab308'
                            for bt in bed_times
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
                            'text': _('Sleep Duration by Cycle Count')
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
            return {'bed_time_chart': chart_config}
        except Exception as e:
            return None
