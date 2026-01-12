from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
from datetime import datetime


class SocialSecurityCalculator(View):
    """
    Class-based view for Social Security Calculator
    Estimates Social Security benefits based on earnings history and retirement age.
    """
    template_name = 'financial_calculators/social_security_calculator.html'
    
    # 2024 Social Security parameters
    FULL_RETIREMENT_AGES = {
        1943: (66, 0), 1944: (66, 0), 1945: (66, 0), 1946: (66, 0), 1947: (66, 0),
        1948: (66, 0), 1949: (66, 0), 1950: (66, 0), 1951: (66, 0), 1952: (66, 0),
        1953: (66, 0), 1954: (66, 0), 1955: (66, 2), 1956: (66, 4), 1957: (66, 6),
        1958: (66, 8), 1959: (66, 10), 1960: (67, 0)
    }
    
    # 2024 bend points for PIA calculation
    BEND_POINT_1 = 1174
    BEND_POINT_2 = 7078
    
    # Maximum taxable earnings 2024
    MAX_TAXABLE_EARNINGS = 168600
    
    def get(self, request):
        """Handle GET request"""
        current_year = datetime.now().year
        birth_years = list(range(current_year - 70, current_year - 20))
        context = {
            'calculator_name': 'Social Security Calculator',
            'birth_years': birth_years,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for Social Security calculations"""
        try:
            data = json.loads(request.body)
            
            birth_year = int(data.get('birth_year', 1960))
            birth_month = int(data.get('birth_month', 1))
            current_annual_earnings = float(str(data.get('current_annual_earnings', 50000)).replace(',', ''))
            years_worked = int(data.get('years_worked', 20))
            planned_retirement_age = int(data.get('planned_retirement_age', 67))
            
            # Validation
            current_year = datetime.now().year
            current_age = current_year - birth_year
            
            if current_age < 22 or current_age > 80:
                return JsonResponse({'success': False, 'error': 'Please enter a valid birth year.'}, status=400)
            if current_annual_earnings < 0:
                return JsonResponse({'success': False, 'error': 'Earnings cannot be negative.'}, status=400)
            if planned_retirement_age < 62 or planned_retirement_age > 70:
                return JsonResponse({'success': False, 'error': 'Retirement age must be between 62 and 70.'}, status=400)
            
            # Calculate Full Retirement Age
            fra_years, fra_months = self._get_full_retirement_age(birth_year)
            fra_total_months = fra_years * 12 + fra_months
            
            # Estimate Average Indexed Monthly Earnings (AIME)
            # Using simplified calculation based on current earnings
            aime = self._estimate_aime(current_annual_earnings, years_worked)
            
            # Calculate Primary Insurance Amount (PIA) at FRA
            pia = self._calculate_pia(aime)
            
            # Calculate benefits at different ages
            benefits = {}
            for age in range(62, 71):
                benefit = self._calculate_benefit_at_age(pia, age, fra_years, fra_months, birth_month)
                benefits[age] = {
                    'monthly': round(benefit, 2),
                    'annual': round(benefit * 12, 2),
                    'adjustment': self._get_adjustment_description(age, fra_years, fra_months)
                }
            
            # Calculate benefit at planned retirement age
            planned_benefit = benefits.get(planned_retirement_age, benefits[67])
            
            # Calculate lifetime benefits comparison (assuming life expectancy of 85)
            life_expectancy = 85
            lifetime_benefits = {}
            for age in [62, planned_retirement_age, 70]:
                if age <= 70:
                    years_collecting = max(0, life_expectancy - age)
                    total = benefits[age]['annual'] * years_collecting
                    lifetime_benefits[age] = {
                        'years_collecting': years_collecting,
                        'total': round(total, 2)
                    }
            
            # Break-even analysis (62 vs 70)
            if benefits[62]['monthly'] > 0:
                early_benefit = benefits[62]['monthly']
                delayed_benefit = benefits[70]['monthly']
                
                # Find break-even age
                # Early: collects from 62, Delayed: collects from 70
                # Break-even when total delayed catches up to total early
                # (70 - 62) * 12 * early_benefit = n * (delayed_benefit - early_benefit)
                months_head_start = (70 - 62) * 12
                monthly_difference = delayed_benefit - early_benefit
                
                if monthly_difference > 0:
                    months_to_breakeven = (months_head_start * early_benefit) / monthly_difference
                    breakeven_age = 70 + (months_to_breakeven / 12)
                else:
                    breakeven_age = None
            else:
                breakeven_age = None
            
            result = {
                'success': True,
                'birth_year': birth_year,
                'current_age': current_age,
                'full_retirement_age': {
                    'years': fra_years,
                    'months': fra_months,
                    'display': f"{fra_years} years, {fra_months} months" if fra_months > 0 else f"{fra_years} years"
                },
                'aime': round(aime, 2),
                'pia': round(pia, 2),
                'planned_retirement': {
                    'age': planned_retirement_age,
                    'monthly_benefit': planned_benefit['monthly'],
                    'annual_benefit': planned_benefit['annual'],
                    'adjustment': planned_benefit['adjustment']
                },
                'benefits_by_age': benefits,
                'lifetime_benefits': lifetime_benefits,
                'breakeven_age': round(breakeven_age, 1) if breakeven_age else None,
                'max_benefit_age': 70,
                'earliest_benefit_age': 62,
                'notes': [
                    'Benefits are estimates based on current earnings.',
                    'Actual benefits depend on your complete earnings history.',
                    f'Maximum taxable earnings in 2024: ${self.MAX_TAXABLE_EARNINGS:,}',
                    'Benefits are adjusted annually for inflation (COLA).'
                ]
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def _get_full_retirement_age(self, birth_year):
        """Get full retirement age based on birth year"""
        if birth_year <= 1937:
            return (65, 0)
        elif birth_year >= 1960:
            return (67, 0)
        else:
            return self.FULL_RETIREMENT_AGES.get(birth_year, (67, 0))
    
    def _estimate_aime(self, current_earnings, years_worked):
        """Estimate Average Indexed Monthly Earnings"""
        # Simplified estimation using current earnings
        # Real calculation uses highest 35 years of indexed earnings
        
        # Cap earnings at maximum taxable
        capped_earnings = min(current_earnings, self.MAX_TAXABLE_EARNINGS)
        
        # Use years worked (max 35) for calculation
        years_used = min(years_worked, 35)
        
        # Estimate total indexed earnings (simplified)
        total_earnings = capped_earnings * years_used
        
        # AIME = total earnings / (35 years * 12 months)
        aime = total_earnings / (35 * 12)
        
        return aime
    
    def _calculate_pia(self, aime):
        """Calculate Primary Insurance Amount using bend points"""
        if aime <= self.BEND_POINT_1:
            pia = aime * 0.90
        elif aime <= self.BEND_POINT_2:
            pia = (self.BEND_POINT_1 * 0.90) + ((aime - self.BEND_POINT_1) * 0.32)
        else:
            pia = (self.BEND_POINT_1 * 0.90) + ((self.BEND_POINT_2 - self.BEND_POINT_1) * 0.32) + ((aime - self.BEND_POINT_2) * 0.15)
        
        return pia
    
    def _calculate_benefit_at_age(self, pia, retirement_age, fra_years, fra_months, birth_month):
        """Calculate benefit amount based on retirement age"""
        fra_in_months = fra_years * 12 + fra_months
        retirement_in_months = retirement_age * 12
        
        # Calculate months difference from FRA
        months_diff = retirement_in_months - fra_in_months
        
        if months_diff == 0:
            # Retiring at FRA
            return pia
        elif months_diff < 0:
            # Early retirement - reduction
            months_early = abs(months_diff)
            
            # First 36 months: 5/9 of 1% per month = 6.67% per year
            # Beyond 36 months: 5/12 of 1% per month = 5% per year
            if months_early <= 36:
                reduction = months_early * (5/9) / 100
            else:
                reduction = (36 * (5/9) / 100) + ((months_early - 36) * (5/12) / 100)
            
            return pia * (1 - reduction)
        else:
            # Delayed retirement - credits
            # 8% per year (2/3 of 1% per month) for years after FRA up to age 70
            months_after = min(months_diff, (70 * 12) - fra_in_months)
            increase = months_after * (2/3) / 100
            
            return pia * (1 + increase)
    
    def _get_adjustment_description(self, age, fra_years, fra_months):
        """Get description of benefit adjustment"""
        fra_in_months = fra_years * 12 + fra_months
        retirement_in_months = age * 12
        months_diff = retirement_in_months - fra_in_months
        
        if months_diff == 0:
            return "Full retirement benefit (100%)"
        elif months_diff < 0:
            years_early = abs(months_diff) / 12
            return f"Reduced {years_early:.1f} years early"
        else:
            years_delayed = months_diff / 12
            return f"Increased {years_delayed:.1f} years delayed"
