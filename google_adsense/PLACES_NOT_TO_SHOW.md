# Places Where Ads Will NOT Show

This is a simple reference guide for all the places where you can exclude ads.

## Quick Reference

### ✅ Default Exclusions (Already Enabled)
These are turned ON by default - ads will NOT show here:

- ❌ **Admin Pages** (`/admin/`) - Admin interface
- ❌ **Login/Register Pages** (`/accounts/login/`, `/user/register/`) - Authentication pages
- ❌ **User Dashboard** (`/user/dashboard/`) - User dashboard
- ❌ **User Settings** (`/user/account/settings/`, `/user/privacy/`, `/user/security/`) - Settings pages
- ❌ **Blog Create/Edit** (`/blog/create/`, `/blog/edit/`) - Blog editing pages
- ❌ **Privacy/Terms Pages** (`/privacy-policy/`, `/terms-of-service/`, `/cookie-policy/`) - Policy pages

### ⚙️ Optional Exclusions (Turn ON if needed)

#### User Pages
- ❌ **User Profiles** (`/user/profile/`) - User profile pages
  - Default: OFF (ads will show)
  - Check box to hide ads

#### Calculator Categories
- ❌ **Math Calculators** (`/math/`) - All math calculator pages
- ❌ **Finance Calculators** (`/finance/`) - All finance calculator pages
- ❌ **Health Calculators** (`/health/`) - All health calculator pages
- ❌ **Other Calculators** (`/other/`) - All other calculator pages

#### Specific Calculators
- ❌ **Exclude Specific Calculators** - List calculator slugs
  - Example: `area-calculator, bmi-calculator, mortgage-calculator`
  - Hides ads on those specific calculator pages

#### Blog Content
- ❌ **Blog Categories** - List category slugs
  - Example: `tutorials, news`
  - Hides ads on `/blog/category/tutorials/`, etc.
  
- ❌ **Blog Tags** - List tag slugs
  - Example: `django, python`
  - Hides ads on `/blog/tag/django/`, etc.

#### Placements
- ❌ **Exclude from Placements** - List placement names
  - Example: `sidebar, footer`
  - This ad won't show in sidebar or footer, even if it matches other criteria

#### URL Patterns
- ❌ **Exclude URLs** - List URL patterns
  - Example: `/user/, /admin/, /blog/create/`
  - Any URL containing these patterns won't show ads

## How to Configure

### In Django Admin:

1. Go to: `/admin/google_adsense/adunit/`
2. Click on an ad unit to edit
3. Scroll to sections:
   - **"Places NOT to Show - General Exclusions"**
   - **"Places NOT to Show - User Pages"**
   - **"Places NOT to Show - Blog Pages"**
   - **"Places NOT to Show - Calculator Pages"**
   - **"Placement Exclusions"**
4. Check boxes or fill in fields as needed
5. Save

## Examples

### Example 1: Hide Ads from All Math Calculators
```
✅ Exclude from Math Calculators: Checked
```
Result: No ads on `/math/area-calculator/`, `/math/triangle-calculator/`, etc.

### Example 2: Hide Ads from Specific Calculators Only
```
Exclude Calculators: area-calculator, bmi-calculator
```
Result: No ads on `/math/area-calculator/` and `/health/bmi-calculator/`, but ads show on other calculators.

### Example 3: Hide Ads from Blog Tutorials
```
Exclude Blog Categories: tutorials
```
Result: No ads on `/blog/category/tutorials/` or any posts in that category.

### Example 4: Hide Ads from Sidebar Placement
```
Placement: sidebar
Exclude Placements: sidebar
```
Result: This ad won't show in sidebar, but will show in other placements.

### Example 5: Hide Ads from User Pages
```
✅ Exclude from User Dashboard: Checked
✅ Exclude from User Profiles: Checked
✅ Exclude from User Settings: Checked
```
Result: No ads on any user-related pages.

## Complete List of Excludable Places

### Pages
- [x] Admin pages (`/admin/`)
- [x] Login pages (`/accounts/login/`, `/user/register/`)
- [x] User dashboard (`/user/dashboard/`)
- [x] User profiles (`/user/profile/`)
- [x] User settings (`/user/account/settings/`, `/user/privacy/`, `/user/security/`)
- [x] Blog create/edit (`/blog/create/`, `/blog/edit/`)
- [x] Privacy/Terms pages (`/privacy-policy/`, `/terms-of-service/`, `/cookie-policy/`)

### Calculator Categories
- [ ] Math calculators (`/math/`)
- [ ] Finance calculators (`/finance/`)
- [ ] Health calculators (`/health/`)
- [ ] Other calculators (`/other/`)

### Specific Content
- [ ] Specific calculators (list slugs)
- [ ] Blog categories (list slugs)
- [ ] Blog tags (list slugs)

### Placements
- [ ] Specific placements (list names)

### URL Patterns
- [ ] Any URL pattern (list patterns)

## Summary

**By default, ads are hidden from:**
- Admin interface
- Login/register pages
- User dashboard
- User settings
- Blog editing pages
- Privacy/terms pages

**You can optionally hide ads from:**
- User profiles
- Calculator categories
- Specific calculators
- Blog categories/tags
- Specific placements
- Any URL pattern

## Need Help?

See `EXCLUSION_GUIDE.md` for detailed explanations and advanced usage.
