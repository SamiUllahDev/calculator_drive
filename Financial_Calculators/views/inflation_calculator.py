from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class InflationCalculator(View):
    """
    Class-based view for Inflation Calculator
    Calculates the effect of inflation on purchasing power over time.
    """
    template_name = 'financial_calculators/inflation_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Inflation Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            amount = float(str(data.get('amount', 0)).replace(',', ''))
            inflation_rate = float(str(data.get('inflation_rate', 0)).replace(',', ''))
            years = int(data.get('years', 0))
            calc_type = data.get('calc_type', 'future')  # 'future' or 'past'
            
            # Validation
            if amount <= 0 or amount > 1000000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid amount.'}, status=400)
            
            if inflation_rate < -20 or inflation_rate > 50:
                return JsonResponse({'success': False, 'error': 'Inflation rate must be between -20% and 50%.'}, status=400)
            
            if years <= 0 or years > 100:
                return JsonResponse({'success': False, 'error': 'Years must be between 1 and 100.'}, status=400)
            
            rate = inflation_rate / 100
            
            if calc_type == 'future':
                # Calculate future value needed to maintain purchasing power
                future_value = amount * ((1 + rate) ** years)
                purchasing_power_lost = future_value - amount
                real_value = amount  # Today's value remains same
            else:
                # Calculate what past amount is worth today
                future_value = amount  # This is today's value
                real_value = amount / ((1 + rate) ** years)
                purchasing_power_lost = amount - real_value
            
            # Calculate cumulative inflation
            cumulative_inflation = (((1 + rate) ** years) - 1) * 100
            
            # Yearly breakdown
            yearly_data = []
            current_value = amount
            for year in range(1, years + 1):
                if calc_type == 'future':
                    value = amount * ((1 + rate) ** year)
                    power = amount / ((1 + rate) ** year)
                else:
                    value = amount
                    power = amount / ((1 + rate) ** year)
                
                yearly_data.append({
                    'year': year,
                    'value': round(value, 2),
                    'purchasing_power': round(power, 2),
                    'inflation_factor': round((1 + rate) ** year, 4)
                })
            
            # Compare different inflation rates
            comparison = []
            for rate_pct in [2, 3, 4, 5, 7, 10]:
                r = rate_pct / 100
                fv = amount * ((1 + r) ** years)
                comparison.append({
                    'rate': rate_pct,
                    'future_value': round(fv, 2),
                    'purchasing_power': round(amount / ((1 + r) ** years), 2)
                })
            
            result = {
                'success': True,
                'summary': {
                    'original_amount': round(amount, 2),
                    'inflation_rate': round(inflation_rate, 2),
                    'years': years,
                    'calc_type': calc_type,
                    'future_value': round(future_value, 2),
                    'real_value': round(real_value, 2),
                    'purchasing_power_change': round(purchasing_power_lost, 2),
                    'cumulative_inflation': round(cumulative_inflation, 2)
                },
                'yearly_data': yearly_data[:50],
                'comparison': comparison,
                'chart_data': {
                    'labels': [f"Year {d['year']}" for d in yearly_data[:20]],
                    'values': [d['value'] for d in yearly_data[:20]],
                    'purchasing_power': [d['purchasing_power'] for d in yearly_data[:20]]
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
