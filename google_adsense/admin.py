from django.contrib import admin
from django.utils.html import format_html
from .models import AdUnit, AdPlacement, AdStatistic


@admin.register(AdUnit)
class AdUnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'placement', 'ad_type', 'is_active', 'priority', 'created_at']
    list_filter = ['is_active', 'ad_type', 'placement', 'show_on_desktop', 'show_on_mobile', 'created_at']
    search_fields = ['name', 'ad_client', 'ad_slot', 'placement', 'custom_placement']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'ad_client', 'ad_slot', 'ad_format', 'ad_type', 'ad_size', 'ad_code', 'notes')
        }),
        ('Placement', {
            'fields': ('placement', 'custom_placement', 'priority', 'css_class', 'custom_css')
        }),
        ('Display Settings', {
            'fields': ('is_active',)
        }),
        ('Page Targeting (Where to Show)', {
            'fields': (
                'show_on_homepage',
                'show_on_blog',
                'show_on_calculator_pages',
                'show_on_user_pages',
                'show_on_static_pages',
                'include_urls',
            )
        }),
        ('Places NOT to Show - General Exclusions', {
            'fields': (
                'exclude_urls',
                'exclude_from_admin',
                'exclude_from_login',
                'exclude_from_privacy_pages',
            ),
            'description': 'General exclusion settings for common pages'
        }),
        ('Places NOT to Show - User Pages', {
            'fields': (
                'exclude_from_user_dashboard',
                'exclude_from_user_profile',
                'exclude_from_user_settings',
            ),
            'description': 'Exclude ads from specific user-related pages'
        }),
        ('Places NOT to Show - Blog Pages', {
            'fields': (
                'exclude_from_blog_create',
                'exclude_blog_categories',
                'exclude_blog_tags',
            ),
            'description': 'Exclude ads from blog-related pages'
        }),
        ('Places NOT to Show - Calculator Pages', {
            'fields': (
                'exclude_from_math_calculators',
                'exclude_from_finance_calculators',
                'exclude_from_health_calculators',
                'exclude_from_other_calculators',
                'exclude_calculators',
            ),
            'description': 'Exclude ads from calculator pages'
        }),
        ('Placement Exclusions', {
            'fields': ('exclude_placements',),
            'description': 'Comma-separated placement names where this ad should NOT appear'
        }),
        ('Device Targeting', {
            'fields': ('show_on_desktop', 'show_on_tablet', 'show_on_mobile')
        }),
        ('User Targeting', {
            'fields': ('show_for_logged_in', 'show_for_anonymous')
        }),
        ('Display Limits', {
            'fields': ('max_display_per_page', 'max_display_per_session')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
    
    def ad_preview(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    ad_preview.short_description = 'Status'


@admin.register(AdPlacement)
class AdPlacementAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_tag', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description', 'template_tag']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AdStatistic)
class AdStatisticAdmin(admin.ModelAdmin):
    list_display = ['ad_unit', 'placement', 'page_url', 'is_mobile', 'displayed_at']
    list_filter = ['is_mobile', 'displayed_at', 'placement']
    search_fields = ['ad_unit__name', 'placement', 'page_url']
    readonly_fields = ['ad_unit', 'placement', 'page_url', 'user_agent', 'ip_address', 'is_mobile', 'displayed_at']
    date_hierarchy = 'displayed_at'
    
    def has_add_permission(self, request):
        return False  # Statistics are created automatically
    
    def has_change_permission(self, request, obj=None):
        return False  # Statistics are read-only
