from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import numpy as np
from datetime import datetime

try:
    from dateutil.relativedelta import relativedelta
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False


def add_months(source_date, months):
    """Add months to a date"""
    if HAS_DATEUTIL:
        return source_date + relativedelta(months=months)
    else:
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        day = min(source_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return datetime(year, month, day)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class CreditCardCalculator(View):
    """
    Professional Credit Card Payoff Calculator with comprehensive features.
    
    Features:
    - Minimum payment analysis
    - Fixed payment payoff calculation
    - Target payoff date calculation
    - Payment strategy comparison
    - Interest savings calculator
    - Monthly payment schedule
    """
    template_name = 'financial_calculators/credit_card_calculator.html'
    
    # Validation limits
    MIN_BALANCE = 1
    MAX_BALANCE = 1000000
    MIN_RATE = 0.01
    MAX_RATE = 40
    
    def _get_data(self, request):
        """Parse JSON or form POST into a flat dict."""
        if request.content_type and 'application/json' in request.content_type:
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Credit Card Calculator'),
            'page_title': _('Credit Card Payoff Calculator - Debt Free Calculator'),
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            balance = self._get_float(data, 'balance', 0)
            interest_rate = self._get_float(data, 'interest_rate', 0)
            calc_mode = data.get('calc_mode', 'fixed_payment')
            if isinstance(calc_mode, list):
                calc_mode = calc_mode[0] if calc_mode else 'fixed_payment'

            monthly_payment = self._get_float(data, 'monthly_payment', 0)
            payoff_months = self._get_int(data, 'payoff_months', 0)
            minimum_payment_pct = self._get_float(data, 'minimum_payment_pct', 2)
            minimum_payment_floor = self._get_float(data, 'minimum_payment_floor', 25)

            errors = []

            if balance < self.MIN_BALANCE:
                errors.append(_('Balance must be at least $%(min)s.') % {'min': self.MIN_BALANCE})
            elif balance > self.MAX_BALANCE:
                errors.append(_('Balance cannot exceed $%(max)s.') % {'max': f'{self.MAX_BALANCE:,.0f}'})
            if interest_rate < self.MIN_RATE:
                errors.append(_('Interest rate must be positive.'))
            elif interest_rate > self.MAX_RATE:
                errors.append(_('Interest rate cannot exceed %(max)s%%.') % {'max': self.MAX_RATE})
            if calc_mode == 'fixed_payment':
                monthly_rate = interest_rate / 100 / 12
                min_payment_for_interest = balance * monthly_rate
                if monthly_payment <= min_payment_for_interest:
                    errors.append(_('Payment (%(payment)s) must exceed monthly interest (%(interest)s).') % {
                        'payment': f'${monthly_payment:,.2f}',
                        'interest': f'${min_payment_for_interest:,.2f}',
                    })
            if calc_mode == 'target_date' and payoff_months < 1:
                errors.append(_('Please enter a valid number of months.'))
            if errors:
                return JsonResponse({'success': False, 'error': errors[0]}, status=400)

            if calc_mode == 'fixed_payment':
                result = self._calculate_fixed_payment(balance, interest_rate, monthly_payment)
            elif calc_mode == 'target_date':
                result = self._calculate_target_date(balance, interest_rate, payoff_months)
            elif calc_mode == 'minimum_payment':
                result = self._calculate_minimum_payment(balance, interest_rate, minimum_payment_pct, minimum_payment_floor)
            else:
                return JsonResponse({'success': False, 'error': _('Invalid calculation mode.')}, status=400)
            
            # Add comparison data
            result['comparison'] = self._compare_strategies(balance, interest_rate, result.get('monthly_payment', monthly_payment))
            
            return JsonResponse({
                'success': True,
                **result
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Calculation error. Please check your inputs and try again.')
            }, status=400)

    def _get_float(self, data, key, default=0):
        """Safely get float value (handles list from form POST)."""
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
        """Safely get int value (handles list from form POST)."""
        try:
            value = data.get(key, default)
            if value is None or value == '' or value == 'null':
                return default
            if isinstance(value, list):
                value = value[0] if value else default
            return int(float(str(value).replace(',', '')))
        except (ValueError, TypeError):
            return default
    
    def _calculate_fixed_payment(self, balance, rate, payment):
        """Calculate payoff with fixed monthly payment"""
        monthly_rate = rate / 100 / 12
        
        schedule = []
        current_balance = balance
        total_interest = 0
        month = 0
        max_months = 600  # 50 years max
        
        chart_labels = ['Start']
        chart_balance = [round(balance, 2)]
        
        while current_balance > 0.01 and month < max_months:
            month += 1
            current_date = add_months(datetime.now(), month - 1)
            
            interest = current_balance * monthly_rate
            principal = min(payment - interest, current_balance)
            
            if principal <= 0:
                # Payment doesn't cover interest
                break
            
            actual_payment = min(payment, current_balance + interest)
            current_balance = max(0, current_balance - principal)
            total_interest += interest
            
            schedule.append({
                'month': month,
                'date': current_date.strftime('%b %Y'),
                'payment': round(actual_payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(current_balance, 2),
            })
            
            if month % 6 == 0 or current_balance <= 0.01:
                chart_labels.append(f'Mo {month}')
                chart_balance.append(round(current_balance, 2))
        
        payoff_date = add_months(datetime.now(), month)
        
        return {
            'calc_mode': 'fixed_payment',
            'monthly_payment': round(payment, 2),
            'months_to_payoff': month,
            'total_interest': round(total_interest, 2),
            'total_paid': round(balance + total_interest, 2),
            'payoff_date': payoff_date.strftime('%B %Y'),
            'schedule': schedule[:60],
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
            }
        }
    
    def _calculate_target_date(self, balance, rate, months):
        """Calculate payment needed for target payoff date"""
        monthly_rate = rate / 100 / 12
        
        if monthly_rate > 0:
            rate_factor = np.power(1 + monthly_rate, months)
            payment = balance * (monthly_rate * rate_factor) / (rate_factor - 1)
        else:
            payment = balance / months
        
        # Now calculate with this payment
        result = self._calculate_fixed_payment(balance, rate, payment)
        result['calc_mode'] = 'target_date'
        result['target_months'] = months
        
        return result
    
    def _calculate_minimum_payment(self, balance, rate, min_pct, min_floor):
        """Calculate payoff with minimum payments"""
        monthly_rate = rate / 100 / 12
        
        schedule = []
        current_balance = balance
        total_interest = 0
        total_paid = 0
        month = 0
        max_months = 600
        
        chart_labels = ['Start']
        chart_balance = [round(balance, 2)]
        
        while current_balance > 0.01 and month < max_months:
            month += 1
            current_date = add_months(datetime.now(), month - 1)
            
            # Calculate minimum payment
            pct_payment = current_balance * (min_pct / 100)
            payment = max(pct_payment, min_floor)
            payment = min(payment, current_balance * (1 + monthly_rate))
            
            interest = current_balance * monthly_rate
            principal = payment - interest
            
            if principal <= 0:
                principal = 0
                payment = interest
            
            current_balance = max(0, current_balance - principal)
            total_interest += interest
            total_paid += payment
            
            schedule.append({
                'month': month,
                'date': current_date.strftime('%b %Y'),
                'payment': round(payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(current_balance, 2),
            })
            
            if month % 12 == 0 or current_balance <= 0.01:
                chart_labels.append(f'Mo {month}')
                chart_balance.append(round(current_balance, 2))
        
        payoff_date = add_months(datetime.now(), month)
        first_payment = schedule[0]['payment'] if schedule else 0
        
        return {
            'calc_mode': 'minimum_payment',
            'initial_minimum': round(first_payment, 2),
            'months_to_payoff': month,
            'years_to_payoff': round(month / 12, 1),
            'total_interest': round(total_interest, 2),
            'total_paid': round(total_paid, 2),
            'payoff_date': payoff_date.strftime('%B %Y'),
            'schedule': schedule[:60],
            'chart_data': {
                'labels': chart_labels,
                'balance': chart_balance,
            }
        }
    
    def _compare_strategies(self, balance, rate, current_payment):
        """Compare different payment strategies"""
        strategies = []
        
        min_result = self._calculate_minimum_payment(balance, rate, 2, 25)
        strategies.append({
            'name': _('Minimum Payment'),
            'payment': min_result.get('initial_minimum', 0),
            'months': min_result['months_to_payoff'],
            'total_interest': min_result['total_interest'],
        })
        if current_payment and current_payment > min_result.get('initial_minimum', 0) * 1.1:
            fixed_result = self._calculate_fixed_payment(balance, rate, current_payment)
            strategies.append({
                'name': _('Fixed Payment'),
                'payment': current_payment,
                'months': fixed_result['months_to_payoff'],
                'total_interest': fixed_result['total_interest'],
            })
        double_payment = min_result.get('initial_minimum', 50) * 2
        double_result = self._calculate_fixed_payment(balance, rate, double_payment)
        strategies.append({
            'name': _('Double Minimum'),
            'payment': round(double_payment, 2),
            'months': double_result['months_to_payoff'],
            'total_interest': double_result['total_interest'],
        })
        twelve_result = self._calculate_target_date(balance, rate, 12)
        strategies.append({
            'name': _('12-Month Payoff'),
            'payment': twelve_result['monthly_payment'],
            'months': 12,
            'total_interest': twelve_result['total_interest'],
        })
        twentyfour_result = self._calculate_target_date(balance, rate, 24)
        strategies.append({
            'name': _('24-Month Payoff'),
            'payment': twentyfour_result['monthly_payment'],
            'months': 24,
            'total_interest': twentyfour_result['total_interest'],
        })
        
        return strategies
