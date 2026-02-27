from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, Eq, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HeightCalculator(View):
    """
    Professional Height Calculator with Comprehensive Features
    
    This calculator provides height calculations with:
    - Convert height between different units (feet/inches, cm, meters)
    - Predict child's height from parents' heights
    - Compare heights
    - Calculate height percentiles
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/height_calculator.html'
    
    # Conversion factors
    INCHES_TO_CM = 2.54
    CM_TO_INCHES = 1.0 / 2.54
    FEET_TO_INCHES = 12.0
    INCHES_TO_FEET = 1.0 / 12.0
    CM_TO_METERS = 0.01
    METERS_TO_CM = 100.0
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Height Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'convert')
            
            if calc_type == 'convert':
                return self._convert_height(data)
            elif calc_type == 'predict':
                return self._predict_height(data)
            elif calc_type == 'compare':
                return self._compare_heights(data)
            elif calc_type == 'percentile':
                return self._calculate_percentile(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('An error occurred')) + ': ' + str(e)
            }, status=500)
    
    def _convert_height(self, data):
        """Convert height between different units"""
        try:
            from_unit = data.get('from_unit', 'feet_inches')
            to_unit = data.get('to_unit', 'cm')
            
            # Handle feet/inches input
            if from_unit == 'feet_inches':
                feet = float(data.get('feet', 0))
                inches = float(data.get('inches', 0))
                if feet < 0 or inches < 0 or inches >= 12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid feet/inches values. Feet must be ≥ 0, inches must be 0-11.')
                    }, status=400)
                total_inches = float(np.add(np.multiply(feet, self.FEET_TO_INCHES), inches))
                value_cm = float(np.multiply(total_inches, self.INCHES_TO_CM))
                value = value_cm  # for step-by-step reference
            else:
                # value is required for non-feet_inches units
                if 'value' not in data or data.get('value') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Height value is required.')
                    }, status=400)
                
                try:
                    value = float(data.get('value', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter a numeric value.')
                    }, status=400)
                
                if from_unit == 'inches':
                    if value < 0:
                        return JsonResponse({
                            'success': False,
                            'error': _('Height must be non-negative.')
                        }, status=400)
                    value_cm = float(np.multiply(value, self.INCHES_TO_CM))
                elif from_unit == 'cm':
                    if value < 0:
                        return JsonResponse({
                            'success': False,
                            'error': _('Height must be non-negative.')
                        }, status=400)
                    value_cm = value
                elif from_unit == 'meters':
                    if value < 0:
                        return JsonResponse({
                            'success': False,
                            'error': _('Height must be non-negative.')
                        }, status=400)
                    value_cm = float(np.multiply(value, self.METERS_TO_CM))
                else:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid from unit.')
                    }, status=400)
            
            # Validate reasonable height range (0.5m to 3m)
            if value_cm < 50 or value_cm > 300:
                return JsonResponse({
                    'success': False,
                    'error': _('Height must be between 50 cm (1.64 ft) and 300 cm (9.84 ft).')
                }, status=400)
            
            # Convert to target unit
            if to_unit == 'feet_inches':
                total_inches = float(np.multiply(value_cm, self.CM_TO_INCHES))
                feet = int(np.floor(np.divide(total_inches, self.FEET_TO_INCHES)))
                inches = float(np.subtract(total_inches, np.multiply(feet, self.FEET_TO_INCHES)))
                result = {'feet': feet, 'inches': round(inches, 2)}
            elif to_unit == 'inches':
                result = round(float(np.multiply(value_cm, self.CM_TO_INCHES)), 2)
            elif to_unit == 'cm':
                result = round(value_cm, 2)
            elif to_unit == 'meters':
                result = round(float(np.multiply(value_cm, self.CM_TO_METERS)), 2)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid to unit.')
                }, status=400)
            
            # Validate result
            if isinstance(result, dict):
                if math.isinf(result['inches']) or math.isnan(result['inches']):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid conversion result.')
                    }, status=400)
            else:
                if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid conversion result.')
                    }, status=400)
            
            steps = self._prepare_convert_steps(value, from_unit, to_unit, result, value_cm, feet if from_unit == 'feet_inches' else None, inches if from_unit == 'feet_inches' else None)
            
            chart_data = self._prepare_convert_chart_data(value_cm, to_unit, result)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': result,
                'value_cm': value_cm,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input')) + ': ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Error converting height')) + ': ' + str(e)
            }, status=500)
    
    def _predict_height(self, data):
        """Predict child's height from parents' heights"""
        try:
            if 'father_height' not in data or data.get('father_height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Father\'s height is required.')
                }, status=400)
            
            if 'mother_height' not in data or data.get('mother_height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mother\'s height is required.')
                }, status=400)
            
            try:
                father_height = float(data.get('father_height', 0))
                mother_height = float(data.get('mother_height', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            height_unit = data.get('height_unit', 'cm')
            child_gender = data.get('child_gender', 'male')
            result_unit = data.get('result_unit', 'cm')
            
            # Validate units
            if height_unit not in ['cm', 'feet_inches', 'inches', 'meters']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid height unit.')
                }, status=400)
            
            if result_unit not in ['cm', 'feet_inches', 'inches', 'meters']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Convert to cm
            father_cm = self._convert_to_cm(father_height, height_unit, data.get('father_feet'), data.get('father_inches'))
            mother_cm = self._convert_to_cm(mother_height, height_unit, data.get('mother_feet'), data.get('mother_inches'))
            
            # Validate ranges
            if father_cm < 50 or father_cm > 300 or mother_cm < 50 or mother_cm > 300:
                return JsonResponse({
                    'success': False,
                    'error': _('Parent heights must be between 50 cm (1.64 ft) and 300 cm (9.84 ft).')
                }, status=400)
            
            # Predict height using mid-parental height method
            # For boys: (Father's height + Mother's height + 13 cm) / 2
            # For girls: (Father's height + Mother's height - 13 cm) / 2
            if child_gender == 'male':
                predicted_cm = float(np.divide(
                    np.add(np.add(father_cm, mother_cm), 13.0),
                    2.0
                ))
            else:
                predicted_cm = float(np.divide(
                    np.subtract(np.add(father_cm, mother_cm), 13.0),
                    2.0
                ))
            
            # Range: ±8.5 cm
            range_low = float(np.subtract(predicted_cm, 8.5))
            range_high = float(np.add(predicted_cm, 8.5))
            
            # Convert to result unit
            result = self._convert_from_cm(predicted_cm, result_unit)
            range_low_result = self._convert_from_cm(range_low, result_unit)
            range_high_result = self._convert_from_cm(range_high, result_unit)
            
            # Validate result
            if math.isinf(predicted_cm) or math.isnan(predicted_cm) or np.isinf(predicted_cm) or np.isnan(predicted_cm):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_predict_steps(father_cm, mother_cm, child_gender, predicted_cm, range_low, range_high, result_unit, result, range_low_result, range_high_result)
            
            chart_data = self._prepare_predict_chart_data(father_cm, mother_cm, predicted_cm, range_low, range_high)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'predict',
                'father_height': father_height,
                'mother_height': mother_height,
                'height_unit': height_unit,
                'child_gender': child_gender,
                'predicted_height_cm': round(predicted_cm, 1),
                'predicted_height': result,
                'range_low': range_low_result,
                'range_high': range_high_result,
                'result_unit': result_unit,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input')) + ': ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Error predicting height')) + ': ' + str(e)
            }, status=500)
    
    def _compare_heights(self, data):
        """Compare two heights"""
        try:
            if 'height1' not in data or data.get('height1') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('First height is required.')
                }, status=400)
            
            if 'height2' not in data or data.get('height2') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Second height is required.')
                }, status=400)
            
            try:
                height1 = float(data.get('height1', 0))
                height2 = float(data.get('height2', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            height_unit = data.get('height_unit', 'cm')
            
            # Convert to cm
            height1_cm = self._convert_to_cm(height1, height_unit, data.get('height1_feet'), data.get('height1_inches'))
            height2_cm = self._convert_to_cm(height2, height_unit, data.get('height2_feet'), data.get('height2_inches'))
            
            # Validate ranges
            if height1_cm < 50 or height1_cm > 300 or height2_cm < 50 or height2_cm > 300:
                return JsonResponse({
                    'success': False,
                    'error': _('Heights must be between 50 cm (1.64 ft) and 300 cm (9.84 ft).')
                }, status=400)
            
            # Calculate difference
            difference_cm = float(np.subtract(height1_cm, height2_cm))
            difference_percent = float(np.multiply(
                np.divide(difference_cm, height2_cm),
                100.0
            )) if height2_cm > 0 else 0
            
            # Validate result
            if math.isinf(difference_cm) or math.isnan(difference_cm) or np.isinf(difference_cm) or np.isnan(difference_cm):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_compare_steps(height1_cm, height2_cm, difference_cm, difference_percent)
            
            chart_data = self._prepare_compare_chart_data(height1_cm, height2_cm)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'compare',
                'height1': height1,
                'height2': height2,
                'height_unit': height_unit,
                'height1_cm': round(height1_cm, 1),
                'height2_cm': round(height2_cm, 1),
                'difference_cm': round(difference_cm, 1),
                'difference_percent': round(difference_percent, 1),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input')) + ': ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Error comparing heights')) + ': ' + str(e)
            }, status=500)
    
    def _calculate_percentile(self, data):
        """Calculate height percentile (simplified)"""
        try:
            if 'height' not in data or data.get('height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Height is required.')
                }, status=400)
            
            try:
                height = float(data.get('height', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            height_unit = data.get('height_unit', 'cm')
            age = int(data.get('age', 18))
            gender = data.get('gender', 'male')
            
            # Convert to cm
            height_cm = self._convert_to_cm(height, height_unit, data.get('feet'), data.get('inches'))
            
            # Validate ranges
            if height_cm < 50 or height_cm > 300:
                return JsonResponse({
                    'success': False,
                    'error': _('Height must be between 50 cm (1.64 ft) and 300 cm (9.84 ft).')
                }, status=400)
            
            if age < 0 or age > 120:
                return JsonResponse({
                    'success': False,
                    'error': _('Age must be between 0 and 120 years.')
                }, status=400)
            
            # Simplified percentile calculation (this is a basic approximation)
            # In reality, percentile calculations require detailed growth charts
            # This is a simplified version for demonstration
            if gender == 'male':
                # Approximate average heights by age (simplified)
                avg_heights = {
                    18: 175, 20: 176, 25: 177, 30: 177, 40: 176, 50: 175
                }
                avg_height = avg_heights.get(age, 175)
                std_dev = 7.0
            else:
                avg_heights = {
                    18: 163, 20: 163, 25: 163, 30: 163, 40: 162, 50: 161
                }
                avg_height = avg_heights.get(age, 163)
                std_dev = 6.5
            
            # Calculate z-score
            z_score = float(np.divide(np.subtract(height_cm, avg_height), std_dev))
            
            # Approximate percentile (simplified)
            # Using normal distribution approximation
            if z_score <= -2:
                percentile = 2.5
            elif z_score <= -1:
                percentile = 16
            elif z_score <= 0:
                percentile = 50
            elif z_score <= 1:
                percentile = 84
            elif z_score <= 2:
                percentile = 97.5
            else:
                percentile = 99.9
            
            steps = self._prepare_percentile_steps(height_cm, age, gender, avg_height, std_dev, z_score, percentile)
            
            chart_data = self._prepare_percentile_chart_data(height_cm, avg_height, std_dev)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'percentile',
                'height': height,
                'height_unit': height_unit,
                'height_cm': round(height_cm, 1),
                'age': age,
                'gender': gender,
                'percentile': round(percentile, 1),
                'z_score': round(z_score, 2),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input')) + ': ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Error calculating percentile')) + ': ' + str(e)
            }, status=500)
    
    def _convert_to_cm(self, value, unit, feet=None, inches=None):
        """Convert height to centimeters"""
        if unit == 'feet_inches':
            if feet is None or inches is None:
                raise ValueError('Feet and inches required for feet_inches unit')
            total_inches = float(np.add(np.multiply(feet, self.FEET_TO_INCHES), inches))
            return float(np.multiply(total_inches, self.INCHES_TO_CM))
        elif unit == 'inches':
            return float(np.multiply(value, self.INCHES_TO_CM))
        elif unit == 'cm':
            return value
        elif unit == 'meters':
            return float(np.multiply(value, self.METERS_TO_CM))
        else:
            raise ValueError(f'Invalid unit: {unit}')
    
    def _convert_from_cm(self, value_cm, unit):
        """Convert height from centimeters"""
        if unit == 'feet_inches':
            total_inches = float(np.multiply(value_cm, self.CM_TO_INCHES))
            feet = int(np.floor(np.divide(total_inches, self.FEET_TO_INCHES)))
            inches = float(np.subtract(total_inches, np.multiply(feet, self.FEET_TO_INCHES)))
            return {'feet': feet, 'inches': round(inches, 2)}
        elif unit == 'inches':
            return round(float(np.multiply(value_cm, self.CM_TO_INCHES)), 2)
        elif unit == 'cm':
            return round(value_cm, 2)
        elif unit == 'meters':
            return round(float(np.multiply(value_cm, self.CM_TO_METERS)), 2)
        else:
            raise ValueError(f'Invalid unit: {unit}')
    
    # Step-by-step solution preparation methods
    def _prepare_convert_steps(self, value, from_unit, to_unit, result, value_cm, feet, inches):
        """Prepare step-by-step solution for height conversion"""
        steps = []
        steps.append(str(_('Step 1: Identify the given value')))
        if from_unit == 'feet_inches':
            steps.append(str(_('Height')) + ': ' + str(int(feet)) + ' ft ' + str(inches) + ' in')
        else:
            steps.append(str(_('Height')) + ': ' + str(value) + ' ' + str(from_unit))
        steps.append('')
        steps.append(str(_('Step 2: Convert to centimeters (base unit)')))
        if from_unit == 'feet_inches':
            total_inches = feet * 12 + inches
            steps.append(str(_('Total inches')) + ' = ' + str(int(feet)) + ' ft × 12 + ' + str(inches) + ' in = ' + str(total_inches) + ' in')
            steps.append(str(_('Centimeters')) + ' = ' + str(total_inches) + ' in × 2.54 = ' + str(value_cm) + ' cm')
        elif from_unit == 'inches':
            steps.append(str(_('Centimeters')) + ' = ' + str(value) + ' in × 2.54 = ' + str(value_cm) + ' cm')
        elif from_unit == 'cm':
            steps.append(str(_('Height in centimeters')) + ': ' + str(value_cm) + ' cm')
        elif from_unit == 'meters':
            steps.append(str(_('Centimeters')) + ' = ' + str(value) + ' m × 100 = ' + str(value_cm) + ' cm')
        steps.append('')
        steps.append(str(_('Step 3: Convert to desired unit')))
        if to_unit == 'feet_inches':
            total_inches = value_cm * self.CM_TO_INCHES
            result_feet = result['feet']
            result_inches = result['inches']
            steps.append(str(_('Inches')) + ' = ' + str(value_cm) + ' cm × (1/2.54) = ' + str(total_inches) + ' in')
            steps.append(str(_('Feet')) + ' = ' + str(total_inches) + ' in / 12 = ' + str(result_feet) + ' ft')
            steps.append(str(_('Remaining inches')) + ' = ' + str(result_inches) + ' in')
            steps.append(str(_('Result')) + ': ' + str(result_feet) + ' ft ' + str(result_inches) + ' in')
        elif to_unit == 'inches':
            steps.append(str(_('Inches')) + ' = ' + str(value_cm) + ' cm × (1/2.54) = ' + str(result) + ' in')
        elif to_unit == 'cm':
            steps.append(str(_('Result')) + ': ' + str(result) + ' cm')
        elif to_unit == 'meters':
            steps.append(str(_('Meters')) + ' = ' + str(value_cm) + ' cm / 100 = ' + str(result) + ' m')
        return steps
    
    def _prepare_predict_steps(self, father_cm, mother_cm, child_gender, predicted_cm, range_low, range_high, result_unit, result, range_low_result, range_high_result):
        """Prepare step-by-step solution for height prediction"""
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Father\'s height')) + ': ' + str(father_cm) + ' cm')
        steps.append(str(_('Mother\'s height')) + ': ' + str(mother_cm) + ' cm')
        steps.append(str(_('Child\'s gender')) + ': ' + (str(_('Male')) if child_gender == 'male' else str(_('Female'))))
        steps.append('')
        steps.append(str(_('Step 2: Apply the mid-parental height formula')))
        if child_gender == 'male':
            steps.append(str(_('Formula for boys: (Father\'s height + Mother\'s height + 13 cm) / 2')))
            steps.append(str(_('Predicted height')) + ' = (' + str(father_cm) + ' + ' + str(mother_cm) + ' + 13) / 2')
        else:
            steps.append(str(_('Formula for girls: (Father\'s height + Mother\'s height - 13 cm) / 2')))
            steps.append(str(_('Predicted height')) + ' = (' + str(father_cm) + ' + ' + str(mother_cm) + ' - 13) / 2')
        steps.append(str(_('Predicted height')) + ' = ' + str(predicted_cm) + ' cm')
        steps.append('')
        steps.append(str(_('Step 3: Calculate prediction range')))
        steps.append(str(_('Range: ±8.5 cm from predicted height')))
        steps.append(str(_('Low range')) + ': ' + str(range_low) + ' cm')
        steps.append(str(_('High range')) + ': ' + str(range_high) + ' cm')
        steps.append('')
        steps.append(str(_('Step 4: Convert to desired unit')))
        if result_unit == 'feet_inches':
            steps.append(str(_('Predicted height')) + ': ' + str(result['feet']) + ' ft ' + str(result['inches']) + ' in')
            steps.append(str(_('Range')) + ': ' + str(range_low_result['feet']) + ' ft ' + str(range_low_result['inches']) + ' in ' + str(_('to')) + ' ' + str(range_high_result['feet']) + ' ft ' + str(range_high_result['inches']) + ' in')
        else:
            steps.append(str(_('Predicted height')) + ': ' + str(result) + ' ' + str(result_unit))
            steps.append(str(_('Range')) + ': ' + str(range_low_result) + ' ' + str(_('to')) + ' ' + str(range_high_result) + ' ' + str(result_unit))
        return steps
    
    def _prepare_compare_steps(self, height1_cm, height2_cm, difference_cm, difference_percent):
        """Prepare step-by-step solution for height comparison"""
        steps = []
        steps.append(str(_('Step 1: Identify the given heights')))
        steps.append(str(_('Height 1')) + ': ' + str(height1_cm) + ' cm')
        steps.append(str(_('Height 2')) + ': ' + str(height2_cm) + ' cm')
        steps.append('')
        steps.append(str(_('Step 2: Calculate difference')))
        steps.append(str(_('Difference')) + ' = ' + str(_('Height 1')) + ' - ' + str(_('Height 2')))
        steps.append(str(_('Difference')) + ' = ' + str(height1_cm) + ' - ' + str(height2_cm) + ' = ' + str(difference_cm) + ' cm')
        steps.append('')
        steps.append(str(_('Step 3: Calculate percentage difference')))
        steps.append(str(_('Percentage')) + ' = (' + str(_('Difference')) + ' / ' + str(_('Height 2')) + ') × 100')
        steps.append(str(_('Percentage')) + ' = (' + str(difference_cm) + ' / ' + str(height2_cm) + ') × 100 = ' + str(difference_percent) + '%')
        if difference_cm > 0:
            steps.append(str(_('Height 1')) + ' ' + str(_('is')) + ' ' + str(abs(difference_cm)) + ' cm (' + str(abs(difference_percent)) + '%) ' + str(_('taller than')) + ' ' + str(_('Height 2')))
        elif difference_cm < 0:
            steps.append(str(_('Height 1')) + ' ' + str(_('is')) + ' ' + str(abs(difference_cm)) + ' cm (' + str(abs(difference_percent)) + '%) ' + str(_('shorter than')) + ' ' + str(_('Height 2')))
        else:
            steps.append(str(_('Both heights are equal')))
        return steps
    
    def _prepare_percentile_steps(self, height_cm, age, gender, avg_height, std_dev, z_score, percentile):
        """Prepare step-by-step solution for percentile calculation"""
        gender_label = str(_('Male')) if gender == 'male' else str(_('Female'))
        gender_plural = str(_('males')) if gender == 'male' else str(_('females'))
        steps = []
        steps.append(str(_('Step 1: Identify the given values')))
        steps.append(str(_('Height')) + ': ' + str(height_cm) + ' cm')
        steps.append(str(_('Age')) + ': ' + str(age) + ' ' + str(_('years')))
        steps.append(str(_('Gender')) + ': ' + gender_label)
        steps.append('')
        steps.append(str(_('Step 2: Determine average height for age and gender')))
        steps.append(str(_('Average height for')) + ' ' + gender_plural + ' ' + str(_('at age')) + ' ' + str(age) + ': ' + str(avg_height) + ' cm')
        steps.append(str(_('Standard deviation')) + ': ' + str(std_dev) + ' cm')
        steps.append('')
        steps.append(str(_('Step 3: Calculate z-score')))
        steps.append(str(_('Z-score')) + ' = (' + str(_('Height')) + ' - ' + str(_('Average')) + ') / ' + str(_('Standard Deviation')))
        steps.append(str(_('Z-score')) + ' = (' + str(height_cm) + ' - ' + str(avg_height) + ') / ' + str(std_dev) + ' = ' + str(z_score))
        steps.append('')
        steps.append(str(_('Step 4: Determine percentile')))
        steps.append(str(_('Percentile')) + ': ' + str(percentile) + '%')
        steps.append(str(_('This means the height is greater than')) + ' ' + str(percentile) + '% ' + str(_('of')) + ' ' + gender_plural + ' ' + str(_('of the same age')))
        return steps
    
    # Chart data preparation methods
    def _prepare_convert_chart_data(self, value_cm, to_unit, result):
        """Prepare chart data for height conversion"""
        try:
            labels = [_('Height (cm)')]
            data_values = [value_cm]
            
            if to_unit == 'feet_inches':
                labels.append(_('Height (ft)'))
                data_values.append(result['feet'] + result['inches'] / 12)
            elif to_unit == 'inches':
                labels.append(_('Height (in)'))
                data_values.append(result)
            elif to_unit == 'meters':
                labels.append(_('Height (m)'))
                data_values.append(result)
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': _('Height'),
                        'data': data_values,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Height Conversion')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Height')
                            }
                        }
                    }
                }
            }
            return {'convert_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_predict_chart_data(self, father_cm, mother_cm, predicted_cm, range_low, range_high):
        """Prepare chart data for height prediction"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Father'), _('Mother'), _('Predicted'), _('Range Low'), _('Range High')],
                    'datasets': [{
                        'label': _('Height (cm)'),
                        'data': [father_cm, mother_cm, predicted_cm, range_low, range_high],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#ec4899',
                            '#10b981',
                            '#fbbf24',
                            '#fbbf24'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Height Prediction')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Height (cm)')
                            }
                        }
                    }
                }
            }
            return {'predict_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_compare_chart_data(self, height1_cm, height2_cm):
        """Prepare chart data for height comparison"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Height 1'), _('Height 2')],
                    'datasets': [{
                        'label': _('Height (cm)'),
                        'data': [height1_cm, height2_cm],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Height Comparison')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Height (cm)')
                            }
                        }
                    }
                }
            }
            return {'compare_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_percentile_chart_data(self, height_cm, avg_height, std_dev):
        """Prepare chart data for percentile calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Your Height'), _('Average Height'), _('+1 SD'), _('-1 SD')],
                    'datasets': [{
                        'label': _('Height (cm)'),
                        'data': [height_cm, avg_height, avg_height + std_dev, avg_height - std_dev],
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#10b981',
                            '#3b82f6',
                            '#fbbf24',
                            '#fbbf24'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Height Percentile')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Height (cm)')
                            }
                        }
                    }
                }
            }
            return {'percentile_chart': chart_config}
        except Exception as e:
            return None
