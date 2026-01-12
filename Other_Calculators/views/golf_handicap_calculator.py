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
class GolfHandicapCalculator(View):
    """
    Professional Golf Handicap Calculator with Comprehensive Features
    
    This calculator provides golf handicap calculations with:
    - Calculate Handicap Index from score differentials (WHS)
    - Calculate Course Handicap from Handicap Index
    - Calculate Score Differential from round scores
    - Calculate Net Score
    - Calculate Playing Handicap
    
    Features:
    - Supports World Handicap System (WHS)
    - Handles multiple calculation modes
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/golf_handicap_calculator.html'
    
    # Standard slope rating for calculation
    STANDARD_SLOPE = 113
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Golf Handicap Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'handicap_index')
            
            if calc_type == 'handicap_index':
                return self._calculate_handicap_index(data)
            elif calc_type == 'course_handicap':
                return self._calculate_course_handicap(data)
            elif calc_type == 'score_differential':
                return self._calculate_score_differential(data)
            elif calc_type == 'net_score':
                return self._calculate_net_score(data)
            elif calc_type == 'playing_handicap':
                return self._calculate_playing_handicap(data)
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
    
    def _calculate_handicap_index(self, data):
        """Calculate Handicap Index from score differentials (WHS)"""
        try:
            # Check for required fields
            if 'differentials' not in data or not isinstance(data.get('differentials'), list):
                return JsonResponse({
                    'success': False,
                    'error': _('Score differentials are required as a list.')
                }, status=400)
            
            differentials = data.get('differentials', [])
            
            if len(differentials) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('At least one score differential is required.')
                }, status=400)
            
            if len(differentials) > 20:
                return JsonResponse({
                    'success': False,
                    'error': _('Maximum 20 score differentials allowed.')
                }, status=400)
            
            try:
                differentials_float = [float(d) for d in differentials]
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validate ranges
            for i, diff in enumerate(differentials_float):
                if diff < 0 or diff > 200:
                    return JsonResponse({
                        'success': False,
                        'error': _('Score differential {num} is out of range (0-200).').format(num=i+1)
                    }, status=400)
            
            # Sort differentials in ascending order (best scores first)
            differentials_sorted = sorted(differentials_float)
            
            # WHS: Use best 8 of last 20 differentials
            # If fewer than 20, use best differentials based on count
            num_differentials = len(differentials_sorted)
            
            if num_differentials >= 20:
                # Use best 8 of 20
                best_differentials = differentials_sorted[:8]
            elif num_differentials >= 10:
                # Use best 6 of available
                best_differentials = differentials_sorted[:6]
            elif num_differentials >= 5:
                # Use best 3 of available
                best_differentials = differentials_sorted[:3]
            elif num_differentials >= 3:
                # Use best 2 of available
                best_differentials = differentials_sorted[:2]
            else:
                # Use best 1
                best_differentials = differentials_sorted[:1]
            
            # Calculate average of best differentials
            avg_differential = float(np.mean(best_differentials))
            
            # Apply adjustment factor (0.96 for WHS)
            handicap_index = float(np.multiply(avg_differential, 0.96))
            
            # Round to one decimal place
            handicap_index = round(handicap_index, 1)
            
            # Validate result
            if math.isinf(handicap_index) or math.isnan(handicap_index) or np.isinf(handicap_index) or np.isnan(handicap_index):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Prepare steps
            steps = self._prepare_handicap_index_steps(differentials_float, differentials_sorted, best_differentials, avg_differential, handicap_index, num_differentials)
            
            # Prepare chart data
            chart_data = self._prepare_handicap_index_chart_data(differentials_sorted, best_differentials, handicap_index)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'handicap_index',
                'differentials': differentials_float,
                'num_differentials': num_differentials,
                'best_differentials': best_differentials,
                'average_differential': avg_differential,
                'handicap_index': handicap_index,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating handicap index: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_course_handicap(self, data):
        """Calculate Course Handicap from Handicap Index"""
        try:
            if 'handicap_index' not in data or data.get('handicap_index') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Handicap Index is required.')
                }, status=400)
            
            if 'slope_rating' not in data or data.get('slope_rating') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Slope Rating is required.')
                }, status=400)
            
            try:
                handicap_index = float(data.get('handicap_index', 0))
                slope_rating = float(data.get('slope_rating', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            course_rating = float(data.get('course_rating', 72.0))  # Default par
            par = float(data.get('par', 72.0))
            
            # Validate ranges
            if handicap_index < 0 or handicap_index > 54:
                return JsonResponse({
                    'success': False,
                    'error': _('Handicap Index must be between 0 and 54.')
                }, status=400)
            
            if slope_rating < 55 or slope_rating > 155:
                return JsonResponse({
                    'success': False,
                    'error': _('Slope Rating must be between 55 and 155.')
                }, status=400)
            
            if course_rating < 60 or course_rating > 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Rating must be between 60 and 80.')
                }, status=400)
            
            if par < 60 or par > 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Par must be between 60 and 80.')
                }, status=400)
            
            # Calculate Course Handicap: CH = HI × (SR / 113) + (CR - Par)
            slope_factor = float(np.divide(slope_rating, self.STANDARD_SLOPE))
            course_handicap = float(np.add(
                np.multiply(handicap_index, slope_factor),
                np.subtract(course_rating, par)
            ))
            
            # Round to nearest integer
            course_handicap = round(course_handicap)
            
            # Validate result
            if math.isinf(course_handicap) or math.isnan(course_handicap) or np.isinf(course_handicap) or np.isnan(course_handicap):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_course_handicap_steps(handicap_index, slope_rating, course_rating, par, slope_factor, course_handicap)
            
            chart_data = self._prepare_course_handicap_chart_data(handicap_index, slope_rating, course_handicap)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'course_handicap',
                'handicap_index': handicap_index,
                'slope_rating': slope_rating,
                'course_rating': course_rating,
                'par': par,
                'course_handicap': course_handicap,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating course handicap: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_score_differential(self, data):
        """Calculate Score Differential from round score"""
        try:
            if 'adjusted_gross_score' not in data or data.get('adjusted_gross_score') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Adjusted Gross Score is required.')
                }, status=400)
            
            if 'course_rating' not in data or data.get('course_rating') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Rating is required.')
                }, status=400)
            
            if 'slope_rating' not in data or data.get('slope_rating') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Slope Rating is required.')
                }, status=400)
            
            try:
                adjusted_gross_score = float(data.get('adjusted_gross_score', 0))
                course_rating = float(data.get('course_rating', 0))
                slope_rating = float(data.get('slope_rating', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validate ranges
            if adjusted_gross_score < 50 or adjusted_gross_score > 200:
                return JsonResponse({
                    'success': False,
                    'error': _('Adjusted Gross Score must be between 50 and 200.')
                }, status=400)
            
            if course_rating < 60 or course_rating > 80:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Rating must be between 60 and 80.')
                }, status=400)
            
            if slope_rating < 55 or slope_rating > 155:
                return JsonResponse({
                    'success': False,
                    'error': _('Slope Rating must be between 55 and 155.')
                }, status=400)
            
            # Calculate Score Differential: SD = (AGS - CR) × (113 / SR)
            score_diff = float(np.multiply(
                np.subtract(adjusted_gross_score, course_rating),
                np.divide(self.STANDARD_SLOPE, slope_rating)
            ))
            
            # Round to one decimal place
            score_diff = round(score_diff, 1)
            
            # Validate result
            if math.isinf(score_diff) or math.isnan(score_diff) or np.isinf(score_diff) or np.isnan(score_diff):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_score_differential_steps(adjusted_gross_score, course_rating, slope_rating, score_diff)
            
            chart_data = self._prepare_score_differential_chart_data(adjusted_gross_score, course_rating, slope_rating, score_diff)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'score_differential',
                'adjusted_gross_score': adjusted_gross_score,
                'course_rating': course_rating,
                'slope_rating': slope_rating,
                'score_differential': score_diff,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating score differential: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_net_score(self, data):
        """Calculate Net Score"""
        try:
            if 'gross_score' not in data or data.get('gross_score') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Gross Score is required.')
                }, status=400)
            
            if 'course_handicap' not in data or data.get('course_handicap') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Handicap is required.')
                }, status=400)
            
            try:
                gross_score = float(data.get('gross_score', 0))
                course_handicap = float(data.get('course_handicap', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validate ranges
            if gross_score < 50 or gross_score > 200:
                return JsonResponse({
                    'success': False,
                    'error': _('Gross Score must be between 50 and 200.')
                }, status=400)
            
            if course_handicap < -10 or course_handicap > 54:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Handicap must be between -10 and 54.')
                }, status=400)
            
            # Calculate Net Score: Net = Gross - Course Handicap
            net_score = float(np.subtract(gross_score, course_handicap))
            
            # Round to nearest integer
            net_score = round(net_score)
            
            # Validate result
            if math.isinf(net_score) or math.isnan(net_score) or np.isinf(net_score) or np.isnan(net_score):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_net_score_steps(gross_score, course_handicap, net_score)
            
            chart_data = self._prepare_net_score_chart_data(gross_score, course_handicap, net_score)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'net_score',
                'gross_score': gross_score,
                'course_handicap': course_handicap,
                'net_score': net_score,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating net score: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_playing_handicap(self, data):
        """Calculate Playing Handicap"""
        try:
            if 'course_handicap' not in data or data.get('course_handicap') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Handicap is required.')
                }, status=400)
            
            try:
                course_handicap = float(data.get('course_handicap', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            handicap_allowance = float(data.get('handicap_allowance', 100.0))  # Default 100%
            
            # Validate ranges
            if course_handicap < -10 or course_handicap > 54:
                return JsonResponse({
                    'success': False,
                    'error': _('Course Handicap must be between -10 and 54.')
                }, status=400)
            
            if handicap_allowance < 0 or handicap_allowance > 200:
                return JsonResponse({
                    'success': False,
                    'error': _('Handicap Allowance must be between 0% and 200%.')
                }, status=400)
            
            # Calculate Playing Handicap: PH = CH × (Allowance / 100)
            playing_handicap = float(np.multiply(
                course_handicap,
                np.divide(handicap_allowance, 100.0)
            ))
            
            # Round to nearest integer
            playing_handicap = round(playing_handicap)
            
            # Validate result
            if math.isinf(playing_handicap) or math.isnan(playing_handicap) or np.isinf(playing_handicap) or np.isnan(playing_handicap):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            steps = self._prepare_playing_handicap_steps(course_handicap, handicap_allowance, playing_handicap)
            
            chart_data = self._prepare_playing_handicap_chart_data(course_handicap, handicap_allowance, playing_handicap)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'playing_handicap',
                'course_handicap': course_handicap,
                'handicap_allowance': handicap_allowance,
                'playing_handicap': playing_handicap,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating playing handicap: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_handicap_index_steps(self, differentials, differentials_sorted, best_differentials, avg_differential, handicap_index, num_differentials):
        """Prepare step-by-step solution for handicap index calculation"""
        steps = []
        steps.append(_('Step 1: Identify the score differentials'))
        steps.append(_('Number of differentials: {num}').format(num=num_differentials))
        steps.append(_('Differentials: {diffs}').format(diffs=', '.join([str(d) for d in differentials])))
        steps.append('')
        steps.append(_('Step 2: Sort differentials in ascending order (best scores first)'))
        steps.append(_('Sorted: {sorted_diffs}').format(sorted_diffs=', '.join([str(d) for d in differentials_sorted])))
        steps.append('')
        steps.append(_('Step 3: Select best differentials based on count'))
        if num_differentials >= 20:
            steps.append(_('Using best 8 of 20 differentials (WHS standard)'))
        elif num_differentials >= 10:
            steps.append(_('Using best 6 of {num} differentials').format(num=num_differentials))
        elif num_differentials >= 5:
            steps.append(_('Using best 3 of {num} differentials').format(num=num_differentials))
        elif num_differentials >= 3:
            steps.append(_('Using best 2 of {num} differentials').format(num=num_differentials))
        else:
            steps.append(_('Using best 1 of {num} differentials').format(num=num_differentials))
        steps.append(_('Best differentials: {best}').format(best=', '.join([str(d) for d in best_differentials])))
        steps.append('')
        steps.append(_('Step 4: Calculate average of best differentials'))
        steps.append(_('Average = ({diffs}) / {count}').format(
            diffs=' + '.join([str(d) for d in best_differentials]),
            count=len(best_differentials)
        ))
        steps.append(_('Average = {avg}').format(avg=avg_differential))
        steps.append('')
        steps.append(_('Step 5: Apply adjustment factor (0.96 for WHS)'))
        steps.append(_('Handicap Index = {avg} × 0.96').format(avg=avg_differential))
        steps.append(_('Handicap Index = {hi}').format(hi=handicap_index))
        return steps
    
    def _prepare_course_handicap_steps(self, handicap_index, slope_rating, course_rating, par, slope_factor, course_handicap):
        """Prepare step-by-step solution for course handicap calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Handicap Index: {hi}').format(hi=handicap_index))
        steps.append(_('Slope Rating: {sr}').format(sr=slope_rating))
        steps.append(_('Course Rating: {cr}').format(cr=course_rating))
        steps.append(_('Par: {par}').format(par=par))
        steps.append('')
        steps.append(_('Step 2: Calculate slope factor'))
        steps.append(_('Slope Factor = Slope Rating / 113'))
        steps.append(_('Slope Factor = {sr} / 113 = {factor}').format(sr=slope_rating, factor=slope_factor))
        steps.append('')
        steps.append(_('Step 3: Apply the course handicap formula'))
        steps.append(_('Formula: Course Handicap = (Handicap Index × Slope Factor) + (Course Rating - Par)'))
        steps.append(_('Course Handicap = ({hi} × {factor}) + ({cr} - {par})').format(
            hi=handicap_index, factor=slope_factor, cr=course_rating, par=par
        ))
        steps.append(_('Course Handicap = {ch}').format(ch=course_handicap))
        return steps
    
    def _prepare_score_differential_steps(self, adjusted_gross_score, course_rating, slope_rating, score_diff):
        """Prepare step-by-step solution for score differential calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Adjusted Gross Score: {ags}').format(ags=adjusted_gross_score))
        steps.append(_('Course Rating: {cr}').format(cr=course_rating))
        steps.append(_('Slope Rating: {sr}').format(sr=slope_rating))
        steps.append('')
        steps.append(_('Step 2: Apply the score differential formula'))
        steps.append(_('Formula: Score Differential = (Adjusted Gross Score - Course Rating) × (113 / Slope Rating)'))
        steps.append(_('Score Differential = ({ags} - {cr}) × (113 / {sr})').format(
            ags=adjusted_gross_score, cr=course_rating, sr=slope_rating
        ))
        diff_part = adjusted_gross_score - course_rating
        slope_part = 113.0 / slope_rating
        steps.append(_('Score Differential = {diff} × {slope}').format(diff=diff_part, slope=slope_part))
        steps.append(_('Score Differential = {sd}').format(sd=score_diff))
        return steps
    
    def _prepare_net_score_steps(self, gross_score, course_handicap, net_score):
        """Prepare step-by-step solution for net score calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Gross Score: {gross}').format(gross=gross_score))
        steps.append(_('Course Handicap: {ch}').format(ch=course_handicap))
        steps.append('')
        steps.append(_('Step 2: Apply the net score formula'))
        steps.append(_('Formula: Net Score = Gross Score - Course Handicap'))
        steps.append(_('Net Score = {gross} - {ch}').format(gross=gross_score, ch=course_handicap))
        steps.append(_('Net Score = {net}').format(net=net_score))
        return steps
    
    def _prepare_playing_handicap_steps(self, course_handicap, handicap_allowance, playing_handicap):
        """Prepare step-by-step solution for playing handicap calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Course Handicap: {ch}').format(ch=course_handicap))
        steps.append(_('Handicap Allowance: {allowance}%').format(allowance=handicap_allowance))
        steps.append('')
        steps.append(_('Step 2: Apply the playing handicap formula'))
        steps.append(_('Formula: Playing Handicap = Course Handicap × (Allowance / 100)'))
        steps.append(_('Playing Handicap = {ch} × ({allowance} / 100)').format(
            ch=course_handicap, allowance=handicap_allowance
        ))
        steps.append(_('Playing Handicap = {ph}').format(ph=playing_handicap))
        return steps
    
    # Chart data preparation methods
    def _prepare_handicap_index_chart_data(self, differentials_sorted, best_differentials, handicap_index):
        """Prepare chart data for handicap index calculation"""
        try:
            chart_config = {
                'type': 'line',
                'data': {
                    'labels': [str(i+1) for i in range(len(differentials_sorted))],
                    'datasets': [{
                        'label': _('All Differentials'),
                        'data': differentials_sorted,
                        'borderColor': 'rgba(156, 163, 175, 0.8)',
                        'backgroundColor': 'rgba(156, 163, 175, 0.1)',
                        'borderWidth': 1,
                        'fill': False
                    }, {
                        'label': _('Best Differentials'),
                        'data': [differentials_sorted[i] if differentials_sorted[i] in best_differentials else None for i in range(len(differentials_sorted))],
                        'borderColor': 'rgba(59, 130, 246, 1)',
                        'backgroundColor': 'rgba(59, 130, 246, 0.2)',
                        'borderWidth': 3,
                        'fill': True,
                        'pointRadius': 5
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'top'
                        },
                        'title': {
                            'display': True,
                            'text': _('Handicap Index: {hi}').format(hi=handicap_index)
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Score Differential')
                            }
                        }
                    }
                }
            }
            return {'handicap_index_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_course_handicap_chart_data(self, handicap_index, slope_rating, course_handicap):
        """Prepare chart data for course handicap calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Handicap Index'), _('Slope Rating'), _('Course Handicap')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [handicap_index, slope_rating, course_handicap],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24'
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
                            'text': _('Course Handicap Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'course_handicap_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_score_differential_chart_data(self, adjusted_gross_score, course_rating, slope_rating, score_diff):
        """Prepare chart data for score differential calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Adjusted Gross Score'), _('Course Rating'), _('Slope Rating'), _('Score Differential')],
                    'datasets': [{
                        'label': _('Values'),
                        'data': [adjusted_gross_score, course_rating, slope_rating, score_diff],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(139, 92, 246, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#8b5cf6',
                            '#fbbf24'
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
                            'text': _('Score Differential Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Value')
                            }
                        }
                    }
                }
            }
            return {'score_differential_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_net_score_chart_data(self, gross_score, course_handicap, net_score):
        """Prepare chart data for net score calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Gross Score'), _('Course Handicap'), _('Net Score')],
                    'datasets': [{
                        'label': _('Scores'),
                        'data': [gross_score, course_handicap, net_score],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24'
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
                            'text': _('Net Score Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Score')
                            }
                        }
                    }
                }
            }
            return {'net_score_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_playing_handicap_chart_data(self, course_handicap, handicap_allowance, playing_handicap):
        """Prepare chart data for playing handicap calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('Course Handicap'), _('Playing Handicap')],
                    'datasets': [{
                        'data': [abs(course_handicap), abs(playing_handicap)],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(251, 191, 36, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#fbbf24'
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
                            'text': _('Playing Handicap (Allowance: {allowance}%)').format(allowance=handicap_allowance)
                        }
                    }
                }
            }
            return {'playing_handicap_chart': chart_config}
        except Exception as e:
            return None
