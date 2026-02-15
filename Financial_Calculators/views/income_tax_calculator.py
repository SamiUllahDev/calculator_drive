from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class IncomeTaxCalculator(View):
    """
    Class-based view for Income Tax Calculator
    Estimates federal income tax based on US tax brackets.
    """
    template_name = 'financial_calculators/income_tax_calculator.html'
    
    # 2024 US Federal Tax Brackets
    TAX_BRACKETS_2024 = {
        'single': [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37)
        ],
        'married_joint': [
            (23200, 0.10),
            (94300, 0.12),
            (201050, 0.22),
            (383900, 0.24),
            (487450, 0.32),
            (731200, 0.35),
            (float('inf'), 0.37)
        ],
        'married_separate': [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (365600, 0.35),
            (float('inf'), 0.37)
        ],
        'head_of_household': [
            (16550, 0.10),
            (63100, 0.12),
            (100500, 0.22),
            (191950, 0.24),
            (243700, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37)
        ]
    }
    
    STANDARD_DEDUCTION_2024 = {
        'single': 14600,
        'married_joint': 29200,
        'married_separate': 14600,
        'head_of_household': 21900
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': str(_('Income Tax Calculator')),
        }
        return render(request, self.template_name, context)

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

    def _get_float(self, data, key, default=0.0):
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def post(self, request):
        """Handle POST request for tax calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            gross_income = self._get_float(data, 'gross_income', 0)
            filing_status = data.get('filing_status', 'single')
            if isinstance(filing_status, list):
                filing_status = filing_status[0] if filing_status else 'single'
            retirement_401k = self._get_float(data, 'retirement_401k', 0)
            hsa_contribution = self._get_float(data, 'hsa_contribution', 0)
            other_pretax = self._get_float(data, 'other_pretax', 0)
            deduction_type = data.get('deduction_type', 'standard')
            if isinstance(deduction_type, list):
                deduction_type = deduction_type[0] if deduction_type else 'standard'
            itemized_deductions = self._get_float(data, 'itemized_deductions', 0)
            child_tax_credit = self._get_float(data, 'child_tax_credit', 0)
            other_credits = self._get_float(data, 'other_credits', 0)
            state_tax_rate = self._get_float(data, 'state_tax_rate', 0)

            if gross_income < 0:
                return JsonResponse({'success': False, 'error': str(_('Gross income cannot be negative.'))}, status=400)
            if filing_status not in self.TAX_BRACKETS_2024:
                return JsonResponse({'success': False, 'error': str(_('Invalid filing status.'))}, status=400)
            
            # Calculate AGI (Adjusted Gross Income)
            total_pretax = retirement_401k + hsa_contribution + other_pretax
            agi = gross_income - total_pretax
            
            # Determine deduction
            standard_deduction = self.STANDARD_DEDUCTION_2024[filing_status]
            if deduction_type == 'standard' or itemized_deductions <= standard_deduction:
                deduction_used = standard_deduction
                deduction_type_used = 'standard'
            else:
                deduction_used = itemized_deductions
                deduction_type_used = 'itemized'
            
            # Calculate taxable income
            taxable_income = max(0, agi - deduction_used)
            
            # Calculate federal tax
            brackets = self.TAX_BRACKETS_2024[filing_status]
            federal_tax = 0
            tax_breakdown = []
            remaining_income = taxable_income
            prev_bracket = 0
            
            for bracket_limit, rate in brackets:
                if remaining_income <= 0:
                    break
                
                bracket_income = min(remaining_income, bracket_limit - prev_bracket)
                bracket_tax = bracket_income * rate
                federal_tax += bracket_tax
                
                if bracket_income > 0:
                    tax_breakdown.append({
                        'bracket': f'${prev_bracket:,.0f} - ${bracket_limit:,.0f}' if bracket_limit != float('inf') else f'${prev_bracket:,.0f}+',
                        'rate': f'{rate * 100:.0f}%',
                        'income': round(bracket_income, 2),
                        'tax': round(bracket_tax, 2)
                    })
                
                remaining_income -= bracket_income
                prev_bracket = bracket_limit
            
            # Apply credits
            total_credits = child_tax_credit + other_credits
            federal_tax_after_credits = max(0, federal_tax - total_credits)
            
            # Calculate state tax
            state_tax = agi * (state_tax_rate / 100)
            
            # Calculate total tax
            total_tax = federal_tax_after_credits + state_tax
            
            # FICA taxes (Social Security + Medicare)
            ss_wage_base = 168600  # 2024 limit
            ss_tax = min(gross_income, ss_wage_base) * 0.062
            medicare_tax = gross_income * 0.0145
            additional_medicare = max(0, gross_income - 200000) * 0.009 if filing_status == 'single' else max(0, gross_income - 250000) * 0.009
            fica_tax = ss_tax + medicare_tax + additional_medicare
            
            # Total including FICA
            total_all_taxes = total_tax + fica_tax
            
            # Effective tax rates
            effective_federal_rate = (federal_tax_after_credits / gross_income * 100) if gross_income > 0 else 0
            effective_total_rate = (total_all_taxes / gross_income * 100) if gross_income > 0 else 0
            marginal_rate = brackets[-1][1] * 100  # Default to highest
            for bracket_limit, rate in brackets:
                if taxable_income <= bracket_limit:
                    marginal_rate = rate * 100
                    break
            
            # Take-home calculations
            annual_take_home = gross_income - total_all_taxes - total_pretax
            monthly_take_home = annual_take_home / 12
            biweekly_take_home = annual_take_home / 26
            
            result = {
                'success': True,
                'income': {
                    'gross': round(gross_income, 2),
                    'pretax_deductions': round(total_pretax, 2),
                    'agi': round(agi, 2),
                    'deduction': round(deduction_used, 2),
                    'deduction_type': deduction_type_used,
                    'taxable_income': round(taxable_income, 2)
                },
                'federal_tax': {
                    'before_credits': round(federal_tax, 2),
                    'credits': round(total_credits, 2),
                    'after_credits': round(federal_tax_after_credits, 2),
                    'breakdown': tax_breakdown
                },
                'state_tax': {
                    'rate': state_tax_rate,
                    'amount': round(state_tax, 2)
                },
                'fica': {
                    'social_security': round(ss_tax, 2),
                    'medicare': round(medicare_tax + additional_medicare, 2),
                    'total': round(fica_tax, 2)
                },
                'totals': {
                    'total_tax': round(total_tax, 2),
                    'total_with_fica': round(total_all_taxes, 2)
                },
                'rates': {
                    'marginal': round(marginal_rate, 2),
                    'effective_federal': round(effective_federal_rate, 2),
                    'effective_total': round(effective_total_rate, 2)
                },
                'take_home': {
                    'annual': round(annual_take_home, 2),
                    'monthly': round(monthly_take_home, 2),
                    'biweekly': round(biweekly_take_home, 2),
                    'weekly': round(annual_take_home / 52, 2)
                },
                'filing_status': filing_status
            }
            result['chart_data'] = self._prepare_chart_data(result)
            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, result):
        """Build Chart.js-ready doughnut: Take-Home, Federal, FICA, State, Pre-Tax."""
        take_home = result.get('take_home', {}).get('annual', 0)
        federal = result.get('federal_tax', {}).get('after_credits', 0)
        fica = result.get('fica', {}).get('total', 0)
        state = result.get('state_tax', {}).get('amount', 0)
        pretax = result.get('income', {}).get('pretax_deductions', 0)
        labels = [
            str(_('Take-Home Pay')),
            str(_('Federal Tax')),
            str(_('FICA')),
            str(_('State Tax')),
            str(_('Pre-Tax Deductions')),
        ]
        values = [
            round(take_home, 2),
            round(federal, 2),
            round(fica, 2),
            round(state, 2),
            round(pretax, 2),
        ]
        return {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': ['#22c55e', '#ef4444', '#f97316', '#8b5cf6', '#3b82f6'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom', 'labels': {'boxWidth': 12}}}
                }
            }
        }
