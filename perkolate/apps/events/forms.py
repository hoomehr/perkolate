from django import forms
from .models import Event, Target, Note

class EventForm(forms.ModelForm):
    """Form for creating and updating events"""
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter event title'}),
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Enter event description'}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TargetForm(forms.ModelForm):
    """Form for creating and updating targets"""
    
    class Meta:
        model = Target
        fields = ['name', 'description', 'status', 'priority', 'due_date', 'assignee']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class NoteForm(forms.ModelForm):
    """Form for creating and updating notes"""
    
    class Meta:
        model = Note
        fields = ['title', 'content', 'events', 'target']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'events': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'target': forms.Select(attrs={'class': 'form-control'}),
        } 