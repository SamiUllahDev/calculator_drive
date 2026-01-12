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
class ResistorCalculator(View):
    """
    Professional Resistor Calculator with Comprehensive Features
    
    This calculator provides resistor calculations with:
    - Calculate resistance from color bands (4-band, 5-band, 6-band)
    - Calculate series resistance
    - Calculate parallel resistance
    - Calculate equivalent resistance (series + parallel combinations)
    - Convert resistance units
    - Calculate power dissipation
    
    Features:
    - Supports multiple calculation modes
    - Handles color code decoding
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/resistor_calculator.html'
    
    # Color code values
    COLOR_CODES = {
        'black': {'value': 0, 'multiplier': 1, 'tolerance': None, 'temp_coeff': 250},
        'brown': {'value': 1, 'multiplier': 10, 'tolerance': 1, 'temp_coeff': 100},
        'red': {'value': 2, 'multiplier': 100, 'tolerance': 2, 'temp_coeff': 50},
        'orange': {'value': 3, 'multiplier': 1000, 'tolerance': None, 'temp_coeff': 15},
        'yellow': {'value': 4, 'multiplier': 10000, 'tolerance': None, 'temp_coeff': 25},
        'green': {'value': 5, 'multiplier': 100000, 'tolerance': 0.5, 'temp_coeff': 20},
        'blue': {'value': 6, 'multiplier': 1000000, 'tolerance': 0.25, 'temp_coeff': 10},
        'violet': {'value': 7, 'multiplier': 10000000, 'tolerance': 0.1, 'temp_coeff': 5},
        'gray': {'value': 8, 'multiplier': 100000000, 'tolerance': 0.05, 'temp_coeff': 1},
        'white': {'value': 9, 'multiplier': 1000000000, 'tolerance': None, 'temp_coeff': None},
        'gold': {'value': None, 'multiplier': 0.1, 'tolerance': 5, 'temp_coeff': None},
        'silver': {'value': None, 'multiplier': 0.01, 'tolerance': 10, 'temp_coeff': None},
    }
    
    # Resistance conversion factors (to ohms)
    RESISTANCE_CONVERSIONS = {
        'ohms': 1.0,
        'kiloohms': 1000.0,  # 1 kΩ = 1000 Ω
        'megaohms': 1000000.0,  # 1 MΩ = 1000000 Ω
        'milliohms': 0.001,  # 1 mΩ = 0.001 Ω
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'ohms': 'Ω',
            'kiloohms': 'kΩ',
            'megaohms': 'MΩ',
            'milliohms': 'mΩ',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Resistor Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'color_code')
            
            if calc_type == 'color_code':
                return self._calculate_from_color_code(data)
            elif calc_type == 'series':
                return self._calculate_series(data)
            elif calc_type == 'parallel':
                return self._calculate_parallel(data)
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
    
    def _calculate_from_color_code(self, data):
        """Calculate resistance from color bands"""
        try:
            band_type = data.get('band_type', '4_band')
            
            if band_type == '4_band':
                band1 = data.get('band1')
                band2 = data.get('band2')
                multiplier = data.get('multiplier')
                tolerance = data.get('tolerance')
                
                if not all([band1, band2, multiplier, tolerance]):
                    return JsonResponse({
                        'success': False,
                        'error': _('All color bands are required.')
                    }, status=400)
                
                # Validate colors
                for color in [band1, band2, multiplier, tolerance]:
                    if color not in self.COLOR_CODES:
                        return JsonResponse({
                            'success': False,
                            'error': _('Invalid color: {color}').format(color=color)
                        }, status=400)
                
                # Get values
                digit1 = self.COLOR_CODES[band1]['value']
                digit2 = self.COLOR_CODES[band2]['value']
                mult = self.COLOR_CODES[multiplier]['multiplier']
                tol = self.COLOR_CODES[tolerance]['tolerance']
                
                if digit1 is None or digit2 is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid color combination for first two bands.')
                    }, status=400)
                
                if mult is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid multiplier color.')
                    }, status=400)
                
                if tol is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid tolerance color.')
                    }, status=400)
                
                # Calculate resistance
                resistance = (digit1 * 10 + digit2) * mult
                
                steps = self._prepare_4band_steps(band1, band2, multiplier, tolerance, digit1, digit2, mult, tol, resistance)
                
            elif band_type == '5_band':
                band1 = data.get('band1')
                band2 = data.get('band2')
                band3 = data.get('band3')
                multiplier = data.get('multiplier')
                tolerance = data.get('tolerance')
                
                if not all([band1, band2, band3, multiplier, tolerance]):
                    return JsonResponse({
                        'success': False,
                        'error': _('All color bands are required.')
                    }, status=400)
                
                # Validate colors
                for color in [band1, band2, band3, multiplier, tolerance]:
                    if color not in self.COLOR_CODES:
                        return JsonResponse({
                            'success': False,
                            'error': _('Invalid color: {color}').format(color=color)
                        }, status=400)
                
                # Get values
                digit1 = self.COLOR_CODES[band1]['value']
                digit2 = self.COLOR_CODES[band2]['value']
                digit3 = self.COLOR_CODES[band3]['value']
                mult = self.COLOR_CODES[multiplier]['multiplier']
                tol = self.COLOR_CODES[tolerance]['tolerance']
                
                if any(d is None for d in [digit1, digit2, digit3]):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid color combination for first three bands.')
                    }, status=400)
                
                if mult is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid multiplier color.')
                    }, status=400)
                
                if tol is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid tolerance color.')
                    }, status=400)
                
                # Calculate resistance
                resistance = (digit1 * 100 + digit2 * 10 + digit3) * mult
                
                steps = self._prepare_5band_steps(band1, band2, band3, multiplier, tolerance, digit1, digit2, digit3, mult, tol, resistance)
                
            else:  # 6_band
                band1 = data.get('band1')
                band2 = data.get('band2')
                band3 = data.get('band3')
                multiplier = data.get('multiplier')
                tolerance = data.get('tolerance')
                temp_coeff = data.get('temp_coeff')
                
                if not all([band1, band2, band3, multiplier, tolerance, temp_coeff]):
                    return JsonResponse({
                        'success': False,
                        'error': _('All color bands are required.')
                    }, status=400)
                
                # Validate colors
                for color in [band1, band2, band3, multiplier, tolerance, temp_coeff]:
                    if color not in self.COLOR_CODES:
                        return JsonResponse({
                            'success': False,
                            'error': _('Invalid color: {color}').format(color=color)
                        }, status=400)
                
                # Get values
                digit1 = self.COLOR_CODES[band1]['value']
                digit2 = self.COLOR_CODES[band2]['value']
                digit3 = self.COLOR_CODES[band3]['value']
                mult = self.COLOR_CODES[multiplier]['multiplier']
                tol = self.COLOR_CODES[tolerance]['tolerance']
                temp = self.COLOR_CODES[temp_coeff]['temp_coeff']
                
                if any(d is None for d in [digit1, digit2, digit3]):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid color combination for first three bands.')
                    }, status=400)
                
                if mult is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid multiplier color.')
                    }, status=400)
                
                if tol is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid tolerance color.')
                    }, status=400)
                
                if temp is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid temperature coefficient color.')
                    }, status=400)
                
                # Calculate resistance
                resistance = (digit1 * 100 + digit2 * 10 + digit3) * mult
                
                steps = self._prepare_6band_steps(band1, band2, band3, multiplier, tolerance, temp_coeff, digit1, digit2, digit3, mult, tol, temp, resistance)
            
            # Calculate min/max resistance from tolerance
            tolerance_value = tol if isinstance(tol, (int, float)) else 0
            min_resistance = resistance * (1 - tolerance_value / 100)
            max_resistance = resistance * (1 + tolerance_value / 100)
            
            # Format resistance value
            if resistance >= 1000000:
                formatted_value = f"{resistance / 1000000:.2f} MΩ"
            elif resistance >= 1000:
                formatted_value = f"{resistance / 1000:.2f} kΩ"
            else:
                formatted_value = f"{resistance:.2f} Ω"
            
            return JsonResponse({
                'success': True,
                'calc_type': 'color_code',
                'band_type': band_type,
                'resistance': round(resistance, 2),
                'tolerance': tolerance_value,
                'min_resistance': round(min_resistance, 2),
                'max_resistance': round(max_resistance, 2),
                'formatted_value': formatted_value,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating resistance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_series(self, data):
        """Calculate total resistance in series"""
        try:
            resistors = data.get('resistors', [])
            
            if not resistors or len(resistors) < 2:
                return JsonResponse({
                    'success': False,
                    'error': _('At least two resistors are required.')
                }, status=400)
            
            try:
                resistor_values = [float(r.get('value', 0)) for r in resistors]
                resistor_units = [r.get('unit', 'ohms') for r in resistors]
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid resistor values.')
                }, status=400)
            
            # Validate units and values
            for i, (value, unit) in enumerate(zip(resistor_values, resistor_units)):
                if unit not in self.RESISTANCE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid unit for resistor {index}.').format(index=i+1)
                    }, status=400)
                
                if value <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Resistor {index} value must be greater than zero.').format(index=i+1)
                    }, status=400)
            
            # Convert to ohms
            resistors_ohms = [value * self.RESISTANCE_CONVERSIONS[unit] for value, unit in zip(resistor_values, resistor_units)]
            
            # Calculate total: R_total = R1 + R2 + R3 + ...
            total_resistance = float(np.sum(resistors_ohms))
            
            result_unit = data.get('result_unit', 'ohms')
            if result_unit not in self.RESISTANCE_CONVERSIONS:
                result_unit = 'ohms'
            
            result = float(np.divide(total_resistance, self.RESISTANCE_CONVERSIONS[result_unit]))
            
            steps = self._prepare_series_steps(resistor_values, resistor_units, resistors_ohms, total_resistance, result, result_unit)
            
            chart_data = self._prepare_series_chart_data(resistors_ohms, total_resistance)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'series',
                'resistors': resistors,
                'total_resistance': round(result, 6),
                'result_unit': result_unit,
                'total_resistance_ohms': round(total_resistance, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating series resistance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_parallel(self, data):
        """Calculate total resistance in parallel"""
        try:
            resistors = data.get('resistors', [])
            
            if not resistors or len(resistors) < 2:
                return JsonResponse({
                    'success': False,
                    'error': _('At least two resistors are required.')
                }, status=400)
            
            try:
                resistor_values = [float(r.get('value', 0)) for r in resistors]
                resistor_units = [r.get('unit', 'ohms') for r in resistors]
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid resistor values.')
                }, status=400)
            
            # Validate units and values
            for i, (value, unit) in enumerate(zip(resistor_values, resistor_units)):
                if unit not in self.RESISTANCE_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid unit for resistor {index}.').format(index=i+1)
                    }, status=400)
                
                if value <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Resistor {index} value must be greater than zero.').format(index=i+1)
                    }, status=400)
            
            # Convert to ohms
            resistors_ohms = [value * self.RESISTANCE_CONVERSIONS[unit] for value, unit in zip(resistor_values, resistor_units)]
            
            # Calculate total: 1/R_total = 1/R1 + 1/R2 + 1/R3 + ...
            reciprocals = [1.0 / r for r in resistors_ohms]
            total_reciprocal = float(np.sum(reciprocals))
            total_resistance = float(np.divide(1.0, total_reciprocal))
            
            result_unit = data.get('result_unit', 'ohms')
            if result_unit not in self.RESISTANCE_CONVERSIONS:
                result_unit = 'ohms'
            
            result = float(np.divide(total_resistance, self.RESISTANCE_CONVERSIONS[result_unit]))
            
            steps = self._prepare_parallel_steps(resistor_values, resistor_units, resistors_ohms, reciprocals, total_reciprocal, total_resistance, result, result_unit)
            
            chart_data = self._prepare_parallel_chart_data(resistors_ohms, total_resistance)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'parallel',
                'resistors': resistors,
                'total_resistance': round(result, 6),
                'result_unit': result_unit,
                'total_resistance_ohms': round(total_resistance, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating parallel resistance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_power(self, data):
        """Calculate power dissipation in resistor"""
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
            
            resistance_unit = data.get('resistance_unit', 'ohms')
            
            # Validate
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
            
            if resistance_unit not in self.RESISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid resistance unit.')
                }, status=400)
            
            # Convert to ohms
            resistance_ohms = float(resistance * self.RESISTANCE_CONVERSIONS[resistance_unit])
            
            # Calculate power: P = V² / R
            power_watts = float(np.divide(np.multiply(voltage, voltage), resistance_ohms))
            
            # Also calculate current: I = V / R
            current_amps = float(np.divide(voltage, resistance_ohms))
            
            steps = self._prepare_power_steps(voltage, resistance, resistance_unit, resistance_ohms, power_watts, current_amps)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'power',
                'voltage': voltage,
                'resistance': resistance,
                'resistance_unit': resistance_unit,
                'power': round(power_watts, 6),
                'current': round(current_amps, 6),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating power: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_4band_steps(self, band1, band2, multiplier, tolerance, digit1, digit2, mult, tol, resistance):
        """Prepare step-by-step solution for 4-band resistor"""
        steps = []
        steps.append(_('Step 1: Identify the color bands'))
        steps.append(_('Band 1 (1st digit): {color} = {value}').format(color=band1, value=digit1))
        steps.append(_('Band 2 (2nd digit): {color} = {value}').format(color=band2, value=digit2))
        steps.append(_('Band 3 (multiplier): {color} = ×{mult}').format(color=multiplier, mult=mult))
        steps.append(_('Band 4 (tolerance): {color} = ±{tol}%').format(color=tolerance, tol=tol))
        steps.append('')
        steps.append(_('Step 2: Calculate resistance'))
        steps.append(_('Resistance = (Digit1 × 10 + Digit2) × Multiplier'))
        steps.append(_('Resistance = ({d1} × 10 + {d2}) × {mult}').format(d1=digit1, d2=digit2, mult=mult))
        steps.append(_('Resistance = {resistance} Ω').format(resistance=resistance))
        return steps
    
    def _prepare_5band_steps(self, band1, band2, band3, multiplier, tolerance, digit1, digit2, digit3, mult, tol, resistance):
        """Prepare step-by-step solution for 5-band resistor"""
        steps = []
        steps.append(_('Step 1: Identify the color bands'))
        steps.append(_('Band 1 (1st digit): {color} = {value}').format(color=band1, value=digit1))
        steps.append(_('Band 2 (2nd digit): {color} = {value}').format(color=band2, value=digit2))
        steps.append(_('Band 3 (3rd digit): {color} = {value}').format(color=band3, value=digit3))
        steps.append(_('Band 4 (multiplier): {color} = ×{mult}').format(color=multiplier, mult=mult))
        steps.append(_('Band 5 (tolerance): {color} = ±{tol}%').format(color=tolerance, tol=tol))
        steps.append('')
        steps.append(_('Step 2: Calculate resistance'))
        steps.append(_('Resistance = (Digit1 × 100 + Digit2 × 10 + Digit3) × Multiplier'))
        steps.append(_('Resistance = ({d1} × 100 + {d2} × 10 + {d3}) × {mult}').format(d1=digit1, d2=digit2, d3=digit3, mult=mult))
        steps.append(_('Resistance = {resistance} Ω').format(resistance=resistance))
        return steps
    
    def _prepare_6band_steps(self, band1, band2, band3, multiplier, tolerance, temp_coeff, digit1, digit2, digit3, mult, tol, temp, resistance):
        """Prepare step-by-step solution for 6-band resistor"""
        steps = []
        steps.append(_('Step 1: Identify the color bands'))
        steps.append(_('Band 1 (1st digit): {color} = {value}').format(color=band1, value=digit1))
        steps.append(_('Band 2 (2nd digit): {color} = {value}').format(color=band2, value=digit2))
        steps.append(_('Band 3 (3rd digit): {color} = {value}').format(color=band3, value=digit3))
        steps.append(_('Band 4 (multiplier): {color} = ×{mult}').format(color=multiplier, mult=mult))
        steps.append(_('Band 5 (tolerance): {color} = ±{tol}%').format(color=tolerance, tol=tol))
        steps.append(_('Band 6 (temp coeff): {color} = {temp} ppm/°C').format(color=temp_coeff, temp=temp))
        steps.append('')
        steps.append(_('Step 2: Calculate resistance'))
        steps.append(_('Resistance = (Digit1 × 100 + Digit2 × 10 + Digit3) × Multiplier'))
        steps.append(_('Resistance = ({d1} × 100 + {d2} × 10 + {d3}) × {mult}').format(d1=digit1, d2=digit2, d3=digit3, mult=mult))
        steps.append(_('Resistance = {resistance} Ω').format(resistance=resistance))
        return steps
    
    def _prepare_series_steps(self, resistor_values, resistor_units, resistors_ohms, total_resistance, result, result_unit):
        """Prepare step-by-step solution for series resistance"""
        steps = []
        steps.append(_('Step 1: Identify the resistor values'))
        for i, (value, unit) in enumerate(zip(resistor_values, resistor_units)):
            steps.append(_('R{index}: {value} {unit}').format(index=i+1, value=value, unit=self._format_unit(unit)))
        steps.append('')
        steps.append(_('Step 2: Convert all to ohms'))
        for i, r_ohms in enumerate(resistors_ohms):
            steps.append(_('R{index}: {value} Ω').format(index=i+1, value=r_ohms))
        steps.append('')
        steps.append(_('Step 3: Calculate total resistance'))
        steps.append(_('Formula: R_total = R1 + R2 + R3 + ...'))
        sum_parts = ' + '.join([_('{value}').format(value=r) for r in resistors_ohms])
        steps.append(_('R_total = {sum}').format(sum=sum_parts))
        steps.append(_('R_total = {total} Ω').format(total=total_resistance))
        if result_unit != 'ohms':
            steps.append('')
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('R_total = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        return steps
    
    def _prepare_parallel_steps(self, resistor_values, resistor_units, resistors_ohms, reciprocals, total_reciprocal, total_resistance, result, result_unit):
        """Prepare step-by-step solution for parallel resistance"""
        steps = []
        steps.append(_('Step 1: Identify the resistor values'))
        for i, (value, unit) in enumerate(zip(resistor_values, resistor_units)):
            steps.append(_('R{index}: {value} {unit}').format(index=i+1, value=value, unit=self._format_unit(unit)))
        steps.append('')
        steps.append(_('Step 2: Convert all to ohms'))
        for i, r_ohms in enumerate(resistors_ohms):
            steps.append(_('R{index}: {value} Ω').format(index=i+1, value=r_ohms))
        steps.append('')
        steps.append(_('Step 3: Calculate reciprocals'))
        for i, rec in enumerate(reciprocals):
            steps.append(_('1/R{index} = 1 / {r} = {rec}').format(index=i+1, r=resistors_ohms[i], rec=round(rec, 6)))
        steps.append('')
        steps.append(_('Step 4: Calculate total resistance'))
        steps.append(_('Formula: 1/R_total = 1/R1 + 1/R2 + 1/R3 + ...'))
        sum_parts = ' + '.join([_('{value}').format(value=round(r, 6)) for r in reciprocals])
        steps.append(_('1/R_total = {sum}').format(sum=sum_parts))
        steps.append(_('1/R_total = {total}').format(total=round(total_reciprocal, 6)))
        steps.append(_('R_total = 1 / {total} = {resistance} Ω').format(total=round(total_reciprocal, 6), resistance=total_resistance))
        if result_unit != 'ohms':
            steps.append('')
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('R_total = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        return steps
    
    def _prepare_power_steps(self, voltage, resistance, resistance_unit, resistance_ohms, power_watts, current_amps):
        """Prepare step-by-step solution for power calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage: {voltage} V').format(voltage=voltage))
        steps.append(_('Resistance: {resistance} {unit}').format(resistance=resistance, unit=self._format_unit(resistance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert resistance to ohms'))
        steps.append(_('Resistance: {resistance} Ω').format(resistance=resistance_ohms))
        steps.append('')
        steps.append(_('Step 3: Calculate current'))
        steps.append(_('Formula: I = V / R'))
        steps.append(_('I = {voltage} V / {resistance} Ω').format(voltage=voltage, resistance=resistance_ohms))
        steps.append(_('I = {current} A').format(current=round(current_amps, 6)))
        steps.append('')
        steps.append(_('Step 4: Calculate power'))
        steps.append(_('Formula: P = V² / R'))
        steps.append(_('P = ({voltage} V)² / {resistance} Ω').format(voltage=voltage, resistance=resistance_ohms))
        steps.append(_('P = {power} W').format(power=round(power_watts, 6)))
        return steps
    
    # Chart data preparation methods
    def _prepare_series_chart_data(self, resistors_ohms, total_resistance):
        """Prepare chart data for series resistance"""
        try:
            labels = [f'R{i+1}' for i in range(len(resistors_ohms))] + [_('Total')]
            data = list(resistors_ohms) + [total_resistance]
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': _('Resistance (Ω)'),
                        'data': data,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in range(len(resistors_ohms))
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in range(len(resistors_ohms))
                        ] + ['#10b981'],
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
                            'text': _('Series Resistance Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Resistance (Ω)')
                            }
                        }
                    }
                }
            }
            return {'series_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_parallel_chart_data(self, resistors_ohms, total_resistance):
        """Prepare chart data for parallel resistance"""
        try:
            labels = [f'R{i+1}' for i in range(len(resistors_ohms))] + [_('Total')]
            data = list(resistors_ohms) + [total_resistance]
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': _('Resistance (Ω)'),
                        'data': data,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in range(len(resistors_ohms))
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in range(len(resistors_ohms))
                        ] + ['#10b981'],
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
                            'text': _('Parallel Resistance Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Resistance (Ω)')
                            }
                        }
                    }
                }
            }
            return {'parallel_chart': chart_config}
        except Exception as e:
            return None
