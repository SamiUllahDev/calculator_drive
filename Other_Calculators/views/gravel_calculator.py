from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GravelCalculator(View):
    """
    Gravel Calculator — volume, weight, cost, coverage & conversions.

    Calc types
        • rectangular   → L × W × D
        • circular      → π × r² × D
        • triangular    → ½ × B × H × D
        • weight        → Volume × Density
        • cost          → Volume × Price
        • coverage      → Volume / Depth
        • convert_volume
        • convert_weight
    """
    template_name = 'other_calculators/gravel_calculator.html'

    # Length → feet
    LEN = {'feet': 1.0, 'inches': 1/12, 'yards': 3.0, 'meters': 3.28084}
    # Volume → cubic feet
    VOL = {'cubic_feet': 1.0, 'cubic_yards': 27.0, 'cubic_meters': 35.3147}
    # Weight → pounds
    WGT = {'pounds': 1.0, 'tons': 2000.0, 'kilograms': 2.20462}
    # Area → square feet
    AREA = {'square_feet': 1.0, 'square_yards': 9.0, 'square_meters': 10.7639}
    # Default gravel density lb/ft³
    DEFAULT_DENSITY = 105.0

    UNIT_SYM = {
        'cubic_feet': 'ft³', 'cubic_yards': 'yd³', 'cubic_meters': 'm³',
        'pounds': 'lbs', 'tons': 'tons', 'kilograms': 'kg',
        'square_feet': 'ft²', 'square_yards': 'yd²', 'square_meters': 'm²',
        'feet': 'ft', 'inches': 'in', 'yards': 'yd', 'meters': 'm',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Gravel Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'rectangular')
            dispatch = {
                'rectangular':     self._calc_rect,
                'circular':        self._calc_circ,
                'triangular':      self._calc_tri,
                'weight':          self._calc_weight,
                'cost':            self._calc_cost,
                'coverage':        self._calc_coverage,
                'convert_volume':  self._calc_cvol,
                'convert_weight':  self._calc_cwgt,
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

    def _sym(self, u):
        return self.UNIT_SYM.get(u, u)

    def _pos(self, data, key, label):
        v = data.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{label} is required.').format(label=label)))
        f = float(v)
        if f <= 0:
            raise ValueError(str(_('{label} must be greater than zero.').format(label=label)))
        return f

    def _nonneg(self, data, key, label):
        v = data.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{label} is required.').format(label=label)))
        f = float(v)
        if f < 0:
            raise ValueError(str(_('{label} must be non-negative.').format(label=label)))
        return f

    def _to_ft(self, val, unit):
        if unit not in self.LEN:
            raise ValueError(str(_('Invalid length unit.')))
        return val * self.LEN[unit]

    def _to_cuft(self, val, unit):
        if unit not in self.VOL:
            raise ValueError(str(_('Invalid volume unit.')))
        return val * self.VOL[unit]

    def _to_lbs(self, val, unit):
        if unit not in self.WGT:
            raise ValueError(str(_('Invalid weight unit.')))
        return val * self.WGT[unit]

    def _vol_multi(self, cuft):
        """Return dict of volume in 3 units."""
        return {
            'cubic_feet':  round(cuft, 2),
            'cubic_yards': round(cuft / 27, 4),
            'cubic_meters': round(cuft / 35.3147, 4),
        }

    def _chart(self, labels, values, title):
        colors = ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(139,92,246,0.8)']
        borders = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']
        n = len(labels)
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Values')),
                    'data': values,
                    'backgroundColor': colors[:n],
                    'borderColor': borders[:n],
                    'borderWidth': 2, 'borderRadius': 6,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(title)}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }

    # ── 1) RECTANGULAR ───────────────────────────────────────────────
    def _calc_rect(self, data):
        l = self._pos(data, 'length', str(_('Length')))
        w = self._pos(data, 'width', str(_('Width')))
        d = self._pos(data, 'depth', str(_('Depth')))
        lu = data.get('length_unit', 'feet')
        wu = data.get('width_unit', 'feet')
        du = data.get('depth_unit', 'inches')
        ru = data.get('result_unit', 'cubic_yards')

        lf = self._to_ft(l, lu); wf = self._to_ft(w, wu); df = self._to_ft(d, du)
        cuft = lf * wf * df
        result = cuft / self.VOL[ru]
        vol = self._vol_multi(cuft)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Length")} = {self._f(l)} {self._sym(lu)}',
            f'  • {_("Width")} = {self._f(w)} {self._sym(wu)}',
            f'  • {_("Depth")} = {self._f(d)} {self._sym(du)}',
            '', str(_('Step 2: Convert to feet')),
            f'  L = {self._f(lf)} ft, W = {self._f(wf)} ft, D = {self._f(df)} ft',
            '', str(_('Step 3: Calculate volume')),
            f'  V = L × W × D = {self._f(lf)} × {self._f(wf)} × {self._f(df)} = {self._f(cuft)} ft³',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'rectangular',
            'result': round(result, 4), 'result_label': str(_('Volume')), 'result_unit_symbol': self._sym(ru),
            'formula': f'V = {self._f(l)} × {self._f(w)} × {self._f(d)} = {self._f(result, 4)} {self._sym(ru)}',
            'volume': vol, 'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Cubic Feet')), str(_('Cubic Yards')), str(_('Cubic Meters'))],
                [vol['cubic_feet'], vol['cubic_yards'], vol['cubic_meters']],
                str(_('Volume Comparison'))
            )},
        })

    # ── 2) CIRCULAR ──────────────────────────────────────────────────
    def _calc_circ(self, data):
        d = self._pos(data, 'diameter', str(_('Diameter')))
        dp = self._pos(data, 'depth', str(_('Depth')))
        du_ = data.get('diameter_unit', 'feet')
        dpu = data.get('depth_unit', 'inches')
        ru = data.get('result_unit', 'cubic_yards')

        df = self._to_ft(d, du_); dpf = self._to_ft(dp, dpu)
        r = df / 2; area = math.pi * r ** 2
        cuft = area * dpf
        result = cuft / self.VOL[ru]
        vol = self._vol_multi(cuft)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Diameter")} = {self._f(d)} {self._sym(du_)}',
            f'  • {_("Depth")} = {self._f(dp)} {self._sym(dpu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  D = {self._f(df)} ft, Depth = {self._f(dpf)} ft',
            '', str(_('Step 3: Calculate radius & area')),
            f'  r = {self._f(r)} ft  →  A = π × r² = {self._f(area)} ft²',
            '', str(_('Step 4: Calculate volume')),
            f'  V = A × Depth = {self._f(area)} × {self._f(dpf)} = {self._f(cuft)} ft³',
            '', str(_('Step 5: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'circular',
            'result': round(result, 4), 'result_label': str(_('Volume')), 'result_unit_symbol': self._sym(ru),
            'formula': f'V = π × ({self._f(d/2)})² × {self._f(dp)} = {self._f(result, 4)} {self._sym(ru)}',
            'volume': vol, 'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Cubic Feet')), str(_('Cubic Yards')), str(_('Cubic Meters'))],
                [vol['cubic_feet'], vol['cubic_yards'], vol['cubic_meters']],
                str(_('Volume Comparison'))
            )},
        })

    # ── 3) TRIANGULAR ────────────────────────────────────────────────
    def _calc_tri(self, data):
        b = self._pos(data, 'base', str(_('Base')))
        h = self._pos(data, 'height', str(_('Height')))
        d = self._pos(data, 'depth', str(_('Depth')))
        bu = data.get('base_unit', 'feet')
        hu = data.get('height_unit', 'feet')
        du = data.get('depth_unit', 'inches')
        ru = data.get('result_unit', 'cubic_yards')

        bf = self._to_ft(b, bu); hf = self._to_ft(h, hu); df = self._to_ft(d, du)
        area = 0.5 * bf * hf
        cuft = area * df
        result = cuft / self.VOL[ru]
        vol = self._vol_multi(cuft)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Base")} = {self._f(b)} {self._sym(bu)}',
            f'  • {_("Height")} = {self._f(h)} {self._sym(hu)}',
            f'  • {_("Depth")} = {self._f(d)} {self._sym(du)}',
            '', str(_('Step 2: Convert to feet')),
            f'  B = {self._f(bf)} ft, H = {self._f(hf)} ft, D = {self._f(df)} ft',
            '', str(_('Step 3: Calculate area')),
            f'  A = ½ × B × H = ½ × {self._f(bf)} × {self._f(hf)} = {self._f(area)} ft²',
            '', str(_('Step 4: Calculate volume')),
            f'  V = A × D = {self._f(area)} × {self._f(df)} = {self._f(cuft)} ft³',
            '', str(_('Step 5: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'triangular',
            'result': round(result, 4), 'result_label': str(_('Volume')), 'result_unit_symbol': self._sym(ru),
            'formula': f'V = ½ × {self._f(b)} × {self._f(h)} × {self._f(d)} = {self._f(result, 4)} {self._sym(ru)}',
            'volume': vol, 'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Cubic Feet')), str(_('Cubic Yards')), str(_('Cubic Meters'))],
                [vol['cubic_feet'], vol['cubic_yards'], vol['cubic_meters']],
                str(_('Volume Comparison'))
            )},
        })

    # ── 4) WEIGHT ────────────────────────────────────────────────────
    def _calc_weight(self, data):
        v = self._pos(data, 'volume', str(_('Volume')))
        vu = data.get('volume_unit', 'cubic_yards')
        density = float(data.get('density', self.DEFAULT_DENSITY))
        ru = data.get('result_unit', 'tons')

        if density <= 0 or density > 300:
            raise ValueError(str(_('Density must be between 0 and 300 lbs/ft³.')))

        cuft = self._to_cuft(v, vu)
        lbs = cuft * density
        result = lbs / self.WGT[ru]

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Volume")} = {self._f(v)} {self._sym(vu)}',
            f'  • {_("Density")} = {self._f(density)} lbs/ft³',
            '', str(_('Step 2: Convert to cubic feet')),
            f'  = {self._f(cuft)} ft³',
            '', str(_('Step 3: Calculate weight')),
            f'  W = V × ρ = {self._f(cuft)} × {self._f(density)} = {self._f(lbs)} lbs',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'weight',
            'result': round(result, 4), 'result_label': str(_('Weight')), 'result_unit_symbol': self._sym(ru),
            'formula': f'W = {self._f(v)} {self._sym(vu)} × {self._f(density)} = {self._f(result, 4)} {self._sym(ru)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Volume (ft³)')), str(_('Weight (lbs)'))],
                [round(cuft, 2), round(lbs, 2)],
                str(_('Volume → Weight'))
            )},
        })

    # ── 5) COST ──────────────────────────────────────────────────────
    def _calc_cost(self, data):
        v = self._pos(data, 'volume', str(_('Volume')))
        vu = data.get('volume_unit', 'cubic_yards')
        price = self._nonneg(data, 'price_per_unit', str(_('Price')))

        total = v * price

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Volume")} = {self._f(v)} {self._sym(vu)}',
            f'  • {_("Price")} = ${self._f(price)} / {self._sym(vu)}',
            '', str(_('Step 2: Calculate total cost')),
            f'  Cost = V × Price = {self._f(v)} × ${self._f(price)} = ${self._f(total)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'cost',
            'result': round(total, 2), 'result_label': str(_('Total Cost')), 'result_unit_symbol': '$',
            'formula': f'{self._f(v)} {self._sym(vu)} × ${self._f(price)} = ${self._f(total)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Volume')), str(_('Price/Unit')), str(_('Total Cost'))],
                [round(v, 2), round(price, 2), round(total, 2)],
                str(_('Cost Breakdown'))
            )},
        })

    # ── 6) COVERAGE ──────────────────────────────────────────────────
    def _calc_coverage(self, data):
        v = self._pos(data, 'volume', str(_('Volume')))
        d = self._pos(data, 'depth', str(_('Depth')))
        vu = data.get('volume_unit', 'cubic_yards')
        du = data.get('depth_unit', 'inches')
        ru = data.get('result_unit', 'square_feet')

        cuft = self._to_cuft(v, vu)
        df = self._to_ft(d, du)
        sqft = cuft / df
        result = sqft / self.AREA.get(ru, 1.0)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Volume")} = {self._f(v)} {self._sym(vu)}',
            f'  • {_("Depth")} = {self._f(d)} {self._sym(du)}',
            '', str(_('Step 2: Convert to base units')),
            f'  Volume = {self._f(cuft)} ft³, Depth = {self._f(df)} ft',
            '', str(_('Step 3: Calculate coverage area')),
            f'  Area = V / D = {self._f(cuft)} / {self._f(df)} = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'coverage',
            'result': round(result, 4), 'result_label': str(_('Coverage Area')), 'result_unit_symbol': self._sym(ru),
            'formula': f'A = {self._f(v)} {self._sym(vu)} / {self._f(d)} {self._sym(du)} = {self._f(result, 4)} {self._sym(ru)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Volume (ft³)')), str(_('Area (ft²)'))],
                [round(cuft, 2), round(sqft, 2)],
                str(_('Volume → Coverage'))
            )},
        })

    # ── 7) CONVERT VOLUME ────────────────────────────────────────────
    def _calc_cvol(self, data):
        v = self._nonneg(data, 'value', str(_('Volume')))
        fu = data.get('from_unit', 'cubic_yards')
        tu = data.get('to_unit', 'cubic_feet')

        cuft = self._to_cuft(v, fu)
        result = cuft / self.VOL[tu]

        steps = [
            str(_('Step 1: Original value')),
            f'  {self._f(v, 4)} {self._sym(fu)}',
            '', str(_('Step 2: Convert to cubic feet')),
            f'  = {self._f(cuft, 4)} ft³',
            '', str(_('Step 3: Convert to {unit}').format(unit=self._sym(tu))),
            f'  = {self._f(result, 6)} {self._sym(tu)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert_volume',
            'result': round(result, 6), 'result_label': str(_('Converted Volume')), 'result_unit_symbol': self._sym(tu),
            'formula': f'{self._f(v, 4)} {self._sym(fu)} = {self._f(result, 6)} {self._sym(tu)}',
            'step_by_step': steps, 'chart_data': None,
        })

    # ── 8) CONVERT WEIGHT ────────────────────────────────────────────
    def _calc_cwgt(self, data):
        v = self._nonneg(data, 'value', str(_('Weight')))
        fu = data.get('from_unit', 'tons')
        tu = data.get('to_unit', 'pounds')

        lbs = self._to_lbs(v, fu)
        result = lbs / self.WGT[tu]

        steps = [
            str(_('Step 1: Original value')),
            f'  {self._f(v, 4)} {self._sym(fu)}',
            '', str(_('Step 2: Convert to pounds')),
            f'  = {self._f(lbs, 4)} lbs',
            '', str(_('Step 3: Convert to {unit}').format(unit=self._sym(tu))),
            f'  = {self._f(result, 6)} {self._sym(tu)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert_weight',
            'result': round(result, 6), 'result_label': str(_('Converted Weight')), 'result_unit_symbol': self._sym(tu),
            'formula': f'{self._f(v, 4)} {self._sym(fu)} = {self._f(result, 6)} {self._sym(tu)}',
            'step_by_step': steps, 'chart_data': None,
        })
