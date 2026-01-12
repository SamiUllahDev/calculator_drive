from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Float, N


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BodyTypeCalculator(View):
    """
    Class-based view for Body Type Calculator
    Determines body type (ectomorph, mesomorph, endomorph) based on measurements.
    Enhanced with SymPy for precision and chart data.
    """
    template_name = 'fitness_and_health_calculators/body_type_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Body Type Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            unit_system = data.get('unit_system', 'metric')
            wrist = float(data.get('wrist', 17))  # cm
            ankle = float(data.get('ankle', 22))  # cm
            height = float(data.get('height', 170))  # cm
            
            # Convert to cm if imperial using SymPy for precision
            if unit_system == 'imperial':
                wrist = float(N(Float(wrist, 15) * Float(2.54, 15), 10))
                ankle = float(N(Float(ankle, 15) * Float(2.54, 15), 10))
                height = float(N(Float(height, 15) * Float(2.54, 15), 10))
            
            # Validation
            if height <= 0 or wrist <= 0 or ankle <= 0:
                return JsonResponse({'success': False, 'error': 'All measurements must be greater than zero.'}, status=400)
            if height < 100 or height > 250:
                return JsonResponse({'success': False, 'error': 'Height must be between 100 and 250 cm.'}, status=400)
            if wrist < 10 or wrist > 30:
                return JsonResponse({'success': False, 'error': 'Wrist measurement must be between 10 and 30 cm.'}, status=400)
            if ankle < 15 or ankle > 40:
                return JsonResponse({'success': False, 'error': 'Ankle measurement must be between 15 and 40 cm.'}, status=400)
            
            # Calculate frame size using SymPy for precision
            # Wrist-to-height ratio
            wrist_sym = Float(wrist, 15)
            height_sym = Float(height, 15)
            wrist_ratio = float(N((wrist_sym / height_sym) * Float(100, 15), 10))
            
            # Determine frame size
            if wrist_ratio < 9.9:
                frame_size = 'small'
                frame_size_name = 'Small'
            elif wrist_ratio < 10.9:
                frame_size = 'medium'
                frame_size_name = 'Medium'
            else:
                frame_size = 'large'
                frame_size_name = 'Large'
            
            # Body type determination
            # Ectomorph: Small frame, narrow shoulders, fast metabolism
            # Mesomorph: Medium frame, athletic build, moderate metabolism
            # Endomorph: Large frame, wider build, slower metabolism
            
            if frame_size == 'small':
                body_type = 'ectomorph'
                body_type_name = 'Ectomorph'
                body_type_color = 'blue'
                description = 'Naturally lean with fast metabolism, narrow frame, difficulty gaining weight'
                characteristics = [
                    'Naturally thin and lean',
                    'Fast metabolism',
                    'Difficulty gaining weight',
                    'Narrow shoulders and hips',
                    'Long limbs',
                    'Low body fat percentage'
                ]
            elif frame_size == 'medium':
                body_type = 'mesomorph'
                body_type_name = 'Mesomorph'
                body_type_color = 'green'
                description = 'Athletic build, naturally muscular, moderate metabolism, gains muscle easily'
                characteristics = [
                    'Athletic and muscular build',
                    'Moderate metabolism',
                    'Gains muscle easily',
                    'Broad shoulders',
                    'Narrow waist',
                    'Naturally strong'
                ]
            else:
                body_type = 'endomorph'
                body_type_name = 'Endomorph'
                body_type_color = 'orange'
                description = 'Naturally wider frame, stores fat easily, slower metabolism, gains muscle and fat easily'
                characteristics = [
                    'Naturally wider frame',
                    'Slower metabolism',
                    'Stores fat easily',
                    'Wider hips and shoulders',
                    'Gains muscle and fat easily',
                    'Rounder body shape'
                ]
            
            # Calculate ankle-to-height ratio for additional insight
            ankle_sym = Float(ankle, 15)
            ankle_ratio = float(N((ankle_sym / height_sym) * Float(100, 15), 10))
            
            # Prepare chart data
            chart_data = self.prepare_chart_data(
                body_type=body_type,
                body_type_color=body_type_color,
                wrist_ratio=wrist_ratio,
                ankle_ratio=ankle_ratio,
                frame_size=frame_size
            )
            
            # Get color info
            color_info = self.get_color_info(body_type_color)
            
            result = {
                'success': True,
                'wrist_cm': round(wrist, 1),
                'ankle_cm': round(ankle, 1),
                'height_cm': round(height, 1),
                'wrist_ratio': round(wrist_ratio, 2),
                'ankle_ratio': round(ankle_ratio, 2),
                'frame_size': frame_size,
                'frame_size_name': frame_size_name,
                'body_type': body_type,
                'body_type_name': body_type_name,
                'body_type_color': body_type_color,
                'description': description,
                'characteristics': characteristics,
                'chart_data': chart_data,
                'color_info': color_info
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Body Type Calculator Error: {error_details}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
    
    def get_color_info(self, body_type_color):
        """Get color information for the body type"""
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
            }
        }
        return color_map.get(body_type_color, color_map['blue'])
    
    def prepare_chart_data(self, body_type, body_type_color, wrist_ratio, ankle_ratio, frame_size):
        """Prepare chart data for visualization"""
        color_info = self.get_color_info(body_type_color)
        
        # Body Type Distribution Chart
        body_types_data = []
        body_types_colors = []
        body_types_labels = ['Ectomorph', 'Mesomorph', 'Endomorph']
        
        if body_type == 'ectomorph':
            body_types_data = [100, 0, 0]
            body_types_colors = ['#3b82f6', '#e5e7eb', '#e5e7eb']
        elif body_type == 'mesomorph':
            body_types_data = [0, 100, 0]
            body_types_colors = ['#e5e7eb', '#10b981', '#e5e7eb']
        else:
            body_types_data = [0, 0, 100]
            body_types_colors = ['#e5e7eb', '#e5e7eb', '#f97316']
        
        body_type_chart = {
            'type': 'doughnut',
            'data': {
                'labels': body_types_labels,
                'datasets': [{
                    'data': body_types_data,
                    'backgroundColor': body_types_colors,
                    'borderColor': ['#2563eb', '#059669', '#ea580c'],
                    'borderWidth': 2
                }]
            }
        }
        
        # Frame Size Comparison Chart
        frame_sizes_labels = ['Small', 'Medium', 'Large']
        frame_sizes_data = []
        frame_sizes_colors = []
        
        if frame_size == 'small':
            frame_sizes_data = [100, 0, 0]
            frame_sizes_colors = ['#3b82f6', '#e5e7eb', '#e5e7eb']
        elif frame_size == 'medium':
            frame_sizes_data = [0, 100, 0]
            frame_sizes_colors = ['#e5e7eb', '#10b981', '#e5e7eb']
        else:
            frame_sizes_data = [0, 0, 100]
            frame_sizes_colors = ['#e5e7eb', '#e5e7eb', '#f97316']
        
        frame_size_chart = {
            'type': 'bar',
            'data': {
                'labels': frame_sizes_labels,
                'datasets': [{
                    'label': 'Frame Size',
                    'data': frame_sizes_data,
                    'backgroundColor': frame_sizes_colors,
                    'borderColor': ['#2563eb', '#059669', '#ea580c'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Ratios Comparison Chart
        ratios_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Wrist-to-Height', 'Ankle-to-Height'],
                'datasets': [{
                    'label': 'Ratio (%)',
                    'data': [round(wrist_ratio, 2), round(ankle_ratio, 2)],
                    'backgroundColor': [color_info['hex'], '#8b5cf6'],
                    'borderColor': [color_info['hex'], '#7c3aed'],
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        return {
            'body_type_chart': body_type_chart,
            'frame_size_chart': frame_size_chart,
            'ratios_chart': ratios_chart
        }
