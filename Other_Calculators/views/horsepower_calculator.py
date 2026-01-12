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
class HorsepowerCalculator(View):
    """
    Professional Horsepower Calculator with Comprehensive Features
    
    This calculator provides horsepower calculations with:
    - Calculate horsepower from torque and RPM
    - Calculate torque from horsepower and RPM
    - Calculate RPM from horsepower and torque
    - Convert between horsepower, kilowatts, and watts
    - Calculate power from force and velocity
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/horsepower_calculator.html'
    
    # Conversion factors
    HP_TO_KW = 0.7457  # 1 HP = 0.7457 kW
    KW_TO_HP = 1.0 / 0.7457  # 1 kW = 1.341 HP
    HP_TO_WATTS = 745.7  # 1 HP = 745.7 W
    WATTS_TO_HP = 1.0 / 745.7  # 1 W = 0.001341 HP
    FT_LB_TO_NM = 1.35582  # 1 ft-lb = 1.35582 N⋅m
    NM_TO_FT_LB = 1.0 / 1.35582  # 1 N⋅m = 0.737562 ft-lb
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Horsepower Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'hp_from_torque')
            
            if calc_type == 'hp_from_torque':
                return self._calculate_hp_from_torque(data)
            elif calc_type == 'torque_from_hp':
                return self._calculate_torque_from_hp(data)
            elif calc_type == 'rpm_from_hp':
                return self._calculate_rpm_from_hp(data)
            elif calc_type == 'convert_power':
                return self._convert_power_units(data)
            elif calc_type == 'hp_from_watts':
                return self._calculate_hp_from_watts(data)
            elif calc_type == 'hp_from_kw':
                return self._calculate_hp_from_kw(data)
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
    
    def _calculate_hp_from_torque(self, data):
        """Calculate horsepower from torque and RPM"""
        try:
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
            
            torque_unit = data.get('torque_unit', 'ft_lb')
            
            # Validate units
            if torque_unit not in ['ft_lb', 'nm']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid torque unit.')
                }, status=400)
            
            # Validate ranges
            if torque <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque must be greater than zero.')
                }, status=400)
            
            if rpm <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM must be greater than zero.')
                }, status=400)
            
            if rpm > 50000:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM must be less than 50,000.')
                }, status=400)
            
            # Convert torque to ft-lb if needed
            if torque_unit == 'nm':
                torque_ft_lb = float(np.multiply(torque, self.NM_TO_FT_LB))
            else:
                torque_ft_lb = torque
            
            # Calculate horsepower: HP = (Torque × RPM) / 5252
            hp = float(np.divide(np.multiply(torque_ft_lb, rpm), 5252.0))
            
            # Convert to other units
            kw = float(np.multiply(hp, self.HP_TO_KW))
            watts = float(np.multiply(hp, self.HP_TO_WATTS))
            
            # Validate result
            if math.isinf(hp) or math.isnan(hp) or np.isinf(hp) or np.isnan(hp):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_hp_from_torque_steps(torque, torque_unit, rpm, torque_ft_lb, hp, kw, watts)
            
            chart_data = self._prepare_hp_from_torque_chart_data(torque_ft_lb, rpm, hp)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'hp_from_torque',
                'torque': torque,
                'torque_unit': torque_unit,
                'rpm': rpm,
                'horsepower': round(hp, 2),
                'kilowatts': round(kw, 2),
                'watts': round(watts, 2),
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
    
    def _calculate_torque_from_hp(self, data):
        """Calculate torque from horsepower and RPM"""
        try:
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
                hp = float(data.get('horsepower', 0))
                rpm = float(data.get('rpm', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            torque_unit = data.get('torque_unit', 'ft_lb')
            
            # Validate units
            if torque_unit not in ['ft_lb', 'nm']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid torque unit.')
                }, status=400)
            
            # Validate ranges
            if hp <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower must be greater than zero.')
                }, status=400)
            
            if rpm <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('RPM must be greater than zero.')
                }, status=400)
            
            # Calculate torque: Torque = (HP × 5252) / RPM
            torque_ft_lb = float(np.divide(np.multiply(hp, 5252.0), rpm))
            
            # Convert to desired unit
            if torque_unit == 'nm':
                torque = float(np.multiply(torque_ft_lb, self.FT_LB_TO_NM))
            else:
                torque = torque_ft_lb
            
            # Validate result
            if math.isinf(torque) or math.isnan(torque) or np.isinf(torque) or np.isnan(torque):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_torque_from_hp_steps(hp, rpm, torque_ft_lb, torque, torque_unit)
            
            chart_data = self._prepare_torque_from_hp_chart_data(hp, rpm, torque_ft_lb)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'torque_from_hp',
                'horsepower': hp,
                'rpm': rpm,
                'torque': round(torque, 2),
                'torque_unit': torque_unit,
                'torque_ft_lb': round(torque_ft_lb, 2),
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
    
    def _calculate_rpm_from_hp(self, data):
        """Calculate RPM from horsepower and torque"""
        try:
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
                hp = float(data.get('horsepower', 0))
                torque = float(data.get('torque', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            torque_unit = data.get('torque_unit', 'ft_lb')
            
            # Validate units
            if torque_unit not in ['ft_lb', 'nm']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid torque unit.')
                }, status=400)
            
            # Validate ranges
            if hp <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Horsepower must be greater than zero.')
                }, status=400)
            
            if torque <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Torque must be greater than zero.')
                }, status=400)
            
            # Convert torque to ft-lb if needed
            if torque_unit == 'nm':
                torque_ft_lb = float(np.multiply(torque, self.NM_TO_FT_LB))
            else:
                torque_ft_lb = torque
            
            # Calculate RPM: RPM = (HP × 5252) / Torque
            rpm = float(np.divide(np.multiply(hp, 5252.0), torque_ft_lb))
            
            # Validate result
            if math.isinf(rpm) or math.isnan(rpm) or np.isinf(rpm) or np.isnan(rpm):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            if rpm > 50000:
                return JsonResponse({
                    'success': False,
                    'error': _('Calculated RPM exceeds reasonable limits (>50,000). Please check your inputs.')
                }, status=400)
            
            steps = self._prepare_rpm_from_hp_steps(hp, torque, torque_unit, torque_ft_lb, rpm)
            
            chart_data = self._prepare_rpm_from_hp_chart_data(hp, torque_ft_lb, rpm)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'rpm_from_hp',
                'horsepower': hp,
                'torque': torque,
                'torque_unit': torque_unit,
                'rpm': round(rpm, 1),
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
        """Convert between power units"""
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
            to_unit = data.get('to_unit', 'kw')
            
            # Validate units
            if from_unit not in ['hp', 'kw', 'watts'] or to_unit not in ['hp', 'kw', 'watts']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Power must be non-negative.')
                }, status=400)
            
            # Convert to horsepower first
            if from_unit == 'hp':
                hp_value = value
            elif from_unit == 'kw':
                hp_value = float(np.multiply(value, self.KW_TO_HP))
            elif from_unit == 'watts':
                hp_value = float(np.multiply(value, self.WATTS_TO_HP))
            
            # Convert to target unit
            if to_unit == 'hp':
                result = hp_value
            elif to_unit == 'kw':
                result = float(np.multiply(hp_value, self.HP_TO_KW))
            elif to_unit == 'watts':
                result = float(np.multiply(hp_value, self.HP_TO_WATTS))
            
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
                'result': round(result, 2),
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _calculate_hp_from_watts(self, data):
        """Calculate horsepower from watts"""
        try:
            if 'watts' not in data or data.get('watts') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Watts is required.')
                }, status=400)
            
            try:
                watts = float(data.get('watts', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            if watts < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Watts must be non-negative.')
                }, status=400)
            
            # Calculate horsepower: HP = Watts / 745.7
            hp = float(np.divide(watts, self.HP_TO_WATTS))
            kw = float(np.multiply(hp, self.HP_TO_KW))
            
            # Validate result
            if math.isinf(hp) or math.isnan(hp) or np.isinf(hp) or np.isnan(hp):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_hp_from_watts_steps(watts, hp, kw)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'hp_from_watts',
                'watts': watts,
                'horsepower': round(hp, 2),
                'kilowatts': round(kw, 2),
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _calculate_hp_from_kw(self, data):
        """Calculate horsepower from kilowatts"""
        try:
            if 'kilowatts' not in data or data.get('kilowatts') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Kilowatts is required.')
                }, status=400)
            
            try:
                kw = float(data.get('kilowatts', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            if kw < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Kilowatts must be non-negative.')
                }, status=400)
            
            # Calculate horsepower: HP = kW / 0.7457
            hp = float(np.multiply(kw, self.KW_TO_HP))
            watts = float(np.multiply(hp, self.HP_TO_WATTS))
            
            # Validate result
            if math.isinf(hp) or math.isnan(hp) or np.isinf(hp) or np.isnan(hp):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_hp_from_kw_steps(kw, hp, watts)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'hp_from_kw',
                'kilowatts': kw,
                'horsepower': round(hp, 2),
                'watts': round(watts, 2),
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    # Step-by-step solution preparation methods
    def _prepare_hp_from_torque_steps(self, torque, torque_unit, rpm, torque_ft_lb, hp, kw, watts):
        """Prepare step-by-step solution for horsepower from torque calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Torque: {torque} {unit}').format(torque=torque, unit='ft-lb' if torque_unit == 'ft_lb' else 'N⋅m'))
        steps.append(_('RPM: {rpm}').format(rpm=rpm))
        steps.append('')
        if torque_unit == 'nm':
            steps.append(_('Step 2: Convert torque to foot-pounds'))
            steps.append(_('Formula: ft-lb = N⋅m × 0.737562'))
            steps.append(_('Torque = {nm} N⋅m × 0.737562 = {ftlb} ft-lb').format(nm=torque, ftlb=torque_ft_lb))
            steps.append('')
        steps.append(_('Step 3: Apply the horsepower formula'))
        steps.append(_('Formula: HP = (Torque × RPM) / 5252'))
        steps.append(_('HP = ({torque} ft-lb × {rpm}) / 5252').format(torque=torque_ft_lb, rpm=rpm))
        steps.append(_('HP = {hp}').format(hp=hp))
        steps.append('')
        steps.append(_('Step 4: Convert to other units'))
        steps.append(_('Kilowatts = {hp} HP × 0.7457 = {kw} kW').format(hp=hp, kw=kw))
        steps.append(_('Watts = {hp} HP × 745.7 = {watts} W').format(hp=hp, watts=watts))
        return steps
    
    def _prepare_torque_from_hp_steps(self, hp, rpm, torque_ft_lb, torque, torque_unit):
        """Prepare step-by-step solution for torque from horsepower calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Horsepower: {hp} HP').format(hp=hp))
        steps.append(_('RPM: {rpm}').format(rpm=rpm))
        steps.append('')
        steps.append(_('Step 2: Apply the torque formula'))
        steps.append(_('Formula: Torque = (HP × 5252) / RPM'))
        steps.append(_('Torque = ({hp} HP × 5252) / {rpm}').format(hp=hp, rpm=rpm))
        steps.append(_('Torque = {torque} ft-lb').format(torque=torque_ft_lb))
        steps.append('')
        if torque_unit == 'nm':
            steps.append(_('Step 3: Convert to Newton-meters'))
            steps.append(_('Formula: N⋅m = ft-lb × 1.35582'))
            steps.append(_('Torque = {ftlb} ft-lb × 1.35582 = {nm} N⋅m').format(ftlb=torque_ft_lb, nm=torque))
        else:
            steps.append(_('Step 3: Result'))
            steps.append(_('Torque = {torque} ft-lb').format(torque=torque))
        return steps
    
    def _prepare_rpm_from_hp_steps(self, hp, torque, torque_unit, torque_ft_lb, rpm):
        """Prepare step-by-step solution for RPM from horsepower calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Horsepower: {hp} HP').format(hp=hp))
        steps.append(_('Torque: {torque} {unit}').format(torque=torque, unit='ft-lb' if torque_unit == 'ft_lb' else 'N⋅m'))
        steps.append('')
        if torque_unit == 'nm':
            steps.append(_('Step 2: Convert torque to foot-pounds'))
            steps.append(_('Formula: ft-lb = N⋅m × 0.737562'))
            steps.append(_('Torque = {nm} N⋅m × 0.737562 = {ftlb} ft-lb').format(nm=torque, ftlb=torque_ft_lb))
            steps.append('')
        steps.append(_('Step 3: Apply the RPM formula'))
        steps.append(_('Formula: RPM = (HP × 5252) / Torque'))
        steps.append(_('RPM = ({hp} HP × 5252) / {torque} ft-lb').format(hp=hp, torque=torque_ft_lb))
        steps.append(_('RPM = {rpm}').format(rpm=rpm))
        return steps
    
    def _prepare_convert_power_steps(self, value, from_unit, to_unit, result, hp_value):
        """Prepare step-by-step solution for power unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        unit_names = {'hp': 'HP', 'kw': 'kW', 'watts': 'W'}
        steps.append(_('Power: {value} {unit}').format(value=value, unit=unit_names[from_unit]))
        steps.append('')
        if from_unit != 'hp':
            steps.append(_('Step 2: Convert to horsepower'))
            if from_unit == 'kw':
                steps.append(_('HP = kW × 1.341'))
                steps.append(_('HP = {kw} kW × 1.341 = {hp} HP').format(kw=value, hp=hp_value))
            elif from_unit == 'watts':
                steps.append(_('HP = W / 745.7'))
                steps.append(_('HP = {w} W / 745.7 = {hp} HP').format(w=value, hp=hp_value))
            steps.append('')
        if to_unit != 'hp':
            steps.append(_('Step 3: Convert from horsepower to {unit}').format(unit=unit_names[to_unit]))
            if to_unit == 'kw':
                steps.append(_('kW = HP × 0.7457'))
                steps.append(_('kW = {hp} HP × 0.7457 = {kw} kW').format(hp=hp_value, kw=result))
            elif to_unit == 'watts':
                steps.append(_('W = HP × 745.7'))
                steps.append(_('W = {hp} HP × 745.7 = {w} W').format(hp=hp_value, w=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Power = {result} HP').format(result=result))
        return steps
    
    def _prepare_hp_from_watts_steps(self, watts, hp, kw):
        """Prepare step-by-step solution for horsepower from watts calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Power: {watts} W').format(watts=watts))
        steps.append('')
        steps.append(_('Step 2: Apply the conversion formula'))
        steps.append(_('Formula: HP = Watts / 745.7'))
        steps.append(_('HP = {watts} W / 745.7 = {hp} HP').format(watts=watts, hp=hp))
        steps.append('')
        steps.append(_('Step 3: Convert to kilowatts'))
        steps.append(_('kW = {hp} HP × 0.7457 = {kw} kW').format(hp=hp, kw=kw))
        return steps
    
    def _prepare_hp_from_kw_steps(self, kw, hp, watts):
        """Prepare step-by-step solution for horsepower from kilowatts calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Power: {kw} kW').format(kw=kw))
        steps.append('')
        steps.append(_('Step 2: Apply the conversion formula'))
        steps.append(_('Formula: HP = kW × 1.341'))
        steps.append(_('HP = {kw} kW × 1.341 = {hp} HP').format(kw=kw, hp=hp))
        steps.append('')
        steps.append(_('Step 3: Convert to watts'))
        steps.append(_('W = {hp} HP × 745.7 = {watts} W').format(hp=hp, watts=watts))
        return steps
    
    # Chart data preparation methods
    def _prepare_hp_from_torque_chart_data(self, torque_ft_lb, rpm, hp):
        """Prepare chart data for horsepower from torque calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Torque (ft-lb)'), _('RPM'), _('Horsepower (HP)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [torque_ft_lb, rpm, hp],
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
                            'text': _('Horsepower Calculation')
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
            return {'hp_from_torque_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_torque_from_hp_chart_data(self, hp, rpm, torque_ft_lb):
        """Prepare chart data for torque from horsepower calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Horsepower (HP)'), _('RPM'), _('Torque (ft-lb)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [hp, rpm, torque_ft_lb],
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
                            'text': _('Torque Calculation')
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
            return {'torque_from_hp_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_rpm_from_hp_chart_data(self, hp, torque_ft_lb, rpm):
        """Prepare chart data for RPM from horsepower calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Horsepower (HP)'), _('Torque (ft-lb)'), _('RPM')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [hp, torque_ft_lb, rpm],
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
                            'text': _('RPM Calculation')
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
            return {'rpm_from_hp_chart': chart_config}
        except Exception as e:
            return None
