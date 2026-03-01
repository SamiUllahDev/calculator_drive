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
class FuelCostCalculator(View):
    """
    Fuel Cost Calculator — Trip cost, efficiency, distance, fuel needed.

    Calc types
        • total_cost        → total $ from distance + efficiency + price
        • cost_per_distance → $/mile or $/km from efficiency + price
        • fuel_efficiency   → MPG or L/100km from distance + fuel used
        • distance          → distance from fuel used + efficiency
        • fuel_needed       → fuel needed from distance + efficiency
        • convert_distance  → miles ↔ km
        • convert_fuel      → gallons ↔ liters

    Conversion constants
        1 km   = 0.621371 mi
        1 L    = 0.264172 gal
        MPG    = 235.214 / (L/100km)
        1 $/L  = 3.78541 $/gal
    """
    template_name = 'other_calculators/fuel_cost_calculator.html'

    # conversion factors → base units (miles, gallons)
    DIST = {'miles': 1.0, 'km': 0.621371}
    FUEL = {'gallons': 1.0, 'liters': 0.264172}
    PRICE = {'per_gallon': 1.0, 'per_liter': 3.78541}

    UNIT_LABEL = {
        'miles': 'miles', 'km': 'km',
        'gallons': 'gallons', 'liters': 'liters',
        'mpg': 'MPG', 'l_per_100km': 'L/100 km',
        'per_gallon': '/gal', 'per_liter': '/L',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Fuel Cost Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'total_cost')
            dispatch = {
                'total_cost':        self._calc_total_cost,
                'cost_per_distance': self._calc_cost_per_dist,
                'fuel_efficiency':   self._calc_efficiency,
                'distance':          self._calc_distance,
                'fuel_needed':       self._calc_fuel_needed,
                'convert_distance':  self._calc_convert_dist,
                'convert_fuel':      self._calc_convert_fuel,
            }
            handler = dispatch.get(calc)
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

    def _fnum(self, v, dp=2):
        if v is None:
            return '0'
        return f'{v:,.{dp}f}'

    def _lbl(self, u):
        return self.UNIT_LABEL.get(u, u)

    def _req(self, d, key, name):
        v = d.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        f = float(v)
        return f

    def _req_pos(self, d, key, name):
        v = self._req(d, key, name)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        return v

    def _req_nn(self, d, key, name):
        v = self._req(d, key, name)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        return v

    def _to_mpg(self, eff, unit):
        if unit == 'l_per_100km':
            return 235.214 / eff
        return eff

    def _safe(self, v):
        if math.isinf(v) or math.isnan(v):
            raise ValueError(str(_('Invalid calculation result.')))
        return v

    # ── 1) TOTAL COST ────────────────────────────────────────────────
    def _calc_total_cost(self, d):
        dist = self._req_nn(d, 'distance', str(_('Distance')))
        eff = self._req_pos(d, 'fuel_efficiency', str(_('Fuel Efficiency')))
        price = self._req_nn(d, 'fuel_price', str(_('Fuel Price')))
        du = d.get('distance_unit', 'miles')
        eu = d.get('efficiency_unit', 'mpg')
        pu = d.get('price_unit', 'per_gallon')

        dist_mi = dist * self.DIST.get(du, 1)
        mpg = self._to_mpg(eff, eu)
        fuel_gal = self._safe(dist_mi / mpg)
        ppg = price * self.PRICE.get(pu, 1)
        cost = self._safe(fuel_gal * ppg)
        fuel_L = fuel_gal / self.FUEL['liters']

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._fnum(dist)} {self._lbl(du)}',
            f'  • {_("Fuel Efficiency")} = {self._fnum(eff)} {self._lbl(eu)}',
            f'  • {_("Fuel Price")} = ${self._fnum(price)} {self._lbl(pu)}',
        ]
        steps += ['', str(_('Step 2: Convert to base units (miles, gallons, $/gal)'))]
        if du != 'miles':
            steps.append(f'  {_("Distance")} = {self._fnum(dist_mi)} miles')
        if eu != 'mpg':
            steps.append(f'  MPG = 235.214 / {self._fnum(eff)} = {self._fnum(mpg)} MPG')
        if pu != 'per_gallon':
            steps.append(f'  {_("Price")} = ${self._fnum(ppg)} /gal')
        steps += [
            '', str(_('Step 3: Calculate fuel needed')),
            f'  {_("Fuel")} = {_("Distance")} / {_("Efficiency")}',
            f'  {_("Fuel")} = {self._fnum(dist_mi)} / {self._fnum(mpg)} = {self._fnum(fuel_gal)} gal ({self._fnum(fuel_L)} L)',
            '', str(_('Step 4: Calculate total cost')),
            f'  {_("Cost")} = {_("Fuel")} × {_("Price")}',
            f'  {_("Cost")} = {self._fnum(fuel_gal)} × ${self._fnum(ppg)} = ${self._fnum(cost)}',
        ]

        chart = self._bar([str(_('Distance (mi)')), str(_('Fuel (gal)')), str(_('Cost ($)'))],
                          [dist_mi, fuel_gal, cost],
                          ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
                          str(_('Fuel Cost Breakdown')))

        return JsonResponse({
            'success': True, 'calc_type': 'total_cost',
            'result': round(cost, 2),
            'result_label': str(_('Total Fuel Cost')),
            'result_unit_symbol': '$',
            'fuel_needed_gal': round(fuel_gal, 2),
            'fuel_needed_L': round(fuel_L, 2),
            'formula': f'${self._fnum(cost)}',
            'step_by_step': steps,
            'chart_data': {'fc_chart': chart},
        })

    # ── 2) COST PER DISTANCE ────────────────────────────────────────
    def _calc_cost_per_dist(self, d):
        eff = self._req_pos(d, 'fuel_efficiency', str(_('Fuel Efficiency')))
        price = self._req_nn(d, 'fuel_price', str(_('Fuel Price')))
        eu = d.get('efficiency_unit', 'mpg')
        pu = d.get('price_unit', 'per_gallon')
        ru = d.get('result_unit', 'miles')

        mpg = self._to_mpg(eff, eu)
        ppg = price * self.PRICE.get(pu, 1)
        cpm = self._safe(ppg / mpg)  # $/mile
        result = cpm if ru == 'miles' else cpm / self.DIST['km']

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Fuel Efficiency")} = {self._fnum(eff)} {self._lbl(eu)}',
            f'  • {_("Fuel Price")} = ${self._fnum(price)} {self._lbl(pu)}',
            '', str(_('Step 2: Convert to base units')),
        ]
        if eu != 'mpg':
            steps.append(f'  MPG = {self._fnum(mpg)}')
        if pu != 'per_gallon':
            steps.append(f'  {_("Price")} = ${self._fnum(ppg)} /gal')
        steps += [
            '', str(_('Step 3: Cost per mile')),
            f'  $/mile = {_("Price")} / MPG = ${self._fnum(ppg)} / {self._fnum(mpg)} = ${self._fnum(cpm)}',
        ]
        if ru != 'miles':
            steps += [
                '', str(_('Step 4: Convert to $/km')),
                f'  $/km = ${self._fnum(result)}',
            ]

        return JsonResponse({
            'success': True, 'calc_type': 'cost_per_distance',
            'result': round(result, 4),
            'result_label': str(_('Cost Per Distance')),
            'result_unit_symbol': f'$/{self._lbl(ru)}',
            'formula': f'${self._fnum(result, 4)} / {self._lbl(ru)}',
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── 3) FUEL EFFICIENCY ───────────────────────────────────────────
    def _calc_efficiency(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        fuel = self._req_pos(d, 'fuel_used', str(_('Fuel Used')))
        du = d.get('distance_unit', 'miles')
        fu = d.get('fuel_unit', 'gallons')
        ru = d.get('result_unit', 'mpg')

        dist_mi = dist * self.DIST.get(du, 1)
        fuel_gal = fuel * self.FUEL.get(fu, 1)
        mpg = self._safe(dist_mi / fuel_gal)
        result = mpg if ru == 'mpg' else 235.214 / mpg

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._fnum(dist)} {self._lbl(du)}',
            f'  • {_("Fuel Used")} = {self._fnum(fuel)} {self._lbl(fu)}',
        ]
        if du != 'miles' or fu != 'gallons':
            steps += ['', str(_('Step 2: Convert to miles and gallons'))]
            if du != 'miles':
                steps.append(f'  {_("Distance")} = {self._fnum(dist_mi)} miles')
            if fu != 'gallons':
                steps.append(f'  {_("Fuel")} = {self._fnum(fuel_gal)} gallons')
        steps += [
            '', str(_('Step 3: Calculate MPG')),
            f'  MPG = {_("Distance")} / {_("Fuel")} = {self._fnum(dist_mi)} / {self._fnum(fuel_gal)} = {self._fnum(mpg)}',
        ]
        if ru != 'mpg':
            steps += [
                '', str(_('Step 4: Convert to L/100 km')),
                f'  L/100 km = 235.214 / {self._fnum(mpg)} = {self._fnum(result)}',
            ]

        chart = self._bar([str(_('Distance (mi)')), str(_('Fuel (gal)')), str(_('Efficiency'))],
                          [dist_mi, fuel_gal, result],
                          ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
                          str(_('Fuel Efficiency Breakdown')))

        return JsonResponse({
            'success': True, 'calc_type': 'fuel_efficiency',
            'result': round(result, 2),
            'result_label': str(_('Fuel Efficiency')),
            'result_unit_symbol': self._lbl(ru),
            'formula': f'{self._fnum(result)} {self._lbl(ru)}',
            'step_by_step': steps,
            'chart_data': {'fc_chart': chart},
        })

    # ── 4) DISTANCE ──────────────────────────────────────────────────
    def _calc_distance(self, d):
        fuel = self._req_pos(d, 'fuel_used', str(_('Fuel Used')))
        eff = self._req_pos(d, 'fuel_efficiency', str(_('Fuel Efficiency')))
        fu = d.get('fuel_unit', 'gallons')
        eu = d.get('efficiency_unit', 'mpg')
        ru = d.get('result_unit', 'miles')

        fuel_gal = fuel * self.FUEL.get(fu, 1)
        mpg = self._to_mpg(eff, eu)
        dist_mi = self._safe(fuel_gal * mpg)
        result = dist_mi if ru == 'miles' else dist_mi / self.DIST['km']

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Fuel Used")} = {self._fnum(fuel)} {self._lbl(fu)}',
            f'  • {_("Fuel Efficiency")} = {self._fnum(eff)} {self._lbl(eu)}',
        ]
        if fu != 'gallons' or eu != 'mpg':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if fu != 'gallons':
                steps.append(f'  {_("Fuel")} = {self._fnum(fuel_gal)} gallons')
            if eu != 'mpg':
                steps.append(f'  MPG = {self._fnum(mpg)}')
        steps += [
            '', str(_('Step 3: Calculate distance')),
            f'  {_("Distance")} = {_("Fuel")} × {_("Efficiency")} = {self._fnum(fuel_gal)} × {self._fnum(mpg)} = {self._fnum(dist_mi)} miles',
        ]
        if ru != 'miles':
            steps += [
                '', str(_('Step 4: Convert to km')),
                f'  {_("Distance")} = {self._fnum(result)} km',
            ]

        chart = self._bar([str(_('Fuel (gal)')), str(_('Efficiency (MPG)')), str(_('Distance (mi)'))],
                          [fuel_gal, mpg, dist_mi],
                          ['rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)', 'rgba(59,130,246,0.8)'],
                          str(_('Distance Calculation')))

        return JsonResponse({
            'success': True, 'calc_type': 'distance',
            'result': round(result, 2),
            'result_label': str(_('Distance')),
            'result_unit_symbol': self._lbl(ru),
            'formula': f'{self._fnum(result)} {self._lbl(ru)}',
            'step_by_step': steps,
            'chart_data': {'fc_chart': chart},
        })

    # ── 5) FUEL NEEDED ───────────────────────────────────────────────
    def _calc_fuel_needed(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        eff = self._req_pos(d, 'fuel_efficiency', str(_('Fuel Efficiency')))
        du = d.get('distance_unit', 'miles')
        eu = d.get('efficiency_unit', 'mpg')
        ru = d.get('result_unit', 'gallons')

        dist_mi = dist * self.DIST.get(du, 1)
        mpg = self._to_mpg(eff, eu)
        fuel_gal = self._safe(dist_mi / mpg)
        result = fuel_gal if ru == 'gallons' else fuel_gal / self.FUEL['liters']

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._fnum(dist)} {self._lbl(du)}',
            f'  • {_("Fuel Efficiency")} = {self._fnum(eff)} {self._lbl(eu)}',
        ]
        if du != 'miles' or eu != 'mpg':
            steps += ['', str(_('Step 2: Convert to base units'))]
            if du != 'miles':
                steps.append(f'  {_("Distance")} = {self._fnum(dist_mi)} miles')
            if eu != 'mpg':
                steps.append(f'  MPG = {self._fnum(mpg)}')
        steps += [
            '', str(_('Step 3: Calculate fuel needed')),
            f'  {_("Fuel")} = {_("Distance")} / {_("Efficiency")} = {self._fnum(dist_mi)} / {self._fnum(mpg)} = {self._fnum(fuel_gal)} gal',
        ]
        if ru != 'gallons':
            steps += [
                '', str(_('Step 4: Convert to liters')),
                f'  {_("Fuel")} = {self._fnum(result)} L',
            ]

        chart = self._bar([str(_('Distance (mi)')), str(_('Efficiency (MPG)')), str(_('Fuel Needed'))],
                          [dist_mi, mpg, fuel_gal],
                          ['rgba(59,130,246,0.8)', 'rgba(251,191,36,0.8)', 'rgba(16,185,129,0.8)'],
                          str(_('Fuel Needed Calculation')))

        return JsonResponse({
            'success': True, 'calc_type': 'fuel_needed',
            'result': round(result, 2),
            'result_label': str(_('Fuel Needed')),
            'result_unit_symbol': self._lbl(ru),
            'formula': f'{self._fnum(result)} {self._lbl(ru)}',
            'step_by_step': steps,
            'chart_data': {'fc_chart': chart},
        })

    # ── 6) CONVERT DISTANCE ──────────────────────────────────────────
    def _calc_convert_dist(self, d):
        val = self._req_nn(d, 'value', str(_('Distance')))
        fu = d.get('from_unit', 'miles')
        tu = d.get('to_unit', 'km')
        mi = val * self.DIST.get(fu, 1)
        result = mi / self.DIST.get(tu, 1)

        steps = [
            str(_('Step 1: Given value')),
            f'  • {self._fnum(val)} {self._lbl(fu)}',
            '', str(_('Step 2: Convert')),
            f'  = {self._fnum(result)} {self._lbl(tu)}',
        ]
        return JsonResponse({
            'success': True, 'calc_type': 'convert_distance',
            'result': round(result, 4),
            'result_label': str(_('Converted Distance')),
            'result_unit_symbol': self._lbl(tu),
            'formula': f'{self._fnum(val)} {self._lbl(fu)} = {self._fnum(result)} {self._lbl(tu)}',
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── 7) CONVERT FUEL ──────────────────────────────────────────────
    def _calc_convert_fuel(self, d):
        val = self._req_nn(d, 'value', str(_('Fuel Volume')))
        fu = d.get('from_unit', 'gallons')
        tu = d.get('to_unit', 'liters')
        gal = val * self.FUEL.get(fu, 1)
        result = gal / self.FUEL.get(tu, 1)

        steps = [
            str(_('Step 1: Given value')),
            f'  • {self._fnum(val)} {self._lbl(fu)}',
            '', str(_('Step 2: Convert')),
            f'  = {self._fnum(result)} {self._lbl(tu)}',
        ]
        return JsonResponse({
            'success': True, 'calc_type': 'convert_fuel',
            'result': round(result, 4),
            'result_label': str(_('Converted Fuel Volume')),
            'result_unit_symbol': self._lbl(tu),
            'formula': f'{self._fnum(val)} {self._lbl(fu)} = {self._fnum(result)} {self._lbl(tu)}',
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── chart helper ─────────────────────────────────────────────────
    def _bar(self, labels, data, colors, title):
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
