from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TipCalculator(View):
    """
    Tip Calculator — standard tip, split bill, reverse tip.

    Calc types
        • standard  → bill + tip% → tip amount, total
        • split     → bill + tip% + people → per-person
        • reverse   → total (incl tip) → back-calculate bill, tip%, tip amount
    """
    template_name = 'other_calculators/tip_calculator.html'

    # Common tip percentages for quick reference
    TIP_PRESETS = [10, 15, 18, 20, 25]

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Tip Calculator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'standard')
            dispatch = {
                'standard': self._calc_standard,
                'split':    self._calc_split,
                'reverse':  self._calc_reverse,
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

    def _nonneg(self, data, key, label):
        v = data.get(key)
        if v is None or v == '':
            return 0.0
        f = float(v)
        if f < 0:
            raise ValueError(str(_('{label} must be non-negative.').format(label=label)))
        return f

    def _chart(self, labels, values, title, chart_type='pie'):
        colors = ['rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(59,130,246,0.8)', 'rgba(139,92,246,0.8)']
        borders = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6']
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

    def _tip_comparison(self, bill):
        """Generate tip amounts for common percentages."""
        return {str(p): {'tip': round(bill * p / 100, 2), 'total': round(bill * (1 + p / 100), 2)} for p in self.TIP_PRESETS}

    # ── 1) STANDARD TIP ──────────────────────────────────────────────
    def _calc_standard(self, data):
        bill = self._pos(data, 'bill_amount', str(_('Bill Amount')))
        tip_pct = self._nonneg(data, 'tip_percent', str(_('Tip Percentage')))

        tip_amount = bill * tip_pct / 100
        total = bill + tip_amount
        comparison = self._tip_comparison(bill)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Bill")} = ${self._f(bill)}',
            f'  • {_("Tip")} = {self._f(tip_pct, 1)}%',
            '', str(_('Step 2: Calculate tip amount')),
            f'  ${self._f(bill)} × {self._f(tip_pct, 1)}% = ${self._f(tip_amount)}',
            '', str(_('Step 3: Calculate total')),
            f'  ${self._f(bill)} + ${self._f(tip_amount)} = ${self._f(total)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'standard',
            'result': round(total, 2),
            'result_label': str(_('Total with Tip')),
            'result_unit_symbol': '$',
            'bill_amount': round(bill, 2),
            'tip_percent': round(tip_pct, 1),
            'tip_amount': round(tip_amount, 2),
            'total': round(total, 2),
            'comparison': comparison,
            'formula': f'${self._f(bill)} + {self._f(tip_pct, 1)}% = ${self._f(total)}',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Bill')), str(_('Tip'))],
                [round(bill, 2), round(tip_amount, 2)],
                str(_('Bill vs Tip'))
            )},
        })

    # ── 2) SPLIT BILL ────────────────────────────────────────────────
    def _calc_split(self, data):
        bill = self._pos(data, 'bill_amount', str(_('Bill Amount')))
        tip_pct = self._nonneg(data, 'tip_percent', str(_('Tip Percentage')))
        people = int(self._pos(data, 'num_people', str(_('Number of People'))))

        tip_amount = bill * tip_pct / 100
        total = bill + tip_amount
        per_person_total = total / people
        per_person_tip = tip_amount / people
        per_person_bill = bill / people

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Bill")} = ${self._f(bill)}',
            f'  • {_("Tip")} = {self._f(tip_pct, 1)}%',
            f'  • {_("People")} = {people}',
            '', str(_('Step 2: Calculate tip amount')),
            f'  ${self._f(bill)} × {self._f(tip_pct, 1)}% = ${self._f(tip_amount)}',
            '', str(_('Step 3: Calculate total')),
            f'  ${self._f(bill)} + ${self._f(tip_amount)} = ${self._f(total)}',
            '', str(_('Step 4: Split per person')),
            f'  {_("Bill per person")}: ${self._f(bill)} / {people} = ${self._f(per_person_bill)}',
            f'  {_("Tip per person")}: ${self._f(tip_amount)} / {people} = ${self._f(per_person_tip)}',
            f'  {_("Total per person")}: ${self._f(total)} / {people} = ${self._f(per_person_total)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'split',
            'result': round(per_person_total, 2),
            'result_label': str(_('Per Person')),
            'result_unit_symbol': '$',
            'bill_amount': round(bill, 2),
            'tip_percent': round(tip_pct, 1),
            'tip_amount': round(tip_amount, 2),
            'total': round(total, 2),
            'num_people': people,
            'per_person_total': round(per_person_total, 2),
            'per_person_tip': round(per_person_tip, 2),
            'per_person_bill': round(per_person_bill, 2),
            'formula': f'${self._f(total)} / {people} = ${self._f(per_person_total)} per person',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Bill/person')), str(_('Tip/person'))],
                [round(per_person_bill, 2), round(per_person_tip, 2)],
                str(_('Per Person Breakdown'))
            )},
        })

    # ── 3) REVERSE TIP ──────────────────────────────────────────────
    def _calc_reverse(self, data):
        total = self._pos(data, 'total_amount', str(_('Total Amount')))
        tip_pct = self._nonneg(data, 'tip_percent', str(_('Tip Percentage')))

        # total = bill × (1 + tip_pct/100)  →  bill = total / (1 + tip_pct/100)
        multiplier = 1 + tip_pct / 100
        bill = total / multiplier
        tip_amount = total - bill

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Total (incl. tip)")} = ${self._f(total)}',
            f'  • {_("Tip")} = {self._f(tip_pct, 1)}%',
            '', str(_('Step 2: Calculate original bill')),
            f'  {_("Bill")} = ${self._f(total)} / (1 + {self._f(tip_pct, 1)}%)',
            f'  {_("Bill")} = ${self._f(total)} / {self._f(multiplier, 4)} = ${self._f(bill)}',
            '', str(_('Step 3: Calculate tip amount')),
            f'  ${self._f(total)} − ${self._f(bill)} = ${self._f(tip_amount)}',
        ]

        return JsonResponse({
            'success': True, 'calc_type': 'reverse',
            'result': round(bill, 2),
            'result_label': str(_('Original Bill')),
            'result_unit_symbol': '$',
            'bill_amount': round(bill, 2),
            'tip_percent': round(tip_pct, 1),
            'tip_amount': round(tip_amount, 2),
            'total': round(total, 2),
            'formula': f'${self._f(total)} / {self._f(multiplier, 4)} = ${self._f(bill)} bill + ${self._f(tip_amount)} tip',
            'step_by_step': steps,
            'chart_data': {'main_chart': self._chart(
                [str(_('Original Bill')), str(_('Tip'))],
                [round(bill, 2), round(tip_amount, 2)],
                str(_('Reverse Tip Breakdown'))
            )},
        })
