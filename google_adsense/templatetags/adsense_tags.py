from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from django.db.models import Q
from google_adsense.models import AdUnit, AdPlacement
import re

register = template.Library()


@register.simple_tag(takes_context=True)
def show_ads(context, placement=None, limit=1):
    """
    Display ads for a specific placement
    
    Usage:
        {% load adsense_tags %}
        {% show_ads 'header' %}
        {% show_ads 'sidebar' 2 %}  # Show up to 2 ads
    """
    request = context.get('request')
    if not request:
        return ""
    
    # Get active ad units for this placement
    if placement:
        # Filter by placement name or custom placement
        from django.db.models import Q
        ad_units = AdUnit.objects.filter(
            is_active=True,
        ).filter(
            Q(placement=placement) | Q(custom_placement=placement)
        ).order_by('-priority', '?')[:limit]
    else:
        # Get all active ads (fallback)
        ad_units = AdUnit.objects.filter(is_active=True).order_by('-priority', '?')[:limit]
    
    # Filter ads that should be displayed based on request context
    displayed_ads = []
    for ad_unit in ad_units:
        if ad_unit.should_display(request, placement=placement):
            displayed_ads.append(ad_unit)
            if limit > 0 and len(displayed_ads) >= limit:
                break
    
    if not displayed_ads:
        return ""
    
    # Render ads
    html_output = []
    for ad_unit in displayed_ads:
        ad_html = render_ad_unit(ad_unit, request)
        if ad_html:
            html_output.append(ad_html)
    
    return mark_safe('\n'.join(html_output))


@register.simple_tag(takes_context=True)
def show_ad_unit(context, ad_unit_name):
    """
    Display a specific ad unit by name
    
    Usage:
        {% load adsense_tags %}
        {% show_ad_unit 'Header Banner' %}
    """
    request = context.get('request')
    if not request:
        return ""
    
    try:
        ad_unit = AdUnit.objects.get(name=ad_unit_name, is_active=True)
        if ad_unit.should_display(request, placement=None):
            return mark_safe(render_ad_unit(ad_unit, request))
    except AdUnit.DoesNotExist:
        pass
    
    return ""


@register.simple_tag(takes_context=True)
def show_ads_by_placement(context, placement_key):
    """
    Display ads by placement key (from AdPlacement model)
    
    Usage:
        {% load adsense_tags %}
        {% show_ads_by_placement 'header_banner' %}
    """
    request = context.get('request')
    if not request:
        return ""
    
    try:
        placement = AdPlacement.objects.get(name=placement_key, is_active=True)
        return show_ads(context, placement.name)
    except AdPlacement.DoesNotExist:
        return ""


@register.inclusion_tag('google_adsense/ad_wrapper.html', takes_context=True)
def ad_wrapper(context, placement=None, css_class='', limit=1):
    """
    Wrapper tag for ads with container div
    
    Usage:
        {% load adsense_tags %}
        {% ad_wrapper 'sidebar' 'ad-sidebar' %}
    """
    request = context.get('request')
    
    if placement:
        ad_units = AdUnit.objects.filter(
            is_active=True,
        ).filter(
            Q(placement=placement) | Q(custom_placement=placement)
        ).order_by('-priority', '?')[:limit]
    else:
        ad_units = AdUnit.objects.filter(is_active=True).order_by('-priority', '?')[:limit]
    
    displayed_ads = []
    for ad_unit in ad_units:
        if ad_unit.should_display(request):
            displayed_ads.append(ad_unit)
            if limit > 0 and len(displayed_ads) >= limit:
                break
    
    return {
        'ads': displayed_ads,
        'css_class': css_class,
        'request': request,
    }


def render_ad_unit(ad_unit, request):
    """
    Render a single ad unit with wrapper and styling
    """
    ad_code = ad_unit.get_ad_code_html()
    if not ad_code:
        return ""
    
    # Build CSS classes
    css_classes = ['adsense-ad-unit', f'adsense-{ad_unit.placement}']
    if ad_unit.css_class:
        css_classes.append(ad_unit.css_class)
    
    # Build wrapper HTML
    wrapper_html = f'<div class="{" ".join(css_classes)}" data-ad-unit="{ad_unit.name}" data-placement="{ad_unit.placement}">'
    
    # Add custom CSS if provided
    if ad_unit.custom_css:
        wrapper_html += f'<style>{ad_unit.custom_css}</style>'
    
    # Add ad code
    wrapper_html += ad_code
    
    # Close wrapper
    wrapper_html += '</div>'
    
    return wrapper_html


@register.simple_tag
def adsense_config():
    """
    Output AdSense configuration script (if needed)
    Usually placed in <head> section
    """
    # This can be used to add global AdSense configuration
    # For now, return empty - ads are configured per unit
    return ""


@register.filter
def is_adsense_enabled(value):
    """
    Check if AdSense is enabled in settings
    """
    return getattr(settings, 'GOOGLE_ADSENSE_ENABLED', True)
