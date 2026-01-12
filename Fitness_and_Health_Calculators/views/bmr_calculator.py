from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BmrCalculator(View):
    """
    Class-based view for BMR (Basal Metabolic Rate) Calculator
    Uses Mifflin-St Jeor and Harris-Benedict equations with NumPy/SymPy.
    Enhanced with chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/bmr_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'BMR Calculator',
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
            
            # Get height and weight based on unit system
            if unit_system == 'imperial':
                height_ft = float(data.get('height_ft', 5))
                height_in = float(data.get('height_in', 10))
                weight_lbs = float(data.get('weight', 160))
                # Convert to metric using SymPy for precision
                height_cm = float(N((Float(height_ft, 15) * Float(12, 15) + Float(height_in, 15)) * Float(2.54, 15), 10))
                weight_kg = float(N(Float(weight_lbs, 15) * Float(0.453592, 15), 10))
            else:
                height_cm = float(data.get('height', 170))
                weight_kg = float(data.get('weight', 70))
            
            activity_level = data.get('activity_level', 'sedentary')
            
            # Validation
            if age < 15 or age > 80:
                return JsonResponse({'success': False, 'error': 'Age must be between 15 and 80.'}, status=400)
            if height_cm < 100 or height_cm > 250:
                return JsonResponse({'success': False, 'error': 'Height must be between 100 and 250 cm.'}, status=400)
            if weight_kg < 30 or weight_kg > 300:
                return JsonResponse({'success': False, 'error': 'Weight must be between 30 and 300 kg.'}, status=400)
            
            # Use NumPy for vectorized calculations
            h = np.array([height_cm])
            w = np.array([weight_kg])
            a = np.array([age])
            
            # Mifflin-St Jeor Equation (most accurate)
            if gender in ['male', 'm']:
                bmr_mifflin = float((10 * w + 6.25 * h - 5 * a + 5)[0])
            else:
                bmr_mifflin = float((10 * w + 6.25 * h - 5 * a - 161)[0])
            
            # Harris-Benedict Equation (revised)
            if gender in ['male', 'm']:
                bmr_harris = float((13.397 * w + 4.799 * h - 5.677 * a + 88.362)[0])
            else:
                bmr_harris = float((9.247 * w + 3.098 * h - 4.330 * a + 447.593)[0])
            
            # Katch-McArdle Formula (if body fat known - we'll estimate)
            # Lean Body Mass estimation
            if gender in ['male', 'm']:
                bf_estimate = 0.19  # 19% body fat estimate for males
            else:
                bf_estimate = 0.25  # 25% body fat estimate for females
            
            lbm = weight_kg * (1 - bf_estimate)
            bmr_katch = 370 + (21.6 * lbm)
            
            # Use Mifflin-St Jeor as primary
            bmr = bmr_mifflin
            
            # Activity multipliers using SymPy for precision
            activity_multipliers = {
                'sedentary': Float('1.2'),      # Little or no exercise
                'light': Float('1.375'),         # Light exercise 1-3 days/week
                'moderate': Float('1.55'),       # Moderate exercise 3-5 days/week
                'active': Float('1.725'),        # Hard exercise 6-7 days/week
                'very_active': Float('1.9'),     # Very hard exercise, physical job
                'extra_active': Float('2.0')     # Professional athlete
            }
            
            multiplier = activity_multipliers.get(activity_level, Float('1.2'))
            tdee = float(N(Float(bmr, 15) * multiplier, 10))
            
            # Calculate calorie targets
            weight_loss = tdee - 500      # Lose ~0.5 kg/week
            mild_loss = tdee - 250        # Lose ~0.25 kg/week
            weight_gain = tdee + 500      # Gain ~0.5 kg/week
            mild_gain = tdee + 250        # Gain ~0.25 kg/week
            
            # Calculate macros (balanced diet)
            protein_g = weight_kg * 1.6   # 1.6g per kg for active people
            protein_cal = protein_g * 4
            fat_cal = tdee * 0.25         # 25% of calories from fat
            fat_g = fat_cal / 9
            carb_cal = tdee - protein_cal - fat_cal
            carb_g = carb_cal / 4
            
            # Determine activity level color
            activity_color = self.get_activity_color(activity_level)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                bmr=bmr,
                tdee=tdee,
                calorie_targets={
                    'extreme_loss': round(tdee - 1000, 0),
                    'weight_loss': round(weight_loss, 0),
                    'mild_loss': round(mild_loss, 0),
                    'maintain': round(tdee, 0),
                    'mild_gain': round(mild_gain, 0),
                    'weight_gain': round(weight_gain, 0)
                },
                macros={
                    'protein': round(protein_cal, 0),
                    'fat': round(fat_cal, 0),
                    'carbs': round(carb_cal, 0)
                },
                bmr_formulas={
                    'mifflin_st_jeor': round(bmr_mifflin, 0),
                    'harris_benedict': round(bmr_harris, 0),
                    'katch_mcardle': round(bmr_katch, 0)
                }
            )
            
            # Get color info
            color_info = self.get_color_info(activity_color)
            
            result = {
                'success': True,
                'bmr': round(bmr, 0),
                'bmr_formulas': {
                    'mifflin_st_jeor': round(bmr_mifflin, 0),
                    'harris_benedict': round(bmr_harris, 0),
                    'katch_mcardle': round(bmr_katch, 0)
                },
                'tdee': round(tdee, 0),
                'activity_level': activity_level,
                'activity_color': activity_color,
                'calorie_targets': {
                    'extreme_loss': round(tdee - 1000, 0),
                    'weight_loss': round(weight_loss, 0),
                    'mild_loss': round(mild_loss, 0),
                    'maintain': round(tdee, 0),
                    'mild_gain': round(mild_gain, 0),
                    'weight_gain': round(weight_gain, 0)
                },
                'macros': {
                    'protein': {'grams': round(protein_g, 0), 'calories': round(protein_cal, 0)},
                    'fat': {'grams': round(fat_g, 0), 'calories': round(fat_cal, 0)},
                    'carbs': {'grams': round(carb_g, 0), 'calories': round(carb_cal, 0)}
                },
                'input': {
                    'height_cm': round(height_cm, 1),
                    'weight_kg': round(weight_kg, 1),
                    'age': age,
                    'gender': gender
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
            print(f"BMR Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_activity_color(self, activity_level):
        """Determine color for activity level"""
        color_map = {
            'sedentary': 'blue',
            'light': 'green',
            'moderate': 'yellow',
            'active': 'orange',
            'very_active': 'red',
            'extra_active': 'purple'
        }
        return color_map.get(activity_level, 'blue')
    
    def get_color_info(self, activity_color):
        """Get color information for the activity level"""
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
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            },
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            },
            'purple': {
                'hex': '#a855f7',
                'rgb': 'rgb(168, 85, 247)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            }
        }
        return color_map.get(activity_color, color_map['blue'])
    
    def prepare_chart_data(self, bmr, tdee, calorie_targets, macros, bmr_formulas):
        """Prepare chart data for visualization"""
        # BMR vs TDEE Comparison Chart
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['BMR', 'TDEE'],
                'datasets': [{
                    'label': 'Calories',
                    'data': [round(bmr, 0), round(tdee, 0)],
                    'backgroundColor': ['#f97316', '#3b82f6'],
                    'borderColor': ['#ea580c', '#2563eb'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Calorie Targets Chart
        targets_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Extreme Loss', 'Weight Loss', 'Mild Loss', 'Maintain', 'Mild Gain', 'Weight Gain'],
                'datasets': [{
                    'label': 'Calories',
                    'data': [
                        calorie_targets['extreme_loss'],
                        calorie_targets['weight_loss'],
                        calorie_targets['mild_loss'],
                        calorie_targets['maintain'],
                        calorie_targets['mild_gain'],
                        calorie_targets['weight_gain']
                    ],
                    'backgroundColor': [
                        '#dc2626',  # Extreme loss - red
                        '#f97316',  # Weight loss - orange
                        '#eab308',  # Mild loss - yellow
                        '#10b981',  # Maintain - green
                        '#3b82f6',  # Mild gain - blue
                        '#8b5cf6'   # Weight gain - purple
                    ],
                    'borderColor': [
                        '#b91c1c', '#ea580c', '#ca8a04', '#059669', '#2563eb', '#7c3aed'
                    ],
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
                    'backgroundColor': ['#10b981', '#eab308', '#ef4444'],
                    'borderColor': ['#059669', '#ca8a04', '#dc2626'],
                    'borderWidth': 2
                }]
            }
        }
        
        # BMR Formulas Comparison Chart
        formulas_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Mifflin-St Jeor', 'Harris-Benedict', 'Katch-McArdle'],
                'datasets': [{
                    'label': 'BMR (calories)',
                    'data': [
                        bmr_formulas['mifflin_st_jeor'],
                        bmr_formulas['harris_benedict'],
                        bmr_formulas['katch_mcardle']
                    ],
                    'backgroundColor': ['#10b981', '#3b82f6', '#8b5cf6'],
                    'borderColor': ['#059669', '#2563eb', '#7c3aed'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'comparison_chart': comparison_chart,
            'targets_chart': targets_chart,
            'macros_chart': macros_chart,
            'formulas_chart': formulas_chart
        }
