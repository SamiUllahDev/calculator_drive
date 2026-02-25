from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from datetime import date
import json
import math
import random
import string
import numpy as np
from sympy import symbols, Eq, simplify, latex


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoveCalculator(View):
    """
    Professional Love Calculator with Comprehensive Emotional Features

    Features:
    - Love percentage calculation (Classic & Balanced algorithms)
    - Compatibility score with multi-factor analysis
    - Name analysis with detailed breakdown
    - 🔥 FLAMES game — classic relationship prediction
    - ♈ Zodiac compatibility — name-based zodiac matching
    - 📏 Distance & closeness meter — visual boy-girl animation
    - 💬 Love language detection — per-person love language
    - 💡 Relationship advice — personalized tips
    - 🌹 Romantic tips by score category
    - Step-by-step solutions & chart visualizations
    """
    template_name = 'other_calculators/love_calculator.html'

    # Love percentage categories
    LOVE_CATEGORIES = {
        'excellent': (90, 100, _('Excellent Match!')),
        'very_good': (75, 89, _('Very Good Match!')),
        'good': (60, 74, _('Good Match!')),
        'fair': (40, 59, _('Fair Match')),
        'poor': (0, 39, _('Needs Work')),
    }

    # Category → simple color key (used for UI, similar idea to BMI colors)
    CATEGORY_COLORS = {
        'excellent': 'pink',
        'very_good': 'rose',
        'good': 'orange',
        'fair': 'yellow',
        'poor': 'gray',
    }

    # Romantic tips by category
    ROMANTIC_TIPS = {
        'excellent': _('A rare connection! Keep nurturing trust and communication.'),
        'very_good': _('Strong compatibility—great foundation for something special.'),
        'good': _('Solid potential. Small gestures and quality time can deepen the bond.'),
        'fair': _('Every relationship takes effort. Patience and understanding go a long way.'),
        'poor': _('Names are just fun—real love is built on respect and shared values.'),
    }

    # Zodiac signs list
    ZODIAC_SIGNS = [
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
    ]

    # Zodiac sign display info (emoji + name)
    ZODIAC_DISPLAY = {
        'aries': ('♈', _('Aries')),
        'taurus': ('♉', _('Taurus')),
        'gemini': ('♊', _('Gemini')),
        'cancer': ('♋', _('Cancer')),
        'leo': ('♌', _('Leo')),
        'virgo': ('♍', _('Virgo')),
        'libra': ('♎', _('Libra')),
        'scorpio': ('♏', _('Scorpio')),
        'sagittarius': ('♐', _('Sagittarius')),
        'capricorn': ('♑', _('Capricorn')),
        'aquarius': ('♒', _('Aquarius')),
        'pisces': ('♓', _('Pisces')),
    }

    # Zodiac compatibility table
    ZODIAC_COMPATIBILITY = {
        ('aries', 'leo'): 95, ('aries', 'sagittarius'): 93, ('aries', 'gemini'): 83,
        ('taurus', 'virgo'): 95, ('taurus', 'capricorn'): 93, ('taurus', 'cancer'): 85,
        ('gemini', 'libra'): 93, ('gemini', 'aquarius'): 92, ('gemini', 'aries'): 83,
        ('cancer', 'scorpio'): 94, ('cancer', 'pisces'): 95, ('cancer', 'taurus'): 85,
        ('leo', 'aries'): 95, ('leo', 'sagittarius'): 93, ('leo', 'gemini'): 80,
        ('virgo', 'taurus'): 95, ('virgo', 'capricorn'): 92, ('virgo', 'cancer'): 80,
        ('libra', 'gemini'): 93, ('libra', 'aquarius'): 90, ('libra', 'leo'): 78,
        ('scorpio', 'cancer'): 94, ('scorpio', 'pisces'): 92, ('scorpio', 'virgo'): 78,
        ('sagittarius', 'aries'): 93, ('sagittarius', 'leo'): 93, ('sagittarius', 'aquarius'): 82,
        ('capricorn', 'taurus'): 93, ('capricorn', 'virgo'): 92, ('capricorn', 'pisces'): 78,
        ('aquarius', 'gemini'): 92, ('aquarius', 'libra'): 90, ('aquarius', 'sagittarius'): 82,
        ('pisces', 'cancer'): 95, ('pisces', 'scorpio'): 92, ('pisces', 'capricorn'): 78,
    }

    # Love languages
    LOVE_LANGUAGES = [
        _('Words of Affirmation'),
        _('Acts of Service'),
        _('Receiving Gifts'),
        _('Quality Time'),
        _('Physical Touch'),
    ]

    # Relationship advice by category
    RELATIONSHIP_ADVICE = {
        'excellent': [
            _('You two are a power couple! Keep supporting each other\'s dreams.'),
            _('Your bond is rare and special. Never stop dating each other.'),
            _('Communication flows naturally between you. Keep it open and honest.'),
        ],
        'very_good': [
            _('Great chemistry! Focus on shared hobbies to deepen your connection.'),
            _('You complement each other well. Celebrate your differences.'),
            _('Your compatibility is strong. Build traditions together.'),
        ],
        'good': [
            _('There\'s real potential here! Spend quality time getting to know each other.'),
            _('You have a solid foundation. Work on understanding each other\'s love language.'),
            _('Good matches grow into great ones with patience and effort.'),
        ],
        'fair': [
            _('Every great love story has its challenges. Embrace them together.'),
            _('Focus on building trust and understanding. Small steps lead to big things.'),
            _('Opposites can attract! Find common ground and build from there.'),
        ],
        'poor': [
            _('Don\'t let a number define your love. The best relationships are unexpected.'),
            _('Real compatibility comes from shared values, not just names.'),
            _('Love is a choice you make every day. Names are just the beginning.'),
        ],
    }

    # Personality options (for optional user inputs)
    PERSONALITY_ENERGY_LEVELS = ['introvert', 'ambivert', 'extrovert']
    PERSONALITY_STYLES = ['romantic', 'playful', 'practical']
    FAVORITE_COLORS = ['red', 'pink', 'purple', 'blue', 'green', 'gold']

    # ---------- Helper methods ----------

    def _get_romantic_tip(self, category_key):
        """Return a short romantic tip for the given category."""
        return self.ROMANTIC_TIPS.get(category_key, self.ROMANTIC_TIPS['poor'])

    def _get_relationship_advice(self, category_key):
        """Return random relationship advice for the given category."""
        advices = self.RELATIONSHIP_ADVICE.get(category_key, self.RELATIONSHIP_ADVICE['poor'])
        return random.choice(advices) if advices else ''

    def _calculate_distance_meter(self, name1, name2):
        """Calculate emotional closeness between two names (1-10 scale)."""
        n1 = name1.lower().replace(' ', '')
        n2 = name2.lower().replace(' ', '')
        common = len(set(n1) & set(n2))
        total_unique = len(set(n1) | set(n2))
        if total_unique == 0:
            return 5
        ratio = common / total_unique
        closeness = max(1, min(10, round(ratio * 10)))
        return closeness

    def _get_love_language(self, name):
        """Determine love language based on name characteristics."""
        n = name.lower().replace(' ', '')
        name_sum = sum(ord(c) - 96 for c in n if c.isalpha())
        idx = name_sum % 5
        return str(self.LOVE_LANGUAGES[idx])

    def _get_zodiac_from_name(self, name):
        """Derive a zodiac sign from name (fun/entertainment)."""
        n = name.lower().replace(' ', '')
        name_sum = sum(ord(c) - 96 for c in n if c.isalpha())
        idx = name_sum % 12
        return self.ZODIAC_SIGNS[idx]

    def _parse_birthdate(self, dob_str):
        """Parse birthdate string (YYYY-MM-DD). Return date or None if invalid."""
        if not dob_str:
            return None
        try:
            parts = [int(p) for p in dob_str.split('-')]
            if len(parts) != 3:
                return None
            year, month, day = parts
            return date(year, month, day)
        except Exception:
            return None

    def _calculate_age(self, birthdate, today=None):
        """Calculate age in years from a birthdate."""
        if not birthdate:
            return None
        if today is None:
            today = date.today()
        years = today.year - birthdate.year
        if (today.month, today.day) < (birthdate.month, birthdate.day):
            years -= 1
        return max(years, 0)

    def _get_zodiac_from_date(self, birthdate):
        """Real zodiac sign from birthdate (Western astrology)."""
        if not birthdate:
            return None
        m, d = birthdate.month, birthdate.day
        # (month, day, sign)
        zodiac_ranges = [
            ((3, 21), (4, 19), 'aries'),
            ((4, 20), (5, 20), 'taurus'),
            ((5, 21), (6, 20), 'gemini'),
            ((6, 21), (7, 22), 'cancer'),
            ((7, 23), (8, 22), 'leo'),
            ((8, 23), (9, 22), 'virgo'),
            ((9, 23), (10, 22), 'libra'),
            ((10, 23), (11, 21), 'scorpio'),
            ((11, 22), (12, 21), 'sagittarius'),
            ((12, 22), (1, 19), 'capricorn'),
            ((1, 20), (2, 18), 'aquarius'),
            ((2, 19), (3, 20), 'pisces'),
        ]

        for (start_m, start_d), (end_m, end_d), sign in zodiac_ranges:
            if (m, d) >= (start_m, start_d) and (m, d) <= (end_m, end_d):
                return sign
            # Capricorn wrap-around (Dec 22–Jan 19)
            if start_m == 12 and ((m, d) >= (12, 22) or (m, d) <= (1, 19)):
                return 'capricorn'
        return None

    def _get_zodiac_display(self, sign):
        """Get display emoji and name for a zodiac sign."""
        info = self.ZODIAC_DISPLAY.get(sign, ('⭐', sign.capitalize()))
        return {'emoji': info[0], 'name': str(info[1])}

    def _get_zodiac_compatibility(self, sign1, sign2):
        """Get zodiac compatibility score."""
        if sign1 == sign2:
            return 75
        pair = (sign1, sign2)
        reverse_pair = (sign2, sign1)
        if pair in self.ZODIAC_COMPATIBILITY:
            return self.ZODIAC_COMPATIBILITY[pair]
        if reverse_pair in self.ZODIAC_COMPATIBILITY:
            return self.ZODIAC_COMPATIBILITY[reverse_pair]
        return 60

    def _calculate_flame(self, name1, name2):
        """Classic FLAMES game calculation."""
        n1 = list(name1.lower().replace(' ', ''))
        n2 = list(name2.lower().replace(' ', ''))
        for c in n1[:]:
            if c in n2:
                n2.remove(c)
                n1.remove(c)
        remaining = len(n1) + len(n2)
        if remaining == 0:
            remaining = 1
        flames = ['Friends', 'Love', 'Affection', 'Marriage', 'Enemy', 'Siblings']
        idx = (remaining % 6) - 1
        if idx < 0:
            idx = 5
        return flames[idx]

    def _get_flame_emoji(self, flame):
        """Return emoji for FLAMES result."""
        mapping = {
            'Friends': '🤝',
            'Love': '❤️',
            'Affection': '💕',
            'Marriage': '💒',
            'Enemy': '⚔️',
            'Siblings': '👫',
        }
        return mapping.get(flame, '🔥')

    def _build_emotional_features(self, name1, name2, category_key, dob1=None, dob2=None):
        """Build all emotional feature data for responses."""
        distance = self._calculate_distance_meter(name1, name2)
        lang1 = self._get_love_language(name1)
        lang2 = self._get_love_language(name2)
        # Fun name-based zodiac (always available)
        zodiac1 = self._get_zodiac_from_name(name1)
        zodiac2 = self._get_zodiac_from_name(name2)
        zodiac1_display = self._get_zodiac_display(zodiac1)
        zodiac2_display = self._get_zodiac_display(zodiac2)
        zodiac_compat = self._get_zodiac_compatibility(zodiac1, zodiac2)
        flame_result = self._calculate_flame(name1, name2)
        flame_emoji = self._get_flame_emoji(flame_result)
        advice = self._get_relationship_advice(category_key)

        # Optional real DOB-based zodiac and ages
        birthdate1 = self._parse_birthdate(dob1) if dob1 else None
        birthdate2 = self._parse_birthdate(dob2) if dob2 else None
        age1 = self._calculate_age(birthdate1) if birthdate1 else None
        age2 = self._calculate_age(birthdate2) if birthdate2 else None
        age_gap = None
        if age1 is not None and age2 is not None:
            age_gap = abs(age1 - age2)

        real_zodiac1 = self._get_zodiac_from_date(birthdate1) if birthdate1 else None
        real_zodiac2 = self._get_zodiac_from_date(birthdate2) if birthdate2 else None
        real_zodiac1_display = self._get_zodiac_display(real_zodiac1) if real_zodiac1 else None
        real_zodiac2_display = self._get_zodiac_display(real_zodiac2) if real_zodiac2 else None
        real_zodiac_compat = None
        if real_zodiac1 and real_zodiac2:
            real_zodiac_compat = self._get_zodiac_compatibility(real_zodiac1, real_zodiac2)

        return {
            'distance_meter': distance,
            'love_language_1': lang1,
            'love_language_2': lang2,
            'zodiac_1': zodiac1,
            'zodiac_1_display': zodiac1_display,
            'zodiac_2': zodiac2,
            'zodiac_2_display': zodiac2_display,
            'zodiac_compatibility': zodiac_compat,
            'flame_result': flame_result,
            'flame_emoji': flame_emoji,
            'relationship_advice': advice,
            'age_1': age1,
            'age_2': age2,
            'age_gap': age_gap,
            'real_zodiac_1': real_zodiac1,
            'real_zodiac_1_display': real_zodiac1_display,
            'real_zodiac_2': real_zodiac2,
            'real_zodiac_2_display': real_zodiac2_display,
            'real_zodiac_compatibility': real_zodiac_compat,
        }

    def _format_unit(self, unit):
        """Format unit name for display"""
        return unit

    # ---------- Personality & "couple color" helpers ----------

    def _calculate_personality_match(self, energy1, energy2, style1, style2, color1, color2):
        """
        Calculate a simple personality/likes match score (0-100).
        All inputs are optional strings; unknown/missing values reduce weight.
        """
        score = 0.0
        weight_total = 0.0

        # Energy match (introvert / ambivert / extrovert)
        if energy1 in self.PERSONALITY_ENERGY_LEVELS and energy2 in self.PERSONALITY_ENERGY_LEVELS:
            weight_total += 40.0
            if energy1 == energy2:
                score += 40.0
            else:
                # Adjacent energies get medium score
                idx1 = self.PERSONALITY_ENERGY_LEVELS.index(energy1)
                idx2 = self.PERSONALITY_ENERGY_LEVELS.index(energy2)
                if abs(idx1 - idx2) == 1:
                    score += 28.0
                else:
                    score += 16.0

        # Style match (romantic / playful / practical)
        if style1 in self.PERSONALITY_STYLES and style2 in self.PERSONALITY_STYLES:
            weight_total += 40.0
            if style1 == style2:
                score += 40.0
            else:
                # Different styles still get some credit
                score += 24.0

        # Favorite color "vibe" match
        if color1 in self.FAVORITE_COLORS and color2 in self.FAVORITE_COLORS:
            weight_total += 20.0
            if color1 == color2:
                score += 20.0
            else:
                # Warm vs cool color grouping
                warm = {'red', 'pink', 'gold'}
                cool = {'blue', 'green', 'purple'}
                if (color1 in warm and color2 in warm) or (color1 in cool and color2 in cool):
                    score += 14.0
                else:
                    score += 8.0

        if weight_total == 0:
            return None

        normalized = max(0.0, min(100.0, (score / weight_total) * 100.0))
        return int(round(normalized))

    def _get_couple_color(self, color1, color2):
        """
        Derive a simple "couple color" key from two favorite colors.
        Used for a fun combined vibe; falls back gracefully.
        """
        if color1 in self.FAVORITE_COLORS and color2 in self.FAVORITE_COLORS:
            if color1 == color2:
                return color1

            pair = {color1, color2}
            # Simple palette mapping
            if 'red' in pair and 'pink' in pair:
                return 'red'
            if 'pink' in pair and 'purple' in pair:
                return 'purple'
            if 'blue' in pair and 'green' in pair:
                return 'green'
            if 'red' in pair and 'gold' in pair:
                return 'gold'
            if 'purple' in pair and 'blue' in pair:
                return 'purple'
            if 'green' in pair and 'gold' in pair:
                return 'green'

            # Default mixed vibe
            return 'purple'

        # If only one color is valid, use it
        if color1 in self.FAVORITE_COLORS:
            return color1
        if color2 in self.FAVORITE_COLORS:
            return color2
        return None

    def _get_couple_color_info(self, couple_color_key):
        """Map couple color key to display name and tailwind classes."""
        if not couple_color_key:
            return None
        mapping = {
            'red': {
                'name': _('Passionate Red'),
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300',
            },
            'pink': {
                'name': _('Romantic Pink'),
                'tailwind_classes': 'bg-pink-100 text-pink-800 border-pink-300',
            },
            'purple': {
                'name': _('Dreamy Purple'),
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300',
            },
            'blue': {
                'name': _('Calm Blue'),
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300',
            },
            'green': {
                'name': _('Balanced Green'),
                'tailwind_classes': 'bg-green-100 text-green-800 border-green-300',
            },
            'gold': {
                'name': _('Golden Glow'),
                'tailwind_classes': 'bg-amber-100 text-amber-800 border-amber-300',
            },
        }
        return mapping.get(couple_color_key)

    # ---------- Views ----------

    def get(self, request, name1=None, name2=None):
        """Handle GET request — supports shared URLs with pre-filled names"""
        import urllib.parse

        context = {
            'calculator_name': _('Love Calculator'),
            'share_name1': '',
            'share_name2': '',
            'share_percentage': 0,
            'share_message': '',
            'share_flame': '',
            'share_zodiac_compat': 0,
            'is_shared_link': False,
        }

        # If names are in URL (shared link), pre-calculate for OG tags
        if name1 and name2:
            n1 = urllib.parse.unquote(name1).strip()[:100]
            n2 = urllib.parse.unquote(name2).strip()[:100]

            if n1 and n2:
                context['is_shared_link'] = True
                context['share_name1'] = n1
                context['share_name2'] = n2

                # Pre-calculate love percentage for OG meta tags
                try:
                    combined = (n1 + n2).lower().replace(' ', '')
                    if len(combined) > 0:
                        l_count = combined.count('l')
                        o_count = combined.count('o')
                        v_count = combined.count('v')
                        e_count = combined.count('e')
                        love_score = l_count + o_count + v_count + e_count
                        total_letters = len(combined)
                        letter_percentage = float(np.multiply(
                            np.divide(love_score, total_letters), 100.0
                        )) if total_letters > 0 else 0

                        n1_lower = n1.lower().replace(' ', '')
                        n2_lower = n2.lower().replace(' ', '')
                        common_letters = 0
                        for char in set(n1_lower):
                            if char.isalpha():
                                common_letters += min(n1_lower.count(char), n2_lower.count(char))
                        total_unique = len(set(n1_lower + n2_lower))
                        common_percentage = float(np.multiply(
                            np.divide(common_letters, total_unique) if total_unique > 0 else 0,
                            100.0
                        ))
                        final_percentage = float(np.add(
                            np.multiply(letter_percentage, 0.4),
                            np.multiply(common_percentage, 0.6)
                        ))
                        length_factor = float(np.multiply(
                            np.divide(min(len(n1_lower), len(n2_lower)),
                                      max(len(n1_lower), len(n2_lower))),
                            10.0
                        )) if max(len(n1_lower), len(n2_lower)) > 0 else 0
                        final_percentage = max(0, min(100, float(np.add(final_percentage, length_factor))))
                        love_percentage = int(round(final_percentage))

                        category = self._get_love_category(love_percentage)
                        flame_result = self._calculate_flame(n1, n2)
                        zodiac1 = self._get_zodiac_from_name(n1)
                        zodiac2 = self._get_zodiac_from_name(n2)
                        zodiac_compat = self._get_zodiac_compatibility(zodiac1, zodiac2)

                        context['share_percentage'] = love_percentage
                        context['share_message'] = str(category['message'])
                        context['share_flame'] = flame_result
                        context['share_zodiac_compat'] = zodiac_compat
                except Exception:
                    pass

        return render(request, self.template_name, context)

    def post(self, request, name1=None, name2=None):
        """Handle POST request for calculations"""
        try:
            data = json.loads(request.body)
            calc_type = data.get('calc_type', 'love_percentage')

            if calc_type == 'love_percentage':
                return self._calculate_love_percentage(data)
            elif calc_type == 'compatibility':
                return self._calculate_compatibility(data)
            elif calc_type == 'name_analysis':
                return self._analyze_names(data)
            else:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid calculation type.')
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

    # ---------- Calculations ----------

    def _calculate_love_percentage(self, data):
        """Calculate love percentage from two names"""
        try:
            if 'name1' not in data or not data.get('name1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First name is required.')
                }, status=400)

            if 'name2' not in data or not data.get('name2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second name is required.')
                }, status=400)

            name1 = data.get('name1', '').strip()
            name2 = data.get('name2', '').strip()
            dob1 = data.get('dob1')
            dob2 = data.get('dob2')
            energy1 = data.get('energy1')
            energy2 = data.get('energy2')
            style1 = data.get('style1')
            style2 = data.get('style2')
            color1 = data.get('color1')
            color2 = data.get('color2')

            if not name1 or not name2:
                return JsonResponse({
                    'success': False,
                    'error': _('Both names are required.')
                }, status=400)

            if len(name1) > 100 or len(name2) > 100:
                return JsonResponse({
                    'success': False,
                    'error': _('Names must be 100 characters or less.')
                }, status=400)

            # Combine names and count letters
            combined = (name1 + name2).lower().replace(' ', '')

            if len(combined) == 0:
                return JsonResponse({
                    'success': False,
                    'error': _('Names must contain at least one letter.')
                }, status=400)

            # Count occurrences of L, O, V, E
            l_count = combined.count('l')
            o_count = combined.count('o')
            v_count = combined.count('v')
            e_count = combined.count('e')

            # Calculate percentage using the "LOVE" algorithm
            love_score = l_count + o_count + v_count + e_count

            total_letters = len(combined)
            letter_percentage = float(np.multiply(
                np.divide(love_score, total_letters),
                100.0
            )) if total_letters > 0 else 0

            name1_lower = name1.lower().replace(' ', '')
            name2_lower = name2.lower().replace(' ', '')

            # Count common letters
            common_letters = 0
            for char in set(name1_lower):
                if char.isalpha():
                    common_letters += min(name1_lower.count(char), name2_lower.count(char))

            # Calculate percentage based on common letters
            total_unique = len(set(name1_lower + name2_lower))
            common_percentage = float(np.multiply(
                np.divide(common_letters, total_unique) if total_unique > 0 else 0,
                100.0
            ))

            # Legacy LOVE-based percentage (kept for transparency in steps)
            algorithm = data.get('algorithm', 'classic')
            if algorithm == 'balanced':
                legacy_base = float(np.add(
                    np.multiply(letter_percentage, 0.5),
                    np.multiply(common_percentage, 0.5)
                ))
            else:
                legacy_base = float(np.add(
                    np.multiply(letter_percentage, 0.4),
                    np.multiply(common_percentage, 0.6)
                ))

            length_factor = float(np.multiply(
                np.divide(min(len(name1_lower), len(name2_lower)), max(len(name1_lower), len(name2_lower))),
                10.0
            )) if max(len(name1_lower), len(name2_lower)) > 0 else 0

            legacy_final = float(np.add(legacy_base, length_factor))
            legacy_final = max(0, min(100, legacy_final))

            # Advanced NumPy-based similarity components
            advanced_components = self._advanced_love_components(name1, name2)
            advanced_score = advanced_components['advanced_score']

            # Blend legacy and advanced scores so we preserve classic feel
            blended_final = float((legacy_final + advanced_score) / 2.0)
            blended_final = max(0.0, min(100.0, blended_final))
            love_percentage = int(round(blended_final))

            # Get category
            category = self._get_love_category(love_percentage)
            color_info = self._get_color_info(category['name'])

            # Build emotional features
            emotional = self._build_emotional_features(name1, name2, category['name'], dob1=dob1, dob2=dob2)

            # Personality / likes match & couple color
            personality_match = self._calculate_personality_match(energy1, energy2, style1, style2, color1, color2)
            couple_color_key = self._get_couple_color(color1, color2)
            couple_color_info = self._get_couple_color_info(couple_color_key)

            steps = self._prepare_love_percentage_steps(
                name1,
                name2,
                combined,
                l_count,
                o_count,
                v_count,
                e_count,
                love_score,
                letter_percentage,
                common_letters,
                common_percentage,
                legacy_final,
                love_percentage,
                advanced_components=advanced_components,
            )
            chart_data = self._prepare_love_percentage_chart_data(love_percentage, category)
            romantic_tip = self._get_romantic_tip(category['name'])

            share_text = f'💕 {name1} & {name2}: {love_percentage}% Love! {category["message"]} 🔥 FLAMES: {emotional["flame_result"]} | ♈ Zodiac: {emotional["zodiac_compatibility"]}%'
            share_summary = f'{name1} & {name2}: {love_percentage}% — {category["message"]}'

            response_data = {
                'success': True,
                'calc_type': 'love_percentage',
                'name1': name1,
                'name2': name2,
                'love_percentage': love_percentage,
                'category': category['name'],
                'message': category['message'],
                'category_color': category.get('color'),
                'color_info': color_info,
                'personality_match': personality_match,
                'couple_color': couple_color_key,
                'couple_color_info': couple_color_info,
                'romantic_tip': romantic_tip,
                'share_summary': share_summary,
                'share_text': share_text,
                'step_by_step': steps,
                'advanced_components': advanced_components,
                'chart_data': chart_data,
            }
            response_data.update(emotional)
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating love percentage: {error}').format(error=str(e))
            }, status=500)

    def _calculate_compatibility(self, data):
        """Calculate compatibility score"""
        try:
            if 'name1' not in data or not data.get('name1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First name is required.')
                }, status=400)

            if 'name2' not in data or not data.get('name2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second name is required.')
                }, status=400)

            name1 = data.get('name1', '').strip()
            name2 = data.get('name2', '').strip()
            dob1 = data.get('dob1')
            dob2 = data.get('dob2')
            energy1 = data.get('energy1')
            energy2 = data.get('energy2')
            style1 = data.get('style1')
            style2 = data.get('style2')
            color1 = data.get('color1')
            color2 = data.get('color2')

            if not name1 or not name2:
                return JsonResponse({
                    'success': False,
                    'error': _('Both names are required.')
                }, status=400)

            name1_lower = name1.lower().replace(' ', '')
            name2_lower = name2.lower().replace(' ', '')

            # Factor 1: Common letters
            common_letters = 0
            for char in set(name1_lower):
                if char.isalpha():
                    common_letters += min(name1_lower.count(char), name2_lower.count(char))

            total_letters = len(name1_lower) + len(name2_lower)
            common_score = float(np.multiply(
                np.divide(common_letters, total_letters) if total_letters > 0 else 0,
                100.0
            ))

            # Factor 2: Name length similarity
            len1 = len(name1_lower)
            len2 = len(name2_lower)
            length_score = float(np.multiply(
                np.divide(min(len1, len2), max(len1, len2)) if max(len1, len2) > 0 else 0,
                100.0
            ))

            # Factor 3: Vowel/Consonant ratio similarity
            vowels = 'aeiou'
            v1 = sum(1 for c in name1_lower if c in vowels)
            v2 = sum(1 for c in name2_lower if c in vowels)
            c1 = len1 - v1
            c2 = len2 - v2

            vowel_ratio1 = float(np.divide(v1, len1)) if len1 > 0 else 0
            vowel_ratio2 = float(np.divide(v2, len2)) if len2 > 0 else 0
            vowel_score = float(np.multiply(
                np.subtract(1.0, abs(np.subtract(vowel_ratio1, vowel_ratio2))),
                100.0
            ))

            # Combine factors
            compatibility = float(np.divide(
                np.add(np.add(common_score, length_score), vowel_score),
                3.0
            ))

            compatibility = max(0, min(100, compatibility))
            compatibility = int(round(compatibility))

            category = self._get_love_category(compatibility)
            color_info = self._get_color_info(category['name'])

            # Build emotional features
            emotional = self._build_emotional_features(name1, name2, category['name'], dob1=dob1, dob2=dob2)

            # Personality / likes match & couple color
            personality_match = self._calculate_personality_match(energy1, energy2, style1, style2, color1, color2)
            couple_color_key = self._get_couple_color(color1, color2)
            couple_color_info = self._get_couple_color_info(couple_color_key)

            steps = self._prepare_compatibility_steps(name1, name2, common_letters, common_score, length_score, vowel_score, compatibility)
            chart_data = self._prepare_compatibility_chart_data(compatibility, common_score, length_score, vowel_score)
            romantic_tip = self._get_romantic_tip(category['name'])

            share_text = f'💕 {name1} & {name2}: {compatibility}% Compatible! {category["message"]} 🔥 FLAMES: {emotional["flame_result"]}'
            share_summary = f'{name1} & {name2}: {compatibility}% — {category["message"]}'

            response_data = {
                'success': True,
                'calc_type': 'compatibility',
                'name1': name1,
                'name2': name2,
                'compatibility': compatibility,
                'common_score': round(common_score, 1),
                'length_score': round(length_score, 1),
                'vowel_score': round(vowel_score, 1),
                'category': category['name'],
                'message': category['message'],
                'category_color': category.get('color'),
                'color_info': color_info,
                'personality_match': personality_match,
                'couple_color': couple_color_key,
                'couple_color_info': couple_color_info,
                'romantic_tip': romantic_tip,
                'share_summary': share_summary,
                'share_text': share_text,
                'step_by_step': steps,
                'chart_data': chart_data,
            }
            response_data.update(emotional)
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error calculating compatibility: {error}').format(error=str(e))
            }, status=500)

    def _analyze_names(self, data):
        """Analyze names for compatibility"""
        try:
            if 'name1' not in data or not data.get('name1'):
                return JsonResponse({
                    'success': False,
                    'error': _('First name is required.')
                }, status=400)

            if 'name2' not in data or not data.get('name2'):
                return JsonResponse({
                    'success': False,
                    'error': _('Second name is required.')
                }, status=400)

            name1 = data.get('name1', '').strip()
            name2 = data.get('name2', '').strip()
            dob1 = data.get('dob1')
            dob2 = data.get('dob2')
            energy1 = data.get('energy1')
            energy2 = data.get('energy2')
            style1 = data.get('style1')
            style2 = data.get('style2')
            color1 = data.get('color1')
            color2 = data.get('color2')

            if not name1 or not name2:
                return JsonResponse({
                    'success': False,
                    'error': _('Both names are required.')
                }, status=400)

            name1_lower = name1.lower().replace(' ', '')
            name2_lower = name2.lower().replace(' ', '')

            vowels = 'aeiou'
            analysis = {
                'name1_length': len(name1_lower),
                'name2_length': len(name2_lower),
                'common_letters': [],
                'unique_letters_name1': [],
                'unique_letters_name2': [],
                'vowel_count_name1': sum(1 for c in name1_lower if c in vowels),
                'vowel_count_name2': sum(1 for c in name2_lower if c in vowels),
                'consonant_count_name1': 0,
                'consonant_count_name2': 0,
            }
            analysis['consonant_count_name1'] = len(name1_lower) - analysis['vowel_count_name1']
            analysis['consonant_count_name2'] = len(name2_lower) - analysis['vowel_count_name2']

            set1 = set(name1_lower)
            set2 = set(name2_lower)
            analysis['common_letters'] = sorted(list(set1.intersection(set2)))
            analysis['unique_letters_name1'] = sorted(list(set1 - set2))
            analysis['unique_letters_name2'] = sorted(list(set2 - set1))

            # Build emotional features
            emotional = self._build_emotional_features(name1, name2, 'good', dob1=dob1, dob2=dob2)

            # Personality / likes match & couple color (uses "good" baseline)
            personality_match = self._calculate_personality_match(energy1, energy2, style1, style2, color1, color2)
            couple_color_key = self._get_couple_color(color1, color2)
            couple_color_info = self._get_couple_color_info(couple_color_key)

            steps = self._prepare_name_analysis_steps(name1, name2, analysis)

            share_text = f'💕 {name1} & {name2}: {len(analysis["common_letters"])} common letters | FLAMES: {emotional["flame_result"]}'
            share_summary = f'{name1} & {name2}: {len(analysis["common_letters"])} common letters'

            response_data = {
                'success': True,
                'calc_type': 'name_analysis',
                'name1': name1,
                'name2': name2,
                'analysis': analysis,
                'share_summary': share_summary,
                'share_text': share_text,
                'step_by_step': steps,
            }
            response_data.update({
                'personality_match': personality_match,
                'couple_color': couple_color_key,
                'couple_color_info': couple_color_info,
            })
            response_data.update(emotional)
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error analyzing names: {error}').format(error=str(e))
            }, status=500)

    # ---------- Utilities ----------

    def _get_love_category(self, percentage):
        """Get love category based on percentage"""
        for key, (min_val, max_val, message) in sorted(self.LOVE_CATEGORIES.items(), key=lambda x: x[1][0], reverse=True):
            if percentage >= min_val:
                return {
                    'name': key,
                    'message': message,
                    'color': self.CATEGORY_COLORS.get(key, 'pink'),
                }
        return {
            'name': 'poor',
            'message': _('Needs Work'),
            'color': self.CATEGORY_COLORS.get('poor', 'gray'),
        }

    def _get_color_info(self, category_key):
        """
        Map a love category key to concrete color information for the frontend,
        similar in spirit to BMI's backend-controlled color mapping.
        """
        color_key = self.CATEGORY_COLORS.get(category_key, 'pink')
        color_map = {
            'pink': {
                'hex': '#ec4899',
                'rgb': 'rgb(236, 72, 153)',
                'tailwind_classes': 'bg-pink-100 text-pink-800 border-pink-300',
            },
            'rose': {
                'hex': '#f43f5e',
                'rgb': 'rgb(244, 63, 94)',
                'tailwind_classes': 'bg-rose-100 text-rose-800 border-rose-300',
            },
            'orange': {
                'hex': '#f97316',
                'rgb': 'rgb(249, 115, 22)',
                'tailwind_classes': 'bg-orange-100 text-orange-800 border-orange-300',
            },
            'yellow': {
                'hex': '#facc15',
                'rgb': 'rgb(250, 204, 21)',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300',
            },
            'gray': {
                'hex': '#6b7280',
                'rgb': 'rgb(107, 114, 128)',
                'tailwind_classes': 'bg-gray-100 text-gray-800 border-gray-300',
            },
        }
        return color_map.get(color_key, color_map['pink'])

    # ---------- Advanced NumPy-based similarity ----------

    def _name_vector(self, name):
        """Return normalized 26-dim letter frequency vector for a name."""
        n = name.lower()
        vec = np.zeros(26, dtype=float)
        for ch in n:
            if 'a' <= ch <= 'z':
                idx = ord(ch) - ord('a')
                vec[idx] += 1.0
        total = vec.sum()
        if total > 0:
            vec /= total
        return vec

    def _cosine_similarity(self, u, v):
        """Cosine similarity between two NumPy vectors."""
        dot = float(np.dot(u, v))
        norm_u = float(np.linalg.norm(u))
        norm_v = float(np.linalg.norm(v))
        if norm_u == 0.0 or norm_v == 0.0:
            return 0.0
        return dot / (norm_u * norm_v)

    def _jaccard_letters(self, name1, name2):
        """Jaccard similarity based on unique letters."""
        n1 = {c for c in name1.lower() if c.isalpha()}
        n2 = {c for c in name2.lower() if c.isalpha()}
        if not n1 and not n2:
            return 0.0
        inter = len(n1 & n2)
        union = len(n1 | n2)
        if union == 0:
            return 0.0
        return inter / union

    def _vowel_fraction(self, name):
        """Fraction of characters that are vowels, computed with NumPy arrays."""
        chars = np.array(list(name.lower()))
        if chars.size == 0:
            return 0.0
        vowels = np.array(list("aeiou"))
        is_vowel = np.isin(chars, vowels)
        return float(is_vowel.sum() / chars.size)

    def _advanced_love_components(self, name1, name2):
        """
        Compute advanced similarity components using NumPy:
        - cosine similarity of letter vectors
        - Jaccard similarity on letter sets
        - length similarity
        - vowel/consonant balance similarity
        Returns all components plus a weighted final score (0-100).
        """
        vec1 = self._name_vector(name1)
        vec2 = self._name_vector(name2)

        cos_score = self._cosine_similarity(vec1, vec2) * 100.0
        jac_score = self._jaccard_letters(name1, name2) * 100.0

        letters1 = [c for c in name1.lower() if c.isalpha()]
        letters2 = [c for c in name2.lower() if c.isalpha()]
        len1 = len(letters1)
        len2 = len(letters2)
        if max(len1, len2) > 0:
            length_score = float(np.divide(min(len1, len2), max(len1, len2)) * 100.0)
        else:
            length_score = 0.0

        v1 = self._vowel_fraction(name1)
        v2 = self._vowel_fraction(name2)
        vowel_score = float((1.0 - abs(v1 - v2)) * 100.0)

        # Weights must sum to 1.0
        w_cos, w_jac, w_len, w_vowel = 0.35, 0.35, 0.20, 0.10
        advanced_score = (
            w_cos * cos_score
            + w_jac * jac_score
            + w_len * length_score
            + w_vowel * vowel_score
        )
        advanced_score = max(0.0, min(100.0, advanced_score))

        return {
            'cosine_score': cos_score,
            'jaccard_score': jac_score,
            'length_score': length_score,
            'vowel_score': vowel_score,
            'advanced_score': advanced_score,
        }

    def _step(self, text, step_type='text'):
        """Return a step dict with text and type for language-agnostic frontend rendering."""
        return {'text': text, 'type': step_type}

    # ---------- Step-by-step solutions ----------

    def _prepare_love_percentage_steps(self, name1, name2, combined, l_count, o_count, v_count, e_count, love_score, letter_percentage, common_letters, common_percentage, final_percentage, love_percentage, advanced_components=None):
        """Prepare step-by-step solution for love percentage calculation (legacy + advanced NumPy-based)."""
        steps = []
        steps.append(self._step(_('Step 1: Identify the given names'), 'step'))
        steps.append(self._step(_('Name 1: {name}').format(name=name1), 'text'))
        steps.append(self._step(_('Name 2: {name}').format(name=name2), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 2: Combine and normalize names'), 'step'))
        steps.append(self._step(_('Combined: {combined}').format(combined=combined), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 3: Count L, O, V, E letters'), 'step'))
        steps.append(self._step(_('L count: {count}').format(count=l_count), 'text'))
        steps.append(self._step(_('O count: {count}').format(count=o_count), 'text'))
        steps.append(self._step(_('V count: {count}').format(count=v_count), 'text'))
        steps.append(self._step(_('E count: {count}').format(count=e_count), 'text'))
        steps.append(self._step(_('Total LOVE letters: {total}').format(total=love_score), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 4: Calculate letter percentage'), 'step'))
        steps.append(self._step(_('Letter Percentage = (LOVE letters / Total letters) × 100'), 'formula'))
        steps.append(self._step(_('Letter Percentage = ({love} / {total}) × 100 = {percent}%').format(
            love=love_score, total=len(combined), percent=round(letter_percentage, 1)
        ), 'formula'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 5: Calculate common letters percentage'), 'step'))
        steps.append(self._step(_('Common Letters: {common}').format(common=common_letters), 'text'))
        steps.append(self._step(_('Common Percentage: {percent}%').format(percent=round(common_percentage, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 6: Combine percentages'), 'step'))
        steps.append(self._step(_('Final Percentage = (Letter % × 0.4) + (Common % × 0.6)'), 'formula'))
        steps.append(self._step(_('Final Percentage = ({letter} × 0.4) + ({common} × 0.6) = {final}%').format(
            letter=round(letter_percentage, 1), common=round(common_percentage, 1), final=love_percentage
        ), 'formula'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 7: Final Result'), 'step'))
        steps.append(self._step(_('Love Percentage: {percent}%').format(percent=love_percentage), 'result'))
        # Advanced NumPy-based explanation (optional)
        if advanced_components:
            steps.append(self._step('', 'blank'))
            steps.append(self._step(_('Advanced analysis with NumPy'), 'step'))
            steps.append(self._step(
                _('We also compute similarity using letter frequency vectors and set-based metrics.'), 'text'
            ))
            steps.append(self._step(
                _('Cosine similarity score (0–100) based on 26-letter vectors: {val}%').format(
                    val=round(advanced_components.get('cosine_score', 0.0), 1)
                ),
                'text',
            ))
            steps.append(self._step(
                _('Jaccard similarity score (0–100) based on unique letter sets: {val}%').format(
                    val=round(advanced_components.get('jaccard_score', 0.0), 1)
                ),
                'text',
            ))
            steps.append(self._step(
                _('Length similarity score (0–100) using min/ max name lengths: {val}%').format(
                    val=round(advanced_components.get('length_score', 0.0), 1)
                ),
                'text',
            ))
            steps.append(self._step(
                _('Vowel balance score (0–100) comparing vowel/consonant ratios: {val}%').format(
                    val=round(advanced_components.get('vowel_score', 0.0), 1)
                ),
                'text',
            ))
            steps.append(self._step('', 'blank'))
            steps.append(self._step(_('Advanced combined score'), 'step'))
            steps.append(self._step(
                _('Advanced Score = 0.35×Cosine + 0.35×Jaccard + 0.20×Length + 0.10×Vowel'), 'formula'
            ))
            steps.append(self._step(
                _('Advanced Score ≈ {val}% (blended with classic score for final result)').format(
                    val=round(advanced_components.get('advanced_score', 0.0), 1)
                ),
                'result',
            ))
        return steps

    def _prepare_compatibility_steps(self, name1, name2, common_letters, common_score, length_score, vowel_score, compatibility):
        """Prepare step-by-step solution for compatibility calculation"""
        steps = []
        steps.append(self._step(_('Step 1: Identify the given names'), 'step'))
        steps.append(self._step(_('Name 1: {name}').format(name=name1), 'text'))
        steps.append(self._step(_('Name 2: {name}').format(name=name2), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 2: Calculate common letters score'), 'step'))
        steps.append(self._step(_('Common Letters: {common}').format(common=common_letters), 'text'))
        steps.append(self._step(_('Common Score: {score}%').format(score=round(common_score, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 3: Calculate name length similarity'), 'step'))
        steps.append(self._step(_('Length Score: {score}%').format(score=round(length_score, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 4: Calculate vowel/consonant ratio similarity'), 'step'))
        steps.append(self._step(_('Vowel Score: {score}%').format(score=round(vowel_score, 1)), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 5: Calculate overall compatibility'), 'step'))
        steps.append(self._step(_('Compatibility = (Common Score + Length Score + Vowel Score) / 3'), 'formula'))
        steps.append(self._step(_('Compatibility = ({common} + {length} + {vowel}) / 3 = {final}%').format(
            common=round(common_score, 1), length=round(length_score, 1),
            vowel=round(vowel_score, 1), final=compatibility
        ), 'result'))
        return steps

    def _prepare_name_analysis_steps(self, name1, name2, analysis):
        """Prepare step-by-step solution for name analysis"""
        steps = []
        steps.append(self._step(_('Step 1: Identify the given names'), 'step'))
        steps.append(self._step(_('Name 1: {name}').format(name=name1), 'text'))
        steps.append(self._step(_('Name 2: {name}').format(name=name2), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 2: Analyze name lengths'), 'step'))
        steps.append(self._step(_('Name 1 Length: {len} characters').format(len=analysis['name1_length']), 'text'))
        steps.append(self._step(_('Name 2 Length: {len} characters').format(len=analysis['name2_length']), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 3: Count vowels and consonants'), 'step'))
        steps.append(self._step(_('Name 1: {vowels} vowels, {consonants} consonants').format(
            vowels=analysis['vowel_count_name1'], consonants=analysis['consonant_count_name1']
        ), 'text'))
        steps.append(self._step(_('Name 2: {vowels} vowels, {consonants} consonants').format(
            vowels=analysis['vowel_count_name2'], consonants=analysis['consonant_count_name2']
        ), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 4: Find common letters'), 'step'))
        if analysis['common_letters']:
            steps.append(self._step(_('Common Letters: {letters}').format(letters=', '.join(analysis['common_letters'])), 'text'))
        else:
            steps.append(self._step(_('Common Letters: None'), 'text'))
        steps.append(self._step('', 'blank'))
        steps.append(self._step(_('Step 5: Find unique letters'), 'step'))
        if analysis['unique_letters_name1']:
            steps.append(self._step(_('Unique to Name 1: {letters}').format(letters=', '.join(analysis['unique_letters_name1'])), 'text'))
        if analysis['unique_letters_name2']:
            steps.append(self._step(_('Unique to Name 2: {letters}').format(letters=', '.join(analysis['unique_letters_name2'])), 'text'))
        return steps

    # ---------- Chart data ----------

    def _prepare_love_percentage_chart_data(self, love_percentage, category):
        """Prepare chart data for love percentage calculation"""
        try:
            chart_config = {
                'type': 'doughnut',
                'data': {
                    'labels': [_('Love Percentage'), _('Remaining')],
                    'datasets': [{
                        'data': [love_percentage, 100 - love_percentage],
                        'backgroundColor': [
                            'rgba(236, 72, 153, 0.8)',
                            'rgba(156, 163, 175, 0.8)'
                        ],
                        'borderColor': [
                            '#ec4899',
                            '#9ca3af'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': True,
                            'position': 'bottom'
                        },
                        'title': {
                            'display': True,
                            'text': _('Love Percentage: {percent}%').format(percent=love_percentage)
                        }
                    }
                }
            }
            return {'love_percentage_chart': chart_config}
        except Exception as e:
            return None

    def _prepare_compatibility_chart_data(self, compatibility, common_score, length_score, vowel_score):
        """Prepare chart data for compatibility calculation"""
        try:
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': [_('Common Letters'), _('Length Similarity'), _('Vowel Ratio'), _('Overall Compatibility')],
                    'datasets': [{
                        'label': _('Score (%)'),
                        'data': [common_score, length_score, vowel_score, compatibility],
                        'backgroundColor': [
                            'rgba(59, 130, 246, 0.8)',
                            'rgba(16, 185, 129, 0.8)',
                            'rgba(251, 191, 36, 0.8)',
                            'rgba(236, 72, 153, 0.8)'
                        ],
                        'borderColor': [
                            '#3b82f6',
                            '#10b981',
                            '#fbbf24',
                            '#ec4899'
                        ],
                        'borderWidth': 2
                    }]
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': True,
                    'plugins': {
                        'legend': {
                            'display': False
                        },
                        'title': {
                            'display': True,
                            'text': _('Compatibility Analysis')
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'max': 100,
                            'title': {
                                'display': True,
                                'text': _('Score (%)')
                            }
                        }
                    }
                }
            }
            return {'compatibility_chart': chart_config}
        except Exception as e:
            return None