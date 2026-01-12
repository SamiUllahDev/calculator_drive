from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PregnancyWeightGainCalculator(View):
    """
    Class-based view for Pregnancy Weight Gain Calculator
    Calculates recommended weight gain during pregnancy based on pre-pregnancy BMI.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/pregnancy_weight_gain_calculator.html'
    
    # Conversion constants using SymPy Float for precision
    LBS_TO_KG = Float('0.453592', 15)
    INCHES_TO_CM = Float('2.54', 15)
    CM_TO_M = Float('0.01', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Pregnancy Weight Gain Calculator',
            'page_title': 'Pregnancy Weight Gain Calculator - Track Healthy Weight Gain',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            weight = float(data.get('weight'))  # kg or lbs
            height = float(data.get('height'))  # cm or inches
            weeks_pregnant = int(data.get('weeks_pregnant', 0))
            current_weight = float(data.get('current_weight', weight))
            unit = data.get('unit', 'metric')
            
            # Convert to metric using SymPy for precision
            if unit == 'imperial':
                weight_sympy = Float(weight, 15) * self.LBS_TO_KG
                current_weight_sympy = Float(current_weight, 15) * self.LBS_TO_KG
                height_sympy = Float(height, 15) * self.INCHES_TO_CM
                weight = float(N(weight_sympy, 10))
                current_weight = float(N(current_weight_sympy, 10))
                height = float(N(height_sympy, 10))
            
            # Calculate BMI using SymPy for precision
            height_m_sympy = Float(height, 15) * self.CM_TO_M
            height_m = float(N(height_m_sympy, 10))
            weight_sympy = Float(weight, 15)
            bmi_sympy = weight_sympy / (height_m_sympy ** 2)
            bmi = float(N(bmi_sympy, 10))
            
            # Determine BMI category and recommended weight gain using NumPy for array operations
            bmi_array = np.array([bmi])
            category, category_info = self.get_bmi_category(bmi)
            
            # Get weight gain recommendations
            total_gain_range = category_info['total_gain_range']
            first_trimester_gain = category_info['first_trimester_gain']
            second_third_gain_per_week = category_info['second_third_gain_per_week']
            
            # Calculate expected weight at current week using NumPy and SymPy
            if weeks_pregnant <= 13:
                # First trimester
                weeks_array = np.array([weeks_pregnant])
                gain_range = np.array([first_trimester_gain[0], first_trimester_gain[1]])
                expected_gain = float(np.mean(gain_range) * (weeks_array[0] / 13))
            else:
                # Second and third trimester
                first_trimester_total = np.mean(np.array([first_trimester_gain[0], first_trimester_gain[1]]))
                weeks_remaining = weeks_pregnant - 13
                weekly_gain = np.mean(np.array([second_third_gain_per_week[0], second_third_gain_per_week[1]]))
                expected_gain = float(first_trimester_total + (weeks_remaining * weekly_gain))
            
            # Use SymPy for weight calculations
            weight_sympy = Float(weight, 15)
            expected_gain_sympy = Float(expected_gain, 15)
            expected_weight_sympy = weight_sympy + expected_gain_sympy
            expected_weight = float(N(expected_weight_sympy, 10))
            
            current_weight_sympy = Float(current_weight, 15)
            current_gain_sympy = current_weight_sympy - weight_sympy
            current_gain = float(N(current_gain_sympy, 10))
            
            # Calculate weight gain by trimester using SymPy
            first_trimester_avg = np.mean(np.array([first_trimester_gain[0], first_trimester_gain[1]]))
            second_third_avg = np.mean(np.array([second_third_gain_per_week[0], second_third_gain_per_week[1]]))
            
            first_trimester_weight_sympy = weight_sympy + Float(first_trimester_avg, 15)
            first_trimester_weight = float(N(first_trimester_weight_sympy, 10))
            
            second_trimester_gain_sympy = Float(second_third_avg, 15) * Float('13', 15)
            second_trimester_weight_sympy = first_trimester_weight_sympy + second_trimester_gain_sympy
            second_trimester_weight = float(N(second_trimester_weight_sympy, 10))
            
            third_trimester_gain_sympy = Float(second_third_avg, 15) * Float('14', 15)
            third_trimester_weight_sympy = second_trimester_weight_sympy + third_trimester_gain_sympy
            third_trimester_weight = float(N(third_trimester_weight_sympy, 10))
            
            # Status assessment
            status, status_color, status_description = self.get_status(
                weeks_pregnant, current_gain, expected_gain, category_info
            )
            
            # Calculate progress percentage
            total_weeks = 40
            progress_percentage = min(100, round((weeks_pregnant / total_weeks) * 100, 1)) if weeks_pregnant > 0 else 0
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                weight=weight,
                current_weight=current_weight,
                expected_weight=expected_weight,
                current_gain=current_gain,
                expected_gain=expected_gain,
                total_gain_range=total_gain_range,
                weeks_pregnant=weeks_pregnant,
                progress_percentage=progress_percentage,
                first_trimester_weight=first_trimester_weight,
                second_trimester_weight=second_trimester_weight,
                third_trimester_weight=third_trimester_weight,
                status_color=status_color,
                category_color=category_info['color']
            )
            
            # Get color info
            color_info = self.get_color_info(status_color)
            category_color_info = self.get_color_info(category_info['color'])
            
            result = {
                'success': True,
                'pre_pregnancy_weight': round(weight, 2),
                'current_weight': round(current_weight, 2),
                'bmi': round(bmi, 2),
                'bmi_category': category,
                'bmi_category_description': category_info['description'],
                'bmi_category_color': category_info['color'],
                'weeks_pregnant': weeks_pregnant,
                'current_gain': round(current_gain, 2),
                'expected_gain': round(expected_gain, 2),
                'expected_weight': round(expected_weight, 2),
                'total_gain_range': {
                    'min': round(total_gain_range[0], 2),
                    'max': round(total_gain_range[1], 2)
                },
                'trimester_weights': {
                    'first': round(first_trimester_weight, 2),
                    'second': round(second_trimester_weight, 2),
                    'third': round(third_trimester_weight, 2)
                },
                'status': status,
                'status_color': status_color,
                'status_description': status_description,
                'progress_percentage': progress_percentage,
                'statistics': {
                    'weeks_pregnant': weeks_pregnant,
                    'progress_percentage': progress_percentage,
                    'gain_difference': round(current_gain - expected_gain, 2),
                    'remaining_weeks': max(0, 40 - weeks_pregnant)
                },
                'chart_data': chart_data,
                'color_info': color_info,
                'category_color_info': category_color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Pregnancy Weight Gain Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_bmi_category(self, bmi):
        """Determine BMI category with detailed information"""
        bmi_array = np.array([bmi])
        
        if np.any(bmi_array < 18.5):
            return 'Underweight', {
                'total_gain_range': (12.5, 18),
                'first_trimester_gain': (0.5, 2),
                'second_third_gain_per_week': (0.44, 0.58),
                'color': 'blue',
                'description': 'Underweight (BMI < 18.5). Higher weight gain recommended to support healthy fetal development and maternal health.'
            }
        elif np.any(bmi_array < 25):
            return 'Normal Weight', {
                'total_gain_range': (11.5, 16),
                'first_trimester_gain': (0.5, 2),
                'second_third_gain_per_week': (0.35, 0.5),
                'color': 'green',
                'description': 'Normal Weight (BMI 18.5-24.9). Standard weight gain recommendations apply for optimal pregnancy outcomes.'
            }
        elif np.any(bmi_array < 30):
            return 'Overweight', {
                'total_gain_range': (7, 11.5),
                'first_trimester_gain': (0.5, 2),
                'second_third_gain_per_week': (0.23, 0.33),
                'color': 'yellow',
                'description': 'Overweight (BMI 25-29.9). Moderate weight gain recommended. Focus on nutrient-dense foods and regular physical activity.'
            }
        else:
            return 'Obese', {
                'total_gain_range': (5, 9),
                'first_trimester_gain': (0.5, 2),
                'second_third_gain_per_week': (0.17, 0.27),
                'color': 'orange',
                'description': 'Obese (BMI ≥ 30). Lower weight gain recommended. Consult with healthcare provider for personalized guidance.'
            }
    
    def get_status(self, weeks_pregnant, current_gain, expected_gain, category_info):
        """Determine weight gain status"""
        if weeks_pregnant == 0:
            return 'Pre-Pregnancy', 'blue', 'Pre-pregnancy baseline. Enter your current pregnancy status to track weight gain.'
        
        gain_difference = current_gain - expected_gain
        
        if gain_difference < -2:
            return 'Below Recommended', 'yellow', 'Your weight gain is below the recommended range. Consult with your healthcare provider to ensure adequate nutrition for you and your baby.'
        elif gain_difference > 2:
            return 'Above Recommended', 'orange', 'Your weight gain is above the recommended range. Focus on nutrient-dense foods and discuss with your healthcare provider about healthy weight management strategies.'
        else:
            return 'On Track', 'green', 'Your weight gain is within the recommended range. Continue following a balanced diet and regular physical activity as approved by your healthcare provider.'
    
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
            'pink': {
                'hex': '#ec4899',
                'rgb': 'rgb(236, 72, 153)',
                'tailwind_classes': 'bg-pink-100 text-pink-800 border-pink-300'
            },
            'purple': {
                'hex': '#a855f7',
                'rgb': 'rgb(168, 85, 247)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, weight, current_weight, expected_weight, current_gain, expected_gain, total_gain_range, weeks_pregnant, progress_percentage, first_trimester_weight, second_trimester_weight, third_trimester_weight, status_color, category_color):
        """Prepare chart data for visualization"""
        status_color_info = self.get_color_info(status_color)
        category_color_info = self.get_color_info(category_color)
        
        # Weight Gain Progress Chart
        weight_gain_chart = {
            'type': 'line',
            'data': {
                'labels': ['Pre-Pregnancy', 'Week 13', 'Week 26', 'Week 40'],
                'datasets': [{
                    'label': 'Expected Weight',
                    'data': [weight, first_trimester_weight, second_trimester_weight, third_trimester_weight],
                    'borderColor': category_color_info['hex'],
                    'backgroundColor': category_color_info['hex'] + '20',
                    'borderWidth': 3,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 5,
                    'pointHoverRadius': 7
                }, {
                    'label': 'Current Weight',
                    'data': [weight, None, None, current_weight] if weeks_pregnant > 0 else [weight, None, None, None],
                    'borderColor': status_color_info['hex'],
                    'backgroundColor': status_color_info['hex'] + '20',
                    'borderWidth': 3,
                    'borderDash': [5, 5],
                    'pointRadius': 7,
                    'pointHoverRadius': 9,
                    'pointBackgroundColor': status_color_info['hex'],
                    'pointBorderColor': '#ffffff',
                    'pointBorderWidth': 2
                }]
            }
        }
        
        # Gain Comparison Chart
        gain_comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Current Gain', 'Expected Gain', 'Recommended Range'],
                'datasets': [{
                    'label': 'Weight Gain (kg)',
                    'data': [
                        round(current_gain, 2) if weeks_pregnant > 0 else 0,
                        round(expected_gain, 2),
                        round((total_gain_range[0] + total_gain_range[1]) / 2, 2)
                    ],
                    'backgroundColor': [
                        status_color_info['hex'] if weeks_pregnant > 0 else '#e5e7eb',
                        category_color_info['hex'],
                        '#a855f7'
                    ],
                    'borderColor': [
                        status_color_info['hex'] if weeks_pregnant > 0 else '#d1d5db',
                        category_color_info['hex'],
                        '#9333ea'
                    ],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Trimester Weight Chart
        trimester_weight_chart = {
            'type': 'bar',
            'data': {
                'labels': ['1st Trimester', '2nd Trimester', '3rd Trimester'],
                'datasets': [{
                    'label': 'Expected Weight (kg)',
                    'data': [
                        round(first_trimester_weight, 2),
                        round(second_trimester_weight, 2),
                        round(third_trimester_weight, 2)
                    ],
                    'backgroundColor': ['#ec4899', '#a855f7', '#3b82f6'],
                    'borderColor': ['#db2777', '#9333ea', '#2563eb'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Progress Gauge Chart
        progress_gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Progress', 'Remaining'],
                'datasets': [{
                    'data': [round(progress_percentage, 2), round(100 - progress_percentage, 2)],
                    'backgroundColor': [category_color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(progress_percentage, 1),
                'label': '% Complete',
                'color': category_color_info['hex']
            }
        }
        
        return {
            'weight_gain_chart': weight_gain_chart,
            'gain_comparison_chart': gain_comparison_chart,
            'trimester_weight_chart': trimester_weight_chart,
            'progress_gauge_chart': progress_gauge_chart
        }
