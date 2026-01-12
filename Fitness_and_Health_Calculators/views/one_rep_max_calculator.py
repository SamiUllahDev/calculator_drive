from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N, exp, symbols, simplify


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OneRepMaxCalculator(View):
    """
    Class-based view for One Rep Max Calculator
    Calculates 1RM using multiple formulas (Brzycki, Epley, Lombardi, O'Conner, Mayhew, etc.).
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/one_rep_max_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'One Rep Max Calculator',
            'page_title': 'One Rep Max Calculator - Calculate 1RM',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            weight = float(data.get('weight', 100))
            reps = int(data.get('reps', 10))
            unit_system = data.get('unit_system', 'metric')
            
            # Validation using NumPy
            weight_array = np.array([weight])
            reps_array = np.array([reps])
            
            if np.any(weight_array <= 0):
                return JsonResponse({'success': False, 'error': 'Weight must be greater than zero.'}, status=400)
            if reps < 1 or reps > 30:
                return JsonResponse({'success': False, 'error': 'Reps must be between 1 and 30.'}, status=400)
            
            # Convert to kg if imperial for calculations (standardize)
            if unit_system == 'imperial':
                weight_kg = float(N(Float(weight, 15) * Float(0.453592, 15), 10))
            else:
                weight_kg = float(weight)
            
            if reps == 1:
                # Already 1RM
                one_rm_kg = weight_kg
                formulas = {
                    'brzycki': round(weight_kg, 1),
                    'epley': round(weight_kg, 1),
                    'lombardi': round(weight_kg, 1),
                    'oconner': round(weight_kg, 1),
                    'mayhew': round(weight_kg, 1),
                    'wathan': round(weight_kg, 1),
                    'average': round(weight_kg, 1)
                }
            else:
                # Use SymPy for precise calculations
                w = Float(weight_kg, 15)
                r = Float(reps, 15)
                
                # Brzycki formula (most popular): 1RM = weight / (1.0278 - 0.0278 × reps)
                brzycki = float(N(w / (Float('1.0278', 15) - Float('0.0278', 15) * r), 10))
                
                # Epley formula: 1RM = weight × (1 + reps/30)
                epley = float(N(w * (Float('1', 15) + r / Float('30', 15)), 10))
                
                # Lombardi formula: 1RM = weight × reps^0.10
                lombardi = float(N(w * (r ** Float('0.10', 15)), 10))
                
                # O'Conner formula: 1RM = weight × (1 + reps/40)
                oconner = float(N(w * (Float('1', 15) + r / Float('40', 15)), 10))
                
                # Mayhew formula: 1RM = (weight × 100) / (52.2 + 41.9 × e^(-0.055 × reps))
                mayhew_exp = N(exp(-Float('0.055', 15) * r), 10)
                mayhew = float(N((w * Float('100', 15)) / (Float('52.2', 15) + Float('41.9', 15) * Float(mayhew_exp, 15)), 10))
                
                # Wathan formula: 1RM = (weight × 100) / (48.8 + 53.8 × e^(-0.075 × reps))
                wathan_exp = N(exp(-Float('0.075', 15) * r), 10)
                wathan = float(N((w * Float('100', 15)) / (Float('48.8', 15) + Float('53.8', 15) * Float(wathan_exp, 15)), 10))
                
                # Average of all formulas
                one_rm_kg = (brzycki + epley + lombardi + oconner + mayhew + wathan) / 6
                
                formulas = {
                    'brzycki': round(brzycki, 1),
                    'epley': round(epley, 1),
                    'lombardi': round(lombardi, 1),
                    'oconner': round(oconner, 1),
                    'mayhew': round(mayhew, 1),
                    'wathan': round(wathan, 1),
                    'average': round(one_rm_kg, 1)
                }
            
            # Convert back to original unit
            if unit_system == 'imperial':
                one_rm = float(N(Float(one_rm_kg, 15) / Float(0.453592, 15), 10))
                weight_display = weight
            else:
                one_rm = one_rm_kg
                weight_display = weight_kg
            
            # Calculate percentages of 1RM for training using SymPy
            training_percentages = {}
            percentages = [50, 60, 70, 75, 80, 85, 90, 95, 100]
            one_rm_sympy = Float(one_rm_kg, 15)
            
            for pct in percentages:
                pct_ratio = Float(pct, 15) / Float(100, 15)
                weight_at_pct_kg = float(N(one_rm_sympy * pct_ratio, 10))
                if unit_system == 'imperial':
                    weight_at_pct = float(N(Float(weight_at_pct_kg, 15) / Float(0.453592, 15), 10))
                else:
                    weight_at_pct = weight_at_pct_kg
                training_percentages[pct] = round(weight_at_pct, 1)
            
            # Calculate estimated max reps at different percentages using inverse formulas
            max_reps_estimates = {}
            for pct in [50, 60, 70, 80, 85, 90, 95]:
                # Use inverse Brzycki: reps = (1.0278 - weight/1RM) / 0.0278
                weight_at_pct_kg = one_rm_kg * (pct / 100)
                if weight_at_pct_kg > 0:
                    estimated_reps_brzycki = max(1, int((1.0278 - (weight_at_pct_kg / one_rm_kg)) / 0.0278))
                    # Use inverse Epley: reps = 30 × (1RM/weight - 1)
                    estimated_reps_epley = max(1, int(30 * ((one_rm_kg / weight_at_pct_kg) - 1)))
                    # Average of both estimates
                    estimated_reps = max(1, int((estimated_reps_brzycki + estimated_reps_epley) / 2))
                else:
                    estimated_reps = 1
                max_reps_estimates[pct] = estimated_reps
            
            # Determine strength level category
            category, category_color, category_description = self.get_strength_category(one_rm_kg, unit_system)
            
            # Calculate strength standards (relative to body weight - assuming average 70kg/154lbs)
            avg_bodyweight_kg = 70.0
            relative_strength = one_rm_kg / avg_bodyweight_kg if avg_bodyweight_kg > 0 else 0
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                one_rm=one_rm,
                formulas=formulas,
                training_percentages=training_percentages,
                max_reps_estimates=max_reps_estimates,
                category_color=category_color,
                unit=unit_system
            )
            
            # Get color info
            color_info = self.get_color_info(category_color)
            
            result = {
                'success': True,
                'weight': round(weight_display, 1),
                'reps': reps,
                'unit': 'kg' if unit_system == 'metric' else 'lbs',
                'one_rm': round(one_rm, 1),
                'one_rm_kg': round(one_rm_kg, 1),
                'formulas': formulas,
                'training_percentages': training_percentages,
                'max_reps_estimates': max_reps_estimates,
                'category': category,
                'category_color': category_color,
                'category_description': category_description,
                'relative_strength': round(relative_strength, 2),
                'statistics': {
                    'formula_range': {
                        'min': round(min(formulas.values()), 1),
                        'max': round(max(formulas.values()), 1),
                        'difference': round(max(formulas.values()) - min(formulas.values()), 1)
                    },
                    'input_weight': round(weight_display, 1),
                    'input_reps': reps,
                    'one_rm_increase': round(one_rm - weight_display, 1) if one_rm > weight_display else 0
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
            print(f"One Rep Max Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_strength_category(self, one_rm_kg, unit_system):
        """Determine strength level category based on 1RM"""
        # Categories based on 1RM in kg (bench press example)
        # These are general guidelines and vary by exercise
        if one_rm_kg < 50:
            category = 'Beginner'
            category_color = 'blue'
            description = 'Starting strength level. Focus on proper form and progressive overload.'
        elif one_rm_kg < 80:
            category = 'Novice'
            category_color = 'green'
            description = 'Developing strength. Continue with structured training program.'
        elif one_rm_kg < 120:
            category = 'Intermediate'
            category_color = 'yellow'
            description = 'Good strength level. Consider periodization and advanced techniques.'
        elif one_rm_kg < 160:
            category = 'Advanced'
            category_color = 'orange'
            description = 'Strong lifter. Advanced programming and recovery strategies recommended.'
        else:
            category = 'Elite'
            category_color = 'red'
            description = 'Exceptional strength. Elite-level training and coaching recommended.'
        
        return category, category_color, description
    
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
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, one_rm, formulas, training_percentages, max_reps_estimates, category_color, unit):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(category_color)
        
        # Formulas Comparison Chart
        formulas_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Brzycki', 'Epley', 'Lombardi', "O'Conner", 'Mayhew', 'Wathan', 'Average'],
                'datasets': [{
                    'label': '1RM Estimate',
                    'data': [
                        formulas['brzycki'],
                        formulas['epley'],
                        formulas['lombardi'],
                        formulas['oconner'],
                        formulas['mayhew'],
                        formulas['wathan'],
                        formulas['average']
                    ],
                    'backgroundColor': [
                        '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#6366f1',
                        color_info['hex']
                    ],
                    'borderColor': [
                        '#2563eb', '#059669', '#d97706', '#7c3aed', '#dc2626', '#4f46e5',
                        color_info['hex']
                    ],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Training Percentages Chart
        percentages_list = list(training_percentages.keys())
        percentages_values = list(training_percentages.values())
        
        training_chart = {
            'type': 'line',
            'data': {
                'labels': [str(p) + '%' for p in percentages_list],
                'datasets': [{
                    'label': 'Weight',
                    'data': percentages_values,
                    'borderColor': color_info['hex'],
                    'backgroundColor': color_info['hex'] + '20',
                    'borderWidth': 3,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 5,
                    'pointHoverRadius': 7
                }]
            }
        }
        
        # Max Reps Estimates Chart
        reps_percentages = list(max_reps_estimates.keys())
        reps_values = list(max_reps_estimates.values())
        
        reps_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(p) + '%' for p in reps_percentages],
                'datasets': [{
                    'label': 'Estimated Max Reps',
                    'data': reps_values,
                    'backgroundColor': '#6366f1',
                    'borderColor': '#4f46e5',
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # 1RM Gauge Chart
        max_display = one_rm * 1.5  # Display up to 150% of 1RM
        one_rm_percentage = min((one_rm / max_display) * 100, 100)
        
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['1RM', 'Remaining'],
                'datasets': [{
                    'data': [round(one_rm_percentage, 2), round(100 - one_rm_percentage, 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(one_rm, 1),
                'label': '1RM',
                'color': color_info['hex']
            }
        }
        
        return {
            'formulas_chart': formulas_chart,
            'training_chart': training_chart,
            'reps_chart': reps_chart,
            'gauge_chart': gauge_chart
        }
