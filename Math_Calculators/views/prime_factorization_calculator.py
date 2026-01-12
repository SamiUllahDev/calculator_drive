from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import factorint, isprime, divisors


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PrimeFactorizationCalculator(View):
    """
    Enhanced Professional Prime Factorization Calculator
    Calculates prime factors, prime factorization, and all factors with step-by-step solutions.
    """
    template_name = 'math_calculators/prime_factorization_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Prime Factorization Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_integer(self, value, name):
        """Validate that a value is a positive integer"""
        try:
            num = int(float(value))
            if num <= 0:
                return None, f'{name} must be a positive integer.'
            if num > 10**15:
                return None, f'{name} is too large. Maximum value is 10^15.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid positive integer.'
    
    def _calculate_prime_factors(self, n):
        """Calculate prime factors using SymPy"""
        try:
            factors = factorint(n)
            return factors, None
        except Exception as e:
            return None, str(e)
    
    def _format_prime_factorization(self, factors_dict):
        """Format prime factorization as string"""
        if not factors_dict:
            return "1"
        
        parts = []
        for prime, exponent in sorted(factors_dict.items()):
            if exponent == 1:
                parts.append(str(prime))
            else:
                parts.append(f"{prime}^{exponent}")
        return " × ".join(parts)
    
    def _get_all_factors(self, n):
        """Get all factors of n"""
        try:
            all_divisors = divisors(n)
            return sorted(all_divisors), None
        except Exception as e:
            return None, str(e)
    
    def _prepare_step_by_step(self, n, factors_dict, all_factors):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given: {n}")
        steps.append("")
        
        # Check if prime
        if isprime(n):
            steps.append("Step 1: Check if the number is prime")
            steps.append(f"  {n} is a prime number.")
            steps.append(f"  Prime factorization: {n} = {n}")
            steps.append("")
            steps.append("Step 2: All factors")
            steps.append(f"  Since {n} is prime, it has only two factors: 1 and {n}")
            return steps
        
        steps.append("Step 1: Find prime factors")
        steps.append(f"  We need to find all prime numbers that divide {n}.")
        steps.append("")
        
        # Show division process
        current = n
        division_steps = []
        temp_factors = {}
        
        for prime, exponent in sorted(factors_dict.items()):
            temp_factors[prime] = exponent
        
        # Reconstruct division steps
        temp_n = n
        for prime in sorted(factors_dict.keys()):
            exponent = factors_dict[prime]
            for i in range(exponent):
                if temp_n % prime == 0:
                    division_steps.append(f"  {temp_n} ÷ {prime} = {temp_n // prime}")
                    temp_n = temp_n // prime
        
        steps.extend(division_steps)
        steps.append("")
        
        steps.append("Step 2: Prime factorization")
        factorization_str = self._format_prime_factorization(factors_dict)
        steps.append(f"  {n} = {factorization_str}")
        steps.append("")
        
        steps.append("Step 3: Verify")
        verification = 1
        for prime, exponent in sorted(factors_dict.items()):
            verification *= prime ** exponent
        steps.append(f"  Verification: {factorization_str} = {verification}")
        if verification == n:
            steps.append(f"  ✓ Verification successful!")
        steps.append("")
        
        steps.append("Step 4: All factors")
        steps.append(f"  Total number of factors: {len(all_factors)}")
        if len(all_factors) <= 20:
            steps.append(f"  Factors: {', '.join(map(str, all_factors))}")
        else:
            steps.append(f"  First 10 factors: {', '.join(map(str, all_factors[:10]))}")
            steps.append(f"  Last 10 factors: {', '.join(map(str, all_factors[-10:]))}")
        
        return steps
    
    def _prepare_chart_data(self, factors_dict, all_factors):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Prime factors chart
            if factors_dict:
                primes = sorted(factors_dict.keys())
                exponents = [factors_dict[p] for p in primes]
                
                chart_data['prime_factors_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': [str(p) for p in primes],
                        'datasets': [{
                            'label': 'Exponent',
                            'data': exponents,
                            'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                            'borderColor': '#3b82f6',
                            'borderWidth': 2
                        }]
                    }
                }
            
            # Factors distribution (if not too many)
            if len(all_factors) <= 50:
                chart_data['factors_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': [str(f) for f in all_factors],
                        'datasets': [{
                            'label': 'Factor',
                            'data': [1] * len(all_factors),
                            'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                            'borderColor': '#10b981',
                            'borderWidth': 1
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
            
            # Get number
            n, error = self._validate_positive_integer(data.get('number'), 'Number')
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate prime factors
            factors_dict, error = self._calculate_prime_factors(n)
            if error:
                return JsonResponse({'success': False, 'error': f'Error calculating prime factors: {error}'}, status=400)
            
            # Get all factors
            all_factors, error = self._get_all_factors(n)
            if error:
                return JsonResponse({'success': False, 'error': f'Error calculating all factors: {error}'}, status=400)
            
            # Format prime factorization
            factorization_str = self._format_prime_factorization(factors_dict)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(n, factors_dict, all_factors)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(factors_dict, all_factors)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Additional information
            is_prime = isprime(n)
            num_factors = len(all_factors)
            num_prime_factors = len(factors_dict)
            
            response = {
                'success': True,
                'number': n,
                'is_prime': is_prime,
                'prime_factors': list(factors_dict.keys()),
                'prime_factorization': factorization_str,
                'factors_dict': {str(k): v for k, v in factors_dict.items()},
                'all_factors': all_factors,
                'num_factors': num_factors,
                'num_prime_factors': num_prime_factors,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Prime Factorization Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
