from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import random
import statistics
from collections import Counter


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DiceRoller(View):
    """
    Dice Roller — single, multiple, and custom dice.

    Roll types
        • single   → 1 die of any standard or custom type
        • multiple → N dice of the same type, with statistics
        • custom   → N dice with custom sides + modifier
    """
    template_name = 'other_calculators/dice_roller.html'

    DICE = {
        'd4':   4,   'd6':   6,   'd8':   8,
        'd10':  10,  'd12':  12,  'd20':  20,  'd100': 100,
    }

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Dice Roller'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            rt = data.get('roll_type', 'single')
            dispatch = {
                'single':   self._roll_single,
                'multiple': self._roll_multiple,
                'custom':   self._roll_custom,
            }
            handler = dispatch.get(rt)
            if not handler:
                return self._err(_('Invalid roll type.'))
            return handler(data)
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(e))
        except Exception:
            return self._err(_('An error occurred during the roll.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    def _sides_from(self, data):
        """Resolve the number of sides from dice_type or explicit 'sides'."""
        dt = data.get('dice_type', '')
        if dt in self.DICE:
            return self.DICE[dt], f'D{self.DICE[dt]}'
        s = data.get('sides')
        if s is None or s == '':
            raise ValueError(str(_('Number of sides is required.')))
        s = int(s)
        if s < 2 or s > 1000:
            raise ValueError(str(_('Sides must be between 2 and 1,000.')))
        return s, f'D{s}'

    @staticmethod
    def _stats(results):
        if len(results) < 2:
            return {'min': results[0], 'max': results[0], 'mean': results[0],
                    'median': results[0], 'std_dev': 0, 'sum': results[0], 'count': 1}
        freq = dict(Counter(results))
        mode_val = max(freq, key=freq.get)
        return {
            'min': min(results), 'max': max(results),
            'mean': round(statistics.mean(results), 2),
            'median': statistics.median(results),
            'mode': mode_val,
            'std_dev': round(statistics.stdev(results), 2),
            'sum': sum(results), 'count': len(results),
            'frequency': freq,
        }

    def _chart_rolls(self, results, sides, title):
        """Bar chart of individual roll results."""
        labels = [f'#{i+1}' for i in range(len(results))]
        colors = ['rgba(99,102,241,0.8)'] * len(results)
        return {'main_chart': {
            'type': 'bar',
            'data': {'labels': labels, 'datasets': [{
                'label': str(_('Roll Result')), 'data': results,
                'backgroundColor': colors,
                'borderColor': ['#6366f1'] * len(results),
                'borderWidth': 2, 'borderRadius': 6,
            }]},
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}, 'title': {'display': True, 'text': str(title)}},
                'scales': {'y': {'beginAtZero': True, 'max': sides, 'title': {'display': True, 'text': str(_('Value'))}}},
            },
        }}

    # ── 1) SINGLE DIE ────────────────────────────────────────────────
    def _roll_single(self, data):
        sides, name = self._sides_from(data)
        result = random.randint(1, sides)
        prob = round(100 / sides, 2)

        steps = [
            str(_('Step 1: Die type')),
            f'  • {name} ({sides} {_("sides")})',
            '', str(_('Step 2: Roll')),
            f'  {_("Random")} 1–{sides} → {result}',
            '', str(_('Step 3: Probability')),
            f'  {_("Each side")} = 1/{sides} = {prob}%',
            '', str(_('Result: {result}').format(result=result)),
        ]

        return JsonResponse({
            'success': True, 'roll_type': 'single',
            'result': result,
            'result_label': str(_('{name} Roll').format(name=name)),
            'dice_name': name, 'sides': sides,
            'probability': prob,
            'formula': f'{name} → {result}',
            'step_by_step': steps,
            'chart_data': self._chart_rolls([result], sides, f'{name}: {result}'),
        })

    # ── 2) MULTIPLE DICE ─────────────────────────────────────────────
    def _roll_multiple(self, data):
        sides, name = self._sides_from(data)
        count = data.get('count')
        if count is None or count == '':
            raise ValueError(str(_('Number of dice is required.')))
        count = int(count)
        if count < 1 or count > 100:
            raise ValueError(str(_('Number of dice must be between 1 and 100.')))

        results = [random.randint(1, sides) for _ in range(count)]
        total = sum(results)
        avg = round(statistics.mean(results), 2)
        st = self._stats(results)

        steps = [
            str(_('Step 1: Configuration')),
            f'  • {count}×{name} ({sides} {_("sides")})',
            '', str(_('Step 2: Individual rolls')),
        ]
        for i, r in enumerate(results, 1):
            steps.append(f'  • #{i}: {r}')
        steps += [
            '', str(_('Step 3: Total')),
            f'  {" + ".join(map(str, results))} = {total}',
            '', str(_('Step 4: Average')),
            f'  {total} / {count} = {avg}',
            '', str(_('Step 5: Statistics')),
            f'  {_("Min")}={st["min"]}, {_("Max")}={st["max"]}, {_("Std Dev")}={st["std_dev"]}',
            '', str(_('Result: Total = {total}, Average = {avg}').format(total=total, avg=avg)),
        ]

        return JsonResponse({
            'success': True, 'roll_type': 'multiple',
            'result': total,
            'result_label': str(_('{count}×{name} Total').format(count=count, name=name)),
            'dice_name': name, 'sides': sides, 'count': count,
            'results': results, 'total': total, 'average': avg,
            'statistics': st,
            'formula': f'{count}d{sides} = {total}',
            'step_by_step': steps,
            'chart_data': self._chart_rolls(results, sides, f'{count}×{name}'),
        })

    # ── 3) CUSTOM DICE ───────────────────────────────────────────────
    def _roll_custom(self, data):
        s = data.get('sides')
        if s is None or s == '':
            raise ValueError(str(_('Number of sides is required.')))
        sides = int(s)
        if sides < 2 or sides > 1000:
            raise ValueError(str(_('Sides must be between 2 and 1,000.')))

        c = data.get('count')
        if c is None or c == '':
            raise ValueError(str(_('Number of dice is required.')))
        count = int(c)
        if count < 1 or count > 100:
            raise ValueError(str(_('Number of dice must be between 1 and 100.')))

        modifier = int(data.get('modifier', 0))
        if modifier < -1000 or modifier > 1000:
            raise ValueError(str(_('Modifier must be between -1,000 and 1,000.')))

        results = [random.randint(1, sides) for _ in range(count)]
        dice_sum = sum(results)
        total = dice_sum + modifier
        avg = round(statistics.mean(results), 2)
        st = self._stats(results)

        mod_str = ''
        if modifier > 0:
            mod_str = f' + {modifier}'
        elif modifier < 0:
            mod_str = f' − {abs(modifier)}'

        steps = [
            str(_('Step 1: Configuration')),
            f'  • {count}d{sides}{mod_str}',
            '', str(_('Step 2: Individual rolls')),
        ]
        for i, r in enumerate(results, 1):
            steps.append(f'  • #{i}: {r}')
        steps += [
            '', str(_('Step 3: Dice sum')),
            f'  {" + ".join(map(str, results))} = {dice_sum}',
        ]
        if modifier != 0:
            steps += [
                '', str(_('Step 4: Apply modifier')),
                f'  {dice_sum}{mod_str} = {total}',
            ]
        steps += [
            '', str(_('Result: Total = {total}').format(total=total)),
        ]

        return JsonResponse({
            'success': True, 'roll_type': 'custom',
            'result': total,
            'result_label': str(_('{count}d{sides}{mod} Total').format(count=count, sides=sides, mod=mod_str)),
            'sides': sides, 'count': count, 'modifier': modifier,
            'results': results, 'total': total, 'average': avg,
            'statistics': st,
            'formula': f'{count}d{sides}{mod_str} = {total}',
            'step_by_step': steps,
            'chart_data': self._chart_rolls(results, sides, f'{count}d{sides}{mod_str}'),
        })
