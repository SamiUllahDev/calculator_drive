from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import Category, Post, Comment, Tag
from .signals import notify_users_about_new_post

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_post_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_post_count(self, obj):
        return obj.posts.count()
    get_post_count.short_description = 'Posts'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_date',)
    fields = ('user', 'author_name', 'author_email', 'content', 'approved', 'created_date')
    
    def has_add_permission(self, request, obj=None):
        return False
    
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'published_date', 'view_count', 'get_comments', 'seo_status', 'view_on_site')
    list_filter = ('status', 'category', 'author', 'published_date', 'no_index')
    search_fields = ('title', 'content', 'excerpt', 'author__username', 'meta_title', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    inlines = [CommentInline]
    date_hierarchy = 'published_date'
    filter_horizontal = ('tags',)
    actions = ['make_published', 'make_draft', 'notify_users', 'reset_view_count']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'tags')
        }),
        ('Content', {
            'fields': ('featured_image', 'image_caption', 'image_alt', 'content', 'excerpt')
        }),
        ('Publication', {
            'fields': ('status', 'created_date', 'updated_date', 'published_date')
        }),
        ('Analytics', {
            'classes': ('collapse',),
            'fields': ('view_count',),
        }),
        ('SEO', {
            'classes': ('collapse',),
            'fields': ('meta_title', 'meta_description', 'meta_keywords', 'canonical_url', 'no_index'),
            'description': _('SEO fields help improve search engine visibility. Meta title should be 50-60 characters, meta description 150-160 characters.')
        }),
        ('Notifications', {
            'classes': ('collapse',),
            'fields': (),
            'description': _('Use the "Notify Users" action from the admin actions dropdown to manually send notifications about this post.')
        }),
    )
    
    readonly_fields = ('created_date', 'updated_date', 'view_count')
    
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        
        # Set published_date when status changes to published
        if 'status' in form.changed_data and obj.status == 'published' and not obj.published_date:
            obj.published_date = timezone.now()
            
        obj.save()
    
    def get_comments(self, obj):
        count = obj.comments.count()
        approved = obj.comments.filter(approved=True).count()
        return f"{approved}/{count}"
    get_comments.short_description = 'Comments (approved/total)'
    
    def seo_status(self, obj):
        if obj.meta_title and obj.meta_description:
            return True
        return False
    seo_status.boolean = True
    seo_status.short_description = 'SEO Ready'
    
    def view_on_site(self, obj):
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">View Post</a>', url)
        return None
    
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        for post in queryset:
            if not post.published_date:
                post.published_date = timezone.now()
                post.save()
        self.message_user(request, f'{updated} posts have been marked as published.')
    make_published.short_description = "Mark selected posts as published"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} posts have been marked as draft.')
    make_draft.short_description = "Mark selected posts as draft"
    
    def notify_users(self, request, queryset):
        """Admin action to manually send notifications about blog posts"""
        published_count = 0
        notification_count = 0
        
        for post in queryset:
            # Only send notifications for published posts
            if post.status == 'published':
                # Call the notification function directly
                notifications = notify_users_about_new_post(post)
                notification_count += len(notifications)
                published_count += 1
            else:
                self.message_user(
                    request,
                    _('Post "{}" must be published before sending notifications.').format(post.title),
                    level=messages.WARNING
                )
        
        if published_count > 0:
            self.message_user(
                request,
                _('Successfully sent {notification_count} notifications about {post_count} posts.').format(
                    notification_count=notification_count,
                    post_count=published_count
                ),
                level=messages.SUCCESS
            )
    notify_users.short_description = "Send notifications about selected posts"
    
    def reset_view_count(self, request, queryset):
        """Admin action to reset view count for selected posts"""
        updated = queryset.update(view_count=0)
        self.message_user(request, f'{updated} posts have had their view count reset.')
    reset_view_count.short_description = "Reset view count for selected posts"

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'author_name', 'post', 'created_date', 'approved', 'view_comment')
    list_filter = ('approved', 'created_date')
    search_fields = ('author_name', 'author_email', 'content', 'post__title')
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f'{updated} comments have been approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f'{updated} comments have been disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"
    
    def view_comment(self, obj):
        url = obj.post.get_absolute_url()
        return format_html('<a href="{}" target="_blank">View on post</a>', url)
    view_comment.short_description = 'View on post'
