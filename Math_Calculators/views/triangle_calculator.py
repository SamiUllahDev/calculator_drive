from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TriangleCalculator(View):
    """
    Enhanced Professional Triangle Calculator
    Calculates triangle properties (sides, angles, area, perimeter) with step-by-step solutions.
    Supports SSS, SAS, ASA, AAS, SSA calculation modes.
    """
    template_name = 'math_calculators/triangle_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Triangle Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0:
                return None, f'{name} must be greater than zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _validate_angle(self, value, name):
        """Validate that an angle is between 0 and 180 degrees"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0 or num >= 180:
                return None, f'{name} must be between 0 and 180 degrees.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _degrees_to_radians(self, degrees):
        """Convert degrees to radians"""
        return degrees * math.pi / 180
    
    def _radians_to_degrees(self, radians):
        """Convert radians to degrees"""
        return radians * 180 / math.pi
    
    def _calculate_sss(self, a, b, c):
        """Calculate triangle from three sides (SSS)"""
        # Check triangle inequality
        if a + b <= c or a + c <= b or b + c <= a:
            return None, "Invalid triangle: sum of any two sides must be greater than the third side."
        
        # Calculate angles using Law of Cosines
        angle_a = self._radians_to_degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
        angle_b = self._radians_to_degrees(math.acos((a**2 + c**2 - b**2) / (2 * a * c)))
        angle_c = self._radians_to_degrees(math.acos((a**2 + b**2 - c**2) / (2 * a * b)))
        
        # Calculate area using Heron's formula
        s = (a + b + c) / 2
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        
        perimeter = a + b + c
        
        return {
            'a': a, 'b': b, 'c': c,
            'angle_a': angle_a, 'angle_b': angle_b, 'angle_c': angle_c,
            'area': area, 'perimeter': perimeter,
            'semiperimeter': s
        }, None
    
    def _calculate_sas(self, a, angle_b, c):
        """Calculate triangle from two sides and included angle (SAS)"""
        # Calculate side b using Law of Cosines
        angle_b_rad = self._degrees_to_radians(angle_b)
        b = math.sqrt(a**2 + c**2 - 2 * a * c * math.cos(angle_b_rad))
        
        # Calculate remaining angles using Law of Cosines
        angle_a = self._radians_to_degrees(math.acos((b**2 + c**2 - a**2) / (2 * b * c)))
        angle_c = self._radians_to_degrees(math.acos((a**2 + b**2 - c**2) / (2 * a * b)))
        
        # Calculate area
        area = 0.5 * a * c * math.sin(angle_b_rad)
        
        perimeter = a + b + c
        s = perimeter / 2
        
        return {
            'a': a, 'b': b, 'c': c,
            'angle_a': angle_a, 'angle_b': angle_b, 'angle_c': angle_c,
            'area': area, 'perimeter': perimeter,
            'semiperimeter': s
        }, None
    
    def _calculate_asa(self, angle_a, c, angle_b):
        """Calculate triangle from two angles and included side (ASA)"""
        # Calculate third angle
        angle_c = 180 - angle_a - angle_b
        if angle_c <= 0:
            return None, "Invalid triangle: sum of angles must be less than 180 degrees."
        
        # Calculate sides using Law of Sines
        angle_a_rad = self._degrees_to_radians(angle_a)
        angle_b_rad = self._degrees_to_radians(angle_b)
        angle_c_rad = self._degrees_to_radians(angle_c)
        
        a = c * math.sin(angle_a_rad) / math.sin(angle_c_rad)
        b = c * math.sin(angle_b_rad) / math.sin(angle_c_rad)
        
        # Calculate area
        area = 0.5 * a * b * math.sin(angle_c_rad)
        
        perimeter = a + b + c
        s = perimeter / 2
        
        return {
            'a': a, 'b': b, 'c': c,
            'angle_a': angle_a, 'angle_b': angle_b, 'angle_c': angle_c,
            'area': area, 'perimeter': perimeter,
            'semiperimeter': s
        }, None
    
    def _calculate_aas(self, angle_a, angle_b, a):
        """Calculate triangle from two angles and non-included side (AAS)"""
        # Calculate third angle
        angle_c = 180 - angle_a - angle_b
        if angle_c <= 0:
            return None, "Invalid triangle: sum of angles must be less than 180 degrees."
        
        # Calculate sides using Law of Sines
        angle_a_rad = self._degrees_to_radians(angle_a)
        angle_b_rad = self._degrees_to_radians(angle_b)
        angle_c_rad = self._degrees_to_radians(angle_c)
        
        b = a * math.sin(angle_b_rad) / math.sin(angle_a_rad)
        c = a * math.sin(angle_c_rad) / math.sin(angle_a_rad)
        
        # Calculate area
        area = 0.5 * a * b * math.sin(angle_c_rad)
        
        perimeter = a + b + c
        s = perimeter / 2
        
        return {
            'a': a, 'b': b, 'c': c,
            'angle_a': angle_a, 'angle_b': angle_b, 'angle_c': angle_c,
            'area': area, 'perimeter': perimeter,
            'semiperimeter': s
        }, None
    
    def _calculate_ssa(self, a, b, angle_a):
        """Calculate triangle from two sides and non-included angle (SSA - ambiguous case)"""
        angle_a_rad = self._degrees_to_radians(angle_a)
        
        # Calculate height
        h = b * math.sin(angle_a_rad)
        
        # Check for ambiguous case
        if a < h:
            return None, "No triangle exists: side a is too short."
        elif abs(a - h) < 1e-10:
            # Right triangle case
            angle_b = 90
            angle_c = 180 - angle_a - angle_b
            angle_c_rad = self._degrees_to_radians(angle_c)
            c = math.sqrt(a**2 - h**2) + math.sqrt(b**2 - h**2)
            area = 0.5 * a * b * math.sin(angle_c_rad)
        elif a > b:
            # One solution
            angle_b = self._radians_to_degrees(math.asin(b * math.sin(angle_a_rad) / a))
            angle_c = 180 - angle_a - angle_b
            angle_c_rad = self._degrees_to_radians(angle_c)
            c = a * math.sin(angle_c_rad) / math.sin(angle_a_rad)
            area = 0.5 * a * b * math.sin(angle_c_rad)
        else:
            # Two possible solutions (ambiguous case)
            # We'll return the acute angle solution
            angle_b = self._radians_to_degrees(math.asin(b * math.sin(angle_a_rad) / a))
            angle_c = 180 - angle_a - angle_b
            angle_c_rad = self._degrees_to_radians(angle_c)
            c = a * math.sin(angle_c_rad) / math.sin(angle_a_rad)
            area = 0.5 * a * b * math.sin(angle_c_rad)
        
        perimeter = a + b + c
        s = perimeter / 2
        
        return {
            'a': a, 'b': b, 'c': c,
            'angle_a': angle_a, 'angle_b': angle_b, 'angle_c': angle_c,
            'area': area, 'perimeter': perimeter,
            'semiperimeter': s
        }, None
    
    def _prepare_step_by_step(self, mode, result, inputs):
        """Prepare step-by-step solution"""
        steps = []
        
        mode_names = {
            'SSS': 'Side-Side-Side (SSS)',
            'SAS': 'Side-Angle-Side (SAS)',
            'ASA': 'Angle-Side-Angle (ASA)',
            'AAS': 'Angle-Angle-Side (AAS)',
            'SSA': 'Side-Side-Angle (SSA)'
        }
        
        steps.append(f"Given: {mode_names.get(mode, mode)}")
        steps.append("")
        
        if mode == 'SSS':
            a, b, c = inputs['a'], inputs['b'], inputs['c']
            steps.append(f"  Side a = {a}")
            steps.append(f"  Side b = {b}")
            steps.append(f"  Side c = {c}")
            steps.append("")
            steps.append("Step 1: Verify triangle inequality")
            steps.append(f"  a + b > c: {a} + {b} = {a+b} > {c} ✓")
            steps.append(f"  a + c > b: {a} + {c} = {a+c} > {b} ✓")
            steps.append(f"  b + c > a: {b} + {c} = {b+c} > {a} ✓")
            steps.append("")
            steps.append("Step 2: Calculate angles using Law of Cosines")
            steps.append(f"  Angle A = arccos((b² + c² - a²) / (2bc))")
            steps.append(f"  Angle A = arccos(({b}² + {c}² - {a}²) / (2 × {b} × {c}))")
            steps.append(f"  Angle A = {result['angle_a']:.6f}°")
            steps.append("")
            steps.append(f"  Angle B = arccos((a² + c² - b²) / (2ac))")
            steps.append(f"  Angle B = arccos(({a}² + {c}² - {b}²) / (2 × {a} × {c}))")
            steps.append(f"  Angle B = {result['angle_b']:.6f}°")
            steps.append("")
            steps.append(f"  Angle C = arccos((a² + b² - c²) / (2ab))")
            steps.append(f"  Angle C = arccos(({a}² + {b}² - {c}²) / (2 × {a} × {b}))")
            steps.append(f"  Angle C = {result['angle_c']:.6f}°")
            steps.append("")
            steps.append("Step 3: Calculate area using Heron's formula")
            steps.append(f"  s = (a + b + c) / 2 = ({a} + {b} + {c}) / 2 = {result['semiperimeter']}")
            steps.append(f"  Area = √[s(s-a)(s-b)(s-c)]")
            steps.append(f"  Area = √[{result['semiperimeter']}({result['semiperimeter']}-{a})({result['semiperimeter']}-{b})({result['semiperimeter']}-{c})]")
            steps.append(f"  Area = {result['area']:.6f}")
        
        elif mode == 'SAS':
            a, angle_b, c = inputs['a'], inputs['angle_b'], inputs['c']
            steps.append(f"  Side a = {a}")
            steps.append(f"  Angle B = {angle_b}°")
            steps.append(f"  Side c = {c}")
            steps.append("")
            steps.append("Step 1: Calculate side b using Law of Cosines")
            steps.append(f"  b² = a² + c² - 2ac cos(B)")
            steps.append(f"  b² = {a}² + {c}² - 2 × {a} × {c} × cos({angle_b}°)")
            steps.append(f"  b = {result['b']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate remaining angles using Law of Cosines")
            steps.append(f"  Angle A = {result['angle_a']:.6f}°")
            steps.append(f"  Angle C = {result['angle_c']:.6f}°")
            steps.append("")
            steps.append("Step 3: Calculate area")
            steps.append(f"  Area = 0.5 × a × c × sin(B)")
            steps.append(f"  Area = 0.5 × {a} × {c} × sin({angle_b}°)")
            steps.append(f"  Area = {result['area']:.6f}")
        
        elif mode == 'ASA':
            angle_a, c, angle_b = inputs['angle_a'], inputs['c'], inputs['angle_b']
            steps.append(f"  Angle A = {angle_a}°")
            steps.append(f"  Side c = {c}")
            steps.append(f"  Angle B = {angle_b}°")
            steps.append("")
            steps.append("Step 1: Calculate third angle")
            steps.append(f"  Angle C = 180° - A - B = 180° - {angle_a}° - {angle_b}° = {result['angle_c']:.6f}°")
            steps.append("")
            steps.append("Step 2: Calculate sides using Law of Sines")
            steps.append(f"  a / sin(A) = c / sin(C)")
            steps.append(f"  a = c × sin(A) / sin(C) = {c} × sin({angle_a}°) / sin({result['angle_c']:.6f}°)")
            steps.append(f"  a = {result['a']:.6f}")
            steps.append("")
            steps.append(f"  b / sin(B) = c / sin(C)")
            steps.append(f"  b = c × sin(B) / sin(C) = {c} × sin({angle_b}°) / sin({result['angle_c']:.6f}°)")
            steps.append(f"  b = {result['b']:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate area")
            steps.append(f"  Area = 0.5 × a × b × sin(C)")
            steps.append(f"  Area = 0.5 × {result['a']:.6f} × {result['b']:.6f} × sin({result['angle_c']:.6f}°)")
            steps.append(f"  Area = {result['area']:.6f}")
        
        elif mode == 'AAS':
            angle_a, angle_b, a = inputs['angle_a'], inputs['angle_b'], inputs['a']
            steps.append(f"  Angle A = {angle_a}°")
            steps.append(f"  Angle B = {angle_b}°")
            steps.append(f"  Side a = {a}")
            steps.append("")
            steps.append("Step 1: Calculate third angle")
            steps.append(f"  Angle C = 180° - A - B = 180° - {angle_a}° - {angle_b}° = {result['angle_c']:.6f}°")
            steps.append("")
            steps.append("Step 2: Calculate sides using Law of Sines")
            steps.append(f"  a / sin(A) = b / sin(B)")
            steps.append(f"  b = a × sin(B) / sin(A) = {a} × sin({angle_b}°) / sin({angle_a}°)")
            steps.append(f"  b = {result['b']:.6f}")
            steps.append("")
            steps.append(f"  a / sin(A) = c / sin(C)")
            steps.append(f"  c = a × sin(C) / sin(A) = {a} × sin({result['angle_c']:.6f}°) / sin({angle_a}°)")
            steps.append(f"  c = {result['c']:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate area")
            steps.append(f"  Area = 0.5 × a × b × sin(C)")
            steps.append(f"  Area = 0.5 × {result['a']:.6f} × {result['b']:.6f} × sin({result['angle_c']:.6f}°)")
            steps.append(f"  Area = {result['area']:.6f}")
        
        elif mode == 'SSA':
            a, b, angle_a = inputs['a'], inputs['b'], inputs['angle_a']
            steps.append(f"  Side a = {a}")
            steps.append(f"  Side b = {b}")
            steps.append(f"  Angle A = {angle_a}°")
            steps.append("")
            steps.append("Step 1: Calculate angle B using Law of Sines")
            steps.append(f"  a / sin(A) = b / sin(B)")
            steps.append(f"  sin(B) = b × sin(A) / a = {b} × sin({angle_a}°) / {a}")
            steps.append(f"  Angle B = {result['angle_b']:.6f}°")
            steps.append("")
            steps.append("Step 2: Calculate third angle")
            steps.append(f"  Angle C = 180° - A - B = 180° - {angle_a}° - {result['angle_b']:.6f}° = {result['angle_c']:.6f}°")
            steps.append("")
            steps.append("Step 3: Calculate side c using Law of Sines")
            steps.append(f"  a / sin(A) = c / sin(C)")
            steps.append(f"  c = a × sin(C) / sin(A) = {a} × sin({result['angle_c']:.6f}°) / sin({angle_a}°)")
            steps.append(f"  c = {result['c']:.6f}")
            steps.append("")
            steps.append("Step 4: Calculate area")
            steps.append(f"  Area = 0.5 × a × b × sin(C)")
            steps.append(f"  Area = 0.5 × {result['a']:.6f} × {result['b']:.6f} × sin({result['angle_c']:.6f}°)")
            steps.append(f"  Area = {result['area']:.6f}")
        
        steps.append("")
        steps.append("Step 4: Calculate perimeter")
        steps.append(f"  Perimeter = a + b + c = {result['a']:.6f} + {result['b']:.6f} + {result['c']:.6f} = {result['perimeter']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Sides comparison chart
            chart_data['sides_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Side a', 'Side b', 'Side c'],
                    'datasets': [{
                        'label': 'Side Length',
                        'data': [result['a'], result['b'], result['c']],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
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
            
            # Angles comparison chart
            chart_data['angles_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': ['Angle A', 'Angle B', 'Angle C'],
                    'datasets': [{
                        'data': [result['angle_a'], result['angle_b'], result['angle_c']],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
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
            
            mode = data.get('mode', 'SSS')
            inputs = {}
            result = None
            error = None
            
            if mode == 'SSS':
                a, err1 = self._validate_positive_number(data.get('a'), 'Side a')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                b, err2 = self._validate_positive_number(data.get('b'), 'Side b')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                c, err3 = self._validate_positive_number(data.get('c'), 'Side c')
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                inputs = {'a': a, 'b': b, 'c': c}
                result, error = self._calculate_sss(a, b, c)
            
            elif mode == 'SAS':
                a, err1 = self._validate_positive_number(data.get('a'), 'Side a')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                angle_b, err2 = self._validate_angle(data.get('angle_b'), 'Angle B')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                c, err3 = self._validate_positive_number(data.get('c'), 'Side c')
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                inputs = {'a': a, 'angle_b': angle_b, 'c': c}
                result, error = self._calculate_sas(a, angle_b, c)
            
            elif mode == 'ASA':
                angle_a, err1 = self._validate_angle(data.get('angle_a'), 'Angle A')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                c, err2 = self._validate_positive_number(data.get('c'), 'Side c')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                angle_b, err3 = self._validate_angle(data.get('angle_b'), 'Angle B')
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                inputs = {'angle_a': angle_a, 'c': c, 'angle_b': angle_b}
                result, error = self._calculate_asa(angle_a, c, angle_b)
            
            elif mode == 'AAS':
                angle_a, err1 = self._validate_angle(data.get('angle_a'), 'Angle A')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                angle_b, err2 = self._validate_angle(data.get('angle_b'), 'Angle B')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                a, err3 = self._validate_positive_number(data.get('a'), 'Side a')
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                inputs = {'angle_a': angle_a, 'angle_b': angle_b, 'a': a}
                result, error = self._calculate_aas(angle_a, angle_b, a)
            
            elif mode == 'SSA':
                a, err1 = self._validate_positive_number(data.get('a'), 'Side a')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                b, err2 = self._validate_positive_number(data.get('b'), 'Side b')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                angle_a, err3 = self._validate_angle(data.get('angle_a'), 'Angle A')
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                inputs = {'a': a, 'b': b, 'angle_a': angle_a}
                result, error = self._calculate_ssa(a, b, angle_a)
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation mode.'}, status=400)
            
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(mode, result, inputs)
            
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
                'mode': mode,
                **result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Triangle Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
