from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, Eq, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HeatIndexCalculator(View):
    """
    Professional Heat Index Calculator with Comprehensive Features
    
    This calculator provides heat index calculations with:
    - Calculate heat index from temperature and relative humidity
    - Calculate temperature from heat index and relative humidity
    - Calculate relative humidity from heat index and temperature
    - Unit conversions (Fahrenheit/Celsius)
    - Heat index categories and risk levels
    
    Features:
    - Supports multiple calculation modes
    - Handles temperature unit conversions
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/heat_index_calculator.html'
    
    # Heat index risk categories
    HEAT_INDEX_CATEGORIES = {
        'caution': (80, 90, _('Caution')),
        'extreme_caution': (90, 103, _('Extreme Caution')),
        'danger': (103, 124, _('Danger')),
        'extreme_danger': (124, float('inf'), _('Extreme Danger')),
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Heat Index Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'heat_index')
            
            if calc_type == 'heat_index':
                return self._calculate_heat_index(data)
            elif calc_type == 'temperature':
                return self._calculate_temperature(data)
            elif calc_type == 'humidity':
                return self._calculate_humidity(data)
            elif calc_type == 'convert_temperature':
                return self._convert_temperature(data)
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
    
    def _calculate_heat_index(self, data):
        """Calculate heat index from temperature and relative humidity"""
        try:
            if 'temperature' not in data or data.get('temperature') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is required.')
                }, status=400)
            
            if 'humidity' not in data or data.get('humidity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity is required.')
                }, status=400)
            
            try:
                temperature = float(data.get('temperature', 0))
                humidity = float(data.get('humidity', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            temp_unit = data.get('temp_unit', 'fahrenheit')
            
            # Validate units
            if temp_unit not in ['fahrenheit', 'celsius']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid temperature unit.')
                }, status=400)
            
            # Convert to Fahrenheit if needed (heat index formula requires Fahrenheit)
            if temp_unit == 'celsius':
                temp_f = float(np.add(np.multiply(temperature, 9.0/5.0), 32.0))
            else:
                temp_f = temperature
            
            # Validate ranges
            if temp_f < 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Heat index is only valid for temperatures above 80°F (27°C).')
                }, status=400)
            
            if humidity < 0 or humidity > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity must be between 0 and 100%.')
                }, status=400)
            
            if humidity < 40:
                return JsonResponse({
                    'success': False,
                    'error': _('Heat index is only valid for relative humidity above 40%.')
                }, status=400)
            
            # Calculate heat index using Rothfusz equation
            # HI = -42.379 + 2.04901523*T + 10.14333127*RH - 0.22475541*T*RH - 6.83783e-3*T^2 - 5.481717e-2*RH^2 + 1.22874e-3*T^2*RH + 8.5282e-4*T*RH^2 - 1.99e-6*T^2*RH^2
            
            T = temp_f
            RH = humidity
            
            # Calculate heat index
            hi = float(np.add(
                -42.379,
                np.add(
                    np.multiply(2.04901523, T),
                    np.add(
                        np.multiply(10.14333127, RH),
                        np.add(
                            np.multiply(-0.22475541, np.multiply(T, RH)),
                            np.add(
                                np.multiply(-6.83783e-3, np.power(T, 2)),
                                np.add(
                                    np.multiply(-5.481717e-2, np.power(RH, 2)),
                                    np.add(
                                        np.multiply(1.22874e-3, np.multiply(np.power(T, 2), RH)),
                                        np.add(
                                            np.multiply(8.5282e-4, np.multiply(T, np.power(RH, 2))),
                                            np.multiply(-1.99e-6, np.multiply(np.power(T, 2), np.power(RH, 2)))
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
            ))
            
            # Apply adjustments
            if RH < 13 and T >= 80 and T <= 112:
                adjustment = float(np.multiply(0.25, np.subtract(13.0, RH)))
                adjustment = float(np.multiply(adjustment, np.sqrt(np.subtract(17.0, np.abs(np.subtract(T, 95.0))))))
                hi = float(np.subtract(hi, adjustment))
            
            if RH > 85 and T >= 80 and T <= 87:
                adjustment = float(np.multiply(0.5, np.subtract(RH, 85.0)))
                adjustment = float(np.multiply(adjustment, np.subtract(87.0, T)))
                hi = float(np.add(hi, adjustment))
            
            # Validate result
            if math.isinf(hi) or math.isnan(hi) or np.isinf(hi) or np.isnan(hi):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Get category
            category = self._get_heat_index_category(hi)
            
            # Convert to Celsius if needed
            if temp_unit == 'celsius':
                hi_celsius = float(np.multiply(np.subtract(hi, 32.0), 5.0/9.0))
            else:
                hi_celsius = None
            
            steps = self._prepare_heat_index_steps(temperature, temp_unit, humidity, temp_f, hi, category)
            
            chart_data = self._prepare_heat_index_chart_data(temp_f, humidity, hi)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'heat_index',
                'temperature': temperature,
                'temp_unit': temp_unit,
                'humidity': humidity,
                'heat_index_f': round(hi, 1),
                'heat_index_c': round(hi_celsius, 1) if hi_celsius else None,
                'category': category['name'],
                'risk_level': category['risk'],
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating heat index: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_temperature(self, data):
        """Calculate temperature from heat index and relative humidity"""
        try:
            if 'heat_index' not in data or data.get('heat_index') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Heat index is required.')
                }, status=400)
            
            if 'humidity' not in data or data.get('humidity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity is required.')
                }, status=400)
            
            try:
                heat_index = float(data.get('heat_index', 0))
                humidity = float(data.get('humidity', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            temp_unit = data.get('temp_unit', 'fahrenheit')
            
            # Validate units
            if temp_unit not in ['fahrenheit', 'celsius']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid temperature unit.')
                }, status=400)
            
            # Convert heat index to Fahrenheit if needed
            if temp_unit == 'celsius':
                hi_f = float(np.add(np.multiply(heat_index, 9.0/5.0), 32.0))
            else:
                hi_f = heat_index
            
            # Validate ranges
            if hi_f < 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Heat index must be at least 80°F (27°C).')
                }, status=400)
            
            if humidity < 0 or humidity > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity must be between 0 and 100%.')
                }, status=400)
            
            if humidity < 40:
                return JsonResponse({
                    'success': False,
                    'error': _('Relative humidity must be at least 40% for heat index calculations.')
                }, status=400)
            
            # Solve for temperature using iterative method
            # We need to reverse the heat index formula
            # This is complex, so we'll use a numerical approach
            
            # Initial guess
            T_guess = 80.0
            max_iterations = 100
            tolerance = 0.01
            
            for i in range(max_iterations):
                # Calculate heat index with current temperature guess
                T = T_guess
                RH = humidity
                
                hi_calc = float(np.add(
                    -42.379,
                    np.add(
                        np.multiply(2.04901523, T),
                        np.add(
                            np.multiply(10.14333127, RH),
                            np.add(
                                np.multiply(-0.22475541, np.multiply(T, RH)),
                                np.add(
                                    np.multiply(-6.83783e-3, np.power(T, 2)),
                                    np.add(
                                        np.multiply(-5.481717e-2, np.power(RH, 2)),
                                        np.add(
                                            np.multiply(1.22874e-3, np.multiply(np.power(T, 2), RH)),
                                            np.add(
                                                np.multiply(8.5282e-4, np.multiply(T, np.power(RH, 2))),
                                                np.multiply(-1.99e-6, np.multiply(np.power(T, 2), np.power(RH, 2)))
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ))
                
                # Apply adjustments
                if RH < 13 and T >= 80 and T <= 112:
                    adjustment = float(np.multiply(0.25, np.subtract(13.0, RH)))
                    adjustment = float(np.multiply(adjustment, np.sqrt(np.subtract(17.0, np.abs(np.subtract(T, 95.0))))))
                    hi_calc = float(np.subtract(hi_calc, adjustment))
                
                if RH > 85 and T >= 80 and T <= 87:
                    adjustment = float(np.multiply(0.5, np.subtract(RH, 85.0)))
                    adjustment = float(np.multiply(adjustment, np.subtract(87.0, T)))
                    hi_calc = float(np.add(hi_calc, adjustment))
                
                # Check if we're close enough
                error = abs(hi_calc - hi_f)
                if error < tolerance:
                    break
                
                # Update guess using Newton's method approximation
                # Derivative approximation
                delta_T = 0.1
                T_plus = T + delta_T
                
                hi_plus = float(np.add(
                    -42.379,
                    np.add(
                        np.multiply(2.04901523, T_plus),
                        np.add(
                            np.multiply(10.14333127, RH),
                            np.add(
                                np.multiply(-0.22475541, np.multiply(T_plus, RH)),
                                np.add(
                                    np.multiply(-6.83783e-3, np.power(T_plus, 2)),
                                    np.add(
                                        np.multiply(-5.481717e-2, np.power(RH, 2)),
                                        np.add(
                                            np.multiply(1.22874e-3, np.multiply(np.power(T_plus, 2), RH)),
                                            np.add(
                                                np.multiply(8.5282e-4, np.multiply(T_plus, np.power(RH, 2))),
                                                np.multiply(-1.99e-6, np.multiply(np.power(T_plus, 2), np.power(RH, 2)))
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ))
                
                # Apply adjustments for T_plus
                if RH < 13 and T_plus >= 80 and T_plus <= 112:
                    adjustment = float(np.multiply(0.25, np.subtract(13.0, RH)))
                    adjustment = float(np.multiply(adjustment, np.sqrt(np.subtract(17.0, np.abs(np.subtract(T_plus, 95.0))))))
                    hi_plus = float(np.subtract(hi_plus, adjustment))
                
                if RH > 85 and T_plus >= 80 and T_plus <= 87:
                    adjustment = float(np.multiply(0.5, np.subtract(RH, 85.0)))
                    adjustment = float(np.multiply(adjustment, np.subtract(87.0, T_plus)))
                    hi_plus = float(np.add(hi_plus, adjustment))
                
                derivative = (hi_plus - hi_calc) / delta_T
                
                if abs(derivative) < 1e-10:
                    break
                
                T_guess = T_guess - (hi_calc - hi_f) / derivative
                
                # Keep within reasonable bounds
                if T_guess < 80:
                    T_guess = 80
                if T_guess > 150:
                    T_guess = 150
            
            temp_f = T_guess
            
            # Validate result
            if math.isinf(temp_f) or math.isnan(temp_f) or np.isinf(temp_f) or np.isnan(temp_f):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Convert to Celsius if needed
            if temp_unit == 'celsius':
                temp_c = float(np.multiply(np.subtract(temp_f, 32.0), 5.0/9.0))
            else:
                temp_c = None
            
            steps = self._prepare_temperature_steps(heat_index, temp_unit, humidity, hi_f, temp_f, temp_c)
            
            chart_data = self._prepare_temperature_chart_data(temp_f, humidity, hi_f)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'temperature',
                'heat_index': heat_index,
                'temp_unit': temp_unit,
                'humidity': humidity,
                'temperature_f': round(temp_f, 1),
                'temperature_c': round(temp_c, 1) if temp_c else None,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating temperature: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_humidity(self, data):
        """Calculate relative humidity from heat index and temperature"""
        try:
            if 'heat_index' not in data or data.get('heat_index') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Heat index is required.')
                }, status=400)
            
            if 'temperature' not in data or data.get('temperature') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature is required.')
                }, status=400)
            
            try:
                heat_index = float(data.get('heat_index', 0))
                temperature = float(data.get('temperature', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            temp_unit = data.get('temp_unit', 'fahrenheit')
            
            # Validate units
            if temp_unit not in ['fahrenheit', 'celsius']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid temperature unit.')
                }, status=400)
            
            # Convert to Fahrenheit if needed
            if temp_unit == 'celsius':
                temp_f = float(np.add(np.multiply(temperature, 9.0/5.0), 32.0))
                hi_f = float(np.add(np.multiply(heat_index, 9.0/5.0), 32.0))
            else:
                temp_f = temperature
                hi_f = heat_index
            
            # Validate ranges
            if temp_f < 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Temperature must be at least 80°F (27°C) for heat index calculations.')
                }, status=400)
            
            if hi_f < 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Heat index must be at least 80°F (27°C).')
                }, status=400)
            
            # Solve for humidity using iterative method
            RH_guess = 40.0
            max_iterations = 100
            tolerance = 0.01
            
            for i in range(max_iterations):
                # Calculate heat index with current humidity guess
                T = temp_f
                RH = RH_guess
                
                hi_calc = float(np.add(
                    -42.379,
                    np.add(
                        np.multiply(2.04901523, T),
                        np.add(
                            np.multiply(10.14333127, RH),
                            np.add(
                                np.multiply(-0.22475541, np.multiply(T, RH)),
                                np.add(
                                    np.multiply(-6.83783e-3, np.power(T, 2)),
                                    np.add(
                                        np.multiply(-5.481717e-2, np.power(RH, 2)),
                                        np.add(
                                            np.multiply(1.22874e-3, np.multiply(np.power(T, 2), RH)),
                                            np.add(
                                                np.multiply(8.5282e-4, np.multiply(T, np.power(RH, 2))),
                                                np.multiply(-1.99e-6, np.multiply(np.power(T, 2), np.power(RH, 2)))
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ))
                
                # Apply adjustments
                if RH < 13 and T >= 80 and T <= 112:
                    adjustment = float(np.multiply(0.25, np.subtract(13.0, RH)))
                    adjustment = float(np.multiply(adjustment, np.sqrt(np.subtract(17.0, np.abs(np.subtract(T, 95.0))))))
                    hi_calc = float(np.subtract(hi_calc, adjustment))
                
                if RH > 85 and T >= 80 and T <= 87:
                    adjustment = float(np.multiply(0.5, np.subtract(RH, 85.0)))
                    adjustment = float(np.multiply(adjustment, np.subtract(87.0, T)))
                    hi_calc = float(np.add(hi_calc, adjustment))
                
                # Check if we're close enough
                error = abs(hi_calc - hi_f)
                if error < tolerance:
                    break
                
                # Update guess using Newton's method approximation
                delta_RH = 0.1
                RH_plus = RH + delta_RH
                
                hi_plus = float(np.add(
                    -42.379,
                    np.add(
                        np.multiply(2.04901523, T),
                        np.add(
                            np.multiply(10.14333127, RH_plus),
                            np.add(
                                np.multiply(-0.22475541, np.multiply(T, RH_plus)),
                                np.add(
                                    np.multiply(-6.83783e-3, np.power(T, 2)),
                                    np.add(
                                        np.multiply(-5.481717e-2, np.power(RH_plus, 2)),
                                        np.add(
                                            np.multiply(1.22874e-3, np.multiply(np.power(T, 2), RH_plus)),
                                            np.add(
                                                np.multiply(8.5282e-4, np.multiply(T, np.power(RH_plus, 2))),
                                                np.multiply(-1.99e-6, np.multiply(np.power(T, 2), np.power(RH_plus, 2)))
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                ))
                
                # Apply adjustments for RH_plus
                if RH_plus < 13 and T >= 80 and T <= 112:
                    adjustment = float(np.multiply(0.25, np.subtract(13.0, RH_plus)))
                    adjustment = float(np.multiply(adjustment, np.sqrt(np.subtract(17.0, np.abs(np.subtract(T, 95.0))))))
                    hi_plus = float(np.subtract(hi_plus, adjustment))
                
                if RH_plus > 85 and T >= 80 and T <= 87:
                    adjustment = float(np.multiply(0.5, np.subtract(RH_plus, 85.0)))
                    adjustment = float(np.multiply(adjustment, np.subtract(87.0, T)))
                    hi_plus = float(np.add(hi_plus, adjustment))
                
                derivative = (hi_plus - hi_calc) / delta_RH
                
                if abs(derivative) < 1e-10:
                    break
                
                RH_guess = RH_guess - (hi_calc - hi_f) / derivative
                
                # Keep within reasonable bounds
                if RH_guess < 40:
                    RH_guess = 40
                if RH_guess > 100:
                    RH_guess = 100
            
            humidity = RH_guess
            
            # Validate result
            if math.isinf(humidity) or math.isnan(humidity) or np.isinf(humidity) or np.isnan(humidity):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_humidity_steps(heat_index, temp_unit, temperature, temp_f, hi_f, humidity)
            
            chart_data = self._prepare_humidity_chart_data(temp_f, humidity, hi_f)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'humidity',
                'heat_index': heat_index,
                'temp_unit': temp_unit,
                'temperature': temperature,
                'humidity': round(humidity, 1),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating humidity: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_temperature(self, data):
        """Convert temperature units"""
        try:
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
            
            from_unit = data.get('from_unit', 'fahrenheit')
            to_unit = data.get('to_unit', 'celsius')
            
            # Validate units
            if from_unit not in ['fahrenheit', 'celsius'] or to_unit not in ['fahrenheit', 'celsius']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            # Convert
            if from_unit == 'fahrenheit' and to_unit == 'celsius':
                result = float(np.multiply(np.subtract(value, 32.0), 5.0/9.0))
            elif from_unit == 'celsius' and to_unit == 'fahrenheit':
                result = float(np.add(np.multiply(value, 9.0/5.0), 32.0))
            else:
                result = value
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_temperature_steps(value, from_unit, to_unit, result)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_temperature',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': round(result, 1),
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _get_heat_index_category(self, hi):
        """Get heat index category and risk level"""
        if hi < 80:
            return {'name': _('Safe'), 'risk': _('Low')}
        elif hi < 90:
            return {'name': _('Caution'), 'risk': _('Moderate')}
        elif hi < 103:
            return {'name': _('Extreme Caution'), 'risk': _('High')}
        elif hi < 124:
            return {'name': _('Danger'), 'risk': _('Very High')}
        else:
            return {'name': _('Extreme Danger'), 'risk': _('Extreme')}
    
    # Step-by-step solution preparation methods
    def _prepare_heat_index_steps(self, temperature, temp_unit, humidity, temp_f, hi, category):
        """Prepare step-by-step solution for heat index calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Temperature: {temp}°{unit}').format(temp=temperature, unit='F' if temp_unit == 'fahrenheit' else 'C'))
        steps.append(_('Relative Humidity: {hum}%').format(hum=humidity))
        steps.append('')
        if temp_unit == 'celsius':
            steps.append(_('Step 2: Convert temperature to Fahrenheit'))
            steps.append(_('Formula: °F = (°C × 9/5) + 32'))
            steps.append(_('°F = ({temp} × 9/5) + 32 = {f}°F').format(temp=temperature, f=temp_f))
            steps.append('')
        steps.append(_('Step 3: Apply the Rothfusz equation'))
        steps.append(_('Heat Index Formula:'))
        steps.append(_('HI = -42.379 + 2.04901523×T + 10.14333127×RH - 0.22475541×T×RH'))
        steps.append(_('     - 6.83783×10⁻³×T² - 5.481717×10⁻²×RH² + 1.22874×10⁻³×T²×RH'))
        steps.append(_('     + 8.5282×10⁻⁴×T×RH² - 1.99×10⁻⁶×T²×RH²'))
        steps.append(_('Where T = {temp}°F, RH = {hum}%').format(temp=temp_f, hum=humidity))
        steps.append('')
        steps.append(_('Step 4: Apply adjustments (if applicable)'))
        if humidity < 13 and temp_f >= 80 and temp_f <= 112:
            steps.append(_('Adjustment for RH < 13%: Subtract correction factor'))
        if humidity > 85 and temp_f >= 80 and temp_f <= 87:
            steps.append(_('Adjustment for RH > 85%: Add correction factor'))
        steps.append('')
        steps.append(_('Step 5: Final result'))
        steps.append(_('Heat Index = {hi}°F').format(hi=round(hi, 1)))
        steps.append(_('Category: {cat} ({risk})').format(cat=category['name'], risk=category['risk']))
        return steps
    
    def _prepare_temperature_steps(self, heat_index, temp_unit, humidity, hi_f, temp_f, temp_c):
        """Prepare step-by-step solution for temperature calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Heat Index: {hi}°{unit}').format(hi=heat_index, unit='F' if temp_unit == 'fahrenheit' else 'C'))
        steps.append(_('Relative Humidity: {hum}%').format(hum=humidity))
        steps.append('')
        if temp_unit == 'celsius':
            steps.append(_('Step 2: Convert heat index to Fahrenheit'))
            steps.append(_('Formula: °F = (°C × 9/5) + 32'))
            steps.append(_('°F = ({hi} × 9/5) + 32 = {f}°F').format(hi=heat_index, f=hi_f))
            steps.append('')
        steps.append(_('Step 3: Solve for temperature using iterative method'))
        steps.append(_('Using the Rothfusz equation, we solve for T where:'))
        steps.append(_('HI = -42.379 + 2.04901523×T + 10.14333127×RH - 0.22475541×T×RH'))
        steps.append(_('     - 6.83783×10⁻³×T² - 5.481717×10⁻²×RH² + 1.22874×10⁻³×T²×RH'))
        steps.append(_('     + 8.5282×10⁻⁴×T×RH² - 1.99×10⁻⁶×T²×RH²'))
        steps.append(_('With HI = {hi}°F, RH = {hum}%').format(hi=hi_f, hum=humidity))
        steps.append('')
        steps.append(_('Step 4: Final result'))
        steps.append(_('Temperature = {temp}°F').format(temp=round(temp_f, 1)))
        if temp_c:
            steps.append(_('Temperature = {temp}°C').format(temp=round(temp_c, 1)))
        return steps
    
    def _prepare_humidity_steps(self, heat_index, temp_unit, temperature, temp_f, hi_f, humidity):
        """Prepare step-by-step solution for humidity calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Heat Index: {hi}°{unit}').format(hi=heat_index, unit='F' if temp_unit == 'fahrenheit' else 'C'))
        steps.append(_('Temperature: {temp}°{unit}').format(temp=temperature, unit='F' if temp_unit == 'fahrenheit' else 'C'))
        steps.append('')
        if temp_unit == 'celsius':
            steps.append(_('Step 2: Convert to Fahrenheit'))
            steps.append(_('Temperature: {temp}°C = {f}°F').format(temp=temperature, f=temp_f))
            steps.append(_('Heat Index: {hi}°C = {f}°F').format(hi=heat_index, f=hi_f))
            steps.append('')
        steps.append(_('Step 3: Solve for relative humidity using iterative method'))
        steps.append(_('Using the Rothfusz equation, we solve for RH where:'))
        steps.append(_('HI = -42.379 + 2.04901523×T + 10.14333127×RH - 0.22475541×T×RH'))
        steps.append(_('     - 6.83783×10⁻³×T² - 5.481717×10⁻²×RH² + 1.22874×10⁻³×T²×RH'))
        steps.append(_('     + 8.5282×10⁻⁴×T×RH² - 1.99×10⁻⁶×T²×RH²'))
        steps.append(_('With HI = {hi}°F, T = {temp}°F').format(hi=hi_f, temp=temp_f))
        steps.append('')
        steps.append(_('Step 4: Final result'))
        steps.append(_('Relative Humidity = {hum}%').format(hum=round(humidity, 1)))
        return steps
    
    def _prepare_convert_temperature_steps(self, value, from_unit, to_unit, result):
        """Prepare step-by-step solution for temperature conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Temperature: {value}°{unit}').format(value=value, unit='F' if from_unit == 'fahrenheit' else 'C'))
        steps.append('')
        if from_unit == 'fahrenheit' and to_unit == 'celsius':
            steps.append(_('Step 2: Convert Fahrenheit to Celsius'))
            steps.append(_('Formula: °C = (°F - 32) × 5/9'))
            steps.append(_('°C = ({f} - 32) × 5/9 = {c}°C').format(f=value, c=result))
        elif from_unit == 'celsius' and to_unit == 'fahrenheit':
            steps.append(_('Step 2: Convert Celsius to Fahrenheit'))
            steps.append(_('Formula: °F = (°C × 9/5) + 32'))
            steps.append(_('°F = ({c} × 9/5) + 32 = {f}°F').format(c=value, f=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Temperature = {result}°{unit}').format(result=result, unit='F' if to_unit == 'fahrenheit' else 'C'))
        return steps
    
    # Chart data preparation methods
    def _prepare_heat_index_chart_data(self, temp_f, humidity, hi):
        """Prepare chart data for heat index calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Temperature (°F)'), _('Relative Humidity (%)'), _('Heat Index (°F)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [temp_f, humidity, hi],
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
                            'text': _('Heat Index Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'heat_index_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_temperature_chart_data(self, temp_f, humidity, hi_f):
        """Prepare chart data for temperature calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Temperature (°F)'), _('Relative Humidity (%)'), _('Heat Index (°F)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [temp_f, humidity, hi_f],
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
                            'text': _('Temperature from Heat Index')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'temperature_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_humidity_chart_data(self, temp_f, humidity, hi_f):
        """Prepare chart data for humidity calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Temperature (°F)'), _('Relative Humidity (%)'), _('Heat Index (°F)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [temp_f, humidity, hi_f],
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
                            'text': _('Relative Humidity from Heat Index')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'humidity_chart': chart_config}
        except Exception as e:
            return None
