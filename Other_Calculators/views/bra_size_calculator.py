from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import re


@method_decorator(ensure_csrf_cookie, name='dispatch')
class BraSizeCalculator(View):
    template_name = 'other_calculators/bra_size_calculator.html'

    CUP_SIZES = {
        'US': ['AA', 'A', 'B', 'C', 'D', 'DD', 'DDD', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'UK': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'EU': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'FR': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'AU': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'PK': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'CA': ['AA', 'A', 'B', 'C', 'D', 'DD', 'DDD', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'IN': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'NZ': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
        'IT': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'ES': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'DE': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'JP': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'CN': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'BR': ['AA', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'MX': ['AA', 'A', 'B', 'C', 'D', 'DD', 'DDD', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'],
        'ZA': ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'FF', 'G', 'GG', 'H', 'HH', 'J', 'JJ'],
    }

    def get(self, request):
        return render(request, self.template_name, {'calculator_name': _('Bra Size Calculator')})

    def post(self, request):
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'bra_size')
            handlers = {
                'bra_size': self._calculate_bra_size,
                'size_conversion': self._convert_size,
                'sister_sizes': self._get_sister_sizes,
            }
            handler = handlers.get(calc_type)
            if not handler:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)
            return handler(data)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid JSON data.'))}, status=400)
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': str(_('Invalid input')) + ': ' + str(e)}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _calculate_bra_size(self, data):
        try:
            underbust = float(data.get('underbust', 0))
            bust = float(data.get('bust', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Please enter valid numeric measurements.'))}, status=400)

        unit = data.get('unit', 'inches')
        sizing_system = data.get('sizing_system', 'US')

        if underbust <= 0 or bust <= 0:
            return JsonResponse({'success': False, 'error': str(_('Measurements must be greater than zero.'))}, status=400)
        if bust <= underbust:
            return JsonResponse({'success': False, 'error': str(_('Bust measurement must be greater than underbust measurement.'))}, status=400)

        if unit == 'cm':
            underbust_in = underbust / 2.54
            bust_in = bust / 2.54
        else:
            underbust_in = underbust
            bust_in = bust

        if underbust_in < 20 or underbust_in > 60:
            return JsonResponse({'success': False, 'error': str(_('Underbust measurement must be between 20 and 60 inches (51-152 cm).'))}, status=400)
        if bust_in < 25 or bust_in > 70:
            return JsonResponse({'success': False, 'error': str(_('Bust measurement must be between 25 and 70 inches (64-178 cm).'))}, status=400)

        band_size = self._calc_band(underbust_in)
        if band_size < 28 or band_size > 50:
            return JsonResponse({'success': False, 'error': str(_('Calculated band size is outside valid range (28-50). Please check your measurements.'))}, status=400)

        cup_diff = bust_in - band_size
        cup_idx = self._cup_index(cup_diff)
        cups = self.CUP_SIZES.get(sizing_system, self.CUP_SIZES['US'])
        cup_letter = cups[cup_idx] if cup_idx < len(cups) else 'N'

        all_sizes = self._all_system_sizes(band_size, cup_idx)
        sister_sizes = self._calc_sister_sizes(band_size, cup_idx, sizing_system)

        steps = [
            str(_('Step 1: Take measurements')),
            str(_('Underbust')) + f': {underbust} {unit}',
            str(_('Bust (fullest point)')) + f': {bust} {unit}',
            '',
        ]
        if unit == 'cm':
            steps.extend([
                str(_('Step 2: Convert to inches')),
                str(_('Underbust')) + f' = {underbust} cm ÷ 2.54 = {round(underbust_in, 2)} ' + str(_('inches')),
                str(_('Bust')) + f' = {bust} cm ÷ 2.54 = {round(bust_in, 2)} ' + str(_('inches')),
                '',
            ])
        steps.extend([
            str(_('Step 3: Calculate band size')),
            str(_('Round underbust to nearest even number')) + f': {round(underbust_in, 2)} → {int(band_size)}',
            str(_('Band Size')) + f' = {int(band_size)}',
            '',
            str(_('Step 4: Calculate cup size')),
            str(_('Cup Difference')) + f' = {str(_("Bust"))} - {str(_("Band"))} = {round(bust_in, 2)} - {int(band_size)} = {round(cup_diff, 2)} ' + str(_('inches')),
            str(_('Cup Size')) + f' = {cup_letter} (' + str(_('based on')) + f' {round(cup_diff, 2)} ' + str(_('inch difference')) + ')',
            '',
            str(_('Final Answer')) + f': {int(band_size)}{cup_letter} ({sizing_system})',
        ])

        chart_data = self._prepare_chart(all_sizes)

        return JsonResponse({
            'success': True, 'calc_type': 'bra_size',
            'measurements': {'underbust': underbust, 'bust': bust, 'unit': unit,
                             'underbust_inches': round(underbust_in, 2), 'bust_inches': round(bust_in, 2)},
            'bra_size': {'band': int(band_size), 'cup': cup_letter,
                         'full_size': f'{int(band_size)}{cup_letter}', 'sizing_system': sizing_system},
            'all_sizes': all_sizes, 'sister_sizes': sister_sizes,
            'cup_difference': round(cup_diff, 2),
            'step_by_step': steps, 'chart_data': chart_data,
        })

    def _convert_size(self, data):
        size = data.get('size', '').strip()
        from_sys = data.get('from_system', 'US')
        to_sys = data.get('to_system', 'UK')

        if not size:
            return JsonResponse({'success': False, 'error': str(_('Please enter a bra size.'))}, status=400)

        match = re.match(r'(\d+)\s*([A-Z]+)', size.upper())
        if not match:
            return JsonResponse({'success': False, 'error': str(_('Invalid size format. Use format like "34C".'))}, status=400)

        band = int(match.group(1))
        cup_letter = match.group(2)

        if from_sys == 'FR':
            if band < 75 or band > 115:
                return JsonResponse({'success': False, 'error': str(_('FR band size must be between 75 and 115.'))}, status=400)
        else:
            if band < 28 or band > 50:
                return JsonResponse({'success': False, 'error': str(_('Band size must be between 28 and 50.'))}, status=400)

        source_cups = self.CUP_SIZES.get(from_sys, self.CUP_SIZES['US'])
        if cup_letter not in source_cups:
            return JsonResponse({'success': False, 'error': str(_('Invalid cup size for the selected system.'))}, status=400)
        cup_idx = source_cups.index(cup_letter)

        target_cups = self.CUP_SIZES.get(to_sys, self.CUP_SIZES['US'])
        if cup_idx >= len(target_cups):
            return JsonResponse({'success': False, 'error': str(_('Cup size not available in target system.'))}, status=400)
        target_cup = target_cups[cup_idx]

        if from_sys == 'FR' and to_sys != 'FR':
            converted_band = band - 15
        elif to_sys == 'FR' and from_sys != 'FR':
            converted_band = band + 15
        else:
            converted_band = band

        steps = [
            str(_('Step 1: Parse original size')),
            str(_('Original Size')) + f': {band}{cup_letter} ({from_sys})',
            '',
            str(_('Step 2: Find cup index')),
            f'{cup_letter} → ' + str(_('index')) + f' {cup_idx} ' + str(_('in')) + f' {from_sys}',
            '',
            str(_('Step 3: Convert band size')),
        ]
        if from_sys == 'FR' and to_sys != 'FR':
            steps.append(str(_('FR to')) + f' {to_sys}: {band} - 15 = {converted_band}')
        elif to_sys == 'FR' and from_sys != 'FR':
            steps.append(f'{from_sys} ' + str(_('to FR')) + f': {band} + 15 = {converted_band}')
        else:
            steps.append(str(_('Band size stays the same')) + f': {band}')
        steps.extend([
            '',
            str(_('Step 4: Convert cup size')),
            str(_('Index')) + f' {cup_idx} ' + str(_('in')) + f' {to_sys} → {target_cup}',
            '',
            str(_('Final Answer')) + f': {int(converted_band)}{target_cup} ({to_sys})',
        ])

        return JsonResponse({
            'success': True, 'calc_type': 'size_conversion',
            'original_size': f'{band}{cup_letter}', 'from_system': from_sys,
            'converted_size': f'{int(converted_band)}{target_cup}', 'to_system': to_sys,
            'step_by_step': steps,
        })

    def _get_sister_sizes(self, data):
        size = data.get('size', '').strip()
        system = data.get('sizing_system', 'US')

        if not size:
            return JsonResponse({'success': False, 'error': str(_('Please enter a bra size.'))}, status=400)
        match = re.match(r'(\d+)\s*([A-Z]+)', size.upper())
        if not match:
            return JsonResponse({'success': False, 'error': str(_('Invalid size format.'))}, status=400)

        band = int(match.group(1))
        cup_letter = match.group(2)
        cups = self.CUP_SIZES.get(system, self.CUP_SIZES['US'])
        if cup_letter not in cups:
            return JsonResponse({'success': False, 'error': str(_('Invalid cup size.'))}, status=400)
        cup_idx = cups.index(cup_letter)

        sister_sizes = self._calc_sister_sizes(band, cup_idx, system)

        steps = [
            str(_('Step 1: Original size')),
            f'{band}{cup_letter} ({system})',
            '',
            str(_('Step 2: Understanding sister sizes')),
            str(_('Sister sizes have the same cup volume but different band/cup combinations.')),
            str(_('When band increases by 1, cup decreases by 1 (and vice versa).')),
            '',
            str(_('Step 3: Calculate sister sizes')),
        ]
        for s in sister_sizes:
            steps.append(f"  {s['size']}")
        steps.extend(['', str(_('Final Answer')) + f': {len(sister_sizes)} ' + str(_('sister sizes found'))])

        return JsonResponse({
            'success': True, 'calc_type': 'sister_sizes',
            'original_size': f'{band}{cup_letter}', 'sizing_system': system,
            'sister_sizes': sister_sizes, 'step_by_step': steps,
        })

    def _calc_band(self, underbust_inches):
        rounded = round(underbust_inches)
        return rounded if rounded % 2 == 0 else rounded + 1

    def _cup_index(self, diff):
        if diff < 0.5: return 0
        idx = int(round(diff))
        return min(max(idx, 0), 14)

    def _all_system_sizes(self, band, cup_idx):
        sizes = {}
        for sys, cups in self.CUP_SIZES.items():
            if cup_idx < len(cups):
                b = int(band + 15) if sys == 'FR' else int(band)
                sizes[sys] = f'{b}{cups[cup_idx]}'
        return sizes

    def _calc_sister_sizes(self, band, cup_idx, system):
        cups = self.CUP_SIZES.get(system, self.CUP_SIZES['US'])
        sisters = []
        for offset in [-2, -1, 1, 2]:
            nb = band + offset
            nc = cup_idx - offset
            if 28 <= nb <= 50 and 0 <= nc < len(cups):
                sisters.append({'band': int(nb), 'cup': cups[nc], 'size': f'{int(nb)}{cups[nc]}'})
        return sisters

    def _prepare_chart(self, all_sizes):
        try:
            systems = list(all_sizes.keys())
            bands = []
            for sys in systems:
                m = re.match(r'(\d+)([A-Z]+)', all_sizes[sys])
                bands.append(int(m.group(1)) if m else 0)
            pink = ['rgba(236,72,153,0.7)', 'rgba(244,63,94,0.7)', 'rgba(251,113,133,0.7)',
                    'rgba(252,165,165,0.7)', 'rgba(253,164,175,0.7)', 'rgba(254,205,211,0.7)',
                    'rgba(255,228,230,0.7)', 'rgba(255,192,203,0.7)', 'rgba(255,182,193,0.7)',
                    'rgba(255,160,122,0.7)', 'rgba(255,105,180,0.7)', 'rgba(255,20,147,0.7)',
                    'rgba(219,112,147,0.7)', 'rgba(199,21,133,0.7)', 'rgba(236,72,153,0.7)',
                    'rgba(244,63,94,0.7)', 'rgba(251,113,133,0.7)']
            borders = ['#ec4899', '#f43f5e', '#fb7185', '#fca5a5', '#fda4af', '#fecdd3',
                       '#ffe4e6', '#ffc0cb', '#ffb6c1', '#ffa07a', '#ff69b4', '#ff1493',
                       '#db7093', '#c71585', '#ec4899', '#f43f5e', '#fb7185']
            return {'band_chart': {'type': 'bar', 'data': {
                'labels': systems,
                'datasets': [{'label': str(_('Band Size')), 'data': bands,
                              'backgroundColor': pink[:len(systems)],
                              'borderColor': borders[:len(systems)],
                              'borderWidth': 2, 'borderRadius': 8}]}}}
        except Exception:
            return None
