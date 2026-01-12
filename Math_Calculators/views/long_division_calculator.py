from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LongDivisionCalculator(View):
    """
    Enhanced Professional Long Division Calculator
    Performs long division with step-by-step solutions and visual representation.
    """
    template_name = 'math_calculators/long_division_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Long Division Calculator',
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
    
    def _perform_long_division(self, dividend, divisor, decimal_places=10):
        """Perform long division and return step-by-step process"""
        if divisor == 0:
            return None, None, None, None, "Cannot divide by zero."
        
        # Handle negative numbers
        negative_result = (dividend < 0) != (divisor < 0)
        dividend = abs(dividend)
        divisor = abs(divisor)
        
        steps = []
        steps.append(f"Divide {dividend} by {divisor}")
        steps.append("")
        
        # Integer part
        quotient_int = int(dividend // divisor)
        remainder = dividend % divisor
        
        steps.append("Step 1: Integer Division")
        steps.append(f"  {dividend} ÷ {divisor} = {quotient_int} remainder {remainder}")
        
        if remainder == 0:
            result = quotient_int
            if negative_result:
                result = -result
            steps.append(f"  Result: {result}")
            return result, quotient_int, 0, steps, None
        
        # Decimal part
        steps.append("")
        steps.append("Step 2: Decimal Division")
        steps.append(f"  Bring down decimal point and continue division")
        
        decimal_digits = []
        current_remainder = remainder
        seen_remainders = {}
        repeating_start = None
        
        for i in range(decimal_places):
            current_remainder *= 10
            digit = int(current_remainder // divisor)
            decimal_digits.append(digit)
            new_remainder = current_remainder % divisor
            
            steps.append(f"  Step 2.{i+1}: {int(current_remainder)} ÷ {divisor} = {digit} remainder {int(new_remainder)}")
            
            # Check for repeating decimals
            if current_remainder in seen_remainders:
                repeating_start = seen_remainders[current_remainder]
                steps.append(f"  Repeating pattern detected starting at position {repeating_start + 1}")
                break
            
            seen_remainders[current_remainder] = i
            
            if new_remainder == 0:
                steps.append(f"  Division complete (no remainder)")
                break
            
            current_remainder = new_remainder
        
        # Build decimal part string
        if repeating_start is not None:
            non_repeating = ''.join(map(str, decimal_digits[:repeating_start]))
            repeating = ''.join(map(str, decimal_digits[repeating_start:]))
            decimal_str = f"{non_repeating}({repeating})"
        else:
            decimal_str = ''.join(map(str, decimal_digits))
        
        # Combine integer and decimal parts
        if decimal_str:
            result = float(f"{quotient_int}.{decimal_str}")
        else:
            result = quotient_int
        
        if negative_result:
            result = -result
            quotient_int = -quotient_int
        
        steps.append("")
        steps.append("Step 3: Final Result")
        if repeating_start is not None:
            steps.append(f"  {dividend} ÷ {divisor} = {quotient_int}.{decimal_str}")
            steps.append(f"  This is a repeating decimal")
        else:
            steps.append(f"  {dividend} ÷ {divisor} = {result}")
        
        return result, quotient_int, remainder, steps, repeating_start
    
    def _prepare_division_steps(self, dividend, divisor, quotient_int, remainder, decimal_digits, repeating_start):
        """Prepare detailed division steps for visual representation"""
        division_steps = []
        
        # Convert to positive for calculation
        abs_dividend = abs(dividend)
        abs_divisor = abs(divisor)
        
        # Integer division steps
        dividend_str = str(int(abs_dividend))
        divisor_str = str(int(abs_divisor))
        
        # First step: how many times divisor goes into first digit(s)
        current = 0
        position = 0
        
        for i, digit in enumerate(dividend_str):
            current = current * 10 + int(digit)
            if current >= abs_divisor:
                q = current // abs_divisor
                r = current % abs_divisor
                
                step = {
                    'step_number': len(division_steps) + 1,
                    'dividend_part': current,
                    'divisor': abs_divisor,
                    'quotient_digit': q,
                    'remainder': r,
                    'position': i,
                    'explanation': f"{current} ÷ {abs_divisor} = {q} remainder {r}"
                }
                division_steps.append(step)
                
                current = r
                position = i + 1
        
        # Decimal steps
        if remainder > 0 and decimal_digits:
            current_remainder = remainder
            for i, digit in enumerate(decimal_digits):
                if repeating_start is not None and i == repeating_start:
                    break
                current_remainder *= 10
                q = current_remainder // abs_divisor
                r = current_remainder % abs_divisor
                
                step = {
                    'step_number': len(division_steps) + 1,
                    'dividend_part': current_remainder,
                    'divisor': abs_divisor,
                    'quotient_digit': digit,
                    'remainder': r,
                    'position': len(dividend_str) + i,
                    'is_decimal': True,
                    'explanation': f"{int(current_remainder)} ÷ {abs_divisor} = {digit} remainder {int(r)}"
                }
                division_steps.append(step)
                
                current_remainder = r
                if r == 0:
                    break
        
        return division_steps
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            dividend, error1 = self._validate_number(data.get('dividend'), 'Dividend')
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            divisor, error2 = self._validate_number(data.get('divisor'), 'Divisor')
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            if divisor == 0:
                return JsonResponse({'success': False, 'error': 'Cannot divide by zero.'}, status=400)
            
            # Get decimal places preference
            decimal_places = int(data.get('decimal_places', 10))
            if decimal_places < 0 or decimal_places > 50:
                decimal_places = 10
            
            # Perform long division
            result, quotient_int, remainder, steps, repeating_start = self._perform_long_division(
                dividend, divisor, decimal_places
            )
            
            if result is None:
                return JsonResponse({'success': False, 'error': steps}, status=400)
            
            # Extract decimal digits for detailed steps
            decimal_digits = []
            if remainder > 0:
                current_remainder = remainder
                seen_remainders = {}
                for i in range(decimal_places):
                    if repeating_start is not None and i == repeating_start:
                        break
                    current_remainder *= 10
                    digit = int(current_remainder // abs(divisor))
                    decimal_digits.append(digit)
                    new_remainder = current_remainder % abs(divisor)
                    
                    if current_remainder in seen_remainders:
                        break
                    seen_remainders[current_remainder] = i
                    
                    if new_remainder == 0:
                        break
                    current_remainder = new_remainder
            
            # Prepare detailed division steps
            division_steps = self._prepare_division_steps(
                dividend, divisor, quotient_int, remainder, decimal_digits, repeating_start
            )
            
            # Format result string
            if repeating_start is not None:
                non_repeating = ''.join(map(str, decimal_digits[:repeating_start]))
                repeating = ''.join(map(str, decimal_digits[repeating_start:]))
                result_str = f"{quotient_int}.{non_repeating}({repeating})"
            elif decimal_digits:
                result_str = f"{quotient_int}.{''.join(map(str, decimal_digits))}"
            else:
                result_str = str(quotient_int)
            
            # Check if result is negative
            is_negative = (dividend < 0) != (divisor < 0)
            if is_negative and quotient_int != 0:
                result_str = '-' + result_str
            
            response = {
                'success': True,
                'dividend': dividend,
                'divisor': divisor,
                'quotient': result,
                'quotient_int': quotient_int,
                'remainder': remainder,
                'result_str': result_str,
                'is_negative': is_negative,
                'is_repeating': repeating_start is not None,
                'repeating_start': repeating_start,
                'decimal_digits': decimal_digits,
                'step_by_step': steps,
                'division_steps': division_steps
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Long Division Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
