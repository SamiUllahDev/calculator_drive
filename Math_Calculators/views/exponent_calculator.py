from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ExponentCalculator(View):
    """
    Professional Exponent Calculator
    Calculates exponentiation, roots, and related operations.
    Supports positive, negative, and fractional exponents.
    """
    template_name = 'math_calculators/exponent_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Exponent Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name, allow_zero=False, allow_negative=True):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num == 0:
                return None, f'{name} cannot be zero.'
            if not allow_negative and num < 0:
                return None, f'{name} must be non-negative.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_exponent(self, base, exponent):
        """Calculate base raised to the power of exponent"""
        try:
            # Handle special cases
            if base == 0 and exponent < 0:
                return None, 'Zero cannot be raised to a negative power.'
            
            if base < 0 and exponent != int(exponent):
                # Negative base with fractional exponent
                if abs(exponent) < 1:
                    return None, 'Negative base with fractional exponent may result in complex number.'
            
            result = base ** exponent
            
            # Check for overflow
            if math.isinf(result):
                return None, 'Result is too large (overflow).'
            
            return result, None
        except Exception as e:
            return None, f'Error calculating exponent: {str(e)}'
    
    def _calculate_root(self, base, root_index):
        """Calculate nth root of base"""
        try:
            if base < 0 and root_index % 2 == 0:
                return None, 'Even root of negative number is not a real number.'
            
            if root_index == 0:
                return None, 'Root index cannot be zero.'
            
            if root_index == 1:
                return base, None
            
            if root_index == 2:
                # Square root
                if base < 0:
                    return None, 'Square root of negative number is not a real number.'
                return math.sqrt(base), None
            elif root_index == 3:
                # Cube root
                if base < 0:
                    return -math.pow(-base, 1/3), None
                return math.pow(base, 1/3), None
            else:
                # General nth root
                if base < 0 and root_index % 2 == 0:
                    return None, 'Even root of negative number is not a real number.'
                
                if base < 0:
                    return -math.pow(-base, 1/root_index), None
                return math.pow(base, 1/root_index), None
        except Exception as e:
            return None, f'Error calculating root: {str(e)}'
    
    def prepare_chart_data(self, base, exponent, result, calc_type):
        """Prepare chart data for exponent visualization"""
        if not result or math.isnan(result) or math.isinf(result):
            return {}
        
        if calc_type == 'exponent':
            # Exponential growth/decay chart
            x_values = []
            y_values = []
            
            # Generate points around the exponent
            if exponent >= 0:
                start = max(0, exponent - 5)
                end = exponent + 5
            else:
                start = exponent - 5
                end = min(0, exponent + 5)
            
            step = (end - start) / 20 if end != start else 0.1
            if step == 0:
                step = 0.1
            
            for i in range(21):
                x = start + i * step
                try:
                    if base > 0:
                        y = base ** x
                        if not (math.isnan(y) or math.isinf(y)):
                            x_values.append(x)
                            y_values.append(y)
                except:
                    pass
            
            chart_data = {
                'type': 'line',
                'data': {
                    'labels': [f'{x:.2f}' for x in x_values],
                    'datasets': [{
                        'label': f'{base}^x',
                        'data': y_values,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
                    }]
                }
            }
            
            # Mark the calculated point
            if exponent in x_values or (min(x_values) <= exponent <= max(x_values) if x_values else False):
                chart_data['data']['datasets'].append({
                    'label': f'Result ({base}^{exponent})',
                    'data': [result if abs(x - exponent) < 0.01 else None for x in x_values],
                    'borderColor': '#ef4444',
                    'backgroundColor': '#ef4444',
                    'pointRadius': 8,
                    'pointHoverRadius': 10,
                    'showLine': False
                })
            
            return {'exponent_chart': chart_data}
        
        elif calc_type == 'root':
            # Root visualization - show base and result
            chart_data = {
                'type': 'bar',
                'data': {
                    'labels': ['Base', 'Root Result'],
                    'datasets': [{
                        'label': 'Values',
                        'data': [abs(base), abs(result)],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            return {'root_chart': chart_data}
        
        return {}
    
    def prepare_display_data(self, base, exponent, result, calc_type, root_index=None):
        """Prepare formatted display data for frontend"""
        display_data = {
            'calc_type': calc_type,
            'result': result,
            'formatted_results': []
        }
        
        if calc_type == 'exponent':
            display_data['formatted_results'] = [
                {
                    'label': 'Base',
                    'value': f"{base:.6f}",
                    'is_primary': False
                },
                {
                    'label': 'Exponent',
                    'value': f"{exponent:.6f}",
                    'is_primary': False
                },
                {
                    'label': 'Result',
                    'value': f"{result:.6f}",
                    'is_primary': True
                },
                {
                    'label': 'Scientific Notation',
                    'value': f"{result:.6e}",
                    'is_primary': False
                },
                {
                    'label': 'Expression',
                    'value': f"{base:.6f}^{exponent:.6f}",
                    'is_primary': False
                }
            ]
        elif calc_type == 'root':
            root_name = 'Square Root' if root_index == 2 else ('Cube Root' if root_index == 3 else f'{root_index}th Root')
            display_data['formatted_results'] = [
                {
                    'label': 'Base',
                    'value': f"{base:.6f}",
                    'is_primary': False
                },
                {
                    'label': 'Root Index',
                    'value': str(root_index),
                    'is_primary': False
                },
                {
                    'label': 'Result',
                    'value': f"{result:.6f}",
                    'is_primary': True
                },
                {
                    'label': 'Scientific Notation',
                    'value': f"{result:.6e}",
                    'is_primary': False
                },
                {
                    'label': 'Expression',
                    'value': f"√[{root_index}]({base:.6f})",
                    'is_primary': False
                },
                {
                    'label': 'Verification',
                    'value': f"{result:.6f}^{root_index} = {result**root_index:.6f}",
                    'is_primary': False
                }
            ]
        
        return display_data
    
    def prepare_step_by_step(self, base, exponent, result, calc_type, root_index=None):
        """Prepare step-by-step solution"""
        steps = []
        
        if calc_type == 'exponent':
            steps.append(f"Given: {base:.6f}^{exponent:.6f}")
            
            # Check if exponent is integer
            if exponent == int(exponent):
                steps.append(f"Step 1: The exponent is an integer ({int(exponent)})")
                if exponent > 0:
                    steps.append(f"Step 2: Multiply {base:.6f} by itself {int(exponent)} times")
                    if int(exponent) <= 10:
                        # Show intermediate steps for small exponents
                        intermediate = 1
                        for i in range(int(exponent)):
                            intermediate *= base
                            steps.append(f"  Step {i+1}: {intermediate:.6f}")
                    else:
                        steps.append(f"  (Calculation performed)")
                    steps.append(f"Step 3: Result = {result:.6f}")
                elif exponent < 0:
                    steps.append(f"Step 2: Negative exponent means we take the reciprocal")
                    positive_exp = abs(exponent)
                    positive_result = base ** positive_exp
                    steps.append(f"  {base:.6f}^{positive_exp} = {positive_result:.6f}")
                    steps.append(f"Step 3: Result = 1 / {positive_result:.6f} = {result:.6f}")
                else:
                    steps.append(f"Step 2: Any number raised to the power of 0 equals 1")
                    steps.append(f"Step 3: Result = 1")
            else:
                # Fractional exponent
                steps.append(f"Step 1: The exponent is fractional ({exponent:.6f})")
                if exponent > 0:
                    steps.append(f"Step 2: This can be written as {base:.6f}^({exponent:.6f})")
                    steps.append(f"Step 3: Using exponential calculation")
                    steps.append(f"Step 4: Result = {result:.6f}")
                else:
                    steps.append(f"Step 2: Negative fractional exponent")
                    positive_exp = abs(exponent)
                    positive_result = base ** positive_exp
                    steps.append(f"  {base:.6f}^{positive_exp} = {positive_result:.6f}")
                    steps.append(f"Step 3: Result = 1 / {positive_result:.6f} = {result:.6f}")
            
            steps.append(f"Final Answer: {base:.6f}^{exponent:.6f} = {result:.6f}")
        
        elif calc_type == 'root':
            root_name = 'square root' if root_index == 2 else ('cube root' if root_index == 3 else f'{root_index}th root')
            steps.append(f"Given: {root_index}th root of {base:.6f}")
            steps.append(f"Step 1: Calculate {root_name} of {base:.6f}")
            
            if root_index == 2:
                steps.append(f"Step 2: √{base:.6f} = {result:.6f}")
                steps.append(f"Step 3: Verification: {result:.6f}² = {result**2:.6f}")
            elif root_index == 3:
                steps.append(f"Step 2: ∛{base:.6f} = {result:.6f}")
                steps.append(f"Step 3: Verification: {result:.6f}³ = {result**3:.6f}")
            else:
                steps.append(f"Step 2: {base:.6f}^(1/{root_index}) = {result:.6f}")
                steps.append(f"Step 3: Verification: {result:.6f}^{root_index} = {result**root_index:.6f}")
            
            steps.append(f"Final Answer: {root_index}th root of {base:.6f} = {result:.6f}")
        
        return steps
    
    def prepare_step_by_step_html(self, steps):
        """Prepare step-by-step solution as HTML structure"""
        if not steps or not isinstance(steps, list):
            return []
        
        return [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(steps)]
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'exponent')  # 'exponent' or 'root'
            
            if calc_type == 'exponent':
                base, error = self._validate_number(data.get('base'), 'Base', allow_zero=True)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                exponent, error = self._validate_number(data.get('exponent'), 'Exponent')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                result, error = self._calculate_exponent(base, exponent)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
            elif calc_type == 'root':
                base, error = self._validate_number(data.get('base'), 'Base', allow_zero=True)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                root_index, error = self._validate_number(data.get('root_index'), 'Root Index', allow_zero=False, allow_negative=False)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                root_index = int(root_index)
                
                result, error = self._calculate_root(base, root_index)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Prepare chart data
            chart_data = {}
            try:
                if calc_type == 'exponent':
                    chart_data = self.prepare_chart_data(base, exponent, result, calc_type)
                elif calc_type == 'root':
                    chart_data = self.prepare_chart_data(base, None, result, calc_type)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare display data
            if calc_type == 'exponent':
                display_data = self.prepare_display_data(base, exponent, result, calc_type)
            else:
                display_data = self.prepare_display_data(base, None, result, calc_type, root_index)
            
            # Prepare step-by-step solution
            if calc_type == 'exponent':
                step_by_step = self.prepare_step_by_step(base, exponent, result, calc_type)
            else:
                step_by_step = self.prepare_step_by_step(base, None, result, calc_type, root_index)
            
            step_by_step_html = self.prepare_step_by_step_html(step_by_step)
            
            # Prepare response
            response = {
                'success': True,
                'calc_type': calc_type,
                'base': base,
                'exponent': exponent if calc_type == 'exponent' else None,
                'root_index': root_index if calc_type == 'root' else None,
                'result': result,
                'chart_data': chart_data,
                'display_data': display_data,
                'step_by_step': step_by_step,
                'step_by_step_html': step_by_step_html
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Exponent Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
