"""
Core models: Custom User, Student, Batch, and related entities.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """
    Custom user model with role-based access.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('parent', 'Parent'),
    ]
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='parent')
    phone = models.CharField(max_length=15, blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, help_text="WhatsApp number with country code (e.g., +919876543210)")
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    class Meta:
        ordering = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_parent(self):
        return self.role == 'parent'


class Batch(models.Model):
    """
    A batch/group of students (e.g., "Evening Batch - 7th Std").
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    teacher = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_batches',
        limit_choices_to={'role': 'teacher'}
    )
    class_level = models.CharField(max_length=20, blank=True, help_text="e.g., 7th, 8th, Jr.KG")
    schedule = models.CharField(max_length=200, blank=True, help_text="e.g., Mon-Fri 4:00-5:30 PM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Batches'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def student_count(self):
        return self.students.count()


BOARD_CHOICES = [
    ('CBSE', 'CBSE'),
    ('ICSE', 'ICSE'),
    ('SSC', 'SSC (Maharashtra State Board)'),
    ('IGCSE', 'IGCSE'),
    ('OTHER', 'Other'),
]

CLASS_CHOICES = [
    ('Jr.KG', 'Jr. KG'),
    ('Sr.KG', 'Sr. KG'),
    ('1st', '1st Standard'),
    ('2nd', '2nd Standard'),
    ('3rd', '3rd Standard'),
    ('4th', '4th Standard'),
    ('5th', '5th Standard'),
    ('6th', '6th Standard'),
    ('7th', '7th Standard'),
    ('8th', '8th Standard'),
    ('9th', '9th Standard'),
]


class Subject(models.Model):
    """
    Subject definition (e.g., Mathematics, English, Science).
    """
    name = models.CharField(max_length=100)
    class_level = models.CharField(max_length=20, choices=CLASS_CHOICES, blank=True)
    board = models.CharField(max_length=10, choices=BOARD_CHOICES, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name', 'class_level']
        unique_together = ['name', 'class_level', 'board']
    
    def __str__(self):
        return self.name


class Concept(models.Model):
    """
    Chapter/Concept within a subject for granular mastery tracking.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='concepts')
    name = models.CharField(max_length=200, help_text="Chapter or concept name")
    chapter_number = models.PositiveIntegerField(blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order within subject")
    
    class Meta:
        ordering = ['subject', 'order', 'chapter_number']
        unique_together = ['subject', 'name']
    
    def __str__(self):
        prefix = f"Ch.{self.chapter_number} - " if self.chapter_number else ""
        return f"{prefix}{self.name} ({self.subject.name})"


class Student(models.Model):
    """
    Student profile linked to a parent user.
    """
    name = models.CharField(max_length=200)
    date_of_birth = models.DateField(blank=True, null=True)
    class_level = models.CharField(max_length=20, choices=CLASS_CHOICES)
    board = models.CharField(max_length=10, choices=BOARD_CHOICES, default='SSC')
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='children',
        limit_choices_to={'role': 'parent'}
    )
    subjects = models.ManyToManyField(Subject, blank=True, related_name='enrolled_students')
    enrollment_date = models.DateField(auto_now_add=True)
    photo = models.ImageField(upload_to='students/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, help_text="Internal notes (visible to admin/teacher only)")
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_class_level_display()} - {self.get_board_display()})"
    
    @property
    def teacher(self):
        """Get the assigned teacher via batch."""
        if self.batch and self.batch.teacher:
            return self.batch.teacher
        return None
