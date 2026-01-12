from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PermutationAndCombinationCalculator(View):
    """
    Enhanced Professional Permutation and Combination Calculator
    Calculates permutations (P(n,r)) and combinations (C(n,r)) with step-by-step solutions.
    """
    template_name = 'math_calculators/permutation_and_combination_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Permutation And Combination Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_integer(self, value, name, min_value=0):
        """Validate that a value is a non-negative integer"""
        try:
            num = int(float(value))
            if num < min_value:
                return None, f'{name} must be at least {min_value}.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid integer.'
    
    def _factorial(self, n):
        """Calculate factorial using math.factorial"""
        if n < 0:
            return None
        try:
            return math.factorial(n)
        except (ValueError, OverflowError):
            return None
    
    def _calculate_permutation(self, n, r):
        """Calculate permutation P(n,r) = n! / (n-r)!"""
        if r > n:
            return None, "r cannot be greater than n for permutations."
        
        n_factorial = self._factorial(n)
        if n_factorial is None:
            return None, "Factorial calculation failed for n."
        
        n_minus_r_factorial = self._factorial(n - r)
        if n_minus_r_factorial is None:
            return None, "Factorial calculation failed for (n-r)."
        
        result = n_factorial // n_minus_r_factorial
        return result, None
    
    def _calculate_combination(self, n, r):
        """Calculate combination C(n,r) = n! / (r! × (n-r)!)"""
        if r > n:
            return None, "r cannot be greater than n for combinations."
        
        n_factorial = self._factorial(n)
        if n_factorial is None:
            return None, "Factorial calculation failed for n."
        
        r_factorial = self._factorial(r)
        if r_factorial is None:
            return None, "Factorial calculation failed for r."
        
        n_minus_r_factorial = self._factorial(n - r)
        if n_minus_r_factorial is None:
            return None, "Factorial calculation failed for (n-r)."
        
        result = n_factorial // (r_factorial * n_minus_r_factorial)
        return result, None
    
    def _prepare_step_by_step_permutation(self, n, r, result):
        """Prepare step-by-step solution for permutation"""
        steps = []
        
        steps.append(f"Given: P({n}, {r})")
        steps.append(f"  n = {n} (total items)")
        steps.append(f"  r = {r} (items to arrange)")
        steps.append("")
        steps.append("Step 1: Understand the formula")
        steps.append("  P(n, r) = n! / (n - r)!")
        steps.append("  This gives the number of ways to arrange r items from n items")
        steps.append("  where order matters.")
        steps.append("")
        steps.append("Step 2: Calculate factorials")
        n_factorial = self._factorial(n)
        n_minus_r = n - r
        n_minus_r_factorial = self._factorial(n_minus_r)
        
        steps.append(f"  n! = {n}! = {n_factorial:,}")
        steps.append(f"  (n - r)! = ({n} - {r})! = {n_minus_r}! = {n_minus_r_factorial:,}")
        steps.append("")
        steps.append("Step 3: Apply the formula")
        steps.append(f"  P({n}, {r}) = {n_factorial:,} / {n_minus_r_factorial:,}")
        steps.append(f"  P({n}, {r}) = {result:,}")
        steps.append("")
        steps.append("Step 4: Interpretation")
        steps.append(f"  There are {result:,} ways to arrange {r} items from {n} items")
        steps.append(f"  where the order matters.")
        
        return steps
    
    def _prepare_step_by_step_combination(self, n, r, result):
        """Prepare step-by-step solution for combination"""
        steps = []
        
        steps.append(f"Given: C({n}, {r})")
        steps.append(f"  n = {n} (total items)")
        steps.append(f"  r = {r} (items to select)")
        steps.append("")
        steps.append("Step 1: Understand the formula")
        steps.append("  C(n, r) = n! / (r! × (n - r)!)")
        steps.append("  This gives the number of ways to select r items from n items")
        steps.append("  where order does not matter.")
        steps.append("")
        steps.append("Step 2: Calculate factorials")
        n_factorial = self._factorial(n)
        r_factorial = self._factorial(r)
        n_minus_r = n - r
        n_minus_r_factorial = self._factorial(n_minus_r)
        
        steps.append(f"  n! = {n}! = {n_factorial:,}")
        steps.append(f"  r! = {r}! = {r_factorial:,}")
        steps.append(f"  (n - r)! = ({n} - {r})! = {n_minus_r}! = {n_minus_r_factorial:,}")
        steps.append("")
        steps.append("Step 3: Apply the formula")
        denominator = r_factorial * n_minus_r_factorial
        steps.append(f"  C({n}, {r}) = {n_factorial:,} / ({r_factorial:,} × {n_minus_r_factorial:,})")
        steps.append(f"  C({n}, {r}) = {n_factorial:,} / {denominator:,}")
        steps.append(f"  C({n}, {r}) = {result:,}")
        steps.append("")
        steps.append("Step 4: Interpretation")
        steps.append(f"  There are {result:,} ways to select {r} items from {n} items")
        steps.append(f"  where the order does not matter.")
        
        return steps
    
    def _prepare_chart_data(self, calc_type, n, r, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if calc_type == 'permutation':
                # Show factorial values
                n_factorial = self._factorial(n)
                n_minus_r_factorial = self._factorial(n - r)
                
                chart_data['factorial_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': [f'{n}!', f'({n}-{r})!'],
                        'datasets': [{
                            'label': 'Factorial Value',
                            'data': [min(n_factorial, 1e10), min(n_minus_r_factorial, 1e10)],
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
            
            elif calc_type == 'combination':
                # Show factorial values
                n_factorial = self._factorial(n)
                r_factorial = self._factorial(r)
                n_minus_r_factorial = self._factorial(n - r)
                
                chart_data['factorial_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': [f'{n}!', f'{r}!', f'({n}-{r})!'],
                        'datasets': [{
                            'label': 'Factorial Value',
                            'data': [
                                min(n_factorial, 1e10),
                                min(r_factorial, 1e10),
                                min(n_minus_r_factorial, 1e10)
                            ],
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
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'permutation')
            
            # Get n and r
            n, error1 = self._validate_integer(data.get('n'), 'n', min_value=0)
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            r, error2 = self._validate_integer(data.get('r'), 'r', min_value=0)
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            if calc_type == 'permutation':
                result, error = self._calculate_permutation(n, r)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step_permutation(n, r, result)
                chart_data = self._prepare_chart_data('permutation', n, r, result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'n': n,
                    'r': r,
                    'result': result,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'combination':
                result, error = self._calculate_combination(n, r)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step_combination(n, r, result)
                chart_data = self._prepare_chart_data('combination', n, r, result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'n': n,
                    'r': r,
                    'result': result,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Permutation and Combination Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
