from django.views import View
from django.shortcuts import render


class ScientificNotationCalculator(View):
    """
    Class-based view for Scientific Notation Calculator
    """
    template_name = 'math_calculators/scientific_notation_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Scientific Notation Calculator',
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for calculations"""
        context = {
            'calculator_name': 'Scientific Notation Calculator',
        }
        return render(request, self.template_name, context)
