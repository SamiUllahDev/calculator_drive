from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import gcd, lcm, factorint, divisors
from functools import reduce


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GreatestCommonFactorCalculator(View):
    """
    Enhanced Professional Greatest Common Factor (GCD) Calculator
    Calculates GCD and LCM for multiple numbers with step-by-step solutions.
    """
    template_name = 'math_calculators/greatest_common_factor_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Greatest Common Factor Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_integer(self, value, name):
        """Validate that a value is a positive integer"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0:
                return None, f'{name} must be greater than zero.'
            if num != int(num):
                return None, f'{name} must be an integer (whole number).'
            if num > 1e10:
                return None, f'{name} is too large. Maximum value is 10,000,000,000.'
            return int(num), None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid integer.'
    
    def _calculate_gcd(self, numbers):
        """Calculate GCD of multiple numbers"""
        try:
            if len(numbers) == 1:
                return abs(numbers[0])
            return int(reduce(gcd, numbers))
        except:
            # Fallback method
            result = abs(numbers[0])
            for num in numbers[1:]:
                result = self._gcd_two(result, abs(num))
            return result
    
    def _gcd_two(self, a, b):
        """Calculate GCD of two numbers using Euclidean algorithm"""
        while b:
            a, b = b, a % b
        return a
    
    def _calculate_lcm(self, numbers):
        """Calculate LCM of multiple numbers"""
        try:
            if len(numbers) == 1:
                return abs(numbers[0])
            return int(reduce(lcm, numbers))
        except:
            # Fallback method
            result = abs(numbers[0])
            for num in numbers[1:]:
                result = abs(result * num) // self._gcd_two(result, abs(num))
            return result
    
    def _get_prime_factors(self, num):
        """Get prime factorization of a number"""
        try:
            factors_dict = factorint(abs(num))
            return factors_dict
        except:
            # Fallback method
            factors = {}
            temp = abs(num)
            i = 2
            while i * i <= temp:
                if temp % i == 0:
                    count = 0
                    while temp % i == 0:
                        count += 1
                        temp //= i
                    factors[i] = count
                i += 1
            if temp > 1:
                factors[temp] = 1
            return factors
    
    def _get_all_factors(self, num):
        """Get all factors of a number"""
        try:
            factors = divisors(abs(num))
            return sorted([int(f) for f in factors if f > 0])
        except:
            # Fallback method
            factors = []
            for i in range(1, int(math.sqrt(abs(num))) + 1):
                if abs(num) % i == 0:
                    factors.append(i)
                    if i != abs(num) // i:
                        factors.append(abs(num) // i)
            return sorted(factors)
    
    def _prepare_step_by_step(self, numbers, gcd_value, lcm_value):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given numbers: {', '.join(map(str, numbers))}")
        steps.append("")
        
        if len(numbers) == 2:
            steps.append("Step 1: Find GCD using Euclidean Algorithm")
            a, b = abs(numbers[0]), abs(numbers[1])
            original_a, original_b = a, b
            step_count = 1
            
            while b != 0:
                quotient = a // b
                remainder = a % b
                steps.append(f"  Step {step_count}.1: {a} = {b} × {quotient} + {remainder}")
                if remainder == 0:
                    steps.append(f"  Since remainder is 0, GCD = {b}")
                    break
                a, b = b, remainder
                step_count += 1
            
            steps.append(f"  Therefore, GCD({original_a}, {original_b}) = {gcd_value}")
            steps.append("")
            
            steps.append("Step 2: Find LCM using the formula")
            steps.append(f"  LCM(a, b) = (a × b) / GCD(a, b)")
            steps.append(f"  LCM({original_a}, {original_b}) = ({original_a} × {original_b}) / {gcd_value}")
            steps.append(f"  = {original_a * original_b} / {gcd_value}")
            steps.append(f"  = {lcm_value}")
            
        else:
            steps.append("Step 1: Find GCD of multiple numbers")
            steps.append("  We'll find GCD by computing GCD of pairs:")
            
            current_gcd = abs(numbers[0])
            for i in range(1, len(numbers)):
                prev_gcd = current_gcd
                current_gcd = self._gcd_two(current_gcd, abs(numbers[i]))
                steps.append(f"  GCD({prev_gcd}, {abs(numbers[i])}) = {current_gcd}")
            
            steps.append(f"  Therefore, GCD({', '.join(map(str, numbers))}) = {gcd_value}")
            steps.append("")
            
            steps.append("Step 2: Find LCM of multiple numbers")
            steps.append("  We'll find LCM by computing LCM of pairs:")
            
            current_lcm = abs(numbers[0])
            for i in range(1, len(numbers)):
                prev_lcm = current_lcm
                current_lcm = abs(current_lcm * abs(numbers[i])) // self._gcd_two(current_lcm, abs(numbers[i]))
                steps.append(f"  LCM({prev_lcm}, {abs(numbers[i])}) = {current_lcm}")
            
            steps.append(f"  Therefore, LCM({', '.join(map(str, numbers))}) = {lcm_value}")
        
        steps.append("")
        steps.append("Step 3: Verification")
        steps.append(f"  GCD = {gcd_value}")
        steps.append(f"  LCM = {lcm_value}")
        
        # Verify GCD divides all numbers
        all_divisible = all(num % gcd_value == 0 for num in numbers)
        if all_divisible:
            steps.append(f"  ✓ GCD({gcd_value}) divides all given numbers")
        
        # Verify LCM is divisible by all numbers
        all_divide = all(lcm_value % abs(num) == 0 for num in numbers)
        if all_divide:
            steps.append(f"  ✓ All numbers divide LCM({lcm_value})")
        
        return steps
    
    def _prepare_chart_data(self, numbers, gcd_value, lcm_value):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        # Numbers comparison chart
        if len(numbers) <= 10:
            chart_data['numbers_comparison'] = {
                'type': 'bar',
                'data': {
                    'labels': [f'Number {i+1}' for i in range(len(numbers))],
                    'datasets': [{
                        'label': 'Value',
                        'data': [abs(n) for n in numbers],
                        'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                        'borderColor': '#3b82f6',
                        'borderWidth': 2
                    }]
                }
            }
        
        # GCD and LCM comparison
        chart_data['gcd_lcm_comparison'] = {
            'type': 'bar',
            'data': {
                'labels': ['GCD', 'LCM'],
                'datasets': [{
                    'label': 'Value',
                    'data': [gcd_value, lcm_value],
                    'backgroundColor': [
                        'rgba(16, 185, 129, 0.6)',
                        'rgba(139, 92, 246, 0.6)'
                    ],
                    'borderColor': [
                        '#10b981',
                        '#8b5cf6'
                    ],
                    'borderWidth': 2
                }]
            }
        }
        
        # Prime factors visualization (for 2 numbers)
        if len(numbers) == 2:
            try:
                factors1 = self._get_prime_factors(numbers[0])
                factors2 = self._get_prime_factors(numbers[1])
                
                all_primes = sorted(set(list(factors1.keys()) + list(factors2.keys())))
                
                if len(all_primes) <= 15:
                    chart_data['prime_factors'] = {
                        'type': 'bar',
                        'data': {
                            'labels': [str(p) for p in all_primes],
                            'datasets': [
                                {
                                    'label': f'Number 1 ({numbers[0]})',
                                    'data': [factors1.get(p, 0) for p in all_primes],
                                    'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                                    'borderColor': '#3b82f6',
                                    'borderWidth': 2
                                },
                                {
                                    'label': f'Number 2 ({numbers[1]})',
                                    'data': [factors2.get(p, 0) for p in all_primes],
                                    'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                                    'borderColor': '#10b981',
                                    'borderWidth': 2
                                }
                            ]
                        }
                    }
            except:
                pass
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get numbers from input
            numbers_list = data.get('numbers', [])
            if not numbers_list:
                # Fallback to individual inputs
                num1 = data.get('input1') or data.get('num1')
                num2 = data.get('input2') or data.get('num2')
                if num1:
                    numbers_list = [num1]
                    if num2:
                        numbers_list.append(num2)
            
            if not numbers_list:
                return JsonResponse({'success': False, 'error': 'Please provide at least one number.'}, status=400)
            
            # Validate and convert numbers
            validated_numbers = []
            for i, num in enumerate(numbers_list):
                validated_num, error = self._validate_positive_integer(num, f'Number {i+1}')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                validated_numbers.append(validated_num)
            
            if len(validated_numbers) < 1:
                return JsonResponse({'success': False, 'error': 'Please provide at least one number.'}, status=400)
            
            # Calculate GCD
            gcd_value = self._calculate_gcd(validated_numbers)
            
            # Calculate LCM (only if more than one number)
            lcm_value = None
            if len(validated_numbers) > 1:
                lcm_value = self._calculate_lcm(validated_numbers)
            
            # Get prime factorizations
            prime_factors_list = []
            for num in validated_numbers:
                factors = self._get_prime_factors(num)
                prime_factors_list.append({
                    'number': num,
                    'factors': factors,
                    'formatted': ' × '.join([f'{p}^{power}' if power > 1 else str(p) 
                                            for p, power in sorted(factors.items())])
                })
            
            # Get all factors for each number
            all_factors_list = []
            for num in validated_numbers:
                factors = self._get_all_factors(num)
                all_factors_list.append({
                    'number': num,
                    'factors': factors
                })
            
            # Find common factors
            if len(validated_numbers) > 1:
                common_factors = set(all_factors_list[0]['factors'])
                for factors_data in all_factors_list[1:]:
                    common_factors &= set(factors_data['factors'])
                common_factors = sorted(list(common_factors))
            else:
                common_factors = all_factors_list[0]['factors']
            
            # Prepare step-by-step solution
            if lcm_value:
                step_by_step = self._prepare_step_by_step(validated_numbers, gcd_value, lcm_value)
            else:
                step_by_step = [f"Given number: {validated_numbers[0]}", 
                               f"GCD of a single number is the number itself: {gcd_value}"]
            
            # Prepare chart data
            chart_data = {}
            try:
                if lcm_value:
                    chart_data = self._prepare_chart_data(validated_numbers, gcd_value, lcm_value)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare response
            response = {
                'success': True,
                'numbers': validated_numbers,
                'gcd': gcd_value,
                'lcm': lcm_value,
                'prime_factors': prime_factors_list,
                'all_factors': all_factors_list,
                'common_factors': common_factors,
                'step_by_step': step_by_step,
                'chart_data': chart_data,
                'count': len(validated_numbers)
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"GCD Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
