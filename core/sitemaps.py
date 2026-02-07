"""
Production-ready sitemap classes for SEO optimization.
Generates comprehensive sitemap.xml with proper URL structure and priorities.
ALL calculators are included for ALL languages (26 languages × 198 calculators = 5148 URLs)
"""
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.utils import translation
from blog.models import Post, Category, Tag
import time


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


def get_all_languages():
    """Get all language codes from settings."""
    return [lang[0] for lang in settings.LANGUAGES]


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages with separate entries for each language.
    SEO-optimized with proper priority and changefreq.
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (url_name, lang_code) tuples for each language."""
        items = []
        url_names = [
            'core:index',
            'blog:post_list',
            'core:privacy_policy',
            'core:terms_of_service',
            'core:cookie_policy',
            'core:search',
        ]
        for url_name in url_names:
            for lang_code in get_all_languages():
                items.append((url_name, lang_code))
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


class CalculatorIndexSitemap(Sitemap):
    """
    Sitemap for calculator index pages with separate entries for each language.
    High priority for main category pages.
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (url_name, lang_code) tuples for each language."""
        items = []
        url_names = [
            'math_calculators:index',
            'financial_calculators:index',
            'fitness_and_health_calculators:index',
            'other_calculators:index',
        ]
        for url_name in url_names:
            for lang_code in get_all_languages():
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


class MathCalculatorSitemap(Sitemap):
    """
    Sitemap for all math calculators with ALL language variants.
    Generates: 44 calculators × 26 languages = 1,144 URLs
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (calculator, lang_code) tuples for ALL languages."""
        from Math_Calculators.views.index import MathIndexView
        calculators = get_calculators_list('math', 'sitemap_math_calculators', MathIndexView)
        
        items = []
        for calc in calculators:
            for lang_code in get_all_languages():
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
                    base_url = f"/math/{url}/"
                    
                    # Add language prefix for non-default languages
                    if lang_code != settings.LANGUAGE_CODE:
                        base_url = f"/{lang_code}{base_url}"
                    
                    return base_url
            return '/math/'
        except (KeyError, TypeError, AttributeError):
            return '/math/'


class FinanceCalculatorSitemap(Sitemap):
    """
    Sitemap for all financial calculators with ALL language variants.
    Generates: 70 calculators × 26 languages = 1,820 URLs
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (calculator, lang_code) tuples for ALL languages."""
        from Financial_Calculators.views.index import FinanceIndexView
        calculators = get_calculators_list('finance', 'sitemap_finance_calculators', FinanceIndexView)
        
        items = []
        for calc in calculators:
            for lang_code in get_all_languages():
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
                    base_url = f"/finance/{url}/"
                    
                    # Add language prefix for non-default languages
                    if lang_code != settings.LANGUAGE_CODE:
                        base_url = f"/{lang_code}{base_url}"
                    
                    return base_url
            return '/finance/'
        except (KeyError, TypeError, AttributeError):
            return '/finance/'


class HealthCalculatorSitemap(Sitemap):
    """
    Sitemap for all health & fitness calculators with ALL language variants.
    Generates: 31 calculators × 26 languages = 806 URLs
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (calculator, lang_code) tuples for ALL languages."""
        from Fitness_and_Health_Calculators.views.index import HealthIndexView
        calculators = get_calculators_list('health', 'sitemap_health_calculators', HealthIndexView)
        
        items = []
        for calc in calculators:
            for lang_code in get_all_languages():
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
                    base_url = f"/health/{url}/"
                    
                    # Add language prefix for non-default languages
                    if lang_code != settings.LANGUAGE_CODE:
                        base_url = f"/{lang_code}{base_url}"
                    
                    return base_url
            return '/health/'
        except (KeyError, TypeError, AttributeError):
            return '/health/'


class OtherCalculatorSitemap(Sitemap):
    """
    Sitemap for all other calculators with ALL language variants.
    Generates: 53 calculators × 26 languages = 1,378 URLs
    """
    changefreq = 'daily'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return list of (calculator, lang_code) tuples for ALL languages."""
        from Other_Calculators.views.index import OtherIndexView
        calculators = get_calculators_list('other', 'sitemap_other_calculators', OtherIndexView)
        
        items = []
        for calc in calculators:
            for lang_code in get_all_languages():
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
                    base_url = f"/other/{url}/"
                    
                    # Add language prefix for non-default languages
                    if lang_code != settings.LANGUAGE_CODE:
                        base_url = f"/{lang_code}{base_url}"
                    
                    return base_url
            return '/other/'
        except (KeyError, TypeError, AttributeError):
            return '/other/'


class BlogPostSitemap(Sitemap):
    """
    Sitemap for published blog posts (no language variants - single URL per post).
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


class BlogCategorySitemap(Sitemap):
    """
    Sitemap for blog categories (no language variants - single URL per category).
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


class BlogTagSitemap(Sitemap):
    """
    Sitemap for blog tags (no language variants - single URL per tag).
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
