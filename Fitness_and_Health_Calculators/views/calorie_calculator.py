from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CalorieCalculator(View):
    """
    Class-based view for Calorie Calculator
    Calculates daily calorie needs based on goals using NumPy/SymPy.
    Enhanced with chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/calorie_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Calorie Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            age = int(data.get('age', 25))
            gender = data.get('gender', 'male').lower()
            unit_system = data.get('unit_system', 'metric')
            goal = data.get('goal', 'maintain')
            
            # Get height and weight using SymPy for precision
            if unit_system == 'imperial':
                height_ft = float(data.get('height_ft', 5))
                height_in = float(data.get('height_in', 10))
                weight_lbs = float(data.get('weight', 160))
                height_cm = float(N((Float(height_ft, 15) * Float(12, 15) + Float(height_in, 15)) * Float(2.54, 15), 10))
                weight_kg = float(N(Float(weight_lbs, 15) * Float(0.453592, 15), 10))
            else:
                height_cm = float(data.get('height', 170))
                weight_kg = float(data.get('weight', 70))
            
            activity_level = data.get('activity_level', 'moderate')
            
            # Validation
            if age < 15 or age > 80:
                return JsonResponse({'success': False, 'error': 'Age must be between 15 and 80.'}, status=400)
            if height_cm < 100 or height_cm > 250:
                return JsonResponse({'success': False, 'error': 'Invalid height.'}, status=400)
            if weight_kg < 30 or weight_kg > 300:
                return JsonResponse({'success': False, 'error': 'Invalid weight.'}, status=400)
            
            # Calculate BMR using Mifflin-St Jeor with NumPy
            h = np.array([height_cm])
            w = np.array([weight_kg])
            a = np.array([age])
            
            if gender in ['male', 'm']:
                bmr = float((10 * w + 6.25 * h - 5 * a + 5)[0])
            else:
                bmr = float((10 * w + 6.25 * h - 5 * a - 161)[0])
            
            # Activity multipliers
            multipliers = {
                'sedentary': 1.2,
                'light': 1.375,
                'moderate': 1.55,
                'active': 1.725,
                'very_active': 1.9
            }
            
            tdee = bmr * multipliers.get(activity_level, 1.55)
            
            # Calculate calories based on goal
            goal_adjustments = {
                'lose_fast': -1000,
                'lose': -500,
                'lose_slow': -250,
                'maintain': 0,
                'gain_slow': 250,
                'gain': 500,
                'gain_fast': 1000
            }
            
            adjustment = goal_adjustments.get(goal, 0)
            target_calories = tdee + adjustment
            
            # Calculate macros based on goal
            if 'lose' in goal:
                protein_ratio = 0.35
                fat_ratio = 0.30
                carb_ratio = 0.35
            elif 'gain' in goal:
                protein_ratio = 0.30
                fat_ratio = 0.25
                carb_ratio = 0.45
            else:
                protein_ratio = 0.30
                fat_ratio = 0.30
                carb_ratio = 0.40
            
            protein_cal = target_calories * protein_ratio
            fat_cal = target_calories * fat_ratio
            carb_cal = target_calories * carb_ratio
            
            protein_g = protein_cal / 4
            fat_g = fat_cal / 9
            carb_g = carb_cal / 4
            
            # Weekly projection
            if adjustment < 0:
                weekly_change = abs(adjustment) * 7 / 7700  # 7700 cal = 1 kg
                weekly_text = f"Lose ~{round(weekly_change, 2)} kg/week"
            elif adjustment > 0:
                weekly_change = adjustment * 7 / 7700
                weekly_text = f"Gain ~{round(weekly_change, 2)} kg/week"
            else:
                weekly_change = 0
                weekly_text = "Maintain weight"
            
            # Meal distribution
            meals = {
                'breakfast': round(target_calories * 0.25),
                'lunch': round(target_calories * 0.35),
                'dinner': round(target_calories * 0.30),
                'snacks': round(target_calories * 0.10)
            }
            
            # Determine goal color
            goal_color = self.get_goal_color(goal)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                bmr=bmr,
                tdee=tdee,
                target_calories=target_calories,
                macros={
                    'protein': round(protein_cal, 0),
                    'fat': round(fat_cal, 0),
                    'carbs': round(carb_cal, 0)
                },
                meals=meals,
                all_targets={
                    'lose_fast': round(tdee - 1000),
                    'lose': round(tdee - 500),
                    'lose_slow': round(tdee - 250),
                    'maintain': round(tdee),
                    'gain_slow': round(tdee + 250),
                    'gain': round(tdee + 500),
                    'gain_fast': round(tdee + 1000)
                },
                goal=goal,
                goal_color=goal_color
            )
            
            # Get color info
            color_info = self.get_color_info(goal_color)
            
            result = {
                'success': True,
                'bmr': round(bmr),
                'tdee': round(tdee),
                'target_calories': round(target_calories),
                'adjustment': adjustment,
                'goal': goal,
                'goal_color': goal_color,
                'macros': {
                    'protein': {'grams': round(protein_g), 'calories': round(protein_cal), 'percent': round(protein_ratio * 100)},
                    'fat': {'grams': round(fat_g), 'calories': round(fat_cal), 'percent': round(fat_ratio * 100)},
                    'carbs': {'grams': round(carb_g), 'calories': round(carb_cal), 'percent': round(carb_ratio * 100)}
                },
                'weekly_projection': {
                    'change_kg': round(weekly_change, 2),
                    'text': weekly_text
                },
                'meals': meals,
                'all_targets': {
                    'lose_fast': round(tdee - 1000),
                    'lose': round(tdee - 500),
                    'lose_slow': round(tdee - 250),
                    'maintain': round(tdee),
                    'gain_slow': round(tdee + 250),
                    'gain': round(tdee + 500),
                    'gain_fast': round(tdee + 1000)
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
            print(f"Calorie Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_goal_color(self, goal):
        """Determine color for goal"""
        color_map = {
            'lose_fast': 'red',
            'lose': 'orange',
            'lose_slow': 'yellow',
            'maintain': 'green',
            'gain_slow': 'blue',
            'gain': 'indigo',
            'gain_fast': 'purple'
        }
        return color_map.get(goal, 'green')
    
    def get_color_info(self, goal_color):
        """Get color information for the goal"""
        color_map = {
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            },
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            },
            'yellow': {
                'hex': '#eab308',
                'rgb': 'rgb(234, 179, 8)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300'
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
            },
            'indigo': {
                'hex': '#6366f1',
                'rgb': 'rgb(99, 102, 241)',
                'tailwind_classes': 'bg-indigo-100 text-indigo-800 border-indigo-300'
            },
            'purple': {
                'hex': '#8b5cf6',
                'rgb': 'rgb(139, 92, 246)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            }
        }
        return color_map.get(goal_color, color_map['green'])
    
    def prepare_chart_data(self, bmr, tdee, target_calories, macros, meals, all_targets, goal, goal_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(goal_color)
        
        # BMR vs TDEE vs Target Calories Chart
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['BMR', 'TDEE', 'Target Calories'],
                'datasets': [{
                    'label': 'Calories',
                    'data': [round(bmr, 0), round(tdee, 0), round(target_calories, 0)],
                    'backgroundColor': ['#6b7280', '#3b82f6', color_info['hex']],
                    'borderColor': ['#4b5563', '#2563eb', color_info['hex']],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Macros Pie Chart
        macros_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Protein', 'Carbs', 'Fat'],
                'datasets': [{
                    'data': [
                        macros['protein'],
                        macros['carbs'],
                        macros['fat']
                    ],
                    'backgroundColor': ['#ef4444', '#eab308', '#3b82f6'],
                    'borderColor': ['#dc2626', '#ca8a04', '#2563eb'],
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
                    'label': 'Calories',
                    'data': [
                        meals['breakfast'],
                        meals['lunch'],
                        meals['dinner'],
                        meals['snacks']
                    ],
                    'backgroundColor': ['#f59e0b', '#10b981', '#3b82f6', '#8b5cf6'],
                    'borderColor': ['#d97706', '#059669', '#2563eb', '#7c3aed'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # All Goals Comparison Chart
        goals_labels = ['Lose Fast', 'Lose', 'Lose Slow', 'Maintain', 'Gain Slow', 'Gain', 'Gain Fast']
        goals_data = [
            all_targets['lose_fast'],
            all_targets['lose'],
            all_targets['lose_slow'],
            all_targets['maintain'],
            all_targets['gain_slow'],
            all_targets['gain'],
            all_targets['gain_fast']
        ]
        goals_colors = []
        for idx, goal_key in enumerate(['lose_fast', 'lose', 'lose_slow', 'maintain', 'gain_slow', 'gain', 'gain_fast']):
            if goal_key == goal:
                goals_colors.append(color_info['hex'])
            else:
                goals_colors.append('#e5e7eb')
        
        goals_chart = {
            'type': 'bar',
            'data': {
                'labels': goals_labels,
                'datasets': [{
                    'label': 'Calories',
                    'data': goals_data,
                    'backgroundColor': goals_colors,
                    'borderColor': ['#dc2626', '#f97316', '#eab308', '#10b981', '#3b82f6', '#6366f1', '#8b5cf6'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'comparison_chart': comparison_chart,
            'macros_chart': macros_chart,
            'meal_chart': meal_chart,
            'goals_chart': goals_chart
        }
