from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Update the Django Sites framework domain to match settings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain to set (defaults to SITE_URL from settings)',
        )

    def handle(self, *args, **options):
        # Get domain from argument or settings
        domain = options.get('domain')
        if not domain:
            # Extract domain from SITE_URL setting
            site_url = getattr(settings, 'SITE_URL', 'https://carepdf.com')
            domain = site_url.replace('https://', '').replace('http://', '')
        
        # Update the site
        site = Site.objects.get_current()
        old_domain = site.domain
        site.domain = domain
        site.name = 'CarePDF'  # Update name as well
        site.save()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated site domain from "{old_domain}" to "{domain}"'
            )
        )
        
        # Verify the change
        updated_site = Site.objects.get_current()
        self.stdout.write(f'Current site: {updated_site.domain} ({updated_site.name})')
