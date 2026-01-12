from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class VatCalculator(View):
    """
    Class-based view for VAT (Value Added Tax) Calculator
    Calculates VAT amounts, net prices, and gross prices.
    """
    template_name = 'financial_calculators/vat_calculator.html'
    
    # Common VAT rates by country
    COMMON_VAT_RATES = {
        'uk': 20,
        'germany': 19,
        'france': 20,
        'italy': 22,
        'spain': 21,
        'netherlands': 21,
        'belgium': 21,
        'austria': 20,
        'poland': 23,
        'sweden': 25,
        'denmark': 25,
        'finland': 24,
        'ireland': 23,
        'portugal': 23,
        'greece': 24,
        'hungary': 27,
        'czech': 21,
        'romania': 19,
        'switzerland': 7.7,
        'norway': 25,
        'canada_gst': 5,
        'australia_gst': 10,
        'new_zealand_gst': 15,
        'japan': 10,
        'singapore_gst': 8,
        'india_gst': 18,
        'south_africa': 15,
        'brazil': 17,
        'mexico': 16,
        'uae': 5,
    }
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'VAT Calculator',
            'vat_rates': self.COMMON_VAT_RATES,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for VAT calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'add_vat')
            amount = float(str(data.get('amount', 0)).replace(',', ''))
            vat_rate = float(str(data.get('vat_rate', 20)).replace(',', ''))
            
            # Validation
            if amount < 0:
                return JsonResponse({'success': False, 'error': 'Amount cannot be negative.'}, status=400)
            if vat_rate < 0 or vat_rate > 100:
                return JsonResponse({'success': False, 'error': 'VAT rate must be between 0% and 100%.'}, status=400)
            
            vat_multiplier = vat_rate / 100
            
            if calc_type == 'add_vat':
                # Calculate gross from net (add VAT)
                net_amount = amount
                vat_amount = net_amount * vat_multiplier
                gross_amount = net_amount + vat_amount
                
                result = {
                    'success': True,
                    'calc_type': 'add_vat',
                    'net_amount': round(net_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'gross_amount': round(gross_amount, 2),
                    'formula': f'Gross = Net × (1 + {vat_rate}%) = {net_amount:,.2f} × {1 + vat_multiplier:.4f} = {gross_amount:,.2f}'
                }
                
            elif calc_type == 'remove_vat':
                # Calculate net from gross (remove VAT)
                gross_amount = amount
                net_amount = gross_amount / (1 + vat_multiplier)
                vat_amount = gross_amount - net_amount
                
                result = {
                    'success': True,
                    'calc_type': 'remove_vat',
                    'gross_amount': round(gross_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'net_amount': round(net_amount, 2),
                    'formula': f'Net = Gross ÷ (1 + {vat_rate}%) = {gross_amount:,.2f} ÷ {1 + vat_multiplier:.4f} = {net_amount:,.2f}'
                }
                
            elif calc_type == 'find_vat_only':
                # Calculate just the VAT amount from net
                net_amount = amount
                vat_amount = net_amount * vat_multiplier
                
                result = {
                    'success': True,
                    'calc_type': 'find_vat_only',
                    'net_amount': round(net_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'formula': f'VAT = Net × {vat_rate}% = {net_amount:,.2f} × {vat_multiplier:.4f} = {vat_amount:,.2f}'
                }
                
            elif calc_type == 'reverse_vat':
                # Calculate VAT amount from gross price
                gross_amount = amount
                vat_amount = gross_amount - (gross_amount / (1 + vat_multiplier))
                net_amount = gross_amount - vat_amount
                
                result = {
                    'success': True,
                    'calc_type': 'reverse_vat',
                    'gross_amount': round(gross_amount, 2),
                    'vat_rate': vat_rate,
                    'vat_amount': round(vat_amount, 2),
                    'net_amount': round(net_amount, 2),
                    'formula': f'VAT = Gross - (Gross ÷ (1 + {vat_rate}%)) = {vat_amount:,.2f}'
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            # Add comparison table for common VAT rates
            comparisons = []
            for country, rate in sorted(self.COMMON_VAT_RATES.items(), key=lambda x: x[1]):
                if calc_type in ['add_vat', 'find_vat_only']:
                    vat = amount * (rate / 100)
                    gross = amount + vat
                    comparisons.append({
                        'country': country.replace('_', ' ').title(),
                        'rate': rate,
                        'vat': round(vat, 2),
                        'total': round(gross, 2)
                    })
                else:
                    net = amount / (1 + rate / 100)
                    vat = amount - net
                    comparisons.append({
                        'country': country.replace('_', ' ').title(),
                        'rate': rate,
                        'vat': round(vat, 2),
                        'net': round(net, 2)
                    })
            
            result['comparisons'] = comparisons[:10]  # Top 10 for display
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
