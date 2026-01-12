"""
Production-ready sitemap classes for SEO optimization.
Generates comprehensive sitemap.xml with proper URL structure, lastmod dates, and priorities.
"""
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.urls import reverse, NoReverseMatch
from django.conf import settings
from django.utils import translation
from blog.models import Post, Category, Tag
from django.utils import timezone
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


class StaticViewSitemap(Sitemap):
    """
    Sitemap for static pages with separate entries for each language.
    SEO-optimized with proper priority and changefreq.
    """
    priority = 1.0
    changefreq = 'monthly'
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
            for lang_code, _ in settings.LANGUAGES:
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

    def lastmod(self, item):
        """Get last modification date for better SEO indexing."""
        try:
            url_name, lang_code = item
            if url_name == 'blog:post_list':
                cache_key = 'sitemap_latest_blog_post'
                if CACHE_AVAILABLE:
                    latest_post = cache.get(cache_key)
                    if latest_post is None:
                        latest_post = Post.objects.filter(
                            status='published', 
                            no_index=False
                        ).order_by('-updated_date').first()
                        if latest_post:
                            cache.set(cache_key, latest_post, 60 * 60)
                else:
                    latest_post = Post.objects.filter(
                        status='published', 
                        no_index=False
                    ).order_by('-updated_date').first()
                
                if latest_post:
                    return latest_post.updated_date or latest_post.published_date or latest_post.created_date
        except Exception:
            pass
        return timezone.now()


class CalculatorIndexSitemap(Sitemap):
    """
    Sitemap for calculator index pages with separate entries for each language.
    High priority for main category pages.
    """
    priority = 0.9
    changefreq = 'weekly'
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
            for lang_code, _ in settings.LANGUAGES:
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

    def lastmod(self, item):
        return timezone.now()


class MathCalculatorSitemap(Sitemap):
    """
    Sitemap for all math calculators.
    SEO-optimized with proper URL structure and priorities.
    """
    priority = 0.8
    changefreq = 'monthly'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        from Math_Calculators.views.index import MathIndexView
        return get_calculators_list('math', 'sitemap_math_calculators', MathIndexView)

    def location(self, item):
        """Generate SEO-friendly calculator URL."""
        try:
            if isinstance(item, dict) and 'url' in item:
                url = item['url'].strip()
                if url:
                    if url.startswith('/'):
                        url = url.lstrip('/')
                    return f"/math/{url}/"
            return '/math/'
        except (KeyError, TypeError, AttributeError):
            return '/math/'

    def lastmod(self, item):
        return timezone.now()


class FinanceCalculatorSitemap(Sitemap):
    """
    Sitemap for all financial calculators.
    SEO-optimized with proper URL structure and priorities.
    """
    priority = 0.8
    changefreq = 'monthly'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        from Financial_Calculators.views.index import FinanceIndexView
        return get_calculators_list('finance', 'sitemap_finance_calculators', FinanceIndexView)

    def location(self, item):
        """Generate SEO-friendly calculator URL."""
        try:
            if isinstance(item, dict) and 'url' in item:
                url = item['url'].strip()
                if url:
                    if url.startswith('/'):
                        url = url.lstrip('/')
                    return f"/finance/{url}/"
            return '/finance/'
        except (KeyError, TypeError, AttributeError):
            return '/finance/'

    def lastmod(self, item):
        return timezone.now()


class HealthCalculatorSitemap(Sitemap):
    """
    Sitemap for all health & fitness calculators.
    SEO-optimized with proper URL structure and priorities.
    """
    priority = 0.8
    changefreq = 'monthly'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        from Fitness_and_Health_Calculators.views.index import HealthIndexView
        return get_calculators_list('health', 'sitemap_health_calculators', HealthIndexView)

    def location(self, item):
        """Generate SEO-friendly calculator URL."""
        try:
            if isinstance(item, dict) and 'url' in item:
                url = item['url'].strip()
                if url:
                    if url.startswith('/'):
                        url = url.lstrip('/')
                    return f"/health/{url}/"
            return '/health/'
        except (KeyError, TypeError, AttributeError):
            return '/health/'

    def lastmod(self, item):
        return timezone.now()


