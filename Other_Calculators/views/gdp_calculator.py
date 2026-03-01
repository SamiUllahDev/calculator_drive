from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GdpCalculator(View):
    """
    GDP Calculator — 10 calculation types.

    Calculation types
        • expenditure  → GDP = C + I + G + (X − M)
        • income       → GDP = W + R + I + P
        • growth_rate  → ((Current − Previous) / Previous) × 100
        • per_capita   → GDP / Population
        • deflator     → (Nominal / Real) × 100
        • convert      → unit conversion between millions / billions / trillions
        • real_gdp     → Nominal GDP / (Deflator / 100)
        • projection   → GDP × (1 + rate)^years  (compound growth)
        • debt_ratio   → (National Debt / GDP) × 100
        • output_gap   → ((Actual − Potential) / Potential) × 100
    """
    template_name = 'other_calculators/gdp_calculator.html'

    UNIT_FACTORS = {
        'millions':  1e-3,    # → billions
        'billions':  1.0,
        'trillions': 1e3,
    }

    UNIT_LABELS = {
        'millions':  str(_('Million')),
        'billions':  str(_('Billion')),
        'trillions': str(_('Trillion')),
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('GDP Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'expenditure')
            dispatch = {
                'expenditure': self._calc_expenditure,
                'income':      self._calc_income,
                'growth_rate': self._calc_growth_rate,
                'per_capita':  self._calc_per_capita,
                'deflator':    self._calc_deflator,
                'convert':     self._calc_convert,
                'real_gdp':    self._calc_real_gdp,
                'projection':  self._calc_projection,
                'debt_ratio':  self._calc_debt_ratio,
                'output_gap':  self._calc_output_gap,
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

    def _ul(self, unit):
        return self.UNIT_LABELS.get(unit, unit)

    def _to_base(self, val, unit):
        return val * self.UNIT_FACTORS.get(unit, 1.0)

    def _from_base(self, val, unit):
        f = self.UNIT_FACTORS.get(unit, 1.0)
        return val / f if f else val

    @staticmethod
    def _fmt(v, dp=2):
        if abs(v) >= 1e12:
            return f'{v:.4e}'
        return f'{v:,.{dp}f}'

    # ── 1) EXPENDITURE APPROACH ──────────────────────────────────────
    def _calc_expenditure(self, data):
        for field in ('consumption', 'investment', 'government', 'exports', 'imports'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.capitalize()))

        C = float(data['consumption'])
        I = float(data['investment'])
        G = float(data['government'])
        X = float(data['exports'])
        M = float(data['imports'])
        unit = data.get('unit', 'billions')
        result_unit = data.get('result_unit', 'billions')

        if unit not in self.UNIT_FACTORS or result_unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        for v, n in [(C, 'Consumption'), (I, 'Investment'), (G, 'Government'), (X, 'Exports'), (M, 'Imports')]:
            if v < 0:
                return self._err(_('{n} must be non-negative.').format(n=n))

        Cb = self._to_base(C, unit)
        Ib = self._to_base(I, unit)
        Gb = self._to_base(G, unit)
        Xb = self._to_base(X, unit)
        Mb = self._to_base(M, unit)
        NX = Xb - Mb
        gdp_b = Cb + Ib + Gb + NX
        gdp_r = self._from_base(gdp_b, result_unit)

        if math.isinf(gdp_r) or math.isnan(gdp_r):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • C = {self._fmt(C)} {ul(unit)}',
            f'  • I = {self._fmt(I)} {ul(unit)}',
            f'  • G = {self._fmt(G)} {ul(unit)}',
            f'  • X = {self._fmt(X)} {ul(unit)}',
            f'  • M = {self._fmt(M)} {ul(unit)}',
            '',
            str(_('Step 2: Calculate net exports')),
            f'  NX = X − M = {self._fmt(Xb)} − {self._fmt(Mb)} = {self._fmt(NX)} {_("Billion")}',
            '',
            str(_('Step 3: Apply expenditure formula')),
            f'  GDP = C + I + G + NX',
            f'  GDP = {self._fmt(Cb)} + {self._fmt(Ib)} + {self._fmt(Gb)} + {self._fmt(NX)}',
            f'  GDP = {self._fmt(gdp_b)} {_("Billion")}',
            '',
        ]
        if result_unit != 'billions':
            steps.append(str(_('Step 4: Convert to {u}').format(u=ul(result_unit))))
            steps.append(f'  GDP = {self._fmt(gdp_r)} {ul(result_unit)}')
            steps.append('')
        steps.append(str(_('Result: GDP = {v} {u}').format(v=self._fmt(gdp_r), u=ul(result_unit))))

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Consumption')), str(_('Investment')), str(_('Government')),
                               str(_('Exports')), str(_('Imports')), str(_('Net Exports')), 'GDP'],
                    'datasets': [{
                        'label': str(_('GDP Components (Billion)')),
                        'data': [round(Cb, 2), round(Ib, 2), round(Gb, 2),
                                 round(Xb, 2), round(Mb, 2), round(NX, 2), round(gdp_b, 2)],
                        'backgroundColor': [
                            'rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)', 'rgba(245,158,11,0.7)',
                            'rgba(139,92,246,0.7)', 'rgba(236,72,153,0.7)',
                            'rgba(99,102,241,0.7)', 'rgba(239,68,68,0.7)'],
                        'borderColor': ['#3b82f6', '#10b981', '#f59e0b',
                                        '#8b5cf6', '#ec4899', '#6366f1', '#ef4444'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True, 'text': str(_('Expenditure Approach Breakdown'))}},
                    'scales': {'y': {'beginAtZero': True,
                                     'title': {'display': True, 'text': str(_('Billion'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'expenditure',
            'result': round(gdp_r, 4), 'result_label': str(_('GDP (Expenditure)')),
            'gdp': round(gdp_r, 4), 'result_unit': result_unit,
            'consumption': C, 'investment': I, 'government': G,
            'exports': X, 'imports': M, 'net_exports': round(self._from_base(NX, result_unit), 4),
            'formula': f'GDP = C + I + G + (X−M) = {self._fmt(gdp_r)} {ul(result_unit)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Consumption (C)')), 'value': self._fmt(C), 'color': 'blue'},
                {'label': str(_('Investment (I)')), 'value': self._fmt(I), 'color': 'green'},
                {'label': str(_('Government (G)')), 'value': self._fmt(G), 'color': 'yellow'},
                {'label': str(_('Net Exports (X−M)')), 'value': self._fmt(self._from_base(NX, result_unit)), 'color': 'purple'},
            ],
        })

    # ── 2) INCOME APPROACH ───────────────────────────────────────────
    def _calc_income(self, data):
        for field in ('wages', 'rent', 'interest', 'profit'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.capitalize()))

        W = float(data['wages'])
        R = float(data['rent'])
        In = float(data['interest'])
        P = float(data['profit'])
        unit = data.get('unit', 'billions')
        result_unit = data.get('result_unit', 'billions')

        if unit not in self.UNIT_FACTORS or result_unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        for v, n in [(W, 'Wages'), (R, 'Rent'), (In, 'Interest')]:
            if v < 0:
                return self._err(_('{n} must be non-negative.').format(n=n))

        Wb = self._to_base(W, unit)
        Rb = self._to_base(R, unit)
        Ib = self._to_base(In, unit)
        Pb = self._to_base(P, unit)
        gdp_b = Wb + Rb + Ib + Pb
        gdp_r = self._from_base(gdp_b, result_unit)

        if math.isinf(gdp_r) or math.isnan(gdp_r):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • W = {self._fmt(W)} {ul(unit)}',
            f'  • R = {self._fmt(R)} {ul(unit)}',
            f'  • I = {self._fmt(In)} {ul(unit)}',
            f'  • P = {self._fmt(P)} {ul(unit)}',
            '',
            str(_('Step 2: Apply income formula')),
            f'  GDP = W + R + I + P',
            f'  GDP = {self._fmt(Wb)} + {self._fmt(Rb)} + {self._fmt(Ib)} + {self._fmt(Pb)}',
            f'  GDP = {self._fmt(gdp_b)} {_("Billion")}',
            '',
        ]
        if result_unit != 'billions':
            steps.append(str(_('Step 3: Convert to {u}').format(u=ul(result_unit))))
            steps.append(f'  GDP = {self._fmt(gdp_r)} {ul(result_unit)}')
            steps.append('')
        steps.append(str(_('Result: GDP = {v} {u}').format(v=self._fmt(gdp_r), u=ul(result_unit))))

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Wages')), str(_('Rent')), str(_('Interest')),
                               str(_('Profit')), 'GDP'],
                    'datasets': [{
                        'label': str(_('GDP Components (Billion)')),
                        'data': [round(Wb, 2), round(Rb, 2), round(Ib, 2), round(Pb, 2), round(gdp_b, 2)],
                        'backgroundColor': [
                            'rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)',
                            'rgba(245,158,11,0.7)', 'rgba(139,92,246,0.7)', 'rgba(239,68,68,0.7)'],
                        'borderColor': ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True, 'text': str(_('Income Approach Breakdown'))}},
                    'scales': {'y': {'beginAtZero': True,
                                     'title': {'display': True, 'text': str(_('Billion'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'income',
            'result': round(gdp_r, 4), 'result_label': str(_('GDP (Income)')),
            'gdp': round(gdp_r, 4), 'result_unit': result_unit,
            'wages': W, 'rent': R, 'interest': In, 'profit': P,
            'formula': f'GDP = W + R + I + P = {self._fmt(gdp_r)} {ul(result_unit)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Wages (W)')), 'value': self._fmt(W), 'color': 'blue'},
                {'label': str(_('Rent (R)')), 'value': self._fmt(R), 'color': 'green'},
                {'label': str(_('Interest (I)')), 'value': self._fmt(In), 'color': 'yellow'},
                {'label': str(_('Profit (P)')), 'value': self._fmt(P), 'color': 'purple'},
            ],
        })

    # ── 3) GROWTH RATE ───────────────────────────────────────────────
    def _calc_growth_rate(self, data):
        for field in ('gdp_current', 'gdp_previous'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.replace('_', ' ').title()))

        cur = float(data['gdp_current'])
        prev = float(data['gdp_previous'])
        unit = data.get('unit', 'billions')

        if unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if cur < 0 or prev < 0:
            return self._err(_('GDP values must be non-negative.'))
        if prev == 0:
            return self._err(_('Previous GDP cannot be zero.'))

        cur_b = self._to_base(cur, unit)
        prev_b = self._to_base(prev, unit)
        change = cur_b - prev_b
        rate = (change / prev_b) * 100

        if math.isinf(rate) or math.isnan(rate):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • {_("Current GDP")} = {self._fmt(cur)} {ul(unit)}',
            f'  • {_("Previous GDP")} = {self._fmt(prev)} {ul(unit)}',
            '',
            str(_('Step 2: Calculate change')),
            f'  Δ = {self._fmt(cur_b)} − {self._fmt(prev_b)} = {self._fmt(change)} {_("Billion")}',
            '',
            str(_('Step 3: Apply growth rate formula')),
            f'  {_("Growth Rate")} = (Δ / {_("Previous")}) × 100',
            f'  = ({self._fmt(change)} / {self._fmt(prev_b)}) × 100',
            f'  = {self._fmt(rate)}%',
            '',
            str(_('Result: Growth Rate = {v}%').format(v=self._fmt(rate))),
        ]

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Previous GDP')), str(_('Current GDP'))],
                    'datasets': [{
                        'label': str(_('GDP (Billion)')),
                        'data': [round(prev_b, 2), round(cur_b, 2)],
                        'backgroundColor': ['rgba(99,102,241,0.7)', 'rgba(16,185,129,0.7)'],
                        'borderColor': ['#6366f1', '#10b981'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True,
                                          'text': str(_('GDP Growth: {r}%').format(r=self._fmt(rate)))}},
                    'scales': {'y': {'beginAtZero': True,
                                     'title': {'display': True, 'text': str(_('Billion'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'growth_rate',
            'result': round(rate, 4), 'result_label': str(_('GDP Growth Rate')),
            'growth_rate': round(rate, 4),
            'gdp_current': cur, 'gdp_previous': prev, 'unit': unit,
            'formula': f'Growth = (({self._fmt(cur_b)} − {self._fmt(prev_b)}) / {self._fmt(prev_b)}) × 100 = {self._fmt(rate)}%',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Current GDP')), 'value': f'{self._fmt(cur)} {ul(unit)}', 'color': 'green'},
                {'label': str(_('Previous GDP')), 'value': f'{self._fmt(prev)} {ul(unit)}', 'color': 'blue'},
                {'label': str(_('Change')), 'value': f'{self._fmt(change)} B', 'color': 'yellow'},
                {'label': str(_('Growth Rate')), 'value': f'{self._fmt(rate)}%', 'color': 'purple'},
            ],
        })

    # ── 4) PER CAPITA ────────────────────────────────────────────────
    def _calc_per_capita(self, data):
        for field in ('gdp', 'population'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.upper() if field == 'gdp' else field.title()))

        gdp = float(data['gdp'])
        pop = float(data['population'])
        gdp_unit = data.get('gdp_unit', 'billions')
        pop_unit = data.get('population_unit', 'millions')

        if gdp_unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid GDP unit.'))
        if gdp < 0:
            return self._err(_('GDP must be non-negative.'))
        if pop <= 0:
            return self._err(_('Population must be greater than zero.'))

        gdp_b = self._to_base(gdp, gdp_unit)

        # Convert population to actual people
        pop_mult = {'thousands': 1e3, 'millions': 1e6, 'billions': 1e9}
        pop_actual = pop * pop_mult.get(pop_unit, 1e6)

        # GDP in actual dollars = gdp_b * 1e9  (billions → actual)
        gdp_actual = gdp_b * 1e9
        per_capita = gdp_actual / pop_actual

        if math.isinf(per_capita) or math.isnan(per_capita):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • GDP = {self._fmt(gdp)} {ul(gdp_unit)}',
            f'  • {_("Population")} = {self._fmt(pop)} {pop_unit}',
            '',
            str(_('Step 2: Convert to absolute values')),
            f'  GDP = {self._fmt(gdp_b)} {_("Billion")} = ${self._fmt(gdp_actual, 0)}',
            f'  {_("Population")} = {self._fmt(pop_actual, 0)} {_("people")}',
            '',
            str(_('Step 3: Calculate per capita')),
            f'  {_("GDP per Capita")} = GDP / {_("Population")}',
            f'  = ${self._fmt(gdp_actual, 0)} / {self._fmt(pop_actual, 0)}',
            f'  = ${self._fmt(per_capita)}',
            '',
            str(_('Result: GDP per Capita = ${v}').format(v=self._fmt(per_capita))),
        ]

        chart = {
            'main_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': [f'GDP ({ul(gdp_unit)})', f'{_("Population")} ({pop_unit})',
                               str(_('Per Capita ($)'))],
                    'datasets': [{
                        'data': [round(gdp, 2), round(pop, 2), round(per_capita, 2)],
                        'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)',
                                            'rgba(245,158,11,0.7)'],
                        'borderColor': ['#3b82f6', '#10b981', '#f59e0b'],
                        'borderWidth': 2,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': True, 'position': 'bottom'},
                                'title': {'display': True, 'text': str(_('GDP Per Capita Breakdown'))}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'per_capita',
            'result': round(per_capita, 2), 'result_label': str(_('GDP Per Capita')),
            'gdp_per_capita': round(per_capita, 2),
            'gdp': gdp, 'gdp_unit': gdp_unit,
            'population': pop, 'population_unit': pop_unit,
            'formula': f'GDP/Pop = ${self._fmt(gdp_actual,0)} / {self._fmt(pop_actual,0)} = ${self._fmt(per_capita)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': 'GDP', 'value': f'{self._fmt(gdp)} {ul(gdp_unit)}', 'color': 'blue'},
                {'label': str(_('Population')), 'value': f'{self._fmt(pop)} {pop_unit}', 'color': 'green'},
                {'label': str(_('Per Capita')), 'value': f'${self._fmt(per_capita)}', 'color': 'yellow'},
            ],
        })

    # ── 5) DEFLATOR ──────────────────────────────────────────────────
    def _calc_deflator(self, data):
        for field in ('nominal_gdp', 'real_gdp'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.replace('_', ' ').title()))

        nom = float(data['nominal_gdp'])
        real = float(data['real_gdp'])
        unit = data.get('unit', 'billions')

        if unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if nom < 0 or real < 0:
            return self._err(_('GDP values must be non-negative.'))
        if real == 0:
            return self._err(_('Real GDP cannot be zero.'))

        nom_b = self._to_base(nom, unit)
        real_b = self._to_base(real, unit)
        deflator = (nom_b / real_b) * 100
        inflation = deflator - 100

        if math.isinf(deflator) or math.isnan(deflator):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • {_("Nominal GDP")} = {self._fmt(nom)} {ul(unit)}',
            f'  • {_("Real GDP")} = {self._fmt(real)} {ul(unit)}',
            '',
            str(_('Step 2: Apply deflator formula')),
            f'  {_("GDP Deflator")} = ({_("Nominal")} / {_("Real")}) × 100',
            f'  = ({self._fmt(nom_b)} / {self._fmt(real_b)}) × 100',
            f'  = {self._fmt(deflator)}',
            '',
            str(_('Step 3: Interpret result')),
            f'  • {_("Deflator")} = 100 → {_("no inflation")}',
            f'  • {_("Deflator")} > 100 → {_("inflation")}',
            f'  • {_("Deflator")} < 100 → {_("deflation")}',
            f'  • {_("Your value")}: {self._fmt(deflator)} → {_("inflation") if inflation > 0 else _("deflation") if inflation < 0 else _("no change")} ({self._fmt(abs(inflation))}%)',
            '',
            str(_('Result: GDP Deflator = {v}').format(v=self._fmt(deflator))),
        ]

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Nominal GDP')), str(_('Real GDP')), str(_('Deflator'))],
                    'datasets': [{
                        'label': str(_('GDP Values')),
                        'data': [round(nom_b, 2), round(real_b, 2), round(deflator, 2)],
                        'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)',
                                            'rgba(245,158,11,0.7)'],
                        'borderColor': ['#3b82f6', '#10b981', '#f59e0b'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True, 'text': str(_('GDP Deflator'))}},
                    'scales': {'y': {'beginAtZero': True}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'deflator',
            'result': round(deflator, 4), 'result_label': str(_('GDP Deflator')),
            'deflator': round(deflator, 4),
            'nominal_gdp': nom, 'real_gdp': real, 'unit': unit,
            'inflation_rate': round(inflation, 4),
            'formula': f'Deflator = ({self._fmt(nom_b)} / {self._fmt(real_b)}) × 100 = {self._fmt(deflator)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Nominal GDP')), 'value': f'{self._fmt(nom)} {ul(unit)}', 'color': 'blue'},
                {'label': str(_('Real GDP')), 'value': f'{self._fmt(real)} {ul(unit)}', 'color': 'green'},
                {'label': str(_('Deflator')), 'value': self._fmt(deflator), 'color': 'yellow'},
                {'label': str(_('Inflation')), 'value': f'{self._fmt(inflation)}%', 'color': 'purple'},
            ],
        })

    # ── 6) CONVERT UNITS ─────────────────────────────────────────────
    def _calc_convert(self, data):
        if 'value' not in data or data['value'] is None or data['value'] == '':
            return self._err(_('GDP value is required.'))

        val = float(data['value'])
        fr = data.get('from_unit', 'billions')
        to = data.get('to_unit', 'billions')

        if fr not in self.UNIT_FACTORS or to not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if val < 0:
            return self._err(_('Value must be non-negative.'))

        base = self._to_base(val, fr)
        result = self._from_base(base, to)

        if math.isinf(result) or math.isnan(result):
            return self._err(_('Invalid conversion result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Given value')),
            f'  {self._fmt(val)} {ul(fr)}',
            '',
            str(_('Step 2: Convert to billions (base unit)')),
            f'  {self._fmt(val)} {ul(fr)} = {self._fmt(base)} {_("Billion")}',
            '',
            str(_('Step 3: Convert to {u}').format(u=ul(to))),
            f'  {self._fmt(base)} {_("Billion")} = {self._fmt(result)} {ul(to)}',
            '',
            str(_('Result: {v1} {u1} = {v2} {u2}').format(
                v1=self._fmt(val), u1=ul(fr), v2=self._fmt(result), u2=ul(to))),
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'convert',
            'result': round(result, 6), 'result_label': str(_('Converted Value')),
            'value': val, 'from_unit': fr, 'to_unit': to,
            'formula': f'{self._fmt(val)} {ul(fr)} = {self._fmt(result)} {ul(to)}',
            'step_by_step': steps,
            'detail_cards': [
                {'label': str(_('From')), 'value': f'{self._fmt(val)} {ul(fr)}', 'color': 'blue'},
                {'label': str(_('To')), 'value': f'{self._fmt(result)} {ul(to)}', 'color': 'green'},
            ],
        })

    # ── 7) REAL GDP ──────────────────────────────────────────────────
    def _calc_real_gdp(self, data):
        """Real GDP = Nominal GDP / (Deflator / 100)"""
        for field in ('nominal_gdp', 'deflator_value'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.replace('_', ' ').title()))

        nom = float(data['nominal_gdp'])
        defl = float(data['deflator_value'])
        unit = data.get('unit', 'billions')
        result_unit = data.get('result_unit', 'billions')

        if unit not in self.UNIT_FACTORS or result_unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if nom < 0:
            return self._err(_('Nominal GDP must be non-negative.'))
        if defl <= 0:
            return self._err(_('GDP Deflator must be greater than zero.'))

        nom_b = self._to_base(nom, unit)
        real_b = nom_b / (defl / 100)
        real_r = self._from_base(real_b, result_unit)
        inflation = defl - 100

        if math.isinf(real_r) or math.isnan(real_r):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • {_("Nominal GDP")} = {self._fmt(nom)} {ul(unit)}',
            f'  • {_("GDP Deflator")} = {self._fmt(defl)}',
            '',
            str(_('Step 2: Apply Real GDP formula')),
            f'  {_("Real GDP")} = {_("Nominal GDP")} / ({_("Deflator")} / 100)',
            f'  = {self._fmt(nom_b)} / ({self._fmt(defl)} / 100)',
            f'  = {self._fmt(nom_b)} / {self._fmt(defl / 100)}',
            f'  = {self._fmt(real_b)} {_("Billion")}',
            '',
            str(_('Step 3: Interpret')),
            f'  • {_("Deflator")} = {self._fmt(defl)} → {_("prices are")}{" " + self._fmt(abs(inflation)) + "% " + (str(_("higher")) if inflation > 0 else str(_("lower"))) if inflation != 0 else " " + str(_("unchanged"))}',
            f'  • {_("Real GDP adjusts for this price change")}',
            '',
        ]
        if result_unit != 'billions':
            steps.append(str(_('Step 4: Convert to {u}').format(u=ul(result_unit))))
            steps.append(f'  {_("Real GDP")} = {self._fmt(real_r)} {ul(result_unit)}')
            steps.append('')
        steps.append(str(_('Result: Real GDP = {v} {u}').format(v=self._fmt(real_r), u=ul(result_unit))))

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Nominal GDP')), str(_('Real GDP')), str(_('Deflator'))],
                    'datasets': [{
                        'label': str(_('GDP Values')),
                        'data': [round(nom_b, 2), round(real_b, 2), round(defl, 2)],
                        'backgroundColor': ['rgba(59,130,246,0.7)', 'rgba(16,185,129,0.7)',
                                            'rgba(245,158,11,0.7)'],
                        'borderColor': ['#3b82f6', '#10b981', '#f59e0b'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True, 'text': str(_('Nominal vs Real GDP'))}},
                    'scales': {'y': {'beginAtZero': True,
                                     'title': {'display': True, 'text': str(_('Billion'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'real_gdp',
            'result': round(real_r, 4), 'result_label': str(_('Real GDP')),
            'real_gdp': round(real_r, 4), 'nominal_gdp': nom,
            'deflator_value': defl, 'result_unit': result_unit,
            'formula': f'Real GDP = {self._fmt(nom_b)} / ({self._fmt(defl)}/100) = {self._fmt(real_r)} {ul(result_unit)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Nominal GDP')), 'value': f'{self._fmt(nom)} {ul(unit)}', 'color': 'blue'},
                {'label': str(_('Deflator')), 'value': self._fmt(defl), 'color': 'yellow'},
                {'label': str(_('Real GDP')), 'value': f'{self._fmt(real_r)} {ul(result_unit)}', 'color': 'green'},
                {'label': str(_('Inflation')), 'value': f'{self._fmt(inflation)}%', 'color': 'purple'},
            ],
        })

    # ── 8) GDP PROJECTION (Compound Growth) ──────────────────────────
    def _calc_projection(self, data):
        """Future GDP = Current GDP × (1 + rate/100)^years"""
        for field in ('current_gdp', 'growth_rate', 'years'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.replace('_', ' ').title()))

        gdp = float(data['current_gdp'])
        rate = float(data['growth_rate'])
        years = int(data['years'])
        unit = data.get('unit', 'billions')

        if unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if gdp <= 0:
            return self._err(_('Current GDP must be positive.'))
        if years < 1 or years > 100:
            return self._err(_('Years must be between 1 and 100.'))
        if rate < -50 or rate > 100:
            return self._err(_('Growth rate must be between -50% and 100%.'))

        gdp_b = self._to_base(gdp, unit)
        multiplier = (1 + rate / 100)
        future_b = gdp_b * (multiplier ** years)
        total_growth = ((future_b - gdp_b) / gdp_b) * 100
        future_r = self._from_base(future_b, unit)

        if math.isinf(future_b) or math.isnan(future_b):
            return self._err(_('Invalid calculation result.'))

        ul = self._ul
        # Build year-by-year projection for chart
        proj_labels = [str(_('Year {n}').format(n=i)) for i in range(years + 1)]
        proj_values = [round(self._from_base(gdp_b * (multiplier ** i), unit), 2) for i in range(years + 1)]

        steps = [
            str(_('Step 1: Identify given values')),
            f'  • {_("Current GDP")} = {self._fmt(gdp)} {ul(unit)}',
            f'  • {_("Annual Growth Rate")} = {self._fmt(rate)}%',
            f'  • {_("Forecast Period")} = {years} {_("years")}',
            '',
            str(_('Step 2: Apply compound growth formula')),
            f'  {_("Future GDP")} = {_("Current GDP")} × (1 + rate/100)^years',
            f'  = {self._fmt(gdp_b)} × (1 + {self._fmt(rate)}/100)^{years}',
            f'  = {self._fmt(gdp_b)} × {self._fmt(multiplier)}^{years}',
            f'  = {self._fmt(gdp_b)} × {self._fmt(multiplier ** years, 4)}',
            f'  = {self._fmt(future_b)} {_("Billion")}',
            '',
            str(_('Step 3: Calculate total growth')),
            f'  {_("Total Growth")} = (({self._fmt(future_b)} − {self._fmt(gdp_b)}) / {self._fmt(gdp_b)}) × 100',
            f'  = {self._fmt(total_growth)}%',
            '',
        ]
        # Show a few yearly milestones
        milestones = [1, 5, 10, 25, 50, years]
        milestones = sorted(set(y for y in milestones if 1 <= y <= years))
        steps.append(str(_('Key milestones:')))
        for y in milestones:
            val_y = self._from_base(gdp_b * (multiplier ** y), unit)
            steps.append(f'  • {_("Year")} {y}: {self._fmt(val_y)} {ul(unit)}')
        steps.append('')
        steps.append(str(_('Result: GDP after {n} years = {v} {u}').format(
            n=years, v=self._fmt(future_r), u=ul(unit))))

        chart = {
            'main_chart': {
                'type': 'line',
                'data': {
                    'labels': proj_labels,
                    'datasets': [{
                        'label': f'GDP ({ul(unit)})',
                        'data': proj_values,
                        'borderColor': '#3b82f6',
                        'backgroundColor': 'rgba(59,130,246,0.1)',
                        'borderWidth': 3, 'fill': True, 'tension': 0.3,
                        'pointRadius': 3 if years <= 20 else 0,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {
                        'legend': {'display': True, 'position': 'bottom'},
                        'title': {'display': True,
                                  'text': str(_('GDP Projection: {r}% over {n} years').format(r=self._fmt(rate), n=years))},
                    },
                    'scales': {'y': {'beginAtZero': False,
                                     'title': {'display': True, 'text': ul(unit)}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'projection',
            'result': round(future_r, 4), 'result_label': str(_('Projected GDP')),
            'future_gdp': round(future_r, 4),
            'current_gdp': gdp, 'growth_rate': rate, 'years': years, 'unit': unit,
            'total_growth': round(total_growth, 4),
            'formula': f'GDP × (1+{self._fmt(rate)}%)^{years} = {self._fmt(future_r)} {ul(unit)}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Current GDP')), 'value': f'{self._fmt(gdp)} {ul(unit)}', 'color': 'blue'},
                {'label': str(_('Growth Rate')), 'value': f'{self._fmt(rate)}%', 'color': 'green'},
                {'label': str(_('Years')), 'value': str(years), 'color': 'yellow'},
                {'label': str(_('Projected GDP')), 'value': f'{self._fmt(future_r)} {ul(unit)}', 'color': 'purple'},
            ],
        })

    # ── 9) DEBT-TO-GDP RATIO ─────────────────────────────────────────
    def _calc_debt_ratio(self, data):
        """Debt-to-GDP = (National Debt / GDP) × 100"""
        for field in ('national_debt', 'gdp'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(
                    field='National Debt' if field == 'national_debt' else 'GDP'))

        debt = float(data['national_debt'])
        gdp = float(data['gdp'])
        unit = data.get('unit', 'billions')

        if unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if debt < 0:
            return self._err(_('National debt must be non-negative.'))
        if gdp <= 0:
            return self._err(_('GDP must be greater than zero.'))

        debt_b = self._to_base(debt, unit)
        gdp_b = self._to_base(gdp, unit)
        ratio = (debt_b / gdp_b) * 100

        if math.isinf(ratio) or math.isnan(ratio):
            return self._err(_('Invalid calculation result.'))

        # Interpretation
        if ratio < 60:
            health = str(_('Healthy — below 60% threshold'))
        elif ratio < 90:
            health = str(_('Moderate — between 60-90% (Maastricht guideline is 60%)'))
        elif ratio < 120:
            health = str(_('High — above 90% may slow growth'))
        else:
            health = str(_('Very High — above 120%, significant risk'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • {_("National Debt")} = {self._fmt(debt)} {ul(unit)}',
            f'  • GDP = {self._fmt(gdp)} {ul(unit)}',
            '',
            str(_('Step 2: Apply debt-to-GDP formula')),
            f'  {_("Debt-to-GDP Ratio")} = ({_("Debt")} / GDP) × 100',
            f'  = ({self._fmt(debt_b)} / {self._fmt(gdp_b)}) × 100',
            f'  = {self._fmt(ratio)}%',
            '',
            str(_('Step 3: Interpret result')),
            f'  • {_("Ratio")}: {self._fmt(ratio)}%',
            f'  • {_("Assessment")}: {health}',
            f'  • {_("For every $100 of GDP, the country owes")} ${self._fmt(ratio)}',
            '',
            str(_('Result: Debt-to-GDP Ratio = {v}%').format(v=self._fmt(ratio))),
        ]

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('National Debt')), 'GDP'],
                    'datasets': [{
                        'label': f'{ul(unit)}',
                        'data': [round(debt_b, 2), round(gdp_b, 2)],
                        'backgroundColor': ['rgba(239,68,68,0.7)', 'rgba(16,185,129,0.7)'],
                        'borderColor': ['#ef4444', '#10b981'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True,
                                          'text': str(_('Debt vs GDP — Ratio: {r}%').format(r=self._fmt(ratio)))}},
                    'scales': {'y': {'beginAtZero': True,
                                     'title': {'display': True, 'text': str(_('Billion'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'debt_ratio',
            'result': round(ratio, 4), 'result_label': str(_('Debt-to-GDP Ratio')),
            'debt_ratio': round(ratio, 4),
            'national_debt': debt, 'gdp': gdp, 'unit': unit,
            'health': health,
            'formula': f'({self._fmt(debt_b)} / {self._fmt(gdp_b)}) × 100 = {self._fmt(ratio)}%',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('National Debt')), 'value': f'{self._fmt(debt)} {ul(unit)}', 'color': 'red'},
                {'label': 'GDP', 'value': f'{self._fmt(gdp)} {ul(unit)}', 'color': 'green'},
                {'label': str(_('Ratio')), 'value': f'{self._fmt(ratio)}%', 'color': 'yellow'},
            ],
        })

    # ── 10) OUTPUT GAP ───────────────────────────────────────────────
    def _calc_output_gap(self, data):
        """Output Gap = ((Actual GDP − Potential GDP) / Potential GDP) × 100"""
        for field in ('actual_gdp', 'potential_gdp'):
            if field not in data or data[field] is None or data[field] == '':
                return self._err(_('{field} is required.').format(field=field.replace('_', ' ').title()))

        actual = float(data['actual_gdp'])
        potential = float(data['potential_gdp'])
        unit = data.get('unit', 'billions')

        if unit not in self.UNIT_FACTORS:
            return self._err(_('Invalid unit.'))
        if actual < 0 or potential < 0:
            return self._err(_('GDP values must be non-negative.'))
        if potential == 0:
            return self._err(_('Potential GDP cannot be zero.'))

        act_b = self._to_base(actual, unit)
        pot_b = self._to_base(potential, unit)
        gap = ((act_b - pot_b) / pot_b) * 100
        gap_abs = act_b - pot_b

        if math.isinf(gap) or math.isnan(gap):
            return self._err(_('Invalid calculation result.'))

        # Interpretation
        if gap > 2:
            interp = str(_('Inflationary Gap — economy overheating, demand exceeds capacity'))
        elif gap > 0:
            interp = str(_('Slight Positive Gap — economy near or slightly above potential'))
        elif gap > -2:
            interp = str(_('Slight Negative Gap — economy near or slightly below potential'))
        else:
            interp = str(_('Recessionary Gap — significant slack, unemployment likely high'))

        ul = self._ul
        steps = [
            str(_('Step 1: Identify given values')),
            f'  • {_("Actual GDP")} = {self._fmt(actual)} {ul(unit)}',
            f'  • {_("Potential GDP")} = {self._fmt(potential)} {ul(unit)}',
            '',
            str(_('Step 2: Calculate the gap')),
            f'  {_("Gap")} = {_("Actual")} − {_("Potential")}',
            f'  = {self._fmt(act_b)} − {self._fmt(pot_b)} = {self._fmt(gap_abs)} {_("Billion")}',
            '',
            str(_('Step 3: Calculate output gap percentage')),
            f'  {_("Output Gap")} = ({_("Gap")} / {_("Potential")}) × 100',
            f'  = ({self._fmt(gap_abs)} / {self._fmt(pot_b)}) × 100',
            f'  = {self._fmt(gap)}%',
            '',
            str(_('Step 4: Interpret result')),
            f'  • {_("Positive gap")}: {_("economy above potential (inflationary pressure)")}',
            f'  • {_("Negative gap")}: {_("economy below potential (recessionary, unemployment)")}',
            f'  • {_("Your result")}: {interp}',
            '',
            str(_('Result: Output Gap = {v}%').format(v=self._fmt(gap))),
        ]

        chart = {
            'main_chart': {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Actual GDP')), str(_('Potential GDP'))],
                    'datasets': [{
                        'label': f'GDP ({ul(unit)})',
                        'data': [round(act_b, 2), round(pot_b, 2)],
                        'backgroundColor': [
                            'rgba(59,130,246,0.7)' if gap >= 0 else 'rgba(239,68,68,0.7)',
                            'rgba(16,185,129,0.7)'],
                        'borderColor': [
                            '#3b82f6' if gap >= 0 else '#ef4444',
                            '#10b981'],
                        'borderWidth': 2, 'borderRadius': 6,
                    }],
                },
                'options': {
                    'responsive': True, 'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False},
                                'title': {'display': True,
                                          'text': str(_('Output Gap: {r}%').format(r=self._fmt(gap)))}},
                    'scales': {'y': {'beginAtZero': True,
                                     'title': {'display': True, 'text': str(_('Billion'))}}},
                },
            }
        }

        return JsonResponse({
            'success': True, 'calc_type': 'output_gap',
            'result': round(gap, 4), 'result_label': str(_('Output Gap')),
            'output_gap': round(gap, 4), 'gap_absolute': round(gap_abs, 4),
            'actual_gdp': actual, 'potential_gdp': potential, 'unit': unit,
            'interpretation': interp,
            'formula': f'(({self._fmt(act_b)} − {self._fmt(pot_b)}) / {self._fmt(pot_b)}) × 100 = {self._fmt(gap)}%',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Actual GDP')), 'value': f'{self._fmt(actual)} {ul(unit)}', 'color': 'blue'},
                {'label': str(_('Potential GDP')), 'value': f'{self._fmt(potential)} {ul(unit)}', 'color': 'green'},
                {'label': str(_('Gap')), 'value': f'{self._fmt(gap_abs)} {ul(unit)}', 'color': 'yellow'},
                {'label': str(_('Output Gap')), 'value': f'{self._fmt(gap)}%', 'color': 'purple'},
            ],
        })
