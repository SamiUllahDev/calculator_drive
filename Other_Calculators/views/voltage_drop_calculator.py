from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class VoltageDropCalculator(View):
    """
    Professional Voltage Drop Calculator with Comprehensive Features
    
    This calculator provides voltage drop calculations with:
    - Calculate voltage drop from current and resistance
    - Calculate wire size needed for acceptable voltage drop
    - Calculate maximum current for given voltage drop
    - Calculate maximum wire length for given voltage drop
    - Support for DC and AC (single-phase and three-phase)
    
    Features:
    - Supports multiple calculation modes
    - Handles various wire materials and sizes
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/voltage_drop_calculator.html'
    
    # Wire resistivity (Ohm-cmil/ft) at 75°C
    WIRE_RESISTIVITY = {
        'copper': 12.9,  # Ohm-cmil/ft
        'aluminum': 21.2,  # Ohm-cmil/ft
    }
    
    # Standard AWG wire sizes (circular mils)
    AWG_SIZES = {
        '14': 4107,
        '12': 6530,
        '10': 10380,
        '8': 16510,
        '6': 26240,
        '4': 41740,
        '3': 52620,
        '2': 66360,
        '1': 83690,
        '1/0': 105600,
        '2/0': 133100,
        '3/0': 167800,
        '4/0': 211600,
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Voltage Drop Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'voltage_drop')
            
            if calc_type == 'voltage_drop':
                return self._calculate_voltage_drop(data)
            elif calc_type == 'wire_size':
                return self._calculate_wire_size(data)
            elif calc_type == 'max_current':
                return self._calculate_max_current(data)
            elif calc_type == 'max_length':
                return self._calculate_max_length(data)
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
    
    def _calculate_voltage_drop(self, data):
        """Calculate voltage drop from current, resistance, and circuit type"""
        try:
            if 'current' not in data or data.get('current') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Current is required.')
                }, status=400)
            
            try:
                current = float(data.get('current', 0))  # Amperes
                voltage = float(data.get('voltage', 120))  # Volts
                length = float(data.get('length', 100))  # feet
                wire_size = data.get('wire_size', '12')  # AWG
                wire_material = data.get('wire_material', 'copper')
                circuit_type = data.get('circuit_type', 'dc')  # dc, single_phase, three_phase
                power_factor = float(data.get('power_factor', 1.0))  # For AC
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validation
            if current <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Current must be greater than zero.')
                }, status=400)
            
            if voltage <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage must be greater than zero.')
                }, status=400)
            
            if length <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Length must be greater than zero.')
                }, status=400)
            
            if wire_material not in self.WIRE_RESISTIVITY:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid wire material.')
                }, status=400)
            
            if wire_size not in self.AWG_SIZES:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid wire size.')
                }, status=400)
            
            # Calculate resistance
            resistivity = self.WIRE_RESISTIVITY[wire_material]
            circular_mils = self.AWG_SIZES[wire_size]
            resistance = (resistivity * length) / circular_mils  # Ohms
            
            # Calculate voltage drop based on circuit type
            if circuit_type == 'dc':
                voltage_drop = current * resistance * 2  # Round trip
            elif circuit_type == 'single_phase':
                voltage_drop = current * resistance * 2 * power_factor
            elif circuit_type == 'three_phase':
                voltage_drop = current * resistance * 1.732 * power_factor  # √3 for three-phase
            else:
                voltage_drop = current * resistance * 2
            
            # Calculate percentage drop
            voltage_drop_percent = (voltage_drop / voltage) * 100
            
            # Calculate voltage at load
            voltage_at_load = voltage - voltage_drop
            
            # Calculate power loss
            power_loss = current * voltage_drop  # Watts
            
            steps = self._prepare_voltage_drop_steps(current, voltage, length, wire_size, wire_material, circuit_type, power_factor, resistivity, circular_mils, resistance, voltage_drop, voltage_drop_percent, voltage_at_load, power_loss)
            chart_data = self._prepare_voltage_drop_chart_data(voltage, voltage_drop, voltage_at_load)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'voltage_drop',
                'current': current,
                'voltage': voltage,
                'length': length,
                'wire_size': wire_size,
                'wire_material': wire_material,
                'circuit_type': circuit_type,
                'resistance': round(resistance, 4),
                'voltage_drop': round(voltage_drop, 2),
                'voltage_drop_percent': round(voltage_drop_percent, 2),
                'voltage_at_load': round(voltage_at_load, 2),
                'power_loss': round(power_loss, 2),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating voltage drop: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_wire_size(self, data):
        """Calculate wire size needed for acceptable voltage drop"""
        try:
            if 'current' not in data or data.get('current') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Current is required.')
                }, status=400)
            
            if 'max_voltage_drop' not in data or data.get('max_voltage_drop') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Maximum voltage drop is required.')
                }, status=400)
            
            try:
                current = float(data.get('current', 0))
                voltage = float(data.get('voltage', 120))
                length = float(data.get('length', 100))
                max_voltage_drop = float(data.get('max_voltage_drop', 3))  # Volts or percentage
                max_voltage_drop_type = data.get('max_voltage_drop_type', 'volts')  # volts or percent
                wire_material = data.get('wire_material', 'copper')
                circuit_type = data.get('circuit_type', 'dc')
                power_factor = float(data.get('power_factor', 1.0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Convert percentage to volts if needed
            if max_voltage_drop_type == 'percent':
                max_voltage_drop_volts = (max_voltage_drop / 100) * voltage
            else:
                max_voltage_drop_volts = max_voltage_drop
            
            # Calculate required resistance
            if circuit_type == 'dc':
                max_resistance = max_voltage_drop_volts / (current * 2)
            elif circuit_type == 'single_phase':
                max_resistance = max_voltage_drop_volts / (current * 2 * power_factor)
            elif circuit_type == 'three_phase':
                max_resistance = max_voltage_drop_volts / (current * 1.732 * power_factor)
            else:
                max_resistance = max_voltage_drop_volts / (current * 2)
            
            # Calculate required circular mils
            resistivity = self.WIRE_RESISTIVITY[wire_material]
            required_circular_mils = (resistivity * length) / max_resistance
            
            # Find appropriate wire size
            recommended_size = None
            for size, cmils in sorted(self.AWG_SIZES.items(), key=lambda x: x[1], reverse=True):
                if cmils >= required_circular_mils:
                    recommended_size = size
                    break
            
            if not recommended_size:
                recommended_size = '4/0'  # Largest available
            
            steps = self._prepare_wire_size_steps(current, voltage, length, max_voltage_drop, max_voltage_drop_type, max_voltage_drop_volts, wire_material, circuit_type, power_factor, resistivity, max_resistance, required_circular_mils, recommended_size)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'wire_size',
                'current': current,
                'voltage': voltage,
                'length': length,
                'max_voltage_drop': max_voltage_drop,
                'max_voltage_drop_type': max_voltage_drop_type,
                'wire_material': wire_material,
                'circuit_type': circuit_type,
                'required_circular_mils': round(required_circular_mils, 0),
                'recommended_wire_size': recommended_size,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating wire size: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_max_current(self, data):
        """Calculate maximum current for given voltage drop"""
        try:
            if 'voltage_drop' not in data or data.get('voltage_drop') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage drop is required.')
                }, status=400)
            
            try:
                voltage_drop = float(data.get('voltage_drop', 0))
                voltage = float(data.get('voltage', 120))
                length = float(data.get('length', 100))
                wire_size = data.get('wire_size', '12')
                wire_material = data.get('wire_material', 'copper')
                circuit_type = data.get('circuit_type', 'dc')
                power_factor = float(data.get('power_factor', 1.0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Calculate resistance
            resistivity = self.WIRE_RESISTIVITY[wire_material]
            circular_mils = self.AWG_SIZES[wire_size]
            resistance = (resistivity * length) / circular_mils
            
            # Calculate maximum current
            if circuit_type == 'dc':
                max_current = voltage_drop / (resistance * 2)
            elif circuit_type == 'single_phase':
                max_current = voltage_drop / (resistance * 2 * power_factor)
            elif circuit_type == 'three_phase':
                max_current = voltage_drop / (resistance * 1.732 * power_factor)
            else:
                max_current = voltage_drop / (resistance * 2)
            
            voltage_drop_percent = (voltage_drop / voltage) * 100
            
            steps = self._prepare_max_current_steps(voltage_drop, voltage, length, wire_size, wire_material, circuit_type, power_factor, resistivity, circular_mils, resistance, max_current, voltage_drop_percent)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'max_current',
                'voltage_drop': voltage_drop,
                'voltage': voltage,
                'length': length,
                'wire_size': wire_size,
                'wire_material': wire_material,
                'circuit_type': circuit_type,
                'resistance': round(resistance, 4),
                'max_current': round(max_current, 2),
                'voltage_drop_percent': round(voltage_drop_percent, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating max current: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_max_length(self, data):
        """Calculate maximum wire length for given voltage drop"""
        try:
            if 'voltage_drop' not in data or data.get('voltage_drop') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Voltage drop is required.')
                }, status=400)
            
            try:
                voltage_drop = float(data.get('voltage_drop', 0))
                voltage = float(data.get('voltage', 120))
                current = float(data.get('current', 0))
                wire_size = data.get('wire_size', '12')
                wire_material = data.get('wire_material', 'copper')
                circuit_type = data.get('circuit_type', 'dc')
                power_factor = float(data.get('power_factor', 1.0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Calculate maximum length
            resistivity = self.WIRE_RESISTIVITY[wire_material]
            circular_mils = self.AWG_SIZES[wire_size]
            
            if circuit_type == 'dc':
                max_length = (voltage_drop * circular_mils) / (current * resistivity * 2)
            elif circuit_type == 'single_phase':
                max_length = (voltage_drop * circular_mils) / (current * resistivity * 2 * power_factor)
            elif circuit_type == 'three_phase':
                max_length = (voltage_drop * circular_mils) / (current * resistivity * 1.732 * power_factor)
            else:
                max_length = (voltage_drop * circular_mils) / (current * resistivity * 2)
            
            voltage_drop_percent = (voltage_drop / voltage) * 100
            
            steps = self._prepare_max_length_steps(voltage_drop, voltage, current, wire_size, wire_material, circuit_type, power_factor, resistivity, circular_mils, max_length, voltage_drop_percent)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'max_length',
                'voltage_drop': voltage_drop,
                'voltage': voltage,
                'current': current,
                'wire_size': wire_size,
                'wire_material': wire_material,
                'circuit_type': circuit_type,
                'max_length': round(max_length, 2),
                'voltage_drop_percent': round(voltage_drop_percent, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating max length: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_voltage_drop_steps(self, current, voltage, length, wire_size, wire_material, circuit_type, power_factor, resistivity, circular_mils, resistance, voltage_drop, voltage_drop_percent, voltage_at_load, power_loss):
        """Prepare step-by-step solution for voltage drop calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Current: {current} A').format(current=current))
        steps.append(_('Voltage: {voltage} V').format(voltage=voltage))
        steps.append(_('Length: {length} ft').format(length=length))
        steps.append(_('Wire Size: {size} AWG').format(size=wire_size))
        steps.append(_('Wire Material: {material}').format(material=wire_material))
        steps.append(_('Circuit Type: {type}').format(type=circuit_type))
        if circuit_type != 'dc':
            steps.append(_('Power Factor: {pf}').format(pf=power_factor))
        steps.append('')
        steps.append(_('Step 2: Calculate wire resistance'))
        steps.append(_('Resistivity: {resistivity} Ω-cmil/ft').format(resistivity=resistivity))
        steps.append(_('Circular Mils: {cmils} cmil').format(cmils=circular_mils))
        steps.append(_('Resistance = (Resistivity × Length) / Circular Mils'))
        steps.append(_('Resistance = ({resistivity} × {length}) / {cmils}').format(resistivity=resistivity, length=length, cmils=circular_mils))
        steps.append(_('Resistance = {resistance} Ω').format(resistance=round(resistance, 4)))
        steps.append('')
        steps.append(_('Step 3: Calculate voltage drop'))
        if circuit_type == 'dc':
            steps.append(_('Voltage Drop = Current × Resistance × 2'))
            steps.append(_('Voltage Drop = {current} × {resistance} × 2').format(current=current, resistance=round(resistance, 4)))
        elif circuit_type == 'single_phase':
            steps.append(_('Voltage Drop = Current × Resistance × 2 × Power Factor'))
            steps.append(_('Voltage Drop = {current} × {resistance} × 2 × {pf}').format(current=current, resistance=round(resistance, 4), pf=power_factor))
        elif circuit_type == 'three_phase':
            steps.append(_('Voltage Drop = Current × Resistance × √3 × Power Factor'))
            steps.append(_('Voltage Drop = {current} × {resistance} × 1.732 × {pf}').format(current=current, resistance=round(resistance, 4), pf=power_factor))
        steps.append(_('Voltage Drop = {drop} V').format(drop=round(voltage_drop, 2)))
        steps.append('')
        steps.append(_('Step 4: Calculate percentage drop'))
        steps.append(_('Voltage Drop % = (Voltage Drop / Voltage) × 100'))
        steps.append(_('Voltage Drop % = ({drop} / {voltage}) × 100 = {percent}%').format(drop=round(voltage_drop, 2), voltage=voltage, percent=round(voltage_drop_percent, 2)))
        steps.append('')
        steps.append(_('Step 5: Calculate voltage at load'))
        steps.append(_('Voltage at Load = Source Voltage - Voltage Drop'))
        steps.append(_('Voltage at Load = {voltage} - {drop} = {load} V').format(voltage=voltage, drop=round(voltage_drop, 2), load=round(voltage_at_load, 2)))
        steps.append('')
        steps.append(_('Step 6: Calculate power loss'))
        steps.append(_('Power Loss = Current × Voltage Drop'))
        steps.append(_('Power Loss = {current} × {drop} = {loss} W').format(current=current, drop=round(voltage_drop, 2), loss=round(power_loss, 2)))
        return steps
    
    def _prepare_wire_size_steps(self, current, voltage, length, max_voltage_drop, max_voltage_drop_type, max_voltage_drop_volts, wire_material, circuit_type, power_factor, resistivity, max_resistance, required_circular_mils, recommended_size):
        """Prepare step-by-step solution for wire size calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Current: {current} A').format(current=current))
        steps.append(_('Voltage: {voltage} V').format(voltage=voltage))
        steps.append(_('Length: {length} ft').format(length=length))
        steps.append(_('Max Voltage Drop: {drop} {type}').format(drop=max_voltage_drop, type=max_voltage_drop_type))
        steps.append('')
        steps.append(_('Step 2: Convert max voltage drop to volts'))
        if max_voltage_drop_type == 'percent':
            steps.append(_('Max Voltage Drop = ({drop}% / 100) × {voltage} = {volts} V').format(drop=max_voltage_drop, voltage=voltage, volts=round(max_voltage_drop_volts, 2)))
        else:
            steps.append(_('Max Voltage Drop = {volts} V').format(volts=round(max_voltage_drop_volts, 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate maximum resistance'))
        if circuit_type == 'dc':
            steps.append(_('Max Resistance = Max Voltage Drop / (Current × 2)'))
            steps.append(_('Max Resistance = {drop} / ({current} × 2) = {resistance} Ω').format(drop=round(max_voltage_drop_volts, 2), current=current, resistance=round(max_resistance, 4)))
        elif circuit_type == 'single_phase':
            steps.append(_('Max Resistance = Max Voltage Drop / (Current × 2 × Power Factor)'))
            steps.append(_('Max Resistance = {drop} / ({current} × 2 × {pf}) = {resistance} Ω').format(drop=round(max_voltage_drop_volts, 2), current=current, pf=power_factor, resistance=round(max_resistance, 4)))
        elif circuit_type == 'three_phase':
            steps.append(_('Max Resistance = Max Voltage Drop / (Current × √3 × Power Factor)'))
            steps.append(_('Max Resistance = {drop} / ({current} × 1.732 × {pf}) = {resistance} Ω').format(drop=round(max_voltage_drop_volts, 2), current=current, pf=power_factor, resistance=round(max_resistance, 4)))
        steps.append('')
        steps.append(_('Step 4: Calculate required circular mils'))
        steps.append(_('Required CM = (Resistivity × Length) / Max Resistance'))
        steps.append(_('Required CM = ({resistivity} × {length}) / {resistance} = {cmils} cmil').format(resistivity=resistivity, length=length, resistance=round(max_resistance, 4), cmils=round(required_circular_mils, 0)))
        steps.append('')
        steps.append(_('Step 5: Select appropriate wire size'))
        steps.append(_('Recommended Wire Size: {size} AWG').format(size=recommended_size))
        return steps
    
    def _prepare_max_current_steps(self, voltage_drop, voltage, length, wire_size, wire_material, circuit_type, power_factor, resistivity, circular_mils, resistance, max_current, voltage_drop_percent):
        """Prepare step-by-step solution for max current calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage Drop: {drop} V').format(drop=voltage_drop))
        steps.append(_('Voltage: {voltage} V').format(voltage=voltage))
        steps.append(_('Length: {length} ft').format(length=length))
        steps.append(_('Wire Size: {size} AWG').format(size=wire_size))
        steps.append('')
        steps.append(_('Step 2: Calculate wire resistance'))
        steps.append(_('Resistance = ({resistivity} × {length}) / {cmils} = {resistance} Ω').format(resistivity=resistivity, length=length, cmils=circular_mils, resistance=round(resistance, 4)))
        steps.append('')
        steps.append(_('Step 3: Calculate maximum current'))
        if circuit_type == 'dc':
            steps.append(_('Max Current = Voltage Drop / (Resistance × 2)'))
            steps.append(_('Max Current = {drop} / ({resistance} × 2) = {current} A').format(drop=voltage_drop, resistance=round(resistance, 4), current=round(max_current, 2)))
        elif circuit_type == 'single_phase':
            steps.append(_('Max Current = Voltage Drop / (Resistance × 2 × Power Factor)'))
            steps.append(_('Max Current = {drop} / ({resistance} × 2 × {pf}) = {current} A').format(drop=voltage_drop, resistance=round(resistance, 4), pf=power_factor, current=round(max_current, 2)))
        elif circuit_type == 'three_phase':
            steps.append(_('Max Current = Voltage Drop / (Resistance × √3 × Power Factor)'))
            steps.append(_('Max Current = {drop} / ({resistance} × 1.732 × {pf}) = {current} A').format(drop=voltage_drop, resistance=round(resistance, 4), pf=power_factor, current=round(max_current, 2)))
        steps.append('')
        steps.append(_('Step 4: Calculate percentage drop'))
        steps.append(_('Voltage Drop % = ({drop} / {voltage}) × 100 = {percent}%').format(drop=voltage_drop, voltage=voltage, percent=round(voltage_drop_percent, 2)))
        return steps
    
    def _prepare_max_length_steps(self, voltage_drop, voltage, current, wire_size, wire_material, circuit_type, power_factor, resistivity, circular_mils, max_length, voltage_drop_percent):
        """Prepare step-by-step solution for max length calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Voltage Drop: {drop} V').format(drop=voltage_drop))
        steps.append(_('Voltage: {voltage} V').format(voltage=voltage))
        steps.append(_('Current: {current} A').format(current=current))
        steps.append(_('Wire Size: {size} AWG').format(size=wire_size))
        steps.append('')
        steps.append(_('Step 2: Calculate maximum length'))
        if circuit_type == 'dc':
            steps.append(_('Max Length = (Voltage Drop × Circular Mils) / (Current × Resistivity × 2)'))
            steps.append(_('Max Length = ({drop} × {cmils}) / ({current} × {resistivity} × 2)').format(drop=voltage_drop, cmils=circular_mils, current=current, resistivity=resistivity))
        elif circuit_type == 'single_phase':
            steps.append(_('Max Length = (Voltage Drop × Circular Mils) / (Current × Resistivity × 2 × Power Factor)'))
            steps.append(_('Max Length = ({drop} × {cmils}) / ({current} × {resistivity} × 2 × {pf})').format(drop=voltage_drop, cmils=circular_mils, current=current, resistivity=resistivity, pf=power_factor))
        elif circuit_type == 'three_phase':
            steps.append(_('Max Length = (Voltage Drop × Circular Mils) / (Current × Resistivity × √3 × Power Factor)'))
            steps.append(_('Max Length = ({drop} × {cmils}) / ({current} × {resistivity} × 1.732 × {pf})').format(drop=voltage_drop, cmils=circular_mils, current=current, resistivity=resistivity, pf=power_factor))
        steps.append(_('Max Length = {length} ft').format(length=round(max_length, 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate percentage drop'))
        steps.append(_('Voltage Drop % = ({drop} / {voltage}) × 100 = {percent}%').format(drop=voltage_drop, voltage=voltage, percent=round(voltage_drop_percent, 2)))
        return steps
    
    # Chart data preparation methods
    def _prepare_voltage_drop_chart_data(self, voltage, voltage_drop, voltage_at_load):
        """Prepare chart data for voltage drop visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Source Voltage'), _('Voltage Drop'), _('Voltage at Load')],
                    'datasets': [{
                        'label': _('Voltage (V)'),
                        'data': [voltage, voltage_drop, voltage_at_load],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#ef4444',
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
                            'text': _('Voltage Distribution')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Voltage (V)')
                            }
                        }
                    }
                }
            }
            return {'voltage_drop_chart': chart_config}
        except Exception as e:
            return None
