from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ScientificCalculator(View):
    """
    Enhanced Professional Scientific Calculator
    Evaluates mathematical expressions with scientific functions and step-by-step solutions.
    """
    template_name = 'math_calculators/scientific_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Scientific Calculator',
        }
        return render(request, self.template_name, context)
    
    def _safe_eval(self, expression):
        """Safely evaluate mathematical expression"""
        # Replace common functions and constants
        expression = expression.replace('π', str(math.pi))
        expression = expression.replace('pi', str(math.pi))
        expression = expression.replace('e', str(math.e))
        expression = expression.replace('E', str(math.e))
        
        # Replace function names with math module equivalents
        replacements = {
            'sin': 'math.sin',
            'cos': 'math.cos',
            'tan': 'math.tan',
            'asin': 'math.asin',
            'acos': 'math.acos',
            'atan': 'math.atan',
            'sinh': 'math.sinh',
            'cosh': 'math.cosh',
            'tanh': 'math.tanh',
            'log': 'math.log10',
            'ln': 'math.log',
            'exp': 'math.exp',
            'sqrt': 'math.sqrt',
            'cbrt': 'lambda x: x**(1/3)',
            'abs': 'abs',
            'floor': 'math.floor',
            'ceil': 'math.ceil',
            'round': 'round',
            'pow': 'pow',
            '^': '**'
        }
        
        # Replace functions (handle function calls)
        for old, new in replacements.items():
            if old == '^':
                expression = expression.replace('^', '**')
            else:
                # Replace function calls like sin(, cos(, etc.
                pattern = r'\b' + re.escape(old) + r'\s*\('
                if old in ['abs', 'round']:
                    expression = re.sub(pattern, new + '(', expression)
                elif old == 'cbrt':
                    # Handle cube root specially
                    pattern = r'cbrt\s*\(([^)]+)\)'
                    expression = re.sub(pattern, r'(\1)**(1/3)', expression)
                else:
                    expression = re.sub(pattern, new + '(', expression)
        
        # Only allow safe characters
        allowed_chars = set('0123456789+-*/.()abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_., ')
        if not all(c in allowed_chars or c in 'math.' for c in expression):
            return None, "Invalid characters in expression."
        
        try:
            result = eval(expression, {"__builtins__": {}}, {"math": math, "abs": abs, "round": round, "pow": pow})
            if math.isnan(result) or math.isinf(result):
                return None, "Result is not a valid number."
            return result, None
        except Exception as e:
            return None, f"Error evaluating expression: {str(e)}"
    
    def _prepare_step_by_step(self, expression, result):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given Expression: {expression}")
        steps.append("")
        
        # Replace constants for display
        display_expr = expression.replace('π', 'π').replace('pi', 'π').replace('e', 'e')
        steps.append("Step 1: Replace constants")
        if 'π' in display_expr or 'pi' in display_expr:
            steps.append(f"  π = {math.pi:.10f}")
        if 'e' in display_expr:
            steps.append(f"  e = {math.e:.10f}")
        steps.append("")
        
        steps.append("Step 2: Evaluate expression")
        steps.append(f"  {display_expr}")
        steps.append("")
        
        steps.append("Step 3: Result")
        steps.append(f"  = {result:.10f}")
        
        # Format result
        if abs(result) < 1e-10:
            steps.append(f"  = 0")
        elif abs(result - int(result)) < 1e-10:
            steps.append(f"  = {int(result)}")
        else:
            steps.append(f"  ≈ {result:.6f}")
        
        return steps
    
    def _prepare_calculation_history(self, expression, result):
        """Prepare calculation history entry"""
        return {
            'expression': expression,
            'result': result,
            'formatted_result': f"{result:.10f}" if abs(result - int(result)) > 1e-10 else str(int(result))
        }
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            expression = data.get('expression', '').strip()
            
            if not expression:
                return JsonResponse({'success': False, 'error': 'Please enter an expression.'}, status=400)
            
            # Evaluate expression
            result, error = self._safe_eval(expression)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(expression, result)
            
            # Prepare calculation history
            history_entry = self._prepare_calculation_history(expression, result)
            
            response = {
                'success': True,
                'expression': expression,
                'result': result,
                'step_by_step': step_by_step,
                'history_entry': history_entry
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Scientific Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
