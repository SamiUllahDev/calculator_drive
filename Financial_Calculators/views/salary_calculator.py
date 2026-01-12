from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class SalaryCalculator(View):
    """
    Class-based view for Salary Calculator
    Converts between hourly, daily, weekly, biweekly, monthly, and annual salary.
    """
    template_name = 'financial_calculators/salary_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Salary Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for salary calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'convert')
            
            if calc_type == 'convert':
                # Convert salary between different pay periods
                amount = float(str(data.get('amount', 0)).replace(',', ''))
                period = data.get('period', 'annual')  # hourly, daily, weekly, biweekly, monthly, annual
                hours_per_week = float(str(data.get('hours_per_week', 40)).replace(',', ''))
                weeks_per_year = float(str(data.get('weeks_per_year', 52)).replace(',', ''))
                
                if amount < 0:
                    return JsonResponse({'success': False, 'error': 'Salary cannot be negative.'}, status=400)
                if hours_per_week <= 0 or hours_per_week > 168:
                    return JsonResponse({'success': False, 'error': 'Hours per week must be between 1 and 168.'}, status=400)
                if weeks_per_year <= 0 or weeks_per_year > 52:
                    return JsonResponse({'success': False, 'error': 'Weeks per year must be between 1 and 52.'}, status=400)
                
                # Calculate annual salary first
                if period == 'hourly':
                    annual = amount * hours_per_week * weeks_per_year
                elif period == 'daily':
                    daily_hours = hours_per_week / 5  # Assuming 5-day work week
                    annual = amount * 5 * weeks_per_year
                elif period == 'weekly':
                    annual = amount * weeks_per_year
                elif period == 'biweekly':
                    annual = amount * (weeks_per_year / 2)
                elif period == 'semimonthly':
                    annual = amount * 24
                elif period == 'monthly':
                    annual = amount * 12
                else:  # annual
                    annual = amount
                
                # Calculate all periods from annual
                hourly = annual / (hours_per_week * weeks_per_year)
                daily = annual / (5 * weeks_per_year)  # Assuming 5-day work week
                weekly = annual / weeks_per_year
                biweekly = annual / (weeks_per_year / 2)
                semimonthly = annual / 24
                monthly = annual / 12
                
                result = {
                    'success': True,
                    'calc_type': 'convert',
                    'input': {
                        'amount': round(amount, 2),
                        'period': period,
                        'hours_per_week': hours_per_week,
                        'weeks_per_year': weeks_per_year
                    },
                    'conversions': {
                        'hourly': round(hourly, 2),
                        'daily': round(daily, 2),
                        'weekly': round(weekly, 2),
                        'biweekly': round(biweekly, 2),
                        'semimonthly': round(semimonthly, 2),
                        'monthly': round(monthly, 2),
                        'annual': round(annual, 2)
                    },
                    'formatted': {
                        'hourly': f'${hourly:,.2f}/hour',
                        'daily': f'${daily:,.2f}/day',
                        'weekly': f'${weekly:,.2f}/week',
                        'biweekly': f'${biweekly:,.2f}/2 weeks',
                        'semimonthly': f'${semimonthly:,.2f}/semi-month',
                        'monthly': f'${monthly:,.2f}/month',
                        'annual': f'${annual:,.2f}/year'
                    }
                }
                
            elif calc_type == 'raise':
                # Calculate salary after raise
                current_salary = float(str(data.get('current_salary', 0)).replace(',', ''))
                raise_type = data.get('raise_type', 'percentage')  # percentage or amount
                raise_value = float(str(data.get('raise_value', 0)).replace(',', ''))
                
                if current_salary < 0:
                    return JsonResponse({'success': False, 'error': 'Current salary cannot be negative.'}, status=400)
                
                if raise_type == 'percentage':
                    raise_amount = current_salary * (raise_value / 100)
                else:
                    raise_amount = raise_value
                
                new_salary = current_salary + raise_amount
                percentage_increase = (raise_amount / current_salary * 100) if current_salary > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': 'raise',
                    'current_salary': round(current_salary, 2),
                    'raise_amount': round(raise_amount, 2),
                    'new_salary': round(new_salary, 2),
                    'percentage_increase': round(percentage_increase, 2),
                    'monthly_increase': round(raise_amount / 12, 2),
                    'biweekly_increase': round(raise_amount / 26, 2)
                }
                
            elif calc_type == 'compare':
                # Compare two job offers
                offer1_salary = float(str(data.get('offer1_salary', 0)).replace(',', ''))
                offer1_period = data.get('offer1_period', 'annual')
                offer2_salary = float(str(data.get('offer2_salary', 0)).replace(',', ''))
                offer2_period = data.get('offer2_period', 'annual')
                hours_per_week = float(str(data.get('hours_per_week', 40)).replace(',', ''))
                
                # Convert both to annual
                def to_annual(amount, period, hrs):
                    if period == 'hourly':
                        return amount * hrs * 52
                    elif period == 'weekly':
                        return amount * 52
                    elif period == 'biweekly':
                        return amount * 26
                    elif period == 'monthly':
                        return amount * 12
                    return amount
                
                offer1_annual = to_annual(offer1_salary, offer1_period, hours_per_week)
                offer2_annual = to_annual(offer2_salary, offer2_period, hours_per_week)
                
                difference = offer1_annual - offer2_annual
                percentage_diff = (difference / offer2_annual * 100) if offer2_annual > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': 'compare',
                    'offer1': {
                        'salary': round(offer1_salary, 2),
                        'period': offer1_period,
                        'annual': round(offer1_annual, 2),
                        'monthly': round(offer1_annual / 12, 2),
                        'hourly': round(offer1_annual / (hours_per_week * 52), 2)
                    },
                    'offer2': {
                        'salary': round(offer2_salary, 2),
                        'period': offer2_period,
                        'annual': round(offer2_annual, 2),
                        'monthly': round(offer2_annual / 12, 2),
                        'hourly': round(offer2_annual / (hours_per_week * 52), 2)
                    },
                    'comparison': {
                        'difference': round(difference, 2),
                        'percentage_difference': round(percentage_diff, 2),
                        'monthly_difference': round(difference / 12, 2),
                        'better_offer': 'Offer 1' if difference > 0 else ('Offer 2' if difference < 0 else 'Equal')
                    }
                }
                
            elif calc_type == 'overtime':
                # Calculate overtime pay
                hourly_rate = float(str(data.get('hourly_rate', 0)).replace(',', ''))
                regular_hours = float(str(data.get('regular_hours', 40)).replace(',', ''))
                overtime_hours = float(str(data.get('overtime_hours', 0)).replace(',', ''))
                overtime_multiplier = float(str(data.get('overtime_multiplier', 1.5)).replace(',', ''))
                
                if hourly_rate < 0:
                    return JsonResponse({'success': False, 'error': 'Hourly rate cannot be negative.'}, status=400)
                
                regular_pay = hourly_rate * regular_hours
                overtime_rate = hourly_rate * overtime_multiplier
                overtime_pay = overtime_rate * overtime_hours
                total_pay = regular_pay + overtime_pay
                
                # Weekly/monthly projections
                weekly_with_ot = total_pay
                monthly_with_ot = weekly_with_ot * 4.33
                annual_with_ot = weekly_with_ot * 52
                
                result = {
                    'success': True,
                    'calc_type': 'overtime',
                    'hourly_rate': round(hourly_rate, 2),
                    'overtime_rate': round(overtime_rate, 2),
                    'regular_hours': regular_hours,
                    'overtime_hours': overtime_hours,
                    'regular_pay': round(regular_pay, 2),
                    'overtime_pay': round(overtime_pay, 2),
                    'total_weekly_pay': round(total_pay, 2),
                    'projections': {
                        'monthly': round(monthly_with_ot, 2),
                        'annual': round(annual_with_ot, 2)
                    }
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
