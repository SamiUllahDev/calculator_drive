from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('feed/', views.blog_rss_feed, name='rss_feed'),
    path('tag/', RedirectView.as_view(pattern_name='blog:post_list', permanent=True), name='tag_index_redirect'),
    path('tag/<slug:slug>/', views.TagPostListView.as_view(), name='tag_detail'),
    path('<slug:category_slug>/', views.CategoryPostListView.as_view(), name='category_detail'),
    path('<slug:category_slug>/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('<slug:category_slug>/<slug:post_slug>/comment/<int:comment_id>/reply/', views.comment_reply, name='comment_reply'),
]