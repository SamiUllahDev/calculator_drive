from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BinaryCalculator(View):
    """
    Professional Binary Calculator with comprehensive binary operations
    Supports binary arithmetic, bitwise operations, and number system conversions.
    Includes backend-controlled rendering for all data.
    """
    template_name = 'math_calculators/binary_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Binary Calculator',
        }
        return render(request, self.template_name, context)
    
    def _parse_binary(self, value):
        """Parse binary string to integer"""
        if not value:
            return None, "Empty input"
        
        value_str = str(value).strip().replace(' ', '')
        
        # Remove common prefixes
        if value_str.startswith('0b') or value_str.startswith('0B'):
            value_str = value_str[2:]
        
        try:
            # Validate binary string
            if not all(c in '01' for c in value_str):
                return None, "Invalid binary string. Only 0 and 1 are allowed."
            
            if not value_str:
                return None, "Empty binary string"
            
            # Convert to integer
            decimal_value = int(value_str, 2)
            
            # Check for reasonable range (32-bit signed integer range)
            if decimal_value > 2147483647:
                return None, "Binary number too large. Maximum value is 2,147,483,647 (32-bit signed integer)"
            
            return decimal_value, None
        except ValueError as e:
            return None, f"Invalid binary format: {str(e)}"
        except Exception as e:
            return None, f"Error parsing binary: {str(e)}"
    
    def _parse_decimal(self, value):
        """Parse decimal string to integer"""
        if not value:
            return None, "Empty input"
        
        try:
            value_str = str(value).strip()
            decimal_value = int(float(value_str))
            
            # Check for reasonable range (32-bit signed integer range)
            if decimal_value < -2147483648 or decimal_value > 2147483647:
                return None, "Number out of range. Please use values between -2,147,483,648 and 2,147,483,647"
            
            return decimal_value, None
        except (ValueError, TypeError) as e:
            return None, f"Invalid decimal format: {str(e)}"
        except Exception as e:
            return None, f"Error parsing decimal: {str(e)}"
    
    def _parse_hex(self, value):
        """Parse hexadecimal string to integer"""
        if not value:
            return None, "Empty input"
        
        value_str = str(value).strip().replace(' ', '')
        
        # Remove common prefixes
        if value_str.startswith('0x') or value_str.startswith('0X'):
            value_str = value_str[2:]
        
        try:
            # Validate hex string
            if not all(c in '0123456789ABCDEFabcdef' for c in value_str):
                return None, "Invalid hexadecimal string. Only 0-9 and A-F are allowed."
            
            if not value_str:
                return None, "Empty hexadecimal string"
            
            decimal_value = int(value_str, 16)
            
            # Check for reasonable range
            if decimal_value > 2147483647:
                return None, "Hexadecimal number too large. Maximum value is 0x7FFFFFFF (32-bit signed integer)"
            
            return decimal_value, None
        except ValueError as e:
            return None, f"Invalid hexadecimal format: {str(e)}"
        except Exception as e:
            return None, f"Error parsing hexadecimal: {str(e)}"
    
    def _parse_octal(self, value):
        """Parse octal string to integer"""
        if not value:
            return None, "Empty input"
        
        value_str = str(value).strip().replace(' ', '')
        
        # Remove common prefixes
        if value_str.startswith('0o') or value_str.startswith('0O'):
            value_str = value_str[2:]
        
        try:
            # Validate octal string
            if not all(c in '01234567' for c in value_str):
                return None, "Invalid octal string. Only 0-7 are allowed."
            
            if not value_str:
                return None, "Empty octal string"
            
            decimal_value = int(value_str, 8)
            
            # Check for reasonable range
            if decimal_value > 2147483647:
                return None, "Octal number too large. Maximum value is 0o17777777777 (32-bit signed integer)"
            
            return decimal_value, None
        except ValueError as e:
            return None, f"Invalid octal format: {str(e)}"
        except Exception as e:
            return None, f"Error parsing octal: {str(e)}"
    
    def _parse_number(self, value, base='binary'):
        """Parse number based on base"""
        parsers = {
            'binary': self._parse_binary,
            'decimal': self._parse_decimal,
            'hexadecimal': self._parse_hex,
            'octal': self._parse_octal
        }
        
        parser = parsers.get(base.lower(), self._parse_binary)
        return parser(value)
    
    def _to_binary(self, num, width=None):
        """Convert integer to binary string"""
        if num < 0:
            # Handle negative numbers using two's complement
            if width:
                return format(num & ((1 << width) - 1), f'0{width}b')
            return bin(num & 0xFFFFFFFF)[2:]  # 32-bit two's complement
        else:
            binary = bin(num)[2:]  # Remove '0b' prefix
            if width:
                return binary.zfill(width)
            return binary
    
    def _to_hex(self, num, width=None):
        """Convert integer to hexadecimal string"""
        hex_str = hex(num)[2:].upper()  # Remove '0x' prefix and uppercase
        if width:
            return hex_str.zfill(width)
        return hex_str
    
    def _to_octal(self, num, width=None):
        """Convert integer to octal string"""
        octal_str = oct(num)[2:]  # Remove '0o' prefix
        if width:
            return octal_str.zfill(width)
        return octal_str
    
    def _calculate_binary_arithmetic(self, num1, num2, operation):
        """Calculate binary arithmetic operations"""
        operations = {
            'add': lambda a, b: a + b,
            'subtract': lambda a, b: a - b,
            'multiply': lambda a, b: a * b,
            'divide': lambda a, b: a // b if b != 0 else None,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num1, num2)
            if result is None:
                return None, "Division by zero"
            return result, None
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def _calculate_bitwise(self, num1, num2, operation):
        """Calculate bitwise operations"""
        operations = {
            'and': lambda a, b: a & b,
            'or': lambda a, b: a | b,
            'xor': lambda a, b: a ^ b,
            'nand': lambda a, b: ~(a & b) & 0xFFFFFFFF,
            'nor': lambda a, b: ~(a | b) & 0xFFFFFFFF,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num1, num2)
            # Handle negative results (two's complement)
            if result < 0:
                result = result & 0xFFFFFFFF
            return result, None
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def _calculate_bitwise_single(self, num, operation):
        """Calculate single-operand bitwise operations"""
        operations = {
            'not': lambda a: (~a) & 0xFFFFFFFF,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num)
            # Handle negative results
            if result < 0:
                result = result & 0xFFFFFFFF
            return result, None
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def _calculate_shift(self, num, shift_amount, operation):
        """Calculate bit shift operations"""
        if shift_amount < 0:
            return None, "Shift amount must be non-negative"
        
        if shift_amount > 32:
            return None, "Shift amount too large. Maximum is 32 bits"
        
        operations = {
            'left_shift': lambda a, s: a << s,
            'right_shift': lambda a, s: a >> s,
        }
        
        if operation not in operations:
            return None, f"Unknown operation: {operation}"
        
        try:
            result = operations[operation](num, shift_amount)
            # Handle negative results (two's complement)
            if result < 0:
                result = result & 0xFFFFFFFF
            # Limit to 32-bit range
            if result > 0xFFFFFFFF:
                result = result & 0xFFFFFFFF
            return result, None
        except OverflowError:
            return None, "Result overflow. Shift amount may be too large."
        except Exception as e:
            return None, f"Calculation error: {str(e)}"
    
    def prepare_chart_data(self, num1, num2, result, operation):
        """Prepare chart data for binary visualization"""
        # Bit comparison chart
        max_bits = max(
            len(self._to_binary(num1)),
            len(self._to_binary(num2)) if num2 is not None else 0,
            len(self._to_binary(result))
        )
        max_bits = max(max_bits, 8)  # Minimum 8 bits
        max_bits = min(max_bits, 32)  # Maximum 32 bits for readability
        
        # Pad to same width
        bin1 = self._to_binary(num1, max_bits)
        bin2 = self._to_binary(num2, max_bits) if num2 is not None else None
        bin_result = self._to_binary(result, max_bits)
        
        # Create bit position labels (show bit position and value)
        bit_labels = [f"B{i}" for i in range(max_bits - 1, -1, -1)]
        
        # Extract individual bits
        bits1 = [int(bit) for bit in bin1]
        bits2 = [int(bit) for bit in bin2] if bin2 else None
        bits_result = [int(bit) for bit in bin_result]
        
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': bit_labels,
                'datasets': [
                    {
                        'label': 'Number 1',
                        'data': bits1,
                        'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                        'borderColor': '#3b82f6',
                        'borderWidth': 1
                    }
                ]
            }
        }
        
        if bits2 is not None:
            comparison_chart['data']['datasets'].append({
                'label': 'Number 2',
                'data': bits2,
                'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                'borderColor': '#10b981',
                'borderWidth': 1
            })
        
        comparison_chart['data']['datasets'].append({
            'label': 'Result',
            'data': bits_result,
            'backgroundColor': 'rgba(245, 158, 11, 0.6)',
            'borderColor': '#f59e0b',
            'borderWidth': 1
        })
        
        return {
            'comparison_chart': comparison_chart
        }
    
    def prepare_display_data(self, num1, num2, result, operation, input_base='binary'):
        """Prepare formatted display data for frontend"""
        def format_binary(num, width=None):
            """Format number as binary with spacing"""
            binary = self._to_binary(num, width)
            # Add space every 4 bits for readability
            return ' '.join([binary[i:i+4] for i in range(0, len(binary), 4)])
        
        def format_large_number(num_str):
            """Format large numbers with thousand separators"""
            try:
                num = int(num_str)
                if abs(num) >= 1000:
                    return f"{num:,}"
                return num_str
            except:
                return num_str
        
        display_data = {
            'num1_binary': format_binary(num1),
            'num1_decimal': format_large_number(str(num1)),
            'num1_hex': '0x' + self._to_hex(num1),
            'num1_octal': '0o' + self._to_octal(num1),
            'result_binary': format_binary(result),
            'result_decimal': format_large_number(str(result)),
            'result_hex': '0x' + self._to_hex(result),
            'result_octal': '0o' + self._to_octal(result),
            'operation_display': self._get_operation_display(operation),
            'conversions': {
                'num1': {
                    'binary': format_binary(num1),
                    'decimal': format_large_number(str(num1)),
                    'hexadecimal': '0x' + self._to_hex(num1),
                    'octal': '0o' + self._to_octal(num1)
                },
                'result': {
                    'binary': format_binary(result),
                    'decimal': format_large_number(str(result)),
                    'hexadecimal': '0x' + self._to_hex(result),
                    'octal': '0o' + self._to_octal(result)
                }
            }
        }
        
        if num2 is not None:
            display_data['num2_binary'] = format_binary(num2)
            display_data['num2_decimal'] = format_large_number(str(num2))
            display_data['num2_hex'] = '0x' + self._to_hex(num2)
            display_data['num2_octal'] = '0o' + self._to_octal(num2)
            display_data['conversions']['num2'] = {
                'binary': format_binary(num2),
                'decimal': format_large_number(str(num2)),
                'hexadecimal': '0x' + self._to_hex(num2),
                'octal': '0o' + self._to_octal(num2)
            }
        
        return display_data
    
    def _get_operation_display(self, operation):
        """Get human-readable operation name"""
        operation_map = {
            'add': 'Binary Addition',
            'subtract': 'Binary Subtraction',
            'multiply': 'Binary Multiplication',
            'divide': 'Binary Division',
            'and': 'Bitwise AND',
            'or': 'Bitwise OR',
            'xor': 'Bitwise XOR',
            'nand': 'Bitwise NAND',
            'nor': 'Bitwise NOR',
            'not': 'Bitwise NOT',
            'left_shift': 'Left Shift',
            'right_shift': 'Right Shift',
            'convert': 'Number Conversion'
        }
        return operation_map.get(operation, operation.capitalize())
    
    def prepare_step_by_step(self, num1, num2, result, operation, input_base='binary'):
        """Prepare step-by-step solution"""
        steps = []
        
        if operation == 'convert':
            steps.append(f"Converting {input_base} number to other bases")
            steps.append(f"Input: {num1} ({input_base})")
            steps.append(f"Binary: {self._to_binary(num1)}")
            steps.append(f"Decimal: {num1}")
            steps.append(f"Hexadecimal: 0x{self._to_hex(num1)}")
            steps.append(f"Octal: 0o{self._to_octal(num1)}")
        elif num2 is not None:
            bin1 = self._to_binary(num1)
            bin2 = self._to_binary(num2)
            
            steps.append(f"Operation: {self._get_operation_display(operation)}")
            steps.append(f"Number 1 (binary): {bin1}")
            steps.append(f"Number 1 (decimal): {num1}")
            steps.append(f"Number 2 (binary): {bin2}")
            steps.append(f"Number 2 (decimal): {num2}")
            
            if operation in ['add', 'subtract', 'multiply', 'divide']:
                op_symbols = {'add': '+', 'subtract': '-', 'multiply': '×', 'divide': '÷'}
                symbol = op_symbols.get(operation, operation)
                steps.append(f"Calculation: {num1} {symbol} {num2} = {result}")
                steps.append(f"Result (binary): {self._to_binary(result)}")
                steps.append(f"Result (decimal): {result}")
                steps.append(f"Result (hex): 0x{self._to_hex(result)}")
                steps.append(f"Result (octal): 0o{self._to_octal(result)}")
            elif operation in ['and', 'or', 'xor', 'nand', 'nor']:
                steps.append(f"Bitwise {operation.upper()} operation performed bit by bit:")
                # Show bit-by-bit operation for small numbers
                bin1 = self._to_binary(num1)
                bin2 = self._to_binary(num2)
                max_len = max(len(bin1), len(bin2))
                bin1_padded = bin1.zfill(max_len)
                bin2_padded = bin2.zfill(max_len)
                result_bin = self._to_binary(result).zfill(max_len)
                
                if max_len <= 16:  # Only show bit-by-bit for numbers up to 16 bits
                    steps.append(f"  {bin1_padded}  (Number 1)")
                    steps.append(f"  {bin2_padded}  (Number 2)")
                    steps.append(f"  {'-' * max_len}  ({operation.upper()})")
                    steps.append(f"  {result_bin}  (Result)")
                
                steps.append(f"Result (binary): {self._to_binary(result)}")
                steps.append(f"Result (decimal): {result}")
                steps.append(f"Result (hex): 0x{self._to_hex(result)}")
                steps.append(f"Result (octal): 0o{self._to_octal(result)}")
        elif operation in ['not', 'left_shift', 'right_shift']:
            bin1 = self._to_binary(num1)
            steps.append(f"Operation: {self._get_operation_display(operation)}")
            steps.append(f"Number (binary): {bin1}")
            steps.append(f"Number (decimal): {num1}")
            
            if operation == 'not':
                steps.append(f"Bitwise NOT inverts all bits (0 becomes 1, 1 becomes 0)")
                # Show bit-by-bit for small numbers
                if len(bin1) <= 16:
                    steps.append(f"Original:  {bin1}")
                    result_bin = self._to_binary(result)
                    max_len = max(len(bin1), len(result_bin))
                    steps.append(f"NOT:      {' ' * (max_len - len(result_bin))}{result_bin}")
            
            if operation in ['left_shift', 'right_shift']:
                shift_amount = num2 if num2 is not None else 0
                symbol = '<<' if operation == 'left_shift' else '>>'
                steps.append(f"Shift amount: {shift_amount} bits")
                steps.append(f"Original (binary): {self._to_binary(num1)}")
                steps.append(f"Calculation: {num1} {symbol} {shift_amount} = {result}")
                if operation == 'left_shift':
                    steps.append(f"Left shift multiplies by 2^{shift_amount} = {2**shift_amount}")
                else:
                    steps.append(f"Right shift divides by 2^{shift_amount} = {2**shift_amount}")
            
            steps.append(f"Result (binary): {self._to_binary(result)}")
            steps.append(f"Result (decimal): {result}")
            steps.append(f"Result (hex): 0x{self._to_hex(result)}")
            steps.append(f"Result (octal): 0o{self._to_octal(result)}")
        
        return steps
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            operation = data.get('operation', 'add')
            num1_str = data.get('num1', '')
            num2_str = data.get('num2', '')
            input_base = data.get('input_base', 'binary')
            
            result = None
            error = None
            step_by_step = []
            
            # Parse first number
            num1, error1 = self._parse_number(num1_str, input_base)
            if error1:
                return JsonResponse({'success': False, 'error': f'Number 1: {error1}'}, status=400)
            
            # Handle conversion operation
            if operation == 'convert':
                result = num1
                step_by_step = self.prepare_step_by_step(num1, None, num1, operation, input_base)
                display_data = self.prepare_display_data(num1, None, num1, operation, input_base)
            # Handle single-operand operations
            elif operation in ['not']:
                result, error = self._calculate_bitwise_single(num1, operation)
                if not error:
                    step_by_step = self.prepare_step_by_step(num1, None, result, operation, input_base)
                    display_data = self.prepare_display_data(num1, None, result, operation, input_base)
            # Handle shift operations
            elif operation in ['left_shift', 'right_shift']:
                shift_amount_str = num2_str if num2_str else '0'
                shift_amount, error2 = self._parse_decimal(shift_amount_str)
                if error2:
                    return JsonResponse({'success': False, 'error': f'Shift amount: {error2}'}, status=400)
                
                result, error = self._calculate_shift(num1, shift_amount, operation)
                if not error:
                    step_by_step = self.prepare_step_by_step(num1, shift_amount, result, operation, input_base)
                    # For display, treat shift_amount as num2
                    display_data = self.prepare_display_data(num1, shift_amount, result, operation, input_base)
            # Handle two-operand operations
            else:
                num2, error2 = self._parse_number(num2_str, input_base)
                if error2:
                    return JsonResponse({'success': False, 'error': f'Number 2: {error2}'}, status=400)
                
                if operation in ['add', 'subtract', 'multiply', 'divide']:
                    result, error = self._calculate_binary_arithmetic(num1, num2, operation)
                elif operation in ['and', 'or', 'xor', 'nand', 'nor']:
                    result, error = self._calculate_bitwise(num1, num2, operation)
                else:
                    error = f"Unknown operation: {operation}"
                
                if not error:
                    step_by_step = self.prepare_step_by_step(num1, num2, result, operation, input_base)
                    display_data = self.prepare_display_data(num1, num2, result, operation, input_base)
            
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare chart data
            chart_data = {}
            try:
                if operation != 'convert' and operation != 'not':
                    num2_for_chart = num2 if num2 is not None else (shift_amount if operation in ['left_shift', 'right_shift'] else None)
                    chart_data = self.prepare_chart_data(num1, num2_for_chart, result, operation)
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
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Binary calculator error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
