import os
import polib
from deep_translator import GoogleTranslator

# Define the languages you want to translate to
languages = [
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
    # ('ms', 'Bahasa Melayu'),
    # ('pl', 'Polski'),
    # ('sv', 'Svenska'),
    # ('th', 'ภาษาไทย'),
    # ('uk', 'Українська'),
    # ('ur', 'اردو'),
    # ('vi', 'Tiếng Việt'),
]

# Translate a single string using deep-translator
def translate_text(text, target_lang):
    try:
        translation = GoogleTranslator(source='auto', target=target_lang).translate(text)
        if translation:
            return translation
        else:
            return text  # Fallback to original text if translation fails
    except Exception as e:
        print(f"Error translating '{text}' to {target_lang}: {e}")
        return text  # Fallback to original text in case of an error

# Automatically translate the .po files
def auto_translate_po_files():
    for lang_code, lang_name in languages:
        po_file_path = f'locale/{lang_code}/LC_MESSAGES/django.po'
        if os.path.exists(po_file_path):
            po_file = polib.pofile(po_file_path)

            # Translate each msgid if msgstr is empty
            for entry in po_file:
                if not entry.msgstr:  # Only translate if msgstr is empty
                    translated_text = translate_text(entry.msgid, lang_code)
                    if translated_text:  # Ensure that msgstr is not None
                        entry.msgstr = translated_text
                    else:
                        entry.msgstr = entry.msgid  # Fallback to original msgid
                    print(f"Translated '{entry.msgid}' -> '{entry.msgstr}' in {lang_name}")

            # Save the translated .po file
            po_file.save()
            print(f"Translation completed and saved for {lang_code} ({lang_name})")

# Compile translations into .mo files
def compile_translations():
    os.system('django-admin compilemessages')

# Run the translation and compilation
if __name__ == '__main__':
    auto_translate_po_files()  # Step 1: Translate the .po files
    compile_translations()     # Step 2: Compile .po to .mo files
