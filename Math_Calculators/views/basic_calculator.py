from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BasicCalculator(View):
    """
    Professional Basic Calculator with comprehensive operations
    Supports arithmetic, advanced operations, and expression evaluation.
    Includes backend-controlled rendering for all data.
    """
    template_name = 'math_calculators/basic_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Basic Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, "Invalid number: NaN or Infinity"
            return num, None
        except (ValueError, TypeError):
            return None, f"Invalid number: {value}"
    
    def _calculate_basic(self, num1, num2, operation):
        """Calculate basic arithmetic operations"""
        num1, error1 = self._validate_number(num1)
        num2, error2 = self._validate_number(num2)
        
        if error1:
            return None, error1
        if error2:
            return None, error2
        
        operations = {
            'add': lambda a, b: a + b,
            'subtract': lambda a, b: a - b,
            'multiply': lambda a, b: a * b,
            'divide': lambda a, b: a / b if b != 0 else None,
            'power': lambda a, b: a ** b,
            'modulo': lambda a, b: a % b if b != 0 else None,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num1, num2)
            if result is None:
                return None, "Division by zero or invalid operation"
            if math.isnan(result) or math.isinf(result):
                return None, "Result is NaN or Infinity"
            return result, None
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def _calculate_advanced(self, num, operation):
        """Calculate advanced single-operand operations"""
        num, error = self._validate_number(num)
        if error:
            return None, error
        
        operations = {
            'sqrt': lambda x: math.sqrt(x) if x >= 0 else None,
            'square': lambda x: x ** 2,
            'cube': lambda x: x ** 3,
            'inverse': lambda x: 1 / x if x != 0 else None,
            'percent': lambda x: x / 100,
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x)),
            'log': lambda x: math.log10(x) if x > 0 else None,
            'ln': lambda x: math.log(x) if x > 0 else None,
            'exp': lambda x: math.exp(x),
            'abs': lambda x: abs(x),
            'floor': lambda x: math.floor(x),
            'ceil': lambda x: math.ceil(x),
            'round': lambda x: round(x),
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num)
            if result is None:
                return None, "Invalid input for operation"
            if math.isnan(result) or math.isinf(result):
                return None, "Result is NaN or Infinity"
            return result, None
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def _evaluate_expression(self, expression):
        """Safely evaluate a mathematical expression"""
        # Remove whitespace
        expression = expression.strip()
        
        if not expression:
            return None, "Empty expression"
        
        # Validate expression contains only allowed characters and functions
        allowed_chars = re.compile(r'^[0-9+\-*/().\s^%a-z]+$', re.IGNORECASE)
        if not allowed_chars.match(expression.replace(' ', '')):
            return None, "Expression contains invalid characters"
        
        # Replace ^ with ** for power
        expression = expression.replace('^', '**')
        
        # Replace % with /100 (but not modulo operator)
        expression = re.sub(r'(\d+(?:\.\d+)?)\s*%', r'(\1/100)', expression)
        
        # Replace function names
        expression = expression.replace('sqrt', 'math.sqrt')
        expression = expression.replace('abs', 'abs')
        expression = expression.replace('round', 'round')
        
        try:
            # Use eval with limited scope including math functions
            safe_dict = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "math": math
            }
            result = eval(expression, safe_dict, {})
            
            if isinstance(result, (int, float)):
                if math.isnan(result) or math.isinf(result):
                    return None, "Result is NaN or Infinity"
                return float(result), None
            return None, "Invalid expression result"
        except ZeroDivisionError:
            return None, "Division by zero"
        except NameError as e:
            return None, f"Unknown function or variable: {str(e)}"
        except Exception as e:
            return None, f"Expression evaluation error: {str(e)}"
    
    def prepare_chart_data(self, calculation_history):
        """Prepare chart data for calculation history visualization"""
        if not calculation_history or len(calculation_history) < 2:
            return {}
        
        # Extract results from history
        results = [item.get('result', 0) for item in calculation_history[-10:]]  # Last 10 calculations
        labels = [f"#{i+1}" for i in range(len(results))]
        
        # History trend chart
        history_chart = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Calculation Results',
                    'data': results,
                    'borderColor': '#3b82f6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 4,
                    'pointBackgroundColor': '#3b82f6'
                }]
            }
        }
        
        # Result distribution (if multiple results)
        if len(results) > 1:
            min_val = min(results)
            max_val = max(results)
            range_val = max_val - min_val if max_val != min_val else 1
            bins = min(5, len(results))
            bin_width = range_val / bins if range_val > 0 else 1
            
            histogram_data = [0] * bins
            bin_labels = []
            for i in range(bins):
                bin_start = min_val + i * bin_width
                bin_end = min_val + (i + 1) * bin_width
                bin_labels.append(f"{bin_start:.1f}-{bin_end:.1f}")
                for result in results:
                    if i == bins - 1:
                        if bin_start <= result <= bin_end:
                            histogram_data[i] += 1
                    else:
                        if bin_start <= result < bin_end:
                            histogram_data[i] += 1
            
            distribution_chart = {
                'type': 'bar',
                'data': {
                    'labels': bin_labels,
                    'datasets': [{
                        'label': 'Frequency',
                        'data': histogram_data,
                        'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                        'borderColor': '#10b981',
                        'borderWidth': 2,
                        'borderRadius': 8
                    }]
                }
            }
        else:
            distribution_chart = None
        
        return {
            'history_chart': history_chart,
            'distribution_chart': distribution_chart
        }
    
    def prepare_display_data(self, result, operation, num1=None, num2=None, expression=None):
        """Prepare formatted display data for frontend"""
        def format_number(num, decimals=10):
            """Format number for display"""
            if num is None:
                return 'N/A'
            if not isinstance(num, (int, float)) or math.isnan(num) or math.isinf(num):
                return 'N/A'
            
            # Format with appropriate precision
            if abs(num) < 0.0001 and num != 0:
                formatted = f"{num:.{decimals}e}"
            elif abs(num) >= 1000000:
                formatted = f"{num:.{decimals}e}"
            else:
                formatted = f"{num:.{decimals}f}".rstrip('0').rstrip('.')
            
            # Add thousand separators for large numbers
            try:
                if 'e' not in formatted.lower():
                    parts = formatted.split('.')
                    parts[0] = f"{float(parts[0]):,}".rstrip('0').rstrip('.')
                    formatted = '.'.join(parts) if len(parts) > 1 else parts[0]
            except:
                pass
            
            return formatted
        
        display_data = {
            'result_formatted': format_number(result, 10),
            'result_formatted_short': format_number(result, 6),
            'operation_display': self._get_operation_display(operation),
            'calculation_details': []
        }
        
        # Add calculation details
        if expression:
            display_data['calculation_details'].append({
                'label': 'Expression',
                'value': expression,
                'is_primary': False
            })
        elif num1 is not None and num2 is not None:
            display_data['calculation_details'].extend([
                {
                    'label': 'First Number',
                    'value': format_number(num1, 6),
                    'is_primary': False
                },
                {
                    'label': 'Second Number',
                    'value': format_number(num2, 6),
                    'is_primary': False
                }
            ])
        elif num1 is not None:
            display_data['calculation_details'].append({
                'label': 'Number',
                'value': format_number(num1, 6),
                'is_primary': False
            })
        
        display_data['calculation_details'].append({
            'label': 'Result',
            'value': format_number(result, 10),
            'is_primary': True
        })
        
        return display_data
    
    def _get_operation_display(self, operation):
        """Get human-readable operation name"""
        operation_map = {
            'add': 'Addition',
            'subtract': 'Subtraction',
            'multiply': 'Multiplication',
            'divide': 'Division',
            'power': 'Power',
            'modulo': 'Modulo',
            'sqrt': 'Square Root',
            'square': 'Square',
            'cube': 'Cube',
            'inverse': 'Inverse',
            'percent': 'Percentage',
            'sin': 'Sine',
            'cos': 'Cosine',
            'tan': 'Tangent',
            'log': 'Logarithm (base 10)',
            'ln': 'Natural Logarithm',
            'exp': 'Exponential',
            'abs': 'Absolute Value',
            'floor': 'Floor',
            'ceil': 'Ceiling',
            'round': 'Round',
            'expression': 'Expression Evaluation'
        }
        return operation_map.get(operation, operation.capitalize())
    
    def prepare_step_by_step(self, operation, num1=None, num2=None, expression=None, result=None):
        """Prepare step-by-step solution"""
        steps = []
        
        if expression:
            steps.append(f"Expression: {expression}")
            steps.append(f"Evaluating expression...")
            steps.append(f"Result: {result}")
        elif num1 is not None and num2 is not None:
            op_symbols = {
                'add': '+',
                'subtract': '-',
                'multiply': '×',
                'divide': '÷',
                'power': '^',
                'modulo': 'mod'
            }
            symbol = op_symbols.get(operation, operation)
            
            steps.append(f"Operation: {self._get_operation_display(operation)}")
            steps.append(f"First number: {num1}")
            steps.append(f"Second number: {num2}")
            
            if operation == 'add':
                steps.append(f"Calculation: {num1} + {num2} = {result}")
            elif operation == 'subtract':
                steps.append(f"Calculation: {num1} - {num2} = {result}")
            elif operation == 'multiply':
                steps.append(f"Calculation: {num1} × {num2} = {result}")
            elif operation == 'divide':
                steps.append(f"Calculation: {num1} ÷ {num2} = {result}")
            elif operation == 'power':
                steps.append(f"Calculation: {num1} ^ {num2} = {result}")
            elif operation == 'modulo':
                steps.append(f"Calculation: {num1} mod {num2} = {result}")
        elif num1 is not None:
            steps.append(f"Operation: {self._get_operation_display(operation)}")
            steps.append(f"Number: {num1}")
            
            if operation == 'sqrt':
                steps.append(f"Calculation: √{num1} = {result}")
            elif operation == 'square':
                steps.append(f"Calculation: {num1}² = {result}")
            elif operation == 'cube':
                steps.append(f"Calculation: {num1}³ = {result}")
            elif operation == 'inverse':
                steps.append(f"Calculation: 1/{num1} = {result}")
            elif operation == 'percent':
                steps.append(f"Calculation: {num1}% = {result}")
            else:
                steps.append(f"Result: {result}")
        
        return steps
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            operation = data.get('operation', 'add')
            num1 = data.get('num1')
            num2 = data.get('num2')
            expression = data.get('expression')
            calculation_history = data.get('history', [])
            
            result = None
            error = None
            step_by_step = []
            
            # Handle expression evaluation
            if expression:
                result, error = self._evaluate_expression(expression)
                if not error:
                    step_by_step = self.prepare_step_by_step('expression', expression=expression, result=result)
                    display_data = self.prepare_display_data(result, 'expression', expression=expression)
            # Handle two-operand operations
            elif num1 is not None and num2 is not None:
                result, error = self._calculate_basic(num1, num2, operation)
                if not error:
                    step_by_step = self.prepare_step_by_step(operation, num1, num2, result=result)
                    display_data = self.prepare_display_data(result, operation, num1, num2)
            # Handle single-operand operations
            elif num1 is not None:
                result, error = self._calculate_advanced(num1, operation)
                if not error:
                    step_by_step = self.prepare_step_by_step(operation, num1=num1, result=result)
                    display_data = self.prepare_display_data(result, operation, num1=num1)
            else:
                error = "Please provide valid input"
            
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Add to history
            history_item = {
                'operation': operation,
                'num1': num1,
                'num2': num2,
                'expression': expression,
                'result': result,
                'timestamp': data.get('timestamp')
            }
            calculation_history.append(history_item)
            
            # Prepare chart data
            chart_data = {}
            if len(calculation_history) >= 2:
                try:
                    chart_data = self.prepare_chart_data(calculation_history)
                except Exception as chart_error:
                    import traceback
                    print(f"Chart data preparation error: {traceback.format_exc()}")
            
            # Prepare response
            response = {
                'success': True,
                'result': result,
                'operation': operation,
                'display_data': display_data,
                'step_by_step': step_by_step,
                'step_by_step_html': [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(step_by_step)],
                'chart_data': chart_data,
                'history': calculation_history[-20:]  # Keep last 20 calculations
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Basic calculator error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
