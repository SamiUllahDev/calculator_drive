from allauth.account.models import EmailAddress
import requests
from django.core.files.base import ContentFile
import os
import logging
from .models import Notification

logger = logging.getLogger(__name__)

def is_email_verified(user):
    """Check if user has verified email"""
    if not user or not user.is_authenticated:
        return False
    return EmailAddress.objects.filter(user=user, verified=True).exists()

def create_notification(user, title, message, notification_type='info', link=None, icon=None):
    """
    Create a notification for a user
    
    Args:
        user: User object to create notification for
        title: Notification title
        message: Notification message content
        notification_type: Type of notification (info, success, warning, error)
        link: Optional URL to include with notification
        icon: Optional icon class to override default
    
    Returns:
        Notification object that was created
    """
    if not user or not user.is_authenticated:
        return None
    
    # Set default icon based on notification type if not provided
    if not icon:
        icon_mapping = {
            'info': '',
            'success': '',
            'warning': '',
            'error': ''
        }
        icon = icon_mapping.get(notification_type, '')
    
    # Create and return the notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        icon=icon,
        link=link
    )
    
    return notification

def download_social_avatar(profile, url):
    """
    Download avatar from social provider URL
    
    Args:
        profile: User profile object
        url: URL to download avatar from
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not url:
        return False
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to download avatar from {url}. Status code: {response.status_code}")
            return False
        
        # Get file extension
        content_type = response.headers.get('content-type', '')
        if 'image/jpeg' in content_type:
            ext = 'jpg'
        elif 'image/png' in content_type:
            ext = 'png'
        else:
            ext = 'jpg'  # Default to jpg
        
        # Create a unique filename
        filename = f"social_avatar_{profile.user.id}.{ext}"
        
        # Save the file to the profile's avatar field
        profile.avatar.save(filename, ContentFile(response.content), save=True)
        
        return True
    
    except Exception as e:
        logger.error(f"Error downloading avatar: {str(e)}")
        return False 