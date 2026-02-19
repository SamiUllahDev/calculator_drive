from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, Eq, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoveCalculator(View):
    """
    Professional Love Calculator with Comprehensive Features
    
    This calculator provides love compatibility calculations with:
    - Calculate love percentage from two names
    - Calculate compatibility score
    - Analyze name compatibility
    - Provide relationship insights
    
    Features:
    - Supports multiple calculation methods
    - Handles various name formats
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/love_calculator.html'
    
    # Love percentage categories
    LOVE_CATEGORIES = {
        'excellent': (90, 100, _('Excellent Match!')),
        'very_good': (75, 89, _('Very Good Match!')),
        'good': (60, 74, _('Good Match!')),
        'fair': (40, 59, _('Fair Match')),
        'poor': (0, 39, _('Needs Work')),
    }

    # Romantic tips by category (for professional UX)
    ROMANTIC_TIPS = {
        'excellent': _('A rare connection! Keep nurturing trust and communication.'),
        'very_good': _('Strong compatibility—great foundation for something special.'),
        'good': _('Solid potential. Small gestures and quality time can deepen the bond.'),
        'fair': _('Every relationship takes effort. Patience and understanding go a long way.'),
        'poor': _('Names are just fun—real love is built on respect and shared values.'),
    }

    def _get_romantic_tip(self, category_key):
        """Return a short romantic tip for the given category."""
        return self.ROMANTIC_TIPS.get(category_key, self.ROMANTIC_TIPS['poor'])

    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Love Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'love_percentage')
            
            if calc_type == 'love_percentage':
                return self._calculate_love_percentage(data)
            elif calc_type == 'compatibility':
                return self._calculate_compatibility(data)
            elif calc_type == 'name_analysis':
                return self._analyze_names(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
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
    
    def _calculate_love_percentage(self, data):
        """Calculate love percentage from two names"""
        try:
            if 'name1' not in data or not data.get('name1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First name is required.')
                }, status=400)
            
            if 'name2' not in data or not data.get('name2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second name is required.')
                }, status=400)
            
            name1 = data.get('name1', '').strip()
            name2 = data.get('name2', '').strip()
            
            if not name1 or not name2:
                return JsonResponse({
                    'success': False,
                    'error': _('Both names are required.')
                }, status=400)
            
            if len(name1) > 100 or len(name2) > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Names must be 100 characters or less.')
                }, status=400)
            
            # Calculate love percentage using simple algorithm
            # Combine names and count letters
            combined = (name1 + name2).lower().replace(' ', '')
            
            if len(combined) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Names must contain at least one letter.')
                }, status=400)
            
            # Count occurrences of L, O, V, E
            l_count = combined.count('l')
            o_count = combined.count('o')
            v_count = combined.count('v')
            e_count = combined.count('e')
            
            # Calculate percentage using the "LOVE" algorithm
            # This is a simplified version - in reality, there are various algorithms
            love_score = l_count + o_count + v_count + e_count
            
            # Alternative algorithm: count all letters and calculate percentage
            total_letters = len(combined)
            letter_percentage = float(np.multiply(
                np.divide(love_score, total_letters),
                100.0
            )) if total_letters > 0 else 0
            
            # Another method: use name lengths and common letters
            name1_lower = name1.lower().replace(' ', '')
            name2_lower = name2.lower().replace(' ', '')
            
            # Count common letters
            common_letters = 0
            for char in set(name1_lower):
                if char.isalpha():
                    common_letters += min(name1_lower.count(char), name2_lower.count(char))
            
            # Calculate percentage based on common letters
            total_unique = len(set(name1_lower + name2_lower))
            common_percentage = float(np.multiply(
                np.divide(common_letters, total_unique) if total_unique > 0 else 0,
                100.0
            ))
            
            # Combine methods for final percentage (algorithm choice)
            algorithm = data.get('algorithm', 'classic')
            if algorithm == 'balanced':
                # 50/50 weights + length similarity
                final_percentage = float(np.add(
                    np.multiply(letter_percentage, 0.5),
                    np.multiply(common_percentage, 0.5)
                ))
            else:
                # Classic: 40% LOVE letters, 60% common
                final_percentage = float(np.add(
                    np.multiply(letter_percentage, 0.4),
                    np.multiply(common_percentage, 0.6)
                ))

            # Length similarity factor (both algorithms)
            length_factor = float(np.multiply(
                np.divide(min(len(name1_lower), len(name2_lower)), max(len(name1_lower), len(name2_lower))),
                10.0
            )) if max(len(name1_lower), len(name2_lower)) > 0 else 0

            final_percentage = float(np.add(final_percentage, length_factor))
            
            # Normalize to 0-100
            final_percentage = max(0, min(100, final_percentage))
            
            # Round to integer for display
            love_percentage = int(round(final_percentage))
            
            # Get category
            category = self._get_love_category(love_percentage)
            
            steps = self._prepare_love_percentage_steps(name1, name2, combined, l_count, o_count, v_count, e_count, love_score, letter_percentage, common_letters, common_percentage, final_percentage, love_percentage)
            
            chart_data = self._prepare_love_percentage_chart_data(love_percentage, category)
            romantic_tip = self._get_romantic_tip(category['name'])
            share_summary = f'{name1} & {name2}: {love_percentage}% — {category["message"]}'

            return JsonResponse({
                'success': True,
                'calc_type': 'love_percentage',
                'name1': name1,
                'name2': name2,
                'love_percentage': love_percentage,
                'category': category['name'],
                'message': category['message'],
                'romantic_tip': romantic_tip,
                'share_summary': share_summary,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating love percentage: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_compatibility(self, data):
        """Calculate compatibility score"""
        try:
            if 'name1' not in data or not data.get('name1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First name is required.')
                }, status=400)
            
            if 'name2' not in data or not data.get('name2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second name is required.')
                }, status=400)
            
            name1 = data.get('name1', '').strip()
            name2 = data.get('name2', '').strip()
            
            if not name1 or not name2:
                return JsonResponse({
                    'success': False,
                    'error': _('Both names are required.')
                }, status=400)
            
            # Calculate compatibility using multiple factors
            name1_lower = name1.lower().replace(' ', '')
            name2_lower = name2.lower().replace(' ', '')
            
            # Factor 1: Common letters
            common_letters = 0
            for char in set(name1_lower):
                if char.isalpha():
                    common_letters += min(name1_lower.count(char), name2_lower.count(char))
            
            total_letters = len(name1_lower) + len(name2_lower)
            common_score = float(np.multiply(
                np.divide(common_letters, total_letters) if total_letters > 0 else 0,
                100.0
            ))
            
            # Factor 2: Name length similarity
            len1 = len(name1_lower)
            len2 = len(name2_lower)
            length_score = float(np.multiply(
                np.divide(min(len1, len2), max(len1, len2)) if max(len1, len2) > 0 else 0,
                100.0
            ))
            
            # Factor 3: Vowel/Consonant ratio similarity
            vowels = 'aeiou'
            v1 = sum(1 for c in name1_lower if c in vowels)
            v2 = sum(1 for c in name2_lower if c in vowels)
            c1 = len1 - v1
            c2 = len2 - v2
            
            vowel_ratio1 = float(np.divide(v1, len1)) if len1 > 0 else 0
            vowel_ratio2 = float(np.divide(v2, len2)) if len2 > 0 else 0
            vowel_score = float(np.multiply(
                np.subtract(1.0, abs(np.subtract(vowel_ratio1, vowel_ratio2))),
                100.0
            ))
            
            # Combine factors
            compatibility = float(np.divide(
                np.add(np.add(common_score, length_score), vowel_score),
                3.0
            ))
            
            compatibility = max(0, min(100, compatibility))
            compatibility = int(round(compatibility))
            
            category = self._get_love_category(compatibility)
            
            steps = self._prepare_compatibility_steps(name1, name2, common_letters, common_score, length_score, vowel_score, compatibility)
            
            chart_data = self._prepare_compatibility_chart_data(compatibility, common_score, length_score, vowel_score)
            romantic_tip = self._get_romantic_tip(category['name'])
            share_summary = f'{name1} & {name2}: {compatibility}% — {category["message"]}'

            return JsonResponse({
                'success': True,
                'calc_type': 'compatibility',
                'name1': name1,
                'name2': name2,
                'compatibility': compatibility,
                'common_score': round(common_score, 1),
                'length_score': round(length_score, 1),
                'vowel_score': round(vowel_score, 1),
                'category': category['name'],
                'message': category['message'],
                'romantic_tip': romantic_tip,
                'share_summary': share_summary,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating compatibility: {error}').format(error=str(e))
            }, status=500)
    
    def _analyze_names(self, data):
        """Analyze names for compatibility"""
        try:
            if 'name1' not in data or not data.get('name1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First name is required.')
                }, status=400)
            
            if 'name2' not in data or not data.get('name2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second name is required.')
                }, status=400)
            
            name1 = data.get('name1', '').strip()
            name2 = data.get('name2', '').strip()
            
            if not name1 or not name2:
                return JsonResponse({
                    'success': False,
                    'error': _('Both names are required.')
                }, status=400)
            
            name1_lower = name1.lower().replace(' ', '')
            name2_lower = name2.lower().replace(' ', '')
            
            # Analyze various aspects
            analysis = {
                'name1_length': len(name1_lower),
                'name2_length': len(name2_lower),
                'common_letters': [],
                'unique_letters_name1': [],
                'unique_letters_name2': [],
                'vowel_count_name1': 0,
                'vowel_count_name2': 0,
                'consonant_count_name1': 0,
                'consonant_count_name2': 0,
            }
            
            vowels = 'aeiou'
            analysis['vowel_count_name1'] = sum(1 for c in name1_lower if c in vowels)
            analysis['vowel_count_name2'] = sum(1 for c in name2_lower if c in vowels)
            analysis['consonant_count_name1'] = len(name1_lower) - analysis['vowel_count_name1']
            analysis['consonant_count_name2'] = len(name2_lower) - analysis['vowel_count_name2']
            
            # Find common letters
            set1 = set(name1_lower)
            set2 = set(name2_lower)
            analysis['common_letters'] = sorted(list(set1.intersection(set2)))
            analysis['unique_letters_name1'] = sorted(list(set1 - set2))
            analysis['unique_letters_name2'] = sorted(list(set2 - set1))
            
            steps = self._prepare_name_analysis_steps(name1, name2, analysis)
            share_summary = f'{name1} & {name2}: {len(analysis["common_letters"])} common letters'

            return JsonResponse({
                'success': True,
                'calc_type': 'name_analysis',
                'name1': name1,
                'name2': name2,
                'analysis': analysis,
                'share_summary': share_summary,
                'step_by_step': steps,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error analyzing names: {error}').format(error=str(e))
            }, status=500)
    
    def _get_love_category(self, percentage):
        """Get love category based on percentage"""
        for key, (min_val, max_val, message) in sorted(self.LOVE_CATEGORIES.items(), key=lambda x: x[1][0], reverse=True):
            if percentage >= min_val:
                return {'name': key, 'message': message}
        return {'name': 'poor', 'message': _('Needs Work')}
    
    def _step(self, text, step_type='text'):
        """Return a step dict with text and type for language-agnostic frontend rendering."""
        return {'text': text, 'type': step_type}

    # Step-by-step solution preparation methods
    def _prepare_love_percentage_steps(self, name1, name2, combined, l_count, o_count, v_count, e_count, love_score, letter_percentage, common_letters, common_percentage, final_percentage, love_percentage):
        """Prepare step-by-step solution for love percentage calculation"""
        steps = []
        steps.append(self._step(_('Step 1: Identify the given names'), 'step'))
        steps.append(self._step(_('Name 1: {name}').format(name=name1), 'text'))
        steps.append(self._step(_('Name 2: {name}').format(name=name2), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 2: Combine and normalize names'), 'step'))
        steps.append(self._step(_('Combined: {combined}').format(combined=combined), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 3: Count L, O, V, E letters'), 'step'))
        steps.append(self._step(_('L count: {count}').format(count=l_count), 'text'))
        steps.append(self._step(_('O count: {count}').format(count=o_count), 'text'))
        steps.append(self._step(_('V count: {count}').format(count=v_count), 'text'))
        steps.append(self._step(_('E count: {count}').format(count=e_count), 'text'))
        steps.append(self._step(_('Total LOVE letters: {total}').format(total=love_score), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 4: Calculate letter percentage'), 'step'))
        steps.append(self._step(_('Letter Percentage = (LOVE letters / Total letters) × 100'), 'formula'))
        steps.append(self._step(_('Letter Percentage = ({love} / {total}) × 100 = {percent}%').format(
            love=love_score, total=len(combined), percent=round(letter_percentage, 1)
        ), 'formula'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 5: Calculate common letters percentage'), 'step'))
        steps.append(self._step(_('Common Letters: {common}').format(common=common_letters), 'text'))
        steps.append(self._step(_('Common Percentage: {percent}%').format(percent=round(common_percentage, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 6: Combine percentages'), 'step'))
        steps.append(self._step(_('Final Percentage = (Letter % × 0.4) + (Common % × 0.6)'), 'formula'))
        steps.append(self._step(_('Final Percentage = ({letter} × 0.4) + ({common} × 0.6) = {final}%').format(
            letter=round(letter_percentage, 1), common=round(common_percentage, 1), final=love_percentage
        ), 'formula'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 7: Final Result'), 'step'))
        steps.append(self._step(_('Love Percentage: {percent}%').format(percent=love_percentage), 'result'))
        return steps

    def _prepare_compatibility_steps(self, name1, name2, common_letters, common_score, length_score, vowel_score, compatibility):
        """Prepare step-by-step solution for compatibility calculation"""
        steps = []
        steps.append(self._step(_('Step 1: Identify the given names'), 'step'))
        steps.append(self._step(_('Name 1: {name}').format(name=name1), 'text'))
        steps.append(self._step(_('Name 2: {name}').format(name=name2), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 2: Calculate common letters score'), 'step'))
        steps.append(self._step(_('Common Letters: {common}').format(common=common_letters), 'text'))
        steps.append(self._step(_('Common Score: {score}%').format(score=round(common_score, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 3: Calculate name length similarity'), 'step'))
        steps.append(self._step(_('Length Score: {score}%').format(score=round(length_score, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 4: Calculate vowel/consonant ratio similarity'), 'step'))
        steps.append(self._step(_('Vowel Score: {score}%').format(score=round(vowel_score, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 5: Calculate overall compatibility'), 'step'))
        steps.append(self._step(_('Compatibility = (Common Score + Length Score + Vowel Score) / 3'), 'formula'))
        steps.append(self._step(_('Compatibility = ({common} + {length} + {vowel}) / 3 = {final}%').format(
            common=round(common_score, 1), length=round(length_score, 1),
            vowel=round(vowel_score, 1), final=compatibility
        ), 'result'))
        return steps

    def _prepare_name_analysis_steps(self, name1, name2, analysis):
        """Prepare step-by-step solution for name analysis"""
        steps = []
        steps.append(self._step(_('Step 1: Identify the given names'), 'step'))
        steps.append(self._step(_('Name 1: {name}').format(name=name1), 'text'))
        steps.append(self._step(_('Name 2: {name}').format(name=name2), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 2: Analyze name lengths'), 'step'))
        steps.append(self._step(_('Name 1 Length: {len} characters').format(len=analysis['name1_length']), 'text'))
        steps.append(self._step(_('Name 2 Length: {len} characters').format(len=analysis['name2_length']), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 3: Count vowels and consonants'), 'step'))
        steps.append(self._step(_('Name 1: {vowels} vowels, {consonants} consonants').format(
            vowels=analysis['vowel_count_name1'], consonants=analysis['consonant_count_name1']
        ), 'text'))
        steps.append(self._step(_('Name 2: {vowels} vowels, {consonants} consonants').format(
            vowels=analysis['vowel_count_name2'], consonants=analysis['consonant_count_name2']
        ), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 4: Find common letters'), 'step'))
        if analysis['common_letters']:
            steps.append(self._step(_('Common Letters: {letters}').format(letters=', '.join(analysis['common_letters'])), 'text'))
        else:
            steps.append(self._step(_('Common Letters: None'), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 5: Find unique letters'), 'step'))
        if analysis['unique_letters_name1']:
            steps.append(self._step(_('Unique to Name 1: {letters}').format(letters=', '.join(analysis['unique_letters_name1'])), 'text'))
        if analysis['unique_letters_name2']:
            steps.append(self._step(_('Unique to Name 2: {letters}').format(letters=', '.join(analysis['unique_letters_name2'])), 'text'))
        return steps
    
    # Chart data preparation methods
    def _prepare_love_percentage_chart_data(self, love_percentage, category):
        """Prepare chart data for love percentage calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('Love Percentage'), _('Remaining')],
                    'datasets': [{
                        'data': [love_percentage, 100 - love_percentage],
                        'backgroundColor': [
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(156, 163, 175, 0.8)'
                        ],
                        'borderColor': [
                            '#ec4899',
                            '#9ca3af'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Love Percentage: {percent}%').format(percent=love_percentage)
                        }
                    }
                }
            }
            return {'love_percentage_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_compatibility_chart_data(self, compatibility, common_score, length_score, vowel_score):
        """Prepare chart data for compatibility calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Common Letters'), _('Length Similarity'), _('Vowel Ratio'), _('Overall Compatibility')],
                    'datasets': [{
                        'label': _('Score (%)'),
                        'data': [common_score, length_score, vowel_score, compatibility],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(236, 72, 153, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#ec4899'
                        ],
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
                            'text': _('Compatibility Analysis')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': _('Score (%)')
                            }
                        }
                    }
                }
            }
            return {'compatibility_chart': chart_config}
        except Exception as e:
            return None
