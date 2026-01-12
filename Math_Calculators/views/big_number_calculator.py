from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from decimal import Decimal, InvalidOperation, getcontext
from fractions import Fraction


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BigNumberCalculator(View):
    """
    Professional Big Number Calculator with arbitrary precision
    Handles very large numbers using Decimal for precision.
    Includes backend-controlled rendering for all data.
    """
    template_name = 'math_calculators/big_number_calculator.html'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set high precision for decimal operations
        getcontext().prec = 100  # 100 decimal places
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Big Number Calculator',
        }
        return render(request, self.template_name, context)
    
    def _parse_number(self, value):
        """Parse number string to Decimal with validation"""
        if not value or not isinstance(value, (str, int, float)):
            return None, "Invalid input: empty or wrong type"
        
        try:
            # Convert to string and strip whitespace
            value_str = str(value).strip()
            
            # Handle scientific notation
            if 'e' in value_str.lower() or 'E' in value_str:
                # Parse scientific notation
                try:
                    num = float(value_str)
                    return Decimal(str(num)), None
                except:
                    return None, "Invalid scientific notation"
            
            # Parse as Decimal
            decimal_value = Decimal(value_str)
            
            # Check for NaN or Infinity
            if decimal_value.is_nan() or decimal_value.is_infinite():
                return None, "Number is NaN or Infinity"
            
            return decimal_value, None
        except (ValueError, InvalidOperation) as e:
            return None, f"Invalid number format: {str(e)}"
        except Exception as e:
            return None, f"Error parsing number: {str(e)}"
    
    def _calculate_basic(self, num1_str, num2_str, operation):
        """Calculate basic arithmetic operations with big numbers"""
        num1, error1 = self._parse_number(num1_str)
        num2, error2 = self._parse_number(num2_str)
        
        if error1:
            return None, error1
        if error2:
            return None, error2
        
        operations = {
            'add': lambda a, b: a + b,
            'subtract': lambda a, b: a - b,
            'multiply': lambda a, b: a * b,
            'divide': lambda a, b: a / b if b != 0 else None,
            'power': lambda a, b: a ** int(b) if b == int(b) and abs(int(b)) < 1000 else None,
            'modulo': lambda a, b: a % b if b != 0 else None,
            'gcd': lambda a, b: Decimal(str(math.gcd(int(a), int(b)))) if a == int(a) and b == int(b) else None,
            'lcm': lambda a, b: Decimal(str(abs(int(a) * int(b)) // math.gcd(int(a), int(b)))) if a == int(a) and b == int(b) else None,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num1, num2)
            if result is None:
                return None, "Invalid operation (e.g., division by zero, non-integer power)"
            
            # Convert to Decimal if not already
            if not isinstance(result, Decimal):
                result = Decimal(str(result))
            
            if result.is_nan() or result.is_infinite():
                return None, "Result is NaN or Infinity"
            
            return result, None
        except (OverflowError, ValueError) as e:
            return None, f"Number too large or invalid: {str(e)}"
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def _calculate_advanced(self, num_str, operation):
        """Calculate advanced single-operand operations"""
        num, error = self._parse_number(num_str)
        if error:
            return None, error
        
        operations = {
            'sqrt': lambda x: x.sqrt() if x >= 0 else None,
            'square': lambda x: x ** 2,
            'cube': lambda x: x ** 3,
            'inverse': lambda x: 1 / x if x != 0 else None,
            'abs': lambda x: abs(x),
            'factorial': lambda x: Decimal(str(math.factorial(int(x)))) if x == int(x) and x >= 0 and x <= 1000 else None,
            'log10': lambda x: math.log10(float(x)) if x > 0 else None,
            'ln': lambda x: math.log(float(x)) if x > 0 else None,
            'exp': lambda x: Decimal(math.exp(float(x))) if abs(float(x)) < 700 else None,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num)
            if result is None:
                return None, "Invalid input for operation"
            
            # Convert to Decimal if not already
            if not isinstance(result, Decimal):
                result = Decimal(str(result))
            
            if result.is_nan() or result.is_infinite():
                return None, "Result is NaN or Infinity"
            
            return result, None
        except (OverflowError, ValueError) as e:
            return None, f"Number too large or invalid: {str(e)}"
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def prepare_chart_data(self, calculation_history):
        """Prepare chart data for calculation history visualization"""
        if not calculation_history or len(calculation_history) < 2:
            return {}
        
        # Extract results from history (convert to float for charting)
        results = []
        for item in calculation_history[-10:]:  # Last 10 calculations
            result = item.get('result')
            if result:
                try:
                    # Convert Decimal to float, handling very large numbers
                    result_float = float(result) if abs(float(result)) < 1e308 else None
                    if result_float is not None and not (math.isnan(result_float) or math.isinf(result_float)):
                        results.append(result_float)
                except:
                    pass
        
        if len(results) < 2:
            return {}
        
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
        
        return {
            'history_chart': history_chart
        }
    
    def prepare_display_data(self, result, operation, num1_str=None, num2_str=None):
        """Prepare formatted display data for frontend"""
        def format_big_number(num):
            """Format big number for display"""
            if num is None:
                return 'N/A'
            
            if not isinstance(num, Decimal):
                try:
                    num = Decimal(str(num))
                except:
                    return 'N/A'
            
            if num.is_nan() or num.is_infinite():
                return 'Infinity' if num.is_infinite() else 'NaN'
            
            # Convert to string
            num_str = str(num)
            
            # For very large or very small numbers, use scientific notation
            try:
                num_float = float(num)
                if abs(num_float) >= 1e15 or (abs(num_float) < 1e-6 and num_float != 0):
                    return f"{num_float:.6e}"
            except:
                pass
            
            # Format with comma separators
            if '.' in num_str:
                integer_part, decimal_part = num_str.split('.')
                # Add commas to integer part
                integer_formatted = f"{int(integer_part):,}"
                # Limit decimal places for readability
                if len(decimal_part) > 20:
                    decimal_part = decimal_part[:20].rstrip('0')
                if decimal_part:
                    return f"{integer_formatted}.{decimal_part}"
                return integer_formatted
            else:
                return f"{int(num):,}"
        
        display_data = {
            'result_formatted': format_big_number(result),
            'result_formatted_full': str(result),  # Full precision string
            'result_scientific': self._to_scientific_notation(result),
            'operation_display': self._get_operation_display(operation),
            'calculation_details': [],
            'number_properties': self._get_number_properties(result)
        }
        
        # Add calculation details
        if num1_str is not None:
            num1_display, _ = self._parse_number(num1_str)
            display_data['calculation_details'].append({
                'label': 'First Number',
                'value': format_big_number(num1_display),
                'is_primary': False
            })
        
        if num2_str is not None:
            num2_display, _ = self._parse_number(num2_str)
            display_data['calculation_details'].append({
                'label': 'Second Number',
                'value': format_big_number(num2_display),
                'is_primary': False
            })
        
        display_data['calculation_details'].append({
            'label': 'Result',
            'value': format_big_number(result),
            'is_primary': True
        })
        
        return display_data
    
    def _to_scientific_notation(self, num):
        """Convert number to scientific notation string"""
        if num is None:
            return 'N/A'
        
        try:
            if not isinstance(num, Decimal):
                num = Decimal(str(num))
            
            if num.is_nan() or num.is_infinite():
                return 'Infinity' if num.is_infinite() else 'NaN'
            
            # Convert to scientific notation
            num_float = float(num)
            if num_float == 0:
                return '0'
            
            return f"{num_float:.6e}"
        except:
            return str(num)
    
    def _get_number_properties(self, num):
        """Get properties of the number"""
        if num is None:
            return {}
        
        try:
            if not isinstance(num, Decimal):
                num = Decimal(str(num))
            
            properties = {
                'is_integer': num == int(num),
                'is_positive': num > 0,
                'is_negative': num < 0,
                'is_zero': num == 0,
                'digit_count': len(str(num).replace('.', '').replace('-', ''))
            }
            
            # Try to get magnitude
            try:
                num_float = float(num)
                if num_float != 0:
                    properties['magnitude'] = math.floor(math.log10(abs(num_float)))
                else:
                    properties['magnitude'] = 0
            except:
                properties['magnitude'] = None
            
            return properties
        except:
            return {}
    
    def _get_operation_display(self, operation):
        """Get human-readable operation name"""
        operation_map = {
            'add': 'Addition',
            'subtract': 'Subtraction',
            'multiply': 'Multiplication',
            'divide': 'Division',
            'power': 'Power',
            'modulo': 'Modulo',
            'gcd': 'Greatest Common Divisor',
            'lcm': 'Least Common Multiple',
            'sqrt': 'Square Root',
            'square': 'Square',
            'cube': 'Cube',
            'inverse': 'Inverse',
            'abs': 'Absolute Value',
            'factorial': 'Factorial',
            'log10': 'Logarithm (base 10)',
            'ln': 'Natural Logarithm',
            'exp': 'Exponential'
        }
        return operation_map.get(operation, operation.capitalize())
    
    def prepare_step_by_step(self, operation, num1_str=None, num2_str=None, result=None):
        """Prepare step-by-step solution"""
        steps = []
        
        if num1_str is not None and num2_str is not None:
            num1, _ = self._parse_number(num1_str)
            num2, _ = self._parse_number(num2_str)
            
            op_symbols = {
                'add': '+',
                'subtract': '-',
                'multiply': '×',
                'divide': '÷',
                'power': '^',
                'modulo': 'mod',
                'gcd': 'GCD',
                'lcm': 'LCM'
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
                steps.append(f"Calculation: {num1} ^ {int(num2)} = {result}")
            elif operation == 'modulo':
                steps.append(f"Calculation: {num1} mod {num2} = {result}")
            elif operation == 'gcd':
                steps.append(f"Calculation: GCD({int(num1)}, {int(num2)}) = {result}")
            elif operation == 'lcm':
                steps.append(f"Calculation: LCM({int(num1)}, {int(num2)}) = {result}")
                
        elif num1_str is not None:
            num1, _ = self._parse_number(num1_str)
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
            elif operation == 'abs':
                steps.append(f"Calculation: |{num1}| = {result}")
            elif operation == 'factorial':
                steps.append(f"Calculation: {int(num1)}! = {result}")
            else:
                steps.append(f"Result: {result}")
        
        return steps
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            operation = data.get('operation', 'add')
            num1_str = data.get('num1')
            num2_str = data.get('num2')
            calculation_history = data.get('history', [])
            
            result = None
            error = None
            step_by_step = []
            
            # Handle two-operand operations
            if num1_str is not None and num2_str is not None:
                result, error = self._calculate_basic(num1_str, num2_str, operation)
                if not error:
                    step_by_step = self.prepare_step_by_step(operation, num1_str, num2_str, result=result)
                    display_data = self.prepare_display_data(result, operation, num1_str, num2_str)
            # Handle single-operand operations
            elif num1_str is not None:
                result, error = self._calculate_advanced(num1_str, operation)
                if not error:
                    step_by_step = self.prepare_step_by_step(operation, num1_str=num1_str, result=result)
                    display_data = self.prepare_display_data(result, operation, num1_str=num1_str)
            else:
                error = "Please provide at least one number"
            
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Convert result to string for JSON serialization
            result_str = str(result)
            
            # Add to history
            history_item = {
                'operation': operation,
                'num1': num1_str,
                'num2': num2_str,
                'result': result_str,
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
                'result': result_str,
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
            print(f"Big number calculator error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
