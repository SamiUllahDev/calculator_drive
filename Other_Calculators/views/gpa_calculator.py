from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np
from sympy import symbols, simplify, N, Float


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GpaCalculator(View):
    template_name = 'other_calculators/gpa_calculator.html'

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
        return render(request, self.template_name, {'calculator_name': _('GPA Calculator')})

    def post(self, request):
        try:
            data = json.loads(request.body)
            courses = data.get('courses', [])
            scale = data.get('scale', '4.0')
            current_gpa = data.get('current_gpa')
            current_credits = data.get('current_credits')

            if scale not in self.GRADE_POINTS:
                return JsonResponse({'success': False, 'error': str(_('Invalid GPA scale. Must be 4.0, 4.3, or 5.0.'))}, status=400)
            if not courses or not isinstance(courses, list):
                return JsonResponse({'success': False, 'error': str(_('Please add at least one course.'))}, status=400)
            if len(courses) > 50:
                return JsonResponse({'success': False, 'error': str(_('Maximum 50 courses allowed.'))}, status=400)

            gp_map = self.GRADE_POINTS[scale]
            processed_courses = []
            total_points = 0
            total_credits = 0

            for i, course in enumerate(courses):
                if not isinstance(course, dict):
                    return JsonResponse({'success': False, 'error': str(_('Invalid course data format.'))}, status=400)
                grade = course.get('grade', '').upper().strip()
                name = course.get('name', '').strip() or str(_('Course')) + f' {i+1}'
                try:
                    credits = float(course.get('credits', 0))
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': str(_('Invalid credits for course')) + f': {name}'}, status=400)
                if grade not in gp_map:
                    return JsonResponse({'success': False, 'error': str(_('Invalid grade')) + f' "{grade}" ' + str(_('for course')) + f': {name}'}, status=400)
                if credits <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Credits must be greater than zero for course')) + f': {name}'}, status=400)
                if credits > 20:
                    return JsonResponse({'success': False, 'error': str(_('Credits cannot exceed 20 for course')) + f': {name}'}, status=400)

                points = gp_map[grade]
                quality_points = float(np.multiply(points, credits))
                processed_courses.append({
                    'name': name, 'grade': grade, 'credits': credits,
                    'points': points, 'quality_points': round(quality_points, 2)
                })
                total_points += quality_points
                total_credits += credits

            if total_credits == 0:
                return JsonResponse({'success': False, 'error': str(_('Total credits must be greater than zero.'))}, status=400)
            if total_credits > 1000:
                return JsonResponse({'success': False, 'error': str(_('Total credits is too large.'))}, status=400)

            semester_gpa = float(np.divide(total_points, total_credits))
            if math.isinf(semester_gpa) or math.isnan(semester_gpa):
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation result.'))}, status=400)

            cumulative_gpa = None
            cumulative_credits = None
            if current_gpa is not None and current_credits is not None:
                try:
                    current_gpa = float(current_gpa)
                    current_credits = float(current_credits)
                    if current_gpa < 0 or current_gpa > float(scale):
                        return JsonResponse({'success': False, 'error': str(_('Current GPA must be between 0 and')) + f' {scale}.'}, status=400)
                    if current_credits < 0:
                        return JsonResponse({'success': False, 'error': str(_('Current credits must be non-negative.'))}, status=400)
                    if current_credits > 0:
                        previous_points = float(np.multiply(current_gpa, current_credits))
                        cumulative_points = float(np.add(previous_points, total_points))
                        cumulative_credits = float(np.add(current_credits, total_credits))
                        cumulative_gpa = float(np.divide(cumulative_points, cumulative_credits))
                        if math.isinf(cumulative_gpa) or math.isnan(cumulative_gpa):
                            cumulative_gpa = None
                except (ValueError, TypeError):
                    pass

            letter_grade = self._gpa_to_letter(semester_gpa, scale)
            cumulative_letter = self._gpa_to_letter(cumulative_gpa, scale) if cumulative_gpa is not None else None
            standing = str(self._get_standing(semester_gpa, scale))
            cumulative_standing = str(self._get_standing(cumulative_gpa, scale)) if cumulative_gpa is not None else None
            steps = self._prepare_gpa_steps(processed_courses, total_points, total_credits, semester_gpa, scale, current_gpa, current_credits, cumulative_gpa, cumulative_credits)
            chart_data = self._prepare_gpa_chart_data(processed_courses, semester_gpa, cumulative_gpa, scale)

            result = {
                'success': True, 'semester_gpa': round(semester_gpa, 3), 'letter_grade': letter_grade,
                'standing': standing, 'total_credits': round(total_credits, 1),
                'total_quality_points': round(total_points, 2), 'courses': processed_courses,
                'scale': scale, 'step_by_step': steps, 'chart_data': chart_data,
            }
            if cumulative_gpa is not None:
                result['cumulative_gpa'] = round(cumulative_gpa, 3)
                result['cumulative_letter'] = cumulative_letter
                result['cumulative_standing'] = cumulative_standing
                result['cumulative_credits'] = round(cumulative_credits, 1)
            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid JSON data.'))}, status=400)
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': str(_('Invalid input')) + ': ' + str(e)}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _gpa_to_letter(self, gpa, scale):
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
        max_gpa = float(scale)
        ratio = float(np.divide(gpa, max_gpa))
        if ratio >= 0.9:
            return _("Dean's List")
        elif ratio >= 0.75:
            return _('Good Standing')
        elif ratio >= 0.5:
            return _('Satisfactory')
        elif ratio >= 0.25:
            return _('Academic Warning')
        else:
            return _('Probation')

    def _prepare_gpa_steps(self, processed_courses, total_points, total_credits, semester_gpa, scale, current_gpa, current_credits, cumulative_gpa, cumulative_credits):
        steps = []
        steps.append(str(_('Step 1: Identify all courses and grades')))
        for i, course in enumerate(processed_courses, 1):
            steps.append(f"{str(_('Course'))} {i}: {course['name']} - {str(_('Grade'))}: {course['grade']}, {str(_('Credits'))}: {course['credits']}")
        steps.append('')
        steps.append(str(_('Step 2: Calculate quality points for each course')))
        steps.append(str(_('Formula')) + ': ' + str(_('Quality Points')) + ' = ' + str(_('Grade Points')) + ' × ' + str(_('Credits')))
        for course in processed_courses:
            steps.append(f"{course['name']}: {course['points']} × {course['credits']} = {course['quality_points']} " + str(_('quality points')))
        steps.append('')
        steps.append(str(_('Step 3: Calculate total quality points')))
        qp_list = [str(c['quality_points']) for c in processed_courses]
        steps.append(str(_('Total Quality Points')) + ' = ' + ' + '.join(qp_list))
        steps.append(str(_('Total Quality Points')) + f' = {round(total_points, 2)}')
        steps.append('')
        steps.append(str(_('Step 4: Calculate total credits')))
        cr_list = [str(c['credits']) for c in processed_courses]
        steps.append(str(_('Total Credits')) + ' = ' + ' + '.join(cr_list))
        steps.append(str(_('Total Credits')) + f' = {total_credits}')
        steps.append('')
        steps.append(str(_('Step 5: Calculate Semester GPA')))
        steps.append(str(_('Formula')) + ': GPA = ' + str(_('Total Quality Points')) + ' / ' + str(_('Total Credits')))
        steps.append(f'GPA = {round(total_points, 2)} / {total_credits}')
        steps.append(str(_('Semester GPA')) + f' = {round(semester_gpa, 3)} (' + str(_('on')) + f' {scale} ' + str(_('scale')) + ')')
        steps.append('')
        if cumulative_gpa is not None and current_gpa is not None and current_credits is not None:
            steps.append(str(_('Step 6: Calculate Cumulative GPA')))
            previous_points = current_gpa * current_credits
            steps.append(str(_('Previous Quality Points')) + f' = {current_gpa} × {current_credits} = {round(previous_points, 2)}')
            cumulative_points = previous_points + total_points
            steps.append(str(_('Cumulative Quality Points')) + f' = {round(previous_points, 2)} + {round(total_points, 2)} = {round(cumulative_points, 2)}')
            steps.append(str(_('Cumulative Credits')) + f' = {current_credits} + {total_credits} = {cumulative_credits}')
            steps.append(str(_('Cumulative GPA')) + f' = {round(cumulative_points, 2)} / {cumulative_credits} = {round(cumulative_gpa, 3)}')
            steps.append('')
        steps.append(str(_('Final Answer')) + ': ' + str(_('Semester GPA')) + f' = {round(semester_gpa, 3)}')
        if cumulative_gpa is not None:
            steps.append(str(_('Cumulative GPA')) + f' = {round(cumulative_gpa, 3)}')
        return steps

    def _prepare_gpa_chart_data(self, processed_courses, semester_gpa, cumulative_gpa, scale):
        try:
            grade_counts = {}
            for course in processed_courses:
                g = course['grade']
                grade_counts[g] = grade_counts.get(g, 0) + 1
            grade_colors = {
                'A+': '#059669', 'A': '#10b981', 'A-': '#34d399',
                'B+': '#3b82f6', 'B': '#60a5fa', 'B-': '#93c5fd',
                'C+': '#f59e0b', 'C': '#fbbf24', 'C-': '#fcd34d',
                'D+': '#f97316', 'D': '#fb923c', 'D-': '#fdba74', 'F': '#ef4444'
            }
            bg_colors = [grade_colors.get(g, '#6b7280') + 'cc' for g in grade_counts.keys()]
            border_colors = [grade_colors.get(g, '#6b7280') for g in grade_counts.keys()]
            grade_chart = {
                'type': 'bar',
                'data': {
                    'labels': list(grade_counts.keys()),
                    'datasets': [{'label': str(_('Number of Courses')), 'data': list(grade_counts.values()),
                                  'backgroundColor': bg_colors, 'borderColor': border_colors, 'borderWidth': 2, 'borderRadius': 8}]
                },
            }
            gpa_labels = [str(_('Semester GPA'))]
            gpa_data = [round(semester_gpa, 3)]
            gpa_bg = ['rgba(59, 130, 246, 0.8)']
            gpa_border = ['#3b82f6']
            if cumulative_gpa is not None:
                gpa_labels.append(str(_('Cumulative GPA')))
                gpa_data.append(round(cumulative_gpa, 3))
                gpa_bg.append('rgba(16, 185, 129, 0.8)')
                gpa_border.append('#10b981')
            gpa_chart = {
                'type': 'bar',
                'data': {
                    'labels': gpa_labels,
                    'datasets': [{'label': 'GPA', 'data': gpa_data,
                                  'backgroundColor': gpa_bg, 'borderColor': gpa_border, 'borderWidth': 2, 'borderRadius': 8}]
                },
            }
            return {'grade_distribution': grade_chart, 'gpa_comparison': gpa_chart}
        except Exception:
            return None
