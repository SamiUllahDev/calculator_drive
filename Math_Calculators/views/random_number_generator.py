from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
import random
import statistics


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RandomNumberGenerator(View):
    """
    Enhanced Professional Random Number Generator
    Generates random numbers with various options and statistics.
    """
    template_name = 'math_calculators/random_number_generator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Random Number Generator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _parse_exclude_list(self, exclude_str):
        """Parse excluded numbers from string"""
        if not exclude_str or exclude_str.strip() == '':
            return []
        
        exclude_list = []
        for item in exclude_str.split(','):
            item = item.strip()
            if item:
                try:
                    exclude_list.append(float(item))
                except ValueError:
                    continue
        return exclude_list
    
    def _generate_random_numbers(self, min_val, max_val, count, number_type, exclude_list=None):
        """Generate random numbers based on parameters"""
        if exclude_list is None:
            exclude_list = []
        
        if min_val >= max_val:
            return None, "Minimum value must be less than maximum value."
        
        if count <= 0:
            return None, "Count must be greater than zero."
        
        if count > 10000:
            return None, "Count cannot exceed 10,000."
        
        # Filter out excluded numbers from range
        if number_type == 'integer':
            available_numbers = [i for i in range(int(min_val), int(max_val) + 1) if i not in exclude_list]
            if len(available_numbers) < count:
                return None, f"Not enough available numbers. Only {len(available_numbers)} numbers available after exclusions."
            
            numbers = random.sample(available_numbers, min(count, len(available_numbers)))
        else:  # decimal
            numbers = []
            attempts = 0
            max_attempts = count * 100
            
            while len(numbers) < count and attempts < max_attempts:
                if number_type == 'decimal':
                    num = random.uniform(min_val, max_val)
                else:
                    num = random.uniform(min_val, max_val)
                
                # Round to 4 decimal places for decimal type
                if number_type == 'decimal':
                    num = round(num, 4)
                
                if num not in exclude_list:
                    numbers.append(num)
                attempts += 1
            
            if len(numbers) < count:
                return None, f"Could not generate {count} numbers. Try reducing exclusions or increasing range."
        
        return numbers, None
    
    def _calculate_statistics(self, numbers):
        """Calculate statistics for generated numbers"""
        if not numbers:
            return {}
        
        stats = {
            'count': len(numbers),
            'min': min(numbers),
            'max': max(numbers),
            'sum': sum(numbers),
            'mean': statistics.mean(numbers),
            'median': statistics.median(numbers),
        }
        
        if len(numbers) > 1:
            try:
                stats['stdev'] = statistics.stdev(numbers)
                stats['variance'] = statistics.variance(numbers)
            except:
                stats['stdev'] = 0
                stats['variance'] = 0
        else:
            stats['stdev'] = 0
            stats['variance'] = 0
        
        # Mode (most frequent)
        try:
            stats['mode'] = statistics.mode(numbers)
        except:
            stats['mode'] = None
        
        return stats
    
    def _prepare_chart_data(self, numbers, min_val, max_val):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if not numbers:
                return chart_data
            
            # Histogram data
            num_bins = min(20, len(numbers))
            if num_bins < 2:
                num_bins = 2
            
            bin_width = (max_val - min_val) / num_bins
            bins = [min_val + i * bin_width for i in range(num_bins + 1)]
            
            histogram = [0] * num_bins
            for num in numbers:
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
            
            # Distribution scatter plot
            chart_data['distribution_chart'] = {
                'type': 'scatter',
                'data': {
                    'datasets': [{
                        'label': 'Random Numbers',
                        'data': [{'x': i, 'y': num} for i, num in enumerate(numbers)],
                        'backgroundColor': 'rgba(16, 185, 129, 0.6)',
                        'borderColor': '#10b981',
                        'pointRadius': 3
                    }]
                }
            }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def _prepare_step_by_step(self, min_val, max_val, count, number_type, exclude_list, numbers, stats):
        """Prepare step-by-step explanation"""
        steps = []
        
        steps.append("Step 1: Parameters")
        steps.append(f"  Minimum value: {min_val}")
        steps.append(f"  Maximum value: {max_val}")
        steps.append(f"  Range: {max_val - min_val}")
        steps.append(f"  Count: {count}")
        steps.append(f"  Number type: {number_type}")
        if exclude_list:
            steps.append(f"  Excluded numbers: {', '.join(map(str, exclude_list))}")
        steps.append("")
        
        steps.append("Step 2: Generation Method")
        if number_type == 'integer':
            steps.append(f"  Generating {count} random integers from {int(min_val)} to {int(max_val)}")
        else:
            steps.append(f"  Generating {count} random decimal numbers from {min_val} to {max_val}")
        if exclude_list:
            steps.append(f"  Excluding: {', '.join(map(str, exclude_list))}")
        steps.append("")
        
        steps.append("Step 3: Generated Numbers")
        if len(numbers) <= 20:
            steps.append(f"  Numbers: {', '.join(map(str, numbers))}")
        else:
            steps.append(f"  First 10: {', '.join(map(str, numbers[:10]))}")
            steps.append(f"  ... ({len(numbers) - 10} more numbers)")
            steps.append(f"  Last 10: {', '.join(map(str, numbers[-10:]))}")
        steps.append("")
        
        steps.append("Step 4: Statistics")
        steps.append(f"  Count: {stats['count']}")
        steps.append(f"  Minimum: {stats['min']:.6f}")
        steps.append(f"  Maximum: {stats['max']:.6f}")
        steps.append(f"  Sum: {stats['sum']:.6f}")
        steps.append(f"  Mean: {stats['mean']:.6f}")
        steps.append(f"  Median: {stats['median']:.6f}")
        if stats.get('stdev'):
            steps.append(f"  Standard Deviation: {stats['stdev']:.6f}")
            steps.append(f"  Variance: {stats['variance']:.6f}")
        if stats.get('mode') is not None:
            steps.append(f"  Mode: {stats['mode']:.6f}")
        
        return steps
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get parameters
            min_val, error1 = self._validate_number(data.get('min'), 'Minimum value')
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            max_val, error2 = self._validate_number(data.get('max'), 'Maximum value')
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            count, error3 = self._validate_number(data.get('count'), 'Count')
            if error3:
                return JsonResponse({'success': False, 'error': error3}, status=400)
            
            count = int(count)
            if count <= 0:
                return JsonResponse({'success': False, 'error': 'Count must be greater than zero.'}, status=400)
            
            number_type = data.get('number_type', 'integer')
            if number_type not in ['integer', 'decimal']:
                number_type = 'integer'
            
            exclude_str = data.get('exclude', '')
            exclude_list = self._parse_exclude_list(exclude_str)
            
            # Generate random numbers
            numbers, error = self._generate_random_numbers(min_val, max_val, count, number_type, exclude_list)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate statistics
            stats = self._calculate_statistics(numbers)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(numbers, min_val, max_val)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare step-by-step
            step_by_step = self._prepare_step_by_step(min_val, max_val, count, number_type, exclude_list, numbers, stats)
            
            response = {
                'success': True,
                'min': min_val,
                'max': max_val,
                'count': count,
                'number_type': number_type,
                'exclude_list': exclude_list,
                'numbers': numbers,
                'statistics': stats,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Random Number Generator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
