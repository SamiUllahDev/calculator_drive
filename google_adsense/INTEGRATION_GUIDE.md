# Google AdSense Integration Guide

## Quick Start

### Step 1: Run Migrations

```bash
python manage.py migrate google_adsense
```

### Step 2: Create Default Placements

```bash
python manage.py setup_default_placements
```

### Step 3: Add Your First Ad Unit

1. Go to Django Admin: `/admin/google_adsense/adunit/add/`
2. Fill in:
   - **Name**: "Header Banner"
   - **Ad Client ID**: Your AdSense Publisher ID (e.g., `ca-pub-1234567890123456`)
   - **Ad Code**: Paste your complete AdSense code
   - **Placement**: Select "Header"
   - **Is Active**: Check this box
3. Save

### Step 4: Add Ads to Templates

#### Option A: Add to Base Template

Edit `core/templates/core/base.html`:

```django
{% load adsense_tags %}

<!DOCTYPE html>
<html>
<head>
    <!-- Your head content -->
</head>
<body>
    <header>
        <!-- Header content -->
        {% show_ads 'header' %}
    </header>
    
    <div class="main-content">
        <aside class="sidebar">
            {% show_ads 'sidebar_top' %}
            <!-- Sidebar content -->
            {% show_ads 'sidebar_bottom' %}
        </aside>
        
        <main>
            {% block content %}{% endblock %}
        </main>
    </div>
    
    <footer>
        {% show_ads 'footer' %}
    </footer>
</body>
</html>
```

#### Option B: Add to Specific Pages

**Blog Post Template** (`blog/templates/blog/post_detail.html`):

```django
{% load adsense_tags %}

<article>
    {% show_ads 'before_post' %}
    
    <h1>{{ post.title }}</h1>
    {{ post.content|safe }}
    
    {% show_ads 'after_post' %}
</article>
```

**Calculator Template** (e.g., `Math_Calculators/templates/math_calculators/area_calculator.html`):

```django
{% load adsense_tags %}

<div class="calculator">
    {% show_ads 'content_top' %}
    
    <!-- Calculator form -->
    
    {% show_ads 'content_bottom' %}
</div>
```

## Common Integration Patterns

### 1. Sidebar Ads

```django
<aside class="sidebar">
    {% show_ads 'sidebar_top' %}
    
    <div class="widget">
        <!-- Widget content -->
    </div>
    
    {% show_ads 'sidebar_middle' %}
    
    <div class="widget">
        <!-- Widget content -->
    </div>
    
    {% show_ads 'sidebar_bottom' %}
</aside>
```

### 2. In-Content Ads

```django
<article>
    <h1>Article Title</h1>
    
    <p>First paragraph...</p>
    
    {% show_ads 'content_middle' %}
    
    <p>More content...</p>
</article>
```

### 3. Between Blog Posts

```django
{% for post in posts %}
    <article>
        <h2>{{ post.title }}</h2>
        {{ post.excerpt }}
    </article>
    
    {% if not forloop.last %}
        {% show_ads 'between_posts' %}
    {% endif %}
{% endfor %}
```

### 4. Sticky Ad

```django
<div class="sticky-ad-container">
    {% show_ads 'sticky' %}
</div>
```

Add CSS:
```css
.sticky-ad-container {
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 1000;
}
```

## Advanced Usage

### Conditional Ads Based on Page Type

```django
{% load adsense_tags %}

{% if request.path == '/' %}
    {% show_ads 'header' %}
{% elif '/blog/' in request.path %}
    {% show_ads 'before_post' %}
{% elif '/math/' in request.path %}
    {% show_ads 'content_top' %}
{% endif %}
```

### Multiple Ads in Same Location

```django
<!-- Show up to 3 ads in sidebar -->
{% show_ads 'sidebar' 3 %}
```

### Custom CSS Styling

In Ad Unit admin, add custom CSS:
```css
.adsense-ad-unit {
    margin: 20px 0;
    text-align: center;
    padding: 10px;
    background: #f5f5f5;
    border-radius: 5px;
}
```

### Responsive Ads

Create separate ad units for different devices:
- Desktop ad unit: `show_on_desktop=True`, `show_on_mobile=False`
- Mobile ad unit: `show_on_mobile=True`, `show_on_desktop=False`

Then in template:
```django
<div class="desktop-ad">
    {% show_ads 'header' %}
</div>
<div class="mobile-ad">
    {% show_ads 'header' %}
</div>
```

With CSS:
```css
.desktop-ad { display: block; }
.mobile-ad { display: none; }

@media (max-width: 768px) {
    .desktop-ad { display: none; }
    .mobile-ad { display: block; }
}
```

## Testing

### Test Ad Display

1. Create a test ad unit with:
   - Simple test content in ad code
   - Set to show on all pages
   - Mark as active
2. Visit different pages to verify placement
3. Check browser console for errors

### Preview Ad Unit

Admin users can preview ads at:
```
/adsense/preview/<ad_unit_id>/
```

## Troubleshooting

### Ads Not Showing

1. **Check Settings**: Verify `GOOGLE_ADSENSE_ENABLED = True`
2. **Check Ad Unit**: Ensure it's marked as `is_active = True`
3. **Check Targeting**: Verify page matches targeting rules
4. **Check Template**: Ensure `{% load adsense_tags %}` is present
5. **Check Browser Console**: Look for JavaScript errors

### Ads Showing in Wrong Places

1. Check placement name matches exactly
2. Verify URL patterns in include/exclude fields
3. Check priority settings (higher priority shows first)

### Performance Issues

1. Limit number of ads per page
2. Use lazy loading for ads below fold
3. Monitor page load times
4. Consider using async ad loading

## Best Practices

1. **Don't Overload**: Maximum 3-4 ads per page
2. **Above the Fold**: Place at least one ad above fold
3. **Mobile Friendly**: Ensure ads work on mobile devices
4. **User Experience**: Don't let ads interfere with content
5. **Compliance**: Follow Google AdSense policies
6. **Testing**: Test on different devices and browsers
7. **Monitoring**: Regularly check AdSense dashboard

## Example: Complete Base Template Integration

```django
{% load adsense_tags %}
{% load static %}

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Calculator Website{% endblock %}</title>
</head>
<body>
    <!-- Header with ad -->
    <header class="site-header">
        <div class="header-content">
            <h1>Calculator Website</h1>
        </div>
        <div class="header-ad">
            {% show_ads 'header' %}
        </div>
    </header>
    
    <!-- Main layout -->
    <div class="main-layout">
        <!-- Sidebar -->
        <aside class="sidebar">
            {% show_ads 'sidebar_top' %}
            
            <nav>
                <!-- Navigation -->
            </nav>
            
            {% show_ads 'sidebar_middle' %}
            
            <div class="widgets">
                <!-- Widgets -->
            </div>
            
            {% show_ads 'sidebar_bottom' %}
        </aside>
        
        <!-- Main content -->
        <main class="content">
            {% show_ads 'content_top' %}
            
            {% block content %}{% endblock %}
            
            {% show_ads 'content_bottom' %}
        </main>
    </div>
    
    <!-- Footer with ad -->
    <footer class="site-footer">
        {% show_ads 'footer' %}
        <p>&copy; 2024 Calculator Website</p>
    </footer>
</body>
</html>
```
