from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np
from sympy import Float, N, symbols, solve


class AnnuityPayoutCalculator(View):
    """
    Class-based view for Annuity Payout Calculator
    Calculates annuity payments and values using NumPy/SymPy.
    """
    template_name = 'financial_calculators/annuity_payout_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Annuity Payout Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'payout')  # payout, present_value, or future_value
            
            principal = float(data.get('principal', 100000))
            annual_rate = float(data.get('annual_rate', 5))
            years = int(data.get('years', 20))
            payment_frequency = data.get('payment_frequency', 'monthly')  # monthly, quarterly, annually
            annuity_type = data.get('annuity_type', 'ordinary')  # ordinary or due
            
            # Validation
            if principal <= 0:
                return JsonResponse({'success': False, 'error': 'Principal must be greater than zero.'}, status=400)
            if annual_rate < 0 or annual_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0 and 50%.'}, status=400)
            if years < 1 or years > 100:
                return JsonResponse({'success': False, 'error': 'Years must be between 1 and 100.'}, status=400)
            
            # Calculate periods and periodic rate
            periods_per_year = {'monthly': 12, 'quarterly': 4, 'annually': 1}
            n_per_year = periods_per_year.get(payment_frequency, 12)
            n_total = years * n_per_year
            periodic_rate = (annual_rate / 100) / n_per_year
            
            # Using NumPy for calculations
            if periodic_rate > 0:
                # Present Value of Ordinary Annuity factor
                pvifa = (1 - np.power(1 + periodic_rate, -n_total)) / periodic_rate
                
                # Future Value of Ordinary Annuity factor
                fvifa = (np.power(1 + periodic_rate, n_total) - 1) / periodic_rate
                
                # Adjustment for annuity due (payments at beginning)
                if annuity_type == 'due':
                    pvifa *= (1 + periodic_rate)
                    fvifa *= (1 + periodic_rate)
                
                # Calculate periodic payment (given present value)
                if calc_type == 'payout':
                    periodic_payment = principal / pvifa
                    total_received = periodic_payment * n_total
                    total_interest = total_received - principal
                    
                    result = {
                        'success': True,
                        'calc_type': 'payout',
                        'periodic_payment': round(periodic_payment, 2),
                        'total_received': round(total_received, 2),
                        'total_interest': round(total_interest, 2),
                        'principal': round(principal, 2)
                    }
                
                elif calc_type == 'present_value':
                    periodic_payment = float(data.get('periodic_payment', 1000))
                    present_value = periodic_payment * pvifa
                    total_payments = periodic_payment * n_total
                    
                    result = {
                        'success': True,
                        'calc_type': 'present_value',
                        'present_value': round(present_value, 2),
                        'periodic_payment': round(periodic_payment, 2),
                        'total_payments': round(total_payments, 2)
                    }
                
                elif calc_type == 'future_value':
                    periodic_payment = float(data.get('periodic_payment', 1000))
                    future_value = periodic_payment * fvifa
                    total_contributions = periodic_payment * n_total
                    total_interest = future_value - total_contributions
                    
                    result = {
                        'success': True,
                        'calc_type': 'future_value',
                        'future_value': round(future_value, 2),
                        'periodic_payment': round(periodic_payment, 2),
                        'total_contributions': round(total_contributions, 2),
                        'total_interest': round(total_interest, 2)
                    }
                else:
                    return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            else:
                # Zero interest rate case
                if calc_type == 'payout':
                    periodic_payment = principal / n_total
                    result = {
                        'success': True,
                        'calc_type': 'payout',
                        'periodic_payment': round(periodic_payment, 2),
                        'total_received': round(principal, 2),
                        'total_interest': 0,
                        'principal': round(principal, 2)
                    }
                else:
                    return JsonResponse({'success': False, 'error': 'Zero interest not supported for this calculation.'}, status=400)
            
            # Add common fields
            result.update({
                'annual_rate': annual_rate,
                'years': years,
                'payment_frequency': payment_frequency,
                'annuity_type': annuity_type,
                'periods_per_year': n_per_year,
                'total_periods': n_total,
                'periodic_rate': round(periodic_rate * 100, 4)
            })
            
            # Generate payment schedule (first 12 periods or all if less)
            schedule = []
            remaining = principal
            for i in range(min(12, n_total)):
                if calc_type == 'payout':
                    interest = remaining * periodic_rate
                    principal_portion = periodic_payment - interest if periodic_payment > interest else remaining
                    remaining -= principal_portion
                    schedule.append({
                        'period': i + 1,
                        'payment': round(periodic_payment, 2),
                        'interest': round(interest, 2),
                        'principal': round(principal_portion, 2),
                        'remaining': round(max(0, remaining), 2)
                    })
            
            result['schedule'] = schedule
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred.'}, status=500)
