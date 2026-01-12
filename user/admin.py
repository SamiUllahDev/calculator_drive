from django.contrib import admin
from .models import Profile, Notification, Activity, UserSession, FavoriteCalculator

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'email', 'location', 'company', 'created', 'updated')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'company', 'location')
    list_filter = ('gender', 'created', 'updated', 'email_notifications')
    readonly_fields = ('created', 'updated')
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'avatar', 'bio')
        }),
        ('Personal Details', {
            'fields': ('gender', 'birth_date', 'location', 'phone')
        }),
        ('Professional Details', {
            'fields': ('company', 'job_title', 'website')
        }),
        ('Social Media', {
            'fields': ('twitter', 'facebook', 'linkedin')
        }),
        ('Preferences', {
            'fields': ('email_notifications', 'theme', 'language', 'timezone')
        }),
        ('Privacy Settings', {
            'fields': ('profile_privacy', 'show_email', 'show_location', 'show_birth_date')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated')
        }),
    )
    
    def full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    full_name.short_description = 'Name'
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Notification Details', {
            'fields': ('title', 'message', 'user', 'notification_type', 'icon', 'link')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f"{queryset.count()} notifications marked as read")
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f"{queryset.count()} notifications marked as unread")
    mark_as_unread.short_description = "Mark selected notifications as unread"


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'description_short', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def description_short(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_short.short_description = 'Description'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'is_active', 'last_activity', 'created_at')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address', 'session_key')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    date_hierarchy = 'created_at'


@admin.register(FavoriteCalculator)
class FavoriteCalculatorAdmin(admin.ModelAdmin):
    list_display = ('calculator_name', 'user', 'calculator_app', 'calculator_category', 'created_at')
    list_filter = ('calculator_app', 'calculator_category', 'created_at')
    search_fields = ('calculator_name', 'user__username', 'user__email', 'calculator_description')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
