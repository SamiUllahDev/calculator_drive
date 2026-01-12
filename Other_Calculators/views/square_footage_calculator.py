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
class SquareFootageCalculator(View):
    """
    Professional Square Footage Calculator with Comprehensive Features
    
    This calculator provides area calculations with:
    - Calculate area for different shapes (rectangle, square, circle, triangle, etc.)
    - Unit conversions (square feet, square meters, square yards, etc.)
    - Multiple shape support
    - Step-by-step solutions
    
    Features:
    - Supports multiple shapes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/square_footage_calculator.html'
    
    # Area conversion factors (to square meters)
    AREA_CONVERSIONS = {
        'square_meters': 1.0,
        'square_feet': 0.092903,  # 1 ft² = 0.092903 m²
        'square_yards': 0.836127,  # 1 yd² = 0.836127 m²
        'square_inches': 0.00064516,  # 1 in² = 0.00064516 m²
        'acres': 4046.86,  # 1 acre = 4046.86 m²
        'hectares': 10000.0,  # 1 hectare = 10000 m²
    }
    
    # Length conversion factors (to meters)
    LENGTH_CONVERSIONS = {
        'meters': 1.0,
        'feet': 0.3048,  # 1 ft = 0.3048 m
        'inches': 0.0254,  # 1 in = 0.0254 m
        'yards': 0.9144,  # 1 yd = 0.9144 m
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'square_meters': 'm²',
            'square_feet': 'ft²',
            'square_yards': 'yd²',
            'square_inches': 'in²',
            'acres': 'acres',
            'hectares': 'hectares',
            'meters': 'm',
            'feet': 'ft',
            'inches': 'in',
            'yards': 'yd',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Square Footage Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            shape = data.get('shape', 'rectangle')
            
            if shape == 'rectangle':
                return self._calculate_rectangle(data)
            elif shape == 'square':
                return self._calculate_square(data)
            elif shape == 'circle':
                return self._calculate_circle(data)
            elif shape == 'triangle':
                return self._calculate_triangle(data)
            elif shape == 'trapezoid':
                return self._calculate_trapezoid(data)
            elif shape == 'ellipse':
                return self._calculate_ellipse(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid shape.')
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
    
    def _calculate_rectangle(self, data):
        """Calculate area of rectangle"""
        try:
            if 'length' not in data or data.get('length') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Length is required.')
                }, status=400)
            
            if 'width' not in data or data.get('width') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Width is required.')
                }, status=400)
            
            try:
                length = float(data.get('length', 0))
                width = float(data.get('width', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if length <= 0 or width <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Length and width must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            length_m = float(length * self.LENGTH_CONVERSIONS[length_unit])
            width_m = float(width * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate area in square meters
            area_m2 = float(np.multiply(length_m, width_m))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            steps = self._prepare_rectangle_steps(length, length_unit, width, length_m, width_m, area_m2, result, result_unit)
            chart_data = self._prepare_area_chart_data(area_m2, result_unit, 'Rectangle')
            
            return JsonResponse({
                'success': True,
                'shape': 'rectangle',
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating rectangle area: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_square(self, data):
        """Calculate area of square"""
        try:
            if 'side' not in data or data.get('side') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Side length is required.')
                }, status=400)
            
            try:
                side = float(data.get('side', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if side <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Side length must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            side_m = float(side * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate area in square meters
            area_m2 = float(np.multiply(side_m, side_m))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            steps = self._prepare_square_steps(side, length_unit, side_m, area_m2, result, result_unit)
            chart_data = self._prepare_area_chart_data(area_m2, result_unit, 'Square')
            
            return JsonResponse({
                'success': True,
                'shape': 'square',
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating square area: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_circle(self, data):
        """Calculate area of circle"""
        try:
            if 'radius' not in data or data.get('radius') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Radius is required.')
                }, status=400)
            
            try:
                radius = float(data.get('radius', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if radius <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Radius must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            radius_m = float(radius * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate area in square meters: A = π × r²
            area_m2 = float(np.multiply(np.pi, np.multiply(radius_m, radius_m)))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            steps = self._prepare_circle_steps(radius, length_unit, radius_m, area_m2, result, result_unit)
            chart_data = self._prepare_area_chart_data(area_m2, result_unit, 'Circle')
            
            return JsonResponse({
                'success': True,
                'shape': 'circle',
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating circle area: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_triangle(self, data):
        """Calculate area of triangle"""
        try:
            if 'base' not in data or data.get('base') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Base is required.')
                }, status=400)
            
            if 'height' not in data or data.get('height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Height is required.')
                }, status=400)
            
            try:
                base = float(data.get('base', 0))
                height = float(data.get('height', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if base <= 0 or height <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Base and height must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            base_m = float(base * self.LENGTH_CONVERSIONS[length_unit])
            height_m = float(height * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate area in square meters: A = (1/2) × base × height
            area_m2 = float(np.multiply(0.5, np.multiply(base_m, height_m)))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            steps = self._prepare_triangle_steps(base, length_unit, height, base_m, height_m, area_m2, result, result_unit)
            chart_data = self._prepare_area_chart_data(area_m2, result_unit, 'Triangle')
            
            return JsonResponse({
                'success': True,
                'shape': 'triangle',
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating triangle area: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_trapezoid(self, data):
        """Calculate area of trapezoid"""
        try:
            if 'base1' not in data or data.get('base1') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Base 1 is required.')
                }, status=400)
            
            if 'base2' not in data or data.get('base2') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Base 2 is required.')
                }, status=400)
            
            if 'height' not in data or data.get('height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Height is required.')
                }, status=400)
            
            try:
                base1 = float(data.get('base1', 0))
                base2 = float(data.get('base2', 0))
                height = float(data.get('height', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if base1 <= 0 or base2 <= 0 or height <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Bases and height must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            base1_m = float(base1 * self.LENGTH_CONVERSIONS[length_unit])
            base2_m = float(base2 * self.LENGTH_CONVERSIONS[length_unit])
            height_m = float(height * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate area in square meters: A = (1/2) × (base1 + base2) × height
            area_m2 = float(np.multiply(0.5, np.multiply(np.add(base1_m, base2_m), height_m)))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            steps = self._prepare_trapezoid_steps(base1, base2, length_unit, height, base1_m, base2_m, height_m, area_m2, result, result_unit)
            chart_data = self._prepare_area_chart_data(area_m2, result_unit, 'Trapezoid')
            
            return JsonResponse({
                'success': True,
                'shape': 'trapezoid',
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating trapezoid area: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_ellipse(self, data):
        """Calculate area of ellipse"""
        try:
            if 'radius_a' not in data or data.get('radius_a') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Radius A (semi-major axis) is required.')
                }, status=400)
            
            if 'radius_b' not in data or data.get('radius_b') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Radius B (semi-minor axis) is required.')
                }, status=400)
            
            try:
                radius_a = float(data.get('radius_a', 0))
                radius_b = float(data.get('radius_b', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if radius_a <= 0 or radius_b <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Radii must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            radius_a_m = float(radius_a * self.LENGTH_CONVERSIONS[length_unit])
            radius_b_m = float(radius_b * self.LENGTH_CONVERSIONS[length_unit])
            
            # Calculate area in square meters: A = π × a × b
            area_m2 = float(np.multiply(np.pi, np.multiply(radius_a_m, radius_b_m)))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            steps = self._prepare_ellipse_steps(radius_a, radius_b, length_unit, radius_a_m, radius_b_m, area_m2, result, result_unit)
            chart_data = self._prepare_area_chart_data(area_m2, result_unit, 'Ellipse')
            
            return JsonResponse({
                'success': True,
                'shape': 'ellipse',
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating ellipse area: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_rectangle_steps(self, length, length_unit, width, length_m, width_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for rectangle"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Length: {length} {unit}').format(length=length, unit=self._format_unit(length_unit)))
        steps.append(_('Width: {width} {unit}').format(width=width, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Length: {length} m').format(length=length_m))
        steps.append(_('Width: {width} m').format(width=width_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Area = Length × Width'))
        steps.append(_('Area = {length} m × {width} m').format(length=length_m, width=width_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_square_steps(self, side, length_unit, side_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for square"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Side: {side} {unit}').format(side=side, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Side: {side} m').format(side=side_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Area = Side × Side'))
        steps.append(_('Area = {side} m × {side} m').format(side=side_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_circle_steps(self, radius, length_unit, radius_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for circle"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Radius: {radius} {unit}').format(radius=radius, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Radius: {radius} m').format(radius=radius_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Area = π × r²'))
        steps.append(_('Area = π × ({radius})²').format(radius=radius_m))
        steps.append(_('Area = π × {radius_sq}').format(radius_sq=round(radius_m * radius_m, 4)))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_triangle_steps(self, base, length_unit, height, base_m, height_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for triangle"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Base: {base} {unit}').format(base=base, unit=self._format_unit(length_unit)))
        steps.append(_('Height: {height} {unit}').format(height=height, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Base: {base} m').format(base=base_m))
        steps.append(_('Height: {height} m').format(height=height_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Area = (1/2) × Base × Height'))
        steps.append(_('Area = (1/2) × {base} m × {height} m').format(base=base_m, height=height_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_trapezoid_steps(self, base1, base2, length_unit, height, base1_m, base2_m, height_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for trapezoid"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Base 1: {base1} {unit}').format(base1=base1, unit=self._format_unit(length_unit)))
        steps.append(_('Base 2: {base2} {unit}').format(base2=base2, unit=self._format_unit(length_unit)))
        steps.append(_('Height: {height} {unit}').format(height=height, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Base 1: {base1} m').format(base1=base1_m))
        steps.append(_('Base 2: {base2} m').format(base2=base2_m))
        steps.append(_('Height: {height} m').format(height=height_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Area = (1/2) × (Base 1 + Base 2) × Height'))
        steps.append(_('Area = (1/2) × ({base1} + {base2}) × {height}').format(base1=base1_m, base2=base2_m, height=height_m))
        steps.append(_('Area = (1/2) × {sum} × {height}').format(sum=base1_m + base2_m, height=height_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_ellipse_steps(self, radius_a, radius_b, length_unit, radius_a_m, radius_b_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for ellipse"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Radius A: {radius_a} {unit}').format(radius_a=radius_a, unit=self._format_unit(length_unit)))
        steps.append(_('Radius B: {radius_b} {unit}').format(radius_b=radius_b, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Radius A: {radius_a} m').format(radius_a=radius_a_m))
        steps.append(_('Radius B: {radius_b} m').format(radius_b=radius_b_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Area = π × a × b'))
        steps.append(_('Area = π × {radius_a} × {radius_b}').format(radius_a=radius_a_m, radius_b=radius_b_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_area_chart_data(self, area_m2, result_unit, shape_name):
        """Prepare chart data for area visualization"""
        try:
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Area')],
                    'datasets': [{
                        'label': _('Area ({unit})').format(unit=self._format_unit(result_unit)),
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
                            'text': _('{shape} Area Calculation').format(shape=shape_name)
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Area ({unit})').format(unit=self._format_unit(result_unit))
                            }
                        }
                    }
                }
            }
            return {'area_chart': chart_config}
        except Exception as e:
            return None
