from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LogCalculator(View):
    """
    Enhanced Professional Logarithm Calculator
    Calculates logarithms with different bases, antilogarithms, and provides step-by-step solutions.
    """
    template_name = 'math_calculators/log_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Log Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name, allow_zero=False):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num <= 0:
                return None, f'{name} must be greater than zero.'
            if allow_zero and num < 0:
                return None, f'{name} must be greater than or equal to zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_log(self, number, base):
        """Calculate logarithm"""
        try:
            if base == 'e' or base == math.e:
                return math.log(number)
            elif base == 10:
                return math.log10(number)
            else:
                return math.log(number, base)
        except:
            return None
    
    def _calculate_antilog(self, log_value, base):
        """Calculate antilogarithm (exponentiation)"""
        try:
            if base == 'e' or base == math.e:
                return math.exp(log_value)
            elif base == 10:
                return 10 ** log_value
            else:
                return base ** log_value
        except:
            return None
    
    def _prepare_step_by_step_log(self, number, base, result):
        """Prepare step-by-step solution for logarithm"""
        steps = []
        
        if base == 'e' or base == math.e:
            steps.append(f"Given: ln({number})")
            steps.append("")
            steps.append("Step 1: Natural Logarithm")
            steps.append(f"  ln({number}) = log_e({number})")
            steps.append(f"  This is the power to which e (≈2.71828) must be raised to get {number}")
            steps.append("")
            steps.append("Step 2: Calculation")
            steps.append(f"  ln({number}) = {result:.6f}")
            steps.append("")
            steps.append("Step 3: Verification")
            steps.append(f"  e^{result:.6f} ≈ {math.exp(result):.6f}")
            if abs(math.exp(result) - number) < 0.0001:
                steps.append(f"  ✓ Verification successful!")
        elif base == 10:
            steps.append(f"Given: log₁₀({number})")
            steps.append("")
            steps.append("Step 1: Common Logarithm")
            steps.append(f"  log₁₀({number}) = log({number})")
            steps.append(f"  This is the power to which 10 must be raised to get {number}")
            steps.append("")
            steps.append("Step 2: Calculation")
            steps.append(f"  log₁₀({number}) = {result:.6f}")
            steps.append("")
            steps.append("Step 3: Verification")
            steps.append(f"  10^{result:.6f} ≈ {10**result:.6f}")
            if abs(10**result - number) < 0.0001:
                steps.append(f"  ✓ Verification successful!")
        else:
            steps.append(f"Given: log_{base}({number})")
            steps.append("")
            steps.append(f"Step 1: Logarithm with base {base}")
            steps.append(f"  log_{base}({number}) = ?")
            steps.append(f"  This is the power to which {base} must be raised to get {number}")
            steps.append("")
            steps.append("Step 2: Calculation")
            steps.append(f"  log_{base}({number}) = {result:.6f}")
            steps.append("")
            steps.append("Step 3: Verification")
            steps.append(f"  {base}^{result:.6f} ≈ {base**result:.6f}")
            if abs(base**result - number) < 0.0001:
                steps.append(f"  ✓ Verification successful!")
        
        return steps
    
    def _prepare_step_by_step_antilog(self, log_value, base, result):
        """Prepare step-by-step solution for antilogarithm"""
        steps = []
        
        if base == 'e' or base == math.e:
            steps.append(f"Given: antilog_e({log_value}) or e^{log_value}")
            steps.append("")
            steps.append("Step 1: Natural Antilogarithm")
            steps.append(f"  e^{log_value} = ?")
            steps.append("")
            steps.append("Step 2: Calculation")
            steps.append(f"  e^{log_value} = {result:.6f}")
        elif base == 10:
            steps.append(f"Given: antilog₁₀({log_value}) or 10^{log_value}")
            steps.append("")
            steps.append("Step 1: Common Antilogarithm")
            steps.append(f"  10^{log_value} = ?")
            steps.append("")
            steps.append("Step 2: Calculation")
            steps.append(f"  10^{log_value} = {result:.6f}")
        else:
            steps.append(f"Given: antilog_{base}({log_value}) or {base}^{log_value}")
            steps.append("")
            steps.append(f"Step 1: Antilogarithm with base {base}")
            steps.append(f"  {base}^{log_value} = ?")
            steps.append("")
            steps.append("Step 2: Calculation")
            steps.append(f"  {base}^{log_value} = {result:.6f}")
        
        steps.append("")
        steps.append("Step 3: Verification")
        if base == 'e' or base == math.e:
            verification = math.log(result)
        elif base == 10:
            verification = math.log10(result)
        else:
            verification = math.log(result, base)
        steps.append(f"  log_{base if base != 'e' else 'e'}({result:.6f}) = {verification:.6f}")
        if abs(verification - log_value) < 0.0001:
            steps.append(f"  ✓ Verification successful!")
        
        return steps
    
    def _prepare_chart_data(self, calc_type, number, base, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        if calc_type == 'log':
            # Logarithm curve
            try:
                if number > 0 and number <= 100:
                    x_values = [i * number / 50 for i in range(1, 51)]
                    y_values = []
                    for x in x_values:
                        if x > 0:
                            if base == 'e' or base == math.e:
                                y_values.append(math.log(x))
                            elif base == 10:
                                y_values.append(math.log10(x))
                            else:
                                y_values.append(math.log(x, base))
                        else:
                            y_values.append(None)
                    
                    chart_data['log_curve'] = {
                        'type': 'line',
                        'data': {
                            'labels': [f'{x:.2f}' for x in x_values],
                            'datasets': [{
                                'label': f'log_{base if base != "e" else "e"}(x)',
                                'data': y_values,
                                'borderColor': '#3b82f6',
                                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                                'borderWidth': 2,
                                'fill': True,
                                'tension': 0.4
                            }]
                        }
                    }
            except:
                pass
        
        elif calc_type == 'antilog':
            # Exponential curve
            try:
                if abs(log_value := number) <= 5:
                    x_values = [i * 10 / 50 - 5 for i in range(51)]
                    y_values = []
                    for x in x_values:
                        if base == 'e' or base == math.e:
                            y_values.append(math.exp(x))
                        elif base == 10:
                            y_values.append(10 ** x)
                        else:
                            y_values.append(base ** x)
                    
                    chart_data['exp_curve'] = {
                        'type': 'line',
                        'data': {
                            'labels': [f'{x:.2f}' for x in x_values],
                            'datasets': [{
                                'label': f'{base if base != "e" else "e"}^x',
                                'data': y_values,
                                'borderColor': '#10b981',
                                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                                'borderWidth': 2,
                                'fill': True,
                                'tension': 0.4
                            }]
                        }
                    }
            except:
                pass
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'log')
            
            if calc_type == 'log':
                # Logarithm calculation
                number, error = self._validate_positive_number(data.get('number'), 'Number')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                base_input = data.get('base', '10')
                if base_input == 'e' or base_input == 'E':
                    base = 'e'
                else:
                    base, error = self._validate_positive_number(base_input, 'Base')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                result = self._calculate_log(number, base)
                if result is None:
                    return JsonResponse({'success': False, 'error': 'Invalid logarithm calculation.'}, status=400)
                
                # Prepare step-by-step
                step_by_step = self._prepare_step_by_step_log(number, base, result)
                
                # Prepare chart data
                chart_data = {}
                try:
                    chart_data = self._prepare_chart_data('log', number, base, result)
                except Exception as e:
                    import traceback
                    print(f"Chart data preparation error: {traceback.format_exc()}")
                    chart_data = {}
                
                response = {
                    'success': True,
                    'calc_type': 'log',
                    'number': number,
                    'base': base if base != 'e' else 'e',
                    'result': result,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
                
            elif calc_type == 'antilog':
                # Antilogarithm calculation
                log_value = data.get('log_value')
                try:
                    log_value = float(log_value)
                    if math.isnan(log_value) or math.isinf(log_value):
                        return JsonResponse({'success': False, 'error': 'Log value must be a valid number.'}, status=400)
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': 'Log value must be a valid number.'}, status=400)
                
                base_input = data.get('base', '10')
                if base_input == 'e' or base_input == 'E':
                    base = 'e'
                else:
                    base, error = self._validate_positive_number(base_input, 'Base')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                result = self._calculate_antilog(log_value, base)
                if result is None:
                    return JsonResponse({'success': False, 'error': 'Invalid antilogarithm calculation.'}, status=400)
                
                # Prepare step-by-step
                step_by_step = self._prepare_step_by_step_antilog(log_value, base, result)
                
                # Prepare chart data
                chart_data = {}
                try:
                    chart_data = self._prepare_chart_data('antilog', log_value, base, result)
                except Exception as e:
                    import traceback
                    print(f"Chart data preparation error: {traceback.format_exc()}")
                    chart_data = {}
                
                response = {
                    'success': True,
                    'calc_type': 'antilog',
                    'log_value': log_value,
                    'base': base if base != 'e' else 'e',
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
            print(f"Log Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
