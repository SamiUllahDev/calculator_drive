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
class ElectricityCalculator(View):
    """
    Professional Electricity Calculator with Comprehensive Features
    
    This calculator provides electrical calculations with:
    - Calculate power from voltage, current, or resistance
    - Calculate voltage from power, current, or resistance
    - Calculate current from power, voltage, or resistance
    - Calculate resistance from voltage, current, or power
    - Calculate energy consumption
    - Calculate electricity cost
    
    Features:
    - Supports multiple calculation modes
    - Handles various units (V, A, W, Ω, kWh, etc.)
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/electricity_calculator.html'
    
    # Power conversion factors (to Watts)
    POWER_CONVERSIONS = {
        'W': 1.0,
        'kW': 1000.0,
        'MW': 1000000.0,
        'hp': 745.7,
        'BTU_per_hour': 0.293071,
    }
    
    # Voltage conversion factors (to Volts)
    VOLTAGE_CONVERSIONS = {
        'V': 1.0,
        'kV': 1000.0,
        'mV': 0.001,
    }
    
    # Current conversion factors (to Amperes)
    CURRENT_CONVERSIONS = {
        'A': 1.0,
        'mA': 0.001,
        'kA': 1000.0,
    }
    
    # Resistance conversion factors (to Ohms)
    RESISTANCE_CONVERSIONS = {
        'ohm': 1.0,
        'kohm': 1000.0,
        'Mohm': 1000000.0,
    }
    
    # Energy conversion factors (to kWh)
    ENERGY_CONVERSIONS = {
        'kWh': 1.0,
        'Wh': 0.001,
        'MWh': 1000.0,
        'J': 2.77778e-7,
        'MJ': 0.277778,
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'W': 'W',
            'kW': 'kW',
            'MW': 'MW',
            'hp': 'hp',
            'BTU_per_hour': 'BTU/h',
            'V': 'V',
            'kV': 'kV',
            'mV': 'mV',
            'A': 'A',
            'mA': 'mA',
            'kA': 'kA',
            'ohm': 'Ω',
            'kohm': 'kΩ',
            'Mohm': 'MΩ',
            'kWh': 'kWh',
            'Wh': 'Wh',
            'MWh': 'MWh',
            'J': 'J',
            'MJ': 'MJ',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Electricity Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'power')
            
            if calc_type == 'power':
                return self._calculate_power(data)
            elif calc_type == 'voltage':
                return self._calculate_voltage(data)
            elif calc_type == 'current':
                return self._calculate_current(data)
            elif calc_type == 'resistance':
                return self._calculate_resistance(data)
            elif calc_type == 'energy':
                return self._calculate_energy(data)
            elif calc_type == 'cost':
                return self._calculate_cost(data)
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
    
    def _calculate_power(self, data):
        """Calculate power from voltage, current, or resistance"""
        try:
            method = data.get('method', 'vi')
            result_unit = data.get('result_unit', 'W')
            
            if method == 'vi':
                # P = V × I
                # Check for required fields
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
                
                voltage_unit = data.get('voltage_unit', 'V')
                current_unit = data.get('current_unit', 'A')
                
                # Validate units
                if voltage_unit not in self.VOLTAGE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid voltage unit.')
                    }, status=400)
                
                if current_unit not in self.CURRENT_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid current unit.')
                    }, status=400)
                
                # Validate ranges
                if voltage < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage must be non-negative.')
                    }, status=400)
                
                if current < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current must be non-negative.')
                    }, status=400)
                
                if voltage > 1e6:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage is too large. Please use a value below 1,000,000 V.')
                    }, status=400)
                
                if current > 1e6:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current is too large. Please use a value below 1,000,000 A.')
                    }, status=400)
                
                # Convert to base units
                voltage_base = float(voltage * self.VOLTAGE_CONVERSIONS.get(voltage_unit, 1.0))
                current_base = float(current * self.CURRENT_CONVERSIONS.get(current_unit, 1.0))
                
                # Calculate power
                power_base = float(np.multiply(voltage_base, current_base))
                
                # Convert to result unit
                if result_unit not in self.POWER_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid power unit.')
                    }, status=400)
                
                power = float(np.divide(power_base, self.POWER_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_power_vi_steps(voltage, voltage_unit, current, current_unit, power, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_power_chart_data(voltage_base, current_base, power_base)
                
                # Validate result
                if math.isinf(power) or math.isnan(power) or np.isinf(power) or np.isnan(power):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                return JsonResponse({
                    'success': True,
                    'calc_type': 'power',
                    'method': 'vi',
                    'result': power,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'P = V × I',
                    'voltage': voltage,
                    'voltage_unit': voltage_unit,
                    'current': current,
                    'current_unit': current_unit,
                    'power_base': power_base,
                    'step_by_step': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'vr':
                # P = V² / R
                voltage = float(data.get('voltage', 0))
                voltage_unit = data.get('voltage_unit', 'V')
                resistance = float(data.get('resistance', 0))
                resistance_unit = data.get('resistance_unit', 'ohm')
                
                # Validate inputs
                if not isinstance(voltage, (int, float)) or not isinstance(resistance, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
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
                
                if voltage > 1e6 or resistance > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                voltage_base = float(voltage * self.VOLTAGE_CONVERSIONS.get(voltage_unit, 1.0))
                resistance_base = float(resistance * self.RESISTANCE_CONVERSIONS.get(resistance_unit, 1.0))
                
                # Calculate power
                voltage_squared = float(np.multiply(voltage_base, voltage_base))
                power_base = float(np.divide(voltage_squared, resistance_base))
                
                # Check for invalid results
                if not np.isfinite(power_base) or power_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.POWER_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid power unit.')
                    }, status=400)
                
                power = float(np.divide(power_base, self.POWER_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_power_vr_steps(voltage, voltage_unit, resistance, resistance_unit, power, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_power_chart_data(voltage_base, None, power_base)
                
                return JsonResponse({
                    'success': True,
                    'result': power,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'P = V² / R',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'ir':
                # P = I² × R
                current = float(data.get('current', 0))
                current_unit = data.get('current_unit', 'A')
                resistance = float(data.get('resistance', 0))
                resistance_unit = data.get('resistance_unit', 'ohm')
                
                # Validate inputs
                if not isinstance(current, (int, float)) or not isinstance(resistance, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
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
                
                if current > 1e6 or resistance > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                current_base = float(current * self.CURRENT_CONVERSIONS.get(current_unit, 1.0))
                resistance_base = float(resistance * self.RESISTANCE_CONVERSIONS.get(resistance_unit, 1.0))
                
                # Calculate power
                current_squared = float(np.multiply(current_base, current_base))
                power_base = float(np.multiply(current_squared, resistance_base))
                
                # Check for invalid results
                if not np.isfinite(power_base) or power_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.POWER_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid power unit.')
                    }, status=400)
                
                power = float(np.divide(power_base, self.POWER_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_power_ir_steps(current, current_unit, resistance, resistance_unit, power, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_power_chart_data(None, current_base, power_base)
                
                return JsonResponse({
                    'success': True,
                    'result': power,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'P = I² × R',
                    'steps': steps,
                    'chart_data': chart_data,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid power calculation method.')
                }, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input values: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_voltage(self, data):
        """Calculate voltage from power, current, or resistance"""
        try:
            method = data.get('method', 'pi')
            result_unit = data.get('result_unit', 'V')
            
            if method == 'pi':
                # V = P / I
                power = float(data.get('power', 0))
                power_unit = data.get('power_unit', 'W')
                current = float(data.get('current', 0))
                current_unit = data.get('current_unit', 'A')
                
                # Validate inputs
                if not isinstance(power, (int, float)) or not isinstance(current, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if power < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Power must be non-negative.')
                    }, status=400)
                
                if current <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current must be greater than zero.')
                    }, status=400)
                
                if power > 1e12 or current > 1e6:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                power_base = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
                current_base = float(current * self.CURRENT_CONVERSIONS.get(current_unit, 1.0))
                
                # Calculate voltage
                voltage_base = float(np.divide(power_base, current_base))
                
                # Check for invalid results
                if not np.isfinite(voltage_base) or voltage_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.VOLTAGE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid voltage unit.')
                    }, status=400)
                
                voltage = float(np.divide(voltage_base, self.VOLTAGE_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_voltage_pi_steps(power, power_unit, current, current_unit, voltage, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_voltage_chart_data(power_base, current_base, voltage_base)
                
                return JsonResponse({
                    'success': True,
                    'result': voltage,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'V = P / I',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'ir':
                # V = I × R
                current = float(data.get('current', 0))
                current_unit = data.get('current_unit', 'A')
                resistance = float(data.get('resistance', 0))
                resistance_unit = data.get('resistance_unit', 'ohm')
                
                # Validate inputs
                if not isinstance(current, (int, float)) or not isinstance(resistance, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if current < 0 or resistance < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current and resistance must be non-negative.')
                    }, status=400)
                
                if current > 1e6 or resistance > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                current_base = float(current * self.CURRENT_CONVERSIONS.get(current_unit, 1.0))
                resistance_base = float(resistance * self.RESISTANCE_CONVERSIONS.get(resistance_unit, 1.0))
                
                # Calculate voltage
                voltage_base = float(np.multiply(current_base, resistance_base))
                
                # Check for invalid results
                if not np.isfinite(voltage_base) or voltage_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.VOLTAGE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid voltage unit.')
                    }, status=400)
                
                voltage = float(np.divide(voltage_base, self.VOLTAGE_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_voltage_ir_steps(current, current_unit, resistance, resistance_unit, voltage, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_voltage_chart_data(None, current_base, voltage_base)
                
                return JsonResponse({
                    'success': True,
                    'result': voltage,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'V = I × R',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'pr':
                # V = √(P × R)
                power = float(data.get('power', 0))
                power_unit = data.get('power_unit', 'W')
                resistance = float(data.get('resistance', 0))
                resistance_unit = data.get('resistance_unit', 'ohm')
                
                # Validate inputs
                if not isinstance(power, (int, float)) or not isinstance(resistance, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if power < 0 or resistance < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Power and resistance must be non-negative.')
                    }, status=400)
                
                if power > 1e12 or resistance > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                power_base = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
                resistance_base = float(resistance * self.RESISTANCE_CONVERSIONS.get(resistance_unit, 1.0))
                
                # Calculate voltage
                pr_product = float(np.multiply(power_base, resistance_base))
                if pr_product < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Cannot calculate voltage from negative power and resistance product.')
                    }, status=400)
                
                voltage_base = float(math.sqrt(pr_product))
                
                # Check for invalid results
                if not np.isfinite(voltage_base) or voltage_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.VOLTAGE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid voltage unit.')
                    }, status=400)
                
                voltage = float(np.divide(voltage_base, self.VOLTAGE_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_voltage_pr_steps(power, power_unit, resistance, resistance_unit, voltage, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_voltage_chart_data(power_base, None, voltage_base)
                
                return JsonResponse({
                    'success': True,
                    'result': voltage,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'V = √(P × R)',
                    'steps': steps,
                    'chart_data': chart_data,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid voltage calculation method.')
                }, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input values: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_current(self, data):
        """Calculate current from power, voltage, or resistance"""
        try:
            method = data.get('method', 'pv')
            result_unit = data.get('result_unit', 'A')
            
            if method == 'pv':
                # I = P / V
                power = float(data.get('power', 0))
                power_unit = data.get('power_unit', 'W')
                voltage = float(data.get('voltage', 0))
                voltage_unit = data.get('voltage_unit', 'V')
                
                # Validate inputs
                if not isinstance(power, (int, float)) or not isinstance(voltage, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if power < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Power must be non-negative.')
                    }, status=400)
                
                if voltage <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage must be greater than zero.')
                    }, status=400)
                
                if power > 1e12 or voltage > 1e6:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                power_base = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
                voltage_base = float(voltage * self.VOLTAGE_CONVERSIONS.get(voltage_unit, 1.0))
                
                # Calculate current
                current_base = float(np.divide(power_base, voltage_base))
                
                # Check for invalid results
                if not np.isfinite(current_base) or current_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.CURRENT_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid current unit.')
                    }, status=400)
                
                current = float(np.divide(current_base, self.CURRENT_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_current_pv_steps(power, power_unit, voltage, voltage_unit, current, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_current_chart_data(power_base, voltage_base, current_base)
                
                return JsonResponse({
                    'success': True,
                    'result': current,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'I = P / V',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'vr':
                # I = V / R
                voltage = float(data.get('voltage', 0))
                voltage_unit = data.get('voltage_unit', 'V')
                resistance = float(data.get('resistance', 0))
                resistance_unit = data.get('resistance_unit', 'ohm')
                
                # Validate inputs
                if not isinstance(voltage, (int, float)) or not isinstance(resistance, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
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
                
                if voltage > 1e6 or resistance > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                voltage_base = float(voltage * self.VOLTAGE_CONVERSIONS.get(voltage_unit, 1.0))
                resistance_base = float(resistance * self.RESISTANCE_CONVERSIONS.get(resistance_unit, 1.0))
                
                # Calculate current
                current_base = float(np.divide(voltage_base, resistance_base))
                
                # Check for invalid results
                if not np.isfinite(current_base) or current_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.CURRENT_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid current unit.')
                    }, status=400)
                
                current = float(np.divide(current_base, self.CURRENT_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_current_vr_steps(voltage, voltage_unit, resistance, resistance_unit, current, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_current_chart_data(voltage_base, None, current_base)
                
                return JsonResponse({
                    'success': True,
                    'result': current,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'I = V / R',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'pr':
                # I = √(P / R)
                power = float(data.get('power', 0))
                power_unit = data.get('power_unit', 'W')
                resistance = float(data.get('resistance', 0))
                resistance_unit = data.get('resistance_unit', 'ohm')
                
                # Validate inputs
                if not isinstance(power, (int, float)) or not isinstance(resistance, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if power < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Power must be non-negative.')
                    }, status=400)
                
                if resistance <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Resistance must be greater than zero.')
                    }, status=400)
                
                if power > 1e12 or resistance > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                power_base = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
                resistance_base = float(resistance * self.RESISTANCE_CONVERSIONS.get(resistance_unit, 1.0))
                
                # Calculate current
                pr_ratio = float(np.divide(power_base, resistance_base))
                if pr_ratio < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Cannot calculate current from negative power and resistance ratio.')
                    }, status=400)
                
                current_base = float(math.sqrt(pr_ratio))
                
                # Check for invalid results
                if not np.isfinite(current_base) or current_base < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.CURRENT_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid current unit.')
                    }, status=400)
                
                current = float(np.divide(current_base, self.CURRENT_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_current_pr_steps(power, power_unit, resistance, resistance_unit, current, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_current_chart_data(power_base, None, current_base)
                
                return JsonResponse({
                    'success': True,
                    'result': current,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'I = √(P / R)',
                    'steps': steps,
                    'chart_data': chart_data,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid current calculation method.')
                }, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input values: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_resistance(self, data):
        """Calculate resistance from voltage, current, or power"""
        try:
            method = data.get('method', 'vi')
            result_unit = data.get('result_unit', 'ohm')
            
            if method == 'vi':
                # R = V / I
                voltage = float(data.get('voltage', 0))
                voltage_unit = data.get('voltage_unit', 'V')
                current = float(data.get('current', 0))
                current_unit = data.get('current_unit', 'A')
                
                # Validate inputs
                if not isinstance(voltage, (int, float)) or not isinstance(current, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
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
                
                if voltage > 1e6 or current > 1e6:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                voltage_base = float(voltage * self.VOLTAGE_CONVERSIONS.get(voltage_unit, 1.0))
                current_base = float(current * self.CURRENT_CONVERSIONS.get(current_unit, 1.0))
                
                # Calculate resistance
                resistance_base = float(np.divide(voltage_base, current_base))
                
                # Check for invalid results
                if not np.isfinite(resistance_base) or resistance_base <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.RESISTANCE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid resistance unit.')
                    }, status=400)
                
                resistance = float(np.divide(resistance_base, self.RESISTANCE_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_resistance_vi_steps(voltage, voltage_unit, current, current_unit, resistance, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_resistance_chart_data(voltage_base, current_base, resistance_base)
                
                return JsonResponse({
                    'success': True,
                    'result': resistance,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'R = V / I',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'vp':
                # R = V² / P
                voltage = float(data.get('voltage', 0))
                voltage_unit = data.get('voltage_unit', 'V')
                power = float(data.get('power', 0))
                power_unit = data.get('power_unit', 'W')
                
                # Validate inputs
                if not isinstance(voltage, (int, float)) or not isinstance(power, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if voltage < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Voltage must be non-negative.')
                    }, status=400)
                
                if power <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Power must be greater than zero.')
                    }, status=400)
                
                if voltage > 1e6 or power > 1e12:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                voltage_base = float(voltage * self.VOLTAGE_CONVERSIONS.get(voltage_unit, 1.0))
                power_base = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
                
                # Calculate resistance
                voltage_squared = float(np.multiply(voltage_base, voltage_base))
                resistance_base = float(np.divide(voltage_squared, power_base))
                
                # Check for invalid results
                if not np.isfinite(resistance_base) or resistance_base <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.RESISTANCE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid resistance unit.')
                    }, status=400)
                
                resistance = float(np.divide(resistance_base, self.RESISTANCE_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_resistance_vp_steps(voltage, voltage_unit, power, power_unit, resistance, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_resistance_chart_data(voltage_base, None, resistance_base)
                
                return JsonResponse({
                    'success': True,
                    'result': resistance,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'R = V² / P',
                    'steps': steps,
                    'chart_data': chart_data,
                })
                
            elif method == 'pi':
                # R = P / I²
                power = float(data.get('power', 0))
                power_unit = data.get('power_unit', 'W')
                current = float(data.get('current', 0))
                current_unit = data.get('current_unit', 'A')
                
                # Validate inputs
                if not isinstance(power, (int, float)) or not isinstance(current, (int, float)):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                if power < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Power must be non-negative.')
                    }, status=400)
                
                if current <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Current must be greater than zero.')
                    }, status=400)
                
                if power > 1e12 or current > 1e6:
                    return JsonResponse({
                        'success': False,
                        'error': _('Values are too large. Please use smaller values.')
                    }, status=400)
                
                # Convert to base units
                power_base = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
                current_base = float(current * self.CURRENT_CONVERSIONS.get(current_unit, 1.0))
                
                # Calculate resistance
                current_squared = float(np.multiply(current_base, current_base))
                resistance_base = float(np.divide(power_base, current_squared))
                
                # Check for invalid results
                if not np.isfinite(resistance_base) or resistance_base <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                # Convert to result unit
                if result_unit not in self.RESISTANCE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid resistance unit.')
                    }, status=400)
                
                resistance = float(np.divide(resistance_base, self.RESISTANCE_CONVERSIONS[result_unit]))
                
                # Prepare steps
                steps = self._prepare_resistance_pi_steps(power, power_unit, current, current_unit, resistance, result_unit)
                
                # Prepare chart data
                chart_data = self._prepare_resistance_chart_data(None, current_base, resistance_base)
                
                return JsonResponse({
                    'success': True,
                    'result': resistance,
                    'result_unit': self._format_unit(result_unit),
                    'formula': 'R = P / I²',
                    'steps': steps,
                    'chart_data': chart_data,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid resistance calculation method.')
                }, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input values: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_energy(self, data):
        """Calculate energy from power and time"""
        try:
            power = float(data.get('power', 0))
            power_unit = data.get('power_unit', 'W')
            time_value = float(data.get('time', 0))
            time_unit = data.get('time_unit', 'hours')
            result_unit = data.get('result_unit', 'kWh')
            
            # Validate inputs
            if not isinstance(power, (int, float)) or not isinstance(time_value, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            if power < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Power must be non-negative.')
                }, status=400)
            
            if time_value <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Time must be greater than zero.')
                }, status=400)
            
            if power > 1e12 or time_value > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Values are too large. Please use smaller values.')
                }, status=400)
            
            # Convert time to hours
            time_conversions = {
                'seconds': 1.0 / 3600.0,
                'minutes': 1.0 / 60.0,
                'hours': 1.0,
                'days': 24.0,
            }
            
            if time_unit not in time_conversions:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid time unit.')
                }, status=400)
            
            time_hours = float(time_value * time_conversions[time_unit])
            
            # Convert power to Watts
            power_watts = float(power * self.POWER_CONVERSIONS.get(power_unit, 1.0))
            
            # Calculate energy in Wh
            energy_wh = float(np.multiply(power_watts, time_hours))
            
            # Convert to result unit
            if result_unit not in self.ENERGY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid energy unit.')
                }, status=400)
            
            energy = float(np.divide(energy_wh / 1000.0, self.ENERGY_CONVERSIONS[result_unit]))
            
            # Check for invalid results
            if not np.isfinite(energy) or energy < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_energy_steps(power, power_unit, time_value, time_unit, energy, result_unit)
            
            # Prepare chart data
            chart_data = self._prepare_energy_chart_data(power_watts, time_hours, energy_wh)
            
            return JsonResponse({
                'success': True,
                'result': energy,
                'result_unit': self._format_unit(result_unit),
                'formula': 'E = P × t',
                'steps': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input values: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_cost(self, data):
        """Calculate electricity cost from energy and rate"""
        try:
            energy = float(data.get('energy', 0))
            energy_unit = data.get('energy_unit', 'kWh')
            rate = float(data.get('rate', 0))
            rate_unit = data.get('rate_unit', 'per_kWh')
            
            # Validate inputs
            if not isinstance(energy, (int, float)) or not isinstance(rate, (int, float)):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            if energy < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Energy must be non-negative.')
                }, status=400)
            
            if rate < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Rate must be non-negative.')
                }, status=400)
            
            if energy > 1e12 or rate > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Values are too large. Please use smaller values.')
                }, status=400)
            
            # Convert energy to kWh
            if energy_unit not in self.ENERGY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid energy unit.')
                }, status=400)
            
            energy_kwh = float(energy * self.ENERGY_CONVERSIONS[energy_unit])
            
            # Calculate cost
            cost = float(np.multiply(energy_kwh, rate))
            
            # Check for invalid results
            if not np.isfinite(cost) or cost < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_cost_steps(energy, energy_unit, rate, rate_unit, cost)
            
            # Prepare chart data
            chart_data = self._prepare_cost_chart_data(energy_kwh, rate, cost)
            
            return JsonResponse({
                'success': True,
                'result': cost,
                'result_unit': _('currency units'),
                'formula': 'Cost = Energy × Rate',
                'steps': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input values: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_power_vi_steps(self, voltage, voltage_unit, current, current_unit, power, result_unit):
        """Prepare step-by-step solution for power calculation from V and I"""
        try:
            V, I = symbols('V I')
            formula = Eq(symbols('P'), V * I)
            formula_latex = latex(formula)
        except:
            formula_latex = 'P = V × I'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Voltage (V) = {value} {unit}').format(value=voltage, unit=self._format_unit(voltage_unit)),
            _('  • Current (I) = {value} {unit}').format(value=current, unit=self._format_unit(current_unit)),
            _('Calculation:'),
            _('  P = {v} {vu} × {c} {cu}').format(v=voltage, vu=self._format_unit(voltage_unit), c=current, cu=self._format_unit(current_unit)),
            _('  P = {result} {unit}').format(result=power, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_power_vr_steps(self, voltage, voltage_unit, resistance, resistance_unit, power, result_unit):
        """Prepare step-by-step solution for power calculation from V and R"""
        try:
            V, R = symbols('V R')
            formula = Eq(symbols('P'), V**2 / R)
            formula_latex = latex(formula)
        except:
            formula_latex = 'P = V² / R'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Voltage (V) = {value} {unit}').format(value=voltage, unit=self._format_unit(voltage_unit)),
            _('  • Resistance (R) = {value} {unit}').format(value=resistance, unit=self._format_unit(resistance_unit)),
            _('Calculation:'),
            _('  V² = ({v} {vu})² = {v2} {vu2}').format(v=voltage, vu=self._format_unit(voltage_unit), v2=voltage**2, vu2=self._format_unit(voltage_unit) + '²'),
            _('  P = {v2} / {r} {ru}').format(v2=voltage**2, r=resistance, ru=self._format_unit(resistance_unit)),
            _('  P = {result} {unit}').format(result=power, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_power_ir_steps(self, current, current_unit, resistance, resistance_unit, power, result_unit):
        """Prepare step-by-step solution for power calculation from I and R"""
        try:
            I, R = symbols('I R')
            formula = Eq(symbols('P'), I**2 * R)
            formula_latex = latex(formula)
        except:
            formula_latex = 'P = I² × R'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Current (I) = {value} {unit}').format(value=current, unit=self._format_unit(current_unit)),
            _('  • Resistance (R) = {value} {unit}').format(value=resistance, unit=self._format_unit(resistance_unit)),
            _('Calculation:'),
            _('  I² = ({c} {cu})² = {c2} {cu2}').format(c=current, cu=self._format_unit(current_unit), c2=current**2, cu2=self._format_unit(current_unit) + '²'),
            _('  P = {c2} × {r} {ru}').format(c2=current**2, r=resistance, ru=self._format_unit(resistance_unit)),
            _('  P = {result} {unit}').format(result=power, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_voltage_pi_steps(self, power, power_unit, current, current_unit, voltage, result_unit):
        """Prepare step-by-step solution for voltage calculation from P and I"""
        try:
            P, I = symbols('P I')
            formula = Eq(symbols('V'), P / I)
            formula_latex = latex(formula)
        except:
            formula_latex = 'V = P / I'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('  • Current (I) = {value} {unit}').format(value=current, unit=self._format_unit(current_unit)),
            _('Calculation:'),
            _('  V = {p} {pu} / {c} {cu}').format(p=power, pu=self._format_unit(power_unit), c=current, cu=self._format_unit(current_unit)),
            _('  V = {result} {unit}').format(result=voltage, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_voltage_ir_steps(self, current, current_unit, resistance, resistance_unit, voltage, result_unit):
        """Prepare step-by-step solution for voltage calculation from I and R"""
        try:
            I, R = symbols('I R')
            formula = Eq(symbols('V'), I * R)
            formula_latex = latex(formula)
        except:
            formula_latex = 'V = I × R'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Current (I) = {value} {unit}').format(value=current, unit=self._format_unit(current_unit)),
            _('  • Resistance (R) = {value} {unit}').format(value=resistance, unit=self._format_unit(resistance_unit)),
            _('Calculation:'),
            _('  V = {c} {cu} × {r} {ru}').format(c=current, cu=self._format_unit(current_unit), r=resistance, ru=self._format_unit(resistance_unit)),
            _('  V = {result} {unit}').format(result=voltage, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_voltage_pr_steps(self, power, power_unit, resistance, resistance_unit, voltage, result_unit):
        """Prepare step-by-step solution for voltage calculation from P and R"""
        try:
            P, R = symbols('P R')
            formula = Eq(symbols('V'), simplify(symbols('sqrt')(P * R)))
            formula_latex = 'V = √(P × R)'
        except:
            formula_latex = 'V = √(P × R)'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('  • Resistance (R) = {value} {unit}').format(value=resistance, unit=self._format_unit(resistance_unit)),
            _('Calculation:'),
            _('  P × R = {p} {pu} × {r} {ru} = {pr}').format(p=power, pu=self._format_unit(power_unit), r=resistance, ru=self._format_unit(resistance_unit), pr=power*resistance),
            _('  V = √({pr})').format(pr=power*resistance),
            _('  V = {result} {unit}').format(result=voltage, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_current_pv_steps(self, power, power_unit, voltage, voltage_unit, current, result_unit):
        """Prepare step-by-step solution for current calculation from P and V"""
        try:
            P, V = symbols('P V')
            formula = Eq(symbols('I'), P / V)
            formula_latex = latex(formula)
        except:
            formula_latex = 'I = P / V'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('  • Voltage (V) = {value} {unit}').format(value=voltage, unit=self._format_unit(voltage_unit)),
            _('Calculation:'),
            _('  I = {p} {pu} / {v} {vu}').format(p=power, pu=self._format_unit(power_unit), v=voltage, vu=self._format_unit(voltage_unit)),
            _('  I = {result} {unit}').format(result=current, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_current_vr_steps(self, voltage, voltage_unit, resistance, resistance_unit, current, result_unit):
        """Prepare step-by-step solution for current calculation from V and R"""
        try:
            V, R = symbols('V R')
            formula = Eq(symbols('I'), V / R)
            formula_latex = latex(formula)
        except:
            formula_latex = 'I = V / R'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Voltage (V) = {value} {unit}').format(value=voltage, unit=self._format_unit(voltage_unit)),
            _('  • Resistance (R) = {value} {unit}').format(value=resistance, unit=self._format_unit(resistance_unit)),
            _('Calculation:'),
            _('  I = {v} {vu} / {r} {ru}').format(v=voltage, vu=self._format_unit(voltage_unit), r=resistance, ru=self._format_unit(resistance_unit)),
            _('  I = {result} {unit}').format(result=current, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_current_pr_steps(self, power, power_unit, resistance, resistance_unit, current, result_unit):
        """Prepare step-by-step solution for current calculation from P and R"""
        try:
            P, R = symbols('P R')
            formula = Eq(symbols('I'), simplify(symbols('sqrt')(P / R)))
            formula_latex = 'I = √(P / R)'
        except:
            formula_latex = 'I = √(P / R)'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('  • Resistance (R) = {value} {unit}').format(value=resistance, unit=self._format_unit(resistance_unit)),
            _('Calculation:'),
            _('  P / R = {p} {pu} / {r} {ru} = {pr}').format(p=power, pu=self._format_unit(power_unit), r=resistance, ru=self._format_unit(resistance_unit), pr=power/resistance),
            _('  I = √({pr})').format(pr=power/resistance),
            _('  I = {result} {unit}').format(result=current, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_resistance_vi_steps(self, voltage, voltage_unit, current, current_unit, resistance, result_unit):
        """Prepare step-by-step solution for resistance calculation from V and I"""
        try:
            V, I = symbols('V I')
            formula = Eq(symbols('R'), V / I)
            formula_latex = latex(formula)
        except:
            formula_latex = 'R = V / I'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Voltage (V) = {value} {unit}').format(value=voltage, unit=self._format_unit(voltage_unit)),
            _('  • Current (I) = {value} {unit}').format(value=current, unit=self._format_unit(current_unit)),
            _('Calculation:'),
            _('  R = {v} {vu} / {c} {cu}').format(v=voltage, vu=self._format_unit(voltage_unit), c=current, cu=self._format_unit(current_unit)),
            _('  R = {result} {unit}').format(result=resistance, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_resistance_vp_steps(self, voltage, voltage_unit, power, power_unit, resistance, result_unit):
        """Prepare step-by-step solution for resistance calculation from V and P"""
        try:
            V, P = symbols('V P')
            formula = Eq(symbols('R'), V**2 / P)
            formula_latex = latex(formula)
        except:
            formula_latex = 'R = V² / P'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Voltage (V) = {value} {unit}').format(value=voltage, unit=self._format_unit(voltage_unit)),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('Calculation:'),
            _('  V² = ({v} {vu})² = {v2} {vu2}').format(v=voltage, vu=self._format_unit(voltage_unit), v2=voltage**2, vu2=self._format_unit(voltage_unit) + '²'),
            _('  R = {v2} / {p} {pu}').format(v2=voltage**2, p=power, pu=self._format_unit(power_unit)),
            _('  R = {result} {unit}').format(result=resistance, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_resistance_pi_steps(self, power, power_unit, current, current_unit, resistance, result_unit):
        """Prepare step-by-step solution for resistance calculation from P and I"""
        try:
            P, I = symbols('P I')
            formula = Eq(symbols('R'), P / I**2)
            formula_latex = latex(formula)
        except:
            formula_latex = 'R = P / I²'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('  • Current (I) = {value} {unit}').format(value=current, unit=self._format_unit(current_unit)),
            _('Calculation:'),
            _('  I² = ({c} {cu})² = {c2} {cu2}').format(c=current, cu=self._format_unit(current_unit), c2=current**2, cu2=self._format_unit(current_unit) + '²'),
            _('  R = {p} {pu} / {c2}').format(p=power, pu=self._format_unit(power_unit), c2=current**2),
            _('  R = {result} {unit}').format(result=resistance, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_energy_steps(self, power, power_unit, time_value, time_unit, energy, result_unit):
        """Prepare step-by-step solution for energy calculation"""
        try:
            P, t = symbols('P t')
            formula = Eq(symbols('E'), P * t)
            formula_latex = latex(formula)
        except:
            formula_latex = 'E = P × t'
        
        steps = [
            _('Formula: {formula}').format(formula=formula_latex),
            _('Given values:'),
            _('  • Power (P) = {value} {unit}').format(value=power, unit=self._format_unit(power_unit)),
            _('  • Time (t) = {value} {unit}').format(value=time_value, unit=time_unit),
            _('Calculation:'),
            _('  E = {p} {pu} × {t} {tu}').format(p=power, pu=self._format_unit(power_unit), t=time_value, tu=time_unit),
            _('  E = {result} {unit}').format(result=energy, unit=self._format_unit(result_unit)),
        ]
        return steps
    
    def _prepare_cost_steps(self, energy, energy_unit, rate, rate_unit, cost):
        """Prepare step-by-step solution for cost calculation"""
        steps = [
            _('Formula: Cost = Energy × Rate'),
            _('Given values:'),
            _('  • Energy = {value} {unit}').format(value=energy, unit=self._format_unit(energy_unit)),
            _('  • Rate = {value} per kWh').format(value=rate),
            _('Calculation:'),
            _('  Cost = {e} {eu} × {r}').format(e=energy, eu=self._format_unit(energy_unit), r=rate),
            _('  Cost = {result} currency units').format(result=cost),
        ]
        return steps
    
    # Chart data preparation methods
    def _prepare_power_chart_data(self, voltage, current, power):
        """Prepare chart data for power visualization"""
        try:
            if voltage is not None and current is not None:
                # Bar chart showing V, I, and P
                chart_config = {
                    'type': 'bar',
                    'data': {
                        'labels': [_('Voltage (V)'), _('Current (A)'), _('Power (W)')],
                        'datasets': [{
                            'label': _('Electrical Parameters'),
                            'data': [voltage, current, power],
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
                                'text': _('Power Calculation Breakdown')
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
                return {'power_chart': chart_config}
            else:
                # Simple bar chart for power
                chart_config = {
                    'type': 'bar',
                    'data': {
                        'labels': [_('Power')],
                        'datasets': [{
                            'label': _('Power (W)'),
                            'data': [power],
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
                                'text': _('Power Result')
                            }
                        },
                        'scales': {
                            'y': {
                                'beginAtZero': True
                            }
                        }
                    }
                }
                return {'power_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_voltage_chart_data(self, power, current, voltage):
        """Prepare chart data for voltage visualization"""
        try:
            if power is not None and current is not None:
                chart_config = {
                    'type': 'bar',
                    'data': {
                        'labels': [_('Power (W)'), _('Current (A)'), _('Voltage (V)')],
                        'datasets': [{
                            'label': _('Electrical Parameters'),
                            'data': [power, current, voltage],
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
                                'text': _('Voltage Calculation Breakdown')
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
            else:
                chart_config = {
                    'type': 'bar',
                    'data': {
                        'labels': [_('Voltage')],
                        'datasets': [{
                            'label': _('Voltage (V)'),
                            'data': [voltage],
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
                                'text': _('Voltage Result')
                            }
                        },
                        'scales': {
                            'y': {
                                'beginAtZero': True
                            }
                        }
                    }
                }
                return {'voltage_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_current_chart_data(self, power, voltage, current):
        """Prepare chart data for current visualization"""
        try:
            if power is not None and voltage is not None:
                labels = [_('Power'), _('Voltage'), _('Current')]
                values = [power, voltage, current]
                return {
                    'type': 'bar',
                    'labels': labels,
                    'data': values,
                }
            else:
                return {
                    'type': 'bar',
                    'labels': [_('Current')],
                    'data': [current],
                }
        except:
            return None
    
    def _prepare_resistance_chart_data(self, voltage, current, resistance):
        """Prepare chart data for resistance visualization"""
        try:
            if voltage is not None and current is not None:
                labels = [_('Voltage'), _('Current'), _('Resistance')]
                values = [voltage, current, resistance]
                return {
                    'type': 'bar',
                    'labels': labels,
                    'data': values,
                }
            else:
                return {
                    'type': 'bar',
                    'labels': [_('Resistance')],
                    'data': [resistance],
                }
        except:
            return None
    
    def _prepare_energy_chart_data(self, power, time, energy):
        """Prepare chart data for energy visualization"""
        try:
            return {
                'type': 'line',
                'labels': [_('Power'), _('Time'), _('Energy')],
                'data': [power, time, energy],
            }
        except:
            return None
    
    def _prepare_cost_chart_data(self, energy, rate, cost):
        """Prepare chart data for cost visualization"""
        try:
            return {
                'type': 'doughnut',
                'labels': [_('Energy'), _('Rate'), _('Cost')],
                'data': [energy, rate, cost],
            }
        except:
            return None
