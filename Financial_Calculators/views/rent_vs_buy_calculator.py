from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import numpy as np


def _parse_num(val, default=0):
    """Parse string with commas/percent to float."""
    if val is None or val == '' or val == 'null':
        return default
    if isinstance(val, (int, float)):
        return float(val)
    return float(str(val).replace(',', '').replace('$', '').replace('%', '').strip() or default)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RentVsBuyCalculator(View):
    """
    Class-based view for Rent vs Buy Calculator.
    Compares the costs of renting vs buying a home over time.
    """
    template_name = 'financial_calculators/rent_vs_buy_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rent vs Buy Calculator',
            'page_title': 'Rent vs Buy Calculator - Should You Buy or Rent?',
        }
        return render(request, self.template_name, context)

    def _get_data(self, request):
        """Parse JSON or form POST into a flat dict."""
        if request.content_type == 'application/json':
            return json.loads(request.body)
        data = {}
        for k in request.POST:
            v = request.POST.getlist(k)
            data[k] = v[0] if len(v) == 1 else v
        return data

    def post(self, request):
        """Handle POST request for calculations (JSON or form)."""
        try:
            data = self._get_data(request)

            # Buy inputs
            home_price = _parse_num(data.get('home_price'), 0)
            down_payment_pct = _parse_num(data.get('down_payment_pct'), 20)
            interest_rate = _parse_num(data.get('interest_rate'), 6.5)
            loan_term = int(float(data.get('loan_term', 30) or 30))
            property_tax_rate = _parse_num(data.get('property_tax_rate'), 1.2)
            home_insurance = _parse_num(data.get('home_insurance'), 1200)
            hoa = _parse_num(data.get('hoa'), 0)
            maintenance_rate = _parse_num(data.get('maintenance_rate'), 1)
            home_appreciation = _parse_num(data.get('home_appreciation'), 3)

            # Rent inputs
            monthly_rent = _parse_num(data.get('monthly_rent'), 0)
            rent_increase = _parse_num(data.get('rent_increase'), 3)
            renters_insurance = _parse_num(data.get('renters_insurance'), 200)

            # Investment
            investment_return = _parse_num(data.get('investment_return'), 7)
            years = int(float(data.get('years', 7) or 7))

            # Validation
            if home_price <= 0:
                return JsonResponse({'success': False, 'error': 'Please enter a valid home price.'}, status=400)
            if monthly_rent <= 0:
                return JsonResponse({'success': False, 'error': 'Please enter a valid monthly rent.'}, status=400)
            if years < 1 or years > 30:
                return JsonResponse({'success': False, 'error': 'Time period must be between 1 and 30 years.'}, status=400)
            if loan_term < 1 or loan_term > 40:
                return JsonResponse({'success': False, 'error': 'Loan term must be between 1 and 40 years.'}, status=400)

            # Calculate buying costs
            down_payment = home_price * (down_payment_pct / 100)
            loan_amount = home_price - down_payment
            monthly_rate = (interest_rate / 100) / 12
            num_payments = loan_term * 12

            if monthly_rate > 0:
                rate_factor = np.power(1 + monthly_rate, num_payments)
                monthly_mortgage = loan_amount * (monthly_rate * rate_factor) / (rate_factor - 1)
            else:
                monthly_mortgage = loan_amount / num_payments

            monthly_property_tax = (home_price * (property_tax_rate / 100)) / 12
            monthly_insurance = home_insurance / 12
            monthly_maintenance = (home_price * (maintenance_rate / 100)) / 12
            total_monthly_buy = monthly_mortgage + monthly_property_tax + monthly_insurance + hoa + monthly_maintenance

            buy_yearly = []
            rent_yearly = []
            remaining_balance = loan_amount
            total_buy_cost = down_payment
            total_rent_cost = 0
            current_rent = monthly_rent
            current_home_value = home_price
            investment_value = down_payment

            for year in range(1, years + 1):
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
                yearly_buy = monthly_mortgage * 12 + yearly_property_tax + yearly_insurance + yearly_hoa + yearly_maintenance
                total_buy_cost += yearly_buy
                current_home_value *= (1 + home_appreciation / 100)

                yearly_rent = current_rent * 12 + renters_insurance
                total_rent_cost += yearly_rent

                monthly_savings = total_monthly_buy - (current_rent + renters_insurance / 12)
                if monthly_savings > 0:
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
                current_rent *= (1 + rent_increase / 100)

            buy_net = (current_home_value - remaining_balance) - total_buy_cost
            rent_net = investment_value - total_rent_cost
            advantage = 'buy' if buy_net > rent_net else 'rent'
            difference = abs(buy_net - rent_net)

            breakeven_year = None
            for year in range(1, years + 1):
                buy_net_y = buy_yearly[year - 1]['home_equity'] - buy_yearly[year - 1]['total_cost']
                rent_net_y = rent_yearly[year - 1]['investment_value'] - rent_yearly[year - 1]['total_cost']
                if buy_net_y > rent_net_y and breakeven_year is None:
                    breakeven_year = year

            # Chart.js-ready data
            chart_data = self._prepare_chart_data(buy_yearly, rent_yearly)

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
                'chart_data': chart_data,
            }
            return JsonResponse(result)

        except (ValueError, TypeError, KeyError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)

    def _prepare_chart_data(self, buy_yearly, rent_yearly):
        """Build Chart.js-ready line chart (wealth over time)."""
        labels = [f"Year {y['year']}" for y in buy_yearly]
        buy_equity = [y['home_equity'] for y in buy_yearly]
        rent_investment = [y['investment_value'] for y in rent_yearly]

        wealth_chart = {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Home Equity (Buy)',
                        'data': buy_equity,
                        'borderColor': '#2563eb',
                        'backgroundColor': 'rgba(37, 99, 235, 0.1)',
                        'fill': True,
                        'tension': 0.3,
                    },
                    {
                        'label': 'Investments (Rent)',
                        'data': rent_investment,
                        'borderColor': '#f59e0b',
                        'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                        'fill': True,
                        'tension': 0.3,
                    }
                ]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'position': 'bottom'}},
                'scales': {'y': {'beginAtZero': True}}
            }
        }
        return {
            'wealth_chart': wealth_chart,
            'labels': labels,
            'buy_equity': buy_equity,
            'rent_investment': rent_investment,
            'buy_cost': [y['total_cost'] for y in buy_yearly],
            'rent_cost': [y['total_cost'] for y in rent_yearly],
        }
