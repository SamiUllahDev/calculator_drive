from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import symbols, simplify, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BmiCalculator(View):
    """
    Class-based view for BMI Calculator with full functionality
    
    Uses NumPy for efficient numerical operations and array-based calculations.
    Uses SymPy for precise mathematical computations and formula representation.
    """
    template_name = 'fitness_and_health_calculators/bmi_calculator.html'
    
    # Conversion constants using SymPy Float for high precision
    INCHES_TO_METERS = Float('0.0254')
    POUNDS_TO_KG = Float('0.45359237')
    CM_TO_METERS = Float('0.01')
    BMI_MIN = Float('18.5')
    BMI_MAX = Float('24.9')
    IDEAL_BMI = 22.5
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'BMI Calculator',
            'page_title': 'BMI Calculator - Calculate Your Body Mass Index',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using NumPy and SymPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get input values
            unit_system = data.get('unit_system', 'metric')  # Height unit system
            weight_unit = data.get('weight_unit', unit_system)  # Weight unit system (separate)
            height = float(data.get('height', 0))
            weight = float(data.get('weight', 0))
            age = int(data.get('age', 20))  # Default to 20 if not provided
            gender = data.get('gender', 'male').lower()  # Default to male
            
            # Validate inputs using NumPy
            height_array = np.array([height])
            weight_array = np.array([weight])
            
            if np.any(height_array <= 0) or np.any(weight_array <= 0):
                return JsonResponse({
                    'error': 'Height and weight must be greater than zero.',
                    'success': False
                }, status=400)
            
            # Validate age
            if age < 2 or age > 120:
                return JsonResponse({
                    'error': 'Age must be between 2 and 120 years.',
                    'success': False
                }, status=400)
            
            # Validate gender
            if gender not in ['male', 'female', 'm', 'f']:
                return JsonResponse({
                    'error': 'Gender must be Male or Female.',
                    'success': False
                }, status=400)
            
            # Normalize gender
            gender = 'male' if gender in ['male', 'm'] else 'female'
            
            # Validate height based on height unit system
            if unit_system == 'imperial':
                if height < 24 or height > 120:  # 2-10 feet in inches
                    return JsonResponse({
                        'error': 'Height must be between 24 and 120 inches.',
                        'success': False
                    }, status=400)
            else:
                if height < 50 or height > 300:  # 50-300 cm
                    return JsonResponse({
                        'error': 'Height must be between 50 and 300 cm.',
                        'success': False
                    }, status=400)
            
            # Validate weight based on weight unit system
            if weight_unit == 'imperial':
                if weight < 20 or weight > 1000:  # 20-1000 lbs
                    return JsonResponse({
                        'error': 'Weight must be between 20 and 1000 pounds.',
                        'success': False
                    }, status=400)
            else:
                if weight < 10 or weight > 500:  # 10-500 kg
                    return JsonResponse({
                        'error': 'Weight must be between 10 and 500 kg.',
                        'success': False
                    }, status=400)
            
            # Convert height to meters
            if unit_system == 'imperial':
                # Height is passed as total inches
                height_m = float(N(height * self.INCHES_TO_METERS, 10))
            else:
                # Metric: convert cm to meters if needed
                if height > 3:  # If height is in cm (likely > 3 meters)
                    height_m = float(N(height * self.CM_TO_METERS, 10))
                else:
                    height_m = float(height)
            
            # Convert weight to kg
            if weight_unit == 'imperial':
                # Convert pounds to kilograms
                weight_kg = float(N(weight * self.POUNDS_TO_KG, 10))
            else:
                weight_kg = float(weight)
            
            # Calculate BMI using SymPy for precise symbolic calculation
            # BMI formula: weight (kg) / height (m)^2
            w, h = symbols('w h', real=True, positive=True)
            bmi_formula = w / (h ** 2)
            bmi_formula_simplified = simplify(bmi_formula)
            
            # Evaluate BMI using SymPy with precise Float values
            bmi_symbolic = bmi_formula_simplified.subs({
                w: Float(weight_kg, 15),  # 15 decimal precision
                h: Float(height_m, 15)
            })
            bmi = float(N(bmi_symbolic, 10))  # Final result with 10 decimal places
            
            # Verify calculation using NumPy (for validation and cross-checking)
            bmi_numpy = np.divide(weight_kg, np.power(height_m, 2))
            # Use the more precise SymPy result, but verify with NumPy
            # Both should be very close (within floating point precision)
            if abs(bmi - bmi_numpy) > 1e-5:
                # If discrepancy is significant, log it but use SymPy result
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"BMI calculation discrepancy: SymPy={bmi}, NumPy={bmi_numpy}")
            
            # Determine BMI category (with age consideration for children/teens)
            category, category_color, description, detailed_category = self.get_bmi_category(bmi, age)
            
            # Calculate BMI Prime
            bmi_prime = bmi / 25.0  # BMI Prime = BMI / 25
            
            # Calculate Ponderal Index (PI)
            # PI = mass (kg) / height^3 (m)
            pi_formula = w / (h ** 3)
            pi_symbolic = pi_formula.subs({
                w: Float(weight_kg, 15),
                h: Float(height_m, 15)
            })
            ponderal_index = float(N(pi_symbolic, 10))
            
            # Calculate healthy weight range using SymPy symbolic formulas
            # Weight = BMI * height^2
            weight_formula_min = self.BMI_MIN * (h ** 2)
            weight_formula_max = self.BMI_MAX * (h ** 2)
            
            min_weight_kg = float(N(weight_formula_min.subs(h, Float(height_m, 15)), 10))
            max_weight_kg = float(N(weight_formula_max.subs(h, Float(height_m, 15)), 10))
            
            # Convert back to user's preferred weight unit if imperial
            if weight_unit == 'imperial':
                min_weight = float(N(min_weight_kg / self.POUNDS_TO_KG, 10))
                max_weight = float(N(max_weight_kg / self.POUNDS_TO_KG, 10))
                display_weight_unit = 'lbs'
            else:
                min_weight = min_weight_kg
                max_weight = max_weight_kg
                display_weight_unit = 'kg'
            
            # Calculate additional statistics using NumPy for efficient array operations
            bmi_array = np.array([bmi])
            bmi_categories = np.array([18.5, 25.0, 30.0])
            category_index = np.searchsorted(bmi_categories, bmi)
            
            # Calculate distance from ideal BMI using NumPy
            ideal_bmi_array = np.array([self.IDEAL_BMI])
            bmi_deviation = float(np.abs(bmi_array - ideal_bmi_array)[0])
            bmi_percentage_from_ideal = float((bmi_deviation / self.IDEAL_BMI) * 100)
            
            # Calculate BMI scale position (backend-controlled)
            scale_position = self.calculate_bmi_scale_position(bmi)
            
            # Prepare chart data (backend-controlled)
            # Use the original weight input in user's preferred unit for the chart
            current_weight_for_chart = weight  # This is already in the user's preferred unit
            
            chart_data = self.prepare_chart_data(
                bmi=bmi,
                category_color=category_color,
                category=category,
                healthy_weight_range={'min': min_weight, 'max': max_weight, 'unit': display_weight_unit},
                current_weight=current_weight_for_chart,
                weight_unit=display_weight_unit
            )
            
            # Prepare color information (backend-controlled)
            color_info = self.get_color_info(category_color)
            
            return JsonResponse({
                'success': True,
                'bmi': round(bmi, 1),
                'bmi_precise': round(bmi, 2),
                'bmi_prime': round(bmi_prime, 2),
                'ponderal_index': round(ponderal_index, 1),
                'category': category,
                'detailed_category': detailed_category,
                'category_color': category_color,
                'description': description,
                'age': age,
                'gender': gender,
                'healthy_weight_range': {
                    'min': round(min_weight, 1),
                    'max': round(max_weight, 1),
                    'unit': display_weight_unit
                },
                'height_m': round(height_m, 3),
                'weight_kg': round(weight_kg, 3),
                'statistics': {
                    'ideal_bmi': 22.5,
                    'deviation_from_ideal': round(bmi_deviation, 2),
                    'percentage_from_ideal': round(bmi_percentage_from_ideal, 1)
                },
                'scale_position': scale_position,
                'chart_data': chart_data,
                'color_info': color_info
            })
            
        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid input: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during calculation.'
            }, status=500)
    
    def get_bmi_category(self, bmi, age=20):
        """Determine BMI category and color using NumPy for efficient comparison
        Based on WHO classification for adults (age 20+)"""
        # Use NumPy for efficient array-based comparison
        bmi_value = np.array([bmi])
        
        # For adults (age 20+), use WHO classification
        if age >= 20:
            # Detailed categories for adults
            thresholds = np.array([16.0, 17.0, 18.5, 25.0, 30.0, 35.0, 40.0])
            category_index = np.searchsorted(thresholds, bmi_value)[0]
            
            detailed_categories = [
                ('Severe Thinness', '< 16'),
                ('Moderate Thinness', '16 - 17'),
                ('Mild Thinness', '17 - 18.5'),
                ('Normal', '18.5 - 25'),
                ('Overweight', '25 - 30'),
                ('Obese Class I', '30 - 35'),
                ('Obese Class II', '35 - 40'),
                ('Obese Class III', '> 40')
            ]
            
            simple_categories = [
                ('Underweight', 'blue', 'You may need to gain weight. Consult with a healthcare provider.'),
                ('Underweight', 'blue', 'You may need to gain weight. Consult with a healthcare provider.'),
                ('Underweight', 'blue', 'You may need to gain weight. Consult with a healthcare provider.'),
                ('Normal weight', 'green', 'Congratulations! You are in a healthy weight range.'),
                ('Overweight', 'yellow', 'Consider a balanced diet and regular exercise.'),
                ('Obese', 'red', 'Consult with a healthcare provider for a weight management plan.'),
                ('Obese', 'red', 'Consult with a healthcare provider for a weight management plan.'),
                ('Obese', 'red', 'Consult with a healthcare provider for a weight management plan.')
            ]
            
            detailed_category = detailed_categories[category_index]
            simple_category = simple_categories[category_index]
            
            return simple_category[0], simple_category[1], simple_category[2], detailed_category
        else:
            # For children/teens (age 2-19), would need percentile calculation
            # For now, use simplified adult categories
            thresholds = np.array([18.5, 25.0, 30.0])
            category_index = np.searchsorted(thresholds, bmi_value)[0]
            
            categories = [
                ('Underweight', 'blue', 'You may need to gain weight. Consult with a healthcare provider.', ('Underweight', '< 18.5')),
                ('Normal weight', 'green', 'Congratulations! You are in a healthy weight range.', ('Normal', '18.5 - 25')),
                ('Overweight', 'yellow', 'Consider a balanced diet and regular exercise.', ('Overweight', '25 - 30')),
                ('Obese', 'red', 'Consult with a healthcare provider for a weight management plan.', ('Obese', '≥ 30'))
            ]
            
            cat = categories[category_index]
            return cat[0], cat[1], cat[2], cat[3]
    
    def calculate_bmi_scale_position(self, bmi):
        """Calculate BMI indicator position on scale (0-100%) using NumPy"""
        # Scale ranges: <18.5 (0-25%), 18.5-25 (25-50%), 25-30 (50-75%), >=30 (75-100%)
        thresholds = np.array([18.5, 25.0, 30.0])
        scale_ranges = np.array([25.0, 25.0, 25.0, 25.0])  # Each quarter is 25%
        
        # Find which range BMI falls into
        range_index = np.searchsorted(thresholds, bmi)
        
        # Calculate position within the range
        if range_index == 0:
            # Underweight: 0 to 25%
            position = (bmi / 18.5) * 25.0
        elif range_index == 1:
            # Normal: 25% to 50%
            position = 25.0 + ((bmi - 18.5) / 6.5) * 25.0
        elif range_index == 2:
            # Overweight: 50% to 75%
            position = 50.0 + ((bmi - 25.0) / 5.0) * 25.0
        else:
            # Obese: 75% to 100%
            # Cap at 40 BMI for display purposes
            max_display_bmi = 40.0
            if bmi > max_display_bmi:
                position = 100.0
            else:
                position = 75.0 + ((bmi - 30.0) / 10.0) * 25.0
        
        return min(100.0, max(0.0, float(position)))
    
    def get_color_info(self, category_color):
        """Get color information for the category (backend-controlled)"""
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
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, bmi, category_color, category, healthy_weight_range, current_weight, weight_unit):
        """Prepare all chart data in backend (backend-controlled)"""
        color_info = self.get_color_info(category_color)
        max_bmi = 40.0
        bmi_percentage = min((bmi / max_bmi) * 100, 100)
        
        # Gauge Chart Data
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
        
        # Category Chart Data
        categories_info = [
            {'name': 'Underweight', 'range': '< 18.5', 'max': 18.5, 'color': '#3b82f6'},
            {'name': 'Normal', 'range': '18.5-24.9', 'max': 24.9, 'color': '#10b981'},
            {'name': 'Overweight', 'range': '25-29.9', 'max': 29.9, 'color': '#f59e0b'},
            {'name': 'Obese', 'range': '≥ 30', 'max': 40.0, 'color': '#ef4444'}
        ]
        
        # Determine current category index using NumPy
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
        
        # Weight Range Chart Data
        min_weight = healthy_weight_range['min']
        max_weight = healthy_weight_range['max']
        current = current_weight
        
        # Determine if current weight is in healthy range
        if current < min_weight:
            current_color = '#3b82f6'  # blue (underweight)
        elif current > max_weight:
            current_color = '#f59e0b'  # yellow (overweight)
        else:
            current_color = '#10b981'  # green (healthy)
        
        # Calculate range for better visualization
        range_span = max_weight - min_weight
        chart_min = max(0, min_weight - range_span * 0.2)
        chart_max = max_weight + range_span * 0.2
        
        weight_range_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Min Healthy', 'Your Weight', 'Max Healthy'],
                'datasets': [
                    {
                        'label': 'Healthy Range',
                        'data': [round(min_weight, 1), None, round(max_weight, 1)],
                        'backgroundColor': ['#10b981', 'transparent', '#10b981'],
                        'borderColor': '#10b981',
                        'borderWidth': 2,
                        'borderRadius': 8,
                        'barThickness': 40
                    },
                    {
                        'label': 'Current Weight',
                        'data': [None, round(current, 1), None],
                        'backgroundColor': current_color,
                        'borderColor': current_color,
                        'borderWidth': 2,
                        'borderRadius': 8,
                        'barThickness': 40
                    }
                ]
            },
            'y_axis': {
                'min': round(chart_min, 1),
                'max': round(chart_max, 1),
                'unit': weight_unit
            },
            'current_color': current_color
        }
        
        return {
            'gauge_chart': gauge_chart,
            'category_chart': category_chart,
            'weight_range_chart': weight_range_chart
        }
