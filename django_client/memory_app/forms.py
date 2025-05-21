from django import forms
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
