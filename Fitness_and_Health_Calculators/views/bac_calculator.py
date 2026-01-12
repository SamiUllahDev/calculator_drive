from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BacCalculator(View):
    """
    Class-based view for BAC (Blood Alcohol Content) Calculator
    Calculates BAC using Widmark formula with SymPy for precision.
    """
    template_name = 'fitness_and_health_calculators/bac_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'BAC Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            gender = data.get('gender', 'male').lower()
            weight = float(data.get('weight', 70))
            weight_unit = data.get('weight_unit', 'kg')
            drinks = float(data.get('drinks', 2))
            drink_type = data.get('drink_type', 'beer')  # beer, wine, liquor
            hours = float(data.get('hours', 0))
            
            # Validation
            if weight <= 0:
                return JsonResponse({'success': False, 'error': 'Weight must be greater than zero.'}, status=400)
            if drinks < 0:
                return JsonResponse({'success': False, 'error': 'Number of drinks cannot be negative.'}, status=400)
            if hours < 0:
                return JsonResponse({'success': False, 'error': 'Hours cannot be negative.'}, status=400)
            
            # Convert weight to kg using SymPy for precision
            if weight_unit == 'lbs':
                weight_kg = float(N(Float(weight, 15) * Float(0.453592, 15), 10))
            else:
                weight_kg = weight
            
            # Standard drink sizes (in grams of pure alcohol)
            # 1 standard drink = 14g pure alcohol (US)
            drink_alcohol_grams = {
                'beer': 14,      # 12 oz beer (5% ABV)
                'wine': 14,      # 5 oz wine (12% ABV)
                'liquor': 14     # 1.5 oz liquor (40% ABV)
            }
            
            total_alcohol_grams = drinks * drink_alcohol_grams.get(drink_type, 14)
            
            # Widmark formula: BAC = (Alcohol consumed in grams / (Body weight in kg × r)) - (β × hours)
            # r = distribution ratio (0.68 for men, 0.55 for women)
            # β = elimination rate (0.15 g/L per hour average)
            
            r = Float(0.68, 15) if gender in ['male', 'm'] else Float(0.55, 15)
            beta = Float(0.15, 15)
            
            # Calculate BAC using SymPy for precision
            weight_sym = Float(weight_kg, 15)
            alcohol_sym = Float(total_alcohol_grams, 15)
            hours_sym = Float(hours, 15)
            
            # BAC = (alcohol / (weight × r)) - (beta × hours)
            bac_numerator = alcohol_sym
            bac_denominator = weight_sym * r
            bac_before_elimination = bac_numerator / bac_denominator
            elimination_amount = beta * hours_sym
            bac = float(N(bac_before_elimination - elimination_amount, 10))
            
            # Ensure BAC is not negative
            if bac < 0:
                bac = 0
            
            # Legal limits
            legal_limit_us = 0.08
            legal_limit_uk = 0.08
            legal_limit_canada = 0.08
            
            # Time to reach legal limit
            if bac > legal_limit_us:
                hours_to_legal = float(N((Float(bac, 15) - Float(legal_limit_us, 15)) / beta, 10))
            else:
                hours_to_legal = 0
            
            # Time to zero BAC
            if bac > 0:
                hours_to_zero = float(N(Float(bac, 15) / beta, 10))
            else:
                hours_to_zero = 0
            
            # Effects based on BAC
            effect, effect_color, category = self.get_bac_effects(bac)
            
            # Calculate scale position (0-100%)
            scale_position = self.calculate_scale_position(bac, legal_limit_us)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                bac=bac,
                legal_limit=legal_limit_us,
                effect_color=effect_color,
                hours_to_zero=hours_to_zero
            )
            
            # Get color info
            color_info = self.get_color_info(effect_color)
            
            result = {
                'success': True,
                'gender': gender,
                'weight_kg': round(weight_kg, 1),
                'drinks': drinks,
                'drink_type': drink_type,
                'hours': hours,
                'total_alcohol_grams': round(total_alcohol_grams, 1),
                'bac': round(bac, 3),
                'bac_percent': round(bac * 100, 2),
                'legal_limit': legal_limit_us,
                'hours_to_legal': round(hours_to_legal, 1),
                'hours_to_zero': round(hours_to_zero, 1),
                'effect': effect,
                'effect_color': effect_color,
                'category': category,
                'over_limit': bac > legal_limit_us,
                'scale_position': scale_position,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"BAC Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_bac_effects(self, bac):
        """Determine BAC effects and category"""
        if bac < 0.02:
            return 'No effects', 'green', 'Safe'
        elif bac < 0.05:
            return 'Mild effects', 'yellow', 'Low'
        elif bac < 0.08:
            return 'Impaired', 'orange', 'Moderate'
        elif bac < 0.15:
            return 'Significantly impaired', 'red', 'High'
        elif bac < 0.20:
            return 'Severely impaired', 'red', 'Very High'
        else:
            return 'Dangerous/Coma risk', 'red', 'Extreme'
    
    def calculate_scale_position(self, bac, legal_limit):
        """Calculate BAC indicator position on scale (0-100%)"""
        # Scale: 0% to 0.20% (200% of legal limit)
        max_display = 0.20
        position = (bac / max_display) * 100
        return min(100.0, max(0.0, float(position)))
    
    def get_color_info(self, effect_color):
        """Get color information for the effect level"""
        color_map = {
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
        return color_map.get(effect_color, color_map['green'])
    
    def prepare_chart_data(self, bac, legal_limit, effect_color, hours_to_zero):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(effect_color)
        
        # BAC Gauge Chart Data
        max_display = 0.20  # 0.20% BAC max for display
        bac_percentage = min((bac / max_display) * 100, 100)
        
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['BAC', 'Remaining'],
                'datasets': [{
                    'data': [round(bac_percentage, 2), round(100 - bac_percentage, 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(bac * 100, 2),
                'label': '% BAC',
                'color': color_info['hex']
            }
        }
        
        # BAC Effects Chart
        effects_data = []
        effects_colors = []
        effects_labels = []
        
        effects_ranges = [
            {'name': 'No effects', 'max': 0.02, 'color': '#10b981'},
            {'name': 'Mild effects', 'max': 0.05, 'color': '#eab308'},
            {'name': 'Impaired', 'max': 0.08, 'color': '#f97316'},
            {'name': 'Significantly impaired', 'max': 0.15, 'color': '#ef4444'},
            {'name': 'Severely impaired', 'max': 0.20, 'color': '#dc2626'}
        ]
        
        current_effect_index = 0
        for idx, effect_info in enumerate(effects_ranges):
            if bac <= effect_info['max']:
                current_effect_index = idx
                break
        else:
            current_effect_index = len(effects_ranges) - 1
        
        for idx, effect_info in enumerate(effects_ranges):
            effects_labels.append(effect_info['name'])
            if idx == current_effect_index:
                effects_data.append(round(bac * 100, 2))
                effects_colors.append(effect_info['color'])
            else:
                effects_data.append(0)
                effects_colors.append('#e5e7eb')
        
        effects_chart = {
            'type': 'bar',
            'data': {
                'labels': effects_labels,
                'datasets': [{
                    'label': 'BAC %',
                    'data': effects_data,
                    'backgroundColor': effects_colors,
                    'borderColor': [r['color'] for r in effects_ranges],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            },
            'current_effect_index': current_effect_index,
            'effects_info': effects_ranges
        }
        
        # Comparison Chart (Current BAC vs Legal Limit)
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Your BAC', 'Legal Limit'],
                'datasets': [{
                    'label': 'BAC %',
                    'data': [round(bac * 100, 2), round(legal_limit * 100, 2)],
                    'backgroundColor': [color_info['hex'], '#6b7280'],
                    'borderColor': [color_info['hex'], '#4b5563'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Time to Zero Chart
        time_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Hours to Zero BAC'],
                'datasets': [{
                    'label': 'Hours',
                    'data': [round(hours_to_zero, 1)],
                    'backgroundColor': color_info['hex'],
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'gauge_chart': gauge_chart,
            'effects_chart': effects_chart,
            'comparison_chart': comparison_chart,
            'time_chart': time_chart
        }
