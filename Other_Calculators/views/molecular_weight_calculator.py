from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import re
import numpy as np
from collections import defaultdict


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MolecularWeightCalculator(View):
    """
    Molecular Weight Calculator — Molar Mass from Chemical Formula.

    Calc types:
        • calculate_mw  → parse formula, sum atomic weights, show breakdown

    Supports:
        - Simple formulas: H2O, CO2, NaCl
        - Parentheses: Ca(OH)2, Al2(SO4)3
        - Hydrates: CuSO4·5H2O (use · or *)
        - Complex: C6H12O6, C8H10N4O2

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/molecular_weight_calculator.html'

    # ── periodic table — atomic weights (g/mol) ──────────────────────
    AW = {
        'H': 1.008, 'He': 4.003, 'Li': 6.941, 'Be': 9.012, 'B': 10.81,
        'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.180,
        'Na': 22.990, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.086, 'P': 30.974,
        'S': 32.066, 'Cl': 35.453, 'Ar': 39.948, 'K': 39.098, 'Ca': 40.078,
        'Sc': 44.956, 'Ti': 47.867, 'V': 50.942, 'Cr': 52.000, 'Mn': 54.938,
        'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.380,
        'Ga': 69.723, 'Ge': 72.631, 'As': 74.922, 'Se': 78.971, 'Br': 79.904,
        'Kr': 83.798, 'Rb': 85.468, 'Sr': 87.62, 'Y': 88.906, 'Zr': 91.224,
        'Nb': 92.906, 'Mo': 95.950, 'Tc': 98.000, 'Ru': 101.07, 'Rh': 102.906,
        'Pd': 106.42, 'Ag': 107.868, 'Cd': 112.411, 'In': 114.818, 'Sn': 118.710,
        'Sb': 121.760, 'Te': 127.600, 'I': 126.904, 'Xe': 131.293, 'Cs': 132.905,
        'Ba': 137.327, 'La': 138.905, 'Ce': 140.116, 'Pr': 140.908, 'Nd': 144.242,
        'Pm': 145.000, 'Sm': 150.360, 'Eu': 151.964, 'Gd': 157.250, 'Tb': 158.925,
        'Dy': 162.500, 'Ho': 164.930, 'Er': 167.259, 'Tm': 168.934, 'Yb': 173.045,
        'Lu': 174.967, 'Hf': 178.490, 'Ta': 180.948, 'W': 183.840, 'Re': 186.207,
        'Os': 190.230, 'Ir': 192.217, 'Pt': 195.085, 'Au': 196.967, 'Hg': 200.592,
        'Tl': 204.383, 'Pb': 207.200, 'Bi': 208.980, 'Po': 209.000, 'At': 210.000,
        'Rn': 222.000, 'Fr': 223.000, 'Ra': 226.000, 'Ac': 227.000, 'Th': 232.038,
        'Pa': 231.036, 'U': 238.029, 'Np': 237.000, 'Pu': 244.000,
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Molecular Weight Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'calculate_mw')
            if calc == 'calculate_mw':
                return self._calc_mw(data)
            return self._err(_('Invalid calculation type.'))
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(_('Invalid input:')) + ' ' + str(e))
        except Exception:
            return self._err(_('An error occurred during calculation.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    def _fnum(self, v, dp=4):
        if v is None:
            return '0'
        return f'{v:,.{dp}f}'

    # ── formula parser ───────────────────────────────────────────────
    def _parse_formula(self, formula):
        """Parse a chemical formula string into {element: count} dict."""
        formula = formula.strip().replace('·', '*').replace('•', '*')
        parts = formula.split('*')
        counts = defaultdict(float)
        for part in parts:
            part = part.strip()
            if not part:
                continue
            # handle leading coefficient like "5H2O"
            m = re.match(r'^(\d+)([A-Z].*)$', part)
            if m:
                coeff = float(m.group(1))
                sub = m.group(2)
            else:
                coeff = 1.0
                sub = part
            sub_counts = self._parse_part(sub)
            if sub_counts is None:
                return None
            for el, cnt in sub_counts.items():
                counts[el] += cnt * coeff
        return dict(counts) if counts else None

    def _parse_part(self, formula):
        counts = defaultdict(float)
        i = 0
        while i < len(formula):
            m = re.match(r'([A-Z][a-z]?)(\d*\.?\d*)', formula[i:])
            mp = re.match(r'\(([^)]+)\)(\d*\.?\d*)', formula[i:])
            if mp and (not m or mp.start() == 0):
                group_counts = self._parse_part(mp.group(1))
                if group_counts is None:
                    return None
                mult = float(mp.group(2)) if mp.group(2) else 1.0
                for el, cnt in group_counts.items():
                    counts[el] += cnt * mult
                i += len(mp.group(0))
            elif m and m.group(1):
                el = m.group(1)
                if el not in self.AW:
                    return None
                cnt = float(m.group(2)) if m.group(2) else 1.0
                counts[el] += cnt
                i += len(m.group(0))
            else:
                return None
        return dict(counts) if counts else None

    # ── CALCULATE MOLECULAR WEIGHT ───────────────────────────────────
    def _calc_mw(self, d):
        formula = (d.get('formula') or '').strip()
        if not formula:
            return self._err(_('Chemical formula is required.'))

        counts = self._parse_formula(formula)
        if counts is None:
            return self._err(_('Invalid chemical formula. Please check the format and element symbols.'))

        # compute breakdown
        details = []
        total_mw = 0.0
        for el in sorted(counts.keys()):
            cnt = counts[el]
            aw = self.AW[el]
            mass = float(np.multiply(aw, cnt))
            total_mw += mass
            details.append({
                'element': el,
                'count': cnt,
                'atomic_weight': aw,
                'mass': round(mass, 4),
                'percentage': 0.0,
            })

        if total_mw <= 0:
            return self._err(_('Molecular weight must be greater than zero.'))

        for det in details:
            det['percentage'] = round(float(np.multiply(np.divide(det['mass'], total_mw), 100)), 2)

        # steps
        steps = [
            str(_('Step 1: Identify the chemical formula')),
            f'  • {formula}',
            '', str(_('Step 2: Identify elements and their counts')),
        ]
        for det in details:
            c = int(det['count']) if det['count'] == int(det['count']) else det['count']
            steps.append(f'  • {det["element"]}: {c} atom(s)')

        steps += ['', str(_('Step 3: Calculate mass contribution of each element'))]
        for det in details:
            c = int(det['count']) if det['count'] == int(det['count']) else det['count']
            steps.append(f'  {det["element"]}: {c} × {det["atomic_weight"]} = {det["mass"]} g/mol')

        mass_sum = ' + '.join([str(det['mass']) for det in details])
        steps += [
            '', str(_('Step 4: Sum all contributions')),
            f'  MW = {mass_sum}',
            f'  MW = {self._fnum(total_mw)} g/mol',
            '', str(_('Step 5: Mass percentage of each element')),
        ]
        for det in details:
            steps.append(f'  {det["element"]}: ({det["mass"]} / {self._fnum(total_mw)}) × 100 = {det["percentage"]}%')

        # charts — pie for percentages, bar for mass contributions
        pie_colors = [
            'rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)',
            'rgba(239,68,68,0.8)', 'rgba(139,92,246,0.8)', 'rgba(236,72,153,0.8)',
            'rgba(20,184,166,0.8)', 'rgba(245,158,11,0.8)', 'rgba(99,102,241,0.8)',
            'rgba(244,63,94,0.8)',
        ]
        pie_chart = {
            'type': 'pie',
            'data': {
                'labels': [d['element'] for d in details],
                'datasets': [{
                    'data': [d['percentage'] for d in details],
                    'backgroundColor': pie_colors[:len(details)],
                    'borderWidth': 2,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True, 'position': 'right'},
                    'title': {'display': True, 'text': str(_('Element Mass Percentage'))},
                },
            },
        }

        bar_chart = self._bar_chart(
            [d['element'] for d in details],
            [d['mass'] for d in details],
            pie_colors[:len(details)],
            str(_('Element Mass Contributions (g/mol)'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'calculate_mw',
            'result': round(total_mw, 4),
            'result_label': str(_('Molecular Weight')),
            'result_unit_symbol': 'g/mol',
            'formula': formula,
            'molecular_weight': round(total_mw, 4),
            'element_details': details,
            'step_by_step': steps,
            'chart_data': {
                'pie_chart': pie_chart,
                'bar_chart': bar_chart,
            },
        })

    # ── chart helper ─────────────────────────────────────────────────
    def _bar_chart(self, labels, data, colors, title):
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Mass (g/mol)')),
                    'data': data,
                    'backgroundColor': colors,
                    'borderColor': [c.replace('0.8', '1') for c in colors],
                    'borderWidth': 2,
                    'borderRadius': 8,
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': False},
                    'title': {'display': True, 'text': title},
                },
                'scales': {
                    'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Mass (g/mol)'))}},
                },
            },
        }
