from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Memory, UserProfile
import uuid

class MemoryForm(forms.ModelForm):
    """Form for creating and editing memories."""
    class Meta:
        model = Memory
        fields = ['text', 'permission', 'expiration_date']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
            'permission': forms.Select(attrs={'class': 'form-select'}),
            'expiration_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }

class MemorySearchForm(forms.Form):
    """Form for searching memories."""
    query = forms.CharField(
        label='Search Query',
        max_length=500,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter search query'})
    )
    limit = forms.IntegerField(
        label='Result Limit',
        min_value=1,
        max_value=50,
        initial=10,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

class UserQueryForm(forms.Form):
    """Form for querying a user's persona."""
    user_id = forms.UUIDField(
        label='User ID',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter user UUID'})
    )
    prompt = forms.CharField(
        label='Query Prompt',
        max_length=1000,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter your question'})
    )

class UserRegistrationForm(UserCreationForm):
    """Form for user registration with email field."""
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class UserProfileForm(forms.ModelForm):
    """Form for updating user profile information."""
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = UserProfile
        fields = ('bio', 'date_of_birth')
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()
            profile.save()
        
        return profile
