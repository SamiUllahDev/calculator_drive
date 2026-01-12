from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HouseAffordabilityCalculator(View):
    """
    Professional House Affordability Calculator with comprehensive features.
    
    Features:
    - Income-based affordability calculation
    - Debt-to-income ratio analysis
    - Monthly budget breakdown
    - Conservative vs aggressive scenarios
    - Including taxes, insurance, and PMI
    """
    template_name = 'financial_calculators/house_affordability_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'House Affordability Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get inputs
            annual_income = self._get_float(data, 'annual_income', 0)
            monthly_debts = self._get_float(data, 'monthly_debts', 0)
            down_payment = self._get_float(data, 'down_payment', 0)
            interest_rate = self._get_float(data, 'interest_rate', 6.5)
            loan_term = self._get_int(data, 'loan_term', 30)
            property_tax_rate = self._get_float(data, 'property_tax_rate', 1.2)
            insurance_rate = self._get_float(data, 'insurance_rate', 0.5)
            hoa_fees = self._get_float(data, 'hoa_fees', 0)
            
            # Validation
            errors = []
            
            if annual_income <= 0:
                errors.append('Annual income must be greater than 0.')
            elif annual_income > 10000000:
                errors.append('Annual income cannot exceed $10,000,000.')
            
            if monthly_debts < 0:
                errors.append('Monthly debts cannot be negative.')
            
            if down_payment < 0:
                errors.append('Down payment cannot be negative.')
            
            if interest_rate <= 0:
                errors.append('Interest rate must be greater than 0.')
            elif interest_rate > 20:
                errors.append('Interest rate cannot exceed 20%.')
            
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)
            
            # Calculate affordability
            result = self._calculate_affordability(
                annual_income, monthly_debts, down_payment,
                interest_rate, loan_term, property_tax_rate,
                insurance_rate, hoa_fees
            )
            
            return JsonResponse({
                'success': True,
                **result
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Calculation error. Please check your inputs and try again.'
            }, status=400)
    
    def _get_float(self, data, key, default=0):
        """Safely get float value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default
    
    def _get_int(self, data, key, default=0):
        """Safely get int value"""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default
    
    def _calculate_affordability(self, annual_income, monthly_debts, down_payment,
                                  interest_rate, loan_term, property_tax_rate,
                                  insurance_rate, hoa_fees):
        """Calculate house affordability based on income and debts"""
        
        monthly_income = annual_income / 12
        
        # Standard DTI ratios
        # Front-end ratio: housing costs should be ≤ 28% of gross income
        # Back-end ratio: all debts should be ≤ 36% of gross income
        
        front_end_ratio = 0.28
        back_end_ratio = 0.36
        
        # Calculate max housing payment based on front-end ratio
        max_housing_front = monthly_income * front_end_ratio
        
        # Calculate max total debt payment based on back-end ratio
        max_total_back = monthly_income * back_end_ratio
        max_housing_back = max_total_back - monthly_debts
        
        # Use the lower of the two
        max_housing_payment = max(0, min(max_housing_front, max_housing_back))
        
        # Calculate what home price this supports
        # We need to account for taxes, insurance, and PMI
        # Solve: housing_payment = P&I + taxes + insurance + PMI + HOA
        
        # Estimate taxes, insurance, PMI as percentages
        # These will be recalculated once we have the home price
        
        home_price = self._calculate_max_price(
            max_housing_payment, down_payment, interest_rate, loan_term,
            property_tax_rate, insurance_rate, hoa_fees
        )
        
        loan_amount = home_price - down_payment
        
        # Calculate actual monthly payment breakdown
        monthly_rate = (interest_rate / 100) / 12
        months = loan_term * 12
        
        if monthly_rate > 0 and loan_amount > 0:
            rate_factor = np.power(1 + monthly_rate, months)
            pi_payment = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            pi_payment = loan_amount / months if months > 0 else 0
        
        monthly_tax = (home_price * property_tax_rate / 100) / 12
        monthly_insurance = (home_price * insurance_rate / 100) / 12
        
        # PMI if less than 20% down
        down_pct = (down_payment / home_price * 100) if home_price > 0 else 0
        monthly_pmi = 0
        if down_pct < 20 and loan_amount > 0:
            monthly_pmi = (loan_amount * 0.007) / 12
        
        total_housing_payment = pi_payment + monthly_tax + monthly_insurance + monthly_pmi + hoa_fees
        
        # Calculate DTI ratios
        actual_front_end = (total_housing_payment / monthly_income * 100) if monthly_income > 0 else 0
        actual_back_end = ((total_housing_payment + monthly_debts) / monthly_income * 100) if monthly_income > 0 else 0
        
        # Create scenarios
        scenarios = self._create_scenarios(
            annual_income, monthly_debts, down_payment, interest_rate,
            loan_term, property_tax_rate, insurance_rate, hoa_fees
        )
        
        # Budget breakdown chart data
        budget_data = {
            'labels': ['P&I', 'Taxes', 'Insurance', 'PMI', 'HOA'],
            'values': [
                round(pi_payment, 2),
                round(monthly_tax, 2),
                round(monthly_insurance, 2),
                round(monthly_pmi, 2),
                round(hoa_fees, 2),
            ]
        }
        
        return {
            'affordability': {
                'max_home_price': round(home_price, 2),
                'loan_amount': round(loan_amount, 2),
                'down_payment': round(down_payment, 2),
                'down_payment_percent': round(down_pct, 1),
            },
            'monthly_payment': {
                'principal_interest': round(pi_payment, 2),
                'property_tax': round(monthly_tax, 2),
                'insurance': round(monthly_insurance, 2),
                'pmi': round(monthly_pmi, 2),
                'hoa': round(hoa_fees, 2),
                'total': round(total_housing_payment, 2),
            },
            'dti_ratios': {
                'front_end': round(actual_front_end, 1),
                'back_end': round(actual_back_end, 1),
                'front_end_limit': 28,
                'back_end_limit': 36,
            },
            'income': {
                'annual': round(annual_income, 2),
                'monthly': round(monthly_income, 2),
                'monthly_debts': round(monthly_debts, 2),
            },
            'scenarios': scenarios,
            'budget_data': budget_data,
        }
    
    def _calculate_max_price(self, max_payment, down_payment, rate, term,
                             tax_rate, insurance_rate, hoa):
        """Iteratively calculate max home price that fits payment budget"""
        
        monthly_rate = (rate / 100) / 12
        months = term * 12
        
        # Start with an estimate
        # Assume P&I is about 70% of total payment
        estimated_pi = max_payment * 0.70 - hoa
        
        if monthly_rate > 0 and estimated_pi > 0:
            rate_factor = np.power(1 + monthly_rate, months)
            estimated_loan = estimated_pi * (rate_factor - 1) / (monthly_rate * rate_factor)
        else:
            estimated_loan = estimated_pi * months
        
        home_price = max(0, estimated_loan + down_payment)
        
        # Iterate to refine
        for _ in range(10):
            loan_amount = home_price - down_payment
            
            if monthly_rate > 0 and loan_amount > 0:
                rate_factor = np.power(1 + monthly_rate, months)
                pi = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
            else:
                pi = loan_amount / months if months > 0 else 0
            
            tax = (home_price * tax_rate / 100) / 12
            insurance = (home_price * insurance_rate / 100) / 12
            
            down_pct = (down_payment / home_price * 100) if home_price > 0 else 0
            pmi = 0
            if down_pct < 20 and loan_amount > 0:
                pmi = (loan_amount * 0.007) / 12
            
            total = pi + tax + insurance + pmi + hoa
            
            if total > max_payment:
                home_price *= (max_payment / total)
            elif total < max_payment * 0.98:
                home_price *= (max_payment / total) * 0.99
            else:
                break
        
        return max(0, home_price)
    
    def _create_scenarios(self, annual_income, monthly_debts, down_payment,
                          rate, term, tax_rate, insurance_rate, hoa):
        """Create conservative, moderate, and aggressive scenarios"""
        
        monthly_income = annual_income / 12
        scenarios = []
        
        # Conservative (25% front-end, 33% back-end)
        max_housing = min(monthly_income * 0.25, (monthly_income * 0.33) - monthly_debts)
        price = self._calculate_max_price(max_housing, down_payment, rate, term, tax_rate, insurance_rate, hoa)
        scenarios.append({
            'name': 'Conservative',
            'description': '25% of income on housing',
            'home_price': round(price, 2),
            'monthly': round(max_housing, 2),
        })
        
        # Moderate (28% front-end, 36% back-end) - standard
        max_housing = min(monthly_income * 0.28, (monthly_income * 0.36) - monthly_debts)
        price = self._calculate_max_price(max_housing, down_payment, rate, term, tax_rate, insurance_rate, hoa)
        scenarios.append({
            'name': 'Moderate',
            'description': '28% of income (recommended)',
            'home_price': round(price, 2),
            'monthly': round(max_housing, 2),
        })
        
        # Aggressive (32% front-end, 43% back-end)
        max_housing = min(monthly_income * 0.32, (monthly_income * 0.43) - monthly_debts)
        price = self._calculate_max_price(max_housing, down_payment, rate, term, tax_rate, insurance_rate, hoa)
        scenarios.append({
            'name': 'Aggressive',
            'description': '32% of income (higher risk)',
            'home_price': round(price, 2),
            'monthly': round(max_housing, 2),
        })
        
        return scenarios
