from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
import statistics
from collections import Counter


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MeanMedianModeRangeCalculator(View):
    """
    Enhanced Professional Mean, Median, Mode, and Range Calculator
    Calculates statistical measures with step-by-step solutions and visualizations.
    """
    template_name = 'math_calculators/mean_median_mode_range_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Mean Median Mode Range Calculator',
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
        try:
            # Remove brackets and split
            numbers_str = numbers_str.strip()
            numbers_str = numbers_str.replace('[', '').replace(']', '')
            
            # Split by comma, space, or newline
            if ',' in numbers_str:
                numbers = [x.strip() for x in numbers_str.split(',')]
            elif '\n' in numbers_str:
                numbers = [x.strip() for x in numbers_str.split('\n')]
            else:
                numbers = numbers_str.split()
            
            # Validate and convert
            validated_numbers = []
            for num_str in numbers:
                if not num_str:
                    continue
                num, error = self._validate_number(num_str)
                if error:
                    return None, f'Invalid number: {num_str}'
                validated_numbers.append(num)
            
            if len(validated_numbers) < 1:
                return None, 'Please provide at least one number.'
            
            return validated_numbers, None
        except Exception as e:
            return None, f'Error parsing numbers: {str(e)}'
    
    def _calculate_mean(self, numbers):
        """Calculate mean (average)"""
        return sum(numbers) / len(numbers)
    
    def _calculate_median(self, numbers):
        """Calculate median"""
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        if n % 2 == 0:
            return (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
        else:
            return sorted_numbers[n//2]
    
    def _calculate_mode(self, numbers):
        """Calculate mode(s)"""
        if len(numbers) == 0:
            return []
        
        # Count frequencies
        counter = Counter(numbers)
        max_frequency = max(counter.values())
        
        # Find all values with max frequency
        modes = [num for num, freq in counter.items() if freq == max_frequency]
        
        # If all values have frequency 1, there's no mode
        if max_frequency == 1 and len(modes) == len(numbers):
            return []
        
        return sorted(modes)
    
    def _calculate_range(self, numbers):
        """Calculate range"""
        return max(numbers) - min(numbers)
    
    def _calculate_variance(self, numbers, mean):
        """Calculate variance"""
        if len(numbers) < 2:
            return 0
        squared_diffs = [(x - mean) ** 2 for x in numbers]
        return sum(squared_diffs) / len(numbers)
    
    def _calculate_standard_deviation(self, variance):
        """Calculate standard deviation"""
        return math.sqrt(variance)
    
    def _calculate_quartiles(self, numbers):
        """Calculate quartiles (Q1, Q2, Q3)"""
        sorted_numbers = sorted(numbers)
        n = len(sorted_numbers)
        
        # Q2 is the median
        q2 = self._calculate_median(sorted_numbers)
        
        # Q1 is median of lower half
        lower_half = sorted_numbers[:n//2]
        q1 = self._calculate_median(lower_half) if lower_half else sorted_numbers[0]
        
        # Q3 is median of upper half
        upper_start = n//2 if n % 2 == 0 else n//2 + 1
        upper_half = sorted_numbers[upper_start:]
        q3 = self._calculate_median(upper_half) if upper_half else sorted_numbers[-1]
        
        return q1, q2, q3
    
    def _calculate_iqr(self, q1, q3):
        """Calculate Interquartile Range"""
        return q3 - q1
    
    def _prepare_step_by_step(self, numbers, mean, median, mode, range_val, variance, std_dev, q1, q2, q3):
        """Prepare step-by-step solution"""
        steps = []
        
        sorted_numbers = sorted(numbers)
        n = len(numbers)
        
        steps.append(f"Given numbers: {', '.join(map(str, numbers))}")
        steps.append(f"Sorted: {', '.join(map(str, sorted_numbers))}")
        steps.append(f"Count (n): {n}")
        steps.append("")
        
        # Mean
        steps.append("Step 1: Calculate Mean (Average)")
        steps.append(f"  Mean = Sum of all numbers / Count")
        steps.append(f"  Mean = ({' + '.join(map(str, numbers))}) / {n}")
        steps.append(f"  Mean = {sum(numbers)} / {n}")
        steps.append(f"  Mean = {mean:.6f}")
        steps.append("")
        
        # Median
        steps.append("Step 2: Calculate Median")
        if n % 2 == 0:
            mid1 = sorted_numbers[n//2 - 1]
            mid2 = sorted_numbers[n//2]
            steps.append(f"  Even number of values: median is average of middle two values")
            steps.append(f"  Median = ({mid1} + {mid2}) / 2")
            steps.append(f"  Median = {median:.6f}")
        else:
            mid = sorted_numbers[n//2]
            steps.append(f"  Odd number of values: median is middle value")
            steps.append(f"  Median = {mid}")
        steps.append("")
        
        # Mode
        steps.append("Step 3: Calculate Mode")
        if mode:
            counter = Counter(numbers)
            max_freq = max(counter.values())
            modes_str = ', '.join(map(str, mode))
            steps.append(f"  Mode is the most frequently occurring value(s)")
            steps.append(f"  Frequency count: {dict(counter)}")
            steps.append(f"  Maximum frequency: {max_freq}")
            steps.append(f"  Mode(s): {modes_str}")
        else:
            steps.append(f"  No mode (all values occur with the same frequency)")
        steps.append("")
        
        # Range
        steps.append("Step 4: Calculate Range")
        steps.append(f"  Range = Maximum - Minimum")
        steps.append(f"  Range = {max(numbers)} - {min(numbers)}")
        steps.append(f"  Range = {range_val:.6f}")
        steps.append("")
        
        # Variance and Standard Deviation
        if n >= 2:
            steps.append("Step 5: Calculate Variance")
            steps.append(f"  Variance = Σ(x - mean)² / n")
            squared_diffs = [(x - mean) ** 2 for x in numbers]
            steps.append(f"  Variance = ({' + '.join([f'({x:.6f} - {mean:.6f})²' for x in numbers[:5]])}{'...' if n > 5 else ''}) / {n}")
            steps.append(f"  Variance = {sum(squared_diffs):.6f} / {n}")
            steps.append(f"  Variance = {variance:.6f}")
            steps.append("")
            
            steps.append("Step 6: Calculate Standard Deviation")
            steps.append(f"  Standard Deviation = √Variance")
            steps.append(f"  Standard Deviation = √{variance:.6f}")
            steps.append(f"  Standard Deviation = {std_dev:.6f}")
            steps.append("")
        
        # Quartiles
        if n >= 4:
            steps.append("Step 7: Calculate Quartiles")
            steps.append(f"  Q1 (First Quartile): {q1:.6f}")
            steps.append(f"  Q2 (Second Quartile / Median): {q2:.6f}")
            steps.append(f"  Q3 (Third Quartile): {q3:.6f}")
            steps.append(f"  IQR (Interquartile Range) = Q3 - Q1 = {q3 - q1:.6f}")
        
        return steps
    
    def _prepare_chart_data(self, numbers, mean, median, mode):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        # Frequency distribution
        counter = Counter(numbers)
        unique_values = sorted(counter.keys())
        frequencies = [counter[val] for val in unique_values]
        
        chart_data['frequency_chart'] = {
            'type': 'bar',
            'data': {
                'labels': [str(v) for v in unique_values],
                'datasets': [{
                    'label': 'Frequency',
                    'data': frequencies,
                    'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                    'borderColor': '#3b82f6',
                    'borderWidth': 2
                }]
            }
        }
        
        # Statistics comparison
        stats_values = []
        stats_labels = []
        
        if mean is not None:
            stats_values.append(mean)
            stats_labels.append('Mean')
        if median is not None:
            stats_values.append(median)
            stats_labels.append('Median')
        if mode:
            stats_values.append(mode[0])
            stats_labels.append('Mode')
        
        if stats_values:
            chart_data['statistics_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': stats_labels,
                    'datasets': [{
                        'label': 'Value',
                        'data': stats_values,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(139, 92, 246, 0.6)'
                        ][:len(stats_values)],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#8b5cf6'
                        ][:len(stats_values)],
                        'borderWidth': 2
                    }]
                }
            }
        
        # Box plot data (for quartiles)
        if len(numbers) >= 4:
            sorted_numbers = sorted(numbers)
            q1, q2, q3 = self._calculate_quartiles(numbers)
            min_val = min(numbers)
            max_val = max(numbers)
            
            chart_data['box_plot_data'] = {
                'min': min_val,
                'q1': q1,
                'median': q2,
                'q3': q3,
                'max': max_val
            }
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get numbers from input
            numbers_str = data.get('numbers', '')
            if not numbers_str:
                return JsonResponse({'success': False, 'error': 'Please provide at least one number.'}, status=400)
            
            numbers, error = self._parse_numbers(numbers_str)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate statistics
            mean = self._calculate_mean(numbers)
            median = self._calculate_median(numbers)
            mode = self._calculate_mode(numbers)
            range_val = self._calculate_range(numbers)
            
            # Additional statistics
            variance = None
            std_dev = None
            q1 = None
            q2 = None
            q3 = None
            iqr = None
            
            if len(numbers) >= 2:
                variance = self._calculate_variance(numbers, mean)
                std_dev = self._calculate_standard_deviation(variance)
            
            if len(numbers) >= 4:
                q1, q2, q3 = self._calculate_quartiles(numbers)
                iqr = self._calculate_iqr(q1, q3)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(
                numbers, mean, median, mode, range_val, 
                variance, std_dev, q1, q2, q3
            )
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(numbers, mean, median, mode)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Frequency distribution
            counter = Counter(numbers)
            frequency_distribution = {
                'values': sorted(counter.keys()),
                'frequencies': [counter[val] for val in sorted(counter.keys())],
                'max_frequency': max(counter.values()) if counter else 0
            }
            
            response = {
                'success': True,
                'numbers': numbers,
                'sorted_numbers': sorted(numbers),
                'count': len(numbers),
                'mean': mean,
                'median': median,
                'mode': mode,
                'range': range_val,
                'variance': variance,
                'standard_deviation': std_dev,
                'q1': q1,
                'q2': q2,
                'q3': q3,
                'iqr': iqr,
                'min': min(numbers),
                'max': max(numbers),
                'sum': sum(numbers),
                'frequency_distribution': frequency_distribution,
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
