from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

def is_admin_user(user):
    return bool(user.is_authenticated and (user.is_staff or user.is_superuser))


def admin_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not is_admin_user(request.user):
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped


def client_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if is_admin_user(request.user):
            return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapped
