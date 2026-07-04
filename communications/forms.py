from django import forms
from .models import Notice
from core.models import Student, Batch


class TeacherNoticeForm(forms.ModelForm):
    send_whatsapp = forms.BooleanField(
        required=False, 
        initial=True, 
        label="Also send via WhatsApp"
    )

    class Meta:
        model = Notice
        fields = ['title', 'message', 'target_scope', 'target_batch', 'target_class', 'notice_type', 'is_pinned']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Tomorrow class is off'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'target_scope': forms.Select(attrs={'class': 'form-input'}),
            'target_batch': forms.Select(attrs={'class': 'form-input'}),
            'target_class': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., 10th Standard'}),
            'notice_type': forms.Select(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher and not teacher.is_admin_user:
            # Teachers can only target their own batches
            self.fields['target_batch'].queryset = Batch.objects.filter(teacher=teacher, is_active=True)


class ParentNoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['student', 'notice_type', 'title', 'message']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-input'}),
            'notice_type': forms.Select(attrs={'class': 'form-input'}),
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Brief subject'}),
            'message': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }
        
    def __init__(self, *args, **kwargs):
        parent = kwargs.pop('parent', None)
        super().__init__(*args, **kwargs)
        if parent:
            self.fields['student'].queryset = Student.objects.filter(parent=parent, is_active=True)
