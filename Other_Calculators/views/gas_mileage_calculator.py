from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GasMileageCalculator(View):
    """
    Gas Mileage Calculator — MPG, distance, fuel needed, trip cost.

    Calc types
        • mpg          → MPG from distance + fuel used
        • distance     → distance from MPG + fuel used
        • fuel_needed  → fuel from distance + MPG
        • cost         → trip cost from distance + MPG + price

    Conversion constants
        1 km = 0.621371 mi   |  1 L = 0.264172 gal
        1 $/L = 3.78541 $/gal
    """
    template_name = 'other_calculators/gas_mileage_calculator.html'

    DIST = {'miles': 1.0, 'km': 0.621371}
    FUEL = {'gallons': 1.0, 'liters': 0.264172}
    PRICE = {'per_gallon': 1.0, 'per_liter': 3.78541}

    LBL = {
        'miles': 'miles', 'km': 'km',
        'gallons': 'gallons', 'liters': 'liters',
        'per_gallon': '/gal', 'per_liter': '/L',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Gas Mileage Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'mpg')
            dispatch = {
                'mpg':         self._calc_mpg,
                'distance':    self._calc_distance,
                'fuel_needed': self._calc_fuel_needed,
                'cost':        self._calc_cost,
            }
            handler = dispatch.get(ct)
            if not handler:
                return self._err(_('Invalid calculation type.'))
            return handler(data)
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(e))
        except Exception:
            return self._err(_('An error occurred during calculation.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    def _f(self, v, dp=2):
        return f'{v:,.{dp}f}'

    def _lbl(self, u):
        return self.LBL.get(u, u)

    def _req_pos(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        f = float(v)
        if f <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        return f

    def _req_nn(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        f = float(v)
        if f < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        return f

    def _safe(self, v):
        if math.isinf(v) or math.isnan(v):
            raise ValueError(str(_('Invalid calculation result.')))
        return v

    # ── efficiency rating helper ─────────────────────────────────────
    @staticmethod
    def _mpg_rating(mpg):
        if mpg >= 45:
            return str(_('Excellent')), str(_('Outstanding fuel economy — hybrid / economy class.'))
        elif mpg >= 30:
            return str(_('Good')), str(_('Good fuel economy — compact / mid-size class.'))
        elif mpg >= 20:
            return str(_('Average')), str(_('Average fuel economy — SUV / sedan class.'))
        elif mpg >= 15:
            return str(_('Below Average')), str(_('Below average — large SUV / truck class.'))
        else:
            return str(_('Poor')), str(_('Poor fuel economy — heavy-duty / performance class.'))

    # ── 1) MPG ────────────────────────────────────────────────────────
    def _calc_mpg(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        fuel = self._req_pos(d, 'fuel_used', str(_('Fuel Used')))
        du = d.get('distance_unit', 'miles')
        fu = d.get('fuel_unit', 'gallons')

        dist_mi = dist * self.DIST.get(du, 1)
        fuel_gal = fuel * self.FUEL.get(fu, 1)
        mpg = self._safe(dist_mi / fuel_gal)
        l100 = 235.214 / mpg
        rating, rating_desc = self._mpg_rating(mpg)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist)} {self._lbl(du)}',
            f'  • {_("Fuel Used")} = {self._f(fuel)} {self._lbl(fu)}',
        ]
        if du != 'miles' or fu != 'gallons':
            steps += ['', str(_('Step 2: Convert to miles and gallons'))]
            if du != 'miles':
                steps.append(f'  {_("Distance")} = {self._f(dist_mi)} miles')
            if fu != 'gallons':
                steps.append(f'  {_("Fuel")} = {self._f(fuel_gal)} gallons')
        steps += [
            '', str(_('Step 3: Calculate MPG')),
            f'  MPG = {_("Distance")} / {_("Fuel")}',
            f'  MPG = {self._f(dist_mi)} / {self._f(fuel_gal)} = {self._f(mpg)}',
            '', str(_('Step 4: Equivalent in metric')),
            f'  L/100 km = 235.214 / {self._f(mpg)} = {self._f(l100)}',
            '', str(_('Step 5: Efficiency rating')),
            f'  • {rating} — {rating_desc}',
        ]

        chart = self._bar(
            [str(_('Distance (mi)')), str(_('Fuel (gal)')), str(_('MPG'))],
            [dist_mi, fuel_gal, mpg],
            str(_('Gas Mileage Breakdown')))

        return JsonResponse({
            'success': True, 'calc_type': 'mpg',
            'result': round(mpg, 2),
            'result_label': str(_('Gas Mileage (MPG)')),
            'result_unit_symbol': 'MPG',
            'formula': f'{self._f(dist_mi)} mi ÷ {self._f(fuel_gal)} gal = {self._f(mpg)} MPG',
            'rating': rating, 'rating_desc': rating_desc,
            'l100': round(l100, 2),
            'step_by_step': steps,
            'chart_data': {'gm_chart': chart},
        })

    # ── 2) DISTANCE ──────────────────────────────────────────────────
    def _calc_distance(self, d):
        mpg = self._req_pos(d, 'mpg', 'MPG')
        fuel = self._req_pos(d, 'fuel_used', str(_('Fuel Used')))
        fu = d.get('fuel_unit', 'gallons')
        ru = d.get('result_unit', 'miles')

        fuel_gal = fuel * self.FUEL.get(fu, 1)
        dist_mi = self._safe(mpg * fuel_gal)
        result = dist_mi if ru == 'miles' else dist_mi / self.DIST['km']

        steps = [
            str(_('Step 1: Given values')),
            f'  • MPG = {self._f(mpg)}',
            f'  • {_("Fuel Used")} = {self._f(fuel)} {self._lbl(fu)}',
        ]
        if fu != 'gallons':
            steps += ['', str(_('Step 2: Convert fuel to gallons')),
                       f'  {_("Fuel")} = {self._f(fuel_gal)} gallons']
        steps += [
            '', str(_('Step 3: Calculate distance')),
            f'  {_("Distance")} = MPG × {_("Fuel")} = {self._f(mpg)} × {self._f(fuel_gal)} = {self._f(dist_mi)} miles',
        ]
        if ru != 'miles':
            steps += ['', str(_('Step 4: Convert to km')),
                       f'  {_("Distance")} = {self._f(result)} km']

        chart = self._bar(
            ['MPG', str(_('Fuel (gal)')), str(_('Distance (mi)'))],
            [mpg, fuel_gal, dist_mi],
            str(_('Distance Calculation')))

        return JsonResponse({
            'success': True, 'calc_type': 'distance',
            'result': round(result, 2),
            'result_label': str(_('Distance')),
            'result_unit_symbol': self._lbl(ru),
            'formula': f'{self._f(mpg)} MPG × {self._f(fuel_gal)} gal = {self._f(result)} {self._lbl(ru)}',
            'step_by_step': steps,
            'chart_data': {'gm_chart': chart},
        })

    # ── 3) FUEL NEEDED ───────────────────────────────────────────────
    def _calc_fuel_needed(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        mpg = self._req_pos(d, 'mpg', 'MPG')
        du = d.get('distance_unit', 'miles')
        ru = d.get('result_unit', 'gallons')

        dist_mi = dist * self.DIST.get(du, 1)
        fuel_gal = self._safe(dist_mi / mpg)
        result = fuel_gal if ru == 'gallons' else fuel_gal / self.FUEL['liters']

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist)} {self._lbl(du)}',
            f'  • MPG = {self._f(mpg)}',
        ]
        if du != 'miles':
            steps += ['', str(_('Step 2: Convert distance to miles')),
                       f'  {_("Distance")} = {self._f(dist_mi)} miles']
        steps += [
            '', str(_('Step 3: Calculate fuel needed')),
            f'  {_("Fuel")} = {_("Distance")} / MPG = {self._f(dist_mi)} / {self._f(mpg)} = {self._f(fuel_gal)} gallons',
        ]
        if ru != 'gallons':
            steps += ['', str(_('Step 4: Convert to liters')),
                       f'  {_("Fuel")} = {self._f(result)} liters']

        chart = self._bar(
            [str(_('Distance (mi)')), 'MPG', str(_('Fuel Needed (gal)'))],
            [dist_mi, mpg, fuel_gal],
            str(_('Fuel Needed Calculation')))

        return JsonResponse({
            'success': True, 'calc_type': 'fuel_needed',
            'result': round(result, 2),
            'result_label': str(_('Fuel Needed')),
            'result_unit_symbol': self._lbl(ru),
            'formula': f'{self._f(dist_mi)} mi ÷ {self._f(mpg)} MPG = {self._f(result)} {self._lbl(ru)}',
            'step_by_step': steps,
            'chart_data': {'gm_chart': chart},
        })

    # ── 4) TRIP COST ─────────────────────────────────────────────────
    def _calc_cost(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        mpg = self._req_pos(d, 'mpg', 'MPG')
        price = self._req_nn(d, 'fuel_price', str(_('Fuel Price')))
        du = d.get('distance_unit', 'miles')
        pu = d.get('price_unit', 'per_gallon')

        dist_mi = dist * self.DIST.get(du, 1)
        ppg = price * self.PRICE.get(pu, 1)
        fuel_gal = self._safe(dist_mi / mpg)
        cost = self._safe(fuel_gal * ppg)
        cpm = cost / dist_mi if dist_mi > 0 else 0

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist)} {self._lbl(du)}',
            f'  • MPG = {self._f(mpg)}',
            f'  • {_("Fuel Price")} = ${self._f(price)} {self._lbl(pu)}',
        ]
        if du != 'miles' or pu != 'per_gallon':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if du != 'miles':
                steps.append(f'  {_("Distance")} = {self._f(dist_mi)} miles')
            if pu != 'per_gallon':
                steps.append(f'  {_("Price")} = ${self._f(ppg)} /gal')
        steps += [
            '', str(_('Step 3: Calculate fuel needed')),
            f'  {_("Fuel")} = {self._f(dist_mi)} / {self._f(mpg)} = {self._f(fuel_gal)} gal',
            '', str(_('Step 4: Calculate total cost')),
            f'  {_("Cost")} = {self._f(fuel_gal)} gal × ${self._f(ppg)} /gal = ${self._f(cost)}',
            '', str(_('Step 5: Cost per mile')),
            f'  $/mile = ${self._f(cost)} / {self._f(dist_mi)} = ${self._f(cpm, 4)}',
        ]

        chart = self._bar(
            [str(_('Distance (mi)')), str(_('Fuel (gal)')), str(_('Cost ($)'))],
            [dist_mi, fuel_gal, cost],
            str(_('Trip Cost Breakdown')))

        return JsonResponse({
            'success': True, 'calc_type': 'cost',
            'result': round(cost, 2),
            'result_label': str(_('Total Trip Cost')),
            'result_unit_symbol': '$',
            'formula': f'${self._f(cost)} ({self._f(fuel_gal)} gal × ${self._f(ppg)}/gal)',
            'cost_per_mile': round(cpm, 4),
            'fuel_needed_gal': round(fuel_gal, 2),
            'step_by_step': steps,
            'chart_data': {'gm_chart': chart},
        })

    # ── chart helper ─────────────────────────────────────────────────
    def _bar(self, labels, data, title):
        colors = ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)']
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Value')),
                    'data': [round(v, 2) for v in data],
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.8', '1') for c in colors],
                    'borderWidth': 2,
                    'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': title}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }
