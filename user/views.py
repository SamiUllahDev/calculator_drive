from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    PasswordChangeView, 
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView
)
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import ensure_csrf_cookie
from allauth.account.models import EmailAddress
from .forms import (
    UserRegistrationForm, 
    UserUpdateForm, 
    ProfileUpdateForm,
    CustomPasswordChangeForm,
    CustomPasswordResetForm
)
from .models import Profile, Notification, Activity, UserSession, FavoriteCalculator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)


def _safe_redirect_url(url, request, fallback=None):
    """Validate a redirect URL to prevent open redirect attacks.
    Returns the URL if it's safe (relative or same-host), otherwise returns the fallback."""
    if not url:
        return fallback
    if url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return url
    return fallback


def register(request):
    """View for user registration"""
    if request.user.is_authenticated:
        return redirect('seo_tools:index')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, _('Your account has been created! You can now log in.'))
            return redirect('account_login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'user/register.html', {'form': form})


@login_required
def profile(request, username=None):
    """View user profile - own or others'"""
    # Check if email is verified for own profile
    if username is None:
        is_verified = EmailAddress.objects.filter(user=request.user, verified=True).exists()
        if not is_verified:
            messages.warning(request, _("You need to verify your email address before accessing your profile. Please check your inbox or spam folder for the verification email."))
            return redirect('account_email')
    
    if username:
        user = get_object_or_404(User, username=username)
        # Check if this is the logged in user
        editable = request.user == user
    else:
        # Default to logged in user's profile
        user = request.user
        editable = True
    
    # Get community data if available
    has_community_data = hasattr(user, 'community_profile')
    
    # Find solutions (posts marked as solutions)
    solutions = []
    try:
        from community.models import Post
        solutions = Post.objects.filter(author=user, is_solution=True).select_related('topic').order_by('-created_at')[:5]
    except (ImportError, NameError):
        pass
    
    context = {
        'profile_user': user,
        'editable': editable,
        'has_community_data': has_community_data,
        'solutions': solutions,
    }
    return render(request, 'user/profile.html', context)


@login_required
def edit_profile(request):
    """Edit user profile"""
    # Check if email is verified
    is_verified = EmailAddress.objects.filter(user=request.user, verified=True).exists()
    if not is_verified:
        messages.warning(request, _("You need to verify your email address before editing your profile. Please check your inbox or spam folder for the verification email."))
        return redirect('account_email')
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, _('Your profile has been updated!'))
            return redirect('user:profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'title': _('Edit Profile'),
    }
    return render(request, 'user/edit_profile.html', context)


