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
class WeightCalculator(View):
    """
    Professional Weight Calculator with Comprehensive Features
    
    This calculator provides weight calculations with:
    - Convert between weight units (kg, lbs, oz, grams, stones, etc.)
    - Calculate weight from mass and gravity
    - Calculate mass from weight and gravity
    - Calculate weight on different planets
    - Compare weights in different units
    
    Features:
    - Supports multiple calculation modes
    - Handles various weight units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/weight_calculator.html'
    
    # Weight unit conversions (to kilograms)
    WEIGHT_UNITS = {
        'kg': 1.0,  # kilogram (base unit)
        'g': 0.001,  # gram
        'mg': 0.000001,  # milligram
        'lb': 0.453592,  # pound
        'oz': 0.0283495,  # ounce
        'st': 6.35029,  # stone
        't': 1000.0,  # metric ton
        'ton': 907.185,  # US ton
        'ct': 0.0002,  # carat
    }
    
    # Gravitational acceleration (m/s²)
    GRAVITY = {
        'earth': 9.80665,  # Standard gravity
        'moon': 1.625,  # Moon
        'mars': 3.711,  # Mars
        'jupiter': 24.79,  # Jupiter
        'saturn': 10.44,  # Saturn
        'venus': 8.87,  # Venus
        'mercury': 3.7,  # Mercury
        'neptune': 11.15,  # Neptune
        'uranus': 8.87,  # Uranus
        'sun': 274.0,  # Sun
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Weight Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'convert')
            
            if calc_type == 'convert':
                return self._convert_weight(data)
            elif calc_type == 'from_mass':
                return self._calculate_from_mass(data)
            elif calc_type == 'from_weight':
                return self._calculate_from_weight(data)
            elif calc_type == 'planet':
                return self._calculate_planet_weight(data)
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
    
    def _convert_weight(self, data):
        """Convert weight between different units"""
        try:
            if 'weight' not in data or data.get('weight') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight is required.')
                }, status=400)
            
            if 'from_unit' not in data:
                return JsonResponse({
                    'success': False,
                    'error': _('Source unit is required.')
                }, status=400)
            
            if 'to_unit' not in data:
                return JsonResponse({
                    'success': False,
                    'error': _('Target unit is required.')
                }, status=400)
            
            try:
                weight = float(data.get('weight', 0))
                from_unit = data.get('from_unit', 'kg')
                to_unit = data.get('to_unit', 'lb')
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validation
            if weight < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight must be non-negative.')
                }, status=400)
            
            if from_unit not in self.WEIGHT_UNITS or to_unit not in self.WEIGHT_UNITS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            # Convert to base unit (kg) first
            weight_in_kg = weight * self.WEIGHT_UNITS[from_unit]
            
            # Convert to target unit
            result = weight_in_kg / self.WEIGHT_UNITS[to_unit]
            
            steps = self._prepare_convert_steps(weight, from_unit, to_unit, weight_in_kg, result)
            chart_data = self._prepare_convert_chart_data(weight, result, from_unit, to_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'weight': weight,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': round(result, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting weight: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_from_mass(self, data):
        """Calculate weight from mass and gravity"""
        try:
            if 'mass' not in data or data.get('mass') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass is required.')
                }, status=400)
            
            try:
                mass = float(data.get('mass', 0))  # kg
                gravity = float(data.get('gravity', 9.80665))  # m/s²
                mass_unit = data.get('mass_unit', 'kg')
                weight_unit = data.get('weight_unit', 'N')  # Newtons
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Convert mass to kg if needed
            if mass_unit in self.WEIGHT_UNITS:
                mass_in_kg = mass * self.WEIGHT_UNITS[mass_unit]
            else:
                mass_in_kg = mass
            
            # Validation
            if mass_in_kg <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass must be greater than zero.')
                }, status=400)
            
            if gravity <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Gravity must be greater than zero.')
                }, status=400)
            
            # Calculate weight in Newtons (F = m × g)
            weight_newtons = mass_in_kg * gravity
            
            # Convert to requested unit if needed
            if weight_unit == 'N':
                weight_result = weight_newtons
            elif weight_unit == 'lb':
                # Convert Newtons to pounds (1 N = 0.224809 lb)
                weight_result = weight_newtons * 0.224809
            elif weight_unit == 'kg':
                # Convert Newtons to kg-force (1 N = 0.101972 kg)
                weight_result = weight_newtons * 0.101972
            else:
                weight_result = weight_newtons
            
            steps = self._prepare_from_mass_steps(mass, mass_unit, mass_in_kg, gravity, weight_newtons, weight_unit, weight_result)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'from_mass',
                'mass': mass,
                'mass_unit': mass_unit,
                'gravity': gravity,
                'weight_newtons': round(weight_newtons, 2),
                'weight_result': round(weight_result, 6),
                'weight_unit': weight_unit,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating from mass: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_from_weight(self, data):
        """Calculate mass from weight and gravity"""
        try:
            if 'weight' not in data or data.get('weight') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight is required.')
                }, status=400)
            
            try:
                weight = float(data.get('weight', 0))  # Newtons
                gravity = float(data.get('gravity', 9.80665))  # m/s²
                weight_unit = data.get('weight_unit', 'N')
                mass_unit = data.get('mass_unit', 'kg')
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Convert weight to Newtons if needed
            if weight_unit == 'N':
                weight_newtons = weight
            elif weight_unit == 'lb':
                # Convert pounds to Newtons (1 lb = 4.44822 N)
                weight_newtons = weight * 4.44822
            elif weight_unit == 'kg':
                # Convert kg-force to Newtons (1 kg = 9.80665 N)
                weight_newtons = weight * 9.80665
            else:
                weight_newtons = weight
            
            # Validation
            if weight_newtons <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight must be greater than zero.')
                }, status=400)
            
            if gravity <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Gravity must be greater than zero.')
                }, status=400)
            
            # Calculate mass (m = F / g)
            mass_kg = weight_newtons / gravity
            
            # Convert to requested unit if needed
            if mass_unit in self.WEIGHT_UNITS:
                mass_result = mass_kg / self.WEIGHT_UNITS[mass_unit]
            else:
                mass_result = mass_kg
            
            steps = self._prepare_from_weight_steps(weight, weight_unit, weight_newtons, gravity, mass_kg, mass_unit, mass_result)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'from_weight',
                'weight': weight,
                'weight_unit': weight_unit,
                'gravity': gravity,
                'mass_kg': round(mass_kg, 6),
                'mass_result': round(mass_result, 6),
                'mass_unit': mass_unit,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating from weight: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_planet_weight(self, data):
        """Calculate weight on different planets"""
        try:
            if 'weight_earth' not in data or data.get('weight_earth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight on Earth is required.')
                }, status=400)
            
            try:
                weight_earth = float(data.get('weight_earth', 0))  # kg or lbs
                weight_unit = data.get('weight_unit', 'kg')
                planet = data.get('planet', 'moon')
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validation
            if weight_earth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight must be greater than zero.')
                }, status=400)
            
            if planet not in self.GRAVITY:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid planet.')
                }, status=400)
            
            # Convert weight to kg if needed
            if weight_unit in self.WEIGHT_UNITS:
                mass_kg = weight_earth * self.WEIGHT_UNITS[weight_unit]
            else:
                mass_kg = weight_earth
            
            # Calculate weight on selected planet
            gravity_earth = self.GRAVITY['earth']
            gravity_planet = self.GRAVITY[planet]
            
            # Weight = mass × gravity, so weight_planet = weight_earth × (gravity_planet / gravity_earth)
            weight_planet = weight_earth * (gravity_planet / gravity_earth)
            
            # Convert back to requested unit if needed
            if weight_unit in self.WEIGHT_UNITS:
                weight_planet_result = weight_planet
            else:
                weight_planet_result = weight_planet
            
            # Calculate all planets for comparison
            planet_weights = {}
            for p, g in self.GRAVITY.items():
                planet_weights[p] = round(weight_earth * (g / gravity_earth), 2)
            
            steps = self._prepare_planet_steps(weight_earth, weight_unit, mass_kg, planet, gravity_earth, gravity_planet, weight_planet, planet_weights)
            chart_data = self._prepare_planet_chart_data(planet_weights, weight_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'planet',
                'weight_earth': weight_earth,
                'weight_unit': weight_unit,
                'planet': planet,
                'weight_planet': round(weight_planet_result, 2),
                'gravity_ratio': round(gravity_planet / gravity_earth, 4),
                'planet_weights': planet_weights,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating planet weight: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_convert_steps(self, weight, from_unit, to_unit, weight_in_kg, result):
        """Prepare step-by-step solution for weight conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Weight: {weight} {unit}').format(weight=weight, unit=from_unit))
        steps.append(_('Convert to: {unit}').format(unit=to_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to base unit (kilograms)'))
        steps.append(_('Conversion factor: 1 {from_unit} = {factor} kg').format(from_unit=from_unit, factor=self.WEIGHT_UNITS[from_unit]))
        steps.append(_('Weight in kg = {weight} × {factor} = {kg} kg').format(weight=weight, factor=self.WEIGHT_UNITS[from_unit], kg=round(weight_in_kg, 6)))
        steps.append('')
        steps.append(_('Step 3: Convert to target unit'))
        steps.append(_('Conversion factor: 1 {to_unit} = {factor} kg').format(to_unit=to_unit, factor=self.WEIGHT_UNITS[to_unit]))
        steps.append(_('Result = {kg} / {factor} = {result} {unit}').format(kg=round(weight_in_kg, 6), factor=self.WEIGHT_UNITS[to_unit], result=round(result, 6), unit=to_unit))
        return steps
    
    def _prepare_from_mass_steps(self, mass, mass_unit, mass_in_kg, gravity, weight_newtons, weight_unit, weight_result):
        """Prepare step-by-step solution for weight from mass"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Mass: {mass} {unit}').format(mass=mass, unit=mass_unit))
        steps.append(_('Gravity: {gravity} m/s²').format(gravity=gravity))
        steps.append('')
        steps.append(_('Step 2: Convert mass to kilograms'))
        if mass_unit != 'kg':
            steps.append(_('Mass in kg = {mass} × {factor} = {kg} kg').format(mass=mass, factor=self.WEIGHT_UNITS.get(mass_unit, 1), kg=round(mass_in_kg, 6)))
        else:
            steps.append(_('Mass in kg = {kg} kg').format(kg=round(mass_in_kg, 6)))
        steps.append('')
        steps.append(_('Step 3: Calculate weight'))
        steps.append(_('Weight = Mass × Gravity'))
        steps.append(_('Weight = {mass} × {gravity} = {weight} N').format(mass=round(mass_in_kg, 6), gravity=gravity, weight=round(weight_newtons, 2)))
        if weight_unit != 'N':
            steps.append(_('Converted to {unit}: {result} {unit}').format(unit=weight_unit, result=round(weight_result, 6)))
        return steps
    
    def _prepare_from_weight_steps(self, weight, weight_unit, weight_newtons, gravity, mass_kg, mass_unit, mass_result):
        """Prepare step-by-step solution for mass from weight"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Weight: {weight} {unit}').format(weight=weight, unit=weight_unit))
        steps.append(_('Gravity: {gravity} m/s²').format(gravity=gravity))
        steps.append('')
        steps.append(_('Step 2: Convert weight to Newtons'))
        if weight_unit != 'N':
            steps.append(_('Weight in N = {weight} × {factor} = {newtons} N').format(weight=weight, factor=4.44822 if weight_unit == 'lb' else 9.80665, newtons=round(weight_newtons, 2)))
        else:
            steps.append(_('Weight in N = {newtons} N').format(newtons=round(weight_newtons, 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate mass'))
        steps.append(_('Mass = Weight / Gravity'))
        steps.append(_('Mass = {weight} / {gravity} = {mass} kg').format(weight=round(weight_newtons, 2), gravity=gravity, mass=round(mass_kg, 6)))
        if mass_unit != 'kg':
            steps.append(_('Converted to {unit}: {result} {unit}').format(unit=mass_unit, result=round(mass_result, 6)))
        return steps
    
    def _prepare_planet_steps(self, weight_earth, weight_unit, mass_kg, planet, gravity_earth, gravity_planet, weight_planet, planet_weights):
        """Prepare step-by-step solution for planet weight"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Weight on Earth: {weight} {unit}').format(weight=weight_earth, unit=weight_unit))
        steps.append(_('Planet: {planet}').format(planet=planet.capitalize()))
        steps.append('')
        steps.append(_('Step 2: Calculate mass'))
        steps.append(_('Mass = Weight on Earth / Gravity on Earth'))
        steps.append(_('Mass = {weight} / {gravity} = {mass} kg').format(weight=weight_earth, gravity=gravity_earth, mass=round(mass_kg, 6)))
        steps.append('')
        steps.append(_('Step 3: Calculate weight on {planet}').format(planet=planet.capitalize()))
        steps.append(_('Gravity on {planet}: {gravity} m/s²').format(planet=planet.capitalize(), gravity=gravity_planet))
        steps.append(_('Weight = Mass × Gravity'))
        steps.append(_('Weight = {mass} × {gravity} = {weight} {unit}').format(mass=round(mass_kg, 6), gravity=gravity_planet, weight=round(weight_planet, 2), unit=weight_unit))
        steps.append('')
        steps.append(_('Step 4: Weight comparison'))
        for p, w in sorted(planet_weights.items(), key=lambda x: x[1], reverse=True):
            steps.append(_('{planet}: {weight} {unit}').format(planet=p.capitalize(), weight=w, unit=weight_unit))
        return steps
    
    # Chart data preparation methods
    def _prepare_convert_chart_data(self, weight, result, from_unit, to_unit):
        """Prepare chart data for weight conversion visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [f'{weight} {from_unit}', f'{round(result, 2)} {to_unit}'],
                    'datasets': [{
                        'label': _('Weight'),
                        'data': [weight, result],
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
                            'text': _('Weight Conversion')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Weight')
                            }
                        }
                    }
                }
            }
            return {'convert_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_planet_chart_data(self, planet_weights, weight_unit):
        """Prepare chart data for planet weight comparison"""
        try:
            planets = list(planet_weights.keys())
            weights = list(planet_weights.values())
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [p.capitalize() for p in planets],
                    'datasets': [{
                        'label': _('Weight ({unit})').format(unit=weight_unit),
                        'data': weights,
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
                            'text': _('Weight on Different Planets')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Weight ({unit})').format(unit=weight_unit)
                            }
                        }
                    }
                }
            }
            return {'planet_chart': chart_config}
        except Exception as e:
            return None
