from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _


class AdUnit(models.Model):
    """
    Represents a Google AdSense ad unit configuration
    """
    AD_TYPE_CHOICES = [
        ('display', _('Display Ad')),
        ('in_article', _('In-Article Ad')),
        ('in_feed', _('In-Feed Ad')),
        ('matched_content', _('Matched Content')),
        ('anchor', _('Anchor Ad')),
        ('vignette', _('Vignette Ad')),
    ]
    
    AD_SIZE_CHOICES = [
        ('auto', _('Auto')),
        ('responsive', _('Responsive')),
        ('rectangle', _('Rectangle (300x250)')),
        ('large_rectangle', _('Large Rectangle (336x280)')),
        ('leaderboard', _('Leaderboard (728x90)')),
        ('banner', _('Banner (468x60)')),
        ('half_banner', _('Half Banner (234x60)')),
        ('skyscraper', _('Skyscraper (120x600)')),
        ('wide_skyscraper', _('Wide Skyscraper (160x600)')),
        ('square', _('Square (250x250)')),
        ('small_square', _('Small Square (200x200)')),
        ('mobile_banner', _('Mobile Banner (320x50)')),
    ]
    
    PLACEMENT_CHOICES = [
        ('header', _('Header')),
        ('sidebar', _('Sidebar')),
        ('footer', _('Footer')),
        ('content_top', _('Content Top')),
        ('content_middle', _('Content Middle')),
        ('content_bottom', _('Content Bottom')),
        ('before_post', _('Before Post')),
        ('after_post', _('After Post')),
        ('between_posts', _('Between Posts')),
        ('sticky', _('Sticky')),
        ('custom', _('Custom')),
    ]
    
    name = models.CharField(max_length=200, verbose_name=_('Ad Unit Name'), help_text=_('Internal name for this ad unit'))
    ad_client = models.CharField(max_length=100, verbose_name=_('Ad Client ID'), help_text=_('Your Google AdSense Publisher ID (e.g., ca-pub-1234567890123456)'))
    ad_slot = models.CharField(max_length=50, verbose_name=_('Ad Slot ID'), help_text=_('AdSense Ad Slot ID (e.g., 1234567890)'), blank=True)
    ad_format = models.CharField(max_length=50, verbose_name=_('Ad Format'), help_text=_('Ad format code from AdSense'), blank=True)
    ad_type = models.CharField(max_length=20, choices=AD_TYPE_CHOICES, default='display', verbose_name=_('Ad Type'))
    ad_size = models.CharField(max_length=20, choices=AD_SIZE_CHOICES, default='auto', verbose_name=_('Ad Size'))
    placement = models.CharField(max_length=30, choices=PLACEMENT_CHOICES, verbose_name=_('Placement Location'))
    custom_placement = models.CharField(max_length=100, blank=True, verbose_name=_('Custom Placement Name'), help_text=_('If placement is "custom", specify the name'))
    
    # Ad Code (full HTML/JavaScript code from AdSense)
    ad_code = models.TextField(verbose_name=_('Ad Code'), help_text=_('Paste your complete AdSense ad code here'))
    
    # Display Settings
    is_active = models.BooleanField(default=True, verbose_name=_('Active'), help_text=_('Enable/disable this ad unit'))
    priority = models.IntegerField(default=0, verbose_name=_('Priority'), help_text=_('Higher priority ads show first (0-100)'), 
                                   validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Page Targeting
    show_on_homepage = models.BooleanField(default=True, verbose_name=_('Show on Homepage'))
    show_on_blog = models.BooleanField(default=True, verbose_name=_('Show on Blog Pages'))
    show_on_calculator_pages = models.BooleanField(default=True, verbose_name=_('Show on Calculator Pages'))
    show_on_user_pages = models.BooleanField(default=False, verbose_name=_('Show on User Pages'))
    show_on_static_pages = models.BooleanField(default=True, verbose_name=_('Show on Static Pages'))
    
    # Specific URL patterns (comma-separated)
    include_urls = models.TextField(blank=True, verbose_name=_('Include URLs'), 
                                   help_text=_('Comma-separated URL patterns to show ad (e.g., /math/, /finance/)'))
    exclude_urls = models.TextField(blank=True, verbose_name=_('Exclude URLs'), 
                                   help_text=_('Comma-separated URL patterns to hide ad (e.g., /user/, /admin/)'))
    
    # Places NOT to Show Ads (Exclusion Settings)
    exclude_from_admin = models.BooleanField(default=True, verbose_name=_('Exclude from Admin Pages'), 
                                            help_text=_('Do not show ads on /admin/ pages'))
    exclude_from_login = models.BooleanField(default=True, verbose_name=_('Exclude from Login Pages'), 
                                             help_text=_('Do not show ads on login/register pages'))
    exclude_from_user_dashboard = models.BooleanField(default=True, verbose_name=_('Exclude from User Dashboard'), 
                                                      help_text=_('Do not show ads on user dashboard'))
    exclude_from_user_profile = models.BooleanField(default=False, verbose_name=_('Exclude from User Profiles'), 
                                                    help_text=_('Do not show ads on user profile pages'))
    exclude_from_user_settings = models.BooleanField(default=True, verbose_name=_('Exclude from User Settings'), 
                                                     help_text=_('Do not show ads on user settings pages'))
    exclude_from_blog_create = models.BooleanField(default=True, verbose_name=_('Exclude from Blog Create/Edit'), 
                                                    help_text=_('Do not show ads on blog post create/edit pages'))
    exclude_from_privacy_pages = models.BooleanField(default=True, verbose_name=_('Exclude from Privacy/Terms Pages'), 
                                                    help_text=_('Do not show ads on privacy policy, terms, cookie policy pages'))
    
    # Calculator Category Exclusions
    exclude_from_math_calculators = models.BooleanField(default=False, verbose_name=_('Exclude from Math Calculators'), 
                                                       help_text=_('Do not show ads on /math/ pages'))
    exclude_from_finance_calculators = models.BooleanField(default=False, verbose_name=_('Exclude from Finance Calculators'), 
                                                          help_text=_('Do not show ads on /finance/ pages'))
    exclude_from_health_calculators = models.BooleanField(default=False, verbose_name=_('Exclude from Health Calculators'), 
                                                         help_text=_('Do not show ads on /health/ pages'))
    exclude_from_other_calculators = models.BooleanField(default=False, verbose_name=_('Exclude from Other Calculators'), 
                                                       help_text=_('Do not show ads on /other/ pages'))
    
    # Specific Calculator Exclusions (comma-separated calculator names/slugs)
    exclude_calculators = models.TextField(blank=True, verbose_name=_('Exclude Specific Calculators'), 
                                          help_text=_('Comma-separated calculator slugs to exclude (e.g., area-calculator, bmi-calculator)'))
    
    # Blog Category/Tag Exclusions
    exclude_blog_categories = models.TextField(blank=True, verbose_name=_('Exclude Blog Categories'), 
                                              help_text=_('Comma-separated blog category slugs to exclude'))
    exclude_blog_tags = models.TextField(blank=True, verbose_name=_('Exclude Blog Tags'), 
                                         help_text=_('Comma-separated blog tag slugs to exclude'))
    
    # Placement Exclusions (don't show this ad in these placements)
    exclude_placements = models.TextField(blank=True, verbose_name=_('Exclude from Placements'), 
                                         help_text=_('Comma-separated placement names where this ad should NOT appear'))
    
    # Device Targeting
    show_on_desktop = models.BooleanField(default=True, verbose_name=_('Show on Desktop'))
    show_on_tablet = models.BooleanField(default=True, verbose_name=_('Show on Tablet'))
    show_on_mobile = models.BooleanField(default=True, verbose_name=_('Show on Mobile'))
    
    # User Targeting
    show_for_logged_in = models.BooleanField(default=True, verbose_name=_('Show for Logged-in Users'))
    show_for_anonymous = models.BooleanField(default=True, verbose_name=_('Show for Anonymous Users'))
    
    # Display Limits
    max_display_per_page = models.IntegerField(default=0, verbose_name=_('Max Displays per Page'), 
                                              help_text=_('0 = unlimited'))
    max_display_per_session = models.IntegerField(default=0, verbose_name=_('Max Displays per Session'), 
                                                  help_text=_('0 = unlimited'))
    
    # Styling
    css_class = models.CharField(max_length=100, blank=True, verbose_name=_('CSS Class'), 
                                help_text=_('Additional CSS classes for styling'))
    custom_css = models.TextField(blank=True, verbose_name=_('Custom CSS'), 
                                  help_text=_('Custom CSS styles for this ad unit'))
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'), help_text=_('Internal notes about this ad unit'))
    
    class Meta:
        verbose_name = _('Ad Unit')
        verbose_name_plural = _('Ad Units')
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_placement_display()})"
    
    def get_ad_code_html(self):
        """Return the ad code HTML"""
        if not self.is_active:
            return ""
        return self.ad_code
    
    def should_display(self, request, placement=None):
        """
        Determine if this ad should be displayed based on request context
        
        Args:
            request: Django request object
            placement: Optional placement name to check exclusion
        """
        if not self.is_active:
            return False
        
        # Check user authentication status
        if request.user.is_authenticated and not self.show_for_logged_in:
            return False
        if not request.user.is_authenticated and not self.show_for_anonymous:
            return False
        
        # Check URL patterns
        path = request.path
        
        # ===== EXCLUSION CHECKS (Places NOT to show) =====
        
        # Exclude from admin pages
        if self.exclude_from_admin and path.startswith('/admin/'):
            return False
        
        # Exclude from login/register pages
        if self.exclude_from_login:
            if any(path.startswith(f'/accounts/{page}/') for page in ['login', 'signup', 'register']):
                return False
            if path.startswith('/user/register/'):
                return False
        
        # Exclude from user dashboard
        if self.exclude_from_user_dashboard and path.startswith('/user/dashboard/'):
            return False
        
        # Exclude from user profile pages
        if self.exclude_from_user_profile and '/user/profile/' in path:
            return False
        
        # Exclude from user settings pages
        if self.exclude_from_user_settings:
            if any(path.startswith(f'/user/{page}/') for page in ['account/settings', 'privacy', 'security', 'password']):
                return False
        
        # Exclude from blog create/edit pages
        if self.exclude_from_blog_create:
            if any(path.startswith(f'/blog/{page}/') for page in ['create', 'edit']):
                return False
        
        # Exclude from privacy/terms pages
        if self.exclude_from_privacy_pages:
            if any(path.startswith(f'/{page}/') for page in ['privacy-policy', 'terms-of-service', 'cookie-policy']):
                return False
        
        # Exclude from calculator categories
        if self.exclude_from_math_calculators and path.startswith('/math/'):
            return False
        if self.exclude_from_finance_calculators and path.startswith('/finance/'):
            return False
        if self.exclude_from_health_calculators and path.startswith('/health/'):
            return False
        if self.exclude_from_other_calculators and path.startswith('/other/'):
            return False
        
        # Exclude specific calculators
        if self.exclude_calculators:
            exclude_calc_list = [c.strip() for c in self.exclude_calculators.split(',') if c.strip()]
            for calc_slug in exclude_calc_list:
                if f'/{calc_slug}/' in path or path.endswith(f'/{calc_slug}/'):
                    return False
        
        # Exclude blog categories
        if self.exclude_blog_categories and path.startswith('/blog/category/'):
            exclude_cats = [c.strip() for c in self.exclude_blog_categories.split(',') if c.strip()]
            for cat_slug in exclude_cats:
                if f'/blog/category/{cat_slug}/' in path or path.endswith(f'/blog/category/{cat_slug}/'):
                    return False
        
        # Exclude blog tags
        if self.exclude_blog_tags and path.startswith('/blog/tag/'):
            exclude_tags = [t.strip() for t in self.exclude_blog_tags.split(',') if t.strip()]
            for tag_slug in exclude_tags:
                if f'/blog/tag/{tag_slug}/' in path or path.endswith(f'/blog/tag/{tag_slug}/'):
                    return False
        
        # Exclude from specific placements
        if placement and self.exclude_placements:
            exclude_placements_list = [p.strip() for p in self.exclude_placements.split(',') if p.strip()]
            if placement in exclude_placements_list:
                return False
        
        # Check exclude URLs (general URL patterns)
        if self.exclude_urls:
            exclude_patterns = [p.strip() for p in self.exclude_urls.split(',') if p.strip()]
            for pattern in exclude_patterns:
                if pattern in path:
                    return False
        
        # ===== INCLUSION CHECKS (Places TO show) =====
        
        # Check include URLs
        if self.include_urls:
            include_patterns = [p.strip() for p in self.include_urls.split(',') if p.strip()]
            if include_patterns:
                matched = False
                for pattern in include_patterns:
                    if pattern in path:
                        matched = True
                        break
                if not matched:
                    return False
        
        # Check page type inclusion
        if path == '/' and not self.show_on_homepage:
            return False
        if path.startswith('/blog/') and not self.show_on_blog:
            return False
        if any(path.startswith(f'/{prefix}/') for prefix in ['math', 'finance', 'health', 'other']) and not self.show_on_calculator_pages:
            return False
        if path.startswith('/user/') and not self.show_on_user_pages:
            return False
        
        return True


