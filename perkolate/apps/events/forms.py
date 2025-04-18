from django import forms
from .models import Event, Target, Note

class EventForm(forms.ModelForm):
    """Form for creating and updating events"""
    
    class Meta:
        model = Event
        fields = ['title', 'description', 'start_date', 'end_date', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
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
        fields = ['title', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
        } 