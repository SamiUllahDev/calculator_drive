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
class GradeCalculator(View):
    """
    Professional Grade Calculator with Comprehensive Features
    
    This calculator provides grade calculations with:
    - Calculate final grade needed to achieve target grade
    - Calculate current grade from completed assignments
    - Calculate grade percentage from points
    - Calculate weighted grade
    - Convert percentage to letter grade
    
    Features:
    - Supports multiple calculation modes
    - Handles weighted and unweighted grades
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/grade_calculator.html'
    
    # Letter grade thresholds (percentage-based)
    GRADE_THRESHOLDS = {
        'A+': 97, 'A': 93, 'A-': 90,
        'B+': 87, 'B': 83, 'B-': 80,
        'C+': 77, 'C': 73, 'C-': 70,
        'D+': 67, 'D': 63, 'D-': 60,
        'F': 0
    }
    
    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Grade Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'final_grade_needed')
            
            if calc_type == 'final_grade_needed':
                return self._calculate_final_grade_needed(data)
            elif calc_type == 'current_grade':
                return self._calculate_current_grade(data)
            elif calc_type == 'grade_percentage':
                return self._calculate_grade_percentage(data)
            elif calc_type == 'weighted_grade':
                return self._calculate_weighted_grade(data)
            elif calc_type == 'convert_to_letter':
                return self._convert_to_letter(data)
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
    
    def _calculate_final_grade_needed(self, data):
        """Calculate final grade needed to achieve target grade"""
        try:
            if 'current_grade' not in data or data.get('current_grade') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Current grade is required.')
                }, status=400)
            
            if 'target_grade' not in data or data.get('target_grade') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Target grade is required.')
                }, status=400)
            
            if 'final_weight' not in data or data.get('final_weight') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Final exam/assignment weight is required.')
                }, status=400)
            
            try:
                current_grade = float(data.get('current_grade', 0))
                target_grade = float(data.get('target_grade', 0))
                final_weight = float(data.get('final_weight', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validate ranges
            if current_grade < 0 or current_grade > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Current grade must be between 0 and 100.')
                }, status=400)
            
            if target_grade < 0 or target_grade > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Target grade must be between 0 and 100.')
                }, status=400)
            
            if final_weight <= 0 or final_weight > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Final weight must be between 0 and 100 (exclusive).')
                }, status=400)
            
            # Calculate current weight (100 - final_weight)
            current_weight = float(np.subtract(100.0, final_weight))
            
            # Calculate points from current grade
            current_points = float(np.multiply(current_grade, np.divide(current_weight, 100.0)))
            
            # Calculate points needed for target grade
            target_points = float(np.multiply(target_grade, 1.0))
            
            # Calculate points needed from final
            points_needed_from_final = float(np.subtract(target_points, current_points))
            
            # Calculate final grade needed
            final_grade_needed = float(np.divide(points_needed_from_final, np.divide(final_weight, 100.0)))
            
            # Validate result
            if math.isinf(final_grade_needed) or math.isnan(final_grade_needed) or np.isinf(final_grade_needed) or np.isnan(final_grade_needed):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Check if achievable
            achievable = final_grade_needed <= 100
            if not achievable and final_grade_needed > 100:
                # Calculate maximum possible grade
                max_possible = float(np.add(
                    current_points,
                    np.multiply(100.0, np.divide(final_weight, 100.0))
                ))
            else:
                max_possible = None
            
            steps = self._prepare_final_grade_needed_steps(current_grade, target_grade, final_weight, current_weight, current_points, final_grade_needed, achievable, max_possible)
            
            chart_data = self._prepare_final_grade_needed_chart_data(current_grade, target_grade, final_grade_needed, final_weight, current_weight)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'final_grade_needed',
                'current_grade': current_grade,
                'target_grade': target_grade,
                'final_weight': final_weight,
                'current_weight': current_weight,
                'final_grade_needed': final_grade_needed,
                'achievable': achievable,
                'max_possible': max_possible,
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
                'error': _('Error calculating final grade needed: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_current_grade(self, data):
        """Calculate current grade from completed assignments"""
        try:
            if 'assignments' not in data or not isinstance(data.get('assignments'), list):
                return JsonResponse({
                    'success': False,
                    'error': _('Assignments are required as a list.')
                }, status=400)
            
            assignments = data.get('assignments', [])
            
            if len(assignments) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('At least one assignment is required.')
                }, status=400)
            
            if len(assignments) > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Maximum 50 assignments allowed.')
                }, status=400)
            
            processed_assignments = []
            total_points_earned = 0
            total_points_possible = 0
            total_weight = 0
            
            for i, assignment in enumerate(assignments):
                if not isinstance(assignment, dict):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid assignment data format.')
                    }, status=400)
                
                name = assignment.get('name', '').strip() or _('Assignment {num}').format(num=i+1)
                
                try:
                    points_earned = float(assignment.get('points_earned', 0))
                    points_possible = float(assignment.get('points_possible', 0))
                    weight = float(assignment.get('weight', 0))  # Optional weight
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid values for assignment: {name}').format(name=name)
                    }, status=400)
                
                # Validate ranges
                if points_earned < 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Points earned must be non-negative for assignment: {name}').format(name=name)
                    }, status=400)
                
                if points_possible <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': _('Points possible must be greater than zero for assignment: {name}').format(name=name)
                    }, status=400)
                
                if points_earned > points_possible:
                    return JsonResponse({
                        'success': False,
                        'error': _('Points earned cannot exceed points possible for assignment: {name}').format(name=name)
                    }, status=400)
                
                if weight < 0 or weight > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Weight must be between 0 and 100 for assignment: {name}').format(name=name)
                    }, status=400)
                
                # Calculate percentage for this assignment
                percentage = float(np.multiply(
                    np.divide(points_earned, points_possible),
                    100.0
                ))
                
                processed_assignments.append({
                    'name': name,
                    'points_earned': points_earned,
                    'points_possible': points_possible,
                    'weight': weight,
                    'percentage': round(percentage, 2)
                })
                
                # If weighted, calculate weighted contribution
                if weight > 0:
                    weighted_contribution = float(np.multiply(percentage, np.divide(weight, 100.0)))
                    total_weight += weight
                else:
                    # Unweighted: just add points
                    weighted_contribution = None
                
                total_points_earned += points_earned
                total_points_possible += points_possible
            
            # Calculate current grade
            if total_points_possible > 0:
                if total_weight > 0:
                    # Weighted average
                    weighted_sum = sum(
                        float(np.multiply(a['percentage'], np.divide(a['weight'], 100.0)))
                        for a in processed_assignments if a['weight'] > 0
                    )
                    current_grade = float(np.divide(weighted_sum, np.divide(total_weight, 100.0))) if total_weight > 0 else 0
                else:
                    # Unweighted average
                    current_grade = float(np.multiply(
                        np.divide(total_points_earned, total_points_possible),
                        100.0
                    ))
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Total points possible must be greater than zero.')
                }, status=400)
            
            # Validate result
            if math.isinf(current_grade) or math.isnan(current_grade) or np.isinf(current_grade) or np.isnan(current_grade):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Get letter grade
            letter_grade = self._percentage_to_letter(current_grade)
            
            steps = self._prepare_current_grade_steps(processed_assignments, total_points_earned, total_points_possible, current_grade, total_weight > 0)
            
            chart_data = self._prepare_current_grade_chart_data(processed_assignments, current_grade)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'current_grade',
                'assignments': processed_assignments,
                'current_grade': round(current_grade, 2),
                'letter_grade': letter_grade,
                'total_points_earned': round(total_points_earned, 2),
                'total_points_possible': round(total_points_possible, 2),
                'is_weighted': total_weight > 0,
                'total_weight': round(total_weight, 2) if total_weight > 0 else None,
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
                'error': _('Error calculating current grade: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_grade_percentage(self, data):
        """Calculate grade percentage from points"""
        try:
            if 'points_earned' not in data or data.get('points_earned') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Points earned is required.')
                }, status=400)
            
            if 'points_possible' not in data or data.get('points_possible') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Points possible is required.')
                }, status=400)
            
            try:
                points_earned = float(data.get('points_earned', 0))
                points_possible = float(data.get('points_possible', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            # Validate ranges
            if points_earned < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Points earned must be non-negative.')
                }, status=400)
            
            if points_possible <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Points possible must be greater than zero.')
                }, status=400)
            
            if points_earned > points_possible:
                return JsonResponse({
                    'success': False,
                    'error': _('Points earned cannot exceed points possible.')
                }, status=400)
            
            # Calculate percentage
            percentage = float(np.multiply(
                np.divide(points_earned, points_possible),
                100.0
            ))
            
            # Validate result
            if math.isinf(percentage) or math.isnan(percentage) or np.isinf(percentage) or np.isnan(percentage):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Get letter grade
            letter_grade = self._percentage_to_letter(percentage)
            
            steps = self._prepare_grade_percentage_steps(points_earned, points_possible, percentage)
            
            chart_data = self._prepare_grade_percentage_chart_data(points_earned, points_possible, percentage)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'grade_percentage',
                'points_earned': points_earned,
                'points_possible': points_possible,
                'percentage': round(percentage, 2),
                'letter_grade': letter_grade,
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
                'error': _('Error calculating grade percentage: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_weighted_grade(self, data):
        """Calculate weighted grade"""
        try:
            if 'assignments' not in data or not isinstance(data.get('assignments'), list):
                return JsonResponse({
                    'success': False,
                    'error': _('Assignments are required as a list.')
                }, status=400)
            
            assignments = data.get('assignments', [])
            
            if len(assignments) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('At least one assignment is required.')
                }, status=400)
            
            processed_assignments = []
            weighted_sum = 0
            total_weight = 0
            
            for i, assignment in enumerate(assignments):
                if not isinstance(assignment, dict):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid assignment data format.')
                    }, status=400)
                
                name = assignment.get('name', '').strip() or _('Assignment {num}').format(num=i+1)
                
                try:
                    grade = float(assignment.get('grade', 0))
                    weight = float(assignment.get('weight', 0))
                except (ValueError, TypeError):
                    return JsonResponse({
                        'success': False,
                        'error': _('Invalid values for assignment: {name}').format(name=name)
                    }, status=400)
                
                # Validate ranges
                if grade < 0 or grade > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Grade must be between 0 and 100 for assignment: {name}').format(name=name)
                    }, status=400)
                
                if weight <= 0 or weight > 100:
                    return JsonResponse({
                        'success': False,
                        'error': _('Weight must be between 0 and 100 for assignment: {name}').format(name=name)
                    }, status=400)
                
                weighted_contribution = float(np.multiply(grade, np.divide(weight, 100.0)))
                
                processed_assignments.append({
                    'name': name,
                    'grade': grade,
                    'weight': weight,
                    'weighted_contribution': round(weighted_contribution, 2)
                })
                
                weighted_sum += weighted_contribution
                total_weight += weight
            
            # Validate total weight
            if total_weight > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Total weight cannot exceed 100%. Current total: {total}%').format(total=total_weight)
                }, status=400)
            
            # Calculate weighted grade
            if total_weight > 0:
                weighted_grade = float(np.divide(weighted_sum, np.divide(total_weight, 100.0)))
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Total weight must be greater than zero.')
                }, status=400)
            
            # Validate result
            if math.isinf(weighted_grade) or math.isnan(weighted_grade) or np.isinf(weighted_grade) or np.isnan(weighted_grade):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation result.')
                }, status=400)
            
            # Get letter grade
            letter_grade = self._percentage_to_letter(weighted_grade)
            
            steps = self._prepare_weighted_grade_steps(processed_assignments, weighted_sum, total_weight, weighted_grade)
            
            chart_data = self._prepare_weighted_grade_chart_data(processed_assignments, weighted_grade)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'weighted_grade',
                'assignments': processed_assignments,
                'weighted_grade': round(weighted_grade, 2),
                'letter_grade': letter_grade,
                'total_weight': round(total_weight, 2),
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
                'error': _('Error calculating weighted grade: {error}').format(error=str(e))
            }, status=500)
    
    def _convert_to_letter(self, data):
        """Convert percentage to letter grade"""
        try:
            if 'percentage' not in data or data.get('percentage') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Percentage is required.')
                }, status=400)
            
            try:
                percentage = float(data.get('percentage', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter a numeric value.')
                }, status=400)
            
            # Validate range
            if percentage < 0 or percentage > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Percentage must be between 0 and 100.')
                }, status=400)
            
            # Get letter grade
            letter_grade = self._percentage_to_letter(percentage)
            
            steps = self._prepare_convert_to_letter_steps(percentage, letter_grade)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'convert_to_letter',
                'percentage': percentage,
                'letter_grade': letter_grade,
                'step_by_step': steps,
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
    
    def _percentage_to_letter(self, percentage):
        """Convert percentage to letter grade"""
        for letter, threshold in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if percentage >= threshold:
                return letter
        return 'F'
    
    # Step-by-step solution preparation methods
    def _prepare_final_grade_needed_steps(self, current_grade, target_grade, final_weight, current_weight, current_points, final_grade_needed, achievable, max_possible):
        """Prepare step-by-step solution for final grade needed calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Current Grade: {grade}%').format(grade=current_grade))
        steps.append(_('Target Grade: {grade}%').format(grade=target_grade))
        steps.append(_('Final Weight: {weight}%').format(weight=final_weight))
        steps.append('')
        steps.append(_('Step 2: Calculate current weight'))
        steps.append(_('Current Weight = 100% - Final Weight'))
        steps.append(_('Current Weight = 100% - {final}% = {current}%').format(final=final_weight, current=current_weight))
        steps.append('')
        steps.append(_('Step 3: Calculate points from current grade'))
        steps.append(_('Current Points = Current Grade × (Current Weight / 100)'))
        steps.append(_('Current Points = {grade}% × ({weight}% / 100)').format(grade=current_grade, weight=current_weight))
        steps.append(_('Current Points = {points}').format(points=current_points))
        steps.append('')
        steps.append(_('Step 4: Calculate points needed for target grade'))
        steps.append(_('Target Points = Target Grade = {grade}').format(grade=target_grade))
        steps.append('')
        steps.append(_('Step 5: Calculate points needed from final'))
        steps.append(_('Points Needed = Target Points - Current Points'))
        steps.append(_('Points Needed = {target} - {current} = {needed}').format(
            target=target_grade, current=current_points, needed=target_grade - current_points
        ))
        steps.append('')
        steps.append(_('Step 6: Calculate final grade needed'))
        steps.append(_('Final Grade Needed = Points Needed / (Final Weight / 100)'))
        steps.append(_('Final Grade Needed = {needed} / ({weight}% / 100)').format(
            needed=target_grade - current_points, weight=final_weight
        ))
        steps.append(_('Final Grade Needed = {grade}%').format(grade=round(final_grade_needed, 2)))
        steps.append('')
        if not achievable:
            steps.append(_('Note: This grade is not achievable. Maximum possible grade: {max}%').format(max=round(max_possible, 2)))
        else:
            steps.append(_('Final Result: You need {grade}% on the final to achieve {target}% overall').format(
                grade=round(final_grade_needed, 2), target=target_grade
            ))
        return steps
    
    def _prepare_current_grade_steps(self, processed_assignments, total_points_earned, total_points_possible, current_grade, is_weighted):
        """Prepare step-by-step solution for current grade calculation"""
        steps = []
        steps.append(_('Step 1: Identify all assignments'))
        for i, assignment in enumerate(processed_assignments, 1):
            if is_weighted and assignment['weight'] > 0:
                steps.append(_('Assignment {num}: {name} - {earned}/{possible} points ({weight}% weight)').format(
                    num=i, name=assignment['name'], earned=assignment['points_earned'],
                    possible=assignment['points_possible'], weight=assignment['weight']
                ))
            else:
                steps.append(_('Assignment {num}: {name} - {earned}/{possible} points').format(
                    num=i, name=assignment['name'], earned=assignment['points_earned'],
                    possible=assignment['points_possible']
                ))
        steps.append('')
        if is_weighted:
            steps.append(_('Step 2: Calculate percentage for each assignment'))
            for assignment in processed_assignments:
                if assignment['weight'] > 0:
                    steps.append(_('{name}: ({earned} / {possible}) × 100 = {percent}%').format(
                        name=assignment['name'], earned=assignment['points_earned'],
                        possible=assignment['points_possible'], percent=assignment['percentage']
                    ))
            steps.append('')
            steps.append(_('Step 3: Calculate weighted contribution for each assignment'))
            for assignment in processed_assignments:
                if assignment['weight'] > 0:
                    contribution = assignment['percentage'] * (assignment['weight'] / 100.0)
                    steps.append(_('{name}: {percent}% × {weight}% = {contribution}').format(
                        name=assignment['name'], percent=assignment['percentage'],
                        weight=assignment['weight'], contribution=round(contribution, 2)
                    ))
            steps.append('')
            steps.append(_('Step 4: Calculate weighted average'))
            contributions = [a['percentage'] * (a['weight'] / 100.0) for a in processed_assignments if a['weight'] > 0]
            total_weight = sum(a['weight'] for a in processed_assignments if a['weight'] > 0)
            steps.append(_('Weighted Average = Sum of Contributions / Total Weight'))
            steps.append(_('Weighted Average = {sum} / {weight} = {grade}%').format(
                sum=round(sum(contributions), 2), weight=total_weight, grade=round(current_grade, 2)
            ))
        else:
            steps.append(_('Step 2: Calculate total points earned'))
            points_list = [str(a['points_earned']) for a in processed_assignments]
            steps.append(_('Total Points Earned = {points}').format(points=' + '.join(points_list)))
            steps.append(_('Total Points Earned = {total}').format(total=total_points_earned))
            steps.append('')
            steps.append(_('Step 3: Calculate total points possible'))
            possible_list = [str(a['points_possible']) for a in processed_assignments]
            steps.append(_('Total Points Possible = {points}').format(points=' + '.join(possible_list)))
            steps.append(_('Total Points Possible = {total}').format(total=total_points_possible))
            steps.append('')
            steps.append(_('Step 4: Calculate current grade'))
            steps.append(_('Current Grade = (Total Points Earned / Total Points Possible) × 100'))
            steps.append(_('Current Grade = ({earned} / {possible}) × 100').format(
                earned=total_points_earned, possible=total_points_possible
            ))
            steps.append(_('Current Grade = {grade}%').format(grade=round(current_grade, 2)))
        return steps
    
    def _prepare_grade_percentage_steps(self, points_earned, points_possible, percentage):
        """Prepare step-by-step solution for grade percentage calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Points Earned: {earned}').format(earned=points_earned))
        steps.append(_('Points Possible: {possible}').format(possible=points_possible))
        steps.append('')
        steps.append(_('Step 2: Apply the percentage formula'))
        steps.append(_('Formula: Percentage = (Points Earned / Points Possible) × 100'))
        steps.append(_('Percentage = ({earned} / {possible}) × 100').format(earned=points_earned, possible=points_possible))
        steps.append(_('Percentage = {percent}%').format(percent=round(percentage, 2)))
        return steps
    
    def _prepare_weighted_grade_steps(self, processed_assignments, weighted_sum, total_weight, weighted_grade):
        """Prepare step-by-step solution for weighted grade calculation"""
        steps = []
        steps.append(_('Step 1: Identify all assignments and their weights'))
        for i, assignment in enumerate(processed_assignments, 1):
            steps.append(_('Assignment {num}: {name} - Grade: {grade}%, Weight: {weight}%').format(
                num=i, name=assignment['name'], grade=assignment['grade'], weight=assignment['weight']
            ))
        steps.append('')
        steps.append(_('Step 2: Calculate weighted contribution for each assignment'))
        steps.append(_('Formula: Weighted Contribution = Grade × (Weight / 100)'))
        for assignment in processed_assignments:
            steps.append(_('{name}: {grade}% × ({weight}% / 100) = {contribution}').format(
                name=assignment['name'], grade=assignment['grade'],
                weight=assignment['weight'], contribution=assignment['weighted_contribution']
            ))
        steps.append('')
        steps.append(_('Step 3: Calculate sum of weighted contributions'))
        contributions_list = [str(a['weighted_contribution']) for a in processed_assignments]
        steps.append(_('Sum = {contributions}').format(contributions=' + '.join(contributions_list)))
        steps.append(_('Sum = {total}').format(total=round(weighted_sum, 2)))
        steps.append('')
        steps.append(_('Step 4: Calculate weighted grade'))
        steps.append(_('Weighted Grade = Sum / (Total Weight / 100)'))
        steps.append(_('Weighted Grade = {sum} / ({weight}% / 100)').format(sum=round(weighted_sum, 2), weight=total_weight))
        steps.append(_('Weighted Grade = {grade}%').format(grade=round(weighted_grade, 2)))
        return steps
    
    def _prepare_convert_to_letter_steps(self, percentage, letter_grade):
        """Prepare step-by-step solution for letter grade conversion"""
        steps = []
        steps.append(_('Step 1: Identify the percentage'))
        steps.append(_('Percentage: {percent}%').format(percent=percentage))
        steps.append('')
        steps.append(_('Step 2: Find the corresponding letter grade'))
        steps.append(_('Using standard grade thresholds:'))
        thresholds = sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: x[1], reverse=True)
        for letter, threshold in thresholds:
            if percentage >= threshold:
                steps.append(_('{percent}% ≥ {threshold}% → Grade: {letter}').format(
                    percent=percentage, threshold=threshold, letter=letter
                ))
                break
        steps.append('')
        steps.append(_('Final Result: Letter Grade = {letter}').format(letter=letter_grade))
        return steps
    
    # Chart data preparation methods
    def _prepare_final_grade_needed_chart_data(self, current_grade, target_grade, final_grade_needed, final_weight, current_weight):
        """Prepare chart data for final grade needed calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Current Grade'), _('Target Grade'), _('Final Grade Needed')],
                    'datasets': [{
                        'label': _('Grades (%)'),
                        'data': [current_grade, target_grade, min(final_grade_needed, 100)],
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
                            'text': _('Final Grade Needed Calculation')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': _('Grade (%)')
                            }
                        }
                    }
                }
            }
            return {'final_grade_needed_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_current_grade_chart_data(self, processed_assignments, current_grade):
        """Prepare chart data for current grade calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [a['name'][:20] for a in processed_assignments] + [_('Current Grade')],
                    'datasets': [{
                        'label': _('Grade (%)'),
                        'data': [a['percentage'] for a in processed_assignments] + [current_grade],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in processed_assignments
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in processed_assignments
                        ] + ['#10b981'],
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
                            'text': _('Current Grade Breakdown')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': _('Grade (%)')
                            }
                        }
                    }
                }
            }
            return {'current_grade_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_grade_percentage_chart_data(self, points_earned, points_possible, percentage):
        """Prepare chart data for grade percentage calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('Points Earned'), _('Points Remaining')],
                    'datasets': [{
                        'data': [points_earned, points_possible - points_earned],
                        'backgroundColor': [
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(156, 163, 175, 0.8)'
                        ],
                        'borderColor': [
                            '#10b981',
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
                            'text': _('Grade: {percent}%').format(percent=round(percentage, 2))
                        }
                    }
                }
            }
            return {'grade_percentage_chart': chart_config}
        except Exception as e:
            return None
    
    def _prepare_weighted_grade_chart_data(self, processed_assignments, weighted_grade):
        """Prepare chart data for weighted grade calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [a['name'][:20] for a in processed_assignments] + [_('Weighted Grade')],
                    'datasets': [{
                        'label': _('Grade (%)'),
                        'data': [a['grade'] for a in processed_assignments] + [weighted_grade],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)' for _ in processed_assignments
                        ] + ['rgba(16, 185, 129, 0.8)'],
                        'borderColor': [
                            '#3b82f6' for _ in processed_assignments
                        ] + ['#10b981'],
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
                            'text': _('Weighted Grade Breakdown')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': _('Grade (%)')
                            }
                        }
                    }
                }
            }
            return {'weighted_grade_chart': chart_config}
        except Exception as e:
            return None
