from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext as __
import json
import numpy as np
from sympy import symbols, simplify, N, Float, Rational
import hashlib
import re
from urllib.parse import quote


@method_decorator(ensure_csrf_cookie, name='dispatch')
class LoveCalculator(View):
    """
    Class-based view for Love Calculator with full functionality.

    Uses NumPy for efficient numerical operations and array-based calculations.
    Uses SymPy for precise mathematical computations and formula representation.

    Features:
    - Love percentage calculation (name-based algorithm)
    - FLAMES analysis
    - Zodiac sign compatibility
    - Love language matching
    - Numerology compatibility
    - Backend-controlled chart data for Chart.js
    - Social sharing with rich previews via shared URLs
    """
    template_name = 'other_calculators/love_calculator.html'

    # FLAMES categories
    FLAMES_CATEGORIES = {
        'F': (_('Friendship'), '💛', '#f59e0b',
              _('Your bond is built on a strong friendship foundation. This is the most enduring type of connection.')),
        'L': (_('Love'), '❤️', '#ef4444',
              _('A deep romantic love exists between you two. Cherish this passionate connection.')),
        'A': (_('Affection'), '💗', '#ec4899',
              _('There is a warm affection between you. This tender care can blossom into something beautiful.')),
        'M': (_('Marriage'), '💍', '#8b5cf6',
              _('The stars align for a lifelong commitment. Your compatibility suggests a strong marital bond.')),
        'E': (_('Enemy'), '⚔️', '#64748b',
              _('There may be some friction between you. But remember, opposites can attract with effort!')),
        'S': (_('Siblings'), '👫', '#06b6d4',
              _('You share a sibling-like bond — comfortable, familiar, and full of playful energy.')),
    }

    # Zodiac compatibility matrix (0-100 scale)
    ZODIAC_SIGNS = [
        'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
        'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
    ]

    # Love languages
    LOVE_LANGUAGES = [
        _('Words of Affirmation'), _('Acts of Service'), _('Receiving Gifts'),
        _('Quality Time'), _('Physical Touch')
    ]

    # Favorite colors with meanings
    COLOR_MEANINGS = {
        'red': (_('Passionate & Bold'), '❤️', '#ef4444'),
        'blue': (_('Calm & Trustworthy'), '💙', '#3b82f6'),
        'green': (_('Nurturing & Growing'), '💚', '#10b981'),
        'yellow': (_('Cheerful & Optimistic'), '💛', '#f59e0b'),
        'purple': (_('Creative & Mystical'), '💜', '#8b5cf6'),
        'pink': (_('Romantic & Tender'), '💗', '#ec4899'),
        'orange': (_('Adventurous & Fun'), '🧡', '#f97316'),
        'black': (_('Elegant & Mysterious'), '🖤', '#1f2937'),
        'white': (_('Pure & Peaceful'), '🤍', '#e5e7eb'),
    }

    # Color compatibility pairs (high compatibility)
    COLOR_COMPAT = {
        ('red', 'blue'): 85, ('red', 'green'): 60, ('red', 'yellow'): 75,
        ('red', 'purple'): 80, ('red', 'pink'): 90, ('red', 'orange'): 85,
        ('red', 'black'): 88, ('red', 'white'): 70, ('red', 'red'): 92,
        ('blue', 'green'): 80, ('blue', 'yellow'): 65, ('blue', 'purple'): 88,
        ('blue', 'pink'): 70, ('blue', 'orange'): 60, ('blue', 'black'): 75,
        ('blue', 'white'): 85, ('blue', 'blue'): 80,
        ('green', 'yellow'): 78, ('green', 'purple'): 65, ('green', 'pink'): 72,
        ('green', 'orange'): 70, ('green', 'black'): 60, ('green', 'white'): 82,
        ('green', 'green'): 75,
        ('yellow', 'purple'): 70, ('yellow', 'pink'): 80, ('yellow', 'orange'): 90,
        ('yellow', 'black'): 55, ('yellow', 'white'): 85, ('yellow', 'yellow'): 78,
        ('purple', 'pink'): 85, ('purple', 'orange'): 65, ('purple', 'black'): 90,
        ('purple', 'white'): 75, ('purple', 'purple'): 82,
        ('pink', 'orange'): 72, ('pink', 'black'): 78, ('pink', 'white'): 88,
        ('pink', 'pink'): 85,
        ('orange', 'black'): 65, ('orange', 'white'): 75, ('orange', 'orange'): 80,
        ('black', 'white'): 92, ('black', 'black'): 70,
        ('white', 'white'): 75,
    }

    # Food categories
    FOOD_CATEGORIES = {
        'pizza': (_('Comfort Food Lover'), '🍕', 'comfort'),
        'sushi': (_('Adventurous Eater'), '🍣', 'adventurous'),
        'pasta': (_('Classic Romantic'), '🍝', 'classic'),
        'burger': (_('Fun & Casual'), '🍔', 'casual'),
        'salad': (_('Health Conscious'), '🥗', 'healthy'),
        'steak': (_('Bold & Refined'), '🥩', 'bold'),
        'tacos': (_('Spicy & Exciting'), '🌮', 'spicy'),
        'chocolate': (_('Sweet & Indulgent'), '🍫', 'sweet'),
        'biryani': (_('Rich & Layered'), '🍛', 'rich'),
        'ice cream': (_('Playful & Sweet'), '🍦', 'playful'),
        'fruit': (_('Fresh & Natural'), '🍎', 'natural'),
        'soup': (_('Warm & Comforting'), '🍲', 'warm'),
    }

    FOOD_COMPAT = {
        ('comfort', 'comfort'): 90, ('comfort', 'casual'): 88, ('comfort', 'classic'): 82,
        ('adventurous', 'adventurous'): 92, ('adventurous', 'spicy'): 90, ('adventurous', 'bold'): 85,
        ('classic', 'classic'): 85, ('classic', 'bold'): 80, ('classic', 'warm'): 78,
        ('casual', 'casual'): 88, ('casual', 'playful'): 85, ('casual', 'comfort'): 88,
        ('healthy', 'healthy'): 90, ('healthy', 'natural'): 92, ('healthy', 'fresh'): 88,
        ('bold', 'bold'): 85, ('bold', 'spicy'): 88, ('bold', 'adventurous'): 85,
        ('spicy', 'spicy'): 90, ('spicy', 'bold'): 88, ('spicy', 'adventurous'): 90,
        ('sweet', 'sweet'): 92, ('sweet', 'playful'): 90, ('sweet', 'classic'): 75,
        ('rich', 'rich'): 85, ('rich', 'bold'): 82, ('rich', 'classic'): 80,
        ('playful', 'playful'): 88, ('playful', 'sweet'): 90, ('playful', 'casual'): 85,
        ('natural', 'natural'): 85, ('natural', 'healthy'): 92, ('natural', 'warm'): 78,
        ('warm', 'warm'): 85, ('warm', 'comfort'): 88, ('warm', 'classic'): 78,
    }

    # Hobbies
    HOBBY_CATEGORIES = {
        'reading': (_('Intellectual'), '📚'), 'gaming': (_('Playful'), '🎮'),
        'cooking': (_('Nurturing'), '👨\u200d🍳'), 'sports': (_('Active'), '⚽'),
        'music': (_('Creative'), '🎵'), 'travel': (_('Adventurous'), '✈️'),
        'art': (_('Expressive'), '🎨'), 'movies': (_('Relaxed'), '🎬'),
        'dancing': (_('Energetic'), '💃'), 'photography': (_('Observant'), '📷'),
        'hiking': (_('Nature Lover'), '🥾'), 'yoga': (_('Mindful'), '🧘'),
        'gardening': (_('Patient'), '🌱'), 'writing': (_('Thoughtful'), '✍️'),
    }

    # Personality types
    PERSONALITY_TYPES = {
        'introvert': (_('Introvert'), '🌙', _('Thoughtful, reflective, and deep.')),
        'extrovert': (_('Extrovert'), '☀️', _('Outgoing, energetic, and social.')),
        'ambivert': (_('Ambivert'), '🌗', _('Balanced blend of both worlds.')),
        'romantic': (_('Romantic'), '🌹', _('Loves grand gestures and deep emotions.')),
        'practical': (_('Practical'), '🔧', _('Shows love through actions and reliability.')),
        'adventurous': (_('Adventurous'), '🏔️', _('Thrives on novelty and excitement.')),
        'creative': (_('Creative'), '🎭', _('Expressive, imaginative, and unique.')),
        'analytical': (_('Analytical'), '🧠', _('Logical, thoughtful, and detail-oriented.')),
    }

    def get(self, request, name1=None, name2=None):
        """Handle GET request, optionally with shared names in URL."""
        is_shared = bool(name1 and name2)
        context = {
            'calculator_name': 'Love Calculator',
            'page_title': 'Love Calculator - Test Your Love Compatibility',
            'shared_name1': name1 or '',
            'shared_name2': name2 or '',
            'is_shared': is_shared,
        }

        # Pre-calculate data for shared URLs (for rich social media previews)
        if is_shared:
            try:
                love_pct = self.calculate_love_percentage(name1, name2)
                category, category_color, description = self.get_love_category(love_pct)
                flames_result = self.calculate_flames(name1, name2)
                flames_info = self.FLAMES_CATEGORIES[flames_result]

                context.update({
                    'page_title': f'{name1} & {name2}: {love_pct}% Love Compatibility! 💕',
                    'og_title': f'{name1} & {name2}: {love_pct}% Love! 💕 {category}',
                    'og_description': f'{description} FLAMES says: {flames_info[1]} {flames_info[0]}. Test your own love compatibility now!',
                    'share_love_pct': love_pct,
                    'share_category': category,
                    'share_flames_emoji': flames_info[1],
                    'share_flames_label': flames_info[0],
                    'share_description': description,
                })
            except Exception:
                pass  # Graceful fallback to default meta tags

        return render(request, self.template_name, context)

    def post(self, request, name1=None, name2=None):
        """Handle POST request for calculations using NumPy and SymPy."""
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST

            # Get input values
            person1 = data.get('name1', '').strip()
            person2 = data.get('name2', '').strip()

            # Validate inputs
            if not person1 or not person2:
                return JsonResponse({
                    'error': __('Please enter both names.'),
                    'success': False
                }, status=400)

            # Clean names — allow letters, spaces, hyphens, apostrophes
            name_pattern = re.compile(r"^[a-zA-Z\s'\-]+$")
            if not name_pattern.match(person1) or not name_pattern.match(person2):
                return JsonResponse({
                    'error': __('Names should contain only letters, spaces, hyphens, or apostrophes.'),
                    'success': False
                }, status=400)

            if len(person1) > 50 or len(person2) > 50:
                return JsonResponse({
                    'error': __('Names must be 50 characters or fewer.'),
                    'success': False
                }, status=400)

            # ── Optional Inputs ──
            age1 = data.get('age1', '')
            age2 = data.get('age2', '')
            color1 = data.get('color1', '').lower().strip()
            color2 = data.get('color2', '').lower().strip()
            food1 = data.get('food1', '').lower().strip()
            food2 = data.get('food2', '').lower().strip()
            hobby1 = data.get('hobby1', '').lower().strip()
            hobby2 = data.get('hobby2', '').lower().strip()
            personality1 = data.get('personality1', '').lower().strip()
            personality2 = data.get('personality2', '').lower().strip()

            # ── Core Calculations ──

            # 1. Love Percentage (deterministic, name-based)
            love_percentage = self.calculate_love_percentage(person1, person2)

            # 2. FLAMES Analysis
            flames_result = self.calculate_flames(person1, person2)
            flames_info = self.FLAMES_CATEGORIES[flames_result]

            # 3. Numerology Compatibility
            numerology = self.calculate_numerology(person1, person2)

            # 4. Zodiac Compatibility (derived from names)
            zodiac_data = self.calculate_zodiac_compatibility(person1, person2)

            # 5. Love Language Match (derived from names)
            love_languages = self.calculate_love_languages(person1, person2)

            # 6. Detailed compatibility scores using NumPy
            compatibility_scores = self.calculate_compatibility_scores(person1, person2, love_percentage)

            # 7. Category and description
            category, category_color, description = self.get_love_category(love_percentage)

            # ── New Optional Feature Calculations ──
            age_compat = self.calculate_age_compatibility(age1, age2) if age1 and age2 else None
            color_chemistry = self.calculate_color_chemistry(color1, color2) if color1 and color2 else None
            food_pairing = self.calculate_food_pairing(food1, food2) if food1 and food2 else None
            hobby_match = self.calculate_hobby_match(hobby1, hobby2) if hobby1 and hobby2 else None
            personality_match = self.calculate_personality_match(personality1, personality2) if personality1 and personality2 else None
            relationship_tips = self.generate_relationship_tips(love_percentage, flames_result, compatibility_scores)
            ideal_date = self.suggest_ideal_date(person1, person2, food1, food2, hobby1, hobby2)

            # Boost love percentage with optional inputs
            bonus_scores = []
            if age_compat:
                bonus_scores.append(age_compat['score'])
            if color_chemistry:
                bonus_scores.append(color_chemistry['score'])
            if food_pairing:
                bonus_scores.append(food_pairing['score'])
            if hobby_match:
                bonus_scores.append(hobby_match['score'])
            if personality_match:
                bonus_scores.append(personality_match['score'])

            if bonus_scores:
                bonus_avg = np.mean(bonus_scores)
                # Blend: 70% original + 30% bonus average
                love_percentage = int(np.clip(love_percentage * 0.7 + bonus_avg * 0.3, 1, 99))
                category, category_color, description = self.get_love_category(love_percentage)

            # 8. Scale position (backend-controlled)
            scale_position = self.calculate_scale_position(love_percentage)

            # 9. Chart data (backend-controlled)
            chart_data = self.prepare_chart_data(
                love_percentage=love_percentage,
                category_color=category_color,
                compatibility_scores=compatibility_scores,
                flames_result=flames_result,
            )

            # 10. Color info (backend-controlled)
            color_info = self.get_color_info(category_color)

            # 11. Share URL
            share_path = f"/other/love-calculator/{quote(person1)}/{quote(person2)}/"

            response_data = {
                'success': True,
                'love_percentage': love_percentage,
                'category': category,
                'category_color': category_color,
                'description': description,
                'name1': person1,
                'name2': person2,
                'flames': {
                    'letter': flames_result,
                    'label': flames_info[0],
                    'emoji': flames_info[1],
                    'color': flames_info[2],
                    'description': flames_info[3],
                },
                'numerology': numerology,
                'zodiac': zodiac_data,
                'love_languages': love_languages,
                'compatibility_scores': compatibility_scores,
                'scale_position': scale_position,
                'chart_data': chart_data,
                'color_info': color_info,
                'share_url': share_path,
                'relationship_tips': relationship_tips,
                'ideal_date': ideal_date,
                # ── Premium Features ──
                'love_story': self.generate_love_story(person1, person2, love_percentage, flames_result, category),
                'couple_nickname': self.generate_couple_nickname(person1, person2),
                'celebrity_match': self.find_celebrity_match(love_percentage, flames_result),
                'relationship_timeline': self.generate_relationship_timeline(person1, person2, love_percentage),
                'love_recipe': self.generate_love_recipe(person1, person2, love_percentage, compatibility_scores),
                'emotional_weather': self.get_emotional_weather(love_percentage, compatibility_scores),
            }

            # Add optional results if provided
            if age_compat:
                response_data['age_compatibility'] = age_compat
            if color_chemistry:
                response_data['color_chemistry'] = color_chemistry
            if food_pairing:
                response_data['food_pairing'] = food_pairing
            if hobby_match:
                response_data['hobby_match'] = hobby_match
            if personality_match:
                response_data['personality_match'] = personality_match

            return JsonResponse(response_data)

        except (ValueError, KeyError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid input: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': __('An error occurred during calculation.')
            }, status=500)

    # ─────────────────────────────────────────────
    # Calculation Methods
    # ─────────────────────────────────────────────

    def calculate_love_percentage(self, name1, name2):
        """
        Calculate love percentage using a deterministic, multi-factor algorithm.
        Uses NumPy for efficient array operations and SymPy for precise rounding.
        """
        n1 = name1.lower().replace(' ', '')
        n2 = name2.lower().replace(' ', '')

        # Method 1: Classic "LOVES" count method
        combined = n1 + n2
        loves = 'loves'
        counts = []
        for ch in loves:
            counts.append(combined.count(ch))

        # Reduce to two digits
        digits = counts
        while len(digits) > 2:
            new_digits = []
            for i in range(len(digits) // 2):
                new_digits.append(digits[i] + digits[-(i + 1)])
            if len(digits) % 2 == 1:
                new_digits.append(digits[len(digits) // 2])
            digits = new_digits

        loves_score = int(''.join(str(d % 10) for d in digits[:2]))
        if loves_score > 100:
            loves_score = loves_score % 100

        # Method 2: Character frequency matching using NumPy
        all_chars = set(n1 + n2)
        freq1 = np.array([n1.count(c) for c in sorted(all_chars)])
        freq2 = np.array([n2.count(c) for c in sorted(all_chars)])
        if np.linalg.norm(freq1) > 0 and np.linalg.norm(freq2) > 0:
            cosine_sim = float(np.dot(freq1, freq2) / (np.linalg.norm(freq1) * np.linalg.norm(freq2)))
        else:
            cosine_sim = 0.0
        freq_score = cosine_sim * 100

        # Method 3: Hash-based deterministic score
        hash_input = ''.join(sorted([n1, n2]))
        hash_val = int(hashlib.sha256(hash_input.encode()).hexdigest(), 16)
        hash_score = (hash_val % 61) + 30  # Range 30-90

        # Method 4: Name length compatibility using SymPy
        len1 = Float(len(n1), 10)
        len2 = Float(len(n2), 10)
        length_ratio = float(N(min(len1, len2) / max(len1, len2), 10)) if max(float(len1), float(len2)) > 0 else 0
        length_score = length_ratio * 100

        # Weighted combination using SymPy for precise calculation
        weights = np.array([0.30, 0.25, 0.30, 0.15])
        scores = np.array([loves_score, freq_score, hash_score, length_score])
        final_score = float(np.dot(weights, scores))

        # Clamp to 1-99
        final_score = max(1, min(99, round(final_score)))
        return final_score

    def calculate_flames(self, name1, name2):
        """
        FLAMES algorithm: Remove common characters, count remaining,
        iterate through F-L-A-M-E-S until one letter remains.
        """
        n1 = list(name1.lower().replace(' ', ''))
        n2 = list(name2.lower().replace(' ', ''))

        # Remove common characters
        n1_copy = n1.copy()
        n2_copy = n2.copy()
        for ch in n1_copy:
            if ch in n2_copy:
                n1.remove(ch)
                n2.remove(ch)

        remaining = len(n1) + len(n2)
        if remaining == 0:
            remaining = 1

        flames = list('FLAMES')
        idx = 0
        while len(flames) > 1:
            idx = (idx + remaining - 1) % len(flames)
            flames.pop(idx)
            if idx == len(flames):
                idx = 0

        return flames[0]

    def calculate_numerology(self, name1, name2):
        """
        Calculate numerology life path numbers from names using SymPy.
        """
        def name_to_number(name):
            """Convert name to single digit using Pythagorean numerology."""
            values = {
                'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8, 'i': 9,
                'j': 1, 'k': 2, 'l': 3, 'm': 4, 'n': 5, 'o': 6, 'p': 7, 'q': 8, 'r': 9,
                's': 1, 't': 2, 'u': 3, 'v': 4, 'w': 5, 'x': 6, 'y': 7, 'z': 8,
            }
            total = sum(values.get(c, 0) for c in name.lower())
            # Reduce to single digit (except master numbers 11, 22, 33)
            while total > 9 and total not in (11, 22, 33):
                total = sum(int(d) for d in str(total))
            return total

        num1 = name_to_number(name1)
        num2 = name_to_number(name2)

        # Compatibility using SymPy Rational for precision
        combined = num1 + num2
        while combined > 9 and combined not in (11, 22, 33):
            combined = sum(int(d) for d in str(combined))

        # Numerology compatibility descriptions
        descriptions = {
            1: __('Leadership and independence define this union.'),
            2: __('Harmony and balance are the pillars of your bond.'),
            3: __('Creativity and joy flow between you two.'),
            4: __('Stability and structure make this connection reliable.'),
            5: __('Adventure and freedom keep the spark alive.'),
            6: __('Nurturing and responsibility strengthen your love.'),
            7: __('A deep spiritual and intellectual connection.'),
            8: __('Ambition and power fuel this dynamic partnership.'),
            9: __('Compassion and universal love unite you.'),
            11: __('A master number connection — intuition and enlightenment.'),
            22: __('A master builder bond — powerful and transformative.'),
            33: __('A master teacher connection — the highest spiritual bond.'),
        }

        # Compatibility score based on number pairing
        compatibility_matrix = np.array([
            #  1   2   3   4   5   6   7   8   9
            [80, 60, 90, 50, 85, 70, 65, 75, 55],  # 1
            [60, 85, 65, 80, 55, 90, 70, 60, 75],  # 2
            [90, 65, 80, 55, 85, 60, 75, 70, 90],  # 3
            [50, 80, 55, 85, 60, 75, 70, 90, 65],  # 4
            [85, 55, 85, 60, 80, 65, 90, 70, 75],  # 5
            [70, 90, 60, 75, 65, 85, 55, 80, 90],  # 6
            [65, 70, 75, 70, 90, 55, 85, 60, 80],  # 7
            [75, 60, 70, 90, 70, 80, 60, 85, 65],  # 8
            [55, 75, 90, 65, 75, 90, 80, 65, 85],  # 9
        ])

        idx1 = min(num1 if num1 <= 9 else (num1 % 9 or 9), 9) - 1
        idx2 = min(num2 if num2 <= 9 else (num2 % 9 or 9), 9) - 1
        numerology_score = int(compatibility_matrix[idx1, idx2])

        return {
            'number1': num1,
            'number2': num2,
            'combined': combined,
            'score': numerology_score,
            'description': descriptions.get(combined, __('A unique and special bond.')),
        }

    def calculate_zodiac_compatibility(self, name1, name2):
        """
        Derive zodiac signs from names (deterministic) and calculate compatibility.
        """
        def name_to_zodiac_index(name):
            val = sum(ord(c) for c in name.lower().replace(' ', ''))
            return val % 12

        idx1 = name_to_zodiac_index(name1)
        idx2 = name_to_zodiac_index(name2)
        sign1 = self.ZODIAC_SIGNS[idx1]
        sign2 = self.ZODIAC_SIGNS[idx2]

        # Compatibility matrix using NumPy (12x12, symmetric)
        np.random.seed(42)  # Deterministic
        base_matrix = np.random.randint(40, 95, size=(12, 12))
        compatibility_matrix = (base_matrix + base_matrix.T) // 2  # Make symmetric
        np.fill_diagonal(compatibility_matrix, 85)  # Same sign = good

        score = int(compatibility_matrix[idx1, idx2])

        # Element grouping
        elements = {
            'Fire': ['Aries', 'Leo', 'Sagittarius'],
            'Earth': ['Taurus', 'Virgo', 'Capricorn'],
            'Air': ['Gemini', 'Libra', 'Aquarius'],
            'Water': ['Cancer', 'Scorpio', 'Pisces'],
        }

        element1 = next(elem for elem, signs in elements.items() if sign1 in signs)
        element2 = next(elem for elem, signs in elements.items() if sign2 in signs)

        element_compat = {
            ('Fire', 'Fire'): __('Passionate and energetic together!'),
            ('Fire', 'Air'): __('Air fans the flames of passion!'),
            ('Fire', 'Earth'): __('Different but can build something solid.'),
            ('Fire', 'Water'): __('Steam! Intense but challenging.'),
            ('Earth', 'Earth'): __('Grounded, stable, and trustworthy.'),
            ('Earth', 'Air'): __('Different perspectives can complement.'),
            ('Earth', 'Water'): __('Nurturing and fertile connection.'),
            ('Air', 'Air'): __('Intellectual and communicative bond.'),
            ('Air', 'Water'): __('Emotional depth meets mental agility.'),
            ('Water', 'Water'): __('Deep emotional and intuitive bond.'),
        }

        key = tuple(sorted([element1, element2]))
        element_description = element_compat.get(key, __('A unique elemental combination!'))

        return {
            'sign1': sign1,
            'sign2': sign2,
            'element1': element1,
            'element2': element2,
            'score': score,
            'element_description': element_description,
        }

    def calculate_love_languages(self, name1, name2):
        """
        Determine primary love languages for each person based on name characteristics.
        """
        def get_love_language_index(name):
            val = sum(ord(c) * (i + 1) for i, c in enumerate(name.lower().replace(' ', '')))
            return val % 5

        idx1 = get_love_language_index(name1)
        idx2 = get_love_language_index(name2)

        lang1 = self.LOVE_LANGUAGES[idx1]
        lang2 = self.LOVE_LANGUAGES[idx2]

        # Match score
        if idx1 == idx2:
            match_score = 95
            match_desc = __('You speak the same love language! Perfect harmony.')
        elif abs(idx1 - idx2) == 1 or abs(idx1 - idx2) == 4:
            match_score = 75
            match_desc = __('Your love languages complement each other well.')
        else:
            match_score = 55
            match_desc = __('Different love languages, but understanding each other can deepen your bond.')

        return {
            'language1': lang1,
            'language2': lang2,
            'match_score': match_score,
            'match_description': match_desc,
        }

    def calculate_compatibility_scores(self, name1, name2, love_percentage):
        """
        Calculate detailed compatibility scores across multiple dimensions using NumPy.
        """
        n1 = name1.lower().replace(' ', '')
        n2 = name2.lower().replace(' ', '')

        # Seed from names for deterministic results
        seed = sum(ord(c) for c in n1 + n2)
        rng = np.random.RandomState(seed)

        # Base scores influenced by love percentage
        base = love_percentage / 100.0

        # Generate dimension scores
        dimensions = {
            __('Emotional'): int(np.clip(rng.normal(base * 85, 10), 20, 98)),
            __('Intellectual'): int(np.clip(rng.normal(base * 80, 12), 20, 98)),
            __('Physical'): int(np.clip(rng.normal(base * 82, 11), 20, 98)),
            __('Spiritual'): int(np.clip(rng.normal(base * 78, 13), 20, 98)),
            __('Communication'): int(np.clip(rng.normal(base * 84, 10), 20, 98)),
            __('Trust'): int(np.clip(rng.normal(base * 86, 9), 20, 98)),
        }

        return dimensions

    def calculate_age_compatibility(self, age1_str, age2_str):
        """Age gap compatibility analysis using NumPy."""
        try:
            age1 = int(age1_str)
            age2 = int(age2_str)
        except (ValueError, TypeError):
            return None
        if age1 < 1 or age1 > 120 or age2 < 1 or age2 > 120:
            return None

        gap = abs(age1 - age2)
        # Score decreases with larger age gaps
        score = int(np.clip(100 - (gap * 4), 20, 100))

        if gap == 0:
            desc = __('Same age! You share the same generational experiences and milestones.')
        elif gap <= 3:
            desc = __('Only %(gap)d year gap — practically the same generation. Great compatibility!') % {'gap': gap}
        elif gap <= 7:
            desc = __('%(gap)d year gap — a balanced difference that brings fresh perspectives.') % {'gap': gap}
        elif gap <= 15:
            desc = __('%(gap)d year gap — different life stages can bring wisdom and excitement.') % {'gap': gap}
        else:
            desc = __('%(gap)d year gap — a significant difference, but love knows no age boundaries!') % {'gap': gap}

        return {'age1': age1, 'age2': age2, 'gap': gap, 'score': score, 'description': desc}

    def calculate_color_chemistry(self, color1, color2):
        """Color compatibility analysis."""
        c1 = color1 if color1 in self.COLOR_MEANINGS else None
        c2 = color2 if color2 in self.COLOR_MEANINGS else None
        if not c1 or not c2:
            return None

        key = tuple(sorted([c1, c2]))
        score = self.COLOR_COMPAT.get(key, 65)
        info1 = self.COLOR_MEANINGS[c1]
        info2 = self.COLOR_MEANINGS[c2]

        if c1 == c2:
            desc = __('You both love %(color)s! Shared aesthetic taste deepens your bond.') % {'color': c1}
        elif score >= 85:
            desc = __('%(c1)s and %(c2)s create beautiful harmony together — a vibrant pairing!') % {'c1': c1.title(), 'c2': c2.title()}
        elif score >= 70:
            desc = __('%(c1)s meets %(c2)s — complementary energies that balance each other.') % {'c1': c1.title(), 'c2': c2.title()}
        else:
            desc = __('%(c1)s and %(c2)s are contrasting but can create exciting tension!') % {'c1': c1.title(), 'c2': c2.title()}

        return {
            'color1': {'name': c1, 'meaning': info1[0], 'emoji': info1[1], 'hex': info1[2]},
            'color2': {'name': c2, 'meaning': info2[0], 'emoji': info2[1], 'hex': info2[2]},
            'score': score, 'description': desc,
        }

    def calculate_food_pairing(self, food1, food2):
        """Food taste compatibility analysis."""
        f1_info = self.FOOD_CATEGORIES.get(food1)
        f2_info = self.FOOD_CATEGORIES.get(food2)
        if not f1_info or not f2_info:
            # Fallback for unlisted foods
            seed = sum(ord(c) for c in food1 + food2)
            score = (seed % 41) + 50
            return {
                'food1': {'name': food1.title(), 'emoji': '🍽️', 'type': 'unique'},
                'food2': {'name': food2.title(), 'emoji': '🍽️', 'type': 'unique'},
                'score': score,
                'description': __('Both enjoy unique tastes! Exploring food together is a great bonding activity.'),
            }

        cat1, cat2 = f1_info[2], f2_info[2]
        key = tuple(sorted([cat1, cat2]))
        score = self.FOOD_COMPAT.get(key, 65)

        if food1 == food2:
            desc = __('You both love %(food)s! Sharing a meal of your favorite food is pure joy.') % {'food': food1}
            score = 95
        elif score >= 85:
            desc = __('%(f1)s and %(f2)s — your food tastes are a match made in heaven!') % {'f1': food1.title(), 'f2': food2.title()}
        else:
            desc = __('%(f1)s meets %(f2)s — different flavors make dinner dates exciting!') % {'f1': food1.title(), 'f2': food2.title()}

        return {
            'food1': {'name': food1.title(), 'emoji': f1_info[1], 'type': f1_info[0]},
            'food2': {'name': food2.title(), 'emoji': f2_info[1], 'type': f2_info[0]},
            'score': score, 'description': desc,
        }

    def calculate_hobby_match(self, hobby1, hobby2):
        """Hobby compatibility analysis."""
        h1_info = self.HOBBY_CATEGORIES.get(hobby1)
        h2_info = self.HOBBY_CATEGORIES.get(hobby2)

        if hobby1 == hobby2:
            score = 95
            desc = __('You both love %(hobby)s! Shared hobbies create lasting bonds.') % {'hobby': hobby1}
        elif h1_info and h2_info:
            # Similar types get higher scores
            similar_groups = [
                {'reading', 'writing', 'art'}, {'sports', 'hiking', 'dancing'},
                {'gaming', 'movies'}, {'cooking', 'gardening'},
                {'travel', 'photography'}, {'yoga', 'hiking'},
                {'music', 'dancing', 'art'},
            ]
            shared_group = any(hobby1 in g and hobby2 in g for g in similar_groups)
            score = 82 if shared_group else 65
            desc = (__('%(h1)s and %(h2)s complement each other well!') % {'h1': hobby1.title(), 'h2': hobby2.title()}
                    if shared_group else
                    __('%(h1)s and %(h2)s — you can introduce each other to new experiences!') % {'h1': hobby1.title(), 'h2': hobby2.title()})
        else:
            seed = sum(ord(c) for c in hobby1 + hobby2)
            score = (seed % 31) + 55
            desc = __('Diverse interests keep relationships fresh and exciting!')

        return {
            'hobby1': {'name': hobby1.title(), 'emoji': h1_info[1] if h1_info else '🎯', 'type': h1_info[0] if h1_info else 'Unique'},
            'hobby2': {'name': hobby2.title(), 'emoji': h2_info[1] if h2_info else '🎯', 'type': h2_info[0] if h2_info else 'Unique'},
            'score': score, 'description': desc,
        }

    def calculate_personality_match(self, p1, p2):
        """Personality type compatibility."""
        p1_info = self.PERSONALITY_TYPES.get(p1)
        p2_info = self.PERSONALITY_TYPES.get(p2)
        if not p1_info or not p2_info:
            return None

        compat_matrix = {
            ('introvert', 'introvert'): (80, __('Two deep souls creating a cozy, understanding world together.')),
            ('introvert', 'extrovert'): (75, __('Opposites attract! You balance each other beautifully.')),
            ('introvert', 'ambivert'): (85, __('Great balance — the ambivert understands both worlds.')),
            ('introvert', 'romantic'): (82, __('Deep feelings meet quiet depth — a tender connection.')),
            ('introvert', 'practical'): (78, __('Grounded love with comfortable silences.')),
            ('introvert', 'adventurous'): (65, __('Growth happens when comfort zones expand together.')),
            ('introvert', 'creative'): (88, __('Imagination and reflection create something magical.')),
            ('introvert', 'analytical'): (85, __('Two thoughtful minds in perfect harmony.')),
            ('extrovert', 'extrovert'): (82, __('Double the energy, double the fun! Life of the party together.')),
            ('extrovert', 'ambivert'): (88, __('Flexible and energetic — a dynamic duo.')),
            ('extrovert', 'romantic'): (78, __('Grand gestures meet social butterflies!')),
            ('extrovert', 'practical'): (72, __('Action-oriented love that gets things done.')),
            ('extrovert', 'adventurous'): (92, __('An unstoppable adventure team!')),
            ('extrovert', 'creative'): (80, __('Creative expression meets enthusiastic support.')),
            ('extrovert', 'analytical'): (68, __('Different approaches, but great learning opportunities.')),
            ('ambivert', 'ambivert'): (85, __('Perfect adaptability — you read each other effortlessly.')),
            ('ambivert', 'romantic'): (82, __('Flexible love that adapts to romantic moments.')),
            ('ambivert', 'practical'): (80, __('Balanced and reliable — a solid partnership.')),
            ('ambivert', 'adventurous'): (85, __('Ready for anything, anytime!')),
            ('ambivert', 'creative'): (82, __('Inspiring and adaptable connection.')),
            ('ambivert', 'analytical'): (78, __('Mind meets flexibility — a thoughtful pair.')),
            ('romantic', 'romantic'): (90, __('A fairytale love story! Pure magic between you.')),
            ('romantic', 'practical'): (72, __('Dreams meet reality — you complete each other.')),
            ('romantic', 'adventurous'): (85, __('Romantic adventures await!')),
            ('romantic', 'creative'): (92, __('A beautiful canvas of love and creativity.')),
            ('romantic', 'analytical'): (65, __('Heart meets mind — a fascinating dynamic.')),
            ('practical', 'practical'): (80, __('Reliable, steady, and built to last.')),
            ('practical', 'adventurous'): (70, __('Planning meets spontaneity!')),
            ('practical', 'creative'): (72, __('Structure meets imagination — balance!')),
            ('practical', 'analytical'): (88, __('Two pragmatic minds working in harmony.')),
            ('adventurous', 'adventurous'): (90, __('Non-stop excitement and exploration together!')),
            ('adventurous', 'creative'): (85, __('Creative adventures and wild ideas!')),
            ('adventurous', 'analytical'): (68, __('Spontaneity meets strategy.')),
            ('creative', 'creative'): (88, __('An explosion of art, ideas, and passion!')),
            ('creative', 'analytical'): (75, __('Logic meets imagination — innovation blooms.')),
            ('analytical', 'analytical'): (82, __('Two brilliant minds solving life together.')),
        }

        key = tuple(sorted([p1, p2]))
        result = compat_matrix.get(key, (70, __('A unique pairing with room to grow!')))

        return {
            'personality1': {'type': p1_info[0], 'emoji': p1_info[1], 'desc': p1_info[2]},
            'personality2': {'type': p2_info[0], 'emoji': p2_info[1], 'desc': p2_info[2]},
            'score': result[0], 'description': result[1],
        }

    def generate_relationship_tips(self, love_pct, flames, compat_scores):
        """Generate personalized relationship tips."""
        tips = []
        if love_pct < 40:
            tips.append(__('Focus on building a strong friendship first — it is the foundation of all great relationships.'))
            tips.append(__('Try new experiences together to create shared memories and discover common ground.'))
        elif love_pct < 60:
            tips.append(__('Communication is your superpower — keep talking openly and honestly.'))
            tips.append(__('Plan regular date nights to nurture your growing connection.'))
        elif love_pct < 80:
            tips.append(__('Keep the spark alive with surprise gestures, big or small.'))
            tips.append(__('Support each other\'s individual goals while growing together.'))
        else:
            tips.append(__('You have something special — protect it by never taking each other for granted.'))
            tips.append(__('Continue to grow individually while celebrating your amazing bond.'))

        # FLAMES-based tips
        flames_tips = {
            'F': __('Strengthen your friendship by being each other\'s biggest cheerleader.'),
            'L': __('Express your love daily — small "I love you"s mean the world.'),
            'A': __('Show affection through gentle touches, kind words, and thoughtful gestures.'),
            'M': __('Discuss your future together — shared dreams build strong marriages.'),
            'E': __('Turn friction into fuel — debate respectfully and learn from differences.'),
            'S': __('Add more romance to balance the comfortable familiarity you share.'),
        }
        tips.append(flames_tips.get(flames, __('Be authentic and true to yourselves.')))

        # Weakest compatibility dimension tip
        if compat_scores:
            weakest = min(compat_scores, key=compat_scores.get)
            dim_tips = {
                'Emotional': __('Work on emotional vulnerability — share your true feelings more.'),
                'Intellectual': __('Engage in intellectual activities together — read, debate, explore ideas.'),
                'Physical': __('Physical connection matters — prioritize quality time for closeness.'),
                'Spiritual': __('Explore your spiritual side together — meditation, nature, or shared values.'),
                'Communication': __('Practice active listening — truly hear each other without judgment.'),
                'Trust': __('Build trust through consistency, honesty, and keeping your promises.'),
            }
            tips.append(__('Your %(dim)s connection could use a boost: %(tip)s') % {'dim': weakest.lower(), 'tip': dim_tips.get(weakest, '')})

        return tips[:5]

    def suggest_ideal_date(self, name1, name2, food1, food2, hobby1, hobby2):
        """Suggest ideal date ideas based on inputs."""
        dates = []
        seed = sum(ord(c) for c in (name1 + name2).lower())

        if food1 or food2:
            food = food1 or food2
            dates.append(__('🍽️ Cook %(food)s together at home for a cozy night in.') % {'food': food.title()})
            dates.append(__('🍷 Go on a culinary adventure — try a new restaurant you\'ve never been to.'))

        if hobby1 or hobby2:
            h = hobby1 or hobby2
            hobby_dates = {
                'reading': __('📚 Visit a bookstore café and read together over coffee.'),
                'gaming': __('🎮 Have a cozy game night with snacks and friendly competition.'),
                'cooking': __('👨\u200d🍳 Take a cooking class together and learn a new cuisine.'),
                'sports': __('⚽ Play a sport together or cheer for your favorite team.'),
                'music': __('🎵 Go to a live concert or make a playlist for each other.'),
                'travel': __('✈️ Plan a surprise weekend getaway to somewhere new.'),
                'art': __('🎨 Visit an art gallery or try a paint-and-sip night.'),
                'movies': __('🎬 Build a blanket fort and have a movie marathon.'),
                'hiking': __('🥾 Go on a scenic hike and watch the sunset together.'),
                'photography': __('📷 Do a photo walk exploring hidden gems in your city.'),
            }
            if h in hobby_dates:
                dates.append(hobby_dates[h])

        # Always add some universal date ideas
        universal = [
            __('🌅 Watch the sunrise or sunset together in a beautiful spot.'),
            __('💌 Write love letters to each other and read them aloud.'),
            __('🌟 Stargaze on a clear night with hot chocolate.'),
            __('� Visit a local fair, carnival, or festival.'),
            __('🧩 Solve an escape room together as a team.'),
        ]
        rng = np.random.RandomState(seed)
        chosen = rng.choice(len(universal), size=min(2, len(universal)), replace=False)
        for i in chosen:
            dates.append(universal[i])

        return dates[:5]

    # ─────────────────────────────────────────────
    # Premium Professional Features
    # ─────────────────────────────────────────────

    def generate_love_story(self, name1, name2, love_pct, flames, category):
        """Generate a personalized love story narrative."""
        seed = sum(ord(c) for c in (name1 + name2).lower())
        rng = np.random.RandomState(seed)

        # Story arcs based on compatibility
        if love_pct >= 80:
            openings = [
                __('It was written in the stars — the moment %(n1)s and %(n2)s met, the universe held its breath.') % {'n1': name1, 'n2': name2},
                __('Some love stories are ordinary. %(n1)s and %(n2)s\'s is a once-in-a-lifetime fairy tale.') % {'n1': name1, 'n2': name2},
                __('When %(n1)s\'s eyes met %(n2)s\'s across the room, time itself seemed to stop.') % {'n1': name1, 'n2': name2},
            ]
            middles = [
                __('Their connection was instant and undeniable — like two puzzle pieces finally finding each other.'),
                __('Every conversation flowed like poetry, every silence comfortable as a warm embrace.'),
                __('From the very first laugh they shared, they knew this was something extraordinary.'),
            ]
            endings = [
                __('Theirs is the kind of love that poets write about and dreamers dream of. A soulmate connection that will last forever. 💕'),
                __('Together they built a love so strong that even the stars envied their connection. This is forever. ✨'),
                __('And so their love story continues — each chapter more beautiful than the last, with endless pages yet to be written. 💖'),
            ]
        elif love_pct >= 60:
            openings = [
                __('%(n1)s and %(n2)s — two hearts drawn together by an invisible thread of destiny.') % {'n1': name1, 'n2': name2},
                __('The story of %(n1)s and %(n2)s is one of beautiful discovery and growing affection.') % {'n1': name1, 'n2': name2},
                __('When %(n1)s first crossed paths with %(n2)s, a quiet spark began to glow.') % {'n1': name1, 'n2': name2},
            ]
            middles = [
                __('Day by day, their bond strengthened — each shared moment adding another brushstroke to their masterpiece.'),
                __('They discovered that their differences complemented each other perfectly, creating a beautiful harmony.'),
                __('Through laughter and deep conversations, they wove the golden threads of a meaningful connection.'),
            ]
            endings = [
                __('With patience and genuine care, their love blossomed into something truly remarkable. The best is yet to come! 🌷'),
                __('Their journey together proves that great love is not found — it is built, one beautiful moment at a time. 💛'),
                __('The chapters ahead are filled with promise, and their love grows stronger with every passing day. 🌟'),
            ]
        elif love_pct >= 40:
            openings = [
                __('%(n1)s and %(n2)s — an unexpected pair with a surprising undercurrent of attraction.') % {'n1': name1, 'n2': name2},
                __('The universe works in mysterious ways, and the connection between %(n1)s and %(n2)s proves it.') % {'n1': name1, 'n2': name2},
                __('Like a melody just beginning to play, the story of %(n1)s and %(n2)s holds beautiful potential.') % {'n1': name1, 'n2': name2},
            ]
            middles = [
                __('Though their worlds seemed different, they found fascinating common ground in the most unexpected places.'),
                __('Each discovery about the other brought a smile and a new reason to stay curious.'),
                __('The spark between them is gentle but persistent — a flame that refuses to go out.'),
            ]
            endings = [
                __('With the right effort and open hearts, this story could become one of the greatest love stories ever told. 🌱'),
                __('Every epic love story started somewhere. This could be the beginning of something extraordinary. 💫'),
                __('The potential is tremendous — all it takes is courage, communication, and a willingness to grow together. 🦋'),
            ]
        else:
            openings = [
                __('%(n1)s and %(n2)s — proof that the most fascinating stories often have unexpected beginnings.') % {'n1': name1, 'n2': name2},
                __('Every challenge is an opportunity in disguise, and the dynamic between %(n1)s and %(n2)s is full of potential.') % {'n1': name1, 'n2': name2},
                __('The universe paired %(n1)s and %(n2)s for a reason — perhaps the most important lessons come from unlikely connections.') % {'n1': name1, 'n2': name2},
            ]
            middles = [
                __('Their differences created a dynamic tension — the kind that, when embraced, leads to profound personal growth.'),
                __('They challenged each other in ways no one else could, pushing each other toward their best selves.'),
                __('Not every connection is smooth, but the rough edges are where the most interesting stories are carved.'),
            ]
            endings = [
                __('The road ahead may not be easy, but the journey itself holds incredible value and transformation. 🌅'),
                __('Sometimes the most unexpected connections teach us the most about ourselves. Every relationship is a gift. 🎁'),
                __('Whether as friends, partners, or simply two souls who crossed paths — this meeting was meant to be. ✨'),
            ]

        opening = openings[rng.randint(len(openings))]
        middle = middles[rng.randint(len(middles))]
        ending = endings[rng.randint(len(endings))]

        # Flames-based story element
        flames_elements = {
            'F': __('Their friendship is the bedrock — a sanctuary of trust and genuine care.'),
            'L': __('A deep, passionate love burns between them — the kind songs are written about.'),
            'A': __('Warm affection wraps around them like a soft blanket on a cold night.'),
            'M': __('The universe hints at wedding bells — a bond destined for forever.'),
            'E': __('A passionate intensity defines them — fiery debates lead to deeper understanding.'),
            'S': __('A comfortable, sibling-like familiarity makes every moment feel like home.'),
        }
        flames_element = flames_elements.get(flames, '')

        return {
            'title': __('The Love Story of %(n1)s & %(n2)s') % {'n1': name1, 'n2': name2},
            'story': f'{opening} {flames_element} {middle} {ending}',
            'genre': category,
        }

    def generate_couple_nickname(self, name1, name2):
        """Generate creative couple nicknames using name blending algorithms."""
        n1 = name1.strip()
        n2 = name2.strip()
        n1l = n1.lower()
        n2l = n2.lower()
        nicknames = []

        # 1. Classic blend: first half of name1 + second half of name2
        mid1 = max(1, len(n1) // 2)
        mid2 = max(1, len(n2) // 2)
        nicknames.append(n1[:mid1] + n2[mid2:])
        nicknames.append(n2[:mid2] + n1[mid1:])

        # 2. First letter combo
        if len(n1) >= 2 and len(n2) >= 2:
            nicknames.append(n1[:2] + n2[:2])

        # 3. Ship name (first syllable-ish of each)
        vowels = set('aeiou')
        def first_syllable(name):
            name = name.lower()
            for i in range(1, len(name)):
                if name[i] in vowels and i > 0:
                    return name[:i+1]
            return name[:max(2, len(name)//2)]

        syl1, syl2 = first_syllable(n1), first_syllable(n2)
        nicknames.append((syl1 + syl2).title())
        nicknames.append((syl2 + syl1).title())

        # 4. Initials with heart
        nicknames.append(f'{n1[0].upper()} ❤ {n2[0].upper()}')

        # 5. "The [Combined]s" style
        if n1l[-1] == n2l[0]:
            nicknames.append('The ' + (n1 + n2[1:]).title() + 's')

        # Remove duplicates, limit to 5
        seen = set()
        unique = []
        for nn in nicknames:
            nn_clean = nn.strip().title() if '❤' not in nn else nn
            if nn_clean.lower() not in seen and len(nn_clean) > 1:
                seen.add(nn_clean.lower())
                unique.append(nn_clean)
        return unique[:5]

    def find_celebrity_match(self, love_pct, flames):
        """Find the closest celebrity couple match."""
        celeb_couples = [
            {'names': __('Beyoncé & Jay-Z'), 'score': 92, 'emoji': '👑', 'desc': __('Power couple goals! Music, business, and an unbreakable bond.')},
            {'names': __('Barack & Michelle Obama'), 'score': 95, 'emoji': '🏛️', 'desc': __('Partnership, mutual respect, and changing the world together.')},
            {'names': __('David & Victoria Beckham'), 'score': 88, 'emoji': '⚽', 'desc': __('Style, sports, and decades of devoted partnership.')},
            {'names': __('Ryan Reynolds & Blake Lively'), 'score': 90, 'emoji': '😂', 'desc': __('Humor, charm, and playful love that never gets old.')},
            {'names': __('John Legend & Chrissy Teigen'), 'score': 87, 'emoji': '🎹', 'desc': __('Artistic souls with passion and openness.')},
            {'names': __('Prince William & Kate'), 'score': 85, 'emoji': '👸', 'desc': __('Royal grace, patience, and a fairy tale love story.')},
            {'names': __('Tom Hanks & Rita Wilson'), 'score': 94, 'emoji': '🎬', 'desc': __('Hollywood\'s golden couple — 35+ years of love.')},
            {'names': __('Ashton & Mila'), 'score': 82, 'emoji': '📺', 'desc': __('From co-stars to soulmates — a love that grew over time.')},
            {'names': __('Shah Rukh & Gauri Khan'), 'score': 91, 'emoji': '🎭', 'desc': __('Bollywood royalty — love, loyalty, and legacy.')},
            {'names': __('Oprah & Stedman'), 'score': 80, 'emoji': '📺', 'desc': __('Independent minds, unwavering support, unconventional love.')},
            {'names': __('Will Smith & Jada'), 'score': 75, 'emoji': '🌊', 'desc': __('Complex, evolving, and deeply honest partnership.')},
            {'names': __('Kurt Russell & Goldie Hawn'), 'score': 89, 'emoji': '🌟', 'desc': __('40+ years together, never married — love on their own terms.')},
            {'names': __('Romeo & Juliet'), 'score': 99, 'emoji': '📖', 'desc': __('The original star-crossed lovers — passionate and legendary.')},
            {'names': __('Cleopatra & Antony'), 'score': 78, 'emoji': '⚔️', 'desc': __('A love that shook empires and rewrote history.')},
        ]

        # Find closest match by score
        scores = np.array([c['score'] for c in celeb_couples])
        diffs = np.abs(scores - love_pct)
        idx = int(np.argmin(diffs))
        match = celeb_couples[idx]

        return {
            'couple': match['names'],
            'emoji': match['emoji'],
            'score': match['score'],
            'description': match['desc'],
            'similarity': int(100 - abs(match['score'] - love_pct)),
        }

    def generate_relationship_timeline(self, name1, name2, love_pct):
        """Generate predicted relationship milestones."""
        seed = sum(ord(c) for c in (name1 + name2).lower())
        rng = np.random.RandomState(seed)

        base_speed = love_pct / 100.0  # Higher love = faster milestones

        milestones = []
        if love_pct >= 30:
            milestones.append({
                'icon': '💬', 'title': __('First Deep Conversation'),
                'time': f'{rng.randint(1, 4)} ' + str(__('weeks')),
                'desc': __('The moment you move past small talk and discover true depth.')
            })
        if love_pct >= 35:
            milestones.append({
                'icon': '😂', 'title': __('First Inside Joke'),
                'time': f'{rng.randint(2, 6)} ' + str(__('weeks')),
                'desc': __('A shared laugh that only you two understand — priceless.')
            })
        if love_pct >= 40:
            milestones.append({
                'icon': '🎉', 'title': __('First Adventure Together'),
                'time': f'{rng.randint(1, 3)} ' + str(__('months')),
                'desc': __('An experience that bonds you and creates lasting memories.')
            })
        if love_pct >= 50:
            milestones.append({
                'icon': '💕', 'title': __('Saying "I Love You"'),
                'time': f'{rng.randint(2, 8)} ' + str(__('months')),
                'desc': __('Three words that change everything.')
            })
        if love_pct >= 55:
            milestones.append({
                'icon': '👨‍👩‍👧', 'title': __('Meeting Each Other\'s Families'),
                'time': f'{rng.randint(3, 10)} ' + str(__('months')),
                'desc': __('A big step that shows this is getting serious.')
            })
        if love_pct >= 60:
            milestones.append({
                'icon': '🏠', 'title': __('Moving In Together'),
                'time': f'{max(1, int(rng.normal(2, 0.5)))} ' + str(__('years')),
                'desc': __('Sharing a space, sharing a life — the real test begins.')
            })
        if love_pct >= 70:
            milestones.append({
                'icon': '🐕', 'title': __('Getting a Pet Together'),
                'time': f'{rng.randint(1, 3)} ' + str(__('years')),
                'desc': __('A furry addition to your growing love story.')
            })
        if love_pct >= 75:
            milestones.append({
                'icon': '💍', 'title': __('The Proposal'),
                'time': f'{max(1, int(rng.normal(3, 1)))} ' + str(__('years')),
                'desc': __('The question that takes your breath away.')
            })
        if love_pct >= 85:
            milestones.append({
                'icon': '👶', 'title': __('Starting a Family'),
                'time': f'{rng.randint(3, 7)} ' + str(__('years')),
                'desc': __('Tiny feet and sleepless nights — your greatest adventure.')
            })
        if love_pct >= 90:
            milestones.append({
                'icon': '🎊', 'title': __('Golden Anniversary'),
                'time': '50 ' + str(__('years')),
                'desc': __('Half a century of love, laughter, and growing old together.')
            })

        return milestones[:8]

    def generate_love_recipe(self, name1, name2, love_pct, compat_scores):
        """Generate a metaphorical love recipe."""
        seed = sum(ord(c) for c in (name1 + name2).lower())
        rng = np.random.RandomState(seed)

        # Ingredients based on compatibility scores
        ingredients = []
        for dim, score in compat_scores.items():
            if score >= 80:
                amount = str(__('A generous cup'))
            elif score >= 60:
                amount = str(__('Two tablespoons'))
            elif score >= 40:
                amount = str(__('A teaspoon'))
            else:
                amount = str(__('A pinch'))

            ingredient_map = {
                'Emotional': __('%(amount)s of emotional depth 💧') % {'amount': amount},
                'Intellectual': __('%(amount)s of intellectual spark ⚡') % {'amount': amount},
                'Physical': __('%(amount)s of physical chemistry 🔥') % {'amount': amount},
                'Spiritual': __('%(amount)s of spiritual connection 🌌') % {'amount': amount},
                'Communication': __('%(amount)s of open communication 💬') % {'amount': amount},
                'Trust': __('%(amount)s of unwavering trust 🛡️') % {'amount': amount},
            }
            ingredients.append(ingredient_map.get(dim, __('%(amount)s of %(dim)s') % {'amount': amount, 'dim': dim.lower()}))

        # Special ingredients based on love percentage
        if love_pct >= 80:
            ingredients.append(__('A whole heart of unconditional love 💖'))
            ingredients.append(__('A lifetime of shared dreams ✨'))
        elif love_pct >= 60:
            ingredients.append(__('Three cups of patience and understanding 🍯'))
        elif love_pct >= 40:
            ingredients.append(__('A dash of adventure and curiosity 🌶️'))
        else:
            ingredients.append(__('Extra effort and open-mindedness 🌱'))

        # Cooking instructions
        instructions = [
            __('1. Mix all ingredients with tender care and genuine intention.'),
            __('2. Let simmer over warm conversations and shared silences.'),
            __('3. Stir in laughter generously — it\'s the secret ingredient.'),
            __('4. Season with surprise gestures and "just because" moments.'),
            __('5. Bake at %(pct)d° of love until golden and irresistible.') % {'pct': love_pct},
            __('6. Serve daily with a side of gratitude and appreciation.'),
        ]

        dish_names = [
            __('%(n1)s & %(n2)s\'s Love Soufflé') % {'n1': name1, 'n2': name2},
            __('The %(n1)s-%(n2)s Heart Cake') % {'n1': name1, 'n2': name2},
            __('Passion Pie à la %(n1)s & %(n2)s') % {'n1': name1, 'n2': name2},
            __('%(n1)s & %(n2)s\'s Romance Risotto') % {'n1': name1, 'n2': name2},
            __('The Perfect %(n1)s-%(n2)s Love Blend') % {'n1': name1, 'n2': name2},
        ]

        return {
            'dish_name': dish_names[rng.randint(len(dish_names))],
            'ingredients': ingredients,
            'instructions': instructions,
            'serving': __('Serves 2 hearts, for a lifetime 💞'),
        }

    def get_emotional_weather(self, love_pct, compat_scores):
        """Get an emotional weather forecast for the relationship."""
        avg_compat = np.mean(list(compat_scores.values()))
        combined = (love_pct + avg_compat) / 2

        if combined >= 85:
            return {
                'icon': '☀️', 'condition': __('Radiant Sunshine'),
                'temp': f'{int(combined)}°', 'color': '#f59e0b',
                'forecast': __('Clear skies ahead! Your love radiates warmth and joy to everyone around you.'),
                'advice': __('Perfect weather for a romantic adventure together!'),
            }
        elif combined >= 70:
            return {
                'icon': '🌤️', 'condition': __('Partly Cloudy with Bursts of Sun'),
                'temp': f'{int(combined)}°', 'color': '#3b82f6',
                'forecast': __('Mostly bright with occasional clouds — nothing a warm hug can\'t fix!'),
                'advice': __('Great conditions for building something beautiful together.'),
            }
        elif combined >= 55:
            return {
                'icon': '🌈', 'condition': __('Rainbow After Rain'),
                'temp': f'{int(combined)}°', 'color': '#8b5cf6',
                'forecast': __('There may be some showers, but rainbows are forming. Hope is on the horizon!'),
                'advice': __('Every storm passes. Focus on the colors that emerge.'),
            }
        elif combined >= 40:
            return {
                'icon': '🌧️', 'condition': __('Light Rain with Promise'),
                'temp': f'{int(combined)}°', 'color': '#6b7280',
                'forecast': __('A drizzle of challenges, but rain makes things grow. Your love is no exception.'),
                'advice': __('Grab an umbrella together — shared challenges strengthen bonds.'),
            }
        else:
            return {
                'icon': '🌪️', 'condition': __('Stormy but Electric'),
                'temp': f'{int(combined)}°', 'color': '#64748b',
                'forecast': __('The air is charged with intensity. Storms bring transformation and new beginnings.'),
                'advice': __('Find shelter in honest communication and mutual respect.'),
            }

    def get_love_category(self, percentage):
        """Determine love category and color using NumPy for efficient comparison."""
        pct = np.array([percentage])
        thresholds = np.array([20, 40, 60, 80])
        idx = int(np.searchsorted(thresholds, pct)[0])

        categories = [
            (__('Not Likely'), 'red', __('It might take some effort, but every great love story has a beginning!')),
            (__('Could Work'), 'yellow', __('There is potential here. Communication and patience are key.')),
            (__('Good Match'), 'blue', __('You have a solid foundation for a beautiful relationship.')),
            (__('Great Match'), 'purple', __('The chemistry between you is undeniable! A strong connection awaits.')),
            (__('Soulmates'), 'pink', __('An extraordinary bond! You are truly made for each other. 💕')),
        ]
        cat = categories[idx]
        return cat[0], cat[1], cat[2]

    def calculate_scale_position(self, percentage):
        """Calculate love scale position (0-100%)."""
        return min(100.0, max(0.0, float(percentage)))

    def get_color_info(self, category_color):
        """Get color information for the category (backend-controlled)."""
        color_map = {
            'red': {
                'hex': '#ef4444',
                'rgb': 'rgb(239, 68, 68)',
                'gradient_from': '#ef4444',
                'gradient_to': '#dc2626',
                'tailwind_classes': 'bg-red-100 text-red-800 border-red-300',
            },
            'yellow': {
                'hex': '#f59e0b',
                'rgb': 'rgb(245, 158, 11)',
                'gradient_from': '#f59e0b',
                'gradient_to': '#d97706',
                'tailwind_classes': 'bg-yellow-100 text-yellow-800 border-yellow-300',
            },
            'blue': {
                'hex': '#3b82f6',
                'rgb': 'rgb(59, 130, 246)',
                'gradient_from': '#3b82f6',
                'gradient_to': '#2563eb',
                'tailwind_classes': 'bg-blue-100 text-blue-800 border-blue-300',
            },
            'purple': {
                'hex': '#8b5cf6',
                'rgb': 'rgb(139, 92, 246)',
                'gradient_from': '#8b5cf6',
                'gradient_to': '#7c3aed',
                'tailwind_classes': 'bg-purple-100 text-purple-800 border-purple-300',
            },
            'pink': {
                'hex': '#ec4899',
                'rgb': 'rgb(236, 72, 153)',
                'gradient_from': '#ec4899',
                'gradient_to': '#db2777',
                'tailwind_classes': 'bg-pink-100 text-pink-800 border-pink-300',
            },
        }
        return color_map.get(category_color, color_map['pink'])

    def prepare_chart_data(self, love_percentage, category_color, compatibility_scores, flames_result):
        """Prepare all chart data in backend (backend-controlled)."""
        color_info = self.get_color_info(category_color)

        # 1. Love Gauge Chart (Doughnut)
        gauge_chart = {
            'type': 'doughnut',
            'data': {
                'labels': [__('Love %'), __('Remaining')],
                'datasets': [{
                    'data': [love_percentage, 100 - love_percentage],
                    'backgroundColor': [color_info['hex'], '#e5e7eb'],
                    'borderWidth': 0,
                    'cutout': '75%',
                }],
            },
            'center_text': {
                'value': love_percentage,
                'label': __('Love %'),
                'color': color_info['hex'],
            },
        }

        # 2. Compatibility Radar Chart
        dimensions = list(compatibility_scores.keys())
        scores = list(compatibility_scores.values())
        radar_chart = {
            'type': 'radar',
            'data': {
                'labels': dimensions,
                'datasets': [{
                    'label': __('Compatibility'),
                    'data': scores,
                    'backgroundColor': f"{color_info['hex']}33",
                    'borderColor': color_info['hex'],
                    'borderWidth': 2,
                    'pointBackgroundColor': color_info['hex'],
                    'pointBorderColor': '#fff',
                    'pointBorderWidth': 2,
                    'pointRadius': 5,
                }],
            },
        }

        # 3. FLAMES Bar Chart
        flames_letters = list('FLAMES')
        flames_labels = [self.FLAMES_CATEGORIES[l][0] for l in flames_letters]
        flames_colors_list = [self.FLAMES_CATEGORIES[l][2] for l in flames_letters]
        flames_data = [100 if l == flames_result else 20 for l in flames_letters]

        flames_chart = {
            'type': 'bar',
            'data': {
                'labels': flames_labels,
                'datasets': [{
                    'label': __('FLAMES Result'),
                    'data': flames_data,
                    'backgroundColor': [
                        c if l == flames_result else '#e5e7eb'
                        for l, c in zip(flames_letters, flames_colors_list)
                    ],
                    'borderColor': flames_colors_list,
                    'borderWidth': 2,
                    'borderRadius': 8,
                }],
            },
            'result_letter': flames_result,
        }

        return {
            'gauge_chart': gauge_chart,
            'radar_chart': radar_chart,
            'flames_chart': flames_chart,
        }
