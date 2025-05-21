from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Memory
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
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
