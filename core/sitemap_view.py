"""
Custom sitemap view that automatically uses request domain for SEO optimization.
Ensures sitemap URLs always match the domain being accessed.
"""
import logging
import re

from django.conf import settings
from django.contrib.sitemaps.views import sitemap as django_sitemap
from django.http import HttpResponse, StreamingHttpResponse
from django.template.response import TemplateResponse
from django.utils import translation

logger = logging.getLogger(__name__)


def _canonical_scheme_and_host(request):
    """
    Scheme + host for every <loc>. Uses SITE_* so URLs match robots.txt canonical
    (apex calculatordrive.com), even when the request hits www behind the CDN.
    """
    protocol = getattr(settings, 'SITE_PROTOCOL', 'https')
    if protocol not in ('http', 'https'):
        protocol = 'https' if request.is_secure() else 'http'

    host = (getattr(settings, 'SITE_URL', '') or '').strip()
    if host:
        # SITE_URL must be hostname only (no scheme, no path)
        host = host.split('/')[0].split('@')[-1]
        if ':' in host:
            host = host.split(':')[0]
    else:
        host = request.get_host().split(':')[0]

    return protocol, host


def _rewrite_sitemap_response(response, protocol, domain):
    """Render TemplateResponse if needed; rewrite <loc> to canonical scheme + host."""
    if isinstance(response, TemplateResponse):
        response.render()

    ct = response.get('Content-Type', '').lower()
    if (
        not isinstance(response, HttpResponse)
        or isinstance(response, StreamingHttpResponse)
        or 'xml' not in ct
    ):
        return response

    content = response.content.decode('utf-8')

    placeholder_domains = [
        'example.com', 'www.example.com',
        'yourdomain.com', 'www.yourdomain.com',
    ]
    for placeholder in placeholder_domains:
        content = content.replace(f'http://{placeholder}', f'{protocol}://{domain}')
        content = content.replace(f'https://{placeholder}', f'{protocol}://{domain}')

    def replace_domain_in_loc(match):
        url = match.group(1)
        url_match = re.match(r'https?://[^/]+(.*)', url)
        if url_match:
            path = url_match.group(1)
            if not path.startswith('/'):
                path = '/' + path
            return f'<loc>{protocol}://{domain}{path}</loc>'
        return match.group(0)

    content = re.sub(r'<loc>(https?://[^<]+)</loc>', replace_domain_in_loc, content)
    return HttpResponse(content.encode('utf-8'), content_type='application/xml; charset=utf-8')


def sitemap(request, sitemaps, **kwargs):
    """
    Custom sitemap view that automatically uses the request domain.
    This ensures URLs always match the domain being accessed for proper SEO indexing.
    """
    protocol, domain = _canonical_scheme_and_host(request)
    try:
        with translation.override(settings.LANGUAGE_CODE):
            response = django_sitemap(request, sitemaps, **kwargs)
        return _rewrite_sitemap_response(response, protocol, domain)
    except Exception:
        logger.exception('sitemap.xml generation failed')
        raise
