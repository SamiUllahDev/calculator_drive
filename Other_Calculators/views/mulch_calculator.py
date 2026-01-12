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
class MulchCalculator(View):
    """
    Professional Mulch Calculator with Comprehensive Features
    
    This calculator provides mulch calculations with:
    - Calculate mulch needed for rectangular areas
    - Calculate mulch needed for circular areas
    - Calculate mulch needed for triangular areas
    - Calculate coverage area from volume
    - Calculate weight from volume
    - Calculate cost from volume/weight
    - Unit conversions
    
    Features:
    - Supports multiple area shapes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/mulch_calculator.html'
    
    # Length conversion factors (to meters)
    LENGTH_CONVERSIONS = {
        'meters': 1.0,
        'feet': 0.3048,  # 1 ft = 0.3048 m
        'yards': 0.9144,  # 1 yd = 0.9144 m
        'inches': 0.0254,  # 1 in = 0.0254 m
        'centimeters': 0.01,  # 1 cm = 0.01 m
    }
    
    # Volume conversion factors (to cubic meters)
    VOLUME_CONVERSIONS = {
        'cubic_meters': 1.0,
        'cubic_feet': 0.0283168,  # 1 ft³ = 0.0283168 m³
        'cubic_yards': 0.764555,  # 1 yd³ = 0.764555 m³
        'cubic_inches': 0.0000163871,  # 1 in³ = 0.0000163871 m³
        'liters': 0.001,  # 1 L = 0.001 m³
        'gallons_us': 0.00378541,  # 1 US gal = 0.00378541 m³
    }
    
    # Area conversion factors (to square meters)
    AREA_CONVERSIONS = {
        'square_meters': 1.0,
        'square_feet': 0.092903,  # 1 ft² = 0.092903 m²
        'square_yards': 0.836127,  # 1 yd² = 0.836127 m²
        'square_inches': 0.00064516,  # 1 in² = 0.00064516 m²
        'acres': 4046.86,  # 1 acre = 4046.86 m²
    }
    
    # Weight conversion factors (to kilograms)
    WEIGHT_CONVERSIONS = {
        'kilograms': 1.0,
        'pounds': 0.453592,  # 1 lb = 0.453592 kg
        'tons': 1000.0,  # 1 metric ton = 1000 kg
        'us_tons': 907.185,  # 1 US ton = 907.185 kg
    }
    
    # Typical mulch density (kg/m³) - varies by type
    MULCH_DENSITY = {
        'wood_chips': 400.0,  # kg/m³
        'bark_mulch': 350.0,
        'straw': 100.0,
        'compost': 600.0,
        'rubber': 200.0,
        'stone': 1600.0,
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'meters': 'm',
            'feet': 'ft',
            'yards': 'yd',
            'inches': 'in',
            'centimeters': 'cm',
            'cubic_meters': 'm³',
            'cubic_feet': 'ft³',
            'cubic_yards': 'yd³',
            'cubic_inches': 'in³',
            'liters': 'L',
            'gallons_us': 'US gal',
            'square_meters': 'm²',
            'square_feet': 'ft²',
            'square_yards': 'yd²',
            'square_inches': 'in²',
            'acres': 'acres',
            'kilograms': 'kg',
            'pounds': 'lbs',
            'tons': 'tons',
            'us_tons': 'US tons',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Mulch Calculator'),
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
            elif calc_type == 'coverage_from_volume':
                return self._calculate_coverage_from_volume(data)
            elif calc_type == 'weight_from_volume':
                return self._calculate_weight_from_volume(data)
            elif calc_type == 'cost_calculation':
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
    
    def _calculate_rectangular(self, data):
        """Calculate mulch needed for rectangular area"""
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
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'cubic_yards')
            
            # Validate units
            if length_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid length unit.')
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
            if length <= 0 or width <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Length and width must be greater than zero.')
                }, status=400)
            
            if depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth must be greater than zero.')
                }, status=400)
            
            # Convert to base units (meters)
            length_m = float(length * self.LENGTH_CONVERSIONS[length_unit])
            width_m = float(width * self.LENGTH_CONVERSIONS[length_unit])
            depth_m = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate volume: V = L × W × D
            volume_m3 = float(np.multiply(np.multiply(length_m, width_m), depth_m))
            
            # Convert to result unit
            result = float(np.divide(volume_m3, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_rectangular_steps(length, length_unit, width, depth, depth_unit, length_m, width_m, depth_m, volume_m3, result, result_unit)
            
            chart_data = self._prepare_rectangular_chart_data(length_m, width_m, depth_m, volume_m3)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'rectangular',
                'length': length,
                'width': width,
                'depth': depth,
                'length_unit': length_unit,
                'depth_unit': depth_unit,
                'volume': round(result, 4),
                'result_unit': result_unit,
                'volume_m3': round(volume_m3, 6),
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
                'error': _('Error calculating mulch: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_circular(self, data):
        """Calculate mulch needed for circular area"""
        try:
            if 'radius' not in data or data.get('radius') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Radius is required.')
                }, status=400)
            
            if 'depth' not in data or data.get('depth') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth is required.')
                }, status=400)
            
            try:
                radius = float(data.get('radius', 0))
                depth = float(data.get('depth', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            radius_unit = data.get('radius_unit', 'feet')
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'cubic_yards')
            
            # Validate units
            if radius_unit not in self.LENGTH_CONVERSIONS or depth_unit not in self.LENGTH_CONVERSIONS:
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
            if radius <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Radius must be greater than zero.')
                }, status=400)
            
            if depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth must be greater than zero.')
                }, status=400)
            
            # Convert to base units (meters)
            radius_m = float(radius * self.LENGTH_CONVERSIONS[radius_unit])
            depth_m = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate volume: V = π × r² × D
            area_m2 = float(np.multiply(np.pi, np.multiply(radius_m, radius_m)))
            volume_m3 = float(np.multiply(area_m2, depth_m))
            
            # Convert to result unit
            result = float(np.divide(volume_m3, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_circular_steps(radius, radius_unit, depth, depth_unit, radius_m, depth_m, area_m2, volume_m3, result, result_unit)
            
            chart_data = self._prepare_circular_chart_data(radius_m, depth_m, volume_m3)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'circular',
                'radius': radius,
                'depth': depth,
                'radius_unit': radius_unit,
                'depth_unit': depth_unit,
                'volume': round(result, 4),
                'result_unit': result_unit,
                'volume_m3': round(volume_m3, 6),
                'area_m2': round(area_m2, 6),
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
                'error': _('Error calculating mulch: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_triangular(self, data):
        """Calculate mulch needed for triangular area"""
        try:
            if 'base' not in data or data.get('base') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Base is required.')
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
            depth_unit = data.get('depth_unit', 'inches')
            result_unit = data.get('result_unit', 'cubic_yards')
            
            # Validate units
            if base_unit not in self.LENGTH_CONVERSIONS or depth_unit not in self.LENGTH_CONVERSIONS:
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
            if base <= 0 or height <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Base and height must be greater than zero.')
                }, status=400)
            
            if depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth must be greater than zero.')
                }, status=400)
            
            # Convert to base units (meters)
            base_m = float(base * self.LENGTH_CONVERSIONS[base_unit])
            height_m = float(height * self.LENGTH_CONVERSIONS[base_unit])
            depth_m = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate volume: V = (1/2 × B × H) × D
            area_m2 = float(np.multiply(0.5, np.multiply(base_m, height_m)))
            volume_m3 = float(np.multiply(area_m2, depth_m))
            
            # Convert to result unit
            result = float(np.divide(volume_m3, self.VOLUME_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_triangular_steps(base, base_unit, height, depth, depth_unit, base_m, height_m, depth_m, area_m2, volume_m3, result, result_unit)
            
            chart_data = self._prepare_triangular_chart_data(base_m, height_m, depth_m, volume_m3)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'triangular',
                'base': base,
                'height': height,
                'depth': depth,
                'base_unit': base_unit,
                'depth_unit': depth_unit,
                'volume': round(result, 4),
                'result_unit': result_unit,
                'volume_m3': round(volume_m3, 6),
                'area_m2': round(area_m2, 6),
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
                'error': _('Error calculating mulch: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_coverage_from_volume(self, data):
        """Calculate coverage area from volume and depth"""
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
            if volume_unit not in self.VOLUME_CONVERSIONS or depth_unit not in self.LENGTH_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if result_unit not in self.AREA_CONVERSIONS:
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
            
            if depth <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Depth must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            volume_m3 = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            depth_m = float(depth * self.LENGTH_CONVERSIONS[depth_unit])
            
            # Calculate area: A = V / D
            area_m2 = float(np.divide(volume_m3, depth_m))
            
            # Convert to result unit
            result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_coverage_steps(volume, volume_unit, depth, depth_unit, volume_m3, depth_m, area_m2, result, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'coverage_from_volume',
                'volume': volume,
                'volume_unit': volume_unit,
                'depth': depth,
                'depth_unit': depth_unit,
                'coverage': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
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
    
    def _calculate_weight_from_volume(self, data):
        """Calculate weight from volume and mulch type"""
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
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            volume_unit = data.get('volume_unit', 'cubic_yards')
            mulch_type = data.get('mulch_type', 'wood_chips')
            result_unit = data.get('result_unit', 'pounds')
            
            # Validate units
            if volume_unit not in self.VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid volume unit.')
                }, status=400)
            
            if mulch_type not in self.MULCH_DENSITY:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid mulch type.')
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
            
            # Convert to base units
            volume_m3 = float(volume * self.VOLUME_CONVERSIONS[volume_unit])
            density_kg_m3 = self.MULCH_DENSITY[mulch_type]
            
            # Calculate weight: W = V × D
            weight_kg = float(np.multiply(volume_m3, density_kg_m3))
            
            # Convert to result unit
            result = float(np.divide(weight_kg, self.WEIGHT_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_weight_steps(volume, volume_unit, mulch_type, density_kg_m3, volume_m3, weight_kg, result, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'weight_from_volume',
                'volume': volume,
                'volume_unit': volume_unit,
                'mulch_type': mulch_type,
                'density': density_kg_m3,
                'weight': round(result, 2),
                'result_unit': result_unit,
                'weight_kg': round(weight_kg, 2),
                'step_by_step': steps,
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
        """Calculate cost from volume/weight and price"""
        try:
            calc_mode = data.get('cost_mode', 'from_volume')
            
            if calc_mode == 'from_volume':
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
                currency = data.get('currency', 'usd')
                
                # Validate
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
                
                steps = self._prepare_cost_volume_steps(volume, volume_unit, price_per_unit, price_unit, total_cost, currency)
                
                return JsonResponse({
                    'success': True,
                    'calc_type': 'cost_calculation',
                    'cost_mode': 'from_volume',
                    'volume': volume,
                    'volume_unit': volume_unit,
                    'price_per_unit': price_per_unit,
                    'price_unit': price_unit,
                    'total_cost': round(total_cost, 2),
                    'currency': currency,
                    'step_by_step': steps,
                })
            
            else:  # from_weight
                if 'weight' not in data or data.get('weight') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Weight is required.')
                    }, status=400)
                
                if 'price_per_unit' not in data or data.get('price_per_unit') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Price per unit is required.')
                    }, status=400)
                
                try:
                    weight = float(data.get('weight', 0))
                    price_per_unit = float(data.get('price_per_unit', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                weight_unit = data.get('weight_unit', 'pounds')
                price_unit = data.get('price_unit', 'per_pound')
                currency = data.get('currency', 'usd')
                
                # Validate
                if weight <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Weight must be greater than zero.')
                    }, status=400)
                
                if price_per_unit < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Price must be non-negative.')
                    }, status=400)
                
                # Calculate cost
                total_cost = float(np.multiply(weight, price_per_unit))
                
                steps = self._prepare_cost_weight_steps(weight, weight_unit, price_per_unit, price_unit, total_cost, currency)
                
                return JsonResponse({
                    'success': True,
                    'calc_type': 'cost_calculation',
                    'cost_mode': 'from_weight',
                    'weight': weight,
                    'weight_unit': weight_unit,
                    'price_per_unit': price_per_unit,
                    'price_unit': price_unit,
                    'total_cost': round(total_cost, 2),
                    'currency': currency,
                    'step_by_step': steps,
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
    
    # Step-by-step solution preparation methods
    def _prepare_rectangular_steps(self, length, length_unit, width, depth, depth_unit, length_m, width_m, depth_m, volume_m3, result, result_unit):
        """Prepare step-by-step solution for rectangular area"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Length: {length} {unit}').format(length=length, unit=self._format_unit(length_unit)))
        steps.append(_('Width: {width} {unit}').format(width=width, unit=self._format_unit(length_unit)))
        steps.append(_('Depth: {depth} {unit}').format(depth=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Length: {length} m').format(length=length_m))
        steps.append(_('Width: {width} m').format(width=width_m))
        steps.append(_('Depth: {depth} m').format(depth=depth_m))
        steps.append('')
        steps.append(_('Step 3: Calculate volume'))
        steps.append(_('Formula: Volume = Length × Width × Depth'))
        steps.append(_('Volume = {length} m × {width} m × {depth} m').format(length=length_m, width=width_m, depth=depth_m))
        steps.append(_('Volume = {volume} m³').format(volume=volume_m3))
        steps.append('')
        if result_unit != 'cubic_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Volume = {result} m³').format(result=result))
        return steps
    
    def _prepare_circular_steps(self, radius, radius_unit, depth, depth_unit, radius_m, depth_m, area_m2, volume_m3, result, result_unit):
        """Prepare step-by-step solution for circular area"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Radius: {radius} {unit}').format(radius=radius, unit=self._format_unit(radius_unit)))
        steps.append(_('Depth: {depth} {unit}').format(depth=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Radius: {radius} m').format(radius=radius_m))
        steps.append(_('Depth: {depth} m').format(depth=depth_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Formula: Area = π × r²'))
        steps.append(_('Area = π × ({radius} m)²').format(radius=radius_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        steps.append(_('Step 4: Calculate volume'))
        steps.append(_('Formula: Volume = Area × Depth'))
        steps.append(_('Volume = {area} m² × {depth} m').format(area=area_m2, depth=depth_m))
        steps.append(_('Volume = {volume} m³').format(volume=volume_m3))
        steps.append('')
        if result_unit != 'cubic_meters':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Volume = {result} m³').format(result=result))
        return steps
    
    def _prepare_triangular_steps(self, base, base_unit, height, depth, depth_unit, base_m, height_m, depth_m, area_m2, volume_m3, result, result_unit):
        """Prepare step-by-step solution for triangular area"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Base: {base} {unit}').format(base=base, unit=self._format_unit(base_unit)))
        steps.append(_('Height: {height} {unit}').format(height=height, unit=self._format_unit(base_unit)))
        steps.append(_('Depth: {depth} {unit}').format(depth=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Base: {base} m').format(base=base_m))
        steps.append(_('Height: {height} m').format(height=height_m))
        steps.append(_('Depth: {depth} m').format(depth=depth_m))
        steps.append('')
        steps.append(_('Step 3: Calculate area'))
        steps.append(_('Formula: Area = (1/2) × Base × Height'))
        steps.append(_('Area = (1/2) × {base} m × {height} m').format(base=base_m, height=height_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        steps.append(_('Step 4: Calculate volume'))
        steps.append(_('Formula: Volume = Area × Depth'))
        steps.append(_('Volume = {area} m² × {depth} m').format(area=area_m2, depth=depth_m))
        steps.append(_('Volume = {volume} m³').format(volume=volume_m3))
        steps.append('')
        if result_unit != 'cubic_meters':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Volume = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Volume = {result} m³').format(result=result))
        return steps
    
    def _prepare_coverage_steps(self, volume, volume_unit, depth, depth_unit, volume_m3, depth_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for coverage calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append(_('Depth: {depth} {unit}').format(depth=depth, unit=self._format_unit(depth_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Volume: {volume} m³').format(volume=volume_m3))
        steps.append(_('Depth: {depth} m').format(depth=depth_m))
        steps.append('')
        steps.append(_('Step 3: Calculate coverage area'))
        steps.append(_('Formula: Area = Volume / Depth'))
        steps.append(_('Area = {volume} m³ / {depth} m').format(volume=volume_m3, depth=depth_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Coverage Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Coverage Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_weight_steps(self, volume, volume_unit, mulch_type, density_kg_m3, volume_m3, weight_kg, result, result_unit):
        """Prepare step-by-step solution for weight calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append(_('Mulch Type: {type}').format(type=mulch_type.replace('_', ' ').title()))
        steps.append('')
        steps.append(_('Step 2: Convert volume to cubic meters'))
        steps.append(_('Volume: {volume} m³').format(volume=volume_m3))
        steps.append('')
        steps.append(_('Step 3: Get density for mulch type'))
        steps.append(_('Density: {density} kg/m³').format(density=density_kg_m3))
        steps.append('')
        steps.append(_('Step 4: Calculate weight'))
        steps.append(_('Formula: Weight = Volume × Density'))
        steps.append(_('Weight = {volume} m³ × {density} kg/m³').format(volume=volume_m3, density=density_kg_m3))
        steps.append(_('Weight = {weight} kg').format(weight=weight_kg))
        steps.append('')
        if result_unit != 'kilograms':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Weight = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Weight = {result} kg').format(result=result))
        return steps
    
    def _prepare_cost_volume_steps(self, volume, volume_unit, price_per_unit, price_unit, total_cost, currency):
        """Prepare step-by-step solution for cost from volume"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Volume: {volume} {unit}').format(volume=volume, unit=self._format_unit(volume_unit)))
        steps.append(_('Price: {price} {currency}/{unit}').format(price=price_per_unit, currency=currency.upper(), unit=self._format_unit(volume_unit)))
        steps.append('')
        steps.append(_('Step 2: Calculate total cost'))
        steps.append(_('Formula: Total Cost = Volume × Price per Unit'))
        steps.append(_('Total Cost = {volume} {unit} × {price} {currency}/{unit}').format(volume=volume, unit=self._format_unit(volume_unit), price=price_per_unit, currency=currency.upper()))
        steps.append(_('Total Cost = {cost} {currency}').format(cost=total_cost, currency=currency.upper()))
        return steps
    
    def _prepare_cost_weight_steps(self, weight, weight_unit, price_per_unit, price_unit, total_cost, currency):
        """Prepare step-by-step solution for cost from weight"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Weight: {weight} {unit}').format(weight=weight, unit=self._format_unit(weight_unit)))
        steps.append(_('Price: {price} {currency}/{unit}').format(price=price_per_unit, currency=currency.upper(), unit=self._format_unit(weight_unit)))
        steps.append('')
        steps.append(_('Step 2: Calculate total cost'))
        steps.append(_('Formula: Total Cost = Weight × Price per Unit'))
        steps.append(_('Total Cost = {weight} {unit} × {price} {currency}/{unit}').format(weight=weight, unit=self._format_unit(weight_unit), price=price_per_unit, currency=currency.upper()))
        steps.append(_('Total Cost = {cost} {currency}').format(cost=total_cost, currency=currency.upper()))
        return steps
    
    # Chart data preparation methods
    def _prepare_rectangular_chart_data(self, length_m, width_m, depth_m, volume_m3):
        """Prepare chart data for rectangular calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Length (m)'), _('Width (m)'), _('Depth (m)'), _('Volume (m³)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [length_m, width_m, depth_m, volume_m3],
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
                            'text': _('Rectangular Mulch Calculation')
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
    
    def _prepare_circular_chart_data(self, radius_m, depth_m, volume_m3):
        """Prepare chart data for circular calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Radius (m)'), _('Depth (m)'), _('Volume (m³)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [radius_m, depth_m, volume_m3],
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
                            'text': _('Circular Mulch Calculation')
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
    
    def _prepare_triangular_chart_data(self, base_m, height_m, depth_m, volume_m3):
        """Prepare chart data for triangular calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Base (m)'), _('Height (m)'), _('Depth (m)'), _('Volume (m³)')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [base_m, height_m, depth_m, volume_m3],
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
                            'text': _('Triangular Mulch Calculation')
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
