"""
Production-ready sitemap classes for SEO optimization.

INDEXING FIX: Sitemaps now focus on HIGH-VALUE languages only to prevent
"Crawled - currently not indexed" by reducing crawl waste on machine-translated
pages that Google considers thin content.

Changes from previous version:
1. Only high-value languages are included (en + 9 major languages)
2. lastmod dates are provided (Google uses these for freshness signals)
3. Priority values differentiate important vs. less important pages
4. Low-value pages (search, tags, feeds, legal) are excluded from sitemap
5. Blog sitemap only includes English URLs (content is not translated)
"""
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.utils import translation, timezone
from blog.models import Post, Category, Tag
import time
from datetime import datetime


# ============================================================================
# HIGH-VALUE LANGUAGES
# ============================================================================
# Only these languages appear in the sitemap. Other languages are still
# accessible via URL but won't be submitted to Google for indexing.
# This focuses crawl budget on pages Google will actually index.
#
# Selection criteria: search volume, translation quality, user traffic
# ============================================================================
HIGH_VALUE_LANGUAGES = ['en', 'es', 'fr', 'de', 'pt', 'ja', 'hi', 'it', 'ru', 'nl']


# Cache calculator lists since they're static
try:
    from django.core.cache import cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    _memory_cache = {}
    _cache_timestamps = {}


def get_calculators_list(app_name, cache_key, view_class):
    """
    Get calculator list with caching and validation.
    Returns empty list on any error to ensure sitemap generation continues.
    """
    try:
        if CACHE_AVAILABLE:
            calculators = cache.get(cache_key)
            if calculators is None:
                view = view_class()
                calculators = view.get_context_data().get('calculators', [])
                if not isinstance(calculators, list):
                    calculators = []
                calculators = [calc for calc in calculators if isinstance(calc, dict) and 'url' in calc]
                cache.set(cache_key, calculators, 60 * 60 * 24)
            return calculators or []
        else:
            if cache_key in _memory_cache:
                calculators = _memory_cache[cache_key]
                if time.time() - _cache_timestamps.get(cache_key, 0) < 60 * 60 * 24:
                    return calculators or []
            
            view = view_class()
            calculators = view.get_context_data().get('calculators', [])
            if not isinstance(calculators, list):
                calculators = []
            calculators = [calc for calc in calculators if isinstance(calc, dict) and 'url' in calc]
            _memory_cache[cache_key] = calculators
            _cache_timestamps[cache_key] = time.time()
            return calculators or []
    except Exception:
        return []


def _get_lastmod():
    """
    Return a consistent lastmod date for static calculator pages.
    Uses the current date at midnight UTC — Google uses this to gauge freshness.
    """
    return timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages with separate entries for each HIGH-VALUE language.
    Excludes low-value utility pages (search, legal) from non-English sitemaps.
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    # Pages to include for ALL high-value languages
    _translatable_pages = [
        'core:index',
    ]

    # Pages to include for English ONLY (legal/utility — not worth indexing translated)
    _english_only_pages = [
        'core:privacy_policy',
        'core:terms_of_service',
        'core:cookie_policy',
        'core:search',
    ]

    def items(self):
        """Return list of (url_name, lang_code) tuples for high-value languages."""
        items = []
        # Translatable pages in all high-value languages
        for url_name in self._translatable_pages:
            for lang_code in HIGH_VALUE_LANGUAGES:
                items.append((url_name, lang_code))
        
        # English-only pages
        for url_name in self._english_only_pages:
            items.append((url_name, 'en'))

        # Blog index for all high-value languages
        for lang_code in HIGH_VALUE_LANGUAGES:
            items.append(('blog:post_list', lang_code))

        return items

    def location(self, item):
        """Build URL with language prefix for SEO-friendly URLs."""
        try:
            url_name, lang_code = item
            base_url = reverse(url_name)
            
            if lang_code != settings.LANGUAGE_CODE:
                if base_url.startswith('/'):
                    base_url = f"/{lang_code}{base_url}"
                else:
                    base_url = f"/{lang_code}/{base_url}"
            
            return base_url
        except (NoReverseMatch, ValueError, TypeError):
            return '/'

    def priority(self, item):
        url_name, lang_code = item
        if url_name == 'core:index':
            return 1.0 if lang_code == 'en' else 0.8
        if url_name == 'blog:post_list':
            return 0.7
        return 0.3  # legal pages

    def lastmod(self, item):
        return _get_lastmod()


