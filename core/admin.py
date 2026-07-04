"""
Admin configuration for core models.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Batch, Subject, Concept, Student


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Nurture Profile', {
            'fields': ('role', 'phone', 'whatsapp_number', 'profile_photo'),
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Nurture Profile', {
            'fields': ('role', 'first_name', 'last_name', 'email', 'phone', 'whatsapp_number'),
        }),
    )


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher', 'class_level', 'schedule', 'student_count', 'is_active']
    list_filter = ['is_active', 'class_level']
    search_fields = ['name', 'teacher__first_name', 'teacher__last_name']


class ConceptInline(admin.TabularInline):
    model = Concept
    extra = 1
    fields = ['name', 'chapter_number', 'order', 'description']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_level', 'board', 'is_active']
    list_filter = ['class_level', 'board', 'is_active']
    search_fields = ['name']
    inlines = [ConceptInline]


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'chapter_number', 'order']
    list_filter = ['subject__name', 'subject__class_level']
    search_fields = ['name', 'subject__name']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_level', 'board', 'batch', 'parent', 'is_active', 'enrollment_date']
    list_filter = ['class_level', 'board', 'batch', 'is_active']
    search_fields = ['name', 'parent__first_name', 'parent__last_name']
    filter_horizontal = ['subjects']
    
    fieldsets = (
        ('Student Info', {
            'fields': ('name', 'date_of_birth', 'photo', 'is_active'),
        }),
        ('Academic', {
            'fields': ('class_level', 'board', 'batch', 'subjects'),
        }),
        ('Parent Link', {
            'fields': ('parent',),
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',),
        }),
    )
