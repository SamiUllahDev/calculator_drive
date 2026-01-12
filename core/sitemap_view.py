"""
Custom sitemap view that automatically uses request domain for SEO optimization.
Ensures sitemap URLs always match the domain being accessed.
"""
from django.contrib.sitemaps.views import sitemap as django_sitemap
from django.http import HttpResponse
import re


def sitemap(request, sitemaps, **kwargs):
    """
    Custom sitemap view that automatically uses the request domain.
    This ensures URLs always match the domain being accessed for proper SEO indexing.
    """
    try:
        domain = request.get_host()
        protocol = 'https' if request.is_secure() else 'http'
        
        response = django_sitemap(request, sitemaps, **kwargs)
        
        if isinstance(response, HttpResponse) and 'xml' in response.get('Content-Type', '').lower():
            try:
                content = response.content.decode('utf-8')
                
                # Replace example.com with request domain
                content = content.replace('http://example.com', f'{protocol}://{domain}')
                content = content.replace('https://example.com', f'{protocol}://{domain}')
                content = content.replace('http://www.example.com', f'{protocol}://{domain}')
                content = content.replace('https://www.example.com', f'{protocol}://{domain}')
                
                # Replace any domain in <loc> tags with request domain
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
                
                response.content = content.encode('utf-8')
                response['Content-Type'] = 'application/xml; charset=utf-8'
                
            except Exception:
                pass
        
        return response
    except Exception:
        return django_sitemap(request, sitemaps, **kwargs)
