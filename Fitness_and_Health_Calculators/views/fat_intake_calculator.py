from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FatIntakeCalculator(View):
    """
    Class-based view for Fat Intake Calculator
    Calculates daily fat needs based on total calories and percentage.
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/fat_intake_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Fat Intake Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            total_calories = float(data.get('total_calories', 2000))
            fat_percent = float(data.get('fat_percent', 30))
            
            # Alternative: calculate from remaining macros
            protein_percent = float(data.get('protein_percent', 0))
            carb_percent = float(data.get('carb_percent', 0))
            
            # If protein and carbs provided, calculate fat as remainder
            if protein_percent > 0 and carb_percent > 0:
                fat_percent = 100 - protein_percent - carb_percent
            
            # Validation
            if total_calories <= 0 or total_calories > 10000:
                return JsonResponse({'success': False, 'error': 'Total calories must be between 1 and 10,000.'}, status=400)
            if fat_percent < 0 or fat_percent > 100:
                return JsonResponse({'success': False, 'error': 'Fat percentage must be between 0 and 100%.'}, status=400)
            if protein_percent < 0 or protein_percent > 100 or carb_percent < 0 or carb_percent > 100:
                return JsonResponse({'success': False, 'error': 'Macro percentages must be between 0 and 100%.'}, status=400)
            if protein_percent > 0 and carb_percent > 0 and (protein_percent + carb_percent) >= 100:
                return JsonResponse({'success': False, 'error': 'Protein and carb percentages cannot sum to 100% or more.'}, status=400)
            
            # Calculate calories from fat using SymPy for precision
            total_cal_sym = Float(total_calories, 15)
            fat_percent_sym = Float(fat_percent, 15)
            fat_calories = float(N(total_cal_sym * (fat_percent_sym / Float(100, 15)), 10))
            
            # Convert to grams (fat: 9 cal/g) using SymPy
            fat_grams = float(N(Float(fat_calories, 15) / Float(9, 15), 10))
            
            # Calculate saturated vs unsaturated (recommendation: max 10% saturated)
            saturated_fat_max = float(N(total_cal_sym * Float(0.10, 15) / Float(9, 15), 10))  # Max 10% of calories from saturated fat
            unsaturated_fat = max(0, fat_grams - saturated_fat_max)
            
            # Calculate per meal (assuming 3 meals + snacks)
            meals = {
                'breakfast': {
                    'grams': round(float(N(Float(fat_grams, 15) * Float(0.25, 15), 10)), 1),
                    'calories': round(float(N(Float(fat_calories, 15) * Float(0.25, 15), 10)))
                },
                'lunch': {
                    'grams': round(float(N(Float(fat_grams, 15) * Float(0.35, 15), 10)), 1),
                    'calories': round(float(N(Float(fat_calories, 15) * Float(0.35, 15), 10)))
                },
                'dinner': {
                    'grams': round(float(N(Float(fat_grams, 15) * Float(0.30, 15), 10)), 1),
                    'calories': round(float(N(Float(fat_calories, 15) * Float(0.30, 15), 10)))
                },
                'snacks': {
                    'grams': round(float(N(Float(fat_grams, 15) * Float(0.10, 15), 10)), 1),
                    'calories': round(float(N(Float(fat_calories, 15) * Float(0.10, 15), 10)))
                }
            }
            
            # Common fat sources (grams per serving)
            fat_sources = {
                'avocado': {'grams': 21, 'serving': '1 medium'},
                'olive_oil': {'grams': 14, 'serving': '1 tbsp'},
                'nuts': {'grams': 14, 'serving': '1 oz'},
                'peanut_butter': {'grams': 16, 'serving': '2 tbsp'},
                'salmon': {'grams': 12, 'serving': '100g'},
                'cheese': {'grams': 9, 'serving': '1 oz'},
                'eggs': {'grams': 5, 'serving': '1 large'},
                'coconut_oil': {'grams': 14, 'serving': '1 tbsp'}
            }
            
            # Calculate servings needed
            servings = {}
            fat_grams_sym = Float(fat_grams, 15)
            for source, info in fat_sources.items():
                servings[source] = round(float(N(fat_grams_sym / Float(info['grams'], 15), 10)), 1)
            
            # Daily recommendations
            recommendations = {
                'minimum': round(float(N(total_cal_sym * Float(0.20, 15) / Float(9, 15), 10))),  # 20% minimum
                'moderate': round(float(N(total_cal_sym * Float(0.30, 15) / Float(9, 15), 10))),  # 30% moderate
                'high': round(float(N(total_cal_sym * Float(0.40, 15) / Float(9, 15), 10)))  # 40% high
            }
            
            # Determine fat level color
            fat_level_color = self.get_fat_level_color(fat_percent)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                fat_percent=fat_percent,
                fat_grams=fat_grams,
                fat_calories=fat_calories,
                saturated_fat_max=saturated_fat_max,
                unsaturated_fat=unsaturated_fat,
                meals=meals,
                recommendations=recommendations,
                fat_level_color=fat_level_color
            )
            
            # Get color info
            color_info = self.get_color_info(fat_level_color)
            
            result = {
                'success': True,
                'total_calories': round(total_calories),
                'fat_percent': round(fat_percent, 1),
                'fat_grams': round(fat_grams, 1),
                'fat_calories': round(fat_calories),
                'saturated_fat_max': round(saturated_fat_max, 1),
                'unsaturated_fat': round(unsaturated_fat, 1),
                'meals': meals,
                'fat_sources': fat_sources,
                'servings_needed': servings,
                'recommendations': recommendations,
                'fat_level_color': fat_level_color,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Fat Intake Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_fat_level_color(self, fat_percent):
        """Determine color based on fat percentage"""
        if fat_percent < 20:
            return 'blue'  # Low fat
        elif fat_percent < 35:
            return 'green'  # Moderate
        else:
            return 'orange'  # High fat
    
    def get_color_info(self, fat_level_color):
        """Get color information for the fat level"""
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
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            }
        }
        return color_map.get(fat_level_color, color_map['green'])
    
    def prepare_chart_data(self, fat_percent, fat_grams, fat_calories, saturated_fat_max, unsaturated_fat, meals, recommendations, fat_level_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(fat_level_color)
        
        # Macro Distribution Chart
        macro_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Fat', 'Other Macros'],
                'datasets': [{
                    'data': [fat_percent, 100 - fat_percent],
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
                    'label': 'Fat (g)',
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
                'labels': ['Minimum (20%)', 'Moderate (30%)', 'High (40%)'],
                'datasets': [{
                    'label': 'Fat (g)',
                    'data': [
                        recommendations['minimum'],
                        recommendations['moderate'],
                        recommendations['high']
                    ],
                    'backgroundColor': ['#3b82f6', '#10b981', '#f97316'],
                    'borderColor': ['#2563eb', '#059669', '#ea580c'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Saturated vs Unsaturated Fat Chart
        fat_type_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Saturated Fat (Max)', 'Unsaturated Fat'],
                'datasets': [{
                    'data': [
                        round(saturated_fat_max, 1),
                        round(unsaturated_fat, 1)
                    ],
                    'backgroundColor': ['#ef4444', '#10b981'],
                    'borderColor': ['#dc2626', '#059669'],
                    'borderWidth': 2
                }]
            }
        }
        
        return {
            'macro_chart': macro_chart,
            'meal_chart': meal_chart,
            'recommendations_chart': recommendations_chart,
            'fat_type_chart': fat_type_chart
        }
