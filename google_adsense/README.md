# Google AdSense App

A comprehensive Django app for managing Google AdSense ads and placements across your website.

## Features

- **Ad Unit Management**: Create and manage multiple AdSense ad units
- **Flexible Placement**: Control where ads appear on your site
- **Targeting Options**: 
  - Page type targeting (homepage, blog, calculators, etc.)
  - URL pattern matching (include/exclude)
  - Device targeting (desktop, tablet, mobile)
  - User targeting (logged-in vs anonymous)
- **Display Limits**: Control how many times ads appear per page/session
- **Template Tags**: Easy-to-use template tags for inserting ads
- **Admin Interface**: Full admin interface for managing ads
- **Statistics Tracking**: Optional ad display statistics (if enabled)

## Installation

1. The app is already added to `INSTALLED_APPS` in `settings.py`
2. Run migrations:
   ```bash
   python manage.py makemigrations google_adsense
   python manage.py migrate
   ```
3. Create default placements:
   ```bash
   python manage.py setup_default_placements
   ```
4. Create a superuser if you haven't already:
   ```bash
   python manage.py createsuperuser
   ```

## Usage

### 1. Create Ad Units in Admin

1. Go to Django Admin → Google AdSense → Ad Units
2. Click "Add Ad Unit"
3. Fill in the required fields:
   - **Name**: Internal name for the ad unit
   - **Ad Client ID**: Your Google AdSense Publisher ID (e.g., `ca-pub-1234567890123456`)
   - **Ad Slot ID**: AdSense Ad Slot ID (optional)
   - **Ad Code**: Paste your complete AdSense ad code here
   - **Placement**: Choose where this ad should appear
   - Configure targeting options as needed
4. Save the ad unit

### 2. Use Template Tags in Templates

#### Basic Usage

```django
{% load adsense_tags %}

<!-- Show ads for a specific placement -->
{% show_ads 'header' %}

<!-- Show multiple ads (up to 2) -->
{% show_ads 'sidebar' 2 %}

<!-- Show a specific ad unit by name -->
{% show_ad_unit 'Header Banner' %}

<!-- Use ad wrapper with custom CSS class -->
{% ad_wrapper 'sidebar' 'ad-sidebar-class' %}
```

#### Common Placements

- `header` - Header section
- `sidebar` - Sidebar area
- `footer` - Footer section
- `content_top` - Top of content
- `content_middle` - Middle of content
- `content_bottom` - Bottom of content
- `before_post` - Before blog post
- `after_post` - After blog post
- `between_posts` - Between blog posts
- `sticky` - Sticky ad

### 3. Example Template Integration

#### In Base Template (`core/templates/core/base.html`)

```django
{% load adsense_tags %}

<!-- Header Ad -->
<header>
    {% show_ads 'header' %}
</header>

<!-- Sidebar Ad -->
<aside class="sidebar">
    {% show_ads 'sidebar_top' %}
    <!-- Your sidebar content -->
    {% show_ads 'sidebar_bottom' %}
</aside>

<!-- Footer Ad -->
<footer>
    {% show_ads 'footer' %}
</footer>
```

#### In Blog Post Template

```django
{% load adsense_tags %}

<article>
    {% show_ads 'before_post' %}
    
    <h1>{{ post.title }}</h1>
    {{ post.content|safe }}
    
    {% show_ads 'after_post' %}
</article>
```

#### In Calculator Templates

```django
{% load adsense_tags %}

<div class="calculator-container">
    {% show_ads 'content_top' %}
    
    <!-- Calculator form -->
    
    {% show_ads 'content_bottom' %}
</div>
```

## Ad Unit Configuration

### Basic Settings

- **Name**: Internal identifier
- **Ad Client ID**: Your AdSense Publisher ID
- **Ad Code**: Complete HTML/JavaScript code from AdSense
- **Placement**: Where the ad appears
- **Priority**: Higher priority ads show first (0-100)

### Targeting Options

#### Page Targeting
- Show on Homepage
- Show on Blog Pages
- Show on Calculator Pages
- Show on User Pages
- Show on Static Pages

#### URL Patterns
- **Include URLs**: Comma-separated patterns (e.g., `/math/`, `/finance/`)
- **Exclude URLs**: Comma-separated patterns (e.g., `/user/`, `/admin/`)

#### Device Targeting
- Show on Desktop
- Show on Tablet
- Show on Mobile

#### User Targeting
- Show for Logged-in Users
- Show for Anonymous Users

### Display Limits

- **Max Displays per Page**: Limit how many times ad shows on a single page (0 = unlimited)
- **Max Displays per Session**: Limit per user session (0 = unlimited)

## Template Tags Reference

### `show_ads`
Display ads for a specific placement.

**Syntax:**
```django
{% show_ads placement [limit] %}
```

**Parameters:**
- `placement` (required): Placement name or key
- `limit` (optional): Maximum number of ads to show (default: 1)

**Example:**
```django
{% show_ads 'sidebar' %}
{% show_ads 'header' 2 %}
```

### `show_ad_unit`
Display a specific ad unit by name.

**Syntax:**
```django
{% show_ad_unit ad_unit_name %}
```

**Example:**
```django
{% show_ad_unit 'Header Banner' %}
```

### `show_ads_by_placement`
Display ads using a placement key from AdPlacement model.

**Syntax:**
```django
{% show_ads_by_placement placement_key %}
```

**Example:**
```django
{% show_ads_by_placement 'header_banner' %}
```

### `ad_wrapper`
Wrapper tag with container div and custom CSS class.

**Syntax:**
```django
{% ad_wrapper placement [css_class] [limit] %}
```

**Example:**
```django
{% ad_wrapper 'sidebar' 'ad-sidebar-class' %}
```

## Admin Interface

Access the admin at `/admin/google_adsense/`:

- **Ad Units**: Manage all ad units
- **Ad Placements**: Manage placement definitions
- **Ad Statistics**: View ad display statistics (if tracking enabled)

### Ad Unit Admin Features

- List view with filtering and search
- Detailed form with organized fieldsets
- Preview functionality
- Bulk actions

## Settings

Add to `settings.py`:

```python
# Google AdSense Configuration
GOOGLE_ADSENSE_ENABLED = True  # Set to False to disable all ads globally
GOOGLE_ADSENSE_TRACK_DISPLAYS = False  # Enable ad display tracking
```

## Best Practices

1. **Don't Overload Pages**: Limit ads per page to maintain good UX
2. **Use Appropriate Placements**: Place ads where they won't interfere with content
3. **Test Responsiveness**: Ensure ads work well on mobile devices
4. **Monitor Performance**: Use AdSense dashboard to track performance
5. **Follow AdSense Policies**: Ensure compliance with Google AdSense policies

## Troubleshooting

### Ads Not Showing

1. Check if `GOOGLE_ADSENSE_ENABLED = True` in settings
2. Verify ad unit is marked as `is_active = True`
3. Check targeting settings match your page
4. Verify ad code is correct and complete
5. Check browser console for JavaScript errors

### Template Tag Not Working

1. Ensure `{% load adsense_tags %}` is at the top of your template
2. Check placement name matches exactly
3. Verify ad unit exists and is active
4. Check request context is available

## Support

For issues or questions, check:
- Django documentation: https://docs.djangoproject.com/
- Google AdSense Help: https://support.google.com/adsense/
