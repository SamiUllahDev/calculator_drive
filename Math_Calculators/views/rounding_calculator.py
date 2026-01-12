from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RoundingCalculator(View):
    """
    Enhanced Professional Rounding Calculator
    Rounds numbers to different decimal places with various rounding methods.
    """
    template_name = 'math_calculators/rounding_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rounding Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _validate_positive_integer(self, value, name):
        """Validate that a value is a non-negative integer"""
        try:
            num = int(value)
            if num < 0:
                return None, f'{name} must be non-negative.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid integer.'
    
    def _round_number(self, number, decimal_places, rounding_method):
        """Round number using specified method"""
        if rounding_method == 'nearest':
            # Standard rounding (round half to even - banker's rounding)
            multiplier = 10 ** decimal_places
            return round(number * multiplier) / multiplier
        elif rounding_method == 'up':
            # Round up (ceiling)
            multiplier = 10 ** decimal_places
            return math.ceil(number * multiplier) / multiplier
        elif rounding_method == 'down':
            # Round down (floor)
            multiplier = 10 ** decimal_places
            return math.floor(number * multiplier) / multiplier
        elif rounding_method == 'toward_zero':
            # Round toward zero (truncate)
            multiplier = 10 ** decimal_places
            if number >= 0:
                return math.floor(number * multiplier) / multiplier
            else:
                return math.ceil(number * multiplier) / multiplier
        elif rounding_method == 'away_zero':
            # Round away from zero
            multiplier = 10 ** decimal_places
            if number >= 0:
                return math.ceil(number * multiplier) / multiplier
            else:
                return math.floor(number * multiplier) / multiplier
        else:
            return round(number, decimal_places)
    
    def _prepare_step_by_step(self, number, decimal_places, rounding_method, result):
        """Prepare step-by-step solution"""
        steps = []
        
        method_names = {
            'nearest': 'Round to Nearest',
            'up': 'Round Up (Ceiling)',
            'down': 'Round Down (Floor)',
            'toward_zero': 'Round Toward Zero',
            'away_zero': 'Round Away from Zero'
        }
        
        steps.append(f"Given: Number = {number}, Decimal Places = {decimal_places}")
        steps.append(f"Method: {method_names.get(rounding_method, 'Round to Nearest')}")
        steps.append("")
        
        steps.append("Step 1: Identify the rounding position")
        multiplier = 10 ** decimal_places
        steps.append(f"  Multiply by 10^{decimal_places} = {multiplier}")
        steps.append(f"  {number} × {multiplier} = {number * multiplier:.10f}")
        steps.append("")
        
        steps.append("Step 2: Apply rounding method")
        if rounding_method == 'nearest':
            steps.append(f"  Round to nearest integer: {round(number * multiplier)}")
        elif rounding_method == 'up':
            steps.append(f"  Round up (ceiling): {math.ceil(number * multiplier)}")
        elif rounding_method == 'down':
            steps.append(f"  Round down (floor): {math.floor(number * multiplier)}")
        elif rounding_method == 'toward_zero':
            if number >= 0:
                steps.append(f"  Round toward zero (floor): {math.floor(number * multiplier)}")
            else:
                steps.append(f"  Round toward zero (ceiling): {math.ceil(number * multiplier)}")
        elif rounding_method == 'away_zero':
            if number >= 0:
                steps.append(f"  Round away from zero (ceiling): {math.ceil(number * multiplier)}")
            else:
                steps.append(f"  Round away from zero (floor): {math.floor(number * multiplier)}")
        steps.append("")
        
        steps.append("Step 3: Divide by multiplier")
        if rounding_method == 'nearest':
            rounded_int = round(number * multiplier)
        elif rounding_method == 'up':
            rounded_int = math.ceil(number * multiplier)
        elif rounding_method == 'down':
            rounded_int = math.floor(number * multiplier)
        elif rounding_method == 'toward_zero':
            rounded_int = math.floor(number * multiplier) if number >= 0 else math.ceil(number * multiplier)
        else:
            rounded_int = math.ceil(number * multiplier) if number >= 0 else math.floor(number * multiplier)
        
        steps.append(f"  {rounded_int} / {multiplier} = {result:.{decimal_places}f}")
        steps.append("")
        steps.append(f"Result: {result:.{decimal_places}f}")
        
        return steps
    
    def _prepare_chart_data(self, number, decimal_places, rounding_method, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Rounding comparison chart (showing different rounding methods)
            methods = ['nearest', 'up', 'down', 'toward_zero', 'away_zero']
            method_labels = ['Nearest', 'Up', 'Down', 'Toward Zero', 'Away from Zero']
            rounded_values = []
            
            for method in methods:
                rounded_values.append(self._round_number(number, decimal_places, method))
            
            chart_data['rounding_comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': method_labels,
                    'datasets': [{
                        'label': 'Rounded Value',
                        'data': rounded_values,
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.8)' if method == rounding_method else 'rgba(59, 130, 246, 0.6)'
                            for method in methods
                        ],
                        'borderColor': [
                            '#10b981' if method == rounding_method else '#3b82f6'
                            for method in methods
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            # Decimal places comparison
            if decimal_places <= 10:
                places_values = []
                places_labels = []
                for i in range(0, min(11, decimal_places + 6)):
                    places_values.append(self._round_number(number, i, rounding_method))
                    places_labels.append(f'{i} places')
                
                chart_data['decimal_places_chart'] = {
                    'type': 'line',
                    'data': {
                        'labels': places_labels,
                        'datasets': [{
                            'label': 'Rounded Value',
                            'data': places_values,
                            'borderColor': '#8b5cf6',
                            'backgroundColor': 'rgba(139, 92, 246, 0.1)',
                            'borderWidth': 2,
                            'fill': True,
                            'tension': 0.4,
                            'pointRadius': 4
                        }]
                    }
                }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            number, error1 = self._validate_number(data.get('number'), 'Number')
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            decimal_places, error2 = self._validate_positive_integer(data.get('decimal_places', '0'), 'Decimal places')
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            if decimal_places > 20:
                return JsonResponse({'success': False, 'error': 'Decimal places cannot exceed 20.'}, status=400)
            
            rounding_method = data.get('rounding_method', 'nearest')
            if rounding_method not in ['nearest', 'up', 'down', 'toward_zero', 'away_zero']:
                rounding_method = 'nearest'
            
            # Round number
            result = self._round_number(number, decimal_places, rounding_method)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(number, decimal_places, rounding_method, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(number, decimal_places, rounding_method, result)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            method_names = {
                'nearest': 'Round to Nearest',
                'up': 'Round Up (Ceiling)',
                'down': 'Round Down (Floor)',
                'toward_zero': 'Round Toward Zero',
                'away_zero': 'Round Away from Zero'
            }
            
            response = {
                'success': True,
                'number': number,
                'decimal_places': decimal_places,
                'rounding_method': rounding_method,
                'rounding_method_name': method_names.get(rounding_method, 'Round to Nearest'),
                'result': result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Rounding Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
