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
class TileCalculator(View):
    """
    Professional Tile Calculator with Comprehensive Features
    
    This calculator provides tile calculations with:
    - Calculate number of tiles needed for an area
    - Calculate area coverage from tiles
    - Calculate cost estimates
    - Account for waste factor
    - Calculate grout needed
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/tile_calculator.html'
    
    # Area conversion factors (to square feet)
    AREA_CONVERSIONS = {
        'square_feet': 1.0,
        'square_meters': 10.764,  # 1 m² = 10.764 ft²
        'square_yards': 9.0,  # 1 yd² = 9 ft²
        'square_inches': 0.00694444,  # 1 in² = 0.00694444 ft²
    }
    
    # Length conversion factors (to inches)
    LENGTH_CONVERSIONS = {
        'inches': 1.0,
        'feet': 12.0,  # 1 ft = 12 in
        'meters': 39.3701,  # 1 m = 39.3701 in
        'centimeters': 0.393701,  # 1 cm = 0.393701 in
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'square_feet': 'ft²',
            'square_meters': 'm²',
            'square_yards': 'yd²',
            'square_inches': 'in²',
            'inches': 'in',
            'feet': 'ft',
            'meters': 'm',
            'centimeters': 'cm',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Tile Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'tiles_needed')
            
            if calc_type == 'tiles_needed':
                return self._calculate_tiles_needed(data)
            elif calc_type == 'coverage':
                return self._calculate_coverage(data)
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
    
    def _calculate_tiles_needed(self, data):
        """Calculate number of tiles needed for an area"""
        try:
            if 'area' not in data or data.get('area') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Area is required.')
                }, status=400)
            
            if 'tile_length' not in data or data.get('tile_length') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile length is required.')
                }, status=400)
            
            if 'tile_width' not in data or data.get('tile_width') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile width is required.')
                }, status=400)
            
            try:
                area = float(data.get('area', 0))
                tile_length = float(data.get('tile_length', 0))
                tile_width = float(data.get('tile_width', 0))
                waste_factor = float(data.get('waste_factor', 10))  # Default 10%
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            area_unit = data.get('area_unit', 'square_feet')
            tile_unit = data.get('tile_unit', 'inches')
            
            # Validate
            if area <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Area must be greater than zero.')
                }, status=400)
            
            if tile_length <= 0 or tile_width <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile dimensions must be greater than zero.')
                }, status=400)
            
            if waste_factor < 0 or waste_factor > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Waste factor must be between 0 and 50 percent.')
                }, status=400)
            
            # Convert to base units (square feet and square inches)
            area_ft2 = float(area * self.AREA_CONVERSIONS[area_unit])
            area_in2 = float(area_ft2 * 144)  # 1 ft² = 144 in²
            
            # Convert tile dimensions to inches
            tile_length_in = float(tile_length * self.LENGTH_CONVERSIONS[tile_unit])
            tile_width_in = float(tile_width * self.LENGTH_CONVERSIONS[tile_unit])
            
            # Calculate tile area in square inches
            tile_area_in2 = float(np.multiply(tile_length_in, tile_width_in))
            
            # Calculate number of tiles needed (without waste)
            tiles_needed = float(np.divide(area_in2, tile_area_in2))
            
            # Add waste factor
            tiles_with_waste = float(np.multiply(tiles_needed, 1.0 + waste_factor / 100.0))
            tiles_to_buy = int(np.ceil(tiles_with_waste))
            
            # Calculate grout needed (approximate: 1 lb per 10 ft²)
            grout_needed = float(np.divide(area_ft2, 10.0))
            
            steps = self._prepare_tiles_needed_steps(area, area_unit, area_ft2, area_in2, tile_length, tile_width, tile_unit, tile_length_in, tile_width_in, tile_area_in2, tiles_needed, waste_factor, tiles_with_waste, tiles_to_buy, grout_needed)
            chart_data = self._prepare_tiles_chart_data(tiles_to_buy, area_ft2)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'tiles_needed',
                'area': area,
                'area_unit': area_unit,
                'tile_length': tile_length,
                'tile_width': tile_width,
                'tile_unit': tile_unit,
                'waste_factor': waste_factor,
                'tiles_needed': tiles_to_buy,
                'tiles_exact': round(tiles_needed, 2),
                'tiles_with_waste': round(tiles_with_waste, 2),
                'grout_needed': round(grout_needed, 2),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating tiles needed: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_coverage(self, data):
        """Calculate area coverage from number of tiles"""
        try:
            if 'num_tiles' not in data or data.get('num_tiles') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of tiles is required.')
                }, status=400)
            
            if 'tile_length' not in data or data.get('tile_length') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile length is required.')
                }, status=400)
            
            if 'tile_width' not in data or data.get('tile_width') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile width is required.')
                }, status=400)
            
            try:
                num_tiles = int(data.get('num_tiles', 0))
                tile_length = float(data.get('tile_length', 0))
                tile_width = float(data.get('tile_width', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            tile_unit = data.get('tile_unit', 'inches')
            result_unit = data.get('result_unit', 'square_feet')
            
            # Validate
            if num_tiles <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of tiles must be greater than zero.')
                }, status=400)
            
            if tile_length <= 0 or tile_width <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile dimensions must be greater than zero.')
                }, status=400)
            
            # Convert tile dimensions to inches
            tile_length_in = float(tile_length * self.LENGTH_CONVERSIONS[tile_unit])
            tile_width_in = float(tile_width * self.LENGTH_CONVERSIONS[tile_unit])
            
            # Calculate tile area in square inches
            tile_area_in2 = float(np.multiply(tile_length_in, tile_width_in))
            
            # Calculate total coverage in square inches
            total_area_in2 = float(np.multiply(tile_area_in2, num_tiles))
            
            # Convert to square feet
            total_area_ft2 = float(np.divide(total_area_in2, 144))
            
            # Convert to result unit
            result = float(np.multiply(total_area_ft2, self.AREA_CONVERSIONS[result_unit] / self.AREA_CONVERSIONS['square_feet']))
            
            steps = self._prepare_coverage_steps(num_tiles, tile_length, tile_width, tile_unit, tile_length_in, tile_width_in, tile_area_in2, total_area_in2, total_area_ft2, result, result_unit)
            chart_data = self._prepare_coverage_chart_data(total_area_ft2, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'coverage',
                'num_tiles': num_tiles,
                'tile_length': tile_length,
                'tile_width': tile_width,
                'tile_unit': tile_unit,
                'coverage': round(result, 4),
                'result_unit': result_unit,
                'coverage_ft2': round(total_area_ft2, 4),
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating coverage: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_cost(self, data):
        """Calculate tile cost estimate"""
        try:
            if 'area' not in data or data.get('area') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Area is required.')
                }, status=400)
            
            if 'tile_length' not in data or data.get('tile_length') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile length is required.')
                }, status=400)
            
            if 'tile_width' not in data or data.get('tile_width') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile width is required.')
                }, status=400)
            
            if 'price_per_tile' not in data or data.get('price_per_tile') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Price per tile is required.')
                }, status=400)
            
            try:
                area = float(data.get('area', 0))
                tile_length = float(data.get('tile_length', 0))
                tile_width = float(data.get('tile_width', 0))
                price_per_tile = float(data.get('price_per_tile', 0))
                grout_cost = float(data.get('grout_cost', 0))
                labor_cost = float(data.get('labor_cost', 0))
                waste_factor = float(data.get('waste_factor', 10))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            area_unit = data.get('area_unit', 'square_feet')
            tile_unit = data.get('tile_unit', 'inches')
            currency = data.get('currency', 'usd')
            
            # Validate
            if area <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Area must be greater than zero.')
                }, status=400)
            
            if tile_length <= 0 or tile_width <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Tile dimensions must be greater than zero.')
                }, status=400)
            
            if price_per_tile < 0 or grout_cost < 0 or labor_cost < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Prices must be non-negative.')
                }, status=400)
            
            # Convert to base units
            area_ft2 = float(area * self.AREA_CONVERSIONS[area_unit])
            area_in2 = float(area_ft2 * 144)
            
            tile_length_in = float(tile_length * self.LENGTH_CONVERSIONS[tile_unit])
            tile_width_in = float(tile_width * self.LENGTH_CONVERSIONS[tile_unit])
            
            # Calculate tiles needed
            tile_area_in2 = float(np.multiply(tile_length_in, tile_width_in))
            tiles_needed = float(np.divide(area_in2, tile_area_in2))
            tiles_with_waste = float(np.multiply(tiles_needed, 1.0 + waste_factor / 100.0))
            tiles_to_buy = int(np.ceil(tiles_with_waste))
            
            # Calculate costs
            tile_cost = float(np.multiply(tiles_to_buy, price_per_tile))
            grout_needed = float(np.divide(area_ft2, 10.0))
            grout_total = float(np.multiply(grout_needed, grout_cost))
            total_cost = float(np.add(np.add(tile_cost, grout_total), labor_cost))
            
            steps = self._prepare_cost_steps(area, area_unit, area_ft2, tile_length, tile_width, tile_unit, tiles_to_buy, price_per_tile, waste_factor, tile_cost, grout_needed, grout_cost, grout_total, labor_cost, total_cost, currency)
            chart_data = self._prepare_cost_chart_data(tile_cost, grout_total, labor_cost, total_cost)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'cost',
                'area': area,
                'area_unit': area_unit,
                'tiles_needed': tiles_to_buy,
                'tile_cost': round(tile_cost, 2),
                'grout_cost': round(grout_total, 2),
                'labor_cost': labor_cost,
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
    def _prepare_tiles_needed_steps(self, area, area_unit, area_ft2, area_in2, tile_length, tile_width, tile_unit, tile_length_in, tile_width_in, tile_area_in2, tiles_needed, waste_factor, tiles_with_waste, tiles_to_buy, grout_needed):
        """Prepare step-by-step solution for tiles needed calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Area: {area} {unit}').format(area=area, unit=self._format_unit(area_unit)))
        steps.append(_('Tile Length: {length} {unit}').format(length=tile_length, unit=self._format_unit(tile_unit)))
        steps.append(_('Tile Width: {width} {unit}').format(width=tile_width, unit=self._format_unit(tile_unit)))
        steps.append(_('Waste Factor: {waste}%').format(waste=waste_factor))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        steps.append(_('Area: {area} ft² = {area_in} in²').format(area=area_ft2, area_in=area_in2))
        steps.append(_('Tile Length: {length} in').format(length=tile_length_in))
        steps.append(_('Tile Width: {width} in').format(width=tile_width_in))
        steps.append('')
        steps.append(_('Step 3: Calculate tile area'))
        steps.append(_('Tile Area = Length × Width'))
        steps.append(_('Tile Area = {length} × {width} = {area} in²').format(length=tile_length_in, width=tile_width_in, area=tile_area_in2))
        steps.append('')
        steps.append(_('Step 4: Calculate tiles needed'))
        steps.append(_('Tiles Needed = Area / Tile Area'))
        steps.append(_('Tiles Needed = {area} / {tile_area} = {tiles} tiles').format(area=area_in2, tile_area=tile_area_in2, tiles=round(tiles_needed, 2)))
        steps.append('')
        steps.append(_('Step 5: Add waste factor'))
        steps.append(_('Tiles with Waste = Tiles Needed × (1 + Waste Factor / 100)'))
        steps.append(_('Tiles with Waste = {tiles} × (1 + {waste} / 100) = {tiles_waste} tiles').format(tiles=round(tiles_needed, 2), waste=waste_factor, tiles_waste=round(tiles_with_waste, 2)))
        steps.append('')
        steps.append(_('Step 6: Round up to whole tiles'))
        steps.append(_('Tiles to Buy = {tiles} tiles').format(tiles=tiles_to_buy))
        steps.append('')
        steps.append(_('Step 7: Calculate grout needed'))
        steps.append(_('Grout Needed ≈ {grout} lbs (approximately 1 lb per 10 ft²)').format(grout=round(grout_needed, 2)))
        return steps
    
    def _prepare_coverage_steps(self, num_tiles, tile_length, tile_width, tile_unit, tile_length_in, tile_width_in, tile_area_in2, total_area_in2, total_area_ft2, result, result_unit):
        """Prepare step-by-step solution for coverage calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Number of Tiles: {num}').format(num=num_tiles))
        steps.append(_('Tile Length: {length} {unit}').format(length=tile_length, unit=self._format_unit(tile_unit)))
        steps.append(_('Tile Width: {width} {unit}').format(width=tile_width, unit=self._format_unit(tile_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (inches)'))
        steps.append(_('Tile Length: {length} in').format(length=tile_length_in))
        steps.append(_('Tile Width: {width} in').format(width=tile_width_in))
        steps.append('')
        steps.append(_('Step 3: Calculate tile area'))
        steps.append(_('Tile Area = Length × Width'))
        steps.append(_('Tile Area = {length} × {width} = {area} in²').format(length=tile_length_in, width=tile_width_in, area=tile_area_in2))
        steps.append('')
        steps.append(_('Step 4: Calculate total coverage'))
        steps.append(_('Total Coverage = Tile Area × Number of Tiles'))
        steps.append(_('Total Coverage = {area} × {num} = {total} in²').format(area=tile_area_in2, num=num_tiles, total=total_area_in2))
        steps.append(_('Total Coverage = {area} ft²').format(area=total_area_ft2))
        steps.append('')
        if result_unit != 'square_feet':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('Coverage = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('Coverage = {result} ft²').format(result=result))
        return steps
    
    def _prepare_cost_steps(self, area, area_unit, area_ft2, tile_length, tile_width, tile_unit, tiles_to_buy, price_per_tile, waste_factor, tile_cost, grout_needed, grout_cost, grout_total, labor_cost, total_cost, currency):
        """Prepare step-by-step solution for cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Area: {area} {unit}').format(area=area, unit=self._format_unit(area_unit)))
        steps.append(_('Tile Size: {length} × {width} {unit}').format(length=tile_length, width=tile_width, unit=self._format_unit(tile_unit)))
        steps.append(_('Price per Tile: {price} {currency}').format(price=price_per_tile, currency=currency.upper()))
        steps.append(_('Waste Factor: {waste}%').format(waste=waste_factor))
        steps.append('')
        steps.append(_('Step 2: Calculate tiles needed (with waste)'))
        steps.append(_('Tiles to Buy: {tiles} tiles').format(tiles=tiles_to_buy))
        steps.append('')
        steps.append(_('Step 3: Calculate tile cost'))
        steps.append(_('Tile Cost = Tiles × Price per Tile'))
        steps.append(_('Tile Cost = {tiles} × {price} = {cost} {currency}').format(tiles=tiles_to_buy, price=price_per_tile, cost=round(tile_cost, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 4: Calculate grout cost'))
        steps.append(_('Grout Needed ≈ {grout} lbs').format(grout=round(grout_needed, 2)))
        steps.append(_('Grout Cost = {grout} × {price} = {cost} {currency}').format(grout=round(grout_needed, 2), price=grout_cost, cost=round(grout_total, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 5: Calculate total cost'))
        steps.append(_('Total Cost = Tile Cost + Grout Cost + Labor Cost'))
        steps.append(_('Total Cost = {tile} + {grout} + {labor} = {total} {currency}').format(tile=round(tile_cost, 2), grout=round(grout_total, 2), labor=labor_cost, total=round(total_cost, 2), currency=currency.upper()))
        return steps
    
    # Chart data preparation methods
    def _prepare_tiles_chart_data(self, tiles_to_buy, area_ft2):
        """Prepare chart data for tiles visualization"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Tiles Needed'), _('Area (ft²)')],
                    'datasets': [{
                        'label': _('Value'),
                        'data': [tiles_to_buy, area_ft2],
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
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Tiles Needed Calculation')
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
            return {'tiles_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_coverage_chart_data(self, total_area_ft2, result_unit):
        """Prepare chart data for coverage visualization"""
        try:
            result = float(total_area_ft2 * self.AREA_CONVERSIONS[result_unit] / self.AREA_CONVERSIONS['square_feet'])
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Coverage')],
                    'datasets': [{
                        'label': _('Area ({unit})').format(unit=self._format_unit(result_unit)),
                        'data': [result],
                        'backgroundColor': 'rgba(16, 185, 129, 0.8)',
                        'borderColor': '#10b981',
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
                            'text': _('Tile Coverage')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Area ({unit})').format(unit=self._format_unit(result_unit))
                            }
                        }
                    }
                }
            }
            return {'coverage_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_cost_chart_data(self, tile_cost, grout_cost, labor_cost, total_cost):
        """Prepare chart data for cost visualization"""
        try:
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': [_('Tile Cost'), _('Grout Cost'), _('Labor Cost')],
                    'datasets': [{
                        'data': [tile_cost, grout_cost, labor_cost],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(234, 179, 8, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#eab308'
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
                            'text': _('Cost Breakdown (Total: {total})').format(total=total_cost)
                        }
                    }
                }
            }
            return {'cost_chart': chart_config}
        except Exception as e:
            return None
