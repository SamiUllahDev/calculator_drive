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
class OhmsLawCalculator(View):
    """
    Professional Ohm's Law Calculator with Comprehensive Features
    
    This calculator provides Ohm's Law calculations with:
    - Calculate voltage from current and resistance (V = I × R)
    - Calculate current from voltage and resistance (I = V / R)
    - Calculate resistance from voltage and current (R = V / I)
    - Calculate power from voltage and current (P = V × I)
    - Calculate power from current and resistance (P = I² × R)
    - Calculate power from voltage and resistance (P = V² / R)
    - Unit conversions
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/ohms_law_calculator.html'
    
    # Unit conversion factors
    VOLTAGE_CONVERSIONS = {
        'volts': 1.0,
        'millivolts': 0.001,  # 1 mV = 0.001 V
        'kilovolts': 1000.0,  # 1 kV = 1000 V
    }
    
    CURRENT_CONVERSIONS = {
        'amperes': 1.0,
        'milliamperes': 0.001,  # 1 mA = 0.001 A
        'microamperes': 0.000001,  # 1 µA = 0.000001 A
    }
    
    RESISTANCE_CONVERSIONS = {
        'ohms': 1.0,
        'kiloohms': 1000.0,  # 1 kΩ = 1000 Ω
        'megaohms': 1000000.0,  # 1 MΩ = 1000000 Ω
        'milliohms': 0.001,  # 1 mΩ = 0.001 Ω
    }
    
    POWER_CONVERSIONS = {
        'watts': 1.0,
        'milliwatts': 0.001,  # 1 mW = 0.001 W
        'kilowatts': 1000.0,  # 1 kW = 1000 W
        'megawatts': 1000000.0,  # 1 MW = 1000000 W
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'volts': 'V',
            'millivolts': 'mV',
            'kilovolts': 'kV',
            'amperes': 'A',
            'milliamperes': 'mA',
            'microamperes': 'µA',
            'ohms': 'Ω',
            'kiloohms': 'kΩ',
            'megaohms': 'MΩ',
            'milliohms': 'mΩ',
            'watts': 'W',
            'milliwatts': 'mW',
            'kilowatts': 'kW',
            'megawatts': 'MW',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Ohm\'s Law Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'voltage')
            
            if calc_type == 'voltage':
                return self._calculate_voltage(data)
            elif calc_type == 'current':
                return self._calculate_current(data)
            elif calc_type == 'resistance':
                return self._calculate_resistance(data)
            elif calc_type == 'power':
                return self._calculate_power(data)
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
    
    def _calculate_voltage(self, data):
        """Calculate voltage from current and resistance: V = I × R"""
        try:
            if 'current' not in data or data.get('current') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Current is required.')
                }, status=400)
            
            if 'resistance' not in data or data.get('resistance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Resistance is required.')
                }, status=400)
            
            try:
                current = float(data.get('current', 0))
                resistance = float(data.get('resistance', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            current_unit = data.get('current_unit', 'amperes')
            resistance_unit = data.get('resistance_unit', 'ohms')
            result_unit = data.get('result_unit', 'volts')
            
            # Validate units
            if current_unit not in self.CURRENT_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid current unit.')
                }, status=400)
            
            if resistance_unit not in self.RESISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid resistance unit.')
                }, status=400)
            
            if result_unit not in self.VOLTAGE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if current < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Current must be non-negative.')
                }, status=400)
            
            if resistance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Resistance must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            current_amps = float(current * self.CURRENT_CONVERSIONS[current_unit])
            resistance_ohms = float(resistance * self.RESISTANCE_CONVERSIONS[resistance_unit])
            
            # Calculate voltage: V = I × R
            voltage_volts = float(np.multiply(current_amps, resistance_ohms))
            
            # Convert to result unit
            result = float(np.divide(voltage_volts, self.VOLTAGE_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_voltage_steps(current, current_unit, resistance, resistance_unit, current_amps, resistance_ohms, voltage_volts, result, result_unit)
            
            chart_data = self._prepare_voltage_chart_data(current_amps, resistance_ohms, voltage_volts)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'voltage',
                'current': current,
                'current_unit': current_unit,
                'resistance': resistance,
                'resistance_unit': resistance_unit,
                'voltage': round(result, 6),
                'result_unit': result_unit,
                'voltage_volts': round(voltage_volts, 6),
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
                'error': _('Error calculating voltage: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_current(self, data):
        """Calculate current from voltage and resistance: I = V / R"""
        try:
            if 'voltage' not in data or data.get('voltage') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage is required.')
                }, status=400)
            
            if 'resistance' not in data or data.get('resistance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Resistance is required.')
                }, status=400)
            
            try:
                voltage = float(data.get('voltage', 0))
                resistance = float(data.get('resistance', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            voltage_unit = data.get('voltage_unit', 'volts')
            resistance_unit = data.get('resistance_unit', 'ohms')
            result_unit = data.get('result_unit', 'amperes')
            
            # Validate units
            if voltage_unit not in self.VOLTAGE_CONVERSIONS or resistance_unit not in self.RESISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if result_unit not in self.CURRENT_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if voltage < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage must be non-negative.')
                }, status=400)
            
            if resistance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Resistance must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            voltage_volts = float(voltage * self.VOLTAGE_CONVERSIONS[voltage_unit])
            resistance_ohms = float(resistance * self.RESISTANCE_CONVERSIONS[resistance_unit])
            
            # Calculate current: I = V / R
            current_amps = float(np.divide(voltage_volts, resistance_ohms))
            
            # Convert to result unit
            result = float(np.divide(current_amps, self.CURRENT_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_current_steps(voltage, voltage_unit, resistance, resistance_unit, voltage_volts, resistance_ohms, current_amps, result, result_unit)
            
            chart_data = self._prepare_current_chart_data(voltage_volts, resistance_ohms, current_amps)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'current',
                'voltage': voltage,
                'voltage_unit': voltage_unit,
                'resistance': resistance,
                'resistance_unit': resistance_unit,
                'current': round(result, 6),
                'result_unit': result_unit,
                'current_amps': round(current_amps, 6),
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
                'error': _('Error calculating current: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_resistance(self, data):
        """Calculate resistance from voltage and current: R = V / I"""
        try:
            if 'voltage' not in data or data.get('voltage') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage is required.')
                }, status=400)
            
            if 'current' not in data or data.get('current') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Current is required.')
                }, status=400)
            
            try:
                voltage = float(data.get('voltage', 0))
                current = float(data.get('current', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            voltage_unit = data.get('voltage_unit', 'volts')
            current_unit = data.get('current_unit', 'amperes')
            result_unit = data.get('result_unit', 'ohms')
            
            # Validate units
            if voltage_unit not in self.VOLTAGE_CONVERSIONS or current_unit not in self.CURRENT_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if result_unit not in self.RESISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if voltage < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage must be non-negative.')
                }, status=400)
            
            if current <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Current must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            voltage_volts = float(voltage * self.VOLTAGE_CONVERSIONS[voltage_unit])
            current_amps = float(current * self.CURRENT_CONVERSIONS[current_unit])
            
            # Calculate resistance: R = V / I
            resistance_ohms = float(np.divide(voltage_volts, current_amps))
            
            # Convert to result unit
            result = float(np.divide(resistance_ohms, self.RESISTANCE_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_resistance_steps(voltage, voltage_unit, current, current_unit, voltage_volts, current_amps, resistance_ohms, result, result_unit)
            
            chart_data = self._prepare_resistance_chart_data(voltage_volts, current_amps, resistance_ohms)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'resistance',
                'voltage': voltage,
                'voltage_unit': voltage_unit,
                'current': current,
                'current_unit': current_unit,
                'resistance': round(result, 6),
                'result_unit': result_unit,
                'resistance_ohms': round(resistance_ohms, 6),
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
                'error': _('Error calculating resistance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_power(self, data):
        """Calculate power using various formulas"""
        try:
            power_mode = data.get('power_mode', 'from_voltage_current')
            
            if power_mode == 'from_voltage_current':
                # P = V × I
                if 'voltage' not in data or data.get('voltage') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage is required.')
                    }, status=400)
                
                if 'current' not in data or data.get('current') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current is required.')
                    }, status=400)
                
                try:
                    voltage = float(data.get('voltage', 0))
                    current = float(data.get('current', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                voltage_unit = data.get('voltage_unit', 'volts')
                current_unit = data.get('current_unit', 'amperes')
                result_unit = data.get('result_unit', 'watts')
                
                # Validate
                if voltage < 0 or current < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage and current must be non-negative.')
                    }, status=400)
                
                # Convert to base units
                voltage_volts = float(voltage * self.VOLTAGE_CONVERSIONS[voltage_unit])
                current_amps = float(current * self.CURRENT_CONVERSIONS[current_unit])
                
                # Calculate power: P = V × I
                power_watts = float(np.multiply(voltage_volts, current_amps))
                
                # Convert to result unit
                result = float(np.divide(power_watts, self.POWER_CONVERSIONS[result_unit]))
                
                steps = self._prepare_power_vi_steps(voltage, voltage_unit, current, current_unit, voltage_volts, current_amps, power_watts, result, result_unit)
                
            elif power_mode == 'from_current_resistance':
                # P = I² × R
                if 'current' not in data or data.get('current') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current is required.')
                    }, status=400)
                
                if 'resistance' not in data or data.get('resistance') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Resistance is required.')
                    }, status=400)
                
                try:
                    current = float(data.get('current', 0))
                    resistance = float(data.get('resistance', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                current_unit = data.get('current_unit', 'amperes')
                resistance_unit = data.get('resistance_unit', 'ohms')
                result_unit = data.get('result_unit', 'watts')
                
                # Validate
                if current < 0 or resistance <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current must be non-negative and resistance must be greater than zero.')
                    }, status=400)
                
                # Convert to base units
                current_amps = float(current * self.CURRENT_CONVERSIONS[current_unit])
                resistance_ohms = float(resistance * self.RESISTANCE_CONVERSIONS[resistance_unit])
                
                # Calculate power: P = I² × R
                power_watts = float(np.multiply(np.multiply(current_amps, current_amps), resistance_ohms))
                
                # Convert to result unit
                result = float(np.divide(power_watts, self.POWER_CONVERSIONS[result_unit]))
                
                steps = self._prepare_power_ir_steps(current, current_unit, resistance, resistance_unit, current_amps, resistance_ohms, power_watts, result, result_unit)
                
            else:  # from_voltage_resistance
                # P = V² / R
                if 'voltage' not in data or data.get('voltage') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage is required.')
                    }, status=400)
                
                if 'resistance' not in data or data.get('resistance') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Resistance is required.')
                    }, status=400)
                
                try:
                    voltage = float(data.get('voltage', 0))
                    resistance = float(data.get('resistance', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                voltage_unit = data.get('voltage_unit', 'volts')
                resistance_unit = data.get('resistance_unit', 'ohms')
                result_unit = data.get('result_unit', 'watts')
                
                # Validate
                if voltage < 0 or resistance <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage must be non-negative and resistance must be greater than zero.')
                    }, status=400)
                
                # Convert to base units
                voltage_volts = float(voltage * self.VOLTAGE_CONVERSIONS[voltage_unit])
                resistance_ohms = float(resistance * self.RESISTANCE_CONVERSIONS[resistance_unit])
                
                # Calculate power: P = V² / R
                power_watts = float(np.divide(np.multiply(voltage_volts, voltage_volts), resistance_ohms))
                
                # Convert to result unit
                result = float(np.divide(power_watts, self.POWER_CONVERSIONS[result_unit]))
                
                steps = self._prepare_power_vr_steps(voltage, voltage_unit, resistance, resistance_unit, voltage_volts, resistance_ohms, power_watts, result, result_unit)
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            chart_data = self._prepare_power_chart_data(power_watts)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'power',
                'power_mode': power_mode,
                'power': round(result, 6),
                'result_unit': result_unit,
                'power_watts': round(power_watts, 6),
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
                'error': _('Error calculating power: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_voltage_steps(self, current, current_unit, resistance, resistance_unit, current_amps, resistance_ohms, voltage_volts, result, result_unit):
        """Prepare step-by-step solution for voltage calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Current: {current} {unit}').format(current=current, unit=self._format_unit(current_unit)))
        steps.append(_('Resistance: {resistance} {unit}').format(resistance=resistance, unit=self._format_unit(resistance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if current_unit != 'amperes':
            steps.append(_('Current: {current} A').format(current=current_amps))
        if resistance_unit != 'ohms':
            steps.append(_('Resistance: {resistance} Ω').format(resistance=resistance_ohms))
        steps.append('')
        steps.append(_('Step 3: Apply Ohm\'s Law'))
        steps.append(_('Formula: Voltage (V) = Current (I) × Resistance (R)'))
        steps.append(_('V = I × R'))
        steps.append(_('V = {current} A × {resistance} Ω').format(current=current_amps, resistance=resistance_ohms))
        steps.append(_('V = {voltage} V').format(voltage=voltage_volts))
        steps.append('')
        if result_unit != 'volts':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Voltage = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Voltage = {result} V').format(result=result))
        return steps
    
    def _prepare_current_steps(self, voltage, voltage_unit, resistance, resistance_unit, voltage_volts, resistance_ohms, current_amps, result, result_unit):
        """Prepare step-by-step solution for current calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage: {voltage} {unit}').format(voltage=voltage, unit=self._format_unit(voltage_unit)))
        steps.append(_('Resistance: {resistance} {unit}').format(resistance=resistance, unit=self._format_unit(resistance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if voltage_unit != 'volts':
            steps.append(_('Voltage: {voltage} V').format(voltage=voltage_volts))
        if resistance_unit != 'ohms':
            steps.append(_('Resistance: {resistance} Ω').format(resistance=resistance_ohms))
        steps.append('')
        steps.append(_('Step 3: Apply Ohm\'s Law'))
        steps.append(_('Formula: Current (I) = Voltage (V) / Resistance (R)'))
        steps.append(_('I = V / R'))
        steps.append(_('I = {voltage} V / {resistance} Ω').format(voltage=voltage_volts, resistance=resistance_ohms))
        steps.append(_('I = {current} A').format(current=current_amps))
        steps.append('')
        if result_unit != 'amperes':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Current = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Current = {result} A').format(result=result))
        return steps
    
    def _prepare_resistance_steps(self, voltage, voltage_unit, current, current_unit, voltage_volts, current_amps, resistance_ohms, result, result_unit):
        """Prepare step-by-step solution for resistance calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage: {voltage} {unit}').format(voltage=voltage, unit=self._format_unit(voltage_unit)))
        steps.append(_('Current: {current} {unit}').format(current=current, unit=self._format_unit(current_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if voltage_unit != 'volts':
            steps.append(_('Voltage: {voltage} V').format(voltage=voltage_volts))
        if current_unit != 'amperes':
            steps.append(_('Current: {current} A').format(current=current_amps))
        steps.append('')
        steps.append(_('Step 3: Apply Ohm\'s Law'))
        steps.append(_('Formula: Resistance (R) = Voltage (V) / Current (I)'))
        steps.append(_('R = V / I'))
        steps.append(_('R = {voltage} V / {current} A').format(voltage=voltage_volts, current=current_amps))
        steps.append(_('R = {resistance} Ω').format(resistance=resistance_ohms))
        steps.append('')
        if result_unit != 'ohms':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Resistance = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Resistance = {result} Ω').format(result=result))
        return steps
    
    def _prepare_power_vi_steps(self, voltage, voltage_unit, current, current_unit, voltage_volts, current_amps, power_watts, result, result_unit):
        """Prepare step-by-step solution for power from V and I"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage: {voltage} {unit}').format(voltage=voltage, unit=self._format_unit(voltage_unit)))
        steps.append(_('Current: {current} {unit}').format(current=current, unit=self._format_unit(current_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if voltage_unit != 'volts':
            steps.append(_('Voltage: {voltage} V').format(voltage=voltage_volts))
        if current_unit != 'amperes':
            steps.append(_('Current: {current} A').format(current=current_amps))
        steps.append('')
        steps.append(_('Step 3: Apply power formula'))
        steps.append(_('Formula: Power (P) = Voltage (V) × Current (I)'))
        steps.append(_('P = V × I'))
        steps.append(_('P = {voltage} V × {current} A').format(voltage=voltage_volts, current=current_amps))
        steps.append(_('P = {power} W').format(power=power_watts))
        steps.append('')
        if result_unit != 'watts':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Power = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Power = {result} W').format(result=result))
        return steps
    
    def _prepare_power_ir_steps(self, current, current_unit, resistance, resistance_unit, current_amps, resistance_ohms, power_watts, result, result_unit):
        """Prepare step-by-step solution for power from I and R"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Current: {current} {unit}').format(current=current, unit=self._format_unit(current_unit)))
        steps.append(_('Resistance: {resistance} {unit}').format(resistance=resistance, unit=self._format_unit(resistance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if current_unit != 'amperes':
            steps.append(_('Current: {current} A').format(current=current_amps))
        if resistance_unit != 'ohms':
            steps.append(_('Resistance: {resistance} Ω').format(resistance=resistance_ohms))
        steps.append('')
        steps.append(_('Step 3: Apply power formula'))
        steps.append(_('Formula: Power (P) = Current² (I²) × Resistance (R)'))
        steps.append(_('P = I² × R'))
        steps.append(_('P = ({current} A)² × {resistance} Ω').format(current=current_amps, resistance=resistance_ohms))
        steps.append(_('P = {power} W').format(power=power_watts))
        steps.append('')
        if result_unit != 'watts':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Power = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Power = {result} W').format(result=result))
        return steps
    
    def _prepare_power_vr_steps(self, voltage, voltage_unit, resistance, resistance_unit, voltage_volts, resistance_ohms, power_watts, result, result_unit):
        """Prepare step-by-step solution for power from V and R"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage: {voltage} {unit}').format(voltage=voltage, unit=self._format_unit(voltage_unit)))
        steps.append(_('Resistance: {resistance} {unit}').format(resistance=resistance, unit=self._format_unit(resistance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if voltage_unit != 'volts':
            steps.append(_('Voltage: {voltage} V').format(voltage=voltage_volts))
        if resistance_unit != 'ohms':
            steps.append(_('Resistance: {resistance} Ω').format(resistance=resistance_ohms))
        steps.append('')
        steps.append(_('Step 3: Apply power formula'))
        steps.append(_('Formula: Power (P) = Voltage² (V²) / Resistance (R)'))
        steps.append(_('P = V² / R'))
        steps.append(_('P = ({voltage} V)² / {resistance} Ω').format(voltage=voltage_volts, resistance=resistance_ohms))
        steps.append(_('P = {power} W').format(power=power_watts))
        steps.append('')
        if result_unit != 'watts':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Power = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Power = {result} W').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_voltage_chart_data(self, current_amps, resistance_ohms, voltage_volts):
        """Prepare chart data for voltage calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Current (A)'), _('Resistance (Ω)'), _('Voltage (V)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [current_amps, resistance_ohms, voltage_volts],
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
                            'text': _('Ohm\'s Law: Voltage Calculation')
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
            return {'voltage_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_current_chart_data(self, voltage_volts, resistance_ohms, current_amps):
        """Prepare chart data for current calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Voltage (V)'), _('Resistance (Ω)'), _('Current (A)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [voltage_volts, resistance_ohms, current_amps],
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
                            'text': _('Ohm\'s Law: Current Calculation')
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
            return {'current_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_resistance_chart_data(self, voltage_volts, current_amps, resistance_ohms):
        """Prepare chart data for resistance calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Voltage (V)'), _('Current (A)'), _('Resistance (Ω)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [voltage_volts, current_amps, resistance_ohms],
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
                            'text': _('Ohm\'s Law: Resistance Calculation')
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
            return {'resistance_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_power_chart_data(self, power_watts):
        """Prepare chart data for power calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Power (W)')],
                    'datasets': [{
                        'label': _('Power'),
                        'data': [power_watts],
                        'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                        'borderColor': '#3b82f6',
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
                            'text': _('Power Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Power (W)')
                            }
                        }
                    }
                }
            }
            return {'power_chart': chart_config}
        except Exception as e:
            return None
