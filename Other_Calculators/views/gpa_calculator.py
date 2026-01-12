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
class GpaCalculator(View):
    """
    Professional GPA Calculator with Comprehensive Features
    
    This calculator provides GPA calculations with:
    - Calculate semester GPA from courses
    - Calculate cumulative GPA
    - Support for 4.0, 4.3, and 5.0 scales
    - Academic standing determination
    - Letter grade conversion
    - Step-by-step solutions
    
    Features:
    - Supports multiple GPA scales
    - Handles course credits and grades
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/gpa_calculator.html'
    
    # Grade point mappings for different scales
    GRADE_POINTS = {
        '4.0': {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        },
        '4.3': {
            'A+': 4.3, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
            'F': 0.0
        },
        '5.0': {
            'A+': 5.0, 'A': 5.0, 'A-': 4.7,
            'B+': 4.3, 'B': 4.0, 'B-': 3.7,
            'C+': 3.3, 'C': 3.0, 'C-': 2.7,
            'D+': 2.3, 'D': 2.0, 'D-': 1.7,
            'F': 0.0
        }
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('GPA Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            courses = data.get('courses', [])
            scale = data.get('scale', '4.0')
            current_gpa = data.get('current_gpa')
            current_credits = data.get('current_credits')
            
            # Validate scale
            if scale not in self.GRADE_POINTS:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid GPA scale. Must be 4.0, 4.3, or 5.0.')
                }, status=400)
            
            # Validate courses
            if not courses or not isinstance(courses, list):
                return JsonResponse({
                    'success': False,
                    'error': _('Please add at least one course.')
                }, status=400)
            
            if len(courses) > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Maximum 50 courses allowed.')
                }, status=400)
            
            gp_map = self.GRADE_POINTS[scale]
            
            # Process courses
            processed_courses = []
            total_points = 0
            total_credits = 0
            
            for i, course in enumerate(courses):
                if not isinstance(course, dict):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid course data format.')
                    }, status=400)
                
                grade = course.get('grade', '').upper().strip()
                name = course.get('name', '').strip() or _('Course {num}').format(num=i+1)
                
                try:
                    credits = float(course.get('credits', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid credits for course: {name}').format(name=name)
                    }, status=400)
                
                # Validate grade
                if grade not in gp_map:
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid grade "{grade}" for course: {name}').format(grade=grade, name=name)
                    }, status=400)
                
                # Validate credits
                if credits <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Credits must be greater than zero for course: {name}').format(name=name)
                    }, status=400)
                
                if credits > 20:
                    return JsonResponse({
                        'success': False,
                        'error': _('Credits cannot exceed 20 for course: {name}').format(name=name)
                    }, status=400)
                
                points = gp_map[grade]
                quality_points = float(np.multiply(points, credits))
                
                processed_courses.append({
                    'name': name,
                    'grade': grade,
                    'credits': credits,
                    'points': points,
                    'quality_points': round(quality_points, 2)
                })
                
                total_points += quality_points
                total_credits += credits
            
            if total_credits == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Total credits must be greater than zero.')
                }, status=400)
            
            # Validate total credits
            if total_credits > 1000:
                return JsonResponse({
                    'success': False,
                    'error': _('Total credits is too large.')
                }, status=400)
            
            # Calculate semester GPA
            semester_gpa = float(np.divide(total_points, total_credits))
            
            # Validate result
            if math.isinf(semester_gpa) or math.isnan(semester_gpa) or np.isinf(semester_gpa) or np.isnan(semester_gpa):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Calculate cumulative GPA if current GPA/credits provided
            cumulative_gpa = None
            cumulative_credits = None
            if current_gpa is not None and current_credits is not None:
                try:
                    current_gpa = float(current_gpa)
                    current_credits = float(current_credits)
                    
                    # Validate current GPA
                    if current_gpa < 0 or current_gpa > float(scale):
                        return JsonResponse({
                            'success': False,
                            'error': _('Current GPA must be between 0 and {scale}.').format(scale=scale)
                        }, status=400)
                    
                    if current_credits < 0:
                        return JsonResponse({
                            'success': False,
                            'error': _('Current credits must be non-negative.')
                        }, status=400)
                    
                    if current_credits > 1000:
                        return JsonResponse({
                            'success': False,
                            'error': _('Current credits is too large.')
                        }, status=400)
                    
                    if current_credits > 0:
                        previous_points = float(np.multiply(current_gpa, current_credits))
                        cumulative_points = float(np.add(previous_points, total_points))
                        cumulative_credits = float(np.add(current_credits, total_credits))
                        cumulative_gpa = float(np.divide(cumulative_points, cumulative_credits))
                        
                        # Validate cumulative result
                        if math.isinf(cumulative_gpa) or math.isnan(cumulative_gpa) or np.isinf(cumulative_gpa) or np.isnan(cumulative_gpa):
                            cumulative_gpa = None
                except (ValueError, TypeError):
                    pass
            
            # Letter grade equivalent
            letter_grade = self._gpa_to_letter(semester_gpa, scale)
            cumulative_letter = None
            if cumulative_gpa is not None:
                cumulative_letter = self._gpa_to_letter(cumulative_gpa, scale)
            
            # Academic standing
            standing = self._get_standing(semester_gpa, scale)
            cumulative_standing = None
            if cumulative_gpa is not None:
                cumulative_standing = self._get_standing(cumulative_gpa, scale)
            
            # Prepare steps
            steps = self._prepare_gpa_steps(processed_courses, total_points, total_credits, semester_gpa, scale, current_gpa, current_credits, cumulative_gpa, cumulative_credits)
            
            # Prepare chart data
            chart_data = self._prepare_gpa_chart_data(processed_courses, semester_gpa, cumulative_gpa, scale)
            
            result = {
                'success': True,
                'semester_gpa': round(semester_gpa, 3),
                'letter_grade': letter_grade,
                'standing': standing,
                'total_credits': round(total_credits, 1),
                'total_quality_points': round(total_points, 2),
                'courses': processed_courses,
                'scale': scale,
                'step_by_step': steps,
                'chart_data': chart_data,
            }
            
            if cumulative_gpa is not None:
                result['cumulative_gpa'] = round(cumulative_gpa, 3)
                result['cumulative_letter'] = cumulative_letter
                result['cumulative_standing'] = cumulative_standing
                result['cumulative_credits'] = round(cumulative_credits, 1)
            
            return JsonResponse(result)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _gpa_to_letter(self, gpa, scale):
        """Convert GPA to letter grade"""
        if scale == '5.0':
            thresholds = [(4.7, 'A'), (4.3, 'A-'), (4.0, 'B+'), (3.7, 'B'), (3.3, 'B-'), 
                          (3.0, 'C+'), (2.7, 'C'), (2.3, 'C-'), (2.0, 'D+'), (1.7, 'D'), (0, 'F')]
        else:
            thresholds = [(3.7, 'A'), (3.3, 'A-'), (3.0, 'B+'), (2.7, 'B'), (2.3, 'B-'), 
                          (2.0, 'C+'), (1.7, 'C'), (1.3, 'C-'), (1.0, 'D+'), (0.7, 'D'), (0, 'F')]
        
        for threshold, letter in thresholds:
            if gpa >= threshold:
                return letter
        return 'F'
    
    def _get_standing(self, gpa, scale):
        """Get academic standing based on GPA"""
        max_gpa = float(scale)
        ratio = float(np.divide(gpa, max_gpa))
        
        if ratio >= 0.9:
            return _('Dean\'s List')
        elif ratio >= 0.75:
            return _('Good Standing')
        elif ratio >= 0.5:
            return _('Satisfactory')
        elif ratio >= 0.25:
            return _('Academic Warning')
        else:
            return _('Probation')
    
    def _prepare_gpa_steps(self, processed_courses, total_points, total_credits, semester_gpa, scale, current_gpa, current_credits, cumulative_gpa, cumulative_credits):
        """Prepare step-by-step solution for GPA calculation"""
        steps = []
        steps.append(_('Step 1: Identify all courses and grades'))
        for i, course in enumerate(processed_courses, 1):
            steps.append(_('Course {num}: {name} - Grade: {grade}, Credits: {credits}').format(
                num=i, name=course['name'], grade=course['grade'], credits=course['credits']
            ))
        steps.append('')
        steps.append(_('Step 2: Calculate quality points for each course'))
        steps.append(_('Formula: Quality Points = Grade Points × Credits'))
        for course in processed_courses:
            steps.append(_('{name}: {points} × {credits} = {qp} quality points').format(
                name=course['name'], points=course['points'], credits=course['credits'], qp=course['quality_points']
            ))
        steps.append('')
        steps.append(_('Step 3: Calculate total quality points'))
        quality_points_list = [str(c['quality_points']) for c in processed_courses]
        steps.append(_('Total Quality Points = {points}').format(points=' + '.join(quality_points_list)))
        steps.append(_('Total Quality Points = {total}').format(total=total_points))
        steps.append('')
        steps.append(_('Step 4: Calculate total credits'))
        credits_list = [str(c['credits']) for c in processed_courses]
        steps.append(_('Total Credits = {credits}').format(credits=' + '.join(credits_list)))
        steps.append(_('Total Credits = {total}').format(total=total_credits))
        steps.append('')
        steps.append(_('Step 5: Calculate Semester GPA'))
        steps.append(_('Formula: GPA = Total Quality Points / Total Credits'))
        steps.append(_('GPA = {points} / {credits}').format(points=total_points, credits=total_credits))
        steps.append(_('Semester GPA = {gpa} (on {scale} scale)').format(gpa=round(semester_gpa, 3), scale=scale))
        steps.append('')
        
        if cumulative_gpa is not None and current_gpa is not None and current_credits is not None:
            steps.append(_('Step 6: Calculate Cumulative GPA'))
            previous_points = current_gpa * current_credits
            steps.append(_('Previous Quality Points = {gpa} × {credits} = {points}').format(
                gpa=current_gpa, credits=current_credits, points=previous_points
            ))
            cumulative_points = previous_points + total_points
            steps.append(_('Cumulative Quality Points = {prev} + {new} = {total}').format(
                prev=previous_points, new=total_points, total=cumulative_points
            ))
            steps.append(_('Cumulative Credits = {prev} + {new} = {total}').format(
                prev=current_credits, new=total_credits, total=cumulative_credits
            ))
            steps.append(_('Cumulative GPA = {points} / {credits} = {gpa}').format(
                points=cumulative_points, credits=cumulative_credits, gpa=round(cumulative_gpa, 3)
            ))
        
        return steps
    
    def _prepare_gpa_chart_data(self, processed_courses, semester_gpa, cumulative_gpa, scale):
        """Prepare chart data for GPA visualization"""
        try:
            # Grade distribution chart
            grade_counts = {}
            for course in processed_courses:
                grade = course['grade']
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
            
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': list(grade_counts.keys()),
                    'datasets': [{
                        'label': _('Number of Courses'),
                        'data': list(grade_counts.values()),
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
                            'display': True,
                            'position': 'top'
                        },
                        'title': {
                            'display': True,
                            'text': _('Grade Distribution')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': _('Number of Courses')
                            }
                        }
                    }
                }
            }
            
            # GPA comparison chart
            gpa_comparison = {
                'type': 'bar',
                'data': {
                    'labels': [_('Semester GPA')] + ([_('Cumulative GPA')] if cumulative_gpa is not None else []),
                    'datasets': [{
                        'label': _('GPA'),
                        'data': [semester_gpa] + ([cumulative_gpa] if cumulative_gpa is not None else []),
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ][:2 if cumulative_gpa is not None else 1],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ][:2 if cumulative_gpa is not None else 1],
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
                            'text': _('GPA Comparison (Scale: {scale})').format(scale=scale)
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': float(scale),
                            'title': {
                                'display': True,
                                'text': _('GPA')
                            }
                        }
                    }
                }
            }
            
            return {
                'grade_distribution': chart_config,
                'gpa_comparison': gpa_comparison
            }
        except Exception as e:
            return None
