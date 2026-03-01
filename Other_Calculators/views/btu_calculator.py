from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BtuCalculator(View):
    """
    BTU Calculator — Room Size, Area, Cooling Load & Unit Conversion.

    Features:
        • Room-size BTU (length × width × height)
        • Area-based BTU
        • Cooling-load BTU (windows, occupants, appliances)
        • Energy-unit conversion (BTU ↔ kWh, Joules, Calories, ft·lb)

    Uses NumPy for arithmetic.
    All user-facing strings wrapped with gettext_lazy for i18n.
    """
    template_name = 'other_calculators/btu_calculator.html'

    # ── conversion factors ───────────────────────────────────────────
    BTU_TO_KWH = 0.000293071
    BTU_TO_JOULES = 1055.06
    BTU_TO_CALORIES = 252.164
    BTU_TO_FOOT_POUNDS = 778.169

    # ── room-type BTU per sq ft ──────────────────────────────────────
    ROOM_TYPES = {
        'general':     {'btu': 20, 'label': _('General')},
        'bedroom':     {'btu': 20, 'label': _('Bedroom')},
        'living_room': {'btu': 25, 'label': _('Living Room')},
        'kitchen':     {'btu': 30, 'label': _('Kitchen')},
        'bathroom':    {'btu': 15, 'label': _('Bathroom')},
        'office':      {'btu': 20, 'label': _('Office')},
        'dining_room': {'btu': 25, 'label': _('Dining Room')},
        'basement':    {'btu': 20, 'label': _('Basement')},
        'attic':       {'btu': 30, 'label': _('Attic')},
        'garage':      {'btu': 15, 'label': _('Garage')},
    }

    INSULATION = {
        'excellent': {'mult': 0.8, 'label': _('Excellent')},
        'good':      {'mult': 1.0, 'label': _('Good')},
        'average':   {'mult': 1.2, 'label': _('Average')},
        'poor':      {'mult': 1.5, 'label': _('Poor')},
        'none':      {'mult': 2.0, 'label': _('None')},
    }

    CLIMATE = {
        'very_cold': {'mult': 1.3, 'label': _('Very Cold (< 0 °F)')},
        'cold':      {'mult': 1.2, 'label': _('Cold (0–20 °F)')},
        'moderate':  {'mult': 1.0, 'label': _('Moderate (20–50 °F)')},
        'warm':      {'mult': 0.9, 'label': _('Warm (50–80 °F)')},
        'hot':       {'mult': 0.8, 'label': _('Hot (> 80 °F)')},
        'tropical':  {'mult': 0.7, 'label': _('Tropical')},
    }

    ENERGY_UNITS = {
        'BTU':         {'to_btu': 1.0,                      'sym': 'BTU'},
        'kWh':         {'to_btu': 1.0 / 0.000293071,        'sym': 'kWh'},
        'Joules':      {'to_btu': 1.0 / 1055.06,            'sym': 'J'},
        'Calories':    {'to_btu': 1.0 / 252.164,            'sym': 'cal'},
        'Foot-Pounds': {'to_btu': 1.0 / 778.169,            'sym': 'ft·lb'},
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('BTU Calculator'),
        })

    # ── POST router ──────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            calc = data.get('calc_type', 'room_size')
            dispatch = {
                'room_size':       self._calc_room_size,
                'area_btu':        self._calc_area_btu,
                'cooling_load':    self._calc_cooling_load,
                'unit_conversion': self._calc_unit_conversion,
            }
            handler = dispatch.get(calc)
            if not handler:
                return self._err(_('Invalid calculation type.'))
            return handler(data)
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

    def _fnum(self, v, dp=6):
        if v is None:
            return '0'
        if abs(v) < 1e-6 or abs(v) >= 1e9:
            return f'{v:.6g}'
        return f'{v:,.{dp}g}'

    def _safe_pos(self, v, name):
        if v is None or v == '':
            raise ValueError(str(_('{name} is required.').format(name=name)))
        v = float(v)
        if v <= 0:
            raise ValueError(str(_('{name} must be greater than zero.').format(name=name)))
        if v > 1e12:
            raise ValueError(str(_('{name} is too large.').format(name=name)))
        return v

    def _safe_nn(self, v, name, default=0):
        """Non-negative float."""
        if v is None or v == '':
            return default
        v = float(v)
        if v < 0:
            raise ValueError(str(_('{name} must be non-negative.').format(name=name)))
        return v

    def _safe_int(self, v, name, min_val=0, default=0):
        if v is None or v == '':
            return default
        v = int(float(v))
        if v < min_val:
            raise ValueError(str(_('{name} must be at least {min}.').format(name=name, min=min_val)))
        return v

    def _room_btu(self, key):
        return self.ROOM_TYPES.get(key, self.ROOM_TYPES['general'])['btu']

    def _room_label(self, key):
        return str(self.ROOM_TYPES.get(key, self.ROOM_TYPES['general'])['label'])

    def _ins_mult(self, key):
        return self.INSULATION.get(key, self.INSULATION['average'])['mult']

    def _ins_label(self, key):
        return str(self.INSULATION.get(key, self.INSULATION['average'])['label'])

    def _clim_mult(self, key):
        return self.CLIMATE.get(key, self.CLIMATE['moderate'])['mult']

    def _clim_label(self, key):
        return str(self.CLIMATE.get(key, self.CLIMATE['moderate'])['label'])

    def _conversions(self, btu):
        return {
            'btu': round(btu, 2),
            'kwh': round(btu * self.BTU_TO_KWH, 6),
            'joules': round(btu * self.BTU_TO_JOULES, 2),
            'calories': round(btu * self.BTU_TO_CALORIES, 2),
            'foot_pounds': round(btu * self.BTU_TO_FOOT_POUNDS, 2),
        }

    def _verify(self, val):
        if not np.isfinite(val):
            raise ValueError(str(_('Calculation produced an invalid result.')))
        return val

    # ── ROOM SIZE: BTU from L × W × H ───────────────────────────────
    def _calc_room_size(self, d):
        length = self._safe_pos(d.get('length'), str(_('Length')))
        width = self._safe_pos(d.get('width'), str(_('Width')))
        height = self._safe_pos(d.get('height'), str(_('Height')))
        unit = d.get('unit', 'feet')
        room_type = d.get('room_type', 'general')
        insulation = d.get('insulation', 'average')
        climate = d.get('climate_zone', 'moderate')

        # convert to feet
        if unit == 'meters':
            lf = float(np.multiply(length, 3.28084))
            wf = float(np.multiply(width, 3.28084))
            hf = float(np.multiply(height, 3.28084))
        else:
            lf, wf, hf = length, width, height

        area = self._verify(float(np.multiply(lf, wf)))
        volume = self._verify(float(np.multiply(area, hf)))
        btu_sqft = self._room_btu(room_type)
        base = self._verify(float(np.multiply(area, btu_sqft)))
        ins_m = self._ins_mult(insulation)
        clim_m = self._clim_mult(climate)
        total = self._verify(float(np.multiply(np.multiply(base, ins_m), clim_m)))

        conv = self._conversions(total)

        steps = [
            str(_('Step 1: Identify the room dimensions')),
            f'  • {_("Length")} = {length} {unit}',
            f'  • {_("Width")} = {width} {unit}',
            f'  • {_("Height")} = {height} {unit}',
        ]
        if unit == 'meters':
            steps += [
                '', str(_('Step 2: Convert to feet')),
                f'  {_("Length")} = {length} × 3.28084 = {self._fnum(lf)} ft',
                f'  {_("Width")} = {width} × 3.28084 = {self._fnum(wf)} ft',
                f'  {_("Height")} = {height} × 3.28084 = {self._fnum(hf)} ft',
            ]
        steps += [
            '', str(_('Step 3: Calculate area and volume')),
            f'  {_("Area")} = {self._fnum(lf)} × {self._fnum(wf)} = {self._fnum(area)} sq ft',
            f'  {_("Volume")} = {self._fnum(area)} × {self._fnum(hf)} = {self._fnum(volume)} cu ft',
            '', str(_('Step 4: Determine base BTU')),
            f'  • {_("Room Type")}: {self._room_label(room_type)} ({btu_sqft} BTU/sq ft)',
            f'  {_("Base BTU")} = {self._fnum(area)} × {btu_sqft} = {self._fnum(base)} BTU',
            '', str(_('Step 5: Apply multipliers')),
            f'  • {_("Insulation")}: {self._ins_label(insulation)} (×{ins_m})',
            f'  • {_("Climate Zone")}: {self._clim_label(climate)} (×{clim_m})',
            '', str(_('Step 6: Calculate total BTU')),
            f'  {_("Formula")}: Total = Base × Insulation × Climate',
            f'  Total = {self._fnum(base)} × {ins_m} × {clim_m}',
            f'  Total = {self._fnum(total)} BTU',
            '', str(_('Step 7: Energy conversions')),
            f'  • {self._fnum(conv["kwh"])} kWh',
            f'  • {self._fnum(conv["joules"])} Joules',
            f'  • {self._fnum(conv["calories"])} Calories',
        ]

        chart = self._bar_chart(
            [str(_('Base')), str(_('Insulation ×')), str(_('Climate ×')), str(_('Total BTU'))],
            [base, base * ins_m, base * ins_m * clim_m, total],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)', 'rgba(239,68,68,0.8)'],
            str(_('BTU Calculation Breakdown'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'room_size',
            'result': round(total, 2),
            'result_label': str(_('Total BTU Required')),
            'result_unit_symbol': 'BTU',
            'formula': f'BTU = Area × {btu_sqft} × {ins_m} × {clim_m}',
            'area_sqft': round(area, 2),
            'volume_cuft': round(volume, 2),
            'conversions': conv,
            'step_by_step': steps,
            'chart_data': {'btu_chart': chart},
        })

    # ── AREA BTU ─────────────────────────────────────────────────────
    def _calc_area_btu(self, d):
        area = self._safe_pos(d.get('area'), str(_('Area')))
        unit = d.get('unit', 'sqft')
        room_type = d.get('room_type', 'general')
        insulation = d.get('insulation', 'average')
        climate = d.get('climate_zone', 'moderate')

        area_sqft = float(np.multiply(area, 10.764)) if unit == 'sqm' else area

        btu_sqft = self._room_btu(room_type)
        base = self._verify(float(np.multiply(area_sqft, btu_sqft)))
        ins_m = self._ins_mult(insulation)
        clim_m = self._clim_mult(climate)
        total = self._verify(float(np.multiply(np.multiply(base, ins_m), clim_m)))

        conv = self._conversions(total)

        steps = [
            str(_('Step 1: Identify the area')),
            f'  • {_("Area")} = {area} {"m²" if unit == "sqm" else "sq ft"}',
        ]
        if unit == 'sqm':
            steps += [
                '', str(_('Step 2: Convert to square feet')),
                f'  {_("Area")} = {area} × 10.764 = {self._fnum(area_sqft)} sq ft',
            ]
        steps += [
            '', str(_('Step 3: Determine base BTU')),
            f'  • {_("Room Type")}: {self._room_label(room_type)} ({btu_sqft} BTU/sq ft)',
            f'  {_("Base BTU")} = {self._fnum(area_sqft)} × {btu_sqft} = {self._fnum(base)} BTU',
            '', str(_('Step 4: Apply multipliers')),
            f'  • {_("Insulation")}: {self._ins_label(insulation)} (×{ins_m})',
            f'  • {_("Climate Zone")}: {self._clim_label(climate)} (×{clim_m})',
            '', str(_('Step 5: Calculate total BTU')),
            f'  {_("Formula")}: Total = Base × Insulation × Climate',
            f'  Total = {self._fnum(base)} × {ins_m} × {clim_m}',
            f'  Total = {self._fnum(total)} BTU',
            '', str(_('Step 6: Energy conversions')),
            f'  • {self._fnum(conv["kwh"])} kWh',
            f'  • {self._fnum(conv["joules"])} Joules',
            f'  • {self._fnum(conv["calories"])} Calories',
        ]

        chart = self._bar_chart(
            [str(_('Base')), str(_('After Insulation')), str(_('Total BTU'))],
            [base, base * ins_m, total],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(239,68,68,0.8)'],
            str(_('Area BTU Breakdown'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'area_btu',
            'result': round(total, 2),
            'result_label': str(_('Total BTU Required')),
            'result_unit_symbol': 'BTU',
            'formula': f'BTU = {self._fnum(area_sqft)} × {btu_sqft} × {ins_m} × {clim_m}',
            'area_sqft': round(area_sqft, 2),
            'conversions': conv,
            'step_by_step': steps,
            'chart_data': {'btu_chart': chart},
        })

    # ── COOLING LOAD ─────────────────────────────────────────────────
    def _calc_cooling_load(self, d):
        area = self._safe_pos(d.get('area'), str(_('Area')))
        unit = d.get('unit', 'sqft')
        room_type = d.get('room_type', 'general')
        insulation = d.get('insulation', 'average')
        climate = d.get('climate_zone', 'moderate')
        windows = self._safe_int(d.get('windows'), str(_('Windows')), 0, 0)
        occupants = self._safe_int(d.get('occupants'), str(_('Occupants')), 1, 1)
        appliances = self._safe_nn(d.get('appliances'), str(_('Appliances')), 0)

        area_sqft = float(np.multiply(area, 10.764)) if unit == 'sqm' else area

        # Cooling uses 20 % more than heating base
        btu_sqft = self._room_btu(room_type) * 1.2
        base = self._verify(float(np.multiply(area_sqft, btu_sqft)))
        ins_m = self._ins_mult(insulation)
        clim_m = self._clim_mult(climate)
        adjusted_base = self._verify(float(np.multiply(np.multiply(base, ins_m), clim_m)))

        window_btu = float(np.multiply(windows, 1000))
        occupant_btu = float(np.multiply(occupants, 400))
        appliance_btu = float(np.multiply(appliances, 3.412))

        total = self._verify(adjusted_base + window_btu + occupant_btu + appliance_btu)
        conv = self._conversions(total)

        steps = [
            str(_('Step 1: Identify the inputs')),
            f'  • {_("Area")} = {area} {"m²" if unit == "sqm" else "sq ft"}',
            f'  • {_("Windows")} = {windows}',
            f'  • {_("Occupants")} = {occupants}',
            f'  • {_("Appliances")} = {appliances} W',
        ]
        if unit == 'sqm':
            steps += [
                '', str(_('Step 2: Convert area to square feet')),
                f'  {_("Area")} = {area} × 10.764 = {self._fnum(area_sqft)} sq ft',
            ]
        steps += [
            '', str(_('Step 3: Calculate base cooling BTU')),
            f'  • {_("Room Type")}: {self._room_label(room_type)} ({btu_sqft:.0f} BTU/sq ft for cooling)',
            f'  {_("Base BTU")} = {self._fnum(area_sqft)} × {btu_sqft:.0f} = {self._fnum(base)} BTU',
            '', str(_('Step 4: Apply multipliers')),
            f'  • {_("Insulation")}: {self._ins_label(insulation)} (×{ins_m})',
            f'  • {_("Climate Zone")}: {self._clim_label(climate)} (×{clim_m})',
            f'  {_("Adjusted Base")} = {self._fnum(base)} × {ins_m} × {clim_m} = {self._fnum(adjusted_base)} BTU',
            '', str(_('Step 5: Add additional loads')),
            f'  • {_("Windows")}: {windows} × 1,000 = {self._fnum(window_btu)} BTU',
            f'  • {_("Occupants")}: {occupants} × 400 = {self._fnum(occupant_btu)} BTU',
            f'  • {_("Appliances")}: {appliances} W × 3.412 = {self._fnum(appliance_btu)} BTU',
            '', str(_('Step 6: Calculate total cooling BTU')),
            f'  {_("Formula")}: Total = Adjusted Base + Windows + Occupants + Appliances',
            f'  Total = {self._fnum(adjusted_base)} + {self._fnum(window_btu)} + {self._fnum(occupant_btu)} + {self._fnum(appliance_btu)}',
            f'  Total = {self._fnum(total)} BTU',
            '', str(_('Step 7: Tons of cooling')),
            f'  {_("Tons")} = {self._fnum(total)} / 12,000 = {self._fnum(total / 12000)} tons',
        ]

        chart = self._bar_chart(
            [str(_('Base Load')), str(_('Windows')), str(_('Occupants')), str(_('Appliances')), str(_('Total'))],
            [adjusted_base, window_btu, occupant_btu, appliance_btu, total],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)',
             'rgba(239,68,68,0.8)', 'rgba(139,92,246,0.8)'],
            str(_('Cooling Load Breakdown'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'cooling_load',
            'result': round(total, 2),
            'result_label': str(_('Cooling BTU Required')),
            'result_unit_symbol': 'BTU',
            'formula': 'Total = Base + Windows + Occupants + Appliances',
            'tons': round(total / 12000, 2),
            'conversions': conv,
            'step_by_step': steps,
            'chart_data': {'btu_chart': chart},
        })

    # ── UNIT CONVERSION ──────────────────────────────────────────────
    def _calc_unit_conversion(self, d):
        value = self._safe_pos(d.get('btu_value'), str(_('Value')))
        from_u = d.get('from_unit', 'BTU')
        to_u = d.get('to_unit', 'kWh')

        if from_u not in self.ENERGY_UNITS:
            return self._err(_('Invalid source unit.'))
        if to_u not in self.ENERGY_UNITS:
            return self._err(_('Invalid target unit.'))

        # convert to BTU first
        btu = float(np.multiply(value, self.ENERGY_UNITS[from_u]['to_btu']))
        # convert from BTU to target
        from_sym = self.ENERGY_UNITS[from_u]['sym']
        to_sym = self.ENERGY_UNITS[to_u]['sym']

        if to_u == 'BTU':
            converted = btu
        elif to_u == 'kWh':
            converted = float(np.multiply(btu, self.BTU_TO_KWH))
        elif to_u == 'Joules':
            converted = float(np.multiply(btu, self.BTU_TO_JOULES))
        elif to_u == 'Calories':
            converted = float(np.multiply(btu, self.BTU_TO_CALORIES))
        elif to_u == 'Foot-Pounds':
            converted = float(np.multiply(btu, self.BTU_TO_FOOT_POUNDS))
        else:
            converted = btu

        converted = self._verify(converted)

        steps = [
            str(_('Step 1: Identify the original value')),
            f'  • {_("Value")} = {value} {from_sym}',
        ]
        if from_u != 'BTU':
            steps += [
                '', str(_('Step 2: Convert to BTU')),
                f'  {_("Formula")}: BTU = {value} {from_sym} × {self.ENERGY_UNITS[from_u]["to_btu"]:.6g}',
                f'  BTU = {self._fnum(btu)}',
            ]
        steps += [
            '', str(_('Step 3: Convert to {unit}').format(unit=to_u)),
            f'  {_("Result")} = {self._fnum(converted)} {to_sym}',
        ]

        chart = self._bar_chart(
            [from_sym, 'BTU', to_sym],
            [value, btu, converted],
            ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
            str(_('Energy Unit Conversion'))
        )

        return JsonResponse({
            'success': True, 'calc_type': 'unit_conversion',
            'result': round(converted, 6),
            'result_label': str(_('{from_u} to {to_u}').format(from_u=from_u, to_u=to_u)),
            'result_unit_symbol': to_sym,
            'formula': f'{value} {from_sym} → {self._fnum(converted)} {to_sym}',
            'btu_equivalent': round(btu, 2),
            'step_by_step': steps,
            'chart_data': {'btu_chart': chart},
        })

    # ── chart helper ─────────────────────────────────────────────────
    def _bar_chart(self, labels, data, colors, title):
        return {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': str(_('Value')),
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
                    'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Value'))}},
                },
            },
        }
