from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class WeightWatcherPointsCalculator(View):
    """
    Class-based view for Weight Watcher Points Calculator
    Calculates SmartPoints using Weight Watchers formula.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/weight_watcher_points_calculator.html'
    
    # Weight Watchers SmartPoints formula constants using SymPy
    CALORIES_DIVISOR = Float('33', 15)
    SATURATED_FAT_DIVISOR = Float('4', 15)
    SUGAR_DIVISOR = Float('9', 15)
    PROTEIN_DIVISOR = Float('10', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Weight Watcher Points Calculator',
            'page_title': 'Weight Watchers Points Calculator - Calculate SmartPoints',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calories = float(data.get('calories', 200))
            saturated_fat = float(data.get('saturated_fat', 0))
            sugar = float(data.get('sugar', 0))
            protein = float(data.get('protein', 0))
            daily_allowance = int(data.get('daily_allowance', 23))
            
            # Validation using NumPy
            calories_array = np.array([calories])
            if np.any(calories_array < 0):
                return JsonResponse({'success': False, 'error': 'Calories cannot be negative.'}, status=400)
            
            # Weight Watchers SmartPoints formula using SymPy
            calories_sympy = Float(calories, 15)
            saturated_fat_sympy = Float(saturated_fat, 15)
            sugar_sympy = Float(sugar, 15)
            protein_sympy = Float(protein, 15)
            
            # Points = (calories / 33) + (saturated_fat / 4) + (sugar / 9) - (protein / 10)
            calories_points_sympy = calories_sympy / self.CALORIES_DIVISOR
            saturated_fat_points_sympy = saturated_fat_sympy / self.SATURATED_FAT_DIVISOR
            sugar_points_sympy = sugar_sympy / self.SUGAR_DIVISOR
            protein_points_sympy = protein_sympy / self.PROTEIN_DIVISOR
            
            points_sympy = calories_points_sympy + saturated_fat_points_sympy + sugar_points_sympy - protein_points_sympy
            
            # Ensure points are not negative using SymPy
            if float(N(points_sympy, 10)) < 0:
                points_sympy = Float('0', 15)
            
            points = float(N(points_sympy, 10))
            
            # Calculate remaining points using SymPy
            daily_allowance_sympy = Float(daily_allowance, 15)
            remaining_points_sympy = daily_allowance_sympy - points_sympy
            remaining_points = float(N(remaining_points_sympy, 10))
            
            # Get points status
            points_status, status_color, status_description = self.get_points_status(points, daily_allowance)
            
            # Calculate percentage of daily allowance used
            percentage_used_sympy = (points_sympy / daily_allowance_sympy) * Float('100', 15)
            percentage_used = float(N(percentage_used_sympy, 10))
            
            # Breakdown of points contribution
            points_breakdown = {
                'calories': {
                    'value': round(float(N(calories_points_sympy, 10)), 2),
                    'contribution': round(float(N((calories_points_sympy / points_sympy) * Float('100', 15), 10)), 1) if points > 0 else 0
                },
                'saturated_fat': {
                    'value': round(float(N(saturated_fat_points_sympy, 10)), 2),
                    'contribution': round(float(N((saturated_fat_points_sympy / points_sympy) * Float('100', 15), 10)), 1) if points > 0 else 0
                },
                'sugar': {
                    'value': round(float(N(sugar_points_sympy, 10)), 2),
                    'contribution': round(float(N((sugar_points_sympy / points_sympy) * Float('100', 15), 10)), 1) if points > 0 else 0
                },
                'protein': {
                    'value': round(float(N(protein_points_sympy, 10)), 2),
                    'contribution': round(float(N((protein_points_sympy / points_sympy) * Float('100', 15), 10)), 1) if points > 0 else 0
                }
            }
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                points=points,
                daily_allowance=daily_allowance,
                remaining_points=remaining_points,
                percentage_used=percentage_used,
                points_breakdown=points_breakdown,
                status_color=status_color
            )
            
            # Get color info
            color_info = self.get_color_info(status_color)
            
            result = {
                'success': True,
                'calories': round(calories, 1),
                'saturated_fat': round(saturated_fat, 1),
                'sugar': round(sugar, 1),
                'protein': round(protein, 1),
                'points': round(points, 1),
                'daily_allowance': daily_allowance,
                'remaining_points': round(remaining_points, 1),
                'over_budget': points > daily_allowance,
                'points_status': points_status,
                'status_color': status_color,
                'status_description': status_description,
                'percentage_used': round(percentage_used, 1),
                'points_breakdown': points_breakdown,
                'statistics': {
                    'points': round(points, 1),
                    'daily_allowance': daily_allowance,
                    'remaining_points': round(remaining_points, 1),
                    'percentage_used': round(percentage_used, 1),
                    'over_budget': points > daily_allowance
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
            print(f"Weight Watchers Points Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_points_status(self, points, daily_allowance):
        """Determine points status with detailed information"""
        percentage = (points / daily_allowance) * 100 if daily_allowance > 0 else 0
        
        if points <= daily_allowance * 0.5:
            return 'Excellent', 'green', 'You\'re well within your daily points allowance. Great job making healthy choices!'
        elif points <= daily_allowance * 0.75:
            return 'Good', 'blue', 'You\'re doing well staying within your points budget. Keep up the good work!'
        elif points <= daily_allowance:
            return 'On Track', 'yellow', 'You\'re at or near your daily points limit. Be mindful of remaining points for the day.'
        elif points <= daily_allowance * 1.25:
            return 'Over Budget', 'orange', 'You\'ve exceeded your daily points allowance. Consider using weekly points or making lower-point choices.'
        else:
            return 'Significantly Over', 'red', 'You\'ve significantly exceeded your daily points. Consider adjusting your food choices or using weekly points.'
    
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
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, points, daily_allowance, remaining_points, percentage_used, points_breakdown, status_color):
        """Prepare chart data for visualization"""
        status_color_info = self.get_color_info(status_color)
        
        # Points Progress Chart
        points_progress_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Points Used', 'Remaining'],
                'datasets': [{
                    'data': [round(points, 2), round(max(0, remaining_points), 2)],
                    'backgroundColor': [status_color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(points, 1),
                'label': 'of ' + str(daily_allowance),
                'color': status_color_info['hex']
            }
        }
        
        # Points Breakdown Chart
        points_breakdown_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Calories', 'Saturated Fat', 'Sugar', 'Protein'],
                'datasets': [{
                    'label': 'Points Contribution',
                    'data': [
                        points_breakdown['calories']['value'],
                        points_breakdown['saturated_fat']['value'],
                        points_breakdown['sugar']['value'],
                        -points_breakdown['protein']['value']  # Negative because protein reduces points
                    ],
                    'backgroundColor': ['#3b82f6', '#f97316', '#eab308', '#10b981'],
                    'borderColor': ['#2563eb', '#ea580c', '#ca8a04', '#059669'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Points Breakdown Percentage Chart
        breakdown_percentage_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Calories', 'Saturated Fat', 'Sugar', 'Protein Reduction'],
                'datasets': [{
                    'data': [
                        abs(points_breakdown['calories']['contribution']),
                        abs(points_breakdown['saturated_fat']['contribution']),
                        abs(points_breakdown['sugar']['contribution']),
                        abs(points_breakdown['protein']['contribution'])
                    ],
                    'backgroundColor': ['#3b82f6', '#f97316', '#eab308', '#10b981'],
                    'borderColor': '#ffffff',
                    'borderWidth': 2
                }]
            }
        }
        
        # Daily Allowance Comparison Chart
        allowance_comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Points Used', 'Daily Allowance', 'Remaining'],
                'datasets': [{
                    'label': 'Points',
                    'data': [
                        round(points, 1),
                        daily_allowance,
                        round(max(0, remaining_points), 1)
                    ],
                    'backgroundColor': [status_color_info['hex'], '#6b7280', '#10b981'],
                    'borderColor': [status_color_info['hex'], '#4b5563', '#059669'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'points_progress_chart': points_progress_chart,
            'points_breakdown_chart': points_breakdown_chart,
            'breakdown_percentage_chart': breakdown_percentage_chart,
            'allowance_comparison_chart': allowance_comparison_chart
        }
