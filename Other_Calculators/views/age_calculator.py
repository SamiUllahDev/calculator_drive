from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
from datetime import datetime, date
from dateutil.relativedelta import relativedelta


@method_decorator(ensure_csrf_cookie, name='dispatch')
class AgeCalculator(View):
    """
    Professional Age Calculator with Comprehensive Features
    
    This calculator provides precise age calculations with:
    - Multiple time unit conversions (years, months, weeks, days, hours, minutes, seconds)
    - Zodiac sign and Chinese zodiac determination
    - Generation classification
    - Life milestones tracking
    - Visual charts and graphs
    - Step-by-step calculation explanations
    - Life progress percentage
    
    Features:
    - Handles leap years correctly
    - Supports custom target dates
    - Provides detailed birth information
    - Interactive visualizations
    """
    template_name = 'other_calculators/age_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Age Calculator'),
            'features': [
                _('Precise age calculation in multiple time units'),
                _('Zodiac sign and Chinese zodiac identification'),
                _('Generation classification'),
                _('Life milestones tracking'),
                _('Interactive charts and visualizations'),
                _('Step-by-step calculation explanations'),
                _('Life progress percentage indicator')
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Parse birth date
            birth_year = int(data.get('birth_year', 2000))
            birth_month = int(data.get('birth_month', 1))
            birth_day = int(data.get('birth_day', 1))
            
            # Parse target date (default to today)
            target_year = int(data.get('target_year', datetime.now().year))
            target_month = int(data.get('target_month', datetime.now().month))
            target_day = int(data.get('target_day', datetime.now().day))
            
            # Validation
            try:
                birth_date = date(birth_year, birth_month, birth_day)
                target_date = date(target_year, target_month, target_day)
            except ValueError as e:
                return JsonResponse({'success': False, 'error': _('Invalid date. Please check your input.')}, status=400)
            
            if birth_date > target_date:
                return JsonResponse({'success': False, 'error': _('Birth date cannot be in the future relative to target date.')}, status=400)
            
            # Calculate age using relativedelta for precise calculation
            age = relativedelta(target_date, birth_date)
            
            # Calculate total days
            delta = target_date - birth_date
            total_days = int(delta.days)
            
            # Calculate various time units
            total_weeks = total_days // 7
            total_months = age.years * 12 + age.months
            total_hours = total_days * 24
            total_minutes = total_hours * 60
            total_seconds = total_minutes * 60
            
            # Next birthday calculation (handles leap years)
            try:
                this_year_birthday = date(target_date.year, birth_month, birth_day)
            except ValueError:
                # Handle leap year edge case (Feb 29)
                this_year_birthday = date(target_date.year, birth_month, 28)
            
            if this_year_birthday < target_date:
                try:
                    next_birthday = date(target_date.year + 1, birth_month, birth_day)
                except ValueError:
                    next_birthday = date(target_date.year + 1, birth_month, 28)
            else:
                next_birthday = this_year_birthday
            
            days_until_birthday = (next_birthday - target_date).days
            turning_age = age.years + 1
            
            # Day of week born
            days_of_week = [
                _('Monday'), _('Tuesday'), _('Wednesday'), _('Thursday'),
                _('Friday'), _('Saturday'), _('Sunday')
            ]
            birth_day_of_week = days_of_week[birth_date.weekday()]
            
            # Zodiac sign
            zodiac = self.get_zodiac_sign(birth_month, birth_day)
            
            # Chinese zodiac
            chinese_zodiac = self.get_chinese_zodiac(birth_year)
            
            # Generation
            generation = self.get_generation(birth_year)
            
            # Life milestones
            milestones = [
                {'age': 18, 'event': _('Legal Adult'), 'date': str(birth_date + relativedelta(years=18))},
                {'age': 21, 'event': _('Drinking Age (US)'), 'date': str(birth_date + relativedelta(years=21))},
                {'age': 25, 'event': _('Quarter Century'), 'date': str(birth_date + relativedelta(years=25))},
                {'age': 30, 'event': _('Turning 30'), 'date': str(birth_date + relativedelta(years=30))},
                {'age': 40, 'event': _('Turning 40'), 'date': str(birth_date + relativedelta(years=40))},
                {'age': 50, 'event': _('Half Century'), 'date': str(birth_date + relativedelta(years=50))},
                {'age': 60, 'event': _('Turning 60'), 'date': str(birth_date + relativedelta(years=60))},
                {'age': 65, 'event': _('Retirement Age'), 'date': str(birth_date + relativedelta(years=65))},
                {'age': 75, 'event': _('Three Quarters Century'), 'date': str(birth_date + relativedelta(years=75))},
                {'age': 100, 'event': _('Centenarian'), 'date': str(birth_date + relativedelta(years=100))},
            ]
            
            # Filter milestones
            upcoming_milestones = [m for m in milestones if m['age'] > age.years][:5]
            passed_milestones = [m for m in milestones if m['age'] <= age.years]
            
            # Calculate percentage of life (assuming 80 years average)
            life_percentage = min((age.years / 80) * 100, 100) if age.years < 80 else 100
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(birth_date, target_date, age, total_days, total_weeks, total_hours, total_minutes, total_seconds)
            
            # Prepare chart data
            chart_data = {}
            try:
                totals = {
                    'years': age.years,
                    'months': total_months,
                    'weeks': total_weeks,
                    'days': total_days
                }
                chart_data = self._prepare_chart_data(totals, age, life_percentage)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            result = {
                'success': True,
                'age': {
                    'years': age.years,
                    'months': age.months,
                    'days': age.days,
                    'formatted': str(_('{years} years, {months} months, {days} days').format(
                        years=age.years, months=age.months, days=age.days
                    ))
                },
                'totals': {
                    'years': age.years,
                    'months': total_months,
                    'weeks': total_weeks,
                    'days': total_days,
                    'hours': total_hours,
                    'minutes': total_minutes,
                    'seconds': total_seconds
                },
                'birth_info': {
                    'date': str(birth_date),
                    'day_of_week': birth_day_of_week,
                    'zodiac': zodiac,
                    'chinese_zodiac': chinese_zodiac,
                    'generation': generation
                },
                'next_birthday': {
                    'date': str(next_birthday),
                    'days_until': days_until_birthday,
                    'turning': turning_age
                },
                'milestones': {
                    'upcoming': upcoming_milestones,
                    'passed': passed_milestones[-3:] if passed_milestones else []
                },
                'life_percentage': round(life_percentage, 2),
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: {error}').format(error=str(e))}, status=400)
        except Exception as e:
            import traceback
            print(f"Age Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
    
    def get_zodiac_sign(self, month, day):
        """Determine zodiac sign from birth date"""
        zodiac_dates = [
            (1, 20, _('Capricorn')), (2, 19, _('Aquarius')), (3, 20, _('Pisces')),
            (4, 20, _('Aries')), (5, 21, _('Taurus')), (6, 21, _('Gemini')),
            (7, 22, _('Cancer')), (8, 23, _('Leo')), (9, 23, _('Virgo')),
            (10, 23, _('Libra')), (11, 22, _('Scorpio')), (12, 22, _('Sagittarius')),
            (12, 31, _('Capricorn'))
        ]
        
        for end_month, end_day, sign in zodiac_dates:
            if month < end_month or (month == end_month and day <= end_day):
                return str(sign)
        return str(_('Capricorn'))
    
    def get_chinese_zodiac(self, year):
        """Determine Chinese zodiac from birth year"""
        animals = [
            _('Rat'), _('Ox'), _('Tiger'), _('Rabbit'), _('Dragon'), _('Snake'),
            _('Horse'), _('Goat'), _('Monkey'), _('Rooster'), _('Dog'), _('Pig')
        ]
        return str(animals[(year - 1900) % 12])
    
    def get_generation(self, year):
        """Determine generation from birth year"""
        if year < 1946:
            return str(_('Silent Generation'))
        elif year < 1965:
            return str(_('Baby Boomer'))
        elif year < 1981:
            return str(_('Generation X'))
        elif year < 1997:
            return str(_('Millennial'))
        elif year < 2013:
            return str(_('Generation Z'))
        else:
            return str(_('Generation Alpha'))
    
    def _prepare_step_by_step(self, birth_date, target_date, age, total_days, total_weeks, total_hours, total_minutes, total_seconds):
        """Prepare step-by-step solution for age calculation"""
        steps = []
        
        steps.append(_("Step 1: Identify the Dates"))
        steps.append(_("  Birth Date: {date}").format(date=birth_date.strftime('%B %d, %Y')))
        steps.append(_("  Target Date: {date}").format(date=target_date.strftime('%B %d, %Y')))
        steps.append("")
        
        steps.append(_("Step 2: Calculate the Difference"))
        steps.append(_("  Total Days = Target Date - Birth Date"))
        steps.append(_("  Total Days = {days:,} days").format(days=total_days))
        steps.append("")
        
        steps.append(_("Step 3: Break Down into Time Units"))
        steps.append(_("  Years: {years} years").format(years=age.years))
        steps.append(_("  Months: {months} months (in addition to {years} years)").format(months=age.months, years=age.years))
        steps.append(_("  Days: {days} days (in addition to {years} years and {months} months)").format(
            days=age.days, years=age.years, months=age.months
        ))
        steps.append("")
        
        steps.append(_("Step 4: Calculate Total Time Units"))
        steps.append(_("  Total Months = (Years × 12) + Months = ({years} × 12) + {months} = {total:,} months").format(
            years=age.years, months=age.months, total=age.years * 12 + age.months
        ))
        steps.append(_("  Total Weeks = Total Days ÷ 7 = {days:,} ÷ 7 = {weeks:,} weeks").format(
            days=total_days, weeks=total_weeks
        ))
        steps.append(_("  Total Hours = Total Days × 24 = {days:,} × 24 = {hours:,} hours").format(
            days=total_days, hours=total_hours
        ))
        steps.append(_("  Total Minutes = Total Hours × 60 = {hours:,} × 60 = {minutes:,} minutes").format(
            hours=total_hours, minutes=total_minutes
        ))
        steps.append(_("  Total Seconds = Total Minutes × 60 = {minutes:,} × 60 = {seconds:,} seconds").format(
            minutes=total_minutes, seconds=total_seconds
        ))
        steps.append("")
        
        steps.append(_("Step 5: Final Result"))
        steps.append(_("  Age: {years} years, {months} months, {days} days").format(
            years=age.years, months=age.months, days=age.days
        ))
        
        return [str(step) for step in steps]
    
    def _prepare_chart_data(self, totals, age, life_percentage):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        try:
            # Time units comparison chart
            chart_data['time_units_chart'] = {
                'type': 'bar',
                'data': {
                    'labels': [str(_('Years')), str(_('Months')), str(_('Weeks')), str(_('Days'))],
                    'datasets': [{
                        'label': str(_('Total Units')),
                        'data': [
                            totals['years'],
                            totals['months'],
                            totals['weeks'],
                            totals['days']
                        ],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.6)',
                            'rgba(16, 185, 129, 0.6)',
                            'rgba(245, 158, 11, 0.6)',
                            'rgba(239, 68, 68, 0.6)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b',
                            '#ef4444'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'scales': {
                        'y': {
                            'beginAtZero': True
                        }
                    }
                }
            }
            
            # Age breakdown pie chart
            if age.years > 0 or age.months > 0 or age.days > 0:
                # Convert to days for proportional representation
                years_in_days = age.years * 365.25
                months_in_days = age.months * 30.44
                days_value = age.days
                total_approx = years_in_days + months_in_days + days_value
                
                if total_approx > 0:
                    chart_data['age_breakdown_chart'] = {
                        'type': 'doughnut',
                        'data': {
                            'labels': [str(_('Years')), str(_('Months')), str(_('Days'))],
                            'datasets': [{
                                'label': str(_('Age Breakdown')),
                                'data': [
                                    round((years_in_days / total_approx) * 100, 1),
                                    round((months_in_days / total_approx) * 100, 1),
                                    round((days_value / total_approx) * 100, 1)
                                ],
                                'backgroundColor': [
                                    'rgba(59, 130, 246, 0.8)',
                                    'rgba(16, 185, 129, 0.8)',
                                    'rgba(245, 158, 11, 0.8)'
                                ],
                                'borderColor': [
                                    '#3b82f6',
                                    '#10b981',
                                    '#f59e0b'
                                ],
                                'borderWidth': 2
                            }]
                        }
                    }
            
            # Life percentage gauge data
            chart_data['life_percentage'] = {
                'percentage': life_percentage,
                'remaining': max(0, 100 - life_percentage)
            }
            
        except Exception as e:
            import traceback
            print(f"Chart data preparation error: {traceback.format_exc()}")
            chart_data = {}
        
        return chart_data
