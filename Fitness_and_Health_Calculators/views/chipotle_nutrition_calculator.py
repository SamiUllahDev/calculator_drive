from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ChipotleNutritionCalculator(View):
    """
    Professional Chipotle Nutrition Calculator.

    Build a custom Chipotle meal and get a detailed nutritional breakdown
    including calories, macros, vitamins, and daily-value percentages.

    Features:
    - Complete Chipotle menu database (per-item nutrition)
    - Multi-item meal builder (base + protein + toppings + extras)
    - NumPy-powered nutritional aggregation
    - Backend-controlled Chart.js configurations
    - Daily-value percentage comparison
    - Meal health rating system
    """
    template_name = 'fitness_and_health_calculators/chipotle_nutrition_calculator.html'

    # ─── RECOMMENDED DAILY VALUES (FDA 2,000 cal diet) ────────────
    DAILY_VALUES = {
        'calories':    2000,
        'total_fat':   78,     # g
        'sat_fat':     20,     # g
        'cholesterol': 300,    # mg
        'sodium':      2300,   # mg
        'carbs':       275,    # g
        'fiber':       28,     # g
        'sugar':       50,     # g
        'protein':     50,     # g
    }

    # ─── CHIPOTLE MENU DATA ──────────────────────────────────────
    # Nutritional values per standard serving (calories, fat(g), sat_fat(g),
    # cholesterol(mg), sodium(mg), carbs(g), fiber(g), sugar(g), protein(g))
    MENU = {
        'base': {
            'burrito': {
                'name': 'Burrito (Flour Tortilla)',
                'nutrition': {'calories': 320, 'total_fat': 9, 'sat_fat': 3.5, 'cholesterol': 0, 'sodium': 600, 'carbs': 50, 'fiber': 3, 'sugar': 1, 'protein': 9},
            },
            'bowl': {
                'name': 'Burrito Bowl',
                'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0},
            },
            'tacos_soft': {
                'name': 'Soft Tacos (3 Flour Tortillas)',
                'nutrition': {'calories': 250, 'total_fat': 7, 'sat_fat': 2.5, 'cholesterol': 0, 'sodium': 470, 'carbs': 39, 'fiber': 2, 'sugar': 1, 'protein': 7},
            },
            'tacos_crispy': {
                'name': 'Crispy Tacos (3 Corn Shells)',
                'nutrition': {'calories': 200, 'total_fat': 7, 'sat_fat': 1, 'cholesterol': 0, 'sodium': 60, 'carbs': 26, 'fiber': 3, 'sugar': 0, 'protein': 3},
            },
            'salad': {
                'name': 'Salad (Supergreens Lettuce Blend)',
                'nutrition': {'calories': 15, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 10, 'carbs': 3, 'fiber': 2, 'sugar': 1, 'protein': 1},
            },
            'quesadilla': {
                'name': 'Quesadilla',
                'nutrition': {'calories': 480, 'total_fat': 19, 'sat_fat': 9, 'cholesterol': 40, 'sodium': 870, 'carbs': 50, 'fiber': 3, 'sugar': 1, 'protein': 22},
            },
            'kids_build_your_own': {
                'name': 'Kids Build Your Own',
                'nutrition': {'calories': 300, 'total_fat': 12, 'sat_fat': 5, 'cholesterol': 15, 'sodium': 530, 'carbs': 35, 'fiber': 2, 'sugar': 1, 'protein': 12},
            },
        },
        'rice': {
            'white_rice': {
                'name': 'White Rice',
                'nutrition': {'calories': 210, 'total_fat': 4, 'sat_fat': 0.5, 'cholesterol': 0, 'sodium': 310, 'carbs': 40, 'fiber': 0, 'sugar': 0, 'protein': 4},
            },
            'brown_rice': {
                'name': 'Brown Rice',
                'nutrition': {'calories': 210, 'total_fat': 6, 'sat_fat': 1, 'cholesterol': 0, 'sodium': 200, 'carbs': 36, 'fiber': 2, 'sugar': 0, 'protein': 4},
            },
            'cauliflower_rice': {
                'name': 'Cauliflower Rice',
                'nutrition': {'calories': 40, 'total_fat': 2, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 330, 'carbs': 4, 'fiber': 2, 'sugar': 2, 'protein': 2},
            },
            'none_rice': {
                'name': 'No Rice',
                'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0},
            },
        },
        'beans': {
            'black_beans': {
                'name': 'Black Beans',
                'nutrition': {'calories': 130, 'total_fat': 1, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 260, 'carbs': 22, 'fiber': 8, 'sugar': 1, 'protein': 8},
            },
            'pinto_beans': {
                'name': 'Pinto Beans',
                'nutrition': {'calories': 130, 'total_fat': 1, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 330, 'carbs': 22, 'fiber': 7, 'sugar': 0, 'protein': 8},
            },
            'none_beans': {
                'name': 'No Beans',
                'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0},
            },
        },
        'protein': {
            'chicken': {
                'name': 'Chicken',
                'nutrition': {'calories': 180, 'total_fat': 7, 'sat_fat': 2, 'cholesterol': 95, 'sodium': 310, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 32},
            },
            'steak': {
                'name': 'Steak',
                'nutrition': {'calories': 150, 'total_fat': 6, 'sat_fat': 2, 'cholesterol': 55, 'sodium': 330, 'carbs': 1, 'fiber': 0, 'sugar': 0, 'protein': 21},
            },
            'barbacoa': {
                'name': 'Barbacoa',
                'nutrition': {'calories': 170, 'total_fat': 7, 'sat_fat': 2.5, 'cholesterol': 60, 'sodium': 460, 'carbs': 2, 'fiber': 0, 'sugar': 1, 'protein': 24},
            },
            'carnitas': {
                'name': 'Carnitas',
                'nutrition': {'calories': 210, 'total_fat': 12, 'sat_fat': 4, 'cholesterol': 65, 'sodium': 450, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 23},
            },
            'sofritas': {
                'name': 'Sofritas',
                'nutrition': {'calories': 150, 'total_fat': 10, 'sat_fat': 1, 'cholesterol': 0, 'sodium': 370, 'carbs': 9, 'fiber': 3, 'sugar': 5, 'protein': 8},
            },
            'veggies': {
                'name': 'Fajita Veggies',
                'nutrition': {'calories': 20, 'total_fat': 0.5, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 170, 'carbs': 4, 'fiber': 1, 'sugar': 2, 'protein': 1},
            },
            'none_protein': {
                'name': 'No Protein',
                'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0},
            },
        },
        'toppings': {
            'fresh_tomato_salsa': {
                'name': 'Fresh Tomato Salsa (Mild)',
                'nutrition': {'calories': 25, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 340, 'carbs': 4, 'fiber': 1, 'sugar': 2, 'protein': 1},
            },
            'roasted_chili_corn_salsa': {
                'name': 'Roasted Chili-Corn Salsa (Medium)',
                'nutrition': {'calories': 80, 'total_fat': 1.5, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 260, 'carbs': 15, 'fiber': 2, 'sugar': 4, 'protein': 2},
            },
            'tomatillo_green_chili_salsa': {
                'name': 'Tomatillo-Green Chili Salsa (Medium)',
                'nutrition': {'calories': 15, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 340, 'carbs': 3, 'fiber': 0, 'sugar': 2, 'protein': 0},
            },
            'tomatillo_red_chili_salsa': {
                'name': 'Tomatillo-Red Chili Salsa (Hot)',
                'nutrition': {'calories': 30, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 310, 'carbs': 4, 'fiber': 2, 'sugar': 3, 'protein': 1},
            },
            'sour_cream': {
                'name': 'Sour Cream',
                'nutrition': {'calories': 110, 'total_fat': 9, 'sat_fat': 5, 'cholesterol': 30, 'sodium': 30, 'carbs': 2, 'fiber': 0, 'sugar': 1, 'protein': 2},
            },
            'cheese': {
                'name': 'Cheese',
                'nutrition': {'calories': 110, 'total_fat': 9, 'sat_fat': 5, 'cholesterol': 30, 'sodium': 200, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 7},
            },
            'guacamole': {
                'name': 'Guacamole',
                'nutrition': {'calories': 230, 'total_fat': 22, 'sat_fat': 3, 'cholesterol': 0, 'sodium': 375, 'carbs': 8, 'fiber': 6, 'sugar': 1, 'protein': 2},
            },
            'queso_blanco': {
                'name': 'Queso Blanco',
                'nutrition': {'calories': 120, 'total_fat': 8, 'sat_fat': 4.5, 'cholesterol': 25, 'sodium': 500, 'carbs': 5, 'fiber': 0, 'sugar': 1, 'protein': 5},
            },
            'romaine_lettuce': {
                'name': 'Romaine Lettuce',
                'nutrition': {'calories': 5, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 1, 'fiber': 1, 'sugar': 0, 'protein': 0},
            },
            'fajita_veggies': {
                'name': 'Fajita Veggies (Topping)',
                'nutrition': {'calories': 20, 'total_fat': 0.5, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 170, 'carbs': 4, 'fiber': 1, 'sugar': 2, 'protein': 1},
            },
        },
        'extras': {
            'chips': {
                'name': 'Chips',
                'nutrition': {'calories': 540, 'total_fat': 25, 'sat_fat': 3.5, 'cholesterol': 0, 'sodium': 420, 'carbs': 73, 'fiber': 5, 'sugar': 0, 'protein': 7},
            },
            'chips_guac': {
                'name': 'Chips & Guacamole',
                'nutrition': {'calories': 770, 'total_fat': 47, 'sat_fat': 6.5, 'cholesterol': 0, 'sodium': 790, 'carbs': 81, 'fiber': 11, 'sugar': 1, 'protein': 9},
            },
            'chips_salsa': {
                'name': 'Chips & Fresh Tomato Salsa',
                'nutrition': {'calories': 570, 'total_fat': 25, 'sat_fat': 3.5, 'cholesterol': 0, 'sodium': 760, 'carbs': 77, 'fiber': 6, 'sugar': 2, 'protein': 8},
            },
            'chips_queso': {
                'name': 'Chips & Queso Blanco',
                'nutrition': {'calories': 660, 'total_fat': 33, 'sat_fat': 8, 'cholesterol': 25, 'sodium': 920, 'carbs': 78, 'fiber': 5, 'sugar': 1, 'protein': 12},
            },
            'drink_regular': {
                'name': 'Fountain Drink (Regular)',
                'nutrition': {'calories': 200, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 45, 'carbs': 54, 'fiber': 0, 'sugar': 54, 'protein': 0},
            },
            'drink_water': {
                'name': 'Water / Unsweetened Tea',
                'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0},
            },
            'none_extras': {
                'name': 'No Extras',
                'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0},
            },
        },
    }

    NUTRIENT_KEYS = ['calories', 'total_fat', 'sat_fat', 'cholesterol', 'sodium', 'carbs', 'fiber', 'sugar', 'protein']

    def get(self, request):
        context = {
            'calculator_name': _('Chipotle Nutrition Calculator'),
            'page_title': _('Chipotle Nutrition Calculator - Build Your Meal'),
            'menu': self._get_menu_for_template(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)
            selected = data.get('items', {})

            # Collect nutrition arrays from selected items
            item_names = []
            nutrition_rows = []

            for category_key, items in selected.items():
                category_menu = self.MENU.get(category_key, {})
                if isinstance(items, str):
                    items = [items]
                for item_key in items:
                    item = category_menu.get(item_key)
                    if item:
                        nutr = item['nutrition']
                        row = [nutr[k] for k in self.NUTRIENT_KEYS]
                        nutrition_rows.append(row)
                        item_names.append(item['name'])

            if not nutrition_rows:
                return JsonResponse({
                    'success': False,
                    'error': str(_('Please select at least one menu item.'))
                }, status=400)

            # ── NumPy aggregation ────────────────────────────────
            nutrition_matrix = np.array(nutrition_rows, dtype=np.float64)
            totals_arr = np.sum(nutrition_matrix, axis=0)
            totals = {k: float(totals_arr[i]) for i, k in enumerate(self.NUTRIENT_KEYS)}

            # ── Daily value percentages ──────────────────────────
            dv_pcts = {}
            for k in self.NUTRIENT_KEYS:
                dv = self.DAILY_VALUES.get(k)
                if dv and dv > 0:
                    dv_pcts[k] = round(totals[k] / dv * 100, 1)
                else:
                    dv_pcts[k] = 0

            # ── Health rating ────────────────────────────────────
            rating = self._compute_meal_rating(totals, dv_pcts)

            # ── Chart data ───────────────────────────────────────
            chart_data = self._prepare_chart_data(totals, dv_pcts, item_names, nutrition_rows, rating)

            return JsonResponse({
                'success': True,
                'totals': {k: round(v, 1) for k, v in totals.items()},
                'daily_values': dv_pcts,
                'items': item_names,
                'item_count': len(item_names),
                'rating': rating,
                'chart_data': chart_data,
                'color_info': self._get_color_info(rating['color']),
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error. Please try again.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    # Build template-friendly menu
    # ─────────────────────────────────────────────────────────────
    def _get_menu_for_template(self):
        result = {}
        for cat_key, items in self.MENU.items():
            cat_items = []
            for item_key, item_data in items.items():
                cat_items.append({
                    'key': item_key,
                    'name': item_data['name'],
                    'calories': item_data['nutrition']['calories'],
                })
            result[cat_key] = cat_items
        return result

    # ─────────────────────────────────────────────────────────────
    # Health rating
    # ─────────────────────────────────────────────────────────────
    def _compute_meal_rating(self, totals, dv_pcts):
        cal = totals['calories']
        sodium_pct = dv_pcts.get('sodium', 0)
        sat_fat_pct = dv_pcts.get('sat_fat', 0)
        fiber_pct = dv_pcts.get('fiber', 0)
        protein_pct = dv_pcts.get('protein', 0)

        score = 100
        # Penalise excessive calories per meal (target ~600 per meal for 3-meal day)
        if cal > 600:
            score -= min((cal - 600) / 20, 30)
        if cal > 1000:
            score -= 15
        # Sodium penalty
        if sodium_pct > 50:
            score -= min((sodium_pct - 50) / 5, 20)
        # Sat-fat penalty
        if sat_fat_pct > 40:
            score -= min((sat_fat_pct - 40) / 5, 15)
        # Bonuses
        if fiber_pct >= 20:
            score += 5
        if protein_pct >= 40:
            score += 5

        score = float(np.clip(score, 0, 100))

        if score >= 80:
            return {'score': round(score), 'label': str(_('Excellent')), 'color': 'green',
                    'description': str(_('A well-balanced meal with moderate calories. Great choice!'))}
        elif score >= 60:
            return {'score': round(score), 'label': str(_('Good')), 'color': 'blue',
                    'description': str(_('A decent meal. Consider lighter toppings to cut calories or sodium.'))}
        elif score >= 40:
            return {'score': round(score), 'label': str(_('Fair')), 'color': 'yellow',
                    'description': str(_('This meal is on the heavier side. Watch your other meals today.'))}
        elif score >= 20:
            return {'score': round(score), 'label': str(_('Heavy')), 'color': 'orange',
                    'description': str(_('High in calories and/or sodium. Balance with lighter meals later.'))}
        else:
            return {'score': round(score), 'label': str(_('Indulgent')), 'color': 'red',
                    'description': str(_('This is a very heavy meal. Enjoy, but plan lighter eating for the rest of the day!'))}

    # ─────────────────────────────────────────────────────────────
    # Color info
    # ─────────────────────────────────────────────────────────────
    def _get_color_info(self, color):
        cmap = {
            'green':  {'hex': '#10b981', 'rgb': 'rgb(16,185,129)',  'tailwind': 'bg-green-100 text-green-800 border-green-300'},
            'blue':   {'hex': '#3b82f6', 'rgb': 'rgb(59,130,246)',  'tailwind': 'bg-blue-100 text-blue-800 border-blue-300'},
            'yellow': {'hex': '#f59e0b', 'rgb': 'rgb(245,158,11)', 'tailwind': 'bg-yellow-100 text-yellow-800 border-yellow-300'},
            'orange': {'hex': '#f97316', 'rgb': 'rgb(249,115,22)', 'tailwind': 'bg-orange-100 text-orange-800 border-orange-300'},
            'red':    {'hex': '#ef4444', 'rgb': 'rgb(239,68,68)',   'tailwind': 'bg-red-100 text-red-800 border-red-300'},
        }
        return cmap.get(color, cmap['blue'])

    # ─────────────────────────────────────────────────────────────
    # Chart data
    # ─────────────────────────────────────────────────────────────
    def _prepare_chart_data(self, totals, dv_pcts, item_names, nutrition_rows, rating):
        color_info = self._get_color_info(rating['color'])

        # 1. Macro Doughnut chart
        macro_labels = [str(_('Fat')), str(_('Carbs')), str(_('Protein'))]
        fat_cals = totals['total_fat'] * 9
        carb_cals = totals['carbs'] * 4
        prot_cals = totals['protein'] * 4
        total_macro_cals = fat_cals + carb_cals + prot_cals
        if total_macro_cals > 0:
            macro_pcts = [round(fat_cals / total_macro_cals * 100, 1),
                          round(carb_cals / total_macro_cals * 100, 1),
                          round(prot_cals / total_macro_cals * 100, 1)]
        else:
            macro_pcts = [0, 0, 0]

        macro_chart = {
            'type': 'doughnut',
            'data': {
                'labels': macro_labels,
                'datasets': [{
                    'data': macro_pcts,
                    'backgroundColor': ['#f59e0b', '#3b82f6', '#10b981'],
                    'borderWidth': 2,
                    'borderColor': '#ffffff',
                }]
            },
            'center_text': {
                'value': str(round(totals['calories'])),
                'label': str(_('Calories')),
                'color': color_info['hex'],
            }
        }

        # 2. Daily Value Bar chart
        dv_keys_display = ['calories', 'total_fat', 'sat_fat', 'sodium', 'carbs', 'fiber', 'protein']
        dv_labels = [str(_('Calories')), str(_('Total Fat')), str(_('Sat Fat')),
                     str(_('Sodium')), str(_('Carbs')), str(_('Fiber')), str(_('Protein'))]
        dv_values = [dv_pcts.get(k, 0) for k in dv_keys_display]
        dv_colors = []
        for v in dv_values:
            if v >= 80:
                dv_colors.append('#ef4444')
            elif v >= 50:
                dv_colors.append('#f97316')
            elif v >= 30:
                dv_colors.append('#f59e0b')
            else:
                dv_colors.append('#10b981')

        dv_chart = {
            'type': 'bar',
            'data': {
                'labels': dv_labels,
                'datasets': [{
                    'label': str(_('% Daily Value')),
                    'data': dv_values,
                    'backgroundColor': dv_colors,
                    'borderRadius': 6,
                }]
            }
        }

        # 3. Per-item calorie breakdown (horizontal bar)
        item_cals = [row[0] for row in nutrition_rows]
        item_colors = ['#6366f1' if c < 200 else '#3b82f6' if c < 400 else '#f59e0b' if c < 600 else '#ef4444' for c in item_cals]

        items_chart = {
            'type': 'bar',
            'data': {
                'labels': item_names,
                'datasets': [{
                    'label': str(_('Calories')),
                    'data': item_cals,
                    'backgroundColor': item_colors,
                    'borderRadius': 6,
                }]
            }
        }

        return {
            'macro_chart': macro_chart,
            'dv_chart': dv_chart,
            'items_chart': items_chart,
        }
