from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.core.serializers.json import DjangoJSONEncoder
import json


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CommissionCalculator(View):
    """
    Class-based view for Commission Calculator.
    Calculates sales commissions with simple, tiered, base plus, draw against, and reverse structures.
    Returns Chart.js-ready chart_data where applicable (BMI-style).
    """
    template_name = 'financial_calculators/commission_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Commission Calculator'),
            'page_title': _('Commission Calculator - Calculate Sales Commission'),
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
        """Handle POST request for commission calculations"""
        try:
            data = self._get_data(request)
            if not data:
                return JsonResponse({'success': False, 'error': str(_('Invalid request data.'))}, status=400)

            calc_type = data.get('calc_type', 'simple')
            if isinstance(calc_type, list):
                calc_type = calc_type[0] if calc_type else 'simple'

            if calc_type == 'simple':
                sales_amount = self._get_float(data, 'sales_amount', 0)
                commission_rate = self._get_float(data, 'commission_rate', 0)
                if sales_amount < 0:
                    return JsonResponse({'success': False, 'error': str(_('Sales amount cannot be negative.'))}, status=400)
                if commission_rate < 0 or commission_rate > 100:
                    return JsonResponse({'success': False, 'error': str(_('Commission rate must be between 0%% and 100%%.'))}, status=400)
                commission = sales_amount * (commission_rate / 100)
                result = {
                    'success': True,
                    'calc_type': 'simple',
                    'sales_amount': round(sales_amount, 2),
                    'commission_rate': commission_rate,
                    'commission': round(commission, 2),
                    'net_to_company': round(sales_amount - commission, 2),
                    'formula': f'Commission = ${sales_amount:,.2f} × {commission_rate}% = ${commission:,.2f}'
                }
                result['chart_data'] = self._prepare_chart_data('simple', result)

            elif calc_type == 'tiered':
                sales_amount = self._get_float(data, 'sales_amount', 0)
                tiers = data.get('tiers', [])
                if sales_amount < 0:
                    return JsonResponse({'success': False, 'error': str(_('Sales amount cannot be negative.'))}, status=400)
                if not tiers:
                    tiers = [
                        {'min': 0, 'max': 10000, 'rate': 5},
                        {'min': 10000, 'max': 25000, 'rate': 7},
                        {'min': 25000, 'max': 50000, 'rate': 10},
                        {'min': 50000, 'max': None, 'rate': 12}
                    ]
                total_commission = 0
                breakdown = []
                remaining = sales_amount
                for tier in tiers:
                    tier_min = self._get_float(tier, 'min', 0)
                    tier_max = tier.get('max')
                    tier_rate = self._get_float(tier, 'rate', 0)
                    if tier_max is not None:
                        tier_max = float(tier_max)
                        tier_amount = min(remaining, max(0, tier_max - tier_min))
                    else:
                        tier_amount = max(0, remaining)
                    if tier_amount > 0 and sales_amount > tier_min:
                        comm = tier_amount * (tier_rate / 100)
                        total_commission += comm
                        breakdown.append({
                            'range': f'${tier_min:,.0f} - ${tier_max:,.0f}' if tier_max else f'${tier_min:,.0f}+',
                            'amount': round(tier_amount, 2),
                            'rate': tier_rate,
                            'commission': round(comm, 2)
                        })
                        remaining -= tier_amount
                    if remaining <= 0:
                        break
                effective_rate = (total_commission / sales_amount * 100) if sales_amount > 0 else 0
                result = {
                    'success': True,
                    'calc_type': 'tiered',
                    'sales_amount': round(sales_amount, 2),
                    'total_commission': round(total_commission, 2),
                    'effective_rate': round(effective_rate, 2),
                    'breakdown': breakdown,
                    'net_to_company': round(sales_amount - total_commission, 2)
                }
                result['chart_data'] = self._prepare_chart_data('tiered', result)

            elif calc_type == 'base_plus_commission':
                base_salary = self._get_float(data, 'base_salary', 0)
                sales_amount = self._get_float(data, 'sales_amount', 0)
                commission_rate = self._get_float(data, 'commission_rate', 0)
                quota = self._get_float(data, 'quota', 0)
                if base_salary < 0 or sales_amount < 0:
                    return JsonResponse({'success': False, 'error': str(_('Values cannot be negative.'))}, status=400)
                commission = sales_amount * (commission_rate / 100)
                total_earnings = base_salary + commission
                quota_achievement = (sales_amount / quota * 100) if quota > 0 else 0
                bonus = 0
                if quota > 0 and sales_amount > quota:
                    bonus = (sales_amount - quota) * 0.05
                result = {
                    'success': True,
                    'calc_type': 'base_plus_commission',
                    'base_salary': round(base_salary, 2),
                    'sales_amount': round(sales_amount, 2),
                    'commission_rate': commission_rate,
                    'commission': round(commission, 2),
                    'quota': round(quota, 2),
                    'quota_achievement': round(quota_achievement, 2),
                    'bonus': round(bonus, 2),
                    'total_earnings': round(total_earnings + bonus, 2),
                    'breakdown': {
                        'base': round(base_salary, 2),
                        'commission': round(commission, 2),
                        'bonus': round(bonus, 2),
                        'total': round(total_earnings + bonus, 2)
                    }
                }
                result['chart_data'] = self._prepare_chart_data('base_plus_commission', result)

            elif calc_type == 'draw_against':
                draw_amount = self._get_float(data, 'draw_amount', 0)
                sales_amount = self._get_float(data, 'sales_amount', 0)
                commission_rate = self._get_float(data, 'commission_rate', 0)
                if draw_amount < 0 or sales_amount < 0:
                    return JsonResponse({'success': False, 'error': str(_('Values cannot be negative.'))}, status=400)
                commission_earned = sales_amount * (commission_rate / 100)
                if commission_earned >= draw_amount:
                    payout = commission_earned - draw_amount
                    carry_forward = 0
                    status = 'earned_over_draw'
                else:
                    payout = 0
                    carry_forward = draw_amount - commission_earned
                    status = 'under_draw'
                result = {
                    'success': True,
                    'calc_type': 'draw_against',
                    'draw_amount': round(draw_amount, 2),
                    'sales_amount': round(sales_amount, 2),
                    'commission_rate': commission_rate,
                    'commission_earned': round(commission_earned, 2),
                    'payout': round(payout, 2),
                    'carry_forward': round(carry_forward, 2),
                    'status': status,
                    'message': f'Commission (${commission_earned:,.2f}) {"exceeds" if status == "earned_over_draw" else "is below"} draw (${draw_amount:,.2f})'
                }
                result['chart_data'] = self._prepare_chart_data('draw_against', result)

            elif calc_type == 'reverse':
                desired_commission = self._get_float(data, 'desired_commission', 0)
                commission_rate = self._get_float(data, 'commission_rate', 0)
                if desired_commission < 0:
                    return JsonResponse({'success': False, 'error': str(_('Desired commission cannot be negative.'))}, status=400)
                if commission_rate <= 0:
                    return JsonResponse({'success': False, 'error': str(_('Commission rate must be greater than 0%%.'))}, status=400)
                sales_needed = desired_commission / (commission_rate / 100)
                result = {
                    'success': True,
                    'calc_type': 'reverse',
                    'desired_commission': round(desired_commission, 2),
                    'commission_rate': commission_rate,
                    'sales_needed': round(sales_needed, 2),
                    'formula': f'Sales Needed = ${desired_commission:,.2f} ÷ {commission_rate}% = ${sales_needed:,.2f}'
                }
                result['chart_data'] = self._prepare_chart_data('reverse', result)

            else:
                return JsonResponse({'success': False, 'error': str(_('Invalid calculation type.'))}, status=400)

            if 'chart_data' not in result:
                result['chart_data'] = {}
            return JsonResponse(result, encoder=DjangoJSONEncoder)

        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': str(_('Invalid input. Please check your numbers.'))}, status=400)
        except Exception:
            return JsonResponse({'success': False, 'error': str(_('An error occurred during calculation.'))}, status=500)

    def _prepare_chart_data(self, calc_type, result):
        """Build Chart.js-ready chart_data (breakdown doughnut) where applicable."""
        commission_label = str(_('Commission'))
        net_label = str(_('Net to Company'))
        base_label = str(_('Base'))
        bonus_label = str(_('Bonus'))
        payout_label = str(_('Payout'))
        carry_label = str(_('Carry Forward'))

        if calc_type == 'simple':
            comm_val = float(result.get('commission', 0))
            net_val = float(result.get('net_to_company', 0))
            if comm_val <= 0 and net_val <= 0:
                return {}
            return {
                'breakdown_chart': {
                    'type': 'doughnut',
                    'data': {
                        'labels': [commission_label, net_label],
                        'datasets': [{'data': [round(comm_val, 2), round(net_val, 2)], 'backgroundColor': ['#8b5cf6', '#10b981'], 'borderWidth': 0}],
                    },
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
                }
            }
        if calc_type == 'tiered' and result.get('breakdown'):
            labels = [t.get('range', '') for t in result['breakdown']]
            values = [float(t.get('commission', 0)) for t in result['breakdown']]
            if not values or sum(values) == 0:
                return {}
            colors = ['#6366f1', '#8b5cf6', '#a855f7', '#c084fc', '#d8b4fe'][:len(labels)]
            return {
                'breakdown_chart': {
                    'type': 'doughnut',
                    'data': {'labels': labels, 'datasets': [{'data': values, 'backgroundColor': colors, 'borderWidth': 0}]},
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
                }
            }
        if calc_type == 'base_plus_commission':
            b = result.get('breakdown', {})
            base_val = float(b.get('base', 0))
            comm_val = float(b.get('commission', 0))
            bonus_val = float(b.get('bonus', 0))
            if base_val <= 0 and comm_val <= 0 and bonus_val <= 0:
                return {}
            labels = [base_label, commission_label]
            values = [base_val, comm_val]
            if bonus_val > 0:
                labels.append(bonus_label)
                values.append(bonus_val)
            return {
                'breakdown_chart': {
                    'type': 'doughnut',
                    'data': {
                        'labels': labels,
                        'datasets': [{'data': [round(x, 2) for x in values], 'backgroundColor': ['#3b82f6', '#8b5cf6', '#f59e0b'], 'borderWidth': 0}],
                    },
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
                }
            }
        if calc_type == 'draw_against':
            payout_val = float(result.get('payout', 0))
            carry_val = float(result.get('carry_forward', 0))
            if payout_val <= 0 and carry_val <= 0:
                return {}
            return {
                'breakdown_chart': {
                    'type': 'doughnut',
                    'data': {
                        'labels': [payout_label, carry_label],
                        'datasets': [{'data': [round(payout_val, 2), round(carry_val, 2)], 'backgroundColor': ['#10b981', '#f59e0b'], 'borderWidth': 0}],
                    },
                    'options': {'responsive': True, 'maintainAspectRatio': False, 'plugins': {'legend': {'position': 'bottom'}}},
                }
            }
        return {}
