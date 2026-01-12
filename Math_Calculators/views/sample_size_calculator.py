from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from scipy import stats


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SampleSizeCalculator(View):
    """
    Enhanced Professional Sample Size Calculator
    Calculates required sample size for surveys and studies with various parameters.
    """
    template_name = 'math_calculators/sample_size_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Sample Size Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_positive_number(self, value, name, min_val=0, max_val=None):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num < min_val:
                return None, f'{name} must be at least {min_val}.'
            if max_val is not None and num > max_val:
                return None, f'{name} must be at most {max_val}.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _get_z_score(self, confidence_level):
        """Get z-score for given confidence level"""
        z_scores = {
            80: 1.282,
            85: 1.440,
            90: 1.645,
            95: 1.960,
            99: 2.576,
            99.5: 2.807,
            99.9: 3.291
        }
        return z_scores.get(confidence_level, stats.norm.ppf((1 + confidence_level / 100) / 2))
    
    def _calculate_sample_size(self, calc_type, confidence_level, margin_of_error, population_proportion=None, 
                               population_size=None, standard_deviation=None):
        """Calculate sample size based on type"""
        z_score = self._get_z_score(confidence_level)
        
        if calc_type == 'proportion':
            # Sample size for proportion
            if population_proportion is None:
                # Use conservative estimate (p = 0.5)
                p = 0.5
            else:
                p = population_proportion / 100 if population_proportion > 1 else population_proportion
            
            # Basic formula: n = (z^2 * p * (1-p)) / e^2
            n = (z_score ** 2 * p * (1 - p)) / ((margin_of_error / 100) ** 2)
            
            # Apply finite population correction if population size is provided
            if population_size is not None and population_size > 0:
                n_corrected = n / (1 + (n - 1) / population_size)
                return {
                    'sample_size': math.ceil(n_corrected),
                    'sample_size_uncorrected': math.ceil(n),
                    'calc_type': 'proportion',
                    'population_proportion': p,
                    'used_fpc': True
                }, None
            else:
                return {
                    'sample_size': math.ceil(n),
                    'sample_size_uncorrected': math.ceil(n),
                    'calc_type': 'proportion',
                    'population_proportion': p,
                    'used_fpc': False
                }, None
        
        elif calc_type == 'mean':
            # Sample size for mean
            if standard_deviation is None:
                return None, "Standard deviation is required for mean calculation."
            
            # Formula: n = (z^2 * σ^2) / e^2
            # Margin of error is in units, not percentage
            n = (z_score ** 2 * standard_deviation ** 2) / (margin_of_error ** 2)
            
            # Apply finite population correction if population size is provided
            if population_size is not None and population_size > 0:
                n_corrected = n / (1 + (n - 1) / population_size)
                return {
                    'sample_size': math.ceil(n_corrected),
                    'sample_size_uncorrected': math.ceil(n),
                    'calc_type': 'mean',
                    'standard_deviation': standard_deviation,
                    'used_fpc': True
                }, None
            else:
                return {
                    'sample_size': math.ceil(n),
                    'sample_size_uncorrected': math.ceil(n),
                    'calc_type': 'mean',
                    'standard_deviation': standard_deviation,
                    'used_fpc': False
                }, None
        
        else:
            return None, "Invalid calculation type."
    
    def _prepare_step_by_step(self, calc_type, confidence_level, margin_of_error, result):
        """Prepare step-by-step solution"""
        steps = []
        
        z_score = self._get_z_score(confidence_level)
        
        steps.append(f"Given:")
        steps.append(f"  Confidence Level: {confidence_level}%")
        steps.append(f"  Margin of Error: {margin_of_error}{'%' if calc_type == 'proportion' else ''}")
        if calc_type == 'proportion':
            steps.append(f"  Population Proportion: {result['population_proportion']*100:.2f}%")
        else:
            steps.append(f"  Standard Deviation: {result['standard_deviation']}")
        if result.get('used_fpc'):
            steps.append(f"  Population Size: Provided")
        steps.append("")
        
        steps.append("Step 1: Find z-score")
        steps.append(f"  For {confidence_level}% confidence level, z = {z_score:.4f}")
        steps.append("")
        
        if calc_type == 'proportion':
            steps.append("Step 2: Apply sample size formula for proportion")
            steps.append("  n = (z² × p × (1-p)) / e²")
            p = result['population_proportion']
            e = margin_of_error / 100
            steps.append(f"  n = ({z_score:.4f}² × {p:.4f} × {1-p:.4f}) / {e:.4f}²")
            steps.append(f"  n = ({z_score**2:.4f} × {p*(1-p):.4f}) / {e**2:.4f}")
            n_uncorrected = (z_score ** 2 * p * (1 - p)) / (e ** 2)
            steps.append(f"  n = {n_uncorrected:.2f}")
            steps.append(f"  n = {math.ceil(n_uncorrected)} (rounded up)")
        else:
            steps.append("Step 2: Apply sample size formula for mean")
            steps.append("  n = (z² × σ²) / e²")
            sigma = result['standard_deviation']
            e = margin_of_error
            steps.append(f"  n = ({z_score:.4f}² × {sigma:.4f}²) / {e:.4f}²")
            steps.append(f"  n = ({z_score**2:.4f} × {sigma**2:.4f}) / {e**2:.4f}")
            n_uncorrected = (z_score ** 2 * sigma ** 2) / (e ** 2)
            steps.append(f"  n = {n_uncorrected:.2f}")
            steps.append(f"  n = {math.ceil(n_uncorrected)} (rounded up)")
        
        if result.get('used_fpc'):
            steps.append("")
            steps.append("Step 3: Apply Finite Population Correction (FPC)")
            steps.append("  n_corrected = n / (1 + (n - 1) / N)")
            steps.append(f"  n_corrected = {result['sample_size_uncorrected']} / (1 + ({result['sample_size_uncorrected']} - 1) / N)")
            steps.append(f"  n_corrected = {result['sample_size']}")
        
        steps.append("")
        steps.append(f"Required Sample Size: {result['sample_size']}")
        
        return steps
    
    def _prepare_chart_data(self, confidence_level, margin_of_error, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Sample size vs confidence level
            confidence_levels = [80, 85, 90, 95, 99]
            sample_sizes = []
            for cl in confidence_levels:
                z = self._get_z_score(cl)
                if result['calc_type'] == 'proportion':
                    p = result['population_proportion']
                    e = margin_of_error / 100
                    n = (z ** 2 * p * (1 - p)) / (e ** 2)
                else:
                    sigma = result['standard_deviation']
                    e = margin_of_error
                    n = (z ** 2 * sigma ** 2) / (e ** 2)
                sample_sizes.append(math.ceil(n))
            
            chart_data['confidence_level_chart'] = {
                'type': 'line',
                'data': {
                    'labels': [f'{cl}%' for cl in confidence_levels],
                    'datasets': [{
                        'label': 'Sample Size',
                        'data': sample_sizes,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4,
                        'pointRadius': 5
                    }]
                }
            }
            
            # Sample size vs margin of error
            margins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            sample_sizes_margin = []
            z = self._get_z_score(confidence_level)
            for m in margins:
                if result['calc_type'] == 'proportion':
                    p = result['population_proportion']
                    e = m / 100
                    n = (z ** 2 * p * (1 - p)) / (e ** 2)
                else:
                    sigma = result['standard_deviation']
                    e = m
                    n = (z ** 2 * sigma ** 2) / (e ** 2)
                sample_sizes_margin.append(math.ceil(n))
            
            chart_data['margin_of_error_chart'] = {
                'type': 'line',
                'data': {
                    'labels': [f'{m}{"%" if result["calc_type"] == "proportion" else ""}' for m in margins],
                    'datasets': [{
                        'label': 'Sample Size',
                        'data': sample_sizes_margin,
                        'borderColor': '#10b981',
                        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4,
                        'pointRadius': 5
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
            
            calc_type = data.get('calc_type', 'proportion')
            confidence_level = float(data.get('confidence_level', 95))
            margin_of_error = float(data.get('margin_of_error', 5))
            
            # Validate confidence level
            if confidence_level not in [80, 85, 90, 95, 99, 99.5, 99.9]:
                return JsonResponse({'success': False, 'error': 'Invalid confidence level.'}, status=400)
            
            # Validate margin of error
            if calc_type == 'proportion':
                margin_of_error, error = self._validate_positive_number(margin_of_error, 'Margin of error', min_val=0.1, max_val=50)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
            else:
                margin_of_error, error = self._validate_positive_number(margin_of_error, 'Margin of error', min_val=0.0001)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
            
            population_proportion = None
            standard_deviation = None
            population_size = None
            
            if calc_type == 'proportion':
                prop_val = data.get('population_proportion', '')
                if prop_val and prop_val.strip():
                    population_proportion, error = self._validate_positive_number(prop_val, 'Population proportion', min_val=0, max_val=100)
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
            
            if calc_type == 'mean':
                std_val = data.get('standard_deviation', '')
                if std_val and std_val.strip():
                    standard_deviation, error = self._validate_positive_number(std_val, 'Standard deviation', min_val=0.0001)
                    if error:
                        return JsonResponse({'success': False, 'error': error}, status=400)
                else:
                    return JsonResponse({'success': False, 'error': 'Standard deviation is required for mean calculation.'}, status=400)
            
            pop_size_val = data.get('population_size', '')
            if pop_size_val and pop_size_val.strip():
                population_size, error = self._validate_positive_number(pop_size_val, 'Population size', min_val=1)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Calculate sample size
            result, error = self._calculate_sample_size(calc_type, confidence_level, margin_of_error,
                                                         population_proportion, population_size, standard_deviation)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(calc_type, confidence_level, margin_of_error, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(confidence_level, margin_of_error, result)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            z_score = self._get_z_score(confidence_level)
            
            response = {
                'success': True,
                'calc_type': calc_type,
                'confidence_level': confidence_level,
                'margin_of_error': margin_of_error,
                'z_score': z_score,
                **result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Sample Size Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
