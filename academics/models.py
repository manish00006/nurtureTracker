"""
Academics models: Attendance, TestScore, ConceptMastery, Homework, FeeRecord.
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import User, Student, Batch, Subject, Concept


class Attendance(models.Model):
    """
    Daily attendance record per student.
    """
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='marked_attendance',
        limit_choices_to={'role__in': ['teacher', 'admin']}
    )
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', 'student__name']
        verbose_name_plural = 'Attendance Records'
    
    def __str__(self):
        return f"{self.student.name} - {self.date} - {self.get_status_display()}"


class TestScore(models.Model):
    """
    Test/exam score record for a student.
    """
    TEST_TYPE_CHOICES = [
        ('weekly', 'Weekly Test'),
        ('monthly', 'Monthly Exam'),
        ('unit', 'Unit Test'),
        ('midterm', 'Mid-Term Exam'),
        ('final', 'Final Exam'),
        ('practice', 'Practice Test'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='test_scores')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='test_scores')
    concept = models.ForeignKey(
        Concept, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='test_scores',
        help_text="Optional: specific chapter/concept tested"
    )
    test_name = models.CharField(max_length=200)
    date = models.DateField()
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
    total_marks = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(1)])
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES, default='weekly')
    entered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='entered_scores'
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', 'student__name']
    
    def __str__(self):
        return f"{self.student.name} - {self.test_name} - {self.marks_obtained}/{self.total_marks}"
    
    @property
    def percentage(self):
        if self.total_marks > 0:
            return round((self.marks_obtained / self.total_marks) * 100, 1)
        return 0


class ConceptMastery(models.Model):
    """
    Per-concept mastery status for a student.
    """
    MASTERY_STATUS = [
        ('not_started', 'Not Started'),
        ('needs_work', 'Needs Work'),
        ('mastered', 'Mastered'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='concept_mastery')
    concept = models.ForeignKey(Concept, on_delete=models.CASCADE, related_name='student_mastery')
    status = models.CharField(max_length=15, choices=MASTERY_STATUS, default='not_started')
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_mastery'
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'concept']
        verbose_name_plural = 'Concept Mastery Records'
        ordering = ['concept__subject', 'concept__order']
    
    def __str__(self):
        return f"{self.student.name} - {self.concept.name} - {self.get_status_display()}"


class Homework(models.Model):
    """
    Homework assignment, can be assigned to a batch or individual student.
    """
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending'),
        ('late', 'Late'),
    ]
    
    student = models.ForeignKey(
        Student, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='homework',
        help_text="Leave blank if assigned to entire batch"
    )
    batch = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='homework',
        help_text="Assign to entire batch"
    )
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='homework')
    description = models.TextField()
    assigned_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='assigned')
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_homework'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-due_date']
        verbose_name_plural = 'Homework'
    
    def __str__(self):
        target = self.student.name if self.student else (self.batch.name if self.batch else "Unassigned")
        return f"{self.subject.name} - {target} - Due: {self.due_date}"


class FeeRecord(models.Model):
    """
    Monthly fee tracking per student.
    """
    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
        ('partial', 'Partially Paid'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_records')
    month = models.DateField(help_text="First day of the billing month")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.student.name} - {self.month.strftime('%B %Y')} - {self.get_status_display()}"
