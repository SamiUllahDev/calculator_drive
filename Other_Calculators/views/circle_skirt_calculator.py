from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CircleSkirtCalculator(View):
    """
    Circle Skirt Calculator — Sewing pattern measurements.

    Calculates waist radius, outer radius, fabric dimensions,
    and yardage for full, 3/4, half, and quarter circle skirts.

    Math:
        waist_radius = waist_circumference / (2 × π × fraction)
        outer_radius = waist_radius + skirt_length
        fabric dimensions depend on skirt type and fold strategy

    Uses NumPy for all circular geometry calculations.
    """
    template_name = 'other_calculators/circle_skirt_calculator.html'

    SKIRT_TYPES = [
        {
            'value': 'full',
            'label': 'Full Circle',
            'fraction': 1.0,
            'description': 'Maximum flare — uses the most fabric but creates the most dramatic look.',
            'folds': 'Fold fabric in quarters; cut quarter-circle arc.',
        },
        {
            'value': 'three_quarter',
            'label': '¾ Circle',
            'fraction': 0.75,
            'description': 'Nice flare with less fabric than a full circle.',
            'folds': 'Fold fabric; requires a single seam.',
        },
        {
            'value': 'half',
            'label': 'Half Circle',
            'fraction': 0.5,
            'description': 'Moderate flare — a great balance of movement and fabric economy.',
            'folds': 'Fold fabric in half; cut half-circle arc.',
        },
        {
            'value': 'quarter',
            'label': '¼ Circle (A-line)',
            'fraction': 0.25,
            'description': 'Minimal flare, A-line shape. Uses the least fabric.',
            'folds': 'Cut on single layer; two panels needed.',
        },
    ]

    # Standard fabric widths (inches)
    FABRIC_WIDTHS = [36, 44, 45, 54, 58, 60]

    def get(self, request):
        context = {
            'calculator_name': _('Circle Skirt Calculator'),
            'page_title': _('Circle Skirt Calculator - Sewing Pattern'),
            'skirt_types': self.SKIRT_TYPES,
            'fabric_widths': self.FABRIC_WIDTHS,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)

            waist = float(data.get('waist', 28))
            skirt_length = float(data.get('skirt_length', 22))
            skirt_type = data.get('skirt_type', 'full')
            seam_allowance = float(data.get('seam_allowance', 0.625))
            hem_allowance = float(data.get('hem_allowance', 0.5))
            unit = data.get('unit', 'inches')
            fabric_width = float(data.get('fabric_width', 45))

            # Validate
            if unit == 'cm':
                # Convert to inches for calculation, convert back for display
                waist_in = waist / 2.54
                length_in = skirt_length / 2.54
                seam_in = seam_allowance / 2.54
                hem_in = hem_allowance / 2.54
                fw_in = fabric_width / 2.54
            else:
                waist_in = waist
                length_in = skirt_length
                seam_in = seam_allowance
                hem_in = hem_allowance
                fw_in = fabric_width

            waist_in = max(10, min(60, waist_in))
            length_in = max(5, min(50, length_in))

            # ── Get skirt type data ──────────────────────────────
            type_data = next((t for t in self.SKIRT_TYPES if t['value'] == skirt_type), self.SKIRT_TYPES[0])
            fraction = type_data['fraction']

            # ── Core geometry (NumPy) ────────────────────────────
            # Waist radius: R_waist = waist_circumference / (2π × fraction)
            waist_circ = waist_in + (2 * seam_in)  # add seam allowance to waist
            r_waist = float(waist_circ / (2 * np.pi * fraction))
            r_outer = r_waist + length_in + hem_in

            # ── Fabric requirements ──────────────────────────────
            fabric_calcs = self._calc_fabric(r_waist, r_outer, fraction, fw_in, seam_in)

            # ── Arc lengths ──────────────────────────────────────
            waist_arc = float(2 * np.pi * r_waist * fraction)
            hem_arc = float(2 * np.pi * r_outer * fraction)

            # ── Convert results to display units ─────────────────
            if unit == 'cm':
                conv = 2.54
                unit_label = 'cm'
                yard_label = str(_('meters'))
            else:
                conv = 1.0
                unit_label = 'in'
                yard_label = str(_('yards'))

            results = {
                'waist_radius': round(r_waist * conv, 2),
                'outer_radius': round(r_outer * conv, 2),
                'waist_arc': round(waist_arc * conv, 2),
                'hem_arc': round(hem_arc * conv, 2),
                'fabric_width_needed': round(fabric_calcs['width_needed'] * conv, 1),
                'fabric_length_needed': round(fabric_calcs['length_needed'] * conv, 1),
                'fabric_area_sq': round(fabric_calcs['area_sq_in'] * (conv ** 2), 1),
                'yardage': round(fabric_calcs['yardage'] if unit != 'cm' else fabric_calcs['meters'], 2),
                'panels': fabric_calcs['panels'],
                'fold_method': fabric_calcs['fold_method'],
            }

            # ── Chart data ───────────────────────────────────────
            chart_data = self._prepare_chart_data(
                r_waist * conv, r_outer * conv, fraction,
                results, unit_label, type_data
            )

            return JsonResponse({
                'success': True,
                'skirt_type': type_data['label'],
                'skirt_description': type_data['description'],
                'fold_instruction': type_data['folds'],
                'unit': unit_label,
                'yard_label': yard_label,
                'results': results,
                'chart_data': chart_data,
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    def _calc_fabric(self, r_waist, r_outer, fraction, fabric_w, seam):
        """Calculate fabric dimensions and yardage."""
        diameter = 2 * r_outer

        if fraction == 1.0:
            # Full circle: fold in quarters → need square of r_outer + seam
            width_needed = r_outer + seam
            length_needed = r_outer + seam
            # But if fabric is wide enough, fold in half
            if fabric_w >= diameter + seam:
                panels = 1
                fold_method = str(_('Fold fabric in quarters. Cut a quarter-circle arc from the folded corner.'))
                length_needed = diameter + seam * 2
                width_needed = r_outer + seam
            else:
                panels = 2
                fold_method = str(_('Cut two half-circles. Fold fabric in half, cut a half-circle. Repeat. Join with side seams.'))
                width_needed = r_outer + seam
                length_needed = (diameter + seam * 2) * 2

        elif fraction == 0.75:
            width_needed = diameter + seam
            length_needed = diameter + seam
            panels = 1
            fold_method = str(_('Lay fabric flat. Mark the waist arc at 270°. One seam needed at the opening.'))

        elif fraction == 0.5:
            # Half circle: fold once
            width_needed = diameter + seam * 2
            length_needed = r_outer + seam
            panels = 1
            fold_method = str(_('Fold fabric in half. Cut a half-circle arc from the fold. Open for the full half-circle.'))
            if fabric_w < diameter + seam:
                panels = 2
                fold_method = str(_('Fabric too narrow for one piece. Cut two quarter-circle panels and join with side seams.'))
                width_needed = r_outer + seam
                length_needed = (r_outer + seam) * 2

        else:  # quarter
            width_needed = r_outer + seam
            length_needed = r_outer + seam
            panels = 2
            fold_method = str(_('Cut two quarter-circle panels from single-layer fabric. Join with side seams.'))

        area_sq_in = width_needed * length_needed * panels
        yardage = length_needed / 36.0  # inches to yards
        meters = length_needed / 39.37  # inches to meters

        return {
            'width_needed': width_needed,
            'length_needed': length_needed,
            'area_sq_in': area_sq_in,
            'yardage': round(yardage, 2),
            'meters': round(meters, 2),
            'panels': panels,
            'fold_method': fold_method,
        }

    # ─────────────────────────────────────────────────────────────
    def _prepare_chart_data(self, r_waist, r_outer, fraction, results, unit, type_data):
        # 1. Dimensions comparison bar
        dims_chart = {
            'type': 'bar',
            'data': {
                'labels': [
                    str(_('Waist Radius')),
                    str(_('Outer Radius')),
                    str(_('Fabric Width')),
                    str(_('Fabric Length')),
                ],
                'datasets': [{
                    'label': unit,
                    'data': [
                        results['waist_radius'],
                        results['outer_radius'],
                        results['fabric_width_needed'],
                        results['fabric_length_needed'],
                    ],
                    'backgroundColor': ['#ec4899', '#8b5cf6', '#3b82f6', '#10b981'],
                    'borderRadius': 6,
                }]
            }
        }

        # 2. Skirt proportion doughnut (waist vs length)
        proportion_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [str(_('Waist Radius')), str(_('Skirt Length'))],
                'datasets': [{
                    'data': [results['waist_radius'], round(r_outer - r_waist, 2)],
                    'backgroundColor': ['#ec4899', '#8b5cf6'],
                    'borderWidth': 2,
                    'borderColor': '#fff',
                }]
            },
            'center_text': {
                'value': type_data['label'],
                'label': f'{results["outer_radius"]} {unit}',
                'color': '#8b5cf6',
            }
        }

        # 3. Arc lengths comparison
        arcs_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Waist Edge')), str(_('Hem Edge'))],
                'datasets': [{
                    'label': unit,
                    'data': [results['waist_arc'], results['hem_arc']],
                    'backgroundColor': ['#f472b6', '#c084fc'],
                    'borderRadius': 8,
                }]
            }
        }

        return {
            'dims_chart': dims_chart,
            'proportion_chart': proportion_chart,
            'arcs_chart': arcs_chart,
        }
