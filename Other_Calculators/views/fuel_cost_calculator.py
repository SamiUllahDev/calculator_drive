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
class FuelCostCalculator(View):
    """
    Professional Fuel Cost Calculator with Comprehensive Features
    
    This calculator provides fuel cost calculations with:
    - Calculate total fuel cost for a trip
    - Calculate fuel cost per distance unit
    - Calculate fuel efficiency (MPG, L/100km)
    - Calculate distance from fuel and efficiency
    - Calculate fuel needed for a distance
    - Unit conversions (gallons/liters, miles/km, etc.)
    
    Features:
    - Supports multiple calculation modes
    - Handles various units (imperial and metric)
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/fuel_cost_calculator.html'
    
    # Distance conversion factors (to miles)
    DISTANCE_CONVERSIONS = {
        'miles': 1.0,
        'km': 0.621371,  # 1 km = 0.621371 miles
    }
    
    # Fuel volume conversion factors (to gallons)
    FUEL_VOLUME_CONVERSIONS = {
        'gallons': 1.0,
        'liters': 0.264172,  # 1 liter = 0.264172 gallons
    }
    
    # Fuel price conversion factors (to USD per gallon)
    PRICE_CONVERSIONS = {
        'per_gallon': 1.0,
        'per_liter': 3.78541,  # 1 USD/L = 3.78541 USD/gal
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'miles': 'miles',
            'km': 'km',
            'gallons': 'gallons',
            'liters': 'liters',
            'per_gallon': 'per gallon',
            'per_liter': 'per liter',
            'mpg': 'MPG',
            'l_per_100km': 'L/100km',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Fuel Cost Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'total_cost')
            
            if calc_type == 'total_cost':
                return self._calculate_total_cost(data)
            elif calc_type == 'cost_per_distance':
                return self._calculate_cost_per_distance(data)
            elif calc_type == 'fuel_efficiency':
                return self._calculate_fuel_efficiency(data)
            elif calc_type == 'distance':
                return self._calculate_distance(data)
            elif calc_type == 'fuel_needed':
                return self._calculate_fuel_needed(data)
            elif calc_type == 'convert_distance':
                return self._convert_distance_units(data)
            elif calc_type == 'convert_fuel':
                return self._convert_fuel_units(data)
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
    
    def _calculate_total_cost(self, data):
        """Calculate total fuel cost for a trip"""
        try:
            # Check for required fields
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'fuel_efficiency' not in data or data.get('fuel_efficiency') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency is required.')
                }, status=400)
            
            if 'fuel_price' not in data or data.get('fuel_price') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                fuel_efficiency = float(data.get('fuel_efficiency', 0))
                fuel_price = float(data.get('fuel_price', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            efficiency_unit = data.get('efficiency_unit', 'mpg')
            price_unit = data.get('price_unit', 'per_gallon')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            if efficiency_unit not in ['mpg', 'l_per_100km']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid efficiency unit.')
                }, status=400)
            
            if price_unit not in self.PRICE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid price unit.')
                }, status=400)
            
            # Validate ranges
            if distance < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be non-negative.')
                }, status=400)
            
            if fuel_efficiency <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency must be greater than zero.')
                }, status=400)
            
            if fuel_price < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price must be non-negative.')
                }, status=400)
            
            if distance > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            if fuel_efficiency > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            if fuel_price > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            # Convert to base units (miles and gallons)
            distance_miles = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Convert efficiency to MPG
            if efficiency_unit == 'mpg':
                mpg = fuel_efficiency
            else:  # l_per_100km
                # Convert L/100km to MPG: MPG = 235.214 / (L/100km)
                mpg = float(235.214 / fuel_efficiency)
            
            # Calculate fuel needed in gallons
            fuel_gallons = float(np.divide(distance_miles, mpg))
            
            # Convert price to USD per gallon
            price_per_gallon = float(fuel_price * self.PRICE_CONVERSIONS[price_unit])
            
            # Calculate total cost
            total_cost = float(np.multiply(fuel_gallons, price_per_gallon))
            
            # Validate result
            if math.isinf(total_cost) or math.isnan(total_cost) or np.isinf(total_cost) or np.isnan(total_cost):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_total_cost_steps(distance, distance_unit, fuel_efficiency, efficiency_unit, fuel_price, price_unit, total_cost, distance_miles, mpg, fuel_gallons, price_per_gallon)
            
            # Prepare chart data
            chart_data = self._prepare_total_cost_chart_data(distance_miles, fuel_gallons, total_cost)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'total_cost',
                'distance': distance,
                'distance_unit': distance_unit,
                'fuel_efficiency': fuel_efficiency,
                'efficiency_unit': efficiency_unit,
                'fuel_price': fuel_price,
                'price_unit': price_unit,
                'total_cost': total_cost,
                'fuel_needed': fuel_gallons,
                'fuel_needed_liters': float(fuel_gallons / self.FUEL_VOLUME_CONVERSIONS['liters']),
                'distance_miles': distance_miles,
                'mpg': mpg,
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
                'error': _('Error calculating total cost: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_cost_per_distance(self, data):
        """Calculate fuel cost per distance unit"""
        try:
            if 'fuel_efficiency' not in data or data.get('fuel_efficiency') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency is required.')
                }, status=400)
            
            if 'fuel_price' not in data or data.get('fuel_price') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price is required.')
                }, status=400)
            
            try:
                fuel_efficiency = float(data.get('fuel_efficiency', 0))
                fuel_price = float(data.get('fuel_price', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            efficiency_unit = data.get('efficiency_unit', 'mpg')
            price_unit = data.get('price_unit', 'per_gallon')
            result_unit = data.get('result_unit', 'miles')
            
            # Validate units
            if efficiency_unit not in ['mpg', 'l_per_100km']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid efficiency unit.')
                }, status=400)
            
            if price_unit not in self.PRICE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid price unit.')
                }, status=400)
            
            if result_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if fuel_efficiency <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency must be greater than zero.')
                }, status=400)
            
            if fuel_price < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price must be non-negative.')
                }, status=400)
            
            # Convert efficiency to MPG
            if efficiency_unit == 'mpg':
                mpg = fuel_efficiency
            else:  # l_per_100km
                mpg = float(235.214 / fuel_efficiency)
            
            # Convert price to USD per gallon
            price_per_gallon = float(fuel_price * self.PRICE_CONVERSIONS[price_unit])
            
            # Calculate cost per mile
            cost_per_mile = float(np.divide(price_per_gallon, mpg))
            
            # Convert to result unit
            if result_unit == 'miles':
                cost_per_distance = cost_per_mile
            else:  # km
                cost_per_distance = float(cost_per_mile / self.DISTANCE_CONVERSIONS['km'])
            
            # Validate result
            if math.isinf(cost_per_distance) or math.isnan(cost_per_distance) or np.isinf(cost_per_distance) or np.isnan(cost_per_distance):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_cost_per_distance_steps(fuel_efficiency, efficiency_unit, fuel_price, price_unit, cost_per_distance, result_unit, mpg, price_per_gallon)
            
            chart_data = self._prepare_cost_per_distance_chart_data(mpg, price_per_gallon, cost_per_mile)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'cost_per_distance',
                'fuel_efficiency': fuel_efficiency,
                'efficiency_unit': efficiency_unit,
                'fuel_price': fuel_price,
                'price_unit': price_unit,
                'cost_per_distance': cost_per_distance,
                'result_unit': result_unit,
                'mpg': mpg,
                'price_per_gallon': price_per_gallon,
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
                'error': _('Error calculating cost per distance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_fuel_efficiency(self, data):
        """Calculate fuel efficiency from distance and fuel used"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'fuel_used' not in data or data.get('fuel_used') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                fuel_used = float(data.get('fuel_used', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            fuel_unit = data.get('fuel_unit', 'gallons')
            result_unit = data.get('result_unit', 'mpg')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            if fuel_unit not in self.FUEL_VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid fuel unit.')
                }, status=400)
            
            if result_unit not in ['mpg', 'l_per_100km']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            if fuel_used <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            distance_miles = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            fuel_gallons = float(fuel_used * self.FUEL_VOLUME_CONVERSIONS[fuel_unit])
            
            # Calculate MPG
            mpg = float(np.divide(distance_miles, fuel_gallons))
            
            # Convert to result unit
            if result_unit == 'mpg':
                efficiency = mpg
            else:  # l_per_100km
                efficiency = float(235.214 / mpg)
            
            # Validate result
            if math.isinf(efficiency) or math.isnan(efficiency) or np.isinf(efficiency) or np.isnan(efficiency):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_fuel_efficiency_steps(distance, distance_unit, fuel_used, fuel_unit, efficiency, result_unit, distance_miles, fuel_gallons, mpg)
            
            chart_data = self._prepare_fuel_efficiency_chart_data(distance_miles, fuel_gallons, mpg)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'fuel_efficiency',
                'distance': distance,
                'distance_unit': distance_unit,
                'fuel_used': fuel_used,
                'fuel_unit': fuel_unit,
                'efficiency': efficiency,
                'result_unit': result_unit,
                'distance_miles': distance_miles,
                'fuel_gallons': fuel_gallons,
                'mpg': mpg,
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
                'error': _('Error calculating fuel efficiency: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_distance(self, data):
        """Calculate distance from fuel used and efficiency"""
        try:
            if 'fuel_used' not in data or data.get('fuel_used') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used is required.')
                }, status=400)
            
            if 'fuel_efficiency' not in data or data.get('fuel_efficiency') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency is required.')
                }, status=400)
            
            try:
                fuel_used = float(data.get('fuel_used', 0))
                fuel_efficiency = float(data.get('fuel_efficiency', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            fuel_unit = data.get('fuel_unit', 'gallons')
            efficiency_unit = data.get('efficiency_unit', 'mpg')
            result_unit = data.get('result_unit', 'miles')
            
            # Validate units
            if fuel_unit not in self.FUEL_VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid fuel unit.')
                }, status=400)
            
            if efficiency_unit not in ['mpg', 'l_per_100km']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid efficiency unit.')
                }, status=400)
            
            if result_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if fuel_used <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used must be greater than zero.')
                }, status=400)
            
            if fuel_efficiency <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            fuel_gallons = float(fuel_used * self.FUEL_VOLUME_CONVERSIONS[fuel_unit])
            
            # Convert efficiency to MPG
            if efficiency_unit == 'mpg':
                mpg = fuel_efficiency
            else:  # l_per_100km
                mpg = float(235.214 / fuel_efficiency)
            
            # Calculate distance in miles
            distance_miles = float(np.multiply(fuel_gallons, mpg))
            
            # Convert to result unit
            if result_unit == 'miles':
                distance_result = distance_miles
            else:  # km
                distance_result = float(distance_miles / self.DISTANCE_CONVERSIONS['km'])
            
            # Validate result
            if math.isinf(distance_result) or math.isnan(distance_result) or np.isinf(distance_result) or np.isnan(distance_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_distance_steps(fuel_used, fuel_unit, fuel_efficiency, efficiency_unit, distance_result, result_unit, fuel_gallons, mpg, distance_miles)
            
            chart_data = self._prepare_distance_chart_data(fuel_gallons, mpg, distance_miles)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'distance',
                'fuel_used': fuel_used,
                'fuel_unit': fuel_unit,
                'fuel_efficiency': fuel_efficiency,
                'efficiency_unit': efficiency_unit,
                'distance': distance_result,
                'result_unit': result_unit,
                'fuel_gallons': fuel_gallons,
                'mpg': mpg,
                'distance_miles': distance_miles,
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
                'error': _('Error calculating distance: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_fuel_needed(self, data):
        """Calculate fuel needed for a distance"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'fuel_efficiency' not in data or data.get('fuel_efficiency') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                fuel_efficiency = float(data.get('fuel_efficiency', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            efficiency_unit = data.get('efficiency_unit', 'mpg')
            result_unit = data.get('result_unit', 'gallons')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            if efficiency_unit not in ['mpg', 'l_per_100km']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid efficiency unit.')
                }, status=400)
            
            if result_unit not in self.FUEL_VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            if fuel_efficiency <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            distance_miles = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Convert efficiency to MPG
            if efficiency_unit == 'mpg':
                mpg = fuel_efficiency
            else:  # l_per_100km
                mpg = float(235.214 / fuel_efficiency)
            
            # Calculate fuel needed in gallons
            fuel_gallons = float(np.divide(distance_miles, mpg))
            
            # Convert to result unit
            if result_unit == 'gallons':
                fuel_result = fuel_gallons
            else:  # liters
                fuel_result = float(fuel_gallons / self.FUEL_VOLUME_CONVERSIONS['liters'])
            
            # Validate result
            if math.isinf(fuel_result) or math.isnan(fuel_result) or np.isinf(fuel_result) or np.isnan(fuel_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_fuel_needed_steps(distance, distance_unit, fuel_efficiency, efficiency_unit, fuel_result, result_unit, distance_miles, mpg, fuel_gallons)
            
            chart_data = self._prepare_fuel_needed_chart_data(distance_miles, mpg, fuel_gallons)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'fuel_needed',
                'distance': distance,
                'distance_unit': distance_unit,
                'fuel_efficiency': fuel_efficiency,
                'efficiency_unit': efficiency_unit,
                'fuel_needed': fuel_result,
                'result_unit': result_unit,
                'distance_miles': distance_miles,
                'mpg': mpg,
                'fuel_gallons': fuel_gallons,
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
                'error': _('Error calculating fuel needed: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_distance_units(self, data):
        """Convert distance units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'miles')
            to_unit = data.get('to_unit', 'miles')
            
            # Validate units
            if from_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid source unit.')
                }, status=400)
            
            if to_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid target unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be non-negative.')
                }, status=400)
            
            # Convert to miles first, then to target unit
            miles_value = float(value * self.DISTANCE_CONVERSIONS[from_unit])
            result = float(miles_value / self.DISTANCE_CONVERSIONS[to_unit])
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_distance_steps(value, from_unit, to_unit, result, miles_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_distance',
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
    
    def _convert_fuel_units(self, data):
        """Convert fuel volume units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'gallons')
            to_unit = data.get('to_unit', 'gallons')
            
            # Validate units
            if from_unit not in self.FUEL_VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid source unit.')
                }, status=400)
            
            if to_unit not in self.FUEL_VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid target unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel volume must be non-negative.')
                }, status=400)
            
            # Convert to gallons first, then to target unit
            gallons_value = float(value * self.FUEL_VOLUME_CONVERSIONS[from_unit])
            result = float(gallons_value / self.FUEL_VOLUME_CONVERSIONS[to_unit])
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_fuel_steps(value, from_unit, to_unit, result, gallons_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_fuel',
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
    def _prepare_total_cost_steps(self, distance, distance_unit, fuel_efficiency, efficiency_unit, fuel_price, price_unit, total_cost, distance_miles, mpg, fuel_gallons, price_per_gallon):
        """Prepare step-by-step solution for total cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {dist} {unit}').format(dist=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Fuel Efficiency: {eff} {unit}').format(eff=fuel_efficiency, unit=self._format_unit(efficiency_unit)))
        steps.append(_('Fuel Price: ${price} {unit}').format(price=fuel_price, unit=self._format_unit(price_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if distance_unit != 'miles':
            steps.append(_('Distance in miles: {dist} miles').format(dist=distance_miles))
        if efficiency_unit != 'mpg':
            steps.append(_('Efficiency in MPG: {mpg} MPG').format(mpg=mpg))
            steps.append(_('Formula: MPG = 235.214 / (L/100km)'))
        if price_unit != 'per_gallon':
            steps.append(_('Price per gallon: ${price}/gallon').format(price=price_per_gallon))
        steps.append('')
        steps.append(_('Step 3: Calculate fuel needed'))
        steps.append(_('Formula: Fuel = Distance / Efficiency'))
        steps.append(_('Fuel = {dist} miles / {mpg} MPG').format(dist=distance_miles, mpg=mpg))
        steps.append(_('Fuel = {fuel} gallons').format(fuel=fuel_gallons))
        steps.append('')
        steps.append(_('Step 4: Calculate total cost'))
        steps.append(_('Formula: Cost = Fuel × Price'))
        steps.append(_('Cost = {fuel} gallons × ${price}/gallon').format(fuel=fuel_gallons, price=price_per_gallon))
        steps.append(_('Total Cost = ${cost}').format(cost=total_cost))
        return steps
    
    def _prepare_cost_per_distance_steps(self, fuel_efficiency, efficiency_unit, fuel_price, price_unit, cost_per_distance, result_unit, mpg, price_per_gallon):
        """Prepare step-by-step solution for cost per distance calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Fuel Efficiency: {eff} {unit}').format(eff=fuel_efficiency, unit=self._format_unit(efficiency_unit)))
        steps.append(_('Fuel Price: ${price} {unit}').format(price=fuel_price, unit=self._format_unit(price_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if efficiency_unit != 'mpg':
            steps.append(_('Efficiency in MPG: {mpg} MPG').format(mpg=mpg))
        if price_unit != 'per_gallon':
            steps.append(_('Price per gallon: ${price}/gallon').format(price=price_per_gallon))
        steps.append('')
        steps.append(_('Step 3: Calculate cost per mile'))
        steps.append(_('Formula: Cost per mile = Price per gallon / MPG'))
        steps.append(_('Cost per mile = ${price}/gallon / {mpg} MPG').format(price=price_per_gallon, mpg=mpg))
        cost_per_mile = float(price_per_gallon / mpg)
        steps.append(_('Cost per mile = ${cost}').format(cost=cost_per_mile))
        steps.append('')
        if result_unit != 'miles':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Cost per {unit} = ${cost}').format(unit=self._format_unit(result_unit), cost=cost_per_distance))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Cost per mile = ${cost}').format(cost=cost_per_distance))
        return steps
    
    def _prepare_fuel_efficiency_steps(self, distance, distance_unit, fuel_used, fuel_unit, efficiency, result_unit, distance_miles, fuel_gallons, mpg):
        """Prepare step-by-step solution for fuel efficiency calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {dist} {unit}').format(dist=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Fuel Used: {fuel} {unit}').format(fuel=fuel_used, unit=self._format_unit(fuel_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if distance_unit != 'miles':
            steps.append(_('Distance in miles: {dist} miles').format(dist=distance_miles))
        if fuel_unit != 'gallons':
            steps.append(_('Fuel in gallons: {fuel} gallons').format(fuel=fuel_gallons))
        steps.append('')
        steps.append(_('Step 3: Calculate efficiency in MPG'))
        steps.append(_('Formula: MPG = Distance / Fuel'))
        steps.append(_('MPG = {dist} miles / {fuel} gallons').format(dist=distance_miles, fuel=fuel_gallons))
        steps.append(_('MPG = {mpg}').format(mpg=mpg))
        steps.append('')
        if result_unit != 'mpg':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Formula: L/100km = 235.214 / MPG'))
            steps.append(_('L/100km = 235.214 / {mpg}').format(mpg=mpg))
            steps.append(_('Efficiency = {eff} L/100km').format(eff=efficiency))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Fuel Efficiency = {eff} MPG').format(eff=efficiency))
        return steps
    
    def _prepare_distance_steps(self, fuel_used, fuel_unit, fuel_efficiency, efficiency_unit, distance_result, result_unit, fuel_gallons, mpg, distance_miles):
        """Prepare step-by-step solution for distance calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Fuel Used: {fuel} {unit}').format(fuel=fuel_used, unit=self._format_unit(fuel_unit)))
        steps.append(_('Fuel Efficiency: {eff} {unit}').format(eff=fuel_efficiency, unit=self._format_unit(efficiency_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if fuel_unit != 'gallons':
            steps.append(_('Fuel in gallons: {fuel} gallons').format(fuel=fuel_gallons))
        if efficiency_unit != 'mpg':
            steps.append(_('Efficiency in MPG: {mpg} MPG').format(mpg=mpg))
        steps.append('')
        steps.append(_('Step 3: Calculate distance in miles'))
        steps.append(_('Formula: Distance = Fuel × Efficiency'))
        steps.append(_('Distance = {fuel} gallons × {mpg} MPG').format(fuel=fuel_gallons, mpg=mpg))
        steps.append(_('Distance = {dist} miles').format(dist=distance_miles))
        steps.append('')
        if result_unit != 'miles':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Distance = {dist} {unit}').format(dist=distance_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Distance = {dist} miles').format(dist=distance_result))
        return steps
    
    def _prepare_fuel_needed_steps(self, distance, distance_unit, fuel_efficiency, efficiency_unit, fuel_result, result_unit, distance_miles, mpg, fuel_gallons):
        """Prepare step-by-step solution for fuel needed calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {dist} {unit}').format(dist=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Fuel Efficiency: {eff} {unit}').format(eff=fuel_efficiency, unit=self._format_unit(efficiency_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if distance_unit != 'miles':
            steps.append(_('Distance in miles: {dist} miles').format(dist=distance_miles))
        if efficiency_unit != 'mpg':
            steps.append(_('Efficiency in MPG: {mpg} MPG').format(mpg=mpg))
        steps.append('')
        steps.append(_('Step 3: Calculate fuel needed in gallons'))
        steps.append(_('Formula: Fuel = Distance / Efficiency'))
        steps.append(_('Fuel = {dist} miles / {mpg} MPG').format(dist=distance_miles, mpg=mpg))
        steps.append(_('Fuel = {fuel} gallons').format(fuel=fuel_gallons))
        steps.append('')
        if result_unit != 'gallons':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Fuel Needed = {fuel} {unit}').format(fuel=fuel_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Fuel Needed = {fuel} gallons').format(fuel=fuel_result))
        return steps
    
    def _prepare_convert_distance_steps(self, value, from_unit, to_unit, result, miles_value):
        """Prepare step-by-step solution for distance unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Distance: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'miles':
            steps.append(_('Step 2: Convert to miles'))
            if from_unit == 'km':
                steps.append(_('Miles = Kilometers × 0.621371'))
                steps.append(_('Miles = {value} km × 0.621371 = {miles} miles').format(value=value, miles=miles_value))
            steps.append('')
        if to_unit != 'miles':
            steps.append(_('Step 3: Convert from miles to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'km':
                steps.append(_('Kilometers = Miles / 0.621371'))
                steps.append(_('Kilometers = {miles} miles / 0.621371 = {result} km').format(miles=miles_value, result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Distance = {result} miles').format(result=result))
        return steps
    
    def _prepare_convert_fuel_steps(self, value, from_unit, to_unit, result, gallons_value):
        """Prepare step-by-step solution for fuel unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Fuel: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'gallons':
            steps.append(_('Step 2: Convert to gallons'))
            if from_unit == 'liters':
                steps.append(_('Gallons = Liters × 0.264172'))
                steps.append(_('Gallons = {value} L × 0.264172 = {gallons} gallons').format(value=value, gallons=gallons_value))
            steps.append('')
        if to_unit != 'gallons':
            steps.append(_('Step 3: Convert from gallons to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'liters':
                steps.append(_('Liters = Gallons / 0.264172'))
                steps.append(_('Liters = {gallons} gallons / 0.264172 = {result} L').format(gallons=gallons_value, result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Fuel = {result} gallons').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_total_cost_chart_data(self, distance_miles, fuel_gallons, total_cost):
        """Prepare chart data for total cost calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance (miles)'), _('Fuel (gallons)'), _('Total Cost ($)')],
                    'datasets': [{
                        'label': _('Trip Parameters'),
                        'data': [distance_miles, fuel_gallons, total_cost],
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
                            'text': _('Fuel Cost Breakdown')
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
            return {'total_cost_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_cost_per_distance_chart_data(self, mpg, price_per_gallon, cost_per_mile):
        """Prepare chart data for cost per distance calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('MPG'), _('Price/Gallon'), _('Cost/Mile')],
                    'datasets': [{
                        'data': [mpg, price_per_gallon, cost_per_mile * 1000],  # Scale cost for visibility
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
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Cost Per Distance Analysis')
                        }
                    }
                }
            }
            return {'cost_per_distance_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_fuel_efficiency_chart_data(self, distance_miles, fuel_gallons, mpg):
        """Prepare chart data for fuel efficiency calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance (miles)'), _('Fuel (gallons)'), _('Efficiency (MPG)')],
                    'datasets': [{
                        'label': _('Efficiency Parameters'),
                        'data': [distance_miles, fuel_gallons, mpg],
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
                            'text': _('Fuel Efficiency Breakdown')
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
            return {'fuel_efficiency_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_distance_chart_data(self, fuel_gallons, mpg, distance_miles):
        """Prepare chart data for distance calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Fuel (gallons)'), _('Efficiency (MPG)'), _('Distance (miles)')],
                    'datasets': [{
                        'label': _('Distance Parameters'),
                        'data': [fuel_gallons, mpg, distance_miles],
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
                            'text': _('Distance Calculation Breakdown')
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
            return {'distance_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_fuel_needed_chart_data(self, distance_miles, mpg, fuel_gallons):
        """Prepare chart data for fuel needed calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance (miles)'), _('Efficiency (MPG)'), _('Fuel Needed (gallons)')],
                    'datasets': [{
                        'label': _('Fuel Needed Parameters'),
                        'data': [distance_miles, mpg, fuel_gallons],
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
                            'text': _('Fuel Needed Breakdown')
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
            return {'fuel_needed_chart': chart_config}
        except Exception as e:
            return None
