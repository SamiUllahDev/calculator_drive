from django.views import View
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DayOfWeekCalculator(View):
    """
    Day of Week Calculator: find weekday for a date, next/previous occurrence,
    count weekdays in range, find all occurrences. BMI-style upgrade.
    """
    template_name = 'other_calculators/day_of_week_calculator.html'

    WEEKDAYS = [
        _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
        _('Friday'), _('Saturday'), _('Sunday')
    ]
    MONTHS = [
        _('January'), _('February'), _('March'), _('April'), _('May'), _('June'),
        _('July'), _('August'), _('September'), _('October'), _('November'), _('December')
    ]

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _val(self, data, key, default=None):
        v = data.get(key, default)
        return (v[0] if isinstance(v, list) and v else v) if v is not None else default

    def _weekday_index(self, weekday_name):
        if not weekday_name:
            return None
        name = str(weekday_name).strip()
        for i, w in enumerate(self.WEEKDAYS):
            if str(w) == name:
                return i
        return None

    def get(self, request):
        context = {'calculator_name': str(_('Day of Week Calculator'))}
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid request data.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            calc_type = self._val(data, 'calc_type', 'find_day')
            if calc_type == 'find_day':
                result = self._find_day_of_week(data)
            elif calc_type == 'next_occurrence':
                result = self._find_next_occurrence(data)
            elif calc_type == 'previous_occurrence':
                result = self._find_previous_occurrence(data)
            elif calc_type == 'count_weekdays':
                result = self._count_weekdays_in_range(data)
            elif calc_type == 'find_all_occurrences':
                result = self._find_all_occurrences(data)
            else:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid calculation type.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            if isinstance(result, dict) and not result.get('success'):
                return HttpResponse(
                    json.dumps(result, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            return HttpResponse(json.dumps(result, cls=SafeJSONEncoder), content_type='application/json')
        except Exception as e:
            logger.exception("Day of week calculator failed: %s", e)
            from django.conf import settings
            err_msg = str(_('An error occurred during calculation.'))
            if getattr(settings, 'DEBUG', False):
                err_msg += ' [' + str(e).replace('"', "'") + ']'
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}, cls=SafeJSONEncoder),
                content_type='application/json',
                status=500
            )

    def _find_day_of_week(self, data):
        target_date_str = self._val(data, 'target_date', '')
        if not target_date_str:
            return {'success': False, 'error': str(_('Please provide a date.'))}
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        weekday_index = target_date.weekday()
        day_of_week = str(self.WEEKDAYS[weekday_index])
        date_formatted = f"{str(self.MONTHS[target_date.month - 1])} {target_date.day}, {target_date.year}"
        return {
            'success': True,
            'calc_type': 'find_day',
            'target_date': str(target_date),
            'date_formatted': date_formatted,
            'day_of_week': day_of_week,
            'weekday_index': weekday_index,
            'is_weekend': weekday_index >= 5,
            'is_weekday': weekday_index < 5,
            'step_by_step': self._prepare_find_day_steps(target_date, day_of_week, weekday_index),
        }

    def _find_next_occurrence(self, data):
        from_date_str = self._val(data, 'from_date', '')
        weekday_name = self._val(data, 'weekday', '')
        if not from_date_str or not weekday_name:
            return {'success': False, 'error': str(_('Please provide a date and weekday.'))}
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        weekday_index = self._weekday_index(weekday_name)
        if weekday_index is None:
            return {'success': False, 'error': str(_('Invalid weekday name.'))}
        current_weekday = from_date.weekday()
        days_ahead = weekday_index - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        next_date = from_date + timedelta(days=days_ahead)
        date_formatted = f"{str(self.MONTHS[next_date.month - 1])} {next_date.day}, {next_date.year}"
        return {
            'success': True,
            'calc_type': 'next_occurrence',
            'from_date': str(from_date),
            'weekday': weekday_name,
            'next_date': str(next_date),
            'date_formatted': date_formatted,
            'days_until': days_ahead,
            'step_by_step': self._prepare_next_occurrence_steps(from_date, weekday_name, next_date, days_ahead),
        }

    def _find_previous_occurrence(self, data):
        from_date_str = self._val(data, 'from_date', '')
        weekday_name = self._val(data, 'weekday', '')
        if not from_date_str or not weekday_name:
            return {'success': False, 'error': str(_('Please provide a date and weekday.'))}
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        weekday_index = self._weekday_index(weekday_name)
        if weekday_index is None:
            return {'success': False, 'error': str(_('Invalid weekday name.'))}
        current_weekday = from_date.weekday()
        days_back = current_weekday - weekday_index
        if days_back <= 0:
            days_back += 7
        previous_date = from_date - timedelta(days=days_back)
        date_formatted = f"{str(self.MONTHS[previous_date.month - 1])} {previous_date.day}, {previous_date.year}"
        return {
            'success': True,
            'calc_type': 'previous_occurrence',
            'from_date': str(from_date),
            'weekday': weekday_name,
            'previous_date': str(previous_date),
            'date_formatted': date_formatted,
            'days_ago': days_back,
            'step_by_step': self._prepare_previous_occurrence_steps(from_date, weekday_name, previous_date, days_back),
        }

    def _count_weekdays_in_range(self, data):
        start_date_str = self._val(data, 'start_date', '')
        end_date_str = self._val(data, 'end_date', '')
        weekday_name = self._val(data, 'weekday', '')
        if not start_date_str or not end_date_str or not weekday_name:
            return {'success': False, 'error': str(_('Please provide start date, end date, and weekday.'))}
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        if start_date > end_date:
            return {'success': False, 'error': str(_('Start date must be before or equal to end date.'))}
        weekday_index = self._weekday_index(weekday_name)
        if weekday_index is None:
            return {'success': False, 'error': str(_('Invalid weekday name.'))}
        count = 0
        current = start_date
        occurrences = []
        while current <= end_date:
            if current.weekday() == weekday_index:
                count += 1
                occurrences.append(str(current))
            current += timedelta(days=1)
        return {
            'success': True,
            'calc_type': 'count_weekdays',
            'start_date': str(start_date),
            'end_date': str(end_date),
            'weekday': weekday_name,
            'count': count,
            'occurrences': occurrences[:10],
            'total_occurrences': len(occurrences),
            'step_by_step': self._prepare_count_weekdays_steps(start_date, end_date, weekday_name, count),
            'chart_data': self._prepare_count_weekdays_chart_data(count, weekday_name),
        }

    def _find_all_occurrences(self, data):
        start_date_str = self._val(data, 'start_date', '')
        end_date_str = self._val(data, 'end_date', '')
        weekday_name = self._val(data, 'weekday', '')
        if not start_date_str or not end_date_str or not weekday_name:
            return {'success': False, 'error': str(_('Please provide start date, end date, and weekday.'))}
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        if start_date > end_date:
            return {'success': False, 'error': str(_('Start date must be before or equal to end date.'))}
        weekday_index = self._weekday_index(weekday_name)
        if weekday_index is None:
            return {'success': False, 'error': str(_('Invalid weekday name.'))}
        occurrences = []
        current = start_date
        while current <= end_date:
            if current.weekday() == weekday_index:
                date_formatted = f"{str(self.MONTHS[current.month - 1])} {current.day}, {current.year}"
                occurrences.append({'date': str(current), 'formatted': date_formatted})
            current += timedelta(days=1)
        return {
            'success': True,
            'calc_type': 'find_all_occurrences',
            'start_date': str(start_date),
            'end_date': str(end_date),
            'weekday': weekday_name,
            'count': len(occurrences),
            'occurrences': occurrences[:20],
            'step_by_step': self._prepare_find_all_steps(start_date, end_date, weekday_name, len(occurrences)),
            'chart_data': self._prepare_count_weekdays_chart_data(len(occurrences), weekday_name),
        }

    def _prepare_find_day_steps(self, target_date, day_of_week, weekday_index):
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
        steps = []
        steps.append(_('Step 1: Identify the starting date'))
        steps.append(_('From Date: {date}').format(date=from_date.strftime('%B %d, %Y')))
        steps.append(_('Target Weekday: {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 2: Calculate days until next occurrence'))
        steps.append(_('Current weekday: {day}').format(day=str(self.WEEKDAYS[from_date.weekday()])))
        steps.append(_('Days until next {target}: {days}').format(target=weekday_name, days=days_until))
        steps.append('')
        steps.append(_('Step 3: Calculate the next date'))
        steps.append(_('Next {day}: {date}').format(day=weekday_name, date=next_date.strftime('%B %d, %Y')))
        return steps

    def _prepare_previous_occurrence_steps(self, from_date, weekday_name, previous_date, days_ago):
        steps = []
        steps.append(_('Step 1: Identify the starting date'))
        steps.append(_('From Date: {date}').format(date=from_date.strftime('%B %d, %Y')))
        steps.append(_('Target Weekday: {day}').format(day=weekday_name))
        steps.append('')
        steps.append(_('Step 2: Calculate days since previous occurrence'))
        steps.append(_('Current weekday: {day}').format(day=str(self.WEEKDAYS[from_date.weekday()])))
        steps.append(_('Days since last {target}: {days}').format(target=weekday_name, days=days_ago))
        steps.append('')
        steps.append(_('Step 3: Calculate the previous date'))
        steps.append(_('Previous {day}: {date}').format(day=weekday_name, date=previous_date.strftime('%B %d, %Y')))
        return steps

    def _prepare_count_weekdays_steps(self, start_date, end_date, weekday_name, count):
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
        other = max(1, 10 - count)
        chart_config = {
            'type': 'doughnut',
            'data': {
                'labels': [
                    str(_('Occurrences of {day}')).format(day=weekday_name),
                    str(_('Other Days'))
                ],
                'datasets': [{
                    'data': [count, other],
                    'backgroundColor': ['#6366f1', '#e5e7eb'],
                    'borderWidth': 0
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': True, 'position': 'bottom'}}
            }
        }
        return {'weekday_chart': chart_config}
