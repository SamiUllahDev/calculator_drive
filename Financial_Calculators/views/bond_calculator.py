from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np
from datetime import datetime, timedelta


class BondCalculator(View):
    """
    Class-based view for Bond Calculator
    Calculates bond price, yield to maturity, current yield, and other bond metrics.
    """
    template_name = 'financial_calculators/bond_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Bond Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for bond calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'price')

            if calc_type == 'price':
                # Calculate bond price from yield
                face_value = float(str(data.get('face_value', 1000)).replace(',', ''))
                coupon_rate = float(str(data.get('coupon_rate', 0)).replace(',', ''))
                yield_to_maturity = float(str(data.get('yield_to_maturity', 0)).replace(',', ''))
                years_to_maturity = float(str(data.get('years_to_maturity', 0)).replace(',', ''))
                payment_frequency = int(data.get('payment_frequency', 2))  # 1=annual, 2=semi-annual, 4=quarterly

                if face_value <= 0:
                    return JsonResponse({'success': False, 'error': 'Face value must be greater than zero.'}, status=400)
                if years_to_maturity <= 0:
                    return JsonResponse({'success': False, 'error': 'Years to maturity must be greater than zero.'}, status=400)

                # Calculate periodic values
                coupon_payment = (face_value * coupon_rate / 100) / payment_frequency
                periods = int(years_to_maturity * payment_frequency)
                periodic_yield = yield_to_maturity / 100 / payment_frequency

                # Bond price calculation using present value formula
                if periodic_yield > 0:
                    # PV of coupon payments
                    pv_coupons = coupon_payment * (1 - np.power(1 + periodic_yield, -periods)) / periodic_yield
                    # PV of face value
                    pv_face = face_value / np.power(1 + periodic_yield, periods)
                    bond_price = pv_coupons + pv_face
                else:
                    bond_price = (coupon_payment * periods) + face_value

                # Current yield
                annual_coupon = face_value * coupon_rate / 100
                current_yield = (annual_coupon / bond_price * 100) if bond_price > 0 else 0

                # Premium/Discount
                premium_discount = bond_price - face_value
                premium_discount_percent = ((bond_price - face_value) / face_value) * 100

                # Duration (Macaulay)
                duration = 0
                if periodic_yield > 0 and bond_price > 0:
                    for t in range(1, periods + 1):
                        cf = coupon_payment if t < periods else coupon_payment + face_value
                        pv = cf / np.power(1 + periodic_yield, t)
                        duration += (t / payment_frequency) * pv
                    duration = duration / bond_price

                # Modified Duration
                modified_duration = duration / (1 + periodic_yield) if periodic_yield > 0 else duration

                # Generate cash flow schedule
                cash_flows = []
                total_income = 0
                for period in range(1, periods + 1):
                    payment = coupon_payment
                    if period == periods:
                        payment += face_value
                    total_income += payment
                    
                    pv = payment / np.power(1 + periodic_yield, period) if periodic_yield > 0 else payment
                    
                    cash_flows.append({
                        'period': period,
                        'year': round(period / payment_frequency, 2),
                        'coupon': round(coupon_payment, 2),
                        'principal': round(face_value if period == periods else 0, 2),
                        'total_payment': round(payment, 2),
                        'present_value': round(pv, 2)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input': {
                        'face_value': round(face_value, 2),
                        'coupon_rate': coupon_rate,
                        'yield_to_maturity': yield_to_maturity,
                        'years_to_maturity': years_to_maturity,
                        'payment_frequency': payment_frequency
                    },
                    'bond_price': round(bond_price, 2),
                    'current_yield': round(current_yield, 2),
                    'premium_discount': round(premium_discount, 2),
                    'premium_discount_percent': round(premium_discount_percent, 2),
                    'bond_status': 'Premium' if bond_price > face_value else ('Discount' if bond_price < face_value else 'Par'),
                    'macaulay_duration': round(duration, 2),
                    'modified_duration': round(modified_duration, 2),
                    'annual_income': round(annual_coupon, 2),
                    'total_income': round(total_income, 2),
                    'cash_flows': cash_flows[:20]  # Limit to 20 periods
                }

            elif calc_type == 'ytm':
                # Calculate Yield to Maturity from price
                face_value = float(str(data.get('face_value', 1000)).replace(',', ''))
                coupon_rate = float(str(data.get('coupon_rate', 0)).replace(',', ''))
                bond_price = float(str(data.get('bond_price', 0)).replace(',', ''))
                years_to_maturity = float(str(data.get('years_to_maturity', 0)).replace(',', ''))
                payment_frequency = int(data.get('payment_frequency', 2))

                if face_value <= 0 or bond_price <= 0:
                    return JsonResponse({'success': False, 'error': 'Face value and bond price must be greater than zero.'}, status=400)
                if years_to_maturity <= 0:
                    return JsonResponse({'success': False, 'error': 'Years to maturity must be greater than zero.'}, status=400)

                coupon_payment = (face_value * coupon_rate / 100) / payment_frequency
                periods = int(years_to_maturity * payment_frequency)

                # Newton-Raphson method to find YTM
                ytm_guess = coupon_rate / 100 / payment_frequency
                if ytm_guess == 0:
                    ytm_guess = 0.05 / payment_frequency

                for _ in range(100):  # Max iterations
                    price_calc = 0
                    dprice = 0
                    
                    for t in range(1, periods + 1):
                        cf = coupon_payment if t < periods else coupon_payment + face_value
                        disc = np.power(1 + ytm_guess, t)
                        price_calc += cf / disc
                        dprice -= t * cf / np.power(1 + ytm_guess, t + 1)
                    
                    diff = price_calc - bond_price
                    if abs(diff) < 0.0001:
                        break
                    
                    ytm_guess = ytm_guess - diff / dprice
                    if ytm_guess < 0:
                        ytm_guess = 0.0001

                ytm_annual = ytm_guess * payment_frequency * 100

                # Current yield
                annual_coupon = face_value * coupon_rate / 100
                current_yield = (annual_coupon / bond_price * 100) if bond_price > 0 else 0

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'input': {
                        'face_value': round(face_value, 2),
                        'coupon_rate': coupon_rate,
                        'bond_price': round(bond_price, 2),
                        'years_to_maturity': years_to_maturity,
                        'payment_frequency': payment_frequency
                    },
                    'yield_to_maturity': round(ytm_annual, 4),
                    'current_yield': round(current_yield, 2),
                    'premium_discount': round(bond_price - face_value, 2),
                    'bond_status': 'Premium' if bond_price > face_value else ('Discount' if bond_price < face_value else 'Par')
                }

            elif calc_type == 'compare':
                # Compare multiple bonds
                bonds = data.get('bonds', [])
                
                if not bonds or len(bonds) < 2:
                    return JsonResponse({'success': False, 'error': 'Please provide at least 2 bonds to compare.'}, status=400)

                comparisons = []
                for i, bond in enumerate(bonds):
                    face_value = float(str(bond.get('face_value', 1000)).replace(',', ''))
                    coupon_rate = float(str(bond.get('coupon_rate', 0)).replace(',', ''))
                    bond_price = float(str(bond.get('price', face_value)).replace(',', ''))
                    years = float(str(bond.get('years_to_maturity', 10)).replace(',', ''))
                    freq = int(bond.get('payment_frequency', 2))
                    
                    coupon_payment = (face_value * coupon_rate / 100) / freq
                    periods = int(years * freq)
                    
                    # Calculate YTM
                    ytm_guess = 0.05 / freq
                    for _ in range(100):
                        price_calc = 0
                        dprice = 0
                        for t in range(1, periods + 1):
                            cf = coupon_payment if t < periods else coupon_payment + face_value
                            disc = np.power(1 + ytm_guess, t)
                            price_calc += cf / disc
                            dprice -= t * cf / np.power(1 + ytm_guess, t + 1)
                        diff = price_calc - bond_price
                        if abs(diff) < 0.0001:
                            break
                        ytm_guess = ytm_guess - diff / dprice
                        if ytm_guess < 0:
                            ytm_guess = 0.0001
                    
                    ytm = ytm_guess * freq * 100
                    current_yield = (face_value * coupon_rate / 100 / bond_price * 100) if bond_price > 0 else 0
                    
                    comparisons.append({
                        'bond': f'Bond {i+1}',
                        'face_value': round(face_value, 2),
                        'coupon_rate': coupon_rate,
                        'price': round(bond_price, 2),
                        'years_to_maturity': years,
                        'ytm': round(ytm, 2),
                        'current_yield': round(current_yield, 2),
                        'premium_discount': round(bond_price - face_value, 2)
                    })

                # Find best YTM
                best_ytm = max(comparisons, key=lambda x: x['ytm'])

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'comparisons': comparisons,
                    'best_yield': best_ytm['bond'],
                    'best_ytm_value': best_ytm['ytm']
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
