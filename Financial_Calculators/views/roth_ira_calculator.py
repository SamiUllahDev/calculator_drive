from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class RothIraCalculator(View):
    """
    Class-based view for Roth IRA Calculator
    Calculates projected Roth IRA balance with tax-free growth and retirement projections.
    """
    template_name = 'financial_calculators/roth_ira_calculator.html'
    
    # 2024 IRS Contribution Limits (same as Traditional IRA)
    CONTRIBUTION_LIMIT_2024 = 7000
    CATCH_UP_LIMIT_2024 = 1000  # For age 50+
    
    # Income limits for Roth IRA contributions (2024) - Single filers
    SINGLE_FULL_CONTRIBUTION_LIMIT = 146000
    SINGLE_PARTIAL_CONTRIBUTION_LIMIT = 161000
    
    # Income limits for Roth IRA contributions (2024) - Married filing jointly
    MARRIED_FULL_CONTRIBUTION_LIMIT = 230000
    MARRIED_PARTIAL_CONTRIBUTION_LIMIT = 240000
    
    def get(self, request):
        """Handle GET request - render the calculator form"""
        context = {
            'calculator_name': 'Roth IRA Calculator',
            'contribution_limit': self.CONTRIBUTION_LIMIT_2024,
            'catch_up_limit': self.CATCH_UP_LIMIT_2024,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Get input values
            current_age = self._get_int(data, 'current_age', 30)
            retirement_age = self._get_int(data, 'retirement_age', 65)
            current_balance = self._get_float(data, 'current_balance', 0)
            annual_contribution = self._get_float(data, 'annual_contribution', 7000)
            annual_return = self._get_float(data, 'annual_return', 7) / 100
            current_tax_rate = self._get_float(data, 'current_tax_rate', 22) / 100
            retirement_tax_rate = self._get_float(data, 'retirement_tax_rate', 25) / 100
            include_catch_up = data.get('include_catch_up', True)
            annual_income = self._get_float(data, 'annual_income', 60000)
            filing_status = data.get('filing_status', 'single')
            
            # Validate inputs
            errors = self._validate_inputs(
                current_age, retirement_age, annual_contribution, annual_return
            )
            if errors:
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            # Calculate projections
            result = self._calculate_roth_ira_projection(
                current_age=current_age,
                retirement_age=retirement_age,
                current_balance=current_balance,
                annual_contribution=annual_contribution,
                annual_return=annual_return,
                current_tax_rate=current_tax_rate,
                retirement_tax_rate=retirement_tax_rate,
                include_catch_up=include_catch_up,
                annual_income=annual_income,
                filing_status=filing_status
            )
            
            return JsonResponse({'success': True, **result})
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'errors': ['Invalid JSON data']
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            }, status=500)
    
    def _get_float(self, data, key, default=0.0):
        """Safely extract float value from data"""
        try:
            value = data.get(key, default)
            return float(value) if value not in [None, ''] else default
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely extract integer value from data"""
        try:
            value = data.get(key, default)
            return int(float(value)) if value not in [None, ''] else default
        except (ValueError, TypeError):
            return default
    
    def _validate_inputs(self, current_age, retirement_age, annual_contribution, annual_return):
        """Validate calculator inputs"""
        errors = []
        
        if current_age < 18 or current_age > 100:
            errors.append('Current age must be between 18 and 100')
        if retirement_age < current_age:
            errors.append('Retirement age must be greater than current age')
        if retirement_age > 100:
            errors.append('Retirement age must be 100 or less')
        if annual_contribution < 0:
            errors.append('Annual contribution must be 0 or greater')
        if annual_return < -0.5 or annual_return > 0.5:
            errors.append('Annual return must be between -50% and 50%')
        
        return errors
    
    def _calculate_contribution_limit(self, annual_income, filing_status, base_limit):
        """Calculate how much can be contributed based on income limits"""
        if filing_status == 'single':
            if annual_income <= self.SINGLE_FULL_CONTRIBUTION_LIMIT:
                return base_limit
            elif annual_income >= self.SINGLE_PARTIAL_CONTRIBUTION_LIMIT:
                return 0
            else:
                # Partial contribution allowed
                range_size = self.SINGLE_PARTIAL_CONTRIBUTION_LIMIT - self.SINGLE_FULL_CONTRIBUTION_LIMIT
                amount_over = annual_income - self.SINGLE_FULL_CONTRIBUTION_LIMIT
                reduction = (amount_over / range_size) * base_limit
                return max(0, base_limit - reduction)
        else:  # married
            if annual_income <= self.MARRIED_FULL_CONTRIBUTION_LIMIT:
                return base_limit
            elif annual_income >= self.MARRIED_PARTIAL_CONTRIBUTION_LIMIT:
                return 0
            else:
                range_size = self.MARRIED_PARTIAL_CONTRIBUTION_LIMIT - self.MARRIED_FULL_CONTRIBUTION_LIMIT
                amount_over = annual_income - self.MARRIED_FULL_CONTRIBUTION_LIMIT
                reduction = (amount_over / range_size) * base_limit
                return max(0, base_limit - reduction)
    
    def _calculate_roth_ira_projection(self, current_age, retirement_age, current_balance,
                                        annual_contribution, annual_return, current_tax_rate,
                                        retirement_tax_rate, include_catch_up, annual_income,
                                        filing_status):
        """Calculate Roth IRA projections year by year"""
        
        years_to_retirement = retirement_age - current_age
        balance = current_balance
        
        # Track totals
        total_contributions = 0
        total_investment_gains = 0
        
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
            base_limit = self.CONTRIBUTION_LIMIT_2024
            if include_catch_up and age >= 50:
                base_limit += self.CATCH_UP_LIMIT_2024
            
            # Apply income-based contribution limit
            max_contribution = self._calculate_contribution_limit(
                annual_income, filing_status, base_limit
            )
            
            # Apply contribution (capped at income-based limit)
            contribution = min(annual_contribution, max_contribution)
            
            # Add contribution to balance
            balance += contribution
            
            # Calculate investment gains
            mid_year_balance = year_start_balance + contribution / 2
            investment_gain = mid_year_balance * annual_return
            balance += investment_gain
            
            # Update totals
            total_contributions += contribution
            total_investment_gains += investment_gain
            
            # Store yearly data
            yearly_breakdown.append({
                'year': year,
                'age': age,
                'contribution': round(contribution, 2),
                'investment_gain': round(investment_gain, 2),
                'year_end_balance': round(balance, 2)
            })
            
            # Chart data
            chart_data['labels'].append(f'Age {age}')
            chart_data['contributions'].append(round(total_contributions, 2))
            chart_data['gains'].append(round(total_investment_gains, 2))
            chart_data['balances'].append(round(balance, 2))
        
        # Roth IRA: All withdrawals are tax-free (after age 59½ and 5-year rule)
        # So the balance IS the after-tax value
        after_tax_balance = balance
        
        # Calculate tax-free monthly retirement income (4% rule)
        monthly_income = (balance * 0.04) / 12
        
        # Calculate tax savings on growth
        # With Roth, you pay taxes now but growth is tax-free
        tax_free_gains = total_investment_gains  # This growth would be taxed in a traditional account
        
        # Compare with Traditional IRA (tax now vs tax later)
        traditional_balance = self._calculate_traditional_comparison(
            current_balance, annual_contribution, annual_return,
            current_tax_rate, retirement_tax_rate, years_to_retirement
        )
        roth_advantage = after_tax_balance - traditional_balance
        
        # Check eligibility status
        base_limit = self.CONTRIBUTION_LIMIT_2024
        allowed_contribution = self._calculate_contribution_limit(
            annual_income, filing_status, base_limit
        )
        eligibility_percent = (allowed_contribution / base_limit) * 100 if base_limit > 0 else 0
        
        return {
            'projected_balance': round(balance, 2),
            'tax_free_balance': round(after_tax_balance, 2),
            'total_contributions': round(total_contributions, 2),
            'total_investment_gains': round(total_investment_gains, 2),
            'tax_free_gains': round(tax_free_gains, 2),
            'years_to_retirement': years_to_retirement,
            'monthly_income': round(monthly_income, 2),
            'traditional_comparison': round(traditional_balance, 2),
            'roth_advantage': round(roth_advantage, 2),
            'eligibility_percent': round(eligibility_percent, 1),
            'max_allowed_contribution': round(allowed_contribution, 2),
            'chart_data': chart_data,
            'yearly_breakdown': yearly_breakdown[:10] + yearly_breakdown[-5:] if len(yearly_breakdown) > 15 else yearly_breakdown,
            'full_breakdown_available': len(yearly_breakdown) > 15
        }
    
    def _calculate_traditional_comparison(self, current_balance, annual_contribution,
                                           annual_return, current_tax_rate, 
                                           retirement_tax_rate, years):
        """Calculate what after-tax balance would be with Traditional IRA for comparison"""
        balance = current_balance
        
        for _ in range(years):
            balance += annual_contribution
            balance *= (1 + annual_return)
        
        # Traditional IRA: withdrawals are taxed
        after_tax_balance = balance * (1 - retirement_tax_rate)
        
        return after_tax_balance
