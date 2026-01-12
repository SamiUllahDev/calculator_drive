from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json
import numpy as np


class RealEstateCalculator(View):
    """
    Class-based view for Real Estate Investment Calculator
    Calculates ROI, cash flow, cap rate, and other investment metrics.
    """
    template_name = 'financial_calculators/real_estate_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Real Estate Calculator',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        """Handle POST request for real estate calculations"""
        try:
            data = json.loads(request.body)

            calc_type = data.get('calc_type', 'investment_analysis')

            if calc_type == 'investment_analysis':
                # Property details
                purchase_price = float(str(data.get('purchase_price', 0)).replace(',', ''))
                down_payment_percent = float(str(data.get('down_payment_percent', 20)).replace(',', ''))
                closing_costs = float(str(data.get('closing_costs', 0)).replace(',', ''))
                repair_costs = float(str(data.get('repair_costs', 0)).replace(',', ''))
                
                # Financing
                interest_rate = float(str(data.get('interest_rate', 0)).replace(',', ''))
                loan_term = int(data.get('loan_term', 360))  # months
                
                # Income
                monthly_rent = float(str(data.get('monthly_rent', 0)).replace(',', ''))
                other_income = float(str(data.get('other_income', 0)).replace(',', ''))
                vacancy_rate = float(str(data.get('vacancy_rate', 5)).replace(',', ''))
                
                # Expenses
                property_tax_annual = float(str(data.get('property_tax', 0)).replace(',', ''))
                insurance_annual = float(str(data.get('insurance', 0)).replace(',', ''))
                hoa_monthly = float(str(data.get('hoa', 0)).replace(',', ''))
                maintenance_percent = float(str(data.get('maintenance_percent', 5)).replace(',', ''))
                management_percent = float(str(data.get('management_percent', 0)).replace(',', ''))
                utilities_monthly = float(str(data.get('utilities', 0)).replace(',', ''))
                
                # Appreciation
                appreciation_rate = float(str(data.get('appreciation_rate', 3)).replace(',', ''))
                rent_increase_rate = float(str(data.get('rent_increase_rate', 2)).replace(',', ''))

                if purchase_price <= 0:
                    return JsonResponse({'success': False, 'error': 'Purchase price must be greater than zero.'}, status=400)

                # Calculate down payment and loan
                down_payment = purchase_price * (down_payment_percent / 100)
                loan_amount = purchase_price - down_payment
                total_cash_needed = down_payment + closing_costs + repair_costs

                # Monthly mortgage payment
                monthly_rate = interest_rate / 100 / 12
                if monthly_rate > 0 and loan_amount > 0:
                    mortgage_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    mortgage_payment = loan_amount / loan_term if loan_term > 0 else 0

                # Gross income
                gross_monthly_rent = monthly_rent + other_income
                gross_annual_rent = gross_monthly_rent * 12
                
                # Effective income (accounting for vacancy)
                effective_gross_income = gross_annual_rent * (1 - vacancy_rate / 100)

                # Operating expenses
                property_tax_monthly = property_tax_annual / 12
                insurance_monthly = insurance_annual / 12
                maintenance_monthly = monthly_rent * (maintenance_percent / 100)
                management_monthly = monthly_rent * (management_percent / 100)
                
                total_monthly_expenses = (property_tax_monthly + insurance_monthly + 
                                         hoa_monthly + maintenance_monthly + 
                                         management_monthly + utilities_monthly)
                total_annual_expenses = total_monthly_expenses * 12

                # Net Operating Income (NOI)
                noi = effective_gross_income - total_annual_expenses

                # Cash flow
                monthly_cash_flow = (effective_gross_income / 12) - total_monthly_expenses - mortgage_payment
                annual_cash_flow = monthly_cash_flow * 12

                # Key metrics
                cap_rate = (noi / purchase_price * 100) if purchase_price > 0 else 0
                cash_on_cash_return = (annual_cash_flow / total_cash_needed * 100) if total_cash_needed > 0 else 0
                gross_rent_multiplier = purchase_price / gross_annual_rent if gross_annual_rent > 0 else 0
                
                # 1% Rule check
                one_percent_rule = monthly_rent >= (purchase_price * 0.01)
                
                # 50% Rule estimate
                estimated_expenses_50 = gross_monthly_rent * 0.5
                estimated_cash_flow_50 = gross_monthly_rent - estimated_expenses_50 - mortgage_payment

                # Debt Service Coverage Ratio (DSCR)
                annual_debt_service = mortgage_payment * 12
                dscr = noi / annual_debt_service if annual_debt_service > 0 else 0

                # Total return projection (5 years)
                projections = []
                property_value = purchase_price
                annual_rent = gross_annual_rent
                cumulative_cash_flow = 0
                loan_balance = loan_amount

                for year in range(1, 6):
                    # Property appreciation
                    property_value *= (1 + appreciation_rate / 100)
                    
                    # Rent increase
                    annual_rent *= (1 + rent_increase_rate / 100)
                    eff_rent = annual_rent * (1 - vacancy_rate / 100)
                    
                    # Update expenses (assume they grow with inflation ~3%)
                    yearly_expenses = total_annual_expenses * np.power(1.03, year - 1)
                    yearly_noi = eff_rent - yearly_expenses
                    yearly_cash_flow = yearly_noi - annual_debt_service
                    cumulative_cash_flow += yearly_cash_flow
                    
                    # Loan paydown (simplified)
                    interest_paid = loan_balance * (interest_rate / 100)
                    principal_paid = annual_debt_service - interest_paid
                    loan_balance = max(0, loan_balance - principal_paid)
                    
                    # Equity
                    equity = property_value - loan_balance
                    
                    projections.append({
                        'year': year,
                        'property_value': round(property_value, 2),
                        'annual_rent': round(annual_rent, 2),
                        'noi': round(yearly_noi, 2),
                        'cash_flow': round(yearly_cash_flow, 2),
                        'cumulative_cash_flow': round(cumulative_cash_flow, 2),
                        'loan_balance': round(loan_balance, 2),
                        'equity': round(equity, 2)
                    })

                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'purchase': {
                        'purchase_price': round(purchase_price, 2),
                        'down_payment': round(down_payment, 2),
                        'down_payment_percent': down_payment_percent,
                        'loan_amount': round(loan_amount, 2),
                        'closing_costs': round(closing_costs, 2),
                        'repair_costs': round(repair_costs, 2),
                        'total_cash_needed': round(total_cash_needed, 2)
                    },
                    'financing': {
                        'loan_amount': round(loan_amount, 2),
                        'interest_rate': interest_rate,
                        'term_years': round(loan_term / 12, 1),
                        'monthly_payment': round(mortgage_payment, 2),
                        'annual_debt_service': round(annual_debt_service, 2)
                    },
                    'income': {
                        'monthly_rent': round(monthly_rent, 2),
                        'other_income': round(other_income, 2),
                        'gross_monthly': round(gross_monthly_rent, 2),
                        'gross_annual': round(gross_annual_rent, 2),
                        'vacancy_rate': vacancy_rate,
                        'effective_gross_income': round(effective_gross_income, 2)
                    },
                    'expenses': {
                        'property_tax_monthly': round(property_tax_monthly, 2),
                        'insurance_monthly': round(insurance_monthly, 2),
                        'hoa_monthly': round(hoa_monthly, 2),
                        'maintenance_monthly': round(maintenance_monthly, 2),
                        'management_monthly': round(management_monthly, 2),
                        'utilities_monthly': round(utilities_monthly, 2),
                        'total_monthly': round(total_monthly_expenses, 2),
                        'total_annual': round(total_annual_expenses, 2)
                    },
                    'analysis': {
                        'noi': round(noi, 2),
                        'monthly_cash_flow': round(monthly_cash_flow, 2),
                        'annual_cash_flow': round(annual_cash_flow, 2),
                        'cap_rate': round(cap_rate, 2),
                        'cash_on_cash_return': round(cash_on_cash_return, 2),
                        'gross_rent_multiplier': round(gross_rent_multiplier, 2),
                        'dscr': round(dscr, 2),
                        'one_percent_rule': one_percent_rule,
                        'estimated_cash_flow_50_rule': round(estimated_cash_flow_50, 2)
                    },
                    'projections': projections
                }

            elif calc_type == 'rent_vs_buy':
                # Rent vs Buy comparison
                home_price = float(str(data.get('home_price', 0)).replace(',', ''))
                down_payment_percent = float(str(data.get('down_payment_percent', 20)).replace(',', ''))
                interest_rate = float(str(data.get('interest_rate', 7)).replace(',', ''))
                property_tax_rate = float(str(data.get('property_tax_rate', 1.2)).replace(',', ''))
                insurance_annual = float(str(data.get('insurance', 1200)).replace(',', ''))
                maintenance_rate = float(str(data.get('maintenance_rate', 1)).replace(',', ''))
                appreciation_rate = float(str(data.get('appreciation_rate', 3)).replace(',', ''))
                
                monthly_rent = float(str(data.get('monthly_rent', 0)).replace(',', ''))
                rent_increase_rate = float(str(data.get('rent_increase_rate', 3)).replace(',', ''))
                investment_return = float(str(data.get('investment_return', 7)).replace(',', ''))
                
                years_to_compare = int(data.get('years', 10))

                if home_price <= 0 or monthly_rent <= 0:
                    return JsonResponse({'success': False, 'error': 'Home price and rent must be greater than zero.'}, status=400)

                # Buy scenario
                down_payment = home_price * (down_payment_percent / 100)
                loan_amount = home_price - down_payment
                monthly_rate = interest_rate / 100 / 12
                loan_term = 360

                if monthly_rate > 0:
                    mortgage_payment = loan_amount * (monthly_rate * np.power(1 + monthly_rate, loan_term)) / (np.power(1 + monthly_rate, loan_term) - 1)
                else:
                    mortgage_payment = loan_amount / loan_term

                # Rent scenario
                comparison = []
                buy_total_cost = down_payment
                rent_total_cost = 0
                investment_balance = down_payment  # If renting, invest the down payment

                current_home_value = home_price
                current_rent = monthly_rent
                loan_balance = loan_amount

                for year in range(1, years_to_compare + 1):
                    # Buying costs for the year
                    yearly_mortgage = mortgage_payment * 12
                    yearly_taxes = current_home_value * (property_tax_rate / 100)
                    yearly_insurance = insurance_annual
                    yearly_maintenance = current_home_value * (maintenance_rate / 100)
                    yearly_buy_cost = yearly_mortgage + yearly_taxes + yearly_insurance + yearly_maintenance
                    buy_total_cost += yearly_buy_cost

                    # Home appreciation
                    current_home_value *= (1 + appreciation_rate / 100)
                    
                    # Loan paydown
                    interest_paid = loan_balance * (interest_rate / 100)
                    principal_paid = yearly_mortgage - interest_paid
                    loan_balance = max(0, loan_balance - principal_paid)
                    
                    equity = current_home_value - loan_balance

                    # Renting costs for the year
                    yearly_rent = current_rent * 12
                    rent_total_cost += yearly_rent
                    current_rent *= (1 + rent_increase_rate / 100)

                    # Investment growth (difference saved from lower payments)
                    monthly_difference = yearly_buy_cost / 12 - monthly_rent
                    if monthly_difference > 0:
                        # Renter can invest the difference
                        investment_balance = investment_balance * (1 + investment_return / 100) + (monthly_difference * 12)
                    else:
                        investment_balance *= (1 + investment_return / 100)

                    comparison.append({
                        'year': year,
                        'buy_yearly_cost': round(yearly_buy_cost, 2),
                        'buy_total_cost': round(buy_total_cost, 2),
                        'home_value': round(current_home_value, 2),
                        'equity': round(equity, 2),
                        'rent_yearly': round(yearly_rent, 2),
                        'rent_total_cost': round(rent_total_cost, 2),
                        'investment_balance': round(investment_balance, 2),
                        'renter_net_worth': round(investment_balance, 2),
                        'buyer_net_worth': round(equity, 2)
                    })

                # Final comparison
                final_buyer_wealth = current_home_value - loan_balance
                final_renter_wealth = investment_balance
                
                result = {
                    'success': True,
                    'calc_type': calc_type,
                    'buy_scenario': {
                        'home_price': round(home_price, 2),
                        'down_payment': round(down_payment, 2),
                        'loan_amount': round(loan_amount, 2),
                        'monthly_mortgage': round(mortgage_payment, 2)
                    },
                    'rent_scenario': {
                        'starting_rent': round(monthly_rent, 2),
                        'rent_increase_rate': rent_increase_rate
                    },
                    'comparison': comparison,
                    'final_analysis': {
                        'buyer_net_worth': round(final_buyer_wealth, 2),
                        'renter_net_worth': round(final_renter_wealth, 2),
                        'difference': round(final_buyer_wealth - final_renter_wealth, 2),
                        'recommendation': 'Buying is better' if final_buyer_wealth > final_renter_wealth else 'Renting is better'
                    }
                }

            else:
                return JsonResponse({'success': False, 'error': 'Invalid calculation type.'}, status=400)

            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
