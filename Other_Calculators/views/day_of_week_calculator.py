from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DayOfWeekCalculator(View):
    """
    Professional Day of Week Calculator with Comprehensive Features
    
    This calculator provides day of week calculations with:
    - Find what day of the week a date falls on
    - Find next occurrence of a weekday
    - Find previous occurrence of a weekday
    - Count weekdays in a date range
    - Find all dates of a weekday in a range
    
    Features:
    - Supports multiple calculation modes
    - Handles leap years correctly
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/day_of_week_calculator.html'
    
    # Weekday names
    WEEKDAYS = [
        _('Monday'),
        _('Tuesday'),
        _('Wednesday'),
        _('Thursday'),
        _('Friday'),
        _('Saturday'),
        _('Sunday')
    ]
    
    # Month names
    MONTHS = [
        _('January'), _('February'), _('March'), _('April'), _('May'), _('June'),
        _('July'), _('August'), _('September'), _('October'), _('November'), _('December')
    ]
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Day Of Week Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'find_day')
            
            if calc_type == 'find_day':
                return self._find_day_of_week(data)
            elif calc_type == 'next_occurrence':
                return self._find_next_occurrence(data)
            elif calc_type == 'previous_occurrence':
                return self._find_previous_occurrence(data)
            elif calc_type == 'count_weekdays':
                return self._count_weekdays_in_range(data)
            elif calc_type == 'find_all_occurrences':
                return self._find_all_occurrences(data)
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
    
    def _find_day_of_week(self, data):
        """Find what day of the week a date falls on"""
        try:
            target_date_str = data.get('target_date')
            
            if not target_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a date.')
                }, status=400)
            
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            
            # Get day of week (0=Monday, 6=Sunday)
            weekday_index = target_date.weekday()
            day_of_week = self.WEEKDAYS[weekday_index]
            
            # Format date
            date_formatted = f"{self.MONTHS[target_date.month - 1]} {target_date.day}, {target_date.year}"
            
            # Additional info
            is_weekend = weekday_index >= 5
            is_weekday = weekday_index < 5
            
            response_data = {
                'success': True,
                'calc_type': 'find_day',
                'target_date': str(target_date),
                'date_formatted': date_formatted,
                'day_of_week': day_of_week,
                'weekday_index': weekday_index,
                'is_weekend': is_weekend,
                'is_weekday': is_weekday,
                'step_by_step': self._prepare_find_day_steps(target_date, day_of_week, weekday_index),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format. Please use YYYY-MM-DD format.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error finding day of week: {error}').format(error=str(e))
            }, status=500)
    
    def _find_next_occurrence(self, data):
        """Find next occurrence of a weekday"""
        try:
            from_date_str = data.get('from_date')
            weekday_name = data.get('weekday')
            
            if not from_date_str or not weekday_name:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a date and weekday.')
                }, status=400)
            
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            
            # Find weekday index
            try:
                weekday_index = self.WEEKDAYS.index(weekday_name)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid weekday name.')
                }, status=400)
            
            # Calculate days until next occurrence
            current_weekday = from_date.weekday()
            days_ahead = weekday_index - current_weekday
            
            if days_ahead <= 0:  # Target weekday already passed this week
                days_ahead += 7
            
            next_date = from_date + timedelta(days=days_ahead)
            
            date_formatted = f"{self.MONTHS[next_date.month - 1]} {next_date.day}, {next_date.year}"
            
            response_data = {
                'success': True,
                'calc_type': 'next_occurrence',
                'from_date': str(from_date),
                'weekday': weekday_name,
                'next_date': str(next_date),
                'date_formatted': date_formatted,
                'days_until': days_ahead,
                'step_by_step': self._prepare_next_occurrence_steps(from_date, weekday_name, next_date, days_ahead),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _find_previous_occurrence(self, data):
        """Find previous occurrence of a weekday"""
        try:
            from_date_str = data.get('from_date')
            weekday_name = data.get('weekday')
            
            if not from_date_str or not weekday_name:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a date and weekday.')
                }, status=400)
            
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            
            # Find weekday index
            try:
                weekday_index = self.WEEKDAYS.index(weekday_name)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid weekday name.')
                }, status=400)
            
            # Calculate days until previous occurrence
            current_weekday = from_date.weekday()
            days_back = current_weekday - weekday_index
            
            if days_back <= 0:  # Target weekday hasn't occurred this week yet
                days_back += 7
            
            previous_date = from_date - timedelta(days=days_back)
            
            date_formatted = f"{self.MONTHS[previous_date.month - 1]} {previous_date.day}, {previous_date.year}"
            
            response_data = {
                'success': True,
                'calc_type': 'previous_occurrence',
                'from_date': str(from_date),
                'weekday': weekday_name,
                'previous_date': str(previous_date),
                'date_formatted': date_formatted,
                'days_ago': days_back,
                'step_by_step': self._prepare_previous_occurrence_steps(from_date, weekday_name, previous_date, days_back),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _count_weekdays_in_range(self, data):
        """Count occurrences of a weekday in a date range"""
        try:
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            weekday_name = data.get('weekday')
            
            if not start_date_str or not end_date_str or not weekday_name:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide start date, end date, and weekday.')
                }, status=400)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            if start_date > end_date:
                return JsonResponse({
                    'success': False,
                    'error': _('Start date must be before or equal to end date.')
                }, status=400)
            
            # Find weekday index
            try:
                weekday_index = self.WEEKDAYS.index(weekday_name)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid weekday name.')
                }, status=400)
            
            # Count occurrences
            count = 0
            current = start_date
            occurrences = []
            
            while current <= end_date:
                if current.weekday() == weekday_index:
                    count += 1
                    occurrences.append(str(current))
                current += timedelta(days=1)
            
            response_data = {
                'success': True,
                'calc_type': 'count_weekdays',
                'start_date': str(start_date),
                'end_date': str(end_date),
                'weekday': weekday_name,
                'count': count,
                'occurrences': occurrences[:10],  # Limit to first 10 for display
                'total_occurrences': len(occurrences),
                'step_by_step': self._prepare_count_weekdays_steps(start_date, end_date, weekday_name, count),
                'chart_data': self._prepare_count_weekdays_chart_data(count, weekday_name),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _find_all_occurrences(self, data):
        """Find all occurrences of a weekday in a date range"""
        try:
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            weekday_name = data.get('weekday')
            
            if not start_date_str or not end_date_str or not weekday_name:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide start date, end date, and weekday.')
                }, status=400)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            if start_date > end_date:
                return JsonResponse({
                    'success': False,
                    'error': _('Start date must be before or equal to end date.')
                }, status=400)
            
            # Find weekday index
            try:
                weekday_index = self.WEEKDAYS.index(weekday_name)
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid weekday name.')
                }, status=400)
            
            # Find all occurrences
            occurrences = []
            current = start_date
            
            while current <= end_date:
                if current.weekday() == weekday_index:
                    date_formatted = f"{self.MONTHS[current.month - 1]} {current.day}, {current.year}"
                    occurrences.append({
                        'date': str(current),
                        'formatted': date_formatted
                    })
                current += timedelta(days=1)
            
            response_data = {
                'success': True,
                'calc_type': 'find_all_occurrences',
                'start_date': str(start_date),
                'end_date': str(end_date),
                'weekday': weekday_name,
                'count': len(occurrences),
                'occurrences': occurrences[:20],  # Limit to first 20 for display
                'step_by_step': self._prepare_find_all_steps(start_date, end_date, weekday_name, len(occurrences)),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _prepare_find_day_steps(self, target_date, day_of_week, weekday_index):
        """Prepare step-by-step for finding day of week"""
        steps = []
        steps.append(_('Step 1: Identify the date'))
        steps.append(_('Target Date: {date}').format(date=target_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the day of week'))
        steps.append(_('Using Python datetime.weekday() method'))
        steps.append(_('Weekday Index: {index} (0=Monday, 6=Sunday)').format(index=weekday_index))
        steps.append('')
        steps.append(_('Step 3: Determine the day name'))
        steps.append(_('Day of Week: {day}').format(day=day_of_week))
        if weekday_index >= 5:
            steps.append(_('Note: This is a weekend day (Saturday or Sunday)'))
        else:
            steps.append(_('Note: This is a weekday (Monday through Friday)'))
        return steps
    
    def _prepare_next_occurrence_steps(self, from_date, weekday_name, next_date, days_until):
        """Prepare step-by-step for next occurrence"""
        steps = []
        steps.append(_('Step 1: Identify the starting date'))
        steps.append(_('From Date: {date}').format(date=from_date.strftime('%B %d, %Y')))
        steps.append(_('Target Weekday: {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 2: Calculate days until next occurrence'))
        steps.append(_('Current weekday: {day}').format(day=self.WEEKDAYS[from_date.weekday()]))
        steps.append(_('Days until next {target}: {days}').format(target=weekday_name, days=days_until))
        steps.append('')
        steps.append(_('Step 3: Calculate the next date'))
        steps.append(_('Next {day}: {date}').format(day=weekday_name, date=next_date.strftime('%B %d, %Y')))
        return steps
    
    def _prepare_previous_occurrence_steps(self, from_date, weekday_name, previous_date, days_ago):
        """Prepare step-by-step for previous occurrence"""
        steps = []
        steps.append(_('Step 1: Identify the starting date'))
        steps.append(_('From Date: {date}').format(date=from_date.strftime('%B %d, %Y')))
        steps.append(_('Target Weekday: {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 2: Calculate days since previous occurrence'))
        steps.append(_('Current weekday: {day}').format(day=self.WEEKDAYS[from_date.weekday()]))
        steps.append(_('Days since last {target}: {days}').format(target=weekday_name, days=days_ago))
        steps.append('')
        steps.append(_('Step 3: Calculate the previous date'))
        steps.append(_('Previous {day}: {date}').format(day=weekday_name, date=previous_date.strftime('%B %d, %Y')))
        return steps
    
    def _prepare_count_weekdays_steps(self, start_date, end_date, weekday_name, count):
        """Prepare step-by-step for counting weekdays"""
        steps = []
        steps.append(_('Step 1: Identify the date range'))
        steps.append(_('Start Date: {date}').format(date=start_date.strftime('%B %d, %Y')))
        steps.append(_('End Date: {date}').format(date=end_date.strftime('%B %d, %Y')))
        steps.append(_('Target Weekday: {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 2: Count occurrences'))
        steps.append(_('Iterate through each date in the range'))
        steps.append(_('Check if each date falls on {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 3: Result'))
        steps.append(_('Total occurrences of {day}: {count}').format(day=weekday_name, count=count))
        return steps
    
    def _prepare_find_all_steps(self, start_date, end_date, weekday_name, count):
        """Prepare step-by-step for finding all occurrences"""
        steps = []
        steps.append(_('Step 1: Identify the date range'))
        steps.append(_('Start Date: {date}').format(date=start_date.strftime('%B %d, %Y')))
        steps.append(_('End Date: {date}').format(date=end_date.strftime('%B %d, %Y')))
        steps.append(_('Target Weekday: {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 2: Find all occurrences'))
        steps.append(_('Iterate through each date in the range'))
        steps.append(_('Collect all dates that fall on {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 3: Result'))
        steps.append(_('Found {count} occurrences of {day}').format(count=count, day=weekday_name))
        return steps
    
    def _prepare_count_weekdays_chart_data(self, count, weekday_name):
        """Prepare chart data for counting weekdays"""
        chart_config = {
            'type': 'doughnut',
            'data': {
                'labels': [
                    _('Occurrences of {day}').format(day=weekday_name),
                    _('Other Days')
                ],
                'datasets': [{
                    'data': [count, max(1, 10 - count)],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(229, 231, 235, 0.8)'
                    ],
                    'borderColor': [
                        '#3b82f6',
                        '#e5e7eb'
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
                        'text': _('Weekday Occurrences')
                    }
                }
            }
        }
        
        return {'weekday_chart': chart_config}
