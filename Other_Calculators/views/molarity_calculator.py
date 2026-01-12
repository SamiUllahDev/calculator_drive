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
class MolarityCalculator(View):
    """
    Professional Molarity Calculator with Comprehensive Features
    
    This calculator provides molarity calculations with:
    - Calculate molarity from moles and volume
    - Calculate moles from molarity and volume
    - Calculate volume from molarity and moles
    - Calculate molarity from mass, molecular weight, and volume
    - Calculate mass from molarity, molecular weight, and volume
    - Dilution calculations (M1V1 = M2V2)
    - Unit conversions
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/molarity_calculator.html'
    
    # Volume conversion factors (to liters)
    VOLUME_CONVERSIONS = {
        'liters': 1.0,
        'milliliters': 0.001,  # 1 mL = 0.001 L
        'microliters': 0.000001,  # 1 µL = 0.000001 L
        'cubic_centimeters': 0.001,  # 1 cm³ = 0.001 L
        'cubic_meters': 1000.0,  # 1 m³ = 1000 L
    }
    
    # Mass conversion factors (to grams)
    MASS_CONVERSIONS = {
        'grams': 1.0,
        'milligrams': 0.001,  # 1 mg = 0.001 g
        'micrograms': 0.000001,  # 1 µg = 0.000001 g
        'kilograms': 1000.0,  # 1 kg = 1000 g
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'liters': 'L',
            'milliliters': 'mL',
            'microliters': 'µL',
            'cubic_centimeters': 'cm³',
            'cubic_meters': 'm³',
            'grams': 'g',
            'milligrams': 'mg',
            'micrograms': 'µg',
            'kilograms': 'kg',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Molarity Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'molarity_from_moles')
            
            if calc_type == 'molarity_from_moles':
                return self._calculate_molarity_from_moles(data)
            elif calc_type == 'moles_from_molarity':
                return self._calculate_moles_from_molarity(data)
            elif calc_type == 'volume_from_molarity':
                return self._calculate_volume_from_molarity(data)
            elif calc_type == 'molarity_from_mass':
                return self._calculate_molarity_from_mass(data)
            elif calc_type == 'mass_from_molarity':
                return self._calculate_mass_from_molarity(data)
            elif calc_type == 'dilution':
                return self._calculate_dilution(data)
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
    
    def _calculate_molarity_from_moles(self, data):
        """Calculate molarity from moles and volume"""
        try:
            if 'moles' not in data or data.get('moles') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Moles is required.')
                }, status=400)
            
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                moles = float(data.get('moles', 0))
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'liters')
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            # Validate ranges
            if moles < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Moles must be non-negative.')
                }, status=400)
            
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            # Convert volume to liters
            volume_liters = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate molarity: M = n / V
            molarity = float(np.divide(moles, volume_liters))
            
            # Validate result
            if math.isinf(molarity) or math.isnan(molarity) or np.isinf(molarity) or np.isnan(molarity):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_molarity_from_moles_steps(moles, volume, volume_unit, volume_liters, molarity)
            
            chart_data = self._prepare_molarity_from_moles_chart_data(moles, volume_liters, molarity)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'molarity_from_moles',
                'moles': moles,
                'volume': volume,
                'volume_unit': volume_unit,
                'molarity': round(molarity, 6),
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
                'error': _('Error calculating molarity: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_moles_from_molarity(self, data):
        """Calculate moles from molarity and volume"""
        try:
            if 'molarity' not in data or data.get('molarity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Molarity is required.')
                }, status=400)
            
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                molarity = float(data.get('molarity', 0))
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'liters')
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            # Validate ranges
            if molarity < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Molarity must be non-negative.')
                }, status=400)
            
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            # Convert volume to liters
            volume_liters = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate moles: n = M × V
            moles = float(np.multiply(molarity, volume_liters))
            
            # Validate result
            if math.isinf(moles) or math.isnan(moles) or np.isinf(moles) or np.isnan(moles):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_moles_from_molarity_steps(molarity, volume, volume_unit, volume_liters, moles)
            
            chart_data = self._prepare_moles_from_molarity_chart_data(molarity, volume_liters, moles)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'moles_from_molarity',
                'molarity': molarity,
                'volume': volume,
                'volume_unit': volume_unit,
                'moles': round(moles, 6),
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
                'error': _('Error calculating moles: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_volume_from_molarity(self, data):
        """Calculate volume from molarity and moles"""
        try:
            if 'molarity' not in data or data.get('molarity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Molarity is required.')
                }, status=400)
            
            if 'moles' not in data or data.get('moles') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Moles is required.')
                }, status=400)
            
            try:
                molarity = float(data.get('molarity', 0))
                moles = float(data.get('moles', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            result_unit = data.get('result_unit', 'liters')
            
            # Validate units
            if result_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if molarity <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Molarity must be greater than zero.')
                }, status=400)
            
            if moles < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Moles must be non-negative.')
                }, status=400)
            
            # Calculate volume in liters: V = n / M
            volume_liters = float(np.divide(moles, molarity))
            
            # Convert to result unit
            result = float(np.divide(volume_liters, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_volume_from_molarity_steps(molarity, moles, volume_liters, result, result_unit)
            
            chart_data = self._prepare_volume_from_molarity_chart_data(molarity, moles, volume_liters)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'volume_from_molarity',
                'molarity': molarity,
                'moles': moles,
                'volume': round(result, 6),
                'result_unit': result_unit,
                'volume_liters': round(volume_liters, 6),
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
                'error': _('Error calculating volume: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_molarity_from_mass(self, data):
        """Calculate molarity from mass, molecular weight, and volume"""
        try:
            if 'mass' not in data or data.get('mass') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass is required.')
                }, status=400)
            
            if 'molecular_weight' not in data or data.get('molecular_weight') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Molecular weight is required.')
                }, status=400)
            
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                mass = float(data.get('mass', 0))
                molecular_weight = float(data.get('molecular_weight', 0))
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            mass_unit = data.get('mass_unit', 'grams')
            volume_unit = data.get('volume_unit', 'liters')
            
            # Validate units
            if mass_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid mass unit.')
                }, status=400)
            
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            # Validate ranges
            if mass <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Mass must be greater than zero.')
                }, status=400)
            
            if molecular_weight <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Molecular weight must be greater than zero.')
                }, status=400)
            
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            mass_grams = float(mass * self.MASS_CONVERSIONS[mass_unit])
            volume_liters = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate moles: n = m / MW
            moles = float(np.divide(mass_grams, molecular_weight))
            
            # Calculate molarity: M = n / V
            molarity = float(np.divide(moles, volume_liters))
            
            # Validate result
            if math.isinf(molarity) or math.isnan(molarity) or np.isinf(molarity) or np.isnan(molarity):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_molarity_from_mass_steps(mass, mass_unit, molecular_weight, volume, volume_unit, mass_grams, volume_liters, moles, molarity)
            
            chart_data = self._prepare_molarity_from_mass_chart_data(mass_grams, molecular_weight, volume_liters, moles, molarity)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'molarity_from_mass',
                'mass': mass,
                'mass_unit': mass_unit,
                'molecular_weight': molecular_weight,
                'volume': volume,
                'volume_unit': volume_unit,
                'moles': round(moles, 6),
                'molarity': round(molarity, 6),
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
                'error': _('Error calculating molarity: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_mass_from_molarity(self, data):
        """Calculate mass from molarity, molecular weight, and volume"""
        try:
            if 'molarity' not in data or data.get('molarity') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Molarity is required.')
                }, status=400)
            
            if 'molecular_weight' not in data or data.get('molecular_weight') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Molecular weight is required.')
                }, status=400)
            
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                molarity = float(data.get('molarity', 0))
                molecular_weight = float(data.get('molecular_weight', 0))
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'liters')
            result_unit = data.get('result_unit', 'grams')
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            if result_unit not in self.MASS_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if molarity < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Molarity must be non-negative.')
                }, status=400)
            
            if molecular_weight <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Molecular weight must be greater than zero.')
                }, status=400)
            
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            # Convert volume to liters
            volume_liters = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate moles: n = M × V
            moles = float(np.multiply(molarity, volume_liters))
            
            # Calculate mass: m = n × MW
            mass_grams = float(np.multiply(moles, molecular_weight))
            
            # Convert to result unit
            result = float(np.divide(mass_grams, self.MASS_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_mass_from_molarity_steps(molarity, molecular_weight, volume, volume_unit, volume_liters, moles, mass_grams, result, result_unit)
            
            chart_data = self._prepare_mass_from_molarity_chart_data(molarity, volume_liters, molecular_weight, moles, mass_grams)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'mass_from_molarity',
                'molarity': molarity,
                'molecular_weight': molecular_weight,
                'volume': volume,
                'volume_unit': volume_unit,
                'moles': round(moles, 6),
                'mass': round(result, 6),
                'result_unit': result_unit,
                'mass_grams': round(mass_grams, 6),
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
                'error': _('Error calculating mass: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_dilution(self, data):
        """Calculate dilution using M1V1 = M2V2"""
        try:
            calc_mode = data.get('dilution_mode', 'find_v2')
            
            if calc_mode == 'find_v2':
                # Find final volume
                if 'm1' not in data or data.get('m1') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Initial molarity (M1) is required.')
                    }, status=400)
                
                if 'v1' not in data or data.get('v1') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Initial volume (V1) is required.')
                    }, status=400)
                
                if 'm2' not in data or data.get('m2') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Final molarity (M2) is required.')
                    }, status=400)
                
                try:
                    m1 = float(data.get('m1', 0))
                    v1 = float(data.get('v1', 0))
                    m2 = float(data.get('m2', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                v1_unit = data.get('v1_unit', 'liters')
                result_unit = data.get('result_unit', 'liters')
                
                # Validate units
                if v1_unit not in self.VOLUME_CONVERSIONS or result_unit not in self.VOLUME_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid volume unit.')
                    }, status=400)
                
                # Validate ranges
                if m1 <= 0 or m2 <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Molarity values must be greater than zero.')
                    }, status=400)
                
                if v1 <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Volume must be greater than zero.')
                    }, status=400)
                
                if m2 > m1:
                    return JsonResponse({
                        'success': False,
                        'error': _('Final molarity (M2) cannot be greater than initial molarity (M1).')
                    }, status=400)
                
                # Convert to liters
                v1_liters = float(v1 * self.VOLUME_CONVERSIONS[v1_unit])
                
                # Calculate V2: V2 = (M1 × V1) / M2
                v2_liters = float(np.divide(np.multiply(m1, v1_liters), m2))
                
                # Convert to result unit
                result = float(np.divide(v2_liters, self.VOLUME_CONVERSIONS[result_unit]))
                
                # Validate result
                if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                steps = self._prepare_dilution_v2_steps(m1, v1, v1_unit, m2, v1_liters, v2_liters, result, result_unit)
                
                chart_data = self._prepare_dilution_chart_data(m1, v1_liters, m2, v2_liters)
                
                return JsonResponse({
                    'success': True,
                    'calc_type': 'dilution',
                    'dilution_mode': 'find_v2',
                    'm1': m1,
                    'v1': v1,
                    'v1_unit': v1_unit,
                    'm2': m2,
                    'v2': round(result, 6),
                    'result_unit': result_unit,
                    'v2_liters': round(v2_liters, 6),
                    'step_by_step': steps,
                    'chart_data': chart_data,
                })
                
            elif calc_mode == 'find_m2':
                # Find final molarity
                if 'm1' not in data or data.get('m1') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Initial molarity (M1) is required.')
                    }, status=400)
                
                if 'v1' not in data or data.get('v1') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Initial volume (V1) is required.')
                    }, status=400)
                
                if 'v2' not in data or data.get('v2') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Final volume (V2) is required.')
                    }, status=400)
                
                try:
                    m1 = float(data.get('m1', 0))
                    v1 = float(data.get('v1', 0))
                    v2 = float(data.get('v2', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                v1_unit = data.get('v1_unit', 'liters')
                v2_unit = data.get('v2_unit', 'liters')
                
                # Validate units
                if v1_unit not in self.VOLUME_CONVERSIONS or v2_unit not in self.VOLUME_CONVERSIONS:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid volume unit.')
                    }, status=400)
                
                # Validate ranges
                if m1 <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Initial molarity must be greater than zero.')
                    }, status=400)
                
                if v1 <= 0 or v2 <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Volumes must be greater than zero.')
                    }, status=400)
                
                # Convert to liters
                v1_liters = float(v1 * self.VOLUME_CONVERSIONS[v1_unit])
                v2_liters = float(v2 * self.VOLUME_CONVERSIONS[v2_unit])
                
                # Calculate M2: M2 = (M1 × V1) / V2
                m2 = float(np.divide(np.multiply(m1, v1_liters), v2_liters))
                
                # Validate result
                if math.isinf(m2) or math.isnan(m2) or np.isinf(m2) or np.isnan(m2):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid calculation result.')
                    }, status=400)
                
                steps = self._prepare_dilution_m2_steps(m1, v1, v1_unit, v2, v2_unit, v1_liters, v2_liters, m2)
                
                chart_data = self._prepare_dilution_chart_data(m1, v1_liters, m2, v2_liters)
                
                return JsonResponse({
                    'success': True,
                    'calc_type': 'dilution',
                    'dilution_mode': 'find_m2',
                    'm1': m1,
                    'v1': v1,
                    'v1_unit': v1_unit,
                    'v2': v2,
                    'v2_unit': v2_unit,
                    'm2': round(m2, 6),
                    'step_by_step': steps,
                    'chart_data': chart_data,
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid dilution mode.')
                }, status=400)
                
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating dilution: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_molarity_from_moles_steps(self, moles, volume, volume_unit, volume_liters, molarity):
        """Prepare step-by-step solution for molarity from moles calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Moles: {moles} mol').format(moles=moles))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append('')
        if volume_unit != 'liters':
            steps.append(_('Step 2: Convert volume to liters'))
            steps.append(_('Volume in liters: {volume} L').format(volume=volume_liters))
            steps.append('')
        steps.append(_('Step 3: Apply the molarity formula'))
        steps.append(_('Formula: Molarity (M) = Moles (n) / Volume (V)'))
        steps.append(_('M = n / V'))
        steps.append(_('M = {moles} mol / {volume} L').format(moles=moles, volume=volume_liters))
        steps.append(_('M = {molarity} M').format(molarity=molarity))
        return steps
    
    def _prepare_moles_from_molarity_steps(self, molarity, volume, volume_unit, volume_liters, moles):
        """Prepare step-by-step solution for moles from molarity calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Molarity: {molarity} M').format(molarity=molarity))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append('')
        if volume_unit != 'liters':
            steps.append(_('Step 2: Convert volume to liters'))
            steps.append(_('Volume in liters: {volume} L').format(volume=volume_liters))
            steps.append('')
        steps.append(_('Step 3: Apply the moles formula'))
        steps.append(_('Formula: Moles (n) = Molarity (M) × Volume (V)'))
        steps.append(_('n = M × V'))
        steps.append(_('n = {molarity} M × {volume} L').format(molarity=molarity, volume=volume_liters))
        steps.append(_('n = {moles} mol').format(moles=moles))
        return steps
    
    def _prepare_volume_from_molarity_steps(self, molarity, moles, volume_liters, result, result_unit):
        """Prepare step-by-step solution for volume from molarity calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Molarity: {molarity} M').format(molarity=molarity))
        steps.append(_('Moles: {moles} mol').format(moles=moles))
        steps.append('')
        steps.append(_('Step 2: Apply the volume formula'))
        steps.append(_('Formula: Volume (V) = Moles (n) / Molarity (M)'))
        steps.append(_('V = n / M'))
        steps.append(_('V = {moles} mol / {molarity} M').format(moles=moles, molarity=molarity))
        steps.append(_('V = {volume} L').format(volume=volume_liters))
        steps.append('')
        if result_unit != 'liters':
            steps.append(_('Step 3: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 3: Result'))
            steps.append(_('Volume = {result} L').format(result=result))
        return steps
    
    def _prepare_molarity_from_mass_steps(self, mass, mass_unit, molecular_weight, volume, volume_unit, mass_grams, volume_liters, moles, molarity):
        """Prepare step-by-step solution for molarity from mass calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Mass: {mass} {unit}').format(mass=mass, unit=self._format_unit(mass_unit)))
        steps.append(_('Molecular Weight: {mw} g/mol').format(mw=molecular_weight))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if mass_unit != 'grams':
            steps.append(_('Mass in grams: {mass} g').format(mass=mass_grams))
        if volume_unit != 'liters':
            steps.append(_('Volume in liters: {volume} L').format(volume=volume_liters))
        steps.append('')
        steps.append(_('Step 3: Calculate moles'))
        steps.append(_('Formula: Moles (n) = Mass (m) / Molecular Weight (MW)'))
        steps.append(_('n = m / MW'))
        steps.append(_('n = {mass} g / {mw} g/mol').format(mass=mass_grams, mw=molecular_weight))
        steps.append(_('n = {moles} mol').format(moles=moles))
        steps.append('')
        steps.append(_('Step 4: Calculate molarity'))
        steps.append(_('Formula: Molarity (M) = Moles (n) / Volume (V)'))
        steps.append(_('M = n / V'))
        steps.append(_('M = {moles} mol / {volume} L').format(moles=moles, volume=volume_liters))
        steps.append(_('M = {molarity} M').format(molarity=molarity))
        return steps
    
    def _prepare_mass_from_molarity_steps(self, molarity, molecular_weight, volume, volume_unit, volume_liters, moles, mass_grams, result, result_unit):
        """Prepare step-by-step solution for mass from molarity calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Molarity: {molarity} M').format(molarity=molarity))
        steps.append(_('Molecular Weight: {mw} g/mol').format(mw=molecular_weight))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert volume to liters'))
        if volume_unit != 'liters':
            steps.append(_('Volume in liters: {volume} L').format(volume=volume_liters))
        steps.append('')
        steps.append(_('Step 3: Calculate moles'))
        steps.append(_('Formula: Moles (n) = Molarity (M) × Volume (V)'))
        steps.append(_('n = M × V'))
        steps.append(_('n = {molarity} M × {volume} L').format(molarity=molarity, volume=volume_liters))
        steps.append(_('n = {moles} mol').format(moles=moles))
        steps.append('')
        steps.append(_('Step 4: Calculate mass'))
        steps.append(_('Formula: Mass (m) = Moles (n) × Molecular Weight (MW)'))
        steps.append(_('m = n × MW'))
        steps.append(_('m = {moles} mol × {mw} g/mol').format(moles=moles, mw=molecular_weight))
        steps.append(_('m = {mass} g').format(mass=mass_grams))
        steps.append('')
        if result_unit != 'grams':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Mass = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Mass = {result} g').format(result=result))
        return steps
    
    def _prepare_dilution_v2_steps(self, m1, v1, v1_unit, m2, v1_liters, v2_liters, result, result_unit):
        """Prepare step-by-step solution for dilution finding V2"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Initial Molarity (M1): {m1} M').format(m1=m1))
        steps.append(_('Initial Volume (V1): {v1} {unit}').format(v1=v1, unit=self._format_unit(v1_unit)))
        steps.append(_('Final Molarity (M2): {m2} M').format(m2=m2))
        steps.append('')
        steps.append(_('Step 2: Convert V1 to liters'))
        if v1_unit != 'liters':
            steps.append(_('V1 in liters: {v1} L').format(v1=v1_liters))
        steps.append('')
        steps.append(_('Step 3: Apply the dilution formula'))
        steps.append(_('Formula: M1 × V1 = M2 × V2'))
        steps.append(_('V2 = (M1 × V1) / M2'))
        steps.append(_('V2 = ({m1} M × {v1} L) / {m2} M').format(m1=m1, v1=v1_liters, m2=m2))
        steps.append(_('V2 = {v2} L').format(v2=v2_liters))
        steps.append('')
        if result_unit != 'liters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Final Volume (V2) = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Final Volume (V2) = {result} L').format(result=result))
        return steps
    
    def _prepare_dilution_m2_steps(self, m1, v1, v1_unit, v2, v2_unit, v1_liters, v2_liters, m2):
        """Prepare step-by-step solution for dilution finding M2"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Initial Molarity (M1): {m1} M').format(m1=m1))
        steps.append(_('Initial Volume (V1): {v1} {unit}').format(v1=v1, unit=self._format_unit(v1_unit)))
        steps.append(_('Final Volume (V2): {v2} {unit}').format(v2=v2, unit=self._format_unit(v2_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert volumes to liters'))
        if v1_unit != 'liters' or v2_unit != 'liters':
            steps.append(_('V1 in liters: {v1} L').format(v1=v1_liters))
            steps.append(_('V2 in liters: {v2} L').format(v2=v2_liters))
        steps.append('')
        steps.append(_('Step 3: Apply the dilution formula'))
        steps.append(_('Formula: M1 × V1 = M2 × V2'))
        steps.append(_('M2 = (M1 × V1) / V2'))
        steps.append(_('M2 = ({m1} M × {v1} L) / {v2} L').format(m1=m1, v1=v1_liters, v2=v2_liters))
        steps.append(_('M2 = {m2} M').format(m2=m2))
        return steps
    
    # Chart data preparation methods
    def _prepare_molarity_from_moles_chart_data(self, moles, volume_liters, molarity):
        """Prepare chart data for molarity from moles calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Moles (mol)'), _('Volume (L)'), _('Molarity (M)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [moles, volume_liters, molarity],
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
                            'text': _('Molarity Calculation')
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
            return {'molarity_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_moles_from_molarity_chart_data(self, molarity, volume_liters, moles):
        """Prepare chart data for moles from molarity calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Molarity (M)'), _('Volume (L)'), _('Moles (mol)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [molarity, volume_liters, moles],
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
                            'text': _('Moles Calculation')
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
            return {'moles_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_volume_from_molarity_chart_data(self, molarity, moles, volume_liters):
        """Prepare chart data for volume from molarity calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Molarity (M)'), _('Moles (mol)'), _('Volume (L)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [molarity, moles, volume_liters],
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
                            'text': _('Volume Calculation')
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
            return {'volume_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_molarity_from_mass_chart_data(self, mass_grams, molecular_weight, volume_liters, moles, molarity):
        """Prepare chart data for molarity from mass calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Mass (g)'), _('MW (g/mol)'), _('Volume (L)'), _('Moles (mol)'), _('Molarity (M)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [mass_grams, molecular_weight, volume_liters, moles, molarity],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#ef4444',
                            '#8b5cf6'
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
                            'text': _('Molarity from Mass Calculation')
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
            return {'molarity_from_mass_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_mass_from_molarity_chart_data(self, molarity, volume_liters, molecular_weight, moles, mass_grams):
        """Prepare chart data for mass from molarity calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Molarity (M)'), _('Volume (L)'), _('MW (g/mol)'), _('Moles (mol)'), _('Mass (g)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [molarity, volume_liters, molecular_weight, moles, mass_grams],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#ef4444',
                            '#8b5cf6'
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
                            'text': _('Mass from Molarity Calculation')
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
            return {'mass_from_molarity_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_dilution_chart_data(self, m1, v1_liters, m2, v2_liters):
        """Prepare chart data for dilution calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('M1 (M)'), _('V1 (L)'), _('M2 (M)'), _('V2 (L)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [m1, v1_liters, m2, v2_liters],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(239, 68, 68, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#ef4444'
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
                            'text': _('Dilution Calculation (M1V1 = M2V2)')
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
            return {'dilution_chart': chart_config}
        except Exception as e:
            return None
