"""
Admin configuration for academics models.
"""

from django.contrib import admin
from .models import Attendance, TestScore, ConceptMastery, Homework, FeeRecord


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status', 'marked_by', 'created_at']
    list_filter = ['status', 'date', 'student__batch']
    search_fields = ['student__name']
    date_hierarchy = 'date'


@admin.register(TestScore)
class TestScoreAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'test_name', 'marks_obtained', 'total_marks', 'percentage', 'test_type', 'date']
    list_filter = ['test_type', 'subject', 'date']
    search_fields = ['student__name', 'test_name']
    date_hierarchy = 'date'


@admin.register(ConceptMastery)
class ConceptMasteryAdmin(admin.ModelAdmin):
    list_display = ['student', 'concept', 'status', 'last_updated', 'updated_by']
    list_filter = ['status', 'concept__subject']
    search_fields = ['student__name', 'concept__name']


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ['subject', 'student', 'batch', 'due_date', 'status', 'assigned_by']
    list_filter = ['status', 'subject', 'due_date']
    search_fields = ['description', 'student__name']
    date_hierarchy = 'due_date'


@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ['student', 'month', 'amount_due', 'amount_paid', 'status', 'due_date']
    list_filter = ['status', 'month']
    search_fields = ['student__name']
