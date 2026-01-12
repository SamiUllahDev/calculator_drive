from django.views import View
from django.shortcuts import render


class MortgageCalculatorUk(View):
    """
    Class-based view for Mortgage Calculator Uk
    """
    template_name = 'financial_calculators/mortgage_calculator_uk.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Mortgage Calculator Uk',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        context = {
            'calculator_name': 'Mortgage Calculator Uk',
        }
        return render(request, self.template_name, context)
