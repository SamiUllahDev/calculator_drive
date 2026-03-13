from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q

from .models import Post
from user.views import create_notification

User = get_user_model()

@receiver(post_save, sender=Post)
def send_notification_on_post_publish(sender, instance, created, **kwargs):
    """
    Send a notification to all users when an admin publishes a new blog post
    """
    # Only trigger when:
    # 1. Post is published (not draft)
    # 2. Post is created by an admin/staff user
    # 3. If not created but status changed from draft to published
    
    is_published = instance.status == 'published'
    is_admin_author = instance.author.is_staff or instance.author.is_superuser
    
    if is_published and is_admin_author:
        # For newly created and published posts
        if created:
            notify_users_about_new_post(instance)
        else:
            # For posts that were drafts and now are published
            # We can tell by checking if published_date was just set (within last minute)
            if instance.published_date and (timezone.now() - instance.published_date).total_seconds() < 60:
                notify_users_about_new_post(instance)


def notify_users_about_new_post(post):
    """
    Send notification to all active users about a new blog post
    """
    # Get active users who have email notifications enabled
    # We use the profile's email_notifications field if it exists
    users = User.objects.filter(is_active=True)
    
    # Create notification for each user
    batch_notifications = []
    for user in users:
        # Skip the author of the post
        if user == post.author:
            continue
            
        # Check if user has email notifications enabled
        send_notification = True
        try:
            if hasattr(user, 'profile') and not user.profile.email_notifications:
                send_notification = False
        except:
            # If profile doesn't exist or has no email_notifications field
            pass
        
        if send_notification:
            notification = create_notification(
                user=user,
                title=_("New Blog Post Published"),
                message=_("%(author)s has published a new article: %(title)s") % {
                    'author': post.author.get_full_name() or post.author.username,
                    'title': post.title
                },
                notification_type='info',
                icon='',
                link=post.get_absolute_url()
            )
            batch_notifications.append(notification)
    
    return batch_notifications


@receiver(post_save, sender=Post)
def notify_mentioned_users(sender, instance, **kwargs):
    """
    Send notifications to users who are mentioned in a blog post
    This function scans the post content for @username mentions and notifies those users
    """
    # Check for @username mentions in content
    content = instance.content
    # Simple regex pattern to find @username
    import re
    mentioned_usernames = re.findall(r'@(\w+)', content)
    
    if mentioned_usernames:
        for username in mentioned_usernames:
            try:
                mentioned_user = User.objects.get(username=username)
                
                # Don't notify the author about their own mentions
                if mentioned_user == instance.author:
                    continue
                    
                # Create notification for the mentioned user
                create_notification(
                    user=mentioned_user,
                    title=_("You were mentioned in a blog post"),
                    message=_("%(author)s mentioned you in the blog post: %(title)s") % {
                        'author': instance.author.get_full_name() or instance.author.username,
                        'title': instance.title
                    },
                    notification_type='info',
                    icon='',
                    link=instance.get_absolute_url()
                )
            except User.DoesNotExist:
                # Username doesn't exist, just skip
                continue 