from functools import wraps
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages

def requiere_permiso(permiso):
    """
    Decorador para verificar permisos específicos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if not request.permisos.get(permiso, False):
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'No tienes permisos para realizar esta acción'
                    }, status=403)
                else:
                    messages.error(request, f"No tienes permisos para acceder a esta sección: {permiso}")
                    return redirect('panel_principal')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def requiere_rol(*roles):
    """
    Decorador para verificar roles específicos
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            if request.permisos.get('rol') not in roles:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({
                        'error': 'No tienes el rol necesario para realizar esta acción'
                    }, status=403)
                else:
                    messages.error(request, f"No tienes el rol necesario para acceder a esta sección")
                    return redirect('panel_principal')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def solo_administradores(view_func):
    """
    Decorador para vistas que solo pueden ver los administradores
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not request.permisos.get('es_admin', False):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Solo los administradores pueden acceder a esta sección'
                }, status=403)
            else:
                messages.error(request, "Solo los administradores pueden acceder a esta sección")
                return redirect('panel_principal')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def solo_mecanicos_y_admin(view_func):
    """
    Decorador para vistas que pueden ver mecánicos y administradores
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.permisos.get('es_mecanico', False) or request.permisos.get('es_admin', False)):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Solo los mecánicos y administradores pueden acceder a esta sección'
                }, status=403)
            else:
                messages.error(request, "Solo los mecánicos y administradores pueden acceder a esta sección")
                return redirect('panel_principal')
        
        return view_func(request, *args, **kwargs)
    return wrapper

def solo_vendedores_y_admin(view_func):
    """
    Decorador para vistas que pueden ver vendedores y administradores
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if not (request.permisos.get('es_vendedor', False) or request.permisos.get('es_admin', False)):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'error': 'Solo los vendedores y administradores pueden acceder a esta sección'
                }, status=403)
            else:
                messages.error(request, "Solo los vendedores y administradores pueden acceder a esta sección")
                return redirect('panel_principal')
        
        return view_func(request, *args, **kwargs)
    return wrapper













