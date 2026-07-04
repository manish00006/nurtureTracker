"""
Admin configuration for communications models.
"""

from django.contrib import admin
from .models import Notice, AIConversationLog


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'sender', 'sender_type', 'notice_type', 'status', 'date_posted', 'expiry_date']
    list_filter = ['sender_type', 'notice_type', 'status']
    search_fields = ['title', 'message', 'sender__first_name', 'sender__last_name']
    date_hierarchy = 'date_posted'


@admin.register(AIConversationLog)
class AIConversationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'student', 'source', 'timestamp', 'tokens_used']
    list_filter = ['source']
    search_fields = ['user__first_name', 'message', 'response']
    date_hierarchy = 'timestamp'
    readonly_fields = ['user', 'student', 'message', 'response', 'source', 'timestamp', 'tokens_used']
