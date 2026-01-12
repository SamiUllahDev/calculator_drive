from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, Eq, solve, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DensityCalculator(View):
    """
    Professional Density Calculator with Comprehensive Features
    
    This calculator provides density calculations with:
    - Calculate density from mass and volume
    - Calculate mass from density and volume
    - Calculate volume from density and mass
    - Unit conversions for density, mass, and volume
    
    Features:
    - Supports multiple calculation modes
    - Handles various units (metric and imperial)
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/density_calculator.html'
    
    # Density conversion factors (to kg/m³)
    DENSITY_CONVERSIONS = {
        'kg_per_m3': 1.0,
        'g_per_cm3': 1000.0,
        'g_per_liter': 1.0,
        'lb_per_ft3': 16.018463,
        'lb_per_in3': 27679.9,
        'oz_per_in3': 1729.99,
        'g_per_ml': 1000.0,
    }
    
    # Mass conversion factors (to kg)
    MASS_CONVERSIONS = {
        'kg': 1.0,
        'g': 0.001,
        'mg': 0.000001,
        'lb': 0.453592,
        'oz': 0.0283495,
        'ton': 1000.0,
    }
    
    # Volume conversion factors (to m³)
    VOLUME_CONVERSIONS = {
        'm3': 1.0,
        'cm3': 0.000001,
        'liter': 0.001,
        'ml': 0.000001,
        'ft3': 0.0283168,
        'in3': 0.0000163871,
        'gallon_us': 0.00378541,
        'gallon_uk': 0.00454609,
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit.replace('_', '/').replace('per', '/')
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Density Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'density')
            
            if calc_type == 'density':
                return self._calculate_density(data)
            elif calc_type == 'mass':
                return self._calculate_mass(data)
            elif calc_type == 'volume':
                return self._calculate_volume(data)
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
    
    def _calculate_density(self, data):
        """Calculate density from mass and volume"""
        try:
            mass = float(data.get('mass', 0))
            mass_unit = data.get('mass_unit', 'kg')
            volume = float(data.get('volume', 0))
            volume_unit = data.get('volume_unit', 'm3')
            result_unit = data.get('result_unit', 'kg_per_m3')
            
            # Validate inputs
            if not isinstance(mass, (int, float)) or not isinstance(volume, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
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
            
            if mass > 1e20 or volume > 1e20:
                return JsonResponse({
                    'success': False,
                    'error': _('Values are too large. Please use smaller values.')
                }, status=400)
            
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
            
            # Convert to base units using numpy for precision
            mass_kg = np.multiply(mass, self.MASS_CONVERSIONS.get(mass_unit, 1.0))
            volume_m3 = np.multiply(volume, self.VOLUME_CONVERSIONS.get(volume_unit, 1.0))
            
            # Calculate density in kg/m³ using numpy for precision
            density_kg_m3 = np.divide(mass_kg, volume_m3)
            
            # Convert to Python float for JSON serialization
            mass_kg = float(mass_kg)
            volume_m3 = float(volume_m3)
            
            # Convert to result unit
            if result_unit not in self.DENSITY_CONVERSIONS:
                result_unit = 'kg_per_m3'
            
            conversion_factor = np.divide(
                self.DENSITY_CONVERSIONS.get('kg_per_m3', 1.0),
                self.DENSITY_CONVERSIONS.get(result_unit, 1.0)
            )
            density_result = np.multiply(density_kg_m3, conversion_factor)
            
            # Convert numpy scalar to Python float
            density_kg_m3 = float(density_kg_m3)
            density_result = float(density_result)
            
            if math.isinf(density_result) or math.isnan(density_result) or np.isinf(density_result) or np.isnan(density_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'density',
                'mass': mass,
                'mass_unit': mass_unit,
                'volume': volume,
                'volume_unit': volume_unit,
                'density': density_result,
                'density_unit': result_unit,
                'density_unit_formatted': self._format_unit(result_unit),
                'density_kg_m3': density_kg_m3,
                'step_by_step': self._prepare_density_steps(mass, mass_unit, volume, volume_unit, density_result, result_unit, mass_kg, volume_m3),
                'chart_data': self._prepare_density_chart_data(density_kg_m3),
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
                'error': _('Error calculating density: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_mass(self, data):
        """Calculate mass from density and volume"""
        try:
            density = float(data.get('density', 0))
            density_unit = data.get('density_unit', 'kg_per_m3')
            volume = float(data.get('volume', 0))
            volume_unit = data.get('volume_unit', 'm3')
            result_unit = data.get('result_unit', 'kg')
            
            # Validate inputs
            if not isinstance(density, (int, float)) or not isinstance(volume, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
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
            
            if density > 1e20 or volume > 1e20:
                return JsonResponse({
                    'success': False,
                    'error': _('Values are too large. Please use smaller values.')
                }, status=400)
            
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
            
            # Convert to base units using numpy for precision
            density_kg_m3 = np.multiply(density, self.DENSITY_CONVERSIONS.get(density_unit, 1.0))
            volume_m3 = np.multiply(volume, self.VOLUME_CONVERSIONS.get(volume_unit, 1.0))
            
            # Calculate mass in kg using numpy for precision
            mass_kg = np.multiply(density_kg_m3, volume_m3)
            
            # Convert to Python float for JSON serialization
            density_kg_m3 = float(density_kg_m3)
            volume_m3 = float(volume_m3)
            
            # Convert to result unit
            if result_unit not in self.MASS_CONVERSIONS:
                result_unit = 'kg'
            
            conversion_factor = np.divide(
                self.MASS_CONVERSIONS.get('kg', 1.0),
                self.MASS_CONVERSIONS.get(result_unit, 1.0)
            )
            mass_result = np.multiply(mass_kg, conversion_factor)
            
            # Convert numpy scalar to Python float
            mass_kg = float(mass_kg)
            mass_result = float(mass_result)
            
            if math.isinf(mass_result) or math.isnan(mass_result) or np.isinf(mass_result) or np.isnan(mass_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'mass',
                'density': density,
                'density_unit': density_unit,
                'density_unit_formatted': self._format_unit(density_unit),
                'volume': volume,
                'volume_unit': volume_unit,
                'mass': mass_result,
                'mass_unit': result_unit,
                'mass_kg': mass_kg,
                'density_kg_m3': density_kg_m3,
                'volume_m3': volume_m3,
                'step_by_step': self._prepare_mass_steps(density, density_unit, volume, volume_unit, mass_result, result_unit, density_kg_m3, volume_m3),
                'chart_data': self._prepare_mass_chart_data(mass_kg, density_kg_m3, volume_m3),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _calculate_volume(self, data):
        """Calculate volume from density and mass"""
        try:
            density = float(data.get('density', 0))
            density_unit = data.get('density_unit', 'kg_per_m3')
            mass = float(data.get('mass', 0))
            mass_unit = data.get('mass_unit', 'kg')
            result_unit = data.get('result_unit', 'm3')
            
            # Validate inputs
            if not isinstance(density, (int, float)) or not isinstance(mass, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            if density <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Density must be greater than zero.')
                }, status=400)
            
            if mass <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass must be greater than zero.')
                }, status=400)
            
            if density > 1e20 or mass > 1e20:
                return JsonResponse({
                    'success': False,
                    'error': _('Values are too large. Please use smaller values.')
                }, status=400)
            
            if density_unit not in self.DENSITY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid density unit.')
                }, status=400)
            
            if mass_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid mass unit.')
                }, status=400)
            
            # Convert to base units using numpy for precision
            density_kg_m3 = np.multiply(density, self.DENSITY_CONVERSIONS.get(density_unit, 1.0))
            mass_kg = np.multiply(mass, self.MASS_CONVERSIONS.get(mass_unit, 1.0))
            
            # Calculate volume in m³ using numpy for precision
            volume_m3 = np.divide(mass_kg, density_kg_m3)
            
            # Convert to Python float for JSON serialization
            density_kg_m3 = float(density_kg_m3)
            mass_kg = float(mass_kg)
            
            # Convert to result unit
            if result_unit not in self.VOLUME_CONVERSIONS:
                result_unit = 'm3'
            
            conversion_factor = np.divide(
                self.VOLUME_CONVERSIONS.get('m3', 1.0),
                self.VOLUME_CONVERSIONS.get(result_unit, 1.0)
            )
            volume_result = np.multiply(volume_m3, conversion_factor)
            
            # Convert numpy scalar to Python float
            volume_m3 = float(volume_m3)
            volume_result = float(volume_result)
            
            if math.isinf(volume_result) or math.isnan(volume_result) or np.isinf(volume_result) or np.isnan(volume_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            response_data = {
                'success': True,
                'calc_type': 'volume',
                'density': density,
                'density_unit': density_unit,
                'density_unit_formatted': self._format_unit(density_unit),
                'mass': mass,
                'mass_unit': mass_unit,
                'volume': volume_result,
                'volume_unit': result_unit,
                'volume_m3': volume_m3,
                'density_kg_m3': density_kg_m3,
                'mass_kg': mass_kg,
                'step_by_step': self._prepare_volume_steps(density, density_unit, mass, mass_unit, volume_result, result_unit, density_kg_m3, mass_kg),
                'chart_data': self._prepare_volume_chart_data(volume_m3, density_kg_m3, mass_kg),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _convert_units(self, data):
        """Convert density units"""
        try:
            value = float(data.get('value', 0))
            from_unit = data.get('from_unit', 'kg_per_m3')
            to_unit = data.get('to_unit', 'kg_per_m3')
            
            # Validate inputs
            if not isinstance(value, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Value must be non-negative.')
                }, status=400)
            
            if value > 1e20:
                return JsonResponse({
                    'success': False,
                    'error': _('Value is too large. Please use a smaller value.')
                }, status=400)
            
            if from_unit not in self.DENSITY_CONVERSIONS or to_unit not in self.DENSITY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            # Convert to base unit (kg/m³) then to target unit using numpy
            value_kg_m3 = np.multiply(value, self.DENSITY_CONVERSIONS.get(from_unit, 1.0))
            conversion_factor = np.divide(
                self.DENSITY_CONVERSIONS.get('kg_per_m3', 1.0),
                self.DENSITY_CONVERSIONS.get(to_unit, 1.0)
            )
            result = np.multiply(value_kg_m3, conversion_factor)
            
            # Convert numpy scalar to Python float
            result = float(result)
            
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
                'from_unit_formatted': self._format_unit(from_unit),
                'to_unit': to_unit,
                'to_unit_formatted': self._format_unit(to_unit),
                'result': result,
                'step_by_step': self._prepare_convert_steps(value, from_unit, to_unit, result),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _prepare_density_steps(self, mass, mass_unit, volume, volume_unit, density, density_unit, mass_kg, volume_m3):
        """Prepare step-by-step for density calculation using sympy for formula display"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Mass: {mass} {unit}').format(mass=mass, unit=mass_unit))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=volume_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Mass in kg: {mass} kg').format(mass=mass_kg))
        steps.append(_('Volume in m³: {volume} m³').format(volume=volume_m3))
        steps.append('')
        steps.append(_('Step 3: Apply the density formula'))
        # Use sympy to display the formula symbolically
        try:
            rho, m, V = symbols('rho m V')
            formula = Eq(rho, m / V)
            formula_str = latex(formula)
            steps.append(_('Formula: ρ = m / V'))
            steps.append(_('Where: ρ = Density, m = Mass, V = Volume'))
        except:
            steps.append(_('Formula: Density = Mass ÷ Volume'))
        steps.append(_('Density = Mass ÷ Volume'))
        steps.append(_('Density = {mass} kg ÷ {volume} m³').format(mass=mass_kg, volume=volume_m3))
        steps.append(_('Density = {density} kg/m³').format(density=mass_kg / volume_m3))
        steps.append('')
        steps.append(_('Step 4: Convert to desired unit'))
        steps.append(_('Density = {density} {unit}').format(density=density, unit=density_unit))
        return steps
    
    def _prepare_mass_steps(self, density, density_unit, volume, volume_unit, mass, mass_unit, density_kg_m3, volume_m3):
        """Prepare step-by-step for mass calculation using sympy for formula display"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Density: {density} {unit}').format(density=density, unit=density_unit))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=volume_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Density in kg/m³: {density} kg/m³').format(density=density_kg_m3))
        steps.append(_('Volume in m³: {volume} m³').format(volume=volume_m3))
        steps.append('')
        steps.append(_('Step 3: Apply the mass formula'))
        # Use sympy to display the formula symbolically
        try:
            rho, m, V = symbols('rho m V')
            formula = Eq(m, rho * V)
            formula_str = latex(formula)
            steps.append(_('Formula: m = ρ × V'))
            steps.append(_('Where: m = Mass, ρ = Density, V = Volume'))
        except:
            steps.append(_('Formula: Mass = Density × Volume'))
        steps.append(_('Mass = Density × Volume'))
        steps.append(_('Mass = {density} kg/m³ × {volume} m³').format(density=density_kg_m3, volume=volume_m3))
        steps.append(_('Mass = {mass} kg').format(mass=density_kg_m3 * volume_m3))
        steps.append('')
        steps.append(_('Step 4: Convert to desired unit'))
        steps.append(_('Mass = {mass} {unit}').format(mass=mass, unit=mass_unit))
        return steps
    
    def _prepare_volume_steps(self, density, density_unit, mass, mass_unit, volume, volume_unit, density_kg_m3, mass_kg):
        """Prepare step-by-step for volume calculation using sympy for formula display"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Density: {density} {unit}').format(density=density, unit=density_unit))
        steps.append(_('Mass: {mass} {unit}').format(mass=mass, unit=mass_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Density in kg/m³: {density} kg/m³').format(density=density_kg_m3))
        steps.append(_('Mass in kg: {mass} kg').format(mass=mass_kg))
        steps.append('')
        steps.append(_('Step 3: Apply the volume formula'))
        # Use sympy to display the formula symbolically
        try:
            rho, m, V = symbols('rho m V')
            formula = Eq(V, m / rho)
            formula_str = latex(formula)
            steps.append(_('Formula: V = m / ρ'))
            steps.append(_('Where: V = Volume, m = Mass, ρ = Density'))
        except:
            steps.append(_('Formula: Volume = Mass ÷ Density'))
        steps.append(_('Volume = Mass ÷ Density'))
        steps.append(_('Volume = {mass} kg ÷ {density} kg/m³').format(mass=mass_kg, density=density_kg_m3))
        steps.append(_('Volume = {volume} m³').format(volume=mass_kg / density_kg_m3))
        steps.append('')
        steps.append(_('Step 4: Convert to desired unit'))
        steps.append(_('Volume = {volume} {unit}').format(volume=volume, unit=volume_unit))
        return steps
    
    def _prepare_convert_steps(self, value, from_unit, to_unit, result):
        """Prepare step-by-step for unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Value: {value} {unit}').format(value=value, unit=from_unit.replace('_', '/').replace('per', '/')))
        steps.append('')
        steps.append(_('Step 2: Convert to base unit (kg/m³)'))
        from_factor = self.DENSITY_CONVERSIONS.get(from_unit, 1.0)
        value_kg_m3 = value * from_factor
        steps.append(_('Conversion factor for {unit}: {factor}').format(unit=from_unit.replace('_', '/').replace('per', '/'), factor=from_factor))
        steps.append(_('Value in kg/m³ = {value} × {factor} = {result} kg/m³').format(value=value, factor=from_factor, result=value_kg_m3))
        steps.append('')
        steps.append(_('Step 3: Convert to target unit'))
        to_factor = self.DENSITY_CONVERSIONS.get(to_unit, 1.0)
        conversion_factor = 1.0 / to_factor
        steps.append(_('Conversion factor for {unit}: {factor}').format(unit=to_unit.replace('_', '/').replace('per', '/'), factor=to_factor))
        steps.append(_('Result = {value} kg/m³ ÷ {factor} = {result}').format(value=value_kg_m3, factor=to_factor, result=result))
        steps.append('')
        steps.append(_('Step 4: Final Result'))
        steps.append(_('Result: {result} {unit}').format(result=result, unit=to_unit.replace('_', '/').replace('per', '/')))
        return steps
    
    def _prepare_density_chart_data(self, density_kg_m3):
        """Prepare chart data for density using numpy for array operations"""
        # Common material densities for comparison (kg/m³)
        materials = np.array([
            _('Water'),
            _('Air'),
            _('Iron'),
            _('Aluminum'),
            _('Gold'),
            _('Calculated')
        ])
        
        densities = np.array([1000, 1.225, 7870, 2700, 19300, density_kg_m3])
        
        # Use numpy to ensure all values are finite
        densities = np.where(np.isfinite(densities), densities, 0)
        
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': materials.tolist(),
                'datasets': [{
                    'label': _('Density (kg/m³)'),
                    'data': densities.tolist(),
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(236, 72, 153, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    'borderColor': [
                        '#3b82f6',
                        '#10b981',
                        '#fbbf24',
                        '#8b5cf6',
                        '#ec4899',
                        '#ef4444'
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
                        'text': _('Density Comparison')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }
        
        return {'density_chart': chart_config}
    
    def _prepare_mass_chart_data(self, mass_kg, density_kg_m3, volume_m3):
        """Prepare chart data for mass calculation"""
        # Create a pie chart showing the relationship
        chart_config = {
            'type': 'doughnut',
            'data': {
                'labels': [
                    _('Mass (kg)'),
                    _('Density (kg/m³)'),
                    _('Volume (m³)')
                ],
                'datasets': [{
                    'data': [
                        mass_kg,
                        density_kg_m3 / 1000,  # Normalize for visualization
                        volume_m3 * 1000  # Normalize for visualization
                    ],
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
                        'text': _('Mass Calculation Breakdown')
                    }
                }
            }
        }
        
        return {'mass_chart': chart_config}
    
    def _prepare_volume_chart_data(self, volume_m3, density_kg_m3, mass_kg):
        """Prepare chart data for volume calculation"""
        # Create a pie chart showing the relationship
        chart_config = {
            'type': 'doughnut',
            'data': {
                'labels': [
                    _('Volume (m³)'),
                    _('Density (kg/m³)'),
                    _('Mass (kg)')
                ],
                'datasets': [{
                    'data': [
                        volume_m3 * 1000,  # Normalize for visualization
                        density_kg_m3 / 1000,  # Normalize for visualization
                        mass_kg
                    ],
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
                        'text': _('Volume Calculation Breakdown')
                    }
                }
            }
        }
        
        return {'volume_chart': chart_config}
