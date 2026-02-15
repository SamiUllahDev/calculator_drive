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
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DayCounter(View):
    """
    Professional Day Counter with Comprehensive Features
    
    This calculator provides day counting calculations with:
    - Days between two dates
    - Days since a date
    - Days until a date
    - Countdown to events
    - Business days calculations
    
    Features:
    - Supports multiple calculation modes
    - Handles leap years correctly
    - Calculates business days (excluding weekends)
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/day_counter.html'
    
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

    def get(self, request):
        """Handle GET request"""
        context = {'calculator_name': str(_('Day Counter'))}
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return HttpResponse(
                    json.dumps({'success': False, 'error': str(_('Invalid request data.'))}, cls=SafeJSONEncoder),
                    content_type='application/json',
                    status=400
                )
            calc_type = self._val(data, 'calc_type', 'between')
            if calc_type == 'between':
                result = self._calculate_days_between(data)
            elif calc_type == 'since':
                result = self._calculate_days_since(data)
            elif calc_type == 'until':
                result = self._calculate_days_until(data)
            elif calc_type == 'countdown':
                result = self._calculate_countdown(data)
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
            logger.exception("Day counter failed: %s", e)
            from django.conf import settings
            err_msg = str(_('An error occurred during calculation.'))
            if getattr(settings, 'DEBUG', False):
                err_msg += ' [' + str(e).replace('"', "'") + ']'
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}, cls=SafeJSONEncoder),
                content_type='application/json',
                status=500
            )
    
    def _calculate_days_between(self, data):
        """Calculate days between two dates"""
        start_date_str = self._val(data, 'start_date', '')
        end_date_str = self._val(data, 'end_date', '')
        if not start_date_str or not end_date_str:
            return {'success': False, 'error': str(_('Please provide both start and end dates.'))}
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        if start_date > end_date:
            return {'success': False, 'error': str(_('Start date must be before or equal to end date.'))}
        delta = end_date - start_date
        total_days = delta.days
        rd = relativedelta(end_date, start_date)
        total_weeks = total_days // 7
        remaining_days = total_days % 7
        total_months = rd.years * 12 + rd.months
        total_hours = total_days * 24
        total_minutes = total_hours * 60
        total_seconds = total_minutes * 60
        business_days = self._calculate_business_days(start_date, end_date)
        return {
            'success': True,
            'calc_type': 'between',
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_days': total_days,
            'formatted': str(_('{days} days')).format(days=total_days),
            'breakdown': {
                'years': rd.years,
                'months': rd.months,
                'days': rd.days,
                'weeks': total_weeks,
                'weeks_days': str(_('{weeks} weeks, {days} days')).format(weeks=total_weeks, days=remaining_days),
                'hours': total_hours,
                'minutes': total_minutes,
                'seconds': total_seconds,
                'business_days': int(business_days)
            },
            'step_by_step': self._prepare_between_steps(start_date, end_date, total_days, business_days, rd),
            'chart_data': self._prepare_between_chart_data(total_days, total_weeks, total_months, business_days),
        }
    
    def _calculate_days_since(self, data):
        """Calculate days since a date"""
        past_date_str = self._val(data, 'past_date', '')
        if not past_date_str:
            return {'success': False, 'error': str(_('Please provide a date.'))}
        try:
            past_date = datetime.strptime(past_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        today = date.today()
        if past_date > today:
            return {'success': False, 'error': str(_('Date must be in the past.'))}
        delta = today - past_date
        total_days = delta.days
        rd = relativedelta(today, past_date)
        total_weeks = total_days // 7
        total_months = rd.years * 12 + rd.months
        chart_data = self._prepare_days_breakdown_chart(total_days, total_weeks, total_months, rd.years)
        return {
            'success': True,
            'calc_type': 'since',
            'past_date': str(past_date),
            'today': str(today),
            'total_days': total_days,
            'formatted': str(_('{days} days ago')).format(days=total_days),
            'breakdown': {
                'years': rd.years,
                'months': rd.months,
                'days': rd.days,
                'weeks': total_weeks
            },
            'step_by_step': self._prepare_since_steps(past_date, today, total_days),
            'chart_data': chart_data,
        }
    
    def _calculate_days_until(self, data):
        """Calculate days until a date"""
        future_date_str = self._val(data, 'future_date', '')
        if not future_date_str:
            return {'success': False, 'error': str(_('Please provide a date.'))}
        try:
            future_date = datetime.strptime(future_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        today = date.today()
        if future_date < today:
            return {'success': False, 'error': str(_('Date must be in the future.'))}
        delta = future_date - today
        total_days = delta.days
        rd = relativedelta(future_date, today)
        total_weeks = total_days // 7
        total_months = rd.years * 12 + rd.months
        chart_data = self._prepare_days_breakdown_chart(total_days, total_weeks, total_months, rd.years)
        return {
            'success': True,
            'calc_type': 'until',
            'future_date': str(future_date),
            'today': str(today),
            'total_days': total_days,
            'formatted': str(_('{days} days from now')).format(days=total_days),
            'breakdown': {
                'years': rd.years,
                'months': rd.months,
                'days': rd.days,
                'weeks': total_weeks
            },
            'step_by_step': self._prepare_until_steps(today, future_date, total_days),
            'chart_data': chart_data,
        }
    
    def _calculate_countdown(self, data):
        """Calculate countdown to an event"""
        event_date_str = self._val(data, 'event_date', '')
        event_name = self._val(data, 'event_name', '') or str(_('Event'))
        if not event_date_str:
            return {'success': False, 'error': str(_('Please provide an event date.'))}
        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        today = date.today()
        if event_date < today:
            return {'success': False, 'error': str(_('Event date must be in the future.'))}
        delta = event_date - today
        total_days = delta.days
        rd = relativedelta(event_date, today)
        total_weeks = total_days // 7
        total_months = rd.years * 12 + rd.months
        total_hours = total_days * 24
        total_minutes = total_hours * 60
        chart_data = self._prepare_days_breakdown_chart(total_days, total_weeks, total_months, rd.years)
        return {
            'success': True,
            'calc_type': 'countdown',
            'event_date': str(event_date),
            'event_name': event_name,
            'today': str(today),
            'total_days': total_days,
            'formatted': str(_('{days} days until {event}')).format(days=total_days, event=event_name),
            'breakdown': {
                'years': rd.years,
                'months': rd.months,
                'days': rd.days,
                'weeks': total_weeks,
                'hours': total_hours,
                'minutes': total_minutes
            },
            'step_by_step': self._prepare_countdown_steps(today, event_date, event_name, total_days),
            'chart_data': chart_data,
        }
    
    def _calculate_business_days(self, start_date, end_date):
        """Calculate business days manually (excluding weekends)"""
        business_days = 0
        current = start_date
        while current < end_date:
            if current.weekday() < 5:  # Monday to Friday
                business_days += 1
            current += timedelta(days=1)
        return business_days
    
    def _prepare_between_steps(self, start_date, end_date, total_days, business_days, rd):
        """Prepare step-by-step solution for days between"""
        steps = []
        steps.append(_('Step 1: Identify the dates'))
        steps.append(_('Start Date: {date}').format(date=start_date.strftime('%B %d, %Y')))
        steps.append(_('End Date: {date}').format(date=end_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate total days'))
        steps.append(_('Formula: End Date - Start Date'))
        steps.append(_('Total Days = {days}').format(days=total_days))
        steps.append('')
        steps.append(_('Step 3: Break down into other units'))
        steps.append(_('Weeks = Total Days ÷ 7 = {weeks}').format(weeks=total_days // 7))
        steps.append(_('Months = Years × 12 + Months = {months}').format(months=rd.years * 12 + rd.months))
        steps.append(_('Hours = Days × 24 = {hours}').format(hours=total_days * 24))
        steps.append('')
        steps.append(_('Step 4: Calculate business days'))
        steps.append(_('Business Days (excluding weekends) = {days}').format(days=business_days))
        return steps
    
    def _prepare_since_steps(self, past_date, today, total_days):
        """Prepare step-by-step for days since"""
        steps = []
        steps.append(_('Step 1: Identify the dates'))
        steps.append(_('Past Date: {date}').format(date=past_date.strftime('%B %d, %Y')))
        steps.append(_('Today: {date}').format(date=today.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the difference'))
        steps.append(_('Days Since = Today - Past Date'))
        steps.append(_('Days Since = {days} days').format(days=total_days))
        return steps
    
    def _prepare_until_steps(self, today, future_date, total_days):
        """Prepare step-by-step for days until"""
        steps = []
        steps.append(_('Step 1: Identify the dates'))
        steps.append(_('Today: {date}').format(date=today.strftime('%B %d, %Y')))
        steps.append(_('Future Date: {date}').format(date=future_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the difference'))
        steps.append(_('Days Until = Future Date - Today'))
        steps.append(_('Days Until = {days} days').format(days=total_days))
        return steps
    
    def _prepare_countdown_steps(self, today, event_date, event_name, total_days):
        """Prepare step-by-step for countdown"""
        steps = []
        steps.append(_('Step 1: Identify the event'))
        steps.append(_('Event: {name}').format(name=event_name))
        steps.append(_('Event Date: {date}').format(date=event_date.strftime('%B %d, %Y')))
        steps.append(_('Today: {date}').format(date=today.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate countdown'))
        steps.append(_('Countdown = Event Date - Today'))
        steps.append(_('Countdown = {days} days until {event}').format(days=total_days, event=event_name))
        return steps
    
    def _prepare_between_chart_data(self, total_days, total_weeks, total_months, business_days):
        """Prepare chart data for days between"""
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Days')), str(_('Weeks')), str(_('Months')), str(_('Business Days'))],
                'datasets': [{
                    'label': str(_('Time Units')),
                    'data': [total_days, total_weeks, total_months, business_days],
                    'backgroundColor': ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd'],
                    'borderRadius': 4,
                    'borderWidth': 0
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}},
                'scales': {
                    'x': {'grid': {'display': False}},
                    'y': {'beginAtZero': True, 'ticks': {'precision': 0}}
                }
            }
        }
        return {'days_chart': chart_config}

    def _prepare_days_breakdown_chart(self, total_days, total_weeks, total_months, years):
        """Prepare chart for since/until/countdown (days, weeks, months, years)."""
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Days')), str(_('Weeks')), str(_('Months')), str(_('Years'))],
                'datasets': [{
                    'label': str(_('Count')),
                    'data': [total_days, total_weeks, total_months, years],
                    'backgroundColor': ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd'],
                    'borderRadius': 4,
                    'borderWidth': 0
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}},
                'scales': {
                    'x': {'grid': {'display': False}},
                    'y': {'beginAtZero': True, 'ticks': {'precision': 0}}
                }
            }
        }
        return {'days_chart': chart_config}
