from django.shortcuts import render
from django.views.generic import TemplateView


class MathIndexView(TemplateView):
    template_name = 'math_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive math calculators list organized by categories
        calculators = [
            # Basic Arithmetic
            {'name': 'Basic Calculator', 'url': 'basic-calculator', 'category': 'Basic Arithmetic', 'description': 'Simple calculator for basic math operations'},
            {'name': 'Percentage Calculator', 'url': 'percentage-calculator', 'category': 'Basic Arithmetic', 'description': 'Calculate percentages and percentage changes'},
            {'name': 'Ratio Calculator', 'url': 'ratio-calculator', 'category': 'Basic Arithmetic', 'description': 'Calculate and simplify ratios'},
            {'name': 'Rounding Calculator', 'url': 'rounding-calculator', 'category': 'Basic Arithmetic', 'description': 'Round numbers to specified decimal places'},
            {'name': 'Long Division Calculator', 'url': 'long-division-calculator', 'category': 'Basic Arithmetic', 'description': 'Perform long division with step-by-step solutions'},
            
            # Algebra & Equations
            {'name': 'Quadratic Formula Calculator', 'url': 'quadratic-formula-calculator', 'category': 'Algebra & Equations', 'description': 'Solve quadratic equations using the quadratic formula'},
            {'name': 'Exponent Calculator', 'url': 'exponent-calculator', 'category': 'Algebra & Equations', 'description': 'Calculate exponential values and powers'},
            {'name': 'Root Calculator', 'url': 'root-calculator', 'category': 'Algebra & Equations', 'description': 'Calculate square roots, cube roots, and nth roots'},
            {'name': 'Log Calculator', 'url': 'log-calculator', 'category': 'Algebra & Equations', 'description': 'Calculate logarithmic values'},
            {'name': 'Scientific Notation Calculator', 'url': 'scientific-notation-calculator', 'category': 'Algebra & Equations', 'description': 'Convert numbers to and from scientific notation'},
            
            # Number Theory
            {'name': 'Factor Calculator', 'url': 'factor-calculator', 'category': 'Number Theory', 'description': 'Find all factors of a number'},
            {'name': 'Prime Factorization Calculator', 'url': 'prime-factorization-calculator', 'category': 'Number Theory', 'description': 'Find prime factorization of numbers'},
            {'name': 'Greatest Common Factor Calculator', 'url': 'greatest-common-factor-calculator', 'category': 'Number Theory', 'description': 'Calculate GCF of multiple numbers'},
            {'name': 'Least Common Multiple Calculator', 'url': 'least-common-multiple-calculator', 'category': 'Number Theory', 'description': 'Calculate LCM of multiple numbers'},
            {'name': 'Common Factor Calculator', 'url': 'common-factor-calculator', 'category': 'Number Theory', 'description': 'Find common factors between numbers'},
            
            # Geometry
            {'name': 'Area Calculator', 'url': 'area-calculator', 'category': 'Geometry', 'description': 'Calculate area of various shapes'},
            {'name': 'Volume Calculator', 'url': 'volume-calculator', 'category': 'Geometry', 'description': 'Calculate volume of 3D shapes'},
            {'name': 'Surface Area Calculator', 'url': 'surface-area-calculator', 'category': 'Geometry', 'description': 'Calculate surface area of 3D objects'},
            {'name': 'Pythagorean Theorem Calculator', 'url': 'pythagorean-theorem-calculator', 'category': 'Geometry', 'description': 'Use Pythagorean theorem to find triangle sides'},
            {'name': 'Circle Calculator', 'url': 'circle-calculator', 'category': 'Geometry', 'description': 'Calculate circle properties (area, circumference, radius)'},
            {'name': 'Triangle Calculator', 'url': 'triangle-calculator', 'category': 'Geometry', 'description': 'Calculate triangle properties and area'},
            {'name': 'Right Triangle Calculator', 'url': 'right-triangle-calculator', 'category': 'Geometry', 'description': 'Calculate right triangle properties'},
            {'name': 'Distance Calculator', 'url': 'distance-calculator', 'category': 'Geometry', 'description': 'Calculate distance between two points'},
            {'name': 'Slope Calculator', 'url': 'slope-calculator', 'category': 'Geometry', 'description': 'Calculate slope between two points'},
            
            # Statistics & Probability
            {'name': 'Average Calculator', 'url': 'average-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate average, mean, median, and mode'},
            {'name': 'Mean Median Mode Range Calculator', 'url': 'mean-median-mode-range-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate all central tendency and range values'},
            {'name': 'Standard Deviation Calculator', 'url': 'standard-deviation-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate standard deviation and variance'},
            {'name': 'Probability Calculator', 'url': 'probability-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate probability and odds'},
            {'name': 'Permutation and Combination Calculator', 'url': 'permutation-and-combination-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate permutations and combinations'},
            {'name': 'Z Score Calculator', 'url': 'z-score-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate z-scores for statistical analysis'},
            {'name': 'P Value Calculator', 'url': 'p-value-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate p-values for hypothesis testing'},
            {'name': 'Confidence Interval Calculator', 'url': 'confidence-interval-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate confidence intervals for data'},
            {'name': 'Sample Size Calculator', 'url': 'sample-size-calculator', 'category': 'Statistics & Probability', 'description': 'Calculate required sample size for studies'},
            {'name': 'Statistics Calculator', 'url': 'statistics-calculator', 'category': 'Statistics & Probability', 'description': 'Comprehensive statistical calculations'},
            
            # Sequences & Series
            {'name': 'Number Sequence Calculator', 'url': 'number-sequence-calculator', 'category': 'Sequences & Series', 'description': 'Generate and analyze number sequences'},
            
            # Number Systems
            {'name': 'Binary Calculator', 'url': 'binary-calculator', 'category': 'Number Systems', 'description': 'Convert and calculate binary numbers'},
            {'name': 'Hex Calculator', 'url': 'hex-calculator', 'category': 'Number Systems', 'description': 'Convert and calculate hexadecimal numbers'},
            {'name': 'Fraction Calculator', 'url': 'fraction-calculator', 'category': 'Number Systems', 'description': 'Calculate and simplify fractions'},
            {'name': 'Big Number Calculator', 'url': 'big-number-calculator', 'category': 'Number Systems', 'description': 'Perform calculations with very large numbers'},
            
            # Utilities
            {'name': 'Scientific Calculator', 'url': 'scientific-calculator', 'category': 'Utilities', 'description': 'Advanced scientific calculator with trigonometry'},
            {'name': 'Random Number Generator', 'url': 'random-number-generator', 'category': 'Utilities', 'description': 'Generate random numbers with custom ranges'},
            {'name': 'Percent Error Calculator', 'url': 'percent-error-calculator', 'category': 'Utilities', 'description': 'Calculate percent error for measurements'},
            {'name': 'Half Life Calculator', 'url': 'half-life-calculator', 'category': 'Utilities', 'description': 'Calculate radioactive decay half-life'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
