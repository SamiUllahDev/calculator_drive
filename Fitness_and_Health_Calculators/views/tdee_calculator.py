from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TdeeCalculator(View):
    """
    Class-based view for TDEE (Total Daily Energy Expenditure) Calculator
    Uses multiple formulas with SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/tdee_calculator.html'
    
    # Conversion constants using SymPy Float for precision
    LBS_TO_KG = Float('0.453592', 15)
    INCHES_TO_CM = Float('2.54', 15)
    CM_TO_M = Float('0.01', 15)
    
    # BMR formula constants using SymPy
    MIFFLIN_MALE_CONSTANT = Float('5', 15)
    MIFFLIN_FEMALE_CONSTANT = Float('-161', 15)
    HARRIS_MALE_CONSTANT = Float('88.362', 15)
    HARRIS_FEMALE_CONSTANT = Float('447.593', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'TDEE Calculator',
            'page_title': 'TDEE Calculator - Total Daily Energy Expenditure',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            age = int(data.get('age', 25))
            gender = data.get('gender', 'male').lower()
            unit_system = data.get('unit_system', 'metric')
            activity_level = data.get('activity_level', 'moderate')
            
            # Get measurements and convert to metric using SymPy
            if unit_system == 'imperial':
                height_ft = float(data.get('height_ft', 5))
                height_in = float(data.get('height_in', 10))
                weight_lbs = float(data.get('weight', 160))
                
                # Convert using SymPy
                total_inches_sympy = Float(height_ft * 12 + height_in, 15)
                height_cm_sympy = total_inches_sympy * self.INCHES_TO_CM
                height_cm = float(N(height_cm_sympy, 10))
                
                weight_sympy = Float(weight_lbs, 15) * self.LBS_TO_KG
                weight_kg = float(N(weight_sympy, 10))
            else:
                height_cm = float(data.get('height', 170))
                weight_kg = float(data.get('weight', 70))
            
            # Validation using NumPy
            age_array = np.array([age])
            height_array = np.array([height_cm])
            weight_array = np.array([weight_kg])
            
            if np.any(age_array < 15) or np.any(age_array > 80):
                return JsonResponse({'success': False, 'error': 'Age must be between 15 and 80.'}, status=400)
            if np.any(height_array < 100) or np.any(height_array > 250):
                return JsonResponse({'success': False, 'error': 'Invalid height. Must be between 100-250 cm.'}, status=400)
            if np.any(weight_array < 30) or np.any(weight_array > 300):
                return JsonResponse({'success': False, 'error': 'Invalid weight. Must be between 30-300 kg.'}, status=400)
            
            # Calculate BMR using SymPy for precision
            h_sympy = Float(height_cm, 15)
            w_sympy = Float(weight_kg, 15)
            a_sympy = Float(age, 15)
            
            # Mifflin-St Jeor (most accurate) using SymPy
            if gender in ['male', 'm']:
                bmr_mifflin_sympy = Float('10', 15) * w_sympy + Float('6.25', 15) * h_sympy - Float('5', 15) * a_sympy + self.MIFFLIN_MALE_CONSTANT
            else:
                bmr_mifflin_sympy = Float('10', 15) * w_sympy + Float('6.25', 15) * h_sympy - Float('5', 15) * a_sympy + self.MIFFLIN_FEMALE_CONSTANT
            
            bmr_mifflin = float(N(bmr_mifflin_sympy, 10))
            
            # Harris-Benedict (revised) using SymPy
            if gender in ['male', 'm']:
                bmr_harris_sympy = Float('13.397', 15) * w_sympy + Float('4.799', 15) * h_sympy - Float('5.677', 15) * a_sympy + self.HARRIS_MALE_CONSTANT
            else:
                bmr_harris_sympy = Float('9.247', 15) * w_sympy + Float('3.098', 15) * h_sympy - Float('4.330', 15) * a_sympy + self.HARRIS_FEMALE_CONSTANT
            
            bmr_harris = float(N(bmr_harris_sympy, 10))
            
            # Use Mifflin as primary
            bmr = bmr_mifflin
            
            # Activity multipliers using SymPy
            activity_multipliers = {
                'sedentary': Float('1.2', 15),          # Little or no exercise
                'light': Float('1.375', 15),             # Light exercise 1-3 days/week
                'moderate': Float('1.55', 15),           # Moderate exercise 3-5 days/week
                'active': Float('1.725', 15),            # Hard exercise 6-7 days/week
                'very_active': Float('1.9', 15),         # Very hard exercise, physical job
                'athlete': Float('2.0', 15)              # Professional athlete
            }
            
            multiplier_sympy = activity_multipliers.get(activity_level, Float('1.55', 15))
            multiplier = float(N(multiplier_sympy, 10))
            
            # Calculate TDEE using SymPy
            bmr_sympy = Float(bmr, 15)
            tdee_sympy = bmr_sympy * multiplier_sympy
            tdee = float(N(tdee_sympy, 10))
            
            # Calculate all activity level TDEEs using SymPy
            all_tdees = {}
            for level, mult_sympy in activity_multipliers.items():
                tdee_level_sympy = bmr_sympy * mult_sympy
                all_tdees[level] = round(float(N(tdee_level_sympy, 10)))
            
            # Calorie targets for different goals using SymPy
            targets = {
                'extreme_loss': round(float(N(tdee_sympy - Float('1000', 15), 10))),
                'loss': round(float(N(tdee_sympy - Float('500', 15), 10))),
                'mild_loss': round(float(N(tdee_sympy - Float('250', 15), 10))),
                'maintain': round(float(N(tdee_sympy, 10))),
                'mild_gain': round(float(N(tdee_sympy + Float('250', 15), 10))),
                'gain': round(float(N(tdee_sympy + Float('500', 15), 10))),
                'extreme_gain': round(float(N(tdee_sympy + Float('1000', 15), 10)))
            }
            
            # Macro calculations using SymPy (balanced approach)
            protein_percent = Float('0.30', 15)  # 30% protein
            fat_percent = Float('0.30', 15)      # 30% fat
            carb_percent = Float('0.40', 15)     # 40% carbs
            
            protein_cal_sympy = tdee_sympy * protein_percent
            fat_cal_sympy = tdee_sympy * fat_percent
            carb_cal_sympy = tdee_sympy * carb_percent
            
            # Convert calories to grams using SymPy
            protein_grams_sympy = protein_cal_sympy / Float('4', 15)  # 4 cal/g
            fat_grams_sympy = fat_cal_sympy / Float('9', 15)          # 9 cal/g
            carb_grams_sympy = carb_cal_sympy / Float('4', 15)        # 4 cal/g
            
            macros = {
                'protein': {
                    'grams': round(float(N(protein_grams_sympy, 10))),
                    'calories': round(float(N(protein_cal_sympy, 10))),
                    'percent': 30
                },
                'fat': {
                    'grams': round(float(N(fat_grams_sympy, 10))),
                    'calories': round(float(N(fat_cal_sympy, 10))),
                    'percent': 30
                },
                'carbs': {
                    'grams': round(float(N(carb_grams_sympy, 10))),
                    'calories': round(float(N(carb_cal_sympy, 10))),
                    'percent': 40
                }
            }
            
            # Get activity level category
            activity_category, activity_color, activity_description = self.get_activity_category(activity_level)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                bmr=bmr,
                tdee=tdee,
                all_tdees=all_tdees,
                targets=targets,
                macros=macros,
                activity_level=activity_level,
                activity_color=activity_color,
                bmr_mifflin=bmr_mifflin,
                bmr_harris=bmr_harris
            )
            
            # Get color info
            activity_color_info = self.get_color_info(activity_color)
            
            result = {
                'success': True,
                'bmr': round(bmr),
                'tdee': round(tdee),
                'bmr_formulas': {
                    'mifflin_st_jeor': round(bmr_mifflin),
                    'harris_benedict': round(bmr_harris)
                },
                'activity_level': activity_level,
                'activity_category': activity_category,
                'activity_color': activity_color,
                'activity_description': activity_description,
                'multiplier': multiplier,
                'all_tdees': all_tdees,
                'targets': targets,
                'macros': macros,
                'input': {
                    'age': age,
                    'gender': gender,
                    'height_cm': round(height_cm, 1),
                    'weight_kg': round(weight_kg, 1)
                },
                'statistics': {
                    'bmr': round(bmr),
                    'tdee': round(tdee),
                    'activity_multiplier': multiplier,
                    'calorie_deficit_500': round(float(N(tdee_sympy - Float('500', 15), 10))),
                    'calorie_surplus_500': round(float(N(tdee_sympy + Float('500', 15), 10)))
                },
                'chart_data': chart_data,
                'activity_color_info': activity_color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"TDEE Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_activity_category(self, activity_level):
        """Determine activity level category with detailed information"""
        categories = {
            'sedentary': ('Sedentary', 'gray', 'Little or no exercise. Office job, minimal physical activity.'),
            'light': ('Light Activity', 'blue', 'Light exercise 1-3 days per week. Walking, light jogging, or recreational activities.'),
            'moderate': ('Moderate Activity', 'green', 'Moderate exercise 3-5 days per week. Regular workouts, sports, or active lifestyle.'),
            'active': ('Active', 'yellow', 'Hard exercise 6-7 days per week. Intense workouts, competitive sports.'),
            'very_active': ('Very Active', 'orange', 'Very hard exercise, physical job. Daily intense exercise or physically demanding work.'),
            'athlete': ('Athlete', 'red', 'Professional athlete level. Multiple daily training sessions, competition preparation.')
        }
        return categories.get(activity_level, ('Moderate Activity', 'green', 'Moderate exercise level.'))
    
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
            'gray': {
                'hex': '#6b7280',
                'rgb': 'rgb(107, 114, 128)',
                'tailwind_classes': 'bg-gray-100 text-gray-800 border-gray-300'
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, bmr, tdee, all_tdees, targets, macros, activity_level, activity_color, bmr_mifflin=None, bmr_harris=None):
        """Prepare chart data for visualization"""
        activity_color_info = self.get_color_info(activity_color)
        
        # Use provided BMR values or default to main BMR
        if bmr_mifflin is None:
            bmr_mifflin = bmr
        if bmr_harris is None:
            bmr_harris = bmr
        
        # TDEE by Activity Level Chart
        activity_levels_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Sedentary', 'Light', 'Moderate', 'Active', 'Very Active', 'Athlete'],
                'datasets': [{
                    'label': 'TDEE (calories)',
                    'data': [
                        all_tdees['sedentary'],
                        all_tdees['light'],
                        all_tdees['moderate'],
                        all_tdees['active'],
                        all_tdees['very_active'],
                        all_tdees['athlete']
                    ],
                    'backgroundColor': ['#6b7280', '#3b82f6', '#10b981', '#eab308', '#f97316', '#ef4444'],
                    'borderColor': ['#4b5563', '#2563eb', '#059669', '#ca8a04', '#ea580c', '#dc2626'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Calorie Targets Chart
        targets_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Extreme Loss', 'Loss', 'Mild Loss', 'Maintain', 'Mild Gain', 'Gain', 'Extreme Gain'],
                'datasets': [{
                    'label': 'Calories',
                    'data': [
                        targets['extreme_loss'],
                        targets['loss'],
                        targets['mild_loss'],
                        targets['maintain'],
                        targets['mild_gain'],
                        targets['gain'],
                        targets['extreme_gain']
                    ],
                    'backgroundColor': ['#ef4444', '#f97316', '#eab308', '#10b981', '#3b82f6', '#6366f1', '#a855f7'],
                    'borderColor': ['#dc2626', '#ea580c', '#ca8a04', '#059669', '#2563eb', '#4f46e5', '#9333ea'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Macro Breakdown Chart
        macro_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Protein', 'Carbs', 'Fat'],
                'datasets': [{
                    'data': [macros['protein']['percent'], macros['carbs']['percent'], macros['fat']['percent']],
                    'backgroundColor': ['#10b981', '#eab308', '#ef4444'],
                    'borderColor': ['#059669', '#ca8a04', '#dc2626'],
                    'borderWidth': 2
                }]
            }
        }
        
        # BMR Comparison Chart
        bmr_comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Mifflin-St Jeor', 'Harris-Benedict'],
                'datasets': [{
                    'label': 'BMR (calories)',
                    'data': [round(bmr_mifflin), round(bmr_harris)],
                    'backgroundColor': ['#3b82f6', '#10b981'],
                    'borderColor': ['#2563eb', '#059669'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'activity_levels_chart': activity_levels_chart,
            'targets_chart': targets_chart,
            'macro_chart': macro_chart,
            'bmr_comparison_chart': bmr_comparison_chart
        }
