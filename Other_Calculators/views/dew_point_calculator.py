from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, Eq, solve, simplify, latex, log, exp


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DewPointCalculator(View):
    """
    Professional Dew Point Calculator with Comprehensive Features
    
    This calculator provides dew point calculations with:
    - Calculate dew point from temperature and relative humidity
    - Calculate relative humidity from temperature and dew point
    - Calculate temperature from dew point and relative humidity
    - Unit conversions (Celsius, Fahrenheit, Kelvin)
    
    Features:
    - Supports multiple calculation modes
    - Handles various temperature units
    - Provides step-by-step solutions
    - Interactive visualizations
    - Uses Magnus formula for accurate calculations
    """
    template_name = 'other_calculators/dew_point_calculator.html'
    
    # Magnus formula constants
    A = 17.27
    B = 237.7  # °C
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit.replace('_', ' ').title()
    
    def _celsius_to_fahrenheit(self, celsius):
        """Convert Celsius to Fahrenheit"""
        result = np.multiply(celsius, 9.0/5.0) + 32.0
        return float(result)
    
    def _fahrenheit_to_celsius(self, fahrenheit):
        """Convert Fahrenheit to Celsius"""
        result = np.multiply(fahrenheit - 32.0, 5.0/9.0)
        return float(result)
    
    def _celsius_to_kelvin(self, celsius):
        """Convert Celsius to Kelvin"""
        return float(celsius + 273.15)
    
    def _kelvin_to_celsius(self, kelvin):
        """Convert Kelvin to Celsius"""
        return float(kelvin - 273.15)
    
    def _convert_temperature(self, value, from_unit, to_unit):
        """Convert temperature between units"""
        # Convert to Celsius first
        if from_unit == 'celsius':
            temp_c = value
        elif from_unit == 'fahrenheit':
            temp_c = self._fahrenheit_to_celsius(value)
        elif from_unit == 'kelvin':
            temp_c = self._kelvin_to_celsius(value)
        else:
            temp_c = value
        
        # Convert from Celsius to target unit
        if to_unit == 'celsius':
            return float(temp_c)
        elif to_unit == 'fahrenheit':
            return float(self._celsius_to_fahrenheit(temp_c))
        elif to_unit == 'kelvin':
            return float(self._celsius_to_kelvin(temp_c))
        else:
            return float(temp_c)
    
    def _calculate_dew_point(self, temperature_c, relative_humidity):
        """
        Calculate dew point using Magnus formula
        
        Td = (B * α) / (A - α)
        where α = (A * T) / (B + T) + ln(RH/100)
        """
        try:
            # Ensure RH is between 0 and 100
            rh = np.clip(relative_humidity, 0.01, 100.0)
            
            # Calculate alpha using numpy
            alpha = np.divide(
                np.multiply(self.A, temperature_c),
                np.add(self.B, temperature_c)
            ) + np.log(np.divide(rh, 100.0))
            
            # Check for division by zero
            denominator = np.subtract(self.A, alpha)
            if abs(float(denominator)) < 1e-10:
                raise ValueError("Invalid calculation: denominator too close to zero")
            
            # Calculate dew point
            dew_point = np.divide(
                np.multiply(self.B, alpha),
                denominator
            )
            
            result = float(dew_point)
            if math.isinf(result) or math.isnan(result):
                raise ValueError("Invalid dew point calculation result")
            
            return result
        except Exception as e:
            raise ValueError(f"Error calculating dew point: {str(e)}")
    
    def _calculate_relative_humidity(self, temperature_c, dew_point_c):
        """
        Calculate relative humidity from temperature and dew point
        
        RH = 100 * exp((A * Td) / (B + Td) - (A * T) / (B + T))
        """
        try:
            # Calculate relative humidity using Magnus formula
            numerator = np.subtract(
                np.divide(np.multiply(self.A, dew_point_c), np.add(self.B, dew_point_c)),
                np.divide(np.multiply(self.A, temperature_c), np.add(self.B, temperature_c))
            )
            rh = np.multiply(100.0, np.exp(numerator))
            
            # Clip to valid range
            rh = np.clip(rh, 0.0, 100.0)
            
            result = float(rh)
            if math.isinf(result) or math.isnan(result):
                raise ValueError("Invalid relative humidity calculation result")
            
            return result
        except Exception as e:
            raise ValueError(f"Error calculating relative humidity: {str(e)}")
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Dew Point Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'dew_point')
            
            if calc_type == 'dew_point':
                return self._calculate_dew_point_mode(data)
            elif calc_type == 'relative_humidity':
                return self._calculate_relative_humidity_mode(data)
            elif calc_type == 'temperature':
                return self._calculate_temperature_mode(data)
            elif calc_type == 'convert':
                return self._convert_units(data)
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
    
    def _calculate_dew_point_mode(self, data):
        """Calculate dew point from temperature and relative humidity"""
        try:
            # Check for required fields
            if 'temperature' not in data or data.get('temperature') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is required.')
                }, status=400)
            
            if 'relative_humidity' not in data or data.get('relative_humidity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity is required.')
                }, status=400)
            
            try:
                temperature = float(data.get('temperature', 0))
                relative_humidity = float(data.get('relative_humidity', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            temp_unit = data.get('temp_unit', 'celsius')
            result_unit = data.get('result_unit', 'celsius')
            
            # Validate units
            valid_units = ['celsius', 'fahrenheit', 'kelvin']
            if temp_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid temperature unit.')
                }, status=400)
            
            if result_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate relative humidity range
            if relative_humidity < 0 or relative_humidity > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity must be between 0 and 100%.')
                }, status=400)
            
            # Validate temperature range based on unit
            if temp_unit == 'celsius':
                if temperature < -100 or temperature > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Temperature must be between -100°C and 100°C.')
                    }, status=400)
            elif temp_unit == 'fahrenheit':
                if temperature < -148 or temperature > 212:
                    return JsonResponse({
                        'success': False,
                        'error': _('Temperature must be between -148°F and 212°F.')
                    }, status=400)
            elif temp_unit == 'kelvin':
                if temperature < 173.15 or temperature > 373.15:
                    return JsonResponse({
                        'success': False,
                        'error': _('Temperature must be between 173.15K and 373.15K.')
                    }, status=400)
            
            # Convert temperature to Celsius
            if temp_unit == 'celsius':
                temp_c = temperature
            elif temp_unit == 'fahrenheit':
                temp_c = self._fahrenheit_to_celsius(temperature)
            elif temp_unit == 'kelvin':
                temp_c = self._kelvin_to_celsius(temperature)
            else:
                temp_c = temperature
            
            # Calculate dew point in Celsius
            dew_point_c = self._calculate_dew_point(temp_c, relative_humidity)
            
            # Convert to result unit
            dew_point_result = self._convert_temperature(dew_point_c, 'celsius', result_unit)
            
            # Validate result
            if math.isinf(dew_point_result) or math.isnan(dew_point_result) or np.isinf(dew_point_result) or np.isnan(dew_point_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'dew_point',
                'temperature': temperature,
                'temp_unit': temp_unit,
                'relative_humidity': relative_humidity,
                'dew_point': dew_point_result,
                'dew_point_unit': result_unit,
                'dew_point_c': dew_point_c,
                'temp_c': temp_c,
                'step_by_step': self._prepare_dew_point_steps(temperature, temp_unit, relative_humidity, dew_point_result, result_unit, temp_c, dew_point_c),
                'chart_data': self._prepare_dew_point_chart_data(temp_c, relative_humidity, dew_point_c),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating dew point: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_relative_humidity_mode(self, data):
        """Calculate relative humidity from temperature and dew point"""
        try:
            # Check for required fields
            if 'temperature' not in data or data.get('temperature') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is required.')
                }, status=400)
            
            if 'dew_point' not in data or data.get('dew_point') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Dew point is required.')
                }, status=400)
            
            try:
                temperature = float(data.get('temperature', 0))
                dew_point = float(data.get('dew_point', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            temp_unit = data.get('temp_unit', 'celsius')
            dew_point_unit = data.get('dew_point_unit', 'celsius')
            
            # Validate units
            valid_units = ['celsius', 'fahrenheit', 'kelvin']
            if temp_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid temperature unit.')
                }, status=400)
            
            if dew_point_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid dew point unit.')
                }, status=400)
            
            # Validate temperature range
            if temp_unit == 'celsius':
                if temperature < -100 or temperature > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Temperature must be between -100°C and 100°C.')
                    }, status=400)
            elif temp_unit == 'fahrenheit':
                if temperature < -148 or temperature > 212:
                    return JsonResponse({
                        'success': False,
                        'error': _('Temperature must be between -148°F and 212°F.')
                    }, status=400)
            elif temp_unit == 'kelvin':
                if temperature < 173.15 or temperature > 373.15:
                    return JsonResponse({
                        'success': False,
                        'error': _('Temperature must be between 173.15K and 373.15K.')
                    }, status=400)
            
            # Validate dew point range
            if dew_point_unit == 'celsius':
                if dew_point < -100 or dew_point > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dew point must be between -100°C and 100°C.')
                    }, status=400)
            elif dew_point_unit == 'fahrenheit':
                if dew_point < -148 or dew_point > 212:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dew point must be between -148°F and 212°F.')
                    }, status=400)
            elif dew_point_unit == 'kelvin':
                if dew_point < 173.15 or dew_point > 373.15:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dew point must be between 173.15K and 373.15K.')
                    }, status=400)
            
            # Convert to Celsius first for comparison
            if temp_unit == 'celsius':
                temp_c = temperature
            elif temp_unit == 'fahrenheit':
                temp_c = self._fahrenheit_to_celsius(temperature)
            elif temp_unit == 'kelvin':
                temp_c = self._kelvin_to_celsius(temperature)
            else:
                temp_c = temperature
            
            if dew_point_unit == 'celsius':
                dew_point_c = dew_point
            elif dew_point_unit == 'fahrenheit':
                dew_point_c = self._fahrenheit_to_celsius(dew_point)
            elif dew_point_unit == 'kelvin':
                dew_point_c = self._kelvin_to_celsius(dew_point)
            else:
                dew_point_c = dew_point
            
            # Check if dew point is greater than temperature (after converting to same unit)
            if dew_point_c > temp_c:
                return JsonResponse({
                    'success': False,
                    'error': _('Dew point cannot be greater than temperature.')
                }, status=400)
            
            # Calculate relative humidity
            relative_humidity = self._calculate_relative_humidity(temp_c, dew_point_c)
            
            # Validate result
            if math.isinf(relative_humidity) or math.isnan(relative_humidity) or np.isinf(relative_humidity) or np.isnan(relative_humidity):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'relative_humidity',
                'temperature': temperature,
                'temp_unit': temp_unit,
                'dew_point': dew_point,
                'dew_point_unit': dew_point_unit,
                'relative_humidity': relative_humidity,
                'temp_c': temp_c,
                'dew_point_c': dew_point_c,
                'step_by_step': self._prepare_rh_steps(temperature, temp_unit, dew_point, dew_point_unit, relative_humidity, temp_c, dew_point_c),
                'chart_data': self._prepare_rh_chart_data(temp_c, dew_point_c, relative_humidity),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _calculate_temperature_mode(self, data):
        """Calculate temperature from dew point and relative humidity"""
        try:
            # Check for required fields
            if 'dew_point' not in data or data.get('dew_point') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Dew point is required.')
                }, status=400)
            
            if 'relative_humidity' not in data or data.get('relative_humidity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity is required.')
                }, status=400)
            
            try:
                dew_point = float(data.get('dew_point', 0))
                relative_humidity = float(data.get('relative_humidity', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            dew_point_unit = data.get('dew_point_unit', 'celsius')
            result_unit = data.get('result_unit', 'celsius')
            
            # Validate units
            valid_units = ['celsius', 'fahrenheit', 'kelvin']
            if dew_point_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid dew point unit.')
                }, status=400)
            
            if result_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate relative humidity range
            if relative_humidity < 0 or relative_humidity > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity must be between 0 and 100%.')
                }, status=400)
            
            # Validate dew point range
            if dew_point_unit == 'celsius':
                if dew_point < -100 or dew_point > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dew point must be between -100°C and 100°C.')
                    }, status=400)
            elif dew_point_unit == 'fahrenheit':
                if dew_point < -148 or dew_point > 212:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dew point must be between -148°F and 212°F.')
                    }, status=400)
            elif dew_point_unit == 'kelvin':
                if dew_point < 173.15 or dew_point > 373.15:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dew point must be between 173.15K and 373.15K.')
                    }, status=400)
            
            # Convert dew point to Celsius
            if dew_point_unit == 'celsius':
                dew_point_c = dew_point
            elif dew_point_unit == 'fahrenheit':
                dew_point_c = self._fahrenheit_to_celsius(dew_point)
            elif dew_point_unit == 'kelvin':
                dew_point_c = self._kelvin_to_celsius(dew_point)
            else:
                dew_point_c = dew_point
            
            # Solve for temperature using iterative method
            # We need to find T such that: RH = 100 * exp((A*Td)/(B+Td) - (A*T)/(B+T))
            # Rearranging: (A*T)/(B+T) = (A*Td)/(B+Td) - ln(RH/100)
            
            target_alpha = np.divide(
                np.multiply(self.A, dew_point_c),
                np.add(self.B, dew_point_c)
            ) - np.log(np.divide(relative_humidity, 100.0))
            
            # Solve for T: (A*T)/(B+T) = target_alpha
            # T = (B * target_alpha) / (A - target_alpha)
            denominator = np.subtract(self.A, target_alpha)
            if abs(float(denominator)) < 1e-10:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation: cannot solve for temperature with given inputs.')
                }, status=400)
            
            temp_c = np.divide(
                np.multiply(self.B, target_alpha),
                denominator
            )
            
            temp_c = float(temp_c)
            
            if math.isinf(temp_c) or math.isnan(temp_c):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Convert to result unit
            temperature_result = self._convert_temperature(temp_c, 'celsius', result_unit)
            
            # Validate result
            if math.isinf(temperature_result) or math.isnan(temperature_result) or np.isinf(temperature_result) or np.isnan(temperature_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'temperature',
                'dew_point': dew_point,
                'dew_point_unit': dew_point_unit,
                'relative_humidity': relative_humidity,
                'temperature': temperature_result,
                'temp_unit': result_unit,
                'temp_c': temp_c,
                'dew_point_c': dew_point_c,
                'step_by_step': self._prepare_temperature_steps(dew_point, dew_point_unit, relative_humidity, temperature_result, result_unit, dew_point_c, temp_c),
                'chart_data': self._prepare_temperature_chart_data(temp_c, dew_point_c, relative_humidity),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _convert_units(self, data):
        """Convert temperature units"""
        try:
            # Check for required fields
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'celsius')
            to_unit = data.get('to_unit', 'celsius')
            
            # Validate units
            valid_units = ['celsius', 'fahrenheit', 'kelvin']
            if from_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid source unit.')
                }, status=400)
            
            if to_unit not in valid_units:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid target unit.')
                }, status=400)
            
            # Validate absolute zero constraint
            if from_unit == 'celsius' and value < -273.15:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature cannot be below absolute zero (-273.15°C).')
                }, status=400)
            elif from_unit == 'fahrenheit' and value < -459.67:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature cannot be below absolute zero (-459.67°F).')
                }, status=400)
            elif from_unit == 'kelvin' and value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature cannot be below absolute zero (0K).')
                }, status=400)
            
            # Validate reasonable upper bounds
            if from_unit == 'celsius' and value > 1000:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is too high. Please enter a value below 1000°C.')
                }, status=400)
            elif from_unit == 'fahrenheit' and value > 1832:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is too high. Please enter a value below 1832°F.')
                }, status=400)
            elif from_unit == 'kelvin' and value > 1273.15:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is too high. Please enter a value below 1273.15K.')
                }, status=400)
            
            # Convert temperature
            result = self._convert_temperature(value, from_unit, to_unit)
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'convert',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': result,
                'step_by_step': self._prepare_convert_steps(value, from_unit, to_unit, result),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _prepare_dew_point_steps(self, temperature, temp_unit, relative_humidity, dew_point, dew_point_unit, temp_c, dew_point_c):
        """Prepare step-by-step for dew point calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Temperature: {temp} {unit}').format(temp=temperature, unit=temp_unit.title()))
        steps.append(_('Relative Humidity: {rh}%').format(rh=relative_humidity))
        steps.append('')
        steps.append(_('Step 2: Convert temperature to Celsius'))
        steps.append(_('Temperature in Celsius: {temp}°C').format(temp=temp_c))
        steps.append('')
        steps.append(_('Step 3: Apply the Magnus formula'))
        try:
            T, Td, RH = symbols('T T_d RH')
            # Simplified formula representation
            steps.append(_('Formula: Td = (B × α) / (A - α)'))
            steps.append(_('Where: α = (A × T) / (B + T) + ln(RH/100)'))
            steps.append(_('A = 17.27, B = 237.7°C'))
        except:
            steps.append(_('Formula: Td = (B × α) / (A - α)'))
        steps.append(_('α = ({a} × {temp}) / ({b} + {temp}) + ln({rh}/100)').format(
            a=self.A, temp=temp_c, b=self.B, rh=relative_humidity
        ))
        alpha = (self.A * temp_c) / (self.B + temp_c) + math.log(relative_humidity / 100.0)
        steps.append(_('α = {alpha}').format(alpha=alpha))
        steps.append(_('Dew Point = ({b} × {alpha}) / ({a} - {alpha})').format(
            b=self.B, alpha=alpha, a=self.A
        ))
        steps.append(_('Dew Point = {dp}°C').format(dp=dew_point_c))
        steps.append('')
        steps.append(_('Step 4: Convert to desired unit'))
        steps.append(_('Dew Point = {dp} {unit}').format(dp=dew_point, unit=dew_point_unit.title()))
        return steps
    
    def _prepare_rh_steps(self, temperature, temp_unit, dew_point, dew_point_unit, relative_humidity, temp_c, dew_point_c):
        """Prepare step-by-step for relative humidity calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Temperature: {temp} {unit}').format(temp=temperature, unit=temp_unit.title()))
        steps.append(_('Dew Point: {dp} {unit}').format(dp=dew_point, unit=dew_point_unit.title()))
        steps.append('')
        steps.append(_('Step 2: Convert to Celsius'))
        steps.append(_('Temperature in Celsius: {temp}°C').format(temp=temp_c))
        steps.append(_('Dew Point in Celsius: {dp}°C').format(dp=dew_point_c))
        steps.append('')
        steps.append(_('Step 3: Apply the Magnus formula'))
        try:
            T, Td, RH = symbols('T T_d RH')
            steps.append(_('Formula: RH = 100 × exp((A×Td)/(B+Td) - (A×T)/(B+T))'))
            steps.append(_('A = 17.27, B = 237.7°C'))
        except:
            steps.append(_('Formula: RH = 100 × exp((A×Td)/(B+Td) - (A×T)/(B+T))'))
        term1 = (self.A * dew_point_c) / (self.B + dew_point_c)
        term2 = (self.A * temp_c) / (self.B + temp_c)
        steps.append(_('Term 1: (A×Td)/(B+Td) = ({a}×{td})/({b}+{td}) = {term1}').format(
            a=self.A, td=dew_point_c, b=self.B, term1=term1
        ))
        steps.append(_('Term 2: (A×T)/(B+T) = ({a}×{t})/({b}+{t}) = {term2}').format(
            a=self.A, t=temp_c, b=self.B, term2=term2
        ))
        diff = term1 - term2
        steps.append(_('Difference: {term1} - {term2} = {diff}').format(term1=term1, term2=term2, diff=diff))
        steps.append(_('RH = 100 × exp({diff}) = {rh}%').format(diff=diff, rh=relative_humidity))
        return steps
    
    def _prepare_temperature_steps(self, dew_point, dew_point_unit, relative_humidity, temperature, temp_unit, dew_point_c, temp_c):
        """Prepare step-by-step for temperature calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Dew Point: {dp} {unit}').format(dp=dew_point, unit=dew_point_unit.title()))
        steps.append(_('Relative Humidity: {rh}%').format(rh=relative_humidity))
        steps.append('')
        steps.append(_('Step 2: Convert dew point to Celsius'))
        steps.append(_('Dew Point in Celsius: {dp}°C').format(dp=dew_point_c))
        steps.append('')
        steps.append(_('Step 3: Apply the Magnus formula (rearranged)'))
        try:
            T, Td, RH = symbols('T T_d RH')
            steps.append(_('Formula: T = (B × α) / (A - α)'))
            steps.append(_('Where: α = (A×Td)/(B+Td) - ln(RH/100)'))
        except:
            steps.append(_('Formula: T = (B × α) / (A - α)'))
        target_alpha = (self.A * dew_point_c) / (self.B + dew_point_c) - math.log(relative_humidity / 100.0)
        steps.append(_('α = ({a}×{td})/({b}+{td}) - ln({rh}/100)').format(
            a=self.A, td=dew_point_c, b=self.B, rh=relative_humidity
        ))
        steps.append(_('α = {alpha}').format(alpha=target_alpha))
        steps.append(_('Temperature = ({b} × {alpha}) / ({a} - {alpha})').format(
            b=self.B, alpha=target_alpha, a=self.A
        ))
        steps.append(_('Temperature = {temp}°C').format(temp=temp_c))
        steps.append('')
        steps.append(_('Step 4: Convert to desired unit'))
        steps.append(_('Temperature = {temp} {unit}').format(temp=temperature, unit=temp_unit.title()))
        return steps
    
    def _prepare_convert_steps(self, value, from_unit, to_unit, result):
        """Prepare step-by-step for unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Temperature: {value} {unit}').format(value=value, unit=from_unit.title()))
        steps.append('')
        
        if from_unit != 'celsius':
            steps.append(_('Step 2: Convert to Celsius'))
            if from_unit == 'fahrenheit':
                steps.append(_('Celsius = (Fahrenheit - 32) × 5/9'))
                steps.append(_('Celsius = ({val} - 32) × 5/9 = {celsius}°C').format(
                    val=value, celsius=self._fahrenheit_to_celsius(value)
                ))
            elif from_unit == 'kelvin':
                steps.append(_('Celsius = Kelvin - 273.15'))
                steps.append(_('Celsius = {val} - 273.15 = {celsius}°C').format(
                    val=value, celsius=self._kelvin_to_celsius(value)
                ))
            steps.append('')
        
        if to_unit != 'celsius':
            temp_c = self._convert_temperature(value, from_unit, 'celsius')
            steps.append(_('Step 3: Convert from Celsius to {unit}').format(unit=to_unit.title()))
            if to_unit == 'fahrenheit':
                steps.append(_('Fahrenheit = Celsius × 9/5 + 32'))
                steps.append(_('Fahrenheit = {celsius} × 9/5 + 32 = {result}°F').format(
                    celsius=temp_c, result=result
                ))
            elif to_unit == 'kelvin':
                steps.append(_('Kelvin = Celsius + 273.15'))
                steps.append(_('Kelvin = {celsius} + 273.15 = {result}K').format(
                    celsius=temp_c, result=result
                ))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Temperature = {result}°C').format(result=result))
        
        steps.append('')
        steps.append(_('Final Result: {result} {unit}').format(result=result, unit=to_unit.title()))
        return steps
    
    def _prepare_dew_point_chart_data(self, temp_c, relative_humidity, dew_point_c):
        """Prepare chart data for dew point calculation"""
        # Create a line chart showing temperature vs dew point relationship
        temps = np.linspace(max(-20, temp_c - 10), min(50, temp_c + 10), 20)
        dew_points = []
        valid_temps = []
        valid_labels = []
        
        for t in temps:
            try:
                dp = self._calculate_dew_point(float(t), relative_humidity)
                if not (math.isinf(dp) or math.isnan(dp)):
                    dew_points.append(dp)
                    valid_temps.append(float(t))
                    valid_labels.append(f'{t:.1f}°C')
            except:
                pass
        
        # Ensure we have data points
        if len(dew_points) < 2:
            valid_temps = [float(t) for t in np.linspace(max(-20, dew_point_c - 5), min(50, dew_point_c + 5), 10)]
            valid_labels = [f'{t:.1f}°C' for t in valid_temps]
            dew_points = []
            for t in valid_temps:
                try:
                    dew_points.append(self._calculate_dew_point(t, relative_humidity))
                except:
                    dew_points.append(dew_point_c)
        
        chart_config = {
            'type': 'line',
            'data': {
                'labels': valid_labels if valid_labels else [f'{t:.1f}°C' for t in temps],
                'datasets': [{
                    'label': _('Dew Point (°C)'),
                    'data': dew_points if dew_points else [dew_point_c],
                    'borderColor': 'rgba(59, 130, 246, 1)',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4
                }, {
                    'label': _('Temperature (°C)'),
                    'data': valid_temps if valid_temps else temps.tolist(),
                    'borderColor': 'rgba(239, 68, 68, 1)',
                    'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                    'borderWidth': 2,
                    'borderDash': [5, 5],
                    'fill': False
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
                        'text': _('Temperature vs Dew Point (RH = {rh}%)').format(rh=relative_humidity)
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': False,
                        'title': {
                            'display': True,
                            'text': _('Temperature (°C)')
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': _('Temperature (°C)')
                        }
                    }
                }
            }
        }
        
        return {'dew_point_chart': chart_config}
    
    def _prepare_rh_chart_data(self, temp_c, dew_point_c, relative_humidity):
        """Prepare chart data for relative humidity calculation"""
        # Create a bar chart showing the relationship
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [_('Temperature'), _('Dew Point'), _('Difference')],
                'datasets': [{
                    'label': _('Temperature (°C)'),
                    'data': [temp_c, dew_point_c, temp_c - dew_point_c],
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
                        'text': _('Temperature Analysis (RH = {rh}%)').format(rh=relative_humidity)
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': _('Temperature (°C)')
                        }
                    }
                }
            }
        }
        
        return {'rh_chart': chart_config}
    
    def _prepare_temperature_chart_data(self, temp_c, dew_point_c, relative_humidity):
        """Prepare chart data for temperature calculation"""
        # Create a doughnut chart
        chart_config = {
            'type': 'doughnut',
            'data': {
                'labels': [_('Temperature'), _('Dew Point'), _('RH')],
                'datasets': [{
                    'data': [temp_c, dew_point_c, relative_humidity],
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
                        'display': True,
                        'position': 'bottom'
                    },
                    'title': {
                        'display': True,
                        'text': _('Temperature Calculation Breakdown')
                    }
                }
            }
        }
        
        return {'temperature_chart': chart_config}
