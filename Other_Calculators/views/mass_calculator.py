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
class MassCalculator(View):
    """
    Professional Mass Calculator with Comprehensive Features
    
    This calculator provides mass calculations with:
    - Convert mass between different units (kg, g, lbs, oz, tons, stone)
    - Calculate mass from density and volume
    - Calculate density from mass and volume
    - Calculate volume from mass and density
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/mass_calculator.html'
    
    # Mass conversion factors (to kilograms)
    MASS_CONVERSIONS = {
        'kilograms': 1.0,
        'grams': 0.001,  # 1 g = 0.001 kg
        'pounds': 0.453592,  # 1 lb = 0.453592 kg
        'ounces': 0.0283495,  # 1 oz = 0.0283495 kg
        'tons': 1000.0,  # 1 metric ton = 1000 kg
        'stone': 6.35029,  # 1 stone = 6.35029 kg
        'milligrams': 0.000001,  # 1 mg = 0.000001 kg
        'metric_tons': 1000.0,  # 1 metric ton = 1000 kg
        'us_tons': 907.185,  # 1 US ton = 907.185 kg
    }
    
    # Volume conversion factors (to cubic meters)
    VOLUME_CONVERSIONS = {
        'cubic_meters': 1.0,
        'liters': 0.001,  # 1 L = 0.001 m³
        'milliliters': 0.000001,  # 1 mL = 0.000001 m³
        'cubic_centimeters': 0.000001,  # 1 cm³ = 0.000001 m³
        'cubic_feet': 0.0283168,  # 1 ft³ = 0.0283168 m³
        'cubic_inches': 0.0000163871,  # 1 in³ = 0.0000163871 m³
        'gallons_us': 0.00378541,  # 1 US gal = 0.00378541 m³
        'gallons_uk': 0.00454609,  # 1 UK gal = 0.00454609 m³
    }
    
    # Density conversion factors (to kg/m³)
    DENSITY_CONVERSIONS = {
        'kg_per_m3': 1.0,
        'g_per_cm3': 1000.0,  # 1 g/cm³ = 1000 kg/m³
        'g_per_ml': 1000.0,  # 1 g/mL = 1000 kg/m³
        'lb_per_ft3': 16.0185,  # 1 lb/ft³ = 16.0185 kg/m³
        'lb_per_in3': 27679.9,  # 1 lb/in³ = 27679.9 kg/m³
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'kilograms': 'kg',
            'grams': 'g',
            'pounds': 'lbs',
            'ounces': 'oz',
            'tons': 'tons',
            'stone': 'stone',
            'milligrams': 'mg',
            'metric_tons': 'metric tons',
            'us_tons': 'US tons',
            'cubic_meters': 'm³',
            'liters': 'L',
            'milliliters': 'mL',
            'cubic_centimeters': 'cm³',
            'cubic_feet': 'ft³',
            'cubic_inches': 'in³',
            'gallons_us': 'US gal',
            'gallons_uk': 'UK gal',
            'kg_per_m3': 'kg/m³',
            'g_per_cm3': 'g/cm³',
            'g_per_ml': 'g/mL',
            'lb_per_ft3': 'lb/ft³',
            'lb_per_in3': 'lb/in³',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Mass Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'convert')
            
            if calc_type == 'convert':
                return self._convert_mass(data)
            elif calc_type == 'mass_from_density':
                return self._calculate_mass_from_density(data)
            elif calc_type == 'density_from_mass':
                return self._calculate_density_from_mass(data)
            elif calc_type == 'volume_from_mass':
                return self._calculate_volume_from_mass(data)
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
    
    def _convert_mass(self, data):
        """Convert mass between different units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'kilograms')
            to_unit = data.get('to_unit', 'pounds')
            
            # Validate units
            if from_unit not in self.MASS_CONVERSIONS or to_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass must be non-negative.')
                }, status=400)
            
            # Convert to kilograms first
            kilograms = float(value * self.MASS_CONVERSIONS[from_unit])
            
            # Convert to target unit
            result = float(np.divide(kilograms, self.MASS_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_mass_steps(value, from_unit, to_unit, result, kilograms)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': round(result, 6),
                'kilograms': round(kilograms, 6),
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting mass: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_mass_from_density(self, data):
        """Calculate mass from density and volume"""
        try:
            if 'density' not in data or data.get('density') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Density is required.')
                }, status=400)
            
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                density = float(data.get('density', 0))
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            density_unit = data.get('density_unit', 'kg_per_m3')
            volume_unit = data.get('volume_unit', 'cubic_meters')
            result_unit = data.get('result_unit', 'kilograms')
            
            # Validate units
            if density_unit not in self.DENSITY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid density unit.')
                }, status=400)
            
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            if result_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if density <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Density must be greater than zero.')
                }, status=400)
            
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            # Convert to base units (kg/m³ and m³)
            density_kg_m3 = float(density * self.DENSITY_CONVERSIONS[density_unit])
            volume_m3 = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate mass: Mass = Density × Volume
            mass_kg = float(np.multiply(density_kg_m3, volume_m3))
            
            # Convert to result unit
            result = float(np.divide(mass_kg, self.MASS_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_mass_from_density_steps(density, density_unit, volume, volume_unit, density_kg_m3, volume_m3, mass_kg, result, result_unit)
            
            chart_data = self._prepare_mass_from_density_chart_data(density_kg_m3, volume_m3, mass_kg)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'mass_from_density',
                'density': density,
                'density_unit': density_unit,
                'volume': volume,
                'volume_unit': volume_unit,
                'mass': round(result, 6),
                'result_unit': result_unit,
                'mass_kg': round(mass_kg, 6),
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
                'error': _('Error calculating mass: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_density_from_mass(self, data):
        """Calculate density from mass and volume"""
        try:
            if 'mass' not in data or data.get('mass') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass is required.')
                }, status=400)
            
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                mass = float(data.get('mass', 0))
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            mass_unit = data.get('mass_unit', 'kilograms')
            volume_unit = data.get('volume_unit', 'cubic_meters')
            result_unit = data.get('result_unit', 'kg_per_m3')
            
            # Validate units
            if mass_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid mass unit.')
                }, status=400)
            
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            if result_unit not in self.DENSITY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if mass <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass must be greater than zero.')
                }, status=400)
            
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            # Convert to base units (kg and m³)
            mass_kg = float(mass * self.MASS_CONVERSIONS[mass_unit])
            volume_m3 = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate density: Density = Mass / Volume
            density_kg_m3 = float(np.divide(mass_kg, volume_m3))
            
            # Convert to result unit
            result = float(np.divide(density_kg_m3, self.DENSITY_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_density_from_mass_steps(mass, mass_unit, volume, volume_unit, mass_kg, volume_m3, density_kg_m3, result, result_unit)
            
            chart_data = self._prepare_density_from_mass_chart_data(mass_kg, volume_m3, density_kg_m3)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'density_from_mass',
                'mass': mass,
                'mass_unit': mass_unit,
                'volume': volume,
                'volume_unit': volume_unit,
                'density': round(result, 6),
                'result_unit': result_unit,
                'density_kg_m3': round(density_kg_m3, 6),
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
                'error': _('Error calculating density: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_volume_from_mass(self, data):
        """Calculate volume from mass and density"""
        try:
            if 'mass' not in data or data.get('mass') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass is required.')
                }, status=400)
            
            if 'density' not in data or data.get('density') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Density is required.')
                }, status=400)
            
            try:
                mass = float(data.get('mass', 0))
                density = float(data.get('density', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            mass_unit = data.get('mass_unit', 'kilograms')
            density_unit = data.get('density_unit', 'kg_per_m3')
            result_unit = data.get('result_unit', 'cubic_meters')
            
            # Validate units
            if mass_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid mass unit.')
                }, status=400)
            
            if density_unit not in self.DENSITY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid density unit.')
                }, status=400)
            
            if result_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if mass <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass must be greater than zero.')
                }, status=400)
            
            if density <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Density must be greater than zero.')
                }, status=400)
            
            # Convert to base units (kg and kg/m³)
            mass_kg = float(mass * self.MASS_CONVERSIONS[mass_unit])
            density_kg_m3 = float(density * self.DENSITY_CONVERSIONS[density_unit])
            
            # Calculate volume: Volume = Mass / Density
            volume_m3 = float(np.divide(mass_kg, density_kg_m3))
            
            # Convert to result unit
            result = float(np.divide(volume_m3, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_volume_from_mass_steps(mass, mass_unit, density, density_unit, mass_kg, density_kg_m3, volume_m3, result, result_unit)
            
            chart_data = self._prepare_volume_from_mass_chart_data(mass_kg, density_kg_m3, volume_m3)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'volume_from_mass',
                'mass': mass,
                'mass_unit': mass_unit,
                'density': density,
                'density_unit': density_unit,
                'volume': round(result, 6),
                'result_unit': result_unit,
                'volume_m3': round(volume_m3, 6),
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
                'error': _('Error calculating volume: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_convert_mass_steps(self, value, from_unit, to_unit, result, kilograms):
        """Prepare step-by-step solution for mass conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Mass: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'kilograms':
            steps.append(_('Step 2: Convert to kilograms (base unit)'))
            if from_unit == 'grams':
                steps.append(_('Kilograms = Grams / 1000'))
                steps.append(_('Kilograms = {g} g / 1000 = {kg} kg').format(g=value, kg=kilograms))
            elif from_unit == 'pounds':
                steps.append(_('Kilograms = Pounds × 0.453592'))
                steps.append(_('Kilograms = {lb} lbs × 0.453592 = {kg} kg').format(lb=value, kg=kilograms))
            elif from_unit == 'ounces':
                steps.append(_('Kilograms = Ounces × 0.0283495'))
                steps.append(_('Kilograms = {oz} oz × 0.0283495 = {kg} kg').format(oz=value, kg=kilograms))
            elif from_unit == 'tons':
                steps.append(_('Kilograms = Tons × 1000'))
                steps.append(_('Kilograms = {tons} tons × 1000 = {kg} kg').format(tons=value, kg=kilograms))
            elif from_unit == 'stone':
                steps.append(_('Kilograms = Stone × 6.35029'))
                steps.append(_('Kilograms = {stone} stone × 6.35029 = {kg} kg').format(stone=value, kg=kilograms))
            else:
                steps.append(_('Kilograms = {value} {unit} × conversion factor = {kg} kg').format(value=value, unit=self._format_unit(from_unit), kg=kilograms))
            steps.append('')
        if to_unit != 'kilograms':
            steps.append(_('Step 3: Convert from kilograms to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'grams':
                steps.append(_('Grams = Kilograms × 1000'))
                steps.append(_('Grams = {kg} kg × 1000 = {result} g').format(kg=kilograms, result=result))
            elif to_unit == 'pounds':
                steps.append(_('Pounds = Kilograms / 0.453592'))
                steps.append(_('Pounds = {kg} kg / 0.453592 = {result} lbs').format(kg=kilograms, result=result))
            elif to_unit == 'ounces':
                steps.append(_('Ounces = Kilograms / 0.0283495'))
                steps.append(_('Ounces = {kg} kg / 0.0283495 = {result} oz').format(kg=kilograms, result=result))
            elif to_unit == 'tons':
                steps.append(_('Tons = Kilograms / 1000'))
                steps.append(_('Tons = {kg} kg / 1000 = {result} tons').format(kg=kilograms, result=result))
            elif to_unit == 'stone':
                steps.append(_('Stone = Kilograms / 6.35029'))
                steps.append(_('Stone = {kg} kg / 6.35029 = {result} stone').format(kg=kilograms, result=result))
            else:
                steps.append(_('Result = {kg} kg / conversion factor = {result} {unit}').format(kg=kilograms, result=result, unit=self._format_unit(to_unit)))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Mass = {result} kg').format(result=result))
        return steps
    
    def _prepare_mass_from_density_steps(self, density, density_unit, volume, volume_unit, density_kg_m3, volume_m3, mass_kg, result, result_unit):
        """Prepare step-by-step solution for mass from density calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Density: {density} {unit}').format(density=density, unit=self._format_unit(density_unit)))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if density_unit != 'kg_per_m3':
            steps.append(_('Density in kg/m³: {density} kg/m³').format(density=density_kg_m3))
        if volume_unit != 'cubic_meters':
            steps.append(_('Volume in m³: {volume} m³').format(volume=volume_m3))
        steps.append('')
        steps.append(_('Step 3: Apply the mass formula'))
        steps.append(_('Formula: Mass = Density × Volume'))
        steps.append(_('Mass = {density} kg/m³ × {volume} m³').format(density=density_kg_m3, volume=volume_m3))
        steps.append(_('Mass = {mass} kg').format(mass=mass_kg))
        steps.append('')
        if result_unit != 'kilograms':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Mass = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Mass = {result} kg').format(result=result))
        return steps
    
    def _prepare_density_from_mass_steps(self, mass, mass_unit, volume, volume_unit, mass_kg, volume_m3, density_kg_m3, result, result_unit):
        """Prepare step-by-step solution for density from mass calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Mass: {mass} {unit}').format(mass=mass, unit=self._format_unit(mass_unit)))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if mass_unit != 'kilograms':
            steps.append(_('Mass in kg: {mass} kg').format(mass=mass_kg))
        if volume_unit != 'cubic_meters':
            steps.append(_('Volume in m³: {volume} m³').format(volume=volume_m3))
        steps.append('')
        steps.append(_('Step 3: Apply the density formula'))
        steps.append(_('Formula: Density = Mass / Volume'))
        steps.append(_('Density = {mass} kg / {volume} m³').format(mass=mass_kg, volume=volume_m3))
        steps.append(_('Density = {density} kg/m³').format(density=density_kg_m3))
        steps.append('')
        if result_unit != 'kg_per_m3':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Density = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Density = {result} kg/m³').format(result=result))
        return steps
    
    def _prepare_volume_from_mass_steps(self, mass, mass_unit, density, density_unit, mass_kg, density_kg_m3, volume_m3, result, result_unit):
        """Prepare step-by-step solution for volume from mass calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Mass: {mass} {unit}').format(mass=mass, unit=self._format_unit(mass_unit)))
        steps.append(_('Density: {density} {unit}').format(density=density, unit=self._format_unit(density_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if mass_unit != 'kilograms':
            steps.append(_('Mass in kg: {mass} kg').format(mass=mass_kg))
        if density_unit != 'kg_per_m3':
            steps.append(_('Density in kg/m³: {density} kg/m³').format(density=density_kg_m3))
        steps.append('')
        steps.append(_('Step 3: Apply the volume formula'))
        steps.append(_('Formula: Volume = Mass / Density'))
        steps.append(_('Volume = {mass} kg / {density} kg/m³').format(mass=mass_kg, density=density_kg_m3))
        steps.append(_('Volume = {volume} m³').format(volume=volume_m3))
        steps.append('')
        if result_unit != 'cubic_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Volume = {result} m³').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_mass_from_density_chart_data(self, density_kg_m3, volume_m3, mass_kg):
        """Prepare chart data for mass from density calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Density (kg/m³)'), _('Volume (m³)'), _('Mass (kg)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [density_kg_m3, volume_m3, mass_kg],
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
                            'text': _('Mass from Density Calculation')
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
            return {'mass_from_density_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_density_from_mass_chart_data(self, mass_kg, volume_m3, density_kg_m3):
        """Prepare chart data for density from mass calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Mass (kg)'), _('Volume (m³)'), _('Density (kg/m³)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [mass_kg, volume_m3, density_kg_m3],
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
                            'text': _('Density from Mass Calculation')
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
            return {'density_from_mass_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_volume_from_mass_chart_data(self, mass_kg, density_kg_m3, volume_m3):
        """Prepare chart data for volume from mass calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Mass (kg)'), _('Density (kg/m³)'), _('Volume (m³)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [mass_kg, density_kg_m3, volume_m3],
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
                            'text': _('Volume from Mass Calculation')
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
            return {'volume_from_mass_chart': chart_config}
        except Exception as e:
            return None
