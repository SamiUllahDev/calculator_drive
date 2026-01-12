from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PercentageCalculator(View):
    """
    Enhanced Professional Percentage Calculator
    Supports multiple calculation modes: percentage of number, percentage increase/decrease, percentage change.
    """
    template_name = 'math_calculators/percentage_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Percentage Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value, name, allow_zero=False, allow_negative=False):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, f'{name} must be a valid number.'
            if not allow_zero and num == 0:
                return None, f'{name} cannot be zero.'
            if not allow_negative and num < 0:
                return None, f'{name} cannot be negative.'
            return num, None
        except (ValueError, TypeError):
            return None, f'{name} must be a valid number.'
    
    def _calculate_percentage_of(self, percentage, number):
        """Calculate percentage of a number"""
        result = (percentage / 100) * number
        return {
            'result': result,
            'percentage': percentage,
            'number': number
        }
    
    def _calculate_percentage_from(self, part, whole):
        """Calculate what percentage is part of whole"""
        if whole == 0:
            return None, "Whole value cannot be zero."
        percentage = (part / whole) * 100
        return {
            'result': percentage,
            'part': part,
            'whole': whole
        }, None
    
    def _calculate_percentage_increase(self, old_value, new_value):
        """Calculate percentage increase"""
        if old_value == 0:
            return None, "Old value cannot be zero for percentage increase calculation."
        increase = new_value - old_value
        percentage = (increase / old_value) * 100
        return {
            'result': percentage,
            'old_value': old_value,
            'new_value': new_value,
            'increase': increase
        }, None
    
    def _calculate_percentage_decrease(self, old_value, new_value):
        """Calculate percentage decrease"""
        if old_value == 0:
            return None, "Old value cannot be zero for percentage decrease calculation."
        decrease = old_value - new_value
        percentage = (decrease / old_value) * 100
        return {
            'result': percentage,
            'old_value': old_value,
            'new_value': new_value,
            'decrease': decrease
        }, None
    
    def _calculate_percentage_change(self, old_value, new_value):
        """Calculate percentage change (can be increase or decrease)"""
        if old_value == 0:
            return None, "Old value cannot be zero for percentage change calculation."
        change = new_value - old_value
        percentage = (change / old_value) * 100
        return {
            'result': percentage,
            'old_value': old_value,
            'new_value': new_value,
            'change': change,
            'is_increase': change > 0,
            'is_decrease': change < 0
        }, None
    
    def _prepare_step_by_step(self, calc_type, result, **kwargs):
        """Prepare step-by-step solution"""
        steps = []
        
        if calc_type == 'percentage_of':
            percentage = result['percentage']
            number = result['number']
            calc_result = result['result']
            
            steps.append(f"Given:")
            steps.append(f"  Percentage: {percentage}%")
            steps.append(f"  Number: {number}")
            steps.append("")
            steps.append("Step 1: Convert percentage to decimal")
            steps.append(f"  {percentage}% = {percentage} / 100 = {percentage / 100:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate percentage of number")
            steps.append(f"  Result = {percentage / 100:.6f} × {number}")
            steps.append(f"  Result = {calc_result:.6f}")
            steps.append("")
            steps.append(f"Answer: {percentage}% of {number} = {calc_result:.6f}")
        
        elif calc_type == 'percentage_from':
            part = result['part']
            whole = result['whole']
            percentage = result['result']
            
            steps.append(f"Given:")
            steps.append(f"  Part: {part}")
            steps.append(f"  Whole: {whole}")
            steps.append("")
            steps.append("Step 1: Calculate percentage")
            steps.append(f"  Percentage = (Part / Whole) × 100%")
            steps.append(f"  Percentage = ({part} / {whole}) × 100%")
            steps.append(f"  Percentage = {part / whole:.6f} × 100%")
            steps.append(f"  Percentage = {percentage:.6f}%")
            steps.append("")
            steps.append(f"Answer: {part} is {percentage:.6f}% of {whole}")
        
        elif calc_type == 'percentage_increase':
            old_value = result['old_value']
            new_value = result['new_value']
            increase = result['increase']
            percentage = result['result']
            
            steps.append(f"Given:")
            steps.append(f"  Old Value: {old_value}")
            steps.append(f"  New Value: {new_value}")
            steps.append("")
            steps.append("Step 1: Calculate increase")
            steps.append(f"  Increase = New Value - Old Value")
            steps.append(f"  Increase = {new_value} - {old_value}")
            steps.append(f"  Increase = {increase:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate percentage increase")
            steps.append(f"  Percentage Increase = (Increase / Old Value) × 100%")
            steps.append(f"  Percentage Increase = ({increase:.6f} / {old_value}) × 100%")
            steps.append(f"  Percentage Increase = {increase / old_value:.6f} × 100%")
            steps.append(f"  Percentage Increase = {percentage:.6f}%")
            steps.append("")
            steps.append(f"Answer: {percentage:.6f}% increase from {old_value} to {new_value}")
        
        elif calc_type == 'percentage_decrease':
            old_value = result['old_value']
            new_value = result['new_value']
            decrease = result['decrease']
            percentage = result['result']
            
            steps.append(f"Given:")
            steps.append(f"  Old Value: {old_value}")
            steps.append(f"  New Value: {new_value}")
            steps.append("")
            steps.append("Step 1: Calculate decrease")
            steps.append(f"  Decrease = Old Value - New Value")
            steps.append(f"  Decrease = {old_value} - {new_value}")
            steps.append(f"  Decrease = {decrease:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate percentage decrease")
            steps.append(f"  Percentage Decrease = (Decrease / Old Value) × 100%")
            steps.append(f"  Percentage Decrease = ({decrease:.6f} / {old_value}) × 100%")
            steps.append(f"  Percentage Decrease = {decrease / old_value:.6f} × 100%")
            steps.append(f"  Percentage Decrease = {percentage:.6f}%")
            steps.append("")
            steps.append(f"Answer: {percentage:.6f}% decrease from {old_value} to {new_value}")
        
        elif calc_type == 'percentage_change':
            old_value = result['old_value']
            new_value = result['new_value']
            change = result['change']
            percentage = result['result']
            is_increase = result['is_increase']
            
            steps.append(f"Given:")
            steps.append(f"  Old Value: {old_value}")
            steps.append(f"  New Value: {new_value}")
            steps.append("")
            steps.append("Step 1: Calculate change")
            steps.append(f"  Change = New Value - Old Value")
            steps.append(f"  Change = {new_value} - {old_value}")
            steps.append(f"  Change = {change:.6f}")
            steps.append("")
            steps.append("Step 2: Calculate percentage change")
            steps.append(f"  Percentage Change = (Change / Old Value) × 100%")
            steps.append(f"  Percentage Change = ({change:.6f} / {old_value}) × 100%")
            steps.append(f"  Percentage Change = {change / old_value:.6f} × 100%")
            steps.append(f"  Percentage Change = {percentage:.6f}%")
            steps.append("")
            if is_increase:
                steps.append(f"Answer: {percentage:.6f}% increase from {old_value} to {new_value}")
            else:
                steps.append(f"Answer: {abs(percentage):.6f}% decrease from {old_value} to {new_value}")
        
        return steps
    
    def _prepare_chart_data(self, calc_type, result):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            if calc_type == 'percentage_of':
                # Pie chart showing percentage
                percentage = result['percentage']
                number = result['number']
                calc_result = result['result']
                remainder = number - calc_result
                
                chart_data['pie_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': [f'{percentage}%', 'Remainder'],
                        'datasets': [{
                            'data': [calc_result, remainder],
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
            
            elif calc_type in ['percentage_increase', 'percentage_decrease', 'percentage_change']:
                # Bar chart comparing old and new values
                old_value = result['old_value']
                new_value = result['new_value']
                
                chart_data['comparison_chart'] = {
                    'type': 'bar',
                    'data': {
                        'labels': ['Old Value', 'New Value'],
                        'datasets': [{
                            'label': 'Value',
                            'data': [old_value, new_value],
                            'backgroundColor': [
                                'rgba(239, 68, 68, 0.6)',
                                'rgba(16, 185, 129, 0.6)'
                            ],
                            'borderColor': [
                                '#ef4444',
                                '#10b981'
                            ],
                            'borderWidth': 2
                        }]
                    }
                }
            
            elif calc_type == 'percentage_from':
                # Pie chart showing part vs whole
                part = result['part']
                whole = result['whole']
                remainder = whole - part
                percentage = result['result']
                
                chart_data['pie_chart'] = {
                    'type': 'doughnut',
                    'data': {
                        'labels': [f'Part ({percentage:.1f}%)', 'Remainder'],
                        'datasets': [{
                            'data': [part, remainder],
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
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            calc_type = data.get('calc_type', 'percentage_of')
            
            if calc_type == 'percentage_of':
                percentage, error1 = self._validate_number(data.get('percentage'), 'Percentage', allow_zero=True, allow_negative=True)
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                number, error2 = self._validate_number(data.get('number'), 'Number', allow_zero=True, allow_negative=True)
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                result = self._calculate_percentage_of(percentage, number)
                step_by_step = self._prepare_step_by_step('percentage_of', result)
                chart_data = self._prepare_chart_data('percentage_of', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'result': result['result'],
                    'percentage': percentage,
                    'number': number,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'percentage_from':
                part, error1 = self._validate_number(data.get('part'), 'Part', allow_zero=True, allow_negative=True)
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                whole, error2 = self._validate_number(data.get('whole'), 'Whole', allow_zero=False, allow_negative=True)
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                result, error = self._calculate_percentage_from(part, whole)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('percentage_from', result)
                chart_data = self._prepare_chart_data('percentage_from', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'result': result['result'],
                    'part': part,
                    'whole': whole,
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'percentage_increase':
                old_value, error1 = self._validate_number(data.get('old_value'), 'Old value', allow_zero=False, allow_negative=True)
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                new_value, error2 = self._validate_number(data.get('new_value'), 'New value', allow_zero=True, allow_negative=True)
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                result, error = self._calculate_percentage_increase(old_value, new_value)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('percentage_increase', result)
                chart_data = self._prepare_chart_data('percentage_increase', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'result': result['result'],
                    'old_value': old_value,
                    'new_value': new_value,
                    'increase': result['increase'],
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'percentage_decrease':
                old_value, error1 = self._validate_number(data.get('old_value'), 'Old value', allow_zero=False, allow_negative=True)
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                new_value, error2 = self._validate_number(data.get('new_value'), 'New value', allow_zero=True, allow_negative=True)
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                result, error = self._calculate_percentage_decrease(old_value, new_value)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('percentage_decrease', result)
                chart_data = self._prepare_chart_data('percentage_decrease', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'result': result['result'],
                    'old_value': old_value,
                    'new_value': new_value,
                    'decrease': result['decrease'],
                    'step_by_step': step_by_step,
                    'chart_data': chart_data
                }
            
            elif calc_type == 'percentage_change':
                old_value, error1 = self._validate_number(data.get('old_value'), 'Old value', allow_zero=False, allow_negative=True)
                if error1:
                    return JsonResponse({'success': False, 'error': error1}, status=400)
                
                new_value, error2 = self._validate_number(data.get('new_value'), 'New value', allow_zero=True, allow_negative=True)
                if error2:
                    return JsonResponse({'success': False, 'error': error2}, status=400)
                
                result, error = self._calculate_percentage_change(old_value, new_value)
                if error:
                    return JsonResponse({'success': False, 'error': error}, status=400)
                
                step_by_step = self._prepare_step_by_step('percentage_change', result)
                chart_data = self._prepare_chart_data('percentage_change', result)
                
                response = {
                    'success': True,
                    'calc_type': calc_type,
                    'result': result['result'],
                    'old_value': old_value,
                    'new_value': new_value,
                    'change': result['change'],
                    'is_increase': result['is_increase'],
                    'is_decrease': result['is_decrease'],
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
            print(f"Percentage Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
