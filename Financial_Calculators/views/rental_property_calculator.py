from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json


def _parse_num(val, default=0):
    """Parse string with commas/percent to float."""
    if val is None or val == '' or val == 'null':
        return default
    if isinstance(val, (int, float)):
        return float(val)
    return float(str(val).replace(',', '').replace('$', '').replace('%', '').strip() or default)


@method_decorator(ensure_csrf_cookie, name='dispatch')
class RentalPropertyCalculator(View):
    """
    Class-based view for Rental Property Calculator.
    Calculates cap rate, NOI, cash flow, gross yield, and related metrics.
    """
    template_name = 'financial_calculators/rental_property_calculator.html'

    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rental Property Calculator',
            'page_title': 'Rental Property Calculator - Cash Flow & ROI Analysis',
        }
        return render(request, self.template_name, context)

    def _get_data(self, request):
        """Parse JSON or form POST into a flat dict."""
        if request.content_type and 'application/json' in request.content_type:
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

            property_price = _parse_num(data.get('property_price'), 0)
            monthly_rent = _parse_num(data.get('monthly_rent'), 0)
            monthly_expenses = _parse_num(data.get('monthly_expenses'), 0)
            vacancy_rate = _parse_num(data.get('vacancy_rate'), 5)
            monthly_mortgage = _parse_num(data.get('monthly_mortgage'), 0)

            if property_price <= 0:
                return JsonResponse({'success': False, 'error': 'Property price must be greater than zero.'}, status=400)
            if monthly_rent < 0:
                return JsonResponse({'success': False, 'error': 'Monthly rental income cannot be negative.'}, status=400)
            if monthly_expenses < 0:
                return JsonResponse({'success': False, 'error': 'Monthly expenses cannot be negative.'}, status=400)

            gross_annual_income = monthly_rent * 12
            effective_annual_income = gross_annual_income * (1 - vacancy_rate / 100)
            annual_expenses = monthly_expenses * 12
            noi = effective_annual_income - annual_expenses
            annual_debt = monthly_mortgage * 12
            annual_cash_flow = noi - annual_debt
            monthly_cash_flow = annual_cash_flow / 12

            cap_rate = (noi / property_price * 100) if property_price > 0 else 0
            gross_yield = (gross_annual_income / property_price * 100) if property_price > 0 else 0

            chart_data = self._prepare_chart_data(
                effective_annual_income, annual_expenses, annual_debt
            )

            result = {
                'success': True,
                'property_price': round(property_price, 2),
                'monthly_rent': round(monthly_rent, 2),
                'monthly_expenses': round(monthly_expenses, 2),
                'vacancy_rate': round(vacancy_rate, 2),
                'gross_annual_income': round(gross_annual_income, 2),
                'effective_annual_income': round(effective_annual_income, 2),
                'annual_expenses': round(annual_expenses, 2),
                'noi': round(noi, 2),
                'monthly_mortgage': round(monthly_mortgage, 2),
                'annual_cash_flow': round(annual_cash_flow, 2),
                'monthly_cash_flow': round(monthly_cash_flow, 2),
                'cap_rate': round(cap_rate, 2),
                'gross_yield': round(gross_yield, 2),
                'chart_data': chart_data,
            }
            return JsonResponse(result)

        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': 'An error occurred during calculation.'}, status=500)

    def _prepare_chart_data(self, effective_income, annual_expenses, annual_debt):
        """Build Chart.js-ready config for income vs expenses breakdown."""
        # Cash flow breakdown: Effective Income, then subtract Expenses and Debt
        breakdown_chart = {
            'type': 'bar',
            'data': {
                'labels': [
                    'Effective Income',
                    'Operating Expenses',
                    'Mortgage (Debt)',
                    'Net Cash Flow'
                ],
                'datasets': [{
                    'label': 'Annual Amount ($)',
                    'data': [
                        round(effective_income, 0),
                        round(-annual_expenses, 0),
                        round(-annual_debt, 0),
                        round(effective_income - annual_expenses - annual_debt, 0)
                    ],
                    'backgroundColor': [
                        'rgba(37, 99, 235, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(5, 150, 105, 0.8)'
                    ],
                    'borderColor': ['#2563eb', '#ef4444', '#f59e0b', '#059669'],
                    'borderWidth': 1
                }]
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {'legend': {'display': False}},
                'scales': {
                    'y': {'beginAtZero': True},
                    'x': {}
                }
            }
        }
        return {'breakdown_chart': breakdown_chart}
