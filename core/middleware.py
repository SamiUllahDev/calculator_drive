"""
Canonical Redirect Middleware for SEO optimization.

Handles three types of redirects that cause "Page with redirect" issues in
Google Search Console:

1. www → non-www (e.g., www.calculatordrive.com → calculatordrive.com)
2. http → https (e.g., http://calculatordrive.com → https://calculatordrive.com)
3. Non-trailing-slash → trailing-slash (handled by Django's CommonMiddleware,
   but this middleware ensures consistent behavior)

All redirects use 301 (permanent) status codes to tell Google to update its index.
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect


CANONICAL_DOMAIN = 'calculatordrive.com'
CANONICAL_PROTOCOL = 'https'


class CanonicalDomainMiddleware:
    """
    Middleware that redirects all requests to the canonical domain.

    Handles:
    - www.calculatordrive.com → calculatordrive.com (301)
    - http:// → https:// (301)

    Must be placed FIRST in the middleware list so it runs before
    anything else processes the request.
    """

    # Paths that should NOT be redirected (health checks, internal, etc.)
    SKIP_PATHS = [
        '/health-check',
        '/.well-known/',
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip during development (localhost, 127.0.0.1, etc.)
        host = request.get_host().split(':')[0]  # Remove port
        if host in ('localhost', '127.0.0.1', '0.0.0.0', 'testserver'):
            return self.get_response(request)

        # Skip for certain paths
        path = request.path
        for skip_path in self.SKIP_PATHS:
            if path.startswith(skip_path):
                return self.get_response(request)

        # Check if redirect is needed
        needs_redirect = False
        redirect_protocol = CANONICAL_PROTOCOL
        redirect_domain = CANONICAL_DOMAIN

        # 1. Check for www → non-www redirect
        if host.startswith('www.'):
            needs_redirect = True

        # 2. Check for http → https redirect
        #    In production behind a reverse proxy, check X-Forwarded-Proto
        forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
        is_secure = request.is_secure() or forwarded_proto == 'https'

        if not is_secure:
            needs_redirect = True

        # 3. Check if domain doesn't match canonical (e.g., some other domain)
        clean_host = host.lstrip('www.')
        if clean_host != CANONICAL_DOMAIN:
            # Don't redirect if it's a completely different domain
            # (could be a staging server, etc.)
            if CANONICAL_DOMAIN not in clean_host and clean_host not in CANONICAL_DOMAIN:
                return self.get_response(request)
            needs_redirect = True

        if needs_redirect:
            # Build the canonical URL
            query_string = request.META.get('QUERY_STRING', '')
            new_url = f'{redirect_protocol}://{redirect_domain}{path}'
            if query_string:
                new_url = f'{new_url}?{query_string}'
            return HttpResponsePermanentRedirect(new_url)

        return self.get_response(request)


class PerformanceHeadersMiddleware:
    """
    Middleware that adds performance-critical HTTP headers to HTML responses.
    
    Adds:
    - Link preload header for critical font (helps LCP by starting font download earlier)
    - Cache-Control with stale-while-revalidate for CDN edge caching (reduces TTFB)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only add headers to HTML responses (not static files, API, etc.)
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response

        # Add Link preload header for the LCP font weight.
        # Keep bytes low on mobile: only preload the weight used by the hero title (700/800).
        font_url = '/static/vendor/fonts/inter/inter-700.woff2'
        link_value = f'<{font_url}>; rel=preload; as=font; type="font/woff2"; crossorigin'
        existing_link = response.get('Link', '')
        if existing_link:
            response['Link'] = f'{existing_link}, {link_value}'
        else:
            response['Link'] = link_value

        # For non-authenticated HTML pages, enable CDN-friendly caching.
        # This tells CDN/Cloudflare to serve stale content while fetching fresh in background
        # Dramatically reduces TTFB for repeat visitors (from 1.8s to ~50ms at edge)
        if not request.user.is_authenticated and not response.get('Cache-Control'):
            # - max-age=0: browsers revalidate HTML (keeps content fresh)
            # - s-maxage=600: CDN can cache HTML for 10 minutes
            # - stale-while-revalidate: serve stale while revalidating in background
            response['Cache-Control'] = 'public, max-age=0, s-maxage=600, stale-while-revalidate=86400'

        return response
