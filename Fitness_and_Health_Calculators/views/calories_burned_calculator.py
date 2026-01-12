from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CaloriesBurnedCalculator(View):
    """
    Class-based view for Calories Burned Calculator
    Calculates calories burned during various activities using MET values.
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/calories_burned_calculator.html'
    
    # MET (Metabolic Equivalent) values for common activities
    MET_VALUES = {
        'walking': {'slow': 2.0, 'moderate': 3.5, 'fast': 4.5, 'very_fast': 5.0},
        'running': {'jogging': 7.0, 'moderate': 8.3, 'fast': 9.8, 'very_fast': 11.0},
        'cycling': {'leisure': 4.0, 'moderate': 6.0, 'vigorous': 8.0, 'racing': 10.0},
        'swimming': {'leisure': 6.0, 'moderate': 8.0, 'vigorous': 10.0, 'butterfly': 13.8},
        'weightlifting': {'light': 3.0, 'moderate': 5.0, 'vigorous': 6.0},
        'yoga': {'hatha': 2.5, 'power': 4.0, 'ashtanga': 6.0},
        'dancing': {'slow': 3.0, 'moderate': 4.8, 'fast': 5.5},
        'basketball': {'casual': 6.0, 'competitive': 8.0},
        'tennis': {'doubles': 5.0, 'singles': 8.0},
        'soccer': {'casual': 7.0, 'competitive': 10.0}
    }
    
    # Activity display names
    ACTIVITY_NAMES = {
        'walking': 'Walking',
        'running': 'Running',
        'cycling': 'Cycling',
        'swimming': 'Swimming',
        'weightlifting': 'Weightlifting',
        'yoga': 'Yoga',
        'dancing': 'Dancing',
        'basketball': 'Basketball',
        'tennis': 'Tennis',
        'soccer': 'Soccer'
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Calories Burned Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            unit_system = data.get('unit_system', 'metric')
            weight = float(data.get('weight', 70))
            activity = data.get('activity', 'walking')
            intensity = data.get('intensity', 'moderate')
            duration_minutes = float(data.get('duration', 30))
            
            # Convert weight to kg if imperial using SymPy for precision
            if unit_system == 'imperial':
                weight_kg = float(N(Float(weight, 15) * Float(0.453592, 15), 10))
            else:
                weight_kg = weight
            
            # Validation
            if weight_kg <= 0 or weight_kg > 300:
                return JsonResponse({'success': False, 'error': 'Weight must be between 1 and 300 kg.'}, status=400)
            if duration_minutes <= 0 or duration_minutes > 600:
                return JsonResponse({'success': False, 'error': 'Duration must be between 1 and 600 minutes.'}, status=400)
            if activity not in self.MET_VALUES:
                return JsonResponse({'success': False, 'error': 'Invalid activity selected.'}, status=400)
            
            # Get MET value
            met_value = self.MET_VALUES.get(activity, {}).get(intensity)
            if met_value is None:
                # Get first available intensity if selected intensity doesn't exist
                available_intensities = list(self.MET_VALUES.get(activity, {}).keys())
                if available_intensities:
                    intensity = available_intensities[0]
                    met_value = self.MET_VALUES[activity][intensity]
                else:
                    met_value = 3.5  # Default moderate activity
            
            # Calculate calories burned using SymPy for precision
            # Formula: Calories = MET × weight(kg) × time(hours)
            duration_hours_sym = Float(duration_minutes, 15) / Float(60, 15)
            met_sym = Float(met_value, 15)
            weight_sym = Float(weight_kg, 15)
            calories_burned = float(N(met_sym * weight_sym * duration_hours_sym, 10))
            
            # Calculate calories per minute
            calories_per_minute = calories_burned / duration_minutes if duration_minutes > 0 else 0
            
            # Calculate for different durations
            durations = {
                '15min': round(float(N(met_sym * weight_sym * Float(0.25, 15), 10)), 1),
                '30min': round(float(N(met_sym * weight_sym * Float(0.5, 15), 10)), 1),
                '45min': round(float(N(met_sym * weight_sym * Float(0.75, 15), 10)), 1),
                '60min': round(float(N(met_sym * weight_sym * Float(1.0, 15), 10)), 1),
                '90min': round(float(N(met_sym * weight_sym * Float(1.5, 15), 10)), 1),
                '120min': round(float(N(met_sym * weight_sym * Float(2.0, 15), 10)), 1)
            }
            
            # Calculate for different intensities of same activity
            intensity_comparison = {}
            if activity in self.MET_VALUES:
                for intensity_name, met in self.MET_VALUES[activity].items():
                    intensity_comparison[intensity_name] = {
                        'met': met,
                        'calories': round(float(N(Float(met, 15) * weight_sym * duration_hours_sym, 10)), 1)
                    }
            
            # Calculate for different activities (same duration and weight)
            activity_comparison = {}
            for act_name, act_intensities in self.MET_VALUES.items():
                # Use moderate intensity or first available
                act_met = act_intensities.get('moderate') or act_intensities.get('casual') or list(act_intensities.values())[0]
                activity_comparison[act_name] = {
                    'name': self.ACTIVITY_NAMES.get(act_name, act_name.title()),
                    'met': act_met,
                    'calories': round(float(N(Float(act_met, 15) * weight_sym * duration_hours_sym, 10)), 1)
                }
            
            # Determine activity color based on MET value
            activity_color = self.get_activity_color(met_value)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                calories_burned=calories_burned,
                durations=durations,
                intensity_comparison=intensity_comparison,
                activity_comparison=activity_comparison,
                activity=activity,
                intensity=intensity,
                activity_color=activity_color
            )
            
            # Get color info
            color_info = self.get_color_info(activity_color)
            
            result = {
                'success': True,
                'weight_kg': round(weight_kg, 1),
                'activity': activity,
                'activity_name': self.ACTIVITY_NAMES.get(activity, activity.title()),
                'intensity': intensity,
                'met_value': met_value,
                'duration_minutes': duration_minutes,
                'calories_burned': round(calories_burned, 1),
                'calories_per_minute': round(calories_per_minute, 2),
                'durations': durations,
                'intensity_comparison': intensity_comparison,
                'activity_comparison': activity_comparison,
                'activity_color': activity_color,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Calories Burned Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_activity_color(self, met_value):
        """Determine color based on MET value (intensity)"""
        if met_value < 3:
            return 'blue'  # Light
        elif met_value < 6:
            return 'green'  # Moderate
        elif met_value < 9:
            return 'orange'  # Vigorous
        else:
            return 'red'  # Very vigorous
    
    def get_color_info(self, activity_color):
        """Get color information for the activity"""
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
        return color_map.get(activity_color, color_map['green'])
    
    def prepare_chart_data(self, calories_burned, durations, intensity_comparison, activity_comparison, activity, intensity, activity_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(activity_color)
        
        # Duration Comparison Chart
        duration_chart = {
            'type': 'bar',
            'data': {
                'labels': ['15 min', '30 min', '45 min', '60 min', '90 min', '120 min'],
                'datasets': [{
                    'label': 'Calories Burned',
                    'data': [
                        durations['15min'],
                        durations['30min'],
                        durations['45min'],
                        durations['60min'],
                        durations['90min'],
                        durations['120min']
                    ],
                    'backgroundColor': color_info['hex'],
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Intensity Comparison Chart
        intensity_labels = []
        intensity_data = []
        intensity_colors = []
        
        for intensity_name, intensity_data_dict in intensity_comparison.items():
            intensity_labels.append(intensity_name.replace('_', ' ').title())
            intensity_data.append(intensity_data_dict['calories'])
            if intensity_name == intensity:
                intensity_colors.append(color_info['hex'])
            else:
                intensity_colors.append('#e5e7eb')
        
        intensity_chart = {
            'type': 'bar',
            'data': {
                'labels': intensity_labels,
                'datasets': [{
                    'label': 'Calories Burned',
                    'data': intensity_data,
                    'backgroundColor': intensity_colors,
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Activity Comparison Chart (top 10 activities)
        activity_labels = []
        activity_data = []
        activity_colors = []
        
        # Sort activities by calories burned
        sorted_activities = sorted(activity_comparison.items(), key=lambda x: x[1]['calories'], reverse=True)[:10]
        
        for act_name, act_data in sorted_activities:
            activity_labels.append(act_data['name'])
            activity_data.append(act_data['calories'])
            if act_name == activity:
                activity_colors.append(color_info['hex'])
            else:
                activity_colors.append('#e5e7eb')
        
        activity_chart = {
            'type': 'bar',
            'data': {
                'labels': activity_labels,
                'datasets': [{
                    'label': 'Calories Burned',
                    'data': activity_data,
                    'backgroundColor': activity_colors,
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'duration_chart': duration_chart,
            'intensity_chart': intensity_chart,
            'activity_chart': activity_chart
        }
