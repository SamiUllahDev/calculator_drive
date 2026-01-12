from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from fractions import Fraction


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RatioCalculator(View):
    """
    Enhanced Professional Ratio Calculator
    Calculates ratios, simplifies them, finds missing values, and converts to percentages.
    """
    template_name = 'math_calculators/ratio_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Ratio Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num < 0:
                return None, f'{name} must be non-negative.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _simplify_ratio(self, a, b):
        """Simplify a ratio to its lowest terms"""
        if a == 0 and b == 0:
            return 1, 1
        
        if b == 0:
            return None, None
        
        if a == 0:
            return 0, 1
        
        # Use fractions to simplify
        try:
            frac = Fraction(int(a), int(b))
            return frac.numerator, frac.denominator
        except:
            # If integers don't work, use GCD
            common = math.gcd(int(a * 1000), int(b * 1000))
            if common == 0:
                return a, b
            simplified_a = (a * 1000) / common
            simplified_b = (b * 1000) / common
            return simplified_a, simplified_b
    
    def _calculate_ratio(self, calc_type, a=None, b=None, c=None, d=None, total=None):
        """Calculate ratio based on type"""
        if calc_type == 'simplify':
            # Simplify ratio a:b
            if a is None or b is None:
                return None, "Both values are required to simplify a ratio."
            if b == 0:
                return None, "Second value cannot be zero."
            simplified_a, simplified_b = self._simplify_ratio(a, b)
            return {
                'original_ratio': f"{a}:{b}",
                'simplified_ratio': f"{simplified_a}:{simplified_b}",
                'a': a,
                'b': b,
                'simplified_a': simplified_a,
                'simplified_b': simplified_b,
                'calc_type': 'simplify'
            }, None
        
        elif calc_type == 'find_missing':
            # Find missing value in ratio a:b = c:d
            if a is None and b is not None and c is not None and d is not None:
                # Find a: a = (b * c) / d
                if d == 0:
                    return None, "Value d cannot be zero."
                result = (b * c) / d
                return {
                    'a': result,
                    'b': b,
                    'c': c,
                    'd': d,
                    'missing': 'a',
                    'ratio1': f"{result}:{b}",
                    'ratio2': f"{c}:{d}",
                    'calc_type': 'find_missing'
                }, None
            elif b is None and a is not None and c is not None and d is not None:
                # Find b: b = (a * d) / c
                if c == 0:
                    return None, "Value c cannot be zero."
                result = (a * d) / c
                return {
                    'a': a,
                    'b': result,
                    'c': c,
                    'd': d,
                    'missing': 'b',
                    'ratio1': f"{a}:{result}",
                    'ratio2': f"{c}:{d}",
                    'calc_type': 'find_missing'
                }, None
            elif c is None and a is not None and b is not None and d is not None:
                # Find c: c = (a * d) / b
                if b == 0:
                    return None, "Value b cannot be zero."
                result = (a * d) / b
                return {
                    'a': a,
                    'b': b,
                    'c': result,
                    'd': d,
                    'missing': 'c',
                    'ratio1': f"{a}:{b}",
                    'ratio2': f"{result}:{d}",
                    'calc_type': 'find_missing'
                }, None
            elif d is None and a is not None and b is not None and c is not None:
                # Find d: d = (b * c) / a
                if a == 0:
                    return None, "Value a cannot be zero."
                result = (b * c) / a
                return {
                    'a': a,
                    'b': b,
                    'c': c,
                    'd': result,
                    'missing': 'd',
                    'ratio1': f"{a}:{b}",
                    'ratio2': f"{c}:{result}",
                    'calc_type': 'find_missing'
                }, None
            else:
                return None, "Exactly one value must be missing."
        
        elif calc_type == 'percentage':
            # Convert ratio a:b to percentages
            if a is None or b is None:
                return None, "Both values are required to convert ratio to percentage."
            if a + b == 0:
                return None, "Sum of values cannot be zero."
            percent_a = (a / (a + b)) * 100
            percent_b = (b / (a + b)) * 100
            return {
                'a': a,
                'b': b,
                'percent_a': percent_a,
                'percent_b': percent_b,
                'ratio': f"{a}:{b}",
                'calc_type': 'percentage'
            }, None
        
        elif calc_type == 'from_total':
            # Calculate ratio parts from total
            if total is None or a is None or b is None:
                return None, "Total and both ratio values are required."
            if a + b == 0:
                return None, "Sum of ratio values cannot be zero."
            part_a = (a / (a + b)) * total
            part_b = (b / (a + b)) * total
            return {
                'a': a,
                'b': b,
                'total': total,
                'part_a': part_a,
                'part_b': part_b,
                'ratio': f"{a}:{b}",
                'calc_type': 'from_total'
            }, None
        
        else:
            return None, "Invalid calculation type."
    
    def _prepare_step_by_step(self, result):
        """Prepare step-by-step solution"""
        steps = []
        calc_type = result['calc_type']
        
        if calc_type == 'simplify':
            steps.append(f"Given: Ratio {result['original_ratio']}")
            steps.append("")
            steps.append("Step 1: Find the Greatest Common Divisor (GCD)")
            steps.append(f"  GCD of {result['a']} and {result['b']}")
            steps.append("")
            steps.append("Step 2: Divide both terms by GCD")
            steps.append(f"  {result['a']} ÷ GCD = {result['simplified_a']}")
            steps.append(f"  {result['b']} ÷ GCD = {result['simplified_b']}")
            steps.append("")
            steps.append(f"Simplified Ratio: {result['simplified_ratio']}")
        
        elif calc_type == 'find_missing':
            missing = result['missing']
            steps.append(f"Given: {result['ratio1']} = {result['ratio2']}")
            steps.append(f"Find: {missing.upper()}")
            steps.append("")
            if missing == 'a':
                steps.append("Step 1: Cross multiply")
                steps.append(f"  a × {result['d']} = {result['b']} × {result['c']}")
                steps.append("")
                steps.append("Step 2: Solve for a")
                steps.append(f"  a = ({result['b']} × {result['c']}) / {result['d']}")
                steps.append(f"  a = {result['b'] * result['c']} / {result['d']}")
                steps.append(f"  a = {result['a']:.6f}")
            elif missing == 'b':
                steps.append("Step 1: Cross multiply")
                steps.append(f"  {result['a']} × {result['d']} = b × {result['c']}")
                steps.append("")
                steps.append("Step 2: Solve for b")
                steps.append(f"  b = ({result['a']} × {result['d']}) / {result['c']}")
                steps.append(f"  b = {result['a'] * result['d']} / {result['c']}")
                steps.append(f"  b = {result['b']:.6f}")
            elif missing == 'c':
                steps.append("Step 1: Cross multiply")
                steps.append(f"  {result['a']} × {result['d']} = {result['b']} × c")
                steps.append("")
                steps.append("Step 2: Solve for c")
                steps.append(f"  c = ({result['a']} × {result['d']}) / {result['b']}")
                steps.append(f"  c = {result['a'] * result['d']} / {result['b']}")
                steps.append(f"  c = {result['c']:.6f}")
            elif missing == 'd':
                steps.append("Step 1: Cross multiply")
                steps.append(f"  {result['a']} × d = {result['b']} × {result['c']}")
                steps.append("")
                steps.append("Step 2: Solve for d")
                steps.append(f"  d = ({result['b']} × {result['c']}) / {result['a']}")
                steps.append(f"  d = {result['b'] * result['c']} / {result['a']}")
                steps.append(f"  d = {result['d']:.6f}")
            steps.append("")
            steps.append(f"Result: {result['ratio1']} = {result['ratio2']}")
        
        elif calc_type == 'percentage':
            steps.append(f"Given: Ratio {result['ratio']}")
            steps.append("")
            steps.append("Step 1: Calculate total")
            steps.append(f"  Total = {result['a']} + {result['b']} = {result['a'] + result['b']}")
            steps.append("")
            steps.append("Step 2: Calculate percentages")
            steps.append(f"  Part A = ({result['a']} / {result['a'] + result['b']}) × 100")
            steps.append(f"  Part A = {result['percent_a']:.2f}%")
            steps.append("")
            steps.append(f"  Part B = ({result['b']} / {result['a'] + result['b']}) × 100")
            steps.append(f"  Part B = {result['percent_b']:.2f}%")
            steps.append("")
            steps.append(f"Verification: {result['percent_a']:.2f}% + {result['percent_b']:.2f}% = 100%")
        
        elif calc_type == 'from_total':
            steps.append(f"Given: Ratio {result['ratio']}, Total = {result['total']}")
            steps.append("")
            steps.append("Step 1: Calculate ratio sum")
            steps.append(f"  Ratio Sum = {result['a']} + {result['b']} = {result['a'] + result['b']}")
            steps.append("")
            steps.append("Step 2: Calculate parts")
            steps.append(f"  Part A = ({result['a']} / {result['a'] + result['b']}) × {result['total']}")
            steps.append(f"  Part A = {result['part_a']:.6f}")
            steps.append("")
            steps.append(f"  Part B = ({result['b']} / {result['a'] + result['b']}) × {result['total']}")
            steps.append(f"  Part B = {result['part_b']:.6f}")
            steps.append("")
            steps.append(f"Verification: {result['part_a']:.6f} + {result['part_b']:.6f} = {result['total']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            calc_type = result['calc_type']
            
            if calc_type == 'simplify':
                # Show original vs simplified ratio
                chart_data['ratio_comparison_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': ['Original', 'Simplified'],
                        'datasets': [
                            {
                                'label': 'First Value',
                                'data': [result['a'], result['simplified_a']],
                                'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                                'borderColor': '#3b82f6',
                                'borderWidth': 2
                            },
                            {
                                'label': 'Second Value',
                                'data': [result['b'], result['simplified_b']],
                                'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                                'borderColor': '#10b981',
                                'borderWidth': 2
                            }
                        ]
                    }
                }
            
            elif calc_type == 'percentage':
                # Pie chart for percentages
                chart_data['percentage_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': ['Part A', 'Part B'],
                        'datasets': [{
                            'data': [result['percent_a'], result['percent_b']],
                            'backgroundColor': [
                                'rgba(59, 130, 246, 0.8)',
                                'rgba(16, 185, 129, 0.8)'
                            ],
                            'borderColor': [
                                '#3b82f6',
                                '#10b981'
                            ],
                            'borderWidth': 2
                        }]
                    }
                }
            
            elif calc_type == 'from_total':
                # Bar chart showing parts
                chart_data['parts_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': ['Part A', 'Part B', 'Total'],
                        'datasets': [{
                            'label': 'Value',
                            'data': [result['part_a'], result['part_b'], result['total']],
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
            
            calc_type = data.get('calc_type', 'simplify')
            
            # Get inputs based on calculation type
            a = None
            b = None
            c = None
            d = None
            total = None
            
            if calc_type == 'simplify':
                a, error1 = self._validate_positive_number(data.get('a'), 'Value a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                b, error2 = self._validate_positive_number(data.get('b'), 'Value b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            elif calc_type == 'find_missing':
                a_val = data.get('a', '').strip()
                b_val = data.get('b', '').strip()
                c_val = data.get('c', '').strip()
                d_val = data.get('d', '').strip()
                
                if a_val:
                    a, error = self._validate_positive_number(a_val, 'Value a')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if b_val:
                    b, error = self._validate_positive_number(b_val, 'Value b')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if c_val:
                    c, error = self._validate_positive_number(c_val, 'Value c')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if d_val:
                    d, error = self._validate_positive_number(d_val, 'Value d')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
            
            elif calc_type == 'percentage':
                a, error1 = self._validate_positive_number(data.get('a'), 'Value a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                b, error2 = self._validate_positive_number(data.get('b'), 'Value b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            elif calc_type == 'from_total':
                a, error1 = self._validate_positive_number(data.get('a'), 'Value a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                b, error2 = self._validate_positive_number(data.get('b'), 'Value b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                total, error3 = self._validate_positive_number(data.get('total'), 'Total')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
            
            # Calculate ratio
            result, error = self._calculate_ratio(calc_type, a, b, c, d, total)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(result)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                **result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Ratio Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
