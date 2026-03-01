from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
import json
import math
import string
import secrets


@method_decorator(ensure_csrf_cookie, name='dispatch')
class PasswordGenerator(View):
    """
    Password Generator — random, passphrase, and PIN.

    Generation types
        • random      → random characters (upper, lower, digits, symbols)
        • passphrase  → N random words separated by a delimiter
        • pin         → numeric PIN of N digits
    """
    template_name = 'other_calculators/password_generator.html'

    WORD_LIST = [
        'apple', 'brave', 'cloud', 'dance', 'eagle', 'flame', 'grape', 'heart',
        'ivory', 'jewel', 'kings', 'lemon', 'maple', 'night', 'ocean', 'pearl',
        'queen', 'river', 'stone', 'tiger', 'unity', 'vivid', 'water', 'xenon',
        'youth', 'zebra', 'amber', 'blaze', 'chase', 'delta', 'ember', 'frost',
        'green', 'honey', 'index', 'joker', 'knife', 'lunar', 'mango', 'noble',
        'olive', 'piano', 'quest', 'royal', 'solar', 'table', 'ultra', 'viola',
        'whirl', 'pixel', 'yacht', 'zephyr', 'alpha', 'brisk', 'coral', 'drift',
        'epoch', 'flora', 'globe', 'haven', 'irony', 'jazzy', 'karma', 'lilac',
        'mocha', 'nexus', 'oasis', 'plume', 'quilt', 'ridge', 'spark', 'torch',
        'umbra', 'venom', 'wages', 'oxide', 'yucca', 'zones', 'atlas', 'bloom',
        'cider', 'dusky', 'elfin', 'fjord', 'grain', 'haste', 'ivory', 'junco',
        'knack', 'lodge', 'marsh', 'north', 'orbit', 'prism', 'quota', 'reign',
        'sable', 'thorn', 'usher', 'valve', 'wrist', 'proxy', 'yearn', 'zonal',
    ]

    # ── GET ───────────────────────────────────────────────────────────
    def get(self, request):
        return render(request, self.template_name, {
            'calculator_name': _('Password Generator'),
        })

    # ── POST ─────────────────────────────────────────────────────────
    def post(self, request):
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            gt = data.get('gen_type', 'random')
            dispatch = {
                'random':     self._gen_random,
                'passphrase': self._gen_passphrase,
                'pin':        self._gen_pin,
            }
            handler = dispatch.get(gt)
            if not handler:
                return self._err(_('Invalid generation type.'))
            return handler(data)
        except json.JSONDecodeError:
            return self._err(_('Invalid JSON data.'))
        except (ValueError, TypeError) as e:
            return self._err(str(e))
        except Exception:
            return self._err(_('An error occurred during generation.'), 500)

    # ── helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _err(msg, status=400):
        return JsonResponse({'success': False, 'error': str(msg)}, status=status)

    @staticmethod
    def _strength(entropy):
        if entropy >= 128:
            return str(_('Very Strong')), 'very_strong'
        elif entropy >= 80:
            return str(_('Strong')), 'strong'
        elif entropy >= 60:
            return str(_('Good')), 'good'
        elif entropy >= 40:
            return str(_('Fair')), 'fair'
        else:
            return str(_('Weak')), 'weak'

    @staticmethod
    def _crack_time(entropy):
        """Rough brute-force crack time at 10 billion guesses/sec."""
        combos = 2 ** entropy
        seconds = combos / 1e10
        if seconds < 1:
            return str(_('Instantly'))
        if seconds < 60:
            return f'{seconds:.0f} {_("seconds")}'
        if seconds < 3600:
            return f'{seconds / 60:.0f} {_("minutes")}'
        if seconds < 86400:
            return f'{seconds / 3600:.0f} {_("hours")}'
        if seconds < 31536000:
            return f'{seconds / 86400:.0f} {_("days")}'
        years = seconds / 31536000
        if years < 1e6:
            return f'{years:,.0f} {_("years")}'
        if years < 1e9:
            return f'{years / 1e6:,.1f} {_("million years")}'
        return f'{years / 1e9:,.1f} {_("billion years")}'

    # ── 1) RANDOM PASSWORD ───────────────────────────────────────────
    def _gen_random(self, data):
        length = int(data.get('length', 16))
        if length < 4 or length > 128:
            raise ValueError(str(_('Length must be between 4 and 128.')))

        use_upper = data.get('uppercase', True)
        use_lower = data.get('lowercase', True)
        use_digits = data.get('digits', True)
        use_symbols = data.get('symbols', True)
        exclude = data.get('exclude_chars', '')

        charset = ''
        pools = []
        if use_upper:
            pool = string.ascii_uppercase
            charset += pool
            pools.append(('uppercase', pool))
        if use_lower:
            pool = string.ascii_lowercase
            charset += pool
            pools.append(('lowercase', pool))
        if use_digits:
            pool = string.digits
            charset += pool
            pools.append(('digits', pool))
        if use_symbols:
            pool = '!@#$%^&*()-_=+[]{}|;:,.<>?'
            charset += pool
            pools.append(('symbols', pool))

        if not charset:
            raise ValueError(str(_('At least one character type must be selected.')))

        # Remove excluded characters
        if exclude:
            charset = ''.join(c for c in charset if c not in exclude)
            if len(charset) < 2:
                raise ValueError(str(_('Too many characters excluded. Not enough characters to generate password.')))

        pool_size = len(charset)

        # Ensure at least one character from each selected pool
        password_chars = []
        for pname, pool in pools:
            filtered = ''.join(c for c in pool if c not in exclude) if exclude else pool
            if filtered:
                password_chars.append(secrets.choice(filtered))

        # Fill the rest
        remaining = length - len(password_chars)
        if remaining > 0:
            password_chars.extend(secrets.choice(charset) for _ in range(remaining))

        # Shuffle
        pw_list = list(password_chars)
        secrets.SystemRandom().shuffle(pw_list)
        password = ''.join(pw_list)

        entropy = round(length * math.log2(pool_size), 1) if pool_size > 0 else 0
        strength_label, strength_key = self._strength(entropy)
        crack = self._crack_time(entropy)

        char_types = []
        if use_upper:
            char_types.append(str(_('Uppercase (A-Z)')))
        if use_lower:
            char_types.append(str(_('Lowercase (a-z)')))
        if use_digits:
            char_types.append(str(_('Digits (0-9)')))
        if use_symbols:
            char_types.append(str(_('Symbols (!@#...)')))

        steps = [
            str(_('Step 1: Character set')),
            f'  • {", ".join(char_types)}',
            f'  • {_("Pool size")} = {pool_size} {_("characters")}',
        ]
        if exclude:
            steps.append(f'  • {_("Excluded")}: {exclude}')
        steps += [
            '', str(_('Step 2: Generate {n} random characters').format(n=length)),
            f'  • {_("One from each pool guaranteed")}',
            f'  • {_("Remaining filled from full charset")}',
            '', str(_('Step 3: Calculate entropy')),
            f'  log₂({pool_size}) × {length} = {entropy} {_("bits")}',
            '', str(_('Step 4: Strength assessment')),
            f'  • {strength_label}',
            f'  • {_("Crack time")}: {crack}',
            '', str(_('Result: Password generated ({n} chars, {e} bits)').format(n=length, e=entropy)),
        ]

        return JsonResponse({
            'success': True, 'gen_type': 'random',
            'result': password,
            'result_label': str(_('Random Password')),
            'password': password, 'length': length,
            'pool_size': pool_size, 'entropy': entropy,
            'strength': strength_label, 'strength_key': strength_key,
            'crack_time': crack,
            'formula': f'{length} {_("chars")} × log₂({pool_size}) = {entropy} {_("bits")}',
            'step_by_step': steps,
            'chart_data': self._strength_chart(entropy),
        })

    # ── 2) PASSPHRASE ────────────────────────────────────────────────
    def _gen_passphrase(self, data):
        num_words = int(data.get('num_words', 4))
        if num_words < 2 or num_words > 12:
            raise ValueError(str(_('Number of words must be between 2 and 12.')))

        delimiter = data.get('delimiter', '-')
        if len(delimiter) > 3:
            raise ValueError(str(_('Delimiter must be 3 characters or fewer.')))

        capitalize = data.get('capitalize', False)
        add_number = data.get('add_number', False)

        words = [secrets.choice(self.WORD_LIST) for _ in range(num_words)]
        if capitalize:
            words = [w.capitalize() for w in words]

        if add_number:
            words.append(str(secrets.randbelow(100)))

        passphrase = delimiter.join(words)

        # Entropy: log2(word_list_size) per word
        wl_size = len(self.WORD_LIST)
        word_entropy = num_words * math.log2(wl_size)
        if add_number:
            word_entropy += math.log2(100)
        entropy = round(word_entropy, 1)
        strength_label, strength_key = self._strength(entropy)
        crack = self._crack_time(entropy)

        steps = [
            str(_('Step 1: Configuration')),
            f'  • {num_words} {_("words")} {_("from a list of")} {wl_size}',
            f'  • {_("Delimiter")}: "{delimiter}"',
            f'  • {_("Capitalize")}: {"✓" if capitalize else "✗"}',
            f'  • {_("Add number")}: {"✓" if add_number else "✗"}',
            '', str(_('Step 2: Select random words')),
        ]
        for i, w in enumerate(words, 1):
            steps.append(f'  • #{i}: {w}')
        steps += [
            '', str(_('Step 3: Calculate entropy')),
            f'  {num_words} × log₂({wl_size}) = {round(num_words * math.log2(wl_size), 1)} {_("bits")}',
        ]
        if add_number:
            steps.append(f'  + log₂(100) = 6.6 {_("bits")}')
        steps += [
            f'  {_("Total")} = {entropy} {_("bits")}',
            '', str(_('Step 4: Strength assessment')),
            f'  • {strength_label}',
            f'  • {_("Crack time")}: {crack}',
            '', str(_('Result: Passphrase generated ({n} words, {e} bits)').format(n=num_words, e=entropy)),
        ]

        return JsonResponse({
            'success': True, 'gen_type': 'passphrase',
            'result': passphrase,
            'result_label': str(_('Passphrase')),
            'password': passphrase, 'num_words': num_words,
            'word_list_size': wl_size, 'entropy': entropy,
            'strength': strength_label, 'strength_key': strength_key,
            'crack_time': crack,
            'formula': f'{num_words} {_("words")} × log₂({wl_size}) = {entropy} {_("bits")}',
            'step_by_step': steps,
            'chart_data': self._strength_chart(entropy),
        })

    # ── 3) PIN ───────────────────────────────────────────────────────
    def _gen_pin(self, data):
        length = int(data.get('pin_length', 6))
        if length < 4 or length > 12:
            raise ValueError(str(_('PIN length must be between 4 and 12.')))

        pin = ''.join(str(secrets.randbelow(10)) for _ in range(length))
        entropy = round(length * math.log2(10), 1)
        strength_label, strength_key = self._strength(entropy)
        crack = self._crack_time(entropy)

        steps = [
            str(_('Step 1: Configuration')),
            f'  • {length}-{_("digit PIN")}',
            f'  • {_("Pool")}: 0–9 (10 {_("digits")})',
            '', str(_('Step 2: Generate {n} random digits').format(n=length)),
            f'  {pin}',
            '', str(_('Step 3: Calculate entropy')),
            f'  {length} × log₂(10) = {entropy} {_("bits")}',
            '', str(_('Step 4: Strength assessment')),
            f'  • {strength_label}',
            f'  • {_("Crack time")}: {crack}',
            '', str(_('Result: PIN generated ({n} digits, {e} bits)').format(n=length, e=entropy)),
        ]

        return JsonResponse({
            'success': True, 'gen_type': 'pin',
            'result': pin,
            'result_label': str(_('PIN Code')),
            'password': pin, 'length': length,
            'pool_size': 10, 'entropy': entropy,
            'strength': strength_label, 'strength_key': strength_key,
            'crack_time': crack,
            'formula': f'{length} × log₂(10) = {entropy} {_("bits")}',
            'step_by_step': steps,
            'chart_data': self._strength_chart(entropy),
        })

    # ── chart helper ─────────────────────────────────────────────────
    @staticmethod
    def _strength_chart(entropy):
        thresholds = [
            (str(_('Weak')), 40),
            (str(_('Fair')), 60),
            (str(_('Good')), 80),
            (str(_('Strong')), 128),
            (str(_('Very Strong')), 200),
        ]
        labels = [t[0] for t in thresholds]
        values = [t[1] for t in thresholds]
        colors = ['rgba(239,68,68,0.7)', 'rgba(245,158,11,0.7)', 'rgba(59,130,246,0.7)',
                  'rgba(34,197,94,0.7)', 'rgba(16,185,129,0.7)']

        return {'main_chart': {
            'type': 'bar',
            'data': {
                'labels': labels,
                'datasets': [
                    {
                        'label': str(_('Threshold (bits)')),
                        'data': values,
                        'backgroundColor': colors,
                        'borderColor': ['#ef4444', '#f59e0b', '#3b82f6', '#22c55e', '#10b981'],
                        'borderWidth': 2, 'borderRadius': 6,
                    },
                    {
                        'label': str(_('Your Entropy')),
                        'data': [entropy] * len(values),
                        'type': 'line',
                        'borderColor': '#7c3aed',
                        'borderWidth': 3,
                        'pointRadius': 0,
                        'borderDash': [6, 3],
                        'fill': False,
                    },
                ],
            },
            'options': {
                'responsive': True, 'maintainAspectRatio': False,
                'plugins': {
                    'legend': {'display': True, 'position': 'bottom'},
                    'title': {'display': True, 'text': str(_('Password Strength vs Thresholds'))},
                },
                'scales': {'y': {'beginAtZero': True, 'title': {'display': True, 'text': str(_('Bits of Entropy'))}}},
            },
        }}
