from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class FutureValueCalculator(View):
    """
    Class-based view for Future Value Calculator
    Calculates future value of investments with regular contributions.
    """
    template_name = 'financial_calculators/future_value_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Future Value Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            present_value = float(str(data.get('present_value', 0)).replace(',', ''))
            periodic_payment = float(str(data.get('periodic_payment', 0)).replace(',', ''))
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            years = int(data.get('years', 0))
            payment_frequency = data.get('payment_frequency', 'monthly')
            compound_frequency = data.get('compound_frequency', 'monthly')
            payment_timing = data.get('payment_timing', 'end')  # 'end' or 'beginning'
            
            # Validation
            if present_value < 0 or present_value > 1000000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid present value.'}, status=400)
            
            if periodic_payment < 0:
                return JsonResponse({'success': False, 'error': 'Periodic payment cannot be negative.'}, status=400)
            
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0% and 50%.'}, status=400)
            
            if years <= 0 or years > 100:
                return JsonResponse({'success': False, 'error': 'Years must be between 1 and 100.'}, status=400)
            
            # Frequency mapping
            freq_map = {'annually': 1, 'semi-annually': 2, 'quarterly': 4, 'monthly': 12, 'biweekly': 26, 'weekly': 52}
            payment_freq = freq_map.get(payment_frequency, 12)
            compound_freq = freq_map.get(compound_frequency, 12)
            
            rate = interest_rate / 100
            period_rate = rate / compound_freq
            total_periods = compound_freq * years
            
            # Future value of present value
            fv_pv = present_value * ((1 + period_rate) ** total_periods)
            
            # Future value of annuity (periodic payments)
            if rate > 0:
                # Adjust for payment frequency
                pmt_per_compound = periodic_payment * (payment_freq / compound_freq)
                if payment_timing == 'beginning':
                    fv_annuity = pmt_per_compound * (((1 + period_rate) ** total_periods - 1) / period_rate) * (1 + period_rate)
                else:
                    fv_annuity = pmt_per_compound * (((1 + period_rate) ** total_periods - 1) / period_rate)
            else:
                fv_annuity = periodic_payment * payment_freq * years
            
            future_value = fv_pv + fv_annuity
            total_contributions = present_value + (periodic_payment * payment_freq * years)
            total_interest = future_value - total_contributions
            
            # Yearly breakdown
            yearly_data = []
            running_balance = present_value
            running_contributions = present_value
            
            for year in range(1, years + 1):
                # Calculate balance at end of year
                year_periods = compound_freq
                annual_contribution = periodic_payment * payment_freq
                
                # Simple approximation for yearly data
                if rate > 0:
                    year_end_balance = running_balance * ((1 + period_rate) ** year_periods)
                    if payment_timing == 'beginning':
                        year_end_balance += (annual_contribution / year_periods) * (((1 + period_rate) ** year_periods - 1) / period_rate) * (1 + period_rate)
                    else:
                        year_end_balance += (annual_contribution / year_periods) * (((1 + period_rate) ** year_periods - 1) / period_rate)
                else:
                    year_end_balance = running_balance + annual_contribution
                
                running_contributions += annual_contribution
                year_interest = year_end_balance - running_contributions
                
                yearly_data.append({
                    'year': year,
                    'contributions': round(running_contributions, 2),
                    'interest': round(year_interest, 2),
                    'balance': round(year_end_balance, 2)
                })
                
                running_balance = year_end_balance
            
            # Different scenarios
            scenarios = []
            for pmt in [0, 100, 200, 500, 1000]:
                if rate > 0:
                    pmt_per_c = pmt * (12 / compound_freq)
                    fv_a = pmt_per_c * (((1 + period_rate) ** total_periods - 1) / period_rate)
                else:
                    fv_a = pmt * 12 * years
                total_fv = fv_pv + fv_a
                scenarios.append({
                    'payment': pmt,
                    'future_value': round(total_fv, 2),
                    'total_contributed': round(present_value + (pmt * 12 * years), 2)
                })
            
            result = {
                'success': True,
                'summary': {
                    'present_value': round(present_value, 2),
                    'periodic_payment': round(periodic_payment, 2),
                    'interest_rate': round(interest_rate, 3),
                    'years': years,
                    'future_value': round(future_value, 2),
                    'total_contributions': round(total_contributions, 2),
                    'total_interest': round(total_interest, 2),
                    'fv_from_pv': round(fv_pv, 2),
                    'fv_from_payments': round(fv_annuity, 2)
                },
                'yearly_data': yearly_data,
                'scenarios': scenarios,
                'chart_data': {
                    'breakdown': {
                        'contributions': round(total_contributions, 2),
                        'interest': round(total_interest, 2)
                    },
                    'growth': {
                        'labels': [f"Year {d['year']}" for d in yearly_data[:20]],
                        'contributions': [d['contributions'] for d in yearly_data[:20]],
                        'balances': [d['balance'] for d in yearly_data[:20]]
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
