from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class MarginCalculator(View):
    """
    Class-based view for Margin Calculator
    Calculates profit margin, markup, cost, and revenue.
    """
    template_name = 'financial_calculators/margin_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Margin Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for margin calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'margin_from_cost_price')
            
            if calc_type == 'margin_from_cost_price':
                # Calculate margin from cost and selling price
                cost = float(str(data.get('cost', 0)).replace(',', ''))
                price = float(str(data.get('price', 0)).replace(',', ''))
                
                if cost < 0 or price < 0:
                    return JsonResponse({'success': False, 'error': 'Values cannot be negative.'}, status=400)
                if price == 0:
                    return JsonResponse({'success': False, 'error': 'Selling price cannot be zero.'}, status=400)
                
                profit = price - cost
                margin = (profit / price) * 100
                markup = (profit / cost) * 100 if cost > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'cost': round(cost, 2),
                    'price': round(price, 2),
                    'profit': round(profit, 2),
                    'margin': round(margin, 2),
                    'markup': round(markup, 2),
                    'formulas': {
                        'profit': f'Profit = Price - Cost = ${price:,.2f} - ${cost:,.2f} = ${profit:,.2f}',
                        'margin': f'Margin = (Profit / Price) × 100 = ({profit:,.2f} / {price:,.2f}) × 100 = {margin:.2f}%',
                        'markup': f'Markup = (Profit / Cost) × 100 = ({profit:,.2f} / {cost:,.2f}) × 100 = {markup:.2f}%'
                    }
                }
                
            elif calc_type == 'price_from_cost_margin':
                # Calculate selling price from cost and desired margin
                cost = float(str(data.get('cost', 0)).replace(',', ''))
                margin = float(str(data.get('margin', 0)).replace(',', ''))
                
                if cost < 0:
                    return JsonResponse({'success': False, 'error': 'Cost cannot be negative.'}, status=400)
                if margin >= 100:
                    return JsonResponse({'success': False, 'error': 'Margin must be less than 100%.'}, status=400)
                
                # Price = Cost / (1 - Margin%)
                price = cost / (1 - margin / 100) if margin < 100 else 0
                profit = price - cost
                markup = (profit / cost) * 100 if cost > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'cost': round(cost, 2),
                    'margin': round(margin, 2),
                    'price': round(price, 2),
                    'profit': round(profit, 2),
                    'markup': round(markup, 2),
                    'formulas': {
                        'price': f'Price = Cost / (1 - Margin%) = ${cost:,.2f} / (1 - {margin}%) = ${price:,.2f}',
                        'profit': f'Profit = ${profit:,.2f}',
                        'markup': f'Markup = {markup:.2f}%'
                    }
                }
                
            elif calc_type == 'price_from_cost_markup':
                # Calculate selling price from cost and markup
                cost = float(str(data.get('cost', 0)).replace(',', ''))
                markup = float(str(data.get('markup', 0)).replace(',', ''))
                
                if cost < 0:
                    return JsonResponse({'success': False, 'error': 'Cost cannot be negative.'}, status=400)
                
                # Price = Cost × (1 + Markup%)
                price = cost * (1 + markup / 100)
                profit = price - cost
                margin = (profit / price) * 100 if price > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'cost': round(cost, 2),
                    'markup': round(markup, 2),
                    'price': round(price, 2),
                    'profit': round(profit, 2),
                    'margin': round(margin, 2),
                    'formulas': {
                        'price': f'Price = Cost × (1 + Markup%) = ${cost:,.2f} × (1 + {markup}%) = ${price:,.2f}',
                        'profit': f'Profit = ${profit:,.2f}',
                        'margin': f'Margin = {margin:.2f}%'
                    }
                }
                
            elif calc_type == 'cost_from_price_margin':
                # Calculate cost from selling price and margin
                price = float(str(data.get('price', 0)).replace(',', ''))
                margin = float(str(data.get('margin', 0)).replace(',', ''))
                
                if price < 0:
                    return JsonResponse({'success': False, 'error': 'Price cannot be negative.'}, status=400)
                if margin >= 100:
                    return JsonResponse({'success': False, 'error': 'Margin must be less than 100%.'}, status=400)
                
                # Cost = Price × (1 - Margin%)
                cost = price * (1 - margin / 100)
                profit = price - cost
                markup = (profit / cost) * 100 if cost > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'price': round(price, 2),
                    'margin': round(margin, 2),
                    'cost': round(cost, 2),
                    'profit': round(profit, 2),
                    'markup': round(markup, 2),
                    'formulas': {
                        'cost': f'Cost = Price × (1 - Margin%) = ${price:,.2f} × (1 - {margin}%) = ${cost:,.2f}',
                        'profit': f'Profit = ${profit:,.2f}',
                        'markup': f'Markup = {markup:.2f}%'
                    }
                }
                
            elif calc_type == 'margin_markup_convert':
                # Convert between margin and markup
                value = float(str(data.get('value', 0)).replace(',', ''))
                convert_from = data.get('convert_from', 'margin')
                
                if value < 0:
                    return JsonResponse({'success': False, 'error': 'Value cannot be negative.'}, status=400)
                
                if convert_from == 'margin':
                    if value >= 100:
                        return JsonResponse({'success': False, 'error': 'Margin must be less than 100%.'}, status=400)
                    # Markup = Margin / (1 - Margin)
                    markup = (value / (100 - value)) * 100 if value < 100 else 0
                    result = {
                        'success': True,
                        'calc_type': calc_type,
                        'margin': round(value, 2),
                        'markup': round(markup, 2),
                        'formula': f'Markup = Margin / (100 - Margin) × 100 = {value} / (100 - {value}) × 100 = {markup:.2f}%'
                    }
                else:
                    # Margin = Markup / (1 + Markup)
                    margin = (value / (100 + value)) * 100
                    result = {
                        'success': True,
                        'calc_type': calc_type,
                        'markup': round(value, 2),
                        'margin': round(margin, 2),
                        'formula': f'Margin = Markup / (100 + Markup) × 100 = {value} / (100 + {value}) × 100 = {margin:.2f}%'
                    }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Add margin vs markup comparison table
            comparison_table = []
            for m in [10, 15, 20, 25, 30, 35, 40, 45, 50]:
                markup_equiv = (m / (100 - m)) * 100
                comparison_table.append({
                    'margin': m,
                    'markup': round(markup_equiv, 1)
                })
            result['comparison_table'] = comparison_table
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
