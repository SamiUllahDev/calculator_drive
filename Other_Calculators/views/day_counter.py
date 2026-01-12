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
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Day Counter',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'between')
            
            if calc_type == 'between':
                return self._calculate_days_between(data)
            elif calc_type == 'since':
                return self._calculate_days_since(data)
            elif calc_type == 'until':
                return self._calculate_days_until(data)
            elif calc_type == 'countdown':
                return self._calculate_countdown(data)
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
    
    def _calculate_days_between(self, data):
        """Calculate days between two dates"""
        try:
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            
            if not start_date_str or not end_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide both start and end dates.')
                }, status=400)
            
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            
            if start_date > end_date:
                return JsonResponse({
                    'success': False,
                    'error': _('Start date must be before or equal to end date.')
                }, status=400)
            
            # Calculate difference
            delta = end_date - start_date
            total_days = delta.days
            
            # Use relativedelta for precise calculation
            rd = relativedelta(end_date, start_date)
            
            # Calculate various units
            total_weeks = total_days // 7
            remaining_days = total_days % 7
            total_months = rd.years * 12 + rd.months
            total_hours = total_days * 24
            total_minutes = total_hours * 60
            total_seconds = total_minutes * 60
            
            # Business days (excluding weekends)
            business_days = self._calculate_business_days(start_date, end_date)
            
            # Prepare response
            response_data = {
                'success': True,
                'calc_type': 'between',
                'start_date': str(start_date),
                'end_date': str(end_date),
                'total_days': total_days,
                'formatted': _('{days} days').format(days=total_days),
                'breakdown': {
                    'years': rd.years,
                    'months': rd.months,
                    'days': rd.days,
                    'weeks': total_weeks,
                    'weeks_days': _('{weeks} weeks, {days} days').format(weeks=total_weeks, days=remaining_days),
                    'hours': total_hours,
                    'minutes': total_minutes,
                    'seconds': total_seconds,
                    'business_days': business_days
                },
                'step_by_step': self._prepare_between_steps(start_date, end_date, total_days, business_days, rd),
                'chart_data': self._prepare_between_chart_data(total_days, total_weeks, total_months, business_days),
            }
            
            return JsonResponse(response_data)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format. Please use YYYY-MM-DD format.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating days: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_days_since(self, data):
        """Calculate days since a date"""
        try:
            past_date_str = data.get('past_date')
            if not past_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a date.')
                }, status=400)
            
            past_date = datetime.strptime(past_date_str, '%Y-%m-%d').date()
            today = date.today()
            
            if past_date > today:
                return JsonResponse({
                    'success': False,
                    'error': _('Date must be in the past.')
                }, status=400)
            
            delta = today - past_date
            total_days = delta.days
            
            rd = relativedelta(today, past_date)
            total_weeks = total_days // 7
            total_months = rd.years * 12 + rd.months
            
            response_data = {
                'success': True,
                'calc_type': 'since',
                'past_date': str(past_date),
                'today': str(today),
                'total_days': total_days,
                'formatted': _('{days} days ago').format(days=total_days),
                'breakdown': {
                    'years': rd.years,
                    'months': rd.months,
                    'days': rd.days,
                    'weeks': total_weeks
                },
                'step_by_step': self._prepare_since_steps(past_date, today, total_days),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _calculate_days_until(self, data):
        """Calculate days until a date"""
        try:
            future_date_str = data.get('future_date')
            if not future_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a date.')
                }, status=400)
            
            future_date = datetime.strptime(future_date_str, '%Y-%m-%d').date()
            today = date.today()
            
            if future_date < today:
                return JsonResponse({
                    'success': False,
                    'error': _('Date must be in the future.')
                }, status=400)
            
            delta = future_date - today
            total_days = delta.days
            
            rd = relativedelta(future_date, today)
            total_weeks = total_days // 7
            total_months = rd.years * 12 + rd.months
            
            response_data = {
                'success': True,
                'calc_type': 'until',
                'future_date': str(future_date),
                'today': str(today),
                'total_days': total_days,
                'formatted': _('{days} days from now').format(days=total_days),
                'breakdown': {
                    'years': rd.years,
                    'months': rd.months,
                    'days': rd.days,
                    'weeks': total_weeks
                },
                'step_by_step': self._prepare_until_steps(today, future_date, total_days),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _calculate_countdown(self, data):
        """Calculate countdown to an event"""
        try:
            event_date_str = data.get('event_date')
            event_name = data.get('event_name', _('Event'))
            
            if not event_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide an event date.')
                }, status=400)
            
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
            today = date.today()
            
            if event_date < today:
                return JsonResponse({
                    'success': False,
                    'error': _('Event date must be in the future.')
                }, status=400)
            
            delta = event_date - today
            total_days = delta.days
            
            rd = relativedelta(event_date, today)
            total_weeks = total_days // 7
            total_months = rd.years * 12 + rd.months
            total_hours = total_days * 24
            total_minutes = total_hours * 60
            
            response_data = {
                'success': True,
                'calc_type': 'countdown',
                'event_date': str(event_date),
                'event_name': event_name,
                'today': str(today),
                'total_days': total_days,
                'formatted': _('{days} days until {event}').format(days=total_days, event=event_name),
                'breakdown': {
                    'years': rd.years,
                    'months': rd.months,
                    'days': rd.days,
                    'weeks': total_weeks,
                    'hours': total_hours,
                    'minutes': total_minutes
                },
                'step_by_step': self._prepare_countdown_steps(today, event_date, event_name, total_days),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
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
                'labels': [
                    _('Days'),
                    _('Weeks'),
                    _('Months'),
                    _('Business Days')
                ],
                'datasets': [{
                    'label': _('Time Units'),
                    'data': [total_days, total_weeks, total_months, business_days],
                    'backgroundColor': [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(139, 92, 246, 0.8)'
                    ],
                    'borderColor': [
                        '#3b82f6',
                        '#10b981',
                        '#fbbf24',
                        '#8b5cf6'
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
                        'text': _('Days Breakdown')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }
        
        return {'days_chart': chart_config}
