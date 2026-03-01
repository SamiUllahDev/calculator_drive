from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sites.shortcuts import get_current_site
from django.utils.html import strip_tags
import re
import bleach
import os
import uuid
from user.utils import is_email_verified, create_notification

from .models import Post, Category, Comment, Tag
from .forms import CommentForm, ReplyForm

# Configure HTML sanitization settings
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'ul', 'ol', 'li', 
    'span', 'blockquote', 'pre', 'code', 's', 'sub', 'sup'
]

# Define allowed attributes
ALLOWED_ATTRIBUTES = {
    '*': ['class'],
    'span': ['style'],
    'p': ['style'],
}

def sanitize_html(html_content):
    """Remove disallowed HTML tags and attributes (images, links, etc.)"""
    
    # Clean using bleach to remove unwanted tags and attributes
    cleaned_content = bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True
    )
    
    # Additional regex to catch any remaining links or images
    cleaned_content = re.sub(r'<a[^>]*>.*?</a>', '', cleaned_content)
    cleaned_content = re.sub(r'<img[^>]*>', '', cleaned_content)
    
    return cleaned_content

@csrf_exempt
@login_required
def tinymce_image_upload(request):
    """Handle image uploads from TinyMCE editor with enhanced security"""
    # Check if user is staff (only staff should upload images for blog posts)
    if not request.user.is_staff:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    if request.method != 'POST' or 'file' not in request.FILES:
        return JsonResponse({'error': 'No file uploaded'}, status=400)
    
    image_file = request.FILES['file']
    
    # Validate file is an image by content type (first check)
    if not image_file.content_type.startswith('image/'):
        return JsonResponse({'error': 'Invalid file type'}, status=400)
    
    # Limit file size (5MB)
    if image_file.size > 5 * 1024 * 1024:
        return JsonResponse({'error': 'File too large (max 5MB)'}, status=400)
    
    # Validate file extension (whitelist approach)
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    _, ext = os.path.splitext(image_file.name.lower())
    if ext not in allowed_extensions:
        return JsonResponse({'error': 'Invalid file extension. Allowed: JPG, PNG, GIF, WEBP'}, status=400)
    
    # Validate actual file content using PIL/Pillow (prevents MIME type spoofing)
    try:
        from PIL import Image
        # Reset file pointer to beginning
        image_file.seek(0)
        # Try to open and verify it's a valid image
        img = Image.open(image_file)
        # Verify the image format
        if img.format not in ['JPEG', 'PNG', 'GIF', 'WEBP']:
            return JsonResponse({'error': 'Invalid image format'}, status=400)
        # Verify the image can be loaded (prevents malicious files)
        img.verify()
        # Reset file pointer again after verification
        image_file.seek(0)
    except Exception as e:
        return JsonResponse({'error': 'Invalid or corrupted image file'}, status=400)
    
    # Generate unique filename to prevent overwriting
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    # Save to blog uploads directory
    upload_path = f"blog/uploads/{timezone.now().strftime('%Y/%m')}/{unique_filename}"
    
    from django.core.files.storage import default_storage
    file_path = default_storage.save(upload_path, image_file)
    file_url = default_storage.url(file_path)
    
    # Return URL for TinyMCE
    return JsonResponse({
        'location': file_url
    })

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        queryset = Post.objects.filter(
            status='published', 
            published_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_date')
        
        # Search functionality
        search_query = self.request.GET.get('q', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(category__name__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
            
        # Filter by tag if provided
        tag = self.request.GET.get('tag', None)
        if tag:
            queryset = queryset.filter(tags__slug=tag)
            
        # Filter by date range
        date_filter = self.request.GET.get('date', None)
        if date_filter:
            today = timezone.now().date()
            if date_filter == 'today':
                queryset = queryset.filter(published_date__date=today)
            elif date_filter == 'week':
                week_ago = today - timezone.timedelta(days=7)
                queryset = queryset.filter(published_date__date__gte=week_ago)
            elif date_filter == 'month':
                month_ago = today - timezone.timedelta(days=30)
                queryset = queryset.filter(published_date__date__gte=month_ago)
            elif date_filter == 'year':
                year_ago = today - timezone.timedelta(days=365)
                queryset = queryset.filter(published_date__date__gte=year_ago)
        
        # Sorting options
        sort_by = self.request.GET.get('sort', None)
        if sort_by:
            if sort_by == 'title_asc':
                queryset = queryset.order_by('title')
            elif sort_by == 'title_desc':
                queryset = queryset.order_by('-title')
            elif sort_by == 'date_asc':
                queryset = queryset.order_by('published_date')
            elif sort_by == 'date_desc':
                queryset = queryset.order_by('-published_date')
            elif sort_by == 'popular':
                # This would require a view count field, for now we'll use comments count as a proxy
                queryset = queryset.annotate(comment_count=Count('comments')).order_by('-comment_count')
                
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all categories for the filter sidebar
        context['categories'] = Category.objects.all()
        
        # Get all tags for the filter sidebar
        context['tags'] = Tag.objects.all()
        
        # Get featured post (most recent published post with at least one comment) - optimized
        featured_post = Post.objects.filter(
            status='published',
            published_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').annotate(
            comment_count=Count('comments')
        ).filter(
            comment_count__gt=0
        ).order_by('-published_date').first()
        
        # If no post with comments, get the most recent post
        if not featured_post:
            featured_post = Post.objects.filter(
                status='published',
                published_date__lte=timezone.now()
            ).select_related('author', 'category').prefetch_related('tags').order_by('-published_date').first()
            
        context['featured_post'] = featured_post
        
        # Add search query to context
        context['search_query'] = self.request.GET.get('q', '')
        
        # Add filter parameters to context
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_date_filter'] = self.request.GET.get('date', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        
        # Keep current filters in pagination links
        get_copy = self.request.GET.copy()
        if 'page' in get_copy:
            get_copy.pop('page')
        context['current_query'] = get_copy.urlencode()
        
        return context

class CategoryPostListView(ListView):
    model = Post
    template_name = 'blog/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
        return Post.objects.filter(
            category=self.category,
            status='published',
            published_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        
        # Get query parameters for pagination
        get_copy = self.request.GET.copy()
        if 'page' in get_copy:
            get_copy.pop('page')
        context['current_query'] = get_copy.urlencode()
        
        return context

class TagPostListView(ListView):
    model = Post
    template_name = 'blog/tag_posts.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return Post.objects.filter(
            tags=self.tag,
            status='published',
            published_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').distinct().order_by('-published_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        
        # Get query parameters for pagination
        get_copy = self.request.GET.copy()
        if 'page' in get_copy:
            get_copy.pop('page')
        context['current_query'] = get_copy.urlencode()
        
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(
            status='published', 
            published_date__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags', 'comments')
    
    def get_object(self, queryset=None):
        """Get the post object and increment view count"""
        if queryset is None:
            queryset = self.get_queryset()
        
        # Get post by slug and category_slug
        category_slug = self.kwargs.get('category_slug')
        post_slug = self.kwargs.get('slug')
        
        obj = get_object_or_404(queryset, slug=post_slug, category__slug=category_slug)
        
        # Increment view count (only for published posts)
        if obj.status == 'published':
            obj.increment_view_count()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        
        # Add reading time to context
        context['reading_time'] = post.reading_time
        
        # Get comments (only top-level comments, i.e., those without a parent)
        # Optimize with prefetch_related
        context['comments'] = post.comments.filter(
            approved=True, 
            parent=None
        ).select_related('user', 'post').prefetch_related('replies').order_by('created_date')
        context['comment_count'] = post.comments.filter(approved=True).count()
        
        # Handle comment forms for authenticated users
        if self.request.user.is_authenticated:
            context['comment_form'] = CommentForm(user=self.request.user)
            context['reply_form'] = ReplyForm(user=self.request.user)
            context['user_email_verified'] = is_email_verified(self.request.user)
        
        # Get related posts (same category, recent) - optimized query
        category_posts = Post.objects.filter(
            category=post.category,
            status='published',
            published_date__lte=timezone.now()
        ).exclude(id=post.id).select_related('author', 'category').prefetch_related('tags')[:3]
        
        # If we don't have enough related posts from the same category,
        # add some recent posts from other categories
        if len(category_posts) < 3:
            # Using Q objects to exclude both the current post and the already selected category posts
            exclude_ids = [post.id] + [p.id for p in category_posts]
            recent_posts = Post.objects.filter(
                status='published',
                published_date__lte=timezone.now()
            ).exclude(id__in=exclude_ids).select_related('author', 'category').prefetch_related('tags').order_by('-published_date')[:3-len(category_posts)]
            
            # Combine the two querysets
            context['related_posts'] = list(category_posts) + list(recent_posts)
        else:
            context['related_posts'] = category_posts
        
        # Get next and previous posts for navigation - optimized queries
        context['prev_post'] = Post.objects.filter(
            status='published',
            published_date__lte=post.published_date
        ).exclude(id=post.id).select_related('author', 'category').order_by('-published_date').first()
        
        context['next_post'] = Post.objects.filter(
            status='published',
            published_date__gte=post.published_date
        ).exclude(id=post.id).select_related('author', 'category').order_by('published_date').first()
        
        # SEO meta tags
        context['meta_title'] = post.get_meta_title
        context['meta_description'] = post.get_meta_description
        context['meta_keywords'] = post.meta_keywords
        # Use custom canonical URL if set, otherwise use the post's get_absolute_url
        context['canonical_url'] = post.canonical_url if post.canonical_url else post.get_absolute_url()
        context['no_index'] = post.no_index
        
        # Add random calculator tools for SEO Resources section (optional)
        import random
        context['random_pdf_tools'] = []
        
        # Try to get calculator tools from various calculator apps
        try:
            # Try Math Calculators
            from Math_Calculators.views.index import MathIndexView
            index_view = MathIndexView()
            index_context = index_view.get_context_data()
            all_tools = []
            
            if 'calculators' in index_context:
                for calc in index_context['calculators']:
                    url_slug = calc.get('url', '')
                    if not url_slug:
                        continue
                    # Convert URL slug (with hyphens) to URL name (with underscores)
                    url_name = url_slug.replace('-', '_')
                    all_tools.append({
                        'name': calc.get('name', ''),
                        'description': calc.get('description', ''),
                        'icon': 'bi bi-calculator',
                        'url_name': f"math_calculators:{url_name}",
                        'category': calc.get('category', 'Math')
                    })
            
            # Try Financial Calculators
            try:
                from Financial_Calculators.views.index import FinanceIndexView
                finance_view = FinanceIndexView()
                finance_context = finance_view.get_context_data()
                if 'calculators' in finance_context:
                    for calc in finance_context['calculators']:
                        url_slug = calc.get('url', '')
                        if not url_slug:
                            continue
                        # Convert URL slug (with hyphens) to URL name (with underscores)
                        url_name = url_slug.replace('-', '_')
                        all_tools.append({
                            'name': calc.get('name', ''),
                            'description': calc.get('description', ''),
                            'icon': 'bi bi-calculator',
                            'url_name': f"financial_calculators:{url_name}",
                            'category': calc.get('category', 'Finance')
                        })
            except ImportError:
                pass
            
            # Select 6 random tools
            if all_tools:
                context['random_pdf_tools'] = random.sample(all_tools, min(6, len(all_tools)))
        except ImportError:
            # If calculator modules are not available, just leave empty list
            pass
        
        return context
    
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Check if user's email is verified
        if not is_email_verified(request.user):
            messages.error(request, "You need to verify your email before posting comments. Please check your inbox for a verification email.")
            return HttpResponseRedirect(reverse('account_email'))
        
        # Check if this is a reply to an existing comment
        parent_comment_id = request.POST.get('parent_comment_id')
        
        if parent_comment_id:
            form = ReplyForm(request.POST, user=request.user)
            parent_comment = get_object_or_404(Comment, id=parent_comment_id, post=self.object)
        else:
            form = CommentForm(request.POST, user=request.user)
            parent_comment = None
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = self.object
            comment.parent = parent_comment
            
            # Set user and author fields from logged in user
            comment.user = request.user
            comment.author_name = request.user.get_full_name() or request.user.username
            comment.author_email = request.user.email
            
            # Sanitize HTML content to remove images and links
            comment.content = sanitize_html(comment.content)
            
            # Auto-approve comments from authenticated users
            if request.user.is_staff or request.user.is_superuser:
                comment.approved = True
                if parent_comment:
                    success_message = "Your reply has been posted."
                else:
                    success_message = "Your comment has been posted."
            else:
                # Regular users still need approval unless we want to auto-approve them too
                comment.approved = True  # Set to False if you want moderation for all non-staff users
                if parent_comment:
                    success_message = "Your reply has been posted."
                else:
                    success_message = "Your comment has been posted."
                
            comment.save()
            
            # Send notification to post author if it's not the author commenting
            if comment.user != self.object.author:
                if parent_comment_id:
                    # This is a reply
                    notification_title = f"New reply on your post"
                    notification_message = f"{comment.author_name} replied to a comment on your post '{self.object.title}'."
                else:
                    # This is a comment
                    notification_title = f"New comment on your post"
                    notification_message = f"{comment.author_name} commented on your post '{self.object.title}'."
                
                create_notification(
                    self.object.author,
                    notification_title,
                    notification_message,
                    'info',
                    self.object.get_absolute_url() + f"#comment-{comment.id}"
                )
            
            # If it's a reply, also notify the parent comment author (unless it's the same user)
            if parent_comment_id and parent_comment.user and parent_comment.user != request.user:
                notification_title = f"New reply to your comment"
                notification_message = f"{comment.author_name} replied to your comment on '{self.object.title}'."
                
                create_notification(
                    parent_comment.user,
                    notification_title,
                    notification_message,
                    'info',
                    self.object.get_absolute_url() + f"#comment-{comment.id}"
                )
            
            messages.success(request, success_message)
            
            # Redirect to the specific comment if approved
            if comment.approved:
                return HttpResponseRedirect(f"{self.object.get_absolute_url()}#comment-{comment.id}")
            return HttpResponseRedirect(self.object.get_absolute_url())
        else:
            context = self.get_context_data(object=self.object)
            if parent_comment_id:
                context['reply_form'] = form
                context['reply_to_comment_id'] = parent_comment_id
            else:
                context['comment_form'] = form
            return self.render_to_response(context)

@require_POST
@login_required
def comment_reply(request, category_slug, post_slug, comment_id):
    """Handle replies to comments"""
    # Check if user's email is verified
    if not is_email_verified(request.user):
        messages.error(request, "You need to verify your email before posting replies. Please check your inbox for a verification email.")
        return redirect('account_email')
    
    post = get_object_or_404(Post, slug=post_slug, category__slug=category_slug)
    parent_comment = get_object_or_404(Comment, id=comment_id, post=post)
    
    form = ReplyForm(request.POST, user=request.user)
    
    if form.is_valid():
        reply = form.save(commit=False)
        reply.post = post
        reply.parent = parent_comment
        
        # Set user and author fields
        reply.user = request.user
        reply.author_name = request.user.get_full_name() or request.user.username
        reply.author_email = request.user.email
        
        # Sanitize HTML content
        reply.content = sanitize_html(reply.content)
        
        # Auto-approve replies from authenticated users
        if request.user.is_staff or request.user.is_superuser:
            reply.approved = True
        else:
            reply.approved = True  # Set to False if you want moderation
        
        reply.save()
        
        # Send notification to post author if it's not the author replying
        if reply.user != post.author:
            notification_title = f"New reply on your post"
            notification_message = f"{reply.author_name} replied to a comment on your post '{post.title}'."
            
            create_notification(
                post.author,
                notification_title,
                notification_message,
                'info',
                post.get_absolute_url() + f"#comment-{reply.id}"
            )
        
        # Notify parent comment author (unless it's the same user)
        if parent_comment.user and parent_comment.user != request.user:
            notification_title = f"New reply to your comment"
            notification_message = f"{reply.author_name} replied to your comment on '{post.title}'."
            
            create_notification(
                parent_comment.user,
                notification_title,
                notification_message,
                'info',
                post.get_absolute_url() + f"#comment-{reply.id}"
            )
        
        messages.success(request, "Your reply has been posted.")
        
        # Redirect to the comment section with the new reply
        if reply.approved:
            return HttpResponseRedirect(f"{post.get_absolute_url()}#comment-{reply.id}")
    else:
        messages.error(request, "There was an error with your reply. Please try again.")
    
    return HttpResponseRedirect(post.get_absolute_url())




def blog_rss_feed(request):
    """RSS feed view for blog posts"""
    from django.contrib.syndication.views import Feed
    
    class BlogRSSFeedView(Feed):
        title = "CalculatorDrive Blog"
        link = "/blog/"
        description = "Expert tips, tutorials, and guides to help you use calculators effectively"
        
        def items(self):
            """Return the latest 20 published blog posts"""
            return Post.objects.filter(
                status='published',
                published_date__lte=timezone.now(),
                no_index=False
            ).select_related('author', 'category').prefetch_related('tags').order_by('-published_date')[:20]
        
        def item_title(self, item):
            return item.title
        
        def item_description(self, item):
            """Return excerpt or truncated content"""
            if item.excerpt:
                return item.excerpt
            # Strip HTML and truncate content
            content = strip_tags(item.content)
            return content[:300] + '...' if len(content) > 300 else content
        
        def item_link(self, item):
            """Return absolute URL for the post"""
            site = get_current_site(request)
            return f"https://{site.domain}{item.get_absolute_url()}"
        
        def item_author_name(self, item):
            return item.author.get_full_name() or item.author.username
        
        def item_pubdate(self, item):
            return item.published_date or item.created_date
        
        def item_updateddate(self, item):
            return item.updated_date
        
        def item_categories(self, item):
            """Return categories and tags"""
            categories = [item.category.name]
            categories.extend([tag.name for tag in item.tags.all()])
            return categories
    
    feed_view = BlogRSSFeedView()
    return feed_view(request)
