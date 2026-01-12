from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import symbols, solve, simplify, latex
from sympy.abc import x


@method_decorator(ensure_csrf_cookie, name='dispatch')
class QuadraticFormulaCalculator(View):
    """
    Enhanced Professional Quadratic Formula Calculator
    Solves quadratic equations using the quadratic formula with step-by-step solutions.
    """
    template_name = 'math_calculators/quadratic_formula_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Quadratic Formula Calculator',
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
    
    def _solve_quadratic(self, a, b, c):
        """Solve quadratic equation ax² + bx + c = 0"""
        if a == 0:
            return None, "Coefficient 'a' cannot be zero (not a quadratic equation)."
        
        # Calculate discriminant
        discriminant = b**2 - 4*a*c
        
        # Calculate solutions
        if discriminant > 0:
            # Two real solutions
            sqrt_discriminant = math.sqrt(discriminant)
            x1 = (-b + sqrt_discriminant) / (2 * a)
            x2 = (-b - sqrt_discriminant) / (2 * a)
            solution_type = 'two_real'
        elif discriminant == 0:
            # One real solution (repeated root)
            x1 = -b / (2 * a)
            x2 = x1
            solution_type = 'one_real'
        else:
            # Two complex solutions
            sqrt_discriminant = math.sqrt(abs(discriminant))
            real_part = -b / (2 * a)
            imaginary_part = sqrt_discriminant / (2 * a)
            x1 = complex(real_part, imaginary_part)
            x2 = complex(real_part, -imaginary_part)
            solution_type = 'two_complex'
        
        # Calculate vertex
        vertex_x = -b / (2 * a)
        vertex_y = a * vertex_x**2 + b * vertex_x + c
        
        # Axis of symmetry
        axis_of_symmetry = vertex_x
        
        return {
            'x1': x1,
            'x2': x2,
            'discriminant': discriminant,
            'solution_type': solution_type,
            'vertex': (vertex_x, vertex_y),
            'axis_of_symmetry': axis_of_symmetry
        }, None
    
    def _prepare_step_by_step(self, a, b, c, result):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given: {a}x² + {b}x + {c} = 0")
        steps.append("")
        steps.append("Step 1: Identify coefficients")
        steps.append(f"  a = {a}")
        steps.append(f"  b = {b}")
        steps.append(f"  c = {c}")
        steps.append("")
        steps.append("Step 2: Apply the quadratic formula")
        steps.append("  x = (-b ± √(b² - 4ac)) / (2a)")
        steps.append("")
        steps.append("Step 3: Calculate the discriminant")
        steps.append(f"  Δ = b² - 4ac")
        steps.append(f"  Δ = {b}² - 4({a})({c})")
        steps.append(f"  Δ = {b**2} - {4*a*c}")
        discriminant = result['discriminant']
        steps.append(f"  Δ = {discriminant:.6f}")
        steps.append("")
        
        if discriminant > 0:
            steps.append("Step 4: Interpret the discriminant")
            steps.append(f"  Δ = {discriminant:.6f} > 0: Two distinct real solutions")
            steps.append("")
            steps.append("Step 5: Calculate solutions")
            sqrt_discriminant = math.sqrt(discriminant)
            steps.append(f"  x₁ = (-b + √Δ) / (2a)")
            steps.append(f"  x₁ = (-{b} + √{discriminant:.6f}) / (2 × {a})")
            steps.append(f"  x₁ = (-{b} + {sqrt_discriminant:.6f}) / {2*a}")
            steps.append(f"  x₁ = {result['x1']:.6f}")
            steps.append("")
            steps.append(f"  x₂ = (-b - √Δ) / (2a)")
            steps.append(f"  x₂ = (-{b} - √{discriminant:.6f}) / (2 × {a})")
            steps.append(f"  x₂ = (-{b} - {sqrt_discriminant:.6f}) / {2*a}")
            steps.append(f"  x₂ = {result['x2']:.6f}")
        elif discriminant == 0:
            steps.append("Step 4: Interpret the discriminant")
            steps.append(f"  Δ = {discriminant:.6f} = 0: One real solution (repeated root)")
            steps.append("")
            steps.append("Step 5: Calculate solution")
            steps.append(f"  x = -b / (2a)")
            steps.append(f"  x = -{b} / (2 × {a})")
            steps.append(f"  x = {result['x1']:.6f}")
        else:
            steps.append("Step 4: Interpret the discriminant")
            steps.append(f"  Δ = {discriminant:.6f} < 0: Two complex solutions")
            steps.append("")
            steps.append("Step 5: Calculate solutions")
            sqrt_discriminant = math.sqrt(abs(discriminant))
            real_part = -b / (2 * a)
            imaginary_part = sqrt_discriminant / (2 * a)
            steps.append(f"  x₁ = (-b + i√|Δ|) / (2a)")
            steps.append(f"  x₁ = (-{b} + i√{abs(discriminant):.6f}) / (2 × {a})")
            steps.append(f"  x₁ = {real_part:.6f} + {imaginary_part:.6f}i")
            steps.append("")
            steps.append(f"  x₂ = (-b - i√|Δ|) / (2a)")
            steps.append(f"  x₂ = (-{b} - i√{abs(discriminant):.6f}) / (2 × {a})")
            steps.append(f"  x₂ = {real_part:.6f} - {imaginary_part:.6f}i")
        
        steps.append("")
        steps.append("Step 6: Additional information")
        vertex = result['vertex']
        steps.append(f"  Vertex: ({vertex[0]:.6f}, {vertex[1]:.6f})")
        steps.append(f"  Axis of symmetry: x = {result['axis_of_symmetry']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, a, b, c, result):
        """Prepare chart data for parabola visualization"""
        chart_data = {}
        
        try:
            vertex_x = result['axis_of_symmetry']
            
            # Generate x values around the vertex
            if result['solution_type'] == 'two_real':
                # Use solutions as range bounds
                x1 = result['x1']
                x2 = result['x2']
                min_x = min(x1, x2) - 2
                max_x = max(x1, x2) + 2
            else:
                # Use vertex as center
                min_x = vertex_x - 5
                max_x = vertex_x + 5
            
            # Generate points for parabola
            x_values = []
            y_values = []
            num_points = 50
            
            for i in range(num_points + 1):
                x_val = min_x + (max_x - min_x) * i / num_points
                y_val = a * x_val**2 + b * x_val + c
                x_values.append(x_val)
                y_values.append(y_val)
            
            chart_data['parabola_chart'] = {
                'type': 'line',
                'data': {
                    'labels': [f'{x:.2f}' for x in x_values],
                    'datasets': [{
                        'label': f'y = {a}x² + {b}x + {c}',
                        'data': y_values,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4,
                        'pointRadius': 0
                    }]
                }
            }
            
            # Mark roots if real
            if result['solution_type'] in ['two_real', 'one_real']:
                roots_data = []
                roots_labels = []
                if result['solution_type'] == 'two_real':
                    roots_data = [result['x1'], result['x2']]
                    roots_labels = ['x₁', 'x₂']
                else:
                    roots_data = [result['x1']]
                    roots_labels = ['x']
                
                chart_data['roots_markers'] = {
                    'x_values': roots_data,
                    'labels': roots_labels
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
            
            # Get coefficients
            a, error1 = self._validate_number(data.get('a'), 'Coefficient a')
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            b, error2 = self._validate_number(data.get('b'), 'Coefficient b')
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            c, error3 = self._validate_number(data.get('c'), 'Coefficient c')
            if error3:
                return JsonResponse({'success': False, 'error': error3}, status=400)
            
            if a == 0:
                return JsonResponse({'success': False, 'error': "Coefficient 'a' cannot be zero (not a quadratic equation)."}, status=400)
            
            # Solve quadratic equation
            result, error = self._solve_quadratic(a, b, c)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(a, b, c, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(a, b, c, result)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Format solutions for JSON
            def format_complex(z):
                if isinstance(z, complex):
                    if z.imag == 0:
                        return z.real
                    return {'real': z.real, 'imaginary': z.imag}
                return z
            
            response = {
                'success': True,
                'a': a,
                'b': b,
                'c': c,
                'equation': f"{a}x² + {b}x + {c} = 0",
                'x1': format_complex(result['x1']),
                'x2': format_complex(result['x2']),
                'discriminant': result['discriminant'],
                'solution_type': result['solution_type'],
                'vertex': {'x': result['vertex'][0], 'y': result['vertex'][1]},
                'axis_of_symmetry': result['axis_of_symmetry'],
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Quadratic Formula Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
