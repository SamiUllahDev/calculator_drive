from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N, Pow


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HealthyWeightCalculator(View):
    """
    Class-based view for Healthy Weight Calculator
    Calculates healthy weight range based on BMI and height.
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/healthy_weight_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Healthy Weight Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            unit_system = data.get('unit_system', 'metric')
            height = float(data.get('height', 170))
            height_in = float(data.get('height_in', 0))
            
            # Convert to cm using SymPy for precision
            if unit_system == 'imperial':
                height_ft_sym = Float(height, 15)
                height_in_sym = Float(height_in, 15)
                height_cm = float(N((height_ft_sym * Float(12, 15) + height_in_sym) * Float(2.54, 15), 10))
            else:
                height_cm = height
            
            height_m = float(N(Float(height_cm, 15) / Float(100, 15), 10))
            height_m_sym = Float(height_m, 15)
            
            # Validation
            if height_cm < 100 or height_cm > 250:
                return JsonResponse({'success': False, 'error': 'Height must be between 100 and 250 cm (3\'3" and 8\'2").'}, status=400)
            
            # BMI ranges
            bmi_ranges = {
                'underweight': {'min': 0, 'max': 18.5, 'color': 'blue'},
                'normal': {'min': 18.5, 'max': 24.9, 'color': 'green'},
                'overweight': {'min': 25, 'max': 29.9, 'color': 'yellow'},
                'obese': {'min': 30, 'max': 100, 'color': 'red'}
            }
            
            # Calculate weight for each BMI category using SymPy
            weights = {}
            height_squared = Pow(height_m_sym, Float(2, 15))
            
            for category, bmi_range in bmi_ranges.items():
                min_bmi_sym = Float(bmi_range['min'], 15)
                max_bmi_sym = Float(bmi_range['max'], 15)
                
                min_weight_kg = float(N(min_bmi_sym * height_squared, 10))
                max_weight_kg = float(N(max_bmi_sym * height_squared, 10))
                
                if unit_system == 'imperial':
                    min_weight = float(N(Float(min_weight_kg, 15) / Float(0.453592, 15), 10))
                    max_weight = float(N(Float(max_weight_kg, 15) / Float(0.453592, 15), 10))
                else:
                    min_weight = min_weight_kg
                    max_weight = max_weight_kg
                
                weights[category] = {
                    'min': round(min_weight, 1),
                    'max': round(max_weight, 1),
                    'bmi_min': bmi_range['min'],
                    'bmi_max': bmi_range['max'],
                    'color': bmi_range['color']
                }
            
            # Ideal weight range (BMI 18.5-24.9)
            ideal_min_bmi = Float(18.5, 15)
            ideal_max_bmi = Float(24.9, 15)
            ideal_min_kg = float(N(ideal_min_bmi * height_squared, 10))
            ideal_max_kg = float(N(ideal_max_bmi * height_squared, 10))
            
            if unit_system == 'imperial':
                ideal_min = float(N(Float(ideal_min_kg, 15) / Float(0.453592, 15), 10))
                ideal_max = float(N(Float(ideal_max_kg, 15) / Float(0.453592, 15), 10))
                unit = 'lbs'
            else:
                ideal_min = ideal_min_kg
                ideal_max = ideal_max_kg
                unit = 'kg'
            
            # Calculate BMI values for visualization
            bmi_values = []
            for category, bmi_range in bmi_ranges.items():
                bmi_values.append({
                    'category': category,
                    'bmi_min': bmi_range['min'],
                    'bmi_max': bmi_range['max'],
                    'weight_min': weights[category]['min'],
                    'weight_max': weights[category]['max'],
                    'color': bmi_range['color']
                })
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                weights=weights,
                ideal_range={'min': ideal_min, 'max': ideal_max},
                unit=unit,
                height_cm=height_cm
            )
            
            # Get color info for ideal range
            color_info = self.get_color_info('green')
            
            result = {
                'success': True,
                'height_cm': round(height_cm, 1),
                'height_m': round(height_m, 2),
                'unit': unit,
                'ideal_range': {
                    'min': round(ideal_min, 1),
                    'max': round(ideal_max, 1)
                },
                'weight_ranges': weights,
                'bmi_values': bmi_values,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Healthy Weight Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_color_info(self, color_name):
        """Get color information for BMI category"""
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
        return color_map.get(color_name, color_map['green'])
    
    def prepare_chart_data(self, weights, ideal_range, unit, height_cm):
        """Prepare chart data for visualization"""
        
        # Weight Ranges Chart
        categories = ['Underweight', 'Normal', 'Overweight', 'Obese']
        colors = ['#3b82f6', '#10b981', '#eab308', '#ef4444']
        
        ranges_chart = {
            'type': 'bar',
            'data': {
                'labels': categories,
                'datasets': [
                    {
                        'label': 'Min Weight',
                        'data': [
                            weights['underweight']['min'],
                            weights['normal']['min'],
                            weights['overweight']['min'],
                            weights['obese']['min']
                        ],
                        'backgroundColor': colors,
                        'borderColor': colors,
                        'borderWidth': 2,
                        'borderRadius': 8
                    },
                    {
                        'label': 'Max Weight',
                        'data': [
                            weights['underweight']['max'],
                            weights['normal']['max'],
                            weights['overweight']['max'],
                            weights['obese']['max']
                        ],
                        'backgroundColor': [c.replace('ff', '80') for c in colors],  # Semi-transparent
                        'borderColor': colors,
                        'borderWidth': 2,
                        'borderRadius': 8
                    }
                ]
            }
        }
        
        # Ideal Range Chart
        ideal_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Ideal Weight Range'],
                'datasets': [{
                    'label': 'Ideal Range',
                    'data': [[ideal_range['min'], ideal_range['max']]],
                    'backgroundColor': '#10b981',
                    'borderColor': '#059669',
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # BMI Categories Distribution Chart
        bmi_distribution = {
            'type': 'doughnut',
            'data': {
                'labels': categories,
                'datasets': [{
                    'data': [
                        weights['underweight']['max'] - weights['underweight']['min'],
                        weights['normal']['max'] - weights['normal']['min'],
                        weights['overweight']['max'] - weights['overweight']['min'],
                        weights['obese']['max'] - weights['obese']['min']
                    ],
                    'backgroundColor': colors,
                    'borderColor': '#ffffff',
                    'borderWidth': 2
                }]
            }
        }
        
        # Weight Range Comparison Chart
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': categories,
                'datasets': [{
                    'label': 'Weight Range Span',
                    'data': [
                        weights['underweight']['max'] - weights['underweight']['min'],
                        weights['normal']['max'] - weights['normal']['min'],
                        weights['overweight']['max'] - weights['overweight']['min'],
                        weights['obese']['max'] - weights['obese']['min']
                    ],
                    'backgroundColor': colors,
                    'borderColor': colors,
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'ranges_chart': ranges_chart,
            'ideal_chart': ideal_chart,
            'bmi_distribution': bmi_distribution,
            'comparison_chart': comparison_chart
        }
