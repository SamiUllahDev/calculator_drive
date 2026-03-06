from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html, strip_tags
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django import forms
from tinymce.widgets import TinyMCE
from django.conf import settings
from .models import Category, Post, Comment, Tag
from .signals import notify_users_about_new_post


# ---------------------------------------------------------------------------
# Admin Form with TinyMCE for Post content
# ---------------------------------------------------------------------------
class PostAdminForm(forms.ModelForm):
    """Custom admin form that uses TinyMCE for content editing with SEO helpers."""
    
    content = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 40}),
        help_text=_('Use H2-H6 headings for structure. Add alt text to all images. '
                     'Use internal links to other calculators for SEO.')
    )
    
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'meta_description': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 160,
                'style': 'width: 100%;',
                'placeholder': 'Write a compelling description (150-160 chars)...',
            }),
            'meta_title': forms.TextInput(attrs={
                'maxlength': 70,
                'style': 'width: 100%;',
                'placeholder': 'Custom SEO title (50-60 chars ideal)...',
            }),
            'meta_keywords': forms.TextInput(attrs={
                'style': 'width: 100%;',
                'placeholder': 'keyword1, keyword2, keyword3...',
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 300,
                'style': 'width: 100%;',
                'placeholder': 'Brief summary shown in post listings (300 chars max)...',
            }),
            'image_alt': forms.TextInput(attrs={
                'style': 'width: 100%;',
                'placeholder': 'Descriptive alt text for the featured image (important for SEO)...',
            }),
            'image_caption': forms.TextInput(attrs={
                'style': 'width: 100%;',
                'placeholder': 'Caption displayed below the featured image...',
            }),
        }


# ---------------------------------------------------------------------------
# Category Admin
# ---------------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'get_post_count')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_post_count(self, obj):
        return obj.posts.count()
    get_post_count.short_description = 'Posts'


# ---------------------------------------------------------------------------
# Tag Admin
# ---------------------------------------------------------------------------
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


# ---------------------------------------------------------------------------
# Comment Inline
# ---------------------------------------------------------------------------
class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_date',)
    fields = ('user', 'author_name', 'author_email', 'content', 'approved', 'created_date')
    
    def has_add_permission(self, request, obj=None):
        return False


