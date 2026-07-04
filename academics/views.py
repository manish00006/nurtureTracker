"""
Views for academics app: Bulk attendance, bulk scores, concept mastery, homework management.
"""

import json
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Avg, Count, Q, F
from django.views.decorators.http import require_POST

from core.models import User, Student, Batch, Subject, Concept
from core.decorators import teacher_or_admin_required
from .models import Attendance, TestScore, ConceptMastery, Homework


# ─── Bulk Attendance ─────────────────────────────────────────

@teacher_or_admin_required
def bulk_attendance(request):
    """Bulk attendance entry — mark entire batch in one screen."""
    user = request.user

    # Get accessible batches
    if user.is_admin_user:
        batches = Batch.objects.filter(is_active=True)
    else:
        batches = Batch.objects.filter(teacher=user, is_active=True)

    selected_batch_id = request.GET.get('batch') or request.POST.get('batch_id')
    selected_date = request.GET.get('date', str(date.today()))

    try:
        att_date = date.fromisoformat(selected_date)
    except (ValueError, TypeError):
        att_date = date.today()

    selected_batch = None
    students = []
    existing_attendance = {}

    if selected_batch_id:
        selected_batch = get_object_or_404(Batch, pk=selected_batch_id)
        # Security: teacher can only access own batches
        if user.is_teacher and selected_batch.teacher != user:
            return HttpResponseForbidden("Not your batch.")

        students = Student.objects.filter(batch=selected_batch, is_active=True).order_by('name')
        # Load existing attendance for this date
        for att in Attendance.objects.filter(student__in=students, date=att_date):
            existing_attendance[att.student_id] = att.status

    if request.method == 'POST' and selected_batch:
        saved_count = 0
        from communications.services import WhatsAppService
        wa_service = WhatsAppService()
        
        for student in students:
            status = request.POST.get(f'status_{student.pk}', 'present')
            att, created = Attendance.objects.update_or_create(
                student=student,
                date=att_date,
                defaults={
                    'status': status,
                    'marked_by': user,
                }
            )
            saved_count += 1
            
            # Send WhatsApp alert for absences/lates (or all, customizable)
            if status in ['absent', 'late'] and student.parent and student.parent.whatsapp_number:
                wa_service.send_attendance_alert(
                    student_name=student.name,
                    parent_phone=student.parent.whatsapp_number,
                    status=status,
                    date_str=att_date.strftime("%d %b %Y")
                )

        messages.success(request, f"✅ Attendance saved for {saved_count} students in {selected_batch.name}")
        return redirect(f'/attendance/bulk/?batch={selected_batch_id}&date={att_date}')

    context = {
        'batches': batches,
        'selected_batch': selected_batch,
        'selected_date': att_date,
        'students': students,
        'existing_attendance': existing_attendance,
    }
    return render(request, 'academics/bulk_attendance.html', context)


# ─── Bulk Score Entry ────────────────────────────────────────

@teacher_or_admin_required
def bulk_scores(request):
    """Bulk test score entry — enter marks for entire batch at once."""
    user = request.user

    if user.is_admin_user:
        batches = Batch.objects.filter(is_active=True)
    else:
        batches = Batch.objects.filter(teacher=user, is_active=True)

    selected_batch_id = request.GET.get('batch') or request.POST.get('batch_id')
    selected_batch = None
    students = []
    subjects = Subject.objects.filter(is_active=True)

    if selected_batch_id:
        selected_batch = get_object_or_404(Batch, pk=selected_batch_id)
        if user.is_teacher and selected_batch.teacher != user:
            return HttpResponseForbidden("Not your batch.")
        students = Student.objects.filter(batch=selected_batch, is_active=True).order_by('name')
        if students.exists():
            subjects = Subject.objects.filter(student__in=students, is_active=True).distinct()

    if request.method == 'POST' and selected_batch:
        test_name = request.POST.get('test_name', '').strip()
        test_date = request.POST.get('test_date', str(date.today()))
        subject_id = request.POST.get('subject')
        total_marks = request.POST.get('total_marks', '100')
        test_type = request.POST.get('test_type', 'weekly')

        if not test_name or not subject_id:
            messages.error(request, "Test name and subject are required.")
        else:
            subject = get_object_or_404(Subject, pk=subject_id)
            try:
                test_dt = date.fromisoformat(test_date)
            except ValueError:
                test_dt = date.today()

            saved_count = 0
            from communications.services import WhatsAppService
            wa_service = WhatsAppService()
            
            for student in students:
                marks = request.POST.get(f'marks_{student.pk}', '').strip()
                if marks:
                    try:
                        marks_val = Decimal(marks)
                        TestScore.objects.create(
                            student=student,
                            subject=subject,
                            test_name=test_name,
                            date=test_dt,
                            marks_obtained=marks_val,
                            total_marks=Decimal(total_marks),
                            test_type=test_type,
                            entered_by=user,
                        )
                        saved_count += 1
                        
                        # Send WhatsApp alert for scores
                        if student.parent and student.parent.whatsapp_number:
                            wa_service.send_score_alert(
                                student_name=student.name,
                                parent_phone=student.parent.whatsapp_number,
                                test_name=test_name,
                                subject=subject.name,
                                marks=marks_val,
                                total=Decimal(total_marks)
                            )
                    except Exception:
                        pass

            messages.success(request, f"✅ {saved_count} scores saved for '{test_name}'")
            return redirect(f'/scores/bulk/?batch={selected_batch_id}')

    context = {
        'batches': batches,
        'selected_batch': selected_batch,
        'students': students,
        'subjects': subjects,
        'test_types': TestScore.TEST_TYPE_CHOICES,
        'today': date.today(),
    }
    return render(request, 'academics/bulk_scores.html', context)


# ─── Concept Mastery Management ──────────────────────────────

@teacher_or_admin_required
def concept_mastery_manage(request):
    """Manage concept mastery statuses for students in a batch."""
    user = request.user

    if user.is_admin_user:
        batches = Batch.objects.filter(is_active=True)
    else:
        batches = Batch.objects.filter(teacher=user, is_active=True)

    selected_batch_id = request.GET.get('batch') or request.POST.get('batch_id')
    selected_subject_id = request.GET.get('subject') or request.POST.get('subject_id')
    selected_batch = None
    selected_subject = None
    students = []
    concepts = []
    mastery_map = {}

    if selected_batch_id:
        selected_batch = get_object_or_404(Batch, pk=selected_batch_id)
        if user.is_teacher and selected_batch.teacher != user:
            return HttpResponseForbidden("Not your batch.")
        students = Student.objects.filter(batch=selected_batch, is_active=True).order_by('name')

    if selected_subject_id:
        selected_subject = get_object_or_404(Subject, pk=selected_subject_id)
        concepts = Concept.objects.filter(subject=selected_subject).order_by('order', 'chapter_number')

        # Build mastery map: {(student_id, concept_id): status}
        if students:
            for cm in ConceptMastery.objects.filter(student__in=students, concept__in=concepts):
                mastery_map[(cm.student_id, cm.concept_id)] = cm.status

    if request.method == 'POST' and selected_batch and selected_subject:
        saved = 0
        for student in students:
            for concept in concepts:
                status = request.POST.get(f'mastery_{student.pk}_{concept.pk}', '')
                if status in ['not_started', 'needs_work', 'mastered']:
                    ConceptMastery.objects.update_or_create(
                        student=student,
                        concept=concept,
                        defaults={'status': status, 'updated_by': user}
                    )
                    saved += 1
        messages.success(request, f"✅ {saved} mastery records updated")
        return redirect(f'/mastery/?batch={selected_batch_id}&subject={selected_subject_id}')

    if students:
        subjects = Subject.objects.filter(student__in=students, is_active=True).distinct()
    else:
        subjects = Subject.objects.filter(is_active=True)

    context = {
        'batches': batches,
        'subjects': subjects,
        'selected_batch': selected_batch,
        'selected_subject': selected_subject,
        'students': students,
        'concepts': concepts,
        'mastery_map': mastery_map,
        'mastery_statuses': ConceptMastery.MASTERY_STATUS,
    }
    return render(request, 'academics/concept_mastery.html', context)


# ─── Homework Management ────────────────────────────────────

@teacher_or_admin_required
def homework_manage(request):
    """Assign and manage homework."""
    user = request.user

    if user.is_admin_user:
        batches = Batch.objects.filter(is_active=True)
        homework_list = Homework.objects.all()
    else:
        batches = Batch.objects.filter(teacher=user, is_active=True)
        homework_list = Homework.objects.filter(
            Q(batch__in=batches) | Q(student__batch__in=batches)
        )

    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        homework_list = homework_list.filter(status=status_filter)

    homework_list = homework_list.order_by('-due_date')[:30]

    context = {
        'batches': batches,
        'homework_list': homework_list,
        'subjects': Subject.objects.filter(is_active=True),
        'status_filter': status_filter,
    }
    return render(request, 'academics/homework_manage.html', context)


@teacher_or_admin_required
def homework_create(request):
    """Create new homework assignment."""
    user = request.user

    if user.is_admin_user:
        batches = Batch.objects.filter(is_active=True)
    else:
        batches = Batch.objects.filter(teacher=user, is_active=True)

    if request.method == 'POST':
        batch_id = request.POST.get('batch')
        subject_id = request.POST.get('subject')
        description = request.POST.get('description', '').strip()
        due_date = request.POST.get('due_date')

        if batch_id and subject_id and description and due_date:
            batch = get_object_or_404(Batch, pk=batch_id)
            subject = get_object_or_404(Subject, pk=subject_id)
            try:
                due = date.fromisoformat(due_date)
            except ValueError:
                due = date.today() + timedelta(days=1)

            Homework.objects.create(
                batch=batch,
                subject=subject,
                description=description,
                due_date=due,
                assigned_by=user,
            )
            messages.success(request, "📝 Homework assigned!")
            return redirect('homework_manage')
        else:
            messages.error(request, "Please fill all required fields.")

    subjects = Subject.objects.filter(is_active=True)
    if request.method == 'GET' and request.GET.get('batch'):
        batch_id = request.GET.get('batch')
        try:
            batch = Batch.objects.get(pk=batch_id)
            batch_students = Student.objects.filter(batch=batch, is_active=True)
            subjects = Subject.objects.filter(student__in=batch_students, is_active=True).distinct()
        except Batch.DoesNotExist:
            pass

    context = {
        'batches': batches,
        'subjects': subjects,
        'today': date.today(),
    }
    return render(request, 'academics/homework_create.html', context)


@require_POST
@teacher_or_admin_required
def homework_update_status(request, pk):
    """Update homework status via AJAX."""
    hw = get_object_or_404(Homework, pk=pk)
    new_status = request.POST.get('status')
    if new_status in ['assigned', 'submitted', 'pending', 'late']:
        hw.status = new_status
        hw.save()
        return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'success': False}, status=400)


# ─── Student Progress API (for charts) ──────────────────────

@login_required
def student_progress_api(request, pk):
    """Return JSON data for student progress charts — strictly scoped."""
    student = get_object_or_404(Student, pk=pk)
    user = request.user

    # Strict scoping
    if user.is_parent and student.parent != user:
        return JsonResponse({'error': 'Forbidden'}, status=403)
    if user.is_teacher:
        my_batches = Batch.objects.filter(teacher=user)
        if student.batch not in my_batches:
            return JsonResponse({'error': 'Forbidden'}, status=403)

    today = date.today()

    # Attendance calendar data (last 60 days)
    attendance_data = []
    for att in Attendance.objects.filter(
        student=student,
        date__gte=today - timedelta(days=60)
    ).order_by('date'):
        attendance_data.append({
            'date': att.date.isoformat(),
            'status': att.status,
        })

    # Score trends (last 20 scores per subject)
    score_trends = {}
    for score in TestScore.objects.filter(student=student).order_by('date')[:40]:
        subj = score.subject.name
        if subj not in score_trends:
            score_trends[subj] = []
        score_trends[subj].append({
            'date': score.date.isoformat(),
            'percentage': float(score.percentage),
            'test': score.test_name,
        })

    # Batch average comparison
    batch_avg = {}
    if student.batch:
        batch_students = Student.objects.filter(batch=student.batch, is_active=True)
        for score in TestScore.objects.filter(student__in=batch_students).values(
            'subject__name', 'test_name'
        ).annotate(avg_pct=Avg(F('marks_obtained') * 100 / F('total_marks'))):
            subj = score['subject__name']
            if subj not in batch_avg:
                batch_avg[subj] = []
            batch_avg[subj].append({
                'test': score['test_name'],
                'avg': round(float(score['avg_pct']), 1),
            })

    # Concept mastery summary
    mastery_summary = {}
    for cm in ConceptMastery.objects.filter(student=student).select_related('concept__subject'):
        subj = cm.concept.subject.name
        if subj not in mastery_summary:
            mastery_summary[subj] = {'mastered': 0, 'needs_work': 0, 'not_started': 0}
        mastery_summary[subj][cm.status] += 1

    return JsonResponse({
        'attendance': attendance_data,
        'score_trends': score_trends,
        'batch_avg': batch_avg,
        'mastery_summary': mastery_summary,
    })


# ─── At-Risk Flagging (plain Python logic, NOT AI) ──────────

def get_at_risk_students(teacher=None):
    """
    Flag students whose average score dropped >15% across two consecutive tests.
    Returns list of dicts with student info and alert details.
    """
    if teacher:
        batches = Batch.objects.filter(teacher=teacher, is_active=True)
        students = Student.objects.filter(batch__in=batches, is_active=True)
    else:
        students = Student.objects.filter(is_active=True)

    at_risk = []
    for student in students:
        # Get last few scores grouped by subject
        subjects = student.subjects.all()
        for subject in subjects:
            scores = list(
                TestScore.objects.filter(student=student, subject=subject)
                .order_by('-date')[:5]
                .values_list('marks_obtained', 'total_marks', 'test_name', 'date')
            )
            if len(scores) >= 2:
                latest_pct = float(scores[0][0] / scores[0][1] * 100)
                prev_pct = float(scores[1][0] / scores[1][1] * 100)
                drop = prev_pct - latest_pct

                if drop > 15:
                    at_risk.append({
                        'student': student,
                        'subject': subject.name,
                        'latest_test': scores[0][2],
                        'latest_pct': round(latest_pct, 1),
                        'prev_pct': round(prev_pct, 1),
                        'drop': round(drop, 1),
                        'date': scores[0][3],
                    })

    return at_risk