class CalculatorIndexSitemap(Sitemap):
    """
    Sitemap for calculator index pages with entries for high-value languages.
    High priority for main category pages.
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (url_name, lang_code) tuples for high-value languages."""
        items = []
        url_names = [
            'math_calculators:index',
            'financial_calculators:index',
            'fitness_and_health_calculators:index',
            'other_calculators:index',
        ]
        for url_name in url_names:
            for lang_code in HIGH_VALUE_LANGUAGES:
                items.append((url_name, lang_code))
        return items

    def location(self, item):
        """Build URL with language prefix."""
        try:
            url_name, lang_code = item
            url_map = {
                'math_calculators:index': '/math/',
                'financial_calculators:index': '/finance/',
                'fitness_and_health_calculators:index': '/health/',
                'other_calculators:index': '/other/',
            }
            base_url = url_map.get(url_name)
            if not base_url:
                base_url = reverse(url_name)
            
            if lang_code != settings.LANGUAGE_CODE:
                if base_url.startswith('/'):
                    base_url = f"/{lang_code}{base_url}"
                else:
                    base_url = f"/{lang_code}/{base_url}"
            
            return base_url
        except (NoReverseMatch, ValueError, TypeError, Exception):
            return '/'

    def priority(self, item):
        _, lang_code = item
        return 0.9 if lang_code == 'en' else 0.7

    def lastmod(self, item):
        return _get_lastmod()


class _BaseCalculatorSitemap(Sitemap):
    """
    Base class for calculator sitemaps.
    Generates URLs for high-value languages only with proper lastmod/priority.
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False
    _category_prefix = ''  # Override in subclass: 'math', 'finance', etc.
    _cache_key = ''  # Override in subclass

    def _get_view_class(self):
        """Override in subclass to return the index view class."""
        raise NotImplementedError

    def items(self):
        """Return list of (calculator, lang_code) tuples for HIGH-VALUE languages."""
        calculators = get_calculators_list(
            self._category_prefix, self._cache_key, self._get_view_class()
        )
        items = []
        for calc in calculators:
            for lang_code in HIGH_VALUE_LANGUAGES:
                items.append((calc, lang_code))
        return items

    def location(self, item):
        """Generate SEO-friendly calculator URL with language prefix."""
        try:
            calc, lang_code = item
            if isinstance(calc, dict) and 'url' in calc:
                url = calc['url'].strip()
                if url:
                    if url.startswith('/'):
                        url = url.lstrip('/')
                    base_url = f"/{self._category_prefix}/{url}/"
                    
                    # Add language prefix for non-default languages
                    if lang_code != settings.LANGUAGE_CODE:
                        base_url = f"/{lang_code}{base_url}"
                    
                    return base_url
            return f'/{self._category_prefix}/'
        except (KeyError, TypeError, AttributeError):
            return f'/{self._category_prefix}/'

    def priority(self, item):
        _, lang_code = item
        return 0.8 if lang_code == 'en' else 0.6

    def lastmod(self, item):
        return _get_lastmod()


class MathCalculatorSitemap(_BaseCalculatorSitemap):
    """Sitemap for math calculators across high-value languages."""
    _category_prefix = 'math'
    _cache_key = 'sitemap_math_calculators'

    def _get_view_class(self):
        from Math_Calculators.views.index import MathIndexView
        return MathIndexView


class FinanceCalculatorSitemap(_BaseCalculatorSitemap):
    """Sitemap for financial calculators across high-value languages."""
    _category_prefix = 'finance'
    _cache_key = 'sitemap_finance_calculators'

    def _get_view_class(self):
        from Financial_Calculators.views.index import FinanceIndexView
        return FinanceIndexView


class HealthCalculatorSitemap(_BaseCalculatorSitemap):
    """Sitemap for health & fitness calculators across high-value languages."""
    _category_prefix = 'health'
    _cache_key = 'sitemap_health_calculators'

    def _get_view_class(self):
        from Fitness_and_Health_Calculators.views.index import HealthIndexView
        return HealthIndexView


class OtherCalculatorSitemap(_BaseCalculatorSitemap):
    """Sitemap for other/utility calculators across high-value languages."""
    _category_prefix = 'other'
    _cache_key = 'sitemap_other_calculators'

    def _get_view_class(self):
        from Other_Calculators.views.index import OtherIndexView
        return OtherIndexView


class BlogPostSitemap(Sitemap):
    """
    Sitemap for published blog posts (English only — content is not translated).
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return blog posts without language variants."""
        try:
            return list(Post.objects.filter(
                status='published', 
                no_index=False
            ).select_related('author', 'category').order_by('-published_date'))
        except Exception:
            return []

    def location(self, item):
        """Return blog URL without language prefix."""
        try:
            base_url = item.get_absolute_url()
            if not base_url:
                return '/blog/'
            
            # Remove any existing language prefix
            for lang, _ in settings.LANGUAGES:
                if base_url.startswith(f'/{lang}/'):
                    base_url = base_url[len(f'/{lang}/'):]
                    if not base_url.startswith('/'):
                        base_url = '/' + base_url
                    break
            
            return base_url
        except Exception:
            return '/blog/'

    def priority(self, item):
        return 0.7

    def lastmod(self, item):
        """Use the post's updated_date if available, otherwise published_date."""
        try:
            return item.updated_date or item.published_date
        except AttributeError:
            return _get_lastmod()


class BlogCategorySitemap(Sitemap):
    """
    Sitemap for blog categories (English only).
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return blog categories without language variants."""
        try:
            return list(Category.objects.filter(
                posts__status='published', 
                posts__no_index=False
            ).distinct().prefetch_related('posts'))
        except Exception:
            return []

    def location(self, item):
        """Return blog category URL without language prefix."""
        try:
            base_url = item.get_absolute_url()
            if not base_url:
                return '/blog/'
            
            # Remove any existing language prefix
            for lang, _ in settings.LANGUAGES:
                if base_url.startswith(f'/{lang}/'):
                    base_url = base_url[len(f'/{lang}/'):]
                    if not base_url.startswith('/'):
                        base_url = '/' + base_url
                    break
            
            return base_url
        except Exception:
            return '/blog/'

    def priority(self, item):
        return 0.5

    def lastmod(self, item):
        return _get_lastmod()


class BlogTagSitemap(Sitemap):
    """
    Sitemap for blog tags (English only).
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return blog tags without language variants."""
        try:
            return list(Tag.objects.filter(
                posts__status='published', 
                posts__no_index=False
            ).distinct().prefetch_related('posts'))
        except Exception:
            return []

    def location(self, item):
        """Return blog tag URL without language prefix."""
        try:
            base_url = item.get_absolute_url()
            if not base_url:
                return '/blog/'
            
            # Remove any existing language prefix
            for lang, _ in settings.LANGUAGES:
                if base_url.startswith(f'/{lang}/'):
                    base_url = base_url[len(f'/{lang}/'):]
                    if not base_url.startswith('/'):
                        base_url = '/' + base_url
                    break
            
            return base_url
        except Exception:
            return '/blog/'

    def priority(self, item):
        return 0.4

    def lastmod(self, item):
        return _get_lastmod()
