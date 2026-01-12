from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SlopeCalculator(View):
    """
    Enhanced Professional Slope Calculator
    Calculates slope from points, equations, and finds line equations with step-by-step solutions.
    """
    template_name = 'math_calculators/slope_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Slope Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_slope_from_points(self, x1, y1, x2, y2):
        """Calculate slope from two points"""
        if x1 == x2:
            return None, "x-coordinates cannot be equal (vertical line, undefined slope)."
        
        slope = (y2 - y1) / (x2 - x1)
        return slope, None
    
    def _calculate_slope_from_equation(self, equation_type, a=None, b=None, c=None, m=None, x0=None, y0=None):
        """Calculate slope from equation"""
        if equation_type == 'slope_intercept':
            # y = mx + b, slope is m
            if m is None:
                return None, "Slope (m) is required for slope-intercept form."
            return m, None
        
        elif equation_type == 'standard':
            # Ax + By = C, slope is -A/B
            if a is None or b is None:
                return None, "Both A and B are required for standard form."
            if b == 0:
                return None, "B cannot be zero (vertical line, undefined slope)."
            return -a / b, None
        
        elif equation_type == 'point_slope':
            # y - y0 = m(x - x0), slope is m
            if m is None:
                return None, "Slope (m) is required for point-slope form."
            return m, None
        
        else:
            return None, "Invalid equation type."
    
    def _find_equation_from_slope_point(self, m, x1, y1):
        """Find line equation from slope and point"""
        # Slope-intercept form: y = mx + b
        # b = y - mx
        b = y1 - m * x1
        
        # Point-slope form: y - y1 = m(x - x1)
        # Standard form: -mx + y = b, or mx - y = -b
        # For standard form: Ax + By = C
        # We can use: -mx + y = b, so A = -m, B = 1, C = b
        # Or: mx - y = -b, so A = m, B = -1, C = -b
        
        return {
            'slope_intercept': f"y = {m}x + {b}" if b >= 0 else f"y = {m}x - {abs(b)}",
            'point_slope': f"y - {y1} = {m}(x - {x1})",
            'standard': f"{m}x - y = {-b}" if -b >= 0 else f"{m}x - y = {-b}"
        }
    
    def _calculate_from_points(self, x1, y1, x2, y2):
        """Calculate all properties from two points"""
        slope, error = self._calculate_slope_from_points(x1, y1, x2, y2)
        if error:
            return None, error
        
        # Calculate y-intercept
        # Using point-slope: y - y1 = m(x - x1)
        # y = mx - mx1 + y1
        # y = mx + (y1 - mx1)
        b = y1 - slope * x1
        
        # Distance between points
        distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        
        # Midpoint
        midpoint_x = (x1 + x2) / 2
        midpoint_y = (y1 + y2) / 2
        
        # Angle of line (in degrees)
        angle = math.degrees(math.atan(slope))
        
        # Equations in different forms
        equations = self._find_equation_from_slope_point(slope, x1, y1)
        
        return {
            'slope': slope,
            'y_intercept': b,
            'distance': distance,
            'midpoint': (midpoint_x, midpoint_y),
            'angle': angle,
            'equations': equations,
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2
        }, None
    
    def _prepare_step_by_step(self, calc_type, result):
        """Prepare step-by-step solution"""
        steps = []
        
        if calc_type == 'from_points':
            steps.append(f"Given: Point 1 = ({result['x1']}, {result['y1']}), Point 2 = ({result['x2']}, {result['y2']})")
            steps.append("")
            steps.append("Step 1: Calculate slope")
            steps.append("  Formula: m = (y₂ - y₁) / (x₂ - x₁)")
            steps.append(f"  m = ({result['y2']} - {result['y1']}) / ({result['x2']} - {result['x1']})")
            steps.append(f"  m = {result['y2'] - result['y1']} / {result['x2'] - result['x1']}")
            steps.append(f"  m = {result['slope']:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate y-intercept")
            steps.append("  Using point-slope form: y - y₁ = m(x - x₁)")
            steps.append(f"  y - {result['y1']} = {result['slope']:.6f}(x - {result['x1']})")
            steps.append(f"  y = {result['slope']:.6f}x + ({result['y1']} - {result['slope']:.6f} × {result['x1']})")
            steps.append(f"  y = {result['slope']:.6f}x + {result['y_intercept']:.6f}")
            steps.append("")
            steps.append("Step 3: Additional calculations")
            steps.append(f"  Distance between points: √[({result['x2']} - {result['x1']})² + ({result['y2']} - {result['y1']})²]")
            steps.append(f"  Distance = {result['distance']:.6f}")
            steps.append(f"  Midpoint: (({result['x1']} + {result['x2']})/2, ({result['y1']} + {result['y2']})/2)")
            steps.append(f"  Midpoint = ({result['midpoint'][0]:.6f}, {result['midpoint'][1]:.6f})")
            steps.append(f"  Angle of line: arctan({result['slope']:.6f}) = {result['angle']:.6f}°")
        
        elif calc_type == 'from_equation':
            steps.append("Step 1: Extract slope from equation")
            steps.append(f"  Slope = {result['slope']:.6f}")
        
        elif calc_type == 'from_slope_point':
            steps.append(f"Given: Slope (m) = {result['slope']}, Point = ({result['x1']}, {result['y1']})")
            steps.append("")
            steps.append("Step 1: Use point-slope form")
            steps.append(f"  y - {result['y1']} = {result['slope']}(x - {result['x1']})")
            steps.append("")
            steps.append("Step 2: Convert to slope-intercept form")
            steps.append(f"  y = {result['slope']}x + ({result['y1']} - {result['slope']} × {result['x1']})")
            b = result['y1'] - result['slope'] * result['x1']
            steps.append(f"  y = {result['slope']}x + {b:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, result, calc_type):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if calc_type == 'from_points':
                # Generate points for line
                x1 = result['x1']
                y1 = result['y1']
                x2 = result['x2']
                y2 = result['y2']
                slope = result['slope']
                b = result['y_intercept']
                
                # Extend line beyond points
                min_x = min(x1, x2) - 2
                max_x = max(x1, x2) + 2
                
                x_values = []
                y_values = []
                for i in range(20):
                    x = min_x + (max_x - min_x) * i / 19
                    y = slope * x + b
                    x_values.append(x)
                    y_values.append(y)
                
                chart_data['line_chart'] = {
                    'type': 'line',
                    'data': {
                        'labels': [f'{x:.2f}' for x in x_values],
                        'datasets': [
                            {
                                'label': 'Line',
                                'data': y_values,
                                'borderColor': '#3b82f6',
                                'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                                'borderWidth': 2,
                                'fill': False,
                                'tension': 0
                            },
                            {
                                'label': 'Point 1',
                                'data': [{'x': x1, 'y': y1}],
                                'backgroundColor': '#10b981',
                                'borderColor': '#10b981',
                                'pointRadius': 8,
                                'pointHoverRadius': 10,
                                'showLine': False
                            },
                            {
                                'label': 'Point 2',
                                'data': [{'x': x2, 'y': y2}],
                                'backgroundColor': '#ef4444',
                                'borderColor': '#ef4444',
                                'pointRadius': 8,
                                'pointHoverRadius': 10,
                                'showLine': False
                            }
                        ]
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
            
            calc_type = data.get('calc_type', 'from_points')
            
            if calc_type == 'from_points':
                x1, error1 = self._validate_number(data.get('x1'), 'x1')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                y1, error2 = self._validate_number(data.get('y1'), 'y1')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                x2, error3 = self._validate_number(data.get('x2'), 'x2')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                
                y2, error4 = self._validate_number(data.get('y2'), 'y2')
                if error4:
                    return JsonResponse({'success': False, 'error': error4}, status=400)
                
                result, error = self._calculate_from_points(x1, y1, x2, y2)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
            
            elif calc_type == 'from_equation':
                equation_type = data.get('equation_type', 'slope_intercept')
                
                if equation_type == 'slope_intercept':
                    m, error = self._validate_number(data.get('m'), 'Slope (m)')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                    slope, error = self._calculate_slope_from_equation(equation_type, m=m)
                
                elif equation_type == 'standard':
                    a, error1 = self._validate_number(data.get('a'), 'A')
                    if error1:
                        return JsonResponse({'success': False, 'error': error1}, status=400)
                    b, error2 = self._validate_number(data.get('b'), 'B')
                    if error2:
                        return JsonResponse({'success': False, 'error': error2}, status=400)
                    slope, error = self._calculate_slope_from_equation(equation_type, a=a, b=b)
                
                elif equation_type == 'point_slope':
                    m, error = self._validate_number(data.get('m'), 'Slope (m)')
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                    slope, error = self._calculate_slope_from_equation(equation_type, m=m)
                
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                result = {'slope': slope}
            
            elif calc_type == 'from_slope_point':
                m, error1 = self._validate_number(data.get('m'), 'Slope (m)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                x1, error2 = self._validate_number(data.get('x1'), 'x')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                y1, error3 = self._validate_number(data.get('y1'), 'y')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                
                equations = self._find_equation_from_slope_point(m, x1, y1)
                b = y1 - m * x1
                result = {
                    'slope': m,
                    'x1': x1,
                    'y1': y1,
                    'y_intercept': b,
                    'equations': equations
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(calc_type, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(result, calc_type)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                'calc_type': calc_type,
                **result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Slope Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
