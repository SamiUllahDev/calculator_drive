from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class MarriageTaxCalculator(View):
    """
    Class-based view for Marriage Tax Calculator
    Calculates marriage tax bonus or penalty by comparing married vs single filing.
    """
    template_name = 'financial_calculators/marriage_tax_calculator.html'

    # 2024 Federal Tax Brackets
    TAX_BRACKETS = {
        'single': [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (609350, 0.35),
            (float('inf'), 0.37)
        ],
        'married_jointly': [
            (23200, 0.10),
            (94300, 0.12),
            (201050, 0.22),
            (383900, 0.24),
            (487450, 0.32),
            (731200, 0.35),
            (float('inf'), 0.37)
        ],
        'married_separately': [
            (11600, 0.10),
            (47150, 0.12),
            (100525, 0.22),
            (191950, 0.24),
            (243725, 0.32),
            (365600, 0.35),
            (float('inf'), 0.37)
        ]
    }

    # 2024 Standard Deductions
    STANDARD_DEDUCTIONS = {
        'single': 14600,
        'married_jointly': 29200,
        'married_separately': 14600
    }

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Marriage Tax Calculator',
        }
        return render(request, self.template_name, context)

    def _calculate_tax(self, taxable_income, filing_status):
        """Calculate federal income tax based on brackets"""
        brackets = self.TAX_BRACKETS[filing_status]
        tax = 0
        remaining = taxable_income
        previous_limit = 0
        
        for limit, rate in brackets:
            if remaining <= 0:
                break
            bracket_amount = min(remaining, limit - previous_limit)
            tax += bracket_amount * rate
            remaining -= bracket_amount
            previous_limit = limit
        
        return tax

    def post(self, request):
        """Handle POST request for marriage tax calculations"""
        try:
            data = json.loads(request.body)

            # Person 1 income
            income_1 = float(str(data.get('income_1', 0)).replace(',', ''))
            pre_tax_deductions_1 = float(str(data.get('pre_tax_deductions_1', 0)).replace(',', ''))
            itemized_deductions_1 = float(str(data.get('itemized_deductions_1', 0)).replace(',', ''))
            
            # Person 2 income
            income_2 = float(str(data.get('income_2', 0)).replace(',', ''))
            pre_tax_deductions_2 = float(str(data.get('pre_tax_deductions_2', 0)).replace(',', ''))
            itemized_deductions_2 = float(str(data.get('itemized_deductions_2', 0)).replace(',', ''))
            
            # Filing preferences
            use_itemized = data.get('use_itemized', False)

            if income_1 < 0 or income_2 < 0:
                return JsonResponse({'success': False, 'error': 'Income cannot be negative.'}, status=400)

            # Calculate AGI for each person
            agi_1 = income_1 - pre_tax_deductions_1
            agi_2 = income_2 - pre_tax_deductions_2
            combined_agi = agi_1 + agi_2

            # SCENARIO 1: Both file as Single
            # Person 1
            if use_itemized and itemized_deductions_1 > self.STANDARD_DEDUCTIONS['single']:
                deduction_1 = itemized_deductions_1
            else:
                deduction_1 = self.STANDARD_DEDUCTIONS['single']
            
            taxable_1 = max(0, agi_1 - deduction_1)
            tax_single_1 = self._calculate_tax(taxable_1, 'single')

            # Person 2
            if use_itemized and itemized_deductions_2 > self.STANDARD_DEDUCTIONS['single']:
                deduction_2 = itemized_deductions_2
            else:
                deduction_2 = self.STANDARD_DEDUCTIONS['single']
            
            taxable_2 = max(0, agi_2 - deduction_2)
            tax_single_2 = self._calculate_tax(taxable_2, 'single')

            total_tax_as_singles = tax_single_1 + tax_single_2

            # SCENARIO 2: Married Filing Jointly
            combined_itemized = itemized_deductions_1 + itemized_deductions_2
            if use_itemized and combined_itemized > self.STANDARD_DEDUCTIONS['married_jointly']:
                deduction_mfj = combined_itemized
            else:
                deduction_mfj = self.STANDARD_DEDUCTIONS['married_jointly']
            
            taxable_mfj = max(0, combined_agi - deduction_mfj)
            tax_married_jointly = self._calculate_tax(taxable_mfj, 'married_jointly')

            # SCENARIO 3: Married Filing Separately
            # Person 1 MFS
            if use_itemized and itemized_deductions_1 > self.STANDARD_DEDUCTIONS['married_separately']:
                deduction_mfs_1 = itemized_deductions_1
            else:
                deduction_mfs_1 = self.STANDARD_DEDUCTIONS['married_separately']
            
            taxable_mfs_1 = max(0, agi_1 - deduction_mfs_1)
            tax_mfs_1 = self._calculate_tax(taxable_mfs_1, 'married_separately')

            # Person 2 MFS
            if use_itemized and itemized_deductions_2 > self.STANDARD_DEDUCTIONS['married_separately']:
                deduction_mfs_2 = itemized_deductions_2
            else:
                deduction_mfs_2 = self.STANDARD_DEDUCTIONS['married_separately']
            
            taxable_mfs_2 = max(0, agi_2 - deduction_mfs_2)
            tax_mfs_2 = self._calculate_tax(taxable_mfs_2, 'married_separately')

            total_tax_mfs = tax_mfs_1 + tax_mfs_2

            # Calculate marriage penalty/bonus
            marriage_effect = total_tax_as_singles - tax_married_jointly
            
            if marriage_effect > 0:
                effect_type = 'bonus'
                effect_description = f'Marriage Bonus: You save ${abs(marriage_effect):,.2f} by being married'
            elif marriage_effect < 0:
                effect_type = 'penalty'
                effect_description = f'Marriage Penalty: You pay ${abs(marriage_effect):,.2f} more by being married'
            else:
                effect_type = 'neutral'
                effect_description = 'No difference between married and single filing'

            # Best filing option for married couple
            if tax_married_jointly <= total_tax_mfs:
                best_married_option = 'Married Filing Jointly'
                best_married_tax = tax_married_jointly
            else:
                best_married_option = 'Married Filing Separately'
                best_married_tax = total_tax_mfs

            # Effective tax rates
            total_income = income_1 + income_2
            effective_rate_single = (total_tax_as_singles / total_income * 100) if total_income > 0 else 0
            effective_rate_mfj = (tax_married_jointly / total_income * 100) if total_income > 0 else 0
            effective_rate_mfs = (total_tax_mfs / total_income * 100) if total_income > 0 else 0

            # Income disparity analysis
            income_ratio = max(income_1, income_2) / min(income_1, income_2) if min(income_1, income_2) > 0 else float('inf')
            
            if income_ratio < 1.5:
                disparity_note = "Similar incomes often lead to marriage penalty"
            elif income_ratio > 3:
                disparity_note = "Large income difference usually results in marriage bonus"
            else:
                disparity_note = "Moderate income difference - effect varies"

            result = {
                'success': True,
                'incomes': {
                    'person_1': round(income_1, 2),
                    'person_2': round(income_2, 2),
                    'combined': round(total_income, 2),
                    'income_ratio': round(income_ratio, 2) if income_ratio != float('inf') else 'N/A'
                },
                'single_filing': {
                    'person_1': {
                        'agi': round(agi_1, 2),
                        'deduction': round(deduction_1, 2),
                        'taxable_income': round(taxable_1, 2),
                        'tax': round(tax_single_1, 2)
                    },
                    'person_2': {
                        'agi': round(agi_2, 2),
                        'deduction': round(deduction_2, 2),
                        'taxable_income': round(taxable_2, 2),
                        'tax': round(tax_single_2, 2)
                    },
                    'total_tax': round(total_tax_as_singles, 2),
                    'effective_rate': round(effective_rate_single, 2)
                },
                'married_jointly': {
                    'combined_agi': round(combined_agi, 2),
                    'deduction': round(deduction_mfj, 2),
                    'taxable_income': round(taxable_mfj, 2),
                    'tax': round(tax_married_jointly, 2),
                    'effective_rate': round(effective_rate_mfj, 2)
                },
                'married_separately': {
                    'person_1': {
                        'taxable_income': round(taxable_mfs_1, 2),
                        'tax': round(tax_mfs_1, 2)
                    },
                    'person_2': {
                        'taxable_income': round(taxable_mfs_2, 2),
                        'tax': round(tax_mfs_2, 2)
                    },
                    'total_tax': round(total_tax_mfs, 2),
                    'effective_rate': round(effective_rate_mfs, 2)
                },
                'marriage_effect': {
                    'type': effect_type,
                    'amount': round(abs(marriage_effect), 2),
                    'description': effect_description
                },
                'best_option': {
                    'if_married': best_married_option,
                    'tax_if_married': round(best_married_tax, 2),
                    'tax_if_single': round(total_tax_as_singles, 2),
                    'savings_vs_singles': round(total_tax_as_singles - best_married_tax, 2)
                },
                'analysis': {
                    'disparity_note': disparity_note,
                    'mfj_vs_mfs_savings': round(total_tax_mfs - tax_married_jointly, 2)
                },
                'comparison_chart': {
                    'labels': ['Filing as Singles', 'Married Filing Jointly', 'Married Filing Separately'],
                    'values': [round(total_tax_as_singles, 2), round(tax_married_jointly, 2), round(total_tax_mfs, 2)]
                },
                'notes': [
                    'Marriage bonus/penalty depends on income disparity',
                    'Couples with similar incomes often face marriage penalty',
                    'Single-earner couples typically get marriage bonus',
                    'MFS loses many deductions/credits (student loan interest, education credits, etc.)',
                    'State taxes may have different marriage effects'
                ]
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
