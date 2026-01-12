from .models import Notification
from django.db.models import Count
from .utils import is_email_verified

def notifications_processor(request):
    """
    Context processor to add notifications data to templates
    """
    context_data = {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'is_email_verified': False
    }
    
    # Check if user attribute exists and is authenticated
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            # Get unread notifications count
            context_data['unread_notifications_count'] = Notification.objects.filter(
                user=request.user, 
                is_read=False
            ).count()
            
            # Get 5 most recent notifications
            context_data['recent_notifications'] = Notification.objects.filter(
                user=request.user
            ).order_by('-created_at')[:5]
            
            # Check if email is verified
            context_data['is_email_verified'] = is_email_verified(request.user)
        except Exception:
            # Handle any errors gracefully
            pass
    
    return context_data 