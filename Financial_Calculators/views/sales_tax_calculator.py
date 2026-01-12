from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class SalesTaxCalculator(View):
    """
    Class-based view for Sales Tax Calculator
    Calculates sales tax amounts and totals using NumPy.
    """
    template_name = 'financial_calculators/sales_tax_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Sales Tax Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'add_tax')
            price = float(data.get('price', 0))
            tax_rate = float(data.get('tax_rate', 0))
            
            # Validation
            if price < 0:
                return JsonResponse({'success': False, 'error': 'Price cannot be negative.'}, status=400)
            if tax_rate < 0 or tax_rate > 100:
                return JsonResponse({'success': False, 'error': 'Tax rate must be between 0 and 100.'}, status=400)
            
            # Use NumPy for calculations
            if calc_type == 'add_tax':
                # Calculate tax to add to price
                tax_amount = np.multiply(price, np.divide(tax_rate, 100))
                total = np.add(price, tax_amount)
                
                result = {
                    'success': True,
                    'calc_type': 'add_tax',
                    'before_tax': round(float(price), 2),
                    'tax_rate': tax_rate,
                    'tax_amount': round(float(tax_amount), 2),
                    'total': round(float(total), 2)
                }
                
            elif calc_type == 'extract_tax':
                # Extract tax from total (price is total including tax)
                # total = before_tax * (1 + rate)
                # before_tax = total / (1 + rate)
                divisor = 1 + (tax_rate / 100)
                before_tax = np.divide(price, divisor)
                tax_amount = np.subtract(price, before_tax)
                
                result = {
                    'success': True,
                    'calc_type': 'extract_tax',
                    'total': round(float(price), 2),
                    'tax_rate': tax_rate,
                    'tax_amount': round(float(tax_amount), 2),
                    'before_tax': round(float(before_tax), 2)
                }
                
            elif calc_type == 'find_rate':
                # Find tax rate given before and after prices
                before_tax = float(data.get('before_tax', 100))
                total = float(data.get('total', 110))
                
                if before_tax <= 0:
                    return JsonResponse({'success': False, 'error': 'Before-tax price must be greater than zero.'}, status=400)
                
                tax_amount = total - before_tax
                calculated_rate = (tax_amount / before_tax) * 100
                
                result = {
                    'success': True,
                    'calc_type': 'find_rate',
                    'before_tax': round(before_tax, 2),
                    'total': round(total, 2),
                    'tax_amount': round(tax_amount, 2),
                    'tax_rate': round(calculated_rate, 4)
                }
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Add common US state tax rates for reference
            result['us_state_rates'] = [
                {'state': 'California', 'rate': 7.25},
                {'state': 'Texas', 'rate': 6.25},
                {'state': 'New York', 'rate': 4.0},
                {'state': 'Florida', 'rate': 6.0},
                {'state': 'Washington', 'rate': 6.5},
                {'state': 'Oregon', 'rate': 0.0},
                {'state': 'Montana', 'rate': 0.0},
                {'state': 'Delaware', 'rate': 0.0}
            ]
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred.'}, status=500)
