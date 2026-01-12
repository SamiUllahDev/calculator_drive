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
class AverageCalculator(View):
    """
    Professional Average Calculator with comprehensive average types
    Calculates various types of averages with charts and visualizations.
    Includes backend-controlled rendering for all data.
    """
    template_name = 'math_calculators/average_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Average Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_numbers(self, numbers):
        """Validate and clean number list"""
        if not numbers or not isinstance(numbers, list):
            return None, "Please provide a list of numbers."
        
        valid_numbers = []
        for num in numbers:
            try:
                n = float(num)
                if math.isnan(n) or math.isinf(n):
                    continue
                valid_numbers.append(n)
            except (ValueError, TypeError):
                continue
        
        if len(valid_numbers) < 1:
            return None, "Please provide at least one valid number."
        
        return valid_numbers, None
    
    def _calculate_mean(self, numbers):
        """Calculate arithmetic mean"""
        return sum(numbers) / len(numbers)
    
    def _calculate_median(self, numbers):
        """Calculate median"""
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        if n % 2 == 0:
            return (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
        return sorted_nums[n//2]
    
    def _calculate_mode(self, numbers):
        """Calculate mode(s)"""
        try:
            mode_result = statistics.mode(numbers)
            return [mode_result]
        except statistics.StatisticsError:
            # Multiple modes or no mode
            counter = Counter(numbers)
            max_count = max(counter.values())
            modes = [num for num, count in counter.items() if count == max_count]
            if len(modes) == len(set(numbers)):
                return None  # All numbers are unique, no mode
            return sorted(modes)
    
    def _calculate_geometric_mean(self, numbers):
        """Calculate geometric mean"""
        if any(n <= 0 for n in numbers):
            return None
        product = 1
        for n in numbers:
            product *= n
        return product ** (1.0 / len(numbers))
    
    def _calculate_harmonic_mean(self, numbers):
        """Calculate harmonic mean"""
        if any(n == 0 for n in numbers):
            return None
        reciprocal_sum = sum(1.0 / n for n in numbers)
        return len(numbers) / reciprocal_sum
    
    def _calculate_quadratic_mean(self, numbers):
        """Calculate quadratic mean (RMS)"""
        sum_squares = sum(n * n for n in numbers)
        return math.sqrt(sum_squares / len(numbers))
    
    def _calculate_trimmed_mean(self, numbers, trim_percent=10):
        """Calculate trimmed mean"""
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)
        trim_count = int(n * trim_percent / 100)
        if trim_count >= n // 2:
            trim_count = (n // 2) - 1
        if trim_count == 0:
            return self._calculate_mean(numbers)
        trimmed = sorted_nums[trim_count:n - trim_count]
        return sum(trimmed) / len(trimmed) if trimmed else self._calculate_mean(numbers)
    
    def prepare_chart_data(self, numbers, results):
        """Prepare comprehensive chart data for visualizations"""
        if not numbers or len(numbers) == 0:
            return {}
        
        sorted_nums = sorted(numbers)
        mean = results.get('mean', 0)
        median = results.get('median', 0)
        
        # Data Distribution Chart (Histogram)
        min_val = min(numbers)
        max_val = max(numbers)
        range_val = max_val - min_val
        bins = min(10, len(numbers))
        bin_width = range_val / bins if range_val > 0 else 1
        
        histogram_data = [0] * bins
        bin_labels = []
        for i in range(bins):
            bin_start = min_val + i * bin_width
            bin_end = min_val + (i + 1) * bin_width
            bin_labels.append(f"{bin_start:.1f}-{bin_end:.1f}")
            for num in numbers:
                if i == bins - 1:
                    if bin_start <= num <= bin_end:
                        histogram_data[i] += 1
                else:
                    if bin_start <= num < bin_end:
                        histogram_data[i] += 1
        
        distribution_chart = {
            'type': 'bar',
            'data': {
                'labels': bin_labels,
                'datasets': [{
                    'label': 'Frequency',
                    'data': histogram_data,
                    'backgroundColor': 'rgba(59, 130, 246, 0.6)',
                    'borderColor': '#3b82f6',
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Average Types Comparison Chart
        avg_types = []
        avg_values = []
        avg_colors = []
        
        if results.get('mean') is not None:
            avg_types.append('Mean')
            avg_values.append(round(results['mean'], 2))
            avg_colors.append('#3b82f6')
        
        if results.get('median') is not None:
            avg_types.append('Median')
            avg_values.append(round(results['median'], 2))
            avg_colors.append('#10b981')
        
        if results.get('mode') is not None and results['mode']:
            mode_val = results['mode'][0] if isinstance(results['mode'], list) else results['mode']
            avg_types.append('Mode')
            avg_values.append(round(mode_val, 2))
            avg_colors.append('#f59e0b')
        
        if results.get('geometric_mean') is not None:
            avg_types.append('Geometric')
            avg_values.append(round(results['geometric_mean'], 2))
            avg_colors.append('#8b5cf6')
        
        if results.get('harmonic_mean') is not None:
            avg_types.append('Harmonic')
            avg_values.append(round(results['harmonic_mean'], 2))
            avg_colors.append('#ec4899')
        
        if results.get('quadratic_mean') is not None:
            avg_types.append('Quadratic')
            avg_values.append(round(results['quadratic_mean'], 2))
            avg_colors.append('#06b6d4')
        
        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': avg_types,
                'datasets': [{
                    'label': 'Average Value',
                    'data': avg_values,
                    'backgroundColor': avg_colors,
                    'borderColor': avg_colors,
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }
        
        # Data Points Chart (Scatter/Line)
        data_points_chart = {
            'type': 'line',
            'data': {
                'labels': [f"#{i+1}" for i in range(len(sorted_nums))],
                'datasets': [
                    {
                        'label': 'Data Points',
                        'data': sorted_nums,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
                    },
                    {
                        'label': 'Mean',
                        'data': [mean] * len(sorted_nums),
                        'borderColor': '#10b981',
                        'borderWidth': 2,
                        'borderDash': [5, 5],
                        'pointRadius': 0
                    },
                    {
                        'label': 'Median',
                        'data': [median] * len(sorted_nums),
                        'borderColor': '#f59e0b',
                        'borderWidth': 2,
                        'borderDash': [3, 3],
                        'pointRadius': 0
                    }
                ]
            }
        }
        
        # Statistics Gauge Chart
        mean_val = results.get('mean', 0)
        max_val = max(numbers) if numbers else 1
        min_val = min(numbers) if numbers else 0
        range_val = max_val - min_val if max_val != min_val else 1
        
        mean_percentage = ((mean_val - min_val) / range_val * 100) if range_val > 0 else 50
        
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Mean', 'Remaining'],
                'datasets': [{
                    'data': [round(mean_percentage, 2), round(100 - mean_percentage, 2)],
                    'backgroundColor': ['#3b82f6', '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(mean_val, 2),
                'label': 'Mean',
                'color': '#3b82f6'
            }
        }
        
        return {
            'distribution_chart': distribution_chart,
            'comparison_chart': comparison_chart,
            'data_points_chart': data_points_chart,
            'gauge_chart': gauge_chart
        }
    
    def prepare_display_data(self, numbers, results):
        """Prepare formatted display data for frontend"""
        def format_number(num, decimals=6):
            """Format number for display"""
            if num is None:
                return 'N/A'
            if not isinstance(num, (int, float)) or math.isnan(num) or math.isinf(num):
                return 'N/A'
            formatted = f"{num:.{decimals}f}".rstrip('0').rstrip('.')
            try:
                num_val = float(formatted)
                if abs(num_val) >= 1000:
                    return f"{num_val:,.{decimals}f}".rstrip('0').rstrip('.')
            except:
                pass
            return formatted
        
        display_data = {
            'numbers_count': len(numbers),
            'numbers_formatted': [format_number(n, 2) for n in numbers],
            'detailed_results': [],
            'statistics': {
                'min': format_number(min(numbers), 2) if numbers else 'N/A',
                'max': format_number(max(numbers), 2) if numbers else 'N/A',
                'range': format_number(max(numbers) - min(numbers), 2) if numbers else 'N/A',
                'sum': format_number(sum(numbers), 2) if numbers else 'N/A'
            }
        }
        
        # Add all average types
        if results.get('mean') is not None:
            display_data['detailed_results'].append({
                'label': 'Arithmetic Mean',
                'value': format_number(results['mean'], 6),
                'formula': f"Sum / Count = {sum(numbers)} / {len(numbers)}",
                'is_primary': True
            })
        
        if results.get('median') is not None:
            display_data['detailed_results'].append({
                'label': 'Median',
                'value': format_number(results['median'], 6),
                'formula': 'Middle value when sorted',
                'is_primary': False
            })
        
        if results.get('mode') is not None and results['mode']:
            mode_val = results['mode']
            if isinstance(mode_val, list):
                mode_str = ', '.join([format_number(m, 2) for m in mode_val])
            else:
                mode_str = format_number(mode_val, 2)
            display_data['detailed_results'].append({
                'label': 'Mode',
                'value': mode_str,
                'formula': 'Most frequent value(s)',
                'is_primary': False
            })
        elif results.get('mode') is None:
            display_data['detailed_results'].append({
                'label': 'Mode',
                'value': 'N/A',
                'formula': 'No mode (all values unique)',
                'is_primary': False
            })
        
        if results.get('geometric_mean') is not None:
            display_data['detailed_results'].append({
                'label': 'Geometric Mean',
                'value': format_number(results['geometric_mean'], 6),
                'formula': 'ⁿ√(x₁ × x₂ × ... × xₙ)',
                'is_primary': False
            })
        
        if results.get('harmonic_mean') is not None:
            display_data['detailed_results'].append({
                'label': 'Harmonic Mean',
                'value': format_number(results['harmonic_mean'], 6),
                'formula': 'n / (1/x₁ + 1/x₂ + ... + 1/xₙ)',
                'is_primary': False
            })
        
        if results.get('quadratic_mean') is not None:
            display_data['detailed_results'].append({
                'label': 'Quadratic Mean (RMS)',
                'value': format_number(results['quadratic_mean'], 6),
                'formula': '√((x₁² + x₂² + ... + xₙ²) / n)',
                'is_primary': False
            })
        
        if results.get('trimmed_mean') is not None:
            display_data['detailed_results'].append({
                'label': 'Trimmed Mean (10%)',
                'value': format_number(results['trimmed_mean'], 6),
                'formula': 'Mean after removing 10% from each end',
                'is_primary': False
            })
        
        return display_data
    
    def prepare_step_by_step(self, numbers, results):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given numbers: {', '.join([str(n) for n in numbers])}")
        steps.append(f"Count of numbers: {len(numbers)}")
        
        if results.get('mean') is not None:
            steps.append(f"Arithmetic Mean:")
            steps.append(f"  Sum = {sum(numbers)}")
            steps.append(f"  Mean = Sum / Count = {sum(numbers)} / {len(numbers)} = {results['mean']:.6f}")
        
        if results.get('median') is not None:
            sorted_nums = sorted(numbers)
            steps.append(f"Median:")
            steps.append(f"  Sorted numbers: {', '.join([str(n) for n in sorted_nums])}")
            n = len(sorted_nums)
            if n % 2 == 0:
                steps.append(f"  Median = ({sorted_nums[n//2 - 1]} + {sorted_nums[n//2]}) / 2 = {results['median']:.6f}")
            else:
                steps.append(f"  Median = {sorted_nums[n//2]} = {results['median']:.6f}")
        
        if results.get('mode') is not None and results['mode']:
            mode_val = results['mode']
            if isinstance(mode_val, list):
                steps.append(f"Mode: {', '.join([str(m) for m in mode_val])} (appears most frequently)")
            else:
                steps.append(f"Mode: {mode_val} (appears most frequently)")
        
        if results.get('geometric_mean') is not None:
            product = 1
            for n in numbers:
                product *= n
            steps.append(f"Geometric Mean:")
            steps.append(f"  Product = {product}")
            steps.append(f"  Geometric Mean = {product}^(1/{len(numbers)}) = {results['geometric_mean']:.6f}")
        
        if results.get('harmonic_mean') is not None:
            reciprocal_sum = sum(1.0 / n for n in numbers)
            steps.append(f"Harmonic Mean:")
            steps.append(f"  Sum of reciprocals = {reciprocal_sum:.6f}")
            steps.append(f"  Harmonic Mean = {len(numbers)} / {reciprocal_sum:.6f} = {results['harmonic_mean']:.6f}")
        
        return steps
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get numbers from input
            numbers_input = data.get('numbers', [])
            if isinstance(numbers_input, str):
                # Try to parse comma-separated string
                try:
                    numbers_input = [float(x.strip()) for x in numbers_input.split(',')]
                except:
                    numbers_input = []
            
            # Validate numbers
            numbers, error = self._validate_numbers(numbers_input)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate all average types
            results = {}
            
            # Arithmetic Mean
            results['mean'] = self._calculate_mean(numbers)
            
            # Median
            results['median'] = self._calculate_median(numbers)
            
            # Mode
            results['mode'] = self._calculate_mode(numbers)
            
            # Geometric Mean
            results['geometric_mean'] = self._calculate_geometric_mean(numbers)
            
            # Harmonic Mean
            results['harmonic_mean'] = self._calculate_harmonic_mean(numbers)
            
            # Quadratic Mean
            results['quadratic_mean'] = self._calculate_quadratic_mean(numbers)
            
            # Trimmed Mean
            results['trimmed_mean'] = self._calculate_trimmed_mean(numbers, 10)
            
            # Prepare chart data
            try:
                chart_data = self.prepare_chart_data(numbers, results)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare display data
            display_data = self.prepare_display_data(numbers, results)
            
            # Prepare step-by-step
            step_by_step = self.prepare_step_by_step(numbers, results)
            
            # Prepare response
            response = {
                'success': True,
                'numbers': numbers,
                'results': results,
                'chart_data': chart_data,
                'display_data': display_data,
                'step_by_step': step_by_step,
                'step_by_step_html': [{'step_number': idx + 1, 'content': step} for idx, step in enumerate(step_by_step)]
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Average calculator error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