class AdPlacement(models.Model):
    """
    Defines specific placement locations in templates
    """
    name = models.CharField(max_length=100, unique=True, verbose_name=_('Placement Name'), 
                           help_text=_('Unique identifier for this placement (e.g., header_banner, sidebar_top)'))
    description = models.TextField(blank=True, verbose_name=_('Description'), 
                                  help_text=_('Description of where this placement appears'))
    template_tag = models.CharField(max_length=100, verbose_name=_('Template Tag'), 
                                  help_text=_('Template tag name to use (e.g., show_ads header_banner)'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Ad Placement')
        verbose_name_plural = _('Ad Placements')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class AdStatistic(models.Model):
    """
    Track ad display statistics (optional, for analytics)
    """
    ad_unit = models.ForeignKey(AdUnit, on_delete=models.CASCADE, related_name='statistics', verbose_name=_('Ad Unit'))
    placement = models.CharField(max_length=100, verbose_name=_('Placement'))
    page_url = models.CharField(max_length=500, verbose_name=_('Page URL'))
    user_agent = models.TextField(blank=True, verbose_name=_('User Agent'))
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name=_('IP Address'))
    is_mobile = models.BooleanField(default=False, verbose_name=_('Mobile Device'))
    displayed_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Displayed At'))
    
    class Meta:
        verbose_name = _('Ad Statistic')
        verbose_name_plural = _('Ad Statistics')
        ordering = ['-displayed_at']
    
    def __str__(self):
        return f"{self.ad_unit.name} - {self.displayed_at}"
