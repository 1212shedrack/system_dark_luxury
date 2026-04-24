from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def cashier_or_admin_required(view_func):
    """Allow only cashier and admin roles to access POS views."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if request.user.role not in ('cashier', 'admin'):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper
