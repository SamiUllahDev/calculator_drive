from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class RentVsBuyCalculator(View):
    """
    Class-based view for Rent vs Buy Calculator
    Compares the costs of renting vs buying a home.
    """
    template_name = 'financial_calculators/rent_vs_buy_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rent vs Buy Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Buy inputs
            home_price = float(str(data.get('home_price', 0)).replace(',', ''))
            down_payment_pct = float(str(data.get('down_payment_pct', 20)).replace(',', ''))
            interest_rate = float(str(data.get('interest_rate', 6.5)).replace(',', ''))
            loan_term = int(data.get('loan_term', 30))
            property_tax_rate = float(str(data.get('property_tax_rate', 1.2)).replace(',', ''))
            home_insurance = float(str(data.get('home_insurance', 1200)).replace(',', ''))
            hoa = float(str(data.get('hoa', 0)).replace(',', ''))
            maintenance_rate = float(str(data.get('maintenance_rate', 1)).replace(',', ''))
            home_appreciation = float(str(data.get('home_appreciation', 3)).replace(',', ''))
            
            # Rent inputs
            monthly_rent = float(str(data.get('monthly_rent', 0)).replace(',', ''))
            rent_increase = float(str(data.get('rent_increase', 3)).replace(',', ''))
            renters_insurance = float(str(data.get('renters_insurance', 200)).replace(',', ''))
            
            # Investment inputs
            investment_return = float(str(data.get('investment_return', 7)).replace(',', ''))
            
            years = int(data.get('years', 7))
            
            # Validation
            if home_price <= 0:
                return JsonResponse({'success': False, 'error': 'Please enter a valid home price.'}, status=400)
            
            if monthly_rent <= 0:
                return JsonResponse({'success': False, 'error': 'Please enter a valid monthly rent.'}, status=400)
            
            # Calculate buying costs
            down_payment = home_price * (down_payment_pct / 100)
            loan_amount = home_price - down_payment
            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term * 12
            
            # Monthly mortgage payment
            if monthly_rate > 0:
                monthly_mortgage = loan_amount * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_mortgage = loan_amount / num_payments
            
            # Monthly costs
            monthly_property_tax = (home_price * (property_tax_rate / 100)) / 12
            monthly_insurance = home_insurance / 12
            monthly_maintenance = (home_price * (maintenance_rate / 100)) / 12
            
            total_monthly_buy = monthly_mortgage + monthly_property_tax + monthly_insurance + hoa + monthly_maintenance
            
            # Calculate over time
            buy_yearly = []
            rent_yearly = []
            
            remaining_balance = loan_amount
            total_buy_cost = down_payment
            total_rent_cost = 0
            current_rent = monthly_rent
            current_home_value = home_price
            investment_value = down_payment  # If renting, invest the down payment
            
            for year in range(1, years + 1):
                # Buy costs for this year
                yearly_mortgage = monthly_mortgage * 12
                yearly_interest = 0
                yearly_principal = 0
                
                for _ in range(12):
                    interest = remaining_balance * monthly_rate
                    principal = monthly_mortgage - interest
                    remaining_balance = max(0, remaining_balance - principal)
                    yearly_interest += interest
                    yearly_principal += principal
                
                yearly_property_tax = home_price * (property_tax_rate / 100)
                yearly_insurance = home_insurance
                yearly_hoa = hoa * 12
                yearly_maintenance = home_price * (maintenance_rate / 100)
                
                yearly_buy = yearly_mortgage + yearly_property_tax + yearly_insurance + yearly_hoa + yearly_maintenance
                total_buy_cost += yearly_buy
                
                # Home appreciation
                current_home_value *= (1 + home_appreciation / 100)
                
                # Rent costs for this year
                yearly_rent = current_rent * 12 + renters_insurance
                total_rent_cost += yearly_rent
                
                # Investment growth (difference invested)
                monthly_savings = total_monthly_buy - (current_rent + renters_insurance / 12)
                if monthly_savings > 0:
                    # Renter can invest the difference
                    investment_value = investment_value * (1 + investment_return / 100) + (monthly_savings * 12)
                else:
                    investment_value = investment_value * (1 + investment_return / 100)
                
                buy_yearly.append({
                    'year': year,
                    'monthly_cost': round(total_monthly_buy, 2),
                    'yearly_cost': round(yearly_buy, 2),
                    'total_cost': round(total_buy_cost, 2),
                    'home_equity': round(current_home_value - remaining_balance, 2),
                    'home_value': round(current_home_value, 2)
                })
                
                rent_yearly.append({
                    'year': year,
                    'monthly_cost': round(current_rent + renters_insurance / 12, 2),
                    'yearly_cost': round(yearly_rent, 2),
                    'total_cost': round(total_rent_cost, 2),
                    'investment_value': round(investment_value, 2)
                })
                
                # Rent increase for next year
                current_rent *= (1 + rent_increase / 100)
            
            # Calculate net position at end
            buy_net = current_home_value - remaining_balance - total_buy_cost
            rent_net = investment_value - total_rent_cost
            
            advantage = 'buy' if buy_net > rent_net else 'rent'
            difference = abs(buy_net - rent_net)
            
            # Breakeven calculation
            breakeven_year = None
            for year in range(1, years + 1):
                buy_equity = buy_yearly[year-1]['home_equity'] - buy_yearly[year-1]['total_cost']
                rent_wealth = rent_yearly[year-1]['investment_value'] - rent_yearly[year-1]['total_cost']
                if buy_equity > rent_wealth and breakeven_year is None:
                    breakeven_year = year
            
            result = {
                'success': True,
                'summary': {
                    'advantage': advantage,
                    'difference': round(difference, 2),
                    'breakeven_year': breakeven_year,
                    'buy': {
                        'monthly_payment': round(total_monthly_buy, 2),
                        'total_cost': round(total_buy_cost, 2),
                        'final_home_value': round(current_home_value, 2),
                        'final_equity': round(current_home_value - remaining_balance, 2),
                        'net_position': round(buy_net, 2)
                    },
                    'rent': {
                        'initial_rent': round(monthly_rent, 2),
                        'final_rent': round(current_rent / (1 + rent_increase / 100), 2),
                        'total_cost': round(total_rent_cost, 2),
                        'investment_value': round(investment_value, 2),
                        'net_position': round(rent_net, 2)
                    }
                },
                'buy_yearly': buy_yearly,
                'rent_yearly': rent_yearly,
                'chart_data': {
                    'labels': [f"Year {y['year']}" for y in buy_yearly],
                    'buy_equity': [y['home_equity'] for y in buy_yearly],
                    'rent_investment': [y['investment_value'] for y in rent_yearly],
                    'buy_cost': [y['total_cost'] for y in buy_yearly],
                    'rent_cost': [y['total_cost'] for y in rent_yearly]
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
