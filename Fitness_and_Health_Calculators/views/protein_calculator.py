from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProteinCalculator(View):
    """
    Class-based view for Protein Calculator
    Calculates daily protein needs based on body weight, activity level, and goals.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/protein_calculator.html'
    
    # Conversion constants using SymPy Float for precision
    LBS_TO_KG = Float('0.453592', 15)
    CALORIES_PER_GRAM_PROTEIN = Float('4', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Protein Calculator',
            'page_title': 'Protein Calculator - Daily Protein Needs Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            unit_system = data.get('unit_system', 'metric')
            weight = float(data.get('weight', 70))
            activity_level = data.get('activity_level', 'moderate')
            goal = data.get('goal', 'maintain')
            body_fat_percent = float(data.get('body_fat_percent', 0))  # Optional
            
            # Convert to kg using SymPy for precision
            if unit_system == 'imperial':
                weight_sympy = Float(weight, 15) * self.LBS_TO_KG
                weight_kg = float(N(weight_sympy, 10))
            else:
                weight_kg = weight
            
            # Validation using NumPy
            weight_array = np.array([weight_kg])
            if np.any(weight_array <= 0):
                return JsonResponse({'success': False, 'error': 'Weight must be greater than zero.'}, status=400)
            if np.any(weight_array > 300):
                return JsonResponse({'success': False, 'error': 'Weight cannot exceed 300 kg.'}, status=400)
            
            # Calculate lean body mass using SymPy if body fat % provided
            lean_body_mass = weight_kg
            if body_fat_percent > 0 and body_fat_percent < 100:
                body_fat_sympy = Float(body_fat_percent, 15)
                lean_body_mass_sympy = Float(weight_kg, 15) * (Float('1', 15) - body_fat_sympy / Float('100', 15))
                lean_body_mass = float(N(lean_body_mass_sympy, 10))
            
            # Base protein recommendations (grams per kg of body weight) using SymPy
            base_protein = {
                'sedentary': Float('0.8', 15),      # RDA minimum
                'light': Float('1.0', 15),          # Light activity
                'moderate': Float('1.2', 15),       # Moderate activity
                'active': Float('1.4', 15),         # Active/athletic
                'very_active': Float('1.6', 15),    # Very active/bodybuilder
                'athlete': Float('1.8', 15)         # Elite athlete
            }
            
            # Goal adjustments using SymPy
            goal_multipliers = {
                'lose': Float('1.2', 15),           # Higher protein for weight loss
                'maintain': Float('1.0', 15),
                'gain': Float('1.1', 15),           # Slightly higher for muscle gain
                'cut': Float('1.3', 15)             # High protein for cutting
            }
            
            base_multiplier = base_protein.get(activity_level, Float('1.2', 15))
            goal_multiplier = goal_multipliers.get(goal, Float('1.0', 15))
            
            # Calculate protein needs using SymPy
            protein_per_kg_sympy = base_multiplier * goal_multiplier
            protein_per_kg = float(N(protein_per_kg_sympy, 10))
            
            weight_sympy = Float(weight_kg, 15)
            protein_grams_sympy = weight_sympy * protein_per_kg_sympy
            protein_grams = float(N(protein_grams_sympy, 10))
            
            # Alternative calculation using lean body mass (if provided)
            protein_from_lbm = 0
            if body_fat_percent > 0:
                lean_body_mass_sympy = Float(lean_body_mass, 15)
                protein_from_lbm_sympy = lean_body_mass_sympy * protein_per_kg_sympy
                protein_from_lbm = float(N(protein_from_lbm_sympy, 10))
            
            # Calculate calories from protein using SymPy
            protein_calories_sympy = protein_grams_sympy * self.CALORIES_PER_GRAM_PROTEIN
            protein_calories = float(N(protein_calories_sympy, 10))
            
            # Meal distribution (assuming 4-5 meals) using SymPy
            meals = {
                'breakfast': round(float(N(protein_grams_sympy * Float('0.20', 15), 10)), 1),
                'lunch': round(float(N(protein_grams_sympy * Float('0.30', 15), 10)), 1),
                'dinner': round(float(N(protein_grams_sympy * Float('0.30', 15), 10)), 1),
                'snacks': round(float(N(protein_grams_sympy * Float('0.20', 15), 10)), 1)
            }
            
            # Common protein sources (grams per serving)
            protein_sources = {
                'chicken_breast': {'grams': 31, 'serving': '100g', 'color': 'blue'},
                'salmon': {'grams': 25, 'serving': '100g', 'color': 'pink'},
                'eggs': {'grams': 6, 'serving': '1 large egg', 'color': 'yellow'},
                'greek_yogurt': {'grams': 10, 'serving': '100g', 'color': 'purple'},
                'protein_powder': {'grams': 25, 'serving': '1 scoop', 'color': 'green'},
                'lean_beef': {'grams': 26, 'serving': '100g', 'color': 'red'},
                'tofu': {'grams': 8, 'serving': '100g', 'color': 'indigo'},
                'lentils': {'grams': 9, 'serving': '100g', 'color': 'orange'}
            }
            
            # Calculate servings needed using SymPy
            servings = {}
            for source, info in protein_sources.items():
                servings_sympy = protein_grams_sympy / Float(info['grams'], 15)
                servings[source] = round(float(N(servings_sympy, 10)), 1)
            
            # Get activity level category
            activity_category, activity_color, activity_description = self.get_activity_category(activity_level)
            
            # Get goal category
            goal_category, goal_color, goal_description = self.get_goal_category(goal)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                protein_grams=protein_grams,
                protein_per_kg=protein_per_kg,
                meals=meals,
                protein_sources=protein_sources,
                servings=servings,
                activity_color=activity_color,
                goal_color=goal_color
            )
            
            # Get color info
            activity_color_info = self.get_color_info(activity_color)
            goal_color_info = self.get_color_info(goal_color)
            
            result = {
                'success': True,
                'weight_kg': round(weight_kg, 1),
                'activity_level': activity_level,
                'activity_category': activity_category,
                'activity_color': activity_color,
                'activity_description': activity_description,
                'goal': goal,
                'goal_category': goal_category,
                'goal_color': goal_color,
                'goal_description': goal_description,
                'protein_grams': round(protein_grams, 1),
                'protein_per_kg': round(protein_per_kg, 2),
                'protein_calories': round(protein_calories),
                'lean_body_mass': round(lean_body_mass, 1) if body_fat_percent > 0 else None,
                'protein_from_lbm': round(protein_from_lbm, 1) if body_fat_percent > 0 else None,
                'meals': meals,
                'protein_sources': protein_sources,
                'servings_needed': servings,
                'recommendations': {
                    'minimum': round(float(N(Float(weight_kg, 15) * Float('0.8', 15), 10)), 1),
                    'moderate': round(float(N(Float(weight_kg, 15) * Float('1.2', 15), 10)), 1),
                    'high': round(float(N(Float(weight_kg, 15) * Float('1.6', 15), 10)), 1),
                    'very_high': round(float(N(Float(weight_kg, 15) * Float('2.0', 15), 10)), 1)
                },
                'statistics': {
                    'protein_grams': round(protein_grams, 1),
                    'protein_per_kg': round(protein_per_kg, 2),
                    'protein_calories': round(protein_calories),
                    'total_meals': 4,
                    'avg_per_meal': round(protein_grams / 4, 1)
                },
                'chart_data': chart_data,
                'activity_color_info': activity_color_info,
                'goal_color_info': goal_color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Protein Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_activity_category(self, activity_level):
        """Determine activity level category with detailed information"""
        categories = {
            'sedentary': ('Sedentary', 'gray', 'Little to no exercise. Office work, minimal physical activity.'),
            'light': ('Light Activity', 'blue', 'Light exercise 1-3 days per week. Walking, light jogging, or recreational activities.'),
            'moderate': ('Moderate Activity', 'green', 'Moderate exercise 3-5 days per week. Regular workouts, sports, or active lifestyle.'),
            'active': ('Active', 'yellow', 'Active exercise 6-7 days per week. Intense workouts, competitive sports, or physically demanding job.'),
            'very_active': ('Very Active', 'orange', 'Very active lifestyle. Physical job, daily intense exercise, or multiple training sessions.'),
            'athlete': ('Elite Athlete', 'red', 'Elite athlete level. Professional training, multiple daily sessions, competition preparation.')
        }
        return categories.get(activity_level, ('Moderate Activity', 'green', 'Moderate exercise level.'))
    
    def get_goal_category(self, goal):
        """Determine goal category with detailed information"""
        categories = {
            'lose': ('Weight Loss', 'blue', 'Higher protein intake helps preserve muscle mass during calorie deficit and increases satiety.'),
            'maintain': ('Maintain Weight', 'green', 'Standard protein intake to maintain current muscle mass and support daily activities.'),
            'gain': ('Muscle Gain', 'purple', 'Slightly higher protein intake to support muscle growth and recovery from training.'),
            'cut': ('Cutting', 'orange', 'High protein intake to preserve muscle mass during aggressive fat loss phase.')
        }
        return categories.get(goal, ('Maintain Weight', 'green', 'Standard protein intake.'))
    
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
            'purple': {
                'hex': '#a855f7',
                'rgb': 'rgb(168, 85, 247)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            },
            'pink': {
                'hex': '#ec4899',
                'rgb': 'rgb(236, 72, 153)',
                'tailwind_classes': 'bg-pink-100 text-pink-800 border-pink-300'
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
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, protein_grams, protein_per_kg, meals, protein_sources, servings, activity_color, goal_color):
        """Prepare chart data for visualization"""
        activity_color_info = self.get_color_info(activity_color)
        goal_color_info = self.get_color_info(goal_color)
        
        # Meal Distribution Chart
        meal_distribution_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Breakfast', 'Lunch', 'Dinner', 'Snacks'],
                'datasets': [{
                    'data': [
                        meals['breakfast'],
                        meals['lunch'],
                        meals['dinner'],
                        meals['snacks']
                    ],
                    'backgroundColor': ['#3b82f6', '#10b981', '#a855f7', '#eab308'],
                    'borderColor': ['#2563eb', '#059669', '#9333ea', '#ca8a04'],
                    'borderWidth': 2
                }]
            }
        }
        
        # Protein Recommendations Comparison Chart
        recommendations_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Minimum (RDA)', 'Moderate', 'High', 'Very High', 'Your Needs'],
                'datasets': [{
                    'label': 'Protein (g)',
                    'data': [
                        round(protein_grams / protein_per_kg * 0.8, 1),
                        round(protein_grams / protein_per_kg * 1.2, 1),
                        round(protein_grams / protein_per_kg * 1.6, 1),
                        round(protein_grams / protein_per_kg * 2.0, 1),
                        round(protein_grams, 1)
                    ],
                    'backgroundColor': ['#6b7280', '#3b82f6', '#10b981', '#a855f7', activity_color_info['hex']],
                    'borderColor': ['#4b5563', '#2563eb', '#059669', '#9333ea', activity_color_info['hex']],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Protein Sources Comparison Chart
        source_names = {
            'chicken_breast': 'Chicken',
            'salmon': 'Salmon',
            'eggs': 'Eggs',
            'greek_yogurt': 'Yogurt',
            'protein_powder': 'Powder',
            'lean_beef': 'Beef',
            'tofu': 'Tofu',
            'lentils': 'Lentils'
        }
        
        sources_chart = {
            'type': 'bar',
            'data': {
                'labels': [source_names.get(k, k) for k in protein_sources.keys()],
                'datasets': [{
                    'label': 'Servings Needed',
                    'data': [servings[k] for k in protein_sources.keys()],
                    'backgroundColor': [self.get_color_info(protein_sources[k]['color'])['hex'] for k in protein_sources.keys()],
                    'borderColor': [self.get_color_info(protein_sources[k]['color'])['hex'] for k in protein_sources.keys()],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Protein per Meal Chart
        meal_bar_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Breakfast', 'Lunch', 'Dinner', 'Snacks'],
                'datasets': [{
                    'label': 'Protein (g)',
                    'data': [
                        meals['breakfast'],
                        meals['lunch'],
                        meals['dinner'],
                        meals['snacks']
                    ],
                    'backgroundColor': ['#3b82f6', '#10b981', '#a855f7', '#eab308'],
                    'borderColor': ['#2563eb', '#059669', '#9333ea', '#ca8a04'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'meal_distribution_chart': meal_distribution_chart,
            'recommendations_chart': recommendations_chart,
            'sources_chart': sources_chart,
            'meal_bar_chart': meal_bar_chart
        }
