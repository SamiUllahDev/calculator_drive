from django import forms
from .models import Comment, Post
from tinymce.widgets import TinyMCE
from django.conf import settings

class PostForm(forms.ModelForm):
    """Form for creating and editing blog posts with rich text editor"""
    
    class Meta:
        model = Post
        fields = ['title', 'category', 'featured_image', 'content', 'excerpt', 'status', 'published_date']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'excerpt': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'content': TinyMCE(attrs={'cols': 80, 'rows': 30}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'published_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        # Make published_date not required
        self.fields['published_date'].required = False
        self.fields['excerpt'].required = False
        self.fields['featured_image'].required = False
        
        # Help texts
        self.fields['title'].help_text = 'Choose a compelling title (70 characters max)'
        self.fields['excerpt'].help_text = 'A brief summary of the post (300 characters max)'
        self.fields['status'].help_text = 'Draft posts are not visible to the public'
        self.fields['published_date'].help_text = 'Leave blank to use current date/time when published'

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': TinyMCE(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': 'Write your comment here...'
            },
            # Custom TinyMCE config to disable images and links
            mce_attrs=settings.TINYMCE_COMMENT_CONFIG),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CommentForm, self).__init__(*args, **kwargs)

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': TinyMCE(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Write your reply here...'
            },
            # Simplified TinyMCE config for replies
            mce_attrs={
                'plugins': 'autolink lists charmap emoticons',
                'toolbar': 'bold italic | bullist numlist | emoticons | removeformat',
                'menubar': False,
                'statusbar': False,
                'height': 120,
                'branding': False,
                'promotion': False,
                'browser_spellcheck': True,
                'paste_data_images': False,
                'relative_urls': False,
                'remove_script_host': True
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ReplyForm, self).__init__(*args, **kwargs) 