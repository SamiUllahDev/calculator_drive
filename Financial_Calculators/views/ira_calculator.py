from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IraCalculator(View):
    """
    Class-based view for Traditional IRA Calculator
    Calculates projected IRA balance with tax benefits and retirement projections.
    """
    template_name = 'financial_calculators/ira_calculator.html'

    CONTRIBUTION_LIMIT_2024 = 7000
    CATCH_UP_LIMIT_2024 = 1000

    SINGLE_FULL_DEDUCTION_LIMIT = 77000
    SINGLE_PARTIAL_DEDUCTION_LIMIT = 87000
    MARRIED_FULL_DEDUCTION_LIMIT = 123000
    MARRIED_PARTIAL_DEDUCTION_LIMIT = 143000

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
            'calculator_name': _('Traditional IRA Calculator'),
            'page_title': _('Traditional IRA Calculator - Retirement Tax Savings'),
            'contribution_limit': self.CONTRIBUTION_LIMIT_2024,
            'catch_up_limit': self.CATCH_UP_LIMIT_2024,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = self._get_data(request)

            current_age = self._get_int(data, 'current_age', 30)
            retirement_age = self._get_int(data, 'retirement_age', 65)
            current_balance = self._get_float(data, 'current_balance', 0)
            annual_contribution = self._get_float(data, 'annual_contribution', 7000)
            annual_return = self._get_float(data, 'annual_return', 7) / 100
            current_tax_rate = self._get_float(data, 'current_tax_rate', 22) / 100
            retirement_tax_rate = self._get_float(data, 'retirement_tax_rate', 15) / 100
            annual_income = self._get_float(data, 'annual_income', 60000)
            filing_status = data.get('filing_status', 'single')
            if isinstance(filing_status, list):
                filing_status = filing_status[0] if filing_status else 'single'

            include_catch_up = data.get('include_catch_up')
            if isinstance(include_catch_up, str):
                include_catch_up = include_catch_up.lower() in ('true', '1', 'yes')
            elif include_catch_up is None:
                include_catch_up = True

            has_workplace_plan = data.get('has_workplace_plan')
            if isinstance(has_workplace_plan, str):
                has_workplace_plan = has_workplace_plan.lower() in ('true', '1', 'yes')
            elif has_workplace_plan is None:
                has_workplace_plan = False

            errors = self._validate_inputs(
                current_age, retirement_age, annual_contribution, annual_return
            )
            if errors:
                return JsonResponse({'success': False, 'error': str(errors[0])}, status=400)

            result = self._calculate_ira_projection(
                current_age=current_age,
                retirement_age=retirement_age,
                current_balance=current_balance,
                annual_contribution=annual_contribution,
                annual_return=annual_return,
                current_tax_rate=current_tax_rate,
                retirement_tax_rate=retirement_tax_rate,
                include_catch_up=include_catch_up,
                has_workplace_plan=has_workplace_plan,
                annual_income=annual_income,
                filing_status=filing_status
            )

            return JsonResponse({'success': True, **result})

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': str(_('Invalid input: %(detail)s') % {'detail': str(e)})}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _get_float(self, data, key, default=0.0):
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

    def _validate_inputs(self, current_age, retirement_age, annual_contribution, annual_return):
        """Validate calculator inputs"""
        errors = []

        if current_age < 18 or current_age > 100:
            errors.append(str(_('Current age must be between 18 and 100.')))
        if retirement_age < current_age:
            errors.append(str(_('Retirement age must be greater than current age.')))
        if retirement_age > 100:
            errors.append(str(_('Retirement age must be 100 or less.')))
        if annual_contribution < 0:
            errors.append(str(_('Annual contribution must be 0 or greater.')))
        if annual_return < -0.5 or annual_return > 0.5:
            errors.append(str(_('Annual return must be between -50%% and 50%%.')))

        return errors
    
    def _calculate_deduction_percentage(self, annual_income, filing_status, has_workplace_plan):
        """Calculate what percentage of IRA contribution is tax-deductible"""
        if not has_workplace_plan:
            return 1.0  # Full deduction if no workplace plan
        
        if filing_status == 'single':
            if annual_income <= self.SINGLE_FULL_DEDUCTION_LIMIT:
                return 1.0
            elif annual_income >= self.SINGLE_PARTIAL_DEDUCTION_LIMIT:
                return 0.0
            else:
                # Partial deduction
                range_size = self.SINGLE_PARTIAL_DEDUCTION_LIMIT - self.SINGLE_FULL_DEDUCTION_LIMIT
                amount_over = annual_income - self.SINGLE_FULL_DEDUCTION_LIMIT
                return 1.0 - (amount_over / range_size)
        else:  # married
            if annual_income <= self.MARRIED_FULL_DEDUCTION_LIMIT:
                return 1.0
            elif annual_income >= self.MARRIED_PARTIAL_DEDUCTION_LIMIT:
                return 0.0
            else:
                range_size = self.MARRIED_PARTIAL_DEDUCTION_LIMIT - self.MARRIED_FULL_DEDUCTION_LIMIT
                amount_over = annual_income - self.MARRIED_FULL_DEDUCTION_LIMIT
                return 1.0 - (amount_over / range_size)
    
    def _calculate_ira_projection(self, current_age, retirement_age, current_balance,
                                   annual_contribution, annual_return, current_tax_rate,
                                   retirement_tax_rate, include_catch_up, has_workplace_plan,
                                   annual_income, filing_status):
        """Calculate Traditional IRA projections year by year"""
        
        years_to_retirement = retirement_age - current_age
        balance = current_balance
        
        # Track totals
        total_contributions = 0
        total_tax_savings = 0
        total_investment_gains = 0
        
        # Calculate deduction percentage
        deduction_pct = self._calculate_deduction_percentage(
            annual_income, filing_status, has_workplace_plan
        )
        
        # Year-by-year breakdown
        yearly_breakdown = []
        chart_data = {
            'labels': [],
            'contributions': [],
            'gains': [],
            'balances': []
        }
        
        for year in range(1, years_to_retirement + 1):
            age = current_age + year
            year_start_balance = balance
            
            # Calculate contribution limit with catch-up
            contribution_limit = self.CONTRIBUTION_LIMIT_2024
            if include_catch_up and age >= 50:
                contribution_limit += self.CATCH_UP_LIMIT_2024
            
            # Apply contribution (capped at IRS limit)
            contribution = min(annual_contribution, contribution_limit)
            
            # Calculate tax savings from deductible contribution
            deductible_amount = contribution * deduction_pct
            tax_savings = deductible_amount * current_tax_rate
            
            # Add contribution to balance
            balance += contribution
            
            # Calculate investment gains
            mid_year_balance = year_start_balance + contribution / 2
            investment_gain = mid_year_balance * annual_return
            balance += investment_gain
            
            # Update totals
            total_contributions += contribution
            total_tax_savings += tax_savings
            total_investment_gains += investment_gain
            
            # Store yearly data
            yearly_breakdown.append({
                'year': year,
                'age': age,
                'contribution': round(contribution, 2),
                'tax_savings': round(tax_savings, 2),
                'investment_gain': round(investment_gain, 2),
                'year_end_balance': round(balance, 2)
            })
            
            # Chart data
            chart_data['labels'].append(f'Age {age}')
            chart_data['contributions'].append(round(total_contributions, 2))
            chart_data['gains'].append(round(total_investment_gains, 2))
            chart_data['balances'].append(round(balance, 2))
        
        # Calculate after-tax value at retirement
        # Traditional IRA: all withdrawals are taxed
        after_tax_balance = balance * (1 - retirement_tax_rate)
        
        # Calculate monthly retirement income (4% rule)
        monthly_income_pretax = (balance * 0.04) / 12
        monthly_income_aftertax = (after_tax_balance * 0.04) / 12
        
        # Tax arbitrage benefit (saving at high rate, withdrawing at low rate)
        if current_tax_rate > retirement_tax_rate:
            tax_arbitrage = total_contributions * (current_tax_rate - retirement_tax_rate)
        else:
            tax_arbitrage = 0
        
        # Compare with taxable account
        taxable_balance = self._calculate_taxable_comparison(
            current_balance, annual_contribution, annual_return,
            current_tax_rate, years_to_retirement
        )
        ira_advantage = balance - taxable_balance
        
        return {
            'projected_balance': round(balance, 2),
            'after_tax_balance': round(after_tax_balance, 2),
            'total_contributions': round(total_contributions, 2),
            'total_tax_savings': round(total_tax_savings, 2),
            'total_investment_gains': round(total_investment_gains, 2),
            'years_to_retirement': years_to_retirement,
            'monthly_income_pretax': round(monthly_income_pretax, 2),
            'monthly_income_aftertax': round(monthly_income_aftertax, 2),
            'deduction_percentage': round(deduction_pct * 100, 1),
            'tax_arbitrage': round(tax_arbitrage, 2),
            'taxable_comparison': round(taxable_balance, 2),
            'ira_advantage': round(ira_advantage, 2),
            'chart_data': chart_data,
            'yearly_breakdown': yearly_breakdown[:10] + yearly_breakdown[-5:] if len(yearly_breakdown) > 15 else yearly_breakdown,
            'full_breakdown_available': len(yearly_breakdown) > 15
        }
    
    def _calculate_taxable_comparison(self, current_balance, annual_contribution,
                                       annual_return, tax_rate, years):
        """Calculate what balance would be in a taxable account for comparison"""
        balance = current_balance
        
        # After-tax contribution (no tax deduction)
        after_tax_contribution = annual_contribution * (1 - tax_rate)
        
        # After-tax return (assuming long-term capital gains rate of 15%)
        cap_gains_rate = 0.15
        after_tax_return = annual_return * (1 - cap_gains_rate)
        
        for _ in range(years):
            balance += after_tax_contribution
            balance *= (1 + after_tax_return)
        
        return balance
