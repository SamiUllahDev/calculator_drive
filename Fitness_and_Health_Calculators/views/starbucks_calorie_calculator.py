from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class StarbucksCalorieCalculator(View):
    """
    Professional Starbucks Calorie Calculator.

    Build a custom Starbucks order and get a detailed nutritional breakdown
    including calories, macros, caffeine, and daily-value percentages.

    Features:
    - Comprehensive Starbucks drink + food database
    - Size / milk / sweetener customisation
    - NumPy-powered nutritional aggregation
    - Backend-controlled Chart.js configurations
    - Daily-value percentage comparison
    - Health rating system
    """
    template_name = 'fitness_and_health_calculators/starbucks_calorie_calculator.html'

    DAILY_VALUES = {
        'calories':    2000,
        'total_fat':   78,
        'sat_fat':     20,
        'cholesterol': 300,
        'sodium':      2300,
        'carbs':       275,
        'fiber':       28,
        'sugar':       50,
        'protein':     50,
        'caffeine':    400,   # FDA recommended max
    }

    NUTRIENT_KEYS = ['calories', 'total_fat', 'sat_fat', 'cholesterol', 'sodium',
                     'carbs', 'fiber', 'sugar', 'protein', 'caffeine']

    # ─── STARBUCKS MENU ──────────────────────────────────────────
    # Values are for Grande (16 oz) with 2% milk unless noted.
    # (calories, fat g, sat_fat g, chol mg, sodium mg, carbs g, fiber g, sugar g, protein g, caffeine mg)
    MENU = {
        'espresso_drinks': {
            '_label': 'Espresso Drinks',
            'caffe_latte': {
                'name': 'Caffè Latte',
                'nutrition': {'calories': 190, 'total_fat': 7, 'sat_fat': 4.5, 'cholesterol': 30, 'sodium': 170, 'carbs': 19, 'fiber': 0, 'sugar': 17, 'protein': 13, 'caffeine': 150},
            },
            'cappuccino': {
                'name': 'Cappuccino',
                'nutrition': {'calories': 140, 'total_fat': 5, 'sat_fat': 3, 'cholesterol': 20, 'sodium': 120, 'carbs': 14, 'fiber': 0, 'sugar': 12, 'protein': 9, 'caffeine': 150},
            },
            'caramel_macchiato': {
                'name': 'Caramel Macchiato',
                'nutrition': {'calories': 250, 'total_fat': 7, 'sat_fat': 4.5, 'cholesterol': 25, 'sodium': 150, 'carbs': 35, 'fiber': 0, 'sugar': 33, 'protein': 10, 'caffeine': 150},
            },
            'flat_white': {
                'name': 'Flat White',
                'nutrition': {'calories': 170, 'total_fat': 9, 'sat_fat': 5, 'cholesterol': 25, 'sodium': 130, 'carbs': 14, 'fiber': 0, 'sugar': 13, 'protein': 11, 'caffeine': 195},
            },
            'caffe_mocha': {
                'name': 'Caffè Mocha',
                'nutrition': {'calories': 370, 'total_fat': 14, 'sat_fat': 8, 'cholesterol': 40, 'sodium': 180, 'carbs': 50, 'fiber': 3, 'sugar': 43, 'protein': 14, 'caffeine': 175},
            },
            'white_mocha': {
                'name': 'White Chocolate Mocha',
                'nutrition': {'calories': 430, 'total_fat': 16, 'sat_fat': 10, 'cholesterol': 45, 'sodium': 250, 'carbs': 56, 'fiber': 0, 'sugar': 53, 'protein': 15, 'caffeine': 150},
            },
            'americano': {
                'name': 'Caffè Americano',
                'nutrition': {'calories': 15, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 10, 'carbs': 3, 'fiber': 0, 'sugar': 0, 'protein': 1, 'caffeine': 225},
            },
            'espresso_shot': {
                'name': 'Espresso (Doppio)',
                'nutrition': {'calories': 10, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 2, 'fiber': 0, 'sugar': 0, 'protein': 1, 'caffeine': 150},
            },
            'pumpkin_spice_latte': {
                'name': 'Pumpkin Spice Latte',
                'nutrition': {'calories': 390, 'total_fat': 14, 'sat_fat': 8, 'cholesterol': 50, 'sodium': 240, 'carbs': 52, 'fiber': 0, 'sugar': 50, 'protein': 14, 'caffeine': 150},
            },
            'vanilla_latte': {
                'name': 'Vanilla Latte',
                'nutrition': {'calories': 250, 'total_fat': 7, 'sat_fat': 4.5, 'cholesterol': 30, 'sodium': 170, 'carbs': 35, 'fiber': 0, 'sugar': 34, 'protein': 13, 'caffeine': 150},
            },
        },
        'frappuccinos': {
            '_label': 'Frappuccinos®',
            'caramel_frappuccino': {
                'name': 'Caramel Frappuccino®',
                'nutrition': {'calories': 380, 'total_fat': 15, 'sat_fat': 9, 'cholesterol': 55, 'sodium': 230, 'carbs': 54, 'fiber': 0, 'sugar': 54, 'protein': 5, 'caffeine': 90},
            },
            'mocha_frappuccino': {
                'name': 'Mocha Frappuccino®',
                'nutrition': {'calories': 370, 'total_fat': 15, 'sat_fat': 9, 'cholesterol': 55, 'sodium': 230, 'carbs': 52, 'fiber': 2, 'sugar': 49, 'protein': 6, 'caffeine': 110},
            },
            'java_chip_frappuccino': {
                'name': 'Java Chip Frappuccino®',
                'nutrition': {'calories': 440, 'total_fat': 19, 'sat_fat': 12, 'cholesterol': 55, 'sodium': 250, 'carbs': 63, 'fiber': 2, 'sugar': 59, 'protein': 6, 'caffeine': 110},
            },
            'vanilla_bean_frappuccino': {
                'name': 'Vanilla Bean Crème Frappuccino®',
                'nutrition': {'calories': 380, 'total_fat': 15, 'sat_fat': 9, 'cholesterol': 55, 'sodium': 230, 'carbs': 56, 'fiber': 0, 'sugar': 55, 'protein': 5, 'caffeine': 0},
            },
            'strawberry_frappuccino': {
                'name': 'Strawberry Crème Frappuccino®',
                'nutrition': {'calories': 370, 'total_fat': 15, 'sat_fat': 9, 'cholesterol': 55, 'sodium': 200, 'carbs': 54, 'fiber': 0, 'sugar': 52, 'protein': 5, 'caffeine': 0},
            },
        },
        'cold_drinks': {
            '_label': 'Cold Coffees & Teas',
            'cold_brew': {
                'name': 'Cold Brew',
                'nutrition': {'calories': 5, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 15, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0, 'caffeine': 205},
            },
            'vanilla_sweet_cream_cold_brew': {
                'name': 'Vanilla Sweet Cream Cold Brew',
                'nutrition': {'calories': 110, 'total_fat': 5, 'sat_fat': 3.5, 'cholesterol': 20, 'sodium': 80, 'carbs': 14, 'fiber': 0, 'sugar': 14, 'protein': 1, 'caffeine': 205},
            },
            'salted_caramel_cream_cold_brew': {
                'name': 'Salted Caramel Cream Cold Brew',
                'nutrition': {'calories': 240, 'total_fat': 12, 'sat_fat': 7, 'cholesterol': 35, 'sodium': 330, 'carbs': 28, 'fiber': 0, 'sugar': 27, 'protein': 4, 'caffeine': 185},
            },
            'iced_coffee': {
                'name': 'Iced Coffee (sweetened)',
                'nutrition': {'calories': 80, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 15, 'carbs': 20, 'fiber': 0, 'sugar': 20, 'protein': 1, 'caffeine': 165},
            },
            'iced_green_tea_lemonade': {
                'name': 'Iced Green Tea Lemonade',
                'nutrition': {'calories': 70, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 10, 'carbs': 17, 'fiber': 0, 'sugar': 15, 'protein': 0, 'caffeine': 25},
            },
            'iced_chai_tea_latte': {
                'name': 'Iced Chai Tea Latte',
                'nutrition': {'calories': 240, 'total_fat': 4.5, 'sat_fat': 2.5, 'cholesterol': 15, 'sodium': 125, 'carbs': 42, 'fiber': 0, 'sugar': 42, 'protein': 8, 'caffeine': 95},
            },
            'pink_drink': {
                'name': 'Pink Drink (Strawberry Açaí)',
                'nutrition': {'calories': 140, 'total_fat': 2.5, 'sat_fat': 2, 'cholesterol': 0, 'sodium': 65, 'carbs': 27, 'fiber': 1, 'sugar': 25, 'protein': 1, 'caffeine': 45},
            },
            'mango_dragonfruit_refresher': {
                'name': 'Mango Dragonfruit Refresher',
                'nutrition': {'calories': 90, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 15, 'carbs': 21, 'fiber': 0, 'sugar': 19, 'protein': 1, 'caffeine': 45},
            },
        },
        'hot_drinks': {
            '_label': 'Hot Coffees & Teas',
            'pike_place_roast': {
                'name': 'Pike Place® Roast',
                'nutrition': {'calories': 5, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 10, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 1, 'caffeine': 310},
            },
            'blonde_roast': {
                'name': 'Blonde Roast',
                'nutrition': {'calories': 5, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 10, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 1, 'caffeine': 360},
            },
            'chai_tea_latte': {
                'name': 'Chai Tea Latte',
                'nutrition': {'calories': 240, 'total_fat': 4.5, 'sat_fat': 2, 'cholesterol': 15, 'sodium': 115, 'carbs': 42, 'fiber': 0, 'sugar': 42, 'protein': 8, 'caffeine': 95},
            },
            'matcha_tea_latte': {
                'name': 'Matcha Tea Latte',
                'nutrition': {'calories': 240, 'total_fat': 7, 'sat_fat': 4.5, 'cholesterol': 25, 'sodium': 160, 'carbs': 34, 'fiber': 1, 'sugar': 32, 'protein': 12, 'caffeine': 80},
            },
            'hot_chocolate': {
                'name': 'Hot Chocolate',
                'nutrition': {'calories': 370, 'total_fat': 14, 'sat_fat': 8, 'cholesterol': 40, 'sodium': 200, 'carbs': 48, 'fiber': 3, 'sugar': 43, 'protein': 15, 'caffeine': 25},
            },
            'london_fog_latte': {
                'name': 'London Fog Tea Latte',
                'nutrition': {'calories': 180, 'total_fat': 4, 'sat_fat': 2.5, 'cholesterol': 15, 'sodium': 115, 'carbs': 30, 'fiber': 0, 'sugar': 28, 'protein': 7, 'caffeine': 40},
            },
        },
        'food': {
            '_label': 'Food & Bakery',
            'butter_croissant': {
                'name': 'Butter Croissant',
                'nutrition': {'calories': 260, 'total_fat': 14, 'sat_fat': 8, 'cholesterol': 45, 'sodium': 310, 'carbs': 28, 'fiber': 1, 'sugar': 5, 'protein': 5, 'caffeine': 0},
            },
            'chocolate_croissant': {
                'name': 'Chocolate Croissant',
                'nutrition': {'calories': 340, 'total_fat': 17, 'sat_fat': 10, 'cholesterol': 35, 'sodium': 310, 'carbs': 38, 'fiber': 2, 'sugar': 14, 'protein': 6, 'caffeine': 5},
            },
            'everything_bagel': {
                'name': 'Everything Bagel',
                'nutrition': {'calories': 300, 'total_fat': 3, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 620, 'carbs': 56, 'fiber': 3, 'sugar': 6, 'protein': 11, 'caffeine': 0},
            },
            'sausage_cheddar_sandwich': {
                'name': 'Sausage, Cheddar & Egg Sandwich',
                'nutrition': {'calories': 480, 'total_fat': 26, 'sat_fat': 10, 'cholesterol': 195, 'sodium': 880, 'carbs': 34, 'fiber': 1, 'sugar': 4, 'protein': 26, 'caffeine': 0},
            },
            'bacon_gouda_sandwich': {
                'name': 'Bacon, Gouda & Egg Sandwich',
                'nutrition': {'calories': 370, 'total_fat': 19, 'sat_fat': 7, 'cholesterol': 170, 'sodium': 820, 'carbs': 26, 'fiber': 1, 'sugar': 3, 'protein': 20, 'caffeine': 0},
            },
            'cake_pop': {
                'name': 'Birthday Cake Pop',
                'nutrition': {'calories': 180, 'total_fat': 9, 'sat_fat': 6, 'cholesterol': 20, 'sodium': 100, 'carbs': 24, 'fiber': 0, 'sugar': 18, 'protein': 2, 'caffeine': 0},
            },
            'banana_nut_bread': {
                'name': 'Banana Nut Bread',
                'nutrition': {'calories': 420, 'total_fat': 22, 'sat_fat': 3.5, 'cholesterol': 55, 'sodium': 380, 'carbs': 52, 'fiber': 2, 'sugar': 29, 'protein': 6, 'caffeine': 0},
            },
            'double_chocolate_brownie': {
                'name': 'Double Chocolate Brownie',
                'nutrition': {'calories': 480, 'total_fat': 27, 'sat_fat': 8, 'cholesterol': 75, 'sodium': 250, 'carbs': 56, 'fiber': 3, 'sugar': 36, 'protein': 6, 'caffeine': 15},
            },
            'cheese_danish': {
                'name': 'Cheese Danish',
                'nutrition': {'calories': 290, 'total_fat': 14, 'sat_fat': 7, 'cholesterol': 50, 'sodium': 280, 'carbs': 35, 'fiber': 0, 'sugar': 14, 'protein': 6, 'caffeine': 0},
            },
            'protein_box_eggs': {
                'name': 'Eggs & Cheddar Protein Box',
                'nutrition': {'calories': 460, 'total_fat': 24, 'sat_fat': 7, 'cholesterol': 220, 'sodium': 730, 'carbs': 38, 'fiber': 3, 'sugar': 13, 'protein': 26, 'caffeine': 0},
            },
        },
    }

    # ─── Size multipliers (relative to Grande=1.0) ───────────────
    SIZE_MULTIPLIERS = {
        'short':  0.50,   # 8 oz
        'tall':   0.75,   # 12 oz
        'grande': 1.00,   # 16 oz
        'venti':  1.25,   # 20 oz / 24 oz iced
    }

    # ─── Milk modifications (calorie delta from 2% base) ─────────
    MILK_MODS = {
        'two_percent':  {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'sugar': 0, 'protein': 0},
        'whole':        {'calories': 20, 'total_fat': 2, 'sat_fat': 1.5, 'sugar': 0, 'protein': 0},
        'nonfat':       {'calories': -30, 'total_fat': -5, 'sat_fat': -3, 'sugar': 1, 'protein': 1},
        'oat':          {'calories': 10, 'total_fat': 1, 'sat_fat': -1, 'sugar': 3, 'protein': -3},
        'almond':       {'calories': -40, 'total_fat': -1, 'sat_fat': -3, 'sugar': -5, 'protein': -6},
        'coconut':      {'calories': -20, 'total_fat': 1, 'sat_fat': 1, 'sugar': -5, 'protein': -7},
        'soy':          {'calories': -10, 'total_fat': 0, 'sat_fat': -2, 'sugar': 1, 'protein': -3},
    }

    # ─── Extra add-ons ────────────────────────────────────────────
    EXTRAS = {
        'whipped_cream':  {'name': 'Whipped Cream', 'nutrition': {'calories': 80, 'total_fat': 8, 'sat_fat': 5, 'cholesterol': 25, 'sodium': 10, 'carbs': 1, 'fiber': 0, 'sugar': 1, 'protein': 0, 'caffeine': 0}},
        'extra_shot':     {'name': 'Extra Espresso Shot', 'nutrition': {'calories': 5, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 1, 'fiber': 0, 'sugar': 0, 'protein': 1, 'caffeine': 75}},
        'vanilla_syrup':  {'name': 'Vanilla Syrup (1 pump)', 'nutrition': {'calories': 20, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 5, 'fiber': 0, 'sugar': 5, 'protein': 0, 'caffeine': 0}},
        'caramel_syrup':  {'name': 'Caramel Syrup (1 pump)', 'nutrition': {'calories': 20, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 5, 'fiber': 0, 'sugar': 5, 'protein': 0, 'caffeine': 0}},
        'mocha_sauce':    {'name': 'Mocha Sauce (1 pump)', 'nutrition': {'calories': 25, 'total_fat': 0.5, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 5, 'fiber': 0, 'sugar': 5, 'protein': 0, 'caffeine': 5}},
        'caramel_drizzle': {'name': 'Caramel Drizzle', 'nutrition': {'calories': 15, 'total_fat': 0.5, 'sat_fat': 0, 'cholesterol': 5, 'sodium': 25, 'carbs': 2, 'fiber': 0, 'sugar': 2, 'protein': 0, 'caffeine': 0}},
        'chocolate_drizzle': {'name': 'Chocolate Drizzle', 'nutrition': {'calories': 10, 'total_fat': 0.5, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 2, 'fiber': 0, 'sugar': 1, 'protein': 0, 'caffeine': 5}},
        'none_extra':     {'name': 'No Extras', 'nutrition': {'calories': 0, 'total_fat': 0, 'sat_fat': 0, 'cholesterol': 0, 'sodium': 0, 'carbs': 0, 'fiber': 0, 'sugar': 0, 'protein': 0, 'caffeine': 0}},
    }

    def get(self, request):
        context = {
            'calculator_name': _('Starbucks Calorie Calculator'),
            'page_title': _('Starbucks Calorie Calculator - Know Your Order'),
            'menu': self._menu_for_template(),
            'extras': self._extras_for_template(),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)

            # Primary drink
            drink_cat = data.get('drink_category', '')
            drink_key = data.get('drink', '')
            size = data.get('size', 'grande')
            milk = data.get('milk', 'two_percent')

            # Food item
            food_key = data.get('food', 'none')

            # Extras (list)
            extras_keys = data.get('extras', [])
            if isinstance(extras_keys, str):
                extras_keys = [extras_keys] if extras_keys else []

            # Validate size & milk
            if size not in self.SIZE_MULTIPLIERS:
                size = 'grande'
            if milk not in self.MILK_MODS:
                milk = 'two_percent'

            items = []         # list of (name, nutrition_dict)

            # ── Drink ───────────────────────────────────────────
            cat_menu = self.MENU.get(drink_cat, {})
            drink_item = cat_menu.get(drink_key)
            is_food_only = drink_cat == 'food'

            if drink_item:
                base_nutr = dict(drink_item['nutrition'])
                if not is_food_only:
                    # Apply size multiplier
                    mult = self.SIZE_MULTIPLIERS.get(size, 1.0)
                    for k in self.NUTRIENT_KEYS:
                        base_nutr[k] = base_nutr[k] * mult

                    # Apply milk modification (only for milk-based drinks)
                    milk_keys_to_skip = {'americano', 'espresso_shot', 'cold_brew',
                                         'iced_coffee', 'pike_place_roast', 'blonde_roast',
                                         'iced_green_tea_lemonade', 'mango_dragonfruit_refresher',
                                         'pink_drink'}
                    if drink_key not in milk_keys_to_skip:
                        mod = self.MILK_MODS.get(milk, {})
                        for mk, mv in mod.items():
                            if mk in base_nutr:
                                base_nutr[mk] = max(0, base_nutr[mk] + mv * mult)

                size_label = size.capitalize() if not is_food_only else ''
                name = f"{drink_item['name']} ({size_label})" if size_label else drink_item['name']
                items.append((name, base_nutr))

            # ── Food ────────────────────────────────────────────
            if food_key and food_key != 'none':
                food_menu = self.MENU.get('food', {})
                food_item = food_menu.get(food_key)
                if food_item:
                    items.append((food_item['name'], dict(food_item['nutrition'])))

            # ── Extras ──────────────────────────────────────────
            for ek in extras_keys:
                extra = self.EXTRAS.get(ek)
                if extra and ek != 'none_extra':
                    items.append((extra['name'], dict(extra['nutrition'])))

            if not items:
                return JsonResponse({'success': False, 'error': str(_('Please select at least one item.'))}, status=400)

            # ── Aggregate with NumPy ────────────────────────────
            rows = [[item[1].get(k, 0) for k in self.NUTRIENT_KEYS] for item in items]
            mat = np.array(rows, dtype=np.float64)
            totals_arr = np.sum(mat, axis=0)
            totals = {k: round(float(totals_arr[i]), 1) for i, k in enumerate(self.NUTRIENT_KEYS)}

            # ── DV percentages ──────────────────────────────────
            dv_pcts = {}
            for k in self.NUTRIENT_KEYS:
                dv = self.DAILY_VALUES.get(k)
                if dv and dv > 0:
                    dv_pcts[k] = round(totals[k] / dv * 100, 1)
                else:
                    dv_pcts[k] = 0

            # ── Rating ──────────────────────────────────────────
            rating = self._compute_rating(totals, dv_pcts)

            # ── Charts ──────────────────────────────────────────
            item_names = [i[0] for i in items]
            chart_data = self._prepare_chart_data(totals, dv_pcts, item_names, rows, rating)

            return JsonResponse({
                'success': True,
                'totals': totals,
                'daily_values': dv_pcts,
                'items': item_names,
                'item_count': len(items),
                'rating': rating,
                'chart_data': chart_data,
                'color_info': self._get_color_info(rating['color']),
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error. Please try again.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    def _menu_for_template(self):
        result = {}
        for cat_key, items in self.MENU.items():
            label = items.get('_label', cat_key.replace('_', ' ').title())
            cat_items = []
            for key, val in items.items():
                if key.startswith('_'):
                    continue
                cat_items.append({'key': key, 'name': val['name'], 'calories': val['nutrition']['calories']})
            result[cat_key] = {'label': label, 'items': cat_items}
        return result

    def _extras_for_template(self):
        return [{'key': k, 'name': v['name'], 'calories': v['nutrition']['calories']}
                for k, v in self.EXTRAS.items()]

    # ─────────────────────────────────────────────────────────────
    def _compute_rating(self, totals, dv_pcts):
        cal = totals['calories']
        sugar_pct = dv_pcts.get('sugar', 0)
        sat_fat_pct = dv_pcts.get('sat_fat', 0)
        caffeine_pct = dv_pcts.get('caffeine', 0)

        score = 100
        if cal > 400:
            score -= min((cal - 400) / 20, 25)
        if cal > 700:
            score -= 15
        if sugar_pct > 50:
            score -= min((sugar_pct - 50) / 5, 20)
        if sat_fat_pct > 35:
            score -= min((sat_fat_pct - 35) / 5, 15)
        if caffeine_pct > 60:
            score -= 5

        score = float(np.clip(score, 0, 100))

        if score >= 80:
            return {'score': round(score), 'label': str(_('Light & Smart')), 'color': 'green',
                    'description': str(_('A low-calorie, mindful choice. Great job!'))}
        elif score >= 60:
            return {'score': round(score), 'label': str(_('Moderate')), 'color': 'blue',
                    'description': str(_('A reasonable order. Watch the sugar if you add food.'))}
        elif score >= 40:
            return {'score': round(score), 'label': str(_('Treat Yourself')), 'color': 'yellow',
                    'description': str(_('This is on the indulgent side. Balance it with lighter meals.'))}
        elif score >= 20:
            return {'score': round(score), 'label': str(_('Heavy')), 'color': 'orange',
                    'description': str(_('High in sugar and/or calories. Consider lighter options.'))}
        else:
            return {'score': round(score), 'label': str(_('Dessert in a Cup')), 'color': 'red',
                    'description': str(_('This order is very high in sugar and calories. Enjoy as a rare treat!'))}

    # ─────────────────────────────────────────────────────────────
    def _get_color_info(self, color):
        cmap = {
            'green':  {'hex': '#10b981', 'tailwind': 'bg-green-100 text-green-800 border-green-300'},
            'blue':   {'hex': '#3b82f6', 'tailwind': 'bg-blue-100 text-blue-800 border-blue-300'},
            'yellow': {'hex': '#f59e0b', 'tailwind': 'bg-yellow-100 text-yellow-800 border-yellow-300'},
            'orange': {'hex': '#f97316', 'tailwind': 'bg-orange-100 text-orange-800 border-orange-300'},
            'red':    {'hex': '#ef4444', 'tailwind': 'bg-red-100 text-red-800 border-red-300'},
        }
        return cmap.get(color, cmap['blue'])

    # ─────────────────────────────────────────────────────────────
    def _prepare_chart_data(self, totals, dv_pcts, item_names, rows, rating):
        ci = self._get_color_info(rating['color'])

        # 1. Macro doughnut
        fat_cal = totals['total_fat'] * 9
        carb_cal = totals['carbs'] * 4
        prot_cal = totals['protein'] * 4
        total_mc = fat_cal + carb_cal + prot_cal
        if total_mc > 0:
            mpcts = [round(fat_cal/total_mc*100, 1), round(carb_cal/total_mc*100, 1), round(prot_cal/total_mc*100, 1)]
        else:
            mpcts = [0, 0, 0]

        macro_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Fat')), str(_('Carbs')), str(_('Protein'))],
                'datasets': [{'data': mpcts, 'backgroundColor': ['#f59e0b', '#3b82f6', '#10b981'], 'borderWidth': 2, 'borderColor': '#fff'}]
            },
            'center_text': {'value': str(round(totals['calories'])), 'label': str(_('Calories')), 'color': ci['hex']}
        }

        # 2. DV bar chart
        dv_keys_show = ['calories', 'total_fat', 'sat_fat', 'sugar', 'sodium', 'caffeine', 'protein']
        dv_labels = [str(_('Calories')), str(_('Fat')), str(_('Sat Fat')), str(_('Sugar')), str(_('Sodium')), str(_('Caffeine')), str(_('Protein'))]
        dv_vals = [dv_pcts.get(k, 0) for k in dv_keys_show]
        dv_colors = ['#ef4444' if v >= 80 else '#f97316' if v >= 50 else '#f59e0b' if v >= 30 else '#10b981' for v in dv_vals]

        dv_chart = {
            'type': 'bar',
            'data': {
                'labels': dv_labels,
                'datasets': [{'label': str(_('% Daily Value')), 'data': dv_vals, 'backgroundColor': dv_colors, 'borderRadius': 6}]
            }
        }

        # 3. Per-item calorie bar
        item_cals = [row[0] for row in rows]
        ic = ['#6366f1' if c < 100 else '#3b82f6' if c < 300 else '#f59e0b' if c < 500 else '#ef4444' for c in item_cals]
        items_chart = {
            'type': 'bar',
            'data': {
                'labels': item_names,
                'datasets': [{'label': str(_('Calories')), 'data': item_cals, 'backgroundColor': ic, 'borderRadius': 6}]
            }
        }

        # 4. Sugar vs caffeine comparison
        compare_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Sugar')), str(_('Caffeine'))],
                'datasets': [{
                    'label': str(_('Amount')),
                    'data': [totals['sugar'], totals['caffeine']],
                    'backgroundColor': ['#f59e0b', '#8b5cf6'],
                    'borderRadius': 8,
                }]
            },
            'units': ['g', 'mg'],
        }

        return {
            'macro_chart': macro_chart,
            'dv_chart': dv_chart,
            'items_chart': items_chart,
            'compare_chart': compare_chart,
        }
