from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import symbols, simplify, N, Float, log


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ArmyBodyFatCalculator(View):
    """
    Class-based view for Army Body Fat Calculator
    Uses US Army body fat calculation method based on measurements.
    Uses SymPy for precise logarithmic calculations.
    """
    template_name = 'fitness_and_health_calculators/army_body_fat_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Army Body Fat Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            gender = data.get('gender', 'male').lower()
            age = int(data.get('age', 25))
            height = float(data.get('height', 70))  # inches
            neck = float(data.get('neck', 15))  # inches
            waist = float(data.get('waist', 32))  # inches
            hip = float(data.get('hip', 0))  # inches (for females)
            
            # Validation
            if age < 17 or age > 65:
                return JsonResponse({'success': False, 'error': 'Age must be between 17 and 65 for Army standards.'}, status=400)
            if height < 48 or height > 84:
                return JsonResponse({'success': False, 'error': 'Height must be between 48 and 84 inches.'}, status=400)
            if neck <= 0 or waist <= 0:
                return JsonResponse({'success': False, 'error': 'Neck and waist measurements must be greater than zero.'}, status=400)
            
            # US Army body fat formula using SymPy for precision
            if gender in ['male', 'm']:
                # Male formula: 86.010 * log10(waist - neck) - 70.041 * log10(height) + 36.76
                waist_neck_diff = Float(waist - neck, 15)
                height_float = Float(height, 15)
                
                # Use SymPy log for precision
                log_waist_neck = N(log(waist_neck_diff, 10), 10)
                log_height = N(log(height_float, 10), 10)
                
                body_fat = float(86.010 * log_waist_neck - 70.041 * log_height + 36.76)
                max_allowed = 20 if age < 30 else (22 if age < 40 else 24)
            else:
                # Female formula: 163.205 * log10(waist + hip - neck) - 97.684 * log10(height) - 78.387
                if hip <= 0:
                    return JsonResponse({'success': False, 'error': 'Hip measurement required for females.'}, status=400)
                
                waist_hip_neck_sum = Float(waist + hip - neck, 15)
                height_float = Float(height, 15)
                
                log_waist_hip_neck = N(log(waist_hip_neck_sum, 10), 10)
                log_height = N(log(height_float, 10), 10)
                
                body_fat = float(163.205 * log_waist_hip_neck - 97.684 * log_height - 78.387)
                max_allowed = 30 if age < 30 else (32 if age < 40 else 34)
            
            # Ensure body fat is within reasonable range
            if body_fat < 0:
                body_fat = 0
            if body_fat > 50:
                body_fat = 50
            
            # Pass/fail status
            passes = body_fat <= max_allowed
            
            # Determine category and color
            category, category_color = self.get_body_fat_category(body_fat, gender, max_allowed, passes)
            
            # Calculate scale position (0-100%)
            scale_position = self.calculate_scale_position(body_fat, max_allowed)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                body_fat=body_fat,
                max_allowed=max_allowed,
                category_color=category_color,
                passes=passes
            )
            
            # Get color info
            color_info = self.get_color_info(category_color)
            
            result = {
                'success': True,
                'gender': gender,
                'age': age,
                'height': round(height, 1),
                'neck': round(neck, 1),
                'waist': round(waist, 1),
                'hip': round(hip, 1) if hip > 0 else 0,
                'body_fat_percent': round(body_fat, 1),
                'max_allowed': max_allowed,
                'passes': passes,
                'status': 'Pass' if passes else 'Fail',
                'difference': round(body_fat - max_allowed, 1),
                'category': category,
                'category_color': category_color,
                'scale_position': scale_position,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Army Body Fat Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_body_fat_category(self, body_fat, gender, max_allowed, passes):
        """Determine body fat category and color"""
        if passes:
            if body_fat <= max_allowed * 0.8:  # Well below limit
                return 'Excellent', 'green'
            elif body_fat <= max_allowed * 0.9:  # Good
                return 'Good', 'green'
            else:  # Just passing
                return 'Acceptable', 'yellow'
        else:
            if body_fat <= max_allowed * 1.1:  # Slightly over
                return 'Slightly Over', 'yellow'
            elif body_fat <= max_allowed * 1.2:  # Over limit
                return 'Over Limit', 'orange'
            else:  # Significantly over
                return 'Significantly Over', 'red'
    
    def calculate_scale_position(self, body_fat, max_allowed):
        """Calculate body fat indicator position on scale (0-100%)"""
        # Scale: 0% to max_allowed*1.5 (150% of max)
        max_display = max_allowed * 1.5
        position = (body_fat / max_display) * 100
        return min(100.0, max(0.0, float(position)))
    
    def get_color_info(self, category_color):
        """Get color information for the category"""
        color_map = {
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            },
            'yellow': {
                'hex': '#eab308',
                'rgb': 'rgb(234, 179, 8)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300'
            },
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            },
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            }
        }
        return color_map.get(category_color, color_map['green'])
    
    def prepare_chart_data(self, body_fat, max_allowed, category_color, passes):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(category_color)
        
        # Gauge Chart Data
        max_display = max_allowed * 1.5
        body_fat_percentage = min((body_fat / max_display) * 100, 100)
        
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Body Fat', 'Remaining'],
                'datasets': [{
                    'data': [round(body_fat_percentage, 2), round(100 - body_fat_percentage, 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(body_fat, 1),
                'label': '% Body Fat',
                'color': color_info['hex']
            }
        }
        
        # Body Fat Standards Chart
        standards_data = []
        standards_colors = []
        standards_labels = []
        
        # Create ranges: Excellent, Good, Acceptable, Over Limit
        ranges = [
            {'name': 'Excellent', 'max': max_allowed * 0.8, 'color': '#10b981'},
            {'name': 'Good', 'max': max_allowed * 0.9, 'color': '#10b981'},
            {'name': 'Acceptable', 'max': max_allowed, 'color': '#eab308'},
            {'name': 'Over Limit', 'max': max_allowed * 1.5, 'color': '#ef4444'}
        ]
        
        current_range_index = 0
        for idx, range_info in enumerate(ranges):
            if body_fat <= range_info['max']:
                current_range_index = idx
                break
        else:
            current_range_index = len(ranges) - 1
        
        for idx, range_info in enumerate(ranges):
            standards_labels.append(range_info['name'])
            if idx == current_range_index:
                standards_data.append(round(body_fat, 1))
                standards_colors.append(range_info['color'])
            else:
                standards_data.append(0)
                standards_colors.append('#e5e7eb')
        
        standards_chart = {
            'type': 'bar',
            'data': {
                'labels': standards_labels,
                'datasets': [{
                    'label': 'Body Fat %',
                    'data': standards_data,
                    'backgroundColor': standards_colors,
                    'borderColor': [r['color'] for r in ranges],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            },
            'current_range_index': current_range_index,
            'ranges_info': ranges
        }
        
        # Comparison Chart (Current vs Max Allowed)
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Your Body Fat', 'Max Allowed'],
                'datasets': [{
                    'label': 'Body Fat %',
                    'data': [round(body_fat, 1), round(max_allowed, 1)],
                    'backgroundColor': [color_info['hex'], '#6b7280'],
                    'borderColor': [color_info['hex'], '#4b5563'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'gauge_chart': gauge_chart,
            'standards_chart': standards_chart,
            'comparison_chart': comparison_chart
        }
