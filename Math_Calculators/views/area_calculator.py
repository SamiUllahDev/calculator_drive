from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import pi, sqrt, N, Rational, tan, sin, cos
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AreaCalculator(View):
    """
    Professional Area Calculator with comprehensive shape support
    Calculates area of various shapes using NumPy and SymPy.
    Includes chart data preparation and enhanced visualizations.
    """
    template_name = 'math_calculators/area_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Area Calculator',
        }
        return render(request, self.template_name, context)
    
    def prepare_shape_visualization(self, result, unit):
        """Prepare shape visualization data with SVG paths and labels"""
        shape = result.get('shape', 'rectangle')
        inputs = result.get('inputs', {})
        area = result.get('area', 0)
        
        svg_size = 400
        center_x = svg_size / 2
        center_y = svg_size / 2
        
        def format_num(num):
            """Format number for display"""
            if not isinstance(num, (int, float)) or math.isnan(num) or math.isinf(num):
                return '0'
            return f"{num:.2f}".rstrip('0').rstrip('.')
        
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
        
        if shape == 'rectangle':
            length = inputs.get('length', 10)
            width = inputs.get('width', 5)
            scale = min(150 / max(length, width), 30)
            w = length * scale
            h = width * scale
            x = center_x - w/2
            y = center_y - h/2
            
            visualization_data['elements'].append({
                'type': 'rect',
                'x': x, 'y': y, 'width': w, 'height': h,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].extend([
                {'x': center_x, 'y': y - 10, 'text': f'l = {format_num(length)} {unit}', 'anchor': 'middle'},
                {'x': x - 10, 'y': center_y, 'text': f'w = {format_num(width)} {unit}', 'anchor': 'end', 'baseline': 'middle'}
            ])
            
        elif shape == 'square':
            side = inputs.get('side', 10)
            scale = min(150 / side, 30)
            s = side * scale
            x = center_x - s/2
            y = center_y - s/2
            
            visualization_data['elements'].append({
                'type': 'rect',
                'x': x, 'y': y, 'width': s, 'height': s,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].append({
                'x': center_x, 'y': y - 10, 'text': f's = {format_num(side)} {unit}', 'anchor': 'middle'
            })
            
        elif shape == 'circle':
            radius = inputs.get('radius', 5)
            scale = min(150 / (radius * 2), 30)
            r = radius * scale
            
            visualization_data['elements'].append({
                'type': 'circle',
                'cx': center_x, 'cy': center_y, 'r': r,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['elements'].append({
                'type': 'line',
                'x1': center_x, 'y1': center_y, 'x2': center_x + r, 'y2': center_y,
                'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'
            })
            visualization_data['labels'].append({
                'x': center_x + r/2, 'y': center_y - 10,
                'text': f'r = {format_num(radius)} {unit}', 'anchor': 'middle'
            })
            
        elif shape == 'triangle':
            base = inputs.get('base', 10)
            height = inputs.get('height', 8)
            scale = min(150 / max(base, height), 20)
            b = base * scale
            h = height * scale
            
            points = f"{center_x},{center_y - h/2} {center_x - b/2},{center_y + h/2} {center_x + b/2},{center_y + h/2}"
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': points,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].extend([
                {'x': center_x, 'y': center_y + h/2 + 25, 'text': f'b = {format_num(base)} {unit}', 'anchor': 'middle'},
                {'x': center_x + b/2 + 15, 'y': center_y, 'text': f'h = {format_num(height)} {unit}', 'anchor': 'start', 'baseline': 'middle'}
            ])
            
        elif shape == 'trapezoid':
            base1 = inputs.get('base1', 10)
            base2 = inputs.get('base2', 6)
            height = inputs.get('height', 5)
            scale = min(150 / max(base1, base2, height), 20)
            b1 = base1 * scale
            b2 = base2 * scale
            h = height * scale
            
            points = f"{center_x - b1/2},{center_y - h/2} {center_x + b1/2},{center_y - h/2} {center_x + b2/2},{center_y + h/2} {center_x - b2/2},{center_y + h/2}"
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': points,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].extend([
                {'x': center_x, 'y': center_y - h/2 - 10, 'text': f'a = {format_num(base1)} {unit}', 'anchor': 'middle'},
                {'x': center_x, 'y': center_y + h/2 + 25, 'text': f'b = {format_num(base2)} {unit}', 'anchor': 'middle'},
                {'x': center_x + b2/2 + 15, 'y': center_y, 'text': f'h = {format_num(height)} {unit}', 'anchor': 'start', 'baseline': 'middle'}
            ])
            
        elif shape == 'parallelogram':
            base = inputs.get('base', 10)
            height = inputs.get('height', 7)
            scale = min(150 / max(base, height), 20)
            b = base * scale
            h = height * scale
            offset = b * 0.2
            
            points = f"{center_x - b/2 + offset},{center_y - h/2} {center_x + b/2 + offset},{center_y - h/2} {center_x + b/2 - offset},{center_y + h/2} {center_x - b/2 - offset},{center_y + h/2}"
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': points,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].extend([
                {'x': center_x, 'y': center_y - h/2 - 10, 'text': f'b = {format_num(base)} {unit}', 'anchor': 'middle'},
                {'x': center_x + b/2 + offset + 15, 'y': center_y, 'text': f'h = {format_num(height)} {unit}', 'anchor': 'start', 'baseline': 'middle'}
            ])
            
        elif shape == 'rhombus':
            d1 = inputs.get('diagonal1', 10)
            d2 = inputs.get('diagonal2', 8)
            scale = min(150 / max(d1, d2), 20)
            dx = d1 * scale / 2
            dy = d2 * scale / 2
            
            points = f"{center_x},{center_y - dy} {center_x + dx},{center_y} {center_x},{center_y + dy} {center_x - dx},{center_y}"
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': points,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['elements'].extend([
                {'type': 'line', 'x1': center_x - dx, 'y1': center_y, 'x2': center_x + dx, 'y2': center_y,
                 'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'},
                {'type': 'line', 'x1': center_x, 'y1': center_y - dy, 'x2': center_x, 'y2': center_y + dy,
                 'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'}
            ])
            visualization_data['labels'].extend([
                {'x': center_x, 'y': center_y + dy + 25, 'text': f'd₁ = {format_num(d1)} {unit}', 'anchor': 'middle'},
                {'x': center_x + dx + 15, 'y': center_y, 'text': f'd₂ = {format_num(d2)} {unit}', 'anchor': 'start', 'baseline': 'middle'}
            ])
            
        elif shape == 'ellipse':
            a = inputs.get('semi_major', 8)
            b = inputs.get('semi_minor', 5)
            scale = min(150 / max(a * 2, b * 2), 20)
            rx = a * scale
            ry = b * scale
            
            visualization_data['elements'].append({
                'type': 'ellipse',
                'cx': center_x, 'cy': center_y, 'rx': rx, 'ry': ry,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].extend([
                {'x': center_x + rx, 'y': center_y - 10, 'text': f'a = {format_num(a)} {unit}', 'anchor': 'middle'},
                {'x': center_x, 'y': center_y + ry + 20, 'text': f'b = {format_num(b)} {unit}', 'anchor': 'middle'}
            ])
            
        elif shape == 'pentagon':
            side = inputs.get('side', 5)
            scale = min(150 / (side * 2), 25)
            r = side * scale * 0.85
            
            points = []
            for i in range(5):
                angle = (2 * math.pi / 5) * i - math.pi / 2
                points.append(f"{center_x + r * math.cos(angle)},{center_y + r * math.sin(angle)}")
            
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': ' '.join(points),
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].append({
                'x': center_x, 'y': center_y + r + 25,
                'text': f's = {format_num(side)} {unit}', 'anchor': 'middle'
            })
            
        elif shape == 'hexagon':
            side = inputs.get('side', 5)
            scale = min(150 / (side * 2), 25)
            r = side * scale
            
            points = []
            for i in range(6):
                angle = (math.pi / 3) * i
                points.append(f"{center_x + r * math.cos(angle)},{center_y + r * math.sin(angle)}")
            
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': ' '.join(points),
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].append({
                'x': center_x, 'y': center_y + r + 25,
                'text': f's = {format_num(side)} {unit}', 'anchor': 'middle'
            })
            
        elif shape == 'octagon':
            side = inputs.get('side', 5)
            scale = min(150 / (side * 2), 25)
            r = side * scale * 1.3
            
            points = []
            for i in range(8):
                angle = (2 * math.pi / 8) * i - math.pi / 8
                points.append(f"{center_x + r * math.cos(angle)},{center_y + r * math.sin(angle)}")
            
            visualization_data['elements'].append({
                'type': 'polygon',
                'points': ' '.join(points),
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['labels'].append({
                'x': center_x, 'y': center_y + r + 25,
                'text': f's = {format_num(side)} {unit}', 'anchor': 'middle'
            })
            
        elif shape == 'sector':
            radius = inputs.get('radius', 5)
            angle = inputs.get('angle', 60)
            scale = min(150 / (radius * 2), 30)
            r = radius * scale
            start_angle = -math.pi / 2
            end_angle = start_angle + math.radians(angle)
            
            x1 = center_x + r * math.cos(start_angle)
            y1 = center_y + r * math.sin(start_angle)
            x2 = center_x + r * math.cos(end_angle)
            y2 = center_y + r * math.sin(end_angle)
            large_arc = 1 if angle > 180 else 0
            
            path_d = f"M {center_x} {center_y} L {x1} {y1} A {r} {r} 0 {large_arc} 1 {x2} {y2} Z"
            visualization_data['elements'].append({
                'type': 'path',
                'd': path_d,
                'fill': 'rgba(59, 130, 246, 0.2)',
                'stroke': '#3b82f6',
                'stroke_width': 3
            })
            visualization_data['elements'].append({
                'type': 'line',
                'x1': center_x, 'y1': center_y, 'x2': x2, 'y2': y2,
                'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'
            })
            visualization_data['labels'].extend([
                {'x': center_x + r/2 * math.cos((start_angle + end_angle)/2),
                 'y': center_y + r/2 * math.sin((start_angle + end_angle)/2) - 10,
                 'text': f'r = {format_num(radius)} {unit}', 'anchor': 'middle'},
                {'x': center_x, 'y': center_y + r + 25,
                 'text': f'θ = {format_num(angle)}°', 'anchor': 'middle'}
            ])
            
        elif shape == 'annulus':
            outer_r = inputs.get('outer_radius', 8)
            inner_r = inputs.get('inner_radius', 5)
            scale = min(150 / (outer_r * 2), 20)
            r_outer = outer_r * scale
            r_inner = inner_r * scale
            
            visualization_data['elements'].extend([
                {
                    'type': 'circle',
                    'cx': center_x, 'cy': center_y, 'r': r_outer,
                    'fill': 'rgba(59, 130, 246, 0.2)',
                    'stroke': '#3b82f6',
                    'stroke_width': 3
                },
                {
                    'type': 'circle',
                    'cx': center_x, 'cy': center_y, 'r': r_inner,
                    'fill': 'rgba(102, 126, 234, 0.5)',
                    'stroke': '#3b82f6',
                    'stroke_width': 3
                },
                {
                    'type': 'line',
                    'x1': center_x, 'y1': center_y, 'x2': center_x + r_outer, 'y2': center_y,
                    'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'
                },
                {
                    'type': 'line',
                    'x1': center_x, 'y1': center_y, 'x2': center_x + r_inner, 'y2': center_y,
                    'stroke': '#1e40af', 'stroke_width': 2, 'stroke_dasharray': '5,5'
                }
            ])
            visualization_data['labels'].extend([
                {'x': center_x + r_outer/2, 'y': center_y - 10,
                 'text': f'R = {format_num(outer_r)} {unit}', 'anchor': 'middle'},
                {'x': center_x + r_inner/2, 'y': center_y + 5,
                 'text': f'r = {format_num(inner_r)} {unit}', 'anchor': 'middle'}
            ])
        
        return visualization_data
    
    def prepare_chart_data(self, result, unit):
        """Prepare comprehensive chart data for visualizations"""
        area = result.get('area', 0)
        shape = result.get('shape', 'unknown')
        
        # Validate area is a valid number
        if not isinstance(area, (int, float)) or math.isnan(area) or math.isinf(area) or area < 0:
            area = 0
        
        # Area Gauge Chart (Doughnut)
        # Handle edge case where area is 0
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
        
        # Shape Comparison Chart (only show if perimeter/circumference exists)
        perimeter_value = result.get('perimeter') or result.get('circumference') or 0
        comparison_data = None
        if perimeter_value > 0:
            comparison_data = {
                'type': 'bar',
                'data': {
                    'labels': ['Area', 'Perimeter' if result.get('perimeter') else 'Circumference'],
                    'datasets': [{
                        'label': 'Measurement',
                        'data': [
                            round(area, 2),
                            round(perimeter_value, 2)
                        ],
                        'backgroundColor': ['#3b82f6', '#10b981'],
                        'borderColor': ['#2563eb', '#059669'],
                        'borderWidth': 2,
                        'borderRadius': 8
                    }]
                }
            }
        else:
            # Fallback: Show area vs a reference value
            comparison_data = {
                'type': 'bar',
                'data': {
                    'labels': ['Area'],
                    'datasets': [{
                        'label': 'Area',
                        'data': [round(area, 2)],
                        'backgroundColor': ['#3b82f6'],
                        'borderColor': ['#2563eb'],
                        'borderWidth': 2,
                        'borderRadius': 8
                    }]
                }
            }
        
        # Properties Chart (showing all calculated properties)
        properties_labels = []
        properties_values = []
        properties_colors = []
        
        # Always include area first
        properties_labels.append('Area')
        properties_values.append(round(area, 2))
        properties_colors.append('#3b82f6')
        
        if result.get('perimeter'):
            properties_labels.append('Perimeter')
            properties_values.append(round(result['perimeter'], 2))
            properties_colors.append('#10b981')
        if result.get('circumference'):
            properties_labels.append('Circumference')
            properties_values.append(round(result['circumference'], 2))
            properties_colors.append('#10b981')
        if result.get('diagonal'):
            properties_labels.append('Diagonal')
            properties_values.append(round(result['diagonal'], 2))
            properties_colors.append('#f59e0b')
        if result.get('diameter'):
            properties_labels.append('Diameter')
            properties_values.append(round(result['diameter'], 2))
            properties_colors.append('#8b5cf6')
        if result.get('side'):
            properties_labels.append('Side Length')
            properties_values.append(round(result['side'], 2))
            properties_colors.append('#ec4899')
        if result.get('arc_length'):
            properties_labels.append('Arc Length')
            properties_values.append(round(result['arc_length'], 2))
            properties_colors.append('#06b6d4')
        
        # Ensure at least area is shown
        if len(properties_labels) == 0:
            properties_labels.append('Area')
            properties_values.append(round(area, 2))
            properties_colors.append('#3b82f6')
        
        properties_chart = {
            'type': 'bar',
            'data': {
                'labels': properties_labels,
                'datasets': [{
                    'label': f'Measurements ({unit})',
                    'data': properties_values,
                    'backgroundColor': properties_colors,
                    'borderColor': properties_colors,
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'gauge_chart': gauge_chart,
            'comparison_chart': comparison_data,
            'properties_chart': properties_chart
        }
    
    def prepare_display_data(self, result, unit):
        """Prepare formatted display data for frontend"""
        area = result.get('area', 0)
        
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
            'area_formatted': format_number(area, 6),
            'area_formatted_short': format_number(area, 2),
            'area_formatted_display': format_number(area, 6),  # For main display
            'detailed_results': [],
            'stats': {
                'shape': result.get('shape', 'unknown').capitalize(),
                'perimeter': format_number(result.get('perimeter', result.get('circumference', 0)), 2) if result.get('perimeter') or result.get('circumference') else None,
                'unit': unit
            }
        }
        
        # Add area
        display_data['detailed_results'].append({
            'label': 'Area',
            'value': format_number(area),
            'unit': f'{unit}²',
            'is_primary': True
        })
        
        # Add other properties
        if result.get('perimeter'):
            display_data['detailed_results'].append({
                'label': 'Perimeter',
                'value': format_number(result['perimeter']),
                'unit': unit,
                'is_primary': False
            })
        
        if result.get('circumference'):
            display_data['detailed_results'].append({
                'label': 'Circumference',
                'value': format_number(result['circumference']),
                'unit': unit,
                'is_primary': False
            })
        
        if result.get('diagonal'):
            display_data['detailed_results'].append({
                'label': 'Diagonal',
                'value': format_number(result['diagonal']),
                'unit': unit,
                'is_primary': False
            })
        
        if result.get('diameter'):
            display_data['detailed_results'].append({
                'label': 'Diameter',
                'value': format_number(result['diameter']),
                'unit': unit,
                'is_primary': False
            })
        
        if result.get('side'):
            display_data['detailed_results'].append({
                'label': 'Side Length',
                'value': format_number(result['side']),
                'unit': unit,
                'is_primary': False
            })
        
        if result.get('arc_length'):
            display_data['detailed_results'].append({
                'label': 'Arc Length',
                'value': format_number(result['arc_length']),
                'unit': unit,
                'is_primary': False
            })
        
        return display_data
    
    def prepare_step_by_step_html(self, steps):
        """Prepare step-by-step solution as HTML structure"""
        if not steps or not isinstance(steps, list):
            return []
        
        return [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(steps)]
    
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
    
    def _calculate_rectangle(self, data):
        """Calculate rectangle area and properties"""
        length, error = self._validate_positive_number(data.get('length', 0), 'Length')
        if error:
            return {'success': False, 'error': error}
        
        width, error = self._validate_positive_number(data.get('width', 0), 'Width')
        if error:
            return {'success': False, 'error': error}
        
        area = length * width
        perimeter = 2 * (length + width)
        diagonal = float(np.sqrt(length**2 + width**2))
        
        return {
            'shape': 'rectangle',
            'area': round(area, 8),
            'perimeter': round(perimeter, 8),
            'diagonal': round(diagonal, 8),
            'formula': f'A = l × w = {length} × {width}',
            'step_by_step': [
                f'Step 1: Identify the length (l) = {length}',
                f'Step 2: Identify the width (w) = {width}',
                f'Step 3: Apply formula A = l × w',
                f'Step 4: A = {length} × {width} = {area}',
            ],
            'inputs': {'length': length, 'width': width}
        }
    
    def _calculate_square(self, data):
        """Calculate square area and properties"""
        side, error = self._validate_positive_number(data.get('side', 0), 'Side')
        if error:
            return {'success': False, 'error': error}
        
        area = side ** 2
        perimeter = 4 * side
        diagonal = side * float(np.sqrt(2))
        
        return {
            'shape': 'square',
            'area': round(area, 8),
            'perimeter': round(perimeter, 8),
            'diagonal': round(diagonal, 8),
            'formula': f'A = s² = {side}²',
            'step_by_step': [
                f'Step 1: Identify the side length (s) = {side}',
                f'Step 2: Apply formula A = s²',
                f'Step 3: A = {side}² = {area}',
            ],
            'inputs': {'side': side}
        }
    
    def _calculate_circle(self, data):
        """Calculate circle area and properties"""
        radius, error = self._validate_positive_number(data.get('radius', 0), 'Radius')
        if error:
            return {'success': False, 'error': error}
        
        area = float(N(pi * radius**2, 15))
        circumference = float(N(2 * pi * radius, 15))
        diameter = 2 * radius
        
        return {
            'shape': 'circle',
            'area': round(area, 8),
            'circumference': round(circumference, 8),
            'diameter': round(diameter, 8),
            'formula': f'A = πr² = π × {radius}²',
            'step_by_step': [
                f'Step 1: Identify the radius (r) = {radius}',
                f'Step 2: Apply formula A = πr²',
                f'Step 3: A = π × {radius}²',
                f'Step 4: A = {pi.evalf(10)} × {radius**2} = {area}',
            ],
            'inputs': {'radius': radius}
        }
    
    def _calculate_triangle(self, data):
        """Calculate triangle area"""
        base, error = self._validate_positive_number(data.get('base', 0), 'Base')
        if error:
            return {'success': False, 'error': error}
        
        height, error = self._validate_positive_number(data.get('height', 0), 'Height')
        if error:
            return {'success': False, 'error': error}
        
        area = 0.5 * base * height
        
        return {
            'shape': 'triangle',
            'area': round(area, 8),
            'formula': f'A = ½ × b × h = ½ × {base} × {height}',
            'step_by_step': [
                f'Step 1: Identify the base (b) = {base}',
                f'Step 2: Identify the height (h) = {height}',
                f'Step 3: Apply formula A = ½ × b × h',
                f'Step 4: A = 0.5 × {base} × {height} = {area}',
            ],
            'inputs': {'base': base, 'height': height}
        }
    
    def _calculate_trapezoid(self, data):
        """Calculate trapezoid area"""
        base1, error = self._validate_positive_number(data.get('base1', 0), 'Base 1')
        if error:
            return {'success': False, 'error': error}
        
        base2, error = self._validate_positive_number(data.get('base2', 0), 'Base 2')
        if error:
            return {'success': False, 'error': error}
        
        height, error = self._validate_positive_number(data.get('height', 0), 'Height')
        if error:
            return {'success': False, 'error': error}
        
        area = 0.5 * (base1 + base2) * height
        
        return {
            'shape': 'trapezoid',
            'area': round(area, 8),
            'formula': f'A = ½ × (a + b) × h = ½ × ({base1} + {base2}) × {height}',
            'step_by_step': [
                f'Step 1: Identify base 1 (a) = {base1}',
                f'Step 2: Identify base 2 (b) = {base2}',
                f'Step 3: Identify height (h) = {height}',
                f'Step 4: Apply formula A = ½ × (a + b) × h',
                f'Step 5: A = 0.5 × ({base1} + {base2}) × {height} = {area}',
            ],
            'inputs': {'base1': base1, 'base2': base2, 'height': height}
        }
    
    def _calculate_ellipse(self, data):
        """Calculate ellipse area"""
        a, error = self._validate_positive_number(data.get('semi_major', 0), 'Semi-major axis')
        if error:
            return {'success': False, 'error': error}
        
        b, error = self._validate_positive_number(data.get('semi_minor', 0), 'Semi-minor axis')
        if error:
            return {'success': False, 'error': error}
        
        area = float(N(pi * a * b, 15))
        h = ((a - b)**2) / ((a + b)**2)
        circumference = float(N(pi * (a + b) * (1 + 3*h / (10 + np.sqrt(4 - 3*h))), 15))
        
        return {
            'shape': 'ellipse',
            'area': round(area, 8),
            'circumference': round(circumference, 8),
            'formula': f'A = πab = π × {a} × {b}',
            'step_by_step': [
                f'Step 1: Identify semi-major axis (a) = {a}',
                f'Step 2: Identify semi-minor axis (b) = {b}',
                f'Step 3: Apply formula A = πab',
                f'Step 4: A = π × {a} × {b} = {area}',
            ],
            'inputs': {'semi_major': a, 'semi_minor': b}
        }
    
    def _calculate_parallelogram(self, data):
        """Calculate parallelogram area"""
        base, error = self._validate_positive_number(data.get('base', 0), 'Base')
        if error:
            return {'success': False, 'error': error}
        
        height, error = self._validate_positive_number(data.get('height', 0), 'Height')
        if error:
            return {'success': False, 'error': error}
        
        area = base * height
        
        return {
            'shape': 'parallelogram',
            'area': round(area, 8),
            'formula': f'A = b × h = {base} × {height}',
            'step_by_step': [
                f'Step 1: Identify the base (b) = {base}',
                f'Step 2: Identify the height (h) = {height}',
                f'Step 3: Apply formula A = b × h',
                f'Step 4: A = {base} × {height} = {area}',
            ],
            'inputs': {'base': base, 'height': height}
        }
    
    def _calculate_rhombus(self, data):
        """Calculate rhombus area"""
        d1, error = self._validate_positive_number(data.get('diagonal1', 0), 'Diagonal 1')
        if error:
            return {'success': False, 'error': error}
        
        d2, error = self._validate_positive_number(data.get('diagonal2', 0), 'Diagonal 2')
        if error:
            return {'success': False, 'error': error}
        
        area = 0.5 * d1 * d2
        side = float(np.sqrt((d1/2)**2 + (d2/2)**2))
        perimeter = 4 * side
        
        return {
            'shape': 'rhombus',
            'area': round(area, 8),
            'side': round(side, 8),
            'perimeter': round(perimeter, 8),
            'formula': f'A = ½ × d₁ × d₂ = ½ × {d1} × {d2}',
            'step_by_step': [
                f'Step 1: Identify diagonal 1 (d₁) = {d1}',
                f'Step 2: Identify diagonal 2 (d₂) = {d2}',
                f'Step 3: Apply formula A = ½ × d₁ × d₂',
                f'Step 4: A = 0.5 × {d1} × {d2} = {area}',
            ],
            'inputs': {'diagonal1': d1, 'diagonal2': d2}
        }
    
    def _calculate_pentagon(self, data):
        """Calculate regular pentagon area"""
        side, error = self._validate_positive_number(data.get('side', 0), 'Side')
        if error:
            return {'success': False, 'error': error}
        
        # Area of regular pentagon: A = (1/4) * sqrt(5(5+2√5)) * s²
        area = (1/4) * np.sqrt(5 * (5 + 2*np.sqrt(5))) * side**2
        perimeter = 5 * side
        
        return {
            'shape': 'pentagon',
            'area': round(area, 8),
            'perimeter': round(perimeter, 8),
            'formula': f'A = (1/4) × √(5(5+2√5)) × s²',
            'step_by_step': [
                f'Step 1: Identify the side length (s) = {side}',
                f'Step 2: Apply formula A = (1/4) × √(5(5+2√5)) × s²',
                f'Step 3: A = {round(area, 8)}',
            ],
            'inputs': {'side': side}
        }
    
    def _calculate_hexagon(self, data):
        """Calculate regular hexagon area"""
        side, error = self._validate_positive_number(data.get('side', 0), 'Side')
        if error:
            return {'success': False, 'error': error}
        
        # Area of regular hexagon: A = (3√3/2) * s²
        area = (3 * np.sqrt(3) / 2) * side**2
        perimeter = 6 * side
        
        return {
            'shape': 'hexagon',
            'area': round(area, 8),
            'perimeter': round(perimeter, 8),
            'formula': f'A = (3√3/2) × s²',
            'step_by_step': [
                f'Step 1: Identify the side length (s) = {side}',
                f'Step 2: Apply formula A = (3√3/2) × s²',
                f'Step 3: A = {round(area, 8)}',
            ],
            'inputs': {'side': side}
        }
    
    def _calculate_octagon(self, data):
        """Calculate regular octagon area"""
        side, error = self._validate_positive_number(data.get('side', 0), 'Side')
        if error:
            return {'success': False, 'error': error}
        
        # Area of regular octagon: A = 2(1+√2) * s²
        area = 2 * (1 + np.sqrt(2)) * side**2
        perimeter = 8 * side
        
        return {
            'shape': 'octagon',
            'area': round(area, 8),
            'perimeter': round(perimeter, 8),
            'formula': f'A = 2(1+√2) × s²',
            'step_by_step': [
                f'Step 1: Identify the side length (s) = {side}',
                f'Step 2: Apply formula A = 2(1+√2) × s²',
                f'Step 3: A = {round(area, 8)}',
            ],
            'inputs': {'side': side}
        }
    
    def _calculate_sector(self, data):
        """Calculate circle sector area"""
        radius, error = self._validate_positive_number(data.get('radius', 0), 'Radius')
        if error:
            return {'success': False, 'error': error}
        
        try:
            angle = float(data.get('angle', 0))
            if math.isnan(angle) or math.isinf(angle):
                return {'success': False, 'error': 'Angle must be a valid number.'}
            if angle <= 0 or angle >= 360:
                return {'success': False, 'error': 'Angle must be between 0 and 360 degrees.'}
        except (ValueError, TypeError):
            return {'success': False, 'error': 'Angle must be a valid number.'}
        
        angle_rad = math.radians(angle)
        area = 0.5 * radius**2 * angle_rad
        arc_length = radius * angle_rad
        
        return {
            'shape': 'sector',
            'area': round(area, 8),
            'arc_length': round(arc_length, 8),
            'formula': f'A = ½ × r² × θ (in radians)',
            'step_by_step': [
                f'Step 1: Identify the radius (r) = {radius}',
                f'Step 2: Identify the angle (θ) = {angle}°',
                f'Step 3: Convert angle to radians: {angle}° = {round(angle_rad, 6)} rad',
                f'Step 4: Apply formula A = ½ × r² × θ',
                f'Step 5: A = 0.5 × {radius}² × {round(angle_rad, 6)} = {area}',
            ],
            'inputs': {'radius': radius, 'angle': angle}
        }
    
    def _calculate_annulus(self, data):
        """Calculate annulus (ring) area"""
        outer_radius, error = self._validate_positive_number(data.get('outer_radius', 0), 'Outer radius')
        if error:
            return {'success': False, 'error': error}
        
        inner_radius, error = self._validate_positive_number(data.get('inner_radius', 0), 'Inner radius')
        if error:
            return {'success': False, 'error': error}
        
        if inner_radius >= outer_radius:
            return {'success': False, 'error': 'Inner radius must be less than outer radius.'}
        
        area = float(N(pi * (outer_radius**2 - inner_radius**2), 15))
        
        return {
            'shape': 'annulus',
            'area': round(area, 8),
            'formula': f'A = π(R² - r²) = π({outer_radius}² - {inner_radius}²)',
            'step_by_step': [
                f'Step 1: Identify outer radius (R) = {outer_radius}',
                f'Step 2: Identify inner radius (r) = {inner_radius}',
                f'Step 3: Apply formula A = π(R² - r²)',
                f'Step 4: A = π × ({outer_radius**2} - {inner_radius**2}) = {area}',
            ],
            'inputs': {'outer_radius': outer_radius, 'inner_radius': inner_radius}
        }
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            shape = data.get('shape', 'rectangle')
            unit = data.get('unit', 'm')
            
            # Shape calculation mapping
            shape_calculators = {
                'rectangle': self._calculate_rectangle,
                'square': self._calculate_square,
                'circle': self._calculate_circle,
                'triangle': self._calculate_triangle,
                'trapezoid': self._calculate_trapezoid,
                'ellipse': self._calculate_ellipse,
                'parallelogram': self._calculate_parallelogram,
                'rhombus': self._calculate_rhombus,
                'pentagon': self._calculate_pentagon,
                'hexagon': self._calculate_hexagon,
                'octagon': self._calculate_octagon,
                'sector': self._calculate_sector,
                'annulus': self._calculate_annulus,
            }
            
            if shape not in shape_calculators:
                return JsonResponse({'success': False, 'error': 'Unknown shape. Please select a valid shape.'}, status=400)
            
            result = shape_calculators[shape](data)
            
            if not result.get('success', True):
                return JsonResponse(result, status=400)
            
            # Validate result before preparing charts
            if 'area' not in result or result.get('area') is None:
                return JsonResponse({'success': False, 'error': 'Calculation failed: No area result.'}, status=500)
            
            # Prepare chart data
            try:
                chart_data = self.prepare_chart_data(result, unit)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                # Continue without charts if chart preparation fails
                chart_data = {}
            
            # Prepare shape visualization data
            try:
                shape_visualization = self.prepare_shape_visualization(result, unit)
            except Exception as viz_error:
                import traceback
                print(f"Shape visualization preparation error: {traceback.format_exc()}")
                shape_visualization = {}
            
            # Prepare formatted display data
            display_data = self.prepare_display_data(result, unit)
            
            # Prepare step-by-step HTML (backend-controlled)
            step_by_step_html = self.prepare_step_by_step_html(result.get('step_by_step', []))
            
            # Enhance result with all prepared data
            result['success'] = True
            result['unit'] = unit
            result['area_unit'] = f'{unit}²'
            result['chart_data'] = chart_data
            result['shape_visualization'] = shape_visualization
            result['display_data'] = display_data
            result['step_by_step_html'] = step_by_step_html
            result['shape_display_name'] = shape.capitalize()
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}. Please check your measurements.'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Area Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
