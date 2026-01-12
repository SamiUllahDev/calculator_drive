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
class MileageCalculator(View):
    """
    Professional Mileage Calculator with Comprehensive Features
    
    This calculator provides mileage calculations with:
    - Calculate mileage reimbursement (distance × rate)
    - Calculate total trip cost
    - Calculate cost per mile
    - Calculate distance from cost and rate
    - Convert distance units
    - Compare mileage rates
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/mileage_calculator.html'
    
    # Distance conversion factors (to kilometers)
    DISTANCE_CONVERSIONS = {
        'kilometers': 1.0,
        'miles': 1.60934,  # 1 mile = 1.60934 km
        'meters': 0.001,  # 1 m = 0.001 km
        'feet': 0.0003048,  # 1 ft = 0.0003048 km
        'yards': 0.0009144,  # 1 yd = 0.0009144 km
        'nautical_miles': 1.852,  # 1 nmi = 1.852 km
    }
    
    # Currency conversion factors (to USD - for display purposes, actual rates would come from API)
    CURRENCY_CONVERSIONS = {
        'usd': 1.0,
        'eur': 1.1,  # Approximate
        'gbp': 1.27,  # Approximate
        'cad': 0.74,  # Approximate
        'aud': 0.67,  # Approximate
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'kilometers': 'km',
            'miles': 'miles',
            'meters': 'm',
            'feet': 'ft',
            'yards': 'yd',
            'nautical_miles': 'nmi',
            'usd': 'USD',
            'eur': 'EUR',
            'gbp': 'GBP',
            'cad': 'CAD',
            'aud': 'AUD',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Mileage Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'reimbursement')
            
            if calc_type == 'reimbursement':
                return self._calculate_reimbursement(data)
            elif calc_type == 'trip_cost':
                return self._calculate_trip_cost(data)
            elif calc_type == 'cost_per_mile':
                return self._calculate_cost_per_mile(data)
            elif calc_type == 'distance_from_cost':
                return self._calculate_distance_from_cost(data)
            elif calc_type == 'convert_distance':
                return self._convert_distance(data)
            elif calc_type == 'compare_rates':
                return self._compare_rates(data)
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
    
    def _calculate_reimbursement(self, data):
        """Calculate mileage reimbursement"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'rate' not in data or data.get('rate') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Mileage rate is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                rate = float(data.get('rate', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            rate_unit = data.get('rate_unit', 'per_mile')
            currency = data.get('currency', 'usd')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            if rate_unit not in ['per_mile', 'per_km']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid rate unit.')
                }, status=400)
            
            # Validate ranges
            if distance < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be non-negative.')
                }, status=400)
            
            if rate < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Rate must be non-negative.')
                }, status=400)
            
            # Convert distance to base unit (km)
            distance_km = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Calculate reimbursement
            if rate_unit == 'per_mile':
                # Convert km to miles for calculation
                distance_miles = float(np.divide(distance_km, self.DISTANCE_CONVERSIONS['miles']))
                reimbursement = float(np.multiply(distance_miles, rate))
            else:  # per_km
                reimbursement = float(np.multiply(distance_km, rate))
            
            # Validate result
            if math.isinf(reimbursement) or math.isnan(reimbursement) or np.isinf(reimbursement) or np.isnan(reimbursement):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_reimbursement_steps(distance, distance_unit, rate, rate_unit, distance_km, distance_miles if rate_unit == 'per_mile' else None, reimbursement, currency)
            
            chart_data = self._prepare_reimbursement_chart_data(distance_km, rate, rate_unit, reimbursement)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'reimbursement',
                'distance': distance,
                'distance_unit': distance_unit,
                'rate': rate,
                'rate_unit': rate_unit,
                'reimbursement': round(reimbursement, 2),
                'currency': currency,
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
                'error': _('Error calculating reimbursement: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_trip_cost(self, data):
        """Calculate total trip cost including fuel and other expenses"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'fuel_cost' not in data or data.get('fuel_cost') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel cost per unit is required.')
                }, status=400)
            
            if 'fuel_efficiency' not in data or data.get('fuel_efficiency') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                fuel_cost = float(data.get('fuel_cost', 0))
                fuel_efficiency = float(data.get('fuel_efficiency', 0))
                other_costs = float(data.get('other_costs', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            efficiency_unit = data.get('efficiency_unit', 'mpg')
            fuel_cost_unit = data.get('fuel_cost_unit', 'per_gallon')
            currency = data.get('currency', 'usd')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            if efficiency_unit not in ['mpg', 'l_per_100km', 'km_per_l']:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid efficiency unit.')
                }, status=400)
            
            # Validate ranges
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            if fuel_cost <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel cost must be greater than zero.')
                }, status=400)
            
            if fuel_efficiency <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Fuel efficiency must be greater than zero.')
                }, status=400)
            
            if other_costs < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Other costs must be non-negative.')
                }, status=400)
            
            # Convert distance to miles for MPG calculations
            distance_km = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            distance_miles = float(np.divide(distance_km, self.DISTANCE_CONVERSIONS['miles']))
            
            # Calculate fuel needed
            if efficiency_unit == 'mpg':
                fuel_needed_gallons = float(np.divide(distance_miles, fuel_efficiency))
                if fuel_cost_unit == 'per_gallon':
                    fuel_cost_total = float(np.multiply(fuel_needed_gallons, fuel_cost))
                else:  # per_liter
                    fuel_needed_liters = float(np.multiply(fuel_needed_gallons, 3.78541))
                    fuel_cost_total = float(np.multiply(fuel_needed_liters, fuel_cost))
            elif efficiency_unit == 'l_per_100km':
                fuel_needed_liters = float(np.multiply(np.divide(distance_km, 100.0), fuel_efficiency))
                if fuel_cost_unit == 'per_gallon':
                    fuel_needed_gallons = float(np.divide(fuel_needed_liters, 3.78541))
                    fuel_cost_total = float(np.multiply(fuel_needed_gallons, fuel_cost))
                else:  # per_liter
                    fuel_cost_total = float(np.multiply(fuel_needed_liters, fuel_cost))
            else:  # km_per_l
                fuel_needed_liters = float(np.divide(distance_km, fuel_efficiency))
                if fuel_cost_unit == 'per_gallon':
                    fuel_needed_gallons = float(np.divide(fuel_needed_liters, 3.78541))
                    fuel_cost_total = float(np.multiply(fuel_needed_gallons, fuel_cost))
                else:  # per_liter
                    fuel_cost_total = float(np.multiply(fuel_needed_liters, fuel_cost))
            
            # Calculate total cost
            total_cost = float(np.add(fuel_cost_total, other_costs))
            
            # Validate result
            if math.isinf(total_cost) or math.isnan(total_cost) or np.isinf(total_cost) or np.isnan(total_cost):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_trip_cost_steps(distance, distance_unit, fuel_cost, fuel_efficiency, efficiency_unit, fuel_cost_unit, other_costs, fuel_cost_total, total_cost, currency)
            
            chart_data = self._prepare_trip_cost_chart_data(fuel_cost_total, other_costs, total_cost)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'trip_cost',
                'distance': distance,
                'distance_unit': distance_unit,
                'fuel_cost': fuel_cost,
                'fuel_efficiency': fuel_efficiency,
                'efficiency_unit': efficiency_unit,
                'fuel_cost_unit': fuel_cost_unit,
                'other_costs': other_costs,
                'fuel_cost_total': round(fuel_cost_total, 2),
                'total_cost': round(total_cost, 2),
                'currency': currency,
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
                'error': _('Error calculating trip cost: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_cost_per_mile(self, data):
        """Calculate cost per mile"""
        try:
            if 'total_cost' not in data or data.get('total_cost') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Total cost is required.')
                }, status=400)
            
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            try:
                total_cost = float(data.get('total_cost', 0))
                distance = float(data.get('distance', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            result_unit = data.get('result_unit', 'per_mile')
            currency = data.get('currency', 'usd')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            # Validate ranges
            if total_cost < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Total cost must be non-negative.')
                }, status=400)
            
            if distance <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be greater than zero.')
                }, status=400)
            
            # Convert distance to base unit (km)
            distance_km = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Calculate cost per unit
            if result_unit == 'per_mile':
                distance_miles = float(np.divide(distance_km, self.DISTANCE_CONVERSIONS['miles']))
                cost_per_unit = float(np.divide(total_cost, distance_miles))
            else:  # per_km
                cost_per_unit = float(np.divide(total_cost, distance_km))
            
            # Validate result
            if math.isinf(cost_per_unit) or math.isnan(cost_per_unit) or np.isinf(cost_per_unit) or np.isnan(cost_per_unit):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_cost_per_mile_steps(total_cost, distance, distance_unit, distance_km, distance_miles if result_unit == 'per_mile' else None, cost_per_unit, result_unit, currency)
            
            chart_data = self._prepare_cost_per_mile_chart_data(total_cost, distance_km, cost_per_unit, result_unit)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'cost_per_mile',
                'total_cost': total_cost,
                'distance': distance,
                'distance_unit': distance_unit,
                'cost_per_unit': round(cost_per_unit, 4),
                'result_unit': result_unit,
                'currency': currency,
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
                'error': _('Error calculating cost per mile: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_distance_from_cost(self, data):
        """Calculate distance from total cost and cost per mile"""
        try:
            if 'total_cost' not in data or data.get('total_cost') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Total cost is required.')
                }, status=400)
            
            if 'cost_per_unit' not in data or data.get('cost_per_unit') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Cost per unit is required.')
                }, status=400)
            
            try:
                total_cost = float(data.get('total_cost', 0))
                cost_per_unit = float(data.get('cost_per_unit', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            cost_unit = data.get('cost_unit', 'per_mile')
            result_unit = data.get('result_unit', 'miles')
            currency = data.get('currency', 'usd')
            
            # Validate ranges
            if total_cost < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Total cost must be non-negative.')
                }, status=400)
            
            if cost_per_unit <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Cost per unit must be greater than zero.')
                }, status=400)
            
            # Calculate distance
            if cost_unit == 'per_mile':
                distance_miles = float(np.divide(total_cost, cost_per_unit))
                distance_km = float(np.multiply(distance_miles, self.DISTANCE_CONVERSIONS['miles']))
            else:  # per_km
                distance_km = float(np.divide(total_cost, cost_per_unit))
                distance_miles = float(np.divide(distance_km, self.DISTANCE_CONVERSIONS['miles']))
            
            # Convert to result unit
            if result_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            result = float(np.divide(distance_km, self.DISTANCE_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_distance_from_cost_steps(total_cost, cost_per_unit, cost_unit, distance_km, distance_miles, result, result_unit, currency)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'distance_from_cost',
                'total_cost': total_cost,
                'cost_per_unit': cost_per_unit,
                'cost_unit': cost_unit,
                'distance': round(result, 2),
                'result_unit': result_unit,
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
                'error': _('Error calculating distance: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_distance(self, data):
        """Convert distance between different units"""
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
            to_unit = data.get('to_unit', 'kilometers')
            
            # Validate units
            if from_unit not in self.DISTANCE_CONVERSIONS or to_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be non-negative.')
                }, status=400)
            
            # Convert to kilometers first
            kilometers = float(value * self.DISTANCE_CONVERSIONS[from_unit])
            
            # Convert to target unit
            result = float(np.divide(kilometers, self.DISTANCE_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_distance_steps(value, from_unit, to_unit, result, kilometers)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_distance',
                'value': value,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'result': round(result, 6),
                'kilometers': round(kilometers, 6),
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
                'error': _('Error converting distance: {error}').format(error=str(e))
            }, status=500)
    
    def _compare_rates(self, data):
        """Compare different mileage rates"""
        try:
            if 'distance' not in data or data.get('distance') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance is required.')
                }, status=400)
            
            if 'rate1' not in data or data.get('rate1') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Rate 1 is required.')
                }, status=400)
            
            if 'rate2' not in data or data.get('rate2') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Rate 2 is required.')
                }, status=400)
            
            try:
                distance = float(data.get('distance', 0))
                rate1 = float(data.get('rate1', 0))
                rate2 = float(data.get('rate2', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            distance_unit = data.get('distance_unit', 'miles')
            rate_unit = data.get('rate_unit', 'per_mile')
            currency = data.get('currency', 'usd')
            
            # Validate units
            if distance_unit not in self.DISTANCE_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid distance unit.')
                }, status=400)
            
            # Validate ranges
            if distance < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Distance must be non-negative.')
                }, status=400)
            
            if rate1 < 0 or rate2 < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Rates must be non-negative.')
                }, status=400)
            
            # Convert distance to base unit (km)
            distance_km = float(distance * self.DISTANCE_CONVERSIONS[distance_unit])
            
            # Calculate reimbursements
            if rate_unit == 'per_mile':
                distance_miles = float(np.divide(distance_km, self.DISTANCE_CONVERSIONS['miles']))
                reimbursement1 = float(np.multiply(distance_miles, rate1))
                reimbursement2 = float(np.multiply(distance_miles, rate2))
            else:  # per_km
                reimbursement1 = float(np.multiply(distance_km, rate1))
                reimbursement2 = float(np.multiply(distance_km, rate2))
            
            difference = float(np.subtract(reimbursement2, reimbursement1))
            percent_difference = float(np.multiply(np.divide(difference, reimbursement1), 100.0)) if reimbursement1 > 0 else 0.0
            
            # Validate results
            if math.isinf(reimbursement1) or math.isnan(reimbursement1) or math.isinf(reimbursement2) or math.isnan(reimbursement2):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_compare_rates_steps(distance, distance_unit, rate1, rate2, rate_unit, distance_km, distance_miles if rate_unit == 'per_mile' else None, reimbursement1, reimbursement2, difference, percent_difference, currency)
            
            chart_data = self._prepare_compare_rates_chart_data(rate1, rate2, reimbursement1, reimbursement2, currency)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'compare_rates',
                'distance': distance,
                'distance_unit': distance_unit,
                'rate1': rate1,
                'rate2': rate2,
                'rate_unit': rate_unit,
                'reimbursement1': round(reimbursement1, 2),
                'reimbursement2': round(reimbursement2, 2),
                'difference': round(difference, 2),
                'percent_difference': round(percent_difference, 2),
                'currency': currency,
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
                'error': _('Error comparing rates: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_reimbursement_steps(self, distance, distance_unit, rate, rate_unit, distance_km, distance_miles, reimbursement, currency):
        """Prepare step-by-step solution for reimbursement calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {distance} {unit}').format(distance=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Rate: {rate} {currency}/{unit}').format(rate=rate, currency=self._format_unit(currency), unit=_('mile') if rate_unit == 'per_mile' else _('km')))
        steps.append('')
        if rate_unit == 'per_mile':
            if distance_unit != 'miles':
                steps.append(_('Step 2: Convert distance to miles'))
                steps.append(_('Distance in miles: {miles} miles').format(miles=distance_miles))
                steps.append('')
            steps.append(_('Step 3: Calculate reimbursement'))
            steps.append(_('Formula: Reimbursement = Distance × Rate'))
            steps.append(_('Reimbursement = {distance} miles × {rate} {currency}/mile').format(distance=distance_miles, rate=rate, currency=self._format_unit(currency)))
        else:
            if distance_unit != 'kilometers':
                steps.append(_('Step 2: Convert distance to kilometers'))
                steps.append(_('Distance in km: {km} km').format(km=distance_km))
                steps.append('')
            steps.append(_('Step 3: Calculate reimbursement'))
            steps.append(_('Formula: Reimbursement = Distance × Rate'))
            steps.append(_('Reimbursement = {distance} km × {rate} {currency}/km').format(distance=distance_km, rate=rate, currency=self._format_unit(currency)))
        steps.append(_('Reimbursement = {result} {currency}').format(result=reimbursement, currency=self._format_unit(currency)))
        return steps
    
    def _prepare_trip_cost_steps(self, distance, distance_unit, fuel_cost, fuel_efficiency, efficiency_unit, fuel_cost_unit, other_costs, fuel_cost_total, total_cost, currency):
        """Prepare step-by-step solution for trip cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {distance} {unit}').format(distance=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Fuel Cost: {cost} {currency}/{unit}').format(cost=fuel_cost, currency=self._format_unit(currency), unit=_('gallon') if fuel_cost_unit == 'per_gallon' else _('liter')))
        steps.append(_('Fuel Efficiency: {efficiency} {unit}').format(efficiency=fuel_efficiency, unit=efficiency_unit))
        if other_costs > 0:
            steps.append(_('Other Costs: {cost} {currency}').format(cost=other_costs, currency=self._format_unit(currency)))
        steps.append('')
        steps.append(_('Step 2: Calculate fuel needed'))
        if efficiency_unit == 'mpg':
            steps.append(_('Fuel Needed = Distance (miles) / MPG'))
        elif efficiency_unit == 'l_per_100km':
            steps.append(_('Fuel Needed = (Distance (km) / 100) × L/100km'))
        else:
            steps.append(_('Fuel Needed = Distance (km) / km/L'))
        steps.append('')
        steps.append(_('Step 3: Calculate fuel cost'))
        steps.append(_('Fuel Cost = Fuel Needed × Cost per Unit'))
        steps.append(_('Fuel Cost = {cost} {currency}').format(cost=fuel_cost_total, currency=self._format_unit(currency)))
        steps.append('')
        steps.append(_('Step 4: Calculate total cost'))
        steps.append(_('Total Cost = Fuel Cost + Other Costs'))
        steps.append(_('Total Cost = {fuel} + {other} = {total} {currency}').format(fuel=fuel_cost_total, other=other_costs, total=total_cost, currency=self._format_unit(currency)))
        return steps
    
    def _prepare_cost_per_mile_steps(self, total_cost, distance, distance_unit, distance_km, distance_miles, cost_per_unit, result_unit, currency):
        """Prepare step-by-step solution for cost per mile calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Total Cost: {cost} {currency}').format(cost=total_cost, currency=self._format_unit(currency)))
        steps.append(_('Distance: {distance} {unit}').format(distance=distance, unit=self._format_unit(distance_unit)))
        steps.append('')
        steps.append(_('Step 2: Convert distance to base unit'))
        if result_unit == 'per_mile':
            if distance_unit != 'miles':
                steps.append(_('Distance in miles: {miles} miles').format(miles=distance_miles))
            steps.append('')
            steps.append(_('Step 3: Calculate cost per mile'))
            steps.append(_('Formula: Cost per Mile = Total Cost / Distance'))
            steps.append(_('Cost per Mile = {cost} {currency} / {distance} miles').format(cost=total_cost, currency=self._format_unit(currency), distance=distance_miles))
        else:
            if distance_unit != 'kilometers':
                steps.append(_('Distance in km: {km} km').format(km=distance_km))
            steps.append('')
            steps.append(_('Step 3: Calculate cost per kilometer'))
            steps.append(_('Formula: Cost per km = Total Cost / Distance'))
            steps.append(_('Cost per km = {cost} {currency} / {distance} km').format(cost=total_cost, currency=self._format_unit(currency), distance=distance_km))
        steps.append(_('Cost per Unit = {result} {currency}/{unit}').format(result=cost_per_unit, currency=self._format_unit(currency), unit=_('mile') if result_unit == 'per_mile' else _('km')))
        return steps
    
    def _prepare_distance_from_cost_steps(self, total_cost, cost_per_unit, cost_unit, distance_km, distance_miles, result, result_unit, currency):
        """Prepare step-by-step solution for distance from cost calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Total Cost: {cost} {currency}').format(cost=total_cost, currency=self._format_unit(currency)))
        steps.append(_('Cost per Unit: {cost} {currency}/{unit}').format(cost=cost_per_unit, currency=self._format_unit(currency), unit=_('mile') if cost_unit == 'per_mile' else _('km')))
        steps.append('')
        steps.append(_('Step 2: Calculate distance'))
        if cost_unit == 'per_mile':
            steps.append(_('Formula: Distance = Total Cost / Cost per Mile'))
            steps.append(_('Distance = {total} {currency} / {cost} {currency}/mile').format(total=total_cost, cost=cost_per_unit, currency=self._format_unit(currency)))
            steps.append(_('Distance = {miles} miles = {km} km').format(miles=distance_miles, km=distance_km))
        else:
            steps.append(_('Formula: Distance = Total Cost / Cost per km'))
            steps.append(_('Distance = {total} {currency} / {cost} {currency}/km').format(total=total_cost, cost=cost_per_unit, currency=self._format_unit(currency)))
            steps.append(_('Distance = {km} km = {miles} miles').format(km=distance_km, miles=distance_miles))
        steps.append('')
        if result_unit not in ['miles', 'kilometers']:
            steps.append(_('Step 3: Convert to desired unit'))
            steps.append(_('Distance = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 3: Result'))
            steps.append(_('Distance = {result} {unit}').format(result=result, unit=self._format_unit(result_unit)))
        return steps
    
    def _prepare_convert_distance_steps(self, value, from_unit, to_unit, result, kilometers):
        """Prepare step-by-step solution for distance conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('Distance: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'kilometers':
            steps.append(_('Step 2: Convert to kilometers (base unit)'))
            if from_unit == 'miles':
                steps.append(_('Kilometers = Miles × 1.60934'))
                steps.append(_('Kilometers = {miles} miles × 1.60934 = {km} km').format(miles=value, km=kilometers))
            elif from_unit == 'meters':
                steps.append(_('Kilometers = Meters / 1000'))
                steps.append(_('Kilometers = {m} m / 1000 = {km} km').format(m=value, km=kilometers))
            else:
                steps.append(_('Kilometers = {value} {unit} × conversion factor = {km} km').format(value=value, unit=self._format_unit(from_unit), km=kilometers))
            steps.append('')
        if to_unit != 'kilometers':
            steps.append(_('Step 3: Convert from kilometers to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'miles':
                steps.append(_('Miles = Kilometers / 1.60934'))
                steps.append(_('Miles = {km} km / 1.60934 = {result} miles').format(km=kilometers, result=result))
            elif to_unit == 'meters':
                steps.append(_('Meters = Kilometers × 1000'))
                steps.append(_('Meters = {km} km × 1000 = {result} m').format(km=kilometers, result=result))
            else:
                steps.append(_('Result = {km} km / conversion factor = {result} {unit}').format(km=kilometers, result=result, unit=self._format_unit(to_unit)))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('Distance = {result} km').format(result=result))
        return steps
    
    def _prepare_compare_rates_steps(self, distance, distance_unit, rate1, rate2, rate_unit, distance_km, distance_miles, reimbursement1, reimbursement2, difference, percent_difference, currency):
        """Prepare step-by-step solution for rate comparison"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Distance: {distance} {unit}').format(distance=distance, unit=self._format_unit(distance_unit)))
        steps.append(_('Rate 1: {rate} {currency}/{unit}').format(rate=rate1, currency=self._format_unit(currency), unit=_('mile') if rate_unit == 'per_mile' else _('km')))
        steps.append(_('Rate 2: {rate} {currency}/{unit}').format(rate=rate2, currency=self._format_unit(currency), unit=_('mile') if rate_unit == 'per_mile' else _('km')))
        steps.append('')
        steps.append(_('Step 2: Calculate reimbursement for Rate 1'))
        if rate_unit == 'per_mile':
            steps.append(_('Reimbursement 1 = {distance} miles × {rate} = {result} {currency}').format(distance=distance_miles, rate=rate1, result=reimbursement1, currency=self._format_unit(currency)))
        else:
            steps.append(_('Reimbursement 1 = {distance} km × {rate} = {result} {currency}').format(distance=distance_km, rate=rate1, result=reimbursement1, currency=self._format_unit(currency)))
        steps.append('')
        steps.append(_('Step 3: Calculate reimbursement for Rate 2'))
        if rate_unit == 'per_mile':
            steps.append(_('Reimbursement 2 = {distance} miles × {rate} = {result} {currency}').format(distance=distance_miles, rate=rate2, result=reimbursement2, currency=self._format_unit(currency)))
        else:
            steps.append(_('Reimbursement 2 = {distance} km × {rate} = {result} {currency}').format(distance=distance_km, rate=rate2, result=reimbursement2, currency=self._format_unit(currency)))
        steps.append('')
        steps.append(_('Step 4: Calculate difference'))
        steps.append(_('Difference = Reimbursement 2 - Reimbursement 1'))
        steps.append(_('Difference = {r2} - {r1} = {diff} {currency}').format(r2=reimbursement2, r1=reimbursement1, diff=difference, currency=self._format_unit(currency)))
        if reimbursement1 > 0:
            steps.append(_('Percentage Difference = ({diff} / {r1}) × 100% = {pct}%').format(diff=difference, r1=reimbursement1, pct=percent_difference))
        return steps
    
    # Chart data preparation methods
    def _prepare_reimbursement_chart_data(self, distance_km, rate, rate_unit, reimbursement):
        """Prepare chart data for reimbursement calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Distance (km)'), _('Rate'), _('Reimbursement')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [distance_km, rate * 100, reimbursement],  # Scale rate for visibility
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
                            'text': _('Mileage Reimbursement Calculation')
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
            return {'reimbursement_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_trip_cost_chart_data(self, fuel_cost_total, other_costs, total_cost):
        """Prepare chart data for trip cost calculation"""
        try:
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': [_('Fuel Cost'), _('Other Costs')],
                    'datasets': [{
                        'data': [fuel_cost_total, other_costs],
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
                            'text': _('Trip Cost Breakdown (Total: {total})').format(total=total_cost)
                        }
                    }
                }
            }
            return {'trip_cost_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_cost_per_mile_chart_data(self, total_cost, distance_km, cost_per_unit, result_unit):
        """Prepare chart data for cost per mile calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Total Cost'), _('Distance (km)'), _('Cost per Unit')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [total_cost, distance_km, cost_per_unit * 100],  # Scale cost per unit for visibility
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
                            'text': _('Cost per Mile Calculation')
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
            return {'cost_per_mile_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_compare_rates_chart_data(self, rate1, rate2, reimbursement1, reimbursement2, currency):
        """Prepare chart data for rate comparison"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Rate 1'), _('Rate 2'), _('Reimbursement 1'), _('Reimbursement 2')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [rate1 * 100, rate2 * 100, reimbursement1, reimbursement2],  # Scale rates for visibility
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
                            'text': _('Mileage Rate Comparison')
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
            return {'compare_rates_chart': chart_config}
        except Exception as e:
            return None
