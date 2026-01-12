from django.views import View
from django.shortcuts import render


class CashBackCalculator(View):
    """
    Class-based view for Cash Back Calculator
    """
    template_name = 'financial_calculators/cash_back_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Cash Back Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        context = {
            'calculator_name': 'Cash Back Calculator',
        }
        return render(request, self.template_name, context)
