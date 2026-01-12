from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import lcm, gcd, factorint
from functools import reduce


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LeastCommonMultipleCalculator(View):
    """
    Enhanced Professional Least Common Multiple (LCM) Calculator
    Calculates LCM for multiple numbers with step-by-step solutions.
    """
    template_name = 'math_calculators/least_common_multiple_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Least Common Multiple Calculator',
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
    
    def _get_gcd(self, a, b):
        """Calculate GCD of two numbers"""
        try:
            return int(gcd(abs(a), abs(b)))
        except:
            a, b = abs(a), abs(b)
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
                result = abs(result * num) // self._get_gcd(result, abs(num))
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
    
    def _prepare_step_by_step(self, numbers, lcm_value):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given numbers: {', '.join(map(str, numbers))}")
        steps.append("")
        
        if len(numbers) == 2:
            steps.append("Step 1: Find LCM using the formula")
            steps.append(f"  LCM(a, b) = (a × b) / GCD(a, b)")
            steps.append(f"  LCM({numbers[0]}, {numbers[1]}) = ({numbers[0]} × {numbers[1]}) / GCD({numbers[0]}, {numbers[1]})")
            
            gcd_value = self._get_gcd(numbers[0], numbers[1])
            steps.append(f"  GCD({numbers[0]}, {numbers[1]}) = {gcd_value}")
            steps.append(f"  LCM({numbers[0]}, {numbers[1]}) = {numbers[0] * numbers[1]} / {gcd_value}")
            steps.append(f"  LCM({numbers[0]}, {numbers[1]}) = {lcm_value}")
            
        else:
            steps.append("Step 1: Find LCM of multiple numbers")
            steps.append("  We'll find LCM by computing LCM of pairs:")
            
            current_lcm = abs(numbers[0])
            for i in range(1, len(numbers)):
                prev_lcm = current_lcm
                gcd_value = self._get_gcd(current_lcm, abs(numbers[i]))
                current_lcm = abs(current_lcm * abs(numbers[i])) // gcd_value
                steps.append(f"  LCM({prev_lcm}, {abs(numbers[i])}) = ({prev_lcm} × {abs(numbers[i])}) / GCD({prev_lcm}, {abs(numbers[i])})")
                steps.append(f"  GCD({prev_lcm}, {abs(numbers[i])}) = {gcd_value}")
                steps.append(f"  LCM({prev_lcm}, {abs(numbers[i])}) = {current_lcm}")
            
            steps.append(f"  Therefore, LCM({', '.join(map(str, numbers))}) = {lcm_value}")
        
        steps.append("")
        steps.append("Step 2: Prime Factorization Method")
        steps.append("  Find prime factors of each number:")
        
        all_prime_factors = {}
        for num in numbers:
            factors = self._get_prime_factors(num)
            all_prime_factors[num] = factors
            factors_str = ' × '.join([f'{p}^{power}' if power > 1 else str(p) 
                                     for p, power in sorted(factors.items())])
            steps.append(f"  {num} = {factors_str}")
        
        steps.append("")
        steps.append("  Take the highest power of each prime factor:")
        combined_factors = {}
        for num, factors in all_prime_factors.items():
            for prime, power in factors.items():
                if prime not in combined_factors or power > combined_factors[prime]:
                    combined_factors[prime] = power
        
        lcm_factors_str = ' × '.join([f'{p}^{power}' if power > 1 else str(p) 
                                     for p, power in sorted(combined_factors.items())])
        steps.append(f"  LCM = {lcm_factors_str}")
        
        # Verify
        verification = 1
        for prime, power in sorted(combined_factors.items()):
            verification *= prime ** power
        
        steps.append(f"  LCM = {verification}")
        if verification == lcm_value:
            steps.append(f"  ✓ Verification successful!")
        
        steps.append("")
        steps.append("Step 3: Verification")
        steps.append(f"  LCM = {lcm_value}")
        
        # Verify LCM is divisible by all numbers
        all_divide = all(lcm_value % abs(num) == 0 for num in numbers)
        if all_divide:
            steps.append(f"  ✓ All numbers divide LCM({lcm_value})")
            for num in numbers:
                steps.append(f"    {lcm_value} ÷ {abs(num)} = {lcm_value // abs(num)}")
        
        return steps
    
    def _prepare_chart_data(self, numbers, lcm_value):
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
        
        # LCM vs Numbers comparison
        chart_data['lcm_comparison'] = {
            'type': 'bar',
            'data': {
                'labels': [f'Number {i+1}' for i in range(len(numbers))] + ['LCM'],
                'datasets': [{
                    'label': 'Value',
                    'data': [abs(n) for n in numbers] + [lcm_value],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.6)' for _ in numbers
                    ] + ['rgba(139, 92, 246, 0.6)'],
                    'borderColor': [
                        '#3b82f6' for _ in numbers
                    ] + ['#8b5cf6'],
                    'borderWidth': 2
                }]
            }
        }
        
        # Prime factors visualization (for 2 numbers)
        if len(numbers) == 2:
            try:
                factors1 = self._get_prime_factors(numbers[0])
                factors2 = self._get_prime_factors(numbers[1])
                
                # Get LCM factors
                combined_factors = {}
                for prime, power in factors1.items():
                    combined_factors[prime] = max(power, factors2.get(prime, 0))
                for prime, power in factors2.items():
                    if prime not in combined_factors:
                        combined_factors[prime] = power
                
                all_primes = sorted(set(list(factors1.keys()) + list(factors2.keys()) + list(combined_factors.keys())))
                
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
                                },
                                {
                                    'label': f'LCM ({lcm_value})',
                                    'data': [combined_factors.get(p, 0) for p in all_primes],
                                    'backgroundColor': 'rgba(139, 92, 246, 0.6)',
                                    'borderColor': '#8b5cf6',
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
            
            # Calculate LCM
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
            
            # Get LCM prime factors
            combined_factors = {}
            for factors_data in prime_factors_list:
                for prime, power in factors_data['factors'].items():
                    if prime not in combined_factors or power > combined_factors[prime]:
                        combined_factors[prime] = power
            
            lcm_factors_formatted = ' × '.join([f'{p}^{power}' if power > 1 else str(p) 
                                                for p, power in sorted(combined_factors.items())])
            
            # Calculate GCD for reference
            gcd_value = None
            if len(validated_numbers) > 1:
                try:
                    gcd_value = int(reduce(gcd, validated_numbers))
                except:
                    gcd_value = validated_numbers[0]
                    for num in validated_numbers[1:]:
                        gcd_value = self._get_gcd(gcd_value, num)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(validated_numbers, lcm_value)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(validated_numbers, lcm_value)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare response
            response = {
                'success': True,
                'numbers': validated_numbers,
                'lcm': lcm_value,
                'gcd': gcd_value,
                'prime_factors': prime_factors_list,
                'lcm_prime_factors': combined_factors,
                'lcm_prime_factors_formatted': lcm_factors_formatted,
                'step_by_step': step_by_step,
                'chart_data': chart_data,
                'count': len(validated_numbers)
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"LCM Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
