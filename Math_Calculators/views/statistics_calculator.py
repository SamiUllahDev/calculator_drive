from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
import statistics


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StatisticsCalculator(View):
    """
    Enhanced Professional Statistics Calculator
    Calculates comprehensive statistics including mean, median, mode, standard deviation, variance, quartiles, and more.
    """
    template_name = 'math_calculators/statistics_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Statistics Calculator',
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
    
    def _calculate_all_statistics(self, numbers):
        """Calculate comprehensive statistics"""
        if len(numbers) == 0:
            return None, "At least one number is required."
        
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        
        # Basic statistics
        mean = statistics.mean(numbers)
        median = statistics.median(numbers)
        
        try:
            mode = statistics.mode(numbers)
        except:
            mode = None
        
        # Measures of spread
        if n > 1:
            stdev = statistics.stdev(numbers)
            variance = statistics.variance(numbers)
        else:
            stdev = 0
            variance = 0
        
        minimum = min(numbers)
        maximum = max(numbers)
        range_val = maximum - minimum
        sum_val = sum(numbers)
        
        # Quartiles
        if n > 0:
            q1_index = n // 4
            q2_index = n // 2
            q3_index = (3 * n) // 4
            
            q1 = sorted_numbers[q1_index] if q1_index < n else sorted_numbers[0]
            q2 = sorted_numbers[q2_index] if q2_index < n else sorted_numbers[-1]
            q3 = sorted_numbers[q3_index] if q3_index < n else sorted_numbers[-1]
            
            iqr = q3 - q1
        else:
            q1 = q2 = q3 = iqr = 0
        
        # Percentiles
        def percentile(data, p):
            if len(data) == 0:
                return 0
            k = (len(data) - 1) * p
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return data[int(k)]
            d0 = data[int(f)] * (c - k)
            d1 = data[int(c)] * (k - f)
            return d0 + d1
        
        p25 = percentile(sorted_numbers, 0.25)
        p50 = percentile(sorted_numbers, 0.50)
        p75 = percentile(sorted_numbers, 0.75)
        p90 = percentile(sorted_numbers, 0.90)
        p95 = percentile(sorted_numbers, 0.95)
        p99 = percentile(sorted_numbers, 0.99)
        
        # Skewness (simplified)
        if n > 2 and stdev > 0:
            skewness = sum(((x - mean) / stdev) ** 3 for x in numbers) / n
        else:
            skewness = 0
        
        # Kurtosis (simplified)
        if n > 2 and stdev > 0:
            kurtosis = sum(((x - mean) / stdev) ** 4 for x in numbers) / n - 3
        else:
            kurtosis = 0
        
        # Frequency distribution
        frequency = {}
        for num in numbers:
            frequency[num] = frequency.get(num, 0) + 1
        
        return {
            'count': n,
            'sum': sum_val,
            'mean': mean,
            'median': median,
            'mode': mode,
            'stdev': stdev,
            'variance': variance,
            'minimum': minimum,
            'maximum': maximum,
            'range': range_val,
            'q1': q1,
            'q2': q2,
            'q3': q3,
            'iqr': iqr,
            'p25': p25,
            'p50': p50,
            'p75': p75,
            'p90': p90,
            'p95': p95,
            'p99': p99,
            'skewness': skewness,
            'kurtosis': kurtosis,
            'frequency': frequency
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
        
        steps.append("Step 1: Basic Statistics")
        steps.append(f"  Count (n) = {stats['count']}")
        steps.append(f"  Sum = {stats['sum']:.6f}")
        steps.append(f"  Mean = Sum / n = {stats['sum']:.6f} / {stats['count']} = {stats['mean']:.6f}")
        steps.append("")
        
        sorted_nums = sorted(numbers)
        steps.append("Step 2: Median")
        if stats['count'] % 2 == 0:
            mid1 = sorted_nums[stats['count'] // 2 - 1]
            mid2 = sorted_nums[stats['count'] // 2]
            steps.append(f"  Median = ({mid1} + {mid2}) / 2 = {stats['median']:.6f}")
        else:
            steps.append(f"  Median = {sorted_nums[stats['count'] // 2]:.6f}")
        steps.append("")
        
        if stats['mode'] is not None:
            steps.append("Step 3: Mode")
            steps.append(f"  Mode = {stats['mode']:.6f} (most frequent value)")
            steps.append("")
        
        steps.append("Step 4: Measures of Spread")
        steps.append(f"  Minimum = {stats['minimum']:.6f}")
        steps.append(f"  Maximum = {stats['maximum']:.6f}")
        steps.append(f"  Range = Maximum - Minimum = {stats['range']:.6f}")
        steps.append("")
        
        if stats['count'] > 1:
            steps.append("Step 5: Standard Deviation and Variance")
            steps.append(f"  Variance = Σ(x - x̄)² / (n-1) = {stats['variance']:.6f}")
            steps.append(f"  Standard Deviation = √(Variance) = {stats['stdev']:.6f}")
            steps.append("")
        
        steps.append("Step 6: Quartiles")
        steps.append(f"  Q1 (First Quartile) = {stats['q1']:.6f}")
        steps.append(f"  Q2 (Median) = {stats['q2']:.6f}")
        steps.append(f"  Q3 (Third Quartile) = {stats['q3']:.6f}")
        steps.append(f"  IQR (Interquartile Range) = Q3 - Q1 = {stats['iqr']:.6f}")
        
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
            
            # Box plot data (for visualization)
            chart_data['box_plot_data'] = {
                'min': stats['minimum'],
                'q1': stats['q1'],
                'median': stats['median'],
                'q3': stats['q3'],
                'max': stats['maximum'],
                'mean': stats['mean']
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
            
            # Parse numbers
            numbers, error = self._parse_numbers(numbers_str)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate statistics
            stats, error = self._calculate_all_statistics(numbers)
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
                **stats,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Statistics Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
