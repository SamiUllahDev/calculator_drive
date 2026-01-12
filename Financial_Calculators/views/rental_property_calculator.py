from django.views import View
from django.shortcuts import render


class RentalPropertyCalculator(View):
    """
    Class-based view for Rental Property Calculator
    """
    template_name = 'financial_calculators/rental_property_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Rental Property Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        context = {
            'calculator_name': 'Rental Property Calculator',
        }
        return render(request, self.template_name, context)
