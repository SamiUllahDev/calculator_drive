from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class TakeHomePaycheckCalculator(View):
    """
    Class-based view for Take Home Paycheck Calculator
    Calculates net pay after federal, state, and local taxes, plus deductions.
    """
    template_name = 'financial_calculators/take_home_paycheck_calculator.html'
    
    # 2024 Federal Tax Brackets (Single filer)
    FEDERAL_BRACKETS_SINGLE = [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float('inf'), 0.37)
    ]
    
    # 2024 Federal Tax Brackets (Married filing jointly)
    FEDERAL_BRACKETS_MARRIED = [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float('inf'), 0.37)
    ]
    
    # Standard deductions 2024
    STANDARD_DEDUCTION = {
        'single': 14600,
        'married': 29200,
        'head_of_household': 21900
    }
    
    # FICA rates 2024
    SOCIAL_SECURITY_RATE = 0.062
    SOCIAL_SECURITY_WAGE_BASE = 168600
    MEDICARE_RATE = 0.0145
    MEDICARE_ADDITIONAL_RATE = 0.009
    MEDICARE_ADDITIONAL_THRESHOLD = 200000
    
    # Common state tax rates (simplified flat rates for estimation)
    STATE_TAX_RATES = {
        'AL': 5.0, 'AK': 0, 'AZ': 2.5, 'AR': 4.4, 'CA': 9.3,
        'CO': 4.4, 'CT': 5.5, 'DE': 6.6, 'FL': 0, 'GA': 5.49,
        'HI': 8.25, 'ID': 5.8, 'IL': 4.95, 'IN': 3.05, 'IA': 5.7,
        'KS': 5.7, 'KY': 4.5, 'LA': 4.25, 'ME': 7.15, 'MD': 5.75,
        'MA': 5.0, 'MI': 4.25, 'MN': 7.85, 'MS': 5.0, 'MO': 4.95,
        'MT': 5.9, 'NE': 5.84, 'NV': 0, 'NH': 0, 'NJ': 6.37,
        'NM': 5.9, 'NY': 6.85, 'NC': 5.25, 'ND': 2.5, 'OH': 3.99,
        'OK': 4.75, 'OR': 9.0, 'PA': 3.07, 'RI': 5.99, 'SC': 6.5,
        'SD': 0, 'TN': 0, 'TX': 0, 'UT': 4.65, 'VT': 7.6,
        'VA': 5.75, 'WA': 0, 'WV': 5.12, 'WI': 5.3, 'WY': 0
    }
    
    def get(self, request):
        """Handle GET request"""
        states = [{'code': code, 'rate': rate} for code, rate in sorted(self.STATE_TAX_RATES.items())]
        context = {
            'calculator_name': 'Take Home Paycheck Calculator',
            'states': states,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for paycheck calculations"""
        try:
            data = json.loads(request.body)
            
            # Input values
            gross_pay = float(str(data.get('gross_pay', 0)).replace(',', ''))
            pay_frequency = data.get('pay_frequency', 'biweekly')  # weekly, biweekly, semimonthly, monthly, annual
            filing_status = data.get('filing_status', 'single')
            state = data.get('state', 'CA')
            
            # Pre-tax deductions
            retirement_401k = float(str(data.get('retirement_401k', 0)).replace(',', ''))
            health_insurance = float(str(data.get('health_insurance', 0)).replace(',', ''))
            hsa_fsa = float(str(data.get('hsa_fsa', 0)).replace(',', ''))
            other_pretax = float(str(data.get('other_pretax', 0)).replace(',', ''))
            
            # Post-tax deductions
            other_posttax = float(str(data.get('other_posttax', 0)).replace(',', ''))
            
            # Federal allowances
            federal_allowances = int(data.get('federal_allowances', 0))
            
            # Validation
            if gross_pay < 0:
                return JsonResponse({'success': False, 'error': 'Gross pay cannot be negative.'}, status=400)
            
            # Calculate pay periods per year
            periods_per_year = {
                'weekly': 52,
                'biweekly': 26,
                'semimonthly': 24,
                'monthly': 12,
                'annual': 1
            }
            periods = periods_per_year.get(pay_frequency, 26)
            
            # Calculate annual gross
            annual_gross = gross_pay * periods
            
            # Calculate annual pre-tax deductions
            annual_pretax = (retirement_401k + health_insurance + hsa_fsa + other_pretax) * periods
            
            # Taxable income for federal
            standard_deduction = self.STANDARD_DEDUCTION.get(filing_status, 14600)
            federal_taxable = max(0, annual_gross - annual_pretax - standard_deduction)
            
            # Calculate federal tax
            brackets = self.FEDERAL_BRACKETS_MARRIED if filing_status == 'married' else self.FEDERAL_BRACKETS_SINGLE
            federal_tax = self._calculate_federal_tax(federal_taxable, brackets)
            
            # Per-period federal tax
            federal_tax_per_period = federal_tax / periods
            
            # State tax
            state_rate = self.STATE_TAX_RATES.get(state, 0) / 100
            state_tax = (annual_gross - annual_pretax) * state_rate
            state_tax_per_period = state_tax / periods
            
            # FICA taxes (calculated on gross, not reduced by pretax deductions)
            # Social Security
            annual_ss_taxable = min(annual_gross, self.SOCIAL_SECURITY_WAGE_BASE)
            social_security_tax = annual_ss_taxable * self.SOCIAL_SECURITY_RATE
            ss_tax_per_period = social_security_tax / periods
            
            # Medicare
            medicare_tax = annual_gross * self.MEDICARE_RATE
            if annual_gross > self.MEDICARE_ADDITIONAL_THRESHOLD:
                medicare_tax += (annual_gross - self.MEDICARE_ADDITIONAL_THRESHOLD) * self.MEDICARE_ADDITIONAL_RATE
            medicare_tax_per_period = medicare_tax / periods
            
            # Total taxes per period
            total_taxes_per_period = federal_tax_per_period + state_tax_per_period + ss_tax_per_period + medicare_tax_per_period
            
            # Total pre-tax deductions per period
            total_pretax_per_period = retirement_401k + health_insurance + hsa_fsa + other_pretax
            
            # Net pay
            net_pay = gross_pay - total_taxes_per_period - total_pretax_per_period - other_posttax
            
            # Annual calculations
            annual_net = net_pay * periods
            annual_taxes = total_taxes_per_period * periods
            
            # Effective tax rate
            effective_rate = (annual_taxes / annual_gross * 100) if annual_gross > 0 else 0
            
            result = {
                'success': True,
                'gross_pay': round(gross_pay, 2),
                'pay_frequency': pay_frequency,
                'filing_status': filing_status,
                'state': state,
                
                'deductions': {
                    'federal_tax': round(federal_tax_per_period, 2),
                    'state_tax': round(state_tax_per_period, 2),
                    'social_security': round(ss_tax_per_period, 2),
                    'medicare': round(medicare_tax_per_period, 2),
                    'total_taxes': round(total_taxes_per_period, 2),
                    'retirement_401k': round(retirement_401k, 2),
                    'health_insurance': round(health_insurance, 2),
                    'hsa_fsa': round(hsa_fsa, 2),
                    'other_pretax': round(other_pretax, 2),
                    'total_pretax': round(total_pretax_per_period, 2),
                    'other_posttax': round(other_posttax, 2),
                    'total_deductions': round(total_taxes_per_period + total_pretax_per_period + other_posttax, 2)
                },
                
                'net_pay': round(net_pay, 2),
                
                'annual': {
                    'gross': round(annual_gross, 2),
                    'federal_tax': round(federal_tax, 2),
                    'state_tax': round(state_tax, 2),
                    'social_security': round(social_security_tax, 2),
                    'medicare': round(medicare_tax, 2),
                    'total_taxes': round(annual_taxes, 2),
                    'pretax_deductions': round(annual_pretax, 2),
                    'net': round(annual_net, 2)
                },
                
                'rates': {
                    'effective_tax_rate': round(effective_rate, 2),
                    'state_rate': round(state_rate * 100, 2),
                    'federal_bracket': self._get_marginal_rate(federal_taxable, brackets) * 100
                },
                
                'breakdown_percentages': {
                    'net_pay': round(net_pay / gross_pay * 100, 1) if gross_pay > 0 else 0,
                    'taxes': round(total_taxes_per_period / gross_pay * 100, 1) if gross_pay > 0 else 0,
                    'pretax': round(total_pretax_per_period / gross_pay * 100, 1) if gross_pay > 0 else 0,
                    'posttax': round(other_posttax / gross_pay * 100, 1) if gross_pay > 0 else 0
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def _calculate_federal_tax(self, taxable_income, brackets):
        """Calculate federal tax using tax brackets"""
        tax = 0
        prev_bracket = 0
        
        for bracket_limit, rate in brackets:
            if taxable_income <= 0:
                break
            
            taxable_in_bracket = min(taxable_income, bracket_limit - prev_bracket)
            tax += taxable_in_bracket * rate
            taxable_income -= taxable_in_bracket
            prev_bracket = bracket_limit
        
        return tax
    
    def _get_marginal_rate(self, taxable_income, brackets):
        """Get the marginal tax rate for the given income"""
        prev_bracket = 0
        for bracket_limit, rate in brackets:
            if taxable_income <= bracket_limit:
                return rate
            prev_bracket = bracket_limit
        return brackets[-1][1]
