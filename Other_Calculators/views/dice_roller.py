from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import random
import statistics
import numpy as np
from collections import Counter


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DiceRoller(View):
    """
    Professional Dice Roller with Comprehensive Features
    
    This calculator provides dice rolling with:
    - Roll single or multiple dice
    - Support for standard dice (d4, d6, d8, d10, d12, d20, d100)
    - Custom dice with any number of sides
    - Statistics and analysis
    - Visualizations
    
    Features:
    - Supports multiple dice types
    - Provides statistics and analysis
    - Interactive visualizations
    - Step-by-step solutions
    """
    template_name = 'other_calculators/dice_roller.html'
    
    # Standard dice configurations
    STANDARD_DICE = {
        'd4': {'sides': 4, 'name': 'D4'},
        'd6': {'sides': 6, 'name': 'D6'},
        'd8': {'sides': 8, 'name': 'D8'},
        'd10': {'sides': 10, 'name': 'D10'},
        'd12': {'sides': 12, 'name': 'D12'},
        'd20': {'sides': 20, 'name': 'D20'},
        'd100': {'sides': 100, 'name': 'D100'},
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Dice Roller'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            roll_type = data.get('roll_type', 'single')
            
            if roll_type == 'single':
                return self._roll_single_die(data)
            elif roll_type == 'multiple':
                return self._roll_multiple_dice(data)
            elif roll_type == 'custom':
                return self._roll_custom_dice(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid roll type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _roll_single_die(self, data):
        """Roll a single die"""
        try:
            # Check for required fields
            if 'dice_type' not in data or data.get('dice_type') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Dice type is required.')
                }, status=400)
            
            dice_type = data.get('dice_type', 'd6')
            
            # Validate dice type
            if dice_type not in self.STANDARD_DICE and dice_type != 'custom':
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid dice type.')
                }, status=400)
            
            if dice_type == 'custom':
                # Custom die
                if 'sides' not in data or data.get('sides') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Number of sides is required for custom dice.')
                    }, status=400)
                
                try:
                    sides = int(data.get('sides', 6))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Number of sides must be a valid integer.')
                    }, status=400)
                
                if sides < 2:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dice must have at least 2 sides.')
                    }, status=400)
                
                if sides > 1000:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dice cannot have more than 1000 sides.')
                    }, status=400)
                
                dice_name = f'D{sides}'
            else:
                # Standard die
                dice_config = self.STANDARD_DICE[dice_type]
                sides = dice_config['sides']
                dice_name = dice_config['name']
            
            # Roll the die
            result = random.randint(1, sides)
            
            response_data = {
                'success': True,
                'roll_type': 'single',
                'dice_type': dice_type,
                'dice_name': dice_name,
                'sides': sides,
                'result': result,
                'step_by_step': self._prepare_single_roll_steps(dice_name, sides, result),
                'chart_data': self._prepare_single_roll_chart_data(sides, result),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error rolling dice: {error}').format(error=str(e))
            }, status=500)
    
    def _roll_multiple_dice(self, data):
        """Roll multiple dice"""
        try:
            # Check for required fields
            if 'dice_type' not in data or data.get('dice_type') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Dice type is required.')
                }, status=400)
            
            if 'count' not in data or data.get('count') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of dice is required.')
                }, status=400)
            
            dice_type = data.get('dice_type', 'd6')
            
            try:
                count = int(data.get('count', 1))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Number of dice must be a valid integer.')
                }, status=400)
            
            if count < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('You must roll at least 1 die.')
                }, status=400)
            
            if count > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('You cannot roll more than 100 dice at once.')
                }, status=400)
            
            # Validate dice type
            if dice_type not in self.STANDARD_DICE and dice_type != 'custom':
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid dice type.')
                }, status=400)
            
            if dice_type == 'custom':
                if 'sides' not in data or data.get('sides') is None:
                    return JsonResponse({
                        'success': False,
                        'error': _('Number of sides is required for custom dice.')
                    }, status=400)
                
                try:
                    sides = int(data.get('sides', 6))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Number of sides must be a valid integer.')
                    }, status=400)
                
                if sides < 2:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dice must have at least 2 sides.')
                    }, status=400)
                
                if sides > 1000:
                    return JsonResponse({
                        'success': False,
                        'error': _('Dice cannot have more than 1000 sides.')
                    }, status=400)
                
                dice_name = f'D{sides}'
            else:
                dice_config = self.STANDARD_DICE[dice_type]
                sides = dice_config['sides']
                dice_name = dice_config['name']
            
            # Roll multiple dice
            results = [random.randint(1, sides) for _ in range(count)]
            total = sum(results)
            average = statistics.mean(results) if results else 0
            
            # Calculate statistics
            stats = self._calculate_statistics(results)
            
            response_data = {
                'success': True,
                'roll_type': 'multiple',
                'dice_type': dice_type,
                'dice_name': dice_name,
                'sides': sides,
                'count': count,
                'results': results,
                'total': total,
                'average': round(average, 2),
                'statistics': stats,
                'step_by_step': self._prepare_multiple_roll_steps(dice_name, sides, count, results, total, average),
                'chart_data': self._prepare_multiple_roll_chart_data(results, sides),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error rolling dice: {error}').format(error=str(e))
            }, status=500)
    
    def _roll_custom_dice(self, data):
        """Roll custom dice with modifiers"""
        try:
            # Check for required fields
            if 'sides' not in data or data.get('sides') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of sides is required.')
                }, status=400)
            
            if 'count' not in data or data.get('count') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of dice is required.')
                }, status=400)
            
            try:
                sides = int(data.get('sides', 6))
                count = int(data.get('count', 1))
                modifier = int(data.get('modifier', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Sides, count, and modifier must be valid integers.')
                }, status=400)
            
            if sides < 2:
                return JsonResponse({
                    'success': False,
                    'error': _('Dice must have at least 2 sides.')
                }, status=400)
            
            if sides > 1000:
                return JsonResponse({
                    'success': False,
                    'error': _('Dice cannot have more than 1000 sides.')
                }, status=400)
            
            if count < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('You must roll at least 1 die.')
                }, status=400)
            
            if count > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('You cannot roll more than 100 dice at once.')
                }, status=400)
            
            if modifier < -1000 or modifier > 1000:
                return JsonResponse({
                    'success': False,
                    'error': _('Modifier must be between -1000 and 1000.')
                }, status=400)
            
            # Roll dice
            results = [random.randint(1, sides) for _ in range(count)]
            total = sum(results) + modifier
            average = statistics.mean(results) if results else 0
            
            # Calculate statistics
            stats = self._calculate_statistics(results)
            
            response_data = {
                'success': True,
                'roll_type': 'custom',
                'sides': sides,
                'count': count,
                'modifier': modifier,
                'results': results,
                'total': total,
                'average': round(average, 2),
                'statistics': stats,
                'step_by_step': self._prepare_custom_roll_steps(sides, count, modifier, results, total),
                'chart_data': self._prepare_multiple_roll_chart_data(results, sides),
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error rolling dice: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_statistics(self, results):
        """Calculate statistics for dice rolls"""
        if not results:
            return {}
        
        stats = {
            'min': min(results),
            'max': max(results),
            'mean': round(statistics.mean(results), 2),
            'median': statistics.median(results),
            'mode': statistics.mode(results) if len(results) > 1 and len(set(results)) < len(results) else None,
            'sum': sum(results),
            'count': len(results),
        }
        
        # Calculate standard deviation if we have enough data
        if len(results) > 1:
            stats['std_dev'] = round(statistics.stdev(results), 2)
        else:
            stats['std_dev'] = 0
        
        # Count frequency of each result
        counter = Counter(results)
        stats['frequency'] = dict(counter)
        
        return stats
    
    def _prepare_single_roll_steps(self, dice_name, sides, result):
        """Prepare step-by-step for single die roll"""
        steps = []
        steps.append(_('Step 1: Identify the die'))
        steps.append(_('Die Type: {dice}').format(dice=dice_name))
        steps.append(_('Number of Sides: {sides}').format(sides=sides))
        steps.append('')
        steps.append(_('Step 2: Roll the die'))
        steps.append(_('Random number generator selects a value between 1 and {sides}').format(sides=sides))
        steps.append('')
        steps.append(_('Step 3: Result'))
        steps.append(_('Roll Result: {result}').format(result=result))
        steps.append('')
        steps.append(_('Note: Each side has an equal probability of {prob}%').format(prob=round(100/sides, 2)))
        return steps
    
    def _prepare_multiple_roll_steps(self, dice_name, sides, count, results, total, average):
        """Prepare step-by-step for multiple dice rolls"""
        steps = []
        steps.append(_('Step 1: Identify the dice'))
        steps.append(_('Die Type: {dice}').format(dice=dice_name))
        steps.append(_('Number of Sides: {sides}').format(sides=sides))
        steps.append(_('Number of Dice: {count}').format(count=count))
        steps.append('')
        steps.append(_('Step 2: Roll all dice'))
        for i, result in enumerate(results, 1):
            steps.append(_('Die {num}: {result}').format(num=i, result=result))
        steps.append('')
        steps.append(_('Step 3: Calculate total'))
        steps.append(_('Total = {results} = {total}').format(
            results=' + '.join(map(str, results)),
            total=total
        ))
        steps.append('')
        steps.append(_('Step 4: Calculate average'))
        steps.append(_('Average = Total ÷ Count = {total} ÷ {count} = {avg}').format(
            total=total, count=count, avg=average
        ))
        return steps
    
    def _prepare_custom_roll_steps(self, sides, count, modifier, results, total):
        """Prepare step-by-step for custom dice roll"""
        steps = []
        steps.append(_('Step 1: Identify the dice'))
        steps.append(_('Number of Sides: {sides}').format(sides=sides))
        steps.append(_('Number of Dice: {count}').format(count=count))
        steps.append(_('Modifier: {modifier}').format(modifier=modifier))
        steps.append('')
        steps.append(_('Step 2: Roll all dice'))
        for i, result in enumerate(results, 1):
            steps.append(_('Die {num}: {result}').format(num=i, result=result))
        steps.append('')
        steps.append(_('Step 3: Calculate total with modifier'))
        dice_sum = sum(results)
        steps.append(_('Dice Sum = {results} = {dice_sum}').format(
            results=' + '.join(map(str, results)),
            dice_sum=dice_sum
        ))
        if modifier != 0:
            steps.append(_('Total = Dice Sum + Modifier = {dice_sum} + {modifier} = {total}').format(
                dice_sum=dice_sum, modifier=modifier, total=total
            ))
        else:
            steps.append(_('Total = {total}').format(total=total))
        return steps
    
    def _prepare_single_roll_chart_data(self, sides, result):
        """Prepare chart data for single roll"""
        # Create a bar chart showing all possible outcomes with the result highlighted
        outcomes = list(range(1, sides + 1))
        colors = ['rgba(239, 68, 68, 0.8)' if x == result else 'rgba(59, 130, 246, 0.3)' for x in outcomes]
        
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(x) for x in outcomes],
                'datasets': [{
                    'label': _('Possible Outcomes'),
                    'data': [1 if x == result else 0.1 for x in outcomes],
                    'backgroundColor': colors,
                    'borderColor': ['#ef4444' if x == result else '#3b82f6' for x in outcomes],
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': True,
                'plugins': {
                    'legend': {
                        'display': False
                    },
                    'title': {
                        'display': True,
                        'text': _('Roll Result: {result}').format(result=result)
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'display': False
                    }
                }
            }
        }
        
        return {'single_roll_chart': chart_config}
    
    def _prepare_multiple_roll_chart_data(self, results, sides):
        """Prepare chart data for multiple rolls"""
        # Create a histogram showing frequency of each result
        counter = Counter(results)
        outcomes = list(range(1, sides + 1))
        frequencies = [counter.get(x, 0) for x in outcomes]
        
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(x) for x in outcomes],
                'datasets': [{
                    'label': _('Frequency'),
                    'data': frequencies,
                    'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                    'borderColor': '#3b82f6',
                    'borderWidth': 2
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': True,
                'plugins': {
                    'legend': {
                        'display': False
                    },
                    'title': {
                        'display': True,
                        'text': _('Roll Frequency Distribution')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True,
                        'title': {
                            'display': True,
                            'text': _('Frequency')
                        }
                    },
                    'x': {
                        'title': {
                            'display': True,
                            'text': _('Roll Value')
                        }
                    }
                }
            }
        }
        
        return {'multiple_roll_chart': chart_config}
