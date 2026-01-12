from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import divisors, factorint, isprime, gcd as sympy_gcd, lcm as sympy_lcm


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FactorCalculator(View):
    """
    Enhanced Professional Factor Calculator
    Finds all factors, prime factors, and related information for a number.
    Includes advanced features: factor pairs, number properties, GCD/LCM, and more.
    """
    template_name = 'math_calculators/factor_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Factor Calculator',
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
            if num > 1e10:  # Prevent extremely large numbers
                return None, f'{name} is too large. Maximum value is 10,000,000,000.'
            return int(num), None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid integer.'
    
    def _get_all_factors(self, num):
        """Get all factors of a number using SymPy"""
        try:
            factors = divisors(num)
            factors_list = sorted([int(f) for f in factors if f > 0])
            return factors_list
        except Exception:
            # Fallback method
            factors = []
            for i in range(1, int(math.sqrt(num)) + 1):
                if num % i == 0:
                    factors.append(i)
                    if i != num // i:
                        factors.append(num // i)
            return sorted(factors)
    
    def _get_factor_pairs(self, num):
        """Get all factor pairs of a number"""
        factors = self._get_all_factors(num)
        pairs = []
        used = set()
        
        for factor in factors:
            if factor not in used:
                complement = num // factor
                if complement not in used:
                    pairs.append([factor, complement])
                    used.add(factor)
                    used.add(complement)
        
        return pairs
    
    def _get_prime_factors(self, num):
        """Get prime factorization using SymPy"""
        try:
            prime_factors_dict = factorint(num)
            prime_factors = []
            for prime, power in sorted(prime_factors_dict.items()):
                if power == 1:
                    prime_factors.append(prime)
                else:
                    prime_factors.append((prime, power))
            return prime_factors, prime_factors_dict
        except Exception:
            # Fallback method
            factors = []
            temp = num
            i = 2
            while i * i <= temp:
                if temp % i == 0:
                    count = 0
                    while temp % i == 0:
                        count += 1
                        temp //= i
                    if count == 1:
                        factors.append(i)
                    else:
                        factors.append((i, count))
                i += 1
            if temp > 1:
                factors.append(temp)
            return factors, {}
    
    def _is_prime(self, num):
        """Check if a number is prime using SymPy"""
        try:
            return isprime(num)
        except Exception:
            # Fallback: simple prime check
            if num < 2:
                return False
            if num == 2:
                return True
            if num % 2 == 0:
                return False
            for i in range(3, int(math.sqrt(num)) + 1, 2):
                if num % i == 0:
                    return False
            return True
    
    def _get_sum_of_factors(self, factors):
        """Calculate sum of all factors"""
        return sum(factors)
    
    def _get_sum_of_proper_factors(self, factors, num):
        """Calculate sum of proper factors (excluding the number itself)"""
        proper_factors = [f for f in factors if f < num]
        return sum(proper_factors)
    
    def _classify_number(self, num, sum_of_proper_factors):
        """Classify number as perfect, abundant, or deficient"""
        if num == 1:
            return 'deficient', '1 has no proper factors'
        
        if sum_of_proper_factors == num:
            return 'perfect', f'Sum of proper factors ({sum_of_proper_factors}) equals the number'
        elif sum_of_proper_factors > num:
            return 'abundant', f'Sum of proper factors ({sum_of_proper_factors}) is greater than the number'
        else:
            return 'deficient', f'Sum of proper factors ({sum_of_proper_factors}) is less than the number'
    
    def _is_even(self, num):
        """Check if number is even"""
        return num % 2 == 0
    
    def _is_square(self, num):
        """Check if number is a perfect square"""
        root = int(math.sqrt(num))
        return root * root == num
    
    def _is_power_of_two(self, num):
        """Check if number is a power of 2"""
        return num > 0 and (num & (num - 1)) == 0
    
    def _get_factor_tree_data(self, num, prime_factors_dict):
        """Generate factor tree structure for visualization"""
        if not prime_factors_dict or num == 1:
            return {'value': num, 'children': []}
        
        if len(prime_factors_dict) == 1:
            prime, power = list(prime_factors_dict.items())[0]
            if power == 1:
                return {'value': num, 'children': [{'value': prime, 'children': []}]}
            else:
                # For powers, show intermediate steps
                children = []
                current = prime
                for _ in range(power - 1):
                    children.append({'value': prime, 'children': []})
                return {'value': num, 'children': [{'value': current, 'children': children}]}
        
        # Multiple prime factors
        children = []
        for prime, power in sorted(prime_factors_dict.items()):
            if power == 1:
                children.append({'value': prime, 'children': []})
            else:
                prime_power = prime ** power
                power_children = [{'value': prime, 'children': []} for _ in range(power)]
                children.append({'value': prime_power, 'children': power_children})
        
        return {'value': num, 'children': children}
    
    def prepare_chart_data(self, num, factors, prime_factors_dict, factor_pairs):
        """Prepare enhanced chart data for factor visualization"""
        if not factors:
            return {}
        
        chart_data = {}
        
        # Factor count chart
        proper_factors = [f for f in factors if f < num]
        proper_factor_count = len(proper_factors)
        
        chart_data['factor_count_chart'] = {
            'type': 'doughnut',
            'data': {
                'labels': ['Proper Factors', 'Number Itself'],
                'datasets': [{
                    'data': [proper_factor_count, 1],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.6)',
                        'rgba(229, 231, 235, 0.6)'
                    ],
                    'borderColor': [
                        '#3b82f6',
                        '#e5e7eb'
                    ],
                    'borderWidth': 2
                }]
            }
        }
        
        # Prime factors visualization
        if prime_factors_dict:
            primes = list(prime_factors_dict.keys())
            powers = list(prime_factors_dict.values())
            
            chart_data['prime_factors_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': [str(p) for p in primes],
                    'datasets': [{
                        'label': 'Power',
                        'data': powers,
                        'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                        'borderColor': '#10b981',
                        'borderWidth': 2
                    }]
                }
            }
        
        # Factor distribution chart (for numbers with reasonable factor count)
        if len(factors) <= 30:
            chart_data['factor_distribution_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': [str(f) for f in factors],
                    'datasets': [{
                        'label': 'Factor',
                        'data': [1] * len(factors),
                        'backgroundColor': [
                            '#ef4444' if f == 1 or f == num else '#3b82f6'
                            for f in factors
                        ],
                        'borderColor': [
                            '#dc2626' if f == 1 or f == num else '#2563eb'
                            for f in factors
                        ],
                        'borderWidth': 2
                    }]
                }
            }
        
        # Factor pairs visualization
        if len(factor_pairs) <= 15:
            pair_labels = [f'{pair[0]} × {pair[1]}' for pair in factor_pairs]
            chart_data['factor_pairs_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': pair_labels,
                    'datasets': [{
                        'label': 'Product',
                        'data': [num] * len(factor_pairs),
                        'backgroundColor': 'rgba(139, 92, 246, 0.6)',
                        'borderColor': '#8b5cf6',
                        'borderWidth': 2
                    }]
                }
            }
        
        # Factor size comparison (for smaller numbers)
        if num <= 1000 and len(factors) <= 20:
            chart_data['factor_size_chart'] = {
                'type': 'line',
                'data': {
                    'labels': [str(f) for f in factors],
                    'datasets': [{
                        'label': 'Factor Value',
                        'data': factors,
                        'borderColor': '#f59e0b',
                        'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
                    }]
                }
            }
        
        return chart_data
    
    def prepare_display_data(self, num, factors, prime_factors, prime_factors_dict, is_prime, 
                            factor_pairs, sum_of_factors, sum_of_proper_factors, number_classification,
                            is_even, is_square, is_power_of_two):
        """Prepare enhanced formatted display data for frontend"""
        proper_factors = [f for f in factors if f < num]
        
        display_data = {
            'number': num,
            'factors': factors,
            'factors_count': len(factors),
            'proper_factors': proper_factors,
            'proper_factors_count': len(proper_factors),
            'is_prime': is_prime,
            'prime_factors': prime_factors,
            'factor_pairs': factor_pairs,
            'factor_pairs_count': len(factor_pairs),
            'sum_of_factors': sum_of_factors,
            'sum_of_proper_factors': sum_of_proper_factors,
            'number_classification': number_classification[0],
            'number_classification_desc': number_classification[1],
            'is_even': is_even,
            'is_square': is_square,
            'is_power_of_two': is_power_of_two,
            'formatted_results': []
        }
        
        # Format prime factorization string
        prime_factorization_str = ''
        if prime_factors_dict:
            parts = []
            for prime, power in sorted(prime_factors_dict.items()):
                if power == 1:
                    parts.append(str(prime))
                else:
                    parts.append(f'{prime}^{power}')
            prime_factorization_str = ' × '.join(parts)
        else:
            prime_factorization_str = str(num)
        
        # Format factor pairs string
        factor_pairs_str = ', '.join([f'{pair[0]} × {pair[1]}' for pair in factor_pairs])
        
        display_data['formatted_results'] = [
            {
                'label': 'Number',
                'value': str(num),
                'is_primary': False
            },
            {
                'label': 'Is Prime?',
                'value': 'Yes' if is_prime else 'No',
                'is_primary': True
            },
            {
                'label': 'Number Type',
                'value': number_classification[0].title(),
                'is_primary': True
            },
            {
                'label': 'Total Factors',
                'value': str(len(factors)),
                'is_primary': False
            },
            {
                'label': 'Proper Factors',
                'value': str(len(proper_factors)),
                'is_primary': False
            },
            {
                'label': 'Factor Pairs',
                'value': str(len(factor_pairs)),
                'is_primary': False
            },
            {
                'label': 'Sum of All Factors',
                'value': str(sum_of_factors),
                'is_primary': False
            },
            {
                'label': 'Sum of Proper Factors',
                'value': str(sum_of_proper_factors),
                'is_primary': False
            },
            {
                'label': 'Prime Factorization',
                'value': prime_factorization_str,
                'is_primary': True
            },
            {
                'label': 'Is Even?',
                'value': 'Yes' if is_even else 'No',
                'is_primary': False
            },
            {
                'label': 'Is Perfect Square?',
                'value': 'Yes' if is_square else 'No',
                'is_primary': False
            },
            {
                'label': 'Is Power of 2?',
                'value': 'Yes' if is_power_of_two else 'No',
                'is_primary': False
            },
            {
                'label': 'All Factors',
                'value': ', '.join(map(str, factors)),
                'is_primary': False
            },
            {
                'label': 'Factor Pairs',
                'value': factor_pairs_str if len(factor_pairs_str) <= 200 else factor_pairs_str[:200] + '...',
                'is_primary': False
            }
        ]
        
        return display_data
    
    def prepare_step_by_step(self, num, factors, prime_factors, prime_factors_dict, is_prime,
                            factor_pairs, sum_of_proper_factors, number_classification):
        """Prepare enhanced step-by-step solution"""
        steps = []
        
        steps.append(f"Given number: {num}")
        
        if is_prime:
            steps.append(f"Step 1: Check if the number is prime")
            steps.append(f"  {num} is a prime number.")
            steps.append(f"Step 2: Prime numbers have exactly 2 factors: 1 and itself")
            steps.append(f"  Factors of {num}: 1, {num}")
            steps.append(f"Step 3: Prime factorization")
            steps.append(f"  Since {num} is prime, its prime factorization is: {num} = {num}")
        else:
            steps.append(f"Step 1: Check if the number is prime")
            steps.append(f"  {num} is not a prime number (it has more than 2 factors).")
            
            steps.append(f"Step 2: Find all factors")
            steps.append(f"  We need to find all numbers that divide {num} evenly.")
            steps.append(f"  Factors of {num}: {', '.join(map(str, factors))}")
            steps.append(f"  Total number of factors: {len(factors)}")
            
            proper_factors = [f for f in factors if f < num]
            if proper_factors:
                steps.append(f"  Proper factors (excluding the number itself): {', '.join(map(str, proper_factors))}")
            
            steps.append(f"Step 3: Factor pairs")
            if len(factor_pairs) <= 10:
                pairs_str = ', '.join([f'{pair[0]} × {pair[1]}' for pair in factor_pairs])
                steps.append(f"  Factor pairs of {num}: {pairs_str}")
            else:
                steps.append(f"  Total factor pairs: {len(factor_pairs)}")
                steps.append(f"  First few pairs: {', '.join([f'{pair[0]} × {pair[1]}' for pair in factor_pairs[:5]])}...")
            
            steps.append(f"Step 4: Prime factorization")
            if prime_factors_dict:
                parts = []
                for prime, power in sorted(prime_factors_dict.items()):
                    if power == 1:
                        parts.append(str(prime))
                    else:
                        parts.append(f'{prime}^{power}')
                prime_factorization = ' × '.join(parts)
                steps.append(f"  {num} = {prime_factorization}")
                
                steps.append(f"Step 5: Verification")
                verification = 1
                for prime, power in sorted(prime_factors_dict.items()):
                    verification *= prime ** power
                steps.append(f"  {prime_factorization} = {verification}")
                if verification == num:
                    steps.append(f"  ✓ Verification successful!")
            else:
                steps.append(f"  Prime factorization: {num} = {num}")
            
            steps.append(f"Step 6: Number classification")
            steps.append(f"  Sum of proper factors: {sum_of_proper_factors}")
            steps.append(f"  {number_classification[1]}")
            steps.append(f"  Therefore, {num} is a {number_classification[0]} number.")
        
        return steps
    
    def prepare_step_by_step_html(self, steps):
        """Prepare step-by-step solution as HTML structure"""
        if not steps or not isinstance(steps, list):
            return []
        
        return [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(steps)]
    
    def calculate_gcd_lcm(self, num1, num2):
        """Calculate GCD and LCM of two numbers"""
        try:
            gcd_value = int(sympy_gcd(num1, num2))
            lcm_value = int(sympy_lcm(num1, num2))
            return gcd_value, lcm_value, None
        except Exception as e:
            # Fallback method
            try:
                def calculate_gcd(a, b):
                    while b:
                        a, b = b, a % b
                    return a
                
                gcd_value = calculate_gcd(num1, num2)
                lcm_value = (num1 * num2) // gcd_value
                return gcd_value, lcm_value, None
            except Exception as fallback_error:
                return None, None, str(fallback_error)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Check if comparing two numbers
            compare_mode = data.get('compare', False)
            num2 = None
            
            # Get number(s) from input
            num, error = self._validate_positive_integer(data.get('number'), 'Number')
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            if compare_mode:
                num2, error2 = self._validate_positive_integer(data.get('number2'), 'Second Number')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            # Get all factors
            factors = self._get_all_factors(num)
            
            # Get factor pairs
            factor_pairs = self._get_factor_pairs(num)
            
            # Get prime factors
            prime_factors, prime_factors_dict = self._get_prime_factors(num)
            
            # Check if prime
            is_prime = self._is_prime(num)
            
            # Calculate sums
            sum_of_factors = self._get_sum_of_factors(factors)
            sum_of_proper_factors = self._get_sum_of_proper_factors(factors, num)
            
            # Classify number
            number_classification = self._classify_number(num, sum_of_proper_factors)
            
            # Additional properties
            is_even = self._is_even(num)
            is_square = self._is_square(num)
            is_power_of_two = self._is_power_of_two(num)
            
            # Get factor tree data
            factor_tree = self._get_factor_tree_data(num, prime_factors_dict)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self.prepare_chart_data(num, factors, prime_factors_dict, factor_pairs)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare display data
            display_data = self.prepare_display_data(
                num, factors, prime_factors, prime_factors_dict, is_prime,
                factor_pairs, sum_of_factors, sum_of_proper_factors, number_classification,
                is_even, is_square, is_power_of_two
            )
            
            # Prepare step-by-step solution
            step_by_step = self.prepare_step_by_step(
                num, factors, prime_factors, prime_factors_dict, is_prime,
                factor_pairs, sum_of_proper_factors, number_classification
            )
            step_by_step_html = self.prepare_step_by_step_html(step_by_step)
            
            # Prepare response
            response = {
                'success': True,
                'number': num,
                'factors': factors,
                'factor_pairs': factor_pairs,
                'prime_factors': prime_factors,
                'prime_factors_dict': prime_factors_dict,
                'is_prime': is_prime,
                'sum_of_factors': sum_of_factors,
                'sum_of_proper_factors': sum_of_proper_factors,
                'number_classification': number_classification[0],
                'number_classification_desc': number_classification[1],
                'is_even': is_even,
                'is_square': is_square,
                'is_power_of_two': is_power_of_two,
                'factor_tree': factor_tree,
                'chart_data': chart_data,
                'display_data': display_data,
                'step_by_step': step_by_step,
                'step_by_step_html': step_by_step_html
            }
            
            # If comparing two numbers, add comparison data
            if compare_mode and num2:
                factors2 = self._get_all_factors(num2)
                gcd, lcm, error = self.calculate_gcd_lcm(num, num2)
                
                if error:
                    response['comparison_error'] = error
                else:
                    response['comparison'] = {
                        'number1': num,
                        'number2': num2,
                        'gcd': gcd,
                        'lcm': lcm,
                        'factors1': factors,
                        'factors2': factors2,
                        'common_factors': sorted(list(set(factors) & set(factors2)))
                    }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Factor Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
