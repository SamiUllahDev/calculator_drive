from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PercentErrorCalculator(View):
    """
    Enhanced Professional Percent Error Calculator
    Calculates percent error, absolute error, and relative error with step-by-step solutions.
    """
    template_name = 'math_calculators/percent_error_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Percent Error Calculator',
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
    
    def _calculate_percent_error(self, experimental, theoretical):
        """Calculate percent error"""
        if theoretical == 0:
            return None, "Theoretical value cannot be zero for percent error calculation."
        
        absolute_error = abs(experimental - theoretical)
        percent_error = (absolute_error / abs(theoretical)) * 100
        
        return {
            'absolute_error': absolute_error,
            'percent_error': percent_error,
            'relative_error': absolute_error / abs(theoretical)
        }, None
    
    def _prepare_step_by_step(self, experimental, theoretical, result):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given:")
        steps.append(f"  Experimental Value: {experimental}")
        steps.append(f"  Theoretical Value: {theoretical}")
        steps.append("")
        
        steps.append("Step 1: Calculate Absolute Error")
        steps.append(f"  Absolute Error = |Experimental - Theoretical|")
        steps.append(f"  Absolute Error = |{experimental} - {theoretical}|")
        absolute_error = abs(experimental - theoretical)
        steps.append(f"  Absolute Error = |{experimental - theoretical}|")
        steps.append(f"  Absolute Error = {absolute_error:.6f}")
        steps.append("")
        
        steps.append("Step 2: Calculate Percent Error")
        steps.append(f"  Percent Error = (Absolute Error / |Theoretical|) × 100%")
        steps.append(f"  Percent Error = ({absolute_error:.6f} / |{theoretical}|) × 100%")
        steps.append(f"  Percent Error = ({absolute_error:.6f} / {abs(theoretical):.6f}) × 100%")
        percent_error = result['percent_error']
        steps.append(f"  Percent Error = {absolute_error / abs(theoretical):.6f} × 100%")
        steps.append(f"  Percent Error = {percent_error:.6f}%")
        steps.append("")
        
        steps.append("Step 3: Calculate Relative Error")
        relative_error = result['relative_error']
        steps.append(f"  Relative Error = Absolute Error / |Theoretical|")
        steps.append(f"  Relative Error = {absolute_error:.6f} / {abs(theoretical):.6f}")
        steps.append(f"  Relative Error = {relative_error:.6f}")
        steps.append("")
        
        steps.append("Step 4: Interpretation")
        if percent_error < 1:
            steps.append(f"  Percent Error = {percent_error:.6f}% < 1%: Excellent accuracy")
        elif percent_error < 5:
            steps.append(f"  Percent Error = {percent_error:.6f}% < 5%: Good accuracy")
        elif percent_error < 10:
            steps.append(f"  Percent Error = {percent_error:.6f}% < 10%: Acceptable accuracy")
        else:
            steps.append(f"  Percent Error = {percent_error:.6f}% ≥ 10%: Poor accuracy - review measurements")
        
        # Determine if experimental is higher or lower
        if experimental > theoretical:
            steps.append(f"  Experimental value ({experimental}) is {percent_error:.6f}% higher than theoretical value ({theoretical})")
        elif experimental < theoretical:
            steps.append(f"  Experimental value ({experimental}) is {percent_error:.6f}% lower than theoretical value ({theoretical})")
        else:
            steps.append(f"  Experimental value matches theoretical value exactly (0% error)")
        
        return steps
    
    def _prepare_chart_data(self, experimental, theoretical, percent_error):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Comparison bar chart
            chart_data['comparison_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Experimental', 'Theoretical'],
                    'datasets': [{
                        'label': 'Value',
                        'data': [experimental, theoretical],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                }
            }
            
            # Error visualization
            error_magnitude = abs(experimental - theoretical)
            chart_data['error_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Absolute Error', 'Percent Error'],
                    'datasets': [{
                        'label': 'Error',
                        'data': [error_magnitude, percent_error],
                        'backgroundColor': [
                            'rgba(239, 68, 68, 0.6)',
                            'rgba(245, 158, 11, 0.6)'
                        ],
                        'borderColor': [
                            '#ef4444',
                            '#f59e0b'
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
            
            # Get inputs
            experimental, error1 = self._validate_number(data.get('experimental'), 'Experimental value', allow_zero=True)
            if error1:
                return JsonResponse({'success': False, 'error': error1}, status=400)
            
            theoretical, error2 = self._validate_number(data.get('theoretical'), 'Theoretical value', allow_zero=False)
            if error2:
                return JsonResponse({'success': False, 'error': error2}, status=400)
            
            # Calculate percent error
            result, error = self._calculate_percent_error(experimental, theoretical)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(experimental, theoretical, result)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(experimental, theoretical, result['percent_error'])
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                'experimental': experimental,
                'theoretical': theoretical,
                'absolute_error': result['absolute_error'],
                'percent_error': result['percent_error'],
                'relative_error': result['relative_error'],
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Percent Error Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
