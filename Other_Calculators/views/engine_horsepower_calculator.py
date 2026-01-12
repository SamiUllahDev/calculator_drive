from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, Eq, solve, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EngineHorsepowerCalculator(View):
    """
    Professional Engine Horsepower Calculator with Comprehensive Features
    
    This calculator provides engine horsepower calculations with:
    - Calculate horsepower from torque and RPM
    - Calculate torque from horsepower and RPM
    - Calculate RPM from horsepower and torque
    - Unit conversions (HP, kW, PS, etc.)
    
    Features:
    - Supports multiple calculation modes
    - Handles various power units
    - Provides step-by-step solutions
    - Interactive visualizations
    - Uses standard automotive formulas
    """
    template_name = 'other_calculators/engine_horsepower_calculator.html'
    
    # Power conversion factors (to HP)
    POWER_CONVERSIONS = {
        'hp': 1.0,
        'kW': 0.7457,  # 1 kW = 0.7457 HP
        'PS': 0.9863,   # 1 PS = 0.9863 HP (metric horsepower)
        'bhp': 1.0,     # Brake horsepower (same as HP)
    }
    
    # Torque conversion factors (to lb-ft)
    TORQUE_CONVERSIONS = {
        'lb_ft': 1.0,
        'nm': 0.737562,  # 1 N⋅m = 0.737562 lb⋅ft
        'kg_m': 7.233,   # 1 kg⋅m = 7.233 lb⋅ft
    }
    
    # Standard constant for HP calculation
    HP_CONSTANT = 5252.0  # Used in HP = (Torque × RPM) / 5252
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'hp': 'HP',
            'kW': 'kW',
            'PS': 'PS',
            'bhp': 'BHP',
            'lb_ft': 'lb⋅ft',
            'nm': 'N⋅m',
            'kg_m': 'kg⋅m',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Engine Horsepower Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'horsepower')
            
            if calc_type == 'horsepower':
                return self._calculate_horsepower(data)
            elif calc_type == 'torque':
                return self._calculate_torque(data)
            elif calc_type == 'rpm':
                return self._calculate_rpm(data)
            elif calc_type == 'convert_power':
                return self._convert_power_units(data)
            elif calc_type == 'convert_torque':
                return self._convert_torque_units(data)
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
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_horsepower(self, data):
        """Calculate horsepower from torque and RPM"""
        try:
            # Check for required fields
            if 'torque' not in data or data.get('torque') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque is required.')
                }, status=400)
            
            if 'rpm' not in data or data.get('rpm') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM is required.')
                }, status=400)
            
            try:
                torque = float(data.get('torque', 0))
                rpm = float(data.get('rpm', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            torque_unit = data.get('torque_unit', 'lb_ft')
            result_unit = data.get('result_unit', 'hp')
            
            # Validate units
            if torque_unit not in self.TORQUE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid torque unit.')
                }, status=400)
            
            if result_unit not in self.POWER_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid power unit.')
                }, status=400)
            
            # Validate ranges
            if torque < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque must be non-negative.')
                }, status=400)
            
            if rpm < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM must be non-negative.')
                }, status=400)
            
            if torque > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            if rpm > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            # Convert torque to lb-ft
            torque_lb_ft = float(torque * self.TORQUE_CONVERSIONS[torque_unit])
            
            # Calculate horsepower: HP = (Torque × RPM) / 5252
            hp_base = float(np.divide(np.multiply(torque_lb_ft, rpm), self.HP_CONSTANT))
            
            # Convert to result unit
            if result_unit == 'hp':
                power_result = hp_base
            else:
                # Convert HP to target unit
                power_result = float(np.divide(hp_base, self.POWER_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(power_result) or math.isnan(power_result) or np.isinf(power_result) or np.isnan(power_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_horsepower_steps(torque, torque_unit, rpm, power_result, result_unit, torque_lb_ft, hp_base)
            
            # Prepare chart data
            chart_data = self._prepare_horsepower_chart_data(torque_lb_ft, rpm, hp_base)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'horsepower',
                'torque': torque,
                'torque_unit': torque_unit,
                'rpm': rpm,
                'horsepower': power_result,
                'horsepower_unit': result_unit,
                'hp_base': hp_base,
                'torque_lb_ft': torque_lb_ft,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating horsepower: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_torque(self, data):
        """Calculate torque from horsepower and RPM"""
        try:
            # Check for required fields
            if 'horsepower' not in data or data.get('horsepower') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower is required.')
                }, status=400)
            
            if 'rpm' not in data or data.get('rpm') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM is required.')
                }, status=400)
            
            try:
                horsepower = float(data.get('horsepower', 0))
                rpm = float(data.get('rpm', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            power_unit = data.get('power_unit', 'hp')
            result_unit = data.get('result_unit', 'lb_ft')
            
            # Validate units
            if power_unit not in self.POWER_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid power unit.')
                }, status=400)
            
            if result_unit not in self.TORQUE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid torque unit.')
                }, status=400)
            
            # Validate ranges
            if horsepower < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower must be non-negative.')
                }, status=400)
            
            if rpm <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM must be greater than zero.')
                }, status=400)
            
            if horsepower > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            if rpm > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            # Convert horsepower to HP
            hp_base = float(horsepower * self.POWER_CONVERSIONS[power_unit])
            
            # Calculate torque: Torque = (HP × 5252) / RPM
            torque_lb_ft = float(np.divide(np.multiply(hp_base, self.HP_CONSTANT), rpm))
            
            # Convert to result unit
            if result_unit == 'lb_ft':
                torque_result = torque_lb_ft
            else:
                torque_result = float(np.divide(torque_lb_ft, self.TORQUE_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(torque_result) or math.isnan(torque_result) or np.isinf(torque_result) or np.isnan(torque_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_torque_steps(horsepower, power_unit, rpm, torque_result, result_unit, hp_base, torque_lb_ft)
            
            # Prepare chart data
            chart_data = self._prepare_torque_chart_data(hp_base, rpm, torque_lb_ft)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'torque',
                'horsepower': horsepower,
                'power_unit': power_unit,
                'rpm': rpm,
                'torque': torque_result,
                'torque_unit': result_unit,
                'hp_base': hp_base,
                'torque_lb_ft': torque_lb_ft,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating torque: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_rpm(self, data):
        """Calculate RPM from horsepower and torque"""
        try:
            # Check for required fields
            if 'horsepower' not in data or data.get('horsepower') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower is required.')
                }, status=400)
            
            if 'torque' not in data or data.get('torque') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque is required.')
                }, status=400)
            
            try:
                horsepower = float(data.get('horsepower', 0))
                torque = float(data.get('torque', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            power_unit = data.get('power_unit', 'hp')
            torque_unit = data.get('torque_unit', 'lb_ft')
            
            # Validate units
            if power_unit not in self.POWER_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid power unit.')
                }, status=400)
            
            if torque_unit not in self.TORQUE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid torque unit.')
                }, status=400)
            
            # Validate ranges
            if horsepower < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower must be non-negative.')
                }, status=400)
            
            if torque <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque must be greater than zero.')
                }, status=400)
            
            if horsepower > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            if torque > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            # Convert to base units
            hp_base = float(horsepower * self.POWER_CONVERSIONS[power_unit])
            torque_lb_ft = float(torque * self.TORQUE_CONVERSIONS[torque_unit])
            
            # Calculate RPM: RPM = (HP × 5252) / Torque
            rpm = float(np.divide(np.multiply(hp_base, self.HP_CONSTANT), torque_lb_ft))
            
            # Validate result
            if math.isinf(rpm) or math.isnan(rpm) or np.isinf(rpm) or np.isnan(rpm):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            if rpm < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Calculated RPM cannot be negative.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_rpm_steps(horsepower, power_unit, torque, torque_unit, rpm, hp_base, torque_lb_ft)
            
            # Prepare chart data
            chart_data = self._prepare_rpm_chart_data(hp_base, torque_lb_ft, rpm)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'rpm',
                'horsepower': horsepower,
                'power_unit': power_unit,
                'torque': torque,
                'torque_unit': torque_unit,
                'rpm': rpm,
                'hp_base': hp_base,
                'torque_lb_ft': torque_lb_ft,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating RPM: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_power_units(self, data):
        """Convert power units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Power value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'hp')
            to_unit = data.get('to_unit', 'hp')
            
            # Validate units
            if from_unit not in self.POWER_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid source unit.')
                }, status=400)
            
            if to_unit not in self.POWER_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid target unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Power must be non-negative.')
                }, status=400)
            
            # Convert to HP first, then to target unit
            hp_value = float(value * self.POWER_CONVERSIONS[from_unit])
            result = float(np.divide(hp_value, self.POWER_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_power_steps(value, from_unit, to_unit, result, hp_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_power',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': result,
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _convert_torque_units(self, data):
        """Convert torque units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'lb_ft')
            to_unit = data.get('to_unit', 'lb_ft')
            
            # Validate units
            if from_unit not in self.TORQUE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid source unit.')
                }, status=400)
            
            if to_unit not in self.TORQUE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid target unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque must be non-negative.')
                }, status=400)
            
            # Convert to lb-ft first, then to target unit
            lb_ft_value = float(value * self.TORQUE_CONVERSIONS[from_unit])
            result = float(np.divide(lb_ft_value, self.TORQUE_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_torque_steps(value, from_unit, to_unit, result, lb_ft_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_torque',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': result,
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    # Step-by-step solution preparation methods
    def _prepare_horsepower_steps(self, torque, torque_unit, rpm, horsepower, result_unit, torque_lb_ft, hp_base):
        """Prepare step-by-step solution for horsepower calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Torque: {torque} {unit}').format(torque=torque, unit=self._format_unit(torque_unit)))
        steps.append(_('RPM: {rpm}').format(rpm=rpm))
        steps.append('')
        steps.append(_('Step 2: Convert torque to lb⋅ft (if needed)'))
        if torque_unit != 'lb_ft':
            steps.append(_('Torque in lb⋅ft: {torque} lb⋅ft').format(torque=torque_lb_ft))
        else:
            steps.append(_('Torque in lb⋅ft: {torque} lb⋅ft').format(torque=torque_lb_ft))
        steps.append('')
        steps.append(_('Step 3: Apply the horsepower formula'))
        steps.append(_('Formula: HP = (Torque × RPM) / 5252'))
        steps.append(_('HP = ({torque} lb⋅ft × {rpm}) / 5252').format(torque=torque_lb_ft, rpm=rpm))
        steps.append(_('HP = {hp} HP').format(hp=hp_base))
        steps.append('')
        if result_unit != 'hp':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Horsepower = {hp} {unit}').format(hp=horsepower, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Horsepower = {hp} HP').format(hp=horsepower))
        return steps
    
    def _prepare_torque_steps(self, horsepower, power_unit, rpm, torque, result_unit, hp_base, torque_lb_ft):
        """Prepare step-by-step solution for torque calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Horsepower: {hp} {unit}').format(hp=horsepower, unit=self._format_unit(power_unit)))
        steps.append(_('RPM: {rpm}').format(rpm=rpm))
        steps.append('')
        steps.append(_('Step 2: Convert horsepower to HP (if needed)'))
        if power_unit != 'hp':
            steps.append(_('Horsepower in HP: {hp} HP').format(hp=hp_base))
        else:
            steps.append(_('Horsepower in HP: {hp} HP').format(hp=hp_base))
        steps.append('')
        steps.append(_('Step 3: Apply the torque formula'))
        steps.append(_('Formula: Torque = (HP × 5252) / RPM'))
        steps.append(_('Torque = ({hp} HP × 5252) / {rpm}').format(hp=hp_base, rpm=rpm))
        steps.append(_('Torque = {torque} lb⋅ft').format(torque=torque_lb_ft))
        steps.append('')
        if result_unit != 'lb_ft':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Torque = {torque} {unit}').format(torque=torque, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Torque = {torque} lb⋅ft').format(torque=torque))
        return steps
    
    def _prepare_rpm_steps(self, horsepower, power_unit, torque, torque_unit, rpm, hp_base, torque_lb_ft):
        """Prepare step-by-step solution for RPM calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Horsepower: {hp} {unit}').format(hp=horsepower, unit=self._format_unit(power_unit)))
        steps.append(_('Torque: {torque} {unit}').format(torque=torque, unit=self._format_unit(torque_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if power_unit != 'hp':
            steps.append(_('Horsepower in HP: {hp} HP').format(hp=hp_base))
        if torque_unit != 'lb_ft':
            steps.append(_('Torque in lb⋅ft: {torque} lb⋅ft').format(torque=torque_lb_ft))
        steps.append('')
        steps.append(_('Step 3: Apply the RPM formula'))
        steps.append(_('Formula: RPM = (HP × 5252) / Torque'))
        steps.append(_('RPM = ({hp} HP × 5252) / {torque} lb⋅ft').format(hp=hp_base, torque=torque_lb_ft))
        steps.append(_('RPM = {rpm}').format(rpm=rpm))
        return steps
    
    def _prepare_convert_power_steps(self, value, from_unit, to_unit, result, hp_value):
        """Prepare step-by-step solution for power unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Power: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'hp':
            steps.append(_('Step 2: Convert to HP'))
            steps.append(_('HP = {value} {unit} × {factor}').format(
                value=value, unit=self._format_unit(from_unit), factor=1.0 / self.POWER_CONVERSIONS[from_unit]
            ))
            steps.append(_('HP = {hp} HP').format(hp=hp_value))
            steps.append('')
        if to_unit != 'hp':
            steps.append(_('Step 3: Convert from HP to {unit}').format(unit=self._format_unit(to_unit)))
            steps.append(_('{unit} = {hp} HP / {factor}').format(
                unit=self._format_unit(to_unit), hp=hp_value, factor=1.0 / self.POWER_CONVERSIONS[to_unit]
            ))
            steps.append(_('{unit} = {result} {unit}').format(unit=self._format_unit(to_unit), result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Power = {result} HP').format(result=result))
        return steps
    
    def _prepare_convert_torque_steps(self, value, from_unit, to_unit, result, lb_ft_value):
        """Prepare step-by-step solution for torque unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Torque: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'lb_ft':
            steps.append(_('Step 2: Convert to lb⋅ft'))
            steps.append(_('lb⋅ft = {value} {unit} × {factor}').format(
                value=value, unit=self._format_unit(from_unit), factor=1.0 / self.TORQUE_CONVERSIONS[from_unit]
            ))
            steps.append(_('lb⋅ft = {lb_ft} lb⋅ft').format(lb_ft=lb_ft_value))
            steps.append('')
        if to_unit != 'lb_ft':
            steps.append(_('Step 3: Convert from lb⋅ft to {unit}').format(unit=self._format_unit(to_unit)))
            steps.append(_('{unit} = {lb_ft} lb⋅ft / {factor}').format(
                unit=self._format_unit(to_unit), lb_ft=lb_ft_value, factor=1.0 / self.TORQUE_CONVERSIONS[to_unit]
            ))
            steps.append(_('{unit} = {result} {unit}').format(unit=self._format_unit(to_unit), result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Torque = {result} lb⋅ft').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_horsepower_chart_data(self, torque_lb_ft, rpm, hp_base):
        """Prepare chart data for horsepower calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Torque (lb⋅ft)'), _('RPM'), _('Horsepower (HP)')],
                    'datasets': [{
                        'label': _('Engine Parameters'),
                        'data': [torque_lb_ft, rpm, hp_base],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
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
                            'text': _('Horsepower Calculation Breakdown')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'horsepower_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_torque_chart_data(self, hp_base, rpm, torque_lb_ft):
        """Prepare chart data for torque calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Horsepower (HP)'), _('RPM'), _('Torque (lb⋅ft)')],
                    'datasets': [{
                        'label': _('Engine Parameters'),
                        'data': [hp_base, rpm, torque_lb_ft],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
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
                            'text': _('Torque Calculation Breakdown')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'torque_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_rpm_chart_data(self, hp_base, torque_lb_ft, rpm):
        """Prepare chart data for RPM calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('Horsepower (HP)'), _('Torque (lb⋅ft)'), _('RPM')],
                    'datasets': [{
                        'data': [hp_base, torque_lb_ft, rpm],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
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
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('RPM Calculation Breakdown')
                        }
                    }
                }
            }
            return {'rpm_chart': chart_config}
        except Exception as e:
            return None
