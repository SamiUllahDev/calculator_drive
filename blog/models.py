from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils import timezone
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, ResizeToFit, Transpose
from tinymce.models import HTMLField
import os

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Ensure unique slug
        if Category.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            count = 1
            while Category.objects.filter(slug=f"{self.slug}-{count}").exists():
                count += 1
            self.slug = f"{self.slug}-{count}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:category_detail', kwargs={'slug': self.slug})

class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(max_length=50, unique=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:tag_detail', kwargs={'slug': self.slug})

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField(Tag, related_name='posts', blank=True)
    featured_image = models.ImageField(upload_to='blog/uploads/%Y/%m/', blank=True, null=True)
    image_caption = models.CharField(max_length=255, blank=True, null=True, help_text="Caption for the featured image")
    image_alt = models.CharField(max_length=255, blank=True, null=True, help_text="Alt text for the featured image (for accessibility and SEO)")
    
    # Optimized image versions
    featured_image_medium = ImageSpecField(
        source='featured_image',
        processors=[Transpose(), ResizeToFit(width=800, height=600, upscale=False)],
        format='JPEG',
        options={'quality': 85}
    )
    featured_image_thumbnail = ImageSpecField(
        source='featured_image',
        processors=[Transpose(), ResizeToFill(width=400, height=300)],
        format='JPEG',
        options={'quality': 80}
    )
    featured_image_small = ImageSpecField(
        source='featured_image',
        processors=[Transpose(), ResizeToFill(width=200, height=150)],
        format='JPEG',
        options={'quality': 75}
    )
    content = HTMLField()
    excerpt = models.TextField(max_length=300, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    published_date = models.DateTimeField(blank=True, null=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=70, blank=True, null=True, help_text="Custom title tag for SEO (70 chars max)")
    meta_description = models.TextField(max_length=160, blank=True, null=True, help_text="Custom meta description for SEO (160 chars max)")
    meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated keywords")
    canonical_url = models.URLField(blank=True, null=True, help_text="URL of the canonical version of this content")
    no_index = models.BooleanField(default=False, help_text="If checked, search engines will not index this page")
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0, help_text="Number of times this post has been viewed")
    
    class Meta:
        ordering = ['-created_date']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Ensure unique slug
        original_slug = self.slug
        
        # Check for conflicts with other posts
        if Post.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            count = 1
            while Post.objects.filter(slug=f"{self.slug}-{count}").exists():
                count += 1
            self.slug = f"{self.slug}-{count}"
        
        # Check for conflicts with categories
        if Category.objects.filter(slug=self.slug).exists():
            count = 1
            while Category.objects.filter(slug=f"{self.slug}-{count}").exists():
                count += 1
            self.slug = f"{self.slug}-{count}"
        
        # Set published date when status is changed to published
        if self.status == 'published' and not self.published_date:
            self.published_date = timezone.now()
            
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={
            'category_slug': self.category.slug,
            'slug': self.slug
        })
    
    @property
    def get_meta_title(self):
        if self.meta_title:
            return self.meta_title
        return self.title
    
    @property
    def get_meta_description(self):
        if self.meta_description:
            return self.meta_description
        if self.excerpt:
            return self.excerpt
        return self.content[:160].replace('"', '')
    
    @property
    def reading_time(self):
        """Calculate approximate reading time in minutes"""
        word_count = len(self.content.split())
        minutes = word_count // 200  # Average reading speed of 200 words per minute
        if minutes < 1:
            return "1 min read"
        return f"{minutes} min read"
        
    def has_image(self):
        """Check if the featured image exists and is accessible"""
        if self.featured_image and os.path.exists(self.featured_image.path):
            return True
        return False
        
    def safe_medium_url(self):
        """Safely get medium image URL"""
        try:
            if self.has_image():
                return self.featured_image_medium.url
        except:
            pass
        return None
        
    def safe_thumbnail_url(self):
        """Safely get thumbnail URL"""
        try:
            if self.has_image():
                return self.featured_image_thumbnail.url
        except:
            pass
        return None
        
    def safe_small_url(self):
        """Safely get small image URL"""
        try:
            if self.has_image():
                return self.featured_image_small.url
        except:
            pass
        return None
    
    def increment_view_count(self):
        """Increment view count atomically"""
        Post.objects.filter(id=self.id).update(view_count=models.F('view_count') + 1)
        self.refresh_from_db()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author_name = models.CharField(max_length=100)
    author_email = models.EmailField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    content = HTMLField()
    created_date = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    
    class Meta:
        ordering = ['created_date']
    
    def __str__(self):
        return f"Comment by {self.author_name} on {self.post.title}"
