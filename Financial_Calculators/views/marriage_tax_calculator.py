from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class MarriageTaxCalculator(View):
    """
    Class-based view for Marriage Tax Calculator.
    Compares married vs single filing; returns marriage bonus/penalty and Chart.js chart_data (BMI-style).
    """
    template_name = 'financial_calculators/marriage_tax_calculator.html'

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
    STANDARD_DEDUCTIONS = {
        'single': 14600,
        'married_jointly': 29200,
        'married_separately': 14600
    }

    def get(self, request):
        context = {'calculator_name': str(_('Marriage Tax Calculator'))}
        return render(request, self.template_name, context)

    def _get_data(self, request):
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = request.body
                if not body:
                    return {}
                return json.loads(body)
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}
        if request.body:
            try:
                return json.loads(request.body)
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
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

    def _get_bool(self, data, key, default=False):
        val = data.get(key, default)
        if isinstance(val, list):
            val = val[0] if val else default
        if val in (True, 'true', '1', 1, 'yes'):
            return True
        if val in (False, 'false', '0', 0, 'no', '', None):
            return False
        return bool(val)

    def _calculate_tax(self, taxable_income, filing_status):
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
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            income_1 = self._get_float(data, 'income_1', 0) or self._get_float(data, 'income1', 0)
            income_2 = self._get_float(data, 'income_2', 0) or self._get_float(data, 'income2', 0)
            pre_tax_deductions_1 = self._get_float(data, 'pre_tax_deductions_1', 0) or self._get_float(data, 'retirement1', 0)
            pre_tax_deductions_2 = self._get_float(data, 'pre_tax_deductions_2', 0) or self._get_float(data, 'retirement2', 0)
            itemized_combined = self._get_float(data, 'itemized', 0)
            if itemized_combined > 0:
                use_itemized = self._get_bool(data, 'use_itemized', True)
                itemized_deductions_1 = itemized_combined / 2
                itemized_deductions_2 = itemized_combined / 2
            else:
                use_itemized = self._get_bool(data, 'use_itemized', False)
                itemized_deductions_1 = self._get_float(data, 'itemized_deductions_1', 0)
                itemized_deductions_2 = self._get_float(data, 'itemized_deductions_2', 0)

            if income_1 < 0 or income_2 < 0:
                return JsonResponse({'success': False, 'error': str(_('Income cannot be negative.'))}, status=400)

            agi_1 = income_1 - pre_tax_deductions_1
            agi_2 = income_2 - pre_tax_deductions_2
            combined_agi = agi_1 + agi_2

            # Single filing
            deduction_1 = itemized_deductions_1 if (use_itemized and itemized_deductions_1 > self.STANDARD_DEDUCTIONS['single']) else self.STANDARD_DEDUCTIONS['single']
            deduction_2 = itemized_deductions_2 if (use_itemized and itemized_deductions_2 > self.STANDARD_DEDUCTIONS['single']) else self.STANDARD_DEDUCTIONS['single']
            taxable_1 = max(0, agi_1 - deduction_1)
            taxable_2 = max(0, agi_2 - deduction_2)
            tax_single_1 = self._calculate_tax(taxable_1, 'single')
            tax_single_2 = self._calculate_tax(taxable_2, 'single')
            total_tax_as_singles = tax_single_1 + tax_single_2

            # Married filing jointly
            combined_itemized = itemized_deductions_1 + itemized_deductions_2
            deduction_mfj = combined_itemized if (use_itemized and combined_itemized > self.STANDARD_DEDUCTIONS['married_jointly']) else self.STANDARD_DEDUCTIONS['married_jointly']
            taxable_mfj = max(0, combined_agi - deduction_mfj)
            tax_married_jointly = self._calculate_tax(taxable_mfj, 'married_jointly')

            # Married filing separately
            deduction_mfs_1 = itemized_deductions_1 if (use_itemized and itemized_deductions_1 > self.STANDARD_DEDUCTIONS['married_separately']) else self.STANDARD_DEDUCTIONS['married_separately']
            deduction_mfs_2 = itemized_deductions_2 if (use_itemized and itemized_deductions_2 > self.STANDARD_DEDUCTIONS['married_separately']) else self.STANDARD_DEDUCTIONS['married_separately']
            taxable_mfs_1 = max(0, agi_1 - deduction_mfs_1)
            taxable_mfs_2 = max(0, agi_2 - deduction_mfs_2)
            tax_mfs_1 = self._calculate_tax(taxable_mfs_1, 'married_separately')
            tax_mfs_2 = self._calculate_tax(taxable_mfs_2, 'married_separately')
            total_tax_mfs = tax_mfs_1 + tax_mfs_2

            marriage_effect = total_tax_as_singles - tax_married_jointly
            if marriage_effect > 0:
                effect_type = 'bonus'
                effect_description = str(_('Marriage Bonus: You save %(amount)s by filing jointly.')) % {'amount': f'${abs(marriage_effect):,.2f}'}
            elif marriage_effect < 0:
                effect_type = 'penalty'
                effect_description = str(_('Marriage Penalty: You pay %(amount)s more by filing jointly.')) % {'amount': f'${abs(marriage_effect):,.2f}'}
            else:
                effect_type = 'neutral'
                effect_description = str(_('No difference between married and single filing.'))

            if tax_married_jointly <= total_tax_mfs:
                best_married_option = str(_('Married Filing Jointly'))
                best_married_tax = tax_married_jointly
            else:
                best_married_option = str(_('Married Filing Separately'))
                best_married_tax = total_tax_mfs

            total_income = income_1 + income_2
            effective_rate_single = (total_tax_as_singles / total_income * 100) if total_income > 0 else 0
            effective_rate_mfj = (tax_married_jointly / total_income * 100) if total_income > 0 else 0
            effective_rate_mfs = (total_tax_mfs / total_income * 100) if total_income > 0 else 0

            income_ratio = max(income_1, income_2) / min(income_1, income_2) if min(income_1, income_2) > 0 else float('inf')
            if income_ratio < 1.5:
                disparity_note = str(_('Similar incomes often lead to marriage penalty.'))
            elif income_ratio > 3:
                disparity_note = str(_('Large income difference usually results in marriage bonus.'))
            else:
                disparity_note = str(_('Moderate income difference — effect varies.'))

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
                    'person_1': {'taxable_income': round(taxable_mfs_1, 2), 'tax': round(tax_mfs_1, 2)},
                    'person_2': {'taxable_income': round(taxable_mfs_2, 2), 'tax': round(tax_mfs_2, 2)},
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
                    'labels': [
                        str(_('Filing as Singles')),
                        str(_('Married Filing Jointly')),
                        str(_('Married Filing Separately'))
                    ],
                    'values': [
                        round(total_tax_as_singles, 2),
                        round(tax_married_jointly, 2),
                        round(total_tax_mfs, 2)
                    ]
                },
                'notes': [
                    str(_('Marriage bonus/penalty depends on income disparity.')),
                    str(_('Couples with similar incomes often face marriage penalty.')),
                    str(_('Single-earner couples typically get marriage bonus.')),
                    str(_('State taxes may have different marriage effects.'))
                ]
            }
            result['chart_data'] = self._prepare_chart_data(result)
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, result):
        comp = result.get('comparison_chart', {})
        labels = comp.get('labels', [])
        values = comp.get('values', [])
        if not labels or not values:
            return {}
        return {
            'comparison_chart': {
                'type': 'bar',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'label': str(_('Tax Amount')),
                        'data': values,
                        'backgroundColor': ['#f472b6', '#10b981', '#6366f1'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'display': False}},
                    'scales': {
                        'y': {'beginAtZero': True}
                    }
                }
            }
        }
