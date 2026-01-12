from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RootCalculator(View):
    """
    Enhanced Professional Root Calculator
    Calculates square roots, cube roots, and nth roots with step-by-step solutions.
    """
    template_name = 'math_calculators/root_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Root Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num < 0:
                return None, f'{name} must be non-negative.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _validate_positive_integer(self, value, name):
        """Validate that a value is a positive integer"""
        try:
            num = int(value)
            if num <= 0:
                return None, f'{name} must be greater than zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid positive integer.'
    
    def _calculate_root(self, number, root_index):
        """Calculate nth root of a number"""
        if root_index == 2:
            # Square root
            result = math.sqrt(number)
        elif root_index == 3:
            # Cube root
            result = number ** (1/3)
        else:
            # Nth root
            result = number ** (1/root_index)
        
        return result
    
    def _is_perfect_power(self, number, root_index):
        """Check if number is a perfect power"""
        if root_index == 2:
            # Perfect square
            sqrt = int(math.sqrt(number))
            return sqrt * sqrt == number, sqrt
        elif root_index == 3:
            # Perfect cube
            cube_root = int(round(number ** (1/3)))
            return cube_root ** 3 == number, cube_root
        else:
            # Perfect nth power
            nth_root = int(round(number ** (1/root_index)))
            return nth_root ** root_index == number, nth_root
    
    def _prepare_step_by_step(self, number, root_index, result):
        """Prepare step-by-step solution"""
        steps = []
        
        root_name = {2: 'square', 3: 'cube'}.get(root_index, f'{root_index}th')
        
        steps.append(f"Given: {root_name.capitalize()} root of {number}")
        steps.append(f"  √[{root_index}]({number}) = ?")
        steps.append("")
        
        # Check if it's a perfect power
        is_perfect, perfect_root = self._is_perfect_power(number, root_index)
        
        if is_perfect:
            steps.append(f"Step 1: Recognize perfect {root_name} root")
            steps.append(f"  {number} is a perfect {root_name} root")
            steps.append(f"  {number} = {perfect_root}^{root_index}")
            steps.append("")
            steps.append(f"Step 2: Calculate root")
            steps.append(f"  √[{root_index}]({number}) = √[{root_index}]({perfect_root}^{root_index}) = {perfect_root}")
            steps.append("")
            steps.append(f"Result: {result:.6f}")
        else:
            steps.append(f"Step 1: Apply {root_name} root formula")
            if root_index == 2:
                steps.append(f"  √{number} = {number}^(1/2)")
            elif root_index == 3:
                steps.append(f"  ∛{number} = {number}^(1/3)")
            else:
                steps.append(f"  √[{root_index}]({number}) = {number}^(1/{root_index})")
            steps.append("")
            
            steps.append("Step 2: Calculate using exponentiation")
            if root_index == 2:
                steps.append(f"  {number}^(1/2) = {result:.6f}")
            elif root_index == 3:
                steps.append(f"  {number}^(1/3) = {result:.6f}")
            else:
                steps.append(f"  {number}^(1/{root_index}) = {result:.6f}")
            steps.append("")
            
            steps.append("Step 3: Verification")
            verification = result ** root_index
            steps.append(f"  ({result:.6f})^{root_index} = {verification:.6f}")
            if abs(verification - number) < 0.0001:
                steps.append(f"  ✓ Verification successful!")
            else:
                steps.append(f"  (Small rounding difference: {abs(verification - number):.6f})")
        
        return steps
    
    def _prepare_chart_data(self, number, root_index, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Root comparison chart (for different root indices)
            if root_index <= 10:
                root_values = []
                root_labels = []
                for i in range(2, min(11, root_index + 4)):
                    if i == root_index:
                        root_values.append(result)
                    else:
                        root_values.append(number ** (1/i))
                    root_labels.append(f'{i}th root')
                
                chart_data['root_comparison_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': root_labels,
                        'datasets': [{
                            'label': 'Root Value',
                            'data': root_values,
                            'backgroundColor': [
                                'rgba(59, 130, 246, 0.6)' if i != root_index - 2 else 'rgba(16, 185, 129, 0.8)'
                                for i in range(len(root_values))
                            ],
                            'borderColor': [
                                '#3b82f6' if i != root_index - 2 else '#10b981'
                                for i in range(len(root_values))
                            ],
                            'borderWidth': 2
                        }]
                    }
                }
            
            # Power visualization
            powers = []
            power_labels = []
            for i in range(1, 6):
                power = result ** i
                powers.append(power)
                power_labels.append(f'{result:.2f}^{i}')
            
            chart_data['power_chart'] = {
                'type': 'line',
                'data': {
                    'labels': power_labels,
                    'datasets': [{
                        'label': 'Power Value',
                        'data': powers,
                        'borderColor': '#8b5cf6',
                        'backgroundColor': 'rgba(139, 92, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
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
            number, error1 = self._validate_positive_number(data.get('number'), 'Number')
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            root_index, error2 = self._validate_positive_integer(data.get('root_index', '2'), 'Root index')
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            if root_index > 100:
                return JsonResponse({'success': False, 'error': 'Root index cannot exceed 100.'}, status=400)
            
            # Calculate root
            result = self._calculate_root(number, root_index)
            
            # Check if perfect power
            is_perfect, perfect_root = self._is_perfect_power(number, root_index)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(number, root_index, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(number, root_index, result)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            root_name = {2: 'square', 3: 'cube'}.get(root_index, f'{root_index}th')
            
            response = {
                'success': True,
                'number': number,
                'root_index': root_index,
                'root_name': root_name,
                'result': result,
                'is_perfect': is_perfect,
                'perfect_root': perfect_root if is_perfect else None,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Root Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
