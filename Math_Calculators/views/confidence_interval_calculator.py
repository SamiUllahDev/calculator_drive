from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
try:
    from scipy import stats
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    # Fallback: Use approximations for critical values
    import statistics


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ConfidenceIntervalCalculator(View):
    """
    Professional Confidence Interval Calculator
    Calculates confidence intervals for means and proportions.
    Supports both z-interval and t-interval.
    """
    template_name = 'math_calculators/confidence_interval_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Confidence Interval Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name, min_val=None, max_val=None, allow_zero=False):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num == 0:
                return None, f'{name} cannot be zero.'
            if min_val is not None and num < min_val:
                return None, f'{name} must be at least {min_val}.'
            if max_val is not None and num > max_val:
                return None, f'{name} must be at most {max_val}.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _validate_confidence_level(self, value):
        """Validate confidence level"""
        num, error = self._validate_number(value, 'Confidence level', min_val=0.01, max_val=0.99)
        if error:
            return None, error
        # Convert percentage to decimal if needed
        if num > 1:
            num = num / 100
        if num < 0.01 or num > 0.99:
            return None, 'Confidence level must be between 1% and 99%.'
        return num, None
    
    def _calculate_z_critical(self, confidence_level):
        """Calculate z-critical value for given confidence level"""
        alpha = 1 - confidence_level
        if SCIPY_AVAILABLE:
            z_critical = stats.norm.ppf(1 - alpha / 2)
        else:
            # Approximation using inverse normal CDF
            # Common z-values: 90% = 1.645, 95% = 1.96, 99% = 2.576
            if abs(confidence_level - 0.90) < 0.01:
                z_critical = 1.645
            elif abs(confidence_level - 0.95) < 0.01:
                z_critical = 1.96
            elif abs(confidence_level - 0.99) < 0.01:
                z_critical = 2.576
            else:
                # Approximation formula for other confidence levels
                z_critical = 2.0 * math.sqrt(-math.log(alpha / 2))
        return z_critical
    
    def _calculate_t_critical(self, confidence_level, degrees_of_freedom):
        """Calculate t-critical value for given confidence level and degrees of freedom"""
        alpha = 1 - confidence_level
        if SCIPY_AVAILABLE:
            t_critical = stats.t.ppf(1 - alpha / 2, degrees_of_freedom)
        else:
            # For large df (>= 30), t approaches z
            if degrees_of_freedom >= 30:
                t_critical = self._calculate_z_critical(confidence_level)
            else:
                # Better approximation for t-distribution
                z_val = self._calculate_z_critical(confidence_level)
                # Wilson-Hilferty transformation approximation
                a = 1.0 / degrees_of_freedom
                correction = 1 + (z_val ** 2) * a / 4
                t_critical = z_val * math.sqrt(correction)
                # Additional correction for very small df
                if degrees_of_freedom < 10:
                    t_critical *= (1 + 0.1 / degrees_of_freedom)
        return t_critical
    
    def _calculate_mean_confidence_interval(self, sample_mean, sample_size, std_dev, confidence_level, use_population_std=False):
        """Calculate confidence interval for population mean"""
        if use_population_std:
            # Z-interval (population standard deviation known)
            z_critical = self._calculate_z_critical(confidence_level)
            margin_of_error = z_critical * (std_dev / math.sqrt(sample_size))
            lower_bound = sample_mean - margin_of_error
            upper_bound = sample_mean + margin_of_error
            method = 'z-interval'
            critical_value = z_critical
        else:
            # T-interval (sample standard deviation)
            degrees_of_freedom = sample_size - 1
            t_critical = self._calculate_t_critical(confidence_level, degrees_of_freedom)
            standard_error = std_dev / math.sqrt(sample_size)
            margin_of_error = t_critical * standard_error
            lower_bound = sample_mean - margin_of_error
            upper_bound = sample_mean + margin_of_error
            method = 't-interval'
            critical_value = t_critical
        
        return {
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'margin_of_error': margin_of_error,
            'sample_mean': sample_mean,
            'method': method,
            'critical_value': critical_value,
            'confidence_level': confidence_level
        }
    
    def _calculate_proportion_confidence_interval(self, sample_proportion, sample_size, confidence_level):
        """Calculate confidence interval for population proportion"""
        # Validate proportion
        if sample_proportion < 0 or sample_proportion > 1:
            return None, 'Sample proportion must be between 0 and 1.'
        
        z_critical = self._calculate_z_critical(confidence_level)
        
        # Standard error for proportion
        standard_error = math.sqrt((sample_proportion * (1 - sample_proportion)) / sample_size)
        
        margin_of_error = z_critical * standard_error
        lower_bound = max(0, sample_proportion - margin_of_error)
        upper_bound = min(1, sample_proportion + margin_of_error)
        
        return {
            'lower_bound': lower_bound,
            'upper_bound': upper_bound,
            'margin_of_error': margin_of_error,
            'sample_proportion': sample_proportion,
            'method': 'z-interval (proportion)',
            'critical_value': z_critical,
            'confidence_level': confidence_level
        }, None
    
    def prepare_chart_data(self, result_data, calc_type):
        """Prepare chart data for confidence interval visualization"""
        if not result_data:
            return {}
        
        if calc_type == 'mean':
            sample_mean = result_data.get('sample_mean', 0)
            lower_bound = result_data.get('lower_bound', 0)
            upper_bound = result_data.get('upper_bound', 0)
            margin_of_error = result_data.get('margin_of_error', 0)
            
            # Confidence interval visualization
            ci_chart = {
                'type': 'bar',
                'data': {
                    'labels': ['Lower Bound', 'Sample Mean', 'Upper Bound'],
                    'datasets': [{
                        'label': 'Values',
                        'data': [lower_bound, sample_mean, upper_bound],
                        'backgroundColor': [
                            'rgba(239, 68, 68, 0.6)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.6)'
                        ],
                        'borderColor': [
                            '#ef4444',
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            # Margin of error visualization
            margin_chart = {
                'type': 'doughnut',
                'data': {
                    'labels': ['Margin of Error', 'Confidence Range'],
                    'datasets': [{
                        'data': [
                            abs(margin_of_error),
                            abs(upper_bound - lower_bound) - abs(margin_of_error)
                        ],
                        'backgroundColor': ['rgba(245, 158, 11, 0.6)', 'rgba(229, 231, 235, 0.6)'],
                        'borderColor': ['#f59e0b', '#e5e7eb'],
                        'borderWidth': 2
                    }]
                }
            }
            
            return {
                'ci_chart': ci_chart,
                'margin_chart': margin_chart
            }
        
        elif calc_type == 'proportion':
            sample_proportion = result_data.get('sample_proportion', 0)
            lower_bound = result_data.get('lower_bound', 0)
            upper_bound = result_data.get('upper_bound', 0)
            margin_of_error = result_data.get('margin_of_error', 0)
            
            # Proportion confidence interval chart
            proportion_chart = {
                'type': 'bar',
                'data': {
                    'labels': ['Lower Bound', 'Sample Proportion', 'Upper Bound'],
                    'datasets': [{
                        'label': 'Proportion',
                        'data': [lower_bound, sample_proportion, upper_bound],
                        'backgroundColor': [
                            'rgba(239, 68, 68, 0.6)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(16, 185, 129, 0.6)'
                        ],
                        'borderColor': [
                            '#ef4444',
                            '#8b5cf6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            return {
                'proportion_chart': proportion_chart
            }
        
        return {}
    
    def prepare_display_data(self, result_data, calc_type):
        """Prepare formatted display data for frontend"""
        display_data = {
            'calc_type': calc_type,
            'result_data': result_data,
            'formatted_results': []
        }
        
        if calc_type == 'mean':
            display_data['formatted_results'] = [
                {
                    'label': 'Sample Mean',
                    'value': f"{result_data.get('sample_mean', 0):.6f}",
                    'is_primary': False
                },
                {
                    'label': 'Lower Bound',
                    'value': f"{result_data.get('lower_bound', 0):.6f}",
                    'is_primary': True
                },
                {
                    'label': 'Upper Bound',
                    'value': f"{result_data.get('upper_bound', 0):.6f}",
                    'is_primary': True
                },
                {
                    'label': 'Margin of Error',
                    'value': f"±{result_data.get('margin_of_error', 0):.6f}",
                    'is_primary': True
                },
                {
                    'label': 'Method',
                    'value': result_data.get('method', 'N/A'),
                    'is_primary': False
                },
                {
                    'label': 'Critical Value',
                    'value': f"{result_data.get('critical_value', 0):.4f}",
                    'is_primary': False
                }
            ]
        elif calc_type == 'proportion':
            display_data['formatted_results'] = [
                {
                    'label': 'Sample Proportion',
                    'value': f"{result_data.get('sample_proportion', 0):.6f} ({result_data.get('sample_proportion', 0)*100:.2f}%)",
                    'is_primary': False
                },
                {
                    'label': 'Lower Bound',
                    'value': f"{result_data.get('lower_bound', 0):.6f} ({result_data.get('lower_bound', 0)*100:.2f}%)",
                    'is_primary': True
                },
                {
                    'label': 'Upper Bound',
                    'value': f"{result_data.get('upper_bound', 0):.6f} ({result_data.get('upper_bound', 0)*100:.2f}%)",
                    'is_primary': True
                },
                {
                    'label': 'Margin of Error',
                    'value': f"±{result_data.get('margin_of_error', 0):.6f} (±{result_data.get('margin_of_error', 0)*100:.2f}%)",
                    'is_primary': True
                },
                {
                    'label': 'Method',
                    'value': result_data.get('method', 'N/A'),
                    'is_primary': False
                },
                {
                    'label': 'Critical Value (z)',
                    'value': f"{result_data.get('critical_value', 0):.4f}",
                    'is_primary': False
                }
            ]
        
        return display_data
    
    def prepare_step_by_step(self, result_data, calc_type, input_data):
        """Prepare step-by-step solution"""
        steps = []
        confidence_level = result_data.get('confidence_level', 0.95)
        confidence_percent = confidence_level * 100
        
        if calc_type == 'mean':
            sample_mean = result_data.get('sample_mean', 0)
            sample_size = input_data.get('sample_size', 0)
            std_dev = input_data.get('std_dev', 0)
            use_population_std = input_data.get('use_population_std', False)
            method = result_data.get('method', '')
            critical_value = result_data.get('critical_value', 0)
            margin_of_error = result_data.get('margin_of_error', 0)
            lower_bound = result_data.get('lower_bound', 0)
            upper_bound = result_data.get('upper_bound', 0)
            
            steps.append(f"Given:")
            steps.append(f"  Sample Mean (x̄) = {sample_mean:.6f}")
            steps.append(f"  Sample Size (n) = {sample_size}")
            steps.append(f"  Standard Deviation (σ) = {std_dev:.6f}")
            steps.append(f"  Confidence Level = {confidence_percent:.1f}%")
            
            steps.append(f"Step 1: Determine the method")
            if use_population_std:
                steps.append(f"  Population standard deviation is known, so we use z-interval")
            else:
                steps.append(f"  Population standard deviation is unknown, so we use t-interval")
            
            steps.append(f"Step 2: Calculate the critical value")
            if use_population_std:
                steps.append(f"  For {confidence_percent:.1f}% confidence level, z-critical = {critical_value:.4f}")
            else:
                degrees_of_freedom = sample_size - 1
                steps.append(f"  Degrees of freedom (df) = n - 1 = {sample_size} - 1 = {degrees_of_freedom}")
                steps.append(f"  For {confidence_percent:.1f}% confidence level and df = {degrees_of_freedom}, t-critical = {critical_value:.4f}")
            
            steps.append(f"Step 3: Calculate the standard error")
            standard_error = std_dev / math.sqrt(sample_size)
            steps.append(f"  Standard Error (SE) = σ / √n = {std_dev:.6f} / √{sample_size} = {standard_error:.6f}")
            
            steps.append(f"Step 4: Calculate the margin of error")
            steps.append(f"  Margin of Error (ME) = {critical_value:.4f} × {standard_error:.6f} = {margin_of_error:.6f}")
            
            steps.append(f"Step 5: Calculate the confidence interval")
            steps.append(f"  Lower Bound = x̄ - ME = {sample_mean:.6f} - {margin_of_error:.6f} = {lower_bound:.6f}")
            steps.append(f"  Upper Bound = x̄ + ME = {sample_mean:.6f} + {margin_of_error:.6f} = {upper_bound:.6f}")
            
            steps.append(f"Step 6: Interpretation")
            steps.append(f"  We are {confidence_percent:.1f}% confident that the true population mean lies between {lower_bound:.6f} and {upper_bound:.6f}")
        
        elif calc_type == 'proportion':
            sample_proportion = result_data.get('sample_proportion', 0)
            sample_size = input_data.get('sample_size', 0)
            critical_value = result_data.get('critical_value', 0)
            margin_of_error = result_data.get('margin_of_error', 0)
            lower_bound = result_data.get('lower_bound', 0)
            upper_bound = result_data.get('upper_bound', 0)
            
            steps.append(f"Given:")
            steps.append(f"  Sample Proportion (p̂) = {sample_proportion:.6f} ({sample_proportion*100:.2f}%)")
            steps.append(f"  Sample Size (n) = {sample_size}")
            steps.append(f"  Confidence Level = {confidence_percent:.1f}%")
            
            steps.append(f"Step 1: Calculate the critical value")
            steps.append(f"  For {confidence_percent:.1f}% confidence level, z-critical = {critical_value:.4f}")
            
            steps.append(f"Step 2: Calculate the standard error")
            standard_error = math.sqrt((sample_proportion * (1 - sample_proportion)) / sample_size)
            steps.append(f"  Standard Error (SE) = √(p̂(1-p̂)/n) = √({sample_proportion:.6f} × {1-sample_proportion:.6f} / {sample_size}) = {standard_error:.6f}")
            
            steps.append(f"Step 3: Calculate the margin of error")
            steps.append(f"  Margin of Error (ME) = z × SE = {critical_value:.4f} × {standard_error:.6f} = {margin_of_error:.6f}")
            
            steps.append(f"Step 4: Calculate the confidence interval")
            steps.append(f"  Lower Bound = p̂ - ME = {sample_proportion:.6f} - {margin_of_error:.6f} = {lower_bound:.6f} ({lower_bound*100:.2f}%)")
            steps.append(f"  Upper Bound = p̂ + ME = {sample_proportion:.6f} + {margin_of_error:.6f} = {upper_bound:.6f} ({upper_bound*100:.2f}%)")
            
            steps.append(f"Step 5: Interpretation")
            steps.append(f"  We are {confidence_percent:.1f}% confident that the true population proportion lies between {lower_bound*100:.2f}% and {upper_bound*100:.2f}%")
        
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
            
            calc_type = data.get('calc_type', 'mean')  # 'mean' or 'proportion'
            
            if calc_type == 'mean':
                # Validate mean calculation inputs
                sample_mean, error = self._validate_number(data.get('sample_mean'), 'Sample mean')
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                sample_size, error = self._validate_number(data.get('sample_size'), 'Sample size', min_val=2, allow_zero=False)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                sample_size = int(sample_size)
                
                std_dev, error = self._validate_number(data.get('std_dev'), 'Standard deviation', min_val=0, allow_zero=False)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                confidence_level, error = self._validate_confidence_level(data.get('confidence_level', 95))
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                use_population_std = data.get('use_population_std', 'false').lower() == 'true'
                
                # Calculate confidence interval
                result_data = self._calculate_mean_confidence_interval(
                    sample_mean, sample_size, std_dev, confidence_level, use_population_std
                )
                
                input_data = {
                    'sample_mean': sample_mean,
                    'sample_size': sample_size,
                    'std_dev': std_dev,
                    'use_population_std': use_population_std
                }
            
            elif calc_type == 'proportion':
                # Validate proportion calculation inputs
                sample_proportion, error = self._validate_number(data.get('sample_proportion'), 'Sample proportion', min_val=0, max_val=1)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                sample_size, error = self._validate_number(data.get('sample_size'), 'Sample size', min_val=2, allow_zero=False)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                sample_size = int(sample_size)
                
                confidence_level, error = self._validate_confidence_level(data.get('confidence_level', 95))
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                # Calculate confidence interval
                result_data, error = self._calculate_proportion_confidence_interval(
                    sample_proportion, sample_size, confidence_level
                )
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                input_data = {
                    'sample_proportion': sample_proportion,
                    'sample_size': sample_size
                }
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self.prepare_chart_data(result_data, calc_type)
            except Exception as chart_error:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            # Prepare display data
            display_data = self.prepare_display_data(result_data, calc_type)
            
            # Prepare step-by-step solution
            step_by_step = self.prepare_step_by_step(result_data, calc_type, input_data)
            step_by_step_html = self.prepare_step_by_step_html(step_by_step)
            
            # Prepare response
            response = {
                'success': True,
                'calc_type': calc_type,
                'result_data': result_data,
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
            print(f"Confidence Interval Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred during calculation: {str(e)}'}, status=500)
