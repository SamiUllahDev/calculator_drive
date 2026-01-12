from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MacroCalculator(View):
    """
    Class-based view for Macro Calculator
    Calculates macronutrient breakdown from total calories and percentages.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/macro_calculator.html'
    
    # Calorie per gram constants using SymPy Float for precision
    PROTEIN_CAL_PER_G = Float('4')
    FAT_CAL_PER_G = Float('9')
    CARBS_CAL_PER_G = Float('4')
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Macro Calculator',
            'page_title': 'Macro Calculator - Calculate Macronutrient Breakdown',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            total_calories = float(data.get('total_calories', 2000))
            protein_percent = float(data.get('protein_percent', 30))
            fat_percent = float(data.get('fat_percent', 30))
            carbs_percent = float(data.get('carbs_percent', 40))
            
            # Validation using NumPy
            calories_array = np.array([total_calories])
            percents_array = np.array([protein_percent, fat_percent, carbs_percent])
            
            if np.any(calories_array <= 0):
                return JsonResponse({'success': False, 'error': 'Total calories must be greater than zero.'}, status=400)
            if np.any(calories_array > 10000):
                return JsonResponse({'success': False, 'error': 'Total calories cannot exceed 10,000.'}, status=400)
            
            # Check if percentages sum to 100
            total_percent = float(np.sum(percents_array))
            if abs(total_percent - 100) > 0.1:  # Allow small rounding differences
                return JsonResponse({'success': False, 'error': f'Macronutrient percentages must sum to 100%. Current sum: {total_percent}%'}, status=400)
            
            if np.any(percents_array < 0):
                return JsonResponse({'success': False, 'error': 'Macronutrient percentages cannot be negative.'}, status=400)
            
            # Calculate calories per macro using SymPy for precision
            total_cal_sympy = Float(total_calories, 15)
            protein_ratio = Float(protein_percent, 15) / Float(100, 15)
            fat_ratio = Float(fat_percent, 15) / Float(100, 15)
            carbs_ratio = Float(carbs_percent, 15) / Float(100, 15)
            
            protein_calories = float(N(total_cal_sympy * protein_ratio, 10))
            fat_calories = float(N(total_cal_sympy * fat_ratio, 10))
            carbs_calories = float(N(total_cal_sympy * carbs_ratio, 10))
            
            # Convert to grams using SymPy (protein & carbs: 4 cal/g, fat: 9 cal/g)
            protein_grams = float(N(Float(protein_calories, 15) / self.PROTEIN_CAL_PER_G, 10))
            fat_grams = float(N(Float(fat_calories, 15) / self.FAT_CAL_PER_G, 10))
            carbs_grams = float(N(Float(carbs_calories, 15) / self.CARBS_CAL_PER_G, 10))
            
            # Calculate per meal using SymPy (assuming 3 meals + snacks)
            meal_ratios = {
                'breakfast': Float('0.25', 15),
                'lunch': Float('0.35', 15),
                'dinner': Float('0.30', 15),
                'snacks': Float('0.10', 15)
            }
            
            meals = {}
            for meal_name, ratio in meal_ratios.items():
                meals[meal_name] = {
                    'calories': round(float(N(total_cal_sympy * ratio, 10))),
                    'protein': round(float(N(Float(protein_grams, 15) * ratio, 10)), 1),
                    'fat': round(float(N(Float(fat_grams, 15) * ratio, 10)), 1),
                    'carbs': round(float(N(Float(carbs_grams, 15) * ratio, 10)), 1)
                }
            
            # Determine macro split category
            split_category, category_color, category_description = self.get_macro_split_category(
                protein_percent, fat_percent, carbs_percent
            )
            
            # Common macro splits for reference
            common_splits = {
                'balanced': {'protein': 30, 'fat': 30, 'carbs': 40, 'name': 'Balanced', 'description': 'Standard balanced diet'},
                'high_protein': {'protein': 40, 'fat': 30, 'carbs': 30, 'name': 'High Protein', 'description': 'For muscle building'},
                'low_carb': {'protein': 35, 'fat': 40, 'carbs': 25, 'name': 'Low Carb', 'description': 'Reduced carbohydrate intake'},
                'low_fat': {'protein': 30, 'fat': 20, 'carbs': 50, 'name': 'Low Fat', 'description': 'Reduced fat intake'},
                'keto': {'protein': 20, 'fat': 70, 'carbs': 10, 'name': 'Ketogenic', 'description': 'Very low carb, high fat'}
            }
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                protein_calories=protein_calories,
                fat_calories=fat_calories,
                carbs_calories=carbs_calories,
                protein_grams=protein_grams,
                fat_grams=fat_grams,
                carbs_grams=carbs_grams,
                total_calories=total_calories,
                meals=meals,
                category_color=category_color
            )
            
            # Get color info
            color_info = self.get_color_info(category_color)
            
            result = {
                'success': True,
                'total_calories': round(total_calories),
                'macros': {
                    'protein': {
                        'grams': round(protein_grams, 1),
                        'calories': round(protein_calories),
                        'percent': round(protein_percent, 1)
                    },
                    'fat': {
                        'grams': round(fat_grams, 1),
                        'calories': round(fat_calories),
                        'percent': round(fat_percent, 1)
                    },
                    'carbs': {
                        'grams': round(carbs_grams, 1),
                        'calories': round(carbs_calories),
                        'percent': round(carbs_percent, 1)
                    }
                },
                'meals': meals,
                'common_splits': common_splits,
                'split_category': split_category,
                'category_color': category_color,
                'category_description': category_description,
                'statistics': {
                    'protein_to_calorie_ratio': round(protein_calories / total_calories * 100, 1) if total_calories > 0 else 0,
                    'fat_to_calorie_ratio': round(fat_calories / total_calories * 100, 1) if total_calories > 0 else 0,
                    'carbs_to_calorie_ratio': round(carbs_calories / total_calories * 100, 1) if total_calories > 0 else 0,
                    'total_grams': round(protein_grams + fat_grams + carbs_grams, 1)
                },
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Macro Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_macro_split_category(self, protein_percent, fat_percent, carbs_percent):
        """Determine macro split category based on percentages"""
        # High protein
        if protein_percent >= 35:
            return 'High Protein', 'blue', 'High protein split ideal for muscle building and satiety. Great for active individuals and athletes.'
        # Low carb / Keto
        elif carbs_percent <= 15:
            return 'Low Carb/Keto', 'purple', 'Very low carbohydrate split, typically ketogenic. High fat intake for energy.'
        # Low carb
        elif carbs_percent <= 30:
            return 'Low Carb', 'indigo', 'Reduced carbohydrate intake. Good for weight loss and blood sugar control.'
        # Low fat
        elif fat_percent <= 25:
            return 'Low Fat', 'green', 'Reduced fat intake. Higher carbohydrate and protein focus.'
        # Balanced
        elif 25 <= protein_percent <= 35 and 25 <= fat_percent <= 35 and 30 <= carbs_percent <= 45:
            return 'Balanced', 'green', 'Well-balanced macronutrient distribution. Suitable for most people and goals.'
        # High fat
        elif fat_percent >= 45:
            return 'High Fat', 'orange', 'Higher fat intake. May be part of low-carb or ketogenic approach.'
        # High carb
        elif carbs_percent >= 50:
            return 'High Carb', 'yellow', 'Higher carbohydrate intake. Good for endurance athletes and active individuals.'
        else:
            return 'Custom', 'gray', 'Custom macronutrient split tailored to your specific needs.'
    
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
            'yellow': {
                'hex': '#f59e0b',
                'rgb': 'rgb(245, 158, 11)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300'
            },
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            },
            'purple': {
                'hex': '#8b5cf6',
                'rgb': 'rgb(139, 92, 246)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            },
            'indigo': {
                'hex': '#6366f1',
                'rgb': 'rgb(99, 102, 241)',
                'tailwind_classes': 'bg-indigo-100 text-indigo-800 border-indigo-300'
            },
            'gray': {
                'hex': '#6b7280',
                'rgb': 'rgb(107, 114, 128)',
                'tailwind_classes': 'bg-gray-100 text-gray-800 border-gray-300'
            }
        }
        return color_map.get(category_color, color_map['green'])
    
    def prepare_chart_data(self, protein_calories, fat_calories, carbs_calories, protein_grams, fat_grams, carbs_grams, total_calories, meals, category_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(category_color)
        
        # Macro Breakdown Doughnut Chart (Calories)
        macro_calories_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Protein', 'Fat', 'Carbs'],
                'datasets': [{
                    'data': [
                        round(protein_calories, 0),
                        round(fat_calories, 0),
                        round(carbs_calories, 0)
                    ],
                    'backgroundColor': ['#2563eb', '#f59e0b', '#16a34a'],
                    'borderColor': ['#1e40af', '#d97706', '#15803d'],
                    'borderWidth': 2
                }]
            },
            'center_text': {
                'value': round(total_calories, 0),
                'label': 'Total Calories',
                'color': color_info['hex']
            }
        }
        
        # Macro Grams Bar Chart
        macro_grams_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Protein', 'Fat', 'Carbs'],
                'datasets': [{
                    'label': 'Grams',
                    'data': [
                        round(protein_grams, 1),
                        round(fat_grams, 1),
                        round(carbs_grams, 1)
                    ],
                    'backgroundColor': ['#2563eb', '#f59e0b', '#16a34a'],
                    'borderColor': ['#1e40af', '#d97706', '#15803d'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Meal Distribution Chart
        meal_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Breakfast', 'Lunch', 'Dinner', 'Snacks'],
                'datasets': [{
                    'label': 'Calories',
                    'data': [
                        meals['breakfast']['calories'],
                        meals['lunch']['calories'],
                        meals['dinner']['calories'],
                        meals['snacks']['calories']
                    ],
                    'backgroundColor': ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b'],
                    'borderColor': ['#2563eb', '#059669', '#7c3aed', '#d97706'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Macro Percentage Comparison Chart
        percentage_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Protein %', 'Fat %', 'Carbs %'],
                'datasets': [{
                    'label': 'Percentage',
                    'data': [
                        round((protein_calories / total_calories) * 100, 1) if total_calories > 0 else 0,
                        round((fat_calories / total_calories) * 100, 1) if total_calories > 0 else 0,
                        round((carbs_calories / total_calories) * 100, 1) if total_calories > 0 else 0
                    ],
                    'backgroundColor': ['#2563eb', '#f59e0b', '#16a34a'],
                    'borderColor': ['#1e40af', '#d97706', '#15803d'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'macro_calories_chart': macro_calories_chart,
            'macro_grams_chart': macro_grams_chart,
            'meal_chart': meal_chart,
            'percentage_chart': percentage_chart
        }
