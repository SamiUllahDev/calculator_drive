from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from allauth.account.models import EmailAddress
from .models import Notification, UserSession
import re

class EmailVerificationMiddleware(MiddlewareMixin):
    """
    Middleware to check if a user's email is verified and handle redirections and notifications
    """
    
    # URLs that are accessible without email verification
    EXEMPT_URLS = [
        r'^/admin/',
        r'^/accounts/logout/',
        r'^/accounts/confirm-email/',
        r'^/accounts/email-verification-sent/',
        r'^/accounts/password/reset/',
        r'^/accounts/inactive/',
        r'^/static/',
        r'^/media/',
        r'^/$',
        r'^/tools/',
    ]
    
    def process_request(self, request):
        if not request.user.is_authenticated:
            return None
        
        # Skip verification check for exempt URLs
        path = request.path_info
        for exempt_url in self.EXEMPT_URLS:
            if re.match(exempt_url, path):
                return None
        
        # Skip for admin users
        if request.user.is_staff or request.user.is_superuser:
            return None
            
        # Check if email is verified
        is_verified = EmailAddress.objects.filter(
            user=request.user, 
            verified=True
        ).exists()
        
        # If not verified, create notification if one doesn't exist
        if not is_verified:
            # Check if verification notification already exists
            notification_exists = Notification.objects.filter(
                user=request.user,
                title=_("Email Verification Required"),
                is_read=False
            ).exists()
            
            if not notification_exists:
                # Create verification notification
                Notification.objects.create(
                    user=request.user,
                    title=_("Email Verification Required"),
                    message=_("Please verify your email address to access all features. Check your inbox or spam folder for the verification email."),
                    notification_type='warning',
                    link=reverse('account_email'),
                    icon='fa-envelope'
                )
            
            # Don't allow access to profile pages
            if path.startswith('/user/profile'):
                messages.warning(
                    request, 
                    _("You need to verify your email address before accessing your profile. "
                      "Please check your inbox or spam folder for the verification email.")
                )
                return redirect('account_email')
        
        # If verified, remove any verification notifications
        elif is_verified:
            Notification.objects.filter(
                user=request.user,
                title=_("Email Verification Required"),
            ).delete()
            
        return None


class UserSessionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user sessions
    """
    
    def process_request(self, request):
        if request.user.is_authenticated and hasattr(request, 'session') and request.session.session_key:
            session_key = request.session.session_key
            
            # Get IP address
            ip_address = None
            if 'HTTP_X_FORWARDED_FOR' in request.META:
                ip_address = request.META['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()
            elif 'REMOTE_ADDR' in request.META:
                ip_address = request.META['REMOTE_ADDR']
            
            # Get user agent
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Update or create session
            UserSession.objects.update_or_create(
                session_key=session_key,
                defaults={
                    'user': request.user,
                    'ip_address': ip_address,
                    'user_agent': user_agent[:500],  # Limit length
                    'is_active': True,
                }
            )
        
        return None
