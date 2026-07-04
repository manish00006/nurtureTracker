"""
URL configuration for academics app.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Bulk Attendance
    path('attendance/bulk/', views.bulk_attendance, name='bulk_attendance'),

    # Bulk Scores
    path('scores/bulk/', views.bulk_scores, name='bulk_scores'),

    # Concept Mastery
    path('mastery/', views.concept_mastery_manage, name='concept_mastery'),

    # Homework
    path('homework/', views.homework_manage, name='homework_manage'),
    path('homework/add/', views.homework_create, name='homework_create'),
    path('homework/<int:pk>/status/', views.homework_update_status, name='homework_update_status'),

    # Student Progress API (JSON for charts)
    path('api/student/<int:pk>/progress/', views.student_progress_api, name='student_progress_api'),
]
