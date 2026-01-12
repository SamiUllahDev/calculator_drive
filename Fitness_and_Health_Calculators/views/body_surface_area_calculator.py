from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N, sqrt, Pow


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BodySurfaceAreaCalculator(View):
    """
    Class-based view for Body Surface Area Calculator
    Calculates BSA using multiple formulas (Du Bois, Mosteller, Haycock, etc.).
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/body_surface_area_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Body Surface Area Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            unit_system = data.get('unit_system', 'metric')
            weight = float(data.get('weight', 70))
            height = float(data.get('height', 170))
            
            # Convert to metric using SymPy for precision
            if unit_system == 'imperial':
                weight_kg = float(N(Float(weight, 15) * Float(0.453592, 15), 10))
                height_cm = float(N(Float(height, 15) * Float(2.54, 15), 10))
            else:
                weight_kg = weight
                height_cm = height
            
            height_m = height_cm / 100
            
            # Validation
            if weight_kg <= 0 or height_cm <= 0:
                return JsonResponse({'success': False, 'error': 'Weight and height must be greater than zero.'}, status=400)
            if weight_kg < 1 or weight_kg > 500:
                return JsonResponse({'success': False, 'error': 'Weight must be between 1 and 500 kg.'}, status=400)
            if height_cm < 50 or height_cm > 250:
                return JsonResponse({'success': False, 'error': 'Height must be between 50 and 250 cm.'}, status=400)
            
            # Calculate BSA using multiple formulas with SymPy for precision
            weight_sym = Float(weight_kg, 15)
            height_cm_sym = Float(height_cm, 15)
            
            # Du Bois formula: BSA = 0.007184 × weight^0.425 × height^0.725
            du_bois = float(N(Float(0.007184, 15) * Pow(weight_sym, Float(0.425, 15)) * Pow(height_cm_sym, Float(0.725, 15)), 10))
            
            # Mosteller formula: BSA = sqrt((height × weight) / 3600)
            mosteller = float(N(sqrt((height_cm_sym * weight_sym) / Float(3600, 15)), 10))
            
            # Haycock formula: BSA = 0.024265 × weight^0.5378 × height^0.3964
            haycock = float(N(Float(0.024265, 15) * Pow(weight_sym, Float(0.5378, 15)) * Pow(height_cm_sym, Float(0.3964, 15)), 10))
            
            # Gehan & George formula: BSA = 0.0235 × weight^0.51456 × height^0.42246
            gehan = float(N(Float(0.0235, 15) * Pow(weight_sym, Float(0.51456, 15)) * Pow(height_cm_sym, Float(0.42246, 15)), 10))
            
            # Average
            average = (du_bois + mosteller + haycock + gehan) / 4
            
            # Determine which formula is closest to average (for highlighting)
            formulas_list = [
                ('du_bois', du_bois),
                ('mosteller', mosteller),
                ('haycock', haycock),
                ('gehan', gehan)
            ]
            
            # Find formula closest to average
            closest_formula = min(formulas_list, key=lambda x: abs(x[1] - average))
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                formulas={
                    'du_bois': du_bois,
                    'mosteller': mosteller,
                    'haycock': haycock,
                    'gehan': gehan,
                    'average': average
                },
                closest_formula=closest_formula[0]
            )
            
            result = {
                'success': True,
                'weight_kg': round(weight_kg, 1),
                'height_cm': round(height_cm, 1),
                'height_m': round(height_m, 2),
                'formulas': {
                    'du_bois': round(du_bois, 3),
                    'mosteller': round(mosteller, 3),
                    'haycock': round(haycock, 3),
                    'gehan': round(gehan, 3),
                    'average': round(average, 3)
                },
                'closest_formula': closest_formula[0],
                'chart_data': chart_data
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Body Surface Area Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def prepare_chart_data(self, formulas, closest_formula):
        """Prepare chart data for visualization"""
        # BSA Formulas Comparison Chart
        formulas_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Du Bois', 'Mosteller', 'Haycock', 'Gehan & George', 'Average'],
                'datasets': [{
                    'label': 'BSA (m²)',
                    'data': [
                        round(formulas['du_bois'], 3),
                        round(formulas['mosteller'], 3),
                        round(formulas['haycock'], 3),
                        round(formulas['gehan'], 3),
                        round(formulas['average'], 3)
                    ],
                    'backgroundColor': [
                        '#3b82f6' if closest_formula == 'du_bois' else '#60a5fa',
                        '#10b981' if closest_formula == 'mosteller' else '#34d399',
                        '#f59e0b' if closest_formula == 'haycock' else '#fbbf24',
                        '#8b5cf6' if closest_formula == 'gehan' else '#a78bfa',
                        '#ef4444'  # Average always highlighted
                    ],
                    'borderColor': [
                        '#2563eb' if closest_formula == 'du_bois' else '#3b82f6',
                        '#059669' if closest_formula == 'mosteller' else '#10b981',
                        '#d97706' if closest_formula == 'haycock' else '#f59e0b',
                        '#7c3aed' if closest_formula == 'gehan' else '#8b5cf6',
                        '#dc2626'
                    ],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # BSA Range Visualization Chart
        min_bsa = min(formulas['du_bois'], formulas['mosteller'], formulas['haycock'], formulas['gehan'])
        max_bsa = max(formulas['du_bois'], formulas['mosteller'], formulas['haycock'], formulas['gehan'])
        range_span = max_bsa - min_bsa
        
        range_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Minimum', 'Average', 'Maximum'],
                'datasets': [{
                    'label': 'BSA (m²)',
                    'data': [
                        round(min_bsa, 3),
                        round(formulas['average'], 3),
                        round(max_bsa, 3)
                    ],
                    'backgroundColor': ['#6b7280', '#ef4444', '#6b7280'],
                    'borderColor': ['#4b5563', '#dc2626', '#4b5563'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'formulas_chart': formulas_chart,
            'range_chart': range_chart
        }
