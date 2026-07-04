"""
Context processor to make user role info available in all templates.
"""


def user_role(request):
    """Add user role information to template context."""
    if request.user.is_authenticated:
        return {
            'user_role': request.user.role,
            'is_admin_user': request.user.is_admin_user,
            'is_teacher': request.user.is_teacher,
            'is_parent': request.user.is_parent,
        }
    return {
        'user_role': None,
        'is_admin_user': False,
        'is_teacher': False,
        'is_parent': False,
    }
