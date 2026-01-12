from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import json


class BudgetCalculator(View):
    """
    Class-based view for Budget Calculator
    Helps users create and analyze their monthly budget.
    """
    template_name = 'financial_calculators/budget_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Budget Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            
            # Income
            salary = float(str(data.get('salary', 0)).replace(',', ''))
            other_income = float(str(data.get('other_income', 0)).replace(',', ''))
            total_income = salary + other_income
            
            # Housing expenses
            rent_mortgage = float(str(data.get('rent_mortgage', 0)).replace(',', ''))
            utilities = float(str(data.get('utilities', 0)).replace(',', ''))
            insurance_home = float(str(data.get('insurance_home', 0)).replace(',', ''))
            
            # Transportation
            car_payment = float(str(data.get('car_payment', 0)).replace(',', ''))
            gas = float(str(data.get('gas', 0)).replace(',', ''))
            car_insurance = float(str(data.get('car_insurance', 0)).replace(',', ''))
            
            # Living expenses
            groceries = float(str(data.get('groceries', 0)).replace(',', ''))
            dining = float(str(data.get('dining', 0)).replace(',', ''))
            entertainment = float(str(data.get('entertainment', 0)).replace(',', ''))
            
            # Debt payments
            credit_cards = float(str(data.get('credit_cards', 0)).replace(',', ''))
            student_loans = float(str(data.get('student_loans', 0)).replace(',', ''))
            other_debt = float(str(data.get('other_debt', 0)).replace(',', ''))
            
            # Savings
            savings = float(str(data.get('savings', 0)).replace(',', ''))
            retirement = float(str(data.get('retirement', 0)).replace(',', ''))
            
            # Other
            healthcare = float(str(data.get('healthcare', 0)).replace(',', ''))
            other_expenses = float(str(data.get('other_expenses', 0)).replace(',', ''))
            
            # Validation
            if total_income <= 0:
                return JsonResponse({'success': False, 'error': 'Please enter a valid income.'}, status=400)
            
            # Calculate category totals
            housing = rent_mortgage + utilities + insurance_home
            transportation = car_payment + gas + car_insurance
            living = groceries + dining + entertainment
            debt = credit_cards + student_loans + other_debt
            savings_total = savings + retirement
            other = healthcare + other_expenses
            
            total_expenses = housing + transportation + living + debt + savings_total + other
            remaining = total_income - total_expenses
            
            # Calculate percentages
            def pct(val):
                return round((val / total_income) * 100, 1) if total_income > 0 else 0
            
            # Budget health assessment
            housing_pct = pct(housing)
            savings_pct = pct(savings_total)
            debt_pct = pct(debt)
            
            status = 'healthy'
            recommendations = []
            
            if remaining < 0:
                status = 'deficit'
                recommendations.append('You are spending more than you earn. Review expenses to reduce spending.')
            elif housing_pct > 30:
                status = 'warning'
                recommendations.append(f'Housing costs ({housing_pct}%) exceed the recommended 30% of income.')
            elif savings_pct < 20:
                recommendations.append(f'Try to save at least 20% of income. Currently saving {savings_pct}%.')
            elif debt_pct > 20:
                recommendations.append(f'Debt payments ({debt_pct}%) are high. Consider debt reduction strategies.')
            
            if remaining > 0 and savings_pct < 20:
                recommendations.append(f'Consider allocating ${remaining:,.0f} to savings or debt payoff.')
            
            if savings_pct >= 20 and housing_pct <= 30 and debt_pct <= 20 and remaining >= 0:
                recommendations.append('Great job! Your budget follows healthy financial guidelines.')
            
            result = {
                'success': True,
                'summary': {
                    'total_income': round(total_income, 2),
                    'total_expenses': round(total_expenses, 2),
                    'remaining': round(remaining, 2),
                    'status': status,
                    'recommendations': recommendations
                },
                'categories': {
                    'housing': {'amount': round(housing, 2), 'percentage': pct(housing)},
                    'transportation': {'amount': round(transportation, 2), 'percentage': pct(transportation)},
                    'living': {'amount': round(living, 2), 'percentage': pct(living)},
                    'debt': {'amount': round(debt, 2), 'percentage': pct(debt)},
                    'savings': {'amount': round(savings_total, 2), 'percentage': pct(savings_total)},
                    'other': {'amount': round(other, 2), 'percentage': pct(other)}
                },
                'chart_data': {
                    'labels': ['Housing', 'Transport', 'Living', 'Debt', 'Savings', 'Other'],
                    'values': [housing, transportation, living, debt, savings_total, other],
                    'colors': ['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6', '#6b7280']
                },
                'recommended': {
                    'housing': round(total_income * 0.30, 2),
                    'transportation': round(total_income * 0.15, 2),
                    'living': round(total_income * 0.15, 2),
                    'debt': round(total_income * 0.10, 2),
                    'savings': round(total_income * 0.20, 2),
                    'other': round(total_income * 0.10, 2)
                }
            }
            
            return JsonResponse(result)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)
