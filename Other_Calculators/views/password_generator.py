from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import secrets
import string
import math


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PasswordGenerator(View):
    """
    Professional Password Generator with Comprehensive Features
    
    This generator provides password generation with:
    - Generate secure random passwords
    - Customizable length and character sets
    - Password strength analysis
    - Multiple password generation
    - Exclude ambiguous characters
    
    Features:
    - Supports multiple generation modes
    - Provides password strength metrics
    - Secure random generation using secrets module
    """
    template_name = 'other_calculators/password_generator.html'
    
    # Character sets
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Ambiguous characters to exclude
    AMBIGUOUS = "0OIl1"
    
    def get(self, request):
        """Handle GET request"""
        context = {
            'calculator_name': _('Password Generator'),
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle POST request for password generation"""
        try:
            data = json.loads(request.body)
            action = data.get('action', 'generate')
            
            if action == 'generate':
                return self._generate_passwords(data)
            elif action == 'analyze':
                return self._analyze_password(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid action.')
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': _('Invalid JSON data.')
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('An error occurred: {error}').format(error=str(e))
            }, status=500)
    
    def _generate_passwords(self, data):
        """Generate passwords based on criteria"""
        try:
            length = data.get('length', 12)
            count = data.get('count', 1)
            include_uppercase = data.get('include_uppercase', True)
            include_lowercase = data.get('include_lowercase', True)
            include_numbers = data.get('include_numbers', True)
            include_special = data.get('include_special', False)
            exclude_ambiguous = data.get('exclude_ambiguous', False)
            
            try:
                length = int(length)
                count = int(count)
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': _('Length and count must be integers.')
                }, status=400)
            
            # Validate ranges
            if length < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('Password length must be at least 1.')
                }, status=400)
            
            if length > 128:
                return JsonResponse({
                    'success': False,
                    'error': _('Password length cannot exceed 128 characters.')
                }, status=400)
            
            if count < 1:
                return JsonResponse({
                    'success': False,
                    'error': _('Count must be at least 1.')
                }, status=400)
            
            if count > 50:
                return JsonResponse({
                    'success': False,
                    'error': _('Count cannot exceed 50.')
                }, status=400)
            
            # Build character set
            char_set = ""
            if include_lowercase:
                char_set += self.LOWERCASE
            if include_uppercase:
                char_set += self.UPPERCASE
            if include_numbers:
                char_set += self.DIGITS
            if include_special:
                char_set += self.SPECIAL
            
            # Remove ambiguous characters if requested
            if exclude_ambiguous:
                for char in self.AMBIGUOUS:
                    char_set = char_set.replace(char, '')
            
            # Validate character set
            if not char_set:
                return JsonResponse({
                    'success': False,
                    'error': _('At least one character type must be selected.')
                }, status=400)
            
            # Ensure at least one character from each selected type
            required_chars = []
            if include_lowercase:
                required_chars.append(self.LOWERCASE)
            if include_uppercase:
                required_chars.append(self.UPPERCASE)
            if include_numbers:
                required_chars.append(self.DIGITS)
            if include_special:
                required_chars.append(self.SPECIAL)
            
            # Remove ambiguous from required chars if needed
            if exclude_ambiguous:
                required_chars = [''.join(c for c in chars if c not in self.AMBIGUOUS) for chars in required_chars]
                required_chars = [chars for chars in required_chars if chars]  # Remove empty
            
            # Generate passwords
            passwords = []
            for _ in range(count):
                password = self._generate_single_password(char_set, length, required_chars, exclude_ambiguous)
                passwords.append(password)
            
            # Analyze first password
            analysis = self._analyze_password_strength(passwords[0])
            
            return JsonResponse({
                'success': True,
                'action': 'generate',
                'passwords': passwords,
                'count': count,
                'length': length,
                'analysis': analysis,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error generating passwords: {error}').format(error=str(e))
            }, status=500)
    
    def _generate_single_password(self, char_set, length, required_chars, exclude_ambiguous):
        """Generate a single password ensuring all required character types are included"""
        # Ensure at least one character from each required type
        password_chars = []
        
        # Add one character from each required type
        for required_set in required_chars:
            if required_set:
                # Remove ambiguous if needed
                if exclude_ambiguous:
                    filtered_set = ''.join(c for c in required_set if c not in self.AMBIGUOUS)
                    if filtered_set:
                        password_chars.append(secrets.choice(filtered_set))
                else:
                    password_chars.append(secrets.choice(required_set))
        
        # Fill the rest with random characters from the full set
        remaining_length = length - len(password_chars)
        for _ in range(remaining_length):
            password_chars.append(secrets.choice(char_set))
        
        # Shuffle to randomize positions
        secrets.SystemRandom().shuffle(password_chars)
        
        return ''.join(password_chars)
    
    def _analyze_password(self, data):
        """Analyze password strength"""
        try:
            password = data.get('password', '')
            
            if not password:
                return JsonResponse({
                    'success': False,
                    'error': _('Password is required.')
                }, status=400)
            
            analysis = self._analyze_password_strength(password)
            
            return JsonResponse({
                'success': True,
                'action': 'analyze',
                'password': password,
                'analysis': analysis,
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error analyzing password: {error}').format(error=str(e))
            }, status=500)
    
    def _analyze_password_strength(self, password):
        """Analyze password strength and return metrics"""
        length = len(password)
        
        # Check character types
        has_lowercase = any(c.islower() for c in password)
        has_uppercase = any(c.isupper() for c in password)
        has_numbers = any(c.isdigit() for c in password)
        has_special = any(c in self.SPECIAL for c in password)
        
        # Count unique characters
        unique_chars = len(set(password))
        
        # Calculate entropy (bits)
        char_set_size = 0
        if has_lowercase:
            char_set_size += 26
        if has_uppercase:
            char_set_size += 26
        if has_numbers:
            char_set_size += 10
        if has_special:
            char_set_size += len(self.SPECIAL)
        
        if char_set_size > 0:
            entropy = length * math.log2(char_set_size)
        else:
            entropy = 0
        
        # Determine strength level
        if entropy < 28:
            strength = 'weak'
            strength_score = 1
        elif entropy < 40:
            strength = 'fair'
            strength_score = 2
        elif entropy < 60:
            strength = 'good'
            strength_score = 3
        elif entropy < 80:
            strength = 'strong'
            strength_score = 4
        else:
            strength = 'very_strong'
            strength_score = 5
        
        # Calculate time to crack (rough estimate)
        # Assuming 1 billion guesses per second
        guesses_per_second = 1_000_000_000
        possible_combinations = char_set_size ** length if char_set_size > 0 else 1
        seconds_to_crack = possible_combinations / (2 * guesses_per_second)  # Average case
        
        # Convert to human-readable time
        if seconds_to_crack < 1:
            time_to_crack = _('Less than a second')
        elif seconds_to_crack < 60:
            time_to_crack = _('{seconds} seconds').format(seconds=int(seconds_to_crack))
        elif seconds_to_crack < 3600:
            time_to_crack = _('{minutes} minutes').format(minutes=int(seconds_to_crack / 60))
        elif seconds_to_crack < 86400:
            time_to_crack = _('{hours} hours').format(hours=int(seconds_to_crack / 3600))
        elif seconds_to_crack < 31536000:
            time_to_crack = _('{days} days').format(days=int(seconds_to_crack / 86400))
        elif seconds_to_crack < 31536000000:
            time_to_crack = _('{years} years').format(years=int(seconds_to_crack / 31536000))
        else:
            time_to_crack = _('Millions of years')
        
        # Generate feedback
        feedback = []
        if length < 8:
            feedback.append(_('Password is too short. Use at least 8 characters.'))
        elif length < 12:
            feedback.append(_('Consider using a longer password (12+ characters).'))
        
        if not has_lowercase:
            feedback.append(_('Add lowercase letters for better security.'))
        if not has_uppercase:
            feedback.append(_('Add uppercase letters for better security.'))
        if not has_numbers:
            feedback.append(_('Add numbers for better security.'))
        if not has_special:
            feedback.append(_('Add special characters for better security.'))
        
        if unique_chars < length * 0.5:
            feedback.append(_('Password has many repeated characters. Consider using more variety.'))
        
        if not feedback:
            feedback.append(_('Password meets good security practices.'))
        
        return {
            'length': length,
            'has_lowercase': has_lowercase,
            'has_uppercase': has_uppercase,
            'has_numbers': has_numbers,
            'has_special': has_special,
            'unique_chars': unique_chars,
            'entropy': round(entropy, 2),
            'strength': strength,
            'strength_score': strength_score,
            'char_set_size': char_set_size,
            'time_to_crack': time_to_crack,
            'feedback': feedback,
        }
