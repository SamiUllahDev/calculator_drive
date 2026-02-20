from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GagCalculator(View):
    """
    GAG (Girl Attractiveness Grade) Calculator — Fun self-assessment tool.

    Users rate themselves on multiple physical and personality attributes
    (1-10 scale) and receive a weighted overall attractiveness grade.

    Features:
    - 14 weighted attributes across Physical & Personality categories
    - NumPy-powered weighted average + percentile estimation
    - Attractiveness grade categories (S-tier → F-tier)
    - Radar chart, bar chart, and gauge chart
    - Fun, entertaining tone — purely for amusement
    """
    template_name = 'other_calculators/gag_calculator.html'

    #  ─── ATTRIBUTES WITH WEIGHTS ─────────────────────────────────
    ATTRIBUTES = {
        'physical': {
            '_label': 'Physical Traits',
            '_weight_group': 0.55,  # 55% of total
            'items': [
                {'key': 'face',    'name': 'Face / Facial Structure', 'weight': 0.18, 'icon': '👤'},
                {'key': 'eyes',    'name': 'Eyes',                    'weight': 0.10, 'icon': '👁'},
                {'key': 'smile',   'name': 'Smile',                   'weight': 0.10, 'icon': '😊'},
                {'key': 'hair',    'name': 'Hair',                    'weight': 0.08, 'icon': '💇'},
                {'key': 'body',    'name': 'Body / Fitness',          'weight': 0.14, 'icon': '💪'},
                {'key': 'style',   'name': 'Style / Fashion',         'weight': 0.08, 'icon': '👗'},
                {'key': 'skin',    'name': 'Skin / Complexion',       'weight': 0.07, 'icon': '✨'},
                {'key': 'height',  'name': 'Height / Proportions',    'weight': 0.05, 'icon': '📏'},
            ],
        },
        'personality': {
            '_label': 'Personality & Social',
            '_weight_group': 0.45,  # 45% of total
            'items': [
                {'key': 'confidence', 'name': 'Confidence',   'weight': 0.20, 'icon': '🔥'},
                {'key': 'humor',      'name': 'Humor',        'weight': 0.15, 'icon': '😂'},
                {'key': 'charisma',   'name': 'Charisma',     'weight': 0.20, 'icon': '🌟'},
                {'key': 'kindness',   'name': 'Kindness',     'weight': 0.15, 'icon': '❤️'},
                {'key': 'intelligence','name': 'Intelligence', 'weight': 0.15, 'icon': '🧠'},
                {'key': 'ambition',   'name': 'Ambition',     'weight': 0.15, 'icon': '🚀'},
            ],
        },
    }

    def get(self, request):
        # Flatten attributes for template
        physical = self.ATTRIBUTES['physical']['items']
        personality = self.ATTRIBUTES['personality']['items']
        context = {
            'calculator_name': _('GAG Calculator'),
            'page_title': _('GAG Calculator - Girl Attractiveness Grade'),
            'physical_attrs': physical,
            'personality_attrs': personality,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)
            scores_raw = data.get('scores', {})

            # ── Collect and validate ─────────────────────────────
            physical_items = self.ATTRIBUTES['physical']['items']
            personality_items = self.ATTRIBUTES['personality']['items']
            phys_weight_group = self.ATTRIBUTES['physical']['_weight_group']
            pers_weight_group = self.ATTRIBUTES['personality']['_weight_group']

            phys_scores = []
            phys_weights = []
            phys_labels = []
            for attr in physical_items:
                val = float(scores_raw.get(attr['key'], 5))
                val = max(1.0, min(10.0, val))
                phys_scores.append(val)
                phys_weights.append(attr['weight'])
                phys_labels.append(attr['name'])

            pers_scores = []
            pers_weights = []
            pers_labels = []
            for attr in personality_items:
                val = float(scores_raw.get(attr['key'], 5))
                val = max(1.0, min(10.0, val))
                pers_scores.append(val)
                pers_weights.append(attr['weight'])
                pers_labels.append(attr['name'])

            # ── NumPy weighted averages ──────────────────────────
            phys_arr = np.array(phys_scores, dtype=np.float64)
            phys_w   = np.array(phys_weights, dtype=np.float64)
            pers_arr = np.array(pers_scores, dtype=np.float64)
            pers_w   = np.array(pers_weights, dtype=np.float64)

            physical_avg  = float(np.average(phys_arr, weights=phys_w))
            personality_avg = float(np.average(pers_arr, weights=pers_w))

            # Combined score
            overall = physical_avg * phys_weight_group + personality_avg * pers_weight_group
            overall = float(np.clip(overall, 1, 10))

            # Percentile estimate (bell-curve centered around 5, std ~1.5)
            from scipy.stats import norm
            percentile = float(norm.cdf(overall, loc=5.0, scale=1.5) * 100)
            percentile = float(np.clip(percentile, 0.1, 99.9))

            # ── Grade / category ─────────────────────────────────
            grade = self._get_grade(overall)

            # ── All individual scores ────────────────────────────
            all_labels = phys_labels + pers_labels
            all_scores = phys_scores + pers_scores

            # ── Chart data ───────────────────────────────────────
            chart_data = self._prepare_chart_data(
                all_labels, all_scores, physical_avg, personality_avg,
                overall, percentile, grade
            )

            return JsonResponse({
                'success': True,
                'overall': round(overall, 2),
                'physical_avg': round(physical_avg, 2),
                'personality_avg': round(personality_avg, 2),
                'percentile': round(percentile, 1),
                'grade': grade,
                'scores': {
                    'labels': all_labels,
                    'values': [round(s, 1) for s in all_scores],
                },
                'chart_data': chart_data,
                'color_info': self._get_color_info(grade['color']),
            })

        except ImportError:
            # Fallback if scipy not available
            return self._post_no_scipy(request)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request.'))}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(_('Calculation error.'))}, status=500)

    def _post_no_scipy(self, request):
        """Fallback without scipy — use simple percentile approximation."""
        try:
            data = json.loads(request.body)
            scores_raw = data.get('scores', {})

            physical_items = self.ATTRIBUTES['physical']['items']
            personality_items = self.ATTRIBUTES['personality']['items']
            phys_weight_group = self.ATTRIBUTES['physical']['_weight_group']
            pers_weight_group = self.ATTRIBUTES['personality']['_weight_group']

            phys_scores, phys_weights, phys_labels = [], [], []
            for attr in physical_items:
                val = float(scores_raw.get(attr['key'], 5))
                val = max(1.0, min(10.0, val))
                phys_scores.append(val)
                phys_weights.append(attr['weight'])
                phys_labels.append(attr['name'])

            pers_scores, pers_weights, pers_labels = [], [], []
            for attr in personality_items:
                val = float(scores_raw.get(attr['key'], 5))
                val = max(1.0, min(10.0, val))
                pers_scores.append(val)
                pers_weights.append(attr['weight'])
                pers_labels.append(attr['name'])

            phys_arr = np.array(phys_scores, dtype=np.float64)
            phys_w = np.array(phys_weights, dtype=np.float64)
            pers_arr = np.array(pers_scores, dtype=np.float64)
            pers_w = np.array(pers_weights, dtype=np.float64)

            physical_avg = float(np.average(phys_arr, weights=phys_w))
            personality_avg = float(np.average(pers_arr, weights=pers_w))
            overall = physical_avg * phys_weight_group + personality_avg * pers_weight_group
            overall = float(np.clip(overall, 1, 10))

            # Simple linear percentile approximation
            percentile = float(np.clip((overall - 1) / 9 * 100, 0.1, 99.9))

            grade = self._get_grade(overall)
            all_labels = phys_labels + pers_labels
            all_scores = phys_scores + pers_scores
            chart_data = self._prepare_chart_data(
                all_labels, all_scores, physical_avg, personality_avg,
                overall, percentile, grade
            )

            return JsonResponse({
                'success': True,
                'overall': round(overall, 2),
                'physical_avg': round(physical_avg, 2),
                'personality_avg': round(personality_avg, 2),
                'percentile': round(percentile, 1),
                'grade': grade,
                'scores': {'labels': all_labels, 'values': [round(s, 1) for s in all_scores]},
                'chart_data': chart_data,
                'color_info': self._get_color_info(grade['color']),
            })
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    def _get_grade(self, score):
        thresholds = np.array([3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
        idx = int(np.searchsorted(thresholds, score))
        grades = [
            {'grade': 'F',  'label': str(_('Below Average')),    'color': 'red',    'emoji': '😕',
             'description': str(_('Room for improvement. Focus on confidence — it changes everything!'))},
            {'grade': 'D',  'label': str(_('Slightly Below Average')), 'color': 'red', 'emoji': '🙁',
             'description': str(_('Not far from average. Small improvements in style and confidence will help.'))},
            {'grade': 'C',  'label': str(_('Average')),          'color': 'orange', 'emoji': '😐',
             'description': str(_('You are right around average. Your personality traits can push you higher!'))},
            {'grade': 'C+', 'label': str(_('Above Average')),    'color': 'yellow', 'emoji': '🙂',
             'description': str(_('Slightly above average. You have solid attributes to build on.'))},
            {'grade': 'B',  'label': str(_('Attractive')),       'color': 'blue',   'emoji': '😊',
             'description': str(_('You are above average! Most people would notice your appeal.'))},
            {'grade': 'A',  'label': str(_('Very Attractive')),  'color': 'green',  'emoji': '😍',
             'description': str(_('Top tier! You stand out in a crowd with strong physical and personality scores.'))},
            {'grade': 'A+', 'label': str(_('Stunning')),         'color': 'green',  'emoji': '🤩',
             'description': str(_('Exceptionally attractive. You are in the top percentile!'))},
            {'grade': 'S',  'label': str(_('Supermodel Tier')),  'color': 'purple', 'emoji': '👑',
             'description': str(_('Nearly perfect scores across the board. You are in a league of your own!'))},
        ]
        return grades[idx]

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

    # ─────────────────────────────────────────────────────────────
    def _prepare_chart_data(self, labels, scores, phys_avg, pers_avg,
                            overall, percentile, grade):
        ci = self._get_color_info(grade['color'])

        # 1. Radar chart — all attributes
        radar_chart = {
            'type': 'radar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Your Scores')),
                    'data': [round(s, 1) for s in scores],
                    'backgroundColor': ci['hex'] + '33',
                    'borderColor': ci['hex'],
                    'borderWidth': 2,
                    'pointBackgroundColor': ci['hex'],
                    'pointBorderColor': '#fff',
                    'pointRadius': 5,
                    'pointBorderWidth': 2,
                }]
            }
        }

        # 2. Gauge (doughnut) for overall score
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Score')), str(_('Remaining'))],
                'datasets': [{
                    'data': [round(overall, 1), round(10 - overall, 1)],
                    'backgroundColor': [ci['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%',
                }]
            },
            'center_text': {
                'value': f'{overall:.1f}',
                'label': grade['grade'],
                'color': ci['hex'],
            }
        }

        # 3. Physical vs Personality comparison
        compare_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Physical')), str(_('Personality'))],
                'datasets': [{
                    'label': str(_('Average Score')),
                    'data': [round(phys_avg, 2), round(pers_avg, 2)],
                    'backgroundColor': ['#ec4899', '#8b5cf6'],
                    'borderRadius': 8,
                }]
            }
        }

        # 4. Individual scores bar chart
        bar_colors = []
        for s in scores:
            if s >= 8:
                bar_colors.append('#10b981')
            elif s >= 6:
                bar_colors.append('#3b82f6')
            elif s >= 4:
                bar_colors.append('#f59e0b')
            else:
                bar_colors.append('#ef4444')

        scores_chart = {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Score')),
                    'data': [round(s, 1) for s in scores],
                    'backgroundColor': bar_colors,
                    'borderRadius': 6,
                }]
            }
        }

        return {
            'radar_chart': radar_chart,
            'gauge_chart': gauge_chart,
            'compare_chart': compare_chart,
            'scores_chart': scores_chart,
        }
