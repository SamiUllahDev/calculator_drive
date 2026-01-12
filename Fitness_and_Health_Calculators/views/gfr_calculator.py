from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N, Pow


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GfrCalculator(View):
    """
    Class-based view for GFR (Glomerular Filtration Rate) Calculator
    Calculates eGFR using CKD-EPI and MDRD formulas.
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/gfr_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'GFR Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            age = int(data.get('age', 40))
            gender = data.get('gender', 'male').lower()
            race = data.get('race', 'non_black').lower()
            creatinine = float(data.get('creatinine', 1.0))
            unit_system = data.get('unit_system', 'metric')
            
            # Convert creatinine to mg/dL if needed using SymPy for precision
            if unit_system == 'si':
                creatinine_mgdl = float(N(Float(creatinine, 15) / Float(88.4, 15), 10))  # Convert from μmol/L to mg/dL
            else:
                creatinine_mgdl = creatinine
            
            # Validation
            if age < 18 or age > 100:
                return JsonResponse({'success': False, 'error': 'Age must be between 18 and 100.'}, status=400)
            if creatinine_mgdl <= 0 or creatinine_mgdl > 10:
                return JsonResponse({'success': False, 'error': 'Creatinine must be between 0.1 and 10 mg/dL.'}, status=400)
            
            # CKD-EPI formula parameters
            if gender in ['male', 'm']:
                if race == 'black':
                    if creatinine_mgdl <= 0.9:
                        kappa = 0.9
                        alpha = -0.411
                        min_value = 1.0
                    else:
                        kappa = 0.9
                        alpha = -1.209
                        min_value = 1.0
                else:
                    if creatinine_mgdl <= 0.9:
                        kappa = 0.9
                        alpha = -0.411
                        min_value = 1.0
                    else:
                        kappa = 0.9
                        alpha = -1.209
                        min_value = 1.0
            else:
                if race == 'black':
                    if creatinine_mgdl <= 0.7:
                        kappa = 0.7
                        alpha = -0.329
                        min_value = 1.018
                    else:
                        kappa = 0.7
                        alpha = -1.209
                        min_value = 1.018
                else:
                    if creatinine_mgdl <= 0.7:
                        kappa = 0.7
                        alpha = -0.329
                        min_value = 1.018
                    else:
                        kappa = 0.7
                        alpha = -1.209
                        min_value = 1.018
            
            # CKD-EPI calculation using SymPy for precision
            creat_sym = Float(creatinine_mgdl, 15)
            kappa_sym = Float(kappa, 15)
            alpha_sym = Float(alpha, 15)
            age_sym = Float(age, 15)
            
            # Calculate (creatinine/kappa)^alpha
            ratio = creat_sym / kappa_sym
            ratio_power = Pow(ratio, alpha_sym)
            
            # Calculate 0.993^age
            age_factor = Pow(Float(0.993, 15), age_sym)
            
            # Base calculation
            base_calc = Float(141, 15) * ratio_power * age_factor
            
            # Apply gender and race factors
            if gender in ['male', 'm']:
                if race == 'black':
                    egfr_ckdepi = float(N(base_calc * Float(1.159, 15), 10))
                else:
                    egfr_ckdepi = float(N(base_calc, 10))
            else:
                if race == 'black':
                    egfr_ckdepi = float(N(base_calc * Float(1.018, 15) * Float(1.159, 15), 10))
                else:
                    egfr_ckdepi = float(N(base_calc * Float(1.018, 15), 10))
            
            # MDRD formula using SymPy
            creat_power = Pow(creat_sym, Float(-1.154, 15))
            age_power = Pow(age_sym, Float(-0.203, 15))
            mdrd_base = Float(175, 15) * creat_power * age_power
            
            if gender in ['male', 'm']:
                if race == 'black':
                    egfr_mdrd = float(N(mdrd_base * Float(1.212, 15), 10))
                else:
                    egfr_mdrd = float(N(mdrd_base, 10))
            else:
                if race == 'black':
                    egfr_mdrd = float(N(mdrd_base * Float(0.742, 15) * Float(1.212, 15), 10))
                else:
                    egfr_mdrd = float(N(mdrd_base * Float(0.742, 15), 10))
            
            # Use CKD-EPI as primary
            egfr = egfr_ckdepi
            
            # CKD stages
            if egfr >= 90:
                stage = 'Stage 1'
                stage_desc = 'Normal or high'
                stage_color = 'green'
            elif egfr >= 60:
                stage = 'Stage 2'
                stage_desc = 'Mildly decreased'
                stage_color = 'yellow'
            elif egfr >= 45:
                stage = 'Stage 3a'
                stage_desc = 'Mildly to moderately decreased'
                stage_color = 'orange'
            elif egfr >= 30:
                stage = 'Stage 3b'
                stage_desc = 'Moderately to severely decreased'
                stage_color = 'orange'
            elif egfr >= 15:
                stage = 'Stage 4'
                stage_desc = 'Severely decreased'
                stage_color = 'red'
            else:
                stage = 'Stage 5'
                stage_desc = 'Kidney failure'
                stage_color = 'red'
            
            # Calculate scale position for visual indicator
            scale_position = self.calculate_scale_position(egfr)
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                egfr=egfr,
                egfr_ckdepi=egfr_ckdepi,
                egfr_mdrd=egfr_mdrd,
                stage=stage,
                stage_color=stage_color
            )
            
            # Get color info
            color_info = self.get_color_info(stage_color)
            
            result = {
                'success': True,
                'age': age,
                'gender': gender,
                'race': race,
                'creatinine_mgdl': round(creatinine_mgdl, 2),
                'egfr_ckdepi': round(egfr_ckdepi, 1),
                'egfr_mdrd': round(egfr_mdrd, 1),
                'egfr': round(egfr, 1),
                'stage': stage,
                'stage_desc': stage_desc,
                'stage_color': stage_color,
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
            print(f"GFR Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_color_info(self, stage_color):
        """Get color information for the CKD stage"""
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
        return color_map.get(stage_color, color_map['green'])
    
    def calculate_scale_position(self, egfr):
        """Calculate position on scale (0-100%) for visual indicator"""
        # Normal range is typically 90-120, but we'll use 0-150 as full scale
        max_egfr = 150
        min_egfr = 0
        position = ((egfr - min_egfr) / (max_egfr - min_egfr)) * 100
        return max(0, min(100, round(position, 1)))
    
    def prepare_chart_data(self, egfr, egfr_ckdepi, egfr_mdrd, stage, stage_color):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(stage_color)
        
        # Formulas Comparison Chart
        formulas_chart = {
            'type': 'bar',
            'data': {
                'labels': ['CKD-EPI', 'MDRD'],
                'datasets': [{
                    'label': 'eGFR (mL/min/1.73m²)',
                    'data': [round(egfr_ckdepi, 1), round(egfr_mdrd, 1)],
                    'backgroundColor': [color_info['hex'], '#6b7280'],
                    'borderColor': [color_info['hex'], '#4b5563'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # CKD Stages Chart
        stages_labels = ['Stage 1\n(≥90)', 'Stage 2\n(60-89)', 'Stage 3a\n(45-59)', 'Stage 3b\n(30-44)', 'Stage 4\n(15-29)', 'Stage 5\n(<15)']
        stages_data = []
        stages_colors = []
        
        stage_ranges = [
            (90, 200, 'green'),
            (60, 89, 'yellow'),
            (45, 59, 'orange'),
            (30, 44, 'orange'),
            (15, 29, 'red'),
            (0, 14, 'red')
        ]
        
        for min_val, max_val, color in stage_ranges:
            if min_val <= egfr <= max_val:
                stages_data.append(100)
                stages_colors.append(self.get_color_info(color)['hex'])
            else:
                stages_data.append(0)
                stages_colors.append('#e5e7eb')
        
        stages_chart = {
            'type': 'bar',
            'data': {
                'labels': stages_labels,
                'datasets': [{
                    'label': 'Current Stage',
                    'data': stages_data,
                    'backgroundColor': stages_colors,
                    'borderColor': ['#10b981', '#eab308', '#f97316', '#f97316', '#ef4444', '#ef4444'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # eGFR Range Chart
        range_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Your eGFR'],
                'datasets': [{
                    'label': 'eGFR (mL/min/1.73m²)',
                    'data': [round(egfr, 1)],
                    'backgroundColor': color_info['hex'],
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'formulas_chart': formulas_chart,
            'stages_chart': stages_chart,
            'range_chart': range_chart
        }
