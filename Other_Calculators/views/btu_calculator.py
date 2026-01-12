from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BtuCalculator(View):
    """
    Professional BTU Calculator with Comprehensive Features
    
    This calculator provides BTU calculations with:
    - Room size calculations (length, width, height)
    - Area-based calculations
    - BTU to other energy unit conversions
    - Cooling/heating load calculations
    - Multiple room types and insulation factors
    - Climate zone considerations
    
    Features:
    - Supports multiple measurement units (feet, meters)
    - Handles different room types (bedroom, living room, kitchen, etc.)
    - Accounts for insulation quality
    - Considers climate zones
    - Provides energy unit conversions
    - Interactive visualizations
    """
    template_name = 'other_calculators/btu_calculator.html'
    
    # BTU conversion factors
    BTU_TO_KWH = 0.000293071
    BTU_TO_JOULES = 1055.06
    BTU_TO_CALORIES = 252.164
    BTU_TO_FOOT_POUNDS = 778.169
    
    # Room type multipliers (base BTU per square foot)
    ROOM_TYPE_MULTIPLIERS = {
        'bedroom': 20,
        'living_room': 25,
        'kitchen': 30,
        'bathroom': 15,
        'office': 20,
        'dining_room': 25,
        'basement': 20,
        'attic': 30,
        'garage': 15,
        'general': 20
    }
    
    # Insulation quality multipliers
    INSULATION_MULTIPLIERS = {
        'excellent': 0.8,
        'good': 1.0,
        'average': 1.2,
        'poor': 1.5,
        'none': 2.0
    }
    
    # Climate zone multipliers
    CLIMATE_ZONE_MULTIPLIERS = {
        'very_cold': 1.3,  # Below 0°F average
        'cold': 1.2,       # 0-20°F average
        'moderate': 1.0,   # 20-50°F average
        'warm': 0.9,       # 50-80°F average
        'hot': 0.8,        # Above 80°F average
        'tropical': 0.7    # Very hot and humid
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('BTU Calculator'),
            'features': [
                _('Room size calculations (length × width × height)'),
                _('Area-based BTU calculations'),
                _('Energy unit conversions (kWh, Joules, Calories)'),
                _('Cooling/heating load calculations'),
                _('Multiple room types and insulation factors'),
                _('Climate zone considerations'),
                _('Step-by-step solutions'),
                _('Interactive visualizations')
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'room_size')
            
            if calc_type == 'room_size':
                return self._calculate_room_btu(data)
            elif calc_type == 'area_btu':
                return self._calculate_area_btu(data)
            elif calc_type == 'unit_conversion':
                return self._convert_units(data)
            elif calc_type == 'cooling_load':
                return self._calculate_cooling_load(data)
            else:
                return JsonResponse({'success': False, 'error': _('Invalid calculation type.')}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('Invalid JSON data.')}, status=400)
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: {error}').format(error=str(e))}, status=400)
        except Exception as e:
            import traceback
            print(f"BTU Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
    
    def _calculate_room_btu(self, data):
        """Calculate BTU from room dimensions"""
        try:
            length = float(data.get('length', 0))
            width = float(data.get('width', 0))
            height = float(data.get('height', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid dimension values. Please enter valid numbers.')}, status=400)
        
        unit = data.get('unit', 'feet')
        room_type = data.get('room_type', 'general')
        insulation = data.get('insulation', 'average')
        climate_zone = data.get('climate_zone', 'moderate')
        
        # Validate dimensions
        if length <= 0 or width <= 0 or height <= 0:
            return JsonResponse({'success': False, 'error': _('All dimensions must be greater than zero.')}, status=400)
        
        # Set reasonable maximum limits (1000 feet or 300 meters)
        max_dimension = 1000 if unit == 'feet' else 300
        if length > max_dimension or width > max_dimension or height > max_dimension:
            return JsonResponse({'success': False, 'error': _('Dimensions are too large. Maximum allowed: {max} {unit}').format(max=max_dimension, unit=unit)}, status=400)
        
        # Convert to feet if needed
        if unit == 'meters':
            length_feet = length * 3.28084
            width_feet = width * 3.28084
            height_feet = height * 3.28084
        else:
            length_feet = length
            width_feet = width
            height_feet = height
        
        # Calculate area
        area_sqft = length_feet * width_feet
        
        # Calculate volume
        volume_cuft = length_feet * width_feet * height_feet
        
        # Base BTU calculation (20 BTU per square foot is standard)
        base_btu_per_sqft = self.ROOM_TYPE_MULTIPLIERS.get(room_type, 20)
        base_btu = area_sqft * base_btu_per_sqft
        
        # Apply multipliers
        insulation_mult = self.INSULATION_MULTIPLIERS.get(insulation, 1.0)
        climate_mult = self.CLIMATE_ZONE_MULTIPLIERS.get(climate_zone, 1.0)
        
        # Final BTU calculation
        total_btu = base_btu * insulation_mult * climate_mult
        
        # Calculate in other units
        conversions = self._calculate_conversions(total_btu)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_room_btu_steps(
            length, width, height, unit, length_feet, width_feet, height_feet,
            area_sqft, volume_cuft, base_btu_per_sqft, base_btu,
            insulation_mult, climate_mult, total_btu, room_type, insulation, climate_zone
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(total_btu, conversions, room_type)
        
        result = {
            'success': True,
            'calc_type': 'room_size',
            'measurements': {
                'length': length,
                'width': width,
                'height': height,
                'unit': unit,
                'length_feet': round(length_feet, 2),
                'width_feet': round(width_feet, 2),
                'height_feet': round(height_feet, 2)
            },
            'calculations': {
                'area_sqft': round(area_sqft, 2),
                'volume_cuft': round(volume_cuft, 2),
                'base_btu_per_sqft': base_btu_per_sqft,
                'base_btu': round(base_btu, 2),
                'insulation_multiplier': insulation_mult,
                'climate_multiplier': climate_mult,
                'total_btu': round(total_btu, 2)
            },
            'conversions': conversions,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_area_btu(self, data):
        """Calculate BTU from area"""
        try:
            area = float(data.get('area', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid area value. Please enter a valid number.')}, status=400)
        
        unit = data.get('unit', 'sqft')
        room_type = data.get('room_type', 'general')
        insulation = data.get('insulation', 'average')
        climate_zone = data.get('climate_zone', 'moderate')
        
        if area <= 0:
            return JsonResponse({'success': False, 'error': _('Area must be greater than zero.')}, status=400)
        
        # Set reasonable maximum limits (1,000,000 sq ft or 100,000 sq m)
        max_area = 1000000 if unit == 'sqft' else 100000
        if area > max_area:
            return JsonResponse({'success': False, 'error': _('Area is too large. Maximum allowed: {max} {unit}').format(max=max_area, unit=unit)}, status=400)
        
        # Convert to square feet if needed
        if unit == 'sqm':
            area_sqft = area * 10.764
        else:
            area_sqft = area
        
        # Base BTU calculation
        base_btu_per_sqft = self.ROOM_TYPE_MULTIPLIERS.get(room_type, 20)
        base_btu = area_sqft * base_btu_per_sqft
        
        # Apply multipliers
        insulation_mult = self.INSULATION_MULTIPLIERS.get(insulation, 1.0)
        climate_mult = self.CLIMATE_ZONE_MULTIPLIERS.get(climate_zone, 1.0)
        
        # Final BTU calculation
        total_btu = base_btu * insulation_mult * climate_mult
        
        # Calculate in other units
        conversions = self._calculate_conversions(total_btu)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_area_btu_steps(
            area, unit, area_sqft, base_btu_per_sqft, base_btu,
            insulation_mult, climate_mult, total_btu, room_type, insulation, climate_zone
        )
        
        # Prepare chart data
        chart_data = self._prepare_chart_data(total_btu, conversions, room_type)
        
        result = {
            'success': True,
            'calc_type': 'area_btu',
            'measurements': {
                'area': area,
                'unit': unit,
                'area_sqft': round(area_sqft, 2)
            },
            'calculations': {
                'base_btu_per_sqft': base_btu_per_sqft,
                'base_btu': round(base_btu, 2),
                'insulation_multiplier': insulation_mult,
                'climate_multiplier': climate_mult,
                'total_btu': round(total_btu, 2)
            },
            'conversions': conversions,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _convert_units(self, data):
        """Convert BTU to other energy units"""
        try:
            btu_value = float(data.get('btu_value', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid value. Please enter a valid number.')}, status=400)
        
        from_unit = data.get('from_unit', 'BTU')
        to_unit = data.get('to_unit', 'kWh')
        
        if btu_value <= 0:
            return JsonResponse({'success': False, 'error': _('Value must be greater than zero.')}, status=400)
        
        # Set reasonable maximum limit (1 billion)
        if btu_value > 1000000000:
            return JsonResponse({'success': False, 'error': _('Value is too large. Maximum allowed: 1,000,000,000.')}, status=400)
        
        # Convert to BTU first if needed
        if from_unit == 'kWh':
            btu = btu_value / self.BTU_TO_KWH
        elif from_unit == 'Joules':
            btu = btu_value / self.BTU_TO_JOULES
        elif from_unit == 'Calories':
            btu = btu_value / self.BTU_TO_CALORIES
        elif from_unit == 'Foot-Pounds':
            btu = btu_value / self.BTU_TO_FOOT_POUNDS
        else:
            btu = btu_value
        
        # Convert to target unit
        if to_unit == 'kWh':
            converted = btu * self.BTU_TO_KWH
        elif to_unit == 'Joules':
            converted = btu * self.BTU_TO_JOULES
        elif to_unit == 'Calories':
            converted = btu * self.BTU_TO_CALORIES
        elif to_unit == 'Foot-Pounds':
            converted = btu * self.BTU_TO_FOOT_POUNDS
        else:
            converted = btu
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_conversion_steps(btu_value, from_unit, btu, converted, to_unit)
        
        result = {
            'success': True,
            'calc_type': 'unit_conversion',
            'original_value': btu_value,
            'from_unit': from_unit,
            'btu_equivalent': round(btu, 2),
            'converted_value': round(converted, 6),
            'to_unit': to_unit,
            'step_by_step': step_by_step
        }
        
        return JsonResponse(result)
    
    def _calculate_cooling_load(self, data):
        """Calculate cooling load BTU"""
        try:
            area = float(data.get('area', 0))
            windows = int(data.get('windows', 0))
            occupants = int(data.get('occupants', 1))
            appliances = float(data.get('appliances', 0))  # Additional heat from appliances in watts
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': _('Invalid input values. Please enter valid numbers.')}, status=400)
        
        unit = data.get('unit', 'sqft')
        room_type = data.get('room_type', 'general')
        insulation = data.get('insulation', 'average')
        climate_zone = data.get('climate_zone', 'moderate')
        
        if area <= 0:
            return JsonResponse({'success': False, 'error': _('Area must be greater than zero.')}, status=400)
        
        # Set reasonable maximum limits
        max_area = 1000000 if unit == 'sqft' else 100000
        if area > max_area:
            return JsonResponse({'success': False, 'error': _('Area is too large. Maximum allowed: {max} {unit}').format(max=max_area, unit=unit)}, status=400)
        
        if windows < 0:
            return JsonResponse({'success': False, 'error': _('Number of windows cannot be negative.')}, status=400)
        
        if occupants < 1:
            return JsonResponse({'success': False, 'error': _('Number of occupants must be at least 1.')}, status=400)
        
        if appliances < 0:
            return JsonResponse({'success': False, 'error': _('Appliance heat cannot be negative.')}, status=400)
        
        # Convert to square feet if needed
        if unit == 'sqm':
            area_sqft = area * 10.764
        else:
            area_sqft = area
        
        # Base cooling BTU (higher than heating for cooling)
        base_btu_per_sqft = self.ROOM_TYPE_MULTIPLIERS.get(room_type, 20) * 1.2  # 20% more for cooling
        base_btu = area_sqft * base_btu_per_sqft
        
        # Apply multipliers
        insulation_mult = self.INSULATION_MULTIPLIERS.get(insulation, 1.0)
        climate_mult = self.CLIMATE_ZONE_MULTIPLIERS.get(climate_zone, 1.0)
        
        # Additional factors
        window_btu = windows * 1000  # 1000 BTU per window
        occupant_btu = occupants * 400  # 400 BTU per person
        appliance_btu = appliances * 3.412  # Convert watts to BTU
        
        # Total cooling BTU
        total_btu = (base_btu * insulation_mult * climate_mult) + window_btu + occupant_btu + appliance_btu
        
        # Calculate in other units
        conversions = self._calculate_conversions(total_btu)
        
        # Prepare step-by-step solution
        step_by_step = self._prepare_cooling_load_steps(
            area, unit, area_sqft, base_btu_per_sqft, base_btu,
            insulation_mult, climate_mult, window_btu, occupant_btu,
            appliance_btu, total_btu, windows, occupants, appliances,
            room_type, insulation, climate_zone
        )
        
        # Prepare chart data
        chart_data = self._prepare_cooling_chart_data(total_btu, base_btu, window_btu, occupant_btu, appliance_btu)
        
        result = {
            'success': True,
            'calc_type': 'cooling_load',
            'measurements': {
                'area': area,
                'unit': unit,
                'area_sqft': round(area_sqft, 2),
                'windows': windows,
                'occupants': occupants,
                'appliances_watts': appliances
            },
            'calculations': {
                'base_btu': round(base_btu, 2),
                'insulation_multiplier': insulation_mult,
                'climate_multiplier': climate_mult,
                'window_btu': round(window_btu, 2),
                'occupant_btu': round(occupant_btu, 2),
                'appliance_btu': round(appliance_btu, 2),
                'total_btu': round(total_btu, 2)
            },
            'conversions': conversions,
            'step_by_step': step_by_step,
            'chart_data': chart_data
        }
        
        return JsonResponse(result)
    
    def _calculate_conversions(self, btu):
        """Calculate BTU in other energy units"""
        return {
            'btu': round(btu, 2),
            'kwh': round(btu * self.BTU_TO_KWH, 6),
            'joules': round(btu * self.BTU_TO_JOULES, 2),
            'calories': round(btu * self.BTU_TO_CALORIES, 2),
            'foot_pounds': round(btu * self.BTU_TO_FOOT_POUNDS, 2)
        }
    
    def _prepare_room_btu_steps(self, length, width, height, unit, length_feet, width_feet, height_feet,
                                area_sqft, volume_cuft, base_btu_per_sqft, base_btu,
                                insulation_mult, climate_mult, total_btu, room_type, insulation, climate_zone):
        """Prepare step-by-step solution for room BTU calculation"""
        steps = []
        
        steps.append(_("Step 1: Enter Room Dimensions"))
        steps.append(_("  Length: {length} {unit}").format(length=length, unit=unit))
        steps.append(_("  Width: {width} {unit}").format(width=width, unit=unit))
        steps.append(_("  Height: {height} {unit}").format(height=height, unit=unit))
        steps.append("")
        
        if unit == 'meters':
            steps.append(_("Step 2: Convert to Feet"))
            steps.append(_("  Length: {m} m × 3.28084 = {ft:.2f} ft").format(m=length, ft=length_feet))
            steps.append(_("  Width: {m} m × 3.28084 = {ft:.2f} ft").format(m=width, ft=width_feet))
            steps.append(_("  Height: {m} m × 3.28084 = {ft:.2f} ft").format(m=height, ft=height_feet))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Area"))
        steps.append(_("  Area = Length × Width"))
        steps.append(_("  Area = {length:.2f} × {width:.2f} = {area:.2f} sq ft").format(
            length=length_feet, width=width_feet, area=area_sqft
        ))
        steps.append("")
        
        steps.append(_("Step 4: Calculate Volume"))
        steps.append(_("  Volume = Length × Width × Height"))
        steps.append(_("  Volume = {length:.2f} × {width:.2f} × {height:.2f} = {volume:.2f} cu ft").format(
            length=length_feet, width=width_feet, height=height_feet, volume=volume_cuft
        ))
        steps.append("")
        
        steps.append(_("Step 5: Determine Base BTU"))
        steps.append(_("  Room Type: {room_type} ({btu_per_sqft} BTU per sq ft)").format(
            room_type=room_type.replace('_', ' ').title(), btu_per_sqft=base_btu_per_sqft
        ))
        steps.append(_("  Base BTU = Area × BTU per sq ft"))
        steps.append(_("  Base BTU = {area:.2f} × {btu_per_sqft} = {base_btu:.2f} BTU").format(
            area=area_sqft, btu_per_sqft=base_btu_per_sqft, base_btu=base_btu
        ))
        steps.append("")
        
        steps.append(_("Step 6: Apply Multipliers"))
        steps.append(_("  Insulation Quality: {insulation} (multiplier: {mult})").format(
            insulation=insulation.replace('_', ' ').title(), mult=insulation_mult
        ))
        steps.append(_("  Climate Zone: {climate} (multiplier: {mult})").format(
            climate=climate_zone.replace('_', ' ').title(), mult=climate_mult
        ))
        steps.append("")
        
        steps.append(_("Step 7: Calculate Total BTU"))
        steps.append(_("  Total BTU = Base BTU × Insulation Multiplier × Climate Multiplier"))
        steps.append(_("  Total BTU = {base:.2f} × {ins_mult} × {clim_mult} = {total:.2f} BTU").format(
            base=base_btu, ins_mult=insulation_mult, clim_mult=climate_mult, total=total_btu
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_area_btu_steps(self, area, unit, area_sqft, base_btu_per_sqft, base_btu,
                                insulation_mult, climate_mult, total_btu, room_type, insulation, climate_zone):
        """Prepare step-by-step solution for area BTU calculation"""
        steps = []
        
        steps.append(_("Step 1: Enter Area"))
        steps.append(_("  Area: {area} {unit}").format(area=area, unit=unit))
        steps.append("")
        
        if unit == 'sqm':
            steps.append(_("Step 2: Convert to Square Feet"))
            steps.append(_("  Area = {sqm} m² × 10.764 = {sqft:.2f} sq ft").format(sqm=area, sqft=area_sqft))
            steps.append("")
        
        steps.append(_("Step 3: Determine Base BTU"))
        steps.append(_("  Room Type: {room_type} ({btu_per_sqft} BTU per sq ft)").format(
            room_type=room_type.replace('_', ' ').title(), btu_per_sqft=base_btu_per_sqft
        ))
        steps.append(_("  Base BTU = Area × BTU per sq ft"))
        steps.append(_("  Base BTU = {area:.2f} × {btu_per_sqft} = {base_btu:.2f} BTU").format(
            area=area_sqft, btu_per_sqft=base_btu_per_sqft, base_btu=base_btu
        ))
        steps.append("")
        
        steps.append(_("Step 4: Apply Multipliers"))
        steps.append(_("  Insulation Quality: {insulation} (multiplier: {mult})").format(
            insulation=insulation.replace('_', ' ').title(), mult=insulation_mult
        ))
        steps.append(_("  Climate Zone: {climate} (multiplier: {mult})").format(
            climate=climate_zone.replace('_', ' ').title(), mult=climate_mult
        ))
        steps.append("")
        
        steps.append(_("Step 5: Calculate Total BTU"))
        steps.append(_("  Total BTU = Base BTU × Insulation Multiplier × Climate Multiplier"))
        steps.append(_("  Total BTU = {base:.2f} × {ins_mult} × {clim_mult} = {total:.2f} BTU").format(
            base=base_btu, ins_mult=insulation_mult, clim_mult=climate_mult, total=total_btu
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_conversion_steps(self, original_value, from_unit, btu, converted, to_unit):
        """Prepare step-by-step solution for unit conversion"""
        steps = []
        
        steps.append(_("Step 1: Original Value"))
        steps.append(_("  Value: {value} {unit}").format(value=original_value, unit=from_unit))
        steps.append("")
        
        if from_unit != 'BTU':
            steps.append(_("Step 2: Convert to BTU"))
            if from_unit == 'kWh':
                steps.append(_("  BTU = {kwh} kWh ÷ {factor} = {btu:.2f} BTU").format(
                    kwh=original_value, factor=self.BTU_TO_KWH, btu=btu
                ))
            elif from_unit == 'Joules':
                steps.append(_("  BTU = {j} J ÷ {factor} = {btu:.2f} BTU").format(
                    j=original_value, factor=self.BTU_TO_JOULES, btu=btu
                ))
            elif from_unit == 'Calories':
                steps.append(_("  BTU = {cal} cal ÷ {factor} = {btu:.2f} BTU").format(
                    cal=original_value, factor=self.BTU_TO_CALORIES, btu=btu
                ))
            elif from_unit == 'Foot-Pounds':
                steps.append(_("  BTU = {fp} ft-lb ÷ {factor} = {btu:.2f} BTU").format(
                    fp=original_value, factor=self.BTU_TO_FOOT_POUNDS, btu=btu
                ))
            steps.append("")
        
        if to_unit != 'BTU':
            steps.append(_("Step 3: Convert to {unit}").format(unit=to_unit))
            if to_unit == 'kWh':
                steps.append(_("  {unit} = {btu} BTU × {factor} = {converted:.6f} {unit}").format(
                    unit=to_unit, btu=btu, factor=self.BTU_TO_KWH, converted=converted
                ))
            elif to_unit == 'Joules':
                steps.append(_("  {unit} = {btu} BTU × {factor} = {converted:.2f} {unit}").format(
                    unit=to_unit, btu=btu, factor=self.BTU_TO_JOULES, converted=converted
                ))
            elif to_unit == 'Calories':
                steps.append(_("  {unit} = {btu} BTU × {factor} = {converted:.2f} {unit}").format(
                    unit=to_unit, btu=btu, factor=self.BTU_TO_CALORIES, converted=converted
                ))
            elif to_unit == 'Foot-Pounds':
                steps.append(_("  {unit} = {btu} BTU × {factor} = {converted:.2f} {unit}").format(
                    unit=to_unit, btu=btu, factor=self.BTU_TO_FOOT_POUNDS, converted=converted
                ))
        else:
            steps.append(_("Step 3: Result"))
            steps.append(_("  {btu:.2f} BTU").format(btu=converted))
        
        return [str(step) for step in steps]
    
    def _prepare_cooling_load_steps(self, area, unit, area_sqft, base_btu_per_sqft, base_btu,
                                    insulation_mult, climate_mult, window_btu, occupant_btu,
                                    appliance_btu, total_btu, windows, occupants, appliances,
                                    room_type, insulation, climate_zone):
        """Prepare step-by-step solution for cooling load calculation"""
        steps = []
        
        steps.append(_("Step 1: Enter Room Information"))
        steps.append(_("  Area: {area} {unit}").format(area=area, unit=unit))
        steps.append(_("  Windows: {windows}").format(windows=windows))
        steps.append(_("  Occupants: {occupants}").format(occupants=occupants))
        steps.append(_("  Appliances: {appliances} watts").format(appliances=appliances))
        steps.append("")
        
        if unit == 'sqm':
            steps.append(_("Step 2: Convert Area to Square Feet"))
            steps.append(_("  Area = {sqm} m² × 10.764 = {sqft:.2f} sq ft").format(sqm=area, sqft=area_sqft))
            steps.append("")
        
        steps.append(_("Step 3: Calculate Base Cooling BTU"))
        steps.append(_("  Room Type: {room_type} ({btu_per_sqft} BTU per sq ft for cooling)").format(
            room_type=room_type.replace('_', ' ').title(), btu_per_sqft=base_btu_per_sqft
        ))
        steps.append(_("  Base BTU = Area × BTU per sq ft"))
        steps.append(_("  Base BTU = {area:.2f} × {btu_per_sqft} = {base_btu:.2f} BTU").format(
            area=area_sqft, btu_per_sqft=base_btu_per_sqft, base_btu=base_btu
        ))
        steps.append("")
        
        steps.append(_("Step 4: Apply Multipliers"))
        steps.append(_("  Insulation: {insulation} (× {mult})").format(
            insulation=insulation.replace('_', ' ').title(), mult=insulation_mult
        ))
        steps.append(_("  Climate Zone: {climate} (× {mult})").format(
            climate=climate_zone.replace('_', ' ').title(), mult=climate_mult
        ))
        steps.append(_("  Adjusted Base BTU = {base:.2f} × {ins_mult} × {clim_mult} = {adjusted:.2f} BTU").format(
            base=base_btu, ins_mult=insulation_mult, clim_mult=climate_mult,
            adjusted=base_btu * insulation_mult * climate_mult
        ))
        steps.append("")
        
        steps.append(_("Step 5: Add Additional Loads"))
        steps.append(_("  Window Load: {windows} windows × 1000 BTU = {window_btu:.2f} BTU").format(
            windows=windows, window_btu=window_btu
        ))
        steps.append(_("  Occupant Load: {occupants} people × 400 BTU = {occupant_btu:.2f} BTU").format(
            occupants=occupants, occupant_btu=occupant_btu
        ))
        steps.append(_("  Appliance Load: {watts} W × 3.412 = {appliance_btu:.2f} BTU").format(
            watts=appliances, appliance_btu=appliance_btu
        ))
        steps.append("")
        
        steps.append(_("Step 6: Calculate Total Cooling BTU"))
        steps.append(_("  Total BTU = Adjusted Base + Windows + Occupants + Appliances"))
        steps.append(_("  Total BTU = {adjusted:.2f} + {win:.2f} + {occ:.2f} + {app:.2f} = {total:.2f} BTU").format(
            adjusted=base_btu * insulation_mult * climate_mult,
            win=window_btu, occ=occupant_btu, app=appliance_btu, total=total_btu
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_chart_data(self, total_btu, conversions, room_type):
        """Prepare chart data for BTU visualization"""
        chart_data = {}
        
        try:
            # Energy units comparison chart (normalized for better visualization)
            # Normalize values to show relative comparison
            max_value = max(total_btu, conversions['kwh'] * 1000, conversions['joules'] / 1000, 
                          conversions['calories'] / 100, conversions['foot_pounds'] / 100)
            
            chart_data['energy_units_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': ['BTU', 'kWh', 'Joules (×1000)', 'Calories (×100)', 'Foot-Pounds (×100)'],
                    'datasets': [{
                        'label': str(_('Energy Units (Normalized)')),
                        'data': [
                            round(total_btu, 2),
                            round(conversions['kwh'] * 1000, 2),
                            round(conversions['joules'] / 1000, 2),
                            round(conversions['calories'] / 100, 2),
                            round(conversions['foot_pounds'] / 100, 2)
                        ],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(239, 68, 68, 0.6)',
                            'rgba(139, 92, 246, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444',
                            '#8b5cf6'
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
                        },
                        'tooltip': {
                            'callbacks': {
                                'label': 'function(context) { return context.dataset.label + ": " + context.parsed.y.toLocaleString(); }'
                            }
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'ticks': {
                                'callback': 'function(value) { return value.toLocaleString(); }'
                            }
                        }
                    }
                }
            }
            
            # BTU gauge chart (doughnut)
            chart_data['btu_gauge_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': [str(_('Required BTU')), str(_('Remaining'))],
                    'datasets': [{
                        'data': [round(total_btu, 2), max(0, 50000 - total_btu)],
                        'backgroundColor': ['rgba(59, 130, 246, 0.8)', 'rgba(229, 231, 235, 0.5)'],
                        'borderColor': ['#3b82f6', '#e5e7eb'],
                        'borderWidth': 2,
                        'cutout': '75%'
                    }]
                },
                'options': {
                    'responsive': True,
                    'plugins': {
                        'legend': {
                            'display': True
                        }
                    }
                },
                'center_text': {
                    'value': round(total_btu, 0),
                    'label': str(_('BTU')),
                    'color': '#3b82f6'
                }
            }
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
    
    def _prepare_cooling_chart_data(self, total_btu, base_btu, window_btu, occupant_btu, appliance_btu):
        """Prepare chart data for cooling load breakdown"""
        chart_data = {}
        
        try:
            # Cooling load breakdown pie chart
            adjusted_base = total_btu - window_btu - occupant_btu - appliance_btu
            chart_data['cooling_load_chart'] = {
                'type': 'doughnut',
                'data': {
                    'labels': [
                        str(_('Base Load')),
                        str(_('Windows')),
                        str(_('Occupants')),
                        str(_('Appliances'))
                    ],
                    'datasets': [{
                        'data': [
                            adjusted_base,
                            window_btu,
                            occupant_btu,
                            appliance_btu
                        ],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(239, 68, 68, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444'
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
