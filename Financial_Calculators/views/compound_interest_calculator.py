from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CompoundInterestCalculator(View):
    """
    Professional Compound Interest Calculator with comprehensive features.
    
    Features:
    - Multiple compounding frequencies
    - Regular contributions (monthly, annual)
    - Growth chart visualization
    - Comparison scenarios
    - Breakdown by year
    """
    template_name = 'financial_calculators/compound_interest_calculator.html'
    
    # Validation limits
    MIN_PRINCIPAL = 0
    MAX_PRINCIPAL = 1000000000
    MIN_RATE = 0
    MAX_RATE = 100
    MIN_TIME = 1
    MAX_TIME = 100
    MAX_CONTRIBUTION = 10000000
    
    COMPOUND_FREQUENCIES = {
        'annually': 1,
        'semiannually': 2,
        'quarterly': 4,
        'monthly': 12,
        'daily': 365,
    }
    
    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Compound Interest Calculator'),
            'page_title': _('Compound Interest Calculator - Free Investment Growth Calculator'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            principal = self._get_float(data, 'principal', 0)
            annual_rate = self._get_float(data, 'interest_rate', 0)
            time_years = self._get_float(data, 'time_years', 0)
            compound_frequency = data.get('compound_frequency', 'monthly')
            if isinstance(compound_frequency, list):
                compound_frequency = compound_frequency[0] if compound_frequency else 'monthly'
            contribution_amount = self._get_float(data, 'contribution_amount', 0)
            contribution_frequency = data.get('contribution_frequency', 'monthly')
            if isinstance(contribution_frequency, list):
                contribution_frequency = contribution_frequency[0] if contribution_frequency else 'monthly'
            contribution_timing = data.get('contribution_timing', 'end')
            if isinstance(contribution_timing, list):
                contribution_timing = contribution_timing[0] if contribution_timing else 'end'

            errors = []

            if principal < self.MIN_PRINCIPAL:
                errors.append(_('Principal cannot be negative.'))
            elif principal > self.MAX_PRINCIPAL:
                errors.append(_('Principal cannot exceed %(max)s.') % {'max': f'${self.MAX_PRINCIPAL:,}'})

            if annual_rate < self.MIN_RATE:
                errors.append(_('Interest rate cannot be negative.'))
            elif annual_rate > self.MAX_RATE:
                errors.append(_('Interest rate cannot exceed %(max)s%%.') % {'max': self.MAX_RATE})

            if time_years < self.MIN_TIME:
                errors.append(_('Time period must be at least %(min)s year.') % {'min': self.MIN_TIME})
            elif time_years > self.MAX_TIME:
                errors.append(_('Time period cannot exceed %(max)s years.') % {'max': self.MAX_TIME})

            if contribution_amount < 0:
                errors.append(_('Contribution amount cannot be negative.'))
            elif contribution_amount > self.MAX_CONTRIBUTION:
                errors.append(_('Contribution amount cannot exceed %(max)s.') % {'max': f'${self.MAX_CONTRIBUTION:,}'})

            if compound_frequency not in self.COMPOUND_FREQUENCIES:
                errors.append(_('Invalid compound frequency.'))

            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate
            n = self.COMPOUND_FREQUENCIES[compound_frequency]
            r = annual_rate / 100
            t = time_years
            
            # Convert contribution to monthly equivalent for calculations
            if contribution_frequency == 'annually':
                monthly_contribution = contribution_amount / 12
            else:
                monthly_contribution = contribution_amount
            
            # Calculate with detailed breakdown
            yearly_breakdown = []
            current_balance = principal
            total_contributions = 0
            total_interest = 0
            
            chart_labels = ['Year 0']
            chart_balance = [principal]
            chart_contributions = [principal]
            chart_interest = [0]
            
            # Calculate year by year
            for year in range(1, int(t) + 1):
                start_balance = current_balance
                year_contributions = 0
                year_interest = 0
                
                # Calculate each compounding period within the year
                periods_per_year = n
                rate_per_period = r / n
                
                for period in range(periods_per_year):
                    # Add contribution at beginning if specified
                    if contribution_timing == 'beginning':
                        period_contribution = monthly_contribution * (12 / periods_per_year)
                        current_balance += period_contribution
                        year_contributions += period_contribution
                    
                    # Calculate interest for this period
                    period_interest = current_balance * rate_per_period
                    current_balance += period_interest
                    year_interest += period_interest
                    
                    # Add contribution at end if specified
                    if contribution_timing == 'end':
                        period_contribution = monthly_contribution * (12 / periods_per_year)
                        current_balance += period_contribution
                        year_contributions += period_contribution
                
                total_contributions += year_contributions
                total_interest += year_interest
                
                yearly_breakdown.append({
                    'year': year,
                    'start_balance': round(start_balance, 2),
                    'contributions': round(year_contributions, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(current_balance, 2),
                })
                
                chart_labels.append(f'Year {year}')
                chart_balance.append(round(current_balance, 2))
                chart_contributions.append(round(principal + total_contributions, 2))
                chart_interest.append(round(total_interest, 2))
            
            # Handle partial years
            remaining_time = t - int(t)
            if remaining_time > 0:
                start_balance = current_balance
                remaining_months = remaining_time * 12
                periods = int(n * remaining_time)
                
                year_contributions = 0
                year_interest = 0
                rate_per_period = r / n
                
                for period in range(max(1, periods)):
                    if contribution_timing == 'beginning':
                        period_contribution = monthly_contribution * (12 / n)
                        current_balance += period_contribution
                        year_contributions += period_contribution
                    
                    period_interest = current_balance * rate_per_period * (remaining_time if periods < 1 else 1)
                    current_balance += period_interest
                    year_interest += period_interest
                    
                    if contribution_timing == 'end':
                        period_contribution = monthly_contribution * (12 / n)
                        current_balance += period_contribution
                        year_contributions += period_contribution
                
                total_contributions += year_contributions
                total_interest += year_interest
                
                yearly_breakdown.append({
                    'year': f'{int(t) + 1} (partial)',
                    'start_balance': round(start_balance, 2),
                    'contributions': round(year_contributions, 2),
                    'interest': round(year_interest, 2),
                    'end_balance': round(current_balance, 2),
                })
            
            # Final values
            final_balance = current_balance
            total_deposits = principal + total_contributions
            
            # Calculate without contributions for comparison
            final_without_contrib = principal * np.power(1 + r/n, n * t)
            
            # Prepare response
            response_data = {
                'success': True,
                'input': {
                    'principal': round(principal, 2),
                    'interest_rate': annual_rate,
                    'time_years': t,
                    'compound_frequency': compound_frequency,
                    'contribution_amount': round(contribution_amount, 2),
                    'contribution_frequency': contribution_frequency,
                },
                'results': {
                    'final_balance': round(final_balance, 2),
                    'total_principal': round(principal, 2),
                    'total_contributions': round(total_contributions, 2),
                    'total_interest': round(total_interest, 2),
                    'total_deposits': round(total_deposits, 2),
                },
                'comparison': {
                    'with_contributions': round(final_balance, 2),
                    'without_contributions': round(final_without_contrib, 2),
                    'contribution_benefit': round(final_balance - final_without_contrib, 2),
                },
                'yearly_breakdown': yearly_breakdown,
                'chart_data': {
                    'labels': chart_labels,
                    'balance': chart_balance,
                    'contributions': chart_contributions,
                    'interest': chart_interest,
                },
            }
            
            return JsonResponse(response_data)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)

    def _get_float(self, data, key, default=0):
        """Safely get float value from data (handles list from form POST)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default
