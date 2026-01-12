from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N, symbols, simplify


@method_decorator(ensure_csrf_cookie, name='dispatch')
class OverweightCalculator(View):
    """
    Class-based view for Overweight Calculator
    Determines if weight is overweight/obese based on BMI.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/overweight_calculator.html'
    
    # Conversion constants using SymPy Float for high precision
    INCHES_TO_METERS = Float('0.0254')
    POUNDS_TO_KG = Float('0.45359237')
    CM_TO_METERS = Float('0.01')
    BMI_MIN = Float('18.5')
    BMI_MAX = Float('24.9')
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Overweight Calculator',
            'page_title': 'Overweight Calculator - BMI Assessment & Weight Analysis',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            unit_system = data.get('unit_system', 'metric')
            weight = float(data.get('weight', 80))
            height = float(data.get('height', 170))
            height_in = float(data.get('height_in', 0))
            
            # Convert to metric using SymPy for precision
            if unit_system == 'imperial':
                weight_kg = float(N(Float(weight, 15) * self.POUNDS_TO_KG, 10))
                height_total_inches = Float(height, 15) * Float(12, 15) + Float(height_in, 15)
                height_cm = float(N(height_total_inches * Float(2.54, 15), 10))
            else:
                weight_kg = float(weight)
                height_cm = float(height)
            
            # Convert height to meters using SymPy
            if height_cm > 3:  # Likely in cm
                height_m = float(N(Float(height_cm, 15) * self.CM_TO_METERS, 10))
            else:
                height_m = float(height_cm)
            
            # Validation using NumPy
            weight_array = np.array([weight_kg])
            height_array = np.array([height_cm])
            
            if np.any(weight_array <= 0) or np.any(height_array <= 0):
                return JsonResponse({'success': False, 'error': 'Weight and height must be greater than zero.'}, status=400)
            if height_cm < 50 or height_cm > 300:
                return JsonResponse({'success': False, 'error': 'Height must be between 50 and 300 cm.'}, status=400)
            if weight_kg < 10 or weight_kg > 500:
                return JsonResponse({'success': False, 'error': 'Weight must be between 10 and 500 kg.'}, status=400)
            
            # Calculate BMI using SymPy for precise symbolic calculation
            w, h = symbols('w h', real=True, positive=True)
            bmi_formula = w / (h ** 2)
            bmi_formula_simplified = simplify(bmi_formula)
            
            bmi_symbolic = bmi_formula_simplified.subs({
                w: Float(weight_kg, 15),
                h: Float(height_m, 15)
            })
            bmi = float(N(bmi_symbolic, 10))
            
            # Determine category with detailed information
            category, category_color, description, is_overweight, severity = self.get_bmi_category(bmi)
            
            # Calculate ideal weight range using SymPy
            ideal_weight_min_kg = float(N(self.BMI_MIN * (Float(height_m, 15) ** 2), 10))
            ideal_weight_max_kg = float(N(self.BMI_MAX * (Float(height_m, 15) ** 2), 10))
            
            # Calculate weight to lose/gain
            if bmi > 24.9:
                weight_to_lose_kg = weight_kg - ideal_weight_max_kg
                weight_to_gain_kg = 0
            elif bmi < 18.5:
                weight_to_lose_kg = 0
                weight_to_gain_kg = ideal_weight_min_kg - weight_kg
            else:
                weight_to_lose_kg = 0
                weight_to_gain_kg = 0
            
            # Convert back to original unit using SymPy
            if unit_system == 'imperial':
                ideal_weight_min = float(N(Float(ideal_weight_min_kg, 15) / self.POUNDS_TO_KG, 10))
                ideal_weight_max = float(N(Float(ideal_weight_max_kg, 15) / self.POUNDS_TO_KG, 10))
                weight_to_lose = float(N(Float(weight_to_lose_kg, 15) / self.POUNDS_TO_KG, 10)) if weight_to_lose_kg > 0 else 0
                weight_to_gain = float(N(Float(weight_to_gain_kg, 15) / self.POUNDS_TO_KG, 10)) if weight_to_gain_kg > 0 else 0
                unit = 'lbs'
            else:
                ideal_weight_min = ideal_weight_min_kg
                ideal_weight_max = ideal_weight_max_kg
                weight_to_lose = weight_to_lose_kg
                weight_to_gain = weight_to_gain_kg
                unit = 'kg'
            
            # Calculate BMI scale position
            scale_position = self.calculate_bmi_scale_position(bmi)
            
            # Calculate percentage above/below normal
            if bmi > 24.9:
                percent_above_normal = ((bmi - 24.9) / 24.9) * 100
                percent_below_normal = 0
            elif bmi < 18.5:
                percent_above_normal = 0
                percent_below_normal = ((18.5 - bmi) / 18.5) * 100
            else:
                percent_above_normal = 0
                percent_below_normal = 0
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                bmi=bmi,
                category_color=category_color,
                current_weight=weight if unit_system == 'metric' else weight,
                ideal_weight_min=ideal_weight_min,
                ideal_weight_max=ideal_weight_max,
                weight_unit=unit,
                is_overweight=is_overweight
            )
            
            # Get color info
            color_info = self.get_color_info(category_color)
            
            result = {
                'success': True,
                'weight_kg': round(weight_kg, 1),
                'height_cm': round(height_cm, 1),
                'bmi': round(bmi, 1),
                'bmi_precise': round(bmi, 2),
                'category': category,
                'category_color': category_color,
                'description': description,
                'is_overweight': is_overweight,
                'severity': severity,
                'ideal_weight_range': {
                    'min': round(ideal_weight_min, 1),
                    'max': round(ideal_weight_max, 1),
                    'unit': unit
                },
                'weight_to_lose': round(weight_to_lose, 1) if weight_to_lose > 0 else 0,
                'weight_to_gain': round(weight_to_gain, 1) if weight_to_gain > 0 else 0,
                'unit': unit,
                'scale_position': scale_position,
                'statistics': {
                    'percent_above_normal': round(percent_above_normal, 1) if percent_above_normal > 0 else 0,
                    'percent_below_normal': round(percent_below_normal, 1) if percent_below_normal > 0 else 0,
                    'bmi_deviation': round(abs(bmi - 21.7), 1),  # Deviation from ideal BMI (21.7)
                    'current_weight': round(weight if unit_system == 'metric' else weight, 1)
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
            print(f"Overweight Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_bmi_category(self, bmi):
        """Determine BMI category with detailed information"""
        if bmi < 16:
            return 'Severe Thinness', 'blue', 'You are severely underweight. Please consult with a healthcare provider for a safe weight gain plan.', False, 'severe'
        elif bmi < 17:
            return 'Moderate Thinness', 'blue', 'You are moderately underweight. Consider consulting with a healthcare provider or registered dietitian.', False, 'moderate'
        elif bmi < 18.5:
            return 'Mild Thinness', 'blue', 'You are mildly underweight. Focus on a balanced diet and gradual weight gain.', False, 'mild'
        elif bmi < 25:
            return 'Normal Weight', 'green', 'Congratulations! You are in a healthy weight range. Continue maintaining a balanced diet and regular physical activity.', False, 'normal'
        elif bmi < 30:
            return 'Overweight', 'yellow', 'You are overweight. Consider a balanced diet and regular exercise to reach a healthy weight range.', True, 'mild'
        elif bmi < 35:
            return 'Obese Class I', 'orange', 'You are in the obese category (Class I). Consult with a healthcare provider for a comprehensive weight management plan.', True, 'moderate'
        elif bmi < 40:
            return 'Obese Class II', 'red', 'You are in the obese category (Class II). It is important to consult with healthcare professionals for a structured weight management program.', True, 'severe'
        else:
            return 'Obese Class III', 'red', 'You are in the obese category (Class III). Please consult with healthcare professionals immediately for a comprehensive treatment plan.', True, 'very_severe'
    
    def calculate_bmi_scale_position(self, bmi):
        """Calculate BMI indicator position on scale (0-100%)"""
        thresholds = np.array([18.5, 25.0, 30.0])
        range_index = np.searchsorted(thresholds, bmi)
        
        if range_index == 0:
            position = (bmi / 18.5) * 25.0
        elif range_index == 1:
            position = 25.0 + ((bmi - 18.5) / 6.5) * 25.0
        elif range_index == 2:
            position = 50.0 + ((bmi - 25.0) / 5.0) * 25.0
        else:
            max_display_bmi = 40.0
            if bmi > max_display_bmi:
                position = 100.0
            else:
                position = 75.0 + ((bmi - 30.0) / 10.0) * 25.0
        
        return min(100.0, max(0.0, float(position)))
    
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
    
    def prepare_chart_data(self, bmi, category_color, current_weight, ideal_weight_min, ideal_weight_max, weight_unit, is_overweight):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(category_color)
        
        # BMI Gauge Chart
        max_bmi = 40.0
        bmi_percentage = min((bmi / max_bmi) * 100, 100)
        
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['BMI', 'Remaining'],
                'datasets': [{
                    'data': [round(bmi_percentage, 2), round(100 - bmi_percentage, 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(bmi, 1),
                'label': 'BMI',
                'color': color_info['hex']
            }
        }
        
        # Weight Comparison Chart
        weight_range_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Min Healthy', 'Your Weight', 'Max Healthy'],
                'datasets': [
                    {
                        'label': 'Healthy Range',
                        'data': [round(ideal_weight_min, 1), None, round(ideal_weight_max, 1)],
                        'backgroundColor': ['#10b981', 'transparent', '#10b981'],
                        'borderColor': '#10b981',
                        'borderWidth': 2,
                        'borderRadius': 8,
                        'barThickness': 40
                    },
                    {
                        'label': 'Current Weight',
                        'data': [None, round(current_weight, 1), None],
                        'backgroundColor': color_info['hex'],
                        'borderColor': color_info['hex'],
                        'borderWidth': 2,
                        'borderRadius': 8,
                        'barThickness': 40
                    }
                ]
            },
            'y_axis': {
                'min': max(0, min(ideal_weight_min, current_weight) - (ideal_weight_max - ideal_weight_min) * 0.2),
                'max': max(ideal_weight_max, current_weight) + (ideal_weight_max - ideal_weight_min) * 0.2,
                'unit': weight_unit
            },
            'current_color': color_info['hex']
        }
        
        # BMI Categories Chart
        categories_info = [
            {'name': 'Underweight', 'range': '< 18.5', 'max': 18.5, 'color': '#3b82f6'},
            {'name': 'Normal', 'range': '18.5-24.9', 'max': 24.9, 'color': '#10b981'},
            {'name': 'Overweight', 'range': '25-29.9', 'max': 29.9, 'color': '#f59e0b'},
            {'name': 'Obese', 'range': '≥ 30', 'max': 40.0, 'color': '#ef4444'}
        ]
        
        bmi_array = np.array([bmi])
        category_thresholds = np.array([18.5, 25.0, 30.0])
        current_category_index = int(np.searchsorted(category_thresholds, bmi_array)[0])
        
        category_chart_data = []
        category_colors = []
        for idx, cat_info in enumerate(categories_info):
            if idx == current_category_index:
                category_chart_data.append(round(bmi, 2))
                category_colors.append(cat_info['color'])
            else:
                category_chart_data.append(0)
                category_colors.append('#e5e7eb')
        
        category_chart = {
            'type': 'bar',
            'data': {
                'labels': [cat['name'] for cat in categories_info],
                'datasets': [{
                    'label': 'BMI Value',
                    'data': category_chart_data,
                    'backgroundColor': category_colors,
                    'borderColor': [cat['color'] for cat in categories_info],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            },
            'current_category_index': current_category_index,
            'categories_info': categories_info
        }
        
        return {
            'gauge_chart': gauge_chart,
            'weight_range_chart': weight_range_chart,
            'category_chart': category_chart
        }
