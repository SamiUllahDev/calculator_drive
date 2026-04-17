"""
Auto-translate .po files using Google Translate.

This script protects Python format placeholders from being corrupted
by the translation engine. It handles:
  - %(name)s  style (Python % formatting)
  - {name}    style (Python .format() / f-strings)
  - %s, %d    style (positional % formatting)
  - {{ }}     style (literal braces in .format strings)

Usage:
    python auto_translate.py                    # Translate all languages
    python auto_translate.py --lang es fr de    # Translate specific languages
    python auto_translate.py --force            # Re-translate already translated entries
"""

import os
import re
import sys
import argparse
import subprocess
import polib
from deep_translator import GoogleTranslator

# ============================================================================
# CONFIGURATION
# ============================================================================

LOCALE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'locale')

# Languages to translate (code, name)
LANGUAGES = [
    ('es', 'Español'),
    ('fr', 'Français'),
    ('de', 'Deutsch'),
    ('it', 'Italiano'),
    ('pt', 'Português'),
    ('ar', 'العربية'),
    ('ja', '日本語'),
    ('tr', 'Türkçe'),
    ('id', 'Bahasa Indonesia'),
    ('ru', 'Pусский'),
    ('ko', '한국어'),
    ('bg', 'Български'),
    ('ca', 'Català'),
    ('nl', 'Nederlands'),
    ('el', 'Ελληνικά'),
    ('hi', 'हिन्दी'),
    ('ms', 'Bahasa Melayu'),
    ('pl', 'Polski'),
    ('sv', 'Svenska'),
    ('th', 'ภาษาไทย'),
    ('uk', 'Українська'),
    ('ur', 'اردو'),
    ('vi', 'Tiếng Việt'),
]

# Plural forms per language (for PO headers)
PLURAL_FORMS = {
    'ar': 'nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5;',
    'bg': 'nplurals=2; plural=(n != 1);',
    'ca': 'nplurals=2; plural=(n != 1);',
    'de': 'nplurals=2; plural=(n != 1);',
    'el': 'nplurals=2; plural=(n != 1);',
    'es': 'nplurals=2; plural=(n != 1);',
    'fr': 'nplurals=2; plural=(n > 1);',
    'hi': 'nplurals=2; plural=(n != 1);',
    'id': 'nplurals=1; plural=0;',
    'it': 'nplurals=2; plural=(n != 1);',
    'ja': 'nplurals=1; plural=0;',
    'ko': 'nplurals=1; plural=0;',
    'ms': 'nplurals=1; plural=0;',
    'nl': 'nplurals=2; plural=(n != 1);',
    'pl': 'nplurals=3; plural=(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);',
    'pt': 'nplurals=2; plural=(n != 1);',
    'ru': 'nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);',
    'sv': 'nplurals=2; plural=(n != 1);',
    'th': 'nplurals=1; plural=0;',
    'tr': 'nplurals=2; plural=(n > 1);',
    'uk': 'nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);',
    'ur': 'nplurals=2; plural=(n != 1);',
    'vi': 'nplurals=1; plural=0;',
    'zh_Hans': 'nplurals=1; plural=0;',
    'zh_Hant': 'nplurals=1; plural=0;',
}

# ============================================================================
# FORMAT PLACEHOLDER PROTECTION
# ============================================================================

# Regex patterns for Python format specifiers (order matters!)
FORMAT_PATTERNS = [
    # 1) Named: %(name)s, %(count)d, etc.
    re.compile(r'%\(\w+\)[sdifFeEgGcrboxXan]'),
    # 2) Brace: {name}, {0}, {count:.2f}, etc.
    re.compile(r'\{[^}]*\}'),
    # 3) Positional: %s, %d, %f, %.2f, %02d, etc.
    re.compile(r'(?<!%)%[#0\- +]?(?:\*|\d+)?(?:\.(?:\*|\d+))?[hlL]?[sdifFeEgGcrboxXan]'),
    # 4) Literal double braces: {{ or }}
    re.compile(r'\{\{|\}\}'),
]

# XML-like tags that Google Translate typically preserves
PLACEHOLDER_TEMPLATE = '<x id="{}" />'


def protect_placeholders(text):
    """
    Replace all format placeholders with XML-like tokens that
    Google Translate will not touch.

    Returns: (protected_text, mapping_dict)
    """
    placeholders = {}
    counter = [0]  # Use list for mutability in closure

    def replacer(match):
        token = PLACEHOLDER_TEMPLATE.format(counter[0])
        placeholders[token] = match.group(0)
        counter[0] += 1
        return token

    protected = text
    for pattern in FORMAT_PATTERNS:
        protected = pattern.sub(replacer, protected)

    return protected, placeholders


def restore_placeholders(translated_text, placeholders):
    """
    Restore original format placeholders from their XML tokens.
    """
    result = translated_text
    for token, original in placeholders.items():
        result = result.replace(token, original)
    return result


