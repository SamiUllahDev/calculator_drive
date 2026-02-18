from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np
from sympy import symbols, simplify, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class InflationCalculator(View):
    """
    Class-based view for Inflation Calculator with full functionality.

    Uses NumPy for efficient numerical operations and array-based calculations.
    Uses SymPy for precise mathematical computations and formula representation.
    Mirrors the BMI Calculator architecture for consistency.
    """
    template_name = 'financial_calculators/inflation_calculator.html'

    # Precision constants using SymPy Float
    HUNDRED = Float('100')
    ONE = Float('1')

    # Inflation severity thresholds (annual %)
    DEFLATION_THRESHOLD = Float('0')
    LOW_INFLATION = Float('2')
    MODERATE_INFLATION = Float('4')
    HIGH_INFLATION = Float('7')
    VERY_HIGH_INFLATION = Float('10')

    IDEAL_INFLATION = 2.0  # Central bank target

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Inflation Calculator',
            'page_title': 'Inflation Calculator - Calculate Purchasing Power Over Time',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations using NumPy and SymPy"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

            # Get input values
            calc_type = data.get('calc_type', 'future')
            amount = float(data.get('amount', 0))
            inflation_rate = float(data.get('inflation_rate', 0))
            years = int(data.get('years', 0))

            # Validate inputs using NumPy
            amount_array = np.array([amount])
            rate_array = np.array([inflation_rate])
            years_array = np.array([years])

            if np.any(amount_array <= 0):
                return JsonResponse({
                    'error': 'Amount must be greater than zero.',
                    'success': False
                }, status=400)

            if amount > 1000000000:
                return JsonResponse({
                    'error': 'Amount must be less than $1,000,000,000.',
                    'success': False
                }, status=400)

            # Validate inflation rate
            if inflation_rate < -20 or inflation_rate > 50:
                return JsonResponse({
                    'error': 'Inflation rate must be between -20% and 50%.',
                    'success': False
                }, status=400)

            # Validate years
            if years <= 0 or years > 100:
                return JsonResponse({
                    'error': 'Time period must be between 1 and 100 years.',
                    'success': False
                }, status=400)

            # Validate calc_type
            if calc_type not in ['future', 'past']:
                return JsonResponse({
                    'error': 'Calculation type must be "future" or "past".',
                    'success': False
                }, status=400)

            # Calculate using SymPy for precise symbolic calculation
            # Inflation formula: FV = PV × (1 + r)^n
            pv, r, n = symbols('pv r n', real=True)
            inflation_formula = pv * ((self.ONE + r) ** n)
            inflation_formula_simplified = simplify(inflation_formula)

            # Convert rate to decimal using SymPy for precision
            rate_decimal = Float(inflation_rate, 15) / self.HUNDRED

            if calc_type == 'future':
                # Future Cost: How much will it cost in the future?
                future_value_symbolic = inflation_formula_simplified.subs({
                    pv: Float(amount, 15),
                    r: rate_decimal,
                    n: Float(years, 15)
                })
                future_value = float(N(future_value_symbolic, 10))
                real_value = amount
                purchasing_power_lost = future_value - amount
            else:
                # Past Value: What is the real value of past money today?
                future_value = amount
                # Real value = Amount / (1 + r)^n
                deflation_formula = pv / ((self.ONE + r) ** n)
                real_value_symbolic = deflation_formula.subs({
                    pv: Float(amount, 15),
                    r: rate_decimal,
                    n: Float(years, 15)
                })
                real_value = float(N(real_value_symbolic, 10))
                purchasing_power_lost = amount - real_value

            # Verify calculation using NumPy (cross-check)
            if calc_type == 'future':
                fv_numpy = amount * np.power(1 + float(rate_decimal), years)
                if abs(future_value - fv_numpy) > 1e-5:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Inflation calculation discrepancy: SymPy={future_value}, NumPy={fv_numpy}")
            else:
                rv_numpy = amount / np.power(1 + float(rate_decimal), years)
                if abs(real_value - rv_numpy) > 1e-5:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Inflation calculation discrepancy: SymPy={real_value}, NumPy={rv_numpy}")

            # Calculate cumulative inflation using SymPy
            cumulative_formula = ((self.ONE + r) ** n - self.ONE) * self.HUNDRED
            cumulative_symbolic = cumulative_formula.subs({
                r: rate_decimal,
                n: Float(years, 15)
            })
            cumulative_inflation = float(N(cumulative_symbolic, 10))

            # Calculate purchasing power ratio (how much $1 is worth after inflation)
            purchasing_power_ratio = float(N(self.ONE / ((self.ONE + rate_decimal) ** Float(years, 15)), 10))

            # Determine inflation severity category
            category, category_color, description, detailed_category = self.get_inflation_category(
                inflation_rate, cumulative_inflation, years
            )

            # Calculate scale position
            scale_position = self.calculate_inflation_scale_position(inflation_rate)

            # Calculate yearly breakdown using NumPy for efficiency
            yearly_data = self._calculate_yearly_data(amount, float(rate_decimal), years, calc_type)

            # Calculate rate comparison
            comparison = self._calculate_rate_comparison(amount, years)

            # Calculate additional statistics using NumPy
            inflation_array = np.array([inflation_rate])
            ideal_array = np.array([self.IDEAL_INFLATION])
            rate_deviation = float(np.abs(inflation_array - ideal_array)[0])
            rate_percentage_from_ideal = float((rate_deviation / self.IDEAL_INFLATION) * 100) if self.IDEAL_INFLATION != 0 else 0

            # Calculate color info (backend-controlled)
            color_info = self.get_color_info(category_color)

            # Prepare chart data (backend-controlled)
            chart_data = self.prepare_chart_data(
                cumulative_inflation=cumulative_inflation,
                category_color=category_color,
                category=category,
                yearly_data=yearly_data,
                comparison=comparison,
                calc_type=calc_type,
                amount=amount,
                future_value=future_value,
                real_value=real_value,
                purchasing_power_ratio=purchasing_power_ratio
            )

            return JsonResponse({
                'success': True,
                'summary': {
                    'original_amount': round(amount, 2),
                    'inflation_rate': round(inflation_rate, 2),
                    'years': years,
                    'calc_type': calc_type,
                    'future_value': round(future_value, 2),
                    'real_value': round(real_value, 2),
                    'purchasing_power_change': round(purchasing_power_lost, 2),
                    'cumulative_inflation': round(cumulative_inflation, 2),
                    'purchasing_power_ratio': round(purchasing_power_ratio, 4),
                },
                'category': category,
                'detailed_category': detailed_category,
                'category_color': category_color,
                'description': description,
                'statistics': {
                    'ideal_inflation': self.IDEAL_INFLATION,
                    'deviation_from_ideal': round(rate_deviation, 2),
                    'percentage_from_ideal': round(rate_percentage_from_ideal, 1)
                },
                'scale_position': scale_position,
                'yearly_data': yearly_data[:50],
                'comparison': comparison,
                'chart_data': chart_data,
                'color_info': color_info
            })

        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid input: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An error occurred during calculation.'
            }, status=500)

    def get_inflation_category(self, inflation_rate, cumulative_inflation, years):
        """Determine inflation severity category using NumPy for efficient comparison.
        Based on economic standards."""
        rate_value = np.array([inflation_rate])

        # Thresholds for annual inflation rate
        thresholds = np.array([-20, 0, 2, 4, 7, 10])
        category_index = np.searchsorted(thresholds, rate_value)[0]

        detailed_categories = [
            ('Severe Deflation', '< -20%'),
            ('Deflation', '< 0%'),
            ('Low Inflation', '0% - 2%'),
            ('Target Inflation', '2% - 4%'),
            ('High Inflation', '4% - 7%'),
            ('Very High Inflation', '7% - 10%'),
            ('Hyperinflation', '> 10%')
        ]

        simple_categories = [
            ('Deflation', 'blue', 'Prices are falling. This can indicate economic weakness and may discourage spending.'),
            ('Deflation', 'blue', 'Prices are falling. This can indicate economic weakness and may discourage spending.'),
            ('Low', 'green', 'Inflation is within a healthy range. Your purchasing power is relatively well preserved.'),
            ('Moderate', 'green', 'Inflation is near central bank targets. This is considered healthy for economic growth.'),
            ('High', 'yellow', 'Inflation is above target. Your purchasing power is eroding faster than usual.'),
            ('Very High', 'orange', 'Inflation is significantly elevated. Consider inflation-protected investments.'),
            ('Extreme', 'red', 'Inflation is extremely high. Purchasing power is rapidly declining. Seek professional advice.')
        ]

        detailed_category = detailed_categories[category_index]
        simple_category = simple_categories[category_index]

        return simple_category[0], simple_category[1], simple_category[2], detailed_category

    def calculate_inflation_scale_position(self, inflation_rate):
        """Calculate inflation indicator position on scale (0-100%) using NumPy.
        Scale: deflation (0-15%), low (15-35%), moderate (35-55%), high (55-75%), very high (75-90%), extreme (90-100%)"""

        if inflation_rate < 0:
            # Deflation: 0% to 15%
            position = max(0, (inflation_rate + 20) / 20 * 15)
        elif inflation_rate <= 2:
            # Low: 15% to 35%
            position = 15 + (inflation_rate / 2) * 20
        elif inflation_rate <= 4:
            # Moderate: 35% to 55%
            position = 35 + ((inflation_rate - 2) / 2) * 20
        elif inflation_rate <= 7:
            # High: 55% to 75%
            position = 55 + ((inflation_rate - 4) / 3) * 20
        elif inflation_rate <= 10:
            # Very High: 75% to 90%
            position = 75 + ((inflation_rate - 7) / 3) * 15
        else:
            # Extreme: 90% to 100%
            max_display = 20
            if inflation_rate > max_display:
                position = 100.0
            else:
                position = 90 + ((inflation_rate - 10) / 10) * 10

        return min(100.0, max(0.0, float(position)))

    def get_color_info(self, category_color):
        """Get color information for the category (backend-controlled)"""
        color_map = {
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300'
            },
            'green': {
                'hex': '#10b981',
                'rgb': 'rgb(16, 185, 129)',
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300'
            },
            'yellow': {
                'hex': '#f59e0b',
                'rgb': 'rgb(245, 158, 11)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300'
            },
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300'
            },
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300'
            }
        }
        return color_map.get(category_color, color_map['green'])

    def _calculate_yearly_data(self, amount, rate_decimal, years, calc_type):
        """Calculate yearly data using NumPy for efficient array operations"""
        year_range = np.arange(1, years + 1)
        inflation_factors = np.power(1 + rate_decimal, year_range)

        if calc_type == 'future':
            values = amount * inflation_factors
            purchasing_powers = amount / inflation_factors
        else:
            values = np.full_like(inflation_factors, amount)
            purchasing_powers = amount / inflation_factors

        yearly_data = []
        for i, year in enumerate(year_range):
            yearly_data.append({
                'year': int(year),
                'value': round(float(values[i]), 2),
                'purchasing_power': round(float(purchasing_powers[i]), 2),
                'inflation_factor': round(float(inflation_factors[i]), 4)
            })

        return yearly_data

    def _calculate_rate_comparison(self, amount, years):
        """Calculate comparison at different rates using NumPy"""
        rates = np.array([1, 2, 3, 4, 5, 7, 10])
        rate_decimals = rates / 100.0
        inflation_factors = np.power(1 + rate_decimals, years)
        future_values = amount * inflation_factors
        purchasing_powers = amount / inflation_factors

        comparison = []
        for i, rate in enumerate(rates):
            comparison.append({
                'rate': int(rate),
                'future_value': round(float(future_values[i]), 2),
                'purchasing_power': round(float(purchasing_powers[i]), 2)
            })

        return comparison

    def prepare_chart_data(self, cumulative_inflation, category_color, category,
                           yearly_data, comparison, calc_type, amount,
                           future_value, real_value, purchasing_power_ratio):
        """Prepare all chart data in backend (backend-controlled)"""
        color_info = self.get_color_info(category_color)

        # 1. Gauge Chart Data (doughnut) — shows purchasing power retained
        power_retained = purchasing_power_ratio * 100
        power_lost = 100 - power_retained
        if power_lost < 0:
            power_lost = 0
            power_retained = 100

        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': ['Power Retained', 'Power Lost'],
                'datasets': [{
                    'data': [round(max(power_retained, 0), 2), round(max(power_lost, 0), 2)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': round(power_retained, 1),
                'label': 'Power Left',
                'suffix': '%',
                'color': color_info['hex']
            }
        }

        # 2. Value Over Time Chart (line) — nominal vs real value
        labels = [f"Year {d['year']}" for d in yearly_data[:30]]
        values = [float(d['value']) for d in yearly_data[:30]]
        powers = [float(d['purchasing_power']) for d in yearly_data[:30]]

        value_chart = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Nominal Value',
                        'data': values,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                        'fill': True,
                        'tension': 0.3,
                        'borderWidth': 2,
                        'pointRadius': 3,
                        'pointHoverRadius': 6
                    },
                    {
                        'label': 'Real Value (Purchasing Power)',
                        'data': powers,
                        'borderColor': '#ef4444',
                        'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                        'fill': True,
                        'tension': 0.3,
                        'borderWidth': 2,
                        'pointRadius': 3,
                        'pointHoverRadius': 6
                    }
                ]
            }
        }

        # 3. Rate Comparison Chart (bar) — future cost at different rates
        rate_labels = [f"{r['rate']}%" for r in comparison]
        fv_values = [float(r['future_value']) for r in comparison]

        # Determine colors based on category thresholds
        rate_colors = []
        for r in comparison:
            if r['rate'] <= 2:
                rate_colors.append('#10b981')  # green
            elif r['rate'] <= 4:
                rate_colors.append('#f59e0b')  # yellow
            elif r['rate'] <= 7:
                rate_colors.append('#f97316')  # orange
            else:
                rate_colors.append('#ef4444')  # red

        comparison_chart = {
            'type': 'bar',
            'data': {
                'labels': rate_labels,
                'datasets': [{
                    'label': 'Future Cost',
                    'data': fv_values,
                    'backgroundColor': rate_colors,
                    'borderColor': rate_colors,
                    'borderWidth': 2,
                    'borderRadius': 8
                }]
            }
        }

        # 4. Purchasing Power Erosion Chart (bar) — original vs retained
        erosion_chart = {
            'type': 'bar',
            'data': {
                'labels': ['Original Amount', 'Real Value After Inflation'],
                'datasets': [
                    {
                        'label': 'Amount',
                        'data': [round(amount, 2), round(real_value, 2)],
                        'backgroundColor': ['#10b981', color_info['hex']],
                        'borderColor': ['#10b981', color_info['hex']],
                        'borderWidth': 2,
                        'borderRadius': 8,
                        'barThickness': 60
                    }
                ]
            },
            'difference': {
                'amount': round(abs(amount - real_value), 2),
                'percentage': round(abs(cumulative_inflation), 1)
            }
        }

        return {
            'gauge_chart': gauge_chart,
            'value_chart': value_chart,
            'comparison_chart': comparison_chart,
            'erosion_chart': erosion_chart
        }
