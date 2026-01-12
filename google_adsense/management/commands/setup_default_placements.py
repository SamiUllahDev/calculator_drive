from django.core.management.base import BaseCommand
from google_adsense.models import AdPlacement


class Command(BaseCommand):
    help = 'Creates default ad placement locations'

    def handle(self, *args, **options):
        default_placements = [
            {
                'name': 'header_banner',
                'description': 'Banner ad in the header section',
                'template_tag': 'show_ads header_banner',
            },
            {
                'name': 'sidebar_top',
                'description': 'Ad at the top of the sidebar',
                'template_tag': 'show_ads sidebar_top',
            },
            {
                'name': 'sidebar_middle',
                'description': 'Ad in the middle of the sidebar',
                'template_tag': 'show_ads sidebar_middle',
            },
            {
                'name': 'sidebar_bottom',
                'description': 'Ad at the bottom of the sidebar',
                'template_tag': 'show_ads sidebar_bottom',
            },
            {
                'name': 'content_top',
                'description': 'Ad at the top of content area',
                'template_tag': 'show_ads content_top',
            },
            {
                'name': 'content_middle',
                'description': 'Ad in the middle of content',
                'template_tag': 'show_ads content_middle',
            },
            {
                'name': 'content_bottom',
                'description': 'Ad at the bottom of content',
                'template_tag': 'show_ads content_bottom',
            },
            {
                'name': 'before_post',
                'description': 'Ad before blog post content',
                'template_tag': 'show_ads before_post',
            },
            {
                'name': 'after_post',
                'description': 'Ad after blog post content',
                'template_tag': 'show_ads after_post',
            },
            {
                'name': 'between_posts',
                'description': 'Ad between blog posts in list view',
                'template_tag': 'show_ads between_posts',
            },
            {
                'name': 'footer',
                'description': 'Ad in the footer section',
                'template_tag': 'show_ads footer',
            },
            {
                'name': 'sticky',
                'description': 'Sticky ad that follows scroll',
                'template_tag': 'show_ads sticky',
            },
        ]

        created_count = 0
        updated_count = 0

        for placement_data in default_placements:
            placement, created = AdPlacement.objects.get_or_create(
                name=placement_data['name'],
                defaults={
                    'description': placement_data['description'],
                    'template_tag': placement_data['template_tag'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created placement: {placement.name}')
                )
            else:
                # Update existing placement
                placement.description = placement_data['description']
                placement.template_tag = placement_data['template_tag']
                placement.is_active = True
                placement.save()
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Updated placement: {placement.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created {created_count} placements and updated {updated_count} placements.'
            )
        )
