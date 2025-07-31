from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def rol_requerido(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if request.user.rol in roles or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permiso para acceder a esta sección')
            return redirect('dashboard')
        return wrapper
    return decorator

# Decoradores específicos
admin_required = rol_requerido('ADMIN')
tecnico_required = rol_requerido('TECNICO', 'ADMIN')