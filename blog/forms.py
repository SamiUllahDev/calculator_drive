from django import forms
from .models import Comment
from tinymce.widgets import TinyMCE
from django.conf import settings


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
                'remove_script_host': True,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ReplyForm, self).__init__(*args, **kwargs)