from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class PercentOffCalculator(View):
    """
    Class-based view for Percent Off Calculator
    Calculates discounted prices and savings.
    """
    template_name = 'financial_calculators/percent_off_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Percent Off Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for percent off calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'calculate_sale_price')
            
            if calc_type == 'calculate_sale_price':
                # Calculate sale price from original and percent off
                original_price = float(str(data.get('original_price', 0)).replace(',', ''))
                percent_off = float(str(data.get('percent_off', 0)).replace(',', ''))
                
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': 'Original price cannot be negative.'}, status=400)
                if percent_off < 0 or percent_off > 100:
                    return JsonResponse({'success': False, 'error': 'Percent off must be between 0 and 100.'}, status=400)
                
                savings = original_price * (percent_off / 100)
                sale_price = original_price - savings
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'percent_off': percent_off,
                    'savings': round(savings, 2),
                    'sale_price': round(sale_price, 2),
                    'formula': f'Sale Price = ${original_price:,.2f} - ({percent_off}% of ${original_price:,.2f}) = ${sale_price:,.2f}'
                }
                
                # Common discount comparison
                discounts = [10, 15, 20, 25, 30, 40, 50, 60, 70]
                comparison = []
                for d in discounts:
                    save = original_price * (d / 100)
                    final = original_price - save
                    comparison.append({
                        'percent': d,
                        'savings': round(save, 2),
                        'final_price': round(final, 2)
                    })
                result['comparison'] = comparison
                
            elif calc_type == 'calculate_percent_off':
                # Calculate percent off from original and sale price
                original_price = float(str(data.get('original_price', 0)).replace(',', ''))
                sale_price = float(str(data.get('sale_price', 0)).replace(',', ''))
                
                if original_price <= 0:
                    return JsonResponse({'success': False, 'error': 'Original price must be greater than zero.'}, status=400)
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': 'Sale price cannot be negative.'}, status=400)
                if sale_price > original_price:
                    return JsonResponse({'success': False, 'error': 'Sale price cannot be higher than original price.'}, status=400)
                
                savings = original_price - sale_price
                percent_off = (savings / original_price) * 100
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'sale_price': round(sale_price, 2),
                    'savings': round(savings, 2),
                    'percent_off': round(percent_off, 2),
                    'formula': f'Percent Off = ((${original_price:,.2f} - ${sale_price:,.2f}) / ${original_price:,.2f}) × 100 = {percent_off:.2f}%'
                }
                
            elif calc_type == 'calculate_original':
                # Calculate original price from sale price and percent off
                sale_price = float(str(data.get('sale_price', 0)).replace(',', ''))
                percent_off = float(str(data.get('percent_off', 0)).replace(',', ''))
                
                if sale_price < 0:
                    return JsonResponse({'success': False, 'error': 'Sale price cannot be negative.'}, status=400)
                if percent_off < 0 or percent_off >= 100:
                    return JsonResponse({'success': False, 'error': 'Percent off must be between 0 and 99.'}, status=400)
                
                original_price = sale_price / (1 - percent_off / 100)
                savings = original_price - sale_price
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'sale_price': round(sale_price, 2),
                    'percent_off': percent_off,
                    'original_price': round(original_price, 2),
                    'savings': round(savings, 2),
                    'formula': f'Original = ${sale_price:,.2f} / (1 - {percent_off}%) = ${original_price:,.2f}'
                }
                
            elif calc_type == 'stacked_discounts':
                # Calculate with multiple stacked discounts
                original_price = float(str(data.get('original_price', 0)).replace(',', ''))
                discounts = data.get('discounts', [])
                
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': 'Original price cannot be negative.'}, status=400)
                
                if not discounts:
                    discounts = [20, 10]  # Default: 20% off, then additional 10%
                
                current_price = original_price
                breakdown = []
                
                for i, discount in enumerate(discounts):
                    discount = float(discount)
                    savings = current_price * (discount / 100)
                    new_price = current_price - savings
                    breakdown.append({
                        'step': i + 1,
                        'discount': discount,
                        'price_before': round(current_price, 2),
                        'savings': round(savings, 2),
                        'price_after': round(new_price, 2)
                    })
                    current_price = new_price
                
                total_savings = original_price - current_price
                effective_discount = (total_savings / original_price) * 100 if original_price > 0 else 0
                
                # Compare with single equivalent discount
                single_discount_price = original_price * (1 - effective_discount / 100)
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'discounts': discounts,
                    'final_price': round(current_price, 2),
                    'total_savings': round(total_savings, 2),
                    'effective_discount': round(effective_discount, 2),
                    'breakdown': breakdown,
                    'note': f'Stacking {len(discounts)} discounts equals a single {effective_discount:.2f}% discount'
                }
                
            elif calc_type == 'buy_x_get_y':
                # Calculate buy X get Y deals
                original_price = float(str(data.get('original_price', 0)).replace(',', ''))
                buy_quantity = int(data.get('buy_quantity', 2))
                get_quantity = int(data.get('get_quantity', 1))
                get_discount = float(str(data.get('get_discount', 100)).replace(',', ''))  # 100 = free, 50 = half off
                
                if original_price < 0:
                    return JsonResponse({'success': False, 'error': 'Price cannot be negative.'}, status=400)
                if buy_quantity < 1 or get_quantity < 1:
                    return JsonResponse({'success': False, 'error': 'Quantities must be at least 1.'}, status=400)
                
                total_items = buy_quantity + get_quantity
                full_price_items = buy_quantity
                discounted_items = get_quantity
                
                regular_total = original_price * total_items
                deal_price = (original_price * full_price_items) + (original_price * discounted_items * (1 - get_discount / 100))
                savings = regular_total - deal_price
                effective_per_item = deal_price / total_items
                effective_discount = (savings / regular_total) * 100
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'original_price': round(original_price, 2),
                    'deal': f'Buy {buy_quantity} Get {get_quantity} {"Free" if get_discount == 100 else f"{get_discount}% Off"}',
                    'total_items': total_items,
                    'regular_total': round(regular_total, 2),
                    'deal_price': round(deal_price, 2),
                    'savings': round(savings, 2),
                    'effective_per_item': round(effective_per_item, 2),
                    'effective_discount': round(effective_discount, 2)
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
