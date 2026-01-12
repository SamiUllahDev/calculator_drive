from django.urls import path
from . import views

app_name = 'google_adsense'

urlpatterns = [
    path('preview/<int:ad_unit_id>/', views.ad_preview, name='ad_preview'),
    path('track/', views.track_ad_display, name='track_ad_display'),
]
