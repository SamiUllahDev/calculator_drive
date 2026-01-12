from django.views import View
from django.shortcuts import render


class FinanceCalculator(View):
    """
    Class-based view for Finance Calculator
    """
    template_name = 'financial_calculators/finance_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Finance Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        context = {
            'calculator_name': 'Finance Calculator',
        }
        return render(request, self.template_name, context)
