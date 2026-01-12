from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class InterestCalculator(View):
    """
    Class-based view for Interest Calculator
    Calculates simple and compound interest with detailed breakdowns.
    """
    template_name = 'financial_calculators/interest_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Interest Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            principal = float(str(data.get('principal', 0)).replace(',', ''))
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            time_period = float(str(data.get('time_period', 0)).replace(',', ''))
            time_unit = data.get('time_unit', 'years')
            interest_type = data.get('interest_type', 'simple')
            compound_frequency = data.get('compound_frequency', 'monthly')
            
            # Validation
            if principal <= 0 or principal > 1000000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid principal amount.'}, status=400)
            
            if interest_rate <= 0 or interest_rate > 100:
                return JsonResponse({'success': False, 'error': 'Interest rate must be between 0.01% and 100%.'}, status=400)
            
            if time_period <= 0 or time_period > 100:
                return JsonResponse({'success': False, 'error': 'Time period must be between 1 and 100.'}, status=400)
            
            # Convert time to years
            if time_unit == 'months':
                years = time_period / 12
            elif time_unit == 'days':
                years = time_period / 365
            else:
                years = time_period
            
            rate = interest_rate / 100
            
            # Calculate based on interest type
            if interest_type == 'simple':
                interest = principal * rate * years
                final_amount = principal + interest
                effective_rate = interest_rate
                
                # Yearly breakdown for simple interest
                yearly_data = []
                for year in range(1, int(years) + 2):
                    if year <= years:
                        yr_interest = principal * rate * min(year, years)
                        yearly_data.append({
                            'year': year,
                            'interest': round(principal * rate, 2),
                            'total_interest': round(yr_interest, 2),
                            'balance': round(principal + yr_interest, 2)
                        })
            else:
                # Compound interest
                frequency_map = {
                    'annually': 1,
                    'semi-annually': 2,
                    'quarterly': 4,
                    'monthly': 12,
                    'daily': 365
                }
                n = frequency_map.get(compound_frequency, 12)
                
                # A = P(1 + r/n)^(nt)
                final_amount = principal * ((1 + rate/n) ** (n * years))
                interest = final_amount - principal
                
                # Effective annual rate
                effective_rate = ((1 + rate/n) ** n - 1) * 100
                
                # Yearly breakdown for compound interest
                yearly_data = []
                for year in range(1, int(years) + 2):
                    if year <= years:
                        balance = principal * ((1 + rate/n) ** (n * year))
                        prev_balance = principal * ((1 + rate/n) ** (n * (year - 1))) if year > 1 else principal
                        yr_interest = balance - prev_balance
                        yearly_data.append({
                            'year': year,
                            'interest': round(yr_interest, 2),
                            'total_interest': round(balance - principal, 2),
                            'balance': round(balance, 2)
                        })
            
            # Compare simple vs compound
            simple_interest = principal * rate * years
            compound_interest = principal * ((1 + rate/12) ** (12 * years)) - principal
            
            result = {
                'success': True,
                'summary': {
                    'principal': round(principal, 2),
                    'interest_rate': round(interest_rate, 3),
                    'time_period': time_period,
                    'time_unit': time_unit,
                    'interest_type': interest_type,
                    'interest_earned': round(interest, 2),
                    'final_amount': round(final_amount, 2),
                    'effective_rate': round(effective_rate, 3),
                    'years': round(years, 2)
                },
                'comparison': {
                    'simple': round(simple_interest, 2),
                    'compound': round(compound_interest, 2),
                    'difference': round(compound_interest - simple_interest, 2)
                },
                'yearly_data': yearly_data[:30],  # Limit to 30 years
                'chart_data': {
                    'breakdown': {
                        'principal': round(principal, 2),
                        'interest': round(interest, 2)
                    },
                    'growth': {
                        'labels': [f"Year {d['year']}" for d in yearly_data[:10]],
                        'balances': [d['balance'] for d in yearly_data[:10]]
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
