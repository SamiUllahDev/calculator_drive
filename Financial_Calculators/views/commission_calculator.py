from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class CommissionCalculator(View):
    """
    Class-based view for Commission Calculator
    Calculates sales commissions with various structures.
    """
    template_name = 'financial_calculators/commission_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Commission Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for commission calculations"""
        try:
            data = json.loads(request.body)
            
            calc_type = data.get('calc_type', 'simple')
            
            if calc_type == 'simple':
                # Simple percentage commission
                sales_amount = float(str(data.get('sales_amount', 0)).replace(',', ''))
                commission_rate = float(str(data.get('commission_rate', 0)).replace(',', ''))
                
                if sales_amount < 0:
                    return JsonResponse({'success': False, 'error': 'Sales amount cannot be negative.'}, status=400)
                if commission_rate < 0 or commission_rate > 100:
                    return JsonResponse({'success': False, 'error': 'Commission rate must be between 0% and 100%.'}, status=400)
                
                commission = sales_amount * (commission_rate / 100)
                
                result = {
                    'success': True,
                    'calc_type': 'simple',
                    'sales_amount': round(sales_amount, 2),
                    'commission_rate': commission_rate,
                    'commission': round(commission, 2),
                    'net_to_company': round(sales_amount - commission, 2),
                    'formula': f'Commission = ${sales_amount:,.2f} × {commission_rate}% = ${commission:,.2f}'
                }
                
            elif calc_type == 'tiered':
                # Tiered commission structure
                sales_amount = float(str(data.get('sales_amount', 0)).replace(',', ''))
                tiers = data.get('tiers', [])
                
                if sales_amount < 0:
                    return JsonResponse({'success': False, 'error': 'Sales amount cannot be negative.'}, status=400)
                
                if not tiers:
                    # Default tiers
                    tiers = [
                        {'min': 0, 'max': 10000, 'rate': 5},
                        {'min': 10000, 'max': 25000, 'rate': 7},
                        {'min': 25000, 'max': 50000, 'rate': 10},
                        {'min': 50000, 'max': None, 'rate': 12}
                    ]
                
                total_commission = 0
                breakdown = []
                remaining = sales_amount
                
                for tier in tiers:
                    tier_min = float(tier.get('min', 0))
                    tier_max = tier.get('max')
                    tier_rate = float(tier.get('rate', 0))
                    
                    if tier_max is not None:
                        tier_max = float(tier_max)
                        tier_amount = min(remaining, max(0, tier_max - tier_min))
                    else:
                        tier_amount = max(0, remaining)
                    
                    if tier_amount > 0 and sales_amount > tier_min:
                        commission = tier_amount * (tier_rate / 100)
                        total_commission += commission
                        breakdown.append({
                            'range': f'${tier_min:,.0f} - ${tier_max:,.0f}' if tier_max else f'${tier_min:,.0f}+',
                            'amount': round(tier_amount, 2),
                            'rate': tier_rate,
                            'commission': round(commission, 2)
                        })
                        remaining -= tier_amount
                    
                    if remaining <= 0:
                        break
                
                effective_rate = (total_commission / sales_amount * 100) if sales_amount > 0 else 0
                
                result = {
                    'success': True,
                    'calc_type': 'tiered',
                    'sales_amount': round(sales_amount, 2),
                    'total_commission': round(total_commission, 2),
                    'effective_rate': round(effective_rate, 2),
                    'breakdown': breakdown,
                    'net_to_company': round(sales_amount - total_commission, 2)
                }
                
            elif calc_type == 'base_plus_commission':
                # Base salary plus commission
                base_salary = float(str(data.get('base_salary', 0)).replace(',', ''))
                sales_amount = float(str(data.get('sales_amount', 0)).replace(',', ''))
                commission_rate = float(str(data.get('commission_rate', 0)).replace(',', ''))
                quota = float(str(data.get('quota', 0)).replace(',', ''))
                
                if base_salary < 0 or sales_amount < 0:
                    return JsonResponse({'success': False, 'error': 'Values cannot be negative.'}, status=400)
                
                commission = sales_amount * (commission_rate / 100)
                total_earnings = base_salary + commission
                
                # Quota achievement
                quota_achievement = (sales_amount / quota * 100) if quota > 0 else 0
                
                # Bonus for exceeding quota
                bonus = 0
                if quota > 0 and sales_amount > quota:
                    excess = sales_amount - quota
                    bonus = excess * 0.05  # 5% bonus on excess
                
                result = {
                    'success': True,
                    'calc_type': 'base_plus_commission',
                    'base_salary': round(base_salary, 2),
                    'sales_amount': round(sales_amount, 2),
                    'commission_rate': commission_rate,
                    'commission': round(commission, 2),
                    'quota': round(quota, 2),
                    'quota_achievement': round(quota_achievement, 2),
                    'bonus': round(bonus, 2),
                    'total_earnings': round(total_earnings + bonus, 2),
                    'breakdown': {
                        'base': round(base_salary, 2),
                        'commission': round(commission, 2),
                        'bonus': round(bonus, 2),
                        'total': round(total_earnings + bonus, 2)
                    }
                }
                
            elif calc_type == 'draw_against':
                # Draw against commission
                draw_amount = float(str(data.get('draw_amount', 0)).replace(',', ''))
                sales_amount = float(str(data.get('sales_amount', 0)).replace(',', ''))
                commission_rate = float(str(data.get('commission_rate', 0)).replace(',', ''))
                
                if draw_amount < 0 or sales_amount < 0:
                    return JsonResponse({'success': False, 'error': 'Values cannot be negative.'}, status=400)
                
                commission_earned = sales_amount * (commission_rate / 100)
                
                if commission_earned >= draw_amount:
                    payout = commission_earned - draw_amount
                    carry_forward = 0
                    status = 'earned_over_draw'
                else:
                    payout = 0
                    carry_forward = draw_amount - commission_earned
                    status = 'under_draw'
                
                result = {
                    'success': True,
                    'calc_type': 'draw_against',
                    'draw_amount': round(draw_amount, 2),
                    'sales_amount': round(sales_amount, 2),
                    'commission_rate': commission_rate,
                    'commission_earned': round(commission_earned, 2),
                    'payout': round(payout, 2),
                    'carry_forward': round(carry_forward, 2),
                    'status': status,
                    'message': f'Commission (${commission_earned:,.2f}) {"exceeds" if status == "earned_over_draw" else "is below"} draw (${draw_amount:,.2f})'
                }
                
            elif calc_type == 'reverse':
                # Reverse calculation - find sales needed for desired commission
                desired_commission = float(str(data.get('desired_commission', 0)).replace(',', ''))
                commission_rate = float(str(data.get('commission_rate', 0)).replace(',', ''))
                
                if desired_commission < 0:
                    return JsonResponse({'success': False, 'error': 'Desired commission cannot be negative.'}, status=400)
                if commission_rate <= 0:
                    return JsonResponse({'success': False, 'error': 'Commission rate must be greater than 0%.'}, status=400)
                
                sales_needed = desired_commission / (commission_rate / 100)
                
                result = {
                    'success': True,
                    'calc_type': 'reverse',
                    'desired_commission': round(desired_commission, 2),
                    'commission_rate': commission_rate,
                    'sales_needed': round(sales_needed, 2),
                    'formula': f'Sales Needed = ${desired_commission:,.2f} ÷ {commission_rate}% = ${sales_needed:,.2f}'
                }
            
            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
