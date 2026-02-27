from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np
from sympy import symbols, simplify, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class WeightCalculator(View):
    """
    Professional Weight Calculator with Comprehensive Features

    Uses NumPy for efficient numerical operations and array-based calculations.
    Uses SymPy for precise mathematical computations and formula representation.

    Supports:
    - Convert between weight units (kg, lbs, oz, grams, stones, etc.)
    - Calculate weight from mass and gravity (W = m × g)
    - Calculate mass from weight and gravity (m = W / g)
    - Calculate weight on different planets
    - Step-by-step solutions
    - Interactive chart visualizations
    """
    template_name = 'other_calculators/weight_calculator.html'

    # Weight unit conversions (to kilograms) using SymPy Float for precision
    WEIGHT_UNITS = {
        'kg': Float('1.0'),
        'g': Float('0.001'),
        'mg': Float('0.000001'),
        'lb': Float('0.45359237'),
        'oz': Float('0.028349523125'),
        'st': Float('6.35029318'),
        't': Float('1000.0'),
        'ton': Float('907.18474'),
        'ct': Float('0.0002'),
    }

    UNIT_LABELS = {
        'kg': _('Kilogram'),
        'g': _('Gram'),
        'mg': _('Milligram'),
        'lb': _('Pound'),
        'oz': _('Ounce'),
        'st': _('Stone'),
        't': _('Metric Ton'),
        'ton': _('US Ton'),
        'ct': _('Carat'),
    }

    # Gravitational acceleration (m/s²) using SymPy Float
    GRAVITY = {
        'earth': Float('9.80665'),
        'moon': Float('1.625'),
        'mars': Float('3.711'),
        'jupiter': Float('24.79'),
        'saturn': Float('10.44'),
        'venus': Float('8.87'),
        'mercury': Float('3.7'),
        'neptune': Float('11.15'),
        'uranus': Float('8.87'),
        'sun': Float('274.0'),
    }

    PLANET_LABELS = {
        'earth': _('Earth'),
        'moon': _('Moon'),
        'mars': _('Mars'),
        'jupiter': _('Jupiter'),
        'saturn': _('Saturn'),
        'venus': _('Venus'),
        'mercury': _('Mercury'),
        'neptune': _('Neptune'),
        'uranus': _('Uranus'),
        'sun': _('Sun'),
    }

    PLANET_COLORS = {
        'earth': '#3b82f6',
        'moon': '#9ca3af',
        'mars': '#ef4444',
        'jupiter': '#f59e0b',
        'saturn': '#d97706',
        'venus': '#f97316',
        'mercury': '#6b7280',
        'neptune': '#6366f1',
        'uranus': '#06b6d4',
        'sun': '#eab308',
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Weight Calculator'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations using NumPy and SymPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc_type = data.get('calc_type', 'convert')

            if calc_type == 'convert':
                return self._convert_weight(data)
            elif calc_type == 'from_mass':
                return self._calculate_from_mass(data)
            elif calc_type == 'from_weight':
                return self._calculate_from_weight(data)
            elif calc_type == 'planet':
                return self._calculate_planet_weight(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Invalid calculation type.'))
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid JSON data.'))
            }, status=400)
        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input')) + ': ' + str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(_('An error occurred during calculation.'))
            }, status=500)

    def _convert_weight(self, data):
        """Convert weight between different units using SymPy for precision"""
        try:
            weight = float(data.get('weight', 0))
            from_unit = data.get('from_unit', 'kg')
            to_unit = data.get('to_unit', 'lb')
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input. Please enter numeric values.'))
            }, status=400)

        # Validate weight using NumPy
        weight_array = np.array([weight])
        if np.any(weight_array < 0):
            return JsonResponse({
                'success': False,
                'error': str(_('Weight must be non-negative.'))
            }, status=400)

        if from_unit not in self.WEIGHT_UNITS or to_unit not in self.WEIGHT_UNITS:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid unit selected.'))
            }, status=400)

        # SymPy symbolic conversion for precision
        w = symbols('w', real=True, nonnegative=True)
        conversion_formula = w * self.WEIGHT_UNITS[from_unit] / self.WEIGHT_UNITS[to_unit]
        conversion_simplified = simplify(conversion_formula)

        # Evaluate with SymPy
        result_symbolic = conversion_simplified.subs(w, Float(weight, 15))
        result = float(N(result_symbolic, 10))

        # Intermediate: weight in kg
        weight_in_kg_symbolic = Float(weight, 15) * self.WEIGHT_UNITS[from_unit]
        weight_in_kg = float(N(weight_in_kg_symbolic, 10))

        # NumPy verification
        result_numpy = float(np.float64(weight) * np.float64(float(self.WEIGHT_UNITS[from_unit])) / np.float64(float(self.WEIGHT_UNITS[to_unit])))

        # Prepare step-by-step solution
        steps = self._prepare_convert_steps(weight, from_unit, to_unit, weight_in_kg, result)

        # Prepare chart data
        chart_data = self._prepare_convert_chart_data(weight, result, from_unit, to_unit)

        # Prepare all-unit conversions for reference table
        all_conversions = {}
        for unit_key, factor in self.WEIGHT_UNITS.items():
            converted = float(N(Float(weight_in_kg, 15) / factor, 10))
            all_conversions[unit_key] = round(converted, 6)

        return JsonResponse({
            'success': True,
            'calc_type': 'convert',
            'weight': weight,
            'from_unit': from_unit,
            'from_unit_label': str(self.UNIT_LABELS.get(from_unit, from_unit)),
            'to_unit': to_unit,
            'to_unit_label': str(self.UNIT_LABELS.get(to_unit, to_unit)),
            'result': round(result, 6),
            'weight_in_kg': round(weight_in_kg, 6),
            'all_conversions': all_conversions,
            'step_by_step': steps,
            'chart_data': chart_data,
        })

    def _calculate_from_mass(self, data):
        """Calculate weight from mass and gravity using SymPy (W = m × g)"""
        try:
            mass = float(data.get('mass', 0))
            gravity = float(data.get('gravity', 9.80665))
            mass_unit = data.get('mass_unit', 'kg')
            weight_unit = data.get('weight_unit', 'N')
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input. Please enter numeric values.'))
            }, status=400)

        # Validate using NumPy
        inputs = np.array([mass, gravity])
        if np.any(inputs <= 0):
            return JsonResponse({
                'success': False,
                'error': str(_('Mass and gravity must be greater than zero.'))
            }, status=400)

        # Convert mass to kg using SymPy
        if mass_unit in self.WEIGHT_UNITS:
            mass_in_kg = float(N(Float(mass, 15) * self.WEIGHT_UNITS[mass_unit], 10))
        else:
            mass_in_kg = mass

        # SymPy symbolic calculation: W = m × g
        m, g = symbols('m g', real=True, positive=True)
        weight_formula = m * g
        weight_simplified = simplify(weight_formula)

        weight_newtons_symbolic = weight_simplified.subs({
            m: Float(mass_in_kg, 15),
            g: Float(gravity, 15)
        })
        weight_newtons = float(N(weight_newtons_symbolic, 10))

        # Convert to requested weight unit
        if weight_unit == 'N':
            weight_result = weight_newtons
        elif weight_unit == 'lb':
            weight_result = float(N(Float(weight_newtons, 15) * Float('0.224808943', 15), 10))
        elif weight_unit == 'kgf':
            weight_result = float(N(Float(weight_newtons, 15) * Float('0.101971621', 15), 10))
        else:
            weight_result = weight_newtons

        # NumPy verification
        weight_newtons_numpy = np.float64(mass_in_kg) * np.float64(gravity)

        steps = self._prepare_from_mass_steps(mass, mass_unit, mass_in_kg, gravity, weight_newtons, weight_unit, weight_result)

        return JsonResponse({
            'success': True,
            'calc_type': 'from_mass',
            'mass': mass,
            'mass_unit': mass_unit,
            'mass_unit_label': str(self.UNIT_LABELS.get(mass_unit, mass_unit)),
            'gravity': gravity,
            'mass_in_kg': round(mass_in_kg, 6),
            'weight_newtons': round(weight_newtons, 4),
            'weight_result': round(weight_result, 6),
            'weight_unit': weight_unit,
            'step_by_step': steps,
        })

    def _calculate_from_weight(self, data):
        """Calculate mass from weight and gravity using SymPy (m = W / g)"""
        try:
            weight = float(data.get('weight', 0))
            gravity = float(data.get('gravity', 9.80665))
            weight_unit = data.get('weight_unit', 'N')
            mass_unit = data.get('mass_unit', 'kg')
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input. Please enter numeric values.'))
            }, status=400)

        # Convert weight to Newtons using SymPy
        if weight_unit == 'N':
            weight_newtons = weight
        elif weight_unit == 'lb':
            weight_newtons = float(N(Float(weight, 15) * Float('4.4482216152605', 15), 10))
        elif weight_unit == 'kgf':
            weight_newtons = float(N(Float(weight, 15) * Float('9.80665', 15), 10))
        else:
            weight_newtons = weight

        # Validate using NumPy
        inputs = np.array([weight_newtons, gravity])
        if np.any(inputs <= 0):
            return JsonResponse({
                'success': False,
                'error': str(_('Weight and gravity must be greater than zero.'))
            }, status=400)

        # SymPy symbolic calculation: m = W / g
        W, g = symbols('W g', real=True, positive=True)
        mass_formula = W / g
        mass_simplified = simplify(mass_formula)

        mass_kg_symbolic = mass_simplified.subs({
            W: Float(weight_newtons, 15),
            g: Float(gravity, 15)
        })
        mass_kg = float(N(mass_kg_symbolic, 10))

        # Convert to requested mass unit
        if mass_unit in self.WEIGHT_UNITS:
            mass_result = float(N(Float(mass_kg, 15) / self.WEIGHT_UNITS[mass_unit], 10))
        else:
            mass_result = mass_kg

        steps = self._prepare_from_weight_steps(weight, weight_unit, weight_newtons, gravity, mass_kg, mass_unit, mass_result)

        return JsonResponse({
            'success': True,
            'calc_type': 'from_weight',
            'weight': weight,
            'weight_unit': weight_unit,
            'gravity': gravity,
            'weight_newtons': round(weight_newtons, 4),
            'mass_kg': round(mass_kg, 6),
            'mass_result': round(mass_result, 6),
            'mass_unit': mass_unit,
            'mass_unit_label': str(self.UNIT_LABELS.get(mass_unit, mass_unit)),
            'step_by_step': steps,
        })

    def _calculate_planet_weight(self, data):
        """Calculate weight on different planets using SymPy"""
        try:
            weight_earth = float(data.get('weight_earth', 0))
            weight_unit = data.get('weight_unit', 'kg')
            planet = data.get('planet', 'moon')
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid input. Please enter numeric values.'))
            }, status=400)

        # Validate
        weight_array = np.array([weight_earth])
        if np.any(weight_array <= 0):
            return JsonResponse({
                'success': False,
                'error': str(_('Weight must be greater than zero.'))
            }, status=400)

        if planet not in self.GRAVITY:
            return JsonResponse({
                'success': False,
                'error': str(_('Invalid planet selected.'))
            }, status=400)

        # SymPy symbolic calculation
        gravity_earth = self.GRAVITY['earth']
        gravity_planet = self.GRAVITY[planet]

        # Weight on planet = Weight on Earth × (gravity_planet / gravity_earth)
        w, ge, gp = symbols('w ge gp', real=True, positive=True)
        planet_formula = w * gp / ge
        planet_simplified = simplify(planet_formula)

        weight_planet_symbolic = planet_simplified.subs({
            w: Float(weight_earth, 15),
            ge: gravity_earth,
            gp: gravity_planet
        })
        weight_planet = float(N(weight_planet_symbolic, 10))

        # Gravity ratio
        gravity_ratio = float(N(gravity_planet / gravity_earth, 10))

        # Calculate all planets using NumPy for efficient batch processing
        planet_names = list(self.GRAVITY.keys())
        gravity_values = np.array([float(self.GRAVITY[p]) for p in planet_names])
        earth_gravity = float(gravity_earth)

        planet_weights_array = np.float64(weight_earth) * (gravity_values / earth_gravity)
        planet_weights = {}
        for i, p in enumerate(planet_names):
            planet_weights[p] = round(float(planet_weights_array[i]), 2)

        # Serialize planet labels to strings for JSON
        planet_labels_str = {k: str(v) for k, v in self.PLANET_LABELS.items()}

        steps = self._prepare_planet_steps(weight_earth, weight_unit, planet, gravity_earth, gravity_planet, weight_planet, gravity_ratio, planet_weights)
        chart_data = self._prepare_planet_chart_data(planet_weights, weight_unit)

        return JsonResponse({
            'success': True,
            'calc_type': 'planet',
            'weight_earth': weight_earth,
            'weight_unit': weight_unit,
            'weight_unit_label': str(self.UNIT_LABELS.get(weight_unit, weight_unit)),
            'planet': planet,
            'planet_label': str(self.PLANET_LABELS.get(planet, planet)),
            'weight_planet': round(weight_planet, 2),
            'gravity_ratio': round(gravity_ratio, 4),
            'gravity_earth': float(gravity_earth),
            'gravity_planet': float(gravity_planet),
            'planet_weights': planet_weights,
            'planet_labels': planet_labels_str,
            'step_by_step': steps,
            'chart_data': chart_data,
        })

    # ======== Step-by-Step Solution Methods ========

    def _prepare_convert_steps(self, weight, from_unit, to_unit, weight_in_kg, result):
        """Prepare step-by-step solution for weight conversion"""
        from_label = str(self.UNIT_LABELS.get(from_unit, from_unit))
        to_label = str(self.UNIT_LABELS.get(to_unit, to_unit))
        from_factor = float(self.WEIGHT_UNITS[from_unit])
        to_factor = float(self.WEIGHT_UNITS[to_unit])

        steps = [
            str(_('Step 1: Identify the given values')),
            str(_('Weight')) + f' = {weight} {from_unit} ({from_label})',
            str(_('Convert to')) + f': {to_unit} ({to_label})',
            '',
            str(_('Step 2: Convert to base unit (kilograms)')),
            str(_('Conversion factor')) + f': 1 {from_unit} = {from_factor} kg',
            str(_('Weight in kg')) + f' = {weight} × {from_factor} = {round(weight_in_kg, 6)} kg',
            '',
            str(_('Step 3: Convert from kilograms to target unit')),
            str(_('Conversion factor')) + f': 1 {to_unit} = {to_factor} kg',
            str(_('Result')) + f' = {round(weight_in_kg, 6)} ÷ {to_factor} = {round(result, 6)} {to_unit}',
            '',
            str(_('Final Answer')) + f': {weight} {from_unit} = {round(result, 6)} {to_unit}',
        ]
        return steps

    def _prepare_from_mass_steps(self, mass, mass_unit, mass_in_kg, gravity, weight_newtons, weight_unit, weight_result):
        """Prepare step-by-step solution for weight from mass"""
        steps = [
            str(_('Step 1: Identify the given values')),
            str(_('Mass')) + f' = {mass} {mass_unit}',
            str(_('Gravitational acceleration (g)')) + f' = {gravity} m/s²',
            '',
            str(_('Step 2: Convert mass to kilograms')),
        ]
        if mass_unit != 'kg':
            factor = float(self.WEIGHT_UNITS.get(mass_unit, 1))
            steps.append(str(_('Mass in kg')) + f' = {mass} × {factor} = {round(mass_in_kg, 6)} kg')
        else:
            steps.append(str(_('Mass is already in kg')) + f' = {round(mass_in_kg, 6)} kg')

        steps.extend([
            '',
            str(_('Step 3: Apply the weight formula (W = m × g)')),
            str(_('Weight')) + ' = ' + str(_('Mass')) + ' × ' + str(_('Gravity')),
            str(_('Weight')) + f' = {round(mass_in_kg, 6)} kg × {gravity} m/s²',
            str(_('Weight')) + f' = {round(weight_newtons, 4)} N (' + str(_('Newtons')) + ')',
        ])

        if weight_unit != 'N':
            steps.extend([
                '',
                str(_('Step 4: Convert to requested unit')) + f' ({weight_unit})',
                str(_('Weight')) + f' = {round(weight_result, 6)} {weight_unit}',
            ])

        steps.extend([
            '',
            str(_('Final Answer')) + ': ' + str(_('Weight')) + f' = {round(weight_result, 6)} {weight_unit}',
        ])
        return steps

    def _prepare_from_weight_steps(self, weight, weight_unit, weight_newtons, gravity, mass_kg, mass_unit, mass_result):
        """Prepare step-by-step solution for mass from weight"""
        steps = [
            str(_('Step 1: Identify the given values')),
            str(_('Weight')) + f' = {weight} {weight_unit}',
            str(_('Gravitational acceleration (g)')) + f' = {gravity} m/s²',
            '',
            str(_('Step 2: Convert weight to Newtons')),
        ]
        if weight_unit != 'N':
            steps.append(str(_('Weight in Newtons')) + f' = {round(weight_newtons, 4)} N')
        else:
            steps.append(str(_('Weight is already in Newtons')) + f' = {round(weight_newtons, 4)} N')

        steps.extend([
            '',
            str(_('Step 3: Apply the mass formula (m = W / g)')),
            str(_('Mass')) + ' = ' + str(_('Weight')) + ' ÷ ' + str(_('Gravity')),
            str(_('Mass')) + f' = {round(weight_newtons, 4)} N ÷ {gravity} m/s²',
            str(_('Mass')) + f' = {round(mass_kg, 6)} kg',
        ])

        if mass_unit != 'kg':
            factor = float(self.WEIGHT_UNITS.get(mass_unit, 1))
            steps.extend([
                '',
                str(_('Step 4: Convert to requested unit')) + f' ({mass_unit})',
                str(_('Mass')) + f' = {round(mass_kg, 6)} kg ÷ {factor}',
                str(_('Mass')) + f' = {round(mass_result, 6)} {mass_unit}',
            ])

        steps.extend([
            '',
            str(_('Final Answer')) + ': ' + str(_('Mass')) + f' = {round(mass_result, 6)} {mass_unit}',
        ])
        return steps

    def _prepare_planet_steps(self, weight_earth, weight_unit, planet, gravity_earth, gravity_planet, weight_planet, gravity_ratio, planet_weights):
        """Prepare step-by-step solution for planet weight"""
        planet_label = str(self.PLANET_LABELS.get(planet, planet))
        ge = float(gravity_earth)
        gp = float(gravity_planet)

        steps = [
            str(_('Step 1: Identify the given values')),
            str(_('Weight on Earth')) + f' = {weight_earth} {weight_unit}',
            str(_('Target planet')) + f' = {planet_label}',
            '',
            str(_('Step 2: Identify gravitational accelerations')),
            str(_('Gravity on Earth (gₑ)')) + f' = {ge} m/s²',
            str(_('Gravity on')) + f' {planet_label} (gₚ) = {gp} m/s²',
            '',
            str(_('Step 3: Calculate gravity ratio')),
            str(_('Gravity ratio')) + f' = gₚ / gₑ = {gp} / {ge} = {round(gravity_ratio, 4)}',
            '',
            str(_('Step 4: Calculate weight on')) + f' {planet_label}',
            str(_('Weight on')) + f' {planet_label} = ' + str(_('Weight on Earth')) + ' × ' + str(_('Gravity ratio')),
            str(_('Weight on')) + f' {planet_label} = {weight_earth} × {round(gravity_ratio, 4)}',
            str(_('Weight on')) + f' {planet_label} = {round(weight_planet, 2)} {weight_unit}',
            '',
            str(_('Step 5: Comparison across all celestial bodies')),
        ]

        # Sort by weight descending for comparison
        sorted_planets = sorted(planet_weights.items(), key=lambda x: x[1], reverse=True)
        for p, w in sorted_planets:
            label = str(self.PLANET_LABELS.get(p, p))
            marker = ' ← ' + str(_('You selected')) if p == planet else (' ← ' + str(_('Earth')) if p == 'earth' else '')
            steps.append(f'{label}: {w} {weight_unit}{marker}')

        return steps

    # ======== Chart Data Methods ========

    def _prepare_convert_chart_data(self, weight, result, from_unit, to_unit):
        """Prepare chart data for weight conversion visualization"""
        from_label = str(self.UNIT_LABELS.get(from_unit, from_unit))
        to_label = str(self.UNIT_LABELS.get(to_unit, to_unit))

        gauge_chart = {
            'type': 'bar',
            'data': {
                'labels': [f'{from_label} ({from_unit})', f'{to_label} ({to_unit})'],
                'datasets': [{
                    'label': str(_('Weight Value')),
                    'data': [round(weight, 4), round(result, 4)],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    'borderColor': ['#3b82f6', '#10b981'],
                    'borderWidth': 2,
                    'borderRadius': 8,
                }]
            },
        }

        return {
            'convert_chart': gauge_chart,
        }

    def _prepare_planet_chart_data(self, planet_weights, weight_unit):
        """Prepare chart data for planet weight comparison"""
        labels = []
        data = []
        bg_colors = []
        border_colors = []

        # Sort by gravity (weight) ascending for a nice visual
        sorted_planets = sorted(planet_weights.items(), key=lambda x: x[1])

        for p, w in sorted_planets:
            labels.append(str(self.PLANET_LABELS.get(p, p)))
            data.append(w)
            color = self.PLANET_COLORS.get(p, '#3b82f6')
            bg_colors.append(color + 'cc')  # with alpha
            border_colors.append(color)

        planet_chart = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Weight')) + f' ({weight_unit})',
                    'data': data,
                    'backgroundColor': bg_colors,
                    'borderColor': border_colors,
                    'borderWidth': 2,
                    'borderRadius': 8,
                }]
            },
        }

        return {
            'planet_chart': planet_chart,
        }
