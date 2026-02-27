from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class ShoeSizeConversion(View):
    template_name = 'other_calculators/shoe_size_conversion.html'

    MEN_US_RANGE = (4, 16)
    WOMEN_US_RANGE = (4, 14)

    def get(self, request):
        return render(request, self.template_name, {'calculator_name': _('Shoe Size Conversion')})

    def post(self, request):
        try:
            data = json.loads(request.body)

            if 'from_size' not in data or data.get('from_size') is None:
                return JsonResponse({'success': False, 'error': str(_('Shoe size is required.'))}, status=400)
            if 'from_system' not in data:
                return JsonResponse({'success': False, 'error': str(_('Source size system is required.'))}, status=400)
            if 'to_system' not in data:
                return JsonResponse({'success': False, 'error': str(_('Target size system is required.'))}, status=400)

            try:
                from_size = float(data['from_size'])
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': str(_('Invalid input. Please enter a valid number.'))}, status=400)

            from_system = data.get('from_system', 'us')
            to_system = data.get('to_system', 'uk')
            gender = data.get('gender', 'men')

            if not self._is_valid_size(from_size, from_system, gender):
                return JsonResponse({'success': False, 'error': str(_('Size is out of valid range for the selected system and gender.'))}, status=400)

            cm_size = self._to_cm(from_size, from_system, gender)
            if cm_size is None:
                return JsonResponse({'success': False, 'error': str(_('Invalid conversion. Please check your input.'))}, status=400)

            to_size = self._from_cm(cm_size, to_system, gender)
            if to_size is None:
                return JsonResponse({'success': False, 'error': str(_('Invalid conversion. Please check your input.'))}, status=400)

            # Round appropriately
            if to_system in ['us', 'uk']:
                to_size = round(to_size * 2) / 2
            elif to_system == 'eu':
                to_size = round(to_size)
            else:
                to_size = round(to_size, 1)

            steps = self._build_steps(from_size, from_system, cm_size, to_size, to_system, gender)
            chart_data = self._build_chart(from_size, from_system, to_system, gender, cm_size)

            return JsonResponse({
                'success': True,
                'from_size': from_size, 'from_system': from_system,
                'to_size': to_size, 'to_system': to_system,
                'gender': gender, 'cm_size': round(cm_size, 1),
                'step_by_step': steps, 'chart_data': chart_data,
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid JSON data.'))}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(_('An error occurred: {error}').format(error=str(e)))}, status=500)

    # ── Conversion helpers using NumPy ────────────────────────────

    def _to_cm(self, size, system, gender):
        try:
            s = np.float64(size)
            if system == 'cm' or system == 'jp':
                return float(s)
            elif system == 'us':
                offset = np.float64(22.0 if gender == 'men' else 20.5)
                return float(np.multiply(np.add(s, offset), 0.847))
            elif system == 'uk':
                offset = np.float64(23.0 if gender == 'men' else 21.5)
                return float(np.multiply(np.add(s, offset), 0.847))
            elif system == 'eu':
                return float(np.multiply(np.divide(np.subtract(s, 2.0), 1.5), 2.54))
            return None
        except Exception:
            return None

    def _from_cm(self, cm, system, gender):
        try:
            c = np.float64(cm)
            if system == 'cm' or system == 'jp':
                return float(c)
            elif system == 'us':
                offset = np.float64(22.0 if gender == 'men' else 20.5)
                return float(np.subtract(np.divide(c, 0.847), offset))
            elif system == 'uk':
                offset = np.float64(23.0 if gender == 'men' else 21.5)
                return float(np.subtract(np.divide(c, 0.847), offset))
            elif system == 'eu':
                return float(np.add(np.multiply(np.divide(c, 2.54), 1.5), 2.0))
            return None
        except Exception:
            return None

    def _is_valid_size(self, size, system, gender):
        try:
            if system == 'cm' or system == 'jp':
                return 20 <= size <= 35
            elif system == 'us':
                r = self.MEN_US_RANGE if gender == 'men' else self.WOMEN_US_RANGE
                return r[0] <= size <= r[1]
            elif system == 'uk':
                if gender == 'men':
                    return 3 <= size <= 15
                return 3 <= size <= 13
            elif system == 'eu':
                return 35 <= size <= 50
            return True
        except Exception:
            return False

    def _sys_name(self, s):
        return {'us': 'US', 'uk': 'UK', 'eu': 'EU', 'cm': 'CM', 'jp': 'JP'}.get(s, s.upper())

    # ── Steps ─────────────────────────────────────────────────────

    def _build_steps(self, from_size, from_sys, cm, to_size, to_sys, gender):
        g = str(_("Men's")) if gender == 'men' else str(_("Women's"))
        steps = [
            str(_('Step 1: Identify the input')),
            str(_('Size')) + f': {from_size} ({self._sys_name(from_sys)})',
            str(_('Gender')) + f': {g}',
            '',
            str(_('Step 2: Convert to centimeters (intermediate unit)')),
        ]

        if from_sys == 'us':
            off = '22' if gender == 'men' else '20.5'
            steps.append(f'CM = ({self._sys_name(from_sys)} + {off}) × 0.847')
            steps.append(f'CM = ({from_size} + {off}) × 0.847')
        elif from_sys == 'uk':
            off = '23' if gender == 'men' else '21.5'
            steps.append(f'CM = ({self._sys_name(from_sys)} + {off}) × 0.847')
            steps.append(f'CM = ({from_size} + {off}) × 0.847')
        elif from_sys == 'eu':
            steps.append(f'CM = (EU - 2) ÷ 1.5 × 2.54')
            steps.append(f'CM = ({from_size} - 2) ÷ 1.5 × 2.54')
        elif from_sys in ('cm', 'jp'):
            steps.append(str(_('Already in centimeters')) + f': {from_size}')

        steps.append(f'CM = {round(cm, 1)} cm')
        steps.append('')

        if to_sys not in ('cm', 'jp'):
            steps.append(str(_('Step 3: Convert centimeters to target system')))
            if to_sys == 'us':
                off = '22' if gender == 'men' else '20.5'
                steps.append(f'US = (CM ÷ 0.847) - {off}')
                steps.append(f'US = ({round(cm, 1)} ÷ 0.847) - {off}')
            elif to_sys == 'uk':
                off = '23' if gender == 'men' else '21.5'
                steps.append(f'UK = (CM ÷ 0.847) - {off}')
                steps.append(f'UK = ({round(cm, 1)} ÷ 0.847) - {off}')
            elif to_sys == 'eu':
                steps.append(f'EU = (CM ÷ 2.54) × 1.5 + 2')
                steps.append(f'EU = ({round(cm, 1)} ÷ 2.54) × 1.5 + 2')
        else:
            steps.append(str(_('Step 3: Result (already in centimeters)')))

        steps.extend([
            '',
            str(_('Final Answer')) + f': {to_size} ({self._sys_name(to_sys)}) {g}',
        ])
        return steps

    # ── Chart ─────────────────────────────────────────────────────

    def _build_chart(self, from_size, from_sys, to_sys, gender, cm):
        try:
            systems = ['us', 'uk', 'eu', 'cm', 'jp']
            labels = [self._sys_name(s) for s in systems]
            sizes = []
            for s in systems:
                v = self._from_cm(cm, s, gender)
                if s in ('us', 'uk'):
                    v = round(v * 2) / 2
                elif s == 'eu':
                    v = round(v)
                else:
                    v = round(v, 1)
                sizes.append(v)

            colors = [
                'rgba(59,130,246,0.8)' if s == from_sys or s == to_sys else 'rgba(156,163,175,0.5)'
                for s in systems
            ]
            borders = [
                '#3b82f6' if s == from_sys or s == to_sys else '#9ca3af'
                for s in systems
            ]

            return {'conversion_chart': {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Shoe Size')),
                        'data': sizes,
                        'backgroundColor': colors,
                        'borderColor': borders,
                        'borderWidth': 2,
                        'borderRadius': 8,
                    }]
                }
            }}
        except Exception:
            return None
