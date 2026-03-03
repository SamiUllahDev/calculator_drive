from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.translation import gettext as _


class MathIndexView(TemplateView):
    template_name = 'math_calculators/index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Comprehensive math calculators list organized by categories
        calculators = [
            # Basic Arithmetic
            {'name': _('Basic Calculator'), 'url': 'basic-calculator', 'category': _('Basic Arithmetic'), 'description': _('Simple calculator for basic math operations'), 'icon': 'fas fa-plus-minus'},
            {'name': _('Percentage Calculator'), 'url': 'percentage-calculator', 'category': _('Basic Arithmetic'), 'description': _('Calculate percentages and percentage changes'), 'icon': 'fas fa-percent'},
            {'name': _('Ratio Calculator'), 'url': 'ratio-calculator', 'category': _('Basic Arithmetic'), 'description': _('Calculate and simplify ratios'), 'icon': 'fas fa-scale-balanced'},
            {'name': _('Rounding Calculator'), 'url': 'rounding-calculator', 'category': _('Basic Arithmetic'), 'description': _('Round numbers to specified decimal places'), 'icon': 'fas fa-arrows-up-down'},
            {'name': _('Long Division Calculator'), 'url': 'long-division-calculator', 'category': _('Basic Arithmetic'), 'description': _('Perform long division with step-by-step solutions'), 'icon': 'fas fa-divide'},
            
            # Algebra & Equations
            {'name': _('Quadratic Formula Calculator'), 'url': 'quadratic-formula-calculator', 'category': _('Algebra & Equations'), 'description': _('Solve quadratic equations using the quadratic formula'), 'icon': 'fas fa-superscript'},
            {'name': _('Exponent Calculator'), 'url': 'exponent-calculator', 'category': _('Algebra & Equations'), 'description': _('Calculate exponential values and powers'), 'icon': 'fas fa-arrow-up-1-9'},
            {'name': _('Root Calculator'), 'url': 'root-calculator', 'category': _('Algebra & Equations'), 'description': _('Calculate square roots, cube roots, and nth roots'), 'icon': 'fas fa-square-root-variable'},
            {'name': _('Log Calculator'), 'url': 'log-calculator', 'category': _('Algebra & Equations'), 'description': _('Calculate logarithmic values'), 'icon': 'fas fa-chart-line'},
            {'name': _('Scientific Notation Calculator'), 'url': 'scientific-notation-calculator', 'category': _('Algebra & Equations'), 'description': _('Convert numbers to and from scientific notation'), 'icon': 'fas fa-e'},
            {'name': _('Matrix Calculator'), 'url': 'matrix-calculator', 'category': _('Algebra & Equations'), 'description': _('Perform matrix operations including addition, subtraction, and multiplication'), 'icon': 'fas fa-border-all'},
            
            # Number Theory
            {'name': _('Factor Calculator'), 'url': 'factor-calculator', 'category': _('Number Theory'), 'description': _('Find all factors of a number'), 'icon': 'fas fa-sitemap'},
            {'name': _('Prime Factorization Calculator'), 'url': 'prime-factorization-calculator', 'category': _('Number Theory'), 'description': _('Find prime factorization of numbers'), 'icon': 'fas fa-code-branch'},
            {'name': _('Greatest Common Factor Calculator'), 'url': 'greatest-common-factor-calculator', 'category': _('Number Theory'), 'description': _('Calculate GCF of multiple numbers'), 'icon': 'fas fa-maximize'},
            {'name': _('Least Common Multiple Calculator'), 'url': 'least-common-multiple-calculator', 'category': _('Number Theory'), 'description': _('Calculate LCM of multiple numbers'), 'icon': 'fas fa-minimize'},
            {'name': _('Common Factor Calculator'), 'url': 'common-factor-calculator', 'category': _('Number Theory'), 'description': _('Find common factors between numbers'), 'icon': 'fas fa-circle-nodes'},
            
            # Geometry
            {'name': _('Area Calculator'), 'url': 'area-calculator', 'category': _('Geometry'), 'description': _('Calculate area of various shapes'), 'icon': 'fas fa-vector-square'},
            {'name': _('Volume Calculator'), 'url': 'volume-calculator', 'category': _('Geometry'), 'description': _('Calculate volume of 3D shapes'), 'icon': 'fas fa-cube'},
            {'name': _('Surface Area Calculator'), 'url': 'surface-area-calculator', 'category': _('Geometry'), 'description': _('Calculate surface area of 3D objects'), 'icon': 'fas fa-cubes'},
            {'name': _('Pythagorean Theorem Calculator'), 'url': 'pythagorean-theorem-calculator', 'category': _('Geometry'), 'description': _('Use Pythagorean theorem to find triangle sides'), 'icon': 'fas fa-draw-polygon'},
            {'name': _('Circle Calculator'), 'url': 'circle-calculator', 'category': _('Geometry'), 'description': _('Calculate circle properties (area, circumference, radius)'), 'icon': 'far fa-circle'},
            {'name': _('Triangle Calculator'), 'url': 'triangle-calculator', 'category': _('Geometry'), 'description': _('Calculate triangle properties and area'), 'icon': 'fas fa-play'},
            {'name': _('Right Triangle Calculator'), 'url': 'right-triangle-calculator', 'category': _('Geometry'), 'description': _('Calculate right triangle properties'), 'icon': 'fas fa-ruler-combined'},
            {'name': _('Distance Calculator'), 'url': 'distance-calculator', 'category': _('Geometry'), 'description': _('Calculate distance between two points'), 'icon': 'fas fa-ruler-horizontal'},
            {'name': _('Slope Calculator'), 'url': 'slope-calculator', 'category': _('Geometry'), 'description': _('Calculate slope between two points'), 'icon': 'fas fa-arrow-trend-up'},
            
            # Statistics & Probability
            {'name': _('Average Calculator'), 'url': 'average-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate average, mean, median, and mode'), 'icon': 'fas fa-chart-bar'},
            {'name': _('Mean Median Mode Range Calculator'), 'url': 'mean-median-mode-range-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate all central tendency and range values'), 'icon': 'fas fa-chart-simple'},
            {'name': _('Standard Deviation Calculator'), 'url': 'standard-deviation-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate standard deviation and variance'), 'icon': 'fas fa-wave-square'},
            {'name': _('Probability Calculator'), 'url': 'probability-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate probability and odds'), 'icon': 'fas fa-dice'},
            {'name': _('Permutation and Combination Calculator'), 'url': 'permutation-and-combination-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate permutations and combinations'), 'icon': 'fas fa-shuffle'},
            {'name': _('Z Score Calculator'), 'url': 'z-score-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate z-scores for statistical analysis'), 'icon': 'fas fa-z'},
            {'name': _('P Value Calculator'), 'url': 'p-value-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate p-values for hypothesis testing'), 'icon': 'fas fa-p'},
            {'name': _('Confidence Interval Calculator'), 'url': 'confidence-interval-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate confidence intervals for data'), 'icon': 'fas fa-arrows-left-right'},
            {'name': _('Sample Size Calculator'), 'url': 'sample-size-calculator', 'category': _('Statistics & Probability'), 'description': _('Calculate required sample size for studies'), 'icon': 'fas fa-users'},
            {'name': _('Statistics Calculator'), 'url': 'statistics-calculator', 'category': _('Statistics & Probability'), 'description': _('Comprehensive statistical calculations'), 'icon': 'fas fa-chart-area'},
            
            # Sequences & Series
            {'name': _('Number Sequence Calculator'), 'url': 'number-sequence-calculator', 'category': _('Sequences & Series'), 'description': _('Generate and analyze number sequences'), 'icon': 'fas fa-list-ol'},
            
            # Number Systems
            {'name': _('Binary Calculator'), 'url': 'binary-calculator', 'category': _('Number Systems'), 'description': _('Convert and calculate binary numbers'), 'icon': 'fas fa-microchip'},
            {'name': _('Hex Calculator'), 'url': 'hex-calculator', 'category': _('Number Systems'), 'description': _('Convert and calculate hexadecimal numbers'), 'icon': 'fas fa-hashtag'},
            {'name': _('Fraction Calculator'), 'url': 'fraction-calculator', 'category': _('Number Systems'), 'description': _('Calculate and simplify fractions'), 'icon': 'fas fa-divide'},
            {'name': _('Big Number Calculator'), 'url': 'big-number-calculator', 'category': _('Number Systems'), 'description': _('Perform calculations with very large numbers'), 'icon': 'fas fa-infinity'},
            
            # Utilities
            {'name': _('Scientific Calculator'), 'url': 'scientific-calculator', 'category': _('Utilities'), 'description': _('Advanced scientific calculator with trigonometry'), 'icon': 'fas fa-calculator'},
            {'name': _('Random Number Generator'), 'url': 'random-number-generator', 'category': _('Utilities'), 'description': _('Generate random numbers with custom ranges'), 'icon': 'fas fa-dice-five'},
            {'name': _('Percent Error Calculator'), 'url': 'percent-error-calculator', 'category': _('Utilities'), 'description': _('Calculate percent error for measurements'), 'icon': 'fas fa-triangle-exclamation'},
            {'name': _('Half Life Calculator'), 'url': 'half-life-calculator', 'category': _('Utilities'), 'description': _('Calculate radioactive decay half-life'), 'icon': 'fas fa-radiation'},
        ]
        
        context['calculators'] = calculators
        context['total_calculators'] = len(calculators)
        
        # Get unique categories
        categories_set = set(calc['category'] for calc in calculators)
        context['categories'] = sorted(list(categories_set))
        
        return context
