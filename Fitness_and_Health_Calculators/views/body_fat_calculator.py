from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N, log


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BodyFatCalculator(View):
    """
    Class-based view for Body Fat Calculator
    Uses US Navy and other formulas with NumPy/SymPy for precision.
    Enhanced with chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/body_fat_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Body Fat Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            gender = data.get('gender', 'male').lower()
            unit_system = data.get('unit_system', 'metric')
            age = int(data.get('age', 25))
            
            # Get measurements based on unit system using SymPy for precision
            if unit_system == 'imperial':
                height_ft = float(data.get('height_ft', 5))
                height_in = float(data.get('height_in', 10))
                height_cm = float(N((Float(height_ft, 15) * Float(12, 15) + Float(height_in, 15)) * Float(2.54, 15), 10))
                weight_lbs = float(data.get('weight', 160))
                weight_kg = float(N(Float(weight_lbs, 15) * Float(0.453592, 15), 10))
                
                waist_in = float(data.get('waist', 34))
                waist_cm = float(N(Float(waist_in, 15) * Float(2.54, 15), 10))
                neck_in = float(data.get('neck', 15))
                neck_cm = float(N(Float(neck_in, 15) * Float(2.54, 15), 10))
                
                if gender == 'female':
                    hip_in = float(data.get('hip', 38))
                    hip_cm = float(N(Float(hip_in, 15) * Float(2.54, 15), 10))
            else:
                height_cm = float(data.get('height', 175))
                weight_kg = float(data.get('weight', 70))
                waist_cm = float(data.get('waist', 86))
                neck_cm = float(data.get('neck', 38))
                if gender == 'female':
                    hip_cm = float(data.get('hip', 96))
            
            # Validation
            if height_cm < 100 or height_cm > 250:
                return JsonResponse({'success': False, 'error': 'Invalid height.'}, status=400)
            if weight_kg < 30 or weight_kg > 300:
                return JsonResponse({'success': False, 'error': 'Invalid weight.'}, status=400)
            if waist_cm < 40 or waist_cm > 200:
                return JsonResponse({'success': False, 'error': 'Invalid waist measurement.'}, status=400)
            if neck_cm <= 0:
                return JsonResponse({'success': False, 'error': 'Invalid neck measurement.'}, status=400)
            
            # US Navy Method - most accurate for general use
            # Uses SymPy log for precision
            if gender in ['male', 'm']:
                # Male formula: 495 / (1.0324 - 0.19077 × log10(waist - neck) + 0.15456 × log10(height)) - 450
                waist_neck_diff = Float(waist_cm - neck_cm, 15)
                height_val = Float(height_cm, 15)
                
                # Use SymPy log for precision
                log_waist_neck = N(log(waist_neck_diff, 10), 10)
                log_height = N(log(height_val, 10), 10)
                
                denominator = Float(1.0324, 15) - Float(0.19077, 15) * Float(log_waist_neck, 15) + Float(0.15456, 15) * Float(log_height, 15)
                body_fat_navy = float(N(Float(495, 15) / denominator - Float(450, 15), 10))
            else:
                # Female formula: 495 / (1.29579 - 0.35004 × log10(waist + hip - neck) + 0.22100 × log10(height)) - 450
                if 'hip_cm' not in locals():
                    return JsonResponse({'success': False, 'error': 'Hip measurement required for females.'}, status=400)
                
                waist_hip_neck_sum = Float(waist_cm + hip_cm - neck_cm, 15)
                height_val = Float(height_cm, 15)
                
                # Use SymPy log for precision
                log_waist_hip_neck = N(log(waist_hip_neck_sum, 10), 10)
                log_height = N(log(height_val, 10), 10)
                
                denominator = Float(1.29579, 15) - Float(0.35004, 15) * Float(log_waist_hip_neck, 15) + Float(0.22100, 15) * Float(log_height, 15)
                body_fat_navy = float(N(Float(495, 15) / denominator - Float(450, 15), 10))
            
            # BMI Method (less accurate but useful for comparison)
            height_m = height_cm / 100
            bmi = weight_kg / (height_m ** 2)
            
            if gender in ['male', 'm']:
                body_fat_bmi = 1.20 * bmi + 0.23 * age - 16.2
            else:
                body_fat_bmi = 1.20 * bmi + 0.23 * age - 5.4
            
            # Ensure body fat is within reasonable range
            body_fat = max(2, min(60, float(body_fat_navy)))
            
            # Calculate lean body mass and fat mass
            fat_mass = weight_kg * (body_fat / 100)
            lean_mass = weight_kg - fat_mass
            
            # Determine body fat category
            category, category_color = self.get_body_fat_category(body_fat, gender)
            
            # Ideal body fat range
            if gender in ['male', 'm']:
                ideal_range = {'min': 10, 'max': 20}
            else:
                ideal_range = {'min': 18, 'max': 28}
            
            # Calculate ideal weight at target body fat
            target_bf = (ideal_range['min'] + ideal_range['max']) / 2
            ideal_weight_kg = lean_mass / (1 - target_bf / 100)
            
            # Calculate scale position (0-100%)
            scale_position = self.calculate_scale_position(body_fat, gender)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                body_fat=body_fat,
                fat_mass=fat_mass,
                lean_mass=lean_mass,
                category_color=category_color,
                ideal_range=ideal_range,
                gender=gender
            )
            
            # Get color info
            color_info = self.get_color_info(category_color)
            
            result = {
                'success': True,
                'body_fat_percent': round(body_fat, 1),
                'method': 'US Navy',
                'bmi_method_result': round(body_fat_bmi, 1),
                'category': category,
                'category_color': category_color,
                'mass': {
                    'total_kg': round(weight_kg, 1),
                    'fat_kg': round(fat_mass, 1),
                    'lean_kg': round(lean_mass, 1)
                },
                'ideal_range': ideal_range,
                'ideal_weight_kg': round(ideal_weight_kg, 1),
                'bmi': round(bmi, 1),
                'gender': gender,
                'age': age,
                'scale_position': scale_position,
                'chart_data': chart_data,
                'color_info': color_info,
                'categories': [
                    {'name': 'Essential Fat', 'range': '2-5%' if gender in ['male', 'm'] else '10-13%'},
                    {'name': 'Athletes', 'range': '6-13%' if gender in ['male', 'm'] else '14-20%'},
                    {'name': 'Fitness', 'range': '14-17%' if gender in ['male', 'm'] else '21-24%'},
                    {'name': 'Average', 'range': '18-24%' if gender in ['male', 'm'] else '25-31%'},
                    {'name': 'Obese', 'range': '>25%' if gender in ['male', 'm'] else '>32%'}
                ]
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Body Fat Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_body_fat_category(self, body_fat, gender):
        """Determine body fat category and color"""
        if gender in ['male', 'm']:
            categories = [
                (5, 'Essential Fat', 'blue'),
                (13, 'Athletes', 'green'),
                (17, 'Fitness', 'teal'),
                (24, 'Average', 'yellow'),
                (100, 'Obese', 'red')
            ]
        else:
            categories = [
                (13, 'Essential Fat', 'blue'),
                (20, 'Athletes', 'green'),
                (24, 'Fitness', 'teal'),
                (31, 'Average', 'yellow'),
                (100, 'Obese', 'red')
            ]
        
        for threshold, cat_name, color in categories:
            if body_fat < threshold:
                return cat_name, color
        
        return 'Obese', 'red'
    
    def calculate_scale_position(self, body_fat, gender):
        """Calculate body fat indicator position on scale (0-100%)"""
        # Scale: 0% to max body fat (60% for display)
        max_display = 60
        position = (body_fat / max_display) * 100
        return min(100.0, max(0.0, float(position)))
    
    def get_color_info(self, category_color):
        """Get color information for the category"""
        color_map = {
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            },
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            },
            'teal': {
                'hex': '#14b8a6',
                'rgb': 'rgb(20, 184, 166)',
                'tailwind_classes': 'bg-teal-100 text-teal-800 border-teal-300'
            },
            'yellow': {
                'hex': '#eab308',
                'rgb': 'rgb(234, 179, 8)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300'
            },
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, body_fat, fat_mass, lean_mass, category_color, ideal_range, gender):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(category_color)
        
        # Body Fat Gauge Chart
        max_display = 60
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
        
        # Body Composition Chart (Fat vs Lean Mass)
        composition_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Fat Mass', 'Lean Mass'],
                'datasets': [{
                    'data': [round(fat_mass, 1), round(lean_mass, 1)],
                    'backgroundColor': ['#ef4444', '#10b981'],
                    'borderColor': ['#dc2626', '#059669'],
                    'borderWidth': 2
                }]
            }
        }
        
        # Body Fat Categories Chart
        if gender in ['male', 'm']:
            categories_data = [
                {'name': 'Essential Fat', 'max': 5, 'color': '#3b82f6'},
                {'name': 'Athletes', 'max': 13, 'color': '#10b981'},
                {'name': 'Fitness', 'max': 17, 'color': '#14b8a6'},
                {'name': 'Average', 'max': 24, 'color': '#eab308'},
                {'name': 'Obese', 'max': 60, 'color': '#ef4444'}
            ]
        else:
            categories_data = [
                {'name': 'Essential Fat', 'max': 13, 'color': '#3b82f6'},
                {'name': 'Athletes', 'max': 20, 'color': '#10b981'},
                {'name': 'Fitness', 'max': 24, 'color': '#14b8a6'},
                {'name': 'Average', 'max': 31, 'color': '#eab308'},
                {'name': 'Obese', 'max': 60, 'color': '#ef4444'}
            ]
        
        categories_labels = [cat['name'] for cat in categories_data]
        categories_values = []
        categories_colors = []
        
        current_category_index = 0
        for idx, cat_info in enumerate(categories_data):
            if body_fat <= cat_info['max']:
                current_category_index = idx
                categories_values.append(round(body_fat, 1))
                categories_colors.append(cat_info['color'])
            else:
                categories_values.append(0)
                categories_colors.append('#e5e7eb')
        
        categories_chart = {
            'type': 'bar',
            'data': {
                'labels': categories_labels,
                'datasets': [{
                    'label': 'Body Fat %',
                    'data': categories_values,
                    'backgroundColor': categories_colors,
                    'borderColor': [cat['color'] for cat in categories_data],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            },
            'current_category_index': current_category_index,
            'categories_info': categories_data
        }
        
        # Ideal Range Comparison Chart
        ideal_range_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Your Body Fat', 'Ideal Min', 'Ideal Max'],
                'datasets': [{
                    'label': 'Body Fat %',
                    'data': [
                        round(body_fat, 1),
                        round(ideal_range['min'], 1),
                        round(ideal_range['max'], 1)
                    ],
                    'backgroundColor': [color_info['hex'], '#10b981', '#10b981'],
                    'borderColor': [color_info['hex'], '#059669', '#059669'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'gauge_chart': gauge_chart,
            'composition_chart': composition_chart,
            'categories_chart': categories_chart,
            'ideal_range_chart': ideal_range_chart
        }