# ---------------------------------------------------------------------------
# Post Admin — TinyMCE + Full SEO Panel
# ---------------------------------------------------------------------------
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    
    list_display = (
        'title', 'author', 'category', 'status',
        'published_date', 'view_count', 'get_comments',
        'seo_score_display', 'view_on_site',
    )
    list_filter = ('status', 'category', 'author', 'published_date', 'no_index')
    search_fields = (
        'title', 'content', 'excerpt', 'author__username',
        'meta_title', 'meta_description',
    )
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    inlines = [CommentInline]
    date_hierarchy = 'published_date'
    filter_horizontal = ('tags',)
    actions = ['make_published', 'make_draft', 'notify_users', 'reset_view_count']
    save_on_top = True
    
    fieldsets = (
        (_('Post Details'), {
            'fields': ('title', 'slug', 'author', 'category', 'tags'),
        }),
        (_('Featured Image'), {
            'fields': ('featured_image', 'image_alt', 'image_caption'),
            'description': _(
                'Recommended image size: 1200×630px (16:9). '
                'Always fill in the Alt Text for SEO and accessibility.'
            ),
        }),
        (_('Content'), {
            'fields': ('content', 'excerpt'),
            'description': _(
                'Tips: Use H2 for main sections, H3 for sub-sections. '
                'Add alt text to every image. Include internal links to calculators. '
                'Keep paragraphs short (2-3 sentences).'
            ),
        }),
        (_('Publication'), {
            'fields': ('status', 'published_date'),
        }),
        (_('SEO — Search Engine Optimization'), {
            'fields': (
                'seo_preview',
                'meta_title', 'meta_description',
                'meta_keywords', 'canonical_url', 'no_index',
            ),
            'description': _(
                'Optimize this post for search engines. '
                'Meta title: 50-60 chars. Meta description: 150-160 chars. '
                'If left blank, the post title and excerpt will be used.'
            ),
        }),
        (_('Analytics & Info'), {
            'classes': ('collapse',),
            'fields': ('view_count', 'created_date', 'updated_date'),
        }),
    )
    
    readonly_fields = ('created_date', 'updated_date', 'view_count', 'seo_preview')
    
    # ----- Custom display methods -----
    
    def seo_preview(self, obj):
        """Render a Google SERP preview snippet in the admin."""
        if not obj.pk:
            return mark_safe(
                '<div style="padding:16px;background:#f8f9fa;border-radius:8px;'
                'border:1px solid #e0e0e0;color:#666;font-size:13px;">'
                'Save the post first to see the SEO preview.</div>'
            )
        
        title = obj.meta_title or obj.title or 'Untitled Post'
        title_display = title[:60] + '...' if len(title) > 60 else title
        
        desc = obj.meta_description or obj.excerpt or strip_tags(obj.content)[:160]
        desc_display = desc[:160] + '...' if len(desc) > 160 else desc
        
        url = f'https://calculatordrive.com{obj.get_absolute_url()}'
        
        # SEO score
        score, checks = self._calculate_seo_score(obj)
        
        if score >= 80:
            score_color = '#16a34a'
            score_bg = '#f0fdf4'
            score_label = 'Excellent'
        elif score >= 60:
            score_color = '#ca8a04'
            score_bg = '#fefce8'
            score_label = 'Good'
        elif score >= 40:
            score_color = '#ea580c'
            score_bg = '#fff7ed'
            score_label = 'Needs Work'
        else:
            score_color = '#dc2626'
            score_bg = '#fef2f2'
            score_label = 'Poor'
        
        checks_html = ''
        for check in checks:
            icon = '✅' if check['pass'] else '❌'
            checks_html += (
                f'<div style="padding:4px 0;font-size:12px;color:#374151;">'
                f'{icon} {check["label"]}</div>'
            )
        
        return format_html(
            '<div style="display:flex;gap:24px;flex-wrap:wrap;">'
            # Google Preview
            '<div style="flex:1;min-width:340px;">'
            '<div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;'
            'letter-spacing:0.5px;margin-bottom:8px;">Google Preview</div>'
            '<div style="padding:16px;background:#fff;border-radius:8px;border:1px solid #e5e7eb;'
            'max-width:600px;font-family:Arial,sans-serif;">'
            '<div style="font-size:20px;color:#1a0dab;line-height:1.3;margin-bottom:4px;">{}</div>'
            '<div style="font-size:14px;color:#006621;margin-bottom:4px;">{}</div>'
            '<div style="font-size:14px;color:#545454;line-height:1.5;">{}</div>'
            '</div></div>'
            # SEO Score
            '<div style="min-width:200px;">'
            '<div style="font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;'
            'letter-spacing:0.5px;margin-bottom:8px;">SEO Score</div>'
            '<div style="text-align:center;padding:12px 16px;background:{};border-radius:8px;'
            'border:1px solid {};margin-bottom:12px;">'
            '<div style="font-size:32px;font-weight:700;color:{};">{}/100</div>'
            '<div style="font-size:12px;color:{};font-weight:600;">{}</div>'
            '</div>'
            '<div>{}</div>'
            '</div></div>',
            title_display, url, desc_display,
            score_bg, score_color, score_color, score, score_color, score_label,
            checks_html,
        )
    seo_preview.short_description = 'SEO Analysis'
    
    def _calculate_seo_score(self, obj):
        """Calculate an SEO score (0-100) with individual checks."""
        checks = []
        score = 0
        
        # 1. Meta title (15 pts)
        if obj.meta_title:
            title_len = len(obj.meta_title)
            if 30 <= title_len <= 60:
                checks.append({'pass': True, 'label': f'Meta title length: {title_len} chars (ideal: 50-60)'})
                score += 15
            elif title_len > 0:
                checks.append({'pass': False, 'label': f'Meta title length: {title_len} chars (ideal: 50-60)'})
                score += 8
        else:
            checks.append({'pass': False, 'label': 'Meta title not set (using post title)'})
            score += 5  # Still gets some points for having a title
        
        # 2. Meta description (15 pts)
        if obj.meta_description:
            desc_len = len(obj.meta_description)
            if 120 <= desc_len <= 160:
                checks.append({'pass': True, 'label': f'Meta description: {desc_len} chars (ideal: 150-160)'})
                score += 15
            elif desc_len > 0:
                checks.append({'pass': False, 'label': f'Meta description: {desc_len} chars (ideal: 150-160)'})
                score += 8
        else:
            checks.append({'pass': False, 'label': 'Meta description not set'})
        
        # 3. Featured image with alt text (10 pts)
        if obj.featured_image:
            if obj.image_alt:
                checks.append({'pass': True, 'label': 'Featured image has alt text'})
                score += 10
            else:
                checks.append({'pass': False, 'label': 'Featured image missing alt text'})
                score += 5
        else:
            checks.append({'pass': False, 'label': 'No featured image'})
        
        # 4. Content length (15 pts)
        content_text = strip_tags(obj.content or '')
        word_count = len(content_text.split())
        if word_count >= 1000:
            checks.append({'pass': True, 'label': f'Content: {word_count} words (good for SEO)'})
            score += 15
        elif word_count >= 500:
            checks.append({'pass': True, 'label': f'Content: {word_count} words (decent, 1000+ preferred)'})
            score += 10
        elif word_count >= 200:
            checks.append({'pass': False, 'label': f'Content: {word_count} words (too short, aim for 1000+)'})
            score += 5
        else:
            checks.append({'pass': False, 'label': f'Content: {word_count} words (very short)'})
        
        # 5. Has headings in content (10 pts)
        content_lower = (obj.content or '').lower()
        has_h2 = '<h2' in content_lower
        has_h3 = '<h3' in content_lower
        if has_h2 and has_h3:
            checks.append({'pass': True, 'label': 'Content uses H2 and H3 headings'})
            score += 10
        elif has_h2 or has_h3:
            checks.append({'pass': True, 'label': 'Content uses headings (add both H2 & H3)'})
            score += 6
        else:
            checks.append({'pass': False, 'label': 'No headings in content (add H2/H3 structure)'})
        
        # 6. Internal links (10 pts)
        has_internal_links = 'calculatordrive.com' in content_lower or 'href="/' in content_lower
        if has_internal_links:
            checks.append({'pass': True, 'label': 'Content has internal links'})
            score += 10
        else:
            checks.append({'pass': False, 'label': 'No internal links (link to calculators!)'})
        
        # 7. Excerpt (5 pts)
        if obj.excerpt:
            checks.append({'pass': True, 'label': 'Excerpt is set'})
            score += 5
        else:
            checks.append({'pass': False, 'label': 'No excerpt'})
        
        # 8. Tags (5 pts)
        if obj.pk and obj.tags.exists():
            checks.append({'pass': True, 'label': f'Has {obj.tags.count()} tag(s)'})
            score += 5
        else:
            checks.append({'pass': False, 'label': 'No tags assigned'})
        
        # 9. Images in content (10 pts)
        has_images = '<img' in content_lower
        if has_images:
            # Check for alt text in images
            import re
            imgs = re.findall(r'<img[^>]*>', obj.content or '', re.IGNORECASE)
            imgs_with_alt = [i for i in imgs if 'alt=' in i.lower() and 'alt=""' not in i.lower()]
            if len(imgs_with_alt) == len(imgs) and imgs:
                checks.append({'pass': True, 'label': f'{len(imgs)} image(s) all with alt text'})
                score += 10
            elif imgs:
                checks.append({'pass': False, 'label': f'{len(imgs_with_alt)}/{len(imgs)} images have alt text'})
                score += 5
        else:
            checks.append({'pass': False, 'label': 'No images in content'})
        
        # 10. Slug quality (5 pts)
        if obj.slug and len(obj.slug) <= 75 and '-' in obj.slug:
            checks.append({'pass': True, 'label': f'URL slug is clean ({len(obj.slug)} chars)'})
            score += 5
        elif obj.slug:
            checks.append({'pass': False, 'label': f'URL slug could be shorter ({len(obj.slug)} chars)'})
            score += 2
        
        return min(score, 100), checks
    
    def seo_score_display(self, obj):
        """Show SEO score as a colored badge in the list view."""
        score, _ = self._calculate_seo_score(obj)
        if score >= 80:
            color, bg = '#16a34a', '#f0fdf4'
        elif score >= 60:
            color, bg = '#ca8a04', '#fefce8'
        elif score >= 40:
            color, bg = '#ea580c', '#fff7ed'
        else:
            color, bg = '#dc2626', '#fef2f2'
        
        return format_html(
            '<span style="padding:3px 10px;border-radius:12px;font-size:12px;'
            'font-weight:600;background:{};color:{};">{}</span>',
            bg, color, f'{score}/100'
        )
    seo_score_display.short_description = 'SEO'
    seo_score_display.admin_order_field = 'meta_title'
    
    def get_comments(self, obj):
        count = obj.comments.count()
        approved = obj.comments.filter(approved=True).count()
        return f"{approved}/{count}"
    get_comments.short_description = 'Comments'
    
    def view_on_site(self, obj):
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html(
                '<a href="{}" target="_blank" style="color:#2563eb;">View ↗</a>', url
            )
        return '-'
    view_on_site.short_description = 'Link'
    
    # ----- Save logic -----
    
    def save_model(self, request, obj, form, change):
        if not obj.pk and not obj.author_id:
            obj.author = request.user
        
        # Auto-set published_date when status changes to published
        if obj.status == 'published' and not obj.published_date:
            obj.published_date = timezone.now()
        
        # Auto-generate excerpt from content if not provided
        if not obj.excerpt and obj.content:
            plain = strip_tags(obj.content)
            obj.excerpt = plain[:297] + '...' if len(plain) > 300 else plain
        
        obj.save()
    
    # ----- Admin actions -----
    
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        for post in queryset:
            if not post.published_date:
                post.published_date = timezone.now()
                post.save()
        self.message_user(request, f'{updated} posts marked as published.')
    make_published.short_description = "Publish selected posts"
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} posts marked as draft.')
    make_draft.short_description = "Unpublish selected posts (draft)"
    
    def notify_users(self, request, queryset):
        """Admin action to manually send notifications about blog posts"""
        published_count = 0
        notification_count = 0
        
        for post in queryset:
            if post.status == 'published':
                notifications = notify_users_about_new_post(post)
                notification_count += len(notifications)
                published_count += 1
            else:
                self.message_user(
                    request,
                    _('Post "{}" must be published first.').format(post.title),
                    level=messages.WARNING
                )
        
        if published_count > 0:
            self.message_user(
                request,
                _('{} notifications sent for {} posts.').format(
                    notification_count, published_count
                ),
                level=messages.SUCCESS
            )
    notify_users.short_description = "Send notifications about selected posts"
    
    def reset_view_count(self, request, queryset):
        updated = queryset.update(view_count=0)
        self.message_user(request, f'{updated} posts had view count reset.')
    reset_view_count.short_description = "Reset view count"
    
    # ----- Custom admin media -----
    
    class Media:
        css = {
            'all': ()
        }
        js = ()


# ---------------------------------------------------------------------------
# Comment Admin
# ---------------------------------------------------------------------------
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'author_name', 'post', 'created_date', 'approved', 'view_comment')
    list_filter = ('approved', 'created_date')
    search_fields = ('author_name', 'author_email', 'content', 'post__title')
    actions = ['approve_comments', 'disapprove_comments']
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(approved=True)
        self.message_user(request, f'{updated} comments approved.')
    approve_comments.short_description = "Approve selected comments"
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(approved=False)
        self.message_user(request, f'{updated} comments disapproved.')
    disapprove_comments.short_description = "Disapprove selected comments"
    
    def view_comment(self, obj):
        url = obj.post.get_absolute_url()
        return format_html('<a href="{}" target="_blank">View on post ↗</a>', url)
    view_comment.short_description = 'View'
