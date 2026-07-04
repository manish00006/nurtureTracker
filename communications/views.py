"""
Views for communications: Notices, WhatsApp broadcasts.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from core.models import User, Student, Batch
from .models import Notice
from .forms import TeacherNoticeForm, ParentNoticeForm
from .services import WhatsAppService


@login_required
def notice_list(request):
    """List notices depending on user role."""
    user = request.user
    
    if user.is_admin_user:
        notices = Notice.objects.all()
    elif user.is_teacher:
        my_batches = Batch.objects.filter(teacher=user)
        notices = Notice.objects.filter(
            Q(sender=user) | 
            Q(target_scope='all_parents') | 
            Q(target_batch__in=my_batches) |
            (Q(sender_type='parent') & Q(student__batch__in=my_batches))
        ).distinct()
    else:
        # Parent
        children = Student.objects.filter(parent=user)
        notices = Notice.objects.filter(
            Q(sender=user) |
            Q(target_scope='all_parents') |
            Q(target_batch__in=children.values('batch')) |
            Q(student__in=children)
        ).distinct()
        
    # Optional filtering
    notice_type = request.GET.get('type', '')
    if notice_type:
        notices = notices.filter(notice_type=notice_type)
        
    return render(request, 'communications/notice_list.html', {
        'notices': notices,
        'types': Notice.NOTICE_TYPE_CHOICES,
        'current_type': notice_type
    })


@login_required
def notice_create(request):
    """Create a new notice."""
    user = request.user
    
    if user.is_teacher or user.is_admin_user:
        form_class = TeacherNoticeForm
        kwargs = {'teacher': user}
        template = 'communications/notice_form_teacher.html'
    else:
        form_class = ParentNoticeForm
        kwargs = {'parent': user}
        template = 'communications/notice_form_parent.html'
        
    if request.method == 'POST':
        form = form_class(request.POST, **kwargs)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.sender = user
            notice.sender_type = user.role
            notice.save()
            
            # Send WhatsApp if requested (teachers only)
            if (user.is_teacher or user.is_admin_user) and form.cleaned_data.get('send_whatsapp'):
                wa_service = WhatsAppService()
                
                # Determine targets
                target_parents = set()
                if notice.target_scope == 'all_parents':
                    target_parents = User.objects.filter(role='parent', is_active=True, whatsapp_number__isnull=False)
                elif notice.target_scope == 'specific_batch' and notice.target_batch:
                    target_parents = User.objects.filter(
                        student__batch=notice.target_batch, 
                        is_active=True, 
                        whatsapp_number__isnull=False
                    )
                
                # Send messages
                success_count = 0
                for parent in target_parents:
                    if parent.whatsapp_number:
                        msg = f"*Notice: {notice.title}*\n\n{notice.message}\n\n- Nurture Coaching"
                        if wa_service.send_text_message(parent.whatsapp_number, msg):
                            success_count += 1
                
                if success_count > 0:
                    messages.success(request, f"Notice posted and sent via WhatsApp to {success_count} parents.")
                else:
                    messages.success(request, "Notice posted, but no WhatsApp numbers were found/sent.")
            else:
                messages.success(request, "Notice posted successfully.")
                
            return redirect('notice_list')
    else:
        form = form_class(**kwargs)
        
    return render(request, template, {'form': form})


@login_required
def notice_detail(request, pk):
    """View details of a notice, and allow teachers to reply to parent queries."""
    notice = get_object_or_404(Notice, pk=pk)
    user = request.user
    
    # Simple access check
    if user.is_parent and notice.sender != user:
        children = Student.objects.filter(parent=user)
        has_access = (
            notice.target_scope == 'all_parents' or 
            (notice.target_scope == 'specific_batch' and notice.target_batch in [c.batch for c in children]) or
            notice.student in children
        )
        if not has_access:
            messages.error(request, "Access denied.")
            return redirect('notice_list')
            
    # Mark as seen if parent viewing teacher notice
    if user.is_parent and notice.sender_type in ['teacher', 'admin'] and notice.status == 'sent':
        notice.status = 'seen'
        notice.save()
        
    # Teacher reply to parent notice
    if request.method == 'POST' and (user.is_teacher or user.is_admin_user):
        reply_text = request.POST.get('reply', '').strip()
        if reply_text and notice.sender_type == 'parent':
            notice.teacher_reply = reply_text
            notice.reply_date = timezone.now()
            notice.status = 'acknowledged'
            notice.save()
            
            # Send WhatsApp to parent that their query was answered
            if notice.sender.whatsapp_number:
                wa = WhatsAppService()
                msg = f"*Reply to your query: {notice.title}*\n\n{reply_text}\n\n- {user.get_full_name()}"
                wa.send_text_message(notice.sender.whatsapp_number, msg)
                
            messages.success(request, "Reply sent.")
            return redirect('notice_detail', pk=pk)
            
    return render(request, 'communications/notice_detail.html', {'notice': notice})


from django.http import JsonResponse
from .ai_services import ClaudeService, OllamaService

@login_required
def ai_assistant(request):
    """
    AI Assistant UI and API endpoint.
    Handles both Parent Q&A (Claude) and Student Doubts (Ollama).
    """
    user = request.user
    
    # If it's an API request (AJAX)
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        mode = request.POST.get('mode', 'parent') # 'parent' or 'student'
        student_id = request.POST.get('student_id')
        
        if not message:
            return JsonResponse({'error': 'Message is empty'}, status=400)
            
        if mode in ['parent', 'general']:
            # Gather context data for Claude
            context_data = {}
            if user.is_parent:
                children = Student.objects.filter(parent=user)
                for child in children:
                    context_data[child.name] = {
                        'class': child.class_level,
                        'recent_scores': list(child.test_scores.order_by('-date')[:3].values('subject__name', 'test_name', 'marks_obtained', 'total_marks'))
                    }
            
            claude = ClaudeService()
            response_text = claude.get_parent_response(user, message, context_data)
            return JsonResponse({'response': response_text})
            
        elif mode == 'student':
            # Ollama doubt solving
            student = None
            if student_id:
                student = Student.objects.filter(pk=student_id, parent=user).first()
                
            ollama = OllamaService()
            response_text = ollama.get_student_response(user, student, message)
            return JsonResponse({'response': response_text})
            
        else:
            return JsonResponse({'error': 'Invalid mode specified.'}, status=400)
            
    # GET request - render UI
    children = []
    if user.is_parent:
        children = Student.objects.filter(parent=user)
        
    return render(request, 'communications/assistant.html', {
        'children': children,
    })
