from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RightTriangleCalculator(View):
    """
    Enhanced Professional Right Triangle Calculator
    Calculates missing sides, angles, area, and perimeter of right triangles.
    """
    template_name = 'math_calculators/right_triangle_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Right Triangle Calculator',
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
        """Validate that a value is a valid angle (0-90 degrees)"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0 or num >= 90:
                return None, f'{name} must be between 0 and 90 degrees.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_triangle(self, calc_type, a=None, b=None, c=None, angle_a=None, angle_b=None):
        """Calculate right triangle properties"""
        if calc_type == 'find_side':
            # Find missing side using Pythagorean theorem
            if a is None and b is not None and c is not None:
                # Find a: a = √(c² - b²)
                if c <= b:
                    return None, "Hypotenuse c must be greater than side b."
                a = math.sqrt(c**2 - b**2)
            elif b is None and a is not None and c is not None:
                # Find b: b = √(c² - a²)
                if c <= a:
                    return None, "Hypotenuse c must be greater than side a."
                b = math.sqrt(c**2 - a**2)
            elif c is None and a is not None and b is not None:
                # Find c: c = √(a² + b²)
                c = math.sqrt(a**2 + b**2)
            else:
                return None, "Exactly one side must be missing."
            
            # Calculate angles
            angle_a = math.degrees(math.asin(a / c))
            angle_b = math.degrees(math.asin(b / c))
        
        elif calc_type == 'find_angle':
            # Find missing angle
            if angle_a is None and angle_b is not None:
                angle_a = 90 - angle_b
            elif angle_b is None and angle_a is not None:
                angle_b = 90 - angle_a
            else:
                return None, "Exactly one angle must be missing."
            
            # Need at least one side to calculate other sides
            if a is None and b is None and c is None:
                return None, "At least one side is required to calculate triangle dimensions."
            
            # Calculate sides using trigonometry
            if c is not None:
                # Hypotenuse known
                if a is None:
                    a = c * math.sin(math.radians(angle_a))
                if b is None:
                    b = c * math.cos(math.radians(angle_a))
            elif a is not None:
                # Side a known
                if c is None:
                    c = a / math.sin(math.radians(angle_a))
                if b is None:
                    b = a / math.tan(math.radians(angle_a))
            elif b is not None:
                # Side b known
                if c is None:
                    c = b / math.cos(math.radians(angle_a))
                if a is None:
                    a = b * math.tan(math.radians(angle_a))
        
        elif calc_type == 'from_sides':
            # Calculate all properties from two sides
            if a is None or b is None:
                return None, "Both sides a and b are required."
            
            # Calculate hypotenuse
            c = math.sqrt(a**2 + b**2)
            
            # Calculate angles
            angle_a = math.degrees(math.asin(a / c))
            angle_b = math.degrees(math.asin(b / c))
        
        elif calc_type == 'from_angle_side':
            # Calculate from one angle and one side
            if angle_a is None:
                return None, "Angle A is required."
            
            if a is not None:
                # Side a known
                c = a / math.sin(math.radians(angle_a))
                b = a / math.tan(math.radians(angle_a))
            elif b is not None:
                # Side b known
                c = b / math.cos(math.radians(angle_a))
                a = b * math.tan(math.radians(angle_a))
            elif c is not None:
                # Hypotenuse known
                a = c * math.sin(math.radians(angle_a))
                b = c * math.cos(math.radians(angle_a))
            else:
                return None, "At least one side is required."
            
            angle_b = 90 - angle_a
        
        # Calculate area and perimeter
        area = 0.5 * a * b
        perimeter = a + b + c
        
        # Calculate other properties
        height = b  # Height from right angle to hypotenuse
        base = a
        
        return {
            'a': a,
            'b': b,
            'c': c,
            'angle_a': angle_a,
            'angle_b': angle_b,
            'angle_c': 90.0,
            'area': area,
            'perimeter': perimeter,
            'height': height,
            'base': base,
            'calc_type': calc_type
        }, None
    
    def _prepare_step_by_step(self, result):
        """Prepare step-by-step solution"""
        steps = []
        calc_type = result['calc_type']
        a = result['a']
        b = result['b']
        c = result['c']
        angle_a = result['angle_a']
        angle_b = result['angle_b']
        
        steps.append("Given: Right triangle (one angle = 90°)")
        steps.append("")
        
        if calc_type == 'find_side':
            steps.append("Step 1: Apply Pythagorean Theorem")
            steps.append("  Formula: a² + b² = c² (where c is the hypotenuse)")
            steps.append("")
            steps.append("Step 2: Calculate missing side")
            if c is None:
                steps.append(f"  c = √(a² + b²)")
                steps.append(f"  c = √({a}² + {b}²)")
                steps.append(f"  c = √({a**2} + {b**2})")
                steps.append(f"  c = √{a**2 + b**2:.6f}")
                steps.append(f"  c = {c:.6f}")
            elif a is None:
                steps.append(f"  a = √(c² - b²)")
                steps.append(f"  a = √({c}² - {b}²)")
                steps.append(f"  a = √({c**2} - {b**2})")
                steps.append(f"  a = √{c**2 - b**2:.6f}")
                steps.append(f"  a = {a:.6f}")
            else:
                steps.append(f"  b = √(c² - a²)")
                steps.append(f"  b = √({c}² - {a}²)")
                steps.append(f"  b = √({c**2} - {a**2})")
                steps.append(f"  b = √{c**2 - a**2:.6f}")
                steps.append(f"  b = {b:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate angles using trigonometry")
            steps.append(f"  sin(A) = a/c = {a}/{c} = {a/c:.6f}")
            steps.append(f"  A = arcsin({a/c:.6f}) = {angle_a:.6f}°")
            steps.append("")
            steps.append(f"  sin(B) = b/c = {b}/{c} = {b/c:.6f}")
            steps.append(f"  B = arcsin({b/c:.6f}) = {angle_b:.6f}°")
        
        elif calc_type == 'find_angle':
            steps.append("Step 1: Use triangle angle sum")
            steps.append("  A + B + C = 180°")
            steps.append("  A + B + 90° = 180°")
            steps.append("  A + B = 90°")
            steps.append("")
            if angle_a is None:
                steps.append(f"  A = 90° - B = 90° - {angle_b}° = {angle_a:.6f}°")
            else:
                steps.append(f"  B = 90° - A = 90° - {angle_a}° = {angle_b:.6f}°")
            steps.append("")
            steps.append("Step 2: Calculate sides using trigonometry")
            if c is not None:
                steps.append(f"  a = c × sin(A) = {c} × sin({angle_a}°) = {a:.6f}")
                steps.append(f"  b = c × cos(A) = {c} × cos({angle_a}°) = {b:.6f}")
            elif a is not None:
                steps.append(f"  c = a / sin(A) = {a} / sin({angle_a}°) = {c:.6f}")
                steps.append(f"  b = a / tan(A) = {a} / tan({angle_a}°) = {b:.6f}")
            elif b is not None:
                steps.append(f"  c = b / cos(A) = {b} / cos({angle_a}°) = {c:.6f}")
                steps.append(f"  a = b × tan(A) = {b} × tan({angle_a}°) = {a:.6f}")
        
        elif calc_type == 'from_sides':
            steps.append(f"Given: Side a = {a}, Side b = {b}")
            steps.append("")
            steps.append("Step 1: Calculate hypotenuse using Pythagorean Theorem")
            steps.append(f"  c = √(a² + b²) = √({a}² + {b}²) = √{a**2 + b**2:.6f} = {c:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate angles")
            steps.append(f"  A = arcsin(a/c) = arcsin({a}/{c}) = {angle_a:.6f}°")
            steps.append(f"  B = arcsin(b/c) = arcsin({b}/{c}) = {angle_b:.6f}°")
        
        elif calc_type == 'from_angle_side':
            steps.append(f"Given: Angle A = {angle_a}°, and one side")
            steps.append("")
            steps.append("Step 1: Calculate other angle")
            steps.append(f"  B = 90° - A = 90° - {angle_a}° = {angle_b:.6f}°")
            steps.append("")
            steps.append("Step 2: Calculate sides using trigonometry")
            if a is not None:
                steps.append(f"  c = a / sin(A) = {a} / sin({angle_a}°) = {c:.6f}")
                steps.append(f"  b = a / tan(A) = {a} / tan({angle_a}°) = {b:.6f}")
            elif b is not None:
                steps.append(f"  c = b / cos(A) = {b} / cos({angle_a}°) = {c:.6f}")
                steps.append(f"  a = b × tan(A) = {b} × tan({angle_a}°) = {a:.6f}")
            elif c is not None:
                steps.append(f"  a = c × sin(A) = {c} × sin({angle_a}°) = {a:.6f}")
                steps.append(f"  b = c × cos(A) = {c} × cos({angle_a}°) = {b:.6f}")
        
        steps.append("")
        steps.append("Step 3: Calculate area and perimeter")
        steps.append(f"  Area = (1/2) × a × b = (1/2) × {a} × {b} = {result['area']:.6f}")
        steps.append(f"  Perimeter = a + b + c = {a} + {b} + {c} = {result['perimeter']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, a, b, c, angle_a, angle_b):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Side lengths comparison
            chart_data['sides_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Side a', 'Side b', 'Hypotenuse c'],
                    'datasets': [{
                        'label': 'Length',
                        'data': [a, b, c],
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
            
            # Angles comparison
            chart_data['angles_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Angle A', 'Angle B', 'Angle C (90°)'],
                    'datasets': [{
                        'label': 'Degrees',
                        'data': [angle_a, angle_b, 90],
                        'backgroundColor': [
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(236, 72, 153, 0.6)',
                            'rgba(139, 92, 246, 0.6)'
                        ],
                        'borderColor': [
                            '#f59e0b',
                            '#ec4899',
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
            
            calc_type = data.get('calc_type', 'from_sides')
            
            # Get inputs based on calculation type
            a = None
            b = None
            c = None
            angle_a = None
            angle_b = None
            
            if calc_type == 'find_side':
                a_val = data.get('a', '').strip()
                b_val = data.get('b', '').strip()
                c_val = data.get('c', '').strip()
                
                if a_val:
                    a, error = self._validate_positive_number(a_val, 'Side a')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if b_val:
                    b, error = self._validate_positive_number(b_val, 'Side b')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if c_val:
                    c, error = self._validate_positive_number(c_val, 'Hypotenuse c')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
            
            elif calc_type == 'find_angle':
                angle_a_val = data.get('angle_a', '').strip()
                angle_b_val = data.get('angle_b', '').strip()
                a_val = data.get('a', '').strip()
                b_val = data.get('b', '').strip()
                c_val = data.get('c', '').strip()
                
                if angle_a_val:
                    angle_a, error = self._validate_angle(angle_a_val, 'Angle A')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if angle_b_val:
                    angle_b, error = self._validate_angle(angle_b_val, 'Angle B')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if a_val:
                    a, error = self._validate_positive_number(a_val, 'Side a')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if b_val:
                    b, error = self._validate_positive_number(b_val, 'Side b')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if c_val:
                    c, error = self._validate_positive_number(c_val, 'Hypotenuse c')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
            
            elif calc_type == 'from_sides':
                a, error1 = self._validate_positive_number(data.get('a'), 'Side a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                b, error2 = self._validate_positive_number(data.get('b'), 'Side b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
            
            elif calc_type == 'from_angle_side':
                angle_a, error1 = self._validate_angle(data.get('angle_a'), 'Angle A')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                a_val = data.get('a', '').strip()
                b_val = data.get('b', '').strip()
                c_val = data.get('c', '').strip()
                
                if a_val:
                    a, error = self._validate_positive_number(a_val, 'Side a')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if b_val:
                    b, error = self._validate_positive_number(b_val, 'Side b')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                
                if c_val:
                    c, error = self._validate_positive_number(c_val, 'Hypotenuse c')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate triangle
            result, error = self._calculate_triangle(calc_type, a, b, c, angle_a, angle_b)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(result['a'], result['b'], result['c'], 
                                                     result['angle_a'], result['angle_b'])
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
            print(f"Right Triangle Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
