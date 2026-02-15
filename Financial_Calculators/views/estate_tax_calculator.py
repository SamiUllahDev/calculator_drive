from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class EstateTaxCalculator(View):
    """
    Class-based view for Estate Tax Calculator.
    Calculates federal estate tax. Accepts simplified (estate_value, debts, etc.)
    or full asset/deduction breakdown. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/estate_tax_calculator.html'

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
    FEDERAL_EXEMPTION = 13610000  # $13.61 million for 2024

    def get(self, request):
        context = {'calculator_name': str(_('Estate Tax Calculator'))}
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

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            # Simplified input: estate_value, debts, charitable, marital_deduction
            use_simple = self._get_float(data, 'estate_value', 0) > 0 or self._get_float(data, 'gross_estate', 0) > 0
            if use_simple:
                gross_estate = self._get_float(data, 'estate_value', 0) or self._get_float(data, 'gross_estate', 0)
                debts = self._get_float(data, 'debts', 0)
                charitable = self._get_float(data, 'charitable_bequests', 0) or self._get_float(data, 'charitable', 0)
                marital_deduction = self._get_float(data, 'marital_deduction', 0) or (
                    self._get_float(data, 'spouse_inheritance', 0) if data.get('marital_status') == 'married' or self._get_bool(data, 'married') else 0
                )
                total_deductions = debts + charitable + marital_deduction
                assets_breakdown = {'gross_estate': round(gross_estate, 2)}
                deductions_breakdown = {
                    'debts': round(debts, 2),
                    'charitable_bequests': round(charitable, 2),
                    'marital_deduction': round(marital_deduction, 2)
                }
            else:
                real_estate = self._get_float(data, 'real_estate', 0)
                bank_accounts = self._get_float(data, 'bank_accounts', 0)
                investments = self._get_float(data, 'investments', 0)
                retirement_accounts = self._get_float(data, 'retirement_accounts', 0)
                life_insurance = self._get_float(data, 'life_insurance', 0)
                business_interests = self._get_float(data, 'business_interests', 0)
                personal_property = self._get_float(data, 'personal_property', 0)
                other_assets = self._get_float(data, 'other_assets', 0)
                gross_estate = (real_estate + bank_accounts + investments + retirement_accounts +
                               life_insurance + business_interests + personal_property + other_assets)
                mortgages = self._get_float(data, 'mortgages', 0)
                other_debts = self._get_float(data, 'other_debts', 0)
                funeral_expenses = self._get_float(data, 'funeral_expenses', 0)
                administrative_expenses = self._get_float(data, 'administrative_expenses', 0)
                charitable_bequests = self._get_float(data, 'charitable_bequests', 0)
                marital_status = data.get('marital_status', 'single')
                if isinstance(marital_status, list):
                    marital_status = marital_status[0] if marital_status else 'single'
                spouse_inheritance = self._get_float(data, 'spouse_inheritance', 0)
                marital_deduction = spouse_inheritance if marital_status == 'married' else 0
                total_deductions = (mortgages + other_debts + funeral_expenses + administrative_expenses +
                                   charitable_bequests + marital_deduction)
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

            if gross_estate < 0:
                return JsonResponse({'success': False, 'error': str(_('Estate value cannot be negative.'))}, status=400)

            net_estate = gross_estate - total_deductions
            prior_taxable_gifts = self._get_float(data, 'prior_taxable_gifts', 0)
            cumulative_transfers = net_estate + prior_taxable_gifts

            use_portability = self._get_bool(data, 'use_portability', False)
            deceased_spouse_exemption = self._get_float(data, 'deceased_spouse_exemption', 0)
            available_exemption = self.FEDERAL_EXEMPTION + (deceased_spouse_exemption if use_portability else 0)
            taxable_amount = max(0, cumulative_transfers - available_exemption)

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
                        'bracket': f'${previous_limit:,.0f} - ${limit:,.0f}' if limit != float('inf') else f'Over ${previous_limit:,.0f}',
                        'rate': f'{rate * 100:.0f}%',
                        'taxable_amount': round(bracket_amount, 2),
                        'tax': round(bracket_tax, 2)
                    })
                remaining -= bracket_amount
                previous_limit = limit

            effective_rate = (estate_tax / net_estate * 100) if net_estate > 0 else 0
            state_exemption = 1000000
            state_taxable = max(0, net_estate - state_exemption)
            state_tax_estimate = state_taxable * 0.16 if state_taxable > 0 else 0
            net_to_heirs = net_estate - estate_tax - state_tax_estimate

            strategies = []
            if gross_estate > self.FEDERAL_EXEMPTION:
                strategies.append(str(_('Charitable giving can reduce taxable estate.')))
                strategies.append(str(_('Consider an Irrevocable Life Insurance Trust (ILIT) if you have life insurance.')))
            strategies.append(str(_('Annual gift exclusion can reduce estate over time.')))

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
                    str(_('Federal estate tax exemption for 2024 is $13.61 million.')),
                    str(_('State estate/inheritance taxes vary and may have lower exemptions.'))
                ]
            }
            result['chart_data'] = self._prepare_chart_data(result)
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, result):
        net_to_heirs = result.get('net_to_heirs', 0)
        federal = result.get('federal_estate_tax', 0)
        state = result.get('state_tax_estimate', 0)
        total_ded = result.get('total_deductions', 0)
        if net_to_heirs <= 0 and federal <= 0 and state <= 0 and total_ded <= 0:
            return {}
        labels = [str(_('Net to Heirs')), str(_('Federal Estate Tax')), str(_('State Tax (Est.)')), str(_('Deductions'))]
        values = [round(net_to_heirs, 2), round(federal, 2), round(state, 2), round(total_ded, 2)]
        return {
            'distribution_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': ['#10b981', '#ef4444', '#f59e0b', '#6366f1'],
                        'borderWidth': 0
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {'legend': {'position': 'bottom'}}
                }
            }
        }
