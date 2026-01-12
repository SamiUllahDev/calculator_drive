from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class VolumeCalculator(View):
    """
    Enhanced Professional Volume Calculator
    Calculates volume for various 3D shapes with step-by-step solutions.
    """
    template_name = 'math_calculators/volume_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Volume Calculator',
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
    
    def _calculate_volume(self, shape_type, **kwargs):
        """Calculate volume based on shape type"""
        if shape_type == 'cube':
            # Cube: V = a³
            a = kwargs.get('a')
            if a is None:
                return None, "Side length (a) is required."
            volume = a ** 3
            return {
                'volume': volume,
                'a': a,
                'formula': 'V = a³',
                'calculation': f'V = {a}³ = {volume}'
            }, None
        
        elif shape_type == 'sphere':
            # Sphere: V = (4/3)πr³
            r = kwargs.get('r')
            if r is None:
                return None, "Radius (r) is required."
            volume = (4/3) * math.pi * r ** 3
            return {
                'volume': volume,
                'r': r,
                'formula': 'V = (4/3)πr³',
                'calculation': f'V = (4/3)π × {r}³ = (4/3)π × {r**3} = {volume:.6f}'
            }, None
        
        elif shape_type == 'cylinder':
            # Cylinder: V = πr²h
            r = kwargs.get('r')
            h = kwargs.get('h')
            if r is None or h is None:
                return None, "Both radius (r) and height (h) are required."
            base_area = math.pi * r ** 2
            volume = base_area * h
            return {
                'volume': volume,
                'r': r,
                'h': h,
                'base_area': base_area,
                'formula': 'V = πr²h',
                'calculation': f'V = π × {r}² × {h} = π × {r**2} × {h} = {volume:.6f}'
            }, None
        
        elif shape_type == 'cone':
            # Cone: V = (1/3)πr²h
            r = kwargs.get('r')
            h = kwargs.get('h')
            if r is None or h is None:
                return None, "Both radius (r) and height (h) are required."
            base_area = math.pi * r ** 2
            volume = (1/3) * base_area * h
            return {
                'volume': volume,
                'r': r,
                'h': h,
                'base_area': base_area,
                'formula': 'V = (1/3)πr²h',
                'calculation': f'V = (1/3) × π × {r}² × {h} = (1/3) × π × {r**2} × {h} = {volume:.6f}'
            }, None
        
        elif shape_type == 'rectangular_prism':
            # Rectangular Prism: V = lwh
            l = kwargs.get('l')
            w = kwargs.get('w')
            h = kwargs.get('h')
            if l is None or w is None or h is None:
                return None, "Length (l), width (w), and height (h) are required."
            volume = l * w * h
            return {
                'volume': volume,
                'l': l,
                'w': w,
                'h': h,
                'formula': 'V = lwh',
                'calculation': f'V = {l} × {w} × {h} = {volume}'
            }, None
        
        elif shape_type == 'triangular_prism':
            # Triangular Prism: V = (1/2) × base × height × length
            base = kwargs.get('base')
            height = kwargs.get('height')
            length = kwargs.get('length')
            if base is None or height is None or length is None:
                return None, "Base, height, and length are required."
            base_area = 0.5 * base * height
            volume = base_area * length
            return {
                'volume': volume,
                'base': base,
                'height': height,
                'length': length,
                'base_area': base_area,
                'formula': 'V = (1/2) × base × height × length',
                'calculation': f'V = (1/2) × {base} × {height} × {length} = {base_area} × {length} = {volume:.6f}'
            }, None
        
        elif shape_type == 'pyramid':
            # Square Pyramid: V = (1/3)a²h
            a = kwargs.get('a')
            h = kwargs.get('h')
            if a is None or h is None:
                return None, "Base side (a) and height (h) are required."
            base_area = a ** 2
            volume = (1/3) * base_area * h
            return {
                'volume': volume,
                'a': a,
                'h': h,
                'base_area': base_area,
                'formula': 'V = (1/3)a²h',
                'calculation': f'V = (1/3) × {a}² × {h} = (1/3) × {base_area} × {h} = {volume:.6f}'
            }, None
        
        elif shape_type == 'ellipsoid':
            # Ellipsoid: V = (4/3)πabc
            a = kwargs.get('a')
            b = kwargs.get('b')
            c = kwargs.get('c')
            if a is None or b is None or c is None:
                return None, "All three semi-axes (a, b, c) are required."
            volume = (4/3) * math.pi * a * b * c
            return {
                'volume': volume,
                'a': a,
                'b': b,
                'c': c,
                'formula': 'V = (4/3)πabc',
                'calculation': f'V = (4/3)π × {a} × {b} × {c} = {volume:.6f}'
            }, None
        
        elif shape_type == 'torus':
            # Torus: V = 2π²Rr²
            R = kwargs.get('R')
            r = kwargs.get('r')
            if R is None or r is None:
                return None, "Both major radius (R) and minor radius (r) are required."
            volume = 2 * math.pi ** 2 * R * r ** 2
            return {
                'volume': volume,
                'R': R,
                'r': r,
                'formula': 'V = 2π²Rr²',
                'calculation': f'V = 2π² × {R} × {r}² = 2π² × {R} × {r**2} = {volume:.6f}'
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
            'pyramid': 'Square Pyramid',
            'ellipsoid': 'Ellipsoid',
            'torus': 'Torus'
        }
        
        steps.append(f"Given: {shape_names.get(shape_type, shape_type)}")
        steps.append("")
        
        if shape_type == 'cube':
            steps.append(f"  Side length (a) = {result['a']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  V = a³")
            steps.append(f"  V = {result['a']}³")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'sphere':
            steps.append(f"  Radius (r) = {result['r']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  V = (4/3)πr³")
            steps.append(f"  V = (4/3)π × {result['r']}³")
            steps.append(f"  V = (4/3)π × {result['r']**3}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'cylinder':
            steps.append(f"  Radius (r) = {result['r']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = πr² = π × {result['r']}² = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate volume")
            steps.append(f"  V = Base Area × Height")
            steps.append(f"  V = {result['base_area']:.6f} × {result['h']}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'cone':
            steps.append(f"  Radius (r) = {result['r']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = πr² = π × {result['r']}² = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate volume")
            steps.append(f"  V = (1/3) × Base Area × Height")
            steps.append(f"  V = (1/3) × {result['base_area']:.6f} × {result['h']}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'rectangular_prism':
            steps.append(f"  Length (l) = {result['l']}")
            steps.append(f"  Width (w) = {result['w']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  V = lwh")
            steps.append(f"  V = {result['l']} × {result['w']} × {result['h']}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'triangular_prism':
            steps.append(f"  Base = {result['base']}")
            steps.append(f"  Height = {result['height']}")
            steps.append(f"  Length = {result['length']}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = (1/2) × base × height = (1/2) × {result['base']} × {result['height']} = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate volume")
            steps.append(f"  V = Base Area × Length")
            steps.append(f"  V = {result['base_area']:.6f} × {result['length']}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'pyramid':
            steps.append(f"  Base side (a) = {result['a']}")
            steps.append(f"  Height (h) = {result['h']}")
            steps.append("")
            steps.append("Step 1: Calculate base area")
            steps.append(f"  Base Area = a² = {result['a']}² = {result['base_area']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate volume")
            steps.append(f"  V = (1/3) × Base Area × Height")
            steps.append(f"  V = (1/3) × {result['base_area']:.6f} × {result['h']}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'ellipsoid':
            steps.append(f"  Semi-axis a = {result['a']}")
            steps.append(f"  Semi-axis b = {result['b']}")
            steps.append(f"  Semi-axis c = {result['c']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  V = (4/3)πabc")
            steps.append(f"  V = (4/3)π × {result['a']} × {result['b']} × {result['c']}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        elif shape_type == 'torus':
            steps.append(f"  Major radius (R) = {result['R']}")
            steps.append(f"  Minor radius (r) = {result['r']}")
            steps.append("")
            steps.append("Step 1: Apply formula")
            steps.append("  V = 2π²Rr²")
            steps.append(f"  V = 2π² × {result['R']} × {result['r']}²")
            steps.append(f"  V = 2π² × {result['R']} × {result['r']**2}")
            steps.append(f"  V = {result['volume']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, shape_type, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # For shapes with base area, show volume breakdown
            if shape_type in ['cylinder', 'cone', 'pyramid', 'triangular_prism']:
                if 'base_area' in result:
                    # This is a conceptual chart showing the relationship
                    # We'll show dimensions comparison instead
                    pass
            
            # Dimensions comparison chart
            if shape_type == 'rectangular_prism':
                chart_data['dimensions_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': ['Length', 'Width', 'Height'],
                        'datasets': [{
                            'label': 'Dimension',
                            'data': [result['l'], result['w'], result['h']],
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
            elif shape_type == 'ellipsoid':
                chart_data['dimensions_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': ['Semi-axis a', 'Semi-axis b', 'Semi-axis c'],
                        'datasets': [{
                            'label': 'Semi-axis',
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
                h, error2 = self._validate_positive_number(data.get('h'), 'Height (h)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                kwargs['r'] = r
                kwargs['h'] = h
            
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
                base, error1 = self._validate_positive_number(data.get('base'), 'Base')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                height, error2 = self._validate_positive_number(data.get('height'), 'Height')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                length, error3 = self._validate_positive_number(data.get('length'), 'Length')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                kwargs['base'] = base
                kwargs['height'] = height
                kwargs['length'] = length
            
            elif shape_type == 'pyramid':
                a, error1 = self._validate_positive_number(data.get('a'), 'Base side (a)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                h, error2 = self._validate_positive_number(data.get('h'), 'Height (h)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                kwargs['a'] = a
                kwargs['h'] = h
            
            elif shape_type == 'ellipsoid':
                a, error1 = self._validate_positive_number(data.get('a'), 'Semi-axis a')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                b, error2 = self._validate_positive_number(data.get('b'), 'Semi-axis b')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                c, error3 = self._validate_positive_number(data.get('c'), 'Semi-axis c')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                kwargs['a'] = a
                kwargs['b'] = b
                kwargs['c'] = c
            
            elif shape_type == 'torus':
                R, error1 = self._validate_positive_number(data.get('R'), 'Major radius (R)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                r, error2 = self._validate_positive_number(data.get('r'), 'Minor radius (r)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                kwargs['R'] = R
                kwargs['r'] = r
            
            # Calculate volume
            result, error = self._calculate_volume(shape_type, **kwargs)
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
                'pyramid': 'Square Pyramid',
                'ellipsoid': 'Ellipsoid',
                'torus': 'Torus'
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
            print(f"Volume Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
