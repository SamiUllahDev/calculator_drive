from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SpeedCalculator(View):
    """
    Professional Speed Calculator with Comprehensive Features
    
    This calculator provides speed calculations with:
    - Calculate speed from distance and time
    - Calculate distance from speed and time
    - Calculate time from speed and distance
    - Unit conversions (mph, km/h, m/s, knots, etc.)
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/speed_calculator.html'
    
    # Speed conversion factors (to m/s)
    SPEED_CONVERSIONS = {
        'm_s': 1.0,  # meters per second (base unit)
        'km_h': 0.277778,  # 1 km/h = 0.277778 m/s
        'mph': 0.44704,  # 1 mph = 0.44704 m/s
        'knots': 0.514444,  # 1 knot = 0.514444 m/s
        'ft_s': 0.3048,  # 1 ft/s = 0.3048 m/s
    }
    
    # Distance conversion factors (to meters)
    DISTANCE_CONVERSIONS = {
        'meters': 1.0,
        'kilometers': 1000.0,
        'miles': 1609.34,
        'feet': 0.3048,
        'yards': 0.9144,
    }
    
    # Time conversion factors (to seconds)
    TIME_CONVERSIONS = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'm_s': 'm/s',
            'km_h': 'km/h',
            'mph': 'mph',
            'knots': 'knots',
            'ft_s': 'ft/s',
            'meters': 'm',
            'kilometers': 'km',
            'miles': 'mi',
            'feet': 'ft',
            'yards': 'yd',
            'seconds': 's',
            'minutes': 'min',
            'hours': 'h',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Speed Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'speed')
            
            if calc_type == 'speed':
                return self._calculate_speed(data)
            elif calc_type == 'distance':
                return self._calculate_distance(data)
            elif calc_type == 'time':
                return self._calculate_time(data)
            elif calc_type == 'convert':
                return self._convert_speed(data)
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
    
    def _calculate_speed(self, data):
        """Calculate speed from distance and time"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'time' not in data or data.get('time') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Time is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                time = float(data.get('time', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'kilometers')
            time_unit = data.get('time_unit', 'hours')
            result_unit = data.get('result_unit', 'km_h')
            
            # Validate
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            if time <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Time must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            distance_m = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            time_s = float(time * self.TIME_CONVERSIONS[time_unit])
            
            # Calculate speed in m/s
            speed_m_s = float(np.divide(distance_m, time_s))
            
            # Convert to result unit
            result = float(np.divide(speed_m_s, self.SPEED_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result) or result <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_speed_steps(distance, distance_unit, time, time_unit, distance_m, time_s, speed_m_s, result, result_unit)
            chart_data = self._prepare_speed_chart_data(speed_m_s, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'speed',
                'distance': distance,
                'distance_unit': distance_unit,
                'time': time,
                'time_unit': time_unit,
                'speed': round(result, 4),
                'result_unit': result_unit,
                'speed_m_s': round(speed_m_s, 4),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating speed: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_distance(self, data):
        """Calculate distance from speed and time"""
        try:
            if 'speed' not in data or data.get('speed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Speed is required.')
                }, status=400)
            
            if 'time' not in data or data.get('time') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Time is required.')
                }, status=400)
            
            try:
                speed = float(data.get('speed', 0))
                time = float(data.get('time', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            speed_unit = data.get('speed_unit', 'km_h')
            time_unit = data.get('time_unit', 'hours')
            result_unit = data.get('result_unit', 'kilometers')
            
            # Validate
            if speed <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Speed must be greater than zero.')
                }, status=400)
            
            if time <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Time must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            speed_m_s = float(speed * self.SPEED_CONVERSIONS[speed_unit])
            time_s = float(time * self.TIME_CONVERSIONS[time_unit])
            
            # Calculate distance in meters
            distance_m = float(np.multiply(speed_m_s, time_s))
            
            # Convert to result unit
            result = float(np.divide(distance_m, self.DISTANCE_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result) or result <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_distance_steps(speed, speed_unit, time, time_unit, speed_m_s, time_s, distance_m, result, result_unit)
            chart_data = self._prepare_distance_chart_data(distance_m, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'distance',
                'speed': speed,
                'speed_unit': speed_unit,
                'time': time,
                'time_unit': time_unit,
                'distance': round(result, 4),
                'result_unit': result_unit,
                'distance_m': round(distance_m, 4),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating distance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_time(self, data):
        """Calculate time from speed and distance"""
        try:
            if 'speed' not in data or data.get('speed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Speed is required.')
                }, status=400)
            
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            try:
                speed = float(data.get('speed', 0))
                distance = float(data.get('distance', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            speed_unit = data.get('speed_unit', 'km_h')
            distance_unit = data.get('distance_unit', 'kilometers')
            result_unit = data.get('result_unit', 'hours')
            
            # Validate
            if speed <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Speed must be greater than zero.')
                }, status=400)
            
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            speed_m_s = float(speed * self.SPEED_CONVERSIONS[speed_unit])
            distance_m = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Calculate time in seconds
            time_s = float(np.divide(distance_m, speed_m_s))
            
            # Convert to result unit
            result = float(np.divide(time_s, self.TIME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result) or result <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_time_steps(speed, speed_unit, distance, distance_unit, speed_m_s, distance_m, time_s, result, result_unit)
            chart_data = self._prepare_time_chart_data(time_s, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'time',
                'speed': speed,
                'speed_unit': speed_unit,
                'distance': distance,
                'distance_unit': distance_unit,
                'time': round(result, 4),
                'result_unit': result_unit,
                'time_s': round(time_s, 4),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating time: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_speed(self, data):
        """Convert speed between units"""
        try:
            if 'speed' not in data or data.get('speed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Speed is required.')
                }, status=400)
            
            try:
                speed = float(data.get('speed', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'km_h')
            to_unit = data.get('to_unit', 'mph')
            
            # Validate
            if speed < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Speed must be non-negative.')
                }, status=400)
            
            # Convert to base unit (m/s)
            speed_m_s = float(speed * self.SPEED_CONVERSIONS[from_unit])
            
            # Convert to target unit
            result = float(np.divide(speed_m_s, self.SPEED_CONVERSIONS[to_unit]))
            
            steps = self._prepare_convert_steps(speed, from_unit, speed_m_s, result, to_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'speed': speed,
                'from_unit': from_unit,
                'result': round(result, 4),
                'to_unit': to_unit,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting speed: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_speed_steps(self, distance, distance_unit, time, time_unit, distance_m, time_s, speed_m_s, result, result_unit):
        """Prepare step-by-step solution for speed calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {distance} {unit}').format(distance=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Time: {time} {unit}').format(time=time, unit=self._format_unit(time_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Distance: {distance} m').format(distance=distance_m))
        steps.append(_('Time: {time} s').format(time=time_s))
        steps.append('')
        steps.append(_('Step 3: Calculate speed'))
        steps.append(_('Speed = Distance / Time'))
        steps.append(_('Speed = {distance} m / {time} s').format(distance=distance_m, time=time_s))
        steps.append(_('Speed = {speed} m/s').format(speed=round(speed_m_s, 4)))
        steps.append('')
        if result_unit != 'm_s':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Speed = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Speed = {result} m/s').format(result=result))
        return steps
    
    def _prepare_distance_steps(self, speed, speed_unit, time, time_unit, speed_m_s, time_s, distance_m, result, result_unit):
        """Prepare step-by-step solution for distance calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Speed: {speed} {unit}').format(speed=speed, unit=self._format_unit(speed_unit)))
        steps.append(_('Time: {time} {unit}').format(time=time, unit=self._format_unit(time_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Speed: {speed} m/s').format(speed=speed_m_s))
        steps.append(_('Time: {time} s').format(time=time_s))
        steps.append('')
        steps.append(_('Step 3: Calculate distance'))
        steps.append(_('Distance = Speed × Time'))
        steps.append(_('Distance = {speed} m/s × {time} s').format(speed=speed_m_s, time=time_s))
        steps.append(_('Distance = {distance} m').format(distance=distance_m))
        steps.append('')
        if result_unit != 'meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Distance = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Distance = {result} m').format(result=result))
        return steps
    
    def _prepare_time_steps(self, speed, speed_unit, distance, distance_unit, speed_m_s, distance_m, time_s, result, result_unit):
        """Prepare step-by-step solution for time calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Speed: {speed} {unit}').format(speed=speed, unit=self._format_unit(speed_unit)))
        steps.append(_('Distance: {distance} {unit}').format(distance=distance, unit=self._format_unit(distance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Speed: {speed} m/s').format(speed=speed_m_s))
        steps.append(_('Distance: {distance} m').format(distance=distance_m))
        steps.append('')
        steps.append(_('Step 3: Calculate time'))
        steps.append(_('Time = Distance / Speed'))
        steps.append(_('Time = {distance} m / {speed} m/s').format(distance=distance_m, speed=speed_m_s))
        steps.append(_('Time = {time} s').format(time=time_s))
        steps.append('')
        if result_unit != 'seconds':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Time = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Time = {result} s').format(result=result))
        return steps
    
    def _prepare_convert_steps(self, speed, from_unit, speed_m_s, result, to_unit):
        """Prepare step-by-step solution for speed conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Speed: {speed} {unit}').format(speed=speed, unit=self._format_unit(from_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base unit (m/s)'))
        steps.append(_('Speed in m/s = {speed} {unit} × conversion factor').format(speed=speed, unit=self._format_unit(from_unit)))
        steps.append(_('Speed = {speed} m/s').format(speed=round(speed_m_s, 4)))
        steps.append('')
        steps.append(_('Step 3: Convert to target unit'))
        steps.append(_('Speed = {result} {unit}').format(result=result, unit=self._format_unit(to_unit)))
        return steps
    
    # Chart data preparation methods
    def _prepare_speed_chart_data(self, speed_m_s, result_unit):
        """Prepare chart data for speed visualization"""
        try:
            # Convert to result unit for display
            result = float(np.divide(speed_m_s, self.SPEED_CONVERSIONS[result_unit]))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Speed')],
                    'datasets': [{
                        'label': _('Speed ({unit})').format(unit=self._format_unit(result_unit)),
                        'data': [result],
                        'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                        'borderColor': '#3b82f6',
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
                            'text': _('Speed Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Speed ({unit})').format(unit=self._format_unit(result_unit))
                            }
                        }
                    }
                }
            }
            return {'speed_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_distance_chart_data(self, distance_m, result_unit):
        """Prepare chart data for distance visualization"""
        try:
            result = float(np.divide(distance_m, self.DISTANCE_CONVERSIONS[result_unit]))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance')],
                    'datasets': [{
                        'label': _('Distance ({unit})').format(unit=self._format_unit(result_unit)),
                        'data': [result],
                        'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                        'borderColor': '#10b981',
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
                            'text': _('Distance Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Distance ({unit})').format(unit=self._format_unit(result_unit))
                            }
                        }
                    }
                }
            }
            return {'distance_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_time_chart_data(self, time_s, result_unit):
        """Prepare chart data for time visualization"""
        try:
            result = float(np.divide(time_s, self.TIME_CONVERSIONS[result_unit]))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Time')],
                    'datasets': [{
                        'label': _('Time ({unit})').format(unit=self._format_unit(result_unit)),
                        'data': [result],
                        'backgroundColor': 'rgba(234, 179, 8, 0.8)',
                        'borderColor': '#eab308',
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
                            'text': _('Time Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Time ({unit})').format(unit=self._format_unit(result_unit))
                            }
                        }
                    }
                }
            }
            return {'time_chart': chart_config}
        except Exception as e:
            return None
