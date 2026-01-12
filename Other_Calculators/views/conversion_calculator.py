from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ConversionCalculator(View):
    """
    Professional Conversion Calculator with Comprehensive Features
    
    This calculator provides unit conversions for:
    - Length (meters, feet, inches, yards, kilometers, miles, etc.)
    - Weight/Mass (kg, lbs, oz, grams, tons, etc.)
    - Volume (liters, gallons, cubic meters, cubic feet, etc.)
    - Temperature (Celsius, Fahrenheit, Kelvin)
    - Area (square meters, square feet, acres, hectares, etc.)
    - Speed (km/h, mph, m/s, knots, etc.)
    - Time (seconds, minutes, hours, days, weeks, months, years)
    - Data (bytes, KB, MB, GB, TB, etc.)
    - Pressure (Pa, psi, bar, atm, etc.)
    - Energy (BTU, kWh, Joules, Calories, etc.)
    
    Features:
    - Supports multiple conversion categories
    - Handles bidirectional conversions
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/conversion_calculator.html'
    
    # Length conversion factors (to meters)
    LENGTH_CONVERSIONS = {
        'meters': 1.0,
        'kilometers': 1000.0,
        'centimeters': 0.01,
        'millimeters': 0.001,
        'miles': 1609.344,
        'yards': 0.9144,
        'feet': 0.3048,
        'inches': 0.0254,
        'nautical_miles': 1852.0,
    }
    
    # Weight/Mass conversion factors (to kilograms)
    WEIGHT_CONVERSIONS = {
        'kilograms': 1.0,
        'grams': 0.001,
        'milligrams': 0.000001,
        'metric_tons': 1000.0,
        'pounds': 0.453592,
        'ounces': 0.0283495,
        'tons_us': 907.185,
        'tons_uk': 1016.05,
        'stones': 6.35029,
    }
    
    # Volume conversion factors (to liters)
    VOLUME_CONVERSIONS = {
        'liters': 1.0,
        'milliliters': 0.001,
        'cubic_meters': 1000.0,
        'cubic_centimeters': 0.001,
        'gallons_us': 3.78541,
        'gallons_uk': 4.54609,
        'quarts_us': 0.946353,
        'pints_us': 0.473176,
        'cups_us': 0.236588,
        'fluid_ounces_us': 0.0295735,
        'cubic_feet': 28.3168,
        'cubic_inches': 0.0163871,
        'cubic_yards': 764.555,
    }
    
    # Area conversion factors (to square meters)
    AREA_CONVERSIONS = {
        'square_meters': 1.0,
        'square_kilometers': 1000000.0,
        'square_centimeters': 0.0001,
        'square_millimeters': 0.000001,
        'square_miles': 2589988.11,
        'acres': 4046.86,
        'hectares': 10000.0,
        'square_yards': 0.836127,
        'square_feet': 0.092903,
        'square_inches': 0.00064516,
    }
    
    # Speed conversion factors (to m/s)
    SPEED_CONVERSIONS = {
        'meters_per_second': 1.0,
        'kilometers_per_hour': 0.277778,
        'miles_per_hour': 0.44704,
        'feet_per_second': 0.3048,
        'knots': 0.514444,
        'mach': 343.0,
    }
    
    # Time conversion factors (to seconds)
    TIME_CONVERSIONS = {
        'seconds': 1.0,
        'milliseconds': 0.001,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': 86400.0,
        'weeks': 604800.0,
        'months': 2592000.0,  # 30 days average
        'years': 31536000.0,  # 365 days
        'decades': 315360000.0,
        'centuries': 3153600000.0,
    }
    
    # Data conversion factors (to bytes)
    DATA_CONVERSIONS = {
        'bytes': 1.0,
        'kilobytes': 1024.0,
        'megabytes': 1048576.0,
        'gigabytes': 1073741824.0,
        'terabytes': 1099511627776.0,
        'petabytes': 1125899906842624.0,
        'bits': 0.125,
        'kilobits': 128.0,
        'megabits': 131072.0,
        'gigabits': 134217728.0,
    }
    
    # Pressure conversion factors (to Pascals)
    PRESSURE_CONVERSIONS = {
        'pascals': 1.0,
        'kilopascals': 1000.0,
        'megapascals': 1000000.0,
        'psi': 6894.76,
        'bar': 100000.0,
        'atmosphere': 101325.0,
        'torr': 133.322,
        'millimeters_hg': 133.322,
    }
    
    # Energy conversion factors (to Joules)
    ENERGY_CONVERSIONS = {
        'joules': 1.0,
        'kilojoules': 1000.0,
        'calories': 4.184,
        'kilocalories': 4184.0,
        'btu': 1055.06,
        'kwh': 3600000.0,
        'foot_pounds': 1.35582,
        'electronvolts': 1.602176634e-19,
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Conversion Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            conversion_type = data.get('conversion_type', 'length')
            value = data.get('value', 0)
            from_unit = data.get('from_unit', 'meters')
            to_unit = data.get('to_unit', 'feet')
            
            # Validate conversion type
            valid_types = ['length', 'weight', 'volume', 'temperature', 'area', 'speed', 'time', 'data', 'pressure', 'energy']
            if conversion_type not in valid_types:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion type. Please select a valid conversion type.')
                }, status=400)
            
            # Validate input value
            try:
                value = float(value)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid value. Please enter a valid number.')
                }, status=400)
            
            # Check for infinity or NaN
            if not math.isfinite(value):
                return JsonResponse({
                    'success': False,
                    'error': _('Value must be a finite number.')
                }, status=400)
            
            # Validate value range
            if value < 0 and conversion_type not in ['temperature']:
                return JsonResponse({
                    'success': False,
                    'error': _('Value must be positive for this conversion type.')
                }, status=400)
            
            # Validate units exist for the conversion type
            if conversion_type == 'temperature':
                valid_units = ['celsius', 'fahrenheit', 'kelvin']
                if from_unit not in valid_units or to_unit not in valid_units:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid temperature unit. Please select Celsius, Fahrenheit, or Kelvin.')
                    }, status=400)
            else:
                conversion_map = {
                    'length': self.LENGTH_CONVERSIONS,
                    'weight': self.WEIGHT_CONVERSIONS,
                    'volume': self.VOLUME_CONVERSIONS,
                    'area': self.AREA_CONVERSIONS,
                    'speed': self.SPEED_CONVERSIONS,
                    'time': self.TIME_CONVERSIONS,
                    'data': self.DATA_CONVERSIONS,
                    'pressure': self.PRESSURE_CONVERSIONS,
                    'energy': self.ENERGY_CONVERSIONS,
                }
                conversions = conversion_map.get(conversion_type)
                if not conversions:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid conversion type.')
                    }, status=400)
                
                if from_unit not in conversions:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid "from" unit for this conversion type.')
                    }, status=400)
                
                if to_unit not in conversions:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid "to" unit for this conversion type.')
                    }, status=400)
            
            # Check if units are the same
            if from_unit == to_unit:
                return JsonResponse({
                    'success': False,
                    'error': _('Please select different units for conversion.')
                }, status=400)
            
            # Perform conversion
            try:
                if conversion_type == 'temperature':
                    result = self._convert_temperature(value, from_unit, to_unit)
                else:
                    result = self._convert_unit(value, conversion_type, from_unit, to_unit)
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': _('Conversion error: {error}').format(error=str(e))
                }, status=500)
            
            # Validate result
            if not math.isfinite(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Conversion resulted in an invalid number.')
                }, status=500)
            
            # Prepare response
            response_data = {
                'success': True,
                'result': result,
                'original_value': value,
                'original_unit': from_unit,
                'converted_value': result,
                'converted_unit': to_unit,
                'conversion_type': conversion_type,
                'step_by_step': self._prepare_step_by_step(value, from_unit, to_unit, result, conversion_type),
                'chart_data': self._prepare_chart_data(value, from_unit, to_unit, result, conversion_type),
            }
            
            return JsonResponse(response_data)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data. Please try again.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_unit(self, value, conversion_type, from_unit, to_unit):
        """Convert between units"""
        conversion_map = {
            'length': self.LENGTH_CONVERSIONS,
            'weight': self.WEIGHT_CONVERSIONS,
            'volume': self.VOLUME_CONVERSIONS,
            'area': self.AREA_CONVERSIONS,
            'speed': self.SPEED_CONVERSIONS,
            'time': self.TIME_CONVERSIONS,
            'data': self.DATA_CONVERSIONS,
            'pressure': self.PRESSURE_CONVERSIONS,
            'energy': self.ENERGY_CONVERSIONS,
        }
        
        conversions = conversion_map.get(conversion_type)
        if not conversions:
            raise ValueError(_('Invalid conversion type'))
        
        if from_unit not in conversions:
            raise ValueError(_('Invalid "from" unit: {unit}').format(unit=from_unit))
        
        if to_unit not in conversions:
            raise ValueError(_('Invalid "to" unit: {unit}').format(unit=to_unit))
        
        # Convert to base unit, then to target unit
        from_factor = conversions[from_unit]
        to_factor = conversions[to_unit]
        
        if from_factor == 0 or to_factor == 0:
            raise ValueError(_('Invalid conversion factor'))
        
        base_value = value * from_factor
        result = base_value / to_factor
        
        # Round to reasonable precision
        if abs(result) < 0.000001:
            return round(result, 15)
        elif abs(result) >= 1000000:
            return round(result, 6)
        else:
            return round(result, 10)
    
    def _convert_temperature(self, value, from_unit, to_unit):
        """Convert temperature between Celsius, Fahrenheit, and Kelvin"""
        # Convert to Celsius first
        if from_unit == 'celsius':
            celsius = value
        elif from_unit == 'fahrenheit':
            celsius = (value - 32) * 5 / 9
        elif from_unit == 'kelvin':
            celsius = value - 273.15
        else:
            raise ValueError(_('Invalid temperature unit'))
        
        # Convert from Celsius to target
        if to_unit == 'celsius':
            return round(celsius, 10)
        elif to_unit == 'fahrenheit':
            return round(celsius * 9 / 5 + 32, 10)
        elif to_unit == 'kelvin':
            return round(celsius + 273.15, 10)
        else:
            raise ValueError(_('Invalid temperature unit'))
    
    def _prepare_step_by_step(self, value, from_unit, to_unit, result, conversion_type):
        """Prepare step-by-step solution"""
        steps = []
        
        if conversion_type == 'temperature':
            steps.append(_('Step 1: Identify the conversion'))
            steps.append(_('Converting from {from_unit} to {to_unit}').format(
                from_unit=from_unit.title(), to_unit=to_unit.title()
            ))
            steps.append('')
            steps.append(_('Step 2: Convert to Celsius (base unit)'))
            if from_unit == 'celsius':
                steps.append(_('Value is already in Celsius: {value}°C').format(value=value))
                celsius = value
            elif from_unit == 'fahrenheit':
                steps.append(_('Formula: Celsius = (Fahrenheit - 32) × 5/9'))
                steps.append(_('Celsius = ({value} - 32) × 5/9').format(value=value))
                celsius = (value - 32) * 5 / 9
                steps.append(_('Celsius = {result}°C').format(result=round(celsius, 2)))
            elif from_unit == 'kelvin':
                steps.append(_('Formula: Celsius = Kelvin - 273.15'))
                steps.append(_('Celsius = {value} - 273.15').format(value=value))
                celsius = value - 273.15
                steps.append(_('Celsius = {result}°C').format(result=round(celsius, 2)))
            steps.append('')
            steps.append(_('Step 3: Convert from Celsius to target unit'))
            if to_unit == 'celsius':
                steps.append(_('Result: {result}°C').format(result=round(celsius, 10)))
            elif to_unit == 'fahrenheit':
                steps.append(_('Formula: Fahrenheit = Celsius × 9/5 + 32'))
                steps.append(_('Fahrenheit = {celsius} × 9/5 + 32').format(celsius=round(celsius, 2)))
                steps.append(_('Fahrenheit = {result}°F').format(result=round(result, 10)))
            elif to_unit == 'kelvin':
                steps.append(_('Formula: Kelvin = Celsius + 273.15'))
                steps.append(_('Kelvin = {celsius} + 273.15').format(celsius=round(celsius, 2)))
                steps.append(_('Kelvin = {result}K').format(result=round(result, 10)))
        else:
            conversion_map = {
                'length': (self.LENGTH_CONVERSIONS, _('meters')),
                'weight': (self.WEIGHT_CONVERSIONS, _('kilograms')),
                'volume': (self.VOLUME_CONVERSIONS, _('liters')),
                'area': (self.AREA_CONVERSIONS, _('square meters')),
                'speed': (self.SPEED_CONVERSIONS, _('meters per second')),
                'time': (self.TIME_CONVERSIONS, _('seconds')),
                'data': (self.DATA_CONVERSIONS, _('bytes')),
                'pressure': (self.PRESSURE_CONVERSIONS, _('pascals')),
                'energy': (self.ENERGY_CONVERSIONS, _('joules')),
            }
            
            conversions, base_unit = conversion_map.get(conversion_type, (None, None))
            if not conversions:
                return steps
            
            steps.append(_('Step 1: Identify the conversion'))
            steps.append(_('Converting {value} {from_unit} to {to_unit}').format(
                value=value, from_unit=from_unit.replace('_', ' ').title(),
                to_unit=to_unit.replace('_', ' ').title()
            ))
            steps.append('')
            steps.append(_('Step 2: Convert to base unit ({base_unit})').format(base_unit=base_unit))
            from_factor = conversions[from_unit]
            base_value = value * from_factor
            steps.append(_('Formula: Base Value = Value × Conversion Factor'))
            steps.append(_('Base Value = {value} × {factor}').format(
                value=value, factor=from_factor
            ))
            steps.append(_('Base Value = {result} {base_unit}').format(
                result=round(base_value, 6), base_unit=base_unit
            ))
            steps.append('')
            steps.append(_('Step 3: Convert from base unit to target unit'))
            to_factor = conversions[to_unit]
            steps.append(_('Formula: Result = Base Value ÷ Conversion Factor'))
            steps.append(_('Result = {base_value} ÷ {factor}').format(
                base_value=round(base_value, 6), factor=to_factor
            ))
            steps.append(_('Result = {result} {to_unit}').format(
                result=round(result, 10), to_unit=to_unit.replace('_', ' ').title()
            ))
        
        return steps
    
    def _prepare_chart_data(self, value, from_unit, to_unit, result, conversion_type):
        """Prepare chart data for visualization"""
        # Create comparison chart showing original and converted values
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [
                    from_unit.replace('_', ' ').title(),
                    to_unit.replace('_', ' ').title()
                ],
                'datasets': [{
                    'label': _('Value'),
                    'data': [value, result],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    'borderColor': [
                        '#3b82f6',
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
                        'text': _('Unit Conversion Comparison')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }
        
        return {'comparison_chart': chart_config}
