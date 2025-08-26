from django import forms
from .models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'owner', 'status', 'priority', 'notes', 'budget', 'file', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract user from kwargs if provided
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set default owner to current user's email if available
        if self.user and hasattr(self.user, 'email') and self.user.email:
            self.fields['owner'].initial = self.user.email
    
    def save(self, commit=True):
        task = super().save(commit=False)
        # Associate task with user if provided
        if self.user:
            task.user = self.user
        if commit:
            task.save()
        return task