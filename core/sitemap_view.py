"""
Custom sitemap view that automatically uses request domain for SEO optimization.
Ensures sitemap URLs always match the domain being accessed.
"""
import logging
import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sitemaps.views import sitemap as django_sitemap
from django.db import IntegrityError
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

    raw = (getattr(settings, 'SITE_URL', '') or '').strip()
    host = ''
    if raw:
        low = raw.lower()
        for prefix in ('https://', 'http://'):
            if low.startswith(prefix):
                raw = raw[len(prefix) :].lstrip()
                low = raw.lower()
                break
        raw = raw.split('/')[0].split('@')[-1]
        if ':' in raw:
            raw = raw.split(':')[0]
        host = raw.strip()

    if not host:
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

    content = response.content.decode('utf-8', errors='replace')

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
    out = HttpResponse(
        content.encode('utf-8'),
        content_type='application/xml; charset=utf-8',
    )
    for hdr in ('Last-Modified', 'X-Robots-Tag'):
        val = response.get(hdr)
        if val:
            out[hdr] = val
    return out


def sitemap(request, sitemaps, **kwargs):
    """
    Custom sitemap view that automatically uses the request domain.
    This ensures URLs always match the domain being accessed for proper SEO indexing.
    """
    protocol, domain = _canonical_scheme_and_host(request)
    site_pk = getattr(settings, 'SITE_ID', None)
    if site_pk and not Site.objects.filter(pk=site_pk).exists():
        try:
            Site.objects.create(pk=site_pk, domain=domain, name='CalculatorDrive')
            logger.warning('Created missing django Site pk=%s domain=%s', site_pk, domain)
        except IntegrityError:
            pass

    with translation.override(settings.LANGUAGE_CODE):
        response = django_sitemap(request, sitemaps, **kwargs)

    try:
        return _rewrite_sitemap_response(response, protocol, domain)
    except Exception:
        logger.exception('sitemap.xml loc rewrite failed; returning unmodified Django sitemap')
        if isinstance(response, TemplateResponse):
            response.render()
        return response
