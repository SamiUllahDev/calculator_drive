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
class MileageCalculator(View):
    """
    Mileage Calculator — reimbursement, trip cost, cost per mile, distance from cost,
    distance conversion, rate comparison.

    Calc types
        • reimbursement      → distance × rate
        • trip_cost          → fuel cost + other costs
        • cost_per_mile      → total cost / distance
        • distance_from_cost → total cost / rate
        • convert_distance   → unit conversion (mi, km, m, ft, yd, nmi)
        • compare_rates      → side-by-side reimbursement for two rates

    Distance base unit = km.
    """
    template_name = 'other_calculators/mileage_calculator.html'

    # to km
    DIST = {
        'miles': 1.60934, 'kilometers': 1.0, 'meters': 0.001,
        'feet': 0.0003048, 'yards': 0.0009144, 'nautical_miles': 1.852,
    }
    DIST_LBL = {
        'miles': 'miles', 'kilometers': 'km', 'meters': 'm',
        'feet': 'ft', 'yards': 'yd', 'nautical_miles': 'nmi',
    }
    CUR_SYM = {'usd': '$', 'eur': '€', 'gbp': '£', 'cad': 'C$', 'aud': 'A$'}

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Mileage Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'reimbursement')
            dispatch = {
                'reimbursement':      self._calc_reimbursement,
                'trip_cost':          self._calc_trip_cost,
                'cost_per_mile':      self._calc_cost_per_mile,
                'distance_from_cost': self._calc_distance_from_cost,
                'convert_distance':   self._calc_convert_distance,
                'compare_rates':      self._calc_compare_rates,
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

    def _dl(self, u):
        return self.DIST_LBL.get(u, u)

    def _cs(self, cur):
        return self.CUR_SYM.get(cur, '$')

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

    def _to_km(self, val, unit):
        return val * self.DIST.get(unit, 1)

    def _km_to(self, km, unit):
        return km / self.DIST.get(unit, 1)

    def _to_miles(self, km):
        return km / self.DIST['miles']

    # ── 1) REIMBURSEMENT ─────────────────────────────────────────────
    def _calc_reimbursement(self, d):
        dist = self._req_nn(d, 'distance', str(_('Distance')))
        rate = self._req_nn(d, 'rate', str(_('Rate')))
        du = d.get('distance_unit', 'miles')
        ru = d.get('rate_unit', 'per_mile')
        cur = d.get('currency', 'usd')
        cs = self._cs(cur)

        dist_km = self._to_km(dist, du)
        if ru == 'per_mile':
            dist_calc = self._to_miles(dist_km)
            unit_lbl = str(_('mile'))
        else:
            dist_calc = dist_km
            unit_lbl = 'km'
        reimb = self._safe(dist_calc * rate)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist)} {self._dl(du)}',
            f'  • {_("Rate")} = {cs}{self._f(rate)} / {unit_lbl}',
        ]
        if (ru == 'per_mile' and du != 'miles') or (ru == 'per_km' and du != 'kilometers'):
            steps += ['', str(_('Step 2: Convert distance')),
                       f'  {_("Distance")} = {self._f(dist_calc)} {unit_lbl}']
        steps += [
            '', str(_('Step 3: Calculate reimbursement')),
            f'  {_("Reimbursement")} = {_("Distance")} × {_("Rate")}',
            f'  {_("Reimbursement")} = {self._f(dist_calc)} × {cs}{self._f(rate)} = {cs}{self._f(reimb)}',
        ]

        chart = self._bar(
            [str(_('Distance')), str(_('Reimbursement'))],
            [dist_calc, reimb],
            ['rgba(59,130,246,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Mileage Reimbursement')))

        return JsonResponse({
            'success': True, 'calc_type': 'reimbursement',
            'result': round(reimb, 2),
            'result_label': str(_('Mileage Reimbursement')),
            'result_unit_symbol': cs,
            'formula': f'{cs}{self._f(reimb)}',
            'step_by_step': steps,
            'chart_data': {'mc_chart': chart},
        })

    # ── 2) TRIP COST ─────────────────────────────────────────────────
    def _calc_trip_cost(self, d):
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        fuel_price = self._req_pos(d, 'fuel_cost', str(_('Fuel Price')))
        eff = self._req_pos(d, 'fuel_efficiency', str(_('Fuel Efficiency')))
        other = float(d.get('other_costs', 0) or 0)
        if other < 0:
            raise ValueError(str(_('Other costs must be non-negative.')))

        du = d.get('distance_unit', 'miles')
        eu = d.get('efficiency_unit', 'mpg')
        fcu = d.get('fuel_cost_unit', 'per_gallon')
        cur = d.get('currency', 'usd')
        cs = self._cs(cur)

        dist_km = self._to_km(dist, du)
        dist_mi = self._to_miles(dist_km)

        # fuel needed
        if eu == 'mpg':
            fuel_gal = dist_mi / eff
            fuel_L = fuel_gal * 3.78541
        elif eu == 'l_per_100km':
            fuel_L = (dist_km / 100) * eff
            fuel_gal = fuel_L / 3.78541
        else:  # km_per_l
            fuel_L = dist_km / eff
            fuel_gal = fuel_L / 3.78541

        fuel_cost = fuel_gal * fuel_price if fcu == 'per_gallon' else fuel_L * fuel_price
        total = self._safe(fuel_cost + other)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist)} {self._dl(du)}',
            f'  • {_("Fuel Efficiency")} = {self._f(eff)} {eu.upper()}',
            f'  • {_("Fuel Price")} = {cs}{self._f(fuel_price)} {"/" + _("gal") if fcu == "per_gallon" else "/" + _("L")}',
        ]
        if other > 0:
            steps.append(f'  • {_("Other Costs")} = {cs}{self._f(other)}')
        steps += [
            '', str(_('Step 2: Calculate fuel needed')),
            f'  {_("Fuel")} ≈ {self._f(fuel_gal)} gal ({self._f(fuel_L)} L)',
            '', str(_('Step 3: Calculate fuel cost')),
            f'  {_("Fuel Cost")} = {cs}{self._f(fuel_cost)}',
            '', str(_('Step 4: Total trip cost')),
            f'  {_("Total")} = {cs}{self._f(fuel_cost)} + {cs}{self._f(other)} = {cs}{self._f(total)}',
        ]

        chart = self._bar(
            [str(_('Fuel Cost')), str(_('Other Costs')), str(_('Total'))],
            [fuel_cost, other, total],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Trip Cost Breakdown')))

        return JsonResponse({
            'success': True, 'calc_type': 'trip_cost',
            'result': round(total, 2),
            'result_label': str(_('Total Trip Cost')),
            'result_unit_symbol': cs,
            'formula': f'{cs}{self._f(total)}',
            'fuel_cost_total': round(fuel_cost, 2),
            'other_costs': round(other, 2),
            'step_by_step': steps,
            'chart_data': {'mc_chart': chart},
        })

    # ── 3) COST PER MILE ─────────────────────────────────────────────
    def _calc_cost_per_mile(self, d):
        cost = self._req_nn(d, 'total_cost', str(_('Total Cost')))
        dist = self._req_pos(d, 'distance', str(_('Distance')))
        du = d.get('distance_unit', 'miles')
        ru = d.get('result_unit', 'per_mile')
        cur = d.get('currency', 'usd')
        cs = self._cs(cur)

        dist_km = self._to_km(dist, du)
        if ru == 'per_mile':
            dist_calc = self._to_miles(dist_km)
            ulbl = str(_('mile'))
        else:
            dist_calc = dist_km
            ulbl = 'km'
        cpm = self._safe(cost / dist_calc)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Total Cost")} = {cs}{self._f(cost)}',
            f'  • {_("Distance")} = {self._f(dist)} {self._dl(du)}',
        ]
        if (ru == 'per_mile' and du != 'miles') or (ru == 'per_km' and du != 'kilometers'):
            steps += ['', str(_('Step 2: Convert distance')),
                       f'  {_("Distance")} = {self._f(dist_calc)} {ulbl}']
        steps += [
            '', str(_('Step 3: Calculate cost per unit')),
            f'  {_("Cost")} / {ulbl} = {cs}{self._f(cost)} / {self._f(dist_calc)} = {cs}{self._f(cpm, 4)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'cost_per_mile',
            'result': round(cpm, 4),
            'result_label': str(_('Cost Per Distance')),
            'result_unit_symbol': f'{cs}/{ulbl}',
            'formula': f'{cs}{self._f(cpm, 4)} / {ulbl}',
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── 4) DISTANCE FROM COST ────────────────────────────────────────
    def _calc_distance_from_cost(self, d):
        cost = self._req_nn(d, 'total_cost', str(_('Total Cost')))
        cpu = self._req_pos(d, 'cost_per_unit', str(_('Cost Per Unit')))
        cu = d.get('cost_unit', 'per_mile')
        ru = d.get('result_unit', 'miles')
        cur = d.get('currency', 'usd')
        cs = self._cs(cur)

        # distance in the cost unit's dimension
        if cu == 'per_mile':
            dist_mi = self._safe(cost / cpu)
            dist_km = dist_mi * self.DIST['miles']
        else:
            dist_km = self._safe(cost / cpu)
            dist_mi = self._to_miles(dist_km)

        result = self._km_to(dist_km, ru) if ru != 'miles' else dist_mi
        if ru == 'kilometers':
            result = dist_km

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Total Cost")} = {cs}{self._f(cost)}',
            f'  • {_("Cost Per Unit")} = {cs}{self._f(cpu)} / {_("mile") if cu == "per_mile" else "km"}',
            '', str(_('Step 2: Calculate distance')),
            f'  {_("Distance")} = {_("Total Cost")} / {_("Cost Per Unit")}',
            f'  {_("Distance")} = {cs}{self._f(cost)} / {cs}{self._f(cpu)} = {self._f(dist_mi)} miles ({self._f(dist_km)} km)',
        ]
        if ru not in ('miles', 'kilometers'):
            steps += ['', str(_('Step 3: Convert to desired unit')),
                       f'  {_("Distance")} = {self._f(result)} {self._dl(ru)}']

        return JsonResponse({
            'success': True, 'calc_type': 'distance_from_cost',
            'result': round(result, 2),
            'result_label': str(_('Calculated Distance')),
            'result_unit_symbol': self._dl(ru),
            'formula': f'{self._f(result)} {self._dl(ru)}',
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── 5) CONVERT DISTANCE ──────────────────────────────────────────
    def _calc_convert_distance(self, d):
        val = self._req_nn(d, 'value', str(_('Distance')))
        fu = d.get('from_unit', 'miles')
        tu = d.get('to_unit', 'kilometers')
        km = self._to_km(val, fu)
        result = self._km_to(km, tu)

        steps = [
            str(_('Step 1: Given value')),
            f'  • {self._f(val)} {self._dl(fu)}',
            '', str(_('Step 2: Convert')),
            f'  = {self._f(result, 4)} {self._dl(tu)}',
        ]
        return JsonResponse({
            'success': True, 'calc_type': 'convert_distance',
            'result': round(result, 6),
            'result_label': str(_('Converted Distance')),
            'result_unit_symbol': self._dl(tu),
            'formula': f'{self._f(val)} {self._dl(fu)} = {self._f(result, 4)} {self._dl(tu)}',
            'step_by_step': steps,
            'chart_data': None,
        })

    # ── 6) COMPARE RATES ─────────────────────────────────────────────
    def _calc_compare_rates(self, d):
        dist = self._req_nn(d, 'distance', str(_('Distance')))
        r1 = self._req_nn(d, 'rate1', str(_('Rate 1')))
        r2 = self._req_nn(d, 'rate2', str(_('Rate 2')))
        du = d.get('distance_unit', 'miles')
        ru = d.get('rate_unit', 'per_mile')
        cur = d.get('currency', 'usd')
        cs = self._cs(cur)

        dist_km = self._to_km(dist, du)
        if ru == 'per_mile':
            dist_calc = self._to_miles(dist_km)
            ulbl = str(_('mile'))
        else:
            dist_calc = dist_km
            ulbl = 'km'

        reimb1 = self._safe(dist_calc * r1)
        reimb2 = self._safe(dist_calc * r2)
        diff = reimb2 - reimb1
        pct = (diff / reimb1 * 100) if reimb1 > 0 else 0

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Distance")} = {self._f(dist)} {self._dl(du)} → {self._f(dist_calc)} {ulbl}',
            f'  • {_("Rate 1")} = {cs}{self._f(r1)} / {ulbl}',
            f'  • {_("Rate 2")} = {cs}{self._f(r2)} / {ulbl}',
            '', str(_('Step 2: Calculate reimbursements')),
            f'  {_("Rate 1")}: {self._f(dist_calc)} × {cs}{self._f(r1)} = {cs}{self._f(reimb1)}',
            f'  {_("Rate 2")}: {self._f(dist_calc)} × {cs}{self._f(r2)} = {cs}{self._f(reimb2)}',
            '', str(_('Step 3: Difference')),
            f'  {cs}{self._f(reimb2)} − {cs}{self._f(reimb1)} = {cs}{self._f(diff)} ({self._f(pct)}%)',
        ]

        chart = self._bar(
            [str(_('Rate 1')), str(_('Rate 2'))],
            [reimb1, reimb2],
            ['rgba(59,130,246,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Rate Comparison')))

        return JsonResponse({
            'success': True, 'calc_type': 'compare_rates',
            'result': round(diff, 2),
            'result_label': str(_('Rate Comparison')),
            'result_unit_symbol': cs,
            'formula': f'{cs}{self._f(reimb1)} vs {cs}{self._f(reimb2)} (Δ {cs}{self._f(diff)})',
            'reimbursement1': round(reimb1, 2),
            'reimbursement2': round(reimb2, 2),
            'difference': round(diff, 2),
            'percent_difference': round(pct, 2),
            'step_by_step': steps,
            'chart_data': {'mc_chart': chart},
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
