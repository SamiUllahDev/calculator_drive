from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SquareFootageCalculator(View):
    """
    Square Footage Calculator — area for 6 shapes.

    Shapes: rectangle, square, circle, triangle, trapezoid, ellipse
    Units:  ft/m/in/yd for length; ft²/m²/yd²/in²/acres/hectares for result
    """
    template_name = 'other_calculators/square_footage_calculator.html'

    # Length → feet
    LEN = {'feet': 1.0, 'meters': 3.28084, 'inches': 1/12, 'yards': 3.0}
    # Area → square feet
    AREA = {
        'square_feet': 1.0, 'square_meters': 10.7639, 'square_yards': 9.0,
        'square_inches': 1/144, 'acres': 43560.0, 'hectares': 107639.0,
    }

    UNIT_SYM = {
        'feet': 'ft', 'meters': 'm', 'inches': 'in', 'yards': 'yd',
        'square_feet': 'ft²', 'square_meters': 'm²', 'square_yards': 'yd²',
        'square_inches': 'in²', 'acres': 'acres', 'hectares': 'ha',
    }

    SHAPE_NAMES = {
        'rectangle': 'Rectangle', 'square': 'Square', 'circle': 'Circle',
        'triangle': 'Triangle', 'trapezoid': 'Trapezoid', 'ellipse': 'Ellipse',
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Square Footage Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            shape = data.get('shape', 'rectangle')
            dispatch = {
                'rectangle': self._calc_rectangle,
                'square':    self._calc_square,
                'circle':    self._calc_circle,
                'triangle':  self._calc_triangle,
                'trapezoid': self._calc_trapezoid,
                'ellipse':   self._calc_ellipse,
            }
            handler = dispatch.get(shape)
            if not handler:
                return self._err(_('Invalid shape.'))
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

    def _to_ft(self, val, unit):
        if unit not in self.LEN:
            raise ValueError(str(_('Invalid length unit.')))
        return val * self.LEN[unit]

    def _multi(self, sqft):
        """Return area in all supported units."""
        return {k: round(sqft / v, 6) for k, v in self.AREA.items()}

    def _chart(self, sqft, shape):
        labels = ['ft²', 'm²', 'yd²']
        values = [round(sqft, 2), round(sqft / 10.7639, 4), round(sqft / 9, 4)]
        colors = ['rgba(99,102,241,0.8)', 'rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)']
        borders = ['#6366f1', '#10b981', '#f59e0b']
        return {'main_chart': {
            'type': 'bar',
            'data': {'labels': labels, 'datasets': [{
                'label': str(_('Area')), 'data': values,
                'backgroundColor': colors, 'borderColor': borders,
                'borderWidth': 2, 'borderRadius': 6,
            }]},
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(_('{shape} Area').format(shape=shape))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

    def _respond(self, shape, sqft, result_unit, formula, steps):
        result = sqft / self.AREA.get(result_unit, 1.0)
        multi = self._multi(sqft)
        return JsonResponse({
            'success': True, 'shape': shape,
            'result': round(result, 6),
            'result_label': str(_('{shape} Area').format(shape=self.SHAPE_NAMES.get(shape, shape))),
            'result_unit_symbol': self._sym(result_unit),
            'area_all': multi,
            'formula': formula,
            'step_by_step': steps,
            'chart_data': self._chart(sqft, self.SHAPE_NAMES.get(shape, shape)),
        })

    # ── 1) RECTANGLE ─────────────────────────────────────────────────
    def _calc_rectangle(self, data):
        l = self._pos(data, 'length', str(_('Length')))
        w = self._pos(data, 'width', str(_('Width')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')
        lf, wf = self._to_ft(l, lu), self._to_ft(w, lu)
        sqft = lf * wf
        result = sqft / self.AREA.get(ru, 1.0)
        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Length")} = {self._f(l)} {self._sym(lu)}',
            f'  • {_("Width")} = {self._f(w)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  L = {self._f(lf)} ft, W = {self._f(wf)} ft',
            '', str(_('Step 3: Area = L × W')),
            f'  {self._f(lf)} × {self._f(wf)} = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 6)} {self._sym(ru)}',
        ]
        return self._respond('rectangle', sqft, ru,
            f'{self._f(l)} × {self._f(w)} {self._sym(lu)} = {self._f(result, 4)} {self._sym(ru)}', steps)

    # ── 2) SQUARE ────────────────────────────────────────────────────
    def _calc_square(self, data):
        s = self._pos(data, 'side', str(_('Side')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')
        sf = self._to_ft(s, lu)
        sqft = sf * sf
        result = sqft / self.AREA.get(ru, 1.0)
        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Side")} = {self._f(s)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  s = {self._f(sf)} ft',
            '', str(_('Step 3: Area = s²')),
            f'  {self._f(sf)}² = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 6)} {self._sym(ru)}',
        ]
        return self._respond('square', sqft, ru,
            f'{self._f(s)}² {self._sym(lu)} = {self._f(result, 4)} {self._sym(ru)}', steps)

    # ── 3) CIRCLE ────────────────────────────────────────────────────
    def _calc_circle(self, data):
        r = self._pos(data, 'radius', str(_('Radius')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')
        rf = self._to_ft(r, lu)
        sqft = math.pi * rf * rf
        result = sqft / self.AREA.get(ru, 1.0)
        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Radius")} = {self._f(r)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  r = {self._f(rf)} ft',
            '', str(_('Step 3: Area = π × r²')),
            f'  π × {self._f(rf)}² = π × {self._f(rf*rf)} = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 6)} {self._sym(ru)}',
        ]
        return self._respond('circle', sqft, ru,
            f'π × {self._f(r)}² {self._sym(lu)} = {self._f(result, 4)} {self._sym(ru)}', steps)

    # ── 4) TRIANGLE ──────────────────────────────────────────────────
    def _calc_triangle(self, data):
        b = self._pos(data, 'base', str(_('Base')))
        h = self._pos(data, 'height', str(_('Height')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')
        bf, hf = self._to_ft(b, lu), self._to_ft(h, lu)
        sqft = 0.5 * bf * hf
        result = sqft / self.AREA.get(ru, 1.0)
        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Base")} = {self._f(b)} {self._sym(lu)}',
            f'  • {_("Height")} = {self._f(h)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  b = {self._f(bf)} ft, h = {self._f(hf)} ft',
            '', str(_('Step 3: Area = ½ × b × h')),
            f'  0.5 × {self._f(bf)} × {self._f(hf)} = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 6)} {self._sym(ru)}',
        ]
        return self._respond('triangle', sqft, ru,
            f'½ × {self._f(b)} × {self._f(h)} {self._sym(lu)} = {self._f(result, 4)} {self._sym(ru)}', steps)

    # ── 5) TRAPEZOID ─────────────────────────────────────────────────
    def _calc_trapezoid(self, data):
        b1 = self._pos(data, 'base1', str(_('Base 1')))
        b2 = self._pos(data, 'base2', str(_('Base 2')))
        h = self._pos(data, 'height', str(_('Height')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')
        b1f, b2f, hf = self._to_ft(b1, lu), self._to_ft(b2, lu), self._to_ft(h, lu)
        sqft = 0.5 * (b1f + b2f) * hf
        result = sqft / self.AREA.get(ru, 1.0)
        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Base 1")} = {self._f(b1)} {self._sym(lu)}',
            f'  • {_("Base 2")} = {self._f(b2)} {self._sym(lu)}',
            f'  • {_("Height")} = {self._f(h)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  b₁ = {self._f(b1f)}, b₂ = {self._f(b2f)}, h = {self._f(hf)} ft',
            '', str(_('Step 3: Area = ½ × (b₁ + b₂) × h')),
            f'  0.5 × ({self._f(b1f)} + {self._f(b2f)}) × {self._f(hf)} = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 6)} {self._sym(ru)}',
        ]
        return self._respond('trapezoid', sqft, ru,
            f'½({self._f(b1)}+{self._f(b2)})×{self._f(h)} {self._sym(lu)} = {self._f(result, 4)} {self._sym(ru)}', steps)

    # ── 6) ELLIPSE ───────────────────────────────────────────────────
    def _calc_ellipse(self, data):
        a = self._pos(data, 'radius_a', str(_('Radius A')))
        b = self._pos(data, 'radius_b', str(_('Radius B')))
        lu = data.get('length_unit', 'feet')
        ru = data.get('result_unit', 'square_feet')
        af, bf = self._to_ft(a, lu), self._to_ft(b, lu)
        sqft = math.pi * af * bf
        result = sqft / self.AREA.get(ru, 1.0)
        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Radius A")} = {self._f(a)} {self._sym(lu)}',
            f'  • {_("Radius B")} = {self._f(b)} {self._sym(lu)}',
            '', str(_('Step 2: Convert to feet')),
            f'  a = {self._f(af)} ft, b = {self._f(bf)} ft',
            '', str(_('Step 3: Area = π × a × b')),
            f'  π × {self._f(af)} × {self._f(bf)} = {self._f(sqft)} ft²',
            '', str(_('Step 4: Convert to {unit}').format(unit=self._sym(ru))),
            f'  = {self._f(result, 6)} {self._sym(ru)}',
        ]
        return self._respond('ellipse', sqft, ru,
            f'π × {self._f(a)} × {self._f(b)} {self._sym(lu)} = {self._f(result, 4)} {self._sym(ru)}', steps)
