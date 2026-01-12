from django.core.management.base import BaseCommand
from django.db.models import Q
from blog.models import Post
import time
import os

class Command(BaseCommand):
    help = 'Regenerates all blog post image thumbnails for optimization'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting thumbnail regeneration...'))
        
        # Get all posts with images
        posts = Post.objects.exclude(Q(featured_image='') | Q(featured_image=None))
        count = posts.count()
        
        self.stdout.write(self.style.SUCCESS(f'Found {count} posts with images to process'))
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No posts with images found. Exiting.'))
            return
        
        # Process each post
        processed = 0
        errors = 0
        
        for post in posts:
            try:
                # Check if the original image exists
                if not os.path.exists(post.featured_image.path):
                    self.stdout.write(self.style.WARNING(f'Image not found for post: {post.title}'))
                    errors += 1
                    continue
                
                # Force imagekit to regenerate thumbnails by accessing the url property
                # This causes the thumbnail to be generated if it doesn't exist
                medium_url = post.featured_image_medium.url
                thumbnail_url = post.featured_image_thumbnail.url
                small_url = post.featured_image_small.url
                
                self.stdout.write(f'Processed post: {post.title}')
                processed += 1
                
                # Add a small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing post {post.id}: {str(e)}'))
                errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'Thumbnail regeneration complete!'))
        self.stdout.write(self.style.SUCCESS(f'Successfully processed: {processed}'))
        
        if errors > 0:
            self.stdout.write(self.style.WARNING(f'Errors encountered: {errors}')) 