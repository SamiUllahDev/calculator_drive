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
class GravelCalculator(View):
    """
    Professional Gravel Calculator with Comprehensive Features
    
    This calculator provides gravel calculations with:
    - Calculate gravel volume for rectangular areas
    - Calculate gravel volume for circular areas
    - Calculate gravel volume for triangular areas
    - Calculate gravel weight from volume
    - Calculate gravel cost
    - Calculate coverage area from volume
    - Unit conversions
    
    Features:
    - Supports multiple shapes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/gravel_calculator.html'
    
    # Volume conversion factors (to cubic feet)
    VOLUME_CONVERSIONS = {
        'cubic_feet': 1.0,
        'cubic_yards': 27.0,  # 1 cubic yard = 27 cubic feet
        'cubic_meters': 35.3147,  # 1 cubic meter = 35.3147 cubic feet
    }
    
    # Weight conversion factors (to pounds)
    WEIGHT_CONVERSIONS = {
        'pounds': 1.0,
        'tons': 2000.0,  # 1 ton = 2000 pounds
        'kilograms': 2.20462,  # 1 kg = 2.20462 pounds
    }
    
    # Length conversion factors (to feet)
    LENGTH_CONVERSIONS = {
        'feet': 1.0,
        'inches': 1.0/12.0,  # 1 inch = 1/12 feet
        'yards': 3.0,  # 1 yard = 3 feet
        'meters': 3.28084,  # 1 meter = 3.28084 feet
    }
    
    # Typical gravel density (pounds per cubic foot)
    GRAVEL_DENSITY_LB_PER_CF = 105.0  # Average density
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'cubic_feet': 'ft³',
            'cubic_yards': 'yd³',
            'cubic_meters': 'm³',
            'pounds': 'lbs',
            'tons': 'tons',
            'kilograms': 'kg',
            'feet': 'ft',
            'inches': 'in',
            'yards': 'yd',
            'meters': 'm',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Gravel Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'rectangular')
            
            if calc_type == 'rectangular':
                return self._calculate_rectangular(data)
            elif calc_type == 'circular':
                return self._calculate_circular(data)
            elif calc_type == 'triangular':
                return self._calculate_triangular(data)
            elif calc_type == 'weight':
                return self._calculate_weight(data)
            elif calc_type == 'cost':
                return self._calculate_cost(data)
            elif calc_type == 'coverage':
                return self._calculate_coverage(data)
            elif calc_type == 'convert_volume':
                return self._convert_volume_units(data)
            elif calc_type == 'convert_weight':
                return self._convert_weight_units(data)
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
    
    def _calculate_rectangular(self, data):
        """Calculate gravel volume for rectangular area"""
        try:
            if 'length' not in data or data.get('length') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Length is required.')
                }, status=400)
            
            if 'width' not in data or data.get('width') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Width is required.')
                }, status=400)
            
            if 'depth' not in data or data.get('depth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth is required.')
                }, status=400)
            
            try:
                length = float(data.get('length', 0))
                width = float(data.get('width', 0))
                depth = float(data.get('depth', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            length_unit = data.get('length_unit', 'feet')
            width_unit = data.get('width_unit', 'feet')
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'cubic_yards')
            
            # Validate units
            if length_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid length unit.')
                }, status=400)
            
            if width_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid width unit.')
                }, status=400)
            
            if depth_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid depth unit.')
                }, status=400)
            
            if result_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if length <= 0 or width <= 0 or depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Length, width, and depth must be greater than zero.')
                }, status=400)
            
            if length > 10000 or width > 10000 or depth > 1000:
                return JsonResponse({
                    'success': False,
                    'error': _('Dimensions are too large. Please use smaller values.')
                }, status=400)
            
            # Convert to feet
            length_ft = float(length * self.LENGTH_CONVERSIONS[length_unit])
            width_ft = float(width * self.LENGTH_CONVERSIONS[width_unit])
            depth_ft = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate volume in cubic feet
            volume_cf = float(np.multiply(np.multiply(length_ft, width_ft), depth_ft))
            
            # Convert to result unit
            volume_result = float(np.divide(volume_cf, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(volume_result) or math.isnan(volume_result) or np.isinf(volume_result) or np.isnan(volume_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_rectangular_steps(length, length_unit, width, width_unit, depth, depth_unit, volume_result, result_unit, length_ft, width_ft, depth_ft, volume_cf)
            
            chart_data = self._prepare_rectangular_chart_data(length_ft, width_ft, depth_ft, volume_cf)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'rectangular',
                'length': length,
                'length_unit': length_unit,
                'width': width,
                'width_unit': width_unit,
                'depth': depth,
                'depth_unit': depth_unit,
                'volume': volume_result,
                'result_unit': result_unit,
                'volume_cubic_feet': volume_cf,
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
                'error': _('Error calculating rectangular volume: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_circular(self, data):
        """Calculate gravel volume for circular area"""
        try:
            if 'diameter' not in data or data.get('diameter') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Diameter is required.')
                }, status=400)
            
            if 'depth' not in data or data.get('depth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth is required.')
                }, status=400)
            
            try:
                diameter = float(data.get('diameter', 0))
                depth = float(data.get('depth', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            diameter_unit = data.get('diameter_unit', 'feet')
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'cubic_yards')
            
            # Validate units
            if diameter_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid diameter unit.')
                }, status=400)
            
            if depth_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid depth unit.')
                }, status=400)
            
            if result_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if diameter <= 0 or depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Diameter and depth must be greater than zero.')
                }, status=400)
            
            # Convert to feet
            diameter_ft = float(diameter * self.LENGTH_CONVERSIONS[diameter_unit])
            depth_ft = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            radius_ft = float(np.divide(diameter_ft, 2.0))
            
            # Calculate volume: V = π × r² × h
            volume_cf = float(np.multiply(
                np.multiply(math.pi, np.power(radius_ft, 2)),
                depth_ft
            ))
            
            # Convert to result unit
            volume_result = float(np.divide(volume_cf, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(volume_result) or math.isnan(volume_result) or np.isinf(volume_result) or np.isnan(volume_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_circular_steps(diameter, diameter_unit, depth, depth_unit, volume_result, result_unit, diameter_ft, depth_ft, radius_ft, volume_cf)
            
            chart_data = self._prepare_circular_chart_data(diameter_ft, depth_ft, volume_cf)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'circular',
                'diameter': diameter,
                'diameter_unit': diameter_unit,
                'depth': depth,
                'depth_unit': depth_unit,
                'volume': volume_result,
                'result_unit': result_unit,
                'radius_ft': radius_ft,
                'volume_cubic_feet': volume_cf,
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
                'error': _('Error calculating circular volume: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_triangular(self, data):
        """Calculate gravel volume for triangular area"""
        try:
            if 'base' not in data or data.get('base') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Base length is required.')
                }, status=400)
            
            if 'height' not in data or data.get('height') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Height is required.')
                }, status=400)
            
            if 'depth' not in data or data.get('depth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth is required.')
                }, status=400)
            
            try:
                base = float(data.get('base', 0))
                height = float(data.get('height', 0))
                depth = float(data.get('depth', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            base_unit = data.get('base_unit', 'feet')
            height_unit = data.get('height_unit', 'feet')
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'cubic_yards')
            
            # Validate units
            if base_unit not in self.LENGTH_CONVERSIONS or height_unit not in self.LENGTH_CONVERSIONS or depth_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if result_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if base <= 0 or height <= 0 or depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Base, height, and depth must be greater than zero.')
                }, status=400)
            
            # Convert to feet
            base_ft = float(base * self.LENGTH_CONVERSIONS[base_unit])
            height_ft = float(height * self.LENGTH_CONVERSIONS[height_unit])
            depth_ft = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate area: A = (1/2) × base × height
            area_sf = float(np.multiply(0.5, np.multiply(base_ft, height_ft)))
            
            # Calculate volume: V = Area × Depth
            volume_cf = float(np.multiply(area_sf, depth_ft))
            
            # Convert to result unit
            volume_result = float(np.divide(volume_cf, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(volume_result) or math.isnan(volume_result) or np.isinf(volume_result) or np.isnan(volume_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_triangular_steps(base, base_unit, height, height_unit, depth, depth_unit, volume_result, result_unit, base_ft, height_ft, depth_ft, area_sf, volume_cf)
            
            chart_data = self._prepare_triangular_chart_data(base_ft, height_ft, depth_ft, volume_cf)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'triangular',
                'base': base,
                'base_unit': base_unit,
                'height': height,
                'height_unit': height_unit,
                'depth': depth,
                'depth_unit': depth_unit,
                'volume': volume_result,
                'result_unit': result_unit,
                'area_square_feet': area_sf,
                'volume_cubic_feet': volume_cf,
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
                'error': _('Error calculating triangular volume: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_weight(self, data):
        """Calculate gravel weight from volume"""
        try:
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            try:
                volume = float(data.get('volume', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'cubic_yards')
            result_unit = data.get('result_unit', 'tons')
            density = float(data.get('density', self.GRAVEL_DENSITY_LB_PER_CF))
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            if result_unit not in self.WEIGHT_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            if density <= 0 or density > 200:
                return JsonResponse({
                    'success': False,
                    'error': _('Density must be between 0 and 200 pounds per cubic foot.')
                }, status=400)
            
            # Convert volume to cubic feet
            volume_cf = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            
            # Calculate weight in pounds: Weight = Volume × Density
            weight_lbs = float(np.multiply(volume_cf, density))
            
            # Convert to result unit
            weight_result = float(np.divide(weight_lbs, self.WEIGHT_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(weight_result) or math.isnan(weight_result) or np.isinf(weight_result) or np.isnan(weight_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_weight_steps(volume, volume_unit, density, weight_result, result_unit, volume_cf, weight_lbs)
            
            chart_data = self._prepare_weight_chart_data(volume_cf, density, weight_lbs)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'weight',
                'volume': volume,
                'volume_unit': volume_unit,
                'density': density,
                'weight': weight_result,
                'result_unit': result_unit,
                'volume_cubic_feet': volume_cf,
                'weight_pounds': weight_lbs,
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
                'error': _('Error calculating weight: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_cost(self, data):
        """Calculate gravel cost"""
        try:
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            if 'price_per_unit' not in data or data.get('price_per_unit') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Price per unit is required.')
                }, status=400)
            
            try:
                volume = float(data.get('volume', 0))
                price_per_unit = float(data.get('price_per_unit', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'cubic_yards')
            price_unit = data.get('price_unit', 'per_cubic_yard')
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            # Validate ranges
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            if price_per_unit < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Price must be non-negative.')
                }, status=400)
            
            # Calculate cost
            total_cost = float(np.multiply(volume, price_per_unit))
            
            # Validate result
            if math.isinf(total_cost) or math.isnan(total_cost) or np.isinf(total_cost) or np.isnan(total_cost):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_cost_steps(volume, volume_unit, price_per_unit, price_unit, total_cost)
            
            chart_data = self._prepare_cost_chart_data(volume, price_per_unit, total_cost)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'cost',
                'volume': volume,
                'volume_unit': volume_unit,
                'price_per_unit': price_per_unit,
                'price_unit': price_unit,
                'total_cost': total_cost,
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
                'error': _('Error calculating cost: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_coverage(self, data):
        """Calculate coverage area from volume"""
        try:
            if 'volume' not in data or data.get('volume') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume is required.')
                }, status=400)
            
            if 'depth' not in data or data.get('depth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth is required.')
                }, status=400)
            
            try:
                volume = float(data.get('volume', 0))
                depth = float(data.get('depth', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'cubic_yards')
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            if depth_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid depth unit.')
                }, status=400)
            
            # Validate ranges
            if volume <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be greater than zero.')
                }, status=400)
            
            if depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth must be greater than zero.')
                }, status=400)
            
            # Convert to cubic feet and feet
            volume_cf = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            depth_ft = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate coverage area: Area = Volume / Depth
            area_sf = float(np.divide(volume_cf, depth_ft))
            
            # Convert to result unit (if needed)
            if result_unit == 'square_feet':
                area_result = area_sf
            elif result_unit == 'square_yards':
                area_result = float(np.divide(area_sf, 9.0))  # 1 sq yd = 9 sq ft
            elif result_unit == 'square_meters':
                area_result = float(np.divide(area_sf, 10.7639))  # 1 sq m = 10.7639 sq ft
            else:
                area_result = area_sf
            
            # Validate result
            if math.isinf(area_result) or math.isnan(area_result) or np.isinf(area_result) or np.isnan(area_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_coverage_steps(volume, volume_unit, depth, depth_unit, area_result, result_unit, volume_cf, depth_ft, area_sf)
            
            chart_data = self._prepare_coverage_chart_data(volume_cf, depth_ft, area_sf)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'coverage',
                'volume': volume,
                'volume_unit': volume_unit,
                'depth': depth,
                'depth_unit': depth_unit,
                'coverage_area': area_result,
                'result_unit': result_unit,
                'volume_cubic_feet': volume_cf,
                'depth_feet': depth_ft,
                'area_square_feet': area_sf,
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
                'error': _('Error calculating coverage: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_volume_units(self, data):
        """Convert volume units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'cubic_yards')
            to_unit = data.get('to_unit', 'cubic_feet')
            
            # Validate units
            if from_unit not in self.VOLUME_CONVERSIONS or to_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Volume must be non-negative.')
                }, status=400)
            
            # Convert to cubic feet first, then to target unit
            cubic_feet_value = float(value * self.VOLUME_CONVERSIONS[from_unit])
            result = float(np.divide(cubic_feet_value, self.VOLUME_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_volume_steps(value, from_unit, to_unit, result, cubic_feet_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_volume',
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
    
    def _convert_weight_units(self, data):
        """Convert weight units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'tons')
            to_unit = data.get('to_unit', 'pounds')
            
            # Validate units
            if from_unit not in self.WEIGHT_CONVERSIONS or to_unit not in self.WEIGHT_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Weight must be non-negative.')
                }, status=400)
            
            # Convert to pounds first, then to target unit
            pounds_value = float(value * self.WEIGHT_CONVERSIONS[from_unit])
            result = float(np.divide(pounds_value, self.WEIGHT_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_weight_steps(value, from_unit, to_unit, result, pounds_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_weight',
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
    def _prepare_rectangular_steps(self, length, length_unit, width, width_unit, depth, depth_unit, volume_result, result_unit, length_ft, width_ft, depth_ft, volume_cf):
        """Prepare step-by-step solution for rectangular volume calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Length: {val} {unit}').format(val=length, unit=self._format_unit(length_unit)))
        steps.append(_('Width: {val} {unit}').format(val=width, unit=self._format_unit(width_unit)))
        steps.append(_('Depth: {val} {unit}').format(val=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to feet'))
        if length_unit != 'feet':
            steps.append(_('Length in feet: {val} ft').format(val=length_ft))
        if width_unit != 'feet':
            steps.append(_('Width in feet: {val} ft').format(val=width_ft))
        if depth_unit != 'feet':
            steps.append(_('Depth in feet: {val} ft').format(val=depth_ft))
        steps.append('')
        steps.append(_('Step 3: Calculate volume in cubic feet'))
        steps.append(_('Formula: Volume = Length × Width × Depth'))
        steps.append(_('Volume = {l} ft × {w} ft × {d} ft').format(l=length_ft, w=width_ft, d=depth_ft))
        steps.append(_('Volume = {vol} ft³').format(vol=volume_cf))
        steps.append('')
        if result_unit != 'cubic_feet':
            steps.append(_('Step 4: Convert to desired unit'))
            if result_unit == 'cubic_yards':
                steps.append(_('Cubic Yards = Cubic Feet / 27'))
                steps.append(_('Volume = {cf} ft³ / 27 = {result} yd³').format(cf=volume_cf, result=volume_result))
            elif result_unit == 'cubic_meters':
                steps.append(_('Cubic Meters = Cubic Feet / 35.3147'))
                steps.append(_('Volume = {cf} ft³ / 35.3147 = {result} m³').format(cf=volume_cf, result=volume_result))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Volume = {result} ft³').format(result=volume_result))
        return steps
    
    def _prepare_circular_steps(self, diameter, diameter_unit, depth, depth_unit, volume_result, result_unit, diameter_ft, depth_ft, radius_ft, volume_cf):
        """Prepare step-by-step solution for circular volume calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Diameter: {val} {unit}').format(val=diameter, unit=self._format_unit(diameter_unit)))
        steps.append(_('Depth: {val} {unit}').format(val=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to feet'))
        if diameter_unit != 'feet':
            steps.append(_('Diameter in feet: {val} ft').format(val=diameter_ft))
        if depth_unit != 'feet':
            steps.append(_('Depth in feet: {val} ft').format(val=depth_ft))
        steps.append('')
        steps.append(_('Step 3: Calculate radius'))
        steps.append(_('Radius = Diameter / 2'))
        steps.append(_('Radius = {d} ft / 2 = {r} ft').format(d=diameter_ft, r=radius_ft))
        steps.append('')
        steps.append(_('Step 4: Calculate volume in cubic feet'))
        steps.append(_('Formula: Volume = π × r² × Depth'))
        steps.append(_('Volume = π × ({r} ft)² × {d} ft').format(r=radius_ft, d=depth_ft))
        steps.append(_('Volume = π × {r2} ft² × {d} ft').format(r2=radius_ft**2, d=depth_ft))
        steps.append(_('Volume = {vol} ft³').format(vol=volume_cf))
        steps.append('')
        if result_unit != 'cubic_feet':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=volume_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Volume = {result} ft³').format(result=volume_result))
        return steps
    
    def _prepare_triangular_steps(self, base, base_unit, height, height_unit, depth, depth_unit, volume_result, result_unit, base_ft, height_ft, depth_ft, area_sf, volume_cf):
        """Prepare step-by-step solution for triangular volume calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Base: {val} {unit}').format(val=base, unit=self._format_unit(base_unit)))
        steps.append(_('Height: {val} {unit}').format(val=height, unit=self._format_unit(height_unit)))
        steps.append(_('Depth: {val} {unit}').format(val=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to feet'))
        if base_unit != 'feet':
            steps.append(_('Base in feet: {val} ft').format(val=base_ft))
        if height_unit != 'feet':
            steps.append(_('Height in feet: {val} ft').format(val=height_ft))
        if depth_unit != 'feet':
            steps.append(_('Depth in feet: {val} ft').format(val=depth_ft))
        steps.append('')
        steps.append(_('Step 3: Calculate area in square feet'))
        steps.append(_('Formula: Area = (1/2) × Base × Height'))
        steps.append(_('Area = (1/2) × {b} ft × {h} ft').format(b=base_ft, h=height_ft))
        steps.append(_('Area = {area} ft²').format(area=area_sf))
        steps.append('')
        steps.append(_('Step 4: Calculate volume in cubic feet'))
        steps.append(_('Formula: Volume = Area × Depth'))
        steps.append(_('Volume = {area} ft² × {d} ft').format(area=area_sf, d=depth_ft))
        steps.append(_('Volume = {vol} ft³').format(vol=volume_cf))
        steps.append('')
        if result_unit != 'cubic_feet':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=volume_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Volume = {result} ft³').format(result=volume_result))
        return steps
    
    def _prepare_weight_steps(self, volume, volume_unit, density, weight_result, result_unit, volume_cf, weight_lbs):
        """Prepare step-by-step solution for weight calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Volume: {val} {unit}').format(val=volume, unit=self._format_unit(volume_unit)))
        steps.append(_('Density: {density} lbs/ft³').format(density=density))
        steps.append('')
        steps.append(_('Step 2: Convert volume to cubic feet'))
        if volume_unit != 'cubic_feet':
            steps.append(_('Volume in cubic feet: {val} ft³').format(val=volume_cf))
        steps.append('')
        steps.append(_('Step 3: Calculate weight in pounds'))
        steps.append(_('Formula: Weight = Volume × Density'))
        steps.append(_('Weight = {vol} ft³ × {density} lbs/ft³').format(vol=volume_cf, density=density))
        steps.append(_('Weight = {weight} lbs').format(weight=weight_lbs))
        steps.append('')
        if result_unit != 'pounds':
            steps.append(_('Step 4: Convert to desired unit'))
            if result_unit == 'tons':
                steps.append(_('Tons = Pounds / 2000'))
                steps.append(_('Weight = {lbs} lbs / 2000 = {result} tons').format(lbs=weight_lbs, result=weight_result))
            elif result_unit == 'kilograms':
                steps.append(_('Kilograms = Pounds / 2.20462'))
                steps.append(_('Weight = {lbs} lbs / 2.20462 = {result} kg').format(lbs=weight_lbs, result=weight_result))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Weight = {result} lbs').format(result=weight_result))
        return steps
    
    def _prepare_cost_steps(self, volume, volume_unit, price_per_unit, price_unit, total_cost):
        """Prepare step-by-step solution for cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Volume: {val} {unit}').format(val=volume, unit=self._format_unit(volume_unit)))
        steps.append(_('Price per {unit}: ${price}').format(unit=self._format_unit(volume_unit), price=price_per_unit))
        steps.append('')
        steps.append(_('Step 2: Calculate total cost'))
        steps.append(_('Formula: Total Cost = Volume × Price per Unit'))
        steps.append(_('Total Cost = {vol} {unit} × ${price}/{unit}').format(vol=volume, unit=self._format_unit(volume_unit), price=price_per_unit))
        steps.append(_('Total Cost = ${cost}').format(cost=total_cost))
        return steps
    
    def _prepare_coverage_steps(self, volume, volume_unit, depth, depth_unit, area_result, result_unit, volume_cf, depth_ft, area_sf):
        """Prepare step-by-step solution for coverage calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Volume: {val} {unit}').format(val=volume, unit=self._format_unit(volume_unit)))
        steps.append(_('Depth: {val} {unit}').format(val=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if volume_unit != 'cubic_feet':
            steps.append(_('Volume in cubic feet: {val} ft³').format(val=volume_cf))
        if depth_unit != 'feet':
            steps.append(_('Depth in feet: {val} ft').format(val=depth_ft))
        steps.append('')
        steps.append(_('Step 3: Calculate coverage area in square feet'))
        steps.append(_('Formula: Area = Volume / Depth'))
        steps.append(_('Area = {vol} ft³ / {d} ft').format(vol=volume_cf, d=depth_ft))
        steps.append(_('Area = {area} ft²').format(area=area_sf))
        steps.append('')
        if result_unit != 'square_feet':
            steps.append(_('Step 4: Convert to desired unit'))
            if result_unit == 'square_yards':
                steps.append(_('Square Yards = Square Feet / 9'))
                steps.append(_('Area = {sf} ft² / 9 = {result} yd²').format(sf=area_sf, result=area_result))
            elif result_unit == 'square_meters':
                steps.append(_('Square Meters = Square Feet / 10.7639'))
                steps.append(_('Area = {sf} ft² / 10.7639 = {result} m²').format(sf=area_sf, result=area_result))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Coverage Area = {result} ft²').format(result=area_result))
        return steps
    
    def _prepare_convert_volume_steps(self, value, from_unit, to_unit, result, cubic_feet_value):
        """Prepare step-by-step solution for volume unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Volume: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'cubic_feet':
            steps.append(_('Step 2: Convert to cubic feet'))
            if from_unit == 'cubic_yards':
                steps.append(_('Cubic Feet = Cubic Yards × 27'))
                steps.append(_('Cubic Feet = {val} yd³ × 27 = {cf} ft³').format(val=value, cf=cubic_feet_value))
            elif from_unit == 'cubic_meters':
                steps.append(_('Cubic Feet = Cubic Meters × 35.3147'))
                steps.append(_('Cubic Feet = {val} m³ × 35.3147 = {cf} ft³').format(val=value, cf=cubic_feet_value))
            steps.append('')
        if to_unit != 'cubic_feet':
            steps.append(_('Step 3: Convert from cubic feet to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'cubic_yards':
                steps.append(_('Cubic Yards = Cubic Feet / 27'))
                steps.append(_('Cubic Yards = {cf} ft³ / 27 = {result} yd³').format(cf=cubic_feet_value, result=result))
            elif to_unit == 'cubic_meters':
                steps.append(_('Cubic Meters = Cubic Feet / 35.3147'))
                steps.append(_('Cubic Meters = {cf} ft³ / 35.3147 = {result} m³').format(cf=cubic_feet_value, result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Volume = {result} ft³').format(result=result))
        return steps
    
    def _prepare_convert_weight_steps(self, value, from_unit, to_unit, result, pounds_value):
        """Prepare step-by-step solution for weight unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Weight: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'pounds':
            steps.append(_('Step 2: Convert to pounds'))
            if from_unit == 'tons':
                steps.append(_('Pounds = Tons × 2000'))
                steps.append(_('Pounds = {val} tons × 2000 = {lbs} lbs').format(val=value, lbs=pounds_value))
            elif from_unit == 'kilograms':
                steps.append(_('Pounds = Kilograms × 2.20462'))
                steps.append(_('Pounds = {val} kg × 2.20462 = {lbs} lbs').format(val=value, lbs=pounds_value))
            steps.append('')
        if to_unit != 'pounds':
            steps.append(_('Step 3: Convert from pounds to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'tons':
                steps.append(_('Tons = Pounds / 2000'))
                steps.append(_('Tons = {lbs} lbs / 2000 = {result} tons').format(lbs=pounds_value, result=result))
            elif to_unit == 'kilograms':
                steps.append(_('Kilograms = Pounds / 2.20462'))
                steps.append(_('Kilograms = {lbs} lbs / 2.20462 = {result} kg').format(lbs=pounds_value, result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Weight = {result} lbs').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_rectangular_chart_data(self, length_ft, width_ft, depth_ft, volume_cf):
        """Prepare chart data for rectangular volume calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Length (ft)'), _('Width (ft)'), _('Depth (ft)'), _('Volume (ft³)')],
                    'datasets': [{
                        'label': _('Dimensions'),
                        'data': [length_ft, width_ft, depth_ft, volume_cf],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
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
                            'text': _('Rectangular Gravel Volume Calculation')
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
            return {'rectangular_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_circular_chart_data(self, diameter_ft, depth_ft, volume_cf):
        """Prepare chart data for circular volume calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Diameter (ft)'), _('Depth (ft)'), _('Volume (ft³)')],
                    'datasets': [{
                        'label': _('Dimensions'),
                        'data': [diameter_ft, depth_ft, volume_cf],
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
                            'text': _('Circular Gravel Volume Calculation')
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
            return {'circular_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_triangular_chart_data(self, base_ft, height_ft, depth_ft, volume_cf):
        """Prepare chart data for triangular volume calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Base (ft)'), _('Height (ft)'), _('Depth (ft)'), _('Volume (ft³)')],
                    'datasets': [{
                        'label': _('Dimensions'),
                        'data': [base_ft, height_ft, depth_ft, volume_cf],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(139, 92, 246, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
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
                            'text': _('Triangular Gravel Volume Calculation')
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
            return {'triangular_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_weight_chart_data(self, volume_cf, density, weight_lbs):
        """Prepare chart data for weight calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Volume (ft³)'), _('Density (lbs/ft³)'), _('Weight (lbs)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [volume_cf, density, weight_lbs],
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
                            'text': _('Gravel Weight Calculation')
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
            return {'weight_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_cost_chart_data(self, volume, price_per_unit, total_cost):
        """Prepare chart data for cost calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Volume'), _('Price/Unit'), _('Total Cost')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [volume, price_per_unit, total_cost],
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
                            'text': _('Gravel Cost Calculation')
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
            return {'cost_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_coverage_chart_data(self, volume_cf, depth_ft, area_sf):
        """Prepare chart data for coverage calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Volume (ft³)'), _('Depth (ft)'), _('Coverage Area (ft²)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [volume_cf, depth_ft, area_sf],
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
                            'text': _('Gravel Coverage Calculation')
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
            return {'coverage_chart': chart_config}
        except Exception as e:
            return None
