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
class WindChillCalculator(View):
    """
    Professional Wind Chill Calculator with Comprehensive Features
    
    This calculator provides wind chill calculations with:
    - Calculate wind chill from temperature and wind speed
    - Calculate temperature from wind chill (reverse calculation)
    - Calculate wind speed from wind chill (reverse calculation)
    - Support for Celsius and Fahrenheit
    - Support for mph, km/h, and m/s wind speeds
    
    Features:
    - Supports multiple calculation modes
    - Handles various temperature and wind speed units
    - Provides step-by-step solutions
    - Interactive visualizations
    - Risk category assessment
    """
    template_name = 'other_calculators/wind_chill_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Wind Chill Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'wind_chill')
            
            if calc_type == 'wind_chill':
                return self._calculate_wind_chill(data)
            elif calc_type == 'from_wind_chill':
                return self._calculate_from_wind_chill(data)
            elif calc_type == 'wind_speed':
                return self._calculate_wind_speed(data)
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
    
    def _fahrenheit_to_celsius(self, f):
        """Convert Fahrenheit to Celsius"""
        return (f - 32) * 5 / 9
    
    def _celsius_to_fahrenheit(self, c):
        """Convert Celsius to Fahrenheit"""
        return (c * 9 / 5) + 32
    
    def _mph_to_kmh(self, mph):
        """Convert mph to km/h"""
        return mph * 1.60934
    
    def _kmh_to_mph(self, kmh):
        """Convert km/h to mph"""
        return kmh / 1.60934
    
    def _mph_to_ms(self, mph):
        """Convert mph to m/s"""
        return mph * 0.44704
    
    def _ms_to_mph(self, ms):
        """Convert m/s to mph"""
        return ms / 0.44704
    
    def _calculate_wind_chill_index(self, temp_f, wind_speed_mph):
        """
        Calculate wind chill using North American Wind Chill Index
        Formula: WC = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16
        Where T is temperature in Fahrenheit and V is wind speed in mph
        """
        if wind_speed_mph < 3:
            # Wind chill only applies when wind speed is 3 mph or higher
            return temp_f
        
        if temp_f > 50:
            # Wind chill only applies when temperature is 50°F or below
            return temp_f
        
        wind_chill = 35.74 + (0.6215 * temp_f) - (35.75 * (wind_speed_mph ** 0.16)) + (0.4275 * temp_f * (wind_speed_mph ** 0.16))
        return wind_chill
    
    def _get_wind_chill_category(self, wind_chill_f):
        """Get risk category based on wind chill"""
        if wind_chill_f >= 32:
            return {'category': _('Little Danger'), 'color': 'green', 'description': _('Little danger from freezing for properly clothed person')}
        elif wind_chill_f >= 0:
            return {'category': _('Caution'), 'color': 'yellow', 'description': _('Uncomfortable. Risk of hypothermia if outside for long periods')}
        elif wind_chill_f >= -20:
            return {'category': _('Caution'), 'color': 'yellow', 'description': _('Uncomfortable. Risk of hypothermia if outside for long periods')}
        elif wind_chill_f >= -40:
            return {'category': _('Danger'), 'color': 'orange', 'description': _('Dangerous. Exposed skin can freeze in 10 minutes')}
        else:
            return {'category': _('Extreme Danger'), 'color': 'red', 'description': _('Extremely dangerous. Exposed skin can freeze in 5 minutes')}
    
    def _calculate_wind_chill(self, data):
        """Calculate wind chill from temperature and wind speed"""
        try:
            if 'temperature' not in data or data.get('temperature') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is required.')
                }, status=400)
            
            if 'wind_speed' not in data or data.get('wind_speed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind speed is required.')
                }, status=400)
            
            try:
                temperature = float(data.get('temperature', 0))
                wind_speed = float(data.get('wind_speed', 0))
                temp_unit = data.get('temp_unit', 'F')
                wind_unit = data.get('wind_unit', 'mph')
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Convert to Fahrenheit and mph for calculation
            if temp_unit == 'C':
                temp_f = self._celsius_to_fahrenheit(temperature)
            else:
                temp_f = temperature
            
            if wind_unit == 'kmh':
                wind_speed_mph = self._kmh_to_mph(wind_speed)
            elif wind_unit == 'ms':
                wind_speed_mph = self._ms_to_mph(wind_speed)
            else:
                wind_speed_mph = wind_speed
            
            # Validation
            if wind_speed_mph < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind speed must be non-negative.')
                }, status=400)
            
            # Calculate wind chill
            wind_chill_f = self._calculate_wind_chill_index(temp_f, wind_speed_mph)
            
            # Convert back to requested unit
            if temp_unit == 'C':
                wind_chill_result = self._fahrenheit_to_celsius(wind_chill_f)
            else:
                wind_chill_result = wind_chill_f
            
            # Get risk category
            category = self._get_wind_chill_category(wind_chill_f)
            
            # Calculate wind chill for different wind speeds (for chart)
            wind_speeds = []
            wind_chills = []
            for ws in range(0, 51, 5):
                wc = self._calculate_wind_chill_index(temp_f, ws)
                wind_speeds.append(ws)
                if temp_unit == 'C':
                    wind_chills.append(self._fahrenheit_to_celsius(wc))
                else:
                    wind_chills.append(wc)
            
            steps = self._prepare_wind_chill_steps(temperature, temp_unit, temp_f, wind_speed, wind_unit, wind_speed_mph, wind_chill_f, wind_chill_result, temp_unit)
            chart_data = self._prepare_wind_chill_chart_data(wind_speeds, wind_chills, temp_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'wind_chill',
                'temperature': temperature,
                'temp_unit': temp_unit,
                'wind_speed': wind_speed,
                'wind_unit': wind_unit,
                'wind_chill': round(wind_chill_result, 2),
                'wind_chill_f': round(wind_chill_f, 2),
                'category': category,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating wind chill: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_from_wind_chill(self, data):
        """Calculate temperature from wind chill and wind speed (reverse calculation)"""
        try:
            if 'wind_chill' not in data or data.get('wind_chill') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind chill is required.')
                }, status=400)
            
            if 'wind_speed' not in data or data.get('wind_speed') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind speed is required.')
                }, status=400)
            
            try:
                wind_chill = float(data.get('wind_chill', 0))
                wind_speed = float(data.get('wind_speed', 0))
                temp_unit = data.get('temp_unit', 'F')
                wind_unit = data.get('wind_unit', 'mph')
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Convert to Fahrenheit and mph
            if temp_unit == 'C':
                wind_chill_f = self._celsius_to_fahrenheit(wind_chill)
            else:
                wind_chill_f = wind_chill
            
            if wind_unit == 'kmh':
                wind_speed_mph = self._kmh_to_mph(wind_speed)
            elif wind_unit == 'ms':
                wind_speed_mph = self._ms_to_mph(wind_speed)
            else:
                wind_speed_mph = wind_speed
            
            # Validation
            if wind_speed_mph < 3:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind speed must be at least 3 mph for wind chill calculation.')
                }, status=400)
            
            # Reverse calculation: solve for T in WC = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16
            # WC = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16
            # WC - 35.74 + 35.75×V^0.16 = T×(0.6215 + 0.4275×V^0.16)
            # T = (WC - 35.74 + 35.75×V^0.16) / (0.6215 + 0.4275×V^0.16)
            
            v_power = wind_speed_mph ** 0.16
            temp_f = (wind_chill_f - 35.74 + 35.75 * v_power) / (0.6215 + 0.4275 * v_power)
            
            # Convert back to requested unit
            if temp_unit == 'C':
                temp_result = self._fahrenheit_to_celsius(temp_f)
            else:
                temp_result = temp_f
            
            steps = self._prepare_from_wind_chill_steps(wind_chill, temp_unit, wind_chill_f, wind_speed, wind_unit, wind_speed_mph, v_power, temp_f, temp_result, temp_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'from_wind_chill',
                'wind_chill': wind_chill,
                'temp_unit': temp_unit,
                'wind_speed': wind_speed,
                'wind_unit': wind_unit,
                'temperature': round(temp_result, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating from wind chill: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_wind_speed(self, data):
        """Calculate wind speed from wind chill and temperature (reverse calculation)"""
        try:
            if 'wind_chill' not in data or data.get('wind_chill') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind chill is required.')
                }, status=400)
            
            if 'temperature' not in data or data.get('temperature') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is required.')
                }, status=400)
            
            try:
                wind_chill = float(data.get('wind_chill', 0))
                temperature = float(data.get('temperature', 0))
                temp_unit = data.get('temp_unit', 'F')
                wind_unit = data.get('wind_unit', 'mph')
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Convert to Fahrenheit
            if temp_unit == 'C':
                temp_f = self._celsius_to_fahrenheit(temperature)
                wind_chill_f = self._celsius_to_fahrenheit(wind_chill)
            else:
                temp_f = temperature
                wind_chill_f = wind_chill
            
            # Validation
            if temp_f > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Wind chill only applies when temperature is 50°F (10°C) or below.')
                }, status=400)
            
            # Reverse calculation: solve for V in WC = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16
            # This requires iterative solving or approximation
            # Using Newton's method or binary search
            
            # Binary search for wind speed
            low = 3.0
            high = 100.0
            tolerance = 0.01
            
            for _ in range(100):  # Max iterations
                mid = (low + high) / 2
                wc_mid = self._calculate_wind_chill_index(temp_f, mid)
                
                if abs(wc_mid - wind_chill_f) < tolerance:
                    wind_speed_mph = mid
                    break
                
                if wc_mid < wind_chill_f:
                    high = mid
                else:
                    low = mid
            else:
                wind_speed_mph = (low + high) / 2
            
            # Convert to requested unit
            if wind_unit == 'kmh':
                wind_speed_result = self._mph_to_kmh(wind_speed_mph)
            elif wind_unit == 'ms':
                wind_speed_result = self._mph_to_ms(wind_speed_mph)
            else:
                wind_speed_result = wind_speed_mph
            
            steps = self._prepare_wind_speed_steps(wind_chill, temp_unit, wind_chill_f, temperature, temp_f, wind_speed_mph, wind_speed_result, wind_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'wind_speed',
                'wind_chill': wind_chill,
                'temp_unit': temp_unit,
                'temperature': temperature,
                'wind_unit': wind_unit,
                'wind_speed': round(wind_speed_result, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating wind speed: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_wind_chill_steps(self, temperature, temp_unit, temp_f, wind_speed, wind_unit, wind_speed_mph, wind_chill_f, wind_chill_result, result_unit):
        """Prepare step-by-step solution for wind chill calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Temperature: {temp}°{unit}').format(temp=temperature, unit=temp_unit))
        steps.append(_('Wind Speed: {speed} {unit}').format(speed=wind_speed, unit=wind_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to standard units'))
        if temp_unit == 'C':
            steps.append(_('Temperature in Fahrenheit = ({temp} × 9/5) + 32 = {f}°F').format(temp=temperature, f=round(temp_f, 2)))
        else:
            steps.append(_('Temperature in Fahrenheit = {f}°F').format(f=round(temp_f, 2)))
        if wind_unit != 'mph':
            steps.append(_('Wind Speed in mph = {speed} {unit} = {mph} mph').format(speed=wind_speed, unit=wind_unit, mph=round(wind_speed_mph, 2)))
        else:
            steps.append(_('Wind Speed in mph = {mph} mph').format(mph=round(wind_speed_mph, 2)))
        steps.append('')
        steps.append(_('Step 3: Apply Wind Chill Index formula'))
        steps.append(_('Wind Chill = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16'))
        steps.append(_('Where T = temperature in °F, V = wind speed in mph'))
        v_power = wind_speed_mph ** 0.16
        steps.append(_('V^0.16 = {v_power}').format(v_power=round(v_power, 4)))
        steps.append(_('Wind Chill = 35.74 + 0.6215×{temp} - 35.75×{v_power} + 0.4275×{temp}×{v_power}').format(temp=round(temp_f, 2), v_power=round(v_power, 4)))
        steps.append(_('Wind Chill = {wc}°F').format(wc=round(wind_chill_f, 2)))
        steps.append('')
        steps.append(_('Step 4: Convert to requested unit'))
        if result_unit == 'C':
            steps.append(_('Wind Chill in Celsius = ({f} - 32) × 5/9 = {c}°C').format(f=round(wind_chill_f, 2), c=round(wind_chill_result, 2)))
        else:
            steps.append(_('Wind Chill = {result}°F').format(result=round(wind_chill_result, 2)))
        return steps
    
    def _prepare_from_wind_chill_steps(self, wind_chill, temp_unit, wind_chill_f, wind_speed, wind_unit, wind_speed_mph, v_power, temp_f, temp_result, result_unit):
        """Prepare step-by-step solution for temperature from wind chill"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Wind Chill: {wc}°{unit}').format(wc=wind_chill, unit=temp_unit))
        steps.append(_('Wind Speed: {speed} {unit}').format(speed=wind_speed, unit=wind_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to standard units'))
        if temp_unit == 'C':
            steps.append(_('Wind Chill in Fahrenheit = ({wc} × 9/5) + 32 = {f}°F').format(wc=wind_chill, f=round(wind_chill_f, 2)))
        if wind_unit != 'mph':
            steps.append(_('Wind Speed in mph = {speed} {unit} = {mph} mph').format(speed=wind_speed, unit=wind_unit, mph=round(wind_speed_mph, 2)))
        steps.append('')
        steps.append(_('Step 3: Solve for temperature'))
        steps.append(_('From: WC = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16'))
        steps.append(_('Solving for T:'))
        steps.append(_('T = (WC - 35.74 + 35.75×V^0.16) / (0.6215 + 0.4275×V^0.16)'))
        steps.append(_('V^0.16 = {v_power}').format(v_power=round(v_power, 4)))
        steps.append(_('T = ({wc} - 35.74 + 35.75×{v_power}) / (0.6215 + 0.4275×{v_power})').format(wc=round(wind_chill_f, 2), v_power=round(v_power, 4)))
        steps.append(_('T = {temp}°F').format(temp=round(temp_f, 2)))
        steps.append('')
        steps.append(_('Step 4: Convert to requested unit'))
        if result_unit == 'C':
            steps.append(_('Temperature in Celsius = ({f} - 32) × 5/9 = {c}°C').format(f=round(temp_f, 2), c=round(temp_result, 2)))
        else:
            steps.append(_('Temperature = {result}°F').format(result=round(temp_result, 2)))
        return steps
    
    def _prepare_wind_speed_steps(self, wind_chill, temp_unit, wind_chill_f, temperature, temp_f, wind_speed_mph, wind_speed_result, result_unit):
        """Prepare step-by-step solution for wind speed from wind chill"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Wind Chill: {wc}°{unit}').format(wc=wind_chill, unit=temp_unit))
        steps.append(_('Temperature: {temp}°{unit}').format(temp=temperature, unit=temp_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to standard units'))
        if temp_unit == 'C':
            steps.append(_('Wind Chill in Fahrenheit = {f}°F').format(f=round(wind_chill_f, 2)))
            steps.append(_('Temperature in Fahrenheit = {f}°F').format(f=round(temp_f, 2)))
        steps.append('')
        steps.append(_('Step 3: Solve for wind speed'))
        steps.append(_('From: WC = 35.74 + 0.6215×T - 35.75×V^0.16 + 0.4275×T×V^0.16'))
        steps.append(_('Using iterative method to solve for V'))
        steps.append(_('Wind Speed = {speed} mph').format(speed=round(wind_speed_mph, 2)))
        steps.append('')
        steps.append(_('Step 4: Convert to requested unit'))
        if result_unit != 'mph':
            steps.append(_('Wind Speed = {result} {unit}').format(result=round(wind_speed_result, 2), unit=result_unit))
        else:
            steps.append(_('Wind Speed = {result} mph').format(result=round(wind_speed_result, 2)))
        return steps
    
    # Chart data preparation methods
    def _prepare_wind_chill_chart_data(self, wind_speeds, wind_chills, temp_unit):
        """Prepare chart data for wind chill visualization"""
        try:
            chart_config = {
                'type': 'line',
                'data': {
                    'labels': [f'{ws} mph' for ws in wind_speeds],
                    'datasets': [{
                        'label': _('Wind Chill (°{unit})').format(unit=temp_unit),
                        'data': wind_chills,
                        'borderColor': 'rgba(59, 130, 246, 1)',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'top'
                        },
                        'title': {
                            'display': True,
                            'text': _('Wind Chill vs Wind Speed')
                        }
                    },
                    'scales': {
                        'x': {
                            'title': {
                                'display': True,
                                'text': _('Wind Speed (mph)')
                            }
                        },
                        'y': {
                            'title': {
                                'display': True,
                                'text': _('Wind Chill (°{unit})').format(unit=temp_unit)
                            }
                        }
                    }
                }
            }
            return {'wind_chill_chart': chart_config}
        except Exception as e:
            return None