class CustomPasswordChangeView(PasswordChangeView):
    """Custom password change view with form styling"""
    form_class = CustomPasswordChangeForm
    template_name = 'user/password_change.html'
    success_url = reverse_lazy('user:password_change_done')


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with form styling"""
    form_class = CustomPasswordResetForm
    template_name = 'user/password_reset.html'
    email_template_name = 'account/email/password_reset_message.txt'
    html_email_template_name = 'account/email/password_reset_message.html'
    subject_template_name = 'account/email/password_reset_subject.txt'
    success_url = reverse_lazy('user:password_reset_done')


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view"""
    template_name = 'user/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirmation view"""
    template_name = 'user/password_reset_confirm.html'
    success_url = reverse_lazy('user:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view"""
    template_name = 'user/password_reset_complete.html'


@login_required
def account_settings(request):
    """View for managing account settings"""
    # Check if email is verified
    is_verified = EmailAddress.objects.filter(user=request.user, verified=True).exists()
    if not is_verified:
        messages.warning(request, _("You need to verify your email address before accessing account settings. Please check your inbox or spam folder for the verification email."))
        return redirect('account_email')
    
    # Get user statistics
    from .models import Activity, Notification, UserSession
    from blog.models import Post, Comment
    
    total_activities = Activity.objects.filter(user=request.user).count()
    total_notifications = Notification.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    active_sessions = UserSession.objects.filter(user=request.user, is_active=True).count()
    
    # Blog stats
    try:
        blog_posts = Post.objects.filter(author=request.user).count()
        blog_comments = Comment.objects.filter(user=request.user).count()
    except:
        blog_posts = 0
        blog_comments = 0
    
    context = {
        'total_activities': total_activities,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'active_sessions': active_sessions,
        'blog_posts': blog_posts,
        'blog_comments': blog_comments,
    }
    return render(request, 'user/account_settings.html', context)


class ProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for account deletion"""
    model = User
    template_name = 'user/account_delete.html'
    success_url = reverse_lazy('seo_tools:index')
    
    def test_func(self):
        user = self.get_object()
        return self.request.user == user
    
    def get_object(self):
        return self.request.user


# Notification Views
class NotificationListView(LoginRequiredMixin, ListView):
    """View to display user notifications"""
    model = Notification
    template_name = 'user/notifications.html'
    context_object_name = 'notifications'
    paginate_by = 15

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = self.get_queryset().filter(is_read=False).count()
        context['title'] = _('Your Notifications')
        return context


class CommunityNotificationListView(NotificationListView):
    """View to display community-specific notifications"""
    template_name = 'user/community_notifications.html'
    
    def get_queryset(self):
        # Filter notifications related to community activity
        # This uses a naming convention where community notifications have specific keywords
        community_related_keywords = [
            'topic', 'post', 'reply', 'solution', 'reputation', 
            'badge', 'community', 'forum', 'trending'
        ]
        
        base_query = super().get_queryset()
        community_notifications = base_query.filter(
            message__iregex=r'(' + '|'.join(community_related_keywords) + ')'
        ) | base_query.filter(
            title__iregex=r'(' + '|'.join(community_related_keywords) + ')'
        )
        
        return community_notifications
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Community Notifications')
        context['community_notifications'] = context['notifications']  # Alias for template clarity
        return context


class BlogNotificationListView(NotificationListView):
    """View to display blog-specific notifications"""
    template_name = 'user/blog_notifications.html'
    
    def get_queryset(self):
        # Filter notifications related to blog activity
        blog_related_keywords = [
            'blog', 'article', 'post published', 'new article', 'mentioned'
        ]
        
        base_query = super().get_queryset()
        blog_notifications = base_query.filter(
            message__iregex=r'(' + '|'.join(blog_related_keywords) + ')'
        ) | base_query.filter(
            title__iregex=r'(' + '|'.join(blog_related_keywords) + ')'
        )
        
        return blog_notifications
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Blog Notifications')
        context['blog_notifications'] = context['notifications']  # Alias for template clarity
        return context


@login_required
def toggle_email_notifications(request):
    """Toggle email notification preferences"""
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            import json
            data = json.loads(request.body)
            enabled = data.get('enabled', False)
            
            profile = request.user.profile
            profile.email_notifications = enabled
            profile.save(update_fields=['email_notifications'])
            
            return JsonResponse({
                'status': 'success',
                'enabled': profile.email_notifications
            })
        except Exception as e:
            logger.error(f"Error toggling email notifications: {e}")
            return JsonResponse({
                'status': 'error',
                'message': 'An error occurred while updating preferences'
            }, status=400)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request'
    }, status=400)


@login_required
def mark_notification_as_read(request, pk):
    """Mark a single notification as read"""
    try:
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        
        # Handle AJAX requests
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'success'})
        
        # Check for next parameter in URL
        next_url = _safe_redirect_url(request.GET.get('next'), request)
        
        # If there's a link in the notification and no next parameter, redirect to it
        if notification.link and not next_url:
            safe_link = _safe_redirect_url(notification.link, request)
            if safe_link:
                return HttpResponseRedirect(safe_link)
        
        # Otherwise return to notifications page or next URL
        fallback = _safe_redirect_url(request.META.get('HTTP_REFERER'), request, fallback=str(reverse_lazy('user:notifications')))
        return HttpResponseRedirect(next_url or fallback)
    except Exception as e:
        # Log the error and redirect safely
        logger.error(f"Error marking notification as read: {e}")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'An error occurred'})
        messages.error(request, _('There was an error processing your request.'))
        return HttpResponseRedirect(reverse_lazy('user:notifications'))


@login_required
def mark_all_notifications_as_read(request):
    """Mark all user's notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Check for next parameter in URL
    next_url = _safe_redirect_url(request.GET.get('next'), request)
    
    messages.success(request, _('All notifications marked as read'))
    fallback = _safe_redirect_url(request.META.get('HTTP_REFERER'), request, fallback=str(reverse_lazy('user:notifications')))
    return HttpResponseRedirect(next_url or fallback)


@login_required
def delete_notification(request, pk):
    """Delete a single notification"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Check for next parameter in URL
    next_url = _safe_redirect_url(request.GET.get('next'), request)
    
    messages.success(request, _('Notification deleted'))
    fallback = _safe_redirect_url(request.META.get('HTTP_REFERER'), request, fallback=str(reverse_lazy('user:notifications')))
    return HttpResponseRedirect(next_url or fallback)


@login_required
def clear_all_notifications(request):
    """Delete all notifications for the user"""
    # Optional filter for community or blog notifications
    filter_type = request.GET.get('filter')
    
    if filter_type == 'community':
        # Delete only community notifications
        community_related_keywords = [
            'topic', 'post', 'reply', 'solution', 'reputation', 
            'badge', 'community', 'forum', 'trending'
        ]
        
        notifications = Notification.objects.filter(user=request.user).filter(
            message__iregex=r'(' + '|'.join(community_related_keywords) + ')'
        ) | Notification.objects.filter(user=request.user).filter(
            title__iregex=r'(' + '|'.join(community_related_keywords) + ')'
        )
        notifications.delete()
    elif filter_type == 'blog':
        # Delete only blog notifications
        blog_related_keywords = [
            'blog', 'article', 'post published', 'new article', 'mentioned'
        ]
        
        notifications = Notification.objects.filter(user=request.user).filter(
            message__iregex=r'(' + '|'.join(blog_related_keywords) + ')'
        ) | Notification.objects.filter(user=request.user).filter(
            title__iregex=r'(' + '|'.join(blog_related_keywords) + ')'
        )
        notifications.delete()
    else:
        # Delete all notifications
        Notification.objects.filter(user=request.user).delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    # Check for next parameter in URL
    next_url = _safe_redirect_url(request.GET.get('next'), request)
    
    messages.success(request, _('All notifications cleared'))
    return HttpResponseRedirect(next_url or reverse_lazy('user:notifications'))


def create_notification(user, title, message, notification_type='info', icon=None, link=None):
    """Helper function to create a notification
    
    This can be imported and used by other apps to create notifications.
    Example: from user.views import create_notification
    """
    if not icon:
        # Default icons based on notification type
        icon_mapping = {
            'info': '',
            'success': '',
            'warning': '',
            'error': ''
        }
        icon = icon_mapping.get(notification_type, '')
    
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        icon=icon,
        link=link
    )
    return notification


@login_required
def activity_history(request):
    """View user activity history"""
    activities = Activity.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_activities': activities.count(),
    }
    return render(request, 'user/activity_history.html', context)


@login_required
def user_statistics(request):
    """View user statistics"""
    from blog.models import Post, Comment
    
    # Activity stats
    total_activities = Activity.objects.filter(user=request.user).count()
    activities_this_month = Activity.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - timedelta(days=30)
    ).count()
    
    # Notification stats
    total_notifications = Notification.objects.filter(user=request.user).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    notifications_by_type = Notification.objects.filter(user=request.user).values('notification_type').annotate(count=Count('id'))
    
    # Blog stats
    try:
        blog_posts = Post.objects.filter(author=request.user).count()
        published_posts = Post.objects.filter(author=request.user, status='published').count()
        blog_comments = Comment.objects.filter(user=request.user).count()
    except:
        blog_posts = 0
        published_posts = 0
        blog_comments = 0
    
    # Session stats
    active_sessions = UserSession.objects.filter(user=request.user, is_active=True).count()
    total_sessions = UserSession.objects.filter(user=request.user).count()
    
    # Account age
    account_age_days = (timezone.now() - request.user.date_joined).days
    
    context = {
        'total_activities': total_activities,
        'activities_this_month': activities_this_month,
        'total_notifications': total_notifications,
        'unread_notifications': unread_notifications,
        'notifications_by_type': notifications_by_type,
        'blog_posts': blog_posts,
        'published_posts': published_posts,
        'blog_comments': blog_comments,
        'active_sessions': active_sessions,
        'total_sessions': total_sessions,
        'account_age_days': account_age_days,
    }
    return render(request, 'user/statistics.html', context)


@login_required
def privacy_settings(request):
    """View and update privacy settings"""
    profile = request.user.profile
    
    if request.method == 'POST':
        # Validate profile_privacy against allowed choices
        privacy_value = request.POST.get('profile_privacy', 'public')
        valid_privacy_choices = [choice[0] for choice in Profile.PRIVACY_CHOICES]
        if privacy_value not in valid_privacy_choices:
            privacy_value = 'public'
        profile.profile_privacy = privacy_value
        profile.show_email = request.POST.get('show_email') == 'on'
        profile.show_location = request.POST.get('show_location') == 'on'
        profile.show_birth_date = request.POST.get('show_birth_date') == 'on'
        profile.save()
        messages.success(request, _('Privacy settings updated successfully!'))
        return redirect('user:privacy_settings')
    
    context = {
        'profile': profile,
    }
    return render(request, 'user/privacy_settings.html', context)


@login_required
def security_settings(request):
    """View security settings and active sessions"""
    # Get active sessions
    active_sessions = UserSession.objects.filter(user=request.user, is_active=True).order_by('-last_activity')
    
    # Get current session
    current_session_key = request.session.session_key
    current_session = None
    if current_session_key:
        try:
            current_session = UserSession.objects.get(session_key=current_session_key, user=request.user)
        except UserSession.DoesNotExist:
            pass
    
    context = {
        'active_sessions': active_sessions,
        'current_session': current_session,
        'current_session_key': current_session_key,
    }
    return render(request, 'user/security_settings.html', context)


@login_required
def terminate_session(request, session_key):
    """Terminate a specific session"""
    if request.method == 'POST':
        try:
            session = UserSession.objects.get(session_key=session_key, user=request.user)
            session.is_active = False
            session.save()
            
            # Also delete from Django session store
            from django.contrib.sessions.models import Session
            try:
                Session.objects.get(session_key=session_key).delete()
            except:
                pass
            
            messages.success(request, _('Session terminated successfully.'))
        except UserSession.DoesNotExist:
            messages.error(request, _('Session not found.'))
    
    return redirect('user:security_settings')


@login_required
def terminate_all_sessions(request):
    """Terminate all sessions except current"""
    if request.method == 'POST':
        current_session_key = request.session.session_key
        UserSession.objects.filter(user=request.user).exclude(session_key=current_session_key).update(is_active=False)
        
        # Delete from Django session store
        from django.contrib.sessions.models import Session
        Session.objects.filter(user=request.user).exclude(session_key=current_session_key).delete()
        
        messages.success(request, _('All other sessions terminated successfully.'))
    
    return redirect('user:security_settings')


@login_required
def export_data(request):
    """Export user data as JSON"""
    if request.method == 'POST':
        # Collect all user data
        data = {
            'user': {
                'username': request.user.username,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'date_joined': request.user.date_joined.isoformat(),
                'last_login': request.user.last_login.isoformat() if request.user.last_login else None,
            },
            'profile': {
                'bio': request.user.profile.bio,
                'location': request.user.profile.location,
                'website': request.user.profile.website,
                'phone': request.user.profile.phone,
                'gender': request.user.profile.get_gender_display() if request.user.profile.gender else None,
                'birth_date': request.user.profile.birth_date.isoformat() if request.user.profile.birth_date else None,
                'company': request.user.profile.company,
                'job_title': request.user.profile.job_title,
                'created': request.user.profile.created.isoformat(),
                'updated': request.user.profile.updated.isoformat(),
            },
            'activities': [
                {
                    'description': activity.description,
                    'created_at': activity.created_at.isoformat(),
                }
                for activity in Activity.objects.filter(user=request.user)
            ],
            'notifications': [
                {
                    'title': notification.title,
                    'message': notification.message,
                    'type': notification.notification_type,
                    'is_read': notification.is_read,
                    'created_at': notification.created_at.isoformat(),
                }
                for notification in Notification.objects.filter(user=request.user)
            ],
        }
        
        # Try to include blog data
        try:
            from blog.models import Post, Comment
            data['blog_posts'] = [
                {
                    'title': post.title,
                    'slug': post.slug,
                    'status': post.status,
                    'created_date': post.created_date.isoformat(),
                }
                for post in Post.objects.filter(author=request.user)
            ]
            data['blog_comments'] = [
                {
                    'content': comment.content[:100],  # First 100 chars
                    'created_date': comment.created_date.isoformat(),
                    'approved': comment.approved,
                }
                for comment in Comment.objects.filter(user=request.user)
            ]
        except:
            pass
        
        # Create JSON response
        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="user_data_{request.user.username}_{timezone.now().strftime("%Y%m%d")}.json"'
        return response
    
    return redirect('user:account_settings')


@login_required
def dashboard(request):
    """User dashboard view showing community stats and recent activity"""
    # Check if email is verified
    is_verified = EmailAddress.objects.filter(user=request.user, verified=True).exists()
    if not is_verified:
        messages.warning(request, _("You need to verify your email address before accessing your dashboard. Please check your inbox or spam folder for the verification email."))
        return redirect('account_email')
    
    # Get community data if available
    has_community_data = hasattr(request.user, 'community_profile')
    
    # Get recent notifications (limited to 5)
    recent_notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get unread count separately (don't filter on a sliced queryset)
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    
    # Get recent activities
    recent_activities = Activity.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get statistics
    total_activities = Activity.objects.filter(user=request.user).count()
    total_notifications = Notification.objects.filter(user=request.user).count()
    
    # Blog stats
    try:
        from blog.models import Post, Comment
        blog_posts = Post.objects.filter(author=request.user).count()
        blog_comments = Comment.objects.filter(user=request.user).count()
    except:
        blog_posts = 0
        blog_comments = 0
    
    # Active sessions
    active_sessions = UserSession.objects.filter(user=request.user, is_active=True).count()
    
    context = {
        'recent_notifications': recent_notifications,
        'unread_notifications_count': unread_count,
        'has_community_data': has_community_data,
        'recent_activities': recent_activities,
        'total_activities': total_activities,
        'total_notifications': total_notifications,
        'blog_posts': blog_posts,
        'blog_comments': blog_comments,
        'active_sessions': active_sessions,
    }
    return render(request, 'user/dashboard.html', context)


from django.utils.decorators import method_decorator

def _normalize_calculator_url(url):
    """Normalize calculator URL for consistent storage and lookup.
    Always stores without trailing slash."""
    if url:
        url = url.strip().rstrip('/')
    return url


@ensure_csrf_cookie
def toggle_favorite(request):
    """Toggle favorite calculator for authenticated user"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    # Check if user is authenticated - return JSON instead of HTML redirect
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        # Parse JSON data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False, 
                'error': 'Invalid JSON format in request'
            }, status=400)
        
        calculator_name = data.get('calculator_name')
        calculator_url = data.get('calculator_url')
        calculator_category = data.get('calculator_category', '')
        calculator_app = data.get('calculator_app', '')
        calculator_description = data.get('calculator_description', '')
        
        # Validate required fields
        if not calculator_name or not calculator_url:
            return JsonResponse({
                'success': False, 
                'error': 'Missing required fields: calculator_name and calculator_url are required'
            }, status=400)
        
        # Normalize URL for consistent storage and lookup
        calculator_url = _normalize_calculator_url(calculator_url)
        
        # Check if favorite already exists
        try:
            # First, try to get existing favorite
            try:
                favorite = FavoriteCalculator.objects.get(
                    user=request.user,
                    calculator_url=calculator_url
                )
                # Favorite exists - remove it
                favorite.delete()
                return JsonResponse({
                    'success': True,
                    'is_favorite': False,
                    'message': 'Calculator removed from favorites'
                })
            except FavoriteCalculator.DoesNotExist:
                # Favorite doesn't exist - create it
                FavoriteCalculator.objects.create(
                    user=request.user,
                    calculator_name=calculator_name,
                    calculator_url=calculator_url,
                    calculator_category=calculator_category,
                    calculator_app=calculator_app,
                    calculator_description=calculator_description,
                )
                return JsonResponse({
                    'success': True,
                    'is_favorite': True,
                    'message': 'Calculator added to favorites'
                })
        except Exception as db_error:
            logger.error(f"Database error in toggle_favorite: {db_error}")
            return JsonResponse({
                'success': False, 
                'error': 'A database error occurred'
            }, status=500)
            
    except Exception as e:
        # Log the full error for debugging
        logger.exception("Unexpected error in toggle_favorite")
        
        return JsonResponse({
            'success': False, 
            'error': 'An unexpected error occurred'
        }, status=500)


