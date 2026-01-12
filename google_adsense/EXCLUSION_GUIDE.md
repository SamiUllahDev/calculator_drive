# Ad Exclusion Guide

This guide explains how to configure places where ads should **NOT** show.

## Overview

The Google AdSense app provides comprehensive exclusion options to control exactly where your ads appear. You can exclude ads from:

- Specific page types (admin, login, user pages, etc.)
- Calculator categories (math, finance, health, other)
- Specific calculators
- Blog categories and tags
- Specific placements
- URL patterns

## Exclusion Options

### 1. General Exclusions

#### Exclude from Admin Pages
**Field**: `exclude_from_admin` (default: True)

Prevents ads from showing on `/admin/` pages.

**Example**: Check this box to hide ads from admin interface.

#### Exclude from Login Pages
**Field**: `exclude_from_login` (default: True)

Prevents ads from showing on login/register pages.

**Example**: Check this box to hide ads from:
- `/accounts/login/`
- `/accounts/signup/`
- `/user/register/`

#### Exclude from Privacy Pages
**Field**: `exclude_from_privacy_pages` (default: True)

Prevents ads from showing on policy pages.

**Example**: Check this box to hide ads from:
- `/privacy-policy/`
- `/terms-of-service/`
- `/cookie-policy/`

### 2. User Page Exclusions

#### Exclude from User Dashboard
**Field**: `exclude_from_user_dashboard` (default: True)

Prevents ads from showing on user dashboard (`/user/dashboard/`).

#### Exclude from User Profiles
**Field**: `exclude_from_user_profile` (default: False)

Prevents ads from showing on user profile pages (`/user/profile/`).

**Example**: Check this to hide ads when users view profiles.

#### Exclude from User Settings
**Field**: `exclude_from_user_settings` (default: True)

Prevents ads from showing on user settings pages:
- `/user/account/settings/`
- `/user/privacy/`
- `/user/security/`
- `/user/password/`

### 3. Blog Page Exclusions

#### Exclude from Blog Create/Edit
**Field**: `exclude_from_blog_create` (default: True)

Prevents ads from showing when creating or editing blog posts:
- `/blog/create/`
- `/blog/edit/<slug>/`

#### Exclude Blog Categories
**Field**: `exclude_blog_categories`

Comma-separated list of blog category slugs to exclude.

**Example**: `tutorials, news, reviews`

This will hide ads on pages like:
- `/blog/category/tutorials/`
- `/blog/category/news/`

#### Exclude Blog Tags
**Field**: `exclude_blog_tags`

Comma-separated list of blog tag slugs to exclude.

**Example**: `django, python, web-development`

This will hide ads on pages like:
- `/blog/tag/django/`
- `/blog/tag/python/`

### 4. Calculator Page Exclusions

#### Exclude from Calculator Categories

You can exclude entire calculator categories:

- **Exclude from Math Calculators** (`exclude_from_math_calculators`)
  - Hides ads on all `/math/` pages
  
- **Exclude from Finance Calculators** (`exclude_from_finance_calculators`)
  - Hides ads on all `/finance/` pages
  
- **Exclude from Health Calculators** (`exclude_from_health_calculators`)
  - Hides ads on all `/health/` pages
  
- **Exclude from Other Calculators** (`exclude_from_other_calculators`)
  - Hides ads on all `/other/` pages

#### Exclude Specific Calculators
**Field**: `exclude_calculators`

Comma-separated list of calculator slugs to exclude.

**Example**: `area-calculator, bmi-calculator, mortgage-calculator`

This will hide ads on pages like:
- `/math/area-calculator/`
- `/health/bmi-calculator/`
- `/finance/mortgage-calculator/`

### 5. Placement Exclusions

#### Exclude from Placements
**Field**: `exclude_placements`

Comma-separated list of placement names where this ad should NOT appear.

**Example**: `sidebar, footer, content_middle`

This prevents the ad from showing in those specific placements, even if it matches other criteria.

### 6. URL Pattern Exclusions

#### Exclude URLs
**Field**: `exclude_urls`

Comma-separated URL patterns to exclude.

**Example**: `/user/, /admin/, /blog/create/`

Any URL containing these patterns will not show the ad.

## Usage Examples

### Example 1: Hide Ads from Admin and Login Pages

```
✅ Exclude from Admin Pages: Checked
✅ Exclude from Login Pages: Checked
```

### Example 2: Hide Ads from All Math Calculators

```
✅ Exclude from Math Calculators: Checked
```

### Example 3: Hide Ads from Specific Calculators

```
Exclude Calculators: area-calculator, triangle-calculator, circle-calculator
```

### Example 4: Hide Ads from Blog Tutorials

```
Exclude Blog Categories: tutorials
```

### Example 5: Hide Ads from Sidebar Only

```
Placement: sidebar
Exclude Placements: sidebar
```

This ad will show in other placements but not in sidebar.

### Example 6: Hide Ads from User Pages

```
✅ Exclude from User Dashboard: Checked
✅ Exclude from User Profiles: Checked
✅ Exclude from User Settings: Checked
```

### Example 7: Complex Exclusion

Hide ads everywhere except calculator pages:

```
Show on Calculator Pages: ✅
Show on Homepage: ❌
Show on Blog: ❌
Show on User Pages: ❌
Show on Static Pages: ❌

Exclude from Admin: ✅
Exclude from Login: ✅
Exclude from Privacy Pages: ✅
```

## Best Practices

1. **Default Exclusions**: Most exclusion fields default to `True` for common pages (admin, login, settings) - this is recommended.

2. **User Experience**: Consider excluding ads from:
   - Forms and input pages
   - Settings pages
   - Checkout/payment pages (if applicable)

3. **Content Quality**: You might want to exclude ads from:
   - High-value content pages
   - Premium calculator pages
   - Educational content

4. **Performance**: Excluding ads from heavy pages can improve performance.

5. **Testing**: Always test exclusions by visiting the excluded pages to verify ads don't show.

## How Exclusions Work

Exclusions are checked **before** inclusions. If any exclusion matches, the ad will NOT show, regardless of inclusion settings.

**Priority Order**:
1. Check if ad is active
2. Check user authentication status
3. Check all exclusion rules
4. Check inclusion rules
5. Check page type settings

## Admin Interface

All exclusion options are organized in the admin interface under:

- **Places NOT to Show - General Exclusions**
- **Places NOT to Show - User Pages**
- **Places NOT to Show - Blog Pages**
- **Places NOT to Show - Calculator Pages**
- **Placement Exclusions**

## Troubleshooting

### Ads Still Showing on Excluded Pages

1. Check that exclusion field is checked/set correctly
2. Verify the URL pattern matches exactly
3. Clear browser cache
4. Check that no other ad unit is overriding
5. Verify the exclusion logic in `should_display()` method

### Ads Not Showing Where Expected

1. Check if exclusion is too broad
2. Verify inclusion settings
3. Check page type settings
4. Review URL patterns

## Migration

After updating the exclusion fields, run:

```bash
python manage.py migrate google_adsense
```

This will add all the new exclusion fields to your database.
