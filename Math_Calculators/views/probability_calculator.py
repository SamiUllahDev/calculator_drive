from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ProbabilityCalculator(View):
    """
    Enhanced Professional Probability Calculator
    Calculates various probability types: basic, conditional, joint, union with step-by-step solutions.
    """
    template_name = 'math_calculators/probability_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Probability Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_probability(self, value, name):
        """Validate that a value is a valid probability (0 to 1)"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if num < 0 or num > 1:
                return None, f'{name} must be between 0 and 1 (inclusive).'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _validate_positive_number(self, value, name, allow_zero=False):
        """Validate that a value is a positive number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num <= 0:
                return None, f'{name} must be greater than zero.'
            if allow_zero and num < 0:
                return None, f'{name} must be greater than or equal to zero.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_basic_probability(self, favorable, total):
        """Calculate basic probability P(A) = favorable / total"""
        if total == 0:
            return None, "Total outcomes cannot be zero."
        probability = favorable / total
        return {
            'probability': probability,
            'favorable': favorable,
            'total': total,
            'unfavorable': total - favorable
        }, None
    
    def _calculate_conditional_probability(self, p_a_and_b, p_b):
        """Calculate conditional probability P(A|B) = P(A and B) / P(B)"""
        if p_b == 0:
            return None, "P(B) cannot be zero for conditional probability."
        probability = p_a_and_b / p_b
        return {
            'probability': probability,
            'p_a_and_b': p_a_and_b,
            'p_b': p_b
        }, None
    
    def _calculate_joint_probability(self, p_a, p_b, independent=True):
        """Calculate joint probability"""
        if independent:
            # P(A and B) = P(A) × P(B) for independent events
            probability = p_a * p_b
            return {
                'probability': probability,
                'p_a': p_a,
                'p_b': p_b,
                'independent': True
            }, None
        else:
            # For dependent events, need P(A|B) or P(B|A)
            return None, "For dependent events, please use conditional probability calculation."
    
    def _calculate_union_probability(self, p_a, p_b, p_a_and_b):
        """Calculate union probability P(A or B) = P(A) + P(B) - P(A and B)"""
        probability = p_a + p_b - p_a_and_b
        if probability < 0:
            return None, "Invalid probabilities: P(A) + P(B) - P(A and B) cannot be negative."
        if probability > 1:
            return None, "Invalid probabilities: Result cannot exceed 1."
        return {
            'probability': probability,
            'p_a': p_a,
            'p_b': p_b,
            'p_a_and_b': p_a_and_b
        }, None
    
    def _prepare_step_by_step(self, calc_type, result, **kwargs):
        """Prepare step-by-step solution"""
        steps = []
        
        if calc_type == 'basic':
            favorable = result['favorable']
            total = result['total']
            probability = result['probability']
            
            steps.append(f"Given:")
            steps.append(f"  Favorable outcomes: {favorable}")
            steps.append(f"  Total outcomes: {total}")
            steps.append("")
            steps.append("Step 1: Apply the probability formula")
            steps.append(f"  P(A) = Favorable outcomes / Total outcomes")
            steps.append(f"  P(A) = {favorable} / {total}")
            steps.append(f"  P(A) = {probability:.6f}")
            steps.append("")
            steps.append("Step 2: Convert to percentage")
            steps.append(f"  P(A) = {probability * 100:.2f}%")
            steps.append("")
            steps.append("Step 3: Interpretation")
            steps.append(f"  The probability of event A occurring is {probability:.6f} or {probability * 100:.2f}%")
            steps.append(f"  Unfavorable outcomes: {result['unfavorable']}")
        
        elif calc_type == 'conditional':
            p_a_and_b = result['p_a_and_b']
            p_b = result['p_b']
            probability = result['probability']
            
            steps.append(f"Given:")
            steps.append(f"  P(A and B) = {p_a_and_b:.6f}")
            steps.append(f"  P(B) = {p_b:.6f}")
            steps.append("")
            steps.append("Step 1: Apply the conditional probability formula")
            steps.append(f"  P(A|B) = P(A and B) / P(B)")
            steps.append(f"  P(A|B) = {p_a_and_b:.6f} / {p_b:.6f}")
            steps.append(f"  P(A|B) = {probability:.6f}")
            steps.append("")
            steps.append("Step 2: Convert to percentage")
            steps.append(f"  P(A|B) = {probability * 100:.2f}%")
            steps.append("")
            steps.append("Step 3: Interpretation")
            steps.append(f"  The probability of A given B is {probability:.6f} or {probability * 100:.2f}%")
        
        elif calc_type == 'joint':
            p_a = result['p_a']
            p_b = result['p_b']
            probability = result['probability']
            independent = result['independent']
            
            steps.append(f"Given:")
            steps.append(f"  P(A) = {p_a:.6f}")
            steps.append(f"  P(B) = {p_b:.6f}")
            steps.append(f"  Events are {'independent' if independent else 'dependent'}")
            steps.append("")
            steps.append("Step 1: Apply the joint probability formula")
            if independent:
                steps.append(f"  For independent events: P(A and B) = P(A) × P(B)")
                steps.append(f"  P(A and B) = {p_a:.6f} × {p_b:.6f}")
                steps.append(f"  P(A and B) = {probability:.6f}")
            else:
                steps.append(f"  For dependent events, use conditional probability")
            steps.append("")
            steps.append("Step 2: Convert to percentage")
            steps.append(f"  P(A and B) = {probability * 100:.2f}%")
            steps.append("")
            steps.append("Step 3: Interpretation")
            steps.append(f"  The probability of both A and B occurring is {probability:.6f} or {probability * 100:.2f}%")
        
        elif calc_type == 'union':
            p_a = result['p_a']
            p_b = result['p_b']
            p_a_and_b = result['p_a_and_b']
            probability = result['probability']
            
            steps.append(f"Given:")
            steps.append(f"  P(A) = {p_a:.6f}")
            steps.append(f"  P(B) = {p_b:.6f}")
            steps.append(f"  P(A and B) = {p_a_and_b:.6f}")
            steps.append("")
            steps.append("Step 1: Apply the union probability formula")
            steps.append(f"  P(A or B) = P(A) + P(B) - P(A and B)")
            steps.append(f"  P(A or B) = {p_a:.6f} + {p_b:.6f} - {p_a_and_b:.6f}")
            steps.append(f"  P(A or B) = {p_a + p_b:.6f} - {p_a_and_b:.6f}")
            steps.append(f"  P(A or B) = {probability:.6f}")
            steps.append("")
            steps.append("Step 2: Convert to percentage")
            steps.append(f"  P(A or B) = {probability * 100:.2f}%")
            steps.append("")
            steps.append("Step 3: Interpretation")
            steps.append(f"  The probability of A or B (or both) occurring is {probability:.6f} or {probability * 100:.2f}%")
        
        return steps
    
    def _prepare_chart_data(self, calc_type, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if calc_type == 'basic':
                # Pie chart showing favorable vs unfavorable
                favorable = result['favorable']
                total = result['total']
                unfavorable = result['unfavorable']
                
                chart_data['probability_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': ['Favorable', 'Unfavorable'],
                        'datasets': [{
                            'data': [favorable, unfavorable],
                            'backgroundColor': [
                                'rgba(59, 130, 246, 0.6)',
                                'rgba(229, 231, 235, 0.6)'
                            ],
                            'borderColor': [
                                '#3b82f6',
                                '#e5e7eb'
                            ],
                            'borderWidth': 2
                        }]
                    }
                }
            
            elif calc_type in ['conditional', 'joint', 'union']:
                # Bar chart comparing probabilities
                labels = []
                values = []
                
                if calc_type == 'conditional':
                    labels = ['P(A and B)', 'P(B)', 'P(A|B)'];
                    values = [result['p_a_and_b'], result['p_b'], result['probability']]
                elif calc_type == 'joint':
                    labels = ['P(A)', 'P(B)', 'P(A and B)'];
                    values = [result['p_a'], result['p_b'], result['probability']]
                elif calc_type == 'union':
                    labels = ['P(A)', 'P(B)', 'P(A and B)', 'P(A or B)'];
                    values = [result['p_a'], result['p_b'], result['p_a_and_b'], result['probability']]
                
                chart_data['probability_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': labels,
                        'datasets': [{
                            'label': 'Probability',
                            'data': values,
                            'backgroundColor': [
                                'rgba(59, 130, 246, 0.6)',
                                'rgba(16, 185, 129, 0.6)',
                                'rgba(139, 92, 246, 0.6)',
                                'rgba(245, 158, 11, 0.6)'
                            ][:len(values)],
                            'borderColor': [
                                '#3b82f6',
                                '#10b981',
                                '#8b5cf6',
                                '#f59e0b'
                            ][:len(values)],
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
            
            calc_type = data.get('calc_type', 'basic')
            
            if calc_type == 'basic':
                # Basic probability: favorable / total
                favorable, error1 = self._validate_positive_number(data.get('favorable'), 'Favorable outcomes', allow_zero=True)
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                total, error2 = self._validate_positive_number(data.get('total'), 'Total outcomes')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                if favorable > total:
                    return JsonResponse({'success': False, 'error': 'Favorable outcomes cannot exceed total outcomes.'}, status=400)
                
                result, error = self._calculate_basic_probability(favorable, total)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('basic', result)
                chart_data = self._prepare_chart_data('basic', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'probability': result['probability'],
                    'favorable': favorable,
                    'total': total,
                    'unfavorable': result['unfavorable'],
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'conditional':
                # Conditional probability: P(A|B) = P(A and B) / P(B)
                p_a_and_b, error1 = self._validate_probability(data.get('p_a_and_b'), 'P(A and B)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                p_b, error2 = self._validate_probability(data.get('p_b'), 'P(B)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                if p_a_and_b > p_b:
                    return JsonResponse({'success': False, 'error': 'P(A and B) cannot be greater than P(B).'}, status=400)
                
                result, error = self._calculate_conditional_probability(p_a_and_b, p_b)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('conditional', result)
                chart_data = self._prepare_chart_data('conditional', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'probability': result['probability'],
                    'p_a_and_b': p_a_and_b,
                    'p_b': p_b,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'joint':
                # Joint probability: P(A and B)
                p_a, error1 = self._validate_probability(data.get('p_a'), 'P(A)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                p_b, error2 = self._validate_probability(data.get('p_b'), 'P(B)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                independent = data.get('independent', 'true').lower() == 'true'
                
                result, error = self._calculate_joint_probability(p_a, p_b, independent)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('joint', result)
                chart_data = self._prepare_chart_data('joint', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'probability': result['probability'],
                    'p_a': p_a,
                    'p_b': p_b,
                    'independent': independent,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'union':
                # Union probability: P(A or B) = P(A) + P(B) - P(A and B)
                p_a, error1 = self._validate_probability(data.get('p_a'), 'P(A)')
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                p_b, error2 = self._validate_probability(data.get('p_b'), 'P(B)')
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                p_a_and_b, error3 = self._validate_probability(data.get('p_a_and_b'), 'P(A and B)')
                if error3:
                    return JsonResponse({'success': False, 'error': error3}, status=400)
                
                result, error = self._calculate_union_probability(p_a, p_b, p_a_and_b)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('union', result)
                chart_data = self._prepare_chart_data('union', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'probability': result['probability'],
                    'p_a': p_a,
                    'p_b': p_b,
                    'p_a_and_b': p_a_and_b,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Probability Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
