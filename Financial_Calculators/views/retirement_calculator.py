from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RetirementCalculator(View):
    """
    Professional Retirement Calculator with comprehensive features.
    
    Features:
    - Retirement savings projection
    - Multiple income sources (401k, IRA, Social Security)
    - Inflation-adjusted withdrawals
    - Retirement readiness score
    - Withdrawal strategy analysis
    - Year-by-year breakdown
    """
    template_name = 'financial_calculators/retirement_calculator.html'
    
    # Validation limits
    MIN_AGE = 18
    MAX_AGE = 100
    MAX_SAVINGS = 100000000
    MAX_RATE = 30
    
    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Retirement Calculator'),
            'page_title': _('Retirement Calculator - Plan Your Retirement Savings'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)

            # Get inputs
            current_age = self._get_int(data, 'current_age', 0)
            retirement_age = self._get_int(data, 'retirement_age', 0)
            life_expectancy = self._get_int(data, 'life_expectancy', 90)
            
            current_savings = self._get_float(data, 'current_savings', 0)
            monthly_contribution = self._get_float(data, 'monthly_contribution', 0)
            employer_match = self._get_float(data, 'employer_match', 0)
            employer_match_limit = self._get_float(data, 'employer_match_limit', 0)
            
            pre_retirement_return = self._get_float(data, 'pre_retirement_return', 7)
            post_retirement_return = self._get_float(data, 'post_retirement_return', 5)
            inflation_rate = self._get_float(data, 'inflation_rate', 3)
            
            desired_income = self._get_float(data, 'desired_income', 0)
            social_security = self._get_float(data, 'social_security', 0)
            other_income = self._get_float(data, 'other_income', 0)
            
            # Validation
            errors = []

            if current_age < self.MIN_AGE or current_age > self.MAX_AGE:
                errors.append(str(_('Current age must be between %(min)s and %(max)s.') % {'min': self.MIN_AGE, 'max': self.MAX_AGE}))

            if retirement_age <= current_age:
                errors.append(str(_('Retirement age must be greater than current age.')))
            elif retirement_age > self.MAX_AGE:
                errors.append(str(_('Retirement age cannot exceed %(max)s.') % {'max': self.MAX_AGE}))

            if life_expectancy <= retirement_age:
                errors.append(str(_('Life expectancy must be greater than retirement age.')))
            elif life_expectancy > 120:
                errors.append(str(_('Life expectancy cannot exceed 120.')))

            if current_savings < 0:
                errors.append(str(_('Current savings cannot be negative.')))
            elif current_savings > self.MAX_SAVINGS:
                errors.append(str(_('Current savings cannot exceed $%(max)s.') % {'max': f'{self.MAX_SAVINGS:,}'}))

            if monthly_contribution < 0:
                errors.append(str(_('Monthly contribution cannot be negative.')))

            if pre_retirement_return < -20 or pre_retirement_return > self.MAX_RATE:
                errors.append(str(_('Pre-retirement return must be between -20%% and %(max)s%%.') % {'max': self.MAX_RATE}))

            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate
            result = self._calculate_retirement(
                current_age, retirement_age, life_expectancy,
                current_savings, monthly_contribution, employer_match, employer_match_limit,
                pre_retirement_return, post_retirement_return, inflation_rate,
                desired_income, social_security, other_income
            )
            
            return JsonResponse({
                'success': True,
                **result
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': str(_('Invalid input: %(detail)s') % {'detail': str(e)})}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)
    
    def _get_float(self, data, key, default=0):
        """Safely get float (handles list, strips % and commas)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely get int value."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '').replace('$', '')))
        except (ValueError, TypeError):
            return default
    
    def _calculate_retirement(self, current_age, retirement_age, life_expectancy,
                             current_savings, monthly_contribution, employer_match,
                             employer_match_limit, pre_return, post_return, inflation,
                             desired_income, social_security, other_income):
        """Calculate comprehensive retirement projection"""
        
        years_to_retirement = retirement_age - current_age
        retirement_years = life_expectancy - retirement_age
        
        # Calculate employer match contribution
        annual_contribution = monthly_contribution * 12
        match_contribution = min(
            annual_contribution * (employer_match / 100),
            employer_match_limit
        ) if employer_match_limit > 0 else annual_contribution * (employer_match / 100)
        
        total_monthly_contribution = monthly_contribution + (match_contribution / 12)
        
        # Phase 1: Accumulation (pre-retirement)
        accumulation_breakdown = []
        balance = current_savings
        total_contributions = current_savings
        total_gains = 0
        
        chart_labels = [f'Age {current_age}']
        chart_balance = [round(balance, 2)]
        
        monthly_rate = pre_return / 100 / 12
        
        for year in range(1, years_to_retirement + 1):
            age = current_age + year
            year_start = balance
            year_contributions = 0
            year_gains = 0
            
            for month in range(12):
                # Add contribution
                balance += total_monthly_contribution
                year_contributions += total_monthly_contribution
                total_contributions += total_monthly_contribution
                
                # Add gains
                gains = balance * monthly_rate
                balance += gains
                year_gains += gains
                total_gains += gains
            
            accumulation_breakdown.append({
                'year': year,
                'age': age,
                'contributions': round(year_contributions, 2),
                'gains': round(year_gains, 2),
                'balance': round(balance, 2),
            })
            
            chart_labels.append(f'Age {age}')
            chart_balance.append(round(balance, 2))
        
        retirement_balance = balance
        
        # Calculate retirement income needs
        # Adjust desired income for inflation at retirement
        inflation_factor = np.power(1 + inflation / 100, years_to_retirement)
        adjusted_desired_income = desired_income * inflation_factor if desired_income > 0 else 0
        
        # Monthly income sources
        monthly_social_security = social_security  # Assume already annual, convert to monthly
        monthly_other = other_income / 12 if other_income > 0 else 0
        monthly_needed = adjusted_desired_income / 12 if adjusted_desired_income > 0 else 0
        
        # Calculate sustainable withdrawal
        monthly_gap = max(0, monthly_needed - monthly_social_security - monthly_other)
        annual_withdrawal_needed = monthly_gap * 12
        
        # Calculate 4% rule suggestion
        safe_withdrawal_rate = 0.04
        sustainable_withdrawal = retirement_balance * safe_withdrawal_rate
        
        # Phase 2: Distribution (retirement)
        distribution_breakdown = []
        post_monthly_rate = post_return / 100 / 12
        inflation_monthly = inflation / 100 / 12
        
        withdrawal_balance = retirement_balance
        annual_withdrawal = annual_withdrawal_needed if annual_withdrawal_needed > 0 else sustainable_withdrawal
        monthly_withdrawal = annual_withdrawal / 12
        
        total_withdrawn = 0
        years_funds_last = 0
        
        for year in range(1, retirement_years + 1):
            age = retirement_age + year
            year_start = withdrawal_balance
            year_withdrawals = 0
            year_gains = 0
            
            if withdrawal_balance > 0:
                for month in range(12):
                    # Withdraw (inflation-adjusted)
                    inflation_adj = np.power(1 + inflation / 100, year - 1)
                    adjusted_withdrawal = monthly_withdrawal * inflation_adj
                    
                    actual_withdrawal = min(adjusted_withdrawal, withdrawal_balance)
                    withdrawal_balance -= actual_withdrawal
                    year_withdrawals += actual_withdrawal
                    total_withdrawn += actual_withdrawal
                    
                    # Add gains on remaining balance
                    if withdrawal_balance > 0:
                        gains = withdrawal_balance * post_monthly_rate
                        withdrawal_balance += gains
                        year_gains += gains
                
                years_funds_last = year
            
            distribution_breakdown.append({
                'year': year,
                'age': age,
                'withdrawals': round(year_withdrawals, 2),
                'gains': round(year_gains, 2),
                'balance': round(max(0, withdrawal_balance), 2),
            })
            
            if year <= 30:  # Limit chart to 30 years in retirement
                chart_labels.append(f'Age {age}')
                chart_balance.append(round(max(0, withdrawal_balance), 2))
        
        # Calculate retirement readiness score
        if desired_income > 0:
            coverage_ratio = (sustainable_withdrawal + (social_security * 12) + other_income) / adjusted_desired_income
            readiness_score = min(100, coverage_ratio * 100)
        else:
            readiness_score = 100 if retirement_balance > 0 else 0
        
        # Determine status
        if years_funds_last >= retirement_years:
            status = 'on_track'
            status_message = 'Your retirement savings are projected to last throughout retirement.'
        elif years_funds_last >= retirement_years * 0.75:
            status = 'needs_attention'
            status_message = f'Your savings may run out around age {retirement_age + years_funds_last}. Consider increasing contributions.'
        else:
            status = 'at_risk'
            status_message = f'Your savings may only last until age {retirement_age + years_funds_last}. Significant adjustments recommended.'
        
        # Calculate shortfall or surplus
        needed_at_retirement = (annual_withdrawal_needed / safe_withdrawal_rate) if annual_withdrawal_needed > 0 else 0
        surplus_shortfall = retirement_balance - needed_at_retirement if needed_at_retirement > 0 else retirement_balance
        
        return {
            'summary': {
                'retirement_balance': round(retirement_balance, 2),
                'total_contributions': round(total_contributions, 2),
                'total_gains': round(total_gains, 2),
                'years_to_retirement': years_to_retirement,
                'monthly_contribution_total': round(total_monthly_contribution, 2),
            },
            'retirement_income': {
                'sustainable_withdrawal': round(sustainable_withdrawal, 2),
                'monthly_sustainable': round(sustainable_withdrawal / 12, 2),
                'social_security_annual': round(social_security * 12, 2),
                'other_income_annual': round(other_income, 2),
                'total_annual_income': round(sustainable_withdrawal + (social_security * 12) + other_income, 2),
            },
            'analysis': {
                'readiness_score': round(readiness_score, 1),
                'years_funds_last': years_funds_last,
                'status': status,
                'status_message': str(status_message),
                'surplus_shortfall': round(surplus_shortfall, 2),
            },
            'accumulation_breakdown': accumulation_breakdown,
            'distribution_breakdown': distribution_breakdown[:30],
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
            },
            'input': {
                'current_age': current_age,
                'retirement_age': retirement_age,
                'life_expectancy': life_expectancy,
            }
        }
