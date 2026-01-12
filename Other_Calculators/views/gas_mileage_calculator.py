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
class GasMileageCalculator(View):
    """
    Professional Gas Mileage Calculator with Comprehensive Features
    
    This calculator provides gas mileage calculations with:
    - Calculate MPG from distance and fuel used
    - Calculate distance from MPG and fuel used
    - Calculate fuel needed from distance and MPG
    - Calculate cost from distance, MPG, and fuel price
    - Compare multiple trips
    - Unit conversions
    
    Features:
    - Supports multiple calculation modes
    - Handles various units (imperial and metric)
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/gas_mileage_calculator.html'
    
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
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Gas Mileage Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'mpg')
            
            if calc_type == 'mpg':
                return self._calculate_mpg(data)
            elif calc_type == 'distance':
                return self._calculate_distance(data)
            elif calc_type == 'fuel_needed':
                return self._calculate_fuel_needed(data)
            elif calc_type == 'cost':
                return self._calculate_cost(data)
            elif calc_type == 'compare':
                return self._compare_trips(data)
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
    
    def _calculate_mpg(self, data):
        """Calculate MPG from distance and fuel used"""
        try:
            # Check for required fields
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
            
            if distance > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            if fuel_used > 1e6:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used is too large. Please use a value below 1,000,000.')
                }, status=400)
            
            # Convert to base units (miles and gallons)
            distance_miles = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            fuel_gallons = float(fuel_used * self.FUEL_VOLUME_CONVERSIONS[fuel_unit])
            
            # Calculate MPG: MPG = Distance / Fuel
            mpg = float(np.divide(distance_miles, fuel_gallons))
            
            # Validate result
            if math.isinf(mpg) or math.isnan(mpg) or np.isinf(mpg) or np.isnan(mpg):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_mpg_steps(distance, distance_unit, fuel_used, fuel_unit, mpg, distance_miles, fuel_gallons)
            
            # Prepare chart data
            chart_data = self._prepare_mpg_chart_data(distance_miles, fuel_gallons, mpg)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'mpg',
                'distance': distance,
                'distance_unit': distance_unit,
                'fuel_used': fuel_used,
                'fuel_unit': fuel_unit,
                'mpg': mpg,
                'distance_miles': distance_miles,
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
                'error': _('Error calculating MPG: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_distance(self, data):
        """Calculate distance from MPG and fuel used"""
        try:
            if 'mpg' not in data or data.get('mpg') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('MPG is required.')
                }, status=400)
            
            if 'fuel_used' not in data or data.get('fuel_used') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used is required.')
                }, status=400)
            
            try:
                mpg = float(data.get('mpg', 0))
                fuel_used = float(data.get('fuel_used', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            fuel_unit = data.get('fuel_unit', 'gallons')
            result_unit = data.get('result_unit', 'miles')
            
            # Validate units
            if fuel_unit not in self.FUEL_VOLUME_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid fuel unit.')
                }, status=400)
            
            if result_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if mpg <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('MPG must be greater than zero.')
                }, status=400)
            
            if fuel_used <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel used must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            fuel_gallons = float(fuel_used * self.FUEL_VOLUME_CONVERSIONS[fuel_unit])
            
            # Calculate distance in miles: Distance = MPG × Fuel
            distance_miles = float(np.multiply(mpg, fuel_gallons))
            
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
            
            steps = self._prepare_distance_steps(mpg, fuel_used, fuel_unit, distance_result, result_unit, fuel_gallons, distance_miles)
            
            chart_data = self._prepare_distance_chart_data(mpg, fuel_gallons, distance_miles)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'distance',
                'mpg': mpg,
                'fuel_used': fuel_used,
                'fuel_unit': fuel_unit,
                'distance': distance_result,
                'result_unit': result_unit,
                'fuel_gallons': fuel_gallons,
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
        """Calculate fuel needed from distance and MPG"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'mpg' not in data or data.get('mpg') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('MPG is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                mpg = float(data.get('mpg', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            result_unit = data.get('result_unit', 'gallons')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
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
            
            if mpg <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('MPG must be greater than zero.')
                }, status=400)
            
            # Convert to base units
            distance_miles = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Calculate fuel needed in gallons: Fuel = Distance / MPG
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
            
            steps = self._prepare_fuel_needed_steps(distance, distance_unit, mpg, fuel_result, result_unit, distance_miles, fuel_gallons)
            
            chart_data = self._prepare_fuel_needed_chart_data(distance_miles, mpg, fuel_gallons)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'fuel_needed',
                'distance': distance,
                'distance_unit': distance_unit,
                'mpg': mpg,
                'fuel_needed': fuel_result,
                'result_unit': result_unit,
                'distance_miles': distance_miles,
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
    
    def _calculate_cost(self, data):
        """Calculate fuel cost from distance, MPG, and fuel price"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'mpg' not in data or data.get('mpg') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('MPG is required.')
                }, status=400)
            
            if 'fuel_price' not in data or data.get('fuel_price') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                mpg = float(data.get('mpg', 0))
                fuel_price = float(data.get('fuel_price', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            price_unit = data.get('price_unit', 'per_gallon')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            if price_unit not in self.PRICE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid price unit.')
                }, status=400)
            
            # Validate ranges
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            if mpg <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('MPG must be greater than zero.')
                }, status=400)
            
            if fuel_price < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel price must be non-negative.')
                }, status=400)
            
            # Convert to base units
            distance_miles = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            price_per_gallon = float(fuel_price * self.PRICE_CONVERSIONS[price_unit])
            
            # Calculate fuel needed
            fuel_gallons = float(np.divide(distance_miles, mpg))
            
            # Calculate total cost
            total_cost = float(np.multiply(fuel_gallons, price_per_gallon))
            
            # Calculate cost per mile
            cost_per_mile = float(np.divide(total_cost, distance_miles))
            
            # Validate result
            if math.isinf(total_cost) or math.isnan(total_cost) or np.isinf(total_cost) or np.isnan(total_cost):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_cost_steps(distance, distance_unit, mpg, fuel_price, price_unit, total_cost, cost_per_mile, distance_miles, fuel_gallons, price_per_gallon)
            
            chart_data = self._prepare_cost_chart_data(distance_miles, fuel_gallons, total_cost)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'cost',
                'distance': distance,
                'distance_unit': distance_unit,
                'mpg': mpg,
                'fuel_price': fuel_price,
                'price_unit': price_unit,
                'total_cost': total_cost,
                'cost_per_mile': cost_per_mile,
                'fuel_needed': fuel_gallons,
                'fuel_needed_liters': float(fuel_gallons / self.FUEL_VOLUME_CONVERSIONS['liters']),
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
                'error': _('Error calculating cost: {error}').format(error=str(e))
            }, status=500)
    
    def _compare_trips(self, data):
        """Compare multiple trips"""
        try:
            if 'trips' not in data or not isinstance(data.get('trips'), list) or len(data.get('trips', [])) < 2:
                return JsonResponse({
                    'success': False,
                    'error': _('At least two trips are required for comparison.')
                }, status=400)
            
            trips = data.get('trips', [])
            if len(trips) > 5:
                return JsonResponse({
                    'success': False,
                    'error': _('Maximum 5 trips can be compared at once.')
                }, status=400)
            
            trip_results = []
            for i, trip in enumerate(trips):
                if 'distance' not in trip or 'fuel_used' not in trip:
                    return JsonResponse({
                        'success': False,
                        'error': _('Trip {num} is missing required fields.').format(num=i+1)
                    }, status=400)
                
                try:
                    distance = float(trip.get('distance', 0))
                    fuel_used = float(trip.get('fuel_used', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Trip {num} has invalid values.').format(num=i+1)
                    }, status=400)
                
                if distance <= 0 or fuel_used <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Trip {num} has invalid values. Distance and fuel must be greater than zero.').format(num=i+1)
                    }, status=400)
                
                distance_unit = trip.get('distance_unit', 'miles')
                fuel_unit = trip.get('fuel_unit', 'gallons')
                
                # Convert to base units
                distance_miles = float(distance * self.DISTANCE_CONVERSIONS.get(distance_unit, 1.0))
                fuel_gallons = float(fuel_used * self.FUEL_VOLUME_CONVERSIONS.get(fuel_unit, 1.0))
                
                # Calculate MPG
                mpg = float(np.divide(distance_miles, fuel_gallons))
                
                trip_results.append({
                    'trip_number': i + 1,
                    'distance': distance,
                    'distance_unit': distance_unit,
                    'fuel_used': fuel_used,
                    'fuel_unit': fuel_unit,
                    'mpg': mpg,
                    'distance_miles': distance_miles,
                    'fuel_gallons': fuel_gallons,
                })
            
            # Find best and worst MPG
            best_trip = max(trip_results, key=lambda x: x['mpg'])
            worst_trip = min(trip_results, key=lambda x: x['mpg'])
            avg_mpg = float(np.mean([t['mpg'] for t in trip_results]))
            
            chart_data = self._prepare_compare_chart_data(trip_results)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'compare',
                'trips': trip_results,
                'best_trip': best_trip,
                'worst_trip': worst_trip,
                'average_mpg': avg_mpg,
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
                'error': _('Error comparing trips: {error}').format(error=str(e))
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
    def _prepare_mpg_steps(self, distance, distance_unit, fuel_used, fuel_unit, mpg, distance_miles, fuel_gallons):
        """Prepare step-by-step solution for MPG calculation"""
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
        steps.append(_('Step 3: Apply the MPG formula'))
        steps.append(_('Formula: MPG = Distance / Fuel'))
        steps.append(_('MPG = {dist} miles / {fuel} gallons').format(dist=distance_miles, fuel=fuel_gallons))
        steps.append(_('MPG = {mpg}').format(mpg=mpg))
        return steps
    
    def _prepare_distance_steps(self, mpg, fuel_used, fuel_unit, distance_result, result_unit, fuel_gallons, distance_miles):
        """Prepare step-by-step solution for distance calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('MPG: {mpg}').format(mpg=mpg))
        steps.append(_('Fuel Used: {fuel} {unit}').format(fuel=fuel_used, unit=self._format_unit(fuel_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if fuel_unit != 'gallons':
            steps.append(_('Fuel in gallons: {fuel} gallons').format(fuel=fuel_gallons))
        steps.append('')
        steps.append(_('Step 3: Calculate distance in miles'))
        steps.append(_('Formula: Distance = MPG × Fuel'))
        steps.append(_('Distance = {mpg} MPG × {fuel} gallons').format(mpg=mpg, fuel=fuel_gallons))
        steps.append(_('Distance = {dist} miles').format(dist=distance_miles))
        steps.append('')
        if result_unit != 'miles':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('Distance = {dist} {unit}').format(dist=distance_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('Distance = {dist} miles').format(dist=distance_result))
        return steps
    
    def _prepare_fuel_needed_steps(self, distance, distance_unit, mpg, fuel_result, result_unit, distance_miles, fuel_gallons):
        """Prepare step-by-step solution for fuel needed calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {dist} {unit}').format(dist=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('MPG: {mpg}').format(mpg=mpg))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if distance_unit != 'miles':
            steps.append(_('Distance in miles: {dist} miles').format(dist=distance_miles))
        steps.append('')
        steps.append(_('Step 3: Calculate fuel needed in gallons'))
        steps.append(_('Formula: Fuel = Distance / MPG'))
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
    
    def _prepare_cost_steps(self, distance, distance_unit, mpg, fuel_price, price_unit, total_cost, cost_per_mile, distance_miles, fuel_gallons, price_per_gallon):
        """Prepare step-by-step solution for cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {dist} {unit}').format(dist=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('MPG: {mpg}').format(mpg=mpg))
        steps.append(_('Fuel Price: ${price} {unit}').format(price=fuel_price, unit=self._format_unit(price_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if distance_unit != 'miles':
            steps.append(_('Distance in miles: {dist} miles').format(dist=distance_miles))
        if price_unit != 'per_gallon':
            steps.append(_('Price per gallon: ${price}/gallon').format(price=price_per_gallon))
        steps.append('')
        steps.append(_('Step 3: Calculate fuel needed'))
        steps.append(_('Formula: Fuel = Distance / MPG'))
        steps.append(_('Fuel = {dist} miles / {mpg} MPG').format(dist=distance_miles, mpg=mpg))
        steps.append(_('Fuel = {fuel} gallons').format(fuel=fuel_gallons))
        steps.append('')
        steps.append(_('Step 4: Calculate total cost'))
        steps.append(_('Formula: Cost = Fuel × Price'))
        steps.append(_('Cost = {fuel} gallons × ${price}/gallon').format(fuel=fuel_gallons, price=price_per_gallon))
        steps.append(_('Total Cost = ${cost}').format(cost=total_cost))
        steps.append('')
        steps.append(_('Step 5: Calculate cost per mile'))
        steps.append(_('Cost per mile = ${cost} / {dist} miles').format(cost=total_cost, dist=distance_miles))
        steps.append(_('Cost per mile = ${cpm}').format(cpm=cost_per_mile))
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
    def _prepare_mpg_chart_data(self, distance_miles, fuel_gallons, mpg):
        """Prepare chart data for MPG calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance (miles)'), _('Fuel (gallons)'), _('MPG')],
                    'datasets': [{
                        'label': _('Gas Mileage Parameters'),
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
                            'text': _('Gas Mileage Calculation Breakdown')
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
            return {'mpg_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_distance_chart_data(self, mpg, fuel_gallons, distance_miles):
        """Prepare chart data for distance calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('MPG'), _('Fuel (gallons)'), _('Distance (miles)')],
                    'datasets': [{
                        'label': _('Distance Parameters'),
                        'data': [mpg, fuel_gallons, distance_miles],
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
                    'labels': [_('Distance (miles)'), _('MPG'), _('Fuel Needed (gallons)')],
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
    
    def _prepare_cost_chart_data(self, distance_miles, fuel_gallons, total_cost):
        """Prepare chart data for cost calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance (miles)'), _('Fuel (gallons)'), _('Total Cost ($)')],
                    'datasets': [{
                        'label': _('Cost Parameters'),
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
            return {'cost_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_compare_chart_data(self, trip_results):
        """Prepare chart data for trip comparison"""
        try:
            labels = [_('Trip {num}').format(num=t['trip_number']) for t in trip_results]
            mpg_values = [t['mpg'] for t in trip_results]
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': _('MPG'),
                        'data': mpg_values,
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(236, 72, 153, 0.8)'
                        ][:len(trip_results)],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#8b5cf6',
                            '#ec4899'
                        ][:len(trip_results)],
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
                            'text': _('Trip Comparison - MPG')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('MPG')
                            }
                        }
                    }
                }
            }
            return {'compare_chart': chart_config}
        except Exception as e:
            return None
