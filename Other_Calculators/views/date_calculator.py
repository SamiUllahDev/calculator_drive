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


def _safe_format(msg_id, **kwargs):
    """
    Safely format a translatable string.
    
    Translators sometimes translate the {placeholder} names inside format
    strings (e.g. {date} → {التاريخ} in Arabic, {years} → {ans} in French).
    When .format() is called, Python raises KeyError because the translated
    placeholder name doesn't match the keyword argument.
    
    This helper tries the translated string first; on any KeyError / IndexError
    it falls back to formatting the original English msgid so the calculator
    still works in every language.
    """
    translated = _(msg_id)
    try:
        return str(translated).format(**kwargs)
    except (KeyError, IndexError, ValueError):
        try:
            return msg_id.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return str(translated)


class SafeJSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o) if o is not None else None


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DateCalculator(View):
    """
    Professional Date Calculator with Comprehensive Features
    
    This calculator provides date calculations with:
    - Date difference calculations (days, weeks, months, years between dates)
    - Add/subtract time from dates (years, months, weeks, days)
    - Days since/until calculations
    - Business days calculations
    - Age calculations
    - Weekday calculations
    
    Features:
    - Supports multiple calculation modes
    - Handles leap years correctly
    - Calculates business days (excluding weekends)
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/date_calculator.html'
    
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
        context = {'calculator_name': str(_('Date Calculator'))}
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
            calc_type = self._val(data, 'calc_type', 'difference')
            if calc_type == 'difference':
                result = self._calculate_difference(data)
            elif calc_type == 'add_subtract':
                result = self._calculate_add_subtract(data)
            elif calc_type == 'days_since':
                result = self._calculate_days_since(data)
            elif calc_type == 'days_until':
                result = self._calculate_days_until(data)
            elif calc_type == 'weekday':
                result = self._calculate_weekday(data)
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
            logger.exception("Date calculator failed: %s", e)
            from django.conf import settings
            err_msg = str(_('An error occurred during calculation.'))
            if getattr(settings, 'DEBUG', False):
                err_msg += ' [' + str(e).replace('"', "'") + ']'
            return HttpResponse(
                json.dumps({'success': False, 'error': err_msg}, cls=SafeJSONEncoder),
                content_type='application/json',
                status=500
            )
    
    def _calculate_difference(self, data):
        """Calculate difference between two dates"""
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
        rd = relativedelta(end_date, start_date)
        delta = end_date - start_date
        total_days = delta.days
        total_weeks = total_days // 7
        remaining_days = total_days % 7
        total_months = rd.years * 12 + rd.months
        total_hours = total_days * 24
        total_minutes = total_hours * 60
        total_seconds = total_minutes * 60
        business_days = self._calculate_business_days(start_date, end_date)
        return {
            'success': True,
            'calc_type': 'difference',
            'start_date': str(start_date),
            'end_date': str(end_date),
            'difference': {
                'years': rd.years,
                'months': rd.months,
                'days': rd.days,
                'formatted': _safe_format('{years} years, {months} months, {days} days',
                    years=rd.years, months=rd.months, days=rd.days
                )
            },
            'totals': {
                'days': total_days,
                'weeks': total_weeks,
                'weeks_days': _safe_format('{weeks} weeks, {days} days', weeks=total_weeks, days=remaining_days),
                'months': total_months,
                'hours': total_hours,
                'minutes': total_minutes,
                'seconds': total_seconds,
                'business_days': int(business_days)
            },
            'step_by_step': self._prepare_difference_steps(start_date, end_date, rd, total_days, business_days),
            'chart_data': self._prepare_difference_chart_data(total_days, total_weeks, total_months, business_days),
        }
    
    def _calculate_add_subtract(self, data):
        """Add or subtract time from a date"""
        base_date_str = self._val(data, 'base_date', '')
        if not base_date_str:
            return {'success': False, 'error': str(_('Please provide a base date.'))}
        try:
            years = int(self._val(data, 'years', 0) or 0)
            months = int(self._val(data, 'months', 0) or 0)
            weeks = int(self._val(data, 'weeks', 0) or 0)
            days = int(self._val(data, 'days', 0) or 0)
        except (ValueError, TypeError):
            return {'success': False, 'error': str(_('Time values must be whole numbers.'))}
        operation = self._val(data, 'operation', 'add')
        if years < 0 or months < 0 or weeks < 0 or days < 0:
            return {'success': False, 'error': str(_('Time values must be non-negative.'))}
        if years > 1000 or months > 12000 or weeks > 52000 or days > 365000:
            return {'success': False, 'error': str(_('Time values are too large. Please use smaller values.'))}
        try:
            base_date = datetime.strptime(base_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        delta = relativedelta(years=years, months=months, weeks=weeks, days=days)
        result_date = base_date + delta if operation == 'add' else base_date - delta
        if result_date.year < 1 or result_date.year > 9999:
            return {'success': False, 'error': str(_('Result date is out of valid range (1-9999 AD).'))}
        days_of_week = [
            str(_('Monday')), str(_('Tuesday')), str(_('Wednesday')), str(_('Thursday')),
            str(_('Friday')), str(_('Saturday')), str(_('Sunday'))
        ]
        month_names = [
            str(_('January')), str(_('February')), str(_('March')), str(_('April')), str(_('May')), str(_('June')),
            str(_('July')), str(_('August')), str(_('September')), str(_('October')), str(_('November')), str(_('December'))
        ]
        result_formatted = f"{month_names[result_date.month - 1]} {result_date.day}, {result_date.year}"
        return {
            'success': True,
            'calc_type': 'add_subtract',
            'base_date': str(base_date),
            'operation': operation,
            'added': {'years': years, 'months': months, 'weeks': weeks, 'days': days},
            'result_date': str(result_date),
            'result_formatted': result_formatted,
            'day_of_week': days_of_week[result_date.weekday()],
            'step_by_step': self._prepare_add_subtract_steps(base_date, result_date, operation, years, months, weeks, days),
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
        years = total_days // 365
        remaining_days = total_days % 365
        months = remaining_days // 30
        weeks = total_days // 7
        chart_data = self._prepare_days_chart_data(total_days, weeks, months, years)
        return {
            'success': True,
            'calc_type': 'days_since',
            'past_date': str(past_date),
            'today': str(today),
            'days_since': total_days,
            'formatted': _safe_format('{days} days ago', days=total_days),
            'breakdown': {'years': years, 'months': months, 'weeks': weeks, 'days': total_days},
            'step_by_step': self._prepare_days_since_steps(past_date, today, total_days),
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
        years = total_days // 365
        remaining_days = total_days % 365
        months = remaining_days // 30
        weeks = total_days // 7
        chart_data = self._prepare_days_chart_data(total_days, weeks, months, years)
        return {
            'success': True,
            'calc_type': 'days_until',
            'future_date': str(future_date),
            'today': str(today),
            'days_until': total_days,
            'formatted': _safe_format('{days} days from now', days=total_days),
            'breakdown': {'years': years, 'months': months, 'weeks': weeks, 'days': total_days},
            'step_by_step': self._prepare_days_until_steps(today, future_date, total_days),
            'chart_data': chart_data,
        }
    
    def _calculate_weekday(self, data):
        """Calculate what day of the week a date falls on"""
        target_date_str = self._val(data, 'target_date', '')
        if not target_date_str:
            return {'success': False, 'error': str(_('Please provide a date.'))}
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return {'success': False, 'error': str(_('Invalid date format. Please use YYYY-MM-DD format.'))}
        days_of_week = [
            str(_('Monday')), str(_('Tuesday')), str(_('Wednesday')), str(_('Thursday')),
            str(_('Friday')), str(_('Saturday')), str(_('Sunday'))
        ]
        month_names = [
            str(_('January')), str(_('February')), str(_('March')), str(_('April')), str(_('May')), str(_('June')),
            str(_('July')), str(_('August')), str(_('September')), str(_('October')), str(_('November')), str(_('December'))
        ]
        date_formatted = f"{month_names[target_date.month - 1]} {target_date.day}, {target_date.year}"
        return {
            'success': True,
            'calc_type': 'weekday',
            'target_date': str(target_date),
            'date_formatted': date_formatted,
            'day_of_week': days_of_week[target_date.weekday()],
            'step_by_step': self._prepare_weekday_steps(target_date, days_of_week[target_date.weekday()]),
        }
    
    def _calculate_business_days(self, start_date, end_date):
        """Calculate business days manually (fallback)"""
        business_days = 0
        current = start_date
        while current < end_date:
            if current.weekday() < 5:  # Monday to Friday
                business_days += 1
            current += timedelta(days=1)
        return business_days
    
    def _prepare_difference_steps(self, start_date, end_date, rd, total_days, business_days):
        """Prepare step-by-step solution for date difference"""
        steps = []
        steps.append(_('Step 1: Identify the dates'))
        steps.append(_safe_format('Start Date: {date}', date=start_date.strftime('%B %d, %Y')))
        steps.append(_safe_format('End Date: {date}', date=end_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the difference'))
        steps.append(_('Using relativedelta to get precise year, month, and day differences'))
        steps.append(_safe_format('Years: {years}', years=rd.years))
        steps.append(_safe_format('Months: {months}', months=rd.months))
        steps.append(_safe_format('Days: {days}', days=rd.days))
        steps.append('')
        steps.append(_('Step 3: Calculate total days'))
        steps.append(_('Formula: End Date - Start Date'))
        steps.append(_safe_format('Total Days = {days}', days=total_days))
        steps.append('')
        steps.append(_('Step 4: Convert to other units'))
        steps.append(_safe_format('Weeks = Total Days ÷ 7 = {weeks}', weeks=total_days // 7))
        steps.append(_safe_format('Months = Years × 12 + Months = {months}', months=rd.years * 12 + rd.months))
        steps.append(_safe_format('Hours = Days × 24 = {hours}', hours=total_days * 24))
        steps.append(_safe_format('Minutes = Hours × 60 = {minutes}', minutes=total_days * 24 * 60))
        steps.append('')
        steps.append(_('Step 5: Calculate business days'))
        steps.append(_safe_format('Business Days (excluding weekends) = {days}', days=business_days))
        return steps
    
    def _prepare_add_subtract_steps(self, base_date, result_date, operation, years, months, weeks, days):
        """Prepare step-by-step solution for add/subtract"""
        steps = []
        steps.append(_('Step 1: Identify the base date'))
        steps.append(_safe_format('Base Date: {date}', date=base_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Determine the operation'))
        steps.append(_safe_format('Operation: {op}', op=_('Add') if operation == 'add' else _('Subtract')))
        steps.append(_safe_format('Time to {op}: {years} years, {months} months, {weeks} weeks, {days} days',
            op=_('add') if operation == 'add' else _('subtract'),
            years=years, months=months, weeks=weeks, days=days
        ))
        steps.append('')
        steps.append(_('Step 3: Calculate the result'))
        if operation == 'add':
            steps.append(_('Result Date = Base Date + Time Period'))
        else:
            steps.append(_('Result Date = Base Date - Time Period'))
        steps.append(_safe_format('Result Date = {date}', date=result_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 4: Determine the day of week'))
        days_of_week = [
            _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
            _('Friday'), _('Saturday'), _('Sunday')
        ]
        steps.append(_safe_format('Day of Week: {day}', day=days_of_week[result_date.weekday()]))
        return steps
    
    def _prepare_days_since_steps(self, past_date, today, total_days):
        """Prepare step-by-step for days since"""
        steps = []
        steps.append(_('Step 1: Identify the dates'))
        steps.append(_safe_format('Past Date: {date}', date=past_date.strftime('%B %d, %Y')))
        steps.append(_safe_format('Today: {date}', date=today.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the difference'))
        steps.append(_('Days Since = Today - Past Date'))
        steps.append(_safe_format('Days Since = {days} days', days=total_days))
        return steps
    
    def _prepare_days_until_steps(self, today, future_date, total_days):
        """Prepare step-by-step for days until"""
        steps = []
        steps.append(_('Step 1: Identify the dates'))
        steps.append(_safe_format('Today: {date}', date=today.strftime('%B %d, %Y')))
        steps.append(_safe_format('Future Date: {date}', date=future_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the difference'))
        steps.append(_('Days Until = Future Date - Today'))
        steps.append(_safe_format('Days Until = {days} days', days=total_days))
        return steps
    
    def _prepare_weekday_steps(self, target_date, day_of_week):
        """Prepare step-by-step for weekday calculation"""
        steps = []
        steps.append(_('Step 1: Identify the date'))
        steps.append(_safe_format('Target Date: {date}', date=target_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the day of week'))
        steps.append(_('Using Python datetime.weekday() method'))
        steps.append(_safe_format('Day of Week: {day}', day=day_of_week))
        return steps
    
    def _prepare_difference_chart_data(self, total_days, total_weeks, total_months, business_days):
        """Prepare chart data for date difference"""
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
        return {'difference_chart': chart_config}

    def _prepare_days_chart_data(self, total_days, weeks, months, years):
        """Prepare chart for days since/until (days, weeks, months, years)."""
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [str(_('Days')), str(_('Weeks')), str(_('Months')), str(_('Years'))],
                'datasets': [{
                    'label': str(_('Count')),
                    'data': [total_days, weeks, months, years],
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

