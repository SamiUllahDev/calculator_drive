from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
import statistics


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StandardDeviationCalculator(View):
    """
    Enhanced Professional Standard Deviation Calculator
    Calculates standard deviation, variance, mean, and other statistics with step-by-step solutions.
    """
    template_name = 'math_calculators/standard_deviation_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Standard Deviation Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, 'Invalid number.'
            return num, None
        except (ValueError, TypeError):
            return None, 'Must be a valid number.'
    
    def _parse_numbers(self, numbers_str):
        """Parse numbers from string input"""
        if not numbers_str or numbers_str.strip() == '':
            return [], "Please enter at least one number."
        
        numbers = []
        # Support comma, space, or newline separated
        for item in numbers_str.replace('\n', ',').replace(' ', ',').split(','):
            item = item.strip()
            if item:
                num, error = self._validate_number(item)
                if error:
                    return None, f"Invalid number: {item}"
                numbers.append(num)
        
        if len(numbers) == 0:
            return None, "Please enter at least one number."
        
        return numbers, None
    
    def _calculate_statistics(self, numbers, is_sample=True):
        """Calculate all statistics"""
        if len(numbers) < 2 and is_sample:
            return None, "At least 2 numbers are required for sample standard deviation."
        
        mean = statistics.mean(numbers)
        median = statistics.median(numbers)
        
        try:
            mode = statistics.mode(numbers)
        except:
            mode = None
        
        if is_sample:
            if len(numbers) < 2:
                stdev = 0
                variance = 0
            else:
                stdev = statistics.stdev(numbers)
                variance = statistics.variance(numbers)
        else:
            if len(numbers) < 1:
                stdev = 0
                variance = 0
            else:
                # Population standard deviation
                variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
                stdev = math.sqrt(variance)
        
        # Additional statistics
        minimum = min(numbers)
        maximum = max(numbers)
        range_val = maximum - minimum
        sum_val = sum(numbers)
        count = len(numbers)
        
        # Quartiles
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        if n > 0:
            q1_index = n // 4
            q2_index = n // 2
            q3_index = (3 * n) // 4
            
            q1 = sorted_numbers[q1_index] if q1_index < n else sorted_numbers[0]
            q2 = sorted_numbers[q2_index] if q2_index < n else sorted_numbers[-1]
            q3 = sorted_numbers[q3_index] if q3_index < n else sorted_numbers[-1]
        else:
            q1 = q2 = q3 = 0
        
        return {
            'mean': mean,
            'median': median,
            'mode': mode,
            'stdev': stdev,
            'variance': variance,
            'minimum': minimum,
            'maximum': maximum,
            'range': range_val,
            'sum': sum_val,
            'count': count,
            'q1': q1,
            'q2': q2,
            'q3': q3,
            'is_sample': is_sample
        }, None
    
    def _prepare_step_by_step(self, numbers, stats):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given: {len(numbers)} number(s)")
        if len(numbers) <= 20:
            steps.append(f"  Data: {', '.join(map(str, numbers))}")
        else:
            steps.append(f"  First 10: {', '.join(map(str, numbers[:10]))}")
            steps.append(f"  ... ({len(numbers) - 10} more numbers)")
        steps.append("")
        
        steps.append("Step 1: Calculate mean")
        steps.append(f"  Mean (μ) = Sum of all values / Count")
        steps.append(f"  Mean = {stats['sum']} / {stats['count']}")
        steps.append(f"  Mean = {stats['mean']:.6f}")
        steps.append("")
        
        steps.append("Step 2: Calculate deviations from mean")
        deviations = [(x - stats['mean']) for x in numbers]
        if len(numbers) <= 10:
            for i, (num, dev) in enumerate(zip(numbers, deviations)):
                steps.append(f"  ({num} - {stats['mean']:.6f}) = {dev:.6f}")
        else:
            steps.append(f"  Calculating deviations for all {len(numbers)} numbers...")
        steps.append("")
        
        steps.append("Step 3: Square the deviations")
        squared_deviations = [dev ** 2 for dev in deviations]
        sum_squared = sum(squared_deviations)
        if len(numbers) <= 10:
            for i, (dev, sq_dev) in enumerate(zip(deviations, squared_deviations)):
                steps.append(f"  ({dev:.6f})² = {sq_dev:.6f}")
        else:
            steps.append(f"  Sum of squared deviations = {sum_squared:.6f}")
        steps.append("")
        
        steps.append("Step 4: Calculate variance")
        if stats['is_sample']:
            steps.append(f"  Sample Variance (s²) = Sum of squared deviations / (n - 1)")
            steps.append(f"  Variance = {sum_squared} / ({stats['count']} - 1)")
            steps.append(f"  Variance = {sum_squared} / {stats['count'] - 1}")
            steps.append(f"  Variance = {stats['variance']:.6f}")
        else:
            steps.append(f"  Population Variance (σ²) = Sum of squared deviations / n")
            steps.append(f"  Variance = {sum_squared} / {stats['count']}")
            steps.append(f"  Variance = {stats['variance']:.6f}")
        steps.append("")
        
        steps.append("Step 5: Calculate standard deviation")
        if stats['is_sample']:
            steps.append(f"  Sample Standard Deviation (s) = √(Variance)")
        else:
            steps.append(f"  Population Standard Deviation (σ) = √(Variance)")
        steps.append(f"  Standard Deviation = √{stats['variance']:.6f}")
        steps.append(f"  Standard Deviation = {stats['stdev']:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, numbers, stats):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if not numbers:
                return chart_data
            
            # Frequency distribution histogram
            num_bins = min(20, max(5, len(numbers) // 5))
            if num_bins < 2:
                num_bins = 2
            
            min_val = stats['minimum']
            max_val = stats['maximum']
            bin_width = (max_val - min_val) / num_bins if max_val != min_val else 1
            
            bins = [min_val + i * bin_width for i in range(num_bins + 1)]
            histogram = [0] * num_bins
            
            for num in numbers:
                if max_val == min_val:
                    bin_index = 0
                else:
                    bin_index = min(int((num - min_val) / bin_width), num_bins - 1)
                histogram[bin_index] += 1
            
            bin_labels = [f'{bins[i]:.2f}-{bins[i+1]:.2f}' for i in range(num_bins)]
            
            chart_data['histogram_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': bin_labels,
                    'datasets': [{
                        'label': 'Frequency',
                        'data': histogram,
                        'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                        'borderColor': '#3b82f6',
                        'borderWidth': 1
                    }]
                }
            }
            
            # Statistics comparison chart
            chart_data['statistics_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Mean', 'Median', 'Min', 'Max', 'Q1', 'Q3'],
                    'datasets': [{
                        'label': 'Value',
                        'data': [stats['mean'], stats['median'], stats['minimum'], 
                                stats['maximum'], stats['q1'], stats['q3']],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(239, 68, 68, 0.6)',
                            'rgba(139, 92, 246, 0.6)',
                            'rgba(236, 72, 153, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444',
                            '#8b5cf6',
                            '#ec4899'
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
            
            numbers_str = data.get('numbers', '')
            is_sample = data.get('is_sample', 'true').lower() == 'true'
            
            # Parse numbers
            numbers, error = self._parse_numbers(numbers_str)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate statistics
            stats, error = self._calculate_statistics(numbers, is_sample)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(numbers, stats)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(numbers, stats)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                'numbers': numbers,
                'is_sample': is_sample,
                **stats,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Standard Deviation Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
