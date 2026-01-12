from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PythagoreanTheoremCalculator(View):
    """
    Enhanced Professional Pythagorean Theorem Calculator
    Calculates missing side of a right triangle using a² + b² = c² with step-by-step solutions.
    """
    template_name = 'math_calculators/pythagorean_theorem_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Pythagorean Theorem Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0:
                return None, f'{name} must be greater than zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_missing_side(self, calc_type, a=None, b=None, c=None):
        """Calculate missing side of right triangle"""
        if calc_type == 'find_c':
            # Find hypotenuse: c = √(a² + b²)
            if a is None or b is None:
                return None, "Both a and b are required to find c."
            result = math.sqrt(a**2 + b**2)
            return {
                'result': result,
                'a': a,
                'b': b,
                'c': result,
                'calc_type': 'find_c'
            }, None
        
        elif calc_type == 'find_a':
            # Find leg a: a = √(c² - b²)
            if c is None or b is None:
                return None, "Both c and b are required to find a."
            if c <= b:
                return None, "c must be greater than b (hypotenuse must be longest side)."
            result = math.sqrt(c**2 - b**2)
            return {
                'result': result,
                'a': result,
                'b': b,
                'c': c,
                'calc_type': 'find_a'
            }, None
        
        elif calc_type == 'find_b':
            # Find leg b: b = √(c² - a²)
            if c is None or a is None:
                return None, "Both c and a are required to find b."
            if c <= a:
                return None, "c must be greater than a (hypotenuse must be longest side)."
            result = math.sqrt(c**2 - a**2)
            return {
                'result': result,
                'a': a,
                'b': result,
                'c': c,
                'calc_type': 'find_b'
            }, None
        
        else:
            return None, "Invalid calculation type."
    
    def _prepare_step_by_step(self, result):
        """Prepare step-by-step solution"""
        steps = []
        calc_type = result['calc_type']
        a = result['a']
        b = result['b']
        c = result['c']
        
        steps.append("Given: Right triangle with sides a, b, and c (where c is the hypotenuse)")
        steps.append(f"  a = {a:.6f}")
        steps.append(f"  b = {b:.6f}")
        steps.append(f"  c = {c:.6f}")
        steps.append("")
        
        if calc_type == 'find_c':
            steps.append("Step 1: Apply the Pythagorean Theorem")
            steps.append("  Formula: a² + b² = c²")
            steps.append("  To find c: c = √(a² + b²)")
            steps.append("")
            steps.append("Step 2: Calculate squares")
            steps.append(f"  a² = {a:.6f}² = {a**2:.6f}")
            steps.append(f"  b² = {b:.6f}² = {b**2:.6f}")
            steps.append("")
            steps.append("Step 3: Add the squares")
            steps.append(f"  a² + b² = {a**2:.6f} + {b**2:.6f} = {a**2 + b**2:.6f}")
            steps.append("")
            steps.append("Step 4: Take the square root")
            steps.append(f"  c = √{a**2 + b**2:.6f} = {c:.6f}")
            steps.append("")
            steps.append("Step 5: Verification")
            steps.append(f"  a² + b² = {a**2:.6f} + {b**2:.6f} = {a**2 + b**2:.6f}")
            steps.append(f"  c² = {c:.6f}² = {c**2:.6f}")
            if abs((a**2 + b**2) - c**2) < 0.0001:
                steps.append(f"  ✓ Verification successful! a² + b² = c²")
        
        elif calc_type == 'find_a':
            steps.append("Step 1: Apply the Pythagorean Theorem")
            steps.append("  Formula: a² + b² = c²")
            steps.append("  To find a: a = √(c² - b²)")
            steps.append("")
            steps.append("Step 2: Calculate squares")
            steps.append(f"  c² = {c:.6f}² = {c**2:.6f}")
            steps.append(f"  b² = {b:.6f}² = {b**2:.6f}")
            steps.append("")
            steps.append("Step 3: Subtract b² from c²")
            steps.append(f"  c² - b² = {c**2:.6f} - {b**2:.6f} = {c**2 - b**2:.6f}")
            steps.append("")
            steps.append("Step 4: Take the square root")
            steps.append(f"  a = √{c**2 - b**2:.6f} = {a:.6f}")
            steps.append("")
            steps.append("Step 5: Verification")
            steps.append(f"  a² + b² = {a**2:.6f} + {b**2:.6f} = {a**2 + b**2:.6f}")
            steps.append(f"  c² = {c:.6f}² = {c**2:.6f}")
            if abs((a**2 + b**2) - c**2) < 0.0001:
                steps.append(f"  ✓ Verification successful! a² + b² = c²")
        
        elif calc_type == 'find_b':
            steps.append("Step 1: Apply the Pythagorean Theorem")
            steps.append("  Formula: a² + b² = c²")
            steps.append("  To find b: b = √(c² - a²)")
            steps.append("")
            steps.append("Step 2: Calculate squares")
            steps.append(f"  c² = {c:.6f}² = {c**2:.6f}")
            steps.append(f"  a² = {a:.6f}² = {a**2:.6f}")
            steps.append("")
            steps.append("Step 3: Subtract a² from c²")
            steps.append(f"  c² - a² = {c**2:.6f} - {a**2:.6f} = {c**2 - a**2:.6f}")
            steps.append("")
            steps.append("Step 4: Take the square root")
            steps.append(f"  b = √{c**2 - a**2:.6f} = {b:.6f}")
            steps.append("")
            steps.append("Step 5: Verification")
            steps.append(f"  a² + b² = {a**2:.6f} + {b**2:.6f} = {a**2 + b**2:.6f}")
            steps.append(f"  c² = {c:.6f}² = {c**2:.6f}")
            if abs((a**2 + b**2) - c**2) < 0.0001:
                steps.append(f"  ✓ Verification successful! a² + b² = c²")
        
        return steps
    
    def _prepare_chart_data(self, a, b, c):
        """Prepare chart data for triangle visualization"""
        chart_data = {}
        
        try:
            # Triangle side comparison
            chart_data['triangle_sides_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Side a', 'Side b', 'Hypotenuse c'],
                    'datasets': [{
                        'label': 'Length',
                        'data': [a, b, c],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(139, 92, 246, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#8b5cf6'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            # Squares comparison
            chart_data['squares_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['a²', 'b²', 'a² + b²', 'c²'],
                    'datasets': [{
                        'label': 'Value',
                        'data': [a**2, b**2, a**2 + b**2, c**2],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(139, 92, 246, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#8b5cf6'
                        ],
                        'borderWidth': 2
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
            
            calc_type = data.get('calc_type', 'find_c')
            
            # Get inputs based on calculation type
            a = None
            b = None
            c = None
            
            if calc_type == 'find_c':
                a, error1 = self._validate_positive_number(data.get('a'), 'Side a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                b, error2 = self._validate_positive_number(data.get('b'), 'Side b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            elif calc_type == 'find_a':
                b, error1 = self._validate_positive_number(data.get('b'), 'Side b')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                c, error2 = self._validate_positive_number(data.get('c'), 'Hypotenuse c')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            elif calc_type == 'find_b':
                a, error1 = self._validate_positive_number(data.get('a'), 'Side a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                c, error2 = self._validate_positive_number(data.get('c'), 'Hypotenuse c')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Calculate missing side
            result, error = self._calculate_missing_side(calc_type, a, b, c)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(result['a'], result['b'], result['c'])
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                'calc_type': calc_type,
                'a': result['a'],
                'b': result['b'],
                'c': result['c'],
                'result': result['result'],
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Pythagorean Theorem Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
