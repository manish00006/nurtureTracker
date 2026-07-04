"""
Views for core app: Authentication, Dashboard, Student CRUD, User management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden, JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import date, timedelta

from .models import User, Student, Batch, Subject, Concept
from .forms import NurtureLoginForm, StudentForm, BatchForm, SubjectForm, UserCreateForm
from .decorators import admin_required, teacher_or_admin_required
from academics.models import Attendance, TestScore, ConceptMastery, Homework
from communications.models import Notice


# ─── Authentication ──────────────────────────────────────────

def login_view(request):
    """Custom login page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = NurtureLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = NurtureLoginForm()
    
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    """Logout and redirect to login."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ─── Dashboard ───────────────────────────────────────────────

@login_required
def dashboard(request):
    """Role-based dashboard."""
    user = request.user
    context = {'today': date.today()}
    
    if user.is_admin_user:
        context.update(get_admin_dashboard_context())
        return render(request, 'core/dashboard_admin.html', context)
    elif user.is_teacher:
        context.update(get_teacher_dashboard_context(user))
        return render(request, 'core/dashboard_teacher.html', context)
    elif user.is_parent:
        context.update(get_parent_dashboard_context(user))
        return render(request, 'core/dashboard_parent.html', context)
    
    return render(request, 'core/dashboard_admin.html', context)


def get_admin_dashboard_context():
    """Admin sees overview of everything."""
    today = date.today()
    return {
        'total_students': Student.objects.filter(is_active=True).count(),
        'total_teachers': User.objects.filter(role='teacher', is_active=True).count(),
        'total_parents': User.objects.filter(role='parent', is_active=True).count(),
        'total_batches': Batch.objects.filter(is_active=True).count(),
        'recent_students': Student.objects.filter(is_active=True).order_by('-enrollment_date')[:5],
        'today_attendance_count': Attendance.objects.filter(date=today).count(),
        'today_present': Attendance.objects.filter(date=today, status='present').count(),
        'today_absent': Attendance.objects.filter(date=today, status='absent').count(),
        'unread_notices': Notice.objects.filter(sender_type='parent', status='sent').count(),
        'recent_notices': Notice.objects.all()[:5],
    }


def get_teacher_dashboard_context(teacher):
    """Teacher sees their batches and assigned students."""
    today = date.today()
    my_batches = Batch.objects.filter(teacher=teacher, is_active=True)
    my_students = Student.objects.filter(batch__in=my_batches, is_active=True)
    
    return {
        'my_batches': my_batches,
        'my_students': my_students,
        'my_student_count': my_students.count(),
        'today_marked': Attendance.objects.filter(
            student__in=my_students, date=today
        ).count(),
        'total_to_mark': my_students.count(),
        'unread_notices': Notice.objects.filter(
            sender_type='parent',
            student__in=my_students,
            status='sent'
        ).count(),
        'parent_messages': Notice.objects.filter(
            sender_type='parent',
            student__in=my_students,
        ).order_by('-date_posted')[:5],
        'recent_scores': TestScore.objects.filter(
            student__in=my_students
        ).order_by('-date')[:5],
        'at_risk_students': _get_at_risk(teacher),
    }


def _get_at_risk(teacher):
    """Lazy import to avoid circular dependency."""
    from academics.views import get_at_risk_students
    return get_at_risk_students(teacher)


def get_parent_dashboard_context(parent):
    """Parent sees only their children's data — strict scoping."""
    today = date.today()
    children = Student.objects.filter(parent=parent, is_active=True)
    
    children_data = []
    for child in children:
        # Today's attendance
        today_attendance = Attendance.objects.filter(
            student=child, date=today
        ).first()
        
        # Latest test scores
        latest_scores = TestScore.objects.filter(
            student=child
        ).order_by('-date')[:3]
        
        # Today's homework
        today_homework = Homework.objects.filter(
            Q(student=child) | Q(batch=child.batch),
            due_date__gte=today
        ).order_by('due_date')[:3]
        
        # Attendance stats this month
        month_start = today.replace(day=1)
        month_attendance = Attendance.objects.filter(
            student=child,
            date__gte=month_start,
            date__lte=today
        )
        total_days = month_attendance.count()
        present_days = month_attendance.filter(status='present').count()
        attendance_pct = round((present_days / total_days * 100), 1) if total_days > 0 else None
        
        children_data.append({
            'student': child,
            'today_attendance': today_attendance,
            'latest_scores': latest_scores,
            'today_homework': today_homework,
            'attendance_pct': attendance_pct,
            'present_days': present_days,
            'total_days': total_days,
        })
    
    recent_notices = Notice.objects.filter(
        Q(target_scope='all_parents') |
        Q(target_batch__in=children.values('batch')) |
        Q(student__in=children)
    ).distinct().order_by('-date_posted')[:5]
    
    return {
        'children': children,
        'children_data': children_data,
        'recent_notices': recent_notices,
    }


# ─── Student CRUD ────────────────────────────────────────────

@teacher_or_admin_required
def student_list(request):
    """List all students (filtered by teacher's batches if teacher)."""
    user = request.user
    
    if user.is_admin_user:
        students = Student.objects.filter(is_active=True)
    else:
        my_batches = Batch.objects.filter(teacher=user)
        students = Student.objects.filter(batch__in=my_batches, is_active=True)
    
    # Filtering
    batch_filter = request.GET.get('batch')
    class_filter = request.GET.get('class_level')
    search = request.GET.get('search', '')
    
    if batch_filter:
        students = students.filter(batch_id=batch_filter)
    if class_filter:
        students = students.filter(class_level=class_filter)
    if search:
        students = students.filter(
            Q(name__icontains=search) | Q(parent__first_name__icontains=search)
        )
    
    from .models import CLASS_CHOICES
    context = {
        'students': students,
        'batches': Batch.objects.filter(is_active=True),
        'class_choices': CLASS_CHOICES,
        'current_batch': batch_filter,
        'current_class': class_filter,
        'search': search,
    }
    return render(request, 'core/student_list.html', context)


