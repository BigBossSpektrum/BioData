from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps

def role_required(roles=[]):
    def check(user):
        return user.is_authenticated and user.rol in roles
    return user_passes_test(check)


def admin_required(view_func):
    """
    Decorador que requiere que el usuario tenga rol de administrador
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if getattr(request.user, 'rol', None) != 'admin':
            raise PermissionDenied("Acceso denegado: Se requieren permisos de administrador")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view