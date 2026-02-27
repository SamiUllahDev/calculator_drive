from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class GradeCalculator(View):
    template_name = 'other_calculators/grade_calculator.html'

    GRADE_THRESHOLDS = {
        'A+': 97, 'A': 93, 'A-': 90, 'B+': 87, 'B': 83, 'B-': 80,
        'C+': 77, 'C': 73, 'C-': 70, 'D+': 67, 'D': 63, 'D-': 60, 'F': 0
    }

    def get(self, request):
        return render(request, self.template_name, {'calculator_name': _('Grade Calculator')})

    def post(self, request):
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'final_grade_needed')
            handlers = {
                'final_grade_needed': self._calc_final_needed,
                'current_grade': self._calc_current_grade,
                'grade_percentage': self._calc_percentage,
                'weighted_grade': self._calc_weighted,
                'convert_to_letter': self._calc_letter,
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

    def _calc_final_needed(self, data):
        try:
            current_grade = float(data.get('current_grade', 0))
            target_grade = float(data.get('target_grade', 0))
            final_weight = float(data.get('final_weight', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Please enter valid numeric values.'))}, status=400)

        if not (0 <= current_grade <= 100):
            return JsonResponse({'success': False, 'error': str(_('Current grade must be between 0 and 100.'))}, status=400)
        if not (0 <= target_grade <= 100):
            return JsonResponse({'success': False, 'error': str(_('Target grade must be between 0 and 100.'))}, status=400)
        if not (0 < final_weight <= 100):
            return JsonResponse({'success': False, 'error': str(_('Final weight must be between 0 and 100.'))}, status=400)

        current_weight = float(np.subtract(100.0, final_weight))
        current_points = float(np.multiply(current_grade, np.divide(current_weight, 100.0)))
        points_needed = float(np.subtract(target_grade, current_points))
        final_needed = float(np.divide(points_needed, np.divide(final_weight, 100.0)))

        if math.isinf(final_needed) or math.isnan(final_needed):
            return JsonResponse({'success': False, 'error': str(_('Invalid calculation result.'))}, status=400)

        achievable = final_needed <= 100
        max_possible = float(np.add(current_points, np.multiply(100.0, np.divide(final_weight, 100.0)))) if not achievable else None

        steps = [
            str(_('Step 1: Identify the given values')),
            str(_('Current Grade')) + f': {current_grade}%',
            str(_('Target Grade')) + f': {target_grade}%',
            str(_('Final Exam Weight')) + f': {final_weight}%',
            '',
            str(_('Step 2: Calculate current weight')),
            str(_('Current Weight')) + f' = 100% - {final_weight}% = {current_weight}%',
            '',
            str(_('Step 3: Calculate points from current grade')),
            str(_('Current Points')) + f' = {current_grade} × ({current_weight}/100) = {round(current_points, 2)}',
            '',
            str(_('Step 4: Calculate final grade needed')),
            str(_('Final Grade Needed')) + f' = ({target_grade} - {round(current_points, 2)}) / ({final_weight}/100)',
            str(_('Final Grade Needed')) + f' = {round(final_needed, 2)}%',
            '',
        ]
        if not achievable:
            steps.append(str(_('Note: Target is not achievable. Maximum possible grade')) + f': {round(max_possible, 2)}%')
        else:
            steps.append(str(_('Final Answer')) + f': ' + str(_('You need')) + f' {round(final_needed, 2)}% ' + str(_('on the final to achieve')) + f' {target_grade}%')

        chart_data = {'final_chart': {'type': 'bar', 'data': {
            'labels': [str(_('Current Grade')), str(_('Target Grade')), str(_('Final Needed'))],
            'datasets': [{'label': '%', 'data': [current_grade, target_grade, min(round(final_needed, 2), 100)],
                          'backgroundColor': ['rgba(59,130,246,0.8)', 'rgba(16,185,129,0.8)', 'rgba(251,191,36,0.8)'],
                          'borderColor': ['#3b82f6', '#10b981', '#fbbf24'], 'borderWidth': 2, 'borderRadius': 8}]}}}

        return JsonResponse({'success': True, 'calc_type': 'final_grade_needed', 'current_grade': current_grade,
            'target_grade': target_grade, 'final_weight': final_weight, 'current_weight': current_weight,
            'final_grade_needed': round(final_needed, 2), 'achievable': achievable, 'max_possible': round(max_possible, 2) if max_possible else None,
            'step_by_step': steps, 'chart_data': chart_data})

    def _calc_current_grade(self, data):
        assignments = data.get('assignments', [])
        if not assignments or not isinstance(assignments, list):
            return JsonResponse({'success': False, 'error': str(_('Please add at least one assignment.'))}, status=400)
        if len(assignments) > 50:
            return JsonResponse({'success': False, 'error': str(_('Maximum 50 assignments allowed.'))}, status=400)

        processed = []
        total_earned = 0
        total_possible = 0
        total_weight = 0

        for i, a in enumerate(assignments):
            if not isinstance(a, dict):
                return JsonResponse({'success': False, 'error': str(_('Invalid assignment data format.'))}, status=400)
            name = a.get('name', '').strip() or str(_('Assignment')) + f' {i+1}'
            try:
                earned = float(a.get('points_earned', 0))
                possible = float(a.get('points_possible', 0))
                weight = float(a.get('weight', 0))
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': str(_('Invalid values for assignment')) + f': {name}'}, status=400)
            if earned < 0:
                return JsonResponse({'success': False, 'error': str(_('Points earned must be non-negative for')) + f': {name}'}, status=400)
            if possible <= 0:
                return JsonResponse({'success': False, 'error': str(_('Points possible must be greater than zero for')) + f': {name}'}, status=400)
            if earned > possible:
                return JsonResponse({'success': False, 'error': str(_('Points earned cannot exceed points possible for')) + f': {name}'}, status=400)

            pct = float(np.multiply(np.divide(earned, possible), 100.0))
            processed.append({'name': name, 'points_earned': earned, 'points_possible': possible, 'weight': weight, 'percentage': round(pct, 2)})
            total_earned += earned
            total_possible += possible
            total_weight += weight

        if total_weight > 0:
            weighted_sum = sum(float(np.multiply(a['percentage'], np.divide(a['weight'], 100.0))) for a in processed if a['weight'] > 0)
            current_grade = float(np.divide(weighted_sum, np.divide(total_weight, 100.0)))
        else:
            current_grade = float(np.multiply(np.divide(total_earned, total_possible), 100.0))

        if math.isinf(current_grade) or math.isnan(current_grade):
            return JsonResponse({'success': False, 'error': str(_('Invalid calculation result.'))}, status=400)

        letter = self._pct_to_letter(current_grade)
        is_weighted = total_weight > 0

        steps = [str(_('Step 1: Identify all assignments'))]
        for i, a in enumerate(processed, 1):
            steps.append(f"{str(_('Assignment'))} {i}: {a['name']} - {a['points_earned']}/{a['points_possible']} ({a['percentage']}%)")
        steps.append('')
        if is_weighted:
            steps.append(str(_('Step 2: Calculate weighted contributions')))
            for a in processed:
                if a['weight'] > 0:
                    c = round(a['percentage'] * a['weight'] / 100, 2)
                    steps.append(f"{a['name']}: {a['percentage']}% × {a['weight']}% = {c}")
            steps.append('')
            steps.append(str(_('Step 3: Calculate weighted average')))
            steps.append(str(_('Current Grade')) + f' = {round(current_grade, 2)}%')
        else:
            steps.append(str(_('Step 2: Calculate totals')))
            steps.append(str(_('Total Points Earned')) + f' = {total_earned}')
            steps.append(str(_('Total Points Possible')) + f' = {total_possible}')
            steps.append('')
            steps.append(str(_('Step 3: Calculate current grade')))
            steps.append(str(_('Current Grade')) + f' = ({total_earned}/{total_possible}) × 100 = {round(current_grade, 2)}%')
        steps.extend(['', str(_('Final Answer')) + ': ' + str(_('Current Grade')) + f' = {round(current_grade, 2)}% ({letter})'])

        chart_data = {'current_chart': {'type': 'bar', 'data': {
            'labels': [a['name'][:15] for a in processed],
            'datasets': [{'label': '%', 'data': [a['percentage'] for a in processed],
                          'backgroundColor': ['rgba(59,130,246,0.8)'] * len(processed),
                          'borderColor': ['#3b82f6'] * len(processed), 'borderWidth': 2, 'borderRadius': 8}]}}}

        return JsonResponse({'success': True, 'calc_type': 'current_grade', 'assignments': processed,
            'current_grade': round(current_grade, 2), 'letter_grade': letter,
            'total_points_earned': round(total_earned, 2), 'total_points_possible': round(total_possible, 2),
            'is_weighted': is_weighted, 'step_by_step': steps, 'chart_data': chart_data})

    def _calc_percentage(self, data):
        try:
            earned = float(data.get('points_earned', 0))
            possible = float(data.get('points_possible', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Please enter valid numeric values.'))}, status=400)
        if earned < 0:
            return JsonResponse({'success': False, 'error': str(_('Points earned must be non-negative.'))}, status=400)
        if possible <= 0:
            return JsonResponse({'success': False, 'error': str(_('Points possible must be greater than zero.'))}, status=400)
        if earned > possible:
            return JsonResponse({'success': False, 'error': str(_('Points earned cannot exceed points possible.'))}, status=400)

        pct = float(np.multiply(np.divide(earned, possible), 100.0))
        letter = self._pct_to_letter(pct)

        steps = [
            str(_('Step 1: Identify the given values')),
            str(_('Points Earned')) + f': {earned}', str(_('Points Possible')) + f': {possible}', '',
            str(_('Step 2: Apply the percentage formula')),
            str(_('Percentage')) + f' = ({earned} / {possible}) × 100 = {round(pct, 2)}%', '',
            str(_('Final Answer')) + f': {round(pct, 2)}% ({letter})',
        ]
        chart_data = {'pct_chart': {'type': 'doughnut', 'data': {
            'labels': [str(_('Points Earned')), str(_('Points Remaining'))],
            'datasets': [{'data': [earned, possible - earned],
                          'backgroundColor': ['rgba(16,185,129,0.8)', 'rgba(156,163,175,0.4)'],
                          'borderColor': ['#10b981', '#9ca3af'], 'borderWidth': 2}]}}}

        return JsonResponse({'success': True, 'calc_type': 'grade_percentage', 'points_earned': earned,
            'points_possible': possible, 'percentage': round(pct, 2), 'letter_grade': letter,
            'step_by_step': steps, 'chart_data': chart_data})

    def _calc_weighted(self, data):
        assignments = data.get('assignments', [])
        if not assignments or not isinstance(assignments, list):
            return JsonResponse({'success': False, 'error': str(_('Please add at least one assignment.'))}, status=400)

        processed = []
        weighted_sum = 0
        total_weight = 0

        for i, a in enumerate(assignments):
            if not isinstance(a, dict):
                return JsonResponse({'success': False, 'error': str(_('Invalid assignment data format.'))}, status=400)
            name = a.get('name', '').strip() or str(_('Assignment')) + f' {i+1}'
            try:
                grade = float(a.get('grade', 0))
                weight = float(a.get('weight', 0))
            except (ValueError, TypeError):
                return JsonResponse({'success': False, 'error': str(_('Invalid values for assignment')) + f': {name}'}, status=400)
            if not (0 <= grade <= 100):
                return JsonResponse({'success': False, 'error': str(_('Grade must be between 0 and 100 for')) + f': {name}'}, status=400)
            if not (0 < weight <= 100):
                return JsonResponse({'success': False, 'error': str(_('Weight must be between 0 and 100 for')) + f': {name}'}, status=400)

            contribution = float(np.multiply(grade, np.divide(weight, 100.0)))
            processed.append({'name': name, 'grade': grade, 'weight': weight, 'weighted_contribution': round(contribution, 2)})
            weighted_sum += contribution
            total_weight += weight

        if total_weight > 100:
            return JsonResponse({'success': False, 'error': str(_('Total weight cannot exceed 100%.'))}, status=400)
        if total_weight == 0:
            return JsonResponse({'success': False, 'error': str(_('Total weight must be greater than zero.'))}, status=400)

        weighted_grade = float(np.divide(weighted_sum, np.divide(total_weight, 100.0)))
        if math.isinf(weighted_grade) or math.isnan(weighted_grade):
            return JsonResponse({'success': False, 'error': str(_('Invalid calculation result.'))}, status=400)

        letter = self._pct_to_letter(weighted_grade)

        steps = [str(_('Step 1: Identify assignments and weights'))]
        for i, a in enumerate(processed, 1):
            steps.append(f"{str(_('Assignment'))} {i}: {a['name']} - {str(_('Grade'))}: {a['grade']}%, {str(_('Weight'))}: {a['weight']}%")
        steps.append('')
        steps.append(str(_('Step 2: Calculate weighted contributions')))
        for a in processed:
            steps.append(f"{a['name']}: {a['grade']}% × ({a['weight']}%/100) = {a['weighted_contribution']}")
        steps.append('')
        steps.append(str(_('Step 3: Calculate weighted grade')))
        steps.append(str(_('Sum of contributions')) + f' = {round(weighted_sum, 2)}')
        steps.append(str(_('Total weight')) + f' = {total_weight}%')
        steps.append(str(_('Weighted Grade')) + f' = {round(weighted_sum, 2)} / ({total_weight}/100) = {round(weighted_grade, 2)}%')
        steps.extend(['', str(_('Final Answer')) + f': {round(weighted_grade, 2)}% ({letter})'])

        chart_data = {'weighted_chart': {'type': 'bar', 'data': {
            'labels': [a['name'][:15] for a in processed],
            'datasets': [{'label': '%', 'data': [a['grade'] for a in processed],
                          'backgroundColor': ['rgba(59,130,246,0.8)'] * len(processed),
                          'borderColor': ['#3b82f6'] * len(processed), 'borderWidth': 2, 'borderRadius': 8}]}}}

        return JsonResponse({'success': True, 'calc_type': 'weighted_grade', 'assignments': processed,
            'weighted_grade': round(weighted_grade, 2), 'letter_grade': letter,
            'total_weight': round(total_weight, 2), 'step_by_step': steps, 'chart_data': chart_data})

    def _calc_letter(self, data):
        try:
            pct = float(data.get('percentage', 0))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Please enter a valid numeric value.'))}, status=400)
        if not (0 <= pct <= 100):
            return JsonResponse({'success': False, 'error': str(_('Percentage must be between 0 and 100.'))}, status=400)

        letter = self._pct_to_letter(pct)
        steps = [
            str(_('Step 1: Identify the percentage')), f'{pct}%', '',
            str(_('Step 2: Find the corresponding letter grade')),
        ]
        for l, t in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if pct >= t:
                steps.append(f'{pct}% ≥ {t}% → {l}')
                break
        steps.extend(['', str(_('Final Answer')) + f': {pct}% = {letter}'])

        return JsonResponse({'success': True, 'calc_type': 'convert_to_letter', 'percentage': pct,
            'letter_grade': letter, 'step_by_step': steps})

    def _pct_to_letter(self, pct):
        for letter, threshold in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if pct >= threshold:
                return letter
        return 'F'
