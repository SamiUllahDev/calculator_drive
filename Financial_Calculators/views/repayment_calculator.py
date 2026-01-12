from django.views import View
from django.shortcuts import render


class RepaymentCalculator(View):
    """
    Class-based view for Repayment Calculator
    """
    template_name = 'financial_calculators/repayment_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Repayment Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        context = {
            'calculator_name': 'Repayment Calculator',
        }
        return render(request, self.template_name, context)
