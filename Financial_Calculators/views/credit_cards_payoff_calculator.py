from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta


class CreditCardsPayoffCalculator(View):
    """
    Class-based view for Credit Cards Payoff Calculator
    Calculates payoff time, interest paid, and provides debt payoff strategies.
    """
    template_name = 'financial_calculators/credit_cards_payoff_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Credit Cards Payoff Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for credit card payoff calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'single_card')
            
            if calc_type == 'single_card':
                # Single card payoff calculation
                balance = float(str(data.get('balance', 0)).replace(',', ''))
                apr = float(str(data.get('apr', 0)).replace(',', ''))
                min_payment_pct = float(str(data.get('min_payment_pct', 2)).replace(',', ''))
                fixed_payment = float(str(data.get('fixed_payment', 0)).replace(',', ''))
                
                # Validation
                if balance <= 0:
                    return JsonResponse({'success': False, 'error': 'Balance must be greater than zero.'}, status=400)
                if apr < 0 or apr > 100:
                    return JsonResponse({'success': False, 'error': 'APR must be between 0% and 100%.'}, status=400)
                
                monthly_rate = apr / 100 / 12
                min_payment = max(25, balance * (min_payment_pct / 100))
                
                # Calculate with minimum payments only
                min_schedule = self._calculate_payoff(balance, monthly_rate, min_payment_pct, is_fixed=False)
                
                # Calculate with fixed payment if provided
                fixed_schedule = None
                savings = {}
                if fixed_payment > 0 and fixed_payment > min_payment:
                    fixed_schedule = self._calculate_payoff(balance, monthly_rate, fixed_payment, is_fixed=True)
                    savings = {
                        'months_saved': min_schedule['months'] - fixed_schedule['months'],
                        'interest_saved': round(min_schedule['total_interest'] - fixed_schedule['total_interest'], 2),
                        'total_saved': round(min_schedule['total_paid'] - fixed_schedule['total_paid'], 2)
                    }
                
                result = {
                    'success': True,
                    'calc_type': 'single_card',
                    'balance': round(balance, 2),
                    'apr': apr,
                    'monthly_rate': round(monthly_rate * 100, 4),
                    'minimum_payment': {
                        'months': min_schedule['months'],
                        'years': round(min_schedule['months'] / 12, 1),
                        'total_interest': round(min_schedule['total_interest'], 2),
                        'total_paid': round(min_schedule['total_paid'], 2),
                        'payoff_date': min_schedule['payoff_date']
                    },
                    'schedule': min_schedule['schedule'][:60]  # First 60 months
                }
                
                if fixed_schedule:
                    result['fixed_payment'] = {
                        'amount': round(fixed_payment, 2),
                        'months': fixed_schedule['months'],
                        'years': round(fixed_schedule['months'] / 12, 1),
                        'total_interest': round(fixed_schedule['total_interest'], 2),
                        'total_paid': round(fixed_schedule['total_paid'], 2),
                        'payoff_date': fixed_schedule['payoff_date']
                    }
                    result['savings'] = savings
                
            elif calc_type == 'multiple_cards':
                # Multiple cards - debt snowball/avalanche
                cards = data.get('cards', [])
                strategy = data.get('strategy', 'avalanche')  # avalanche (highest APR) or snowball (lowest balance)
                extra_payment = float(str(data.get('extra_payment', 0)).replace(',', ''))
                
                if not cards or len(cards) == 0:
                    return JsonResponse({'success': False, 'error': 'Please add at least one credit card.'}, status=400)
                
                # Parse and validate cards
                parsed_cards = []
                for i, card in enumerate(cards):
                    card_balance = float(str(card.get('balance', 0)).replace(',', ''))
                    card_apr = float(str(card.get('apr', 0)).replace(',', ''))
                    card_min = float(str(card.get('min_payment', 0)).replace(',', ''))
                    card_name = card.get('name', f'Card {i+1}')
                    
                    if card_balance > 0:
                        parsed_cards.append({
                            'name': card_name,
                            'balance': card_balance,
                            'apr': card_apr,
                            'min_payment': max(25, card_min) if card_min > 0 else max(25, card_balance * 0.02),
                            'monthly_rate': card_apr / 100 / 12
                        })
                
                if not parsed_cards:
                    return JsonResponse({'success': False, 'error': 'No valid card balances found.'}, status=400)
                
                # Sort cards by strategy
                if strategy == 'avalanche':
                    parsed_cards.sort(key=lambda x: x['apr'], reverse=True)
                else:  # snowball
                    parsed_cards.sort(key=lambda x: x['balance'])
                
                # Calculate payoff with strategy
                payoff_result = self._calculate_multi_card_payoff(parsed_cards, extra_payment, strategy)
                
                result = {
                    'success': True,
                    'calc_type': 'multiple_cards',
                    'strategy': strategy,
                    'extra_payment': round(extra_payment, 2),
                    'total_balance': round(sum(c['balance'] for c in parsed_cards), 2),
                    'total_min_payments': round(sum(c['min_payment'] for c in parsed_cards), 2),
                    'cards_count': len(parsed_cards),
                    'payoff': payoff_result,
                    'cards_order': [{'name': c['name'], 'balance': c['balance'], 'apr': c['apr']} for c in parsed_cards]
                }
                
            elif calc_type == 'payoff_goal':
                # Calculate payment needed to reach payoff goal
                balance = float(str(data.get('balance', 0)).replace(',', ''))
                apr = float(str(data.get('apr', 0)).replace(',', ''))
                target_months = int(data.get('target_months', 12))
                
                if balance <= 0:
                    return JsonResponse({'success': False, 'error': 'Balance must be greater than zero.'}, status=400)
                if target_months <= 0:
                    return JsonResponse({'success': False, 'error': 'Target months must be at least 1.'}, status=400)
                
                monthly_rate = apr / 100 / 12
                
                # Calculate required payment using PMT formula
                if monthly_rate > 0:
                    required_payment = balance * (monthly_rate * np.power(1 + monthly_rate, target_months)) / (np.power(1 + monthly_rate, target_months) - 1)
                else:
                    required_payment = balance / target_months
                
                total_paid = required_payment * target_months
                total_interest = total_paid - balance
                
                result = {
                    'success': True,
                    'calc_type': 'payoff_goal',
                    'balance': round(balance, 2),
                    'apr': apr,
                    'target_months': target_months,
                    'required_payment': round(required_payment, 2),
                    'total_interest': round(total_interest, 2),
                    'total_paid': round(total_paid, 2),
                    'payoff_date': (datetime.now() + relativedelta(months=target_months)).strftime('%B %Y')
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
    
    def _calculate_payoff(self, balance, monthly_rate, payment_value, is_fixed=True):
        """Calculate payoff schedule"""
        schedule = []
        current_balance = balance
        total_interest = 0
        total_paid = 0
        month = 0
        max_months = 600  # 50 years cap
        
        while current_balance > 0.01 and month < max_months:
            month += 1
            
            # Calculate interest
            interest = current_balance * monthly_rate
            total_interest += interest
            
            # Determine payment
            if is_fixed:
                payment = min(payment_value, current_balance + interest)
            else:
                min_pmt = max(25, current_balance * (payment_value / 100))
                payment = min(min_pmt, current_balance + interest)
            
            principal = payment - interest
            current_balance = max(0, current_balance - principal)
            total_paid += payment
            
            schedule.append({
                'month': month,
                'payment': round(payment, 2),
                'principal': round(principal, 2),
                'interest': round(interest, 2),
                'balance': round(current_balance, 2)
            })
        
        payoff_date = (datetime.now() + relativedelta(months=month)).strftime('%B %Y')
        
        return {
            'months': month,
            'total_interest': total_interest,
            'total_paid': total_paid,
            'payoff_date': payoff_date,
            'schedule': schedule
        }
    
    def _calculate_multi_card_payoff(self, cards, extra_payment, strategy):
        """Calculate multi-card payoff with snowball/avalanche strategy"""
        # Make copies to track balances
        card_balances = [{'name': c['name'], 'balance': c['balance'], 'apr': c['apr'], 
                         'min_payment': c['min_payment'], 'monthly_rate': c['monthly_rate']} for c in cards]
        
        total_paid = 0
        total_interest = 0
        month = 0
        max_months = 600
        paid_off_order = []
        
        while any(c['balance'] > 0.01 for c in card_balances) and month < max_months:
            month += 1
            
            # Calculate total minimum payments
            active_mins = sum(c['min_payment'] for c in card_balances if c['balance'] > 0.01)
            
            # Available extra payment (from paid off cards + extra)
            freed_payments = sum(c['min_payment'] for c in card_balances if c['balance'] <= 0.01)
            total_extra = extra_payment + freed_payments
            
            for card in card_balances:
                if card['balance'] <= 0.01:
                    continue
                
                # Calculate interest
                interest = card['balance'] * card['monthly_rate']
                total_interest += interest
                
                # Determine payment
                payment = card['min_payment']
                
                # Add extra to first unpaid card (based on strategy order)
                if total_extra > 0 and card == next((c for c in card_balances if c['balance'] > 0.01), None):
                    payment += total_extra
                    total_extra = 0
                
                payment = min(payment, card['balance'] + interest)
                principal = payment - interest
                card['balance'] = max(0, card['balance'] - principal)
                total_paid += payment
                
                # Track when card is paid off
                if card['balance'] <= 0.01 and card['name'] not in [p['name'] for p in paid_off_order]:
                    paid_off_order.append({
                        'name': card['name'],
                        'month': month,
                        'date': (datetime.now() + relativedelta(months=month)).strftime('%B %Y')
                    })
        
        payoff_date = (datetime.now() + relativedelta(months=month)).strftime('%B %Y')
        
        return {
            'months': month,
            'years': round(month / 12, 1),
            'total_interest': round(total_interest, 2),
            'total_paid': round(total_paid, 2),
            'payoff_date': payoff_date,
            'paid_off_order': paid_off_order
        }
