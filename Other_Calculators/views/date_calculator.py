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
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Date Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'difference')
            
            if calc_type == 'difference':
                return self._calculate_difference(data)
            elif calc_type == 'add_subtract':
                return self._calculate_add_subtract(data)
            elif calc_type == 'days_since':
                return self._calculate_days_since(data)
            elif calc_type == 'days_until':
                return self._calculate_days_until(data)
            elif calc_type == 'weekday':
                return self._calculate_weekday(data)
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
    
    def _calculate_difference(self, data):
        """Calculate difference between two dates"""
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
            
            # Use relativedelta for precise calculation
            rd = relativedelta(end_date, start_date)
            
            # Total days
            delta = end_date - start_date
            total_days = delta.days
            
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
                'calc_type': 'difference',
                'start_date': str(start_date),
                'end_date': str(end_date),
                'difference': {
                    'years': rd.years,
                    'months': rd.months,
                    'days': rd.days,
                    'formatted': _('{years} years, {months} months, {days} days').format(
                        years=rd.years, months=rd.months, days=rd.days
                    )
                },
                'totals': {
                    'days': total_days,
                    'weeks': total_weeks,
                    'weeks_days': _('{weeks} weeks, {days} days').format(weeks=total_weeks, days=remaining_days),
                    'months': total_months,
                    'hours': total_hours,
                    'minutes': total_minutes,
                    'seconds': total_seconds,
                    'business_days': int(business_days)
                },
                'step_by_step': self._prepare_difference_steps(start_date, end_date, rd, total_days, business_days),
                'chart_data': self._prepare_difference_chart_data(total_days, total_weeks, total_months, business_days),
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
                'error': _('Error calculating date difference: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_add_subtract(self, data):
        """Add or subtract time from a date"""
        try:
            base_date_str = data.get('base_date')
            years = int(data.get('years', 0))
            months = int(data.get('months', 0))
            weeks = int(data.get('weeks', 0))
            days = int(data.get('days', 0))
            operation = data.get('operation', 'add')
            
            if not base_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a base date.')
                }, status=400)
            
            # Validate inputs
            if years < 0 or months < 0 or weeks < 0 or days < 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Time values must be non-negative.')
                }, status=400)
            
            if years > 1000 or months > 12000 or weeks > 52000 or days > 365000:
                return JsonResponse({
                    'success': False,
                    'error': _('Time values are too large. Please use smaller values.')
                }, status=400)
            
            base_date = datetime.strptime(base_date_str, '%Y-%m-%d').date()
            
            delta = relativedelta(years=years, months=months, weeks=weeks, days=days)
            
            if operation == 'add':
                result_date = base_date + delta
            else:
                result_date = base_date - delta
            
            # Validate result date
            if result_date.year < 1 or result_date.year > 9999:
                return JsonResponse({
                    'success': False,
                    'error': _('Result date is out of valid range (1-9999 AD).')
                }, status=400)
            
            # Get day of week
            days_of_week = [
                _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
                _('Friday'), _('Saturday'), _('Sunday')
            ]
            day_of_week = days_of_week[result_date.weekday()]
            
            # Format date
            month_names = [
                _('January'), _('February'), _('March'), _('April'), _('May'), _('June'),
                _('July'), _('August'), _('September'), _('October'), _('November'), _('December')
            ]
            result_formatted = f"{month_names[result_date.month - 1]} {result_date.day}, {result_date.year}"
            
            response_data = {
                'success': True,
                'calc_type': 'add_subtract',
                'base_date': str(base_date),
                'operation': operation,
                'added': {
                    'years': years,
                    'months': months,
                    'weeks': weeks,
                    'days': days
                },
                'result_date': str(result_date),
                'result_formatted': result_formatted,
                'day_of_week': day_of_week,
                'step_by_step': self._prepare_add_subtract_steps(base_date, result_date, operation, years, months, weeks, days),
            }
            
            return JsonResponse(response_data)
            
        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': _('Invalid input: {error}').format(error=str(e))
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating date: {error}').format(error=str(e))
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
            
            years = total_days // 365
            remaining_days = total_days % 365
            months = remaining_days // 30
            weeks = total_days // 7
            
            response_data = {
                'success': True,
                'calc_type': 'days_since',
                'past_date': str(past_date),
                'today': str(today),
                'days_since': total_days,
                'formatted': _('{days} days ago').format(days=total_days),
                'breakdown': {
                    'years': years,
                    'months': months,
                    'weeks': weeks,
                    'days': total_days
                },
                'step_by_step': self._prepare_days_since_steps(past_date, today, total_days),
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
            
            years = total_days // 365
            remaining_days = total_days % 365
            months = remaining_days // 30
            weeks = total_days // 7
            
            response_data = {
                'success': True,
                'calc_type': 'days_until',
                'future_date': str(future_date),
                'today': str(today),
                'days_until': total_days,
                'formatted': _('{days} days from now').format(days=total_days),
                'breakdown': {
                    'years': years,
                    'months': months,
                    'weeks': weeks,
                    'days': total_days
                },
                'step_by_step': self._prepare_days_until_steps(today, future_date, total_days),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
    def _calculate_weekday(self, data):
        """Calculate what day of the week a date falls on"""
        try:
            target_date_str = data.get('target_date')
            if not target_date_str:
                return JsonResponse({
                    'success': False,
                    'error': _('Please provide a date.')
                }, status=400)
            
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            
            days_of_week = [
                _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
                _('Friday'), _('Saturday'), _('Sunday')
            ]
            day_of_week = days_of_week[target_date.weekday()]
            
            month_names = [
                _('January'), _('February'), _('March'), _('April'), _('May'), _('June'),
                _('July'), _('August'), _('September'), _('October'), _('November'), _('December')
            ]
            date_formatted = f"{month_names[target_date.month - 1]} {target_date.day}, {target_date.year}"
            
            response_data = {
                'success': True,
                'calc_type': 'weekday',
                'target_date': str(target_date),
                'date_formatted': date_formatted,
                'day_of_week': day_of_week,
                'step_by_step': self._prepare_weekday_steps(target_date, day_of_week),
            }
            
            return JsonResponse(response_data)
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid date format.')
            }, status=400)
    
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
        steps.append(_('Start Date: {date}').format(date=start_date.strftime('%B %d, %Y')))
        steps.append(_('End Date: {date}').format(date=end_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the difference'))
        steps.append(_('Using relativedelta to get precise year, month, and day differences'))
        steps.append(_('Years: {years}').format(years=rd.years))
        steps.append(_('Months: {months}').format(months=rd.months))
        steps.append(_('Days: {days}').format(days=rd.days))
        steps.append('')
        steps.append(_('Step 3: Calculate total days'))
        steps.append(_('Formula: End Date - Start Date'))
        steps.append(_('Total Days = {days}').format(days=total_days))
        steps.append('')
        steps.append(_('Step 4: Convert to other units'))
        steps.append(_('Weeks = Total Days ÷ 7 = {weeks}').format(weeks=total_days // 7))
        steps.append(_('Months = Years × 12 + Months = {months}').format(months=rd.years * 12 + rd.months))
        steps.append(_('Hours = Days × 24 = {hours}').format(hours=total_days * 24))
        steps.append(_('Minutes = Hours × 60 = {minutes}').format(minutes=total_days * 24 * 60))
        steps.append('')
        steps.append(_('Step 5: Calculate business days'))
        steps.append(_('Business Days (excluding weekends) = {days}').format(days=business_days))
        return steps
    
    def _prepare_add_subtract_steps(self, base_date, result_date, operation, years, months, weeks, days):
        """Prepare step-by-step solution for add/subtract"""
        steps = []
        steps.append(_('Step 1: Identify the base date'))
        steps.append(_('Base Date: {date}').format(date=base_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Determine the operation'))
        steps.append(_('Operation: {op}').format(op=_('Add') if operation == 'add' else _('Subtract')))
        steps.append(_('Time to {op}: {years} years, {months} months, {weeks} weeks, {days} days').format(
            op=_('add') if operation == 'add' else _('subtract'),
            years=years, months=months, weeks=weeks, days=days
        ))
        steps.append('')
        steps.append(_('Step 3: Calculate the result'))
        if operation == 'add':
            steps.append(_('Result Date = Base Date + Time Period'))
        else:
            steps.append(_('Result Date = Base Date - Time Period'))
        steps.append(_('Result Date = {date}').format(date=result_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 4: Determine the day of week'))
        days_of_week = [
            _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
            _('Friday'), _('Saturday'), _('Sunday')
        ]
        steps.append(_('Day of Week: {day}').format(day=days_of_week[result_date.weekday()]))
        return steps
    
    def _prepare_days_since_steps(self, past_date, today, total_days):
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
    
    def _prepare_days_until_steps(self, today, future_date, total_days):
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
    
    def _prepare_weekday_steps(self, target_date, day_of_week):
        """Prepare step-by-step for weekday calculation"""
        steps = []
        steps.append(_('Step 1: Identify the date'))
        steps.append(_('Target Date: {date}').format(date=target_date.strftime('%B %d, %Y')))
        steps.append('')
        steps.append(_('Step 2: Calculate the day of week'))
        steps.append(_('Using Python datetime.weekday() method'))
        steps.append(_('Day of Week: {day}').format(day=day_of_week))
        return steps
    
    def _prepare_difference_chart_data(self, total_days, total_weeks, total_months, business_days):
        """Prepare chart data for date difference"""
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
                        'text': _('Time Difference Breakdown')
                    }
                },
                'scales': {
                    'y': {
                        'beginAtZero': True
                    }
                }
            }
        }
        
        return {'difference_chart': chart_config}
