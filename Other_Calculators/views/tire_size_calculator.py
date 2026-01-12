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
class TireSizeCalculator(View):
    """
    Professional Tire Size Calculator with Comprehensive Features
    
    This calculator provides tire size calculations with:
    - Calculate tire dimensions (diameter, circumference, width)
    - Convert between metric and imperial tire sizes
    - Compare tire sizes
    - Calculate speedometer difference
    - Calculate revolutions per mile/km
    
    Features:
    - Supports multiple calculation modes
    - Handles metric (P-metric) and imperial (flotation) sizes
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/tire_size_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Tire Size Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'dimensions')
            
            if calc_type == 'dimensions':
                return self._calculate_dimensions(data)
            elif calc_type == 'convert':
                return self._convert_size(data)
            elif calc_type == 'compare':
                return self._compare_tires(data)
            elif calc_type == 'speedometer':
                return self._calculate_speedometer(data)
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
    
    def _parse_metric_tire(self, tire_str):
        """Parse metric tire size (e.g., 205/55R16)"""
        try:
            # Remove spaces and common prefixes
            tire_str = tire_str.strip().upper().replace(' ', '')
            if tire_str.startswith('P'):
                tire_str = tire_str[1:]
            
            # Pattern: WIDTH/ASPECTRATIO R DIAMETER
            import re
            pattern = r'(\d+)/(\d+)R?(\d+)'
            match = re.match(pattern, tire_str)
            
            if not match:
                return None
            
            width = int(match.group(1))  # mm
            aspect_ratio = int(match.group(2))  # percentage
            rim_diameter = int(match.group(3))  # inches
            
            return {
                'width': width,
                'aspect_ratio': aspect_ratio,
                'rim_diameter': rim_diameter,
                'format': 'metric'
            }
        except Exception:
            return None
    
    def _parse_imperial_tire(self, tire_str):
        """Parse imperial tire size (e.g., 31x10.5R15)"""
        try:
            tire_str = tire_str.strip().upper().replace(' ', '')
            
            # Pattern: DIAMETER x WIDTH R DIAMETER
            import re
            pattern = r'(\d+(?:\.\d+)?)X(\d+(?:\.\d+)?)R?(\d+)'
            match = re.match(pattern, tire_str)
            
            if not match:
                return None
            
            overall_diameter = float(match.group(1))  # inches
            width = float(match.group(2))  # inches
            rim_diameter = int(match.group(3))  # inches
            
            return {
                'overall_diameter': overall_diameter,
                'width': width,
                'rim_diameter': rim_diameter,
                'format': 'imperial'
            }
        except Exception:
            return None
    
    def _calculate_tire_dimensions(self, tire_data):
        """Calculate tire dimensions from tire data"""
        if tire_data['format'] == 'metric':
            width_mm = tire_data['width']
            aspect_ratio = tire_data['aspect_ratio']
            rim_diameter = tire_data['rim_diameter']
            
            # Convert width to inches
            width_inches = width_mm / 25.4
            
            # Calculate sidewall height
            sidewall_height = (width_mm * aspect_ratio / 100) / 25.4  # inches
            
            # Calculate overall diameter
            overall_diameter = rim_diameter + (2 * sidewall_height)
            
            # Calculate circumference
            circumference = math.pi * overall_diameter  # inches
            
            # Calculate revolutions per mile
            revolutions_per_mile = 63360 / circumference  # 63360 inches per mile
            
            # Calculate revolutions per km
            revolutions_per_km = 100000 / (circumference * 25.4)  # 100000 mm per km
            
            return {
                'width_mm': width_mm,
                'width_inches': width_inches,
                'aspect_ratio': aspect_ratio,
                'rim_diameter': rim_diameter,
                'sidewall_height': sidewall_height,
                'overall_diameter': overall_diameter,
                'circumference': circumference,
                'revolutions_per_mile': revolutions_per_mile,
                'revolutions_per_km': revolutions_per_km,
            }
        else:  # imperial
            overall_diameter = tire_data['overall_diameter']
            width = tire_data['width']
            rim_diameter = tire_data['rim_diameter']
            
            # Calculate sidewall height
            sidewall_height = (overall_diameter - rim_diameter) / 2
            
            # Calculate circumference
            circumference = math.pi * overall_diameter
            
            # Calculate revolutions per mile
            revolutions_per_mile = 63360 / circumference
            
            # Calculate revolutions per km
            revolutions_per_km = 100000 / (circumference * 25.4)
            
            # Calculate aspect ratio (approximate)
            aspect_ratio = (sidewall_height / width) * 100
            
            return {
                'width_mm': width * 25.4,
                'width_inches': width,
                'aspect_ratio': aspect_ratio,
                'rim_diameter': rim_diameter,
                'sidewall_height': sidewall_height,
                'overall_diameter': overall_diameter,
                'circumference': circumference,
                'revolutions_per_mile': revolutions_per_mile,
                'revolutions_per_km': revolutions_per_km,
            }
    
    def _calculate_dimensions(self, data):
        """Calculate tire dimensions from tire size"""
        try:
            if 'tire_size' not in data or not data.get('tire_size'):
                return JsonResponse({
                    'success': False,
                    'error': _('Tire size is required.')
                }, status=400)
            
            tire_size = data.get('tire_size', '').strip()
            
            # Try to parse as metric first
            tire_data = self._parse_metric_tire(tire_size)
            
            if not tire_data:
                # Try imperial
                tire_data = self._parse_imperial_tire(tire_size)
            
            if not tire_data:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid tire size format. Use metric (e.g., 205/55R16) or imperial (e.g., 31x10.5R15) format.')
                }, status=400)
            
            dimensions = self._calculate_tire_dimensions(tire_data)
            
            steps = self._prepare_dimensions_steps(tire_data, dimensions)
            chart_data = self._prepare_dimensions_chart_data(dimensions)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'dimensions',
                'tire_size': tire_size,
                'tire_format': tire_data['format'],
                'dimensions': {
                    'width_mm': round(dimensions['width_mm'], 2),
                    'width_inches': round(dimensions['width_inches'], 2),
                    'aspect_ratio': round(dimensions['aspect_ratio'], 2),
                    'rim_diameter': dimensions['rim_diameter'],
                    'sidewall_height': round(dimensions['sidewall_height'], 2),
                    'overall_diameter': round(dimensions['overall_diameter'], 2),
                    'circumference': round(dimensions['circumference'], 2),
                    'revolutions_per_mile': round(dimensions['revolutions_per_mile'], 2),
                    'revolutions_per_km': round(dimensions['revolutions_per_km'], 2),
                },
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating dimensions: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_size(self, data):
        """Convert tire size between metric and imperial"""
        try:
            if 'tire_size' not in data or not data.get('tire_size'):
                return JsonResponse({
                    'success': False,
                    'error': _('Tire size is required.')
                }, status=400)
            
            tire_size = data.get('tire_size', '').strip()
            target_format = data.get('target_format', 'imperial')
            
            # Parse tire
            tire_data = self._parse_metric_tire(tire_size)
            if not tire_data:
                tire_data = self._parse_imperial_tire(tire_size)
            
            if not tire_data:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid tire size format.')
                }, status=400)
            
            dimensions = self._calculate_tire_dimensions(tire_data)
            
            # Convert to target format
            if target_format == 'imperial' and tire_data['format'] == 'metric':
                converted_size = f"{dimensions['overall_diameter']:.1f}x{dimensions['width_inches']:.1f}R{dimensions['rim_diameter']}"
            elif target_format == 'metric' and tire_data['format'] == 'imperial':
                # Find closest standard metric size
                width_mm = round(dimensions['width_mm'] / 5) * 5  # Round to nearest 5mm
                aspect_ratio = round(dimensions['aspect_ratio'] / 5) * 5  # Round to nearest 5%
                converted_size = f"{int(width_mm)}/{int(aspect_ratio)}R{dimensions['rim_diameter']}"
            else:
                converted_size = tire_size
            
            steps = self._prepare_convert_steps(tire_size, tire_data, dimensions, target_format, converted_size)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'original_size': tire_size,
                'original_format': tire_data['format'],
                'converted_size': converted_size,
                'target_format': target_format,
                'dimensions': {
                    'overall_diameter': round(dimensions['overall_diameter'], 2),
                    'width_mm': round(dimensions['width_mm'], 2),
                    'width_inches': round(dimensions['width_inches'], 2),
                },
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error converting size: {error}').format(error=str(e))
            }, status=500)
    
    def _compare_tires(self, data):
        """Compare two tire sizes"""
        try:
            if 'tire1' not in data or not data.get('tire1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First tire size is required.')
                }, status=400)
            
            if 'tire2' not in data or not data.get('tire2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second tire size is required.')
                }, status=400)
            
            tire1_str = data.get('tire1', '').strip()
            tire2_str = data.get('tire2', '').strip()
            
            # Parse tires
            tire1_data = self._parse_metric_tire(tire1_str)
            if not tire1_data:
                tire1_data = self._parse_imperial_tire(tire1_str)
            
            tire2_data = self._parse_metric_tire(tire2_str)
            if not tire2_data:
                tire2_data = self._parse_imperial_tire(tire2_str)
            
            if not tire1_data or not tire2_data:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid tire size format.')
                }, status=400)
            
            dim1 = self._calculate_tire_dimensions(tire1_data)
            dim2 = self._calculate_tire_dimensions(tire2_data)
            
            # Calculate differences
            diameter_diff = dim2['overall_diameter'] - dim1['overall_diameter']
            diameter_diff_percent = (diameter_diff / dim1['overall_diameter']) * 100
            circumference_diff = dim2['circumference'] - dim1['circumference']
            speed_diff = (diameter_diff_percent)  # Speed difference percentage
            
            steps = self._prepare_compare_steps(tire1_str, tire2_str, dim1, dim2, diameter_diff, diameter_diff_percent, circumference_diff, speed_diff)
            chart_data = self._prepare_compare_chart_data(dim1, dim2, tire1_str, tire2_str)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'compare',
                'tire1': {
                    'size': tire1_str,
                    'dimensions': {
                        'overall_diameter': round(dim1['overall_diameter'], 2),
                        'circumference': round(dim1['circumference'], 2),
                        'width_inches': round(dim1['width_inches'], 2),
                    }
                },
                'tire2': {
                    'size': tire2_str,
                    'dimensions': {
                        'overall_diameter': round(dim2['overall_diameter'], 2),
                        'circumference': round(dim2['circumference'], 2),
                        'width_inches': round(dim2['width_inches'], 2),
                    }
                },
                'differences': {
                    'diameter_diff': round(diameter_diff, 2),
                    'diameter_diff_percent': round(diameter_diff_percent, 2),
                    'circumference_diff': round(circumference_diff, 2),
                    'speed_diff': round(speed_diff, 2),
                },
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error comparing tires: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_speedometer(self, data):
        """Calculate speedometer difference when changing tire size"""
        try:
            if 'original_tire' not in data or not data.get('original_tire'):
                return JsonResponse({
                    'success': False,
                    'error': _('Original tire size is required.')
                }, status=400)
            
            if 'new_tire' not in data or not data.get('new_tire'):
                return JsonResponse({
                    'success': False,
                    'error': _('New tire size is required.')
                }, status=400)
            
            original_str = data.get('original_tire', '').strip()
            new_str = data.get('new_tire', '').strip()
            speed = float(data.get('speed', 60))  # mph or km/h
            
            # Parse tires
            original_data = self._parse_metric_tire(original_str)
            if not original_data:
                original_data = self._parse_imperial_tire(original_str)
            
            new_data = self._parse_metric_tire(new_str)
            if not new_data:
                new_data = self._parse_imperial_tire(new_str)
            
            if not original_data or not new_data:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid tire size format.')
                }, status=400)
            
            dim_original = self._calculate_tire_dimensions(original_data)
            dim_new = self._calculate_tire_dimensions(new_data)
            
            # Calculate speed difference
            diameter_ratio = dim_new['overall_diameter'] / dim_original['overall_diameter']
            actual_speed = speed * diameter_ratio
            speed_diff = actual_speed - speed
            speed_diff_percent = ((actual_speed - speed) / speed) * 100
            
            steps = self._prepare_speedometer_steps(original_str, new_str, dim_original, dim_new, speed, actual_speed, speed_diff, speed_diff_percent, diameter_ratio)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'speedometer',
                'original_tire': original_str,
                'new_tire': new_str,
                'indicated_speed': speed,
                'actual_speed': round(actual_speed, 2),
                'speed_difference': round(speed_diff, 2),
                'speed_difference_percent': round(speed_diff_percent, 2),
                'diameter_ratio': round(diameter_ratio, 4),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating speedometer: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_dimensions_steps(self, tire_data, dimensions):
        """Prepare step-by-step solution for dimensions calculation"""
        steps = []
        steps.append(_('Step 1: Identify tire specifications'))
        if tire_data['format'] == 'metric':
            steps.append(_('Width: {width} mm').format(width=tire_data['width']))
            steps.append(_('Aspect Ratio: {ratio}%').format(ratio=tire_data['aspect_ratio']))
            steps.append(_('Rim Diameter: {diameter}"').format(diameter=tire_data['rim_diameter']))
        else:
            steps.append(_('Overall Diameter: {diameter}"').format(diameter=tire_data['overall_diameter']))
            steps.append(_('Width: {width}"').format(width=tire_data['width']))
            steps.append(_('Rim Diameter: {diameter}"').format(diameter=tire_data['rim_diameter']))
        steps.append('')
        steps.append(_('Step 2: Calculate sidewall height'))
        if tire_data['format'] == 'metric':
            steps.append(_('Sidewall Height = (Width × Aspect Ratio / 100) / 25.4'))
            steps.append(_('Sidewall Height = ({width} × {ratio} / 100) / 25.4').format(width=tire_data['width'], ratio=tire_data['aspect_ratio']))
        else:
            steps.append(_('Sidewall Height = (Overall Diameter - Rim Diameter) / 2'))
            steps.append(_('Sidewall Height = ({diameter} - {rim}) / 2').format(diameter=tire_data['overall_diameter'], rim=tire_data['rim_diameter']))
        steps.append(_('Sidewall Height = {height}"').format(height=round(dimensions['sidewall_height'], 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate overall diameter'))
        if tire_data['format'] == 'metric':
            steps.append(_('Overall Diameter = Rim Diameter + (2 × Sidewall Height)'))
            steps.append(_('Overall Diameter = {rim} + (2 × {sidewall})').format(rim=tire_data['rim_diameter'], sidewall=round(dimensions['sidewall_height'], 2)))
        steps.append(_('Overall Diameter = {diameter}"').format(diameter=round(dimensions['overall_diameter'], 2)))
        steps.append('')
        steps.append(_('Step 4: Calculate circumference'))
        steps.append(_('Circumference = π × Overall Diameter'))
        steps.append(_('Circumference = π × {diameter}').format(diameter=round(dimensions['overall_diameter'], 2)))
        steps.append(_('Circumference = {circ}"').format(circ=round(dimensions['circumference'], 2)))
        steps.append('')
        steps.append(_('Step 5: Calculate revolutions'))
        steps.append(_('Revolutions per Mile = 63360 / Circumference'))
        steps.append(_('Revolutions per Mile = 63360 / {circ} = {rev}').format(circ=round(dimensions['circumference'], 2), rev=round(dimensions['revolutions_per_mile'], 2)))
        return steps
    
    def _prepare_convert_steps(self, original_size, tire_data, dimensions, target_format, converted_size):
        """Prepare step-by-step solution for conversion"""
        steps = []
        steps.append(_('Step 1: Parse original tire size'))
        steps.append(_('Original Size: {size} ({format})').format(size=original_size, format=tire_data['format']))
        steps.append('')
        steps.append(_('Step 2: Calculate dimensions'))
        steps.append(_('Overall Diameter: {diameter}"').format(diameter=round(dimensions['overall_diameter'], 2)))
        steps.append(_('Width: {width}" ({width_mm} mm)').format(width=round(dimensions['width_inches'], 2), width_mm=round(dimensions['width_mm'], 2)))
        steps.append('')
        steps.append(_('Step 3: Convert to {format} format').format(format=target_format))
        steps.append(_('Converted Size: {size}').format(size=converted_size))
        return steps
    
    def _prepare_compare_steps(self, tire1_str, tire2_str, dim1, dim2, diameter_diff, diameter_diff_percent, circumference_diff, speed_diff):
        """Prepare step-by-step solution for comparison"""
        steps = []
        steps.append(_('Step 1: Identify tire sizes'))
        steps.append(_('Tire 1: {size}').format(size=tire1_str))
        steps.append(_('Tire 2: {size}').format(size=tire2_str))
        steps.append('')
        steps.append(_('Step 2: Calculate dimensions'))
        steps.append(_('Tire 1 Diameter: {diameter}"').format(diameter=round(dim1['overall_diameter'], 2)))
        steps.append(_('Tire 2 Diameter: {diameter}"').format(diameter=round(dim2['overall_diameter'], 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate differences'))
        steps.append(_('Diameter Difference = Tire 2 - Tire 1'))
        steps.append(_('Diameter Difference = {d2} - {d1} = {diff}"').format(d2=round(dim2['overall_diameter'], 2), d1=round(dim1['overall_diameter'], 2), diff=round(diameter_diff, 2)))
        steps.append(_('Diameter Difference % = ({diff} / {d1}) × 100 = {percent}%').format(diff=round(diameter_diff, 2), d1=round(dim1['overall_diameter'], 2), percent=round(diameter_diff_percent, 2)))
        steps.append('')
        steps.append(_('Step 4: Speed difference'))
        steps.append(_('Speed Difference = {diff}%').format(diff=round(speed_diff, 2)))
        steps.append(_('When speedometer shows 60 mph, actual speed is {actual} mph').format(actual=round(60 * (1 + speed_diff/100), 2)))
        return steps
    
    def _prepare_speedometer_steps(self, original_str, new_str, dim_original, dim_new, speed, actual_speed, speed_diff, speed_diff_percent, diameter_ratio):
        """Prepare step-by-step solution for speedometer calculation"""
        steps = []
        steps.append(_('Step 1: Identify tire sizes'))
        steps.append(_('Original Tire: {size}').format(size=original_str))
        steps.append(_('New Tire: {size}').format(size=new_str))
        steps.append('')
        steps.append(_('Step 2: Calculate diameters'))
        steps.append(_('Original Diameter: {diameter}"').format(diameter=round(dim_original['overall_diameter'], 2)))
        steps.append(_('New Diameter: {diameter}"').format(diameter=round(dim_new['overall_diameter'], 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate diameter ratio'))
        steps.append(_('Diameter Ratio = New Diameter / Original Diameter'))
        steps.append(_('Diameter Ratio = {new} / {original} = {ratio}').format(new=round(dim_new['overall_diameter'], 2), original=round(dim_original['overall_diameter'], 2), ratio=round(diameter_ratio, 4)))
        steps.append('')
        steps.append(_('Step 4: Calculate actual speed'))
        steps.append(_('Actual Speed = Indicated Speed × Diameter Ratio'))
        steps.append(_('Actual Speed = {speed} × {ratio} = {actual}').format(speed=speed, ratio=round(diameter_ratio, 4), actual=round(actual_speed, 2)))
        steps.append('')
        steps.append(_('Step 5: Calculate speed difference'))
        steps.append(_('Speed Difference = Actual Speed - Indicated Speed'))
        steps.append(_('Speed Difference = {actual} - {speed} = {diff}').format(actual=round(actual_speed, 2), speed=speed, diff=round(speed_diff, 2)))
        steps.append(_('Speed Difference % = {percent}%').format(percent=round(speed_diff_percent, 2)))
        return steps
    
    # Chart data preparation methods
    def _prepare_dimensions_chart_data(self, dimensions):
        """Prepare chart data for dimensions visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Width (in)'), _('Sidewall (in)'), _('Diameter (in)'), _('Circumference (in)')],
                    'datasets': [{
                        'label': _('Tire Dimensions'),
                        'data': [
                            round(dimensions['width_inches'], 2),
                            round(dimensions['sidewall_height'], 2),
                            round(dimensions['overall_diameter'], 2),
                            round(dimensions['circumference'], 2)
                        ],
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
                            'text': _('Tire Dimensions')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Inches')
                            }
                        }
                    }
                }
            }
            return {'dimensions_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_compare_chart_data(self, dim1, dim2, tire1_str, tire2_str):
        """Prepare chart data for tire comparison"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Diameter'), _('Circumference'), _('Width')],
                    'datasets': [{
                        'label': tire1_str,
                        'data': [
                            round(dim1['overall_diameter'], 2),
                            round(dim1['circumference'], 2),
                            round(dim1['width_inches'], 2)
                        ],
                        'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                        'borderColor': '#3b82f6',
                        'borderWidth': 2
                    }, {
                        'label': tire2_str,
                        'data': [
                            round(dim2['overall_diameter'], 2),
                            round(dim2['circumference'], 2),
                            round(dim2['width_inches'], 2)
                        ],
                        'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                        'borderColor': '#10b981',
                        'borderWidth': 2
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
                            'text': _('Tire Comparison')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Inches')
                            }
                        }
                    }
                }
            }
            return {'compare_chart': chart_config}
        except Exception as e:
            return None
