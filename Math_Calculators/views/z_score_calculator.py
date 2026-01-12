from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math
from scipy import stats


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ZScoreCalculator(View):
    """
    Enhanced Professional Z-Score Calculator
    Calculates z-scores, raw scores, probabilities, and percentiles with step-by-step solutions.
    """
    template_name = 'math_calculators/z_score_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Z-Score Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name, allow_zero=False):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num == 0:
                return None, f'{name} cannot be zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_z_score(self, raw_score, mean, std_dev):
        """Calculate z-score from raw score, mean, and standard deviation"""
        if std_dev == 0:
            return None, "Standard deviation cannot be zero."
        z_score = (raw_score - mean) / std_dev
        return z_score, None
    
    def _calculate_raw_score(self, z_score, mean, std_dev):
        """Calculate raw score from z-score, mean, and standard deviation"""
        if std_dev == 0:
            return None, "Standard deviation cannot be zero."
        raw_score = mean + (z_score * std_dev)
        return raw_score, None
    
    def _calculate_probability(self, z_score, tail_type='two'):
        """Calculate probability from z-score"""
        # Calculate cumulative probability
        if tail_type == 'left':
            # P(Z <= z)
            probability = stats.norm.cdf(z_score)
        elif tail_type == 'right':
            # P(Z >= z)
            probability = 1 - stats.norm.cdf(z_score)
        else:  # two-tailed
            # P(|Z| >= |z|)
            probability = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        percentile = stats.norm.cdf(z_score) * 100
        
        return {
            'probability': probability,
            'percentile': percentile,
            'tail_type': tail_type
        }
    
    def _prepare_step_by_step(self, mode, result, inputs):
        """Prepare step-by-step solution"""
        steps = []
        
        mode_names = {
            'z_score': 'Calculate Z-Score',
            'raw_score': 'Calculate Raw Score',
            'probability': 'Calculate Probability'
        }
        
        steps.append(f"Given: {mode_names.get(mode, mode)}")
        steps.append("")
        
        if mode == 'z_score':
            raw_score, mean, std_dev = inputs['raw_score'], inputs['mean'], inputs['std_dev']
            steps.append(f"  Raw Score (X) = {raw_score}")
            steps.append(f"  Mean (μ) = {mean}")
            steps.append(f"  Standard Deviation (σ) = {std_dev}")
            steps.append("")
            steps.append("Step 1: Apply z-score formula")
            steps.append("  z = (X - μ) / σ")
            steps.append(f"  z = ({raw_score} - {mean}) / {std_dev}")
            steps.append(f"  z = {raw_score - mean} / {std_dev}")
            steps.append(f"  z = {result['z_score']:.6f}")
            steps.append("")
            steps.append("Step 2: Interpretation")
            if abs(result['z_score']) < 1:
                steps.append(f"  z = {result['z_score']:.6f} is within 1 standard deviation of the mean.")
            elif abs(result['z_score']) < 2:
                steps.append(f"  z = {result['z_score']:.6f} is within 2 standard deviations of the mean.")
            elif abs(result['z_score']) < 3:
                steps.append(f"  z = {result['z_score']:.6f} is within 3 standard deviations of the mean.")
            else:
                steps.append(f"  z = {result['z_score']:.6f} is more than 3 standard deviations from the mean (outlier).")
        
        elif mode == 'raw_score':
            z_score, mean, std_dev = inputs['z_score'], inputs['mean'], inputs['std_dev']
            steps.append(f"  Z-Score (z) = {z_score}")
            steps.append(f"  Mean (μ) = {mean}")
            steps.append(f"  Standard Deviation (σ) = {std_dev}")
            steps.append("")
            steps.append("Step 1: Apply raw score formula")
            steps.append("  X = μ + (z × σ)")
            steps.append(f"  X = {mean} + ({z_score} × {std_dev})")
            steps.append(f"  X = {mean} + {z_score * std_dev}")
            steps.append(f"  X = {result['raw_score']:.6f}")
        
        elif mode == 'probability':
            z_score = inputs['z_score']
            tail_type = inputs.get('tail_type', 'two')
            steps.append(f"  Z-Score (z) = {z_score}")
            steps.append(f"  Tail Type = {tail_type}")
            steps.append("")
            steps.append("Step 1: Calculate cumulative probability")
            steps.append(f"  Using standard normal distribution (mean = 0, std dev = 1)")
            if tail_type == 'left':
                steps.append(f"  P(Z ≤ {z_score}) = {result['probability']:.6f}")
                steps.append(f"  This means {result['probability']*100:.2f}% of values are below this z-score.")
            elif tail_type == 'right':
                steps.append(f"  P(Z ≥ {z_score}) = {result['probability']:.6f}")
                steps.append(f"  This means {result['probability']*100:.2f}% of values are above this z-score.")
            else:  # two-tailed
                steps.append(f"  P(|Z| ≥ |{z_score}|) = {result['probability']:.6f}")
                steps.append(f"  This means {result['probability']*100:.2f}% of values are more extreme than ±{abs(z_score):.6f}.")
            steps.append("")
            steps.append("Step 2: Percentile")
            steps.append(f"  Percentile = {result['percentile']:.2f}%")
            steps.append(f"  This means {result['percentile']:.2f}% of values are below this z-score.")
        
        return steps
    
    def _prepare_chart_data(self, z_score, tail_type='two'):
        """Prepare chart data for normal distribution visualization"""
        chart_data = {}
        
        try:
            # Generate points for normal distribution curve
            x_min = -4
            x_max = 4
            x_points = [x_min + i * 0.1 for i in range(int((x_max - x_min) / 0.1) + 1)]
            y_points = [stats.norm.pdf(x) for x in x_points]
            
            # Calculate probability area
            if tail_type == 'left':
                # Shade area to the left of z_score
                x_shade = [x for x in x_points if x <= z_score]
                y_shade = [stats.norm.pdf(x) for x in x_shade]
            elif tail_type == 'right':
                # Shade area to the right of z_score
                x_shade = [x for x in x_points if x >= z_score]
                y_shade = [stats.norm.pdf(x) for x in x_shade]
            else:  # two-tailed
                # Shade areas beyond ±|z_score|
                x_shade_left = [x for x in x_points if x <= -abs(z_score)]
                x_shade_right = [x for x in x_points if x >= abs(z_score)]
                x_shade = x_shade_left + x_shade_right
                y_shade = [stats.norm.pdf(x) for x in x_shade]
            
            chart_data['distribution_chart'] = {
                'type': 'line',
                'data': {
                    'labels': [f'{x:.1f}' for x in x_points],
                    'datasets': [
                        {
                            'label': 'Normal Distribution',
                            'data': y_points,
                            'borderColor': 'rgba(59, 130, 246, 1)',
                            'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                            'borderWidth': 2,
                            'fill': False
                        },
                        {
                            'label': 'Probability Area',
                            'data': [stats.norm.pdf(x) if x in x_shade else None for x in x_points],
                            'borderColor': 'rgba(239, 68, 68, 1)',
                            'backgroundColor': 'rgba(239, 68, 68, 0.3)',
                            'borderWidth': 2,
                            'fill': True
                        }
                    ]
                },
                'options': {
                    'scales': {
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Z-Score'
                            }
                        },
                        'y': {
                            'title': {
                                'display': True,
                                'text': 'Probability Density'
                            }
                        }
                    },
                    'plugins': {
                        'legend': {
                            'display': True
                        },
                        'annotation': {
                            'annotations': [
                                {
                                    'type': 'line',
                                    'xMin': z_score,
                                    'xMax': z_score,
                                    'borderColor': 'rgba(16, 185, 129, 1)',
                                    'borderWidth': 2,
                                    'label': {
                                        'display': True,
                                        'content': f'z = {z_score:.2f}'
                                    }
                                }
                            ]
                        }
                    }
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
            
            mode = data.get('mode', 'z_score')
            result = {}
            error = None
            inputs = {}
            
            if mode == 'z_score':
                raw_score, err1 = self._validate_number(data.get('raw_score'), 'Raw Score')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                mean, err2 = self._validate_number(data.get('mean'), 'Mean')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                std_dev, err3 = self._validate_number(data.get('std_dev'), 'Standard Deviation', allow_zero=False)
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                
                inputs = {'raw_score': raw_score, 'mean': mean, 'std_dev': std_dev}
                z_score, error = self._calculate_z_score(raw_score, mean, std_dev)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                # Also calculate probability
                prob_data = self._calculate_probability(z_score, 'two')
                
                result = {
                    'z_score': z_score,
                    'raw_score': raw_score,
                    'mean': mean,
                    'std_dev': std_dev,
                    **prob_data
                }
            
            elif mode == 'raw_score':
                z_score, err1 = self._validate_number(data.get('z_score'), 'Z-Score')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                mean, err2 = self._validate_number(data.get('mean'), 'Mean')
                if err2:
                    return JsonResponse({'success': False, 'error': err2}, status=400)
                std_dev, err3 = self._validate_number(data.get('std_dev'), 'Standard Deviation', allow_zero=False)
                if err3:
                    return JsonResponse({'success': False, 'error': err3}, status=400)
                
                inputs = {'z_score': z_score, 'mean': mean, 'std_dev': std_dev}
                raw_score, error = self._calculate_raw_score(z_score, mean, std_dev)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                # Also calculate probability
                prob_data = self._calculate_probability(z_score, 'two')
                
                result = {
                    'raw_score': raw_score,
                    'z_score': z_score,
                    'mean': mean,
                    'std_dev': std_dev,
                    **prob_data
                }
            
            elif mode == 'probability':
                z_score, err1 = self._validate_number(data.get('z_score'), 'Z-Score')
                if err1:
                    return JsonResponse({'success': False, 'error': err1}, status=400)
                tail_type = data.get('tail_type', 'two')
                
                inputs = {'z_score': z_score, 'tail_type': tail_type}
                prob_data = self._calculate_probability(z_score, tail_type)
                
                result = {
                    'z_score': z_score,
                    **prob_data
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation mode.'}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(mode, result, inputs)
            
            # Prepare chart data
            chart_data = {}
            try:
                tail_type = result.get('tail_type', 'two')
                chart_data = self._prepare_chart_data(result['z_score'], tail_type)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                'mode': mode,
                **result,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Z-Score Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
