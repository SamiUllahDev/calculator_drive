from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DebtConsolidationCalculator(View):
    """
    Class-based view for Debt Consolidation Calculator
    Analyzes consolidating multiple debts into a single loan.
    """
    template_name = 'financial_calculators/debt_consolidation_calculator.html'

    def _get_data(self, request):
        """Parse JSON or form POST into a dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float from data (works with dict or list values)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def _get_int(self, data, key, default=0):
        """Safely get int from data."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Debt Consolidation Calculator'),
            'page_title': _('Debt Consolidation Calculator - Compare Consolidation Options'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for debt consolidation calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            debts = data.get('debts', [])
            if not debts or len(debts) == 0:
                return JsonResponse({'success': False, 'error': _('Please add at least one debt.')}, status=400)

            consolidation_rate = self._get_float(data, 'consolidation_rate', 0)
            consolidation_term = self._get_int(data, 'consolidation_term', 60)
            consolidation_fees = self._get_float(data, 'consolidation_fees', 0)

            # Process existing debts
            debt_details = []
            total_balance = 0
            total_monthly_payment = 0
            weighted_rate_sum = 0

            for debt in debts:
                balance = self._get_float(debt, 'balance', 0)
                rate = self._get_float(debt, 'rate', 0)
                payment = self._get_float(debt, 'payment', 0)
                name = debt.get('name')
                if isinstance(name, list):
                    name = name[0] if name else ''
                name = (name or '').strip() or _('Debt %(number)s') % {'number': len(debt_details) + 1}

                if balance <= 0:
                    continue

                # Calculate payoff time and total interest for this debt
                monthly_rate = rate / 100 / 12
                months = 0
                remaining = balance
                total_interest = 0

                while remaining > 0 and months < 600:
                    interest = remaining * monthly_rate
                    principal = payment - interest
                    if principal <= 0:
                        months = 999  # Infinite - payment too low
                        break
                    remaining -= principal
                    total_interest += interest
                    months += 1

                total_balance += balance
                total_monthly_payment += payment
                weighted_rate_sum += balance * rate

                debt_details.append({
                    'name': name,
                    'balance': round(balance, 2),
                    'rate': rate,
                    'payment': round(payment, 2),
                    'months_to_payoff': months if months < 999 else 'N/A',
                    'total_interest': round(total_interest, 2) if months < 999 else 'N/A',
                    'total_cost': round(balance + total_interest, 2) if months < 999 else 'N/A'
                })

            if total_balance <= 0:
                return JsonResponse({'success': False, 'error': _('Total debt balance must be greater than zero.')}, status=400)

            # Weighted average interest rate
            weighted_avg_rate = weighted_rate_sum / total_balance if total_balance > 0 else 0

            # Calculate current situation totals
            current_total_interest = sum([d['total_interest'] for d in debt_details if d['total_interest'] != 'N/A'])
            current_max_months = max([d['months_to_payoff'] for d in debt_details if d['months_to_payoff'] != 'N/A'], default=0)

            # Consolidation loan calculation
            consolidation_balance = total_balance + consolidation_fees
            monthly_rate_consol = consolidation_rate / 100 / 12

            if monthly_rate_consol > 0:
                consolidation_payment = consolidation_balance * (monthly_rate_consol * np.power(1 + monthly_rate_consol, consolidation_term)) / (np.power(1 + monthly_rate_consol, consolidation_term) - 1)
            else:
                consolidation_payment = consolidation_balance / consolidation_term

            consolidation_total = consolidation_payment * consolidation_term
            consolidation_interest = consolidation_total - consolidation_balance

            # Comparison
            monthly_savings = total_monthly_payment - consolidation_payment
            total_interest_savings = current_total_interest - consolidation_interest
            time_difference = current_max_months - consolidation_term

            # Break-even analysis (if there are upfront fees)
            if consolidation_fees > 0 and monthly_savings > 0:
                break_even_months = consolidation_fees / monthly_savings
            else:
                break_even_months = 0

            # Generate amortization schedule for consolidated loan
            schedule = []
            balance = consolidation_balance
            total_int_paid = 0

            for month in range(1, consolidation_term + 1):
                interest = balance * monthly_rate_consol
                principal = consolidation_payment - interest
                if principal > balance:
                    principal = balance
                balance = max(0, balance - principal)
                total_int_paid += interest

                if month <= 12 or month % 12 == 0 or month == consolidation_term:
                    schedule.append({
                        'month': month,
                        'payment': round(consolidation_payment, 2),
                        'principal': round(principal, 2),
                        'interest': round(interest, 2),
                        'balance': round(balance, 2),
                        'total_interest': round(total_int_paid, 2)
                    })

            # Recommendation
            if total_interest_savings > 0 and monthly_savings > 0:
                recommendation = _("Consolidation is beneficial - you'll save money and pay off debt faster.")
                recommendation_class = "positive"
            elif total_interest_savings > 0:
                recommendation = _("Consolidation saves interest but increases monthly payment.")
                recommendation_class = "neutral"
            elif monthly_savings > 0:
                recommendation = _("Consolidation lowers monthly payment but costs more in total interest.")
                recommendation_class = "neutral"
            else:
                recommendation = _("Consolidation may not be beneficial with these terms.")
                recommendation_class = "negative"

            result = {
                'success': True,
                'current_debts': {
                    'details': debt_details,
                    'total_balance': round(total_balance, 2),
                    'total_monthly_payment': round(total_monthly_payment, 2),
                    'weighted_avg_rate': round(weighted_avg_rate, 2),
                    'total_interest': round(current_total_interest, 2),
                    'longest_payoff_months': current_max_months,
                    'longest_payoff_years': round(current_max_months / 12, 1)
                },
                'consolidation_loan': {
                    'total_balance': round(consolidation_balance, 2),
                    'original_debt': round(total_balance, 2),
                    'fees': round(consolidation_fees, 2),
                    'interest_rate': consolidation_rate,
                    'term_months': consolidation_term,
                    'term_years': round(consolidation_term / 12, 1),
                    'monthly_payment': round(consolidation_payment, 2),
                    'total_interest': round(consolidation_interest, 2),
                    'total_cost': round(consolidation_total, 2)
                },
                'comparison': {
                    'monthly_savings': round(monthly_savings, 2),
                    'total_interest_savings': round(total_interest_savings, 2),
                    'time_difference_months': time_difference,
                    'rate_difference': round(weighted_avg_rate - consolidation_rate, 2),
                    'break_even_months': round(break_even_months, 1) if break_even_months > 0 else None
                },
                'recommendation': recommendation,
                'recommendation_class': recommendation_class,
                'schedule': schedule,
                'chart_data': {
                    'current_interest': round(current_total_interest, 2),
                    'consolidation_interest': round(consolidation_interest, 2),
                    'current_principal': round(total_balance, 2),
                    'consolidation_principal': round(consolidation_balance, 2)
                }
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
