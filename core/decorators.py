"""
Custom decorators for role-based access control.
Separated from views to avoid circular imports.
"""

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def admin_required(view_func):
    """Allow only admin users."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin_user:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)


def teacher_or_admin_required(view_func):
    """Allow teachers and admins."""
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_teacher or request.user.is_admin_user):
            messages.error(request, "Access denied. Teacher privileges required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return login_required(wrapper)
