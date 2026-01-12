from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ConcreteCalculator(View):
    """
    Professional Concrete Calculator with Comprehensive Features
    
    This calculator provides concrete calculations with:
    - Volume calculations for different shapes (rectangular, circular, column, etc.)
    - Material requirements (cement, sand, aggregate)
    - Unit conversions (cubic feet, cubic yards, cubic meters)
    - Multiple concrete mix ratios
    - Cost estimation
    - Step-by-step solutions
    
    Features:
    - Supports multiple measurement units (feet, meters)
    - Handles different concrete shapes
    - Accounts for different mix ratios
    - Provides material breakdown
    - Interactive visualizations
    """
    template_name = 'other_calculators/concrete_calculator.html'
    
    # Conversion factors
    CUBIC_FEET_TO_CUBIC_YARDS = 1 / 27
    CUBIC_FEET_TO_CUBIC_METERS = 0.0283168
    CUBIC_YARDS_TO_CUBIC_METERS = 0.764555
    
    # Standard concrete mix ratios (cement:sand:aggregate)
    MIX_RATIOS = {
        '1:2:4': {'cement': 1, 'sand': 2, 'aggregate': 4, 'total': 7},
        '1:1.5:3': {'cement': 1, 'sand': 1.5, 'aggregate': 3, 'total': 5.5},
        '1:3:6': {'cement': 1, 'sand': 3, 'aggregate': 6, 'total': 10},
        '1:2:3': {'cement': 1, 'sand': 2, 'aggregate': 3, 'total': 6},
        '1:1:2': {'cement': 1, 'sand': 1, 'aggregate': 2, 'total': 4},
    }
    
    # Material densities (per cubic foot)
    CEMENT_DENSITY_CUBIC_FT = 94  # pounds per cubic foot
    SAND_DENSITY_CUBIC_FT = 100   # pounds per cubic foot
    AGGREGATE_DENSITY_CUBIC_FT = 150  # pounds per cubic foot
    
    # Bag sizes
    CEMENT_BAG_SIZE = 94  # pounds per bag
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Concrete Calculator'),
            'features': [
                _('Volume calculations for multiple shapes'),
                _('Material requirements (cement, sand, aggregate)'),
                _('Unit conversions (cubic feet, yards, meters)'),
                _('Multiple concrete mix ratios'),
                _('Cost estimation'),
                _('Step-by-step solutions'),
                _('Interactive visualizations')
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'rectangular_slab')
            
            if calc_type == 'rectangular_slab':
                return self._calculate_rectangular_slab(data)
            elif calc_type == 'circular_slab':
                return self._calculate_circular_slab(data)
            elif calc_type == 'column':
                return self._calculate_column(data)
            elif calc_type == 'footing':
                return self._calculate_footing(data)
            elif calc_type == 'wall':
                return self._calculate_wall(data)
            elif calc_type == 'volume_conversion':
                return self._convert_volume_units(data)
            else:
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('Invalid JSON data.')}, status=400)
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: {error}').format(error=str(e))}, status=400)
        except Exception as e:
            import traceback
            print(f"Concrete Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
    
    def _calculate_rectangular_slab(self, data):
        """Calculate concrete for rectangular slab"""
        try:
            length = float(data.get('length', 0))
            width = float(data.get('width', 0))
            thickness = float(data.get('thickness', 0))
            unit = data.get('unit', 'feet')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid dimension values. Please enter valid numbers.')}, status=400)
        
        mix_ratio = data.get('mix_ratio', '1:2:4')
        
        if length <= 0 or width <= 0 or thickness <= 0:
            return JsonResponse({'success': False, 'error': _('All dimensions must be greater than zero.')}, status=400)
        
        # Set reasonable maximum limits
        max_dimension = 1000 if unit == 'feet' else 300
        if length > max_dimension or width > max_dimension or thickness > max_dimension:
            return JsonResponse({'success': False, 'error': _('Dimensions are too large. Maximum allowed: {max} {unit}').format(max=max_dimension, unit=unit)}, status=400)
        
        # Convert to feet if needed
        if unit == 'meters':
            length_ft = length * 3.28084
            width_ft = width * 3.28084
            thickness_ft = thickness * 3.28084
        else:
            length_ft = length
            width_ft = width
            thickness_ft = thickness
        
        # Calculate volume in cubic feet
        volume_cuft = length_ft * width_ft * thickness_ft
        
        # Convert to other units
        volume_cuyd = volume_cuft * self.CUBIC_FEET_TO_CUBIC_YARDS
        volume_cum = volume_cuft * self.CUBIC_FEET_TO_CUBIC_METERS
        
        # Calculate materials
        materials = self._calculate_materials(volume_cuft, mix_ratio)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_rectangular_steps(
            length, width, thickness, unit, length_ft, width_ft, thickness_ft,
            volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(volume_cuft, volume_cuyd, volume_cum, materials)
        
        result = {
            'success': True,
            'calc_type': 'rectangular_slab',
            'measurements': {
                'length': length,
                'width': width,
                'thickness': thickness,
                'unit': unit,
                'length_feet': round(length_ft, 2),
                'width_feet': round(width_ft, 2),
                'thickness_feet': round(thickness_ft, 2)
            },
            'volume': {
                'cubic_feet': round(volume_cuft, 2),
                'cubic_yards': round(volume_cuyd, 2),
                'cubic_meters': round(volume_cum, 2)
            },
            'materials': materials,
            'mix_ratio': mix_ratio,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_circular_slab(self, data):
        """Calculate concrete for circular slab"""
        try:
            diameter = float(data.get('diameter', 0))
            thickness = float(data.get('thickness', 0))
            unit = data.get('unit', 'feet')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid dimension values. Please enter valid numbers.')}, status=400)
        
        mix_ratio = data.get('mix_ratio', '1:2:4')
        
        if diameter <= 0 or thickness <= 0:
            return JsonResponse({'success': False, 'error': _('All dimensions must be greater than zero.')}, status=400)
        
        # Convert to feet if needed
        if unit == 'meters':
            diameter_ft = diameter * 3.28084
            thickness_ft = thickness * 3.28084
        else:
            diameter_ft = diameter
            thickness_ft = thickness
        
        # Calculate volume in cubic feet
        radius_ft = diameter_ft / 2
        area_sqft = math.pi * radius_ft ** 2
        volume_cuft = area_sqft * thickness_ft
        
        # Convert to other units
        volume_cuyd = volume_cuft * self.CUBIC_FEET_TO_CUBIC_YARDS
        volume_cum = volume_cuft * self.CUBIC_FEET_TO_CUBIC_METERS
        
        # Calculate materials
        materials = self._calculate_materials(volume_cuft, mix_ratio)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_circular_steps(
            diameter, thickness, unit, diameter_ft, thickness_ft,
            radius_ft, area_sqft, volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(volume_cuft, volume_cuyd, volume_cum, materials)
        
        result = {
            'success': True,
            'calc_type': 'circular_slab',
            'measurements': {
                'diameter': diameter,
                'thickness': thickness,
                'unit': unit,
                'diameter_feet': round(diameter_ft, 2),
                'thickness_feet': round(thickness_ft, 2),
                'radius_feet': round(radius_ft, 2)
            },
            'volume': {
                'cubic_feet': round(volume_cuft, 2),
                'cubic_yards': round(volume_cuyd, 2),
                'cubic_meters': round(volume_cum, 2)
            },
            'materials': materials,
            'mix_ratio': mix_ratio,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_column(self, data):
        """Calculate concrete for column"""
        try:
            diameter = float(data.get('diameter', 0))
            height = float(data.get('height', 0))
            unit = data.get('unit', 'feet')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid dimension values. Please enter valid numbers.')}, status=400)
        
        mix_ratio = data.get('mix_ratio', '1:2:4')
        
        if diameter <= 0 or height <= 0:
            return JsonResponse({'success': False, 'error': _('All dimensions must be greater than zero.')}, status=400)
        
        # Convert to feet if needed
        if unit == 'meters':
            diameter_ft = diameter * 3.28084
            height_ft = height * 3.28084
        else:
            diameter_ft = diameter
            height_ft = height
        
        # Calculate volume in cubic feet
        radius_ft = diameter_ft / 2
        area_sqft = math.pi * radius_ft ** 2
        volume_cuft = area_sqft * height_ft
        
        # Convert to other units
        volume_cuyd = volume_cuft * self.CUBIC_FEET_TO_CUBIC_YARDS
        volume_cum = volume_cuft * self.CUBIC_FEET_TO_CUBIC_METERS
        
        # Calculate materials
        materials = self._calculate_materials(volume_cuft, mix_ratio)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_column_steps(
            diameter, height, unit, diameter_ft, height_ft,
            radius_ft, area_sqft, volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(volume_cuft, volume_cuyd, volume_cum, materials)
        
        result = {
            'success': True,
            'calc_type': 'column',
            'measurements': {
                'diameter': diameter,
                'height': height,
                'unit': unit,
                'diameter_feet': round(diameter_ft, 2),
                'height_feet': round(height_ft, 2),
                'radius_feet': round(radius_ft, 2)
            },
            'volume': {
                'cubic_feet': round(volume_cuft, 2),
                'cubic_yards': round(volume_cuyd, 2),
                'cubic_meters': round(volume_cum, 2)
            },
            'materials': materials,
            'mix_ratio': mix_ratio,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_footing(self, data):
        """Calculate concrete for footing"""
        try:
            length = float(data.get('length', 0))
            width = float(data.get('width', 0))
            depth = float(data.get('depth', 0))
            unit = data.get('unit', 'feet')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid dimension values. Please enter valid numbers.')}, status=400)
        
        mix_ratio = data.get('mix_ratio', '1:2:4')
        
        if length <= 0 or width <= 0 or depth <= 0:
            return JsonResponse({'success': False, 'error': _('All dimensions must be greater than zero.')}, status=400)
        
        # Convert to feet if needed
        if unit == 'meters':
            length_ft = length * 3.28084
            width_ft = width * 3.28084
            depth_ft = depth * 3.28084
        else:
            length_ft = length
            width_ft = width
            depth_ft = depth
        
        # Calculate volume in cubic feet
        volume_cuft = length_ft * width_ft * depth_ft
        
        # Convert to other units
        volume_cuyd = volume_cuft * self.CUBIC_FEET_TO_CUBIC_YARDS
        volume_cum = volume_cuft * self.CUBIC_FEET_TO_CUBIC_METERS
        
        # Calculate materials
        materials = self._calculate_materials(volume_cuft, mix_ratio)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_footing_steps(
            length, width, depth, unit, length_ft, width_ft, depth_ft,
            volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(volume_cuft, volume_cuyd, volume_cum, materials)
        
        result = {
            'success': True,
            'calc_type': 'footing',
            'measurements': {
                'length': length,
                'width': width,
                'depth': depth,
                'unit': unit,
                'length_feet': round(length_ft, 2),
                'width_feet': round(width_ft, 2),
                'depth_feet': round(depth_ft, 2)
            },
            'volume': {
                'cubic_feet': round(volume_cuft, 2),
                'cubic_yards': round(volume_cuyd, 2),
                'cubic_meters': round(volume_cum, 2)
            },
            'materials': materials,
            'mix_ratio': mix_ratio,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_wall(self, data):
        """Calculate concrete for wall"""
        try:
            length = float(data.get('length', 0))
            height = float(data.get('height', 0))
            thickness = float(data.get('thickness', 0))
            unit = data.get('unit', 'feet')
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid dimension values. Please enter valid numbers.')}, status=400)
        
        mix_ratio = data.get('mix_ratio', '1:2:4')
        
        if length <= 0 or height <= 0 or thickness <= 0:
            return JsonResponse({'success': False, 'error': _('All dimensions must be greater than zero.')}, status=400)
        
        # Convert to feet if needed
        if unit == 'meters':
            length_ft = length * 3.28084
            height_ft = height * 3.28084
            thickness_ft = thickness * 3.28084
        else:
            length_ft = length
            height_ft = height
            thickness_ft = thickness
        
        # Calculate volume in cubic feet
        volume_cuft = length_ft * height_ft * thickness_ft
        
        # Convert to other units
        volume_cuyd = volume_cuft * self.CUBIC_FEET_TO_CUBIC_YARDS
        volume_cum = volume_cuft * self.CUBIC_FEET_TO_CUBIC_METERS
        
        # Calculate materials
        materials = self._calculate_materials(volume_cuft, mix_ratio)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_wall_steps(
            length, height, thickness, unit, length_ft, height_ft, thickness_ft,
            volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(volume_cuft, volume_cuyd, volume_cum, materials)
        
        result = {
            'success': True,
            'calc_type': 'wall',
            'measurements': {
                'length': length,
                'height': height,
                'thickness': thickness,
                'unit': unit,
                'length_feet': round(length_ft, 2),
                'height_feet': round(height_ft, 2),
                'thickness_feet': round(thickness_ft, 2)
            },
            'volume': {
                'cubic_feet': round(volume_cuft, 2),
                'cubic_yards': round(volume_cuyd, 2),
                'cubic_meters': round(volume_cum, 2)
            },
            'materials': materials,
            'mix_ratio': mix_ratio,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _convert_volume_units(self, data):
        """Convert volume units"""
        try:
            volume_value = float(data.get('volume_value', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid value. Please enter a valid number.')}, status=400)
        
        from_unit = data.get('from_unit', 'cubic_feet')
        to_unit = data.get('to_unit', 'cubic_yards')
        
        if volume_value <= 0:
            return JsonResponse({'success': False, 'error': _('Value must be greater than zero.')}, status=400)
        
        # Convert to cubic feet first
        if from_unit == 'cubic_yards':
            volume_cuft = volume_value / self.CUBIC_FEET_TO_CUBIC_YARDS
        elif from_unit == 'cubic_meters':
            volume_cuft = volume_value / self.CUBIC_FEET_TO_CUBIC_METERS
        else:
            volume_cuft = volume_value
        
        # Convert to target unit
        if to_unit == 'cubic_yards':
            converted = volume_cuft * self.CUBIC_FEET_TO_CUBIC_YARDS
        elif to_unit == 'cubic_meters':
            converted = volume_cuft * self.CUBIC_FEET_TO_CUBIC_METERS
        else:
            converted = volume_cuft
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_conversion_steps(volume_value, from_unit, volume_cuft, converted, to_unit)
        
        result = {
            'success': True,
            'calc_type': 'volume_conversion',
            'original_value': volume_value,
            'from_unit': from_unit,
            'cubic_feet_equivalent': round(volume_cuft, 2),
            'converted_value': round(converted, 6),
            'to_unit': to_unit,
            'step_by_step': step_by_step
        }
        
        return JsonResponse(result)
    
    def _calculate_materials(self, volume_cuft, mix_ratio):
        """Calculate material requirements based on volume and mix ratio"""
        if mix_ratio not in self.MIX_RATIOS:
            mix_ratio = '1:2:4'
        
        ratio = self.MIX_RATIOS[mix_ratio]
        
        # Calculate parts (approximate - based on standard concrete mix calculations)
        # For 1 cubic foot of concrete, approximate material volumes
        cement_volume_cuft = (volume_cuft * ratio['cement']) / ratio['total']
        sand_volume_cuft = (volume_cuft * ratio['sand']) / ratio['total']
        aggregate_volume_cuft = (volume_cuft * ratio['aggregate']) / ratio['total']
        
        # Convert to weights
        cement_weight_lbs = cement_volume_cuft * self.CEMENT_DENSITY_CUBIC_FT
        sand_weight_lbs = sand_volume_cuft * self.SAND_DENSITY_CUBIC_FT
        aggregate_weight_lbs = aggregate_volume_cuft * self.AGGREGATE_DENSITY_CUBIC_FT
        
        # Calculate number of cement bags
        cement_bags = math.ceil(cement_weight_lbs / self.CEMENT_BAG_SIZE)
        
        # Convert to tons
        cement_tons = cement_weight_lbs / 2000
        sand_tons = sand_weight_lbs / 2000
        aggregate_tons = aggregate_weight_lbs / 2000
        
        return {
            'cement': {
                'bags': cement_bags,
                'pounds': round(cement_weight_lbs, 2),
                'tons': round(cement_tons, 3),
                'cubic_feet': round(cement_volume_cuft, 2)
            },
            'sand': {
                'pounds': round(sand_weight_lbs, 2),
                'tons': round(sand_tons, 3),
                'cubic_feet': round(sand_volume_cuft, 2)
            },
            'aggregate': {
                'pounds': round(aggregate_weight_lbs, 2),
                'tons': round(aggregate_tons, 3),
                'cubic_feet': round(aggregate_volume_cuft, 2)
            }
        }
    
    def _prepare_rectangular_steps(self, length, width, thickness, unit, length_ft, width_ft, thickness_ft,
                                   volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials):
        """Prepare step-by-step solution for rectangular slab"""
        steps = []
        
        steps.append(_("Step 1: Enter Dimensions"))
        steps.append(_("  Length: {length} {unit}").format(length=length, unit=unit))
        steps.append(_("  Width: {width} {unit}").format(width=width, unit=unit))
        steps.append(_("  Thickness: {thickness} {unit}").format(thickness=thickness, unit=unit))
        steps.append("")
        
        if unit == 'meters':
            steps.append(_("Step 2: Convert to Feet"))
            steps.append(_("  Length: {m} m × 3.28084 = {ft:.2f} ft").format(m=length, ft=length_ft))
            steps.append(_("  Width: {m} m × 3.28084 = {ft:.2f} ft").format(m=width, ft=width_ft))
            steps.append(_("  Thickness: {m} m × 3.28084 = {ft:.2f} ft").format(m=thickness, ft=thickness_ft))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Volume"))
        steps.append(_("  Volume = Length × Width × Thickness"))
        steps.append(_("  Volume = {length:.2f} × {width:.2f} × {thickness:.2f} = {volume:.2f} cu ft").format(
            length=length_ft, width=width_ft, thickness=thickness_ft, volume=volume_cuft
        ))
        steps.append("")
        
        steps.append(_("Step 4: Convert to Other Units"))
        steps.append(_("  Cubic Yards: {cuyd:.2f} cu yd").format(cuyd=volume_cuyd))
        steps.append(_("  Cubic Meters: {cum:.2f} m³").format(cum=volume_cum))
        steps.append("")
        
        steps.append(_("Step 5: Calculate Materials (Mix Ratio: {ratio})").format(ratio=mix_ratio))
        steps.append(_("  Cement: {bags} bags ({lbs:.2f} lbs)").format(
            bags=materials['cement']['bags'], lbs=materials['cement']['pounds']
        ))
        steps.append(_("  Sand: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['sand']['pounds'], tons=materials['sand']['tons']
        ))
        steps.append(_("  Aggregate: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['aggregate']['pounds'], tons=materials['aggregate']['tons']
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_circular_steps(self, diameter, thickness, unit, diameter_ft, thickness_ft,
                               radius_ft, area_sqft, volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials):
        """Prepare step-by-step solution for circular slab"""
        steps = []
        
        steps.append(_("Step 1: Enter Dimensions"))
        steps.append(_("  Diameter: {diameter} {unit}").format(diameter=diameter, unit=unit))
        steps.append(_("  Thickness: {thickness} {unit}").format(thickness=thickness, unit=unit))
        steps.append("")
        
        if unit == 'meters':
            steps.append(_("Step 2: Convert to Feet"))
            steps.append(_("  Diameter: {m} m × 3.28084 = {ft:.2f} ft").format(m=diameter, ft=diameter_ft))
            steps.append(_("  Thickness: {m} m × 3.28084 = {ft:.2f} ft").format(m=thickness, ft=thickness_ft))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Radius and Area"))
        steps.append(_("  Radius = Diameter ÷ 2 = {diameter:.2f} ÷ 2 = {radius:.2f} ft").format(
            diameter=diameter_ft, radius=radius_ft
        ))
        steps.append(_("  Area = π × r² = π × {radius:.2f}² = {area:.2f} sq ft").format(
            radius=radius_ft, area=area_sqft
        ))
        steps.append("")
        
        steps.append(_("Step 4: Calculate Volume"))
        steps.append(_("  Volume = Area × Thickness"))
        steps.append(_("  Volume = {area:.2f} × {thickness:.2f} = {volume:.2f} cu ft").format(
            area=area_sqft, thickness=thickness_ft, volume=volume_cuft
        ))
        steps.append("")
        
        steps.append(_("Step 5: Convert to Other Units"))
        steps.append(_("  Cubic Yards: {cuyd:.2f} cu yd").format(cuyd=volume_cuyd))
        steps.append(_("  Cubic Meters: {cum:.2f} m³").format(cum=volume_cum))
        steps.append("")
        
        steps.append(_("Step 6: Calculate Materials (Mix Ratio: {ratio})").format(ratio=mix_ratio))
        steps.append(_("  Cement: {bags} bags ({lbs:.2f} lbs)").format(
            bags=materials['cement']['bags'], lbs=materials['cement']['pounds']
        ))
        steps.append(_("  Sand: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['sand']['pounds'], tons=materials['sand']['tons']
        ))
        steps.append(_("  Aggregate: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['aggregate']['pounds'], tons=materials['aggregate']['tons']
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_column_steps(self, diameter, height, unit, diameter_ft, height_ft,
                              radius_ft, area_sqft, volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials):
        """Prepare step-by-step solution for column"""
        steps = []
        
        steps.append(_("Step 1: Enter Dimensions"))
        steps.append(_("  Diameter: {diameter} {unit}").format(diameter=diameter, unit=unit))
        steps.append(_("  Height: {height} {unit}").format(height=height, unit=unit))
        steps.append("")
        
        if unit == 'meters':
            steps.append(_("Step 2: Convert to Feet"))
            steps.append(_("  Diameter: {m} m × 3.28084 = {ft:.2f} ft").format(m=diameter, ft=diameter_ft))
            steps.append(_("  Height: {m} m × 3.28084 = {ft:.2f} ft").format(m=height, ft=height_ft))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Radius and Area"))
        steps.append(_("  Radius = Diameter ÷ 2 = {diameter:.2f} ÷ 2 = {radius:.2f} ft").format(
            diameter=diameter_ft, radius=radius_ft
        ))
        steps.append(_("  Area = π × r² = π × {radius:.2f}² = {area:.2f} sq ft").format(
            radius=radius_ft, area=area_sqft
        ))
        steps.append("")
        
        steps.append(_("Step 4: Calculate Volume"))
        steps.append(_("  Volume = Area × Height"))
        steps.append(_("  Volume = {area:.2f} × {height:.2f} = {volume:.2f} cu ft").format(
            area=area_sqft, height=height_ft, volume=volume_cuft
        ))
        steps.append("")
        
        steps.append(_("Step 5: Convert to Other Units"))
        steps.append(_("  Cubic Yards: {cuyd:.2f} cu yd").format(cuyd=volume_cuyd))
        steps.append(_("  Cubic Meters: {cum:.2f} m³").format(cum=volume_cum))
        steps.append("")
        
        steps.append(_("Step 6: Calculate Materials (Mix Ratio: {ratio})").format(ratio=mix_ratio))
        steps.append(_("  Cement: {bags} bags ({lbs:.2f} lbs)").format(
            bags=materials['cement']['bags'], lbs=materials['cement']['pounds']
        ))
        steps.append(_("  Sand: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['sand']['pounds'], tons=materials['sand']['tons']
        ))
        steps.append(_("  Aggregate: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['aggregate']['pounds'], tons=materials['aggregate']['tons']
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_footing_steps(self, length, width, depth, unit, length_ft, width_ft, depth_ft,
                               volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials):
        """Prepare step-by-step solution for footing"""
        steps = []
        
        steps.append(_("Step 1: Enter Dimensions"))
        steps.append(_("  Length: {length} {unit}").format(length=length, unit=unit))
        steps.append(_("  Width: {width} {unit}").format(width=width, unit=unit))
        steps.append(_("  Depth: {depth} {unit}").format(depth=depth, unit=unit))
        steps.append("")
        
        if unit == 'meters':
            steps.append(_("Step 2: Convert to Feet"))
            steps.append(_("  Length: {m} m × 3.28084 = {ft:.2f} ft").format(m=length, ft=length_ft))
            steps.append(_("  Width: {m} m × 3.28084 = {ft:.2f} ft").format(m=width, ft=width_ft))
            steps.append(_("  Depth: {m} m × 3.28084 = {ft:.2f} ft").format(m=depth, ft=depth_ft))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Volume"))
        steps.append(_("  Volume = Length × Width × Depth"))
        steps.append(_("  Volume = {length:.2f} × {width:.2f} × {depth:.2f} = {volume:.2f} cu ft").format(
            length=length_ft, width=width_ft, depth=depth_ft, volume=volume_cuft
        ))
        steps.append("")
        
        steps.append(_("Step 4: Convert to Other Units"))
        steps.append(_("  Cubic Yards: {cuyd:.2f} cu yd").format(cuyd=volume_cuyd))
        steps.append(_("  Cubic Meters: {cum:.2f} m³").format(cum=volume_cum))
        steps.append("")
        
        steps.append(_("Step 5: Calculate Materials (Mix Ratio: {ratio})").format(ratio=mix_ratio))
        steps.append(_("  Cement: {bags} bags ({lbs:.2f} lbs)").format(
            bags=materials['cement']['bags'], lbs=materials['cement']['pounds']
        ))
        steps.append(_("  Sand: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['sand']['pounds'], tons=materials['sand']['tons']
        ))
        steps.append(_("  Aggregate: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['aggregate']['pounds'], tons=materials['aggregate']['tons']
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_wall_steps(self, length, height, thickness, unit, length_ft, height_ft, thickness_ft,
                            volume_cuft, volume_cuyd, volume_cum, mix_ratio, materials):
        """Prepare step-by-step solution for wall"""
        steps = []
        
        steps.append(_("Step 1: Enter Dimensions"))
        steps.append(_("  Length: {length} {unit}").format(length=length, unit=unit))
        steps.append(_("  Height: {height} {unit}").format(height=height, unit=unit))
        steps.append(_("  Thickness: {thickness} {unit}").format(thickness=thickness, unit=unit))
        steps.append("")
        
        if unit == 'meters':
            steps.append(_("Step 2: Convert to Feet"))
            steps.append(_("  Length: {m} m × 3.28084 = {ft:.2f} ft").format(m=length, ft=length_ft))
            steps.append(_("  Height: {m} m × 3.28084 = {ft:.2f} ft").format(m=height, ft=height_ft))
            steps.append(_("  Thickness: {m} m × 3.28084 = {ft:.2f} ft").format(m=thickness, ft=thickness_ft))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Volume"))
        steps.append(_("  Volume = Length × Height × Thickness"))
        steps.append(_("  Volume = {length:.2f} × {height:.2f} × {thickness:.2f} = {volume:.2f} cu ft").format(
            length=length_ft, height=height_ft, thickness=thickness_ft, volume=volume_cuft
        ))
        steps.append("")
        
        steps.append(_("Step 4: Convert to Other Units"))
        steps.append(_("  Cubic Yards: {cuyd:.2f} cu yd").format(cuyd=volume_cuyd))
        steps.append(_("  Cubic Meters: {cum:.2f} m³").format(cum=volume_cum))
        steps.append("")
        
        steps.append(_("Step 5: Calculate Materials (Mix Ratio: {ratio})").format(ratio=mix_ratio))
        steps.append(_("  Cement: {bags} bags ({lbs:.2f} lbs)").format(
            bags=materials['cement']['bags'], lbs=materials['cement']['pounds']
        ))
        steps.append(_("  Sand: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['sand']['pounds'], tons=materials['sand']['tons']
        ))
        steps.append(_("  Aggregate: {lbs:.2f} lbs ({tons:.3f} tons)").format(
            lbs=materials['aggregate']['pounds'], tons=materials['aggregate']['tons']
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_conversion_steps(self, original_value, from_unit, volume_cuft, converted, to_unit):
        """Prepare step-by-step solution for volume conversion"""
        steps = []
        
        steps.append(_("Step 1: Original Value"))
        steps.append(_("  Value: {value} {unit}").format(value=original_value, unit=from_unit.replace('_', ' ').title()))
        steps.append("")
        
        if from_unit != 'cubic_feet':
            steps.append(_("Step 2: Convert to Cubic Feet"))
            if from_unit == 'cubic_yards':
                steps.append(_("  Cubic Feet = {cuyd} cu yd ÷ {factor} = {cuft:.2f} cu ft").format(
                    cuyd=original_value, factor=self.CUBIC_FEET_TO_CUBIC_YARDS, cuft=volume_cuft
                ))
            elif from_unit == 'cubic_meters':
                steps.append(_("  Cubic Feet = {cum} m³ ÷ {factor} = {cuft:.2f} cu ft").format(
                    cum=original_value, factor=self.CUBIC_FEET_TO_CUBIC_METERS, cuft=volume_cuft
                ))
            steps.append("")
        
        if to_unit != 'cubic_feet':
            steps.append(_("Step 3: Convert to {unit}").format(unit=to_unit.replace('_', ' ').title()))
            if to_unit == 'cubic_yards':
                steps.append(_("  {unit} = {cuft} cu ft × {factor} = {converted:.6f} {unit}").format(
                    unit=to_unit.replace('_', ' ').title(), cuft=volume_cuft,
                    factor=self.CUBIC_FEET_TO_CUBIC_YARDS, converted=converted
                ))
            elif to_unit == 'cubic_meters':
                steps.append(_("  {unit} = {cuft} cu ft × {factor} = {converted:.6f} {unit}").format(
                    unit=to_unit.replace('_', ' ').title(), cuft=volume_cuft,
                    factor=self.CUBIC_FEET_TO_CUBIC_METERS, converted=converted
                ))
        else:
            steps.append(_("Step 3: Result"))
            steps.append(_("  {cuft:.2f} cu ft").format(cuft=converted))
        
        return [str(step) for step in steps]
    
    def _prepare_chart_data(self, volume_cuft, volume_cuyd, volume_cum, materials):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Volume units comparison chart
            chart_data['volume_units_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['Cubic Feet', 'Cubic Yards', 'Cubic Meters'],
                    'datasets': [{
                        'label': str(_('Volume Units')),
                        'data': [
                            round(volume_cuft, 2),
                            round(volume_cuyd, 2),
                            round(volume_cum, 2)
                        ],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b'
                        ],
                        'borderWidth': 2,
                        'borderRadius': 4
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'display': True
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True
                        }
                    }
                }
            }
            
            # Materials breakdown pie chart
            chart_data['materials_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': [
                        str(_('Cement')),
                        str(_('Sand')),
                        str(_('Aggregate'))
                    ],
                    'datasets': [{
                        'data': [
                            materials['cement']['pounds'],
                            materials['sand']['pounds'],
                            materials['aggregate']['pounds']
                        ],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'right'
                        }
                    }
                }
            }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
