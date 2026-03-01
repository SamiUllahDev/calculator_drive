from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CircleSkirtCalculator(View):
    """
    Circle Skirt Calculator — 4 skirt types.

    Skirt types
        • full           → 360° — maximum flare
        • three_quarter  → 270° — nice drape, less bulk
        • half           → 180° — moderate, everyday
        • quarter        → 90°  — A-line, least fabric

    Math
        waist_radius = waist_circumference / (2 × π × fraction)
        outer_radius = waist_radius + skirt_length + hem_allowance
        fabric needs depend on type and fabric width
    """
    template_name = 'other_calculators/circle_skirt_calculator.html'

    TYPES = {
        'full':          (1.0,  'Full Circle (360°)'),
        'three_quarter': (0.75, '¾ Circle (270°)'),
        'half':          (0.5,  'Half Circle (180°)'),
        'quarter':       (0.25, '¼ Circle / A-Line (90°)'),
    }
    FABRIC_WIDTHS = [36, 44, 45, 54, 58, 60]

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Circle Skirt Calculator'),
        })

    # ── POST ──────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            ct = data.get('calc_type', 'pattern')
            dispatch = {
                'pattern':    self._calc_pattern,
                'compare':    self._calc_compare,
                'yardage':    self._calc_yardage,
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

    def _parse_inputs(self, data, skip_length_check=False):
        """Parse and validate common measurement inputs."""
        unit = data.get('unit', 'inches')
        conv_in = 2.54 if unit == 'cm' else 1.0  # cm→in factor

        waist = float(data.get('waist', 0))
        default_len = 56 if unit == 'cm' else 22
        length = float(data.get('skirt_length', default_len) or default_len)
        seam = float(data.get('seam_allowance', 0.625 if unit == 'inches' else 1.5))
        hem = float(data.get('hem_allowance', 0.5 if unit == 'inches' else 1.3))
        fw = float(data.get('fabric_width', 45 if unit == 'inches' else 114))
        skirt_type = data.get('skirt_type', 'full')

        # Convert to inches for internal math
        w_in = waist / conv_in
        l_in = length / conv_in
        s_in = seam / conv_in
        h_in = hem / conv_in
        fw_in = fw / conv_in

        if w_in < 10 or w_in > 80:
            raise ValueError(str(_('Waist must be between 10" and 80" (25–200 cm).')))
        if not skip_length_check and (l_in < 5 or l_in > 60):
            raise ValueError(str(_('Length must be between 5" and 60" (13–150 cm).')))

        frac, label = self.TYPES.get(skirt_type, self.TYPES['full'])

        return {
            'waist': waist, 'length': length, 'seam': seam, 'hem': hem,
            'fw': fw, 'unit': unit, 'skirt_type': skirt_type,
            'w_in': w_in, 'l_in': l_in, 's_in': s_in, 'h_in': h_in,
            'fw_in': fw_in, 'frac': frac, 'label': label,
            'conv': conv_in,
        }

    def _core_geometry(self, w_in, l_in, s_in, h_in, frac):
        """Core circle-skirt math — all in inches."""
        waist_circ_adj = w_in + 2 * s_in
        r_waist = waist_circ_adj / (2 * math.pi * frac)
        r_outer = r_waist + l_in + h_in
        waist_arc = 2 * math.pi * r_waist * frac
        hem_arc = 2 * math.pi * r_outer * frac
        return r_waist, r_outer, waist_arc, hem_arc

    def _fabric_needs(self, r_waist, r_outer, frac, fw_in, s_in):
        """Compute fabric width/length/panels/yardage."""
        diameter = 2 * r_outer

        if frac == 1.0:
            if fw_in >= diameter + 2 * s_in:
                panels = 1
                fold = str(_('Fold fabric in quarters. Cut a quarter-circle arc from the folded corner.'))
                w = r_outer + s_in
                l = diameter + 2 * s_in
            else:
                panels = 2
                fold = str(_('Cut two half-circles. Fold fabric in half, cut half-circle. Repeat. Join with side seams.'))
                w = r_outer + s_in
                l = (diameter + 2 * s_in) * 2
        elif frac == 0.75:
            panels = 1
            fold = str(_('Lay fabric flat. Mark the waist arc at 270°. One seam needed at the opening.'))
            w = diameter + s_in
            l = diameter + s_in
        elif frac == 0.5:
            if fw_in >= diameter + 2 * s_in:
                panels = 1
                fold = str(_('Fold fabric in half. Cut a half-circle arc from the fold.'))
                w = diameter + 2 * s_in
                l = r_outer + s_in
            else:
                panels = 2
                fold = str(_('Fabric too narrow for one piece. Cut two quarter-circle panels and join with side seams.'))
                w = r_outer + s_in
                l = (r_outer + s_in) * 2
        else:  # quarter
            panels = 2
            fold = str(_('Cut two quarter-circle panels from single-layer fabric. Join with side seams.'))
            w = r_outer + s_in
            l = r_outer + s_in

        yardage = round(l / 36, 2)
        meters = round(l / 39.37, 2)
        return {
            'width': w, 'length': l, 'panels': panels,
            'fold': fold, 'yardage': yardage, 'meters': meters,
        }

    def _to_display(self, val_in, conv):
        """Convert inches → display unit, rounded."""
        return round(val_in * conv, 2)

    # ── 1) PATTERN ───────────────────────────────────────────────────
    def _calc_pattern(self, data):
        p = self._parse_inputs(data)
        r_w, r_o, warc, harc = self._core_geometry(
            p['w_in'], p['l_in'], p['s_in'], p['h_in'], p['frac'])
        fab = self._fabric_needs(r_w, r_o, p['frac'], p['fw_in'], p['s_in'])

        c = p['conv']
        u = 'cm' if p['unit'] == 'cm' else 'in'
        yl = str(_('meters')) if p['unit'] == 'cm' else str(_('yards'))

        rw_d = self._to_display(r_w, c)
        ro_d = self._to_display(r_o, c)
        wa_d = self._to_display(warc, c)
        ha_d = self._to_display(harc, c)
        fw_d = self._to_display(fab['width'], c)
        fl_d = self._to_display(fab['length'], c)
        yard = fab['meters'] if p['unit'] == 'cm' else fab['yardage']

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Waist")} = {p["waist"]} {u}',
            f'  • {_("Length")} = {p["length"]} {u}',
            f'  • {_("Type")} = {p["label"]}  (fraction = {p["frac"]})',
            f'  • {_("Seam")} = {p["seam"]} {u},  {_("Hem")} = {p["hem"]} {u}',
            '',
            str(_('Step 2: Adjusted waist circumference')),
            f'  {p["waist"]} + 2 × {p["seam"]} = {round(p["waist"] + 2*p["seam"], 2)} {u}',
            '',
            str(_('Step 3: Waist radius')),
            f'  R = {round(p["waist"] + 2*p["seam"], 2)} ÷ (2 × π × {p["frac"]})',
            f'  R = {rw_d} {u}',
            '',
            str(_('Step 4: Outer radius')),
            f'  R_outer = {rw_d} + {p["length"]} + {p["hem"]}',
            f'  R_outer = {ro_d} {u}',
            '',
            str(_('Step 5: Arc lengths')),
            f'  {_("Waist arc")} = 2π × {rw_d} × {p["frac"]} = {wa_d} {u}',
            f'  {_("Hem arc")} = 2π × {ro_d} × {p["frac"]} = {ha_d} {u}',
            '',
            str(_('Step 6: Fabric requirements')),
            f'  {_("Width")} = {fw_d} {u}',
            f'  {_("Length")} = {fl_d} {u}',
            f'  {_("Panels")} = {fab["panels"]}',
            f'  {_("Yardage")} = {yard} {yl}',
            '',
            str(_('Step 7: Cutting instructions')),
            f'  {fab["fold"]}',
            '',
            str(_('Result: {label} — R_waist = {r} {u}, Fabric = {y} {yl}').format(
                label=p['label'], r=rw_d, u=u, y=yard, yl=yl)),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': [str(_('Waist Radius')), str(_('Outer Radius')),
                           str(_('Fabric Width')), str(_('Fabric Length'))],
                'datasets': [{
                    'label': u,
                    'data': [rw_d, ro_d, fw_d, fl_d],
                    'backgroundColor': ['#ec4899', '#8b5cf6', '#3b82f6', '#10b981'],
                    'borderRadius': 6,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'indexAxis': 'y',
                'plugins': {'legend': {'display': False},
                            'title': {'display': True, 'text': str(_('Dimensions'))}},
                'scales': {'x': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'pattern',
            'result': f'{rw_d} {u}',
            'result_label': str(_('Waist Radius')),
            'skirt_type': p['label'],
            'unit': u, 'yard_label': yl,
            'waist_radius': rw_d, 'outer_radius': ro_d,
            'waist_arc': wa_d, 'hem_arc': ha_d,
            'fabric_width': fw_d, 'fabric_length': fl_d,
            'yardage': yard, 'panels': fab['panels'],
            'fold_instruction': fab['fold'],
            'formula': f'R = Waist / (2π × {p["frac"]}) = {rw_d} {u}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': str(_('Waist R')), 'value': f'{rw_d} {u}', 'color': 'pink'},
                {'label': str(_('Outer R')), 'value': f'{ro_d} {u}', 'color': 'purple'},
                {'label': str(_('Fabric')), 'value': f'{yard} {yl}', 'color': 'blue'},
                {'label': str(_('Panels')), 'value': str(fab['panels']), 'color': 'green'},
                {'label': str(_('Waist Arc')), 'value': f'{wa_d} {u}', 'color': 'yellow'},
                {'label': str(_('Hem Arc')), 'value': f'{ha_d} {u}', 'color': 'indigo'},
            ],
        })

    # ── 2) COMPARE (all 4 types) ─────────────────────────────────────
    def _calc_compare(self, data):
        p = self._parse_inputs(data)
        c = p['conv']
        u = 'cm' if p['unit'] == 'cm' else 'in'
        yl = str(_('meters')) if p['unit'] == 'cm' else str(_('yards'))

        rows = []
        labels, radii, yards = [], [], []
        for key, (frac, label) in self.TYPES.items():
            r_w, r_o, warc, harc = self._core_geometry(
                p['w_in'], p['l_in'], p['s_in'], p['h_in'], frac)
            fab = self._fabric_needs(r_w, r_o, frac, p['fw_in'], p['s_in'])
            rw_d = self._to_display(r_w, c)
            ro_d = self._to_display(r_o, c)
            yard = fab['meters'] if p['unit'] == 'cm' else fab['yardage']
            rows.append({
                'type': label, 'waist_r': rw_d, 'outer_r': ro_d,
                'yardage': yard, 'panels': fab['panels'],
            })
            labels.append(label)
            radii.append(rw_d)
            yards.append(yard)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Waist")} = {p["waist"]} {u},  {_("Length")} = {p["length"]} {u}',
            '',
            str(_('Step 2: Compare all 4 skirt types')),
        ]
        for r in rows:
            steps.append(f'  • {r["type"]}: R={r["waist_r"]} {u}, Fabric={r["yardage"]} {yl}, Panels={r["panels"]}')
        steps += [
            '',
            str(_('Result: Full circle uses the most fabric, quarter/A-line uses the least.')),
        ]

        chart = {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [
                    {'label': str(_('Waist Radius')) + f' ({u})', 'data': radii,
                     'backgroundColor': 'rgba(236,72,153,0.7)', 'borderColor': '#ec4899',
                     'borderWidth': 2, 'borderRadius': 6},
                    {'label': str(_('Yardage')) + f' ({yl})', 'data': yards,
                     'backgroundColor': 'rgba(139,92,246,0.7)', 'borderColor': '#8b5cf6',
                     'borderWidth': 2, 'borderRadius': 6},
                ],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': True, 'position': 'bottom'},
                            'title': {'display': True, 'text': str(_('Skirt Type Comparison'))}},
                'scales': {'y': {'beginAtZero': True}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'compare',
            'result': f'{len(rows)} types compared',
            'result_label': str(_('Skirt Type Comparison')),
            'rows': rows,
            'formula': f'Waist {p["waist"]} {u}, Length {p["length"]} {u}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': rows[0]['type'], 'value': f'{rows[0]["yardage"]} {yl}', 'color': 'pink'},
                {'label': rows[1]['type'], 'value': f'{rows[1]["yardage"]} {yl}', 'color': 'purple'},
                {'label': rows[2]['type'], 'value': f'{rows[2]["yardage"]} {yl}', 'color': 'blue'},
                {'label': rows[3]['type'], 'value': f'{rows[3]["yardage"]} {yl}', 'color': 'green'},
            ],
        })

    # ── 3) YARDAGE for multiple lengths ──────────────────────────────
    def _calc_yardage(self, data):
        p = self._parse_inputs(data, skip_length_check=True)
        c = p['conv']
        u = 'cm' if p['unit'] == 'cm' else 'in'
        yl = str(_('meters')) if p['unit'] == 'cm' else str(_('yards'))

        # Calculate for several common lengths
        if p['unit'] == 'cm':
            lengths = [40, 50, 60, 70, 80, 100]
        else:
            lengths = [16, 18, 20, 22, 25, 30]

        rows = []
        labels, yds = [], []
        for ln in lengths:
            l_in = ln / c
            r_w, r_o, _wa, _ha = self._core_geometry(
                p['w_in'], l_in, p['s_in'], p['h_in'], p['frac'])
            fab = self._fabric_needs(r_w, r_o, p['frac'], p['fw_in'], p['s_in'])
            yard = fab['meters'] if p['unit'] == 'cm' else fab['yardage']
            rows.append({'length': f'{ln} {u}', 'yardage': yard})
            labels.append(f'{ln} {u}')
            yds.append(yard)

        steps = [
            str(_('Step 1: Given values')),
            f'  • {_("Waist")} = {p["waist"]} {u}',
            f'  • {_("Type")} = {p["label"]}',
            '',
            str(_('Step 2: Yardage for various lengths')),
        ]
        for r in rows:
            steps.append(f'  • {_("Length")} {r["length"]}: {r["yardage"]} {yl}')
        steps += ['', str(_('Result: Longer skirts need more fabric.'))]

        chart = {'main_chart': {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Fabric')) + f' ({yl})',
                    'data': yds,
                    'borderColor': '#ec4899',
                    'backgroundColor': 'rgba(236,72,153,0.15)',
                    'fill': True, 'tension': 0.3,
                    'pointBackgroundColor': '#ec4899',
                    'pointBorderWidth': 2, 'pointRadius': 5,
                }],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False},
                            'title': {'display': True,
                                      'text': str(_('Yardage by Skirt Length'))}},
                'scales': {'y': {'beginAtZero': True,
                                 'title': {'display': True, 'text': yl}}},
            },
        }}

        return JsonResponse({
            'success': True, 'calc_type': 'yardage',
            'result': f'{len(rows)} lengths',
            'result_label': str(_('Yardage Chart')),
            'rows': rows, 'skirt_type': p['label'],
            'formula': f'{p["label"]} — Waist {p["waist"]} {u}',
            'step_by_step': steps, 'chart_data': chart,
            'detail_cards': [
                {'label': rows[0]['length'], 'value': f'{rows[0]["yardage"]} {yl}', 'color': 'pink'},
                {'label': rows[2]['length'], 'value': f'{rows[2]["yardage"]} {yl}', 'color': 'purple'},
                {'label': rows[4]['length'], 'value': f'{rows[4]["yardage"]} {yl}', 'color': 'blue'},
                {'label': rows[5]['length'], 'value': f'{rows[5]["yardage"]} {yl}', 'color': 'green'},
            ],
        })