class OtherCalculatorSitemap(Sitemap):
    """
    Sitemap for all other calculators.
    SEO-optimized with proper URL structure and priorities.
    """
    priority = 0.8
    changefreq = 'monthly'
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        from Other_Calculators.views.index import OtherIndexView
        return get_calculators_list('other', 'sitemap_other_calculators', OtherIndexView)

    def location(self, item):
        """Generate SEO-friendly calculator URL."""
        try:
            if isinstance(item, dict) and 'url' in item:
                url = item['url'].strip()
                if url:
                    if url.startswith('/'):
                        url = url.lstrip('/')
                    return f"/other/{url}/"
            return '/other/'
        except (KeyError, TypeError, AttributeError):
            return '/other/'

    def lastmod(self, item):
        return timezone.now()


class BlogPostSitemap(Sitemap):
    """
    Sitemap for published blog posts without language prefixes.
    SEO-optimized with proper lastmod dates.
    """
    changefreq = 'weekly'
    priority = 0.7
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return blog posts without language variants."""
        try:
            return Post.objects.filter(
                status='published', 
                no_index=False
            ).select_related('author', 'category').order_by('-published_date')
        except Exception:
            return Post.objects.none()

    def lastmod(self, obj):
        """Return last modification date for SEO."""
        try:
            return obj.updated_date or obj.published_date or obj.created_date or timezone.now()
        except Exception:
            return timezone.now()

    def location(self, obj):
        """Return blog URL without language prefix."""
        try:
            base_url = obj.get_absolute_url()
            if not base_url:
                return '/blog/'
            
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
    Sitemap for blog categories without language prefixes.
    SEO-optimized with proper lastmod dates.
    """
    changefreq = 'monthly'
    priority = 0.6
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return blog categories without language variants."""
        try:
            return Category.objects.filter(
                posts__status='published', 
                posts__no_index=False
            ).distinct().prefetch_related('posts')
        except Exception:
            return Category.objects.none()

    def lastmod(self, obj):
        """Get the latest post update date in this category."""
        try:
            latest_post = None
            try:
                if hasattr(obj, '_prefetched_objects_cache'):
                    posts = obj._prefetched_objects_cache.get('posts', None)
                    if posts:
                        published_posts = [p for p in posts if p.status == 'published' and not p.no_index]
                        if published_posts:
                            latest_post = max(
                                published_posts,
                                key=lambda p: p.updated_date or p.published_date or p.created_date,
                                default=None
                            )
            except (AttributeError, TypeError):
                pass
            
            if not latest_post:
                latest_post = obj.posts.filter(
                    status='published', 
                    no_index=False
                ).order_by('-updated_date').first()
            
            if latest_post:
                return latest_post.updated_date or latest_post.published_date or latest_post.created_date or timezone.now()
            return timezone.now()
        except Exception:
            return timezone.now()

    def location(self, obj):
        """Return blog category URL without language prefix."""
        try:
            base_url = obj.get_absolute_url()
            if not base_url:
                return '/blog/'
            
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
    Sitemap for blog tags without language prefixes.
    SEO-optimized with proper lastmod dates.
    """
    changefreq = 'monthly'
    priority = 0.5
    i18n = False
    alternates = False
    x_default = False

    def items(self):
        """Return blog tags without language variants."""
        try:
            return Tag.objects.filter(
                posts__status='published', 
                posts__no_index=False
            ).distinct().prefetch_related('posts')
        except Exception:
            return Tag.objects.none()

    def lastmod(self, obj):
        """Get the latest post update date with this tag."""
        try:
            latest_post = None
            try:
                if hasattr(obj, '_prefetched_objects_cache'):
                    posts = obj._prefetched_objects_cache.get('posts', None)
                    if posts:
                        published_posts = [p for p in posts if p.status == 'published' and not p.no_index]
                        if published_posts:
                            latest_post = max(
                                published_posts,
                                key=lambda p: p.updated_date or p.published_date or p.created_date,
                                default=None
                            )
            except (AttributeError, TypeError):
                pass
            
            if not latest_post:
                latest_post = obj.posts.filter(
                    status='published', 
                    no_index=False
                ).order_by('-updated_date').first()
            
            if latest_post:
                return latest_post.updated_date or latest_post.published_date or latest_post.created_date or timezone.now()
            return timezone.now()
        except Exception:
            return timezone.now()

    def location(self, obj):
        """Return blog tag URL without language prefix."""
        try:
            base_url = obj.get_absolute_url()
            if not base_url:
                return '/blog/'
            
            for lang, _ in settings.LANGUAGES:
                if base_url.startswith(f'/{lang}/'):
                    base_url = base_url[len(f'/{lang}/'):]
                    if not base_url.startswith('/'):
                        base_url = '/' + base_url
                    break
            
            return base_url
        except Exception:
            return '/blog/'
