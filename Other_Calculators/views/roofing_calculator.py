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
class RoofingCalculator(View):
    """
    Professional Roofing Calculator with Comprehensive Features
    
    This calculator provides roofing calculations with:
    - Calculate roof area for different shapes
    - Calculate materials needed (shingles, tiles, etc.)
    - Calculate roof pitch/slope
    - Calculate cost estimates
    - Calculate waste factor
    
    Features:
    - Supports multiple roof shapes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/roofing_calculator.html'
    
    # Length conversion factors (to meters)
    LENGTH_CONVERSIONS = {
        'meters': 1.0,
        'feet': 0.3048,  # 1 ft = 0.3048 m
        'inches': 0.0254,  # 1 in = 0.0254 m
    }
    
    # Area conversion factors (to square meters)
    AREA_CONVERSIONS = {
        'square_meters': 1.0,
        'square_feet': 0.092903,  # 1 ft² = 0.092903 m²
        'square_yards': 0.836127,  # 1 yd² = 0.836127 m²
        'square_inches': 0.00064516,  # 1 in² = 0.00064516 m²
    }
    
    # Material coverage (square feet per bundle/square)
    MATERIAL_COVERAGE = {
        'asphalt_shingles': 33.33,  # 3 bundles per square (100 sq ft)
        'wood_shingles': 25.0,  # 4 bundles per square
        'slate_tiles': 100.0,  # 1 square per square
        'clay_tiles': 100.0,  # 1 square per square
        'metal_roofing': 100.0,  # 1 square per square
        'rubber_roofing': 100.0,  # 1 square per square
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'meters': 'm',
            'feet': 'ft',
            'inches': 'in',
            'square_meters': 'm²',
            'square_feet': 'ft²',
            'square_yards': 'yd²',
            'square_inches': 'in²',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Roofing Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'area')
            
            if calc_type == 'area':
                return self._calculate_area(data)
            elif calc_type == 'materials':
                return self._calculate_materials(data)
            elif calc_type == 'pitch':
                return self._calculate_pitch(data)
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
    
    def _calculate_area(self, data):
        """Calculate roof area for different shapes"""
        try:
            roof_shape = data.get('roof_shape', 'gable')
            
            if roof_shape == 'gable':
                # Simple gable roof: 2 rectangular sides
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
                
                if 'pitch' not in data or data.get('pitch') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Roof pitch is required.')
                    }, status=400)
                
                try:
                    length = float(data.get('length', 0))
                    width = float(data.get('width', 0))
                    pitch = float(data.get('pitch', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                length_unit = data.get('length_unit', 'feet')
                result_unit = data.get('result_unit', 'square_feet')
                
                # Validate
                if length <= 0 or width <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Length and width must be greater than zero.')
                    }, status=400)
                
                if pitch < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Pitch must be non-negative.')
                    }, status=400)
                
                # Convert to base units
                length_m = float(length * self.LENGTH_CONVERSIONS[length_unit])
                width_m = float(width * self.LENGTH_CONVERSIONS[length_unit])
                
                # Calculate roof area with pitch
                # Pitch multiplier = sqrt(1 + (pitch/12)²)
                pitch_multiplier = float(np.sqrt(1.0 + np.multiply(np.divide(pitch, 12.0), np.divide(pitch, 12.0))))
                
                # Area = length × width × pitch_multiplier (for 2 sides)
                area_m2 = float(np.multiply(np.multiply(length_m, width_m), pitch_multiplier))
                
                # Convert to result unit
                result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
                
                steps = self._prepare_gable_area_steps(length, length_unit, width, pitch, length_m, width_m, pitch_multiplier, area_m2, result, result_unit)
                
            elif roof_shape == 'hip':
                # Hip roof: 4 triangular sides
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
                
                if 'pitch' not in data or data.get('pitch') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Roof pitch is required.')
                    }, status=400)
                
                try:
                    length = float(data.get('length', 0))
                    width = float(data.get('width', 0))
                    pitch = float(data.get('pitch', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                length_unit = data.get('length_unit', 'feet')
                result_unit = data.get('result_unit', 'square_feet')
                
                # Validate
                if length <= 0 or width <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Length and width must be greater than zero.')
                    }, status=400)
                
                # Convert to base units
                length_m = float(length * self.LENGTH_CONVERSIONS[length_unit])
                width_m = float(width * self.LENGTH_CONVERSIONS[length_unit])
                
                # Calculate hip roof area (more complex, simplified calculation)
                pitch_multiplier = float(np.sqrt(1.0 + np.multiply(np.divide(pitch, 12.0), np.divide(pitch, 12.0))))
                area_m2 = float(np.multiply(np.multiply(length_m, width_m), pitch_multiplier))
                
                # Convert to result unit
                result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
                
                steps = self._prepare_hip_area_steps(length, length_unit, width, pitch, length_m, width_m, pitch_multiplier, area_m2, result, result_unit)
                
            else:  # flat
                # Flat roof: simple rectangle
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
                
                try:
                    length = float(data.get('length', 0))
                    width = float(data.get('width', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid input type. Please enter numeric values.')
                    }, status=400)
                
                length_unit = data.get('length_unit', 'feet')
                result_unit = data.get('result_unit', 'square_feet')
                
                # Validate
                if length <= 0 or width <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Length and width must be greater than zero.')
                    }, status=400)
                
                # Convert to base units
                length_m = float(length * self.LENGTH_CONVERSIONS[length_unit])
                width_m = float(width * self.LENGTH_CONVERSIONS[length_unit])
                
                # Calculate flat roof area
                area_m2 = float(np.multiply(length_m, width_m))
                
                # Convert to result unit
                result = float(np.divide(area_m2, self.AREA_CONVERSIONS[result_unit]))
                
                steps = self._prepare_flat_area_steps(length, length_unit, width, length_m, width_m, area_m2, result, result_unit)
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result) or result <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            chart_data = self._prepare_area_chart_data(area_m2, roof_shape)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'area',
                'roof_shape': roof_shape,
                'area': round(result, 4),
                'result_unit': result_unit,
                'area_m2': round(area_m2, 6),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating area: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_materials(self, data):
        """Calculate materials needed for roofing"""
        try:
            if 'area' not in data or data.get('area') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Roof area is required.')
                }, status=400)
            
            try:
                area = float(data.get('area', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            area_unit = data.get('area_unit', 'square_feet')
            material_type = data.get('material_type', 'asphalt_shingles')
            waste_factor = float(data.get('waste_factor', 10))  # Default 10% waste
            
            # Validate
            if area <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Area must be greater than zero.')
                }, status=400)
            
            if material_type not in self.MATERIAL_COVERAGE:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid material type.')
                }, status=400)
            
            if waste_factor < 0 or waste_factor > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Waste factor must be between 0 and 50 percent.')
                }, status=400)
            
            # Convert area to square feet
            area_ft2 = float(area * self.AREA_CONVERSIONS[area_unit] / self.AREA_CONVERSIONS['square_feet'])
            
            # Calculate materials needed
            coverage = self.MATERIAL_COVERAGE[material_type]
            area_with_waste = float(area_ft2 * (1.0 + waste_factor / 100.0))
            bundles_needed = float(np.ceil(np.divide(area_with_waste, coverage)))
            squares_needed = float(np.divide(area_with_waste, 100.0))  # 1 square = 100 sq ft
            
            steps = self._prepare_materials_steps(area, area_unit, area_ft2, material_type, coverage, waste_factor, area_with_waste, bundles_needed, squares_needed)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'materials',
                'area': area,
                'area_unit': area_unit,
                'material_type': material_type,
                'waste_factor': waste_factor,
                'bundles_needed': int(bundles_needed),
                'squares_needed': round(squares_needed, 2),
                'area_with_waste': round(area_with_waste, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating materials: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_pitch(self, data):
        """Calculate roof pitch from rise and run"""
        try:
            if 'rise' not in data or data.get('rise') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Rise is required.')
                }, status=400)
            
            if 'run' not in data or data.get('run') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Run is required.')
                }, status=400)
            
            try:
                rise = float(data.get('rise', 0))
                run = float(data.get('run', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validate
            if rise < 0 or run <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Rise must be non-negative and run must be greater than zero.')
                }, status=400)
            
            # Calculate pitch (rise over 12 inches of run)
            pitch = float(np.multiply(np.divide(rise, run), 12.0))
            
            # Calculate angle in degrees
            angle_rad = float(np.arctan(np.divide(rise, run)))
            angle_deg = float(np.multiply(angle_rad, 180.0 / np.pi))
            
            # Calculate slope as percentage
            slope_percent = float(np.multiply(np.divide(rise, run), 100.0))
            
            steps = self._prepare_pitch_steps(rise, run, pitch, angle_deg, slope_percent)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'pitch',
                'rise': rise,
                'run': run,
                'pitch': round(pitch, 2),
                'angle': round(angle_deg, 2),
                'slope_percent': round(slope_percent, 2),
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating pitch: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_cost(self, data):
        """Calculate roofing cost"""
        try:
            if 'area' not in data or data.get('area') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Roof area is required.')
                }, status=400)
            
            if 'price_per_square' not in data or data.get('price_per_square') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Price per square is required.')
                }, status=400)
            
            try:
                area = float(data.get('area', 0))
                price_per_square = float(data.get('price_per_square', 0))
                labor_cost = float(data.get('labor_cost', 0))
                waste_factor = float(data.get('waste_factor', 10))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            area_unit = data.get('area_unit', 'square_feet')
            currency = data.get('currency', 'usd')
            
            # Validate
            if area <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Area must be greater than zero.')
                }, status=400)
            
            if price_per_square < 0 or labor_cost < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Prices must be non-negative.')
                }, status=400)
            
            # Convert area to square feet
            area_ft2 = float(area * self.AREA_CONVERSIONS[area_unit] / self.AREA_CONVERSIONS['square_feet'])
            
            # Calculate squares needed (with waste)
            area_with_waste = float(area_ft2 * (1.0 + waste_factor / 100.0))
            squares_needed = float(np.divide(area_with_waste, 100.0))
            
            # Calculate costs
            material_cost = float(np.multiply(squares_needed, price_per_square))
            total_cost = float(np.add(material_cost, labor_cost))
            
            steps = self._prepare_cost_steps(area, area_unit, area_ft2, waste_factor, area_with_waste, squares_needed, price_per_square, labor_cost, material_cost, total_cost, currency)
            
            chart_data = self._prepare_cost_chart_data(material_cost, labor_cost, total_cost)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'cost',
                'area': area,
                'area_unit': area_unit,
                'price_per_square': price_per_square,
                'labor_cost': labor_cost,
                'waste_factor': waste_factor,
                'squares_needed': round(squares_needed, 2),
                'material_cost': round(material_cost, 2),
                'total_cost': round(total_cost, 2),
                'currency': currency,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating cost: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_gable_area_steps(self, length, length_unit, width, pitch, length_m, width_m, pitch_multiplier, area_m2, result, result_unit):
        """Prepare step-by-step solution for gable roof area"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Length: {length} {unit}').format(length=length, unit=self._format_unit(length_unit)))
        steps.append(_('Width: {width} {unit}').format(width=width, unit=self._format_unit(length_unit)))
        steps.append(_('Pitch: {pitch} in 12').format(pitch=pitch))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Length: {length} m').format(length=length_m))
        steps.append(_('Width: {width} m').format(width=width_m))
        steps.append('')
        steps.append(_('Step 3: Calculate pitch multiplier'))
        steps.append(_('Pitch Multiplier = √(1 + (pitch/12)²)'))
        steps.append(_('Pitch Multiplier = √(1 + ({pitch}/12)²)').format(pitch=pitch))
        steps.append(_('Pitch Multiplier = {mult}').format(mult=round(pitch_multiplier, 4)))
        steps.append('')
        steps.append(_('Step 4: Calculate roof area'))
        steps.append(_('Area = Length × Width × Pitch Multiplier'))
        steps.append(_('Area = {length} m × {width} m × {mult}').format(length=length_m, width=width_m, mult=round(pitch_multiplier, 4)))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_hip_area_steps(self, length, length_unit, width, pitch, length_m, width_m, pitch_multiplier, area_m2, result, result_unit):
        """Prepare step-by-step solution for hip roof area"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Length: {length} {unit}').format(length=length, unit=self._format_unit(length_unit)))
        steps.append(_('Width: {width} {unit}').format(width=width, unit=self._format_unit(length_unit)))
        steps.append(_('Pitch: {pitch} in 12').format(pitch=pitch))
        steps.append('')
        steps.append(_('Step 2: Calculate pitch multiplier'))
        steps.append(_('Pitch Multiplier = √(1 + (pitch/12)²)'))
        steps.append(_('Pitch Multiplier = {mult}').format(mult=round(pitch_multiplier, 4)))
        steps.append('')
        steps.append(_('Step 3: Calculate roof area (hip roof)'))
        steps.append(_('Area = Length × Width × Pitch Multiplier'))
        steps.append(_('Area = {length} m × {width} m × {mult}').format(length=length_m, width=width_m, mult=round(pitch_multiplier, 4)))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_flat_area_steps(self, length, length_unit, width, length_m, width_m, area_m2, result, result_unit):
        """Prepare step-by-step solution for flat roof area"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Length: {length} {unit}').format(length=length, unit=self._format_unit(length_unit)))
        steps.append(_('Width: {width} {unit}').format(width=width, unit=self._format_unit(length_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (meters)'))
        steps.append(_('Length: {length} m').format(length=length_m))
        steps.append(_('Width: {width} m').format(width=width_m))
        steps.append('')
        steps.append(_('Step 3: Calculate roof area'))
        steps.append(_('Area = Length × Width'))
        steps.append(_('Area = {length} m × {width} m').format(length=length_m, width=width_m))
        steps.append(_('Area = {area} m²').format(area=area_m2))
        steps.append('')
        if result_unit != 'square_meters':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Area = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Area = {result} m²').format(result=result))
        return steps
    
    def _prepare_materials_steps(self, area, area_unit, area_ft2, material_type, coverage, waste_factor, area_with_waste, bundles_needed, squares_needed):
        """Prepare step-by-step solution for materials calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Roof Area: {area} {unit}').format(area=area, unit=self._format_unit(area_unit)))
        steps.append(_('Material Type: {type}').format(type=material_type.replace('_', ' ').title()))
        steps.append(_('Waste Factor: {waste}%').format(waste=waste_factor))
        steps.append('')
        steps.append(_('Step 2: Convert area to square feet'))
        steps.append(_('Area: {area} ft²').format(area=area_ft2))
        steps.append('')
        steps.append(_('Step 3: Add waste factor'))
        steps.append(_('Area with Waste = Area × (1 + Waste Factor / 100)'))
        steps.append(_('Area with Waste = {area} × (1 + {waste} / 100)').format(area=area_ft2, waste=waste_factor))
        steps.append(_('Area with Waste = {area} ft²').format(area=area_with_waste))
        steps.append('')
        steps.append(_('Step 4: Calculate materials needed'))
        steps.append(_('Coverage per bundle: {coverage} ft²').format(coverage=coverage))
        steps.append(_('Bundles Needed = Area with Waste / Coverage'))
        steps.append(_('Bundles Needed = {area} / {coverage} = {bundles} bundles').format(area=area_with_waste, coverage=coverage, bundles=int(bundles_needed)))
        steps.append('')
        steps.append(_('Step 5: Calculate squares'))
        steps.append(_('Squares Needed = Area with Waste / 100'))
        steps.append(_('Squares Needed = {area} / 100 = {squares} squares').format(area=area_with_waste, squares=round(squares_needed, 2)))
        return steps
    
    def _prepare_pitch_steps(self, rise, run, pitch, angle_deg, slope_percent):
        """Prepare step-by-step solution for pitch calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Rise: {rise} inches').format(rise=rise))
        steps.append(_('Run: {run} inches').format(run=run))
        steps.append('')
        steps.append(_('Step 2: Calculate pitch'))
        steps.append(_('Pitch = (Rise / Run) × 12'))
        steps.append(_('Pitch = ({rise} / {run}) × 12').format(rise=rise, run=run))
        steps.append(_('Pitch = {pitch} in 12').format(pitch=round(pitch, 2)))
        steps.append('')
        steps.append(_('Step 3: Calculate angle'))
        steps.append(_('Angle = arctan(Rise / Run)'))
        steps.append(_('Angle = arctan({rise} / {run})').format(rise=rise, run=run))
        steps.append(_('Angle = {angle}°').format(angle=round(angle_deg, 2)))
        steps.append('')
        steps.append(_('Step 4: Calculate slope percentage'))
        steps.append(_('Slope = (Rise / Run) × 100%'))
        steps.append(_('Slope = ({rise} / {run}) × 100%').format(rise=rise, run=run))
        steps.append(_('Slope = {slope}%').format(slope=round(slope_percent, 2)))
        return steps
    
    def _prepare_cost_steps(self, area, area_unit, area_ft2, waste_factor, area_with_waste, squares_needed, price_per_square, labor_cost, material_cost, total_cost, currency):
        """Prepare step-by-step solution for cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Roof Area: {area} {unit}').format(area=area, unit=self._format_unit(area_unit)))
        steps.append(_('Price per Square: {price} {currency}').format(price=price_per_square, currency=currency.upper()))
        steps.append(_('Labor Cost: {cost} {currency}').format(cost=labor_cost, currency=currency.upper()))
        steps.append(_('Waste Factor: {waste}%').format(waste=waste_factor))
        steps.append('')
        steps.append(_('Step 2: Convert area to square feet'))
        steps.append(_('Area: {area} ft²').format(area=area_ft2))
        steps.append('')
        steps.append(_('Step 3: Add waste factor'))
        steps.append(_('Area with Waste = {area} ft²').format(area=area_with_waste))
        steps.append('')
        steps.append(_('Step 4: Calculate squares needed'))
        steps.append(_('Squares = Area with Waste / 100'))
        steps.append(_('Squares = {area} / 100 = {squares} squares').format(area=area_with_waste, squares=round(squares_needed, 2)))
        steps.append('')
        steps.append(_('Step 5: Calculate material cost'))
        steps.append(_('Material Cost = Squares × Price per Square'))
        steps.append(_('Material Cost = {squares} × {price} = {cost} {currency}').format(squares=round(squares_needed, 2), price=price_per_square, cost=round(material_cost, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 6: Calculate total cost'))
        steps.append(_('Total Cost = Material Cost + Labor Cost'))
        steps.append(_('Total Cost = {material} + {labor} = {total} {currency}').format(material=round(material_cost, 2), labor=labor_cost, total=round(total_cost, 2), currency=currency.upper()))
        return steps
    
    # Chart data preparation methods
    def _prepare_area_chart_data(self, area_m2, roof_shape):
        """Prepare chart data for area calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Roof Area')],
                    'datasets': [{
                        'label': _('Area (m²)'),
                        'data': [area_m2],
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
                            'text': _('Roof Area Calculation ({shape})').format(shape=roof_shape.title())
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Area (m²)')
                            }
                        }
                    }
                }
            }
            return {'area_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_cost_chart_data(self, material_cost, labor_cost, total_cost):
        """Prepare chart data for cost calculation"""
        try:
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': [_('Material Cost'), _('Labor Cost')],
                    'datasets': [{
                        'data': [material_cost, labor_cost],
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
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Roofing Cost Breakdown (Total: {total})').format(total=total_cost)
                        }
                    }
                }
            }
            return {'cost_chart': chart_config}
        except Exception as e:
            return None