def validate_format_strings(msgid, msgstr):
    """
    Verify that msgstr has exactly the same format placeholders as msgid.
    Returns True if valid, False if corrupted.
    """
    for pattern in FORMAT_PATTERNS:
        id_matches = sorted(pattern.findall(msgid))
        str_matches = sorted(pattern.findall(msgstr))
        if id_matches != str_matches:
            return False
    return True


# ============================================================================
# TRANSLATION
# ============================================================================

def translate_text(text, target_lang):
    """
    Translate text while protecting format placeholders.
    Returns the translated string with placeholders intact.
    """
    if not text or not text.strip():
        return text

    # Step 1: Protect placeholders
    protected, placeholders = protect_placeholders(text)

    # Step 2: Translate
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(protected)
        if not translated:
            return text  # Fallback to original
    except Exception as e:
        print(f"    ⚠ Translation API error: {e}")
        return text

    # Step 3: Restore placeholders
    result = restore_placeholders(translated, placeholders)

    # Step 4: Validate — if format strings are broken, use original
    if not validate_format_strings(text, result):
        print(f"    ⚠ Format string mismatch detected, using original English text")
        return text

    return result


# ============================================================================
# PO FILE HEADER
# ============================================================================

def ensure_po_header(po_file, lang_code):
    """
    Ensure the PO file has a valid header with charset and plural forms.
    This prevents the 'Charset missing in header' fatal error.
    """
    metadata = po_file.metadata

    # Required header fields
    if 'Content-Type' not in metadata or 'charset' not in metadata.get('Content-Type', ''):
        metadata['Content-Type'] = 'text/plain; charset=UTF-8'

    if 'Content-Transfer-Encoding' not in metadata:
        metadata['Content-Transfer-Encoding'] = '8bit'

    if 'MIME-Version' not in metadata:
        metadata['MIME-Version'] = '1.0'

    if 'Plural-Forms' not in metadata:
        plural = PLURAL_FORMS.get(lang_code, 'nplurals=2; plural=(n != 1);')
        metadata['Plural-Forms'] = plural

    if 'Language' not in metadata or not metadata['Language']:
        metadata['Language'] = lang_code

    # Optional but nice to have
    if 'Project-Id-Version' not in metadata:
        metadata['Project-Id-Version'] = 'CalculatorDrive'

    po_file.metadata = metadata


# ============================================================================
# MAIN LOGIC
# ============================================================================

def translate_po_file(lang_code, lang_name, force=False):
    """Translate a single .po file."""
    po_path = os.path.join(LOCALE_DIR, lang_code, 'LC_MESSAGES', 'django.po')

    if not os.path.exists(po_path):
        print(f"  ⚠ File not found: {po_path}")
        return 0

    po = polib.pofile(po_path)

    # Ensure valid header FIRST
    ensure_po_header(po, lang_code)

    translated_count = 0
    error_count = 0
    total = len([e for e in po if not e.msgstr or force])

    print(f"  📝 {total} entries to translate")

    for i, entry in enumerate(po):
        # Skip already translated entries (unless --force)
        if entry.msgstr and not force:
            continue

        # Skip empty msgid (header entry)
        if not entry.msgid:
            continue

        translated = translate_text(entry.msgid, lang_code)

        if translated and translated != entry.msgid:
            entry.msgstr = translated
            translated_count += 1
        elif translated == entry.msgid:
            # Translation same as original (API returned original or fallback)
            entry.msgstr = translated
            error_count += 1

        # Progress indicator every 50 entries
        if (i + 1) % 50 == 0:
            print(f"    ... {i + 1} entries processed")

    # Save the file
    po.save()

    print(f"  ✅ {translated_count} translated, {error_count} kept as English")
    return translated_count


def compile_messages():
    """Run Django compilemessages."""
    print("\n📦 Compiling messages...")
    result = subprocess.run(
        [sys.executable, 'manage.py', 'compilemessages'],
        capture_output=True, text=True,
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    if result.returncode == 0:
        print("✅ compilemessages completed successfully!")
    else:
        print(f"❌ compilemessages failed:\n{result.stderr}")
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description='Auto-translate .po files safely')
    parser.add_argument('--lang', nargs='+', help='Specific language codes to translate (e.g., es fr de)')
    parser.add_argument('--force', action='store_true', help='Re-translate already translated entries')
    parser.add_argument('--no-compile', action='store_true', help='Skip compilemessages after translation')
    args = parser.parse_args()

    # Filter languages if specified
    if args.lang:
        languages = [(code, name) for code, name in LANGUAGES if code in args.lang]
        if not languages:
            print(f"❌ No matching languages found for: {args.lang}")
            sys.exit(1)
    else:
        languages = LANGUAGES

    print(f"🌍 Translating {len(languages)} language(s)...\n")

    total_translated = 0
    for lang_code, lang_name in languages:
        print(f"🔤 [{lang_code}] {lang_name}")
        count = translate_po_file(lang_code, lang_name, force=args.force)
        total_translated += count
        print()

    print(f"{'='*60}")
    print(f"📊 Total entries translated: {total_translated}")

    # Compile
    if not args.no_compile:
        compile_messages()


if __name__ == '__main__':
    main()
