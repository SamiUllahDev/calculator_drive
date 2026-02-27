from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ConversionCalculator(View):
    """
    Class-based view for Universal Conversion Calculator with full functionality

    Uses NumPy for efficient numerical operations and precise conversions.
    Supports 10 conversion categories with comprehensive unit options.
    All user-facing strings wrapped with gettext_lazy for i18n translation.
    """
    template_name = 'other_calculators/conversion_calculator.html'

    # ========== CONVERSION DATA ==========
    # All factors convert TO the base unit of each category

    LENGTH_UNITS = {
        'meter': {'factor': 1.0, 'label': _('Meter (m)'), 'symbol': 'm'},
        'kilometer': {'factor': 1000.0, 'label': _('Kilometer (km)'), 'symbol': 'km'},
        'centimeter': {'factor': 0.01, 'label': _('Centimeter (cm)'), 'symbol': 'cm'},
        'millimeter': {'factor': 0.001, 'label': _('Millimeter (mm)'), 'symbol': 'mm'},
        'micrometer': {'factor': 1e-6, 'label': _('Micrometer (μm)'), 'symbol': 'μm'},
        'nanometer': {'factor': 1e-9, 'label': _('Nanometer (nm)'), 'symbol': 'nm'},
        'mile': {'factor': 1609.344, 'label': _('Mile (mi)'), 'symbol': 'mi'},
        'yard': {'factor': 0.9144, 'label': _('Yard (yd)'), 'symbol': 'yd'},
        'foot': {'factor': 0.3048, 'label': _('Foot (ft)'), 'symbol': 'ft'},
        'inch': {'factor': 0.0254, 'label': _('Inch (in)'), 'symbol': 'in'},
        'nautical_mile': {'factor': 1852.0, 'label': _('Nautical Mile (nmi)'), 'symbol': 'nmi'},
        'light_year': {'factor': 9.461e15, 'label': _('Light Year (ly)'), 'symbol': 'ly'},
    }

    WEIGHT_UNITS = {
        'kilogram': {'factor': 1.0, 'label': _('Kilogram (kg)'), 'symbol': 'kg'},
        'gram': {'factor': 0.001, 'label': _('Gram (g)'), 'symbol': 'g'},
        'milligram': {'factor': 1e-6, 'label': _('Milligram (mg)'), 'symbol': 'mg'},
        'microgram': {'factor': 1e-9, 'label': _('Microgram (μg)'), 'symbol': 'μg'},
        'metric_ton': {'factor': 1000.0, 'label': _('Metric Ton (t)'), 'symbol': 't'},
        'pound': {'factor': 0.45359237, 'label': _('Pound (lb)'), 'symbol': 'lb'},
        'ounce': {'factor': 0.02834952, 'label': _('Ounce (oz)'), 'symbol': 'oz'},
        'stone': {'factor': 6.35029, 'label': _('Stone (st)'), 'symbol': 'st'},
        'us_ton': {'factor': 907.185, 'label': _('US Ton (short ton)'), 'symbol': 'US ton'},
        'imperial_ton': {'factor': 1016.05, 'label': _('Imperial Ton (long ton)'), 'symbol': 'imp ton'},
        'carat': {'factor': 0.0002, 'label': _('Carat (ct)'), 'symbol': 'ct'},
    }

    TEMPERATURE_UNITS = {
        'celsius': {'label': _('Celsius (°C)'), 'symbol': '°C'},
        'fahrenheit': {'label': _('Fahrenheit (°F)'), 'symbol': '°F'},
        'kelvin': {'label': _('Kelvin (K)'), 'symbol': 'K'},
        'rankine': {'label': _('Rankine (°R)'), 'symbol': '°R'},
    }

    VOLUME_UNITS = {
        'liter': {'factor': 1.0, 'label': _('Liter (L)'), 'symbol': 'L'},
        'milliliter': {'factor': 0.001, 'label': _('Milliliter (mL)'), 'symbol': 'mL'},
        'cubic_meter': {'factor': 1000.0, 'label': _('Cubic Meter (m³)'), 'symbol': 'm³'},
        'cubic_centimeter': {'factor': 0.001, 'label': _('Cubic Centimeter (cm³)'), 'symbol': 'cm³'},
        'us_gallon': {'factor': 3.78541, 'label': _('US Gallon (gal)'), 'symbol': 'gal'},
        'us_quart': {'factor': 0.946353, 'label': _('US Quart (qt)'), 'symbol': 'qt'},
        'us_pint': {'factor': 0.473176, 'label': _('US Pint (pt)'), 'symbol': 'pt'},
        'us_cup': {'factor': 0.236588, 'label': _('US Cup'), 'symbol': 'cup'},
        'us_fluid_ounce': {'factor': 0.0295735, 'label': _('US Fluid Ounce (fl oz)'), 'symbol': 'fl oz'},
        'us_tablespoon': {'factor': 0.0147868, 'label': _('US Tablespoon (tbsp)'), 'symbol': 'tbsp'},
        'us_teaspoon': {'factor': 0.00492892, 'label': _('US Teaspoon (tsp)'), 'symbol': 'tsp'},
        'imperial_gallon': {'factor': 4.54609, 'label': _('Imperial Gallon'), 'symbol': 'imp gal'},
        'cubic_foot': {'factor': 28.3168, 'label': _('Cubic Foot (ft³)'), 'symbol': 'ft³'},
        'cubic_inch': {'factor': 0.0163871, 'label': _('Cubic Inch (in³)'), 'symbol': 'in³'},
    }

    AREA_UNITS = {
        'square_meter': {'factor': 1.0, 'label': _('Square Meter (m²)'), 'symbol': 'm²'},
        'square_kilometer': {'factor': 1e6, 'label': _('Square Kilometer (km²)'), 'symbol': 'km²'},
        'square_centimeter': {'factor': 1e-4, 'label': _('Square Centimeter (cm²)'), 'symbol': 'cm²'},
        'square_millimeter': {'factor': 1e-6, 'label': _('Square Millimeter (mm²)'), 'symbol': 'mm²'},
        'hectare': {'factor': 10000.0, 'label': _('Hectare (ha)'), 'symbol': 'ha'},
        'acre': {'factor': 4046.86, 'label': _('Acre (ac)'), 'symbol': 'ac'},
        'square_mile': {'factor': 2.59e6, 'label': _('Square Mile (mi²)'), 'symbol': 'mi²'},
        'square_yard': {'factor': 0.836127, 'label': _('Square Yard (yd²)'), 'symbol': 'yd²'},
        'square_foot': {'factor': 0.092903, 'label': _('Square Foot (ft²)'), 'symbol': 'ft²'},
        'square_inch': {'factor': 0.00064516, 'label': _('Square Inch (in²)'), 'symbol': 'in²'},
    }

    SPEED_UNITS = {
        'meter_per_second': {'factor': 1.0, 'label': _('Meter/Second (m/s)'), 'symbol': 'm/s'},
        'kilometer_per_hour': {'factor': 0.277778, 'label': _('Kilometer/Hour (km/h)'), 'symbol': 'km/h'},
        'mile_per_hour': {'factor': 0.44704, 'label': _('Mile/Hour (mph)'), 'symbol': 'mph'},
        'knot': {'factor': 0.514444, 'label': _('Knot (kn)'), 'symbol': 'kn'},
        'foot_per_second': {'factor': 0.3048, 'label': _('Foot/Second (ft/s)'), 'symbol': 'ft/s'},
        'mach': {'factor': 343.0, 'label': _('Mach (Ma)'), 'symbol': 'Ma'},
        'speed_of_light': {'factor': 299792458.0, 'label': _('Speed of Light (c)'), 'symbol': 'c'},
    }

    TIME_UNITS = {
        'second': {'factor': 1.0, 'label': _('Second (s)'), 'symbol': 's'},
        'millisecond': {'factor': 0.001, 'label': _('Millisecond (ms)'), 'symbol': 'ms'},
        'microsecond': {'factor': 1e-6, 'label': _('Microsecond (μs)'), 'symbol': 'μs'},
        'nanosecond': {'factor': 1e-9, 'label': _('Nanosecond (ns)'), 'symbol': 'ns'},
        'minute': {'factor': 60.0, 'label': _('Minute (min)'), 'symbol': 'min'},
        'hour': {'factor': 3600.0, 'label': _('Hour (h)'), 'symbol': 'h'},
        'day': {'factor': 86400.0, 'label': _('Day (d)'), 'symbol': 'd'},
        'week': {'factor': 604800.0, 'label': _('Week (wk)'), 'symbol': 'wk'},
        'month': {'factor': 2629746.0, 'label': _('Month (mo)'), 'symbol': 'mo'},
        'year': {'factor': 31556952.0, 'label': _('Year (yr)'), 'symbol': 'yr'},
        'decade': {'factor': 315569520.0, 'label': _('Decade'), 'symbol': 'decade'},
        'century': {'factor': 3155695200.0, 'label': _('Century'), 'symbol': 'century'},
    }

    DIGITAL_STORAGE_UNITS = {
        'byte': {'factor': 1.0, 'label': _('Byte (B)'), 'symbol': 'B'},
        'kilobyte': {'factor': 1000.0, 'label': _('Kilobyte (KB)'), 'symbol': 'KB'},
        'megabyte': {'factor': 1e6, 'label': _('Megabyte (MB)'), 'symbol': 'MB'},
        'gigabyte': {'factor': 1e9, 'label': _('Gigabyte (GB)'), 'symbol': 'GB'},
        'terabyte': {'factor': 1e12, 'label': _('Terabyte (TB)'), 'symbol': 'TB'},
        'petabyte': {'factor': 1e15, 'label': _('Petabyte (PB)'), 'symbol': 'PB'},
        'kibibyte': {'factor': 1024.0, 'label': _('Kibibyte (KiB)'), 'symbol': 'KiB'},
        'mebibyte': {'factor': 1048576.0, 'label': _('Mebibyte (MiB)'), 'symbol': 'MiB'},
        'gibibyte': {'factor': 1073741824.0, 'label': _('Gibibyte (GiB)'), 'symbol': 'GiB'},
        'tebibyte': {'factor': 1099511627776.0, 'label': _('Tebibyte (TiB)'), 'symbol': 'TiB'},
        'bit': {'factor': 0.125, 'label': _('Bit (b)'), 'symbol': 'b'},
        'kilobit': {'factor': 125.0, 'label': _('Kilobit (Kb)'), 'symbol': 'Kb'},
        'megabit': {'factor': 125000.0, 'label': _('Megabit (Mb)'), 'symbol': 'Mb'},
        'gigabit': {'factor': 125000000.0, 'label': _('Gigabit (Gb)'), 'symbol': 'Gb'},
    }

    PRESSURE_UNITS = {
        'pascal': {'factor': 1.0, 'label': _('Pascal (Pa)'), 'symbol': 'Pa'},
        'kilopascal': {'factor': 1000.0, 'label': _('Kilopascal (kPa)'), 'symbol': 'kPa'},
        'megapascal': {'factor': 1e6, 'label': _('Megapascal (MPa)'), 'symbol': 'MPa'},
        'bar': {'factor': 100000.0, 'label': _('Bar (bar)'), 'symbol': 'bar'},
        'millibar': {'factor': 100.0, 'label': _('Millibar (mbar)'), 'symbol': 'mbar'},
        'psi': {'factor': 6894.76, 'label': _('PSI (psi)'), 'symbol': 'psi'},
        'atmosphere': {'factor': 101325.0, 'label': _('Atmosphere (atm)'), 'symbol': 'atm'},
        'torr': {'factor': 133.322, 'label': _('Torr (Torr)'), 'symbol': 'Torr'},
        'mmhg': {'factor': 133.322, 'label': _('mmHg'), 'symbol': 'mmHg'},
    }

    ENERGY_UNITS = {
        'joule': {'factor': 1.0, 'label': _('Joule (J)'), 'symbol': 'J'},
        'kilojoule': {'factor': 1000.0, 'label': _('Kilojoule (kJ)'), 'symbol': 'kJ'},
        'calorie': {'factor': 4.184, 'label': _('Calorie (cal)'), 'symbol': 'cal'},
        'kilocalorie': {'factor': 4184.0, 'label': _('Kilocalorie (kcal)'), 'symbol': 'kcal'},
        'watt_hour': {'factor': 3600.0, 'label': _('Watt Hour (Wh)'), 'symbol': 'Wh'},
        'kilowatt_hour': {'factor': 3600000.0, 'label': _('Kilowatt Hour (kWh)'), 'symbol': 'kWh'},
        'electronvolt': {'factor': 1.602e-19, 'label': _('Electronvolt (eV)'), 'symbol': 'eV'},
        'btu': {'factor': 1055.06, 'label': _('BTU'), 'symbol': 'BTU'},
        'foot_pound': {'factor': 1.35582, 'label': _('Foot-Pound (ft·lb)'), 'symbol': 'ft·lb'},
        'erg': {'factor': 1e-7, 'label': _('Erg'), 'symbol': 'erg'},
    }

    CATEGORIES = {
        'length': {
            'label': _('Length'),
            'icon': '📏',
            'color': '#3b82f6',
            'units': LENGTH_UNITS,
            'default_from': 'meter',
            'default_to': 'foot',
        },
        'weight': {
            'label': _('Weight / Mass'),
            'icon': '⚖️',
            'color': '#10b981',
            'units': WEIGHT_UNITS,
            'default_from': 'kilogram',
            'default_to': 'pound',
        },
        'temperature': {
            'label': _('Temperature'),
            'icon': '🌡️',
            'color': '#ef4444',
            'units': TEMPERATURE_UNITS,
            'default_from': 'celsius',
            'default_to': 'fahrenheit',
        },
        'volume': {
            'label': _('Volume'),
            'icon': '🧪',
            'color': '#8b5cf6',
            'units': VOLUME_UNITS,
            'default_from': 'liter',
            'default_to': 'us_gallon',
        },
        'area': {
            'label': _('Area'),
            'icon': '📐',
            'color': '#f59e0b',
            'units': AREA_UNITS,
            'default_from': 'square_meter',
            'default_to': 'square_foot',
        },
        'speed': {
            'label': _('Speed'),
            'icon': '🏎️',
            'color': '#06b6d4',
            'units': SPEED_UNITS,
            'default_from': 'kilometer_per_hour',
            'default_to': 'mile_per_hour',
        },
        'time': {
            'label': _('Time'),
            'icon': '⏱️',
            'color': '#ec4899',
            'units': TIME_UNITS,
            'default_from': 'hour',
            'default_to': 'minute',
        },
        'digital_storage': {
            'label': _('Digital Storage'),
            'icon': '💾',
            'color': '#6366f1',
            'units': DIGITAL_STORAGE_UNITS,
            'default_from': 'gigabyte',
            'default_to': 'megabyte',
        },
        'pressure': {
            'label': _('Pressure'),
            'icon': '🔧',
            'color': '#14b8a6',
            'units': PRESSURE_UNITS,
            'default_from': 'atmosphere',
            'default_to': 'psi',
        },
        'energy': {
            'label': _('Energy'),
            'icon': '⚡',
            'color': '#f97316',
            'units': ENERGY_UNITS,
            'default_from': 'joule',
            'default_to': 'calorie',
        },
    }

    def get(self, request):
        """Handle GET request"""
        # Build categories data for template
        # str() is used to force evaluation of lazy translation strings for JSON serialization
        categories_data = {}
        for cat_key, cat_info in self.CATEGORIES.items():
            units = {}
            for unit_key, unit_info in cat_info['units'].items():
                units[unit_key] = {
                    'label': str(unit_info['label']),
                    'symbol': unit_info['symbol'],
                }
            categories_data[cat_key] = {
                'label': str(cat_info['label']),
                'icon': cat_info['icon'],
                'color': cat_info['color'],
                'units': units,
                'default_from': cat_info['default_from'],
                'default_to': cat_info['default_to'],
            }

        context = {
            'calculator_name': _('Conversion Calculator'),
            'page_title': _('Conversion Calculator - Universal Unit Converter'),
            'categories_data': json.dumps(categories_data),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for conversions using NumPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

            category = data.get('category', 'length')
            from_unit = data.get('from_unit', '')
            to_unit = data.get('to_unit', '')
            value = data.get('value', 0)

            # Validate category
            if category not in self.CATEGORIES:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid conversion category.'))
                }, status=400)

            cat_info = self.CATEGORIES[category]
            units = cat_info['units']

            # Validate units
            if from_unit not in units:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid source unit: %(unit)s') % {'unit': from_unit})
                }, status=400)

            if to_unit not in units:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid target unit: %(unit)s') % {'unit': to_unit})
                }, status=400)

            # Validate value
            try:
                value = float(value)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': str(_('Please enter a valid number.'))
                }, status=400)

            # Temperature validation
            if category == 'temperature':
                if from_unit == 'kelvin' and value < 0:
                    return JsonResponse({
                        'success': False,
                        'error': str(_('Kelvin cannot be negative.'))
                    }, status=400)
                if from_unit == 'rankine' and value < 0:
                    return JsonResponse({
                        'success': False,
                        'error': str(_('Rankine cannot be negative.'))
                    }, status=400)
                if from_unit == 'celsius' and value < -273.15:
                    return JsonResponse({
                        'success': False,
                        'error': str(_('Temperature cannot be below absolute zero (-273.15°C).'))
                    }, status=400)
                if from_unit == 'fahrenheit' and value < -459.67:
                    return JsonResponse({
                        'success': False,
                        'error': str(_('Temperature cannot be below absolute zero (-459.67°F).'))
                    }, status=400)

            # Perform conversion
            if category == 'temperature':
                result = self._convert_temperature(value, from_unit, to_unit)
            else:
                result = self._convert_standard(value, from_unit, to_unit, units)

            # Prepare all conversions for this value
            all_conversions = self._get_all_conversions(value, from_unit, category, units)

            # Prepare step-by-step solution
            steps = self._prepare_steps(value, from_unit, to_unit, result, category, units)

            # Prepare chart data
            chart_data = self._prepare_chart_data(value, from_unit, category, units, cat_info['color'])

            # Format result intelligently
            formatted_result = self._format_number(result)
            formatted_value = self._format_number(value)

            from_symbol = units[from_unit]['symbol']
            to_symbol = units[to_unit]['symbol']

            # Conversion formula string
            if category == 'temperature':
                formula = self._get_temperature_formula(from_unit, to_unit)
            else:
                from_factor = units[from_unit].get('factor', 1)
                to_factor = units[to_unit].get('factor', 1)
                ratio = from_factor / to_factor
                formula = f"1 {from_symbol} = {self._format_number(ratio)} {to_symbol}"

            return JsonResponse({
                'success': True,
                'value': value,
                'result': result,
                'formatted_value': formatted_value,
                'formatted_result': formatted_result,
                'from_unit': from_unit,
                'to_unit': to_unit,
                'from_symbol': from_symbol,
                'to_symbol': to_symbol,
                'from_label': str(units[from_unit]['label']),
                'to_label': str(units[to_unit]['label']),
                'category': category,
                'category_label': str(cat_info['label']),
                'category_color': cat_info['color'],
                'formula': formula,
                'step_by_step': steps,
                'all_conversions': all_conversions,
                'chart_data': chart_data,
            })

        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input: %(error)s') % {'error': str(e)})
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('An error occurred during conversion.'))
            }, status=500)

    def _convert_standard(self, value, from_unit, to_unit, units):
        """Convert using standard factor-based conversion with NumPy"""
        from_factor = np.float64(units[from_unit]['factor'])
        to_factor = np.float64(units[to_unit]['factor'])
        # Convert: value * from_factor / to_factor
        base_value = np.multiply(np.float64(value), from_factor)
        result = np.divide(base_value, to_factor)
        return float(result)

    def _convert_temperature(self, value, from_unit, to_unit):
        """Convert temperature with special formulas using NumPy"""
        val = np.float64(value)

        # Convert to Celsius first
        if from_unit == 'celsius':
            celsius = val
        elif from_unit == 'fahrenheit':
            celsius = np.multiply(np.subtract(val, 32.0), 5.0 / 9.0)
        elif from_unit == 'kelvin':
            celsius = np.subtract(val, 273.15)
        elif from_unit == 'rankine':
            celsius = np.multiply(np.subtract(val, 491.67), 5.0 / 9.0)
        else:
            celsius = val

        # Convert from Celsius to target
        if to_unit == 'celsius':
            result = celsius
        elif to_unit == 'fahrenheit':
            result = np.add(np.multiply(celsius, 9.0 / 5.0), 32.0)
        elif to_unit == 'kelvin':
            result = np.add(celsius, 273.15)
        elif to_unit == 'rankine':
            result = np.add(np.multiply(celsius, 9.0 / 5.0), 491.67)
        else:
            result = celsius

        return float(result)

    def _get_all_conversions(self, value, from_unit, category, units):
        """Get conversion results for all units in the category"""
        conversions = []
        for unit_key, unit_info in units.items():
            if category == 'temperature':
                converted = self._convert_temperature(value, from_unit, unit_key)
            else:
                converted = self._convert_standard(value, from_unit, unit_key, units)

            conversions.append({
                'unit': unit_key,
                'label': str(unit_info['label']),
                'symbol': unit_info['symbol'],
                'value': converted,
                'formatted': self._format_number(converted),
                'is_source': unit_key == from_unit,
            })
        return conversions

    def _prepare_steps(self, value, from_unit, to_unit, result, category, units):
        """Prepare step-by-step solution"""
        steps = []
        from_symbol = units[from_unit]['symbol']
        to_symbol = units[to_unit]['symbol']

        steps.append({
            'title': str(_('Step 1: Identify the conversion')),
            'content': str(_('Convert %(value)s %(from)s to %(to)s') % {
                'value': self._format_number(value),
                'from': from_symbol,
                'to': to_symbol
            })
        })

        if category == 'temperature':
            formula = self._get_temperature_formula(from_unit, to_unit)
            steps.append({
                'title': str(_('Step 2: Apply the formula')),
                'content': formula
            })
            steps.append({
                'title': str(_('Step 3: Calculate')),
                'content': f'{self._format_number(value)} {from_symbol} = {self._format_number(result)} {to_symbol}'
            })
        else:
            from_factor = units[from_unit]['factor']
            to_factor = units[to_unit]['factor']
            base_value = value * from_factor

            # Get base unit name
            base_unit = None
            for uk, ui in units.items():
                if ui['factor'] == 1.0:
                    base_unit = ui['symbol']
                    break
            if not base_unit:
                base_unit = str(_('base unit'))

            steps.append({
                'title': str(_('Step 2: Convert to base unit')),
                'content': f'{self._format_number(value)} {from_symbol} × {from_factor} = {self._format_number(base_value)} {base_unit}'
            })
            steps.append({
                'title': str(_('Step 3: Convert to target unit')),
                'content': f'{self._format_number(base_value)} {base_unit} ÷ {to_factor} = {self._format_number(result)} {to_symbol}'
            })

        steps.append({
            'title': str(_('Result')),
            'content': f'{self._format_number(value)} {from_symbol} = {self._format_number(result)} {to_symbol}'
        })

        return steps

    def _get_temperature_formula(self, from_unit, to_unit):
        """Get temperature conversion formula string"""
        formulas = {
            ('celsius', 'fahrenheit'): '°F = (°C × 9/5) + 32',
            ('celsius', 'kelvin'): 'K = °C + 273.15',
            ('celsius', 'rankine'): '°R = (°C × 9/5) + 491.67',
            ('fahrenheit', 'celsius'): '°C = (°F − 32) × 5/9',
            ('fahrenheit', 'kelvin'): 'K = (°F − 32) × 5/9 + 273.15',
            ('fahrenheit', 'rankine'): '°R = °F + 459.67',
            ('kelvin', 'celsius'): '°C = K − 273.15',
            ('kelvin', 'fahrenheit'): '°F = (K − 273.15) × 9/5 + 32',
            ('kelvin', 'rankine'): '°R = K × 9/5',
            ('rankine', 'celsius'): '°C = (°R − 491.67) × 5/9',
            ('rankine', 'fahrenheit'): '°F = °R − 459.67',
            ('rankine', 'kelvin'): 'K = °R × 5/9',
        }
        if from_unit == to_unit:
            return str(_('Same unit — no conversion needed'))
        return formulas.get((from_unit, to_unit), str(_('Direct conversion')))

    def _prepare_chart_data(self, value, from_unit, category, units, color):
        """Prepare chart data for visualization"""
        # Pick top 6 most common units for chart
        chart_units = list(units.keys())[:6]
        labels = []
        values = []
        colors = []

        for unit_key in chart_units:
            if category == 'temperature':
                converted = self._convert_temperature(value, from_unit, unit_key)
            else:
                converted = self._convert_standard(value, from_unit, unit_key, units)

            labels.append(units[unit_key]['symbol'])
            values.append(round(converted, 6))

            if unit_key == from_unit:
                colors.append(color)
            else:
                colors.append(color + '80')  # 50% opacity hex

        bar_chart = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Converted Values')),
                    'data': values,
                    'backgroundColor': colors,
                    'borderColor': color,
                    'borderWidth': 2,
                    'borderRadius': 8,
                }]
            },
        }

        return {
            'bar_chart': bar_chart,
            'primary_color': color,
        }

    def _format_number(self, num):
        """Format number intelligently for display"""
        if num == 0:
            return '0'

        abs_num = abs(num)

        # Very large or very small numbers use scientific notation
        if abs_num >= 1e12 or (abs_num < 1e-6 and abs_num > 0):
            return f'{num:.6e}'

        # Numbers with no decimal part
        if num == int(num) and abs_num < 1e12:
            return f'{int(num):,}'

        # Determine decimal places based on magnitude
        if abs_num >= 1000:
            return f'{num:,.2f}'
        elif abs_num >= 1:
            return f'{num:,.4f}'
        elif abs_num >= 0.01:
            return f'{num:.6f}'
        else:
            return f'{num:.8f}'
