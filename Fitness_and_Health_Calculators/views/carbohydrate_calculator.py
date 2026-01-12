from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CarbohydrateCalculator(View):
    """
    Class-based view for Carbohydrate Calculator
    Calculates daily carbohydrate needs based on total calories and percentage.
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/carbohydrate_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Carbohydrate Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            total_calories = float(data.get('total_calories', 2000))
            carb_percent = float(data.get('carb_percent', 40))
            
            # Alternative: calculate from remaining macros
            protein_percent = float(data.get('protein_percent', 0))
            fat_percent = float(data.get('fat_percent', 0))
            
            # If protein and fat provided, calculate carbs as remainder
            if protein_percent > 0 and fat_percent > 0:
                carb_percent = 100 - protein_percent - fat_percent
            
            # Validation
            if total_calories <= 0 or total_calories > 10000:
                return JsonResponse({'success': False, 'error': 'Total calories must be between 1 and 10,000.'}, status=400)
            if carb_percent < 0 or carb_percent > 100:
                return JsonResponse({'success': False, 'error': 'Carbohydrate percentage must be between 0 and 100%.'}, status=400)
            if protein_percent < 0 or protein_percent > 100 or fat_percent < 0 or fat_percent > 100:
                return JsonResponse({'success': False, 'error': 'Macro percentages must be between 0 and 100%.'}, status=400)
            if protein_percent > 0 and fat_percent > 0 and (protein_percent + fat_percent) >= 100:
                return JsonResponse({'success': False, 'error': 'Protein and fat percentages cannot sum to 100% or more.'}, status=400)
            
            # Calculate calories from carbs using SymPy for precision
            total_cal_sym = Float(total_calories, 15)
            carb_percent_sym = Float(carb_percent, 15)
            carb_calories = float(N(total_cal_sym * (carb_percent_sym / Float(100, 15)), 10))
            
            # Convert to grams (carbs: 4 cal/g) using SymPy
            carb_grams = float(N(Float(carb_calories, 15) / Float(4, 15), 10))
            
            # Calculate per meal (assuming 3 meals + snacks)
            meals = {
                'breakfast': {
                    'grams': round(float(N(Float(carb_grams, 15) * Float(0.25, 15), 10)), 1),
                    'calories': round(float(N(Float(carb_calories, 15) * Float(0.25, 15), 10)))
                },
                'lunch': {
                    'grams': round(float(N(Float(carb_grams, 15) * Float(0.35, 15), 10)), 1),
                    'calories': round(float(N(Float(carb_calories, 15) * Float(0.35, 15), 10)))
                },
                'dinner': {
                    'grams': round(float(N(Float(carb_grams, 15) * Float(0.30, 15), 10)), 1),
                    'calories': round(float(N(Float(carb_calories, 15) * Float(0.30, 15), 10)))
                },
                'snacks': {
                    'grams': round(float(N(Float(carb_grams, 15) * Float(0.10, 15), 10)), 1),
                    'calories': round(float(N(Float(carb_calories, 15) * Float(0.10, 15), 10)))
                }
            }
            
            # Common carb sources (grams per serving)
            carb_sources = {
                'rice': {'grams': 45, 'serving': '1 cup cooked'},
                'oats': {'grams': 27, 'serving': '1/2 cup dry'},
                'bread': {'grams': 15, 'serving': '1 slice'},
                'pasta': {'grams': 43, 'serving': '1 cup cooked'},
                'potato': {'grams': 37, 'serving': '1 medium'},
                'banana': {'grams': 27, 'serving': '1 medium'},
                'sweet_potato': {'grams': 24, 'serving': '1 medium'},
                'quinoa': {'grams': 39, 'serving': '1 cup cooked'}
            }
            
            # Calculate servings needed
            servings = {}
            carb_grams_sym = Float(carb_grams, 15)
            for source, info in carb_sources.items():
                servings[source] = round(float(N(carb_grams_sym / Float(info['grams'], 15), 10)), 1)
            
            # Daily recommendations by activity level
            recommendations = {
                'low_carb': round(float(N(total_cal_sym * Float(0.10, 15) / Float(4, 15), 10))),  # 10% of calories
                'moderate': round(float(N(total_cal_sym * Float(0.40, 15) / Float(4, 15), 10))),  # 40% of calories
                'high_carb': round(float(N(total_cal_sym * Float(0.60, 15) / Float(4, 15), 10)))  # 60% of calories
            }
            
            # Determine carb level color
            carb_level_color = self.get_carb_level_color(carb_percent)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                carb_percent=carb_percent,
                carb_grams=carb_grams,
                carb_calories=carb_calories,
                meals=meals,
                recommendations=recommendations,
                carb_level_color=carb_level_color
            )
            
            # Get color info
            color_info = self.get_color_info(carb_level_color)
            
            result = {
                'success': True,
                'total_calories': round(total_calories),
                'carb_percent': round(carb_percent, 1),
                'carb_grams': round(carb_grams, 1),
                'carb_calories': round(carb_calories),
                'meals': meals,
                'carb_sources': carb_sources,
                'servings_needed': servings,
                'recommendations': recommendations,
                'carb_level_color': carb_level_color,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Carbohydrate Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_carb_level_color(self, carb_percent):
        """Determine color based on carb percentage"""
        if carb_percent < 20:
            return 'red'  # Low carb
        elif carb_percent < 45:
            return 'green'  # Moderate
        else:
            return 'blue'  # High carb
    
    def get_color_info(self, carb_level_color):
        """Get color information for the carb level"""
        color_map = {
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            },
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            },
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            }
        }
        return color_map.get(carb_level_color, color_map['green'])
    
    def prepare_chart_data(self, carb_percent, carb_grams, carb_calories, meals, recommendations, carb_level_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(carb_level_color)
        
        # Macro Distribution Chart (if we had protein/fat data)
        macro_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Carbohydrates', 'Other Macros'],
                'datasets': [{
                    'data': [carb_percent, 100 - carb_percent],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderColor': [color_info['hex'], '#d1d5db'],
                    'borderWidth': 2
                }]
            }
        }
        
        # Meal Distribution Chart
        meal_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Breakfast', 'Lunch', 'Dinner', 'Snacks'],
                'datasets': [{
                    'label': 'Carbohydrates (g)',
                    'data': [
                        meals['breakfast']['grams'],
                        meals['lunch']['grams'],
                        meals['dinner']['grams'],
                        meals['snacks']['grams']
                    ],
                    'backgroundColor': ['#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'],
                    'borderColor': ['#d97706', '#059669', '#2563eb', '#7c3aed'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Recommendations Comparison Chart
        recommendations_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Low Carb (10%)', 'Moderate (40%)', 'High Carb (60%)'],
                'datasets': [{
                    'label': 'Carbohydrates (g)',
                    'data': [
                        recommendations['low_carb'],
                        recommendations['moderate'],
                        recommendations['high_carb']
                    ],
                    'backgroundColor': ['#ef4444', '#10b981', '#3b82f6'],
                    'borderColor': ['#dc2626', '#059669', '#2563eb'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Percentage Range Chart
        percentage_ranges = []
        percentage_labels = []
        percentage_colors = []
        
        ranges = [
            (0, 20, 'Low Carb', '#ef4444'),
            (20, 45, 'Moderate', '#10b981'),
            (45, 100, 'High Carb', '#3b82f6')
        ]
        
        for min_val, max_val, label, color in ranges:
            percentage_labels.append(label)
            if min_val <= carb_percent < max_val:
                percentage_ranges.append(100)
                percentage_colors.append(color)
            else:
                percentage_ranges.append(0)
                percentage_colors.append('#e5e7eb')
        
        percentage_chart = {
            'type': 'bar',
            'data': {
                'labels': percentage_labels,
                'datasets': [{
                    'label': 'Your Range',
                    'data': percentage_ranges,
                    'backgroundColor': percentage_colors,
                    'borderColor': percentage_colors,
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'macro_chart': macro_chart,
            'meal_chart': meal_chart,
            'recommendations_chart': recommendations_chart,
            'percentage_chart': percentage_chart
        }
