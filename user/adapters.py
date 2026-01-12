from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.translation import gettext_lazy as _
from allauth.account.models import EmailAddress
from .models import Profile
from django.db import transaction
from django.conf import settings
from .utils import download_social_avatar

class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter for regular account signup/login"""
    pass

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for social account login"""
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        If email exists and is verified, don't allow auto signup
        """
        email = sociallogin.user.email
        return super().is_auto_signup_allowed(request, sociallogin)
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields from social login data
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Get data from social account
        social_data = sociallogin.account.extra_data
        
        # Get profile data
        if sociallogin.account.provider == 'google':
            # Set user's name from Google profile
            if 'name' in social_data:
                name_parts = social_data['name'].split(' ', 1)
                if len(name_parts) > 0:
                    user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                    
            # Set profile picture URL
            if 'picture' in social_data:
                # We'll handle this in the save_user method
                user.socialaccount_picture = social_data.get('picture')
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the user and create/update profile
        """
        with transaction.atomic():
            # Save the user
            user = super().save_user(request, sociallogin, form)
            
            # Create or get user profile
            profile, created = Profile.objects.get_or_create(user=user)
            
            # Update profile with social data
            social_data = sociallogin.account.extra_data
            
            # Download and set avatar from social provider if available
            if hasattr(user, 'socialaccount_picture') and user.socialaccount_picture:
                # Only set avatar if the user doesn't already have one or if it's a new profile
                if not profile.avatar or created:
                    download_social_avatar(profile, user.socialaccount_picture)
            
            # Ensure email is verified for social accounts
            EmailAddress.objects.update_or_create(
                user=user,
                email=user.email,
                defaults={
                    'verified': True,
                    'primary': True
                }
            )
            
            return user 