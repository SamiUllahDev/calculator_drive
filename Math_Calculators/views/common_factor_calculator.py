from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from sympy import gcd, divisors


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CommonFactorCalculator(View):
    """
    Professional Common Factor Calculator
    Finds all common factors between two or more numbers.
    Includes step-by-step solutions and visualizations.
    """
    template_name = 'math_calculators/common_factor_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Common Factor Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_integer(self, value, name):
        """Validate that a value is a positive integer"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num <= 0:
                return None, f'{name} must be greater than zero.'
            if num != int(num):
                return None, f'{name} must be an integer (whole number).'
            if num > 1e10:  # Prevent extremely large numbers
                return None, f'{name} is too large. Maximum value is 10,000,000,000.'
            return int(num), None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid integer.'
    
    def _get_all_factors(self, num):
        """Get all factors of a number using SymPy"""
        try:
            # Use SymPy divisors for efficient factorization
            factors = divisors(num)
            # Convert to sorted list and remove negative factors
            factors_list = sorted([int(f) for f in factors if f > 0])
            return factors_list
        except Exception:
            # Fallback method
            factors = []
            for i in range(1, int(math.sqrt(num)) + 1):
                if num % i == 0:
                    factors.append(i)
                    if i != num // i:
                        factors.append(num // i)
            return sorted(factors)
    
    def _find_common_factors(self, numbers):
        """Find all common factors between numbers"""
        if not numbers or len(numbers) < 2:
            return []
        
        # Get factors for each number
        all_factors = []
        for num in numbers:
            factors = self._get_all_factors(num)
            all_factors.append(set(factors))
        
        # Find intersection of all factor sets
        common_factors = all_factors[0]
        for factor_set in all_factors[1:]:
            common_factors = common_factors.intersection(factor_set)
        
        return sorted(list(common_factors))
    
    def _calculate_gcf(self, numbers):
        """Calculate Greatest Common Factor using SymPy"""
        if len(numbers) < 2:
            return None
        
        result = numbers[0]
        for num in numbers[1:]:
            result = int(gcd(result, num))
        
        return result
    
    def prepare_chart_data(self, numbers, common_factors, gcf):
        """Prepare chart data for factor visualization"""
        if not numbers or len(numbers) == 0:
            return {}
        
        # Factor comparison chart - show factors of each number
        max_num = max(numbers)
        max_factors = min(20, max_num)  # Limit to 20 factors for readability
        
        # Get factors for each number (limited)
        number_factors = {}
        for num in numbers:
            factors = self._get_all_factors(num)
            # Limit factors for chart
            limited_factors = [f for f in factors if f <= max_factors]
            number_factors[num] = limited_factors
        
        # Create labels (factor values)
        all_factor_values = set()
        for factors in number_factors.values():
            all_factor_values.update(factors)
        factor_labels = sorted([f for f in all_factor_values if f <= max_factors])
        
        # Create datasets for each number
        datasets = []
        colors = [
            {'bg': 'rgba(59, 130, 246, 0.6)', 'border': '#3b82f6'},
            {'bg': 'rgba(16, 185, 129, 0.6)', 'border': '#10b981'},
            {'bg': 'rgba(245, 158, 11, 0.6)', 'border': '#f59e0b'},
            {'bg': 'rgba(139, 92, 246, 0.6)', 'border': '#8b5cf6'},
            {'bg': 'rgba(236, 72, 153, 0.6)', 'border': '#ec4899'}
        ]
        
        for idx, num in enumerate(numbers):
            color = colors[idx % len(colors)]
            data = [1 if factor in number_factors[num] else 0 for factor in factor_labels]
            datasets.append({
                'label': f'Number {num}',
                'data': data,
                'backgroundColor': color['bg'],
                'borderColor': color['border'],
                'borderWidth': 1
            })
        
        # Add common factors dataset
        common_data = [1 if factor in common_factors and factor <= max_factors else 0 for factor in factor_labels]
        datasets.append({
            'label': 'Common Factors',
            'data': common_data,
            'backgroundColor': 'rgba(239, 68, 68, 0.8)',
            'borderColor': '#ef4444',
            'borderWidth': 2
        })
        
        factor_comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(f) for f in factor_labels],
                'datasets': datasets
            }
        }
        
        # GCF Gauge Chart
        if gcf and gcf > 0:
            max_gcf = max(numbers)  # Use max number as reference
            gcf_percentage = min((gcf / max_gcf) * 100, 100) if max_gcf > 0 else 0
            
            gcf_gauge_chart = {
                'type': 'doughnut',
                'data': {
                    'labels': ['GCF', 'Remaining'],
                    'datasets': [{
                        'data': [round(gcf_percentage, 2), round(100 - gcf_percentage, 2)],
                        'backgroundColor': ['#ef4444', '#e5e7eb'],
                        'borderWidth': 0,
                        'cutout': '75%'
                    }]
                },
                'center_text': {
                    'value': gcf,
                    'label': 'GCF',
                    'color': '#ef4444'
                }
            }
        else:
            gcf_gauge_chart = None
        
        # Common factors count chart
        if common_factors:
            factor_count_data = {
                'type': 'bar',
                'data': {
                    'labels': ['Common Factors'],
                    'datasets': [{
                        'label': 'Count',
                        'data': [len(common_factors)],
                        'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                        'borderColor': '#3b82f6',
                        'borderWidth': 2,
                        'borderRadius': 8
                    }]
                }
            }
        else:
            factor_count_data = None
        
        chart_data = {
            'factor_comparison_chart': factor_comparison_chart
        }
        
        if gcf_gauge_chart:
            chart_data['gcf_gauge_chart'] = gcf_gauge_chart
        
        if factor_count_data:
            chart_data['factor_count_chart'] = factor_count_data
        
        return chart_data
    
    def prepare_display_data(self, numbers, common_factors, gcf):
        """Prepare formatted display data for frontend"""
        display_data = {
            'numbers': numbers,
            'numbers_count': len(numbers),
            'common_factors': common_factors,
            'common_factors_count': len(common_factors),
            'gcf': gcf,
            'detailed_results': []
        }
        
        # Add number factors
        for num in numbers:
            factors = self._get_all_factors(num)
            display_data['detailed_results'].append({
                'label': f'Factors of {num}',
                'value': ', '.join(map(str, factors)),
                'count': len(factors),
                'is_primary': False
            })
        
        # Add common factors
        if common_factors:
            display_data['detailed_results'].append({
                'label': 'Common Factors',
                'value': ', '.join(map(str, common_factors)),
                'count': len(common_factors),
                'is_primary': True
            })
        else:
            display_data['detailed_results'].append({
                'label': 'Common Factors',
                'value': 'None',
                'count': 0,
                'is_primary': True
            })
        
        # Add GCF
        if gcf:
            display_data['detailed_results'].append({
                'label': 'Greatest Common Factor (GCF)',
                'value': str(gcf),
                'count': 1,
                'is_primary': True
            })
        
        return display_data
    
    def prepare_step_by_step(self, numbers, common_factors, gcf):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given numbers: {', '.join(map(str, numbers))}")
        steps.append(f"Step 1: Find all factors of each number")
        
        # Show factors for each number
        for num in numbers:
            factors = self._get_all_factors(num)
            steps.append(f"  Factors of {num}: {', '.join(map(str, factors))}")
        
        steps.append(f"Step 2: Identify common factors")
        if common_factors:
            steps.append(f"  Common factors are numbers that appear in all factor lists")
            steps.append(f"  Common factors: {', '.join(map(str, common_factors))}")
        else:
            steps.append(f"  No common factors found (except 1, which is always a common factor)")
            steps.append(f"  Note: If numbers are coprime, they only share 1 as a common factor")
        
        if gcf:
            steps.append(f"Step 3: Find the Greatest Common Factor (GCF)")
            steps.append(f"  GCF = {gcf}")
            steps.append(f"  This is the largest number that divides all given numbers")
        
        # Show prime factorization if helpful
        if len(numbers) == 2 and gcf and gcf > 1:
            steps.append(f"Step 4: Verification")
            steps.append(f"  {numbers[0]} ÷ {gcf} = {numbers[0] // gcf}")
            steps.append(f"  {numbers[1]} ÷ {gcf} = {numbers[1] // gcf}")
        
        return steps
    
    def prepare_step_by_step_html(self, steps):
        """Prepare step-by-step solution as HTML structure"""
        if not steps or not isinstance(steps, list):
            return []
        
        return [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(steps)]
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get numbers from input
            numbers_input = data.get('numbers', [])
            if isinstance(numbers_input, str):
                # Try to parse comma-separated string
                try:
                    numbers_input = [int(float(x.strip())) for x in numbers_input.split(',')]
                except:
                    numbers_input = []
            
            # Validate we have at least 2 numbers
            if not numbers_input or len(numbers_input) < 2:
                return JsonResponse({'success': False, 'error': 'Please provide at least 2 numbers.'}, status=400)
            
            # Validate all numbers
            validated_numbers = []
            for idx, num_str in enumerate(numbers_input):
                num, error = self._validate_positive_integer(num_str, f'Number {idx + 1}')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                validated_numbers.append(num)
            
            # Find common factors
            common_factors = self._find_common_factors(validated_numbers)
            
            # Calculate GCF
            gcf = self._calculate_gcf(validated_numbers)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self.prepare_chart_data(validated_numbers, common_factors, gcf)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare display data
            display_data = self.prepare_display_data(validated_numbers, common_factors, gcf)
            
            # Prepare step-by-step solution
            step_by_step = self.prepare_step_by_step(validated_numbers, common_factors, gcf)
            step_by_step_html = self.prepare_step_by_step_html(step_by_step)
            
            # Prepare response
            response = {
                'success': True,
                'numbers': validated_numbers,
                'common_factors': common_factors,
                'gcf': gcf,
                'chart_data': chart_data,
                'display_data': display_data,
                'step_by_step': step_by_step,
                'step_by_step_html': step_by_step_html
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Common Factor Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