def check_favorite(request):
    """Check if calculator is in user's favorites"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    calculator_url = request.GET.get('calculator_url')
    # Normalize URL for consistent lookup
    calculator_url = _normalize_calculator_url(calculator_url)
    if not calculator_url:
        return JsonResponse({'success': False, 'error': 'Missing calculator_url'}, status=400)
    
    is_favorite = FavoriteCalculator.objects.filter(
        user=request.user,
        calculator_url=calculator_url
    ).exists()
    
    return JsonResponse({
        'success': True,
        'is_favorite': is_favorite
    })


@ensure_csrf_cookie
def check_favorites_bulk(request):
    """Check multiple calculators' favorite status in a single request.
    Accepts POST with JSON body: { "calculator_urls": ["/math/calc1/", "/finance/calc2/"] }
    Returns: { "success": true, "favorites": { "/math/calc1": true, "/finance/calc2": false } }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    calculator_urls = data.get('calculator_urls', [])
    if not isinstance(calculator_urls, list):
        return JsonResponse({'success': False, 'error': 'calculator_urls must be a list'}, status=400)
    
    # Normalize all URLs
    normalized_urls = [_normalize_calculator_url(url) for url in calculator_urls if url]
    
    # Single query to get all favorited URLs
    favorited_urls = set(
        FavoriteCalculator.objects.filter(
            user=request.user,
            calculator_url__in=normalized_urls
        ).values_list('calculator_url', flat=True)
    )
    
    # Build response mapping normalized URL -> is_favorite
    favorites = {url: (url in favorited_urls) for url in normalized_urls}
    
    return JsonResponse({
        'success': True,
        'favorites': favorites
    })


@login_required
def favorites_list(request):
    """Display user's favorite calculators"""
    favorites = FavoriteCalculator.objects.filter(user=request.user).order_by('-created_at')
    
    # Group by app
    favorites_by_app = {}
    for favorite in favorites:
        app = favorite.calculator_app or 'other'
        if app not in favorites_by_app:
            favorites_by_app[app] = []
        favorites_by_app[app].append(favorite)
    
    context = {
        'favorites': favorites,
        'favorites_by_app': favorites_by_app,
        'total_favorites': favorites.count(),
    }
    
    return render(request, 'user/favorites.html', context)
