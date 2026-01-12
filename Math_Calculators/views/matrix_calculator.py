from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import Matrix, eye, zeros, ones
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MatrixCalculator(View):
    """
    Enhanced Professional Matrix Calculator
    Performs matrix operations: addition, subtraction, multiplication, transpose, determinant, inverse.
    """
    template_name = 'math_calculators/matrix_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Matrix Calculator',
        }
        return render(request, self.template_name, context)
    
    def _parse_matrix(self, matrix_str, rows, cols):
        """Parse matrix from string input"""
        try:
            # Remove brackets and split
            matrix_str = matrix_str.strip()
            matrix_str = matrix_str.replace('[', '').replace(']', '')
            
            # Split by rows (semicolon or newline)
            if ';' in matrix_str:
                rows_str = matrix_str.split(';')
            elif '\n' in matrix_str:
                rows_str = matrix_str.split('\n')
            else:
                # Single row
                rows_str = [matrix_str]
            
            matrix = []
            for row_str in rows_str:
                row_str = row_str.strip()
                if not row_str:
                    continue
                # Split by comma or space
                if ',' in row_str:
                    elements = [float(x.strip()) for x in row_str.split(',')]
                else:
                    elements = [float(x.strip()) for x in row_str.split()]
                matrix.append(elements)
            
            # Validate dimensions
            if len(matrix) != rows:
                return None, f'Matrix must have {rows} rows.'
            
            for i, row in enumerate(matrix):
                if len(row) != cols:
                    return None, f'Row {i+1} must have {cols} columns.'
            
            return matrix, None
        except (ValueError, TypeError) as e:
            return None, f'Invalid matrix format: {str(e)}'
    
    def _validate_matrix_dimensions(self, matrix1, matrix2, operation):
        """Validate matrix dimensions for operations"""
        rows1, cols1 = len(matrix1), len(matrix1[0])
        rows2, cols2 = len(matrix2), len(matrix2[0])
        
        if operation in ['add', 'subtract']:
            if rows1 != rows2 or cols1 != cols2:
                return False, f'Matrices must have the same dimensions for {operation}.'
        elif operation == 'multiply':
            if cols1 != rows2:
                return False, f'Number of columns of first matrix ({cols1}) must equal number of rows of second matrix ({rows2}) for multiplication.'
        
        return True, None
    
    def _matrix_add(self, matrix1, matrix2):
        """Add two matrices"""
        result = []
        for i in range(len(matrix1)):
            row = []
            for j in range(len(matrix1[0])):
                row.append(matrix1[i][j] + matrix2[i][j])
            result.append(row)
        return result
    
    def _matrix_subtract(self, matrix1, matrix2):
        """Subtract two matrices"""
        result = []
        for i in range(len(matrix1)):
            row = []
            for j in range(len(matrix1[0])):
                row.append(matrix1[i][j] - matrix2[i][j])
            result.append(row)
        return result
    
    def _matrix_multiply(self, matrix1, matrix2):
        """Multiply two matrices"""
        rows1, cols1 = len(matrix1), len(matrix1[0])
        rows2, cols2 = len(matrix2), len(matrix2[0])
        
        result = [[0 for _ in range(cols2)] for _ in range(rows1)]
        
        for i in range(rows1):
            for j in range(cols2):
                for k in range(cols1):
                    result[i][j] += matrix1[i][k] * matrix2[k][j]
        
        return result
    
    def _matrix_transpose(self, matrix):
        """Transpose a matrix"""
        rows, cols = len(matrix), len(matrix[0])
        result = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for i in range(rows):
            for j in range(cols):
                result[j][i] = matrix[i][j]
        
        return result
    
    def _matrix_determinant(self, matrix):
        """Calculate determinant using SymPy"""
        try:
            sympy_matrix = Matrix(matrix)
            return float(sympy_matrix.det())
        except:
            # Fallback for 2x2
            if len(matrix) == 2 and len(matrix[0]) == 2:
                return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
            return None
    
    def _matrix_inverse(self, matrix):
        """Calculate matrix inverse using SymPy"""
        try:
            sympy_matrix = Matrix(matrix)
            inverse = sympy_matrix.inv()
            result = []
            for i in range(inverse.rows):
                row = []
                for j in range(inverse.cols):
                    val = inverse[i, j]
                    if isinstance(val, float) or isinstance(val, int):
                        row.append(float(val))
                    else:
                        row.append(float(val.evalf()))
                result.append(row)
            return result, None
        except Exception as e:
            return None, str(e)
    
    def _prepare_step_by_step(self, operation, matrix1, matrix2, result, rows1, cols1, rows2=None, cols2=None):
        """Prepare step-by-step solution"""
        steps = []
        
        if operation == 'add':
            steps.append(f"Given: A + B")
            steps.append(f"  A = {self._format_matrix(matrix1)}")
            steps.append(f"  B = {self._format_matrix(matrix2)}")
            steps.append("")
            steps.append("Step 1: Add corresponding elements")
            for i in range(rows1):
                for j in range(cols1):
                    steps.append(f"  Result[{i+1}][{j+1}] = A[{i+1}][{j+1}] + B[{i+1}][{j+1}] = {matrix1[i][j]} + {matrix2[i][j]} = {result[i][j]}")
            steps.append("")
            steps.append(f"Result = {self._format_matrix(result)}")
            
        elif operation == 'subtract':
            steps.append(f"Given: A - B")
            steps.append(f"  A = {self._format_matrix(matrix1)}")
            steps.append(f"  B = {self._format_matrix(matrix2)}")
            steps.append("")
            steps.append("Step 1: Subtract corresponding elements")
            for i in range(rows1):
                for j in range(cols1):
                    steps.append(f"  Result[{i+1}][{j+1}] = A[{i+1}][{j+1}] - B[{i+1}][{j+1}] = {matrix1[i][j]} - {matrix2[i][j]} = {result[i][j]}")
            steps.append("")
            steps.append(f"Result = {self._format_matrix(result)}")
            
        elif operation == 'multiply':
            steps.append(f"Given: A × B")
            steps.append(f"  A = {self._format_matrix(matrix1)} ({rows1}×{cols1})")
            steps.append(f"  B = {self._format_matrix(matrix2)} ({rows2}×{cols2})")
            steps.append("")
            steps.append(f"Step 1: Matrix multiplication")
            steps.append(f"  Result will be {rows1}×{cols2} matrix")
            steps.append("")
            steps.append("Step 2: Calculate each element")
            for i in range(rows1):
                for j in range(cols2):
                    calc_parts = []
                    for k in range(cols1):
                        calc_parts.append(f"{matrix1[i][k]}×{matrix2[k][j]}")
                    calc_str = " + ".join(calc_parts)
                    steps.append(f"  Result[{i+1}][{j+1}] = {calc_str} = {result[i][j]}")
            steps.append("")
            steps.append(f"Result = {self._format_matrix(result)}")
            
        elif operation == 'transpose':
            steps.append(f"Given: A^T")
            steps.append(f"  A = {self._format_matrix(matrix1)} ({rows1}×{cols1})")
            steps.append("")
            steps.append("Step 1: Swap rows and columns")
            steps.append(f"  Transpose will be {cols1}×{rows1} matrix")
            for i in range(rows1):
                for j in range(cols1):
                    steps.append(f"  Result[{j+1}][{i+1}] = A[{i+1}][{j+1}] = {matrix1[i][j]}")
            steps.append("")
            steps.append(f"Result = {self._format_matrix(result)}")
            
        elif operation == 'determinant':
            steps.append(f"Given: det(A)")
            steps.append(f"  A = {self._format_matrix(matrix1)}")
            steps.append("")
            if rows1 == 2 and cols1 == 2:
                steps.append("Step 1: 2×2 Determinant Formula")
                steps.append(f"  det(A) = a₁₁ × a₂₂ - a₁₂ × a₂₁")
                steps.append(f"  det(A) = {matrix1[0][0]} × {matrix1[1][1]} - {matrix1[0][1]} × {matrix1[1][0]}")
                steps.append(f"  det(A) = {matrix1[0][0] * matrix1[1][1]} - {matrix1[0][1] * matrix1[1][0]}")
                steps.append(f"  det(A) = {result}")
            else:
                steps.append("Step 1: Calculate determinant using expansion")
                steps.append(f"  det(A) = {result}")
            steps.append("")
            steps.append(f"Result = {result}")
            
        elif operation == 'inverse':
            steps.append(f"Given: A⁻¹")
            steps.append(f"  A = {self._format_matrix(matrix1)}")
            steps.append("")
            steps.append("Step 1: Calculate determinant")
            det = self._matrix_determinant(matrix1)
            steps.append(f"  det(A) = {det}")
            if det == 0:
                steps.append("  Matrix is singular (determinant is 0), so it has no inverse.")
            else:
                steps.append("")
                steps.append("Step 2: Calculate inverse matrix")
                steps.append(f"  A⁻¹ = (1/det(A)) × adj(A)")
                steps.append(f"  A⁻¹ = {self._format_matrix(result)}")
            steps.append("")
            steps.append(f"Result = {self._format_matrix(result)}")
        
        return steps
    
    def _format_matrix(self, matrix):
        """Format matrix as string"""
        if not matrix:
            return "[]"
        rows = []
        for row in matrix:
            rows.append("[" + ", ".join([f"{x:.6f}".rstrip('0').rstrip('.') if abs(x) < 1e10 else f"{x:.2e}" for x in row]) + "]")
        return "[" + ", ".join(rows) + "]"
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            operation = data.get('operation', 'add')
            
            if operation in ['add', 'subtract', 'multiply']:
                # Two matrices needed
                matrix1_str = data.get('matrix1', '')
                matrix2_str = data.get('matrix2', '')
                rows1 = int(data.get('rows1', 2))
                cols1 = int(data.get('cols1', 2))
                rows2 = int(data.get('rows2', 2))
                cols2 = int(data.get('cols2', 2))
                
                matrix1, error1 = self._parse_matrix(matrix1_str, rows1, cols1)
                if error1:
                    return JsonResponse({'success': False, 'error': f'Matrix 1: {error1}'}, status=400)
                
                matrix2, error2 = self._parse_matrix(matrix2_str, rows2, cols2)
                if error2:
                    return JsonResponse({'success': False, 'error': f'Matrix 2: {error2}'}, status=400)
                
                # Validate dimensions
                valid, error = self._validate_matrix_dimensions(matrix1, matrix2, operation)
                if not valid:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                # Perform operation
                if operation == 'add':
                    result = self._matrix_add(matrix1, matrix2)
                elif operation == 'subtract':
                    result = self._matrix_subtract(matrix1, matrix2)
                else:  # multiply
                    result = self._matrix_multiply(matrix1, matrix2)
                
                # Prepare step-by-step
                result_rows = len(result)
                result_cols = len(result[0]) if result else 0
                step_by_step = self._prepare_step_by_step(operation, matrix1, matrix2, result, rows1, cols1, rows2, cols2)
                
                response = {
                    'success': True,
                    'operation': operation,
                    'matrix1': matrix1,
                    'matrix2': matrix2,
                    'result': result,
                    'rows1': rows1,
                    'cols1': cols1,
                    'rows2': rows2,
                    'cols2': cols2,
                    'result_rows': result_rows,
                    'result_cols': result_cols,
                    'step_by_step': step_by_step
                }
                
            elif operation in ['transpose', 'determinant', 'inverse']:
                # Single matrix needed
                matrix1_str = data.get('matrix1', '')
                rows1 = int(data.get('rows1', 2))
                cols1 = int(data.get('cols1', 2))
                
                matrix1, error1 = self._parse_matrix(matrix1_str, rows1, cols1)
                if error1:
                    return JsonResponse({'success': False, 'error': f'Matrix: {error1}'}, status=400)
                
                # Validate for specific operations
                if operation == 'determinant' or operation == 'inverse':
                    if rows1 != cols1:
                        return JsonResponse({'success': False, 'error': 'Matrix must be square (same number of rows and columns) for determinant and inverse.'}, status=400)
                
                # Perform operation
                if operation == 'transpose':
                    result = self._matrix_transpose(matrix1)
                    result_rows = len(result)
                    result_cols = len(result[0]) if result else 0
                    step_by_step = self._prepare_step_by_step(operation, matrix1, None, result, rows1, cols1)
                    
                    response = {
                        'success': True,
                        'operation': operation,
                        'matrix1': matrix1,
                        'result': result,
                        'rows1': rows1,
                        'cols1': cols1,
                        'result_rows': result_rows,
                        'result_cols': result_cols,
                        'step_by_step': step_by_step
                    }
                    
                elif operation == 'determinant':
                    result = self._matrix_determinant(matrix1)
                    if result is None:
                        return JsonResponse({'success': False, 'error': 'Could not calculate determinant.'}, status=400)
                    
                    step_by_step = self._prepare_step_by_step(operation, matrix1, None, result, rows1, cols1)
                    
                    response = {
                        'success': True,
                        'operation': operation,
                        'matrix1': matrix1,
                        'result': result,
                        'rows1': rows1,
                        'cols1': cols1,
                        'step_by_step': step_by_step
                    }
                    
                elif operation == 'inverse':
                    result, error = self._matrix_inverse(matrix1)
                    if error:
                        return JsonResponse({'success': False, 'error': f'Cannot calculate inverse: {error}'}, status=400)
                    
                    step_by_step = self._prepare_step_by_step(operation, matrix1, None, result, rows1, cols1)
                    
                    response = {
                        'success': True,
                        'operation': operation,
                        'matrix1': matrix1,
                        'result': result,
                        'rows1': rows1,
                        'cols1': cols1,
                        'result_rows': rows1,
                        'result_cols': cols1,
                        'step_by_step': step_by_step
                    }
            else:
                return JsonResponse({'success': False, 'error': 'Invalid operation.'}, status=400)
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Matrix Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
