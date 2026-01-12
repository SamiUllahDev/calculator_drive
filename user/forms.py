from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm, PasswordResetForm
from django.utils.translation import gettext_lazy as _
from .models import Profile


class UserRegistrationForm(UserCreationForm):
    """Extended user registration form with email field"""
    email = forms.EmailField(required=True, label=_('Email Address'))
    first_name = forms.CharField(required=True, max_length=150, label=_('First Name'))
    last_name = forms.CharField(required=True, max_length=150, label=_('Last Name'))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 '
                         'placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 '
                         'focus:border-blue-500'
            })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Email already exists. Please use another email.'))
        return email


class UserUpdateForm(forms.ModelForm):
    """Form for updating basic user information"""
    email = forms.EmailField(required=True, label=_('Email Address'))
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
    
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 '
                         'placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 '
                         'focus:border-blue-500'
            })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(_('Email already exists. Please use another email.'))
        return email


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating profile information"""
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
        label=_('Birth Date')
    )
    
    language = forms.ChoiceField(
        choices=[
            ('en', _('English')),  # ~1.5 billion speakers
            ('zh', _('Mandarin Chinese')),  # ~1.1 billion speakers
            ('hi', _('Hindi')),  # ~600 million speakers
            ('es', _('Spanish')),  # ~550 million speakers
            ('fr', _('French')),  # ~280 million speakers
            ('ar', _('Arabic')),  # ~310 million speakers
            ('bn', _('Bengali')),  # ~265 million speakers
            ('pt', _('Portuguese')),  # ~260 million speakers
            ('ru', _('Russian')),  # ~260 million speakers
            ('ja', _('Japanese')),  # ~125 million speakers
            ('de', _('German')),  # ~130 million speakers
            ('pa', _('Punjabi')),  # ~125 million speakers
            ('jv', _('Javanese')),  # ~84 million speakers
            ('id', _('Indonesian')),  # ~200 million speakers
            ('te', _('Telugu')),  # ~95 million speakers
            ('vi', _('Vietnamese')),  # ~85 million speakers
            ('it', _('Italian')),  # ~85 million speakers
            ('tr', _('Turkish')),  # ~88 million speakers
            ('ko', _('Korean')),  # ~82 million speakers
            ('ur', _('Urdu')),  # ~230 million speakers
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
        label=_('Language')
    )
    
    timezone = forms.ChoiceField(
        choices=[
            ('UTC', 'UTC'),
            ('America/New_York', 'Eastern Time (US & Canada)'),
            ('America/Chicago', 'Central Time (US & Canada)'),
            ('America/Denver', 'Mountain Time (US & Canada)'),
            ('America/Los_Angeles', 'Pacific Time (US & Canada)'),
            ('Europe/London', 'London'),
            ('Europe/Paris', 'Paris'),
            ('Asia/Dubai', 'Dubai'),
            ('Asia/Kolkata', 'Mumbai, Kolkata, Chennai, New Delhi'),
            ('Asia/Tokyo', 'Tokyo'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
        label=_('Timezone')
    )
    
    class Meta:
        model = Profile
        fields = ('avatar', 'bio', 'location', 'website', 'phone', 'gender', 
                  'birth_date', 'company', 'job_title', 'twitter', 'facebook', 
                  'linkedin', 'email_notifications', 'profile_privacy', 
                  'show_email', 'show_location', 'show_birth_date', 'theme', 
                  'language', 'timezone')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'location': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'website': forms.URLInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'phone': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'gender': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'company': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'job_title': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'twitter': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'facebook': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'linkedin': forms.TextInput(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
            'profile_privacy': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
            'show_location': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
            'show_birth_date': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500'}),
            'theme': forms.Select(attrs={'class': 'block w-full rounded-lg border border-gray-300 bg-white px-4 py-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500'}),
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    def __init__(self, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 '
                         'placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 '
                         'focus:border-blue-500'
            })


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with Bootstrap styling"""
    def __init__(self, *args, **kwargs):
        super(CustomPasswordResetForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'block w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-gray-900 '
                         'placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 '
                         'focus:border-blue-500'
            })