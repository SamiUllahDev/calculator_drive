from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class CdCalculator(View):
    """
    Class-based view for CD (Certificate of Deposit) Calculator
    Calculates CD returns with different compounding options.
    """
    template_name = 'financial_calculators/cd_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'CD Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Extract and validate inputs
            deposit = float(str(data.get('deposit', 0)).replace(',', ''))
            apy = float(str(data.get('apy', 0)).replace(',', ''))
            term_months = int(data.get('term_months', 0))
            compound_frequency = data.get('compound_frequency', 'daily')
            
            # Validation
            if deposit <= 0 or deposit > 10000000:
                return JsonResponse({'success': False, 'error': 'Please enter a valid deposit amount.'}, status=400)
            
            if apy < 0 or apy > 25:
                return JsonResponse({'success': False, 'error': 'APY must be between 0% and 25%.'}, status=400)
            
            if term_months <= 0 or term_months > 120:
                return JsonResponse({'success': False, 'error': 'CD term must be between 1 and 120 months.'}, status=400)
            
            years = term_months / 12
            rate = apy / 100
            
            # Compounding frequency
            frequency_map = {
                'annually': 1,
                'semi-annually': 2,
                'quarterly': 4,
                'monthly': 12,
                'daily': 365
            }
            n = frequency_map.get(compound_frequency, 365)
            
            # Calculate final amount
            final_amount = deposit * ((1 + rate/n) ** (n * years))
            interest_earned = final_amount - deposit
            
            # Calculate effective APY
            effective_apy = ((1 + rate/n) ** n - 1) * 100
            
            # Monthly breakdown
            monthly_data = []
            for month in range(1, term_months + 1):
                month_years = month / 12
                balance = deposit * ((1 + rate/n) ** (n * month_years))
                monthly_data.append({
                    'month': month,
                    'balance': round(balance, 2),
                    'interest': round(balance - deposit, 2)
                })
            
            # Compare different terms
            comparison = []
            for months in [3, 6, 12, 24, 36, 60]:
                yrs = months / 12
                amt = deposit * ((1 + rate/n) ** (n * yrs))
                comparison.append({
                    'term': f'{months} mo' if months < 12 else f'{months//12} yr',
                    'months': months,
                    'final_amount': round(amt, 2),
                    'interest': round(amt - deposit, 2)
                })
            
            result = {
                'success': True,
                'summary': {
                    'deposit': round(deposit, 2),
                    'apy': round(apy, 3),
                    'effective_apy': round(effective_apy, 3),
                    'term_months': term_months,
                    'final_amount': round(final_amount, 2),
                    'interest_earned': round(interest_earned, 2),
                    'compound_frequency': compound_frequency
                },
                'monthly_data': monthly_data[:24],  # First 2 years
                'comparison': comparison,
                'chart_data': {
                    'breakdown': {
                        'deposit': round(deposit, 2),
                        'interest': round(interest_earned, 2)
                    },
                    'growth': {
                        'labels': [f"Mo {d['month']}" for d in monthly_data[::max(1, term_months//12)]],
                        'values': [d['balance'] for d in monthly_data[::max(1, term_months//12)]]
                    }
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
