"""
Forms for core app: Authentication, Student CRUD, User management.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, Student, Batch, Subject


class NurtureLoginForm(AuthenticationForm):
    """Custom login form with styled fields."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
        })
    )


class StudentForm(forms.ModelForm):
    """Form for creating/editing students."""
    
    class Meta:
        model = Student
        fields = ['name', 'date_of_birth', 'class_level', 'board', 'batch', 'parent', 'subjects', 'photo', 'is_active', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Student full name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'class_level': forms.Select(attrs={'class': 'form-input'}),
            'board': forms.Select(attrs={'class': 'form-input'}),
            'batch': forms.Select(attrs={'class': 'form-input'}),
            'parent': forms.Select(attrs={'class': 'form-input'}),
            'subjects': forms.CheckboxSelectMultiple(attrs={'class': 'form-checkbox-list'}),
            'photo': forms.FileInput(attrs={'class': 'form-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': '3', 'placeholder': 'Internal notes...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = User.objects.filter(role='parent')
        self.fields['batch'].required = False
        self.fields['date_of_birth'].required = False
        self.fields['notes'].required = False


class BatchForm(forms.ModelForm):
    """Form for creating/editing batches."""
    
    class Meta:
        model = Batch
        fields = ['name', 'description', 'teacher', 'class_level', 'schedule', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Batch name'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
            'teacher': forms.Select(attrs={'class': 'form-input'}),
            'class_level': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 7th, 8th'}),
            'schedule': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Mon-Fri 4:00-5:30 PM'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(role='teacher')
        self.fields['teacher'].required = False


class SubjectForm(forms.ModelForm):
    """Form for creating/editing subjects."""
    
    class Meta:
        model = Subject
        fields = ['name', 'class_level', 'board', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Subject name'}),
            'class_level': forms.Select(attrs={'class': 'form-input'}),
            'board': forms.Select(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': '2'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class UserCreateForm(forms.ModelForm):
    """Form for admin to create new users (teachers/parents)."""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Set password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm password'}))
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'role', 'phone', 'whatsapp_number']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Email address'}),
            'role': forms.Select(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Phone number'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+919876543210'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError("Passwords don't match.")
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
