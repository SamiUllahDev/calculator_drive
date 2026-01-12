from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IdealWeightCalculator(View):
    """
    Class-based view for Ideal Weight Calculator
    Calculates ideal body weight using multiple formulas (Robinson, Miller, Devine, Hamwi).
    """
    template_name = 'fitness_and_health_calculators/ideal_weight_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Ideal Weight Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            unit_system = data.get('unit_system', 'metric')
            gender = data.get('gender', 'male').lower()
            height = float(data.get('height', 170))
            height_in = float(data.get('height_in', 0))
            
            # Convert to inches if metric
            if unit_system == 'metric':
                height_inches = height / 2.54
            else:
                height_inches = height * 12 + height_in
            
            # Convert to cm for calculations
            height_cm = height_inches * 2.54
            
            # Validation
            if height_inches < 48 or height_inches > 96:
                return JsonResponse({'success': False, 'error': 'Height must be between 48 and 96 inches.'}, status=400)
            
            # Calculate ideal weight using multiple formulas
            # Robinson formula (1983)
            if gender in ['male', 'm']:
                robinson_kg = 52 + (1.9 * (height_inches - 60))
            else:
                robinson_kg = 49 + (1.7 * (height_inches - 60))
            
            # Miller formula (1983)
            if gender in ['male', 'm']:
                miller_kg = 56.2 + (1.41 * (height_inches - 60))
            else:
                miller_kg = 53.1 + (1.36 * (height_inches - 60))
            
            # Devine formula (1974)
            if gender in ['male', 'm']:
                devine_kg = 50 + (2.3 * (height_inches - 60))
            else:
                devine_kg = 45.5 + (2.3 * (height_inches - 60))
            
            # Hamwi formula (1964)
            if gender in ['male', 'm']:
                hamwi_kg = 48 + (2.7 * (height_inches - 60))
            else:
                hamwi_kg = 45.5 + (2.2 * (height_inches - 60))
            
            # Average of all formulas
            average_kg = (robinson_kg + miller_kg + devine_kg + hamwi_kg) / 4
            
            # Convert to requested unit
            if unit_system == 'imperial':
                robinson = robinson_kg / 0.453592
                miller = miller_kg / 0.453592
                devine = devine_kg / 0.453592
                hamwi = hamwi_kg / 0.453592
                average = average_kg / 0.453592
                unit = 'lbs'
            else:
                robinson = robinson_kg
                miller = miller_kg
                devine = devine_kg
                hamwi = hamwi_kg
                average = average_kg
                unit = 'kg'
            
            # BMI range for ideal weight (18.5-24.9)
            height_m = height_cm / 100
            ideal_bmi_min = 18.5
            ideal_bmi_max = 24.9
            
            ideal_weight_min_kg = ideal_bmi_min * (height_m ** 2)
            ideal_weight_max_kg = ideal_bmi_max * (height_m ** 2)
            
            if unit_system == 'imperial':
                ideal_weight_min = ideal_weight_min_kg / 0.453592
                ideal_weight_max = ideal_weight_max_kg / 0.453592
            else:
                ideal_weight_min = ideal_weight_min_kg
                ideal_weight_max = ideal_weight_max_kg
            
            result = {
                'success': True,
                'height_cm': round(height_cm, 1),
                'height_inches': round(height_inches, 1),
                'gender': gender,
                'unit': unit,
                'formulas': {
                    'robinson': round(robinson, 1),
                    'miller': round(miller, 1),
                    'devine': round(devine, 1),
                    'hamwi': round(hamwi, 1),
                    'average': round(average, 1)
                },
                'bmi_range': {
                    'min': round(ideal_weight_min, 1),
                    'max': round(ideal_weight_max, 1)
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
