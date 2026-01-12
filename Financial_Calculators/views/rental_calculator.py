from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class RentalCalculator(View):
    """
    Class-based view for Rental Property Calculator
    Calculates rental property cash flow, ROI, and investment metrics.
    """
    template_name = 'financial_calculators/rental_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rental Property Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for rental property calculations"""
        try:
            data = json.loads(request.body)

            # Property info
            purchase_price = float(str(data.get('purchase_price', 0)).replace(',', ''))
            down_payment = float(str(data.get('down_payment', 0)).replace(',', ''))
            down_payment_type = data.get('down_payment_type', 'percent')
            closing_costs = float(str(data.get('closing_costs', 0)).replace(',', ''))
            renovation_costs = float(str(data.get('renovation_costs', 0)).replace(',', ''))
            after_repair_value = float(str(data.get('after_repair_value', 0)).replace(',', ''))
            
            # Financing
            interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
            loan_term = int(data.get('loan_term', 360))
            
            # Rental income
            monthly_rent = float(str(data.get('monthly_rent', 0)).replace(',', ''))
            vacancy_rate = float(str(data.get('vacancy_rate', 8)).replace(',', ''))
            
            # Operating expenses (monthly)
            property_tax = float(str(data.get('property_tax', 0)).replace(',', ''))
            insurance = float(str(data.get('insurance', 0)).replace(',', ''))
            hoa_fees = float(str(data.get('hoa_fees', 0)).replace(',', ''))
            property_management = float(str(data.get('property_management', 0)).replace(',', ''))
            maintenance = float(str(data.get('maintenance', 0)).replace(',', ''))
            utilities = float(str(data.get('utilities', 0)).replace(',', ''))
            other_expenses = float(str(data.get('other_expenses', 0)).replace(',', ''))

            if purchase_price <= 0:
                return JsonResponse({'success': False, 'error': 'Purchase price must be greater than zero.'}, status=400)
            if monthly_rent <= 0:
                return JsonResponse({'success': False, 'error': 'Monthly rent must be greater than zero.'}, status=400)

            # Calculate down payment
            if down_payment_type == 'percent':
                down_payment_amount = purchase_price * (down_payment / 100)
                down_payment_percent = down_payment
            else:
                down_payment_amount = down_payment
                down_payment_percent = (down_payment / purchase_price * 100) if purchase_price > 0 else 0

            # Loan amount
            loan_amount = purchase_price - down_payment_amount

            # Total investment
            total_investment = down_payment_amount + closing_costs + renovation_costs

            # Monthly mortgage payment
            monthly_rate = interest_rate / 100 / 12
            if monthly_rate > 0 and loan_amount > 0:
                mortgage_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
            else:
                mortgage_payment = loan_amount / loan_term if loan_term > 0 else 0

            # Income calculations
            gross_monthly_income = monthly_rent
            gross_annual_income = gross_monthly_income * 12
            vacancy_loss = gross_monthly_income * (vacancy_rate / 100)
            effective_monthly_income = gross_monthly_income - vacancy_loss
            effective_annual_income = effective_monthly_income * 12

            # Operating expenses (monthly)
            total_operating_expenses = (property_tax + insurance + hoa_fees + 
                                       property_management + maintenance + 
                                       utilities + other_expenses)
            annual_operating_expenses = total_operating_expenses * 12

            # Net Operating Income (NOI)
            monthly_noi = effective_monthly_income - total_operating_expenses
            annual_noi = monthly_noi * 12

            # Cash flow (after debt service)
            monthly_cash_flow = monthly_noi - mortgage_payment
            annual_cash_flow = monthly_cash_flow * 12

            # Key investment metrics
            # Cap Rate = NOI / Purchase Price
            cap_rate = (annual_noi / purchase_price * 100) if purchase_price > 0 else 0

            # Cash on Cash Return = Annual Cash Flow / Total Investment
            cash_on_cash = (annual_cash_flow / total_investment * 100) if total_investment > 0 else 0

            # Gross Rent Multiplier = Purchase Price / Gross Annual Rent
            grm = purchase_price / gross_annual_income if gross_annual_income > 0 else 0

            # Operating Expense Ratio
            expense_ratio = (annual_operating_expenses / effective_annual_income * 100) if effective_annual_income > 0 else 0

            # Debt Service Coverage Ratio (DSCR)
            annual_debt_service = mortgage_payment * 12
            dscr = annual_noi / annual_debt_service if annual_debt_service > 0 else 0

            # 1% Rule and 2% Rule
            one_percent_rule = monthly_rent >= (purchase_price * 0.01)
            two_percent_rule = monthly_rent >= (purchase_price * 0.02)

            # 50% Rule estimation
            estimated_expenses_50 = gross_monthly_income * 0.5
            estimated_cash_flow_50 = gross_monthly_income - estimated_expenses_50 - mortgage_payment

            # Break-even Rent (what rent is needed to break even)
            break_even_rent = (total_operating_expenses + mortgage_payment) / (1 - vacancy_rate / 100)

            # BRRRR Analysis (if after repair value provided)
            brrrr_analysis = None
            if after_repair_value > 0:
                # Assume 75% LTV refinance
                max_refinance = after_repair_value * 0.75
                cash_recouped = max_refinance - loan_amount
                money_left_in_deal = total_investment - cash_recouped
                
                brrrr_analysis = {
                    'after_repair_value': round(after_repair_value, 2),
                    'max_refinance_75_ltv': round(max_refinance, 2),
                    'cash_recouped': round(cash_recouped, 2),
                    'money_left_in_deal': round(money_left_in_deal, 2),
                    'infinite_roi': money_left_in_deal <= 0
                }

            # Monthly breakdown
            income_breakdown = {
                'gross_rent': round(monthly_rent, 2),
                'vacancy_loss': round(vacancy_loss, 2),
                'effective_income': round(effective_monthly_income, 2)
            }

            expense_breakdown = {
                'property_tax': round(property_tax, 2),
                'insurance': round(insurance, 2),
                'hoa_fees': round(hoa_fees, 2),
                'property_management': round(property_management, 2),
                'maintenance': round(maintenance, 2),
                'utilities': round(utilities, 2),
                'other': round(other_expenses, 2),
                'total_operating': round(total_operating_expenses, 2),
                'mortgage': round(mortgage_payment, 2),
                'total_expenses': round(total_operating_expenses + mortgage_payment, 2)
            }

            # Annual projection (5 years)
            projections = []
            annual_appreciation = 3  # Assume 3% appreciation
            annual_rent_growth = 2   # Assume 2% rent growth
            
            property_value = purchase_price
            annual_rent_current = gross_annual_income
            cumulative_cash_flow = 0
            remaining_balance = loan_amount

            for year in range(1, 6):
                # Update values
                property_value *= (1 + annual_appreciation / 100)
                annual_rent_current *= (1 + annual_rent_growth / 100)
                
                # Calculate year's metrics
                year_effective_income = annual_rent_current * (1 - vacancy_rate / 100)
                year_expenses = annual_operating_expenses * (1.03 ** (year - 1))  # 3% expense growth
                year_noi = year_effective_income - year_expenses
                year_cash_flow = year_noi - annual_debt_service
                cumulative_cash_flow += year_cash_flow
                
                # Loan balance (simplified)
                interest_portion = remaining_balance * (interest_rate / 100)
                principal_portion = annual_debt_service - interest_portion
                remaining_balance = max(0, remaining_balance - principal_portion)
                
                # Equity
                equity = property_value - remaining_balance
                
                projections.append({
                    'year': year,
                    'property_value': round(property_value, 2),
                    'annual_rent': round(annual_rent_current, 2),
                    'noi': round(year_noi, 2),
                    'cash_flow': round(year_cash_flow, 2),
                    'cumulative_cash_flow': round(cumulative_cash_flow, 2),
                    'equity': round(equity, 2)
                })

            result = {
                'success': True,
                'property': {
                    'purchase_price': round(purchase_price, 2),
                    'down_payment': round(down_payment_amount, 2),
                    'down_payment_percent': round(down_payment_percent, 1),
                    'loan_amount': round(loan_amount, 2),
                    'closing_costs': round(closing_costs, 2),
                    'renovation_costs': round(renovation_costs, 2),
                    'total_investment': round(total_investment, 2)
                },
                'financing': {
                    'interest_rate': interest_rate,
                    'loan_term_years': round(loan_term / 12, 1),
                    'monthly_payment': round(mortgage_payment, 2),
                    'annual_debt_service': round(annual_debt_service, 2)
                },
                'income': income_breakdown,
                'expenses': expense_breakdown,
                'analysis': {
                    'monthly_noi': round(monthly_noi, 2),
                    'annual_noi': round(annual_noi, 2),
                    'monthly_cash_flow': round(monthly_cash_flow, 2),
                    'annual_cash_flow': round(annual_cash_flow, 2)
                },
                'metrics': {
                    'cap_rate': round(cap_rate, 2),
                    'cash_on_cash_return': round(cash_on_cash, 2),
                    'gross_rent_multiplier': round(grm, 2),
                    'expense_ratio': round(expense_ratio, 2),
                    'dscr': round(dscr, 2),
                    'break_even_rent': round(break_even_rent, 2)
                },
                'rules': {
                    'one_percent_rule': one_percent_rule,
                    'one_percent_amount': round(purchase_price * 0.01, 2),
                    'two_percent_rule': two_percent_rule,
                    'two_percent_amount': round(purchase_price * 0.02, 2),
                    'fifty_percent_rule_cash_flow': round(estimated_cash_flow_50, 2)
                },
                'brrrr_analysis': brrrr_analysis,
                'projections': projections,
                'chart_data': {
                    'income': round(effective_monthly_income, 2),
                    'operating_expenses': round(total_operating_expenses, 2),
                    'mortgage': round(mortgage_payment, 2),
                    'cash_flow': round(monthly_cash_flow, 2)
                }
            }

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)

