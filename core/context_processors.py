"""
SEO Context Processor for hreflang and canonical URL support.

Fixes the "Crawled - currently not indexed" issue by:
1. Generating proper hreflang alternate links for all language versions
2. Building correct self-referencing canonical URLs
3. Providing x-default hreflang pointing to the English version
4. noindexing low-value translated pages to focus crawl budget
"""
import re
from django.conf import settings
from django.utils.translation import get_language


# High-value languages that should be fully indexed.
# Other languages will still be accessible but will get noindex on low-value pages.
HIGH_VALUE_LANGUAGES = {'en', 'es', 'fr', 'de', 'pt', 'ja', 'hi', 'it', 'ru', 'nl'}


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


def _is_low_value_path(base_path):
    """
    Check if a path is a low-value utility/navigation page that should
    NOT be indexed in non-primary languages.
    
    These pages waste crawl budget when translated:
    - Search pages (no unique content)
    - Blog tag/category listing pages (aggregation pages)
    - Blog RSS feeds
    - Sitemap HTML page
    - Legal pages (cookie/terms/privacy — rarely searched in foreign languages)
    """
    low_value_patterns = [
        '/search/',
        '/blog/tag/',
        '/blog/feed/',
        '/sitemap/',
        '/cookie-policy/',
        '/terms-of-service/',
        '/privacy-policy/',
    ]
    return any(base_path.startswith(p) or base_path == p.rstrip('/')
               for p in low_value_patterns)


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

    # Get the base path without any language prefix
    base_path = get_path_without_language_prefix(path)
    current_lang = get_language() or settings.LANGUAGE_CODE

    # ──────────────────────────────────────────────────────────────────
    # NEW: noindex low-value pages in non-primary languages
    # These are pages Google crawls but refuses to index because they
    # add no unique value in translated form (search, tags, feeds, legal).
    # ──────────────────────────────────────────────────────────────────
    if not is_noindex_page and current_lang != settings.LANGUAGE_CODE:
        if _is_low_value_path(base_path):
            is_noindex_page = True

    # ──────────────────────────────────────────────────────────────────
    # NEW: noindex all pages for low-traffic languages that aren't in
    # our high-value set. These machine-translated pages dilute crawl
    # budget. They remain accessible to users but won't waste indexing.
    # ──────────────────────────────────────────────────────────────────
    if not is_noindex_page and current_lang not in HIGH_VALUE_LANGUAGES:
        is_noindex_page = True

    # For noindex pages, don't generate hreflang tags
    if is_noindex_page:
        # Still provide canonical for noindex pages (helps with crawl signals)
        canonical_url = build_absolute_url_for_lang(request, base_path, current_lang)
        return {
            'hreflang_tags': [],
            'canonical_url': canonical_url,
            'is_noindex_page': True,
        }

    # Build the canonical URL (self-referencing - points to current language version)
    # If the page is a blog page, the primary content is NOT translated (database models).
    # Google will see English content on foreign language URLs and flag it as a duplicate.
    # To fix 'Duplicate, Google chose different canonical than user', we force the canonical
    # to the English version and omit the hreflang tags to prevent crawler waste.
    is_untranslated_content = base_path.startswith('/blog/')

    if is_untranslated_content:
        canonical_url = build_absolute_url_for_lang(request, base_path, settings.LANGUAGE_CODE)
    else:
        canonical_url = build_absolute_url_for_lang(request, base_path, current_lang)

    # Build hreflang alternate URLs for HIGH-VALUE languages only
    # (reduces hreflang tag count from 25 to ~10, focusing Google's attention)
    hreflang_tags = []
    if not is_untranslated_content and not _is_low_value_path(base_path):
        for lang_code, lang_name in settings.LANGUAGES:
            # Only include high-value languages in hreflang
            if lang_code not in HIGH_VALUE_LANGUAGES:
                continue
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
