from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import numpy as np


@method_decorator(ensure_csrf_cookie, name='dispatch')
class TipCalculator(View):
    """
    Professional Tip Calculator with Comprehensive Features
    
    This calculator provides tip calculations with:
    - Calculate tip amount and total
    - Split bill among multiple people
    - Round up total option
    - Compare different tip percentages
    - Calculate tip from total (reverse calculation)
    
    Features:
    - Supports multiple calculation modes
    - Handles various currencies
    - Provides step-by-step solutions
    - Interactive visualizations
    """
    template_name = 'other_calculators/tip_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Tip Calculator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'standard')
            
            if calc_type == 'standard':
                return self._calculate_standard(data)
            elif calc_type == 'from_total':
                return self._calculate_from_total(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_standard(self, data):
        """Calculate tip from bill amount"""
        try:
            if 'bill_amount' not in data or data.get('bill_amount') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Bill amount is required.')
                }, status=400)
            
            try:
                bill_amount = float(data.get('bill_amount', 0))
                tip_percent = float(data.get('tip_percent', 15))
                num_people = int(data.get('num_people', 1))
                round_up = data.get('round_up', False)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            currency = data.get('currency', 'usd')
            
            # Validation
            if bill_amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Bill amount must be greater than zero.')
                }, status=400)
            
            if tip_percent < 0 or tip_percent > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Tip percentage must be between 0 and 100.')
                }, status=400)
            
            if num_people < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('Number of people must be at least 1.')
                }, status=400)
            
            # Calculate tip and total
            tip_amount = float(np.multiply(bill_amount, np.divide(tip_percent, 100.0)))
            total = float(np.add(bill_amount, tip_amount))
            
            # Round up if requested
            if round_up:
                total = float(np.ceil(total))
                tip_amount = float(np.subtract(total, bill_amount))
            
            # Calculate per person amounts
            per_person_bill = float(np.divide(bill_amount, num_people))
            per_person_tip = float(np.divide(tip_amount, num_people))
            per_person_total = float(np.divide(total, num_people))
            
            # Calculate different tip scenarios
            tip_scenarios = []
            for pct in [10, 15, 18, 20, 25]:
                scenario_tip = float(np.multiply(bill_amount, np.divide(pct, 100.0)))
                scenario_total = float(np.add(bill_amount, scenario_tip))
                tip_scenarios.append({
                    'percent': pct,
                    'tip': round(scenario_tip, 2),
                    'total': round(scenario_total, 2),
                    'per_person': round(scenario_total / num_people, 2)
                })
            
            steps = self._prepare_standard_steps(bill_amount, tip_percent, tip_amount, total, num_people, per_person_bill, per_person_tip, per_person_total, round_up, currency)
            chart_data = self._prepare_tip_chart_data(bill_amount, tip_amount, total, currency)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'standard',
                'bill_amount': round(bill_amount, 2),
                'tip_percent': tip_percent,
                'tip_amount': round(tip_amount, 2),
                'total': round(total, 2),
                'num_people': num_people,
                'round_up': round_up,
                'currency': currency,
                'per_person': {
                    'bill': round(per_person_bill, 2),
                    'tip': round(per_person_tip, 2),
                    'total': round(per_person_total, 2)
                },
                'tip_scenarios': tip_scenarios,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating tip: {error}').format(error=str(e))
            }, status=500)
    
    def _calculate_from_total(self, data):
        """Calculate tip percentage from total amount"""
        try:
            if 'total_amount' not in data or data.get('total_amount') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Total amount is required.')
                }, status=400)
            
            if 'bill_amount' not in data or data.get('bill_amount') is None:
                return JsonResponse({
                    'success': False,
                    'error': _('Bill amount is required.')
                }, status=400)
            
            try:
                total_amount = float(data.get('total_amount', 0))
                bill_amount = float(data.get('bill_amount', 0))
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid input type. Please enter numeric values.')
                }, status=400)
            
            currency = data.get('currency', 'usd')
            
            # Validate
            if bill_amount <= 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Bill amount must be greater than zero.')
                }, status=400)
            
            if total_amount < bill_amount:
                return JsonResponse({
                    'success': False,
                    'error': _('Total amount must be greater than or equal to bill amount.')
                }, status=400)
            
            # Calculate tip
            tip_amount = float(np.subtract(total_amount, bill_amount))
            tip_percent = float(np.multiply(np.divide(tip_amount, bill_amount), 100.0))
            
            steps = self._prepare_from_total_steps(bill_amount, total_amount, tip_amount, tip_percent, currency)
            chart_data = self._prepare_tip_chart_data(bill_amount, tip_amount, total_amount, currency)
            
            return JsonResponse({
                'success': True,
                'calc_type': 'from_total',
                'bill_amount': round(bill_amount, 2),
                'total_amount': round(total_amount, 2),
                'tip_amount': round(tip_amount, 2),
                'tip_percent': round(tip_percent, 2),
                'currency': currency,
                'step_by_step': steps,
                'chart_data': chart_data,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating from total: {error}').format(error=str(e))
            }, status=500)
    
    # Step-by-step solution preparation methods
    def _prepare_standard_steps(self, bill_amount, tip_percent, tip_amount, total, num_people, per_person_bill, per_person_tip, per_person_total, round_up, currency):
        """Prepare step-by-step solution for standard calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Bill Amount: {amount} {currency}').format(amount=bill_amount, currency=currency.upper()))
        steps.append(_('Tip Percentage: {percent}%').format(percent=tip_percent))
        steps.append(_('Number of People: {num}').format(num=num_people))
        if round_up:
            steps.append(_('Round Up: Yes'))
        steps.append('')
        steps.append(_('Step 2: Calculate tip amount'))
        steps.append(_('Tip Amount = Bill Amount × (Tip Percentage / 100)'))
        steps.append(_('Tip Amount = {bill} × ({percent} / 100)').format(bill=bill_amount, percent=tip_percent))
        steps.append(_('Tip Amount = {tip} {currency}').format(tip=round(tip_amount, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 3: Calculate total'))
        steps.append(_('Total = Bill Amount + Tip Amount'))
        steps.append(_('Total = {bill} + {tip} = {total} {currency}').format(bill=bill_amount, tip=round(tip_amount, 2), total=round(total, 2), currency=currency.upper()))
        if round_up:
            steps.append(_('Rounded Up Total = {total} {currency}').format(total=round(total, 2), currency=currency.upper()))
        steps.append('')
        if num_people > 1:
            steps.append(_('Step 4: Calculate per person amounts'))
            steps.append(_('Per Person Bill = Bill Amount / Number of People'))
            steps.append(_('Per Person Bill = {bill} / {num} = {per_bill} {currency}').format(bill=bill_amount, num=num_people, per_bill=round(per_person_bill, 2), currency=currency.upper()))
            steps.append(_('Per Person Tip = Tip Amount / Number of People'))
            steps.append(_('Per Person Tip = {tip} / {num} = {per_tip} {currency}').format(tip=round(tip_amount, 2), num=num_people, per_tip=round(per_person_tip, 2), currency=currency.upper()))
            steps.append(_('Per Person Total = Total / Number of People'))
            steps.append(_('Per Person Total = {total} / {num} = {per_total} {currency}').format(total=round(total, 2), num=num_people, per_total=round(per_person_total, 2), currency=currency.upper()))
        return steps
    
    def _prepare_from_total_steps(self, bill_amount, total_amount, tip_amount, tip_percent, currency):
        """Prepare step-by-step solution for from total calculation"""
        steps = []
        steps.append(_('Step 1: Identify the given values'))
        steps.append(_('Bill Amount: {amount} {currency}').format(amount=bill_amount, currency=currency.upper()))
        steps.append(_('Total Amount: {amount} {currency}').format(amount=total_amount, currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 2: Calculate tip amount'))
        steps.append(_('Tip Amount = Total Amount - Bill Amount'))
        steps.append(_('Tip Amount = {total} - {bill} = {tip} {currency}').format(total=total_amount, bill=bill_amount, tip=round(tip_amount, 2), currency=currency.upper()))
        steps.append('')
        steps.append(_('Step 3: Calculate tip percentage'))
        steps.append(_('Tip Percentage = (Tip Amount / Bill Amount) × 100'))
        steps.append(_('Tip Percentage = ({tip} / {bill}) × 100').format(tip=round(tip_amount, 2), bill=bill_amount))
        steps.append(_('Tip Percentage = {percent}%').format(percent=round(tip_percent, 2)))
        return steps
    
    # Chart data preparation methods
    def _prepare_tip_chart_data(self, bill_amount, tip_amount, total, currency):
        """Prepare chart data for tip visualization"""
        try:
            chart_config = {
                'type': 'pie',
                'data': {
                    'labels': [_('Bill Amount'), _('Tip Amount')],
                    'datasets': [{
                        'data': [bill_amount, tip_amount],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Bill Breakdown (Total: {total})').format(total=total)
                        }
                    }
                }
            }
            return {'tip_chart': chart_config}
        except Exception as e:
            return None
