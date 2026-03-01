from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RoofingCalculator(View):
    """
    Roofing Calculator — area, materials, pitch, cost.

    Calc types
        • area       → L × W × pitch multiplier (gable / hip / flat)
        • materials   → area → bundles & squares
        • pitch       → rise / run → X:12, angle, slope %
        • cost        → squares × price + labor
    """
    template_name = 'other_calculators/roofing_calculator.html'

    # Length → feet
    LEN = {'feet': 1.0, 'inches': 1/12, 'meters': 3.28084}
    # Area → square feet
    AREA = {'square_feet': 1.0, 'square_meters': 10.7639, 'square_yards': 9.0}

    # Material coverage: ft² per bundle
    COVERAGE = {
        'asphalt_shingles': 33.33,   # 3 bundles / square
        'wood_shingles':    25.0,    # 4 bundles / square
        'slate_tiles':      100.0,   # 1 bundle / square
        'clay_tiles':       100.0,
        'metal_roofing':    100.0,
        'rubber_roofing':   100.0,
    }

    UNIT_SYM = {
        'feet': 'ft', 'inches': 'in', 'meters': 'm',
        'square_feet': 'ft²', 'square_meters': 'm²', 'square_yards': 'yd²',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Roofing Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'area')
            dispatch = {
                'area':      self._calc_area,
                'materials': self._calc_materials,
                'pitch':     self._calc_pitch,
                'cost':      self._calc_cost,
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

    def _to_ft(self, val, unit):
        if unit not in self.LEN:
            raise ValueError(str(_('Invalid length unit.')))
        return val * self.LEN[unit]

    def _to_sqft(self, val, unit):
        if unit not in self.AREA:
            raise ValueError(str(_('Invalid area unit.')))
        return val * self.AREA[unit]

    def _area_multi(self, sqft):
        return {
            'square_feet':   round(sqft, 2),
            'square_meters': round(sqft / 10.7639, 4),
            'square_yards':  round(sqft / 9, 4),
        }

    def _chart(self, labels, values, title, chart_type='bar'):
        colors = ['rgba(239,68,68,0.8)', 'rgba(59,130,246,0.8)', 'rgba(245,158,11,0.8)', 'rgba(16,185,129,0.8)']
        borders = ['#ef4444', '#3b82f6', '#f59e0b', '#10b981']
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

    def _pitch_multiplier(self, pitch):
        """pitch = rise per 12 run. Multiplier = √(1 + (pitch/12)²)"""
        return math.sqrt(1 + (pitch / 12) ** 2)

    # ── 1) ROOF AREA ─────────────────────────────────────────────────
    def _calc_area(self, data):
        shape = data.get('roof_shape', 'gable')
        l = self._pos(data, 'length', str(_('Length')))
        w = self._pos(data, 'width', str(_('Width')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')

        lf = self._to_ft(l, lu)
        wf = self._to_ft(w, lu)

        if shape == 'flat':
            pm = 1.0
            pitch = 0
        else:
            pitch = self._nonneg(data, 'pitch', str(_('Pitch')))
            pm = self._pitch_multiplier(pitch)

        base_sqft = lf * wf
        roof_sqft = base_sqft * pm
        result = roof_sqft / self.AREA.get(ru, 1.0)
        aream = self._area_multi(roof_sqft)
        squares = roof_sqft / 100  # roofing squares

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Shape")} = {shape.title()}',
            f'  • {_("Length")} = {self._f(l)} {self._sym(lu)}',
            f'  • {_("Width")} = {self._f(w)} {self._sym(lu)}',
        ]
        if shape != 'flat':
            steps.append(f'  • {_("Pitch")} = {self._f(pitch, 1)}:12')
        steps += [
            '', str(_('Step 2: Convert to feet')),
            f'  L = {self._f(lf)} ft, W = {self._f(wf)} ft',
        ]
        if shape != 'flat':
            steps += [
                '', str(_('Step 3: Pitch multiplier')),
                f'  √(1 + ({self._f(pitch, 1)}/12)²) = {self._f(pm, 4)}',
                '', str(_('Step 4: Calculate roof area')),
                f'  A = L × W × PM = {self._f(lf)} × {self._f(wf)} × {self._f(pm, 4)} = {self._f(roof_sqft)} ft²',
            ]
        else:
            steps += [
                '', str(_('Step 3: Calculate roof area')),
                f'  A = L × W = {self._f(lf)} × {self._f(wf)} = {self._f(roof_sqft)} ft²',
            ]
        steps += [
            '', str(_('Step {n}: Roofing squares').format(n=5 if shape != 'flat' else 4)),
            f'  {self._f(roof_sqft)} / 100 = {self._f(squares)} squares',
            '', str(_('Step {n}: Convert to {unit}').format(n=6 if shape != 'flat' else 5, unit=self._sym(ru))),
            f'  = {self._f(result, 4)} {self._sym(ru)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'area',
            'result': round(result, 4),
            'result_label': str(_('Roof Area')),
            'result_unit_symbol': self._sym(ru),
            'roof_shape': shape,
            'pitch_multiplier': round(pm, 4),
            'squares': round(squares, 2),
            'area': aream,
            'formula': f'{self._f(l)} × {self._f(w)} {self._sym(lu)}' + (f' × PM({self._f(pitch, 1)}:12)' if shape != 'flat' else '') + f' = {self._f(result, 4)} {self._sym(ru)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('ft²')), str(_('m²')), str(_('yd²'))],
                [aream['square_feet'], aream['square_meters'], aream['square_yards']],
                str(_('Roof Area Comparison'))
            )},
        })

    # ── 2) MATERIALS ─────────────────────────────────────────────────
    def _calc_materials(self, data):
        area = self._pos(data, 'area', str(_('Roof Area')))
        au = data.get('area_unit', 'square_feet')
        mt = data.get('material_type', 'asphalt_shingles')
        wf = float(data.get('waste_factor', 10))

        if mt not in self.COVERAGE:
            raise ValueError(str(_('Invalid material type.')))
        if wf < 0 or wf > 50:
            raise ValueError(str(_('Waste factor must be between 0 and 50%.')))

        sqft = self._to_sqft(area, au)
        sqft_waste = sqft * (1 + wf / 100)
        coverage = self.COVERAGE[mt]
        bundles = math.ceil(sqft_waste / coverage)
        squares = sqft_waste / 100
        mt_label = mt.replace('_', ' ').title()

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Area")} = {self._f(area)} {self._sym(au)}',
            f'  • {_("Material")} = {mt_label}',
            f'  • {_("Waste")} = {self._f(wf, 0)}%',
            '', str(_('Step 2: Convert to square feet')),
            f'  = {self._f(sqft)} ft²',
            '', str(_('Step 3: Add waste ({pct}%)').format(pct=int(wf))),
            f'  {self._f(sqft)} × {self._f(1 + wf/100, 2)} = {self._f(sqft_waste)} ft²',
            '', str(_('Step 4: Calculate bundles')),
            f'  Coverage: {self._f(coverage)} ft²/bundle',
            f'  {self._f(sqft_waste)} / {self._f(coverage)} = {bundles} bundles',
            '', str(_('Step 5: Roofing squares')),
            f'  {self._f(sqft_waste)} / 100 = {self._f(squares)} squares',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'materials',
            'result': bundles,
            'result_label': str(_('Bundles Needed')),
            'result_unit_symbol': str(_('bundles')),
            'squares': round(squares, 2),
            'area_with_waste': round(sqft_waste, 2),
            'material_type': mt,
            'formula': f'{self._f(area)} {self._sym(au)} + {int(wf)}% waste → {bundles} bundles ({self._f(squares)} sq)',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Area (ft²)')), str(_('w/ Waste (ft²)')), str(_('Bundles'))],
                [round(sqft, 1), round(sqft_waste, 1), bundles],
                str(_('Materials Breakdown'))
            )},
        })

    # ── 3) PITCH ─────────────────────────────────────────────────────
    def _calc_pitch(self, data):
        rise = self._nonneg(data, 'rise', str(_('Rise')))
        run = self._pos(data, 'run', str(_('Run')))

        pitch = (rise / run) * 12  # X:12
        angle = math.degrees(math.atan(rise / run))
        slope_pct = (rise / run) * 100
        pm = self._pitch_multiplier(pitch)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Rise")} = {self._f(rise)} in',
            f'  • {_("Run")} = {self._f(run)} in',
            '', str(_('Step 2: Calculate pitch (X:12)')),
            f'  ({self._f(rise)} / {self._f(run)}) × 12 = {self._f(pitch)}:12',
            '', str(_('Step 3: Calculate angle')),
            f'  arctan({self._f(rise)} / {self._f(run)}) = {self._f(angle)}°',
            '', str(_('Step 4: Slope percentage')),
            f'  ({self._f(rise)} / {self._f(run)}) × 100 = {self._f(slope_pct)}%',
            '', str(_('Step 5: Pitch multiplier')),
            f'  √(1 + ({self._f(pitch)}/12)²) = {self._f(pm, 4)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'pitch',
            'result': round(pitch, 2),
            'result_label': str(_('Roof Pitch')),
            'result_unit_symbol': ':12',
            'angle': round(angle, 2),
            'slope_percent': round(slope_pct, 2),
            'pitch_multiplier': round(pm, 4),
            'formula': f'{self._f(rise)} / {self._f(run)} = {self._f(pitch)}:12 ({self._f(angle)}°)',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Rise (in)')), str(_('Run (in)')), str(_('Pitch (:12)')), str(_('Angle (°)'))],
                [round(rise, 2), round(run, 2), round(pitch, 2), round(angle, 2)],
                str(_('Pitch Analysis'))
            )},
        })

    # ── 4) COST ──────────────────────────────────────────────────────
    def _calc_cost(self, data):
        area = self._pos(data, 'area', str(_('Roof Area')))
        pps = self._nonneg(data, 'price_per_square', str(_('Price per Square')))
        au = data.get('area_unit', 'square_feet')
        wf = float(data.get('waste_factor', 10))
        labor = self._nonneg(data, 'labor_cost', str(_('Labor Cost')))

        if wf < 0 or wf > 50:
            raise ValueError(str(_('Waste factor must be between 0 and 50%.')))

        sqft = self._to_sqft(area, au)
        sqft_waste = sqft * (1 + wf / 100)
        squares = sqft_waste / 100
        material_cost = squares * pps
        total = material_cost + labor

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Area")} = {self._f(area)} {self._sym(au)}',
            f'  • {_("Price/square")} = ${self._f(pps)}',
            f'  • {_("Labor")} = ${self._f(labor)}',
            f'  • {_("Waste")} = {self._f(wf, 0)}%',
            '', str(_('Step 2: Area with waste')),
            f'  {self._f(sqft)} × {self._f(1 + wf/100, 2)} = {self._f(sqft_waste)} ft²',
            '', str(_('Step 3: Roofing squares')),
            f'  {self._f(sqft_waste)} / 100 = {self._f(squares)} squares',
            '', str(_('Step 4: Material cost')),
            f'  {self._f(squares)} × ${self._f(pps)} = ${self._f(material_cost)}',
            '', str(_('Step 5: Total cost')),
            f'  ${self._f(material_cost)} + ${self._f(labor)} = ${self._f(total)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'cost',
            'result': round(total, 2),
            'result_label': str(_('Total Cost')),
            'result_unit_symbol': '$',
            'squares': round(squares, 2),
            'material_cost': round(material_cost, 2),
            'labor_cost': round(labor, 2),
            'formula': f'{self._f(squares)} sq × ${self._f(pps)} + ${self._f(labor)} = ${self._f(total)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Material Cost')), str(_('Labor Cost'))],
                [round(material_cost, 2), round(labor, 2)],
                str(_('Cost Breakdown')),
                'pie'
            )},
        })
