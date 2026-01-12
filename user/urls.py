from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

app_name = 'user'

urlpatterns = [
    # User dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # User registration and profile
    path('register/', views.register, name='register'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='profile_detail'),
    path('account/settings/', views.account_settings, name='account_settings'),
    path('account/delete/', views.ProfileDeleteView.as_view(), name='account_delete'),
    
    # Activity and Statistics
    path('activity/', views.activity_history, name='activity_history'),
    path('statistics/', views.user_statistics, name='statistics'),
    
    # Privacy and Security
    path('privacy/', views.privacy_settings, name='privacy_settings'),
    path('security/', views.security_settings, name='security_settings'),
    path('security/terminate-session/<str:session_key>/', views.terminate_session, name='terminate_session'),
    path('security/terminate-all-sessions/', views.terminate_all_sessions, name='terminate_all_sessions'),
    
    # Data Export
    path('export-data/', views.export_data, name='export_data'),
    
    # Favorites
    path('favorites/', views.favorites_list, name='favorites'),
    path('favorites/toggle/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/check/', views.check_favorite, name='check_favorite'),
    
    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/community/', views.CommunityNotificationListView.as_view(), name='community_notifications'),
    path('notifications/blog/', views.BlogNotificationListView.as_view(), name='blog_notifications'),
    path('notifications/mark-read/<int:pk>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_as_read, name='mark_all_notifications_read'),
    path('notifications/delete/<int:pk>/', views.delete_notification, name='delete_notification'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),
    path('toggle-email-notifications/', views.toggle_email_notifications, name='toggle_email_notifications'),
    
    # Password management
    path('password/change/', 
         views.CustomPasswordChangeView.as_view(), 
         name='password_change'),
    path('password/change/done/', 
         auth_views.PasswordChangeDoneView.as_view(template_name='user/password_change_done.html'), 
         name='password_change_done'),
    path('password/reset/', 
         views.CustomPasswordResetView.as_view(), 
         name='password_reset'),
    path('password/reset/done/', 
         views.CustomPasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('password/reset/complete/', 
         views.CustomPasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
] 