from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HexCalculator(View):
    """
    Enhanced Professional Hexadecimal Calculator
    Converts between hex, decimal, binary, octal and performs arithmetic operations.
    """
    template_name = 'math_calculators/hex_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Hex Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_hex(self, value):
        """Validate hexadecimal input"""
        if not value:
            return None, 'Hexadecimal value cannot be empty.'
        
        # Remove common prefixes
        value = value.strip().upper()
        if value.startswith('0X'):
            value = value[2:]
        if value.startswith('#'):
            value = value[1:]
        
        # Validate hex characters
        if not re.match(r'^[0-9A-F]+$', value):
            return None, 'Invalid hexadecimal value. Use digits 0-9 and letters A-F.'
        
        return value, None
    
    def _hex_to_decimal(self, hex_value):
        """Convert hexadecimal to decimal"""
        try:
            return int(hex_value, 16)
        except:
            return None
    
    def _decimal_to_hex(self, decimal_value):
        """Convert decimal to hexadecimal"""
        try:
            return hex(int(decimal_value))[2:].upper()
        except:
            return None
    
    def _hex_to_binary(self, hex_value):
        """Convert hexadecimal to binary"""
        try:
            decimal = self._hex_to_decimal(hex_value)
            if decimal is None:
                return None
            return bin(decimal)[2:]
        except:
            return None
    
    def _hex_to_octal(self, hex_value):
        """Convert hexadecimal to octal"""
        try:
            decimal = self._hex_to_decimal(hex_value)
            if decimal is None:
                return None
            return oct(decimal)[2:]
        except:
            return None
    
    def _binary_to_hex(self, binary_value):
        """Convert binary to hexadecimal"""
        try:
            decimal = int(binary_value, 2)
            return hex(decimal)[2:].upper()
        except:
            return None
    
    def _octal_to_hex(self, octal_value):
        """Convert octal to hexadecimal"""
        try:
            decimal = int(octal_value, 8)
            return hex(decimal)[2:].upper()
        except:
            return None
    
    def _perform_arithmetic(self, hex1, hex2, operation):
        """Perform arithmetic operation on two hex numbers"""
        try:
            dec1 = self._hex_to_decimal(hex1)
            dec2 = self._hex_to_decimal(hex2)
            
            if dec1 is None or dec2 is None:
                return None
            
            if operation == '+':
                result = dec1 + dec2
            elif operation == '-':
                result = dec1 - dec2
            elif operation == '*':
                result = dec1 * dec2
            elif operation == '/':
                if dec2 == 0:
                    return None
                result = dec1 // dec2  # Integer division
            elif operation == '%':
                if dec2 == 0:
                    return None
                result = dec1 % dec2
            else:
                return None
            
            # Convert result back to hex
            return self._decimal_to_hex(result)
        except:
            return None
    
    def _prepare_step_by_step_conversion(self, hex_value, decimal, binary, octal):
        """Prepare step-by-step conversion solution"""
        steps = []
        
        steps.append(f"Given hexadecimal: {hex_value}")
        steps.append("")
        
        steps.append("Step 1: Convert to Decimal")
        steps.append(f"  Each hex digit represents a power of 16:")
        hex_digits = list(hex_value)
        hex_digits.reverse()
        decimal_parts = []
        for i, digit in enumerate(hex_digits):
            digit_value = int(digit, 16)
            power = 16 ** i
            product = digit_value * power
            decimal_parts.append(f"{digit} × 16^{i} = {digit_value} × {power} = {product}")
        steps.extend(decimal_parts)
        steps.append(f"  Sum: {decimal}")
        steps.append("")
        
        steps.append("Step 2: Convert to Binary")
        steps.append(f"  Decimal {decimal} in binary:")
        binary_steps = []
        temp = decimal
        while temp > 0:
            remainder = temp % 2
            binary_steps.append(f"  {temp} ÷ 2 = {temp // 2} remainder {remainder}")
            temp = temp // 2
        steps.extend(binary_steps)
        steps.append(f"  Reading remainders from bottom to top: {binary}")
        steps.append("")
        
        steps.append("Step 3: Convert to Octal")
        steps.append(f"  Decimal {decimal} in octal:")
        octal_steps = []
        temp = decimal
        while temp > 0:
            remainder = temp % 8
            octal_steps.append(f"  {temp} ÷ 8 = {temp // 8} remainder {remainder}")
            temp = temp // 8
        steps.extend(octal_steps)
        steps.append(f"  Reading remainders from bottom to top: {octal}")
        
        return steps
    
    def _prepare_step_by_step_arithmetic(self, hex1, hex2, operation, result):
        """Prepare step-by-step arithmetic solution"""
        steps = []
        
        dec1 = self._hex_to_decimal(hex1)
        dec2 = self._hex_to_decimal(hex2)
        result_dec = self._hex_to_decimal(result)
        
        steps.append(f"Given: {hex1} {operation} {hex2}")
        steps.append("")
        
        steps.append("Step 1: Convert to Decimal")
        steps.append(f"  {hex1}₁₆ = {dec1}₁₀")
        steps.append(f"  {hex2}₁₆ = {dec2}₁₀")
        steps.append("")
        
        steps.append(f"Step 2: Perform {operation} Operation")
        if operation == '+':
            steps.append(f"  {dec1} + {dec2} = {result_dec}")
        elif operation == '-':
            steps.append(f"  {dec1} - {dec2} = {result_dec}")
        elif operation == '*':
            steps.append(f"  {dec1} × {dec2} = {result_dec}")
        elif operation == '/':
            steps.append(f"  {dec1} ÷ {dec2} = {result_dec} (integer division)")
        elif operation == '%':
            steps.append(f"  {dec1} mod {dec2} = {result_dec}")
        steps.append("")
        
        steps.append("Step 3: Convert Result to Hexadecimal")
        steps.append(f"  {result_dec}₁₀ = {result}₁₆")
        
        return steps
    
    def _prepare_chart_data(self, hex_value, decimal, binary, octal):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        # Number system comparison
        chart_data['number_systems'] = {
            'type': 'bar',
            'data': {
                'labels': ['Hexadecimal', 'Decimal', 'Binary', 'Octal'],
                'datasets': [{
                    'label': 'Value (as Decimal)',
                    'data': [decimal, decimal, decimal, decimal],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.6)',
                        'rgba(16, 185, 129, 0.6)',
                        'rgba(139, 92, 246, 0.6)',
                        'rgba(245, 158, 11, 0.6)'
                    ],
                    'borderColor': [
                        '#3b82f6',
                        '#10b981',
                        '#8b5cf6',
                        '#f59e0b'
                    ],
                    'borderWidth': 2
                }]
            }
        }
        
        # Bit representation (for smaller numbers)
        if decimal <= 255:
            binary_bits = list(binary.zfill(8))
            chart_data['bit_representation'] = {
                'type': 'bar',
                'data': {
                    'labels': [f'Bit {7-i}' for i in range(8)],
                    'datasets': [{
                        'label': 'Bit Value',
                        'data': [int(bit) for bit in binary_bits],
                        'backgroundColor': [
                            '#10b981' if bit == '1' else '#e5e7eb'
                            for bit in binary_bits
                        ],
                        'borderColor': [
                            '#059669' if bit == '1' else '#9ca3af'
                            for bit in binary_bits
                        ],
                        'borderWidth': 1
                    }]
                }
            }
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'convert')
            
            if calc_type == 'convert':
                # Conversion mode
                hex_value = data.get('hex_value', '')
                hex_value, error = self._validate_hex(hex_value)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                # Convert to other bases
                decimal = self._hex_to_decimal(hex_value)
                if decimal is None:
                    return JsonResponse({'success': False, 'error': 'Invalid hexadecimal value.'}, status=400)
                
                binary = self._hex_to_binary(hex_value)
                octal = self._hex_to_octal(hex_value)
                
                # Prepare step-by-step
                step_by_step = self._prepare_step_by_step_conversion(hex_value, decimal, binary, octal)
                
                # Prepare chart data
                chart_data = {}
                try:
                    chart_data = self._prepare_chart_data(hex_value, decimal, binary, octal)
                except Exception as e:
                    import traceback
                    print(f"Chart data preparation error: {traceback.format_exc()}")
                    chart_data = {}
                
                response = {
                    'success': True,
                    'calc_type': 'convert',
                    'hex': hex_value,
                    'decimal': decimal,
                    'binary': binary,
                    'octal': octal,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
                
            elif calc_type == 'arithmetic':
                # Arithmetic mode
                hex1 = data.get('hex1', '')
                hex2 = data.get('hex2', '')
                operation = data.get('operation', '+')
                
                hex1, error1 = self._validate_hex(hex1)
                if error1:
                    return JsonResponse({'success': False, 'error': f'First number: {error1}'}, status=400)
                
                hex2, error2 = self._validate_hex(hex2)
                if error2:
                    return JsonResponse({'success': False, 'error': f'Second number: {error2}'}, status=400)
                
                if operation not in ['+', '-', '*', '/', '%']:
                    return JsonResponse({'success': False, 'error': 'Invalid operation.'}, status=400)
                
                result = self._perform_arithmetic(hex1, hex2, operation)
                if result is None:
                    return JsonResponse({'success': False, 'error': 'Invalid calculation (possibly division by zero).'}, status=400)
                
                # Get decimal values for display
                dec1 = self._hex_to_decimal(hex1)
                dec2 = self._hex_to_decimal(hex2)
                result_dec = self._hex_to_decimal(result)
                
                # Prepare step-by-step
                step_by_step = self._prepare_step_by_step_arithmetic(hex1, hex2, operation, result)
                
                response = {
                    'success': True,
                    'calc_type': 'arithmetic',
                    'hex1': hex1,
                    'hex2': hex2,
                    'operation': operation,
                    'result': result,
                    'decimal1': dec1,
                    'decimal2': dec2,
                    'result_decimal': result_dec,
                    'step_by_step': step_by_step
                }
                
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Hex Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
