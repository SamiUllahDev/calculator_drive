"""
Management command to set up Google OAuth for social login.
Usage:
    python manage.py setup_google_oauth --client-id=YOUR_CLIENT_ID --client-secret=YOUR_CLIENT_SECRET
    
Or interactively:
    python manage.py setup_google_oauth
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp


class Command(BaseCommand):
    help = 'Set up Google OAuth2 credentials for social login'

    def add_arguments(self, parser):
        parser.add_argument(
            '--client-id',
            type=str,
            help='Google OAuth2 Client ID',
        )
        parser.add_argument(
            '--client-secret',
            type=str,
            help='Google OAuth2 Client Secret',
        )

    def handle(self, *args, **options):
        client_id = options.get('client_id')
        client_secret = options.get('client_secret')

        if not client_id:
            client_id = input('Enter Google OAuth2 Client ID: ').strip()
        if not client_secret:
            client_secret = input('Enter Google OAuth2 Client Secret: ').strip()

        if not client_id or not client_secret:
            self.stderr.write(self.style.ERROR('Both Client ID and Client Secret are required.'))
            return

        # Get or create the SocialApp
        social_app, created = SocialApp.objects.update_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': client_id,
                'secret': client_secret,
            }
        )

        # Associate with all sites
        sites = Site.objects.all()
        social_app.sites.set(sites)

        if created:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Google OAuth app created successfully!\n'
                f'   Client ID: {client_id[:20]}...\n'
                f'   Associated with {sites.count()} site(s)'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'✅ Google OAuth app updated successfully!\n'
                f'   Client ID: {client_id[:20]}...\n'
                f'   Associated with {sites.count()} site(s)'
            ))

        self.stdout.write(self.style.WARNING(
            '\n📋 Next steps:\n'
            '1. Go to https://console.cloud.google.com/apis/credentials\n'
            '2. Make sure your OAuth2 client has these Authorized redirect URIs:\n'
            '   - http://localhost:8000/accounts/google/login/callback/\n'
            '   - https://calculatordrive.com/accounts/google/login/callback/\n'
            '3. Under "OAuth consent screen", ensure the app is configured correctly\n'
            '4. Restart the Django development server\n'
        ))
