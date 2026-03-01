from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TileCalculator(View):
    """
    Tile Calculator — tiles needed, coverage, cost.

    Calc types
        • tiles_needed  → Area / Tile Area + waste
        • coverage       → Num Tiles × Tile Area
        • cost           → Tiles × Price + Grout + Labor
    """
    template_name = 'other_calculators/tile_calculator.html'

    # Area → square feet
    AREA = {'square_feet': 1.0, 'square_meters': 10.7639, 'square_yards': 9.0}
    # Tile dimensions → inches
    TILE_LEN = {'inches': 1.0, 'feet': 12.0, 'centimeters': 0.393701, 'meters': 39.3701}

    UNIT_SYM = {
        'square_feet': 'ft²', 'square_meters': 'm²', 'square_yards': 'yd²',
        'inches': 'in', 'feet': 'ft', 'centimeters': 'cm', 'meters': 'm',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Tile Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'tiles_needed')
            dispatch = {
                'tiles_needed': self._calc_tiles,
                'coverage':     self._calc_coverage,
                'cost':         self._calc_cost,
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
            return 0.0
        f = float(v)
        if f < 0:
            raise ValueError(str(_('{label} must be non-negative.').format(label=label)))
        return f

    def _to_in(self, val, unit):
        if unit not in self.TILE_LEN:
            raise ValueError(str(_('Invalid tile dimension unit.')))
        return val * self.TILE_LEN[unit]

    def _to_sqft(self, val, unit):
        if unit not in self.AREA:
            raise ValueError(str(_('Invalid area unit.')))
        return val * self.AREA[unit]

    def _chart(self, labels, values, title, chart_type='bar'):
        colors = ['rgba(99,102,241,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)']
        borders = ['#6366f1', '#10b981', '#f59e0b', '#ef4444']
        n = len(labels)
        ds = {
            'label': str(_('Values')),
            'data': values,
            'backgroundColor': colors[:n],
            'borderColor': borders[:n],
            'borderWidth': 2,
        }
        if chart_type == 'bar':
            ds['borderRadius'] = 6
        opts = {
            'responsive': True, 'maintainAspectRatio': False,
            'plugins': {'title': {'display': True, 'text': str(title)}},
        }
        if chart_type == 'bar':
            opts['plugins']['legend'] = {'display': False}
            opts['scales'] = {'y': {'beginAtZero': True}}
        else:
            opts['plugins']['legend'] = {'display': True, 'position': 'bottom'}
        return {'type': chart_type, 'data': {'labels': labels, 'datasets': [ds]}, 'options': opts}

    # ── 1) TILES NEEDED ──────────────────────────────────────────────
    def _calc_tiles(self, data):
        area = self._pos(data, 'area', str(_('Area')))
        tl = self._pos(data, 'tile_length', str(_('Tile Length')))
        tw = self._pos(data, 'tile_width', str(_('Tile Width')))
        au = data.get('area_unit', 'square_feet')
        tu = data.get('tile_unit', 'inches')
        wf = float(data.get('waste_factor', 10))

        if wf < 0 or wf > 50:
            raise ValueError(str(_('Waste factor must be between 0 and 50%.')))

        # Convert area to sq inches
        area_sqft = self._to_sqft(area, au)
        area_sqin = area_sqft * 144

        # Convert tile dims to inches
        tl_in = self._to_in(tl, tu)
        tw_in = self._to_in(tw, tu)
        tile_area = tl_in * tw_in  # sq in

        # Tiles
        tiles_exact = area_sqin / tile_area
        tiles_waste = tiles_exact * (1 + wf / 100)
        tiles_buy = math.ceil(tiles_waste)

        # Grout: ~1 lb per 10 ft²
        grout_lbs = round(area_sqft / 10, 2)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Area")} = {self._f(area)} {self._sym(au)}',
            f'  • {_("Tile")} = {self._f(tl)} × {self._f(tw)} {self._sym(tu)}',
            f'  • {_("Waste")} = {self._f(wf, 0)}%',
            '', str(_('Step 2: Convert to square inches')),
            f'  Area = {self._f(area_sqft)} ft² = {self._f(area_sqin)} in²',
            f'  Tile = {self._f(tl_in)} × {self._f(tw_in)} = {self._f(tile_area)} in²',
            '', str(_('Step 3: Calculate tiles (exact)')),
            f'  Tiles = {self._f(area_sqin)} / {self._f(tile_area)} = {self._f(tiles_exact)}',
            '', str(_('Step 4: Add waste factor ({pct}%)').format(pct=int(wf))),
            f'  {self._f(tiles_exact)} × {self._f(1 + wf/100, 2)} = {self._f(tiles_waste)}',
            '', str(_('Step 5: Round up')),
            f'  {_("Tiles to buy")} = {tiles_buy}',
            '', str(_('Step 6: Grout estimate')),
            f'  ≈ {self._f(grout_lbs)} lbs (1 lb / 10 ft²)',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'tiles_needed',
            'result': tiles_buy,
            'result_label': str(_('Tiles Needed')),
            'result_unit_symbol': str(_('tiles')),
            'tiles_exact': round(tiles_exact, 2),
            'tiles_with_waste': round(tiles_waste, 2),
            'grout_lbs': grout_lbs,
            'formula': f'{self._f(area)} {self._sym(au)} ÷ ({self._f(tl)}×{self._f(tw)} {self._sym(tu)}) + {int(wf)}% = {tiles_buy} tiles',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Exact')), str(_('With Waste')), str(_('To Buy'))],
                [round(tiles_exact, 1), round(tiles_waste, 1), tiles_buy],
                str(_('Tiles Breakdown'))
            )},
        })

    # ── 2) COVERAGE ──────────────────────────────────────────────────
    def _calc_coverage(self, data):
        nt = self._pos(data, 'num_tiles', str(_('Number of Tiles')))
        tl = self._pos(data, 'tile_length', str(_('Tile Length')))
        tw = self._pos(data, 'tile_width', str(_('Tile Width')))
        tu = data.get('tile_unit', 'inches')
        ru = data.get('result_unit', 'square_feet')

        nt = int(nt)
        tl_in = self._to_in(tl, tu)
        tw_in = self._to_in(tw, tu)
        tile_area = tl_in * tw_in
        total_sqin = tile_area * nt
        total_sqft = total_sqin / 144
        result = total_sqft / self.AREA.get(ru, 1.0)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Tiles")} = {nt}',
            f'  • {_("Tile")} = {self._f(tl)} × {self._f(tw)} {self._sym(tu)}',
            '', str(_('Step 2: Convert tile dims to inches')),
            f'  {self._f(tl_in)} × {self._f(tw_in)} = {self._f(tile_area)} in²',
            '', str(_('Step 3: Total coverage')),
            f'  {self._f(tile_area)} × {nt} = {self._f(total_sqin)} in² = {self._f(total_sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'coverage',
            'result': round(result, 4),
            'result_label': str(_('Coverage Area')),
            'result_unit_symbol': self._sym(ru),
            'coverage_sqft': round(total_sqft, 4),
            'formula': f'{nt} × ({self._f(tl)}×{self._f(tw)} {self._sym(tu)}) = {self._f(result, 4)} {self._sym(ru)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Coverage (ft²)')), str(_('Coverage ({u})').format(u=self._sym(ru)))],
                [round(total_sqft, 2), round(result, 2)],
                str(_('Tile Coverage'))
            )},
        })

    # ── 3) COST ──────────────────────────────────────────────────────
    def _calc_cost(self, data):
        area = self._pos(data, 'area', str(_('Area')))
        tl = self._pos(data, 'tile_length', str(_('Tile Length')))
        tw = self._pos(data, 'tile_width', str(_('Tile Width')))
        ppt = self._nonneg(data, 'price_per_tile', str(_('Price per Tile')))
        au = data.get('area_unit', 'square_feet')
        tu = data.get('tile_unit', 'inches')
        wf = float(data.get('waste_factor', 10))
        grout_cost_per_lb = self._nonneg(data, 'grout_cost', str(_('Grout Cost')))
        labor = self._nonneg(data, 'labor_cost', str(_('Labor Cost')))

        if wf < 0 or wf > 50:
            raise ValueError(str(_('Waste factor must be between 0 and 50%.')))

        area_sqft = self._to_sqft(area, au)
        area_sqin = area_sqft * 144
        tl_in = self._to_in(tl, tu)
        tw_in = self._to_in(tw, tu)
        tile_area = tl_in * tw_in
        tiles_exact = area_sqin / tile_area
        tiles_waste = tiles_exact * (1 + wf / 100)
        tiles_buy = math.ceil(tiles_waste)

        tile_cost = tiles_buy * ppt
        grout_lbs = area_sqft / 10
        grout_total = grout_lbs * grout_cost_per_lb
        total = tile_cost + grout_total + labor

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Area")} = {self._f(area)} {self._sym(au)}',
            f'  • {_("Tile")} = {self._f(tl)} × {self._f(tw)} {self._sym(tu)}',
            f'  • {_("Price/tile")} = ${self._f(ppt)}',
            f'  • {_("Waste")} = {self._f(wf, 0)}%',
            '', str(_('Step 2: Calculate tiles to buy')),
            f'  {self._f(tiles_exact)} exact → +{int(wf)}% → {tiles_buy} tiles',
            '', str(_('Step 3: Tile cost')),
            f'  {tiles_buy} × ${self._f(ppt)} = ${self._f(tile_cost)}',
            '', str(_('Step 4: Grout cost')),
            f'  {self._f(grout_lbs)} lbs × ${self._f(grout_cost_per_lb)} = ${self._f(grout_total)}',
            '', str(_('Step 5: Total cost')),
            f'  Tile ${self._f(tile_cost)} + Grout ${self._f(grout_total)} + Labor ${self._f(labor)} = ${self._f(total)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'cost',
            'result': round(total, 2),
            'result_label': str(_('Total Cost')),
            'result_unit_symbol': '$',
            'tiles_needed': tiles_buy,
            'tile_cost': round(tile_cost, 2),
            'grout_cost_total': round(grout_total, 2),
            'labor_cost': round(labor, 2),
            'formula': f'{tiles_buy} tiles × ${self._f(ppt)} + grout + labor = ${self._f(total)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Tile Cost')), str(_('Grout Cost')), str(_('Labor Cost'))],
                [round(tile_cost, 2), round(grout_total, 2), round(labor, 2)],
                str(_('Cost Breakdown')),
                'pie'
            )},
        })
