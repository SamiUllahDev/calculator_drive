from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AnorexicBmiCalculator(View):
    """
    Class-based view for Anorexic BMI Calculator.
    
    - Focuses on the very-low-BMI range used in eating disorder assessment.
    - Uses NumPy for robust numeric validation and calculations.
    - Returns structured JSON with chart data for visualizations.
    """

    template_name = 'fitness_and_health_calculators/anorexic_bmi_calculator.html'

    # Thresholds based on DSM-5 and clinical criteria
    ANOREXIC_THRESHOLD = 17.5
    HEALTHY_MIN_BMI = 18.5
    SEVERE_ANOREXIA_THRESHOLD = 15.0

    def get(self, request):
        """Render the calculator page."""
        context = {
            'calculator_name': 'Anorexic BMI Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """
        Handle POST request for calculations with chart data.
        """
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

            unit_system = data.get('unit_system', 'metric')
            weight = float(data.get('weight', 50))
            height = float(data.get('height', 160))
            height_in = float(data.get('height_in', 0))

            # Basic numeric validation using NumPy
            values = np.array([weight, height], dtype=float)
            if np.any(values <= 0):
                return JsonResponse(
                    {'success': False, 'error': 'Weight and height must be greater than zero.'},
                    status=400,
                )

            # Reasonable range validation
            if unit_system == 'imperial':
                if height < 3 or height > 8:
                    return JsonResponse(
                        {'success': False, 'error': 'Height must be between 3 and 8 feet.'},
                        status=400,
                    )
                if height_in < 0 or height_in >= 12:
                    return JsonResponse(
                        {'success': False, 'error': 'Inches must be between 0 and 11.'},
                        status=400,
                    )
                if weight < 40 or weight > 600:
                    return JsonResponse(
                        {'success': False, 'error': 'Weight must be between 40 and 600 lbs.'},
                        status=400,
                    )
            else:
                if height < 120 or height > 220:
                    return JsonResponse(
                        {'success': False, 'error': 'Height must be between 120 and 220 cm.'},
                        status=400,
                    )
                if weight < 25 or weight > 300:
                    return JsonResponse(
                        {'success': False, 'error': 'Weight must be between 25 and 300 kg.'},
                        status=400,
                    )

            # Convert to metric
            if unit_system == 'imperial':
                total_inches = height * 12 + height_in
                height_cm = total_inches * 2.54
                weight_kg = weight * 0.453592
                unit = 'lbs'
            else:
                height_cm = height
                weight_kg = weight
                unit = 'kg'

            height_m = height_cm / 100.0

            # Calculate BMI
            bmi = weight_kg / (height_m ** 2)

            # Determine category and severity
            if bmi < self.SEVERE_ANOREXIA_THRESHOLD:
                category = 'Severe Anorexia'
                category_color = 'red'
                severity = 'severe'
            elif bmi < self.ANOREXIC_THRESHOLD:
                category = 'Anorexia'
                category_color = 'orange'
                severity = 'moderate'
            elif bmi < self.HEALTHY_MIN_BMI:
                category = 'Underweight'
                category_color = 'yellow'
                severity = 'mild'
            else:
                category = 'Normal'
                category_color = 'green'
                severity = 'normal'

            # Calculate healthy weight range
            healthy_weight_min_kg = self.HEALTHY_MIN_BMI * (height_m ** 2)
            healthy_weight_max_kg = 24.9 * (height_m ** 2)  # Upper normal BMI
            weight_difference_kg = healthy_weight_min_kg - weight_kg

            if unit_system == 'imperial':
                healthy_weight_min = healthy_weight_min_kg / 0.453592
                healthy_weight_max = healthy_weight_max_kg / 0.453592
                weight_difference = weight_difference_kg / 0.453592
            else:
                healthy_weight_min = healthy_weight_min_kg
                healthy_weight_max = healthy_weight_max_kg
                weight_difference = weight_difference_kg

            # Prepare chart data
            chart_data = self.prepare_chart_data(
                bmi=bmi,
                category_color=category_color,
                healthy_weight_min=healthy_weight_min,
                healthy_weight_max=healthy_weight_max,
                current_weight=weight,
                weight_unit=unit
            )

            # Calculate scale position for BMI indicator
            scale_position = self.calculate_bmi_scale_position(bmi)

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
                'severity': severity,
                'is_anorexic': bmi < self.ANOREXIC_THRESHOLD,
                'anorexic_threshold': self.ANOREXIC_THRESHOLD,
                'healthy_weight_min': round(healthy_weight_min, 1),
                'healthy_weight_max': round(healthy_weight_max, 1),
                'weight_difference': round(weight_difference, 1),
                'unit': unit,
                'warning': bmi < self.ANOREXIC_THRESHOLD,
                'chart_data': chart_data,
                'scale_position': scale_position,
                'color_info': color_info,
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse(
                {'success': False, 'error': f'Invalid input: {str(e)}'},
                status=400,
            )
        except Exception as e:
            # Log the error for debugging (in production, use proper logging)
            import traceback
            error_details = traceback.format_exc()
            print(f"Anorexic BMI Calculator Error: {error_details}")
            return JsonResponse(
                {'success': False, 'error': f'An error occurred during calculation: {str(e)}'},
                status=500,
            )

    def calculate_bmi_scale_position(self, bmi):
        """Calculate BMI indicator position on scale (0-100%)"""
        # Scale ranges focused on low BMI: <15 (0-30%), 15-17.5 (30-50%), 17.5-18.5 (50-60%), >=18.5 (60-100%)
        if bmi < self.SEVERE_ANOREXIA_THRESHOLD:
            position = (bmi / self.SEVERE_ANOREXIA_THRESHOLD) * 30.0
        elif bmi < self.ANOREXIC_THRESHOLD:
            position = 30.0 + ((bmi - self.SEVERE_ANOREXIA_THRESHOLD) / (self.ANOREXIC_THRESHOLD - self.SEVERE_ANOREXIA_THRESHOLD)) * 20.0
        elif bmi < self.HEALTHY_MIN_BMI:
            position = 50.0 + ((bmi - self.ANOREXIC_THRESHOLD) / (self.HEALTHY_MIN_BMI - self.ANOREXIC_THRESHOLD)) * 10.0
        else:
            # Normal range: 60-100% (18.5 to 25)
            max_display_bmi = 25.0
            if bmi > max_display_bmi:
                position = 100.0
            else:
                position = 60.0 + ((bmi - self.HEALTHY_MIN_BMI) / (max_display_bmi - self.HEALTHY_MIN_BMI)) * 40.0
        
        return min(100.0, max(0.0, float(position)))

    def get_color_info(self, category_color):
        """Get color information for the category"""
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
            }
        }
        # Default to red if color not found
        return color_map.get(category_color, color_map['red'])

    def prepare_chart_data(self, bmi, category_color, healthy_weight_min, healthy_weight_max, current_weight, weight_unit):
        """Prepare all chart data for visualizations"""
        color_info = self.get_color_info(category_color)
        max_bmi = 25.0  # Focus on range up to normal BMI
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

        # Category Chart Data (focused on anorexia ranges)
        categories_info = [
            {'name': 'Severe Anorexia', 'range': '< 15', 'max': 15.0, 'color': '#ef4444'},
            {'name': 'Anorexia', 'range': '15-17.5', 'max': 17.5, 'color': '#f97316'},
            {'name': 'Underweight', 'range': '17.5-18.5', 'max': 18.5, 'color': '#eab308'},
            {'name': 'Normal', 'range': '18.5-25', 'max': 25.0, 'color': '#10b981'}
        ]

        # Determine current category index
        bmi_array = np.array([bmi])
        category_thresholds = np.array([self.SEVERE_ANOREXIA_THRESHOLD, self.ANOREXIC_THRESHOLD, self.HEALTHY_MIN_BMI])
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
        range_span = healthy_weight_max - healthy_weight_min
        if range_span <= 0:
            range_span = 1.0  # Prevent division by zero
        chart_min = max(0, healthy_weight_min - range_span * 0.3)
        chart_max = healthy_weight_max + range_span * 0.2

        # Determine current weight color
        if current_weight < healthy_weight_min:
            current_color = color_info['hex']
        elif current_weight > healthy_weight_max:
            current_color = '#f59e0b'  # yellow (overweight)
        else:
            current_color = '#10b981'  # green (healthy)

        weight_range_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Min Healthy', 'Your Weight', 'Max Healthy'],
                'datasets': [
                    {
                        'label': 'Healthy Range',
                        'data': [round(healthy_weight_min, 1), None, round(healthy_weight_max, 1)],
                        'backgroundColor': ['#10b981', 'transparent', '#10b981'],
                        'borderColor': '#10b981',
                        'borderWidth': 2,
                        'borderRadius': 8,
                        'barThickness': 40
                    },
                    {
                        'label': 'Current Weight',
                        'data': [None, round(current_weight, 1), None],
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
