from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SurfaceAreaCalculator(View):
    """
    Enhanced Professional Surface Area Calculator
    Calculates surface area for various 3D shapes with step-by-step solutions.
    """
    template_name = 'math_calculators/surface_area_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Surface Area Calculator',
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
    
    def _calculate_surface_area(self, shape_type, **kwargs):
        """Calculate surface area based on shape type"""
        if shape_type == 'cube':
            # Cube: SA = 6a²
            a = kwargs.get('a')
            if a is None:
                return None, "Side length (a) is required."
            surface_area = 6 * a ** 2
            return {
                'surface_area': surface_area,
                'a': a,
                'formula': 'SA = 6a²',
                'calculation': f'SA = 6 × {a}² = 6 × {a**2} = {surface_area}'
            }, None
        
        elif shape_type == 'sphere':
            # Sphere: SA = 4πr²
            r = kwargs.get('r')
            if r is None:
                return None, "Radius (r) is required."
            surface_area = 4 * math.pi * r ** 2
            return {
                'surface_area': surface_area,
                'r': r,
                'formula': 'SA = 4πr²',
                'calculation': f'SA = 4π × {r}² = 4π × {r**2} = {surface_area:.6f}'
            }, None
        
        elif shape_type == 'cylinder':
            # Cylinder: SA = 2πr² + 2πrh = 2πr(r + h)
            r = kwargs.get('r')
            h = kwargs.get('h')
            if r is None or h is None:
                return None, "Both radius (r) and height (h) are required."
            surface_area = 2 * math.pi * r * (r + h)
            base_area = math.pi * r ** 2
            lateral_area = 2 * math.pi * r * h
            return {
                'surface_area': surface_area,
                'r': r,
                'h': h,
                'base_area': base_area,
                'lateral_area': lateral_area,
                'formula': 'SA = 2πr² + 2πrh = 2πr(r + h)',
                'calculation': f'SA = 2π × {r} × ({r} + {h}) = 2π × {r} × {r+h} = {surface_area:.6f}'
            }, None
        
        elif shape_type == 'cone':
            # Cone: SA = πr² + πrl = πr(r + l)
            r = kwargs.get('r')
            h = kwargs.get('h')
            l = kwargs.get('l')
            if r is None:
                return None, "Radius (r) is required."
            if l is None and h is None:
                return None, "Either height (h) or slant height (l) is required."
            if l is None:
                # Calculate slant height from height
                l = math.sqrt(r ** 2 + h ** 2)
            base_area = math.pi * r ** 2
            lateral_area = math.pi * r * l
            surface_area = base_area + lateral_area
            return {
                'surface_area': surface_area,
                'r': r,
                'h': h if h is not None else None,
                'l': l,
                'base_area': base_area,
                'lateral_area': lateral_area,
                'formula': 'SA = πr² + πrl = πr(r + l)',
                'calculation': f'SA = π × {r}² + π × {r} × {l:.6f} = {base_area:.6f} + {lateral_area:.6f} = {surface_area:.6f}'
            }, None
        
        elif shape_type == 'rectangular_prism':
            # Rectangular Prism: SA = 2(lw + lh + wh)
            l = kwargs.get('l')
            w = kwargs.get('w')
            h = kwargs.get('h')
            if l is None or w is None or h is None:
                return None, "Length (l), width (w), and height (h) are required."
            surface_area = 2 * (l * w + l * h + w * h)
            return {
                'surface_area': surface_area,
                'l': l,
                'w': w,
                'h': h,
                'formula': 'SA = 2(lw + lh + wh)',
                'calculation': f'SA = 2({l}×{w} + {l}×{h} + {w}×{h}) = 2({l*w} + {l*h} + {w*h}) = {surface_area}'
            }, None
        
        elif shape_type == 'triangular_prism':
            # Triangular Prism: SA = 2B + Ph (B = base area, P = perimeter of base, h = height)
            a = kwargs.get('a')  # Base side
            b = kwargs.get('b')  # Base side
            c = kwargs.get('c')  # Base side
            h = kwargs.get('h')  # Height of prism
            base_h = kwargs.get('base_h')  # Height of triangular base
            if a is None or b is None or c is None or h is None or base_h is None:
                return None, "All dimensions are required for triangular prism."
            # Using Heron's formula for base area
            s = (a + b + c) / 2
            base_area = math.sqrt(s * (s - a) * (s - b) * (s - c))
            perimeter = a + b + c
            lateral_area = perimeter * h
            surface_area = 2 * base_area + lateral_area
            return {
                'surface_area': surface_area,
                'a': a,
                'b': b,
                'c': c,
                'h': h,
                'base_h': base_h,
                'base_area': base_area,
                'lateral_area': lateral_area,
                'formula': 'SA = 2B + Ph',
                'calculation': f'SA = 2 × {base_area:.6f} + {perimeter} × {h} = {surface_area:.6f}'
            }, None
        
        elif shape_type == 'pyramid':
            # Square Pyramid: SA = a² + 2al
            a = kwargs.get('a')  # Base side
            h = kwargs.get('h')  # Height
            l = kwargs.get('l')  # Slant height
            if a is None:
                return None, "Base side (a) is required."
            if l is None and h is None:
                return None, "Either height (h) or slant height (l) is required."
            if l is None:
                l = math.sqrt((a/2)**2 + h**2)
            base_area = a ** 2
            lateral_area = 2 * a * l
            surface_area = base_area + lateral_area
            return {
                'surface_area': surface_area,
                'a': a,
                'h': h if h is not None else None,
                'l': l,
                'base_area': base_area,
                'lateral_area': lateral_area,
                'formula': 'SA = a² + 2al',
                'calculation': f'SA = {a}² + 2 × {a} × {l:.6f} = {base_area} + {lateral_area:.6f} = {surface_area:.6f}'
            }, None
        
        else:
            return None, "Invalid shape type."
    
    def _prepare_step_by_step(self, shape_type, result):
        """Prepare step-by-step solution"""
        steps = []
        
        shape_names = {
            'cube': 'Cube',
            'sphere': 'Sphere',
            'cylinder': 'Cylinder',
            'cone': 'Cone',
            'rectangular_prism': 'Rectangular Prism',
            'triangular_prism': 'Triangular Prism',
            'pyramid': 'Square Pyramid'
        }
        
        steps.append(f"Given: {shape_names.get(shape_type, shape_type)}")
        steps.append("")
        
        if shape_type == 'cube':
            steps.append(f"  Side length (a) = {result['a']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  SA = 6a²")
            steps.append(f"  SA = 6 × {result['a']}²")
            steps.append(f"  SA = 6 × {result['a']**2}")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        elif shape_type == 'sphere':
            steps.append(f"  Radius (r) = {result['r']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  SA = 4πr²")
            steps.append(f"  SA = 4π × {result['r']}²")
            steps.append(f"  SA = 4π × {result['r']**2}")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        elif shape_type == 'cylinder':
            steps.append(f"  Radius (r) = {result['r']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = πr² = π × {result['r']}² = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate lateral area")
            steps.append(f"  Lateral Area = 2πrh = 2π × {result['r']} × {result['h']} = {result['lateral_area']:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate total surface area")
            steps.append(f"  SA = 2 × Base Area + Lateral Area")
            steps.append(f"  SA = 2 × {result['base_area']:.6f} + {result['lateral_area']:.6f}")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        elif shape_type == 'cone':
            steps.append(f"  Radius (r) = {result['r']}")
            if result.get('h') is not None:
                steps.append(f"  Height (h) = {result['h']}")
            steps.append(f"  Slant Height (l) = {result['l']:.6f}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = πr² = π × {result['r']}² = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate lateral area")
            steps.append(f"  Lateral Area = πrl = π × {result['r']} × {result['l']:.6f} = {result['lateral_area']:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate total surface area")
            steps.append(f"  SA = Base Area + Lateral Area")
            steps.append(f"  SA = {result['base_area']:.6f} + {result['lateral_area']:.6f}")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        elif shape_type == 'rectangular_prism':
            steps.append(f"  Length (l) = {result['l']}")
            steps.append(f"  Width (w) = {result['w']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  SA = 2(lw + lh + wh)")
            steps.append(f"  SA = 2({result['l']}×{result['w']} + {result['l']}×{result['h']} + {result['w']}×{result['h']})")
            steps.append(f"  SA = 2({result['l']*result['w']} + {result['l']*result['h']} + {result['w']*result['h']})")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        elif shape_type == 'triangular_prism':
            steps.append(f"  Base sides: a = {result['a']}, b = {result['b']}, c = {result['c']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Calculate base area using Heron's formula")
            steps.append(f"  s = (a + b + c) / 2 = ({result['a']} + {result['b']} + {result['c']}) / 2")
            s = (result['a'] + result['b'] + result['c']) / 2
            steps.append(f"  s = {s}")
            steps.append(f"  Base Area = √[s(s-a)(s-b)(s-c)] = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate lateral area")
            perimeter = result['a'] + result['b'] + result['c']
            steps.append(f"  Lateral Area = Perimeter × Height = {perimeter} × {result['h']} = {result['lateral_area']:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate total surface area")
            steps.append(f"  SA = 2 × Base Area + Lateral Area")
            steps.append(f"  SA = 2 × {result['base_area']:.6f} + {result['lateral_area']:.6f}")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        elif shape_type == 'pyramid':
            steps.append(f"  Base side (a) = {result['a']}")
            if result.get('h') is not None:
                steps.append(f"  Height (h) = {result['h']}")
            steps.append(f"  Slant Height (l) = {result['l']:.6f}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = a² = {result['a']}² = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate lateral area")
            steps.append(f"  Lateral Area = 2al = 2 × {result['a']} × {result['l']:.6f} = {result['lateral_area']:.6f}")
            steps.append("")
            steps.append("Step 3: Calculate total surface area")
            steps.append(f"  SA = Base Area + Lateral Area")
            steps.append(f"  SA = {result['base_area']:.6f} + {result['lateral_area']:.6f}")
            steps.append(f"  SA = {result['surface_area']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, shape_type, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Surface area breakdown chart (for shapes with base and lateral areas)
            if shape_type in ['cylinder', 'cone', 'pyramid', 'triangular_prism']:
                if 'base_area' in result and 'lateral_area' in result:
                    chart_data['area_breakdown_chart'] = {
                        'type': 'doughnut',
                        'data': {
                            'labels': ['Base Area', 'Lateral Area'],
                            'datasets': [{
                                'data': [result['base_area'], result['lateral_area']],
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
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            shape_type = data.get('shape_type', 'cube')
            
            # Get dimensions based on shape type
            kwargs = {}
            
            if shape_type == 'cube':
                a, error = self._validate_positive_number(data.get('a'), 'Side length (a)')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                kwargs['a'] = a
            
            elif shape_type == 'sphere':
                r, error = self._validate_positive_number(data.get('r'), 'Radius (r)')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                kwargs['r'] = r
            
            elif shape_type == 'cylinder':
                r, error1 = self._validate_positive_number(data.get('r'), 'Radius (r)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                h, error2 = self._validate_positive_number(data.get('h'), 'Height (h)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                kwargs['r'] = r
                kwargs['h'] = h
            
            elif shape_type == 'cone':
                r, error1 = self._validate_positive_number(data.get('r'), 'Radius (r)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                h_val = data.get('h', '').strip()
                l_val = data.get('l', '').strip()
                if h_val:
                    h, error = self._validate_positive_number(h_val, 'Height (h)')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                    kwargs['h'] = h
                if l_val:
                    l, error = self._validate_positive_number(l_val, 'Slant height (l)')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                    kwargs['l'] = l
                kwargs['r'] = r
            
            elif shape_type == 'rectangular_prism':
                l, error1 = self._validate_positive_number(data.get('l'), 'Length (l)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                w, error2 = self._validate_positive_number(data.get('w'), 'Width (w)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                h, error3 = self._validate_positive_number(data.get('h'), 'Height (h)')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                kwargs['l'] = l
                kwargs['w'] = w
                kwargs['h'] = h
            
            elif shape_type == 'triangular_prism':
                a, error1 = self._validate_positive_number(data.get('a'), 'Base side a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                b, error2 = self._validate_positive_number(data.get('b'), 'Base side b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                c, error3 = self._validate_positive_number(data.get('c'), 'Base side c')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                h, error4 = self._validate_positive_number(data.get('h'), 'Height (h)')
                if error4:
                    return JsonResponse({'success': False, 'error': error4}, status=400)
                base_h, error5 = self._validate_positive_number(data.get('base_h'), 'Base height')
                if error5:
                    return JsonResponse({'success': False, 'error': error5}, status=400)
                kwargs['a'] = a
                kwargs['b'] = b
                kwargs['c'] = c
                kwargs['h'] = h
                kwargs['base_h'] = base_h
            
            elif shape_type == 'pyramid':
                a, error1 = self._validate_positive_number(data.get('a'), 'Base side (a)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                h_val = data.get('h', '').strip()
                l_val = data.get('l', '').strip()
                if h_val:
                    h, error = self._validate_positive_number(h_val, 'Height (h)')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                    kwargs['h'] = h
                if l_val:
                    l, error = self._validate_positive_number(l_val, 'Slant height (l)')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                    kwargs['l'] = l
                kwargs['a'] = a
            
            # Calculate surface area
            result, error = self._calculate_surface_area(shape_type, **kwargs)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(shape_type, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(shape_type, result)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            shape_names = {
                'cube': 'Cube',
                'sphere': 'Sphere',
                'cylinder': 'Cylinder',
                'cone': 'Cone',
                'rectangular_prism': 'Rectangular Prism',
                'triangular_prism': 'Triangular Prism',
                'pyramid': 'Square Pyramid'
            }
            
            response = {
                'success': True,
                'shape_type': shape_type,
                'shape_name': shape_names.get(shape_type, shape_type),
                **result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Surface Area Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
