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
class GdpCalculator(View):
    """
    Professional GDP Calculator with Comprehensive Features
    
    This calculator provides GDP calculations with:
    - Calculate GDP using expenditure approach (C + I + G + (X - M))
    - Calculate GDP using income approach (W + R + I + P)
    - Calculate GDP growth rate
    - Calculate GDP per capita
    - Calculate GDP deflator
    - Unit conversions (billions, trillions, etc.)
    
    Features:
    - Supports multiple calculation modes
    - Handles various units
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/gdp_calculator.html'
    
    # Currency unit conversion factors (to base units)
    CURRENCY_CONVERSIONS = {
        'millions': 1e-3,      # 1 million = 0.001 billion
        'billions': 1.0,       # Base unit
        'trillions': 1000.0,   # 1 trillion = 1000 billion
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        unit_map = {
            'millions': 'Million',
            'billions': 'Billion',
            'trillions': 'Trillion',
        }
        return unit_map.get(unit, unit)
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('GDP Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'expenditure')
            
            if calc_type == 'expenditure':
                return self._calculate_expenditure_gdp(data)
            elif calc_type == 'income':
                return self._calculate_income_gdp(data)
            elif calc_type == 'growth_rate':
                return self._calculate_growth_rate(data)
            elif calc_type == 'per_capita':
                return self._calculate_per_capita(data)
            elif calc_type == 'deflator':
                return self._calculate_deflator(data)
            elif calc_type == 'convert':
                return self._convert_units(data)
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
    
    def _calculate_expenditure_gdp(self, data):
        """Calculate GDP using expenditure approach: GDP = C + I + G + (X - M)"""
        try:
            # Check for required fields
            if 'consumption' not in data or data.get('consumption') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Consumption (C) is required.')
                }, status=400)
            
            if 'investment' not in data or data.get('investment') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Investment (I) is required.')
                }, status=400)
            
            if 'government' not in data or data.get('government') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Government spending (G) is required.')
                }, status=400)
            
            if 'exports' not in data or data.get('exports') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Exports (X) is required.')
                }, status=400)
            
            if 'imports' not in data or data.get('imports') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Imports (M) is required.')
                }, status=400)
            
            try:
                consumption = float(data.get('consumption', 0))
                investment = float(data.get('investment', 0))
                government = float(data.get('government', 0))
                exports = float(data.get('exports', 0))
                imports = float(data.get('imports', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            unit = data.get('unit', 'billions')
            result_unit = data.get('result_unit', 'billions')
            
            # Validate units
            if unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid currency unit.')
                }, status=400)
            
            if result_unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges (allow negative for net exports)
            if consumption < 0 or investment < 0 or government < 0 or exports < 0 or imports < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Consumption, Investment, Government spending, Exports, and Imports must be non-negative.')
                }, status=400)
            
            # Convert to base units (billions)
            consumption_base = float(consumption * self.CURRENCY_CONVERSIONS[unit])
            investment_base = float(investment * self.CURRENCY_CONVERSIONS[unit])
            government_base = float(government * self.CURRENCY_CONVERSIONS[unit])
            exports_base = float(exports * self.CURRENCY_CONVERSIONS[unit])
            imports_base = float(imports * self.CURRENCY_CONVERSIONS[unit])
            
            # Calculate net exports
            net_exports_base = float(np.subtract(exports_base, imports_base))
            
            # Calculate GDP: GDP = C + I + G + (X - M)
            gdp_base = float(np.add(
                np.add(consumption_base, investment_base),
                np.add(government_base, net_exports_base)
            ))
            
            # Convert to result unit
            gdp_result = float(np.divide(gdp_base, self.CURRENCY_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(gdp_result) or math.isnan(gdp_result) or np.isinf(gdp_result) or np.isnan(gdp_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_expenditure_steps(consumption, investment, government, exports, imports, unit, gdp_result, result_unit, consumption_base, investment_base, government_base, exports_base, imports_base, net_exports_base, gdp_base)
            
            # Prepare chart data
            chart_data = self._prepare_expenditure_chart_data(consumption_base, investment_base, government_base, exports_base, imports_base, gdp_base)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'expenditure',
                'consumption': consumption,
                'investment': investment,
                'government': government,
                'exports': exports,
                'imports': imports,
                'unit': unit,
                'gdp': gdp_result,
                'result_unit': result_unit,
                'net_exports': float(net_exports_base / self.CURRENCY_CONVERSIONS[result_unit]),
                'gdp_base': gdp_base,
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
                'error': _('Error calculating GDP: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_income_gdp(self, data):
        """Calculate GDP using income approach: GDP = W + R + I + P"""
        try:
            # Check for required fields
            if 'wages' not in data or data.get('wages') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Wages (W) is required.')
                }, status=400)
            
            if 'rent' not in data or data.get('rent') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Rent (R) is required.')
                }, status=400)
            
            if 'interest' not in data or data.get('interest') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Interest (I) is required.')
                }, status=400)
            
            if 'profit' not in data or data.get('profit') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Profit (P) is required.')
                }, status=400)
            
            try:
                wages = float(data.get('wages', 0))
                rent = float(data.get('rent', 0))
                interest = float(data.get('interest', 0))
                profit = float(data.get('profit', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            unit = data.get('unit', 'billions')
            result_unit = data.get('result_unit', 'billions')
            
            # Validate units
            if unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid currency unit.')
                }, status=400)
            
            if result_unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid result unit.')
                }, status=400)
            
            # Validate ranges
            if wages < 0 or rent < 0 or interest < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Wages, Rent, and Interest must be non-negative.')
                }, status=400)
            
            # Convert to base units
            wages_base = float(wages * self.CURRENCY_CONVERSIONS[unit])
            rent_base = float(rent * self.CURRENCY_CONVERSIONS[unit])
            interest_base = float(interest * self.CURRENCY_CONVERSIONS[unit])
            profit_base = float(profit * self.CURRENCY_CONVERSIONS[unit])
            
            # Calculate GDP: GDP = W + R + I + P
            gdp_base = float(np.add(
                np.add(wages_base, rent_base),
                np.add(interest_base, profit_base)
            ))
            
            # Convert to result unit
            gdp_result = float(np.divide(gdp_base, self.CURRENCY_CONVERSIONS[result_unit]))
            
            # Validate result
            if math.isinf(gdp_result) or math.isnan(gdp_result) or np.isinf(gdp_result) or np.isnan(gdp_result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_income_steps(wages, rent, interest, profit, unit, gdp_result, result_unit, wages_base, rent_base, interest_base, profit_base, gdp_base)
            
            # Prepare chart data
            chart_data = self._prepare_income_chart_data(wages_base, rent_base, interest_base, profit_base, gdp_base)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'income',
                'wages': wages,
                'rent': rent,
                'interest': interest,
                'profit': profit,
                'unit': unit,
                'gdp': gdp_result,
                'result_unit': result_unit,
                'gdp_base': gdp_base,
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
                'error': _('Error calculating GDP: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_growth_rate(self, data):
        """Calculate GDP growth rate"""
        try:
            if 'gdp_current' not in data or data.get('gdp_current') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Current GDP is required.')
                }, status=400)
            
            if 'gdp_previous' not in data or data.get('gdp_previous') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Previous GDP is required.')
                }, status=400)
            
            try:
                gdp_current = float(data.get('gdp_current', 0))
                gdp_previous = float(data.get('gdp_previous', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            unit = data.get('unit', 'billions')
            
            # Validate units
            if unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid currency unit.')
                }, status=400)
            
            # Validate ranges
            if gdp_current < 0 or gdp_previous < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('GDP values must be non-negative.')
                }, status=400)
            
            if gdp_previous == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Previous GDP cannot be zero for growth rate calculation.')
                }, status=400)
            
            # Convert to base units
            gdp_current_base = float(gdp_current * self.CURRENCY_CONVERSIONS[unit])
            gdp_previous_base = float(gdp_previous * self.CURRENCY_CONVERSIONS[unit])
            
            # Calculate growth rate: Growth Rate = ((Current - Previous) / Previous) × 100
            growth_rate = float(np.multiply(
                np.divide(
                    np.subtract(gdp_current_base, gdp_previous_base),
                    gdp_previous_base
                ),
                100.0
            ))
            
            # Validate result
            if math.isinf(growth_rate) or math.isnan(growth_rate) or np.isinf(growth_rate) or np.isnan(growth_rate):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_growth_rate_steps(gdp_current, gdp_previous, unit, growth_rate, gdp_current_base, gdp_previous_base)
            
            chart_data = self._prepare_growth_rate_chart_data(gdp_previous_base, gdp_current_base, growth_rate)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'growth_rate',
                'gdp_current': gdp_current,
                'gdp_previous': gdp_previous,
                'unit': unit,
                'growth_rate': growth_rate,
                'gdp_current_base': gdp_current_base,
                'gdp_previous_base': gdp_previous_base,
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
                'error': _('Error calculating growth rate: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_per_capita(self, data):
        """Calculate GDP per capita"""
        try:
            if 'gdp' not in data or data.get('gdp') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('GDP is required.')
                }, status=400)
            
            if 'population' not in data or data.get('population') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Population is required.')
                }, status=400)
            
            try:
                gdp = float(data.get('gdp', 0))
                population = float(data.get('population', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            gdp_unit = data.get('gdp_unit', 'billions')
            population_unit = data.get('population_unit', 'millions')
            
            # Validate units
            if gdp_unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid GDP unit.')
                }, status=400)
            
            # Validate ranges
            if gdp < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('GDP must be non-negative.')
                }, status=400)
            
            if population <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Population must be greater than zero.')
                }, status=400)
            
            # Convert GDP to base units (billions)
            gdp_base = float(gdp * self.CURRENCY_CONVERSIONS[gdp_unit])
            
            # Convert population to millions (standard for per capita calculations)
            if population_unit == 'millions':
                population_millions = population
            elif population_unit == 'thousands':
                population_millions = float(population / 1000.0)
            elif population_unit == 'billions':
                population_millions = float(population * 1000.0)
            else:
                population_millions = population
            
            # Calculate GDP per capita: GDP per capita = GDP / Population
            # GDP in billions, population in millions
            # Result: (GDP billions × 1000) / Population millions = thousands per person
            gdp_per_capita = float(np.divide(
                np.multiply(gdp_base, 1000.0),
                population_millions
            ))
            
            # Validate result
            if math.isinf(gdp_per_capita) or math.isnan(gdp_per_capita) or np.isinf(gdp_per_capita) or np.isnan(gdp_per_capita):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_per_capita_steps(gdp, gdp_unit, population, population_unit, gdp_per_capita, gdp_base, population_millions)
            
            chart_data = self._prepare_per_capita_chart_data(gdp_base, population_millions, gdp_per_capita)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'per_capita',
                'gdp': gdp,
                'gdp_unit': gdp_unit,
                'population': population,
                'population_unit': population_unit,
                'gdp_per_capita': gdp_per_capita,
                'gdp_base': gdp_base,
                'population_millions': population_millions,
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
                'error': _('Error calculating GDP per capita: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_deflator(self, data):
        """Calculate GDP deflator"""
        try:
            if 'nominal_gdp' not in data or data.get('nominal_gdp') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Nominal GDP is required.')
                }, status=400)
            
            if 'real_gdp' not in data or data.get('real_gdp') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Real GDP is required.')
                }, status=400)
            
            try:
                nominal_gdp = float(data.get('nominal_gdp', 0))
                real_gdp = float(data.get('real_gdp', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            unit = data.get('unit', 'billions')
            
            # Validate units
            if unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid currency unit.')
                }, status=400)
            
            # Validate ranges
            if nominal_gdp < 0 or real_gdp < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('GDP values must be non-negative.')
                }, status=400)
            
            if real_gdp == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Real GDP cannot be zero for deflator calculation.')
                }, status=400)
            
            # Convert to base units
            nominal_gdp_base = float(nominal_gdp * self.CURRENCY_CONVERSIONS[unit])
            real_gdp_base = float(real_gdp * self.CURRENCY_CONVERSIONS[unit])
            
            # Calculate GDP deflator: Deflator = (Nominal GDP / Real GDP) × 100
            deflator = float(np.multiply(
                np.divide(nominal_gdp_base, real_gdp_base),
                100.0
            ))
            
            # Validate result
            if math.isinf(deflator) or math.isnan(deflator) or np.isinf(deflator) or np.isnan(deflator):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_deflator_steps(nominal_gdp, real_gdp, unit, deflator, nominal_gdp_base, real_gdp_base)
            
            chart_data = self._prepare_deflator_chart_data(nominal_gdp_base, real_gdp_base, deflator)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'deflator',
                'nominal_gdp': nominal_gdp,
                'real_gdp': real_gdp,
                'unit': unit,
                'deflator': deflator,
                'nominal_gdp_base': nominal_gdp_base,
                'real_gdp_base': real_gdp_base,
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
                'error': _('Error calculating GDP deflator: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_units(self, data):
        """Convert currency units"""
        try:
            if 'value' not in data or data.get('value') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('GDP value is required.')
                }, status=400)
            
            try:
                value = float(data.get('value', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            from_unit = data.get('from_unit', 'billions')
            to_unit = data.get('to_unit', 'billions')
            
            # Validate units
            if from_unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid source unit.')
                }, status=400)
            
            if to_unit not in self.CURRENCY_CONVERSIONS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid target unit.')
                }, status=400)
            
            if value < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('GDP value must be non-negative.')
                }, status=400)
            
            # Convert to billions first, then to target unit
            billions_value = float(value * self.CURRENCY_CONVERSIONS[from_unit])
            result = float(np.divide(billions_value, self.CURRENCY_CONVERSIONS[to_unit]))
            
            # Validate result
            if math.isinf(result) or math.isnan(result) or np.isinf(result) or np.isnan(result):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid conversion result.')
                }, status=400)
            
            steps = self._prepare_convert_steps(value, from_unit, to_unit, result, billions_value)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert',
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
    def _prepare_expenditure_steps(self, consumption, investment, government, exports, imports, unit, gdp_result, result_unit, consumption_base, investment_base, government_base, exports_base, imports_base, net_exports_base, gdp_base):
        """Prepare step-by-step solution for expenditure GDP calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Consumption (C): {val} {unit}').format(val=consumption, unit=self._format_unit(unit)))
        steps.append(_('Investment (I): {val} {unit}').format(val=investment, unit=self._format_unit(unit)))
        steps.append(_('Government Spending (G): {val} {unit}').format(val=government, unit=self._format_unit(unit)))
        steps.append(_('Exports (X): {val} {unit}').format(val=exports, unit=self._format_unit(unit)))
        steps.append(_('Imports (M): {val} {unit}').format(val=imports, unit=self._format_unit(unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (billions)'))
        if unit != 'billions':
            steps.append(_('All values converted to billions'))
        steps.append('')
        steps.append(_('Step 3: Calculate net exports'))
        steps.append(_('Formula: Net Exports = Exports - Imports'))
        steps.append(_('Net Exports = {x} - {m} = {nx} billions').format(x=exports_base, m=imports_base, nx=net_exports_base))
        steps.append('')
        steps.append(_('Step 4: Apply the expenditure approach formula'))
        steps.append(_('Formula: GDP = C + I + G + (X - M)'))
        steps.append(_('GDP = {c} + {i} + {g} + {nx}').format(c=consumption_base, i=investment_base, g=government_base, nx=net_exports_base))
        steps.append(_('GDP = {gdp} billions').format(gdp=gdp_base))
        steps.append('')
        if result_unit != 'billions':
            steps.append(_('Step 5: Convert to desired unit'))
            steps.append(_('GDP = {gdp} {unit}').format(gdp=gdp_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 5: Result'))
            steps.append(_('GDP = {gdp} billions').format(gdp=gdp_result))
        return steps
    
    def _prepare_income_steps(self, wages, rent, interest, profit, unit, gdp_result, result_unit, wages_base, rent_base, interest_base, profit_base, gdp_base):
        """Prepare step-by-step solution for income GDP calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Wages (W): {val} {unit}').format(val=wages, unit=self._format_unit(unit)))
        steps.append(_('Rent (R): {val} {unit}').format(val=rent, unit=self._format_unit(unit)))
        steps.append(_('Interest (I): {val} {unit}').format(val=interest, unit=self._format_unit(unit)))
        steps.append(_('Profit (P): {val} {unit}').format(val=profit, unit=self._format_unit(unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (billions)'))
        if unit != 'billions':
            steps.append(_('All values converted to billions'))
        steps.append('')
        steps.append(_('Step 3: Apply the income approach formula'))
        steps.append(_('Formula: GDP = W + R + I + P'))
        steps.append(_('GDP = {w} + {r} + {i} + {p}').format(w=wages_base, r=rent_base, i=interest_base, p=profit_base))
        steps.append(_('GDP = {gdp} billions').format(gdp=gdp_base))
        steps.append('')
        if result_unit != 'billions':
            steps.append(_('Step 4: Convert to desired unit'))
            steps.append(_('GDP = {gdp} {unit}').format(gdp=gdp_result, unit=self._format_unit(result_unit)))
        else:
            steps.append(_('Step 4: Result'))
            steps.append(_('GDP = {gdp} billions').format(gdp=gdp_result))
        return steps
    
    def _prepare_growth_rate_steps(self, gdp_current, gdp_previous, unit, growth_rate, gdp_current_base, gdp_previous_base):
        """Prepare step-by-step solution for growth rate calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Current GDP: {val} {unit}').format(val=gdp_current, unit=self._format_unit(unit)))
        steps.append(_('Previous GDP: {val} {unit}').format(val=gdp_previous, unit=self._format_unit(unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (billions)'))
        if unit != 'billions':
            steps.append(_('All values converted to billions'))
        steps.append('')
        steps.append(_('Step 3: Apply the growth rate formula'))
        steps.append(_('Formula: Growth Rate = ((Current - Previous) / Previous) × 100'))
        steps.append(_('Growth Rate = (({current} - {previous}) / {previous}) × 100').format(current=gdp_current_base, previous=gdp_previous_base))
        change = gdp_current_base - gdp_previous_base
        steps.append(_('Growth Rate = ({change} / {previous}) × 100').format(change=change, previous=gdp_previous_base))
        steps.append(_('Growth Rate = {rate}%').format(rate=growth_rate))
        return steps
    
    def _prepare_per_capita_steps(self, gdp, gdp_unit, population, population_unit, gdp_per_capita, gdp_base, population_millions):
        """Prepare step-by-step solution for per capita calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('GDP: {val} {unit}').format(val=gdp, unit=self._format_unit(gdp_unit)))
        steps.append(_('Population: {val} {unit}').format(val=population, unit=population_unit))
        steps.append('')
        steps.append(_('Step 2: Convert to base units'))
        if gdp_unit != 'billions':
            steps.append(_('GDP in billions: {val} billions').format(val=gdp_base))
        if population_unit != 'millions':
            steps.append(_('Population in millions: {val} millions').format(val=population_millions))
        steps.append('')
        steps.append(_('Step 3: Apply the per capita formula'))
        steps.append(_('Formula: GDP per capita = (GDP × 1000) / Population'))
        steps.append(_('GDP per capita = ({gdp} billions × 1000) / {pop} millions').format(gdp=gdp_base, pop=population_millions))
        steps.append(_('GDP per capita = {result} (thousands per person)').format(result=gdp_per_capita))
        return steps
    
    def _prepare_deflator_steps(self, nominal_gdp, real_gdp, unit, deflator, nominal_gdp_base, real_gdp_base):
        """Prepare step-by-step solution for deflator calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Nominal GDP: {val} {unit}').format(val=nominal_gdp, unit=self._format_unit(unit)))
        steps.append(_('Real GDP: {val} {unit}').format(val=real_gdp, unit=self._format_unit(unit)))
        steps.append('')
        steps.append(_('Step 2: Convert to base units (billions)'))
        if unit != 'billions':
            steps.append(_('All values converted to billions'))
        steps.append('')
        steps.append(_('Step 3: Apply the deflator formula'))
        steps.append(_('Formula: GDP Deflator = (Nominal GDP / Real GDP) × 100'))
        steps.append(_('Deflator = ({nominal} / {real}) × 100').format(nominal=nominal_gdp_base, real=real_gdp_base))
        steps.append(_('GDP Deflator = {deflator}').format(deflator=deflator))
        return steps
    
    def _prepare_convert_steps(self, value, from_unit, to_unit, result, billions_value):
        """Prepare step-by-step solution for unit conversion"""
        steps = []
        steps.append(_('Step 1: Identify the given value'))
        steps.append(_('GDP: {value} {unit}').format(value=value, unit=self._format_unit(from_unit)))
        steps.append('')
        if from_unit != 'billions':
            steps.append(_('Step 2: Convert to billions'))
            if from_unit == 'millions':
                steps.append(_('Billions = Millions / 1000'))
                steps.append(_('Billions = {val} / 1000 = {billions} billions').format(val=value, billions=billions_value))
            elif from_unit == 'trillions':
                steps.append(_('Billions = Trillions × 1000'))
                steps.append(_('Billions = {val} × 1000 = {billions} billions').format(val=value, billions=billions_value))
            steps.append('')
        if to_unit != 'billions':
            steps.append(_('Step 3: Convert from billions to {unit}').format(unit=self._format_unit(to_unit)))
            if to_unit == 'millions':
                steps.append(_('Millions = Billions × 1000'))
                steps.append(_('Millions = {billions} × 1000 = {result} millions').format(billions=billions_value, result=result))
            elif to_unit == 'trillions':
                steps.append(_('Trillions = Billions / 1000'))
                steps.append(_('Trillions = {billions} / 1000 = {result} trillions').format(billions=billions_value, result=result))
        else:
            steps.append(_('Step 2: Result'))
            steps.append(_('GDP = {result} billions').format(result=result))
        return steps
    
    # Chart data preparation methods
    def _prepare_expenditure_chart_data(self, consumption_base, investment_base, government_base, exports_base, imports_base, gdp_base):
        """Prepare chart data for expenditure GDP calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Consumption'), _('Investment'), _('Government'), _('Exports'), _('Imports'), _('GDP')],
                    'datasets': [{
                        'label': _('GDP Components'),
                        'data': [consumption_base, investment_base, government_base, exports_base, imports_base, gdp_base],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(239, 68, 68, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#8b5cf6',
                            '#ec4899',
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
                            'text': _('GDP Expenditure Approach Breakdown')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value (Billions)')
                            }
                        }
                    }
                }
            }
            return {'expenditure_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_income_chart_data(self, wages_base, rent_base, interest_base, profit_base, gdp_base):
        """Prepare chart data for income GDP calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Wages'), _('Rent'), _('Interest'), _('Profit'), _('GDP')],
                    'datasets': [{
                        'label': _('GDP Components'),
                        'data': [wages_base, rent_base, interest_base, profit_base, gdp_base],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(239, 68, 68, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#8b5cf6',
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
                            'text': _('GDP Income Approach Breakdown')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value (Billions)')
                            }
                        }
                    }
                }
            }
            return {'income_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_growth_rate_chart_data(self, gdp_previous_base, gdp_current_base, growth_rate):
        """Prepare chart data for growth rate calculation"""
        try:
            chart_config = {
                'type': 'line',
                'data': {
                    'labels': [_('Previous GDP'), _('Current GDP')],
                    'datasets': [{
                        'label': _('GDP (Billions)'),
                        'data': [gdp_previous_base, gdp_current_base],
                        'borderColor': 'rgba(59, 130, 246, 1)',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'borderWidth': 2,
                        'fill': True,
                        'tension': 0.4
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'top'
                        },
                        'title': {
                            'display': True,
                            'text': _('GDP Growth Rate: {rate}%').format(rate=growth_rate)
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('GDP (Billions)')
                            }
                        }
                    }
                }
            }
            return {'growth_rate_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_per_capita_chart_data(self, gdp_base, population_millions, gdp_per_capita):
        """Prepare chart data for per capita calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('GDP (Billions)'), _('Population (Millions)'), _('GDP per Capita')],
                    'datasets': [{
                        'data': [gdp_base, population_millions, gdp_per_capita],
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
                            'text': _('GDP per Capita Breakdown')
                        }
                    }
                }
            }
            return {'per_capita_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_deflator_chart_data(self, nominal_gdp_base, real_gdp_base, deflator):
        """Prepare chart data for deflator calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Nominal GDP'), _('Real GDP'), _('Deflator')],
                    'datasets': [{
                        'label': _('GDP Values'),
                        'data': [nominal_gdp_base, real_gdp_base, deflator],
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
                            'text': _('GDP Deflator Calculation')
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
            return {'deflator_chart': chart_config}
        except Exception as e:
            return None
