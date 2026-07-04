"""
Communications models: Notice (bidirectional messaging), AIConversationLog.
"""

from django.db import models
from core.models import User, Student, Batch


class Notice(models.Model):
    """
    Bidirectional notice/message between teachers and parents.
    """
    SENDER_TYPE_CHOICES = [
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
        ('admin', 'Admin'),
    ]
    
    TARGET_SCOPE_CHOICES = [
        ('all_parents', 'All Parents'),
        ('specific_batch', 'Specific Batch'),
        ('specific_class', 'Specific Class'),
        ('single_parent', 'Single Parent'),
    ]
    
    NOTICE_TYPE_CHOICES = [
        ('class_off', 'Class Off'),
        ('announcement', 'Announcement'),
        ('leave_request', 'Leave Request'),
        ('query', 'Query'),
        ('general_note', 'General Note'),
        ('fee_reminder', 'Fee Reminder'),
    ]
    
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('seen', 'Seen'),
        ('acknowledged', 'Acknowledged'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    
    sender_type = models.CharField(max_length=10, choices=SENDER_TYPE_CHOICES)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notices')
    
    # For parent-originated notices: tied to their child
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notices',
        help_text="Required for parent-originated notices"
    )
    
    # For teacher-originated notices: target scope
    target_scope = models.CharField(
        max_length=20, 
        choices=TARGET_SCOPE_CHOICES, 
        blank=True,
        help_text="Used for teacher/admin notices"
    )
    target_batch = models.ForeignKey(
        Batch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notices',
        help_text="When target_scope is specific_batch"
    )
    target_class = models.CharField(max_length=20, blank=True, help_text="When target_scope is specific_class")
    
    notice_type = models.CharField(max_length=15, choices=NOTICE_TYPE_CHOICES, default='general_note')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='sent')
    
    teacher_reply = models.TextField(blank=True, help_text="Teacher's reply to parent note")
    reply_date = models.DateTimeField(null=True, blank=True)
    
    expiry_date = models.DateField(null=True, blank=True, help_text="Auto-hide after this date")
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_posted']
        verbose_name_plural = 'Notices'
    
    def __str__(self):
        return f"[{self.get_notice_type_display()}] {self.title} — by {self.sender.get_full_name()}"


class AIConversationLog(models.Model):
    """
    Logs for AI assistant conversations.
    """
    SOURCE_CHOICES = [
        ('parent_qa', 'Parent Q&A'),
        ('student_doubt', 'Student Doubt Solving'),
        ('auto_summary', 'Auto Progress Summary'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    message = models.TextField()
    response = models.TextField()
    source = models.CharField(max_length=15, choices=SOURCE_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    tokens_used = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_source_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
