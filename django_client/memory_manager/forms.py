from django import forms
from .models import Memory


class MemoryForm(forms.ModelForm):
    """Form for creating and updating memories"""
    class Meta:
        model = Memory
        fields = ['text', 'is_public']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }


class QueryForm(forms.Form):
    """Form for querying the user's memories"""
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your question...'}),
        label="Your Question"
    )
