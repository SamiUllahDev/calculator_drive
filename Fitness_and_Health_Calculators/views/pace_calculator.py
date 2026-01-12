from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PaceCalculator(View):
    """
    Class-based view for Pace Calculator
    Calculates running pace, speed, and time conversions.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/pace_calculator.html'
    
    # Conversion constants using SymPy Float for precision
    MILES_TO_KM = Float('1.60934', 15)
    KM_TO_MILES = Float('0.621371', 15)
    SECONDS_PER_MINUTE = Float('60', 15)
    MINUTES_PER_HOUR = Float('60', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Pace Calculator',
            'page_title': 'Pace Calculator - Calculate Running Pace & Speed',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'pace_from_time')
            
            if calc_type == 'pace_from_time':
                # Calculate pace from distance and time
                distance = float(data.get('distance', 5))
                distance_unit = data.get('distance_unit', 'km')
                hours = int(data.get('hours', 0))
                minutes = int(data.get('minutes', 30))
                seconds = int(data.get('seconds', 0))
                
                # Convert to km using SymPy
                if distance_unit == 'miles':
                    distance_km = float(N(Float(distance, 15) * self.MILES_TO_KM, 10))
                else:
                    distance_km = float(distance)
                
                # Calculate total time using SymPy
                hours_sympy = Float(hours, 15)
                minutes_sympy = Float(minutes, 15)
                seconds_sympy = Float(seconds, 15)
                
                total_minutes = float(N(hours_sympy * self.MINUTES_PER_HOUR + minutes_sympy + seconds_sympy / self.SECONDS_PER_MINUTE, 10))
                total_seconds = float(N(hours_sympy * self.MINUTES_PER_HOUR * self.SECONDS_PER_MINUTE + minutes_sympy * self.SECONDS_PER_MINUTE + seconds_sympy, 10))
                
                # Validation using NumPy
                distance_array = np.array([distance_km])
                time_array = np.array([total_minutes])
                
                if np.any(distance_array <= 0):
                    return JsonResponse({'success': False, 'error': 'Distance must be greater than zero.'}, status=400)
                if np.any(time_array <= 0):
                    return JsonResponse({'success': False, 'error': 'Time must be greater than zero.'}, status=400)
                
                # Calculate pace per km using SymPy
                distance_km_sympy = Float(distance_km, 15)
                total_minutes_sympy = Float(total_minutes, 15)
                pace_per_km_total = float(N(total_minutes_sympy / distance_km_sympy, 10))
                pace_per_km_minutes = int(pace_per_km_total)
                pace_per_km_seconds = int((pace_per_km_total - pace_per_km_minutes) * 60)
                
                # Calculate pace per mile using SymPy
                distance_miles = float(N(distance_km_sympy / self.MILES_TO_KM, 10))
                distance_miles_sympy = Float(distance_miles, 15)
                pace_per_mile_total = float(N(total_minutes_sympy / distance_miles_sympy, 10))
                pace_per_mile_minutes = int(pace_per_mile_total)
                pace_per_mile_seconds = int((pace_per_mile_total - pace_per_mile_minutes) * 60)
                
                # Calculate speed using SymPy
                speed_kmh = float(N((distance_km_sympy / total_minutes_sympy) * self.MINUTES_PER_HOUR, 10))
                speed_mph = float(N(Float(speed_kmh, 15) / self.MILES_TO_KM, 10))
                
                # Calculate for common distances using SymPy
                pace_per_km_sympy = Float(pace_per_km_total, 15)
                common_distances = {
                    '1km': round(float(N(pace_per_km_sympy * Float('1', 15), 10)), 2),
                    '5km': round(float(N(pace_per_km_sympy * Float('5', 15), 10)), 2),
                    '10km': round(float(N(pace_per_km_sympy * Float('10', 15), 10)), 2),
                    'half_marathon': round(float(N(pace_per_km_sympy * Float('21.0975', 15), 10)), 2),
                    'marathon': round(float(N(pace_per_km_sympy * Float('42.195', 15), 10)), 2)
                }
                
                # Determine pace category
                pace_category, pace_color, pace_description = self.get_pace_category(pace_per_km_total)
                
                # Prepare chart data
                chart_data = self.prepare_chart_data(
                    pace_per_km=pace_per_km_total,
                    speed_kmh=speed_kmh,
                    common_distances=common_distances,
                    pace_color=pace_color
                )
                
                # Get color info
                color_info = self.get_color_info(pace_color)
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'distance_km': round(distance_km, 2),
                    'distance_miles': round(distance_miles, 2),
                    'total_time_minutes': round(total_minutes, 2),
                    'total_time_seconds': round(total_seconds, 2),
                    'pace_per_km': {
                        'minutes': pace_per_km_minutes,
                        'seconds': pace_per_km_seconds,
                        'total': round(pace_per_km_total, 2)
                    },
                    'pace_per_mile': {
                        'minutes': pace_per_mile_minutes,
                        'seconds': pace_per_mile_seconds,
                        'total': round(pace_per_mile_total, 2)
                    },
                    'speed': {
                        'kmh': round(speed_kmh, 2),
                        'mph': round(speed_mph, 2)
                    },
                    'common_distances': common_distances,
                    'pace_category': pace_category,
                    'pace_color': pace_color,
                    'pace_description': pace_description,
                    'statistics': {
                        'pace_per_km_total': round(pace_per_km_total, 2),
                        'pace_per_mile_total': round(pace_per_mile_total, 2),
                        'speed_kmh': round(speed_kmh, 2),
                        'speed_mph': round(speed_mph, 2)
                    },
                    'chart_data': chart_data,
                    'color_info': color_info
                }
                
            elif calc_type == 'time_from_pace':
                # Calculate time from distance and pace
                distance = float(data.get('distance', 5))
                distance_unit = data.get('distance_unit', 'km')
                pace_minutes = int(data.get('pace_minutes', 5))
                pace_seconds = int(data.get('pace_seconds', 0))
                
                # Convert to km using SymPy
                if distance_unit == 'miles':
                    distance_km = float(N(Float(distance, 15) * self.MILES_TO_KM, 10))
                else:
                    distance_km = float(distance)
                
                # Calculate pace using SymPy
                pace_minutes_sympy = Float(pace_minutes, 15)
                pace_seconds_sympy = Float(pace_seconds, 15)
                pace_total = float(N(pace_minutes_sympy + pace_seconds_sympy / self.SECONDS_PER_MINUTE, 10))
                
                # Validation using NumPy
                distance_array = np.array([distance_km])
                pace_array = np.array([pace_total])
                
                if np.any(distance_array <= 0):
                    return JsonResponse({'success': False, 'error': 'Distance must be greater than zero.'}, status=400)
                if np.any(pace_array <= 0):
                    return JsonResponse({'success': False, 'error': 'Pace must be greater than zero.'}, status=400)
                
                # Calculate total time using SymPy
                distance_km_sympy = Float(distance_km, 15)
                pace_total_sympy = Float(pace_total, 15)
                total_minutes = float(N(distance_km_sympy * pace_total_sympy, 10))
                
                hours = int(total_minutes // 60)
                minutes = int(total_minutes % 60)
                secs = int((total_minutes % 1) * 60)
                
                # Determine pace category
                pace_category, pace_color, pace_description = self.get_pace_category(pace_total)
                
                # Get color info
                color_info = self.get_color_info(pace_color)
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'distance_km': round(distance_km, 2),
                    'pace_per_km': round(pace_total, 2),
                    'total_time': {
                        'hours': hours,
                        'minutes': minutes,
                        'seconds': secs,
                        'total_minutes': round(total_minutes, 2)
                    },
                    'pace_category': pace_category,
                    'pace_color': pace_color,
                    'pace_description': pace_description,
                    'color_info': color_info
                }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Pace Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def get_pace_category(self, pace_per_km):
        """Determine pace category based on pace per km"""
        # Categories based on pace per km (minutes)
        if pace_per_km < 3.5:
            return 'Elite', 'red', 'Elite runner pace. World-class performance level.'
        elif pace_per_km < 4.0:
            return 'Advanced', 'orange', 'Advanced runner pace. Excellent performance.'
        elif pace_per_km < 5.0:
            return 'Intermediate', 'yellow', 'Intermediate runner pace. Good fitness level.'
        elif pace_per_km < 6.0:
            return 'Recreational', 'green', 'Recreational runner pace. Healthy activity level.'
        elif pace_per_km < 7.0:
            return 'Beginner', 'blue', 'Beginner runner pace. Building fitness.'
        else:
            return 'Walking', 'purple', 'Walking pace. Great for health and recovery.'
    
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
                'hex': '#f59e0b',
                'rgb': 'rgb(245, 158, 11)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300'
            },
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            },
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            },
            'purple': {
                'hex': '#a855f7',
                'rgb': 'rgb(168, 85, 247)',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300'
            }
        }
        return color_map.get(category_color, color_map['blue'])
    
    def prepare_chart_data(self, pace_per_km, speed_kmh, common_distances, pace_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(pace_color)
        
        # Pace Gauge Chart
        max_pace = 10.0  # 10 min/km max display
        pace_percentage = min((pace_per_km / max_pace) * 100, 100)
        
        pace_gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Pace', 'Remaining'],
                'datasets': [{
                    'data': [round(pace_percentage, 2), round(100 - pace_percentage, 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(pace_per_km, 2),
                'label': 'min/km',
                'color': color_info['hex']
            }
        }
        
        # Common Distances Chart
        distances_labels = ['1km', '5km', '10km', 'Half Marathon', 'Marathon']
        distances_values = [
            common_distances['1km'],
            common_distances['5km'],
            common_distances['10km'],
            common_distances['half_marathon'],
            common_distances['marathon']
        ]
        
        distances_chart = {
            'type': 'bar',
            'data': {
                'labels': distances_labels,
                'datasets': [{
                    'label': 'Time (minutes)',
                    'data': distances_values,
                    'backgroundColor': color_info['hex'],
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Speed Comparison Chart
        speed_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Speed'],
                'datasets': [
                    {
                        'label': 'km/h',
                        'data': [round(speed_kmh, 2)],
                        'backgroundColor': '#3b82f6',
                        'borderColor': '#2563eb',
                        'borderWidth': 2,
                        'borderRadius': 8
                    },
                    {
                        'label': 'mph',
                        'data': [round(speed_kmh / 1.60934, 2)],
                        'backgroundColor': '#10b981',
                        'borderColor': '#059669',
                        'borderWidth': 2,
                        'borderRadius': 8
                    }
                ]
            }
        }
        
        return {
            'pace_gauge_chart': pace_gauge_chart,
            'distances_chart': distances_chart,
            'speed_chart': speed_chart
        }
