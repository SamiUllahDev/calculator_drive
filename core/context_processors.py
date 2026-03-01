"""
SEO Context Processor for hreflang and canonical URL support.

Fixes the "Duplicate, Google chose different canonical than user" issue by:
1. Generating proper hreflang alternate links for all language versions
2. Building correct self-referencing canonical URLs
3. Providing x-default hreflang pointing to the English version
"""
import re
from django.conf import settings
from django.utils.translation import get_language


def get_path_without_language_prefix(path):
    """
    Strip the language prefix from a URL path.
    e.g., /zh-hans/finance/bond-calculator/ -> /finance/bond-calculator/
          /finance/bond-calculator/ -> /finance/bond-calculator/
    """
    for lang_code, _ in settings.LANGUAGES:
        prefix = f'/{lang_code}/'
        if path.startswith(prefix):
            return '/' + path[len(prefix):]
        # Also check if path IS exactly the language prefix
        if path == f'/{lang_code}':
            return '/'
    return path


def build_absolute_url_for_lang(request, base_path, lang_code):
    """
    Build the full absolute URL for a given language code.
    English (default language) has no prefix: /finance/bond-calculator/
    Other languages get prefix: /zh-hans/finance/bond-calculator/
    """
    protocol = 'https'  # Always use https for production canonical/hreflang
    domain = 'calculatordrive.com'  # Hardcode the canonical domain

    if lang_code == settings.LANGUAGE_CODE:
        # Default language (English) - no prefix
        return f'{protocol}://{domain}{base_path}'
    else:
        # Non-default language - add prefix
        return f'{protocol}://{domain}/{lang_code}{base_path}'


def seo_context(request):
    """
    Context processor that provides:
    - hreflang_tags: list of dicts with 'lang' and 'url' for all language versions
    - canonical_url: the correct self-referencing canonical URL
    - is_noindex_page: whether this page should have noindex

    This tells Google that /zh-hans/finance/bond-calculator/ is the Chinese version
    of /finance/bond-calculator/, NOT a duplicate.
    """
    path = request.path

    # Determine if this page should be noindexed
    noindex_patterns = [
        '/accounts/',
        '/admin/',
        '/user/',
        '/i18n/',
        '/adsense/',
    ]
    is_noindex_page = any(
        pattern in path for pattern in noindex_patterns
    )

    # Also noindex login URLs with ?next= parameters
    if 'login' in path and request.GET.get('next'):
        is_noindex_page = True

    # For noindex pages, don't generate hreflang tags
    if is_noindex_page:
        return {
            'hreflang_tags': [],
            'canonical_url': '',
            'is_noindex_page': True,
        }

    # Get the base path without any language prefix
    base_path = get_path_without_language_prefix(path)

    # Build the canonical URL (self-referencing - points to current language version)
    current_lang = get_language() or settings.LANGUAGE_CODE
    canonical_url = build_absolute_url_for_lang(request, base_path, current_lang)

    # Build hreflang alternate URLs for ALL languages
    hreflang_tags = []
    for lang_code, lang_name in settings.LANGUAGES:
        alt_url = build_absolute_url_for_lang(request, base_path, lang_code)
        hreflang_tags.append({
            'lang': lang_code,
            'url': alt_url,
        })

    # Add x-default (points to English/default version)
    x_default_url = build_absolute_url_for_lang(
        request, base_path, settings.LANGUAGE_CODE
    )
    hreflang_tags.append({
        'lang': 'x-default',
        'url': x_default_url,
    })

    return {
        'hreflang_tags': hreflang_tags,
        'canonical_url': canonical_url,
        'is_noindex_page': False,
    }