@admin_required
def student_create(request):
    """Create a new student."""
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Student '{student.name}' added successfully!")
            return redirect('student_list')
    else:
        form = StudentForm()
    
    return render(request, 'core/student_form.html', {'form': form, 'title': 'Add New Student'})


@admin_required
def student_edit(request, pk):
    """Edit an existing student."""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.name}' updated!")
            return redirect('student_list')
    else:
        form = StudentForm(instance=student)
    
    return render(request, 'core/student_form.html', {
        'form': form,
        'title': f'Edit Student: {student.name}',
        'student': student,
    })


@admin_required
def student_delete(request, pk):
    """Delete a student (soft delete by deactivating)."""
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        student.is_active = False
        student.save()
        messages.success(request, f"Student '{student.name}' deactivated.")
        return redirect('student_list')
    
    return render(request, 'core/student_confirm_delete.html', {'student': student})


@login_required
def student_detail(request, pk):
    """View student profile — with strict data scoping."""
    student = get_object_or_404(Student, pk=pk)
    user = request.user
    
    # Data scoping enforcement
    if user.is_parent and student.parent != user:
        return HttpResponseForbidden("You don't have permission to view this student.")
    if user.is_teacher:
        my_batches = Batch.objects.filter(teacher=user)
        if student.batch not in my_batches:
            return HttpResponseForbidden("This student is not in your batch.")
    
    # Gather student data
    today = date.today()
    month_start = today.replace(day=1)
    
    # Attendance
    recent_attendance = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:30]
    
    month_attendance = Attendance.objects.filter(
        student=student, date__gte=month_start
    )
    total_days = month_attendance.count()
    present_days = month_attendance.filter(status='present').count()
    attendance_pct = round((present_days / total_days * 100), 1) if total_days > 0 else None
    
    # Scores
    recent_scores = TestScore.objects.filter(student=student).order_by('-date')[:10]
    
    # Concept mastery
    mastery = ConceptMastery.objects.filter(student=student).select_related('concept', 'concept__subject')
    
    # Homework
    pending_homework = Homework.objects.filter(
        Q(student=student) | Q(batch=student.batch),
        status__in=['assigned', 'pending']
    ).order_by('due_date')[:5]
    
    context = {
        'student': student,
        'recent_attendance': recent_attendance,
        'attendance_pct': attendance_pct,
        'present_days': present_days,
        'total_days': total_days,
        'recent_scores': recent_scores,
        'mastery': mastery,
        'pending_homework': pending_homework,
    }
    return render(request, 'core/student_detail.html', context)


# ─── Batch CRUD ──────────────────────────────────────────────

@admin_required
def batch_list(request):
    """List all batches."""
    batches = Batch.objects.filter(is_active=True)
    return render(request, 'core/batch_list.html', {'batches': batches})


@admin_required
def batch_create(request):
    """Create a new batch."""
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save()
            messages.success(request, f"Batch '{batch.name}' created!")
            return redirect('batch_list')
    else:
        form = BatchForm()
    
    return render(request, 'core/batch_form.html', {'form': form, 'title': 'Create New Batch'})


@admin_required
def batch_edit(request, pk):
    """Edit a batch."""
    batch = get_object_or_404(Batch, pk=pk)
    
    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            messages.success(request, f"Batch '{batch.name}' updated!")
            return redirect('batch_list')
    else:
        form = BatchForm(instance=batch)
    
    return render(request, 'core/batch_form.html', {
        'form': form,
        'title': f'Edit Batch: {batch.name}',
        'batch': batch,
    })


# ─── User Management ─────────────────────────────────────────

@admin_required
def user_list(request):
    """List all users."""
    role_filter = request.GET.get('role', '')
    users = User.objects.exclude(is_superuser=True).filter(is_active=True)
    
    if role_filter:
        users = users.filter(role=role_filter)
    
    return render(request, 'core/user_list.html', {
        'users': users,
        'current_role': role_filter,
    })


@admin_required
def user_create(request):
    """Create a new user (teacher or parent)."""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.get_full_name()}' ({user.get_role_display()}) created!")
            return redirect('user_list')
    else:
        form = UserCreateForm()
    
    return render(request, 'core/user_form.html', {'form': form, 'title': 'Create New User'})


@admin_required
def user_delete(request, pk):
    """Delete a user (soft delete by deactivating)."""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.is_active = False
        user.save()
        messages.success(request, f"User '{user.get_full_name()}' deactivated.")
        return redirect('user_list')
    
    return render(request, 'core/user_confirm_delete.html', {'target_user': user})


# ─── Subject Management ──────────────────────────────────────

@admin_required
def subject_list(request):
    """List all subjects."""
    subjects = Subject.objects.filter(is_active=True)
    return render(request, 'core/subject_list.html', {'subjects': subjects})


@admin_required
def subject_create(request):
    """Create a new subject."""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject created!")
            return redirect('subject_list')
    else:
        form = SubjectForm()
    
    return render(request, 'core/subject_form.html', {'form': form, 'title': 'Add Subject'})
