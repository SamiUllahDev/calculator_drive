from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class FemaleDelusionCalculator(View):
    """
    Female Delusion Calculator — Dating Reality Check.

    Calculates the statistical probability of finding a male partner
    who meets all of the user's selected criteria simultaneously,
    based on US Census / demographic survey data (approximate).

    Factors:
    - Age range
    - Minimum height
    - Minimum income
    - Not married
    - Not obese
    - Race preference

    Uses NumPy for probability multiplication and chart data.
    """
    template_name = 'other_calculators/female_delusion_calculator.html'

    # ─── STATISTICAL DATA (US male population, approx.) ──────────
    # Sources: US Census, BLS, CDC, Pew Research — simplified / averaged.

    # % of US males in each age bracket
    AGE_DISTRIBUTION = {
        '18-25': 0.133,
        '26-30': 0.098,
        '31-35': 0.098,
        '36-40': 0.093,
        '41-45': 0.087,
        '46-50': 0.083,
        '51-55': 0.085,
        '56-65': 0.148,
    }

    # % of US males AT or ABOVE a given height
    # Based on CDC NHANES anthropometric data
    HEIGHT_CUMULATIVE = {
        '5\'0" (152 cm)':  0.99,
        '5\'3" (160 cm)':  0.95,
        '5\'5" (165 cm)':  0.88,
        '5\'7" (170 cm)':  0.75,
        '5\'8" (173 cm)':  0.66,
        '5\'9" (175 cm)':  0.57,
        '5\'10" (178 cm)': 0.47,
        '5\'11" (180 cm)': 0.37,
        '6\'0" (183 cm)':  0.27,
        '6\'1" (185 cm)':  0.18,
        '6\'2" (188 cm)':  0.11,
        '6\'3" (191 cm)':  0.06,
        '6\'4" (193 cm)':  0.03,
        '6\'5"+ (196 cm+)': 0.01,
    }

    # % of US males earning AT or ABOVE a given annual income
    # Based on BLS / Census Current Population Survey
    INCOME_CUMULATIVE = {
        '$0 (Any)':         1.00,
        '$25,000':          0.72,
        '$30,000':          0.65,
        '$40,000':          0.53,
        '$50,000':          0.42,
        '$60,000':          0.34,
        '$75,000':          0.24,
        '$100,000':         0.15,
        '$125,000':         0.09,
        '$150,000':         0.06,
        '$200,000':         0.035,
        '$250,000':         0.022,
        '$300,000':         0.015,
        '$500,000+':        0.005,
    }

    # % of US males who are NOT married (single, divorced, widowed)
    NOT_MARRIED_RATE = 0.51   # ~51 % of adult US males are unmarried

    # % of US males who are NOT obese (BMI < 30)
    NOT_OBESE_RATE = 0.575    # ~42.5 % obesity rate → 57.5 % not obese

    # Race distribution of US male population (Census 2020 approx.)
    RACE_DISTRIBUTION = {
        'any':      1.00,
        'white':    0.576,
        'black':    0.122,
        'hispanic': 0.185,
        'asian':    0.058,
        'other':    0.059,
    }

    def get(self, request):
        context = {
            'calculator_name': _('Female Delusion Calculator'),
            'page_title': _('Female Delusion Calculator - Dating Reality Check'),
            'age_ranges': list(self.AGE_DISTRIBUTION.keys()),
            'heights': list(self.HEIGHT_CUMULATIVE.keys()),
            'incomes': list(self.INCOME_CUMULATIVE.keys()),
            'races': [
                {'key': 'any',      'label': str(_('Any Race'))},
                {'key': 'white',    'label': str(_('White'))},
                {'key': 'black',    'label': str(_('Black'))},
                {'key': 'hispanic', 'label': str(_('Hispanic / Latino'))},
                {'key': 'asian',    'label': str(_('Asian'))},
                {'key': 'other',    'label': str(_('Other'))},
            ],
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)

            age_range   = data.get('age_range', '26-30')
            min_height  = data.get('min_height', '5\'9" (175 cm)')
            min_income  = data.get('min_income', '$50,000')
            not_married = data.get('not_married', True)
            not_obese   = data.get('not_obese', False)
            race        = data.get('race', 'any')

            # ── Look up probabilities ────────────────────────────
            p_age    = self.AGE_DISTRIBUTION.get(age_range, 0.10)
            p_height = self.HEIGHT_CUMULATIVE.get(min_height, 0.50)
            p_income = self.INCOME_CUMULATIVE.get(min_income, 0.50)
            p_marry  = self.NOT_MARRIED_RATE if not_married else 1.0
            p_obese  = self.NOT_OBESE_RATE if not_obese else 1.0
            p_race   = self.RACE_DISTRIBUTION.get(race, 1.0)

            # ── Multiply with NumPy (assumes independence) ───────
            factors = np.array([p_age, p_height, p_income, p_marry, p_obese, p_race], dtype=np.float64)
            probability = float(np.prod(factors)) * 100   # percentage
            probability = float(np.clip(probability, 0, 100))

            # ── Factor labels for breakdown ──────────────────────
            factor_names = [
                str(_('Age Range')),
                str(_('Minimum Height')),
                str(_('Minimum Income')),
                str(_('Not Married')),
                str(_('Not Obese')),
                str(_('Race Preference')),
            ]
            factor_pcts = (factors * 100).tolist()

            # ── Category / verdict ───────────────────────────────
            category = self._get_category(probability)

            # ── Estimated pool (US male pop ~165 million) ────────
            us_male_pop = 165_000_000
            estimated_pool = int(us_male_pop * probability / 100)

            # ── Chart data ───────────────────────────────────────
            chart_data = self._prepare_chart_data(
                probability, factor_names, factor_pcts, factors, category
            )

            # ── Breakdown rows ───────────────────────────────────
            breakdown = []
            criteria_labels = [age_range, min_height, min_income,
                               str(_('Yes')) if not_married else str(_('No')),
                               str(_('Yes')) if not_obese else str(_('No')),
                               dict(self._race_labels()).get(race, race)]
            for i, name in enumerate(factor_names):
                breakdown.append({
                    'factor': name,
                    'criteria': criteria_labels[i],
                    'pool_pct': round(factor_pcts[i], 1),
                })

            return JsonResponse({
                'success': True,
                'probability': round(probability, 4),
                'probability_display': self._format_probability(probability),
                'category': category,
                'estimated_pool': f'{estimated_pool:,}',
                'breakdown': breakdown,
                'chart_data': chart_data,
                'color_info': self._get_color_info(category['color']),
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    def _race_labels(self):
        return [('any', str(_('Any Race'))), ('white', str(_('White'))),
                ('black', str(_('Black'))), ('hispanic', str(_('Hispanic / Latino'))),
                ('asian', str(_('Asian'))), ('other', str(_('Other')))]

    def _format_probability(self, p):
        if p >= 10:
            return f'{p:.1f}%'
        elif p >= 1:
            return f'{p:.2f}%'
        elif p >= 0.1:
            return f'{p:.3f}%'
        else:
            return f'{p:.4f}%'

    def _get_category(self, p):
        if p >= 20:
            return {'name': str(_('Very Realistic')), 'color': 'green', 'emoji': '✅',
                    'description': str(_('Your standards are very reasonable! You have a large pool of potential matches.'))}
        elif p >= 10:
            return {'name': str(_('Realistic')), 'color': 'blue', 'emoji': '👍',
                    'description': str(_('Your expectations are grounded in reality. Good chances of finding someone.'))}
        elif p >= 3:
            return {'name': str(_('Moderate')), 'color': 'yellow', 'emoji': '🤔',
                    'description': str(_('Your criteria are somewhat selective. You may need patience but it is not impossible.'))}
        elif p >= 0.5:
            return {'name': str(_('Picky')), 'color': 'orange', 'emoji': '😬',
                    'description': str(_('Your standards are quite high. Statistically, fewer than 1 in 100 men meet all your criteria.'))}
        elif p >= 0.05:
            return {'name': str(_('Very Picky')), 'color': 'red', 'emoji': '🦄',
                    'description': str(_('You are looking for a unicorn. Fewer than 1 in 1,000 men meet all these criteria.'))}
        else:
            return {'name': str(_('Delusional')), 'color': 'purple', 'emoji': '🌈',
                    'description': str(_('Statistically, the man you are looking for barely exists. Consider relaxing a criterion or two!'))}

    def _get_color_info(self, color):
        cmap = {
            'green':  {'hex': '#10b981', 'tailwind': 'bg-green-100 text-green-800 border-green-300'},
            'blue':   {'hex': '#3b82f6', 'tailwind': 'bg-blue-100 text-blue-800 border-blue-300'},
            'yellow': {'hex': '#f59e0b', 'tailwind': 'bg-yellow-100 text-yellow-800 border-yellow-300'},
            'orange': {'hex': '#f97316', 'tailwind': 'bg-orange-100 text-orange-800 border-orange-300'},
            'red':    {'hex': '#ef4444', 'tailwind': 'bg-red-100 text-red-800 border-red-300'},
            'purple': {'hex': '#8b5cf6', 'tailwind': 'bg-purple-100 text-purple-800 border-purple-300'},
        }
        return cmap.get(color, cmap['blue'])

    def _prepare_chart_data(self, probability, factor_names, factor_pcts, factors, category):
        ci = self._get_color_info(category['color'])

        # 1. Gauge (doughnut)
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Match Probability')), str(_('Remaining'))],
                'datasets': [{
                    'data': [round(probability, 2), round(100 - probability, 2)],
                    'backgroundColor': [ci['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': self._format_probability(probability),
                'label': str(_('Chance')),
                'color': ci['hex'],
            }
        }

        # 2. Factor bar chart (horizontal)
        bar_colors = []
        for p in factor_pcts:
            if p >= 70:
                bar_colors.append('#10b981')
            elif p >= 40:
                bar_colors.append('#3b82f6')
            elif p >= 20:
                bar_colors.append('#f59e0b')
            elif p >= 5:
                bar_colors.append('#f97316')
            else:
                bar_colors.append('#ef4444')

        factor_chart = {
            'type': 'bar',
            'data': {
                'labels': factor_names,
                'datasets': [{
                    'label': str(_('% of Men Who Qualify')),
                    'data': [round(p, 1) for p in factor_pcts],
                    'backgroundColor': bar_colors,
                    'borderRadius': 6,
                }]
            }
        }

        # 3. Funnel-style waterfall (shows progressive narrowing)
        cumulative = []
        running = 100.0
        for f in factors:
            running *= f
            cumulative.append(round(running, 4))

        funnel_chart = {
            'type': 'line',
            'data': {
                'labels': factor_names,
                'datasets': [{
                    'label': str(_('Remaining Pool %')),
                    'data': cumulative,
                    'borderColor': ci['hex'],
                    'backgroundColor': ci['hex'] + '33',
                    'borderWidth': 3,
                    'fill': True,
                    'tension': 0.3,
                    'pointBackgroundColor': ci['hex'],
                    'pointBorderColor': '#fff',
                    'pointBorderWidth': 2,
                    'pointRadius': 6,
                }]
            }
        }

        return {
            'gauge_chart': gauge_chart,
            'factor_chart': factor_chart,
            'funnel_chart': funnel_chart,
        }
