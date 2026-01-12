from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class DiscountCalculator(View):
    """
    Class-based view for Discount Calculator
    Calculates discounts, sale prices, and savings using NumPy.
    """
    template_name = 'financial_calculators/discount_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Discount Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'find_sale_price')
            
            if calc_type == 'find_sale_price':
                # Calculate sale price from original price and discount
                original_price = float(data.get('original_price', 100))
                discount_percent = float(data.get('discount_percent', 20))
                
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': 'Price cannot be negative.'}, status=400)
                if discount_percent < 0 or discount_percent > 100:
                    return JsonResponse({'success': False, 'error': 'Discount must be between 0 and 100%.'}, status=400)
                
                discount_amount = np.multiply(original_price, np.divide(discount_percent, 100))
                sale_price = np.subtract(original_price, discount_amount)
                
                result = {
                    'success': True,
                    'calc_type': 'find_sale_price',
                    'original_price': round(float(original_price), 2),
                    'discount_percent': discount_percent,
                    'discount_amount': round(float(discount_amount), 2),
                    'sale_price': round(float(sale_price), 2)
                }
                
            elif calc_type == 'find_discount':
                # Calculate discount percentage from original and sale price
                original_price = float(data.get('original_price', 100))
                sale_price = float(data.get('sale_price', 80))
                
                if original_price <= 0:
                    return JsonResponse({'success': False, 'error': 'Original price must be greater than zero.'}, status=400)
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': 'Sale price cannot be negative.'}, status=400)
                
                discount_amount = original_price - sale_price
                discount_percent = (discount_amount / original_price) * 100
                
                result = {
                    'success': True,
                    'calc_type': 'find_discount',
                    'original_price': round(original_price, 2),
                    'sale_price': round(sale_price, 2),
                    'discount_amount': round(discount_amount, 2),
                    'discount_percent': round(discount_percent, 2)
                }
                
            elif calc_type == 'find_original':
                # Calculate original price from sale price and discount
                sale_price = float(data.get('sale_price', 80))
                discount_percent = float(data.get('discount_percent', 20))
                
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': 'Sale price cannot be negative.'}, status=400)
                if discount_percent < 0 or discount_percent >= 100:
                    return JsonResponse({'success': False, 'error': 'Discount must be between 0 and 99%.'}, status=400)
                
                # original = sale_price / (1 - discount/100)
                original_price = sale_price / (1 - discount_percent / 100)
                discount_amount = original_price - sale_price
                
                result = {
                    'success': True,
                    'calc_type': 'find_original',
                    'sale_price': round(sale_price, 2),
                    'discount_percent': discount_percent,
                    'original_price': round(original_price, 2),
                    'discount_amount': round(discount_amount, 2)
                }
                
            elif calc_type == 'double_discount':
                # Calculate with multiple discounts
                original_price = float(data.get('original_price', 100))
                discount1 = float(data.get('discount1', 20))
                discount2 = float(data.get('discount2', 10))
                
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': 'Price cannot be negative.'}, status=400)
                
                # Apply first discount
                price_after_first = original_price * (1 - discount1 / 100)
                # Apply second discount
                final_price = price_after_first * (1 - discount2 / 100)
                
                total_savings = original_price - final_price
                effective_discount = (total_savings / original_price) * 100
                
                result = {
                    'success': True,
                    'calc_type': 'double_discount',
                    'original_price': round(original_price, 2),
                    'discount1': discount1,
                    'discount2': discount2,
                    'price_after_first': round(price_after_first, 2),
                    'final_price': round(final_price, 2),
                    'total_savings': round(total_savings, 2),
                    'effective_discount': round(effective_discount, 2)
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred.'}, status=500)
