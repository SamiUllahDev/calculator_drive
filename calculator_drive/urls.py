"""
URL configuration for CalculatorDrive project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
import os
from core.sitemap_view import sitemap
from core.sitemaps import (
    StaticViewSitemap,
    CalculatorIndexSitemap,
    MathCalculatorSitemap,
    FinanceCalculatorSitemap,
    HealthCalculatorSitemap,
    OtherCalculatorSitemap,
    BlogPostSitemap,
    BlogCategorySitemap,
    BlogTagSitemap,
)
from core.views import custom_404_view

# Sitemap dictionary
sitemaps = {
    'static': StaticViewSitemap,
    'calculator-indexes': CalculatorIndexSitemap,
    'math-calculators': MathCalculatorSitemap,
    'finance-calculators': FinanceCalculatorSitemap,
    'health-calculators': HealthCalculatorSitemap,
    'other-calculators': OtherCalculatorSitemap,
    'blog-posts': BlogPostSitemap,
    'blog-categories': BlogCategorySitemap,
    'blog-tags': BlogTagSitemap,
}

# ads.txt view for Google AdSense
def ads_txt(request):
    ads_txt_path = os.path.join(settings.BASE_DIR, 'ads.txt')
    with open(ads_txt_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/plain')

# robots.txt view for search engine crawlers
def robots_txt(request):
    robots_txt_path = os.path.join(settings.BASE_DIR, 'robots.txt')
    with open(robots_txt_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='text/plain')

# URLs that should NOT have language prefix
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/setlang/', set_language, name='set_language'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('ads.txt', ads_txt, name='ads_txt'),
    path('robots.txt', robots_txt, name='robots_txt'),
    # TinyMCE image upload (outside i18n so admin can always reach it)
    path('blog/tinymce/upload/', __import__('blog.views', fromlist=['tinymce_image_upload']).tinymce_image_upload, name='tinymce_image_upload'),
]

# URLs that should have language prefix (e.g., /ar/, /fr/, but NOT /en/ for default)
urlpatterns += i18n_patterns(
    path('', include('core.urls')),
    path('finance/', include('Financial_Calculators.urls')),
    path('health/', include('Fitness_and_Health_Calculators.urls')),
    path('math/', include('Math_Calculators.urls')),
    path('other/', include('Other_Calculators.urls')),
    path('blog/', include('blog.urls')),
    path('user/', include('user.urls')),
    path('adsense/', include('google_adsense.urls')),
    path('accounts/', include('allauth.urls')),
    prefix_default_language=False,  # Don't prefix default language (en) - /blog/ not /en/blog/
)

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.views.custom_404_view'
