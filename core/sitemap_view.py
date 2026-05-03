"""
Custom sitemap view that automatically uses request domain for SEO optimization.
Ensures sitemap URLs always match the domain being accessed.
"""
from django.conf import settings
from django.contrib.sitemaps.views import sitemap as django_sitemap
from django.http import HttpResponse, StreamingHttpResponse
from django.template.response import TemplateResponse
from django.utils import translation
import re


def _protocol_and_domain(request):
    domain = request.get_host()
    protocol = getattr(settings, 'SITE_PROTOCOL', 'https')
    if protocol not in ('http', 'https'):
        protocol = 'https' if request.is_secure() else 'http'
    return protocol, domain


def _rewrite_sitemap_response(response, protocol, domain):
    """Render TemplateResponse if needed; rewrite <loc> to canonical scheme + request host."""
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
    protocol, domain = _protocol_and_domain(request)
    try:
        with translation.override(settings.LANGUAGE_CODE):
            response = django_sitemap(request, sitemaps, **kwargs)
        return _rewrite_sitemap_response(response, protocol, domain)
    except Exception:
        with translation.override(settings.LANGUAGE_CODE):
            response = django_sitemap(request, sitemaps, **kwargs)
        return _rewrite_sitemap_response(response, protocol, domain)
