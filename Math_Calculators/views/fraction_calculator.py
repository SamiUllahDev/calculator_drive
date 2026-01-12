from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import Rational, gcd, lcm, simplify, nsimplify, factorint
from fractions import Fraction as PyFraction


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FractionCalculator(View):
    """
    Enhanced Professional Fraction Calculator
    Performs fraction arithmetic with step-by-step solutions and detailed analysis.
    """
    template_name = 'math_calculators/fraction_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Fraction Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_fraction(self, num, den, name):
        """Validate fraction inputs"""
        try:
            num = int(num)
            den = int(den)
            if den == 0:
                return None, None, f'{name} denominator cannot be zero.'
            return num, den, None
        except (ValueError, TypeError):
            return None, None, f'{name} must be valid integers.'
    
    def _get_gcd(self, a, b):
        """Calculate GCD"""
        try:
            return int(gcd(abs(a), abs(b)))
        except:
            a, b = abs(a), abs(b)
            while b:
                a, b = b, a % b
            return a
    
    def _get_lcm(self, a, b):
        """Calculate LCM"""
        try:
            return int(lcm(abs(a), abs(b)))
        except:
            return abs(a * b) // self._get_gcd(a, b) if a and b else 0
    
    def _simplify_fraction(self, num, den):
        """Simplify a fraction to lowest terms"""
        if den == 0:
            return num, den
        common = self._get_gcd(num, den)
        return num // common, den // common
    
    def _get_mixed_number(self, num, den):
        """Convert improper fraction to mixed number"""
        if den == 0:
            return None
        
        whole_part = abs(num) // abs(den)
        remainder = abs(num) % abs(den)
        sign = -1 if (num < 0) != (den < 0) else 1
        
        if whole_part > 0 and remainder > 0:
            return {
                'whole': int(whole_part) * sign,
                'numerator': int(remainder),
                'denominator': int(abs(den)),
                'formatted': f"{int(whole_part) * sign} {int(remainder)}/{int(abs(den))}"
            }
        return None
    
    def _prepare_step_by_step(self, num1, den1, num2, den2, operation, result_num, result_den, common_lcm):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given: {num1}/{den1} {operation} {num2}/{den2}")
        steps.append("")
        
        if operation in ['+', '-']:
            steps.append("Step 1: Find the Least Common Denominator (LCD)")
            steps.append(f"  Denominators: {den1} and {den2}")
            steps.append(f"  LCD = LCM({den1}, {den2}) = {common_lcm}")
            steps.append("")
            
            steps.append("Step 2: Convert fractions to equivalent fractions with LCD")
            mult1 = common_lcm // den1
            mult2 = common_lcm // den2
            new_num1 = num1 * mult1
            new_num2 = num2 * mult2
            steps.append(f"  {num1}/{den1} = ({num1} × {mult1})/({den1} × {mult1}) = {new_num1}/{common_lcm}")
            steps.append(f"  {num2}/{den2} = ({num2} × {mult2})/({den2} × {mult2}) = {new_num2}/{common_lcm}")
            steps.append("")
            
            steps.append(f"Step 3: Perform {operation} operation")
            if operation == '+':
                steps.append(f"  {new_num1}/{common_lcm} + {new_num2}/{common_lcm} = ({new_num1} + {new_num2})/{common_lcm}")
                steps.append(f"  = {new_num1 + new_num2}/{common_lcm}")
            else:
                steps.append(f"  {new_num1}/{common_lcm} - {new_num2}/{common_lcm} = ({new_num1} - {new_num2})/{common_lcm}")
                steps.append(f"  = {new_num1 - new_num2}/{common_lcm}")
            steps.append("")
            
        elif operation == '×':
            steps.append("Step 1: Multiply numerators and denominators")
            steps.append(f"  ({num1}/{den1}) × ({num2}/{den2}) = ({num1} × {num2})/({den1} × {den2})")
            steps.append(f"  = {num1 * num2}/{den1 * den2}")
            steps.append("")
            
        elif operation == '÷':
            steps.append("Step 1: Multiply by the reciprocal")
            steps.append(f"  ({num1}/{den1}) ÷ ({num2}/{den2}) = ({num1}/{den1}) × ({den2}/{num2})")
            steps.append(f"  = ({num1} × {den2})/({den1} × {num2})")
            steps.append(f"  = {num1 * den2}/{den1 * num2}")
            steps.append("")
        
        steps.append("Step 4: Simplify the result")
        simplified_num, simplified_den = self._simplify_fraction(result_num, result_den)
        if simplified_num != result_num or simplified_den != result_den:
            steps.append(f"  GCD of {result_num} and {result_den} = {self._get_gcd(result_num, result_den)}")
            steps.append(f"  {result_num}/{result_den} = {simplified_num}/{simplified_den}")
        else:
            steps.append(f"  {result_num}/{result_den} is already in simplest form")
        
        return steps
    
    def _prepare_chart_data(self, frac1, frac2, result, operation):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        # Fraction comparison chart
        try:
            decimal1 = float(frac1)
            decimal2 = float(frac2)
            decimal_result = float(result)
            
            chart_data['fraction_comparison'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Fraction 1', 'Fraction 2', 'Result'],
                    'datasets': [{
                        'label': 'Decimal Value',
                        'data': [decimal1, decimal2, decimal_result],
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
        except:
            pass
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            num1, den1, error1 = self._validate_fraction(
                data.get('num1', 1), 
                data.get('den1', 2), 
                'Fraction 1'
            )
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            num2, den2, error2 = self._validate_fraction(
                data.get('num2', 1), 
                data.get('den2', 4), 
                'Fraction 2'
            )
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            calc_type = data.get('calc_type', 'add')
            
            # Map operation
            operation_map = {
                'add': '+',
                'subtract': '-',
                'multiply': '×',
                'divide': '÷'
            }
            operation = operation_map.get(calc_type, '+')
            
            # Create SymPy Rationals for exact arithmetic
            try:
                frac1 = Rational(num1, den1)
                frac2 = Rational(num2, den2)
            except:
                return JsonResponse({'success': False, 'error': 'Invalid fraction values.'}, status=400)
            
            # Perform calculation
            if calc_type == 'add':
                result = frac1 + frac2
            elif calc_type == 'subtract':
                result = frac1 - frac2
            elif calc_type == 'multiply':
                result = frac1 * frac2
            elif calc_type == 'divide':
                if frac2 == 0:
                    return JsonResponse({'success': False, 'error': 'Cannot divide by zero.'}, status=400)
                result = frac1 / frac2
            else:
                return JsonResponse({'success': False, 'error': 'Invalid operation.'}, status=400)
            
            # Get result as fraction
            result_num = int(result.p)
            result_den = int(result.q)
            
            # Simplify result
            simplified_num, simplified_den = self._simplify_fraction(result_num, result_den)
            
            # Calculate decimal value
            try:
                decimal_value = float(result)
            except:
                decimal_value = 0.0
            
            # Get mixed number if applicable
            mixed_number = self._get_mixed_number(simplified_num, simplified_den)
            
            # Calculate GCD and LCM of original denominators
            common_gcd = self._get_gcd(den1, den2)
            common_lcm = self._get_lcm(den1, den2)
            
            # Calculate GCD and LCM of numerators
            num_gcd = self._get_gcd(num1, num2)
            num_lcm = self._get_lcm(num1, num2)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(
                num1, den1, num2, den2, operation,
                simplified_num, simplified_den, common_lcm
            )
            
            # Prepare chart data
            chart_data = self._prepare_chart_data(frac1, frac2, result, operation)
            
            # Additional fraction properties
            frac1_simplified_num, frac1_simplified_den = self._simplify_fraction(num1, den1)
            frac2_simplified_num, frac2_simplified_den = self._simplify_fraction(num2, den2)
            
            # Check if fractions are equivalent
            frac1_value = frac1_simplified_num / frac1_simplified_den if frac1_simplified_den != 0 else 0
            frac2_value = frac2_simplified_num / frac2_simplified_den if frac2_simplified_den != 0 else 0
            are_equivalent = abs(frac1_value - frac2_value) < 1e-10
            
            # Determine which fraction is larger
            comparison = None
            if abs(frac1_value - frac2_value) > 1e-10:
                if frac1_value > frac2_value:
                    comparison = 'Fraction 1 is greater than Fraction 2'
                else:
                    comparison = 'Fraction 2 is greater than Fraction 1'
            else:
                comparison = 'Fractions are equal'
            
            response = {
                'success': True,
                'fraction1': {
                    'numerator': num1,
                    'denominator': den1,
                    'formatted': f"{num1}/{den1}",
                    'simplified': f"{frac1_simplified_num}/{frac1_simplified_den}" if frac1_simplified_den != 1 else str(frac1_simplified_num),
                    'decimal': round(frac1_value, 8),
                    'percentage': round(frac1_value * 100, 4)
                },
                'fraction2': {
                    'numerator': num2,
                    'denominator': den2,
                    'formatted': f"{num2}/{den2}",
                    'simplified': f"{frac2_simplified_num}/{frac2_simplified_den}" if frac2_simplified_den != 1 else str(frac2_simplified_num),
                    'decimal': round(frac2_value, 8),
                    'percentage': round(frac2_value * 100, 4)
                },
                'operation': operation,
                'result': {
                    'numerator': simplified_num,
                    'denominator': simplified_den,
                    'formatted': f"{simplified_num}/{simplified_den}" if simplified_den != 1 else str(simplified_num),
                    'decimal': round(decimal_value, 8),
                    'percentage': round(decimal_value * 100, 4),
                    'unsimplified': f"{result_num}/{result_den}" if result_den != 1 else str(result_num)
                },
                'mixed_number': mixed_number,
                'lcm': common_lcm,
                'gcd': common_gcd,
                'num_gcd': num_gcd,
                'num_lcm': num_lcm,
                'step_by_step': step_by_step,
                'chart_data': chart_data,
                'are_equivalent': are_equivalent,
                'comparison': comparison,
                'expression': f"{num1}/{den1} {operation} {num2}/{den2}"
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Fraction Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
