from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
import json
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class NumberSequenceCalculator(View):
    """
    Enhanced Professional Number Sequence Calculator
    Identifies sequence patterns, generates next terms, and calculates nth terms.
    """
    template_name = 'math_calculators/number_sequence_calculator.html'
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': 'Number Sequence Calculator',
        }
        return render(request, self.template_name, context)
    
    def _validate_number(self, value):
        """Validate that a value is a valid number"""
        try:
            num = float(value)
            if math.isnan(num) or math.isinf(num):
                return None, 'Invalid number.'
            return num, None
        except (ValueError, TypeError):
            return None, 'Must be a valid number.'
    
    def _parse_numbers(self, numbers_str):
        """Parse numbers from string input"""
        try:
            numbers_str = numbers_str.strip()
            numbers_str = numbers_str.replace('[', '').replace(']', '')
            
            if ',' in numbers_str:
                numbers = [x.strip() for x in numbers_str.split(',')]
            elif '\n' in numbers_str:
                numbers = [x.strip() for x in numbers_str.split('\n')]
            else:
                numbers = numbers_str.split()
            
            validated_numbers = []
            for num_str in numbers:
                if not num_str:
                    continue
                num, error = self._validate_number(num_str)
                if error:
                    return None, f'Invalid number: {num_str}'
                validated_numbers.append(num)
            
            if len(validated_numbers) < 2:
                return None, 'Please provide at least 2 numbers.'
            
            return validated_numbers, None
        except Exception as e:
            return None, f'Error parsing numbers: {str(e)}'
    
    def _detect_arithmetic(self, numbers):
        """Detect arithmetic sequence"""
        if len(numbers) < 2:
            return None
        
        differences = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
        if len(set(differences)) == 1:
            return {
                'type': 'arithmetic',
                'common_difference': differences[0],
                'first_term': numbers[0],
                'formula': f'a_n = {numbers[0]} + (n-1) × {differences[0]}'
            }
        return None
    
    def _detect_geometric(self, numbers):
        """Detect geometric sequence"""
        if len(numbers) < 2:
            return None
        
        # Check for zero
        if 0 in numbers:
            return None
        
        ratios = [numbers[i+1] / numbers[i] for i in range(len(numbers)-1)]
        if len(set(ratios)) == 1:
            return {
                'type': 'geometric',
                'common_ratio': ratios[0],
                'first_term': numbers[0],
                'formula': f'a_n = {numbers[0]} × {ratios[0]}^(n-1)'
            }
        return None
    
    def _detect_fibonacci(self, numbers):
        """Detect Fibonacci-like sequence"""
        if len(numbers) < 3:
            return None
        
        # Check if each term is sum of previous two
        for i in range(2, len(numbers)):
            if abs(numbers[i] - (numbers[i-1] + numbers[i-2])) > 0.0001:
                return None
        
        return {
            'type': 'fibonacci',
            'first_term': numbers[0],
            'second_term': numbers[1],
            'formula': 'a_n = a_(n-1) + a_(n-2)'
        }
    
    def _detect_power(self, numbers):
        """Detect power sequence (n², n³, etc.)"""
        if len(numbers) < 3:
            return None
        
        # Try different powers
        for power in [2, 3, 4, 5]:
            matches = True
            for i, num in enumerate(numbers, 1):
                expected = i ** power
                if abs(num - expected) > 0.0001:
                    matches = False
                    break
            if matches:
                return {
                    'type': 'power',
                    'power': power,
                    'formula': f'a_n = n^{power}'
                }
        return None
    
    def _detect_square(self, numbers):
        """Detect square number sequence"""
        if len(numbers) < 2:
            return None
        
        matches = True
        for i, num in enumerate(numbers, 1):
            expected = i ** 2
            if abs(num - expected) > 0.0001:
                matches = False
                break
        
        if matches:
            return {
                'type': 'square',
                'formula': 'a_n = n²'
            }
        return None
    
    def _detect_pattern(self, numbers):
        """Detect sequence pattern"""
        patterns = []
        
        # Try different pattern detectors
        arithmetic = self._detect_arithmetic(numbers)
        if arithmetic:
            patterns.append(arithmetic)
        
        geometric = self._detect_geometric(numbers)
        if geometric:
            patterns.append(geometric)
        
        fibonacci = self._detect_fibonacci(numbers)
        if fibonacci:
            patterns.append(fibonacci)
        
        square = self._detect_square(numbers)
        if square:
            patterns.append(square)
        
        power = self._detect_power(numbers)
        if power:
            patterns.append(power)
        
        return patterns[0] if patterns else {'type': 'unknown', 'formula': 'Pattern not recognized'}
    
    def _generate_next_terms(self, numbers, pattern, count=5):
        """Generate next terms in sequence"""
        if pattern['type'] == 'unknown':
            return []
        
        next_terms = []
        current_numbers = numbers.copy()
        
        for _ in range(count):
            if pattern['type'] == 'arithmetic':
                next_term = current_numbers[-1] + pattern['common_difference']
            elif pattern['type'] == 'geometric':
                next_term = current_numbers[-1] * pattern['common_ratio']
            elif pattern['type'] == 'fibonacci':
                next_term = current_numbers[-1] + current_numbers[-2]
            elif pattern['type'] == 'square':
                n = len(current_numbers) + 1
                next_term = n ** 2
            elif pattern['type'] == 'power':
                n = len(current_numbers) + 1
                next_term = n ** pattern['power']
            else:
                break
            
            next_terms.append(next_term)
            current_numbers.append(next_term)
        
        return next_terms
    
    def _calculate_nth_term(self, pattern, n):
        """Calculate nth term of sequence"""
        if pattern['type'] == 'unknown':
            return None
        
        if pattern['type'] == 'arithmetic':
            return pattern['first_term'] + (n - 1) * pattern['common_difference']
        elif pattern['type'] == 'geometric':
            return pattern['first_term'] * (pattern['common_ratio'] ** (n - 1))
        elif pattern['type'] == 'square':
            return n ** 2
        elif pattern['type'] == 'power':
            return n ** pattern['power']
        else:
            return None
    
    def _prepare_step_by_step(self, numbers, pattern, next_terms):
        """Prepare step-by-step solution"""
        steps = []
        
        steps.append(f"Given sequence: {', '.join(map(str, numbers))}")
        steps.append("")
        
        steps.append("Step 1: Analyze the sequence")
        steps.append(f"  Number of terms: {len(numbers)}")
        steps.append(f"  Terms: {', '.join(map(str, numbers))}")
        steps.append("")
        
        if pattern['type'] == 'arithmetic':
            steps.append("Step 2: Identify pattern type")
            steps.append("  This is an arithmetic sequence (constant difference)")
            steps.append(f"  Common difference (d) = {pattern['common_difference']}")
            steps.append("")
            steps.append("Step 3: Formula")
            steps.append(f"  {pattern['formula']}")
            steps.append("")
            steps.append("Step 4: Verify")
            for i, num in enumerate(numbers, 1):
                calculated = pattern['first_term'] + (i - 1) * pattern['common_difference']
                steps.append(f"  Term {i}: {pattern['first_term']} + ({i}-1) × {pattern['common_difference']} = {calculated} ✓")
            steps.append("")
            if next_terms:
                steps.append("Step 5: Next terms")
                for i, term in enumerate(next_terms, len(numbers) + 1):
                    steps.append(f"  Term {i}: {term}")
        
        elif pattern['type'] == 'geometric':
            steps.append("Step 2: Identify pattern type")
            steps.append("  This is a geometric sequence (constant ratio)")
            steps.append(f"  Common ratio (r) = {pattern['common_ratio']}")
            steps.append("")
            steps.append("Step 3: Formula")
            steps.append(f"  {pattern['formula']}")
            steps.append("")
            steps.append("Step 4: Verify")
            for i, num in enumerate(numbers, 1):
                calculated = pattern['first_term'] * (pattern['common_ratio'] ** (i - 1))
                steps.append(f"  Term {i}: {pattern['first_term']} × {pattern['common_ratio']}^({i}-1) = {calculated} ✓")
            steps.append("")
            if next_terms:
                steps.append("Step 5: Next terms")
                for i, term in enumerate(next_terms, len(numbers) + 1):
                    steps.append(f"  Term {i}: {term}")
        
        elif pattern['type'] == 'fibonacci':
            steps.append("Step 2: Identify pattern type")
            steps.append("  This is a Fibonacci-like sequence")
            steps.append(f"  Each term is the sum of the previous two terms")
            steps.append(f"  First term: {pattern['first_term']}")
            steps.append(f"  Second term: {pattern['second_term']}")
            steps.append("")
            steps.append("Step 3: Formula")
            steps.append(f"  {pattern['formula']}")
            steps.append("")
            steps.append("Step 4: Verify")
            for i in range(2, len(numbers)):
                steps.append(f"  Term {i+1}: {numbers[i-1]} + {numbers[i-2]} = {numbers[i]} ✓")
            steps.append("")
            if next_terms:
                steps.append("Step 5: Next terms")
                for i, term in enumerate(next_terms, len(numbers) + 1):
                    steps.append(f"  Term {i}: {term}")
        
        elif pattern['type'] == 'square':
            steps.append("Step 2: Identify pattern type")
            steps.append("  This is a square number sequence")
            steps.append("  Each term is n² where n is the position")
            steps.append("")
            steps.append("Step 3: Formula")
            steps.append(f"  {pattern['formula']}")
            steps.append("")
            steps.append("Step 4: Verify")
            for i, num in enumerate(numbers, 1):
                calculated = i ** 2
                steps.append(f"  Term {i}: {i}² = {calculated} ✓")
            steps.append("")
            if next_terms:
                steps.append("Step 5: Next terms")
                for i, term in enumerate(next_terms, len(numbers) + 1):
                    steps.append(f"  Term {i}: {i}² = {term}")
        
        elif pattern['type'] == 'power':
            steps.append("Step 2: Identify pattern type")
            steps.append(f"  This is a power sequence (n^{pattern['power']})")
            steps.append(f"  Each term is n^{pattern['power']} where n is the position")
            steps.append("")
            steps.append("Step 3: Formula")
            steps.append(f"  {pattern['formula']}")
            steps.append("")
            steps.append("Step 4: Verify")
            for i, num in enumerate(numbers, 1):
                calculated = i ** pattern['power']
                steps.append(f"  Term {i}: {i}^{pattern['power']} = {calculated} ✓")
            steps.append("")
            if next_terms:
                steps.append("Step 5: Next terms")
                for i, term in enumerate(next_terms, len(numbers) + 1):
                    steps.append(f"  Term {i}: {i}^{pattern['power']} = {term}")
        
        else:
            steps.append("Step 2: Pattern identification")
            steps.append("  Pattern not recognized")
            steps.append("  Try providing more terms or check for typos")
        
        return steps
    
    def _prepare_chart_data(self, numbers, next_terms):
        """Prepare chart data for visualization"""
        chart_data = {}
        
        all_terms = numbers + next_terms
        positions = list(range(1, len(all_terms) + 1))
        
        chart_data['sequence_chart'] = {
            'type': 'line',
            'data': {
                'labels': [str(p) for p in positions],
                'datasets': [{
                    'label': 'Sequence Terms',
                    'data': all_terms,
                    'borderColor': '#3b82f6',
                    'backgroundColor': 'rgba(59, 130, 246, 0.1)',
                    'borderWidth': 2,
                    'fill': True,
                    'tension': 0.4,
                    'pointRadius': 5,
                    'pointHoverRadius': 7
                }]
            }
        }
        
        return chart_data
    
    def post(self, request):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            
            # Get numbers from input
            numbers_str = data.get('numbers', '')
            if not numbers_str:
                return JsonResponse({'success': False, 'error': 'Please provide at least two numbers.'}, status=400)
            
            numbers, error = self._parse_numbers(numbers_str)
            if error:
                return JsonResponse({'success': False, 'error': error}, status=400)
            
            # Detect pattern
            pattern = self._detect_pattern(numbers)
            
            # Generate next terms
            next_count = int(data.get('next_count', 5))
            if next_count < 0 or next_count > 20:
                next_count = 5
            next_terms = self._generate_next_terms(numbers, pattern, next_count)
            
            # Calculate nth term if requested
            nth_term = None
            nth_position = data.get('nth_position')
            if nth_position:
                try:
                    n = int(nth_position)
                    if n > 0:
                        nth_term = self._calculate_nth_term(pattern, n)
                except:
                    pass
            
            # Prepare step-by-step solution
            step_by_step = self._prepare_step_by_step(numbers, pattern, next_terms)
            
            # Prepare chart data
            chart_data = {}
            try:
                chart_data = self._prepare_chart_data(numbers, next_terms)
            except Exception as e:
                import traceback
                print(f"Chart data preparation error: {traceback.format_exc()}")
                chart_data = {}
            
            response = {
                'success': True,
                'numbers': numbers,
                'pattern': pattern,
                'next_terms': next_terms,
                'nth_term': nth_term,
                'nth_position': int(nth_position) if nth_position and nth_term else None,
                'step_by_step': step_by_step,
                'chart_data': chart_data
            }
            
            return JsonResponse(response)
            
        except (ValueError, TypeError) as e:
            return JsonResponse({'success': False, 'error': f'Invalid input: {str(e)}'}, status=400)
        except Exception as e:
            import traceback
            print(f"Number Sequence Calculator Error: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': f'An error occurred: {str(e)}'}, status=500)
