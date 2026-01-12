from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HalfLifeCalculator(View):
    """
    Enhanced Professional Half-Life Calculator
    Calculates half-life, decay constant, remaining amount, and time elapsed.
    """
    template_name = 'math_calculators/half_life_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Half-Life Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num < 0:
                return None, f'{name} must be greater than or equal to zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_decay_constant(self, half_life):
        """Calculate decay constant from half-life"""
        if half_life <= 0:
            return None
        return math.log(2) / half_life
    
    def _calculate_half_life(self, decay_constant):
        """Calculate half-life from decay constant"""
        if decay_constant <= 0:
            return None
        return math.log(2) / decay_constant
    
    def _calculate_remaining_amount(self, initial_amount, half_life, time_elapsed):
        """Calculate remaining amount after time elapsed"""
        if half_life <= 0 or time_elapsed < 0:
            return None
        decay_constant = self._calculate_decay_constant(half_life)
        return initial_amount * math.exp(-decay_constant * time_elapsed)
    
    def _calculate_time_elapsed(self, initial_amount, remaining_amount, half_life):
        """Calculate time elapsed given initial and remaining amounts"""
        if half_life <= 0 or initial_amount <= 0 or remaining_amount < 0:
            return None
        if remaining_amount >= initial_amount:
            return 0
        decay_constant = self._calculate_decay_constant(half_life)
        return -math.log(remaining_amount / initial_amount) / decay_constant
    
    def _calculate_initial_amount(self, remaining_amount, half_life, time_elapsed):
        """Calculate initial amount given remaining amount and time"""
        if half_life <= 0 or time_elapsed < 0 or remaining_amount < 0:
            return None
        decay_constant = self._calculate_decay_constant(half_life)
        return remaining_amount / math.exp(-decay_constant * time_elapsed)
    
    def _prepare_step_by_step(self, calc_type, initial_amount, remaining_amount, half_life, time_elapsed, decay_constant, result):
        """Prepare step-by-step solution"""
        steps = []
        
        if calc_type == 'remaining':
            steps.append(f"Given:")
            steps.append(f"  Initial Amount (N₀) = {initial_amount}")
            steps.append(f"  Half-Life (t₁/₂) = {half_life}")
            steps.append(f"  Time Elapsed (t) = {time_elapsed}")
            steps.append("")
            steps.append("Step 1: Calculate decay constant (λ)")
            steps.append(f"  λ = ln(2) / t₁/₂")
            steps.append(f"  λ = {math.log(2):.6f} / {half_life}")
            steps.append(f"  λ = {decay_constant:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate remaining amount (N)")
            steps.append(f"  N = N₀ × e^(-λt)")
            steps.append(f"  N = {initial_amount} × e^(-{decay_constant:.6f} × {time_elapsed})")
            steps.append(f"  N = {initial_amount} × e^(-{decay_constant * time_elapsed:.6f})")
            steps.append(f"  N = {initial_amount} × {math.exp(-decay_constant * time_elapsed):.6f}")
            steps.append(f"  N = {result:.6f}")
            steps.append("")
            steps.append(f"Step 3: Result")
            steps.append(f"  Remaining Amount = {result:.6f}")
            steps.append(f"  Percentage Remaining = {(result/initial_amount)*100:.2f}%")
            
        elif calc_type == 'time':
            steps.append(f"Given:")
            steps.append(f"  Initial Amount (N₀) = {initial_amount}")
            steps.append(f"  Remaining Amount (N) = {remaining_amount}")
            steps.append(f"  Half-Life (t₁/₂) = {half_life}")
            steps.append("")
            steps.append("Step 1: Calculate decay constant (λ)")
            steps.append(f"  λ = ln(2) / t₁/₂")
            steps.append(f"  λ = {math.log(2):.6f} / {half_life}")
            steps.append(f"  λ = {decay_constant:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate time elapsed (t)")
            steps.append(f"  N = N₀ × e^(-λt)")
            steps.append(f"  {remaining_amount} = {initial_amount} × e^(-{decay_constant:.6f} × t)")
            steps.append(f"  {remaining_amount/initial_amount:.6f} = e^(-{decay_constant:.6f} × t)")
            steps.append(f"  ln({remaining_amount/initial_amount:.6f}) = -{decay_constant:.6f} × t")
            steps.append(f"  t = -ln({remaining_amount/initial_amount:.6f}) / {decay_constant:.6f}")
            steps.append(f"  t = {result:.6f}")
            steps.append("")
            steps.append(f"Step 3: Result")
            steps.append(f"  Time Elapsed = {result:.6f}")
            steps.append(f"  Number of Half-Lives = {result / half_life:.4f}")
            
        elif calc_type == 'initial':
            steps.append(f"Given:")
            steps.append(f"  Remaining Amount (N) = {remaining_amount}")
            steps.append(f"  Half-Life (t₁/₂) = {half_life}")
            steps.append(f"  Time Elapsed (t) = {time_elapsed}")
            steps.append("")
            steps.append("Step 1: Calculate decay constant (λ)")
            steps.append(f"  λ = ln(2) / t₁/₂")
            steps.append(f"  λ = {math.log(2):.6f} / {half_life}")
            steps.append(f"  λ = {decay_constant:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate initial amount (N₀)")
            steps.append(f"  N = N₀ × e^(-λt)")
            steps.append(f"  {remaining_amount} = N₀ × e^(-{decay_constant:.6f} × {time_elapsed})")
            steps.append(f"  {remaining_amount} = N₀ × e^(-{decay_constant * time_elapsed:.6f})")
            steps.append(f"  {remaining_amount} = N₀ × {math.exp(-decay_constant * time_elapsed):.6f}")
            steps.append(f"  N₀ = {remaining_amount} / {math.exp(-decay_constant * time_elapsed):.6f}")
            steps.append(f"  N₀ = {result:.6f}")
            steps.append("")
            steps.append(f"Step 3: Result")
            steps.append(f"  Initial Amount = {result:.6f}")
            
        elif calc_type == 'half_life':
            steps.append(f"Given:")
            steps.append(f"  Initial Amount (N₀) = {initial_amount}")
            steps.append(f"  Remaining Amount (N) = {remaining_amount}")
            steps.append(f"  Time Elapsed (t) = {time_elapsed}")
            steps.append("")
            steps.append("Step 1: Calculate decay constant (λ)")
            steps.append(f"  N = N₀ × e^(-λt)")
            steps.append(f"  {remaining_amount} = {initial_amount} × e^(-λ × {time_elapsed})")
            steps.append(f"  {remaining_amount/initial_amount:.6f} = e^(-λ × {time_elapsed})")
            steps.append(f"  ln({remaining_amount/initial_amount:.6f}) = -λ × {time_elapsed}")
            steps.append(f"  λ = -ln({remaining_amount/initial_amount:.6f}) / {time_elapsed}")
            steps.append(f"  λ = {decay_constant:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate half-life (t₁/₂)")
            steps.append(f"  t₁/₂ = ln(2) / λ")
            steps.append(f"  t₁/₂ = {math.log(2):.6f} / {decay_constant:.6f}")
            steps.append(f"  t₁/₂ = {result:.6f}")
            steps.append("")
            steps.append(f"Step 3: Result")
            steps.append(f"  Half-Life = {result:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, initial_amount, half_life, decay_constant, time_points=None):
        """Prepare chart data for decay visualization"""
        if time_points is None:
            # Generate time points up to 5 half-lives
            max_time = half_life * 5
            time_points = [i * max_time / 50 for i in range(51)]
        
        amounts = []
        percentages = []
        
        for t in time_points:
            amount = initial_amount * math.exp(-decay_constant * t)
            amounts.append(amount)
            percentages.append((amount / initial_amount) * 100)
        
        chart_data = {
            'decay_curve': {
                'type': 'line',
                'data': {
                    'labels': [f'{t:.2f}' for t in time_points],
                    'datasets': [
                        {
                            'label': 'Remaining Amount',
                            'data': amounts,
                            'borderColor': '#3b82f6',
                            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                            'borderWidth': 2,
                            'fill': True,
                            'tension': 0.4
                        },
                        {
                            'label': 'Percentage Remaining',
                            'data': percentages,
                            'borderColor': '#10b981',
                            'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                            'borderWidth': 2,
                            'fill': False,
                            'tension': 0.4,
                            'yAxisID': 'y1'
                        }
                    ]
                }
            }
        }
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'remaining')
            
            # Get and validate inputs
            initial_amount = data.get('initial_amount')
            remaining_amount = data.get('remaining_amount')
            half_life = data.get('half_life')
            time_elapsed = data.get('time_elapsed')
            decay_constant = None
            
            # Validate based on calculation type
            if calc_type == 'remaining':
                # Need: initial_amount, half_life, time_elapsed
                initial_amount, error = self._validate_positive_number(initial_amount, 'Initial Amount')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                half_life, error = self._validate_positive_number(half_life, 'Half-Life')
                if error or half_life == 0:
                    return JsonResponse({'success': False, 'error': 'Half-life must be greater than zero.'}, status=400)
                
                time_elapsed, error = self._validate_positive_number(time_elapsed, 'Time Elapsed')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                decay_constant = self._calculate_decay_constant(half_life)
                result = self._calculate_remaining_amount(initial_amount, half_life, time_elapsed)
                
            elif calc_type == 'time':
                # Need: initial_amount, remaining_amount, half_life
                initial_amount, error = self._validate_positive_number(initial_amount, 'Initial Amount')
                if error or initial_amount == 0:
                    return JsonResponse({'success': False, 'error': 'Initial amount must be greater than zero.'}, status=400)
                
                remaining_amount, error = self._validate_positive_number(remaining_amount, 'Remaining Amount')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                if remaining_amount > initial_amount:
                    return JsonResponse({'success': False, 'error': 'Remaining amount cannot be greater than initial amount.'}, status=400)
                
                half_life, error = self._validate_positive_number(half_life, 'Half-Life')
                if error or half_life == 0:
                    return JsonResponse({'success': False, 'error': 'Half-life must be greater than zero.'}, status=400)
                
                decay_constant = self._calculate_decay_constant(half_life)
                result = self._calculate_time_elapsed(initial_amount, remaining_amount, half_life)
                
            elif calc_type == 'initial':
                # Need: remaining_amount, half_life, time_elapsed
                remaining_amount, error = self._validate_positive_number(remaining_amount, 'Remaining Amount')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                half_life, error = self._validate_positive_number(half_life, 'Half-Life')
                if error or half_life == 0:
                    return JsonResponse({'success': False, 'error': 'Half-life must be greater than zero.'}, status=400)
                
                time_elapsed, error = self._validate_positive_number(time_elapsed, 'Time Elapsed')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                decay_constant = self._calculate_decay_constant(half_life)
                result = self._calculate_initial_amount(remaining_amount, half_life, time_elapsed)
                initial_amount = result
                
            elif calc_type == 'half_life':
                # Need: initial_amount, remaining_amount, time_elapsed
                initial_amount, error = self._validate_positive_number(initial_amount, 'Initial Amount')
                if error or initial_amount == 0:
                    return JsonResponse({'success': False, 'error': 'Initial amount must be greater than zero.'}, status=400)
                
                remaining_amount, error = self._validate_positive_number(remaining_amount, 'Remaining Amount')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                if remaining_amount > initial_amount:
                    return JsonResponse({'success': False, 'error': 'Remaining amount cannot be greater than initial amount.'}, status=400)
                
                time_elapsed, error = self._validate_positive_number(time_elapsed, 'Time Elapsed')
                if error or time_elapsed == 0:
                    return JsonResponse({'success': False, 'error': 'Time elapsed must be greater than zero.'}, status=400)
                
                # Calculate decay constant first
                decay_constant = -math.log(remaining_amount / initial_amount) / time_elapsed
                result = self._calculate_half_life(decay_constant)
                half_life = result
                
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            if result is None:
                return JsonResponse({'success': False, 'error': 'Invalid calculation. Please check your inputs.'}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(
                calc_type, initial_amount, remaining_amount, half_life, 
                time_elapsed, decay_constant, result
            )
            
            # Prepare chart data
            chart_data = {}
            try:
                if calc_type in ['remaining', 'initial']:
                    chart_data = self._prepare_chart_data(initial_amount, half_life, decay_constant)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Calculate additional metrics
            percentage_remaining = None
            number_of_half_lives = None
            
            if calc_type == 'remaining':
                percentage_remaining = (result / initial_amount) * 100
                number_of_half_lives = time_elapsed / half_life
            elif calc_type == 'time':
                percentage_remaining = (remaining_amount / initial_amount) * 100
                number_of_half_lives = result / half_life
            
            response = {
                'success': True,
                'calc_type': calc_type,
                'initial_amount': initial_amount,
                'remaining_amount': remaining_amount if calc_type != 'initial' else remaining_amount,
                'half_life': half_life,
                'time_elapsed': time_elapsed if calc_type != 'time' else result,
                'decay_constant': decay_constant,
                'result': result,
                'percentage_remaining': percentage_remaining,
                'number_of_half_lives': number_of_half_lives,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Half-Life Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
