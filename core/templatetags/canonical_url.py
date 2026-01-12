from django import template

register = template.Library()


@register.simple_tag
def canonical_url_for_post(post, request):
    """Get the canonical URL for a blog post"""
    # Use custom canonical URL if set, otherwise use the post's absolute URL
    if post.canonical_url:
        return post.canonical_url
    return request.build_absolute_uri(post.get_absolute_url())
