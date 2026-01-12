from django import template
import re

register = template.Library()

@register.filter
def filter_community_notifications(notifications):
    """Filter notifications related to community activity"""
    community_related_keywords = [
        'topic', 'post', 'reply', 'solution', 'reputation', 
        'badge', 'community', 'forum', 'trending'
    ]
    
    # Build a regex pattern for matching
    pattern = '|'.join(community_related_keywords)
    regex = re.compile(pattern, re.IGNORECASE)
    
    # Filter notifications where title or message contains community keywords
    result = []
    for notification in notifications:
        if (regex.search(notification.title) or regex.search(notification.message)):
            result.append(notification)
            
    return result


@register.filter
def filter_blog_notifications(notifications):
    """Filter notifications related to blog activity"""
    blog_related_keywords = [
        'blog', 'article', 'post published', 'new article', 'mentioned'
    ]
    
    # Build a regex pattern for matching
    pattern = '|'.join(blog_related_keywords)
    regex = re.compile(pattern, re.IGNORECASE)
    
    # Filter notifications where title or message contains blog keywords
    result = []
    for notification in notifications:
        if (regex.search(notification.title) or regex.search(notification.message)):
            result.append(notification)
            
    return result 