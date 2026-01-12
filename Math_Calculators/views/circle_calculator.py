from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import pi, N
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CircleCalculator(View):
    """
    Professional Circle Calculator with comprehensive circle calculations
    Calculates circle properties (area, circumference, diameter, radius) from any given value.
    Includes chart data preparation and enhanced visualizations.
    """
    template_name = 'math_calculators/circle_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Circle Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0:
                return None, f'{name} must be greater than zero.'
            if num > 1e10:  # Prevent extremely large numbers
                return None, f'{name} is too large. Maximum value is 10,000,000,000.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_from_radius(self, radius):
        """Calculate all circle properties from radius"""
        area = float(N(pi * radius**2, 15))
        circumference = float(N(2 * pi * radius, 15))
        diameter = 2 * radius
        
        return {
            'radius': radius,
            'diameter': diameter,
            'circumference': circumference,
            'area': area,
            'input_type': 'radius'
        }
    
    def _calculate_from_diameter(self, diameter):
        """Calculate all circle properties from diameter"""
        radius = diameter / 2
        area = float(N(pi * radius**2, 15))
        circumference = float(N(2 * pi * radius, 15))
        
        return {
            'radius': radius,
            'diameter': diameter,
            'circumference': circumference,
            'area': area,
            'input_type': 'diameter'
        }
    
    def _calculate_from_circumference(self, circumference):
        """Calculate all circle properties from circumference"""
        radius = circumference / (2 * pi)
        diameter = 2 * radius
        area = float(N(pi * radius**2, 15))
        
        return {
            'radius': radius,
            'diameter': diameter,
            'circumference': circumference,
            'area': area,
            'input_type': 'circumference'
        }
    
    def _calculate_from_area(self, area):
        """Calculate all circle properties from area"""
        radius = float(N(math.sqrt(area / pi), 15))
        diameter = 2 * radius
        circumference = float(N(2 * pi * radius, 15))
        
        return {
            'radius': radius,
            'diameter': diameter,
            'circumference': circumference,
            'area': area,
            'input_type': 'area'
        }
    
    def prepare_circle_visualization(self, result, unit):
        """Prepare circle visualization data with SVG"""
        radius = result.get('radius', 5)
        diameter = result.get('diameter', 10)
        area = result.get('area', 0)
        
        svg_size = 400
        center_x = svg_size / 2
        center_y = svg_size / 2
        
        def format_num(num):
            """Format number for display"""
            if not isinstance(num, (int, float)) or math.isnan(num) or math.isinf(num):
                return '0'
            return f"{num:.2f}".rstrip('0').rstrip('.')
        
        # Scale circle to fit in SVG (leave space for labels)
        max_radius = min(150, svg_size / 2 - 50)
        scale = min(max_radius / radius, 30) if radius > 0 else 1
        r = radius * scale
        
        visualization_data = {
            'svg_size': svg_size,
            'center_x': center_x,
            'center_y': center_y,
            'unit': unit,
            'area': area,
            'area_unit': f'{unit}²',
            'elements': [],
            'labels': []
        }
        
        # Draw circle
        visualization_data['elements'].append({
            'type': 'circle',
            'cx': center_x, 'cy': center_y, 'r': r,
            'fill': 'rgba(59, 130, 246, 0.2)',
            'stroke': '#3b82f6',
            'stroke_width': 3
        })
        
        # Draw radius line
        visualization_data['elements'].append({
            'type': 'line',
            'x1': center_x, 'y1': center_y, 'x2': center_x + r, 'y2': center_y,
            'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'
        })
        
        # Draw diameter line
        visualization_data['elements'].append({
            'type': 'line',
            'x1': center_x - r, 'y1': center_y, 'x2': center_x + r, 'y2': center_y,
            'stroke': '#10b981', 'stroke_width': 2, 'stroke_dasharray': '3,3'
        })
        
        # Draw center point
        visualization_data['elements'].append({
            'type': 'circle',
            'cx': center_x, 'cy': center_y, 'r': 3,
            'fill': '#ef4444', 'stroke': '#dc2626', 'stroke_width': 1
        })
        
        # Labels
        visualization_data['labels'].extend([
            {'x': center_x + r/2, 'y': center_y - 10, 'text': f'r = {format_num(radius)} {unit}', 'anchor': 'middle'},
            {'x': center_x, 'y': center_y + r + 30, 'text': f'd = {format_num(diameter)} {unit}', 'anchor': 'middle'},
            {'x': center_x, 'y': center_y - r - 20, 'text': f'A = {format_num(area)} {unit}²', 'anchor': 'middle'}
        ])
        
        return visualization_data
    
    def prepare_chart_data(self, result, unit):
        """Prepare comprehensive chart data for visualizations"""
        radius = result.get('radius', 0)
        diameter = result.get('diameter', 0)
        circumference = result.get('circumference', 0)
        area = result.get('area', 0)
        
        # Validate values
        if not isinstance(area, (int, float)) or math.isnan(area) or math.isinf(area) or area < 0:
            area = 0
        
        # Area Gauge Chart (Doughnut)
        if area == 0:
            max_area_for_gauge = 100
            area_percentage = 0
        else:
            max_area_for_gauge = area * 1.5
            area_percentage = min((area / max_area_for_gauge) * 100, 100)
        
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Area', 'Remaining'],
                'datasets': [{
                    'data': [round(area_percentage, 2), round(100 - area_percentage, 2)],
                    'backgroundColor': ['#3b82f6', '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(area, 2),
                'label': f'Area ({unit}²)',
                'color': '#3b82f6'
            }
        }
        
        # Properties Comparison Chart
        properties_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Radius', 'Diameter', 'Circumference', 'Area'],
                'datasets': [{
                    'label': f'Measurements ({unit})',
                    'data': [
                        round(radius, 2),
                        round(diameter, 2),
                        round(circumference, 2),
                        round(area, 2)
                    ],
                    'backgroundColor': ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6'],
                    'borderColor': ['#2563eb', '#059669', '#d97706', '#7c3aed'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Relationship Chart (showing mathematical relationships)
        relationship_data = {
            'type': 'line',
            'data': {
                'labels': ['Radius', 'Diameter', 'Circumference', 'Area'],
                'datasets': [
                    {
                        'label': 'Value',
                        'data': [radius, diameter, circumference, area],
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 3,
                        'fill': True,
                        'tension': 0.4,
                        'pointRadius': 6,
                        'pointBackgroundColor': '#3b82f6'
                    }
                ]
            }
        }
        
        return {
            'gauge_chart': gauge_chart,
            'properties_chart': properties_chart,
            'relationship_chart': relationship_data
        }
    
    def prepare_display_data(self, result, unit):
        """Prepare formatted display data for frontend"""
        def format_number(num, decimals=6):
            """Format number for display"""
            if not isinstance(num, (int, float)) or math.isnan(num) or math.isinf(num):
                return '0'
            formatted = f"{num:.{decimals}f}".rstrip('0').rstrip('.')
            # Add thousand separators for large numbers
            try:
                num_val = float(formatted)
                if num_val >= 1000:
                    return f"{num_val:,.{decimals}f}".rstrip('0').rstrip('.')
            except:
                pass
            return formatted
        
        display_data = {
            'radius_formatted': format_number(result.get('radius', 0)),
            'diameter_formatted': format_number(result.get('diameter', 0)),
            'circumference_formatted': format_number(result.get('circumference', 0)),
            'area_formatted': format_number(result.get('area', 0)),
            'area_formatted_short': format_number(result.get('area', 0), 2),
            'detailed_results': [],
            'input_type': result.get('input_type', 'radius')
        }
        
        # Add all properties
        display_data['detailed_results'].extend([
            {
                'label': 'Radius',
                'value': format_number(result.get('radius', 0)),
                'unit': unit,
                'is_primary': result.get('input_type') == 'radius',
                'formula': 'r = d/2 = C/(2π) = √(A/π)'
            },
            {
                'label': 'Diameter',
                'value': format_number(result.get('diameter', 0)),
                'unit': unit,
                'is_primary': result.get('input_type') == 'diameter',
                'formula': 'd = 2r = C/π = 2√(A/π)'
            },
            {
                'label': 'Circumference',
                'value': format_number(result.get('circumference', 0)),
                'unit': unit,
                'is_primary': result.get('input_type') == 'circumference',
                'formula': 'C = 2πr = πd = 2√(πA)'
            },
            {
                'label': 'Area',
                'value': format_number(result.get('area', 0)),
                'unit': f'{unit}²',
                'is_primary': result.get('input_type') == 'area',
                'formula': 'A = πr² = π(d/2)² = C²/(4π)'
            }
        ])
        
        return display_data
    
    def prepare_step_by_step(self, result, input_value, input_type, unit):
        """Prepare step-by-step solution"""
        steps = []
        
        radius = result.get('radius', 0)
        diameter = result.get('diameter', 0)
        circumference = result.get('circumference', 0)
        area = result.get('area', 0)
        
        if input_type == 'radius':
            steps.append(f"Given: Radius (r) = {input_value} {unit}")
            steps.append(f"Step 1: Calculate diameter")
            steps.append(f"  d = 2 × r = 2 × {input_value} = {diameter:.6f} {unit}")
            steps.append(f"Step 2: Calculate circumference")
            steps.append(f"  C = 2πr = 2 × π × {input_value}")
            steps.append(f"  C = 2 × {pi.evalf(10)} × {input_value} = {circumference:.6f} {unit}")
            steps.append(f"Step 3: Calculate area")
            steps.append(f"  A = πr² = π × {input_value}²")
            steps.append(f"  A = {pi.evalf(10)} × {input_value**2} = {area:.6f} {unit}²")
        
        elif input_type == 'diameter':
            steps.append(f"Given: Diameter (d) = {input_value} {unit}")
            steps.append(f"Step 1: Calculate radius")
            steps.append(f"  r = d/2 = {input_value}/2 = {radius:.6f} {unit}")
            steps.append(f"Step 2: Calculate circumference")
            steps.append(f"  C = πd = π × {input_value}")
            steps.append(f"  C = {pi.evalf(10)} × {input_value} = {circumference:.6f} {unit}")
            steps.append(f"Step 3: Calculate area")
            steps.append(f"  A = πr² = π × ({radius:.6f})²")
            steps.append(f"  A = {pi.evalf(10)} × {radius**2} = {area:.6f} {unit}²")
        
        elif input_type == 'circumference':
            steps.append(f"Given: Circumference (C) = {input_value} {unit}")
            steps.append(f"Step 1: Calculate radius")
            steps.append(f"  r = C/(2π) = {input_value}/(2 × π)")
            steps.append(f"  r = {input_value}/(2 × {pi.evalf(10)}) = {radius:.6f} {unit}")
            steps.append(f"Step 2: Calculate diameter")
            steps.append(f"  d = 2r = 2 × {radius:.6f} = {diameter:.6f} {unit}")
            steps.append(f"Step 3: Calculate area")
            steps.append(f"  A = πr² = π × ({radius:.6f})²")
            steps.append(f"  A = {pi.evalf(10)} × {radius**2} = {area:.6f} {unit}²")
        
        elif input_type == 'area':
            steps.append(f"Given: Area (A) = {input_value} {unit}²")
            steps.append(f"Step 1: Calculate radius")
            steps.append(f"  r = √(A/π) = √({input_value}/π)")
            steps.append(f"  r = √({input_value}/{pi.evalf(10)}) = {radius:.6f} {unit}")
            steps.append(f"Step 2: Calculate diameter")
            steps.append(f"  d = 2r = 2 × {radius:.6f} = {diameter:.6f} {unit}")
            steps.append(f"Step 3: Calculate circumference")
            steps.append(f"  C = 2πr = 2 × π × {radius:.6f}")
            steps.append(f"  C = 2 × {pi.evalf(10)} × {radius:.6f} = {circumference:.6f} {unit}")
        
        return steps
    
    def prepare_step_by_step_html(self, steps):
        """Prepare step-by-step solution as HTML structure"""
        if not steps or not isinstance(steps, list):
            return []
        
        return [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(steps)]
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            input_type = data.get('input_type', 'radius')
            input_value = data.get('input_value', '0')
            unit = data.get('unit', 'm')
            
            # Validate input value
            input_value_num, error = self._validate_positive_number(input_value, 'Input value')
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate based on input type
            calculators = {
                'radius': self._calculate_from_radius,
                'diameter': self._calculate_from_diameter,
                'circumference': self._calculate_from_circumference,
                'area': self._calculate_from_area
            }
            
            if input_type not in calculators:
                return JsonResponse({'success': False, 'error': 'Invalid input type. Please select radius, diameter, circumference, or area.'}, status=400)
            
            result = calculators[input_type](input_value_num)
            
            # Validate result
            if 'area' not in result or result.get('area') is None:
                return JsonResponse({'success': False, 'error': 'Calculation failed: No area result.'}, status=500)
            
            # Prepare chart data
            try:
                chart_data = self.prepare_chart_data(result, unit)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare circle visualization data
            try:
                circle_visualization = self.prepare_circle_visualization(result, unit)
            except Exception as viz_error:
                import traceback
                print(f"Circle visualization preparation error: {traceback.format_exc()}")
                circle_visualization = {}
            
            # Prepare formatted display data
            display_data = self.prepare_display_data(result, unit)
            
            # Prepare step-by-step solution
            step_by_step = self.prepare_step_by_step(result, input_value_num, input_type, unit)
            step_by_step_html = self.prepare_step_by_step_html(step_by_step)
            
            # Enhance result with all prepared data
            result['success'] = True
            result['unit'] = unit
            result['area_unit'] = f'{unit}²'
            result['chart_data'] = chart_data
            result['circle_visualization'] = circle_visualization
            result['display_data'] = display_data
            result['step_by_step'] = step_by_step
            result['step_by_step_html'] = step_by_step_html
            result['input_value'] = input_value_num
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}. Please check your input value.'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Circle Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
