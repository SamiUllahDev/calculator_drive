from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TargetHeartRateCalculator(View):
    """
    Class-based view for Target Heart Rate Calculator
    Calculates target heart rate zones for different training intensities.
    Uses SymPy for precise calculations and NumPy for array operations.
    Enhanced with comprehensive chart data and visualizations.
    """
    template_name = 'fitness_and_health_calculators/target_heart_rate_calculator.html'
    
    # Constants using SymPy Float for precision
    STANDARD_MAX_HR_BASE = Float('220', 15)
    TANAKA_MAX_HR_BASE = Float('208', 15)
    TANAKA_MULTIPLIER = Float('0.7', 15)
    GELLISH_MAX_HR_BASE = Float('207', 15)
    GELLISH_MULTIPLIER = Float('0.7', 15)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Target Heart Rate Calculator',
            'page_title': 'Target Heart Rate Calculator - Calculate Heart Rate Zones',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations using SymPy and NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            age = int(data.get('age', 30))
            resting_hr = int(data.get('resting_hr', 60))
            max_hr_method = data.get('max_hr_method', 'age')  # age, karvonen
            
            # Validation using NumPy
            age_array = np.array([age])
            resting_hr_array = np.array([resting_hr])
            
            if np.any(age_array < 10) or np.any(age_array > 100):
                return JsonResponse({'success': False, 'error': 'Age must be between 10 and 100.'}, status=400)
            if np.any(resting_hr_array < 30) or np.any(resting_hr_array > 120):
                return JsonResponse({'success': False, 'error': 'Resting heart rate must be between 30 and 120 bpm.'}, status=400)
            
            # Calculate max heart rate using SymPy
            age_sympy = Float(age, 15)
            
            # Standard formula: 220 - age
            max_hr_standard_sympy = self.STANDARD_MAX_HR_BASE - age_sympy
            max_hr_standard = int(float(N(max_hr_standard_sympy, 10)))
            
            # Tanaka formula: 208 - (0.7 * age)
            max_hr_tanaka_sympy = self.TANAKA_MAX_HR_BASE - (self.TANAKA_MULTIPLIER * age_sympy)
            max_hr_tanaka = int(float(N(max_hr_tanaka_sympy, 10)))
            
            # Gellish formula: 207 - (0.7 * age)
            max_hr_gellish_sympy = self.GELLISH_MAX_HR_BASE - (self.GELLISH_MULTIPLIER * age_sympy)
            max_hr_gellish = int(float(N(max_hr_gellish_sympy, 10)))
            
            # Use standard for main calculation
            max_hr = max_hr_standard
            
            # Calculate heart rate reserve (HRR) using SymPy
            resting_hr_sympy = Float(resting_hr, 15)
            max_hr_sympy = Float(max_hr, 15)
            hrr_sympy = max_hr_sympy - resting_hr_sympy
            hrr = int(float(N(hrr_sympy, 10)))
            
            # Target heart rate zones using SymPy
            zones = self.calculate_zones(max_hr, resting_hr, hrr)
            
            # Get zone category information
            zone_categories = self.get_zone_categories()
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                max_hr=max_hr,
                resting_hr=resting_hr,
                hrr=hrr,
                zones=zones,
                max_hr_standard=max_hr_standard,
                max_hr_tanaka=max_hr_tanaka,
                max_hr_gellish=max_hr_gellish
            )
            
            result = {
                'success': True,
                'age': age,
                'resting_hr': resting_hr,
                'max_hr': {
                    'standard': max_hr_standard,
                    'tanaka': max_hr_tanaka,
                    'gellish': max_hr_gellish
                },
                'hrr': hrr,
                'zones': zones,
                'zone_categories': zone_categories,
                'statistics': {
                    'max_hr': max_hr,
                    'resting_hr': resting_hr,
                    'hrr': hrr,
                    'zones_count': len(zones)
                },
                'chart_data': chart_data
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Target Heart Rate Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def calculate_zones(self, max_hr, resting_hr, hrr):
        """Calculate heart rate zones using SymPy"""
        max_hr_sympy = Float(max_hr, 15)
        resting_hr_sympy = Float(resting_hr, 15)
        hrr_sympy = Float(hrr, 15)
        
        zones_config = [
            ('warmup', 'Warm-up', 50, 60, 'blue', 'Light activity for warm-up and recovery. Improves blood flow and prepares muscles.'),
            ('fat_burn', 'Fat Burn', 60, 70, 'green', 'Optimal zone for fat burning. Low to moderate intensity, sustainable for longer durations.'),
            ('aerobic', 'Aerobic', 70, 80, 'yellow', 'Cardiovascular fitness zone. Improves heart and lung function, builds endurance.'),
            ('anaerobic', 'Anaerobic', 80, 90, 'orange', 'High-intensity training zone. Improves speed, power, and anaerobic capacity.'),
            ('maximum', 'Maximum', 90, 100, 'red', 'Maximum effort zone. Short bursts only, improves peak performance. Use sparingly.')
        ]
        
        zones = {}
        for zone_key, zone_name, percent_min, percent_max, color, description in zones_config:
            percent_min_sympy = Float(percent_min, 15) / Float('100', 15)
            percent_max_sympy = Float(percent_max, 15) / Float('100', 15)
            
            # Standard method
            hr_min_standard = int(float(N(max_hr_sympy * percent_min_sympy, 10)))
            hr_max_standard = int(float(N(max_hr_sympy * percent_max_sympy, 10)))
            
            # Karvonen method
            hr_min_karvonen = int(float(N(resting_hr_sympy + (hrr_sympy * percent_min_sympy), 10)))
            hr_max_karvonen = int(float(N(resting_hr_sympy + (hrr_sympy * percent_max_sympy), 10)))
            
            zones[zone_key] = {
                'name': zone_name,
                'percent_min': percent_min,
                'percent_max': percent_max,
                'hr_min_standard': hr_min_standard,
                'hr_max_standard': hr_max_standard,
                'hr_min_karvonen': hr_min_karvonen,
                'hr_max_karvonen': hr_max_karvonen,
                'hr_avg_standard': int((hr_min_standard + hr_max_standard) / 2),
                'hr_avg_karvonen': int((hr_min_karvonen + hr_max_karvonen) / 2),
                'color': color,
                'description': description
            }
        
        return zones
    
    def get_zone_categories(self):
        """Get zone category information"""
        return {
            'warmup': {
                'intensity': 'Very Light',
                'rpe': '2-3',
                'duration': '5-10 minutes',
                'benefits': 'Warm-up, recovery, active rest'
            },
            'fat_burn': {
                'intensity': 'Light',
                'rpe': '4-5',
                'duration': '30-60 minutes',
                'benefits': 'Fat burning, endurance base building'
            },
            'aerobic': {
                'intensity': 'Moderate',
                'rpe': '6-7',
                'duration': '20-40 minutes',
                'benefits': 'Cardiovascular fitness, endurance'
            },
            'anaerobic': {
                'intensity': 'Hard',
                'rpe': '8-9',
                'duration': '5-15 minutes',
                'benefits': 'Speed, power, anaerobic capacity'
            },
            'maximum': {
                'intensity': 'Maximum',
                'rpe': '10',
                'duration': '1-5 minutes',
                'benefits': 'Peak performance, sprint training'
            }
        }
    
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
    
    def prepare_chart_data(self, max_hr, resting_hr, hrr, zones, max_hr_standard, max_hr_tanaka, max_hr_gellish):
        """Prepare chart data for visualization"""
        # Heart Rate Zones Chart
        zones_chart = {
            'type': 'bar',
            'data': {
                'labels': [zone['name'] for zone in zones.values()],
                'datasets': [{
                    'label': 'Min HR (Standard)',
                    'data': [zone['hr_min_standard'] for zone in zones.values()],
                    'backgroundColor': '#3b82f6',
                    'borderColor': '#2563eb',
                    'borderWidth': 2
                }, {
                    'label': 'Max HR (Standard)',
                    'data': [zone['hr_max_standard'] for zone in zones.values()],
                    'backgroundColor': '#10b981',
                    'borderColor': '#059669',
                    'borderWidth': 2
                }]
            }
        }
        
        # Zone Range Chart
        zone_range_chart = {
            'type': 'bar',
            'data': {
                'labels': [zone['name'] for zone in zones.values()],
                'datasets': [{
                    'label': 'Heart Rate Range',
                    'data': [
                        [zone['hr_min_standard'], zone['hr_max_standard']] for zone in zones.values()
                    ],
                    'backgroundColor': [self.get_color_info(zone['color'])['hex'] for zone in zones.values()],
                    'borderColor': [self.get_color_info(zone['color'])['hex'] for zone in zones.values()],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Max HR Comparison Chart
        max_hr_comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Standard', 'Tanaka', 'Gellish'],
                'datasets': [{
                    'label': 'Max Heart Rate (bpm)',
                    'data': [max_hr_standard, max_hr_tanaka, max_hr_gellish],
                    'backgroundColor': ['#3b82f6', '#10b981', '#a855f7'],
                    'borderColor': ['#2563eb', '#059669', '#9333ea'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Heart Rate Scale Chart
        hr_scale_data = []
        hr_scale_labels = []
        hr_scale_colors = []
        
        for zone in zones.values():
            hr_scale_data.append(zone['hr_max_standard'] - zone['hr_min_standard'])
            hr_scale_labels.append(zone['name'])
            hr_scale_colors.append(self.get_color_info(zone['color'])['hex'])
        
        hr_scale_chart = {
            'type': 'doughnut',
            'data': {
                'labels': hr_scale_labels,
                'datasets': [{
                    'data': hr_scale_data,
                    'backgroundColor': hr_scale_colors,
                    'borderColor': '#ffffff',
                    'borderWidth': 2
                }]
            }
        }
        
        return {
            'zones_chart': zones_chart,
            'zone_range_chart': zone_range_chart,
            'max_hr_comparison_chart': max_hr_comparison_chart,
            'hr_scale_chart': hr_scale_chart
        }
