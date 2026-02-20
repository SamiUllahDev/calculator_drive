from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ScheduleOneCalculator(View):
    """
    Schedule 1 Game Mix Calculator.

    Calculate drug-mix profits, optimal ingredient combos, and
    selling-price multipliers for the game "Schedule I".

    Features:
    - Complete product + ingredient database
    - Effect stacking with price multipliers
    - NumPy cost / profit / margin calculations
    - Backend-driven Chart.js configs
    """
    template_name = 'other_calculators/schedule_one_calculator.html'

    # ─── BASE PRODUCTS ────────────────────────────────────────────
    # (base_price, cost, category)
    PRODUCTS = {
        'og_kush':          {'name': 'OG Kush',           'base_price': 38,  'cost': 30,  'category': 'Weed'},
        'sour_diesel':      {'name': 'Sour Diesel',       'base_price': 40,  'cost': 32,  'category': 'Weed'},
        'green_crack':      {'name': 'Green Crack',       'base_price': 35,  'cost': 28,  'category': 'Weed'},
        'granddaddy_purple':{'name': 'Granddaddy Purple', 'base_price': 44,  'cost': 35,  'category': 'Weed'},
        'blue_dream':       {'name': 'Blue Dream',        'base_price': 42,  'cost': 33,  'category': 'Weed'},
        'meth':             {'name': 'Meth',              'base_price': 70,  'cost': 25,  'category': 'Meth'},
        'cocaine':          {'name': 'Cocaine',           'base_price': 150, 'cost': 60,  'category': 'Cocaine'},
    }

    # ─── MIX INGREDIENTS ──────────────────────────────────────────
    # Each ingredient has a cost and one or more effects it can trigger.
    # The effect and multiplier depend on which product it's mixed with.
    INGREDIENTS = {
        'cuke':          {'name': 'Cuke',          'cost': 2,  'effect': 'Euphoric',          'multiplier': 0.18},
        'flu_medicine':  {'name': 'Flu Medicine',  'cost': 3,  'effect': 'Sedating',          'multiplier': 0.14},
        'gasoline':      {'name': 'Gasoline',      'cost': 5,  'effect': 'Toxic',             'multiplier': 0.12},
        'donut':         {'name': 'Donut',         'cost': 1,  'effect': 'Calming',           'multiplier': 0.10},
        'energy_drink':  {'name': 'Energy Drink',  'cost': 4,  'effect': 'Athletic',          'multiplier': 0.22},
        'mouth_wash':    {'name': 'Mouth Wash',    'cost': 2,  'effect': 'Balding',           'multiplier': 0.08},
        'motor_oil':     {'name': 'Motor Oil',     'cost': 6,  'effect': 'Slippery',          'multiplier': 0.12},
        'banana':        {'name': 'Banana',        'cost': 1,  'effect': 'Gingeritis',        'multiplier': 0.08},
        'chili':         {'name': 'Chili',         'cost': 2,  'effect': 'Spicy',             'multiplier': 0.14},
        'iodine':        {'name': 'Iodine',        'cost': 4,  'effect': 'Jennerising',       'multiplier': 0.12},
        'paracetamol':   {'name': 'Paracetamol',   'cost': 3,  'effect': 'Sneaky',            'multiplier': 0.16},
        'viagra':        {'name': 'Viagra',        'cost': 8,  'effect': 'Tropic Thunder',    'multiplier': 0.20},
        'horse_semen':   {'name': 'Horse Semen',   'cost': 5,  'effect': 'Zombifying',        'multiplier': 0.14},
        'mega_bean':     {'name': 'Mega Bean',     'cost': 3,  'effect': 'Foggy',             'multiplier': 0.10},
        'addy':          {'name': 'Addy',          'cost': 7,  'effect': 'Thought-Provoking', 'multiplier': 0.22},
        'battery':       {'name': 'Battery',       'cost': 6,  'effect': 'Bright-Eyed',       'multiplier': 0.18},
    }

    def get(self, request):
        products_list = [{'key': k, **v} for k, v in self.PRODUCTS.items()]
        ingredients_list = [{'key': k, **v} for k, v in self.INGREDIENTS.items()]
        context = {
            'calculator_name': _('Schedule 1 Calculator'),
            'page_title': _('Schedule 1 Mix Calculator - Maximize Your Profits'),
            'products': products_list,
            'ingredients': ingredients_list,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)
            product_key = data.get('product', '')
            ingredient_keys = data.get('ingredients', [])
            quantity = int(data.get('quantity', 1))
            quantity = max(1, min(quantity, 100))

            product = self.PRODUCTS.get(product_key)
            if not product:
                return JsonResponse({'success': False, 'error': str(_('Please select a product.'))}, status=400)

            # ── Gather ingredients ───────────────────────────────
            selected_ingredients = []
            for ik in ingredient_keys:
                ing = self.INGREDIENTS.get(ik)
                if ing:
                    selected_ingredients.append({'key': ik, **ing})

            # ── NumPy Calculations ───────────────────────────────
            base_price = float(product['base_price'])
            product_cost = float(product['cost'])

            # Effect multipliers
            if selected_ingredients:
                multipliers = np.array([ing['multiplier'] for ing in selected_ingredients], dtype=np.float64)
                ingredient_costs = np.array([ing['cost'] for ing in selected_ingredients], dtype=np.float64)
                total_multiplier = float(np.sum(multipliers))
                total_ingredient_cost = float(np.sum(ingredient_costs))
            else:
                multipliers = np.array([], dtype=np.float64)
                ingredient_costs = np.array([], dtype=np.float64)
                total_multiplier = 0.0
                total_ingredient_cost = 0.0

            # Final selling price per unit
            sell_price_per_unit = base_price * (1.0 + total_multiplier)
            cost_per_unit = product_cost + total_ingredient_cost
            profit_per_unit = sell_price_per_unit - cost_per_unit
            margin_pct = (profit_per_unit / sell_price_per_unit * 100) if sell_price_per_unit > 0 else 0

            # Batch totals
            total_revenue = sell_price_per_unit * quantity
            total_cost = cost_per_unit * quantity
            total_profit = profit_per_unit * quantity

            # Effects list
            effects = [ing['effect'] for ing in selected_ingredients]

            # ── Compute rating ───────────────────────────────────
            rating = self._compute_rating(margin_pct, total_multiplier, sell_price_per_unit, len(selected_ingredients))

            # ── Ingredient breakdown ─────────────────────────────
            breakdown = []
            for ing in selected_ingredients:
                contribution = base_price * ing['multiplier']
                breakdown.append({
                    'name': ing['name'],
                    'effect': ing['effect'],
                    'cost': ing['cost'],
                    'multiplier': f"+{int(ing['multiplier'] * 100)}%",
                    'price_added': round(contribution, 2),
                })

            # ── Chart data ───────────────────────────────────────
            chart_data = self._prepare_chart_data(
                product, selected_ingredients, base_price, sell_price_per_unit,
                cost_per_unit, profit_per_unit, total_multiplier, rating
            )

            return JsonResponse({
                'success': True,
                'product_name': product['name'],
                'product_category': product['category'],
                'effects': effects,
                'per_unit': {
                    'sell_price': round(sell_price_per_unit, 2),
                    'cost': round(cost_per_unit, 2),
                    'profit': round(profit_per_unit, 2),
                    'margin': round(margin_pct, 1),
                    'multiplier': f"+{int(total_multiplier * 100)}%",
                },
                'batch': {
                    'quantity': quantity,
                    'revenue': round(total_revenue, 2),
                    'cost': round(total_cost, 2),
                    'profit': round(total_profit, 2),
                },
                'breakdown': breakdown,
                'rating': rating,
                'chart_data': chart_data,
                'color_info': self._get_color_info(rating['color']),
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    def _compute_rating(self, margin, multiplier, sell_price, n_ingredients):
        score = 50.0
        # Margin bonus
        if margin >= 70:
            score += 25
        elif margin >= 50:
            score += 15
        elif margin >= 30:
            score += 5
        else:
            score -= 10
        # Multiplier bonus
        score += min(multiplier * 30, 25)
        # Selling price bonus
        if sell_price >= 200:
            score += 10
        elif sell_price >= 100:
            score += 5
        # Efficiency (not too many ingredients)
        if n_ingredients <= 3 and multiplier > 0.3:
            score += 5

        score = float(np.clip(score, 0, 100))

        if score >= 85:
            return {'score': round(score), 'label': str(_('S-Tier')), 'emoji': '🔥', 'color': 'green',
                    'description': str(_('This is an elite mix. Maximum profit with great effects!'))}
        elif score >= 70:
            return {'score': round(score), 'label': str(_('A-Tier')), 'emoji': '💰', 'color': 'blue',
                    'description': str(_('Solid recipe. Good margins and effects.'))}
        elif score >= 55:
            return {'score': round(score), 'label': str(_('B-Tier')), 'emoji': '👍', 'color': 'yellow',
                    'description': str(_('Decent mix. Consider optimising ingredients for better margins.'))}
        elif score >= 40:
            return {'score': round(score), 'label': str(_('C-Tier')), 'emoji': '😐', 'color': 'orange',
                    'description': str(_('Below average. The ingredient costs are eating into your profits.'))}
        else:
            return {'score': round(score), 'label': str(_('D-Tier')), 'emoji': '💀', 'color': 'red',
                    'description': str(_('Poor recipe. You might be losing money or barely breaking even.'))}

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
    def _prepare_chart_data(self, product, ingredients, base_price, sell_price,
                            cost_per_unit, profit_per_unit, total_multiplier, rating):
        ci = self._get_color_info(rating['color'])

        # 1. Profit breakdown doughnut
        product_cost = product['cost']
        ing_cost = cost_per_unit - product_cost
        profit_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Product Cost')), str(_('Ingredient Cost')), str(_('Profit'))],
                'datasets': [{
                    'data': [round(product_cost, 2), round(max(ing_cost, 0), 2), round(max(profit_per_unit, 0), 2)],
                    'backgroundColor': ['#ef4444', '#f59e0b', '#10b981'],
                    'borderWidth': 2,
                    'borderColor': '#fff',
                }]
            },
            'center_text': {
                'value': f'${round(sell_price)}',
                'label': str(_('Sell Price')),
                'color': ci['hex'],
            }
        }

        # 2. Effect contribution bar (how much each ingredient adds to price)
        if ingredients:
            ing_names = [ing['name'] for ing in ingredients]
            ing_contributions = [round(base_price * ing['multiplier'], 2) for ing in ingredients]
            ing_colors = ['#8b5cf6' if c >= 10 else '#6366f1' if c >= 5 else '#a78bfa' for c in ing_contributions]
        else:
            ing_names = [str(_('No Ingredients'))]
            ing_contributions = [0]
            ing_colors = ['#d1d5db']

        effect_chart = {
            'type': 'bar',
            'data': {
                'labels': ing_names,
                'datasets': [{
                    'label': str(_('Price Added ($)')),
                    'data': ing_contributions,
                    'backgroundColor': ing_colors,
                    'borderRadius': 6,
                }]
            }
        }

        # 3. Price waterfall (base → +effects → sell price)
        price_parts = [base_price]
        labels = [str(_('Base Price'))]
        colors = ['#3b82f6']
        running = base_price
        for ing in ingredients:
            added = base_price * ing['multiplier']
            running += added
            price_parts.append(round(running, 2))
            labels.append(f"+{ing['name']}")
            colors.append('#8b5cf6')
        if ingredients:
            price_parts.append(round(sell_price, 2))
            labels.append(str(_('Final Price')))
            colors.append(ci['hex'])

        waterfall_chart = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Price ($)')),
                    'data': price_parts,
                    'borderColor': ci['hex'],
                    'backgroundColor': ci['hex'] + '33',
                    'borderWidth': 3,
                    'fill': True,
                    'tension': 0.3,
                    'pointBackgroundColor': colors,
                    'pointBorderColor': '#fff',
                    'pointBorderWidth': 2,
                    'pointRadius': 7,
                }]
            }
        }

        return {
            'profit_chart': profit_chart,
            'effect_chart': effect_chart,
            'waterfall_chart': waterfall_chart,
        }
