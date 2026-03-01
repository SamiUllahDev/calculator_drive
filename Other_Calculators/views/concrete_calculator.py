from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ConcreteCalculator(View):
    """
    Concrete Calculator — volume & material requirements.

    Calc types
        • rectangular_slab  → L × W × Thickness
        • circular_slab     → π × r² × Thickness
        • column            → π × r² × Height
        • footing           → L × W × Depth
        • wall              → L × H × Thickness
        • volume_conversion → cu ft / cu yd / m³

    Supports feet & metres input.  Mix ratios: 1:2:4, 1:1.5:3, 1:3:6, 1:2:3, 1:1:2.
    """
    template_name = 'other_calculators/concrete_calculator.html'

    # Conversion
    CUFT_TO_CUYD = 1 / 27
    CUFT_TO_CUM  = 0.0283168
    CUYD_TO_CUM  = 0.764555
    FT_PER_M     = 3.28084

    # Mix ratios   cement : sand : aggregate
    MIX = {
        '1:2:4':   (1, 2,   4),
        '1:1.5:3': (1, 1.5, 3),
        '1:3:6':   (1, 3,   6),
        '1:2:3':   (1, 2,   3),
        '1:1:2':   (1, 1,   2),
    }

    # Densities (lb/cu ft)
    CEMENT_D = 94
    SAND_D   = 100
    AGG_D    = 150
    BAG_LB   = 94   # 1 bag of cement

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Concrete Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'rectangular_slab')
            dispatch = {
                'rectangular_slab':  self._calc_rect,
                'circular_slab':     self._calc_circ,
                'column':            self._calc_column,
                'footing':           self._calc_footing,
                'wall':              self._calc_wall,
                'volume_conversion': self._calc_convert,
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

    def _pos(self, data, key, label):
        v = data.get(key)
        if v is None or v == '':
            raise ValueError(str(_('{label} is required.').format(label=label)))
        f = float(v)
        if f <= 0:
            raise ValueError(str(_('{label} must be greater than zero.').format(label=label)))
        return f

    def _to_ft(self, val, unit):
        return val * self.FT_PER_M if unit == 'meters' else val

    def _volumes(self, cuft):
        cuyd = cuft * self.CUFT_TO_CUYD
        cum  = cuft * self.CUFT_TO_CUM
        return {
            'cubic_feet':  round(cuft, 2),
            'cubic_yards': round(cuyd, 2),
            'cubic_meters': round(cum, 2),
        }

    def _materials(self, cuft, ratio_key):
        c, s, a = self.MIX.get(ratio_key, (1, 2, 4))
        total = c + s + a
        cv = cuft * c / total
        sv = cuft * s / total
        av = cuft * a / total
        c_lb = cv * self.CEMENT_D
        s_lb = sv * self.SAND_D
        a_lb = av * self.AGG_D
        return {
            'cement':    {'bags': math.ceil(c_lb / self.BAG_LB), 'pounds': round(c_lb, 2), 'tons': round(c_lb / 2000, 3), 'cubic_feet': round(cv, 2)},
            'sand':      {'pounds': round(s_lb, 2), 'tons': round(s_lb / 2000, 3), 'cubic_feet': round(sv, 2)},
            'aggregate': {'pounds': round(a_lb, 2), 'tons': round(a_lb / 2000, 3), 'cubic_feet': round(av, 2)},
        }

    def _vol_chart(self, vol):
        return {
            'type': 'bar',
            'data': {
                'labels': [str(_('Cubic Feet')), str(_('Cubic Yards')), str(_('Cubic Meters'))],
                'datasets': [{
                    'label': str(_('Volume')),
                    'data': [vol['cubic_feet'], vol['cubic_yards'], vol['cubic_meters']],
                    'backgroundColor': ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)'],
                    'borderColor': ['#3b82f6', '#10b981', '#f59e0b'],
                    'borderWidth': 2, 'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('Volume Comparison'))}},
                'scales': {'y': {'beginAtZero': True}},
            }
        }

    def _mat_chart(self, mat):
        return {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Cement')), str(_('Sand')), str(_('Aggregate'))],
                'datasets': [{
                    'data': [mat['cement']['pounds'], mat['sand']['pounds'], mat['aggregate']['pounds']],
                    'backgroundColor': ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)'],
                    'borderColor': ['#3b82f6', '#10b981', '#f59e0b'],
                    'borderWidth': 2,
                }]
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': True, 'position': 'right'}, 'title': {'display': True, 'text': str(_('Materials Breakdown (lbs)'))}},
            }
        }

    def _mat_steps(self, ratio_key, mat):
        return [
            '', str(_('Materials (Mix {ratio})').format(ratio=ratio_key)),
            f'  • {_("Cement")}: {mat["cement"]["bags"]} {_("bags")} ({self._f(mat["cement"]["pounds"])} lbs / {self._f(mat["cement"]["tons"], 3)} {_("tons")})',
            f'  • {_("Sand")}: {self._f(mat["sand"]["pounds"])} lbs ({self._f(mat["sand"]["tons"], 3)} {_("tons")})',
            f'  • {_("Aggregate")}: {self._f(mat["aggregate"]["pounds"])} lbs ({self._f(mat["aggregate"]["tons"], 3)} {_("tons")})',
        ]

    # ── 1) RECTANGULAR SLAB ──────────────────────────────────────────
    def _calc_rect(self, data):
        l = self._pos(data, 'length', str(_('Length')))
        w = self._pos(data, 'width', str(_('Width')))
        t = self._pos(data, 'thickness', str(_('Thickness')))
        u = data.get('unit', 'feet')
        mr = data.get('mix_ratio', '1:2:4')

        lf, wf, tf = self._to_ft(l, u), self._to_ft(w, u), self._to_ft(t, u)
        cuft = lf * wf * tf
        vol = self._volumes(cuft)
        mat = self._materials(cuft, mr)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Length")} = {self._f(l)} {u}',
            f'  • {_("Width")} = {self._f(w)} {u}',
            f'  • {_("Thickness")} = {self._f(t)} {u}',
        ]
        if u == 'meters':
            steps += ['', str(_('Step 2: Convert to feet')),
                       f'  L = {self._f(lf)} ft, W = {self._f(wf)} ft, T = {self._f(tf)} ft']
        steps += [
            '', str(_('Step 3: Calculate volume')),
            f'  V = L × W × T = {self._f(lf)} × {self._f(wf)} × {self._f(tf)} = {self._f(cuft)} cu ft',
            '', str(_('Step 4: Unit conversions')),
            f'  {self._f(vol["cubic_yards"])} cu yd  |  {self._f(vol["cubic_meters"])} m³',
        ] + self._mat_steps(mr, mat)

        return JsonResponse({
            'success': True, 'calc_type': 'rectangular_slab',
            'result': vol['cubic_yards'], 'result_label': str(_('Volume')), 'result_unit_symbol': 'cu yd',
            'formula': f'V = {self._f(l)} × {self._f(w)} × {self._f(t)} {u} = {self._f(vol["cubic_yards"])} cu yd',
            'volume': vol, 'materials': mat, 'mix_ratio': mr,
            'step_by_step': steps,
            'chart_data': {'volume_chart': self._vol_chart(vol), 'materials_chart': self._mat_chart(mat)},
        })

    # ── 2) CIRCULAR SLAB ────────────────────────────────────────────
    def _calc_circ(self, data):
        d = self._pos(data, 'diameter', str(_('Diameter')))
        t = self._pos(data, 'thickness', str(_('Thickness')))
        u = data.get('unit', 'feet')
        mr = data.get('mix_ratio', '1:2:4')

        df, tf = self._to_ft(d, u), self._to_ft(t, u)
        r = df / 2
        area = math.pi * r ** 2
        cuft = area * tf
        vol = self._volumes(cuft)
        mat = self._materials(cuft, mr)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Diameter")} = {self._f(d)} {u}',
            f'  • {_("Thickness")} = {self._f(t)} {u}',
        ]
        if u == 'meters':
            steps += ['', str(_('Step 2: Convert to feet')),
                       f'  D = {self._f(df)} ft, T = {self._f(tf)} ft']
        steps += [
            '', str(_('Step 3: Calculate radius & area')),
            f'  r = {self._f(df)} / 2 = {self._f(r)} ft',
            f'  A = π × r² = π × {self._f(r)}² = {self._f(area)} sq ft',
            '', str(_('Step 4: Calculate volume')),
            f'  V = A × T = {self._f(area)} × {self._f(tf)} = {self._f(cuft)} cu ft',
            '', str(_('Step 5: Unit conversions')),
            f'  {self._f(vol["cubic_yards"])} cu yd  |  {self._f(vol["cubic_meters"])} m³',
        ] + self._mat_steps(mr, mat)

        return JsonResponse({
            'success': True, 'calc_type': 'circular_slab',
            'result': vol['cubic_yards'], 'result_label': str(_('Volume')), 'result_unit_symbol': 'cu yd',
            'formula': f'V = π × ({self._f(d/2)})² × {self._f(t)} = {self._f(vol["cubic_yards"])} cu yd',
            'volume': vol, 'materials': mat, 'mix_ratio': mr,
            'step_by_step': steps,
            'chart_data': {'volume_chart': self._vol_chart(vol), 'materials_chart': self._mat_chart(mat)},
        })

    # ── 3) COLUMN ────────────────────────────────────────────────────
    def _calc_column(self, data):
        d = self._pos(data, 'diameter', str(_('Diameter')))
        h = self._pos(data, 'height', str(_('Height')))
        u = data.get('unit', 'feet')
        mr = data.get('mix_ratio', '1:2:4')

        df, hf = self._to_ft(d, u), self._to_ft(h, u)
        r = df / 2
        area = math.pi * r ** 2
        cuft = area * hf
        vol = self._volumes(cuft)
        mat = self._materials(cuft, mr)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Diameter")} = {self._f(d)} {u}',
            f'  • {_("Height")} = {self._f(h)} {u}',
        ]
        if u == 'meters':
            steps += ['', str(_('Step 2: Convert to feet')),
                       f'  D = {self._f(df)} ft, H = {self._f(hf)} ft']
        steps += [
            '', str(_('Step 3: Calculate radius & area')),
            f'  r = {self._f(r)} ft  |  A = π × r² = {self._f(area)} sq ft',
            '', str(_('Step 4: Calculate volume')),
            f'  V = A × H = {self._f(area)} × {self._f(hf)} = {self._f(cuft)} cu ft',
            '', str(_('Step 5: Unit conversions')),
            f'  {self._f(vol["cubic_yards"])} cu yd  |  {self._f(vol["cubic_meters"])} m³',
        ] + self._mat_steps(mr, mat)

        return JsonResponse({
            'success': True, 'calc_type': 'column',
            'result': vol['cubic_yards'], 'result_label': str(_('Volume')), 'result_unit_symbol': 'cu yd',
            'formula': f'V = π × ({self._f(d/2)})² × {self._f(h)} = {self._f(vol["cubic_yards"])} cu yd',
            'volume': vol, 'materials': mat, 'mix_ratio': mr,
            'step_by_step': steps,
            'chart_data': {'volume_chart': self._vol_chart(vol), 'materials_chart': self._mat_chart(mat)},
        })

    # ── 4) FOOTING ───────────────────────────────────────────────────
    def _calc_footing(self, data):
        l = self._pos(data, 'length', str(_('Length')))
        w = self._pos(data, 'width', str(_('Width')))
        d = self._pos(data, 'depth', str(_('Depth')))
        u = data.get('unit', 'feet')
        mr = data.get('mix_ratio', '1:2:4')

        lf, wf, df = self._to_ft(l, u), self._to_ft(w, u), self._to_ft(d, u)
        cuft = lf * wf * df
        vol = self._volumes(cuft)
        mat = self._materials(cuft, mr)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Length")} = {self._f(l)} {u}',
            f'  • {_("Width")} = {self._f(w)} {u}',
            f'  • {_("Depth")} = {self._f(d)} {u}',
        ]
        if u == 'meters':
            steps += ['', str(_('Step 2: Convert to feet')),
                       f'  L = {self._f(lf)} ft, W = {self._f(wf)} ft, D = {self._f(df)} ft']
        steps += [
            '', str(_('Step 3: Calculate volume')),
            f'  V = L × W × D = {self._f(lf)} × {self._f(wf)} × {self._f(df)} = {self._f(cuft)} cu ft',
            '', str(_('Step 4: Unit conversions')),
            f'  {self._f(vol["cubic_yards"])} cu yd  |  {self._f(vol["cubic_meters"])} m³',
        ] + self._mat_steps(mr, mat)

        return JsonResponse({
            'success': True, 'calc_type': 'footing',
            'result': vol['cubic_yards'], 'result_label': str(_('Volume')), 'result_unit_symbol': 'cu yd',
            'formula': f'V = {self._f(l)} × {self._f(w)} × {self._f(d)} {u} = {self._f(vol["cubic_yards"])} cu yd',
            'volume': vol, 'materials': mat, 'mix_ratio': mr,
            'step_by_step': steps,
            'chart_data': {'volume_chart': self._vol_chart(vol), 'materials_chart': self._mat_chart(mat)},
        })

    # ── 5) WALL ──────────────────────────────────────────────────────
    def _calc_wall(self, data):
        l = self._pos(data, 'length', str(_('Length')))
        h = self._pos(data, 'height', str(_('Height')))
        t = self._pos(data, 'thickness', str(_('Thickness')))
        u = data.get('unit', 'feet')
        mr = data.get('mix_ratio', '1:2:4')

        lf, hf, tf = self._to_ft(l, u), self._to_ft(h, u), self._to_ft(t, u)
        cuft = lf * hf * tf
        vol = self._volumes(cuft)
        mat = self._materials(cuft, mr)

        steps = [
            str(_('Step 1: Given dimensions')),
            f'  • {_("Length")} = {self._f(l)} {u}',
            f'  • {_("Height")} = {self._f(h)} {u}',
            f'  • {_("Thickness")} = {self._f(t)} {u}',
        ]
        if u == 'meters':
            steps += ['', str(_('Step 2: Convert to feet')),
                       f'  L = {self._f(lf)} ft, H = {self._f(hf)} ft, T = {self._f(tf)} ft']
        steps += [
            '', str(_('Step 3: Calculate volume')),
            f'  V = L × H × T = {self._f(lf)} × {self._f(hf)} × {self._f(tf)} = {self._f(cuft)} cu ft',
            '', str(_('Step 4: Unit conversions')),
            f'  {self._f(vol["cubic_yards"])} cu yd  |  {self._f(vol["cubic_meters"])} m³',
        ] + self._mat_steps(mr, mat)

        return JsonResponse({
            'success': True, 'calc_type': 'wall',
            'result': vol['cubic_yards'], 'result_label': str(_('Volume')), 'result_unit_symbol': 'cu yd',
            'formula': f'V = {self._f(l)} × {self._f(h)} × {self._f(t)} {u} = {self._f(vol["cubic_yards"])} cu yd',
            'volume': vol, 'materials': mat, 'mix_ratio': mr,
            'step_by_step': steps,
            'chart_data': {'volume_chart': self._vol_chart(vol), 'materials_chart': self._mat_chart(mat)},
        })

    # ── 6) VOLUME CONVERSION ────────────────────────────────────────
    def _calc_convert(self, data):
        v = self._pos(data, 'volume_value', str(_('Volume')))
        fu = data.get('from_unit', 'cubic_feet')
        tu = data.get('to_unit', 'cubic_yards')

        # → cubic feet base
        if fu == 'cubic_yards':
            cuft = v * 27
        elif fu == 'cubic_meters':
            cuft = v / self.CUFT_TO_CUM
        else:
            cuft = v

        # → target
        if tu == 'cubic_yards':
            result = cuft / 27
        elif tu == 'cubic_meters':
            result = cuft * self.CUFT_TO_CUM
        else:
            result = cuft

        fl = lambda u: u.replace('_', ' ').title()

        steps = [
            str(_('Step 1: Original value')),
            f'  {self._f(v, 4)} {fl(fu)}',
            '', str(_('Step 2: Convert to cubic feet')),
            f'  = {self._f(cuft, 4)} cu ft',
            '', str(_('Step 3: Convert to {unit}').format(unit=fl(tu))),
            f'  = {self._f(result, 6)} {fl(tu)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'volume_conversion',
            'result': round(result, 6),
            'result_label': str(_('Converted Volume')),
            'result_unit_symbol': fl(tu),
            'formula': f'{self._f(v, 4)} {fl(fu)} = {self._f(result, 6)} {fl(tu)}',
            'original_value': v, 'from_unit': fu,
            'converted_value': round(result, 6), 'to_unit': tu,
            'cubic_feet_equivalent': round(cuft, 2),
            'step_by_step': steps,
            'chart_data': None,
        })
