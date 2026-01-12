from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class PresentValueCalculator(View):
    """
    Class-based view for Present Value Calculator
    Calculates present value of future cash flows.
    """
    template_name = 'financial_calculators/present_value_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Present Value Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            future_value = float(str(data.get('future_value', 0)).replace(',', ''))
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            years = int(data.get('years', 0))
            compound_frequency = data.get('compound_frequency', 'monthly')
            
            # Validation
            if future_value <= 0 or future_value > 1000000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid future value.'}, status=400)
            
            if interest_rate < 0 or interest_rate > 50:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0% and 50%.'}, status=400)
            
            if years <= 0 or years > 100:
                return JsonResponse({'success': False, 'error': 'Years must be between 1 and 100.'}, status=400)
            
            # Frequency mapping
            freq_map = {'annually': 1, 'semi-annually': 2, 'quarterly': 4, 'monthly': 12, 'daily': 365}
            n = freq_map.get(compound_frequency, 12)
            
            rate = interest_rate / 100
            
            # Present Value = FV / (1 + r/n)^(n*t)
            present_value = future_value / ((1 + rate/n) ** (n * years))
            
            # Calculate discount amount
            discount = future_value - present_value
            
            # Effective rate
            effective_rate = ((1 + rate/n) ** n - 1) * 100
            
            # Yearly breakdown
            yearly_data = []
            for year in range(1, years + 1):
                pv_at_year = future_value / ((1 + rate/n) ** (n * (years - year + 1)))
                yearly_data.append({
                    'year': year,
                    'years_from_now': years - year + 1,
                    'present_value': round(pv_at_year, 2),
                    'discount_factor': round(1 / ((1 + rate/n) ** (n * (years - year + 1))), 4)
                })
            
            # Compare different rates
            comparison = []
            for r in [3, 5, 7, 10, 12, 15]:
                rate_dec = r / 100
                pv = future_value / ((1 + rate_dec/n) ** (n * years))
                comparison.append({
                    'rate': r,
                    'present_value': round(pv, 2),
                    'discount': round(future_value - pv, 2)
                })
            
            result = {
                'success': True,
                'summary': {
                    'future_value': round(future_value, 2),
                    'present_value': round(present_value, 2),
                    'discount': round(discount, 2),
                    'interest_rate': round(interest_rate, 3),
                    'effective_rate': round(effective_rate, 3),
                    'years': years,
                    'discount_factor': round(present_value / future_value, 4)
                },
                'yearly_data': yearly_data,
                'comparison': comparison,
                'chart_data': {
                    'breakdown': {
                        'present_value': round(present_value, 2),
                        'discount': round(discount, 2)
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
