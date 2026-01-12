from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class EstateTaxCalculator(View):
    """
    Class-based view for Estate Tax Calculator
    Calculates federal estate tax based on estate value and exemptions.
    """
    template_name = 'financial_calculators/estate_tax_calculator.html'

    # 2024 Federal Estate Tax Brackets
    ESTATE_TAX_BRACKETS = [
        (10000, 0.18),
        (20000, 0.20),
        (40000, 0.22),
        (60000, 0.24),
        (80000, 0.26),
        (100000, 0.28),
        (150000, 0.30),
        (250000, 0.32),
        (500000, 0.34),
        (750000, 0.37),
        (1000000, 0.39),
        (float('inf'), 0.40)
    ]

    # 2024 Federal Estate Tax Exemption
    FEDERAL_EXEMPTION = 13610000  # $13.61 million for 2024

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Estate Tax Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for estate tax calculations"""
        try:
            data = json.loads(request.body)

            # Estate assets
            real_estate = float(str(data.get('real_estate', 0)).replace(',', ''))
            bank_accounts = float(str(data.get('bank_accounts', 0)).replace(',', ''))
            investments = float(str(data.get('investments', 0)).replace(',', ''))
            retirement_accounts = float(str(data.get('retirement_accounts', 0)).replace(',', ''))
            life_insurance = float(str(data.get('life_insurance', 0)).replace(',', ''))
            business_interests = float(str(data.get('business_interests', 0)).replace(',', ''))
            personal_property = float(str(data.get('personal_property', 0)).replace(',', ''))
            other_assets = float(str(data.get('other_assets', 0)).replace(',', ''))
            
            # Deductions
            mortgages = float(str(data.get('mortgages', 0)).replace(',', ''))
            other_debts = float(str(data.get('other_debts', 0)).replace(',', ''))
            funeral_expenses = float(str(data.get('funeral_expenses', 0)).replace(',', ''))
            administrative_expenses = float(str(data.get('administrative_expenses', 0)).replace(',', ''))
            charitable_bequests = float(str(data.get('charitable_bequests', 0)).replace(',', ''))
            
            # Marital status
            marital_status = data.get('marital_status', 'single')  # single, married
            spouse_inheritance = float(str(data.get('spouse_inheritance', 0)).replace(',', ''))
            
            # Prior gifts
            prior_taxable_gifts = float(str(data.get('prior_taxable_gifts', 0)).replace(',', ''))
            
            # Custom exemption (for married couples who may have more)
            use_portability = data.get('use_portability', False)
            deceased_spouse_exemption = float(str(data.get('deceased_spouse_exemption', 0)).replace(',', ''))

            # Calculate Gross Estate
            gross_estate = (real_estate + bank_accounts + investments + 
                          retirement_accounts + life_insurance + business_interests + 
                          personal_property + other_assets)

            # Calculate Deductions
            total_debts = mortgages + other_debts
            total_expenses = funeral_expenses + administrative_expenses
            marital_deduction = spouse_inheritance if marital_status == 'married' else 0
            
            total_deductions = total_debts + total_expenses + charitable_bequests + marital_deduction

            # Calculate Taxable Estate
            net_estate = gross_estate - total_deductions
            
            # Add prior taxable gifts (for cumulative tax calculation)
            cumulative_transfers = net_estate + prior_taxable_gifts

            # Calculate Exemption
            available_exemption = self.FEDERAL_EXEMPTION
            if use_portability and deceased_spouse_exemption > 0:
                available_exemption += deceased_spouse_exemption
            
            # Taxable amount (after exemption)
            taxable_amount = max(0, cumulative_transfers - available_exemption)

            # Calculate Estate Tax
            estate_tax = 0
            remaining = taxable_amount
            tax_breakdown = []
            previous_limit = 0
            
            for limit, rate in self.ESTATE_TAX_BRACKETS:
                if remaining <= 0:
                    break
                
                bracket_amount = min(remaining, limit - previous_limit)
                bracket_tax = bracket_amount * rate
                
                if bracket_amount > 0:
                    estate_tax += bracket_tax
                    tax_breakdown.append({
                        'bracket': f'${previous_limit:,} - ${limit:,}' if limit != float('inf') else f'Over ${previous_limit:,}',
                        'rate': f'{rate * 100:.0f}%',
                        'taxable_amount': round(bracket_amount, 2),
                        'tax': round(bracket_tax, 2)
                    })
                
                remaining -= bracket_amount
                previous_limit = limit

            # Effective tax rate
            effective_rate = (estate_tax / net_estate * 100) if net_estate > 0 else 0

            # State estate tax estimate (varies by state)
            # Example: Some states have lower exemptions
            state_exemption = 1000000  # Example: $1M state exemption
            state_taxable = max(0, net_estate - state_exemption)
            state_tax_estimate = state_taxable * 0.16 if state_taxable > 0 else 0  # Example: 16% max rate

            # Assets breakdown for display
            assets_breakdown = {
                'real_estate': round(real_estate, 2),
                'bank_accounts': round(bank_accounts, 2),
                'investments': round(investments, 2),
                'retirement_accounts': round(retirement_accounts, 2),
                'life_insurance': round(life_insurance, 2),
                'business_interests': round(business_interests, 2),
                'personal_property': round(personal_property, 2),
                'other_assets': round(other_assets, 2)
            }

            deductions_breakdown = {
                'mortgages': round(mortgages, 2),
                'other_debts': round(other_debts, 2),
                'funeral_expenses': round(funeral_expenses, 2),
                'administrative_expenses': round(administrative_expenses, 2),
                'charitable_bequests': round(charitable_bequests, 2),
                'marital_deduction': round(marital_deduction, 2)
            }

            # Net amount to heirs
            net_to_heirs = net_estate - estate_tax - state_tax_estimate

            # Tax reduction strategies
            strategies = []
            if marital_status == 'single' and gross_estate > self.FEDERAL_EXEMPTION:
                strategies.append("Consider marriage for marital deduction benefits")
            if charitable_bequests == 0 and gross_estate > self.FEDERAL_EXEMPTION:
                strategies.append("Charitable giving can reduce taxable estate")
            if life_insurance > 0 and gross_estate > self.FEDERAL_EXEMPTION:
                strategies.append("Consider an Irrevocable Life Insurance Trust (ILIT)")
            if business_interests > 0:
                strategies.append("Family Limited Partnerships may help reduce estate value")
            if not use_portability and marital_status == 'married':
                strategies.append("Ensure portability election is made at first spouse's death")
            strategies.append("Annual gift exclusion ($18,000/person in 2024) reduces estate")

            result = {
                'success': True,
                'assets': assets_breakdown,
                'gross_estate': round(gross_estate, 2),
                'deductions': deductions_breakdown,
                'total_deductions': round(total_deductions, 2),
                'net_estate': round(net_estate, 2),
                'prior_taxable_gifts': round(prior_taxable_gifts, 2),
                'cumulative_transfers': round(cumulative_transfers, 2),
                'exemption': {
                    'federal_exemption': round(self.FEDERAL_EXEMPTION, 2),
                    'portability_amount': round(deceased_spouse_exemption, 2) if use_portability else 0,
                    'total_available': round(available_exemption, 2)
                },
                'taxable_amount': round(taxable_amount, 2),
                'federal_estate_tax': round(estate_tax, 2),
                'tax_breakdown': tax_breakdown,
                'state_tax_estimate': round(state_tax_estimate, 2),
                'total_taxes': round(estate_tax + state_tax_estimate, 2),
                'effective_rate': round(effective_rate, 2),
                'net_to_heirs': round(net_to_heirs, 2),
                'percent_to_heirs': round(net_to_heirs / gross_estate * 100, 1) if gross_estate > 0 else 0,
                'strategies': strategies,
                'notes': [
                    f'Federal estate tax exemption for 2024 is ${self.FEDERAL_EXEMPTION:,}',
                    'The exemption is scheduled to decrease to approximately $7 million in 2026',
                    'State estate/inheritance taxes vary and may have lower exemptions',
                    'Life insurance owned by the deceased is included in the gross estate'
                ]
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
