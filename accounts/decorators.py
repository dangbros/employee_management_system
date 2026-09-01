from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render


def hr_required(view_func):
    """Allow access only to authenticated users with the HR role.

    Authorization is enforced server-side here; hiding UI elements alone is
    never relied upon.
    """

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_hr:
            return render(request, "403.html", status=403)
        return view_func(request, *args, **kwargs)

    return _wrapped
