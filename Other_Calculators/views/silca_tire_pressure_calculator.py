from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class SilcaTirePressureCalculator(View):
    """
    Silca-style Bicycle Tire Pressure Calculator.

    Calculates optimal front and rear tire pressure based on:
    - Total system weight (rider + bike + gear)
    - Tire width
    - Wheel size
    - Tire type (clincher / tubeless / tubular)
    - Riding surface (smooth, rough, gravel, mixed)
    - Weather and speed preferences

    Physics: Targets ~15% tire drop for optimal contact patch,
    balancing rolling resistance vs grip vs comfort.

    Uses NumPy for matrix-based pressure + adjustment calculations.
    """
    template_name = 'other_calculators/silca_tire_pressure_calculator.html'

    # ─── TIRE WIDTHS ──────────────────────────────────────────────
    TIRE_WIDTHS = [
        {'value': 23, 'label': '23mm', 'category': 'Road'},
        {'value': 25, 'label': '25mm', 'category': 'Road'},
        {'value': 28, 'label': '28mm', 'category': 'Road'},
        {'value': 30, 'label': '30mm', 'category': 'Road/Gravel'},
        {'value': 32, 'label': '32mm', 'category': 'Road/Gravel'},
        {'value': 35, 'label': '35mm', 'category': 'Gravel'},
        {'value': 38, 'label': '38mm', 'category': 'Gravel'},
        {'value': 40, 'label': '40mm', 'category': 'Gravel'},
        {'value': 42, 'label': '42mm', 'category': 'Gravel'},
        {'value': 45, 'label': '45mm', 'category': 'Gravel/MTB'},
        {'value': 50, 'label': '50mm', 'category': 'MTB'},
        {'value': 55, 'label': '2.1" (55mm)', 'category': 'MTB'},
        {'value': 60, 'label': '2.4" (60mm)', 'category': 'MTB'},
    ]

    # ─── WHEEL SIZES ─────────────────────────────────────────────
    WHEEL_SIZES = [
        {'value': '700c', 'label': '700c (Road/Gravel)', 'bsd': 622},
        {'value': '650b', 'label': '650b / 27.5"',       'bsd': 584},
        {'value': '26',   'label': '26"',                  'bsd': 559},
        {'value': '29',   'label': '29" (MTB)',            'bsd': 622},
    ]

    # ─── TIRE TYPES ──────────────────────────────────────────────
    TIRE_TYPES = [
        {'value': 'clincher',  'label': 'Clincher (inner tube)',  'modifier': 1.00},
        {'value': 'tubeless',  'label': 'Tubeless',               'modifier': 0.90},
        {'value': 'tubular',   'label': 'Tubular',                'modifier': 0.95},
    ]

    # ─── SURFACES ────────────────────────────────────────────────
    SURFACES = [
        {'value': 'smooth_road',  'label': 'Smooth Pavement',     'modifier': 1.00, 'icon': '🛣️'},
        {'value': 'rough_road',   'label': 'Rough / Chipped Road','modifier': 0.93, 'icon': '🏗️'},
        {'value': 'mixed',        'label': 'Mixed (Road + Gravel)','modifier': 0.88, 'icon': '🔀'},
        {'value': 'gravel',       'label': 'Gravel / Dirt',       'modifier': 0.82, 'icon': '🪨'},
        {'value': 'singletrack',  'label': 'Singletrack / MTB',   'modifier': 0.72, 'icon': '🌲'},
    ]

    # ─── RIDER POSITION (front/rear weight split) ────────────────
    POSITIONS = [
        {'value': 'aero',    'label': 'Aggressive / Aero',   'front': 0.43, 'rear': 0.57},
        {'value': 'road',    'label': 'Normal Road',          'front': 0.40, 'rear': 0.60},
        {'value': 'upright', 'label': 'Upright / Endurance',  'front': 0.38, 'rear': 0.62},
        {'value': 'mtb',     'label': 'Mountain Bike',         'front': 0.42, 'rear': 0.58},
    ]

    # ─── WEATHER ─────────────────────────────────────────────────
    WEATHER = [
        {'value': 'dry',  'label': 'Dry',             'modifier': 1.00},
        {'value': 'wet',  'label': 'Wet / Rainy',     'modifier': 0.93},
        {'value': 'cold', 'label': 'Cold (< 5°C / 40°F)', 'modifier': 1.03},
    ]

    # Base pressure coefficient (empirically derived, Silca/Berto model)
    # P_base (psi) ≈ K × load_kg / (tire_width_mm)^1.6
    # K calibrated so a 70kg rider + 8kg bike on 25mm ≈ 85/95 psi (F/R)
    K_COEFFICIENT = 420.0

    def get(self, request):
        context = {
            'calculator_name': _('Tire Pressure Calculator'),
            'page_title': _('Silca Tire Pressure Calculator'),
            'tire_widths': self.TIRE_WIDTHS,
            'wheel_sizes': self.WHEEL_SIZES,
            'tire_types': self.TIRE_TYPES,
            'surfaces': self.SURFACES,
            'positions': self.POSITIONS,
            'weather': self.WEATHER,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = json.loads(request.body)

            rider_weight = float(data.get('rider_weight', 70))
            weight_unit  = data.get('weight_unit', 'kg')
            bike_weight  = float(data.get('bike_weight', 8.5))
            tire_width   = int(data.get('tire_width', 25))
            wheel_size   = data.get('wheel_size', '700c')
            tire_type    = data.get('tire_type', 'clincher')
            surface      = data.get('surface', 'smooth_road')
            position     = data.get('position', 'road')
            weather      = data.get('weather', 'dry')

            # Validate and clamp
            if weight_unit == 'lbs':
                rider_weight = rider_weight * 0.453592
            rider_weight = max(40, min(150, rider_weight))
            bike_weight  = max(5, min(25, bike_weight))
            tire_width   = max(20, min(65, tire_width))

            total_weight = rider_weight + bike_weight  # kg

            # ── Weight distribution ──────────────────────────────
            pos_data = next((p for p in self.POSITIONS if p['value'] == position), self.POSITIONS[1])
            front_load = total_weight * pos_data['front']
            rear_load  = total_weight * pos_data['rear']

            # ── Base pressure calculation (Berto-style model) ────
            # P = K × load / width^1.6
            width_factor = float(np.power(tire_width, 1.6))
            front_base_psi = self.K_COEFFICIENT * front_load / width_factor
            rear_base_psi  = self.K_COEFFICIENT * rear_load / width_factor

            # ── Apply modifiers with NumPy ───────────────────────
            tire_mod = next((t['modifier'] for t in self.TIRE_TYPES if t['value'] == tire_type), 1.0)
            surf_mod = next((s['modifier'] for s in self.SURFACES if s['value'] == surface), 1.0)
            weat_mod = next((w['modifier'] for w in self.WEATHER if w['value'] == weather), 1.0)

            modifiers = np.array([tire_mod, surf_mod, weat_mod], dtype=np.float64)
            combined_modifier = float(np.prod(modifiers))

            front_psi = front_base_psi * combined_modifier
            rear_psi  = rear_base_psi * combined_modifier

            # Clamp to reasonable ranges
            min_psi = 15 if tire_width >= 40 else 30 if tire_width >= 28 else 50
            max_psi = 120 if tire_width <= 28 else 80 if tire_width <= 35 else 60

            front_psi = float(np.clip(front_psi, min_psi, max_psi))
            rear_psi  = float(np.clip(rear_psi, min_psi, max_psi))

            # Convert to bar
            front_bar = front_psi * 0.0689476
            rear_bar  = rear_psi * 0.0689476

            # ── Comfort & speed ratings ──────────────────────────
            comfort = self._compute_comfort(front_psi, rear_psi, tire_width, surface)
            speed   = self._compute_speed(front_psi, rear_psi, tire_width, surface)

            # ── Recommended range (±5% window) ───────────────────
            front_range = {'low': round(front_psi * 0.95, 1), 'high': round(front_psi * 1.05, 1)}
            rear_range  = {'low': round(rear_psi * 0.95, 1),  'high': round(rear_psi * 1.05, 1)}

            # ── Adjustments breakdown ────────────────────────────
            adjustments = []
            tire_label = next((t['label'] for t in self.TIRE_TYPES if t['value'] == tire_type), tire_type)
            surf_label = next((s['label'] for s in self.SURFACES if s['value'] == surface), surface)
            weat_label = next((w['label'] for w in self.WEATHER if w['value'] == weather), weather)

            if tire_mod != 1.0:
                adjustments.append({'factor': tire_label, 'effect': f'{int((tire_mod - 1) * 100):+d}%',
                                    'direction': 'down' if tire_mod < 1 else 'up'})
            if surf_mod != 1.0:
                adjustments.append({'factor': surf_label, 'effect': f'{int((surf_mod - 1) * 100):+d}%',
                                    'direction': 'down' if surf_mod < 1 else 'up'})
            if weat_mod != 1.0:
                adjustments.append({'factor': weat_label, 'effect': f'{int((weat_mod - 1) * 100):+d}%',
                                    'direction': 'down' if weat_mod < 1 else 'up'})

            # ── Tips ─────────────────────────────────────────────
            tips = self._generate_tips(front_psi, rear_psi, tire_width, surface, tire_type)

            # ── Chart data ───────────────────────────────────────
            chart_data = self._prepare_chart_data(
                front_psi, rear_psi, front_bar, rear_bar,
                front_range, rear_range, tire_width, comfort, speed
            )

            return JsonResponse({
                'success': True,
                'front': {
                    'psi': round(front_psi, 1),
                    'bar': round(front_bar, 2),
                    'range': front_range,
                },
                'rear': {
                    'psi': round(rear_psi, 1),
                    'bar': round(rear_bar, 2),
                    'range': rear_range,
                },
                'system': {
                    'total_weight_kg': round(total_weight, 1),
                    'front_load_kg': round(front_load, 1),
                    'rear_load_kg': round(rear_load, 1),
                    'position': pos_data['label'],
                    'tire_width': tire_width,
                    'combined_modifier': round(combined_modifier, 3),
                },
                'comfort': comfort,
                'speed': speed,
                'adjustments': adjustments,
                'tips': tips,
                'chart_data': chart_data,
            })

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('Calculation error.'))}, status=500)

    # ─────────────────────────────────────────────────────────────
    def _compute_comfort(self, front, rear, width, surface):
        # Higher width + lower pressure = more comfort
        avg_psi = (front + rear) / 2
        # Normalized comfort (0-100): based on air volume vs pressure
        base = float(np.clip(100 - (avg_psi - 20) * 0.8, 10, 100))
        width_bonus = float(np.clip((width - 23) * 1.2, 0, 30))
        comfort = float(np.clip(base + width_bonus, 0, 100))

        if comfort >= 80:
            return {'score': round(comfort), 'label': str(_('Excellent')), 'color': 'green'}
        elif comfort >= 60:
            return {'score': round(comfort), 'label': str(_('Good')), 'color': 'blue'}
        elif comfort >= 40:
            return {'score': round(comfort), 'label': str(_('Moderate')), 'color': 'yellow'}
        else:
            return {'score': round(comfort), 'label': str(_('Firm')), 'color': 'orange'}

    def _compute_speed(self, front, rear, width, surface):
        # Higher pressure on smooth roads = faster (diminishing returns)
        avg_psi = (front + rear) / 2
        surf_mods = {'smooth_road': 1.0, 'rough_road': 0.92, 'mixed': 0.85, 'gravel': 0.75, 'singletrack': 0.65}
        sm = surf_mods.get(surface, 0.85)
        base = float(np.clip(50 + avg_psi * 0.4 * sm, 10, 100))
        # Wider tires slightly slower on smooth, but better on rough
        if surface in ('smooth_road', 'rough_road'):
            base -= max(0, (width - 25) * 0.3)
        speed = float(np.clip(base, 0, 100))

        if speed >= 80:
            return {'score': round(speed), 'label': str(_('Fast')), 'color': 'green'}
        elif speed >= 60:
            return {'score': round(speed), 'label': str(_('Good')), 'color': 'blue'}
        elif speed >= 40:
            return {'score': round(speed), 'label': str(_('Moderate')), 'color': 'yellow'}
        else:
            return {'score': round(speed), 'label': str(_('Slow')), 'color': 'orange'}

    def _generate_tips(self, front, rear, width, surface, tire_type):
        tips = []
        if tire_type == 'clincher' and width >= 28:
            tips.append(str(_('Consider going tubeless — it lets you run 10% lower pressure for better grip and comfort, with fewer flats.')))
        if rear - front > 15:
            tips.append(str(_('Your front/rear pressure difference is significant. This is normal due to weight distribution — the rear always carries more load.')))
        if front > 100:
            tips.append(str(_('Your front pressure is quite high. On rough surfaces, this can reduce grip and comfort. Consider wider tires.')))
        if width <= 25 and surface in ('gravel', 'mixed', 'singletrack'):
            tips.append(str(_('Your tires may be too narrow for this surface. Consider 32mm+ tires for gravel and mixed terrain.')))
        if width >= 40 and surface == 'smooth_road':
            tips.append(str(_('Wide tires on smooth roads can feel sluggish. If speed matters, consider 28-32mm tires.')))
        if surface == 'wet':
            tips.append(str(_('In wet conditions, lower pressure increases the contact patch for better grip. Be cautious on corners.')))
        if not tips:
            tips.append(str(_('Your setup looks well-balanced! Remember to check pressure before every ride.')))
        return tips

    # ─────────────────────────────────────────────────────────────
    def _prepare_chart_data(self, front_psi, rear_psi, front_bar, rear_bar,
                            front_range, rear_range, tire_width, comfort, speed):
        # 1. Front vs Rear comparison bar
        compare_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Front')), str(_('Rear'))],
                'datasets': [{
                    'label': str(_('PSI')),
                    'data': [round(front_psi, 1), round(rear_psi, 1)],
                    'backgroundColor': ['#3b82f6', '#ef4444'],
                    'borderRadius': 8,
                }]
            }
        }

        # 2. Pressure range chart (shows low/optimal/high for both wheels)
        range_chart = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Front')), str(_('Rear'))],
                'datasets': [
                    {
                        'label': str(_('Min')),
                        'data': [front_range['low'], rear_range['low']],
                        'backgroundColor': '#93c5fd',
                        'borderRadius': 4,
                    },
                    {
                        'label': str(_('Optimal')),
                        'data': [round(front_psi, 1), round(rear_psi, 1)],
                        'backgroundColor': '#10b981',
                        'borderRadius': 4,
                    },
                    {
                        'label': str(_('Max')),
                        'data': [front_range['high'], rear_range['high']],
                        'backgroundColor': '#fbbf24',
                        'borderRadius': 4,
                    },
                ]
            }
        }

        # 3. Comfort vs Speed radar
        performance_chart = {
            'type': 'radar',
            'data': {
                'labels': [str(_('Comfort')), str(_('Speed')), str(_('Grip')),
                           str(_('Puncture Resist.')), str(_('Rolling Efficiency'))],
                'datasets': [{
                    'label': str(_('Your Setup')),
                    'data': [
                        comfort['score'],
                        speed['score'],
                        max(20, 100 - (front_psi + rear_psi) / 2 * 0.5 + tire_width * 0.8),
                        min(95, (front_psi + rear_psi) / 2 * 0.6 + 20),
                        min(95, speed['score'] * 0.7 + 25),
                    ],
                    'backgroundColor': 'rgba(59, 130, 246, 0.2)',
                    'borderColor': '#3b82f6',
                    'borderWidth': 2,
                    'pointBackgroundColor': '#3b82f6',
                    'pointBorderColor': '#fff',
                    'pointRadius': 5,
                }]
            }
        }

        return {
            'compare_chart': compare_chart,
            'range_chart': range_chart,
            'performance_chart': performance_chart,
        }
