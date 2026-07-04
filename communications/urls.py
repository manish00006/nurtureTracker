from django.urls import path
from . import views

urlpatterns = [
    path('notices/', views.notice_list, name='notice_list'),
    path('notices/new/', views.notice_create, name='notice_create'),
    path('notices/<int:pk>/', views.notice_detail, name='notice_detail'),
    path('assistant/', views.ai_assistant, name='ai_assistant'),
]
