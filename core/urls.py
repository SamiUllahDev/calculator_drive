

from django.urls import path
from .views import Index, PrivacyPolicyView, TermsOfServiceView, CookiePolicyView, AboutUsView, SitemapView, SearchView

app_name = 'core'

urlpatterns = [
    path('', Index.as_view(), name='index'),
    path('search/', SearchView.as_view(), name='search'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('terms-of-service/', TermsOfServiceView.as_view(), name='terms_of_service'),
    path('cookie-policy/', CookiePolicyView.as_view(), name='cookie_policy'),
    path('sitemap/', SitemapView.as_view(), name='sitemap'),
    path('about/', AboutUsView.as_view(), name='about_us'),
]
