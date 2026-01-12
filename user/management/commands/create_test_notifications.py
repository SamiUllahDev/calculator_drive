from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from user.models import Notification
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
    help = 'Creates test notifications for development'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to create notifications for')
        parser.add_argument('--count', type=int, default=5, help='Number of notifications to create')

    def handle(self, *args, **options):
        username = options['username']
        count = options['count']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
            return
        
        notification_types = ['info', 'success', 'warning', 'error']
        
        sample_notifications = [
            {
                'title': _('Welcome to BlueSEO Tools!'),
                'message': _('Thanks for joining our platform. Explore our tools and boost your SEO strategy.'),
                'notification_type': 'info',
            },
            {
                'title': _('Profile Updated'),
                'message': _('Your profile information has been successfully updated.'),
                'notification_type': 'success',
            },
            {
                'title': _('Subscription Expiring'),
                'message': _('Your premium subscription will expire in 7 days. Renew now to avoid interruption.'),
                'notification_type': 'warning',
            },
            {
                'title': _('Backlink Report Complete'),
                'message': _('Your backlink analysis report is now ready to view.'),
                'notification_type': 'success',
                'link': '/tools/backlink-link/backlink-checker/',
            },
            {
                'title': _('Security Alert'),
                'message': _('We detected an unusual login attempt on your account. Please verify it was you.'),
                'notification_type': 'error',
            },
            {
                'title': _('New Feature Available'),
                'message': _('Try our new Keyword Research tool with AI suggestions.'),
                'notification_type': 'info',
                'link': '/tools/keyword-content/',
            },
            {
                'title': _('Saved Report Ready'),
                'message': _('The SEO report you requested for example.com is now available.'),
                'notification_type': 'success',
            },
            {
                'title': _('Complete Your Profile'),
                'message': _('Add your social media links to complete your profile and improve networking.'),
                'notification_type': 'warning',
                'link': '/user/profile/edit/',
            },
        ]
        
        created_count = 0
        for i in range(min(count, len(sample_notifications))):
            notif = sample_notifications[i]
            Notification.objects.create(
                user=user,
                title=notif['title'],
                message=notif['message'],
                notification_type=notif['notification_type'],
                link=notif.get('link')
            )
            created_count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} test notifications for {username}')) 