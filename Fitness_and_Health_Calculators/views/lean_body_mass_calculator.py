from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LeanBodyMassCalculator(View):
    """
    Class-based view for Lean Body Mass Calculator
    Calculates lean body mass (LBM) and fat-free mass from body weight and body fat percentage.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/lean_body_mass_calculator.html'
    
    # Conversion constants using SymPy Float for high precision
    POUNDS_TO_KG = Float('0.45359237')
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Lean Body Mass Calculator',
            'page_title': 'Lean Body Mass Calculator - Calculate LBM & Fat-Free Mass',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            unit_system = data.get('unit_system', 'metric')
            weight = float(data.get('weight', 70))
            body_fat_percent = float(data.get('body_fat_percent', 15))
            
            # Convert to kg using SymPy for precision
            if unit_system == 'imperial':
                weight_kg = float(N(Float(weight, 15) * self.POUNDS_TO_KG, 10))
            else:
                weight_kg = float(weight)
            
            # Validation using NumPy
            weight_array = np.array([weight_kg])
            body_fat_array = np.array([body_fat_percent])
            
            if np.any(weight_array <= 0):
                return JsonResponse({'success': False, 'error': 'Weight must be greater than zero.'}, status=400)
            if np.any(weight_array > 300):
                return JsonResponse({'success': False, 'error': 'Weight cannot exceed 300 kg.'}, status=400)
            if np.any(body_fat_array < 0) or np.any(body_fat_array > 50):
                return JsonResponse({'success': False, 'error': 'Body fat percentage must be between 0 and 50%.'}, status=400)
            
            # Calculate fat mass using SymPy for precision
            body_fat_ratio = Float(body_fat_percent, 15) / Float(100, 15)
            weight_sympy = Float(weight_kg, 15)
            fat_mass_kg = float(N(weight_sympy * body_fat_ratio, 10))
            
            # Calculate lean body mass (LBM) using SymPy
            lean_body_mass_kg = float(N(weight_sympy - Float(fat_mass_kg, 15), 10))
            
            # Convert back to original unit using SymPy
            if unit_system == 'imperial':
                fat_mass = float(N(Float(fat_mass_kg, 15) / self.POUNDS_TO_KG, 10))
                lean_body_mass = float(N(Float(lean_body_mass_kg, 15) / self.POUNDS_TO_KG, 10))
                weight_unit = 'lbs'
            else:
                fat_mass = fat_mass_kg
                lean_body_mass = lean_body_mass_kg
                weight_unit = 'kg'
            
            # Calculate LBM percentage
            lbm_percent = 100 - body_fat_percent
            
            # Protein needs based on LBM (1.6-2.2g per kg LBM for athletes)
            protein_needs_min = float(N(Float(lean_body_mass_kg, 15) * Float(1.6, 15), 10))
            protein_needs_max = float(N(Float(lean_body_mass_kg, 15) * Float(2.2, 15), 10))
            
            # Additional protein recommendations
            protein_needs_sedentary = float(N(Float(lean_body_mass_kg, 15) * Float(1.2, 15), 10))
            protein_needs_moderate = float(N(Float(lean_body_mass_kg, 15) * Float(1.6, 15), 10))
            protein_needs_active = float(N(Float(lean_body_mass_kg, 15) * Float(2.0, 15), 10))
            protein_needs_athlete = float(N(Float(lean_body_mass_kg, 15) * Float(2.2, 15), 10))
            
            # Body composition categories with detailed descriptions
            category, category_color, description = self.get_body_composition_category(body_fat_percent)
            
            # Calculate fat-to-muscle ratio
            fat_to_muscle_ratio = fat_mass_kg / lean_body_mass_kg if lean_body_mass_kg > 0 else 0
            
            # Calculate ideal LBM range (assuming 10-20% body fat is ideal)
            ideal_bf_min = 10
            ideal_bf_max = 20
            ideal_lbm_min_kg = lean_body_mass_kg / (1 - ideal_bf_max / 100) * (1 - ideal_bf_max / 100)
            ideal_lbm_max_kg = lean_body_mass_kg / (1 - ideal_bf_min / 100) * (1 - ideal_bf_min / 100)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                lean_body_mass_kg=lean_body_mass_kg,
                fat_mass_kg=fat_mass_kg,
                weight_kg=weight_kg,
                lbm_percent=lbm_percent,
                body_fat_percent=body_fat_percent,
                category_color=category_color
            )
            
            # Get color info
            color_info = self.get_color_info(category_color)
            
            result = {
                'success': True,
                'weight_kg': round(weight_kg, 1),
                'body_fat_percent': round(body_fat_percent, 1),
                'fat_mass': round(fat_mass, 1),
                'fat_mass_kg': round(fat_mass_kg, 1),
                'lean_body_mass': round(lean_body_mass, 1),
                'lean_body_mass_kg': round(lean_body_mass_kg, 1),
                'lbm_percent': round(lbm_percent, 1),
                'weight_unit': weight_unit,
                'protein_needs': {
                    'min': round(protein_needs_min, 1),
                    'max': round(protein_needs_max, 1),
                    'sedentary': round(protein_needs_sedentary, 1),
                    'moderate': round(protein_needs_moderate, 1),
                    'active': round(protein_needs_active, 1),
                    'athlete': round(protein_needs_athlete, 1)
                },
                'category': category,
                'category_color': category_color,
                'description': description,
                'fat_to_muscle_ratio': round(fat_to_muscle_ratio, 3),
                'statistics': {
                    'fat_percentage': round(body_fat_percent, 1),
                    'lbm_percentage': round(lbm_percent, 1),
                    'fat_mass_percentage': round((fat_mass_kg / weight_kg) * 100, 1) if weight_kg > 0 else 0
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
            print(f"Lean Body Mass Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_body_composition_category(self, body_fat_percent):
        """Determine body composition category and color"""
        if body_fat_percent < 6:
            return 'Essential Fat', 'blue', 'Essential body fat is the minimum amount of fat necessary for basic physical and physiological health. This level is typically only seen in competitive bodybuilders.'
        elif body_fat_percent < 14:
            return 'Athletic', 'green', 'Excellent body composition typical of athletes. This range is associated with optimal performance and health.'
        elif body_fat_percent < 18:
            return 'Fitness', 'green', 'Good body composition for fitness enthusiasts. This range indicates a healthy balance of muscle and fat.'
        elif body_fat_percent < 25:
            return 'Average', 'yellow', 'Average body composition. Consider incorporating strength training and a balanced diet to improve body composition.'
        else:
            return 'Above Average', 'orange', 'Body fat percentage is above average. Focus on a combination of strength training, cardio, and a balanced diet to improve body composition.'
    
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
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, lean_body_mass_kg, fat_mass_kg, weight_kg, lbm_percent, body_fat_percent, category_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(category_color)
        
        # Composition Doughnut Chart
        composition_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Lean Body Mass', 'Fat Mass'],
                'datasets': [{
                    'data': [round(lean_body_mass_kg, 1), round(fat_mass_kg, 1)],
                    'backgroundColor': ['#2563eb', '#ef4444'],
                    'borderColor': ['#1e40af', '#dc2626'],
                    'borderWidth': 2
                }]
            },
            'center_text': {
                'value': round(lbm_percent, 1),
                'label': 'LBM %',
                'color': color_info['hex']
            }
        }
        
        # Percentage Comparison Chart
        percentage_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Lean Body Mass %', 'Body Fat %'],
                'datasets': [{
                    'label': 'Percentage',
                    'data': [round(lbm_percent, 1), round(body_fat_percent, 1)],
                    'backgroundColor': ['#10b981', '#ef4444'],
                    'borderColor': ['#059669', '#dc2626'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Mass Comparison Chart
        mass_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Total Weight', 'Lean Body Mass', 'Fat Mass'],
                'datasets': [{
                    'label': 'Mass (kg)',
                    'data': [
                        round(weight_kg, 1),
                        round(lean_body_mass_kg, 1),
                        round(fat_mass_kg, 1)
                    ],
                    'backgroundColor': ['#6b7280', '#2563eb', '#ef4444'],
                    'borderColor': ['#4b5563', '#1e40af', '#dc2626'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'composition_chart': composition_chart,
            'percentage_chart': percentage_chart,
            'mass_chart': mass_chart
        }
