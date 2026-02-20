from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SnowDayCalculator(View):
    """
    Professional Snow Day Calculator with comprehensive features.

    Predicts the likelihood of a snow day (school closure) based on
    multiple weather and environmental factors using a weighted scoring model.

    Features:
    - 8 input factors with weighted scoring
    - NumPy-based probability calculation
    - Category-based color coding
    - Backend-controlled Chart.js configurations
    - Step-by-step breakdown
    - Scale visualization
    - Detailed tips and recommendations
    """
    template_name = 'other_calculators/snow_day_calculator.html'

    # ─── Scoring weights (must sum to 1.0) ──────────────────────────
    WEIGHTS = {
        'snowfall':      0.25,   # Most important factor
        'temperature':   0.15,
        'wind_speed':    0.10,
        'ice':           0.15,   # Ice is very dangerous
        'timing':        0.10,
        'road_condition': 0.10,
        'school_history': 0.10,
        'location':      0.05,
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Snow Day Calculator'),
            'page_title': _('Snow Day Calculator - Predict School Snow Days'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations using NumPy"""
        try:
            data = json.loads(request.body)

            # ── Parse & validate inputs ──────────────────────────
            snowfall = self._get_float(data, 'snowfall', 0)            # inches expected
            temperature = self._get_float(data, 'temperature', 32)     # °F
            wind_speed = self._get_float(data, 'wind_speed', 0)        # mph
            ice_accumulation = self._get_float(data, 'ice_accumulation', 0)  # inches
            timing = data.get('timing', 'during')                       # before/during/after
            road_condition = data.get('road_condition', 'wet')          # dry/wet/snowy/icy
            school_history = data.get('school_history', 'average')      # rarely/average/often
            location = data.get('location', 'suburban')                 # urban/suburban/rural
            temp_unit = data.get('temp_unit', 'F')                      # F or C

            # Convert Celsius to Fahrenheit for internal calculation
            if temp_unit == 'C':
                temperature_f = temperature * 9.0 / 5.0 + 32.0
            else:
                temperature_f = temperature

            # ── Validation ───────────────────────────────────────
            errors = []
            if snowfall < 0 or snowfall > 60:
                errors.append(_('Snowfall must be between 0 and 60 inches.'))
            if temperature_f < -60 or temperature_f > 60:
                errors.append(_('Temperature must be between -60°F and 60°F (-51°C to 15°C).'))
            if wind_speed < 0 or wind_speed > 120:
                errors.append(_('Wind speed must be between 0 and 120 mph.'))
            if ice_accumulation < 0 or ice_accumulation > 5:
                errors.append(_('Ice accumulation must be between 0 and 5 inches.'))
            if timing not in ('before', 'during', 'after'):
                errors.append(_('Invalid timing selection.'))
            if road_condition not in ('dry', 'wet', 'snowy', 'icy'):
                errors.append(_('Invalid road condition.'))
            if school_history not in ('rarely', 'average', 'often'):
                errors.append(_('Invalid school history selection.'))
            if location not in ('urban', 'suburban', 'rural'):
                errors.append(_('Invalid location type.'))

            if errors:
                return JsonResponse({'success': False, 'error': str(errors[0])}, status=400)

            # ── Individual factor scores (0-100) via NumPy ───────
            scores = self._calculate_factor_scores(
                snowfall, temperature_f, wind_speed, ice_accumulation,
                timing, road_condition, school_history, location
            )

            # ── Weighted total probability ───────────────────────
            weights_arr = np.array([
                self.WEIGHTS['snowfall'],
                self.WEIGHTS['temperature'],
                self.WEIGHTS['wind_speed'],
                self.WEIGHTS['ice'],
                self.WEIGHTS['timing'],
                self.WEIGHTS['road_condition'],
                self.WEIGHTS['school_history'],
                self.WEIGHTS['location'],
            ])
            scores_arr = np.array([
                scores['snowfall'],
                scores['temperature'],
                scores['wind_speed'],
                scores['ice'],
                scores['timing'],
                scores['road_condition'],
                scores['school_history'],
                scores['location'],
            ])

            probability = float(np.dot(weights_arr, scores_arr))
            probability = float(np.clip(probability, 0, 99))

            # ── Category classification ──────────────────────────
            category = self._get_category(probability)

            # ── Scale position ───────────────────────────────────
            scale_position = float(np.clip(probability, 0, 100))

            # ── Chart data (backend-controlled) ──────────────────
            chart_data = self._prepare_chart_data(scores, probability, category)

            # ── Tips ─────────────────────────────────────────────
            tips = self._get_tips(probability, snowfall, temperature_f, ice_accumulation, wind_speed)

            # ── Step-by-step breakdown ────────────────────────────
            breakdown = self._prepare_breakdown(scores, weights_arr, scores_arr, probability)

            # ── Build response ───────────────────────────────────
            return JsonResponse({
                'success': True,
                'probability': round(probability, 1),
                'category': category['name'],
                'category_color': category['color'],
                'category_description': category['description'],
                'scale_position': round(scale_position, 1),
                'scores': {k: round(v, 1) for k, v in scores.items()},
                'chart_data': chart_data,
                'tips': tips,
                'breakdown': breakdown,
                'color_info': self._get_color_info(category['color']),
                'inputs': {
                    'snowfall': snowfall,
                    'temperature': temperature,
                    'temp_unit': temp_unit,
                    'wind_speed': wind_speed,
                    'ice_accumulation': ice_accumulation,
                    'timing': timing,
                    'road_condition': road_condition,
                    'school_history': school_history,
                    'location': location,
                },
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': _('Invalid request data.')}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('Calculation error. Please check your inputs.')}, status=500)

    # ─────────────────────────────────────────────────────────────────
    # Helper: safe float parse
    # ─────────────────────────────────────────────────────────────────
    def _get_float(self, data, key, default=0):
        try:
            val = data.get(key, default)
            if val is None or val == '':
                return default
            return float(str(val).replace(',', ''))
        except (ValueError, TypeError):
            return default

    # ─────────────────────────────────────────────────────────────────
    # Factor scoring (each returns 0-100)
    # ─────────────────────────────────────────────────────────────────
    def _calculate_factor_scores(self, snowfall, temp_f, wind_speed, ice,
                                  timing, road_condition, school_history, location):
        """Score every input factor on a 0-100 scale using NumPy."""

        # 1. Snowfall (most impactful)
        snow_thresholds = np.array([0, 1, 2, 4, 6, 8, 12, 18, 24])
        snow_scores     = np.array([0, 10, 25, 45, 65, 80, 90, 95, 99])
        snowfall_score  = float(np.interp(snowfall, snow_thresholds, snow_scores))

        # 2. Temperature (colder = higher score)
        temp_thresholds = np.array([-40, -20, -10, 0, 10, 20, 25, 32, 40, 50])
        temp_scores     = np.array([99,  95,  90, 85, 75, 60, 45, 30, 10, 0])
        temperature_score = float(np.interp(temp_f, temp_thresholds, temp_scores))

        # 3. Wind speed
        wind_thresholds = np.array([0, 10, 20, 30, 40, 50, 60])
        wind_scores     = np.array([0, 10, 30, 55, 75, 90, 99])
        wind_score      = float(np.interp(wind_speed, wind_thresholds, wind_scores))

        # 4. Ice accumulation (very dangerous, even small amounts)
        ice_thresholds = np.array([0, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0])
        ice_scores     = np.array([0, 30,  55,   75,  90,  97,  99])
        ice_score      = float(np.interp(ice, ice_thresholds, ice_scores))

        # 5. Timing
        timing_map = {
            'before': 85,     # snow expected before school start
            'during': 60,     # during school hours
            'after':  20,     # after school hours
        }
        timing_score = timing_map.get(timing, 50)

        # 6. Road condition
        road_map = {
            'dry':   0,
            'wet':   20,
            'snowy': 65,
            'icy':   90,
        }
        road_score = road_map.get(road_condition, 30)

        # 7. School history
        history_map = {
            'rarely':  20,
            'average': 50,
            'often':   80,
        }
        history_score = history_map.get(school_history, 50)

        # 8. Location
        location_map = {
            'urban':    30,
            'suburban': 50,
            'rural':    75,
        }
        location_score = location_map.get(location, 50)

        return {
            'snowfall':       snowfall_score,
            'temperature':    temperature_score,
            'wind_speed':     wind_score,
            'ice':            ice_score,
            'timing':         float(timing_score),
            'road_condition': float(road_score),
            'school_history': float(history_score),
            'location':       float(location_score),
        }

    # ─────────────────────────────────────────────────────────────────
    # Category classification
    # ─────────────────────────────────────────────────────────────────
    def _get_category(self, probability):
        thresholds = np.array([20, 40, 60, 80])
        idx = int(np.searchsorted(thresholds, probability))

        categories = [
            {'name': _('Very Unlikely'), 'color': 'green',
             'description': _('School will almost certainly be open. Enjoy your day!')},
            {'name': _('Unlikely'), 'color': 'blue',
             'description': _('School is likely to be open, but keep an eye on forecasts.')},
            {'name': _('Possible'), 'color': 'yellow',
             'description': _('There is a reasonable chance of a snow day. Stay tuned for announcements!')},
            {'name': _('Likely'), 'color': 'orange',
             'description': _('A snow day is looking probable! Check local news and school alerts.')},
            {'name': _('Very Likely'), 'color': 'red',
             'description': _('Snow day is highly likely! Start planning your day off.')},
        ]
        return categories[idx]

    # ─────────────────────────────────────────────────────────────────
    # Color info (mirrors BMI pattern)
    # ─────────────────────────────────────────────────────────────────
    def _get_color_info(self, color):
        color_map = {
            'green':  {'hex': '#10b981', 'rgb': 'rgb(16, 185, 129)',
                       'tailwind': 'bg-green-100 text-green-800 border-green-300'},
            'blue':   {'hex': '#3b82f6', 'rgb': 'rgb(59, 130, 246)',
                       'tailwind': 'bg-blue-100 text-blue-800 border-blue-300'},
            'yellow': {'hex': '#f59e0b', 'rgb': 'rgb(245, 158, 11)',
                       'tailwind': 'bg-yellow-100 text-yellow-800 border-yellow-300'},
            'orange': {'hex': '#f97316', 'rgb': 'rgb(249, 115, 22)',
                       'tailwind': 'bg-orange-100 text-orange-800 border-orange-300'},
            'red':    {'hex': '#ef4444', 'rgb': 'rgb(239, 68, 68)',
                       'tailwind': 'bg-red-100 text-red-800 border-red-300'},
        }
        return color_map.get(color, color_map['blue'])

    # ─────────────────────────────────────────────────────────────────
    # Chart data (all charts built in backend)
    # ─────────────────────────────────────────────────────────────────
    def _prepare_chart_data(self, scores, probability, category):
        color_info = self._get_color_info(category['color'])

        # 1. Gauge (doughnut) chart
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Snow Day Chance')), str(_('Remaining'))],
                'datasets': [{
                    'data': [round(probability, 1), round(100 - probability, 1)],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%'
                }]
            },
            'center_text': {
                'value': f'{round(probability, 1)}%',
                'label': str(_('Probability')),
                'color': color_info['hex']
            }
        }

        # 2. Factor breakdown (radar chart)
        factor_labels = [
            str(_('Snowfall')), str(_('Temperature')), str(_('Wind')),
            str(_('Ice')), str(_('Timing')), str(_('Roads')),
            str(_('History')), str(_('Location'))
        ]
        factor_values = [
            scores['snowfall'], scores['temperature'], scores['wind_speed'],
            scores['ice'], scores['timing'], scores['road_condition'],
            scores['school_history'], scores['location']
        ]

        radar_chart = {
            'type': 'radar',
            'data': {
                'labels': factor_labels,
                'datasets': [{
                    'label': str(_('Factor Scores')),
                    'data': [round(v, 1) for v in factor_values],
                    'backgroundColor': f'{color_info["hex"]}33',
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'pointBackgroundColor': color_info['hex'],
                    'pointBorderColor': '#fff',
                    'pointBorderWidth': 2,
                    'pointRadius': 5,
                }]
            }
        }

        # 3. Horizontal bar chart – factor contributions
        weight_keys = list(self.WEIGHTS.keys())
        contribution_values = []
        contribution_colors = []
        for k in weight_keys:
            contrib = scores[k] * self.WEIGHTS[k]
            contribution_values.append(round(contrib, 1))
            # colour by contribution level
            if contrib >= 15:
                contribution_colors.append('#ef4444')
            elif contrib >= 10:
                contribution_colors.append('#f97316')
            elif contrib >= 5:
                contribution_colors.append('#f59e0b')
            else:
                contribution_colors.append('#10b981')

        bar_chart = {
            'type': 'bar',
            'data': {
                'labels': factor_labels,
                'datasets': [{
                    'label': str(_('Weighted Contribution')),
                    'data': contribution_values,
                    'backgroundColor': contribution_colors,
                    'borderColor': contribution_colors,
                    'borderWidth': 1,
                    'borderRadius': 6,
                }]
            }
        }

        return {
            'gauge_chart': gauge_chart,
            'radar_chart': radar_chart,
            'bar_chart': bar_chart,
        }

    # ─────────────────────────────────────────────────────────────────
    # Tips
    # ─────────────────────────────────────────────────────────────────
    def _get_tips(self, prob, snowfall, temp_f, ice, wind):
        tips = []
        if prob >= 70:
            tips.append(str(_('Charge your devices — you may have a day off!')))
            tips.append(str(_('Check your school\'s website or app for official announcements.')))
        if prob >= 50:
            tips.append(str(_('Prepare a backup plan in case school is cancelled.')))
        if snowfall >= 6:
            tips.append(str(_('Heavy snowfall expected. Avoid unnecessary travel.')))
        if ice >= 0.25:
            tips.append(str(_('Ice accumulation can be extremely dangerous. Stay off the roads if possible.')))
        if temp_f <= 0:
            tips.append(str(_('Dangerously cold temperatures. Dress in warm layers if going outside.')))
        if wind >= 30:
            tips.append(str(_('High winds may cause blowing snow and reduced visibility.')))
        if prob < 30:
            tips.append(str(_('Looks like a normal school day. Don\'t forget your homework!')))
            tips.append(str(_('Dress warmly just in case the weather changes.')))
        return tips

    # ─────────────────────────────────────────────────────────────────
    # Step-by-step breakdown
    # ─────────────────────────────────────────────────────────────────
    def _prepare_breakdown(self, scores, weights_arr, scores_arr, probability):
        factor_names = [
            str(_('Snowfall')), str(_('Temperature')), str(_('Wind Speed')),
            str(_('Ice Accumulation')), str(_('Timing')), str(_('Road Condition')),
            str(_('School History')), str(_('Location'))
        ]
        weight_pcts = (weights_arr * 100).tolist()
        contributions = (weights_arr * scores_arr).tolist()

        rows = []
        for i, name in enumerate(factor_names):
            rows.append({
                'factor': name,
                'score': round(float(scores_arr[i]), 1),
                'weight': round(weight_pcts[i], 0),
                'contribution': round(contributions[i], 1),
            })

        return {
            'rows': rows,
            'total': round(probability, 1),
        }
