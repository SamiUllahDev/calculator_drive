from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
from datetime import date


class RmdCalculator(View):
    """
    Class-based view for Required Minimum Distribution (RMD) Calculator
    Calculates RMDs based on IRS Uniform Lifetime Table and SECURE Act 2.0 rules.
    """
    template_name = 'financial_calculators/rmd_calculator.html'
    
    # IRS Uniform Lifetime Table (2024) - used for most beneficiaries
    # Maps age to distribution period (life expectancy factor)
    UNIFORM_LIFETIME_TABLE = {
        72: 27.4, 73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0,
        79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8, 85: 16.0,
        86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2, 91: 11.5, 92: 10.8,
        93: 10.1, 94: 9.5, 95: 8.9, 96: 8.4, 97: 7.8, 98: 7.3, 99: 6.8,
        100: 6.4, 101: 6.0, 102: 5.6, 103: 5.2, 104: 4.9, 105: 4.6, 106: 4.3,
        107: 4.1, 108: 3.9, 109: 3.7, 110: 3.5, 111: 3.4, 112: 3.3, 113: 3.1,
        114: 3.0, 115: 2.9, 116: 2.8, 117: 2.7, 118: 2.5, 119: 2.3, 120: 2.0
    }
    
    # SECURE Act 2.0 RMD starting ages
    RMD_START_AGE_2023 = 73  # For those born 1951-1959
    RMD_START_AGE_2033 = 75  # For those born 1960 or later
    
    def get(self, request):
        """Handle GET request - render the calculator form"""
        context = {
            'calculator_name': 'RMD Calculator',
            'current_year': date.today().year,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Get input values
            birth_year = self._get_int(data, 'birth_year', 1955)
            account_balance = self._get_float(data, 'account_balance', 500000)
            account_type = data.get('account_type', 'traditional_ira')
            spouse_age = self._get_int(data, 'spouse_age', 0)
            spouse_sole_beneficiary = data.get('spouse_sole_beneficiary', False)
            expected_return = self._get_float(data, 'expected_return', 5) / 100
            
            # Calculate current age
            current_year = date.today().year
            current_age = current_year - birth_year
            
            # Validate inputs
            errors = self._validate_inputs(birth_year, account_balance, current_age)
            if errors:
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            # Calculate RMD projections
            result = self._calculate_rmd_projection(
                birth_year=birth_year,
                current_age=current_age,
                account_balance=account_balance,
                account_type=account_type,
                spouse_age=spouse_age,
                spouse_sole_beneficiary=spouse_sole_beneficiary,
                expected_return=expected_return
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
    
    def _validate_inputs(self, birth_year, account_balance, current_age):
        """Validate calculator inputs"""
        errors = []
        
        current_year = date.today().year
        if birth_year < 1920 or birth_year > current_year - 18:
            errors.append('Please enter a valid birth year')
        if account_balance < 0:
            errors.append('Account balance must be 0 or greater')
        if current_age < 18 or current_age > 120:
            errors.append('Age must be between 18 and 120')
        
        return errors
    
    def _get_rmd_start_age(self, birth_year):
        """Determine RMD start age based on birth year per SECURE Act 2.0"""
        if birth_year <= 1950:
            return 72  # Already started RMDs under old rules
        elif birth_year <= 1959:
            return 73  # SECURE 2.0 for 1951-1959
        else:
            return 75  # SECURE 2.0 for 1960+
    
    def _get_distribution_period(self, age, spouse_age=0, spouse_sole_beneficiary=False):
        """Get the distribution period (life expectancy factor) for RMD calculation"""
        # If spouse is sole beneficiary and more than 10 years younger,
        # use Joint Life and Last Survivor table (not implemented here for simplicity)
        # Otherwise use Uniform Lifetime Table
        
        age = max(72, min(120, age))  # Clamp to table range
        return self.UNIFORM_LIFETIME_TABLE.get(age, 2.0)
    
    def _calculate_rmd_projection(self, birth_year, current_age, account_balance,
                                   account_type, spouse_age, spouse_sole_beneficiary,
                                   expected_return):
        """Calculate RMD projections year by year"""
        
        current_year = date.today().year
        rmd_start_age = self._get_rmd_start_age(birth_year)
        
        # Check if RMDs have started
        rmd_has_started = current_age >= rmd_start_age
        years_until_rmd = max(0, rmd_start_age - current_age)
        
        # Calculate current year RMD if applicable
        current_rmd = 0
        current_distribution_period = 0
        if rmd_has_started:
            current_distribution_period = self._get_distribution_period(
                current_age, spouse_age, spouse_sole_beneficiary
            )
            current_rmd = account_balance / current_distribution_period
        
        # Project RMDs for the next 20 years (or until account depleted)
        balance = account_balance
        yearly_breakdown = []
        chart_data = {
            'labels': [],
            'rmd_amounts': [],
            'balances': []
        }
        
        total_rmds = 0
        
        for year_offset in range(20):
            year = current_year + year_offset
            age = current_age + year_offset
            
            if age < rmd_start_age:
                # No RMD required yet
                balance *= (1 + expected_return)
                rmd = 0
                distribution_period = 0
            else:
                # Calculate RMD
                distribution_period = self._get_distribution_period(
                    age, spouse_age + year_offset if spouse_age else 0, 
                    spouse_sole_beneficiary
                )
                rmd = balance / distribution_period if distribution_period > 0 else 0
                
                # Apply RMD and growth
                balance -= rmd
                if balance > 0:
                    balance *= (1 + expected_return)
                else:
                    balance = 0
                
                total_rmds += rmd
            
            yearly_breakdown.append({
                'year': year,
                'age': age,
                'starting_balance': round(balance + rmd if rmd else balance / (1 + expected_return), 2),
                'distribution_period': round(distribution_period, 1),
                'rmd': round(rmd, 2),
                'ending_balance': round(balance, 2)
            })
            
            chart_data['labels'].append(f'{year}')
            chart_data['rmd_amounts'].append(round(rmd, 2))
            chart_data['balances'].append(round(balance, 2))
            
            if balance <= 0:
                break
        
        # Calculate tax impact estimate (assuming 22% bracket)
        estimated_tax_rate = 0.22
        current_rmd_tax = current_rmd * estimated_tax_rate
        
        # Monthly equivalent
        monthly_rmd = current_rmd / 12 if current_rmd > 0 else 0
        
        return {
            'current_age': current_age,
            'rmd_start_age': rmd_start_age,
            'rmd_has_started': rmd_has_started,
            'years_until_rmd': years_until_rmd,
            'account_balance': round(account_balance, 2),
            'current_rmd': round(current_rmd, 2),
            'monthly_rmd': round(monthly_rmd, 2),
            'distribution_period': round(current_distribution_period, 1),
            'current_rmd_tax': round(current_rmd_tax, 2),
            'total_projected_rmds': round(total_rmds, 2),
            'chart_data': chart_data,
            'yearly_breakdown': yearly_breakdown
        }
