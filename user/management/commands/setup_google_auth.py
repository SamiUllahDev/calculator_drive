from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Sets up the Google OAuth configuration for testing'

    def add_arguments(self, parser):
        parser.add_argument('--client_id', type=str, help='Google OAuth Client ID')
        parser.add_argument('--client_secret', type=str, help='Google OAuth Client Secret')
        parser.add_argument('--domain', type=str, default='localhost:8000', help='Site domain (default: localhost:8000)')
        
    def handle(self, *args, **options):
        # Set up site
        domain = options.get('domain', 'localhost:8000')
        client_id = options.get('client_id', '')
        client_secret = options.get('client_secret', '')
        
        # Update default site
        site, created = Site.objects.update_or_create(
            id=1,
            defaults={
                'domain': domain,
                'name': domain
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created site: {domain}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated site: {domain}'))
            
        # Create Google social app if client ID and secret are provided
        if client_id and client_secret:
            social_app, created = SocialApp.objects.update_or_create(
                provider='google',
                defaults={
                    'name': 'Google',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            # Make sure the app is associated with the site
            social_app.sites.add(site)
            
            if created:
                self.stdout.write(self.style.SUCCESS('Created Google social app'))
            else:
                self.stdout.write(self.style.SUCCESS('Updated Google social app'))
        else:
            self.stdout.write(self.style.WARNING(
                'No client_id or client_secret provided. Only site was updated. '
                'To set up Google auth, run:\n'
                f'python manage.py setup_google_auth --client_id=YOUR_CLIENT_ID --client_secret=YOUR_CLIENT_SECRET --domain={domain}'
            ))
            
        self.stdout.write(self.style.SUCCESS(
            '\nNext steps:\n'
            '1. Go to https://console.cloud.google.com/apis/credentials\n'
            '2. Create an OAuth Client ID (Web Application)\n'
            f'3. Add authorized redirect URI: http://{domain}/accounts/google/login/callback/\n'
            '4. Run this command again with the client ID and secret'
        )) 