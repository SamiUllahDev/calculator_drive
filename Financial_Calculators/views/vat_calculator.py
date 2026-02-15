from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class VatCalculator(View):
    """
    Class-based view for VAT (Value Added Tax) Calculator.
    Add VAT, remove VAT, or find VAT amount. Returns Chart.js-ready chart_data (BMI-style).
    """
    template_name = 'financial_calculators/vat_calculator.html'

    COMMON_VAT_RATES = {
        'uk': 20,
        'germany': 19,
        'france': 20,
        'italy': 22,
        'spain': 21,
        'netherlands': 21,
        'belgium': 21,
        'austria': 20,
        'poland': 23,
        'sweden': 25,
        'denmark': 25,
        'finland': 24,
        'ireland': 23,
        'portugal': 23,
        'greece': 24,
        'hungary': 27,
        'czech': 21,
        'romania': 19,
        'switzerland': 7.7,
        'norway': 25,
        'canada_gst': 5,
        'australia_gst': 10,
        'new_zealand_gst': 15,
        'japan': 10,
        'singapore_gst': 8,
        'india_gst': 18,
        'south_africa': 15,
        'brazil': 17,
        'mexico': 16,
        'uae': 5,
    }

    def get(self, request):
        context = {
            'calculator_name': str(_('VAT Calculator')),
            'vat_rates': self.COMMON_VAT_RATES,
        }
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
            return float(str(value).replace(',', '').replace('$', '').replace('£', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def post(self, request):
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'add_vat')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'add_vat'

            amount = self._get_float(data, 'amount', 0)
            vat_rate = self._get_float(data, 'vat_rate', 20)

            if amount < 0:
                return JsonResponse({'success': False, 'error': str(_('Amount cannot be negative.'))}, status=400)
            if vat_rate < 0 or vat_rate > 100:
                return JsonResponse({'success': False, 'error': str(_('VAT rate must be between 0%% and 100%%.'))}, status=400)

            vat_multiplier = vat_rate / 100

            if calc_type == 'add_vat':
                net_amount = amount
                vat_amount = net_amount * vat_multiplier
                gross_amount = net_amount + vat_amount
                result = {
                    'success': True,
                    'calc_type': 'add_vat',
                    'net_amount': round(net_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'gross_amount': round(gross_amount, 2),
                    'formula': str(_('Gross = Net × (1 + VAT%%)')) + f' = {net_amount:,.2f} × {1 + vat_multiplier:.4f} = {gross_amount:,.2f}'
                }
            elif calc_type == 'remove_vat':
                gross_amount = amount
                net_amount = gross_amount / (1 + vat_multiplier)
                vat_amount = gross_amount - net_amount
                result = {
                    'success': True,
                    'calc_type': 'remove_vat',
                    'gross_amount': round(gross_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'net_amount': round(net_amount, 2),
                    'formula': str(_('Net = Gross ÷ (1 + VAT%%)')) + f' = {gross_amount:,.2f} ÷ {1 + vat_multiplier:.4f} = {net_amount:,.2f}'
                }
            elif calc_type == 'find_vat_only':
                net_amount = amount
                vat_amount = net_amount * vat_multiplier
                result = {
                    'success': True,
                    'calc_type': 'find_vat_only',
                    'net_amount': round(net_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'gross_amount': round(net_amount + vat_amount, 2),
                    'formula': str(_('VAT = Net × VAT%%')) + f' = {net_amount:,.2f} × {vat_multiplier:.4f} = {vat_amount:,.2f}'
                }
            elif calc_type == 'reverse_vat':
                gross_amount = amount
                vat_amount = gross_amount - (gross_amount / (1 + vat_multiplier))
                net_amount = gross_amount - vat_amount
                result = {
                    'success': True,
                    'calc_type': 'reverse_vat',
                    'gross_amount': round(gross_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'net_amount': round(net_amount, 2),
                    'formula': str(_('VAT = Gross - (Gross ÷ (1 + VAT%%))')) + f' = {vat_amount:,.2f}'
                }
            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            comparisons = []
            for country, rate in sorted(self.COMMON_VAT_RATES.items(), key=lambda x: x[1])[:10]:
                if calc_type in ['add_vat', 'find_vat_only']:
                    base = amount
                    vat = base * (rate / 100)
                    total = base + vat
                    comparisons.append({
                        'country': country.replace('_', ' ').title(),
                        'rate': rate,
                        'vat': round(vat, 2),
                        'total': round(total, 2)
                    })
                else:
                    gross = amount
                    net = gross / (1 + rate / 100)
                    vat = gross - net
                    comparisons.append({
                        'country': country.replace('_', ' ').title(),
                        'rate': rate,
                        'vat': round(vat, 2),
                        'net': round(net, 2)
                    })
            result['comparisons'] = comparisons
            result['chart_data'] = self._prepare_chart_data(result)
            return JsonResponse(result, encoder=DjangoJSONEncoder)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, result):
        net = result.get('net_amount', 0)
        vat = result.get('vat_amount', 0)
        if net <= 0 and vat <= 0:
            return {}
        labels = [str(_('Net')), str(_('VAT'))]
        values = [round(net, 2), round(vat, 2)]
        return {
            'breakdown_chart': {
                'type': 'doughnut',
                'data': {
                    'labels': labels,
                    'datasets': [{
                        'data': values,
                        'backgroundColor': ['#10b981', '#ef4444'],
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
