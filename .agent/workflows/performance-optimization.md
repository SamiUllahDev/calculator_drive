---
description: How to optimize Core Web Vitals and deploy performance improvements
---

# Performance Optimization Workflow

## Pre-Deployment Checklist

### 1. Cloudflare Configuration (CRITICAL - do these in Cloudflare Dashboard)

These items cause **160ms render-blocking** and **258KB unused JS** that we CANNOT fix in code:

- **Disable Rocket Loader**: Speed → Optimization → Content Optimization → Rocket Loader → OFF
  - Rocket Loader wraps ALL scripts and defers them, adding ~160ms delay
  - We already defer 3rd party scripts manually with `requestIdleCallback`
  
- **Disable Email Address Obfuscation**: Scrape Shield → Email Address Obfuscation → OFF
  - `email-decode.min.js` is injected and render-blocks
  - Only disable if you don't have email addresses exposed in HTML

- **Enable Auto Minify**: Speed → Optimization → Content Optimization → Auto Minify → JS, CSS, HTML

- **Set Browser Cache TTL**: Caching → Configuration → Browser Cache TTL → 1 year
  - Fixes the "47m 49s cache TTL" warning in Lighthouse

- **Review Page Rules for Cache**: Add a page rule for `calculatordrive.com/*`:
  - Cache Level: Cache Everything
  - Edge Cache TTL: 2 hours
  - Browser Cache TTL: 4 hours (for HTML)

### 2. Remove/Optimize Grow.me (saves 258KB)

If `grow.me` widget is installed via Cloudflare Apps or a third-party integration:
- Consider removing it or lazy-loading it
- It contributes 258KB of unused JavaScript

### 3. Deploy Code Changes

// turbo
```bash
# Collect static files with WhiteNoise hashing
python manage.py collectstatic --noinput
```

### 4. Verify After Deploy

// turbo
```bash
# Run a quick Lighthouse check (requires lighthouse CLI)
npx lighthouse https://calculatordrive.com --only-categories=performance --output=json --output-path=./lighthouse-report.json --chrome-flags='--headless' --preset=perf
```

## What's Been Optimized (Code-Side)

### CLS Fixes (was 0.673 → target <0.1)
- Tailwind CSS kept render-blocking (async caused CLS 0.67)
- Critical hero section CSS inlined (hero-section, hero-title, hero-subtitle, quick-tags dimensions)
- Hero glow orbs dimensions inlined
- Search bar and button dimensions inlined

### LCP Fixes (was 4.7s → target <2.5s)  
- GTM moved from `<head>` to deferred loader at bottom of `<body>`
- `site.min.css` made async (critical parts inlined)
- FontAwesome made async (icons are decorative)
- Only Inter-400 preloaded (was preloading 3 fonts = 330KB competing with LCP)
- All scripts marked `data-cfasync="false"` to prevent Rocket Loader interference
- PerformanceHeadersMiddleware adds Link preload header for font
- Cache-Control: stale-while-revalidate for CDN edge caching

### INP Fixes (was 268ms → target <200ms)
- Hero orb animations simplified (removed scale transforms)
- Orb animations disabled on mobile (<768px)
- `prefers-reduced-motion` support added
- Content-visibility: auto on below-fold sections

### Accessibility
- `<header>` role changed to "banner"
- Mobile drawer role changed to "dialog" with aria-modal="true"

### Server-Side
- Homepage cache increased to 30 minutes
- PerformanceHeadersMiddleware for Link preload and Cache-Control headers
