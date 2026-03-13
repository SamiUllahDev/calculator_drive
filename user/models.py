from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.

class Activity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    description = models.TextField(verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Activity')
        verbose_name_plural = _('Activities')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s activity on {self.created_at}"

class Profile(models.Model):
    GENDER_CHOICES = (
        ('M', _('Male')),
        ('F', _('Female')),
        ('O', _('Other')),
        ('P', _('Prefer not to say'))
    )
    
    PRIVACY_CHOICES = (
        ('public', _('Public')),
        ('friends', _('Friends Only')),
        ('private', _('Private')),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, verbose_name=_('Biography'))
    avatar = models.ImageField(upload_to='uploads/avatars/', blank=True, null=True, verbose_name=_('Profile Picture'))
    website = models.URLField(blank=True, null=True, verbose_name=_('Website'))
    location = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Location'))
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_('Phone Number'))
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True, verbose_name=_('Gender'))
    birth_date = models.DateField(blank=True, null=True, verbose_name=_('Birth Date'))
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Company'))
    job_title = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Job Title'))
    twitter = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Twitter'))
    facebook = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Facebook'))
    linkedin = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('LinkedIn'))
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    email_notifications = models.BooleanField(default=True, verbose_name=_('Email Notifications'))
    
    # Privacy Settings
    profile_privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public', verbose_name=_('Profile Privacy'))
    show_email = models.BooleanField(default=False, verbose_name=_('Show Email on Profile'))
    show_location = models.BooleanField(default=True, verbose_name=_('Show Location on Profile'))
    show_birth_date = models.BooleanField(default=False, verbose_name=_('Show Birth Date on Profile'))
    
    # Preferences
    theme = models.CharField(max_length=20, default='light', choices=[('light', _('Light')), ('dark', _('Dark')), ('auto', _('Auto'))], verbose_name=_('Theme'))
    language = models.CharField(max_length=10, default='en', verbose_name=_('Language'))
    timezone = models.CharField(max_length=50, default='UTC', verbose_name=_('Timezone'))
    
    def __str__(self):
        return f"Profile of {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('user:profile', kwargs={'username': self.user.username})


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', _('Information')),
        ('success', _('Success')),
        ('warning', _('Warning')),
        ('error', _('Error')),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    message = models.TextField(verbose_name=_('Message'))
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, default='info', verbose_name=_('Type'))
    icon = models.CharField(max_length=50, default='', verbose_name=_('Icon Class'))
    link = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Link'))
    is_read = models.BooleanField(default=False, verbose_name=_('Read Status'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()
    
    def get_icon_class(self):
        icon_mapping = {
            'info': 'text-primary',
            'success': 'text-success',
            'warning': 'text-warning',
            'error': 'text-danger'
        }
        return icon_mapping.get(self.notification_type, '')


class UserSession(models.Model):
    """Track user login sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-last_activity']
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.created_at}"


class FavoriteCalculator(models.Model):
    """Store user's favorite calculators"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_calculators')
    calculator_name = models.CharField(max_length=255, verbose_name=_('Calculator Name'))
    calculator_url = models.CharField(max_length=500, verbose_name=_('Calculator URL'), db_index=True)
    calculator_category = models.CharField(max_length=100, blank=True, null=True, verbose_name=_('Category'))
    calculator_app = models.CharField(max_length=50, blank=True, null=True, verbose_name=_('App'))  # math, finance, health, other
    calculator_description = models.TextField(blank=True, null=True, verbose_name=_('Description'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Favorite Calculator')
        verbose_name_plural = _('Favorite Calculators')
        unique_together = [('user', 'calculator_url')]  # Prevent duplicates
        indexes = [
            models.Index(fields=['user', 'calculator_url']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.calculator_name}"
