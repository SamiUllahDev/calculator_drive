from django import template

register = template.Library()


@register.filter
def add_class(field, css_class):
    """Add a CSS class to a form field"""
    if field.field.widget.attrs.get('class'):
        field.field.widget.attrs['class'] += f' {css_class}'
    else:
        field.field.widget.attrs['class'] = css_class
    return field


@register.filter
def attr(field, attr_string):
    """Add HTML attributes to a form field
    
    Usage: {{ field|attr:"placeholder:Enter text|rows:5|aria-label:Input" }}
    """
    if not attr_string:
        return field
    
    # Parse attribute string (format: "key:value|key2:value2")
    attrs = attr_string.split('|')
    for attr_pair in attrs:
        if ':' in attr_pair:
            key, value = attr_pair.split(':', 1)
            key = key.strip()
            value = value.strip()
            field.field.widget.attrs[key] = value
    
    return field


@register.simple_tag
def absolute_url(request):
    """Get the absolute URL for the current request"""
    return request.build_absolute_uri()


@register.simple_tag
def path_without_language(request):
    """Get the current path without the language prefix for language switching"""
    from django.conf import settings
    from django.utils import translation
    
    path = request.path
    current_language = translation.get_language()
    
    # Remove language prefix if it exists
    for lang_code, lang_name in settings.LANGUAGES:
        if path.startswith(f'/{lang_code}/'):
            path = path[len(f'/{lang_code}/'):]
            if not path.startswith('/'):
                path = '/' + path
            break
        elif path == f'/{lang_code}':
            path = '/'
            break
    
    # Add query string if present
    if request.GET:
        query_string = request.GET.urlencode()
        path = f'{path}?{query_string}'
    
    return path

@register.simple_tag(takes_context=True)
def get_breadcrumbs(context):
    request = context.get('request')
    if not request:
        return []

    from django.urls import resolve, Resolver404
    from django.utils.translation import gettext as _
    
    path = request.path
    # Try to strip language prefix
    from django.conf import settings
    from django.utils import translation
    for lang_code, lang_name in settings.LANGUAGES:
        if path.startswith(f'/{lang_code}/'):
            path = path[len(f'/{lang_code}/'):]
            if not path.startswith('/'):
                path = '/' + path
            break
        elif path == f'/{lang_code}':
            path = '/'
            break
            
    paths = [p for p in path.split('/') if p]
    breadcrumbs = []
    
    # Root is Home
    # But we don't return it here, template handles it explicitly
    current_url = '/'
    for p in paths:
        current_url += p + '/'
        
        # Clean the name: e.g., sales-tax-calculator -> Sales Tax Calculator
        clean_name = p.replace('-', ' ').replace('_', ' ').title()
        
        # We can try to use resolver to check if valid, or just yield it
        breadcrumbs.append({
            'name': _(clean_name),
            'url': current_url
        })
        
    return breadcrumbs
