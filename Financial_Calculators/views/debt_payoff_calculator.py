from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta


@method_decorator(ensure_csrf_cookie, name='dispatch')
class DebtPayoffCalculator(View):
    """
    Class-based view for Debt Payoff Calculator
    Calculates time and interest to pay off debt with various strategies.
    """
    template_name = 'financial_calculators/debt_payoff_calculator.html'

    def _get_data(self, request):
        """Parse JSON or form POST into a flat dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def _get_float(self, data, key, default=0):
        """Safely get float from data."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return float(str(value).replace(',', '').replace('$', '').replace('%', ''))
        except (ValueError, TypeError):
            return default

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Debt Payoff Calculator',
            'page_title': 'Debt Payoff Calculator - Pay Off Debt Faster',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            debt_amount = self._get_float(data, 'debt_amount', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            monthly_payment = self._get_float(data, 'monthly_payment', 0)
            extra_payment = self._get_float(data, 'extra_payment', 0)
            
            # Validation
            if debt_amount <= 0 or debt_amount > 10000000:
                return JsonResponse({'success': False, 'error': _('Please enter a valid debt amount.')}, status=400)
            
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': _('Interest rate must be between 0% and 50%.')}, status=400)
            
            if monthly_payment <= 0:
                return JsonResponse({'success': False, 'error': _('Monthly payment must be greater than 0.')}, status=400)
            
            monthly_rate = (interest_rate / 100) / 12
            
            # Check if payment covers interest
            first_month_interest = debt_amount * monthly_rate
            if monthly_payment <= first_month_interest:
                return JsonResponse({
                    'success': False,
                    'error': _('Payment (%(payment)s) must exceed monthly interest (%(interest)s).') % {
                        'payment': f'${monthly_payment:,.2f}',
                        'interest': f'${first_month_interest:,.2f}',
                    }
                }, status=400)
            
            # Calculate without extra payment
            def calculate_payoff(balance, payment, rate):
                months = 0
                total_interest = 0
                schedule = []
                start_date = datetime.now()
                
                while balance > 0.01 and months < 600:  # Max 50 years
                    months += 1
                    interest = balance * rate
                    principal = min(payment - interest, balance)
                    balance = max(0, balance - principal)
                    total_interest += interest
                    
                    if months <= 60:  # First 5 years for schedule
                        current_date = start_date + relativedelta(months=months)
                        schedule.append({
                            'month': months,
                            'date': current_date.strftime('%b %Y'),
                            'payment': round(principal + interest, 2),
                            'principal': round(principal, 2),
                            'interest': round(interest, 2),
                            'balance': round(balance, 2)
                        })
                
                return months, total_interest, schedule
            
            # Standard payoff
            std_months, std_interest, std_schedule = calculate_payoff(
                debt_amount, monthly_payment, monthly_rate
            )
            
            # Accelerated payoff with extra payment
            total_payment = monthly_payment + extra_payment
            acc_months, acc_interest, acc_schedule = calculate_payoff(
                debt_amount, total_payment, monthly_rate
            )
            
            # Calculate savings
            time_saved = std_months - acc_months
            interest_saved = std_interest - acc_interest
            
            # Different payment scenarios
            scenarios = []
            for extra in [0, 50, 100, 200, 300, 500]:
                m, i, _ = calculate_payoff(debt_amount, monthly_payment + extra, monthly_rate)
                scenarios.append({
                    'extra': extra,
                    'total_payment': monthly_payment + extra,
                    'months': m,
                    'years': round(m / 12, 1),
                    'total_interest': round(i, 2),
                    'interest_saved': round(std_interest - i, 2)
                })
            
            # Payoff date
            payoff_date = datetime.now() + relativedelta(months=acc_months)
            
            result = {
                'success': True,
                'summary': {
                    'debt_amount': round(debt_amount, 2),
                    'interest_rate': round(interest_rate, 2),
                    'monthly_payment': round(monthly_payment, 2),
                    'extra_payment': round(extra_payment, 2),
                    'total_payment': round(total_payment, 2),
                    'payoff_months': acc_months,
                    'payoff_years': round(acc_months / 12, 1),
                    'payoff_date': payoff_date.strftime('%B %Y'),
                    'total_interest': round(acc_interest, 2),
                    'total_paid': round(debt_amount + acc_interest, 2),
                    'time_saved': time_saved,
                    'interest_saved': round(interest_saved, 2)
                },
                'comparison': {
                    'standard': {
                        'months': std_months,
                        'interest': round(std_interest, 2)
                    },
                    'accelerated': {
                        'months': acc_months,
                        'interest': round(acc_interest, 2)
                    }
                },
                'scenarios': scenarios,
                'schedule': acc_schedule[:36],
                'chart_data': {
                    'breakdown': {
                        'principal': round(debt_amount, 2),
                        'interest': round(acc_interest, 2)
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': _('Invalid input: %(detail)s') % {'detail': str(e)}}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': _('An error occurred during calculation.')}, status=500)
