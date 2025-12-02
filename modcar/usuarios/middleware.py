"""
Middleware de permisos
"""
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages


class PermisosMiddleware:
    """
    Middleware para manejar permisos de usuarios según su rol
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Inicializar permisos siempre (incluso si el usuario no está autenticado)
        # Esto asegura que request.permisos siempre exista
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.permisos = self.obtener_permisos(request.user)
        else:
            request.permisos = {
                'diagnosticos': False,
                'trabajos': False,
                'pos': False,
                'compras': False,
                'inventario': False,
                'administracion': False,
                'crear_clientes': False,
                'crear_vehiculos': False,
                'aprobar_diagnosticos': False,
                'gestionar_usuarios': False,
                'rol': None,
                'es_mecanico': False,
                'es_vendedor': False,
                'es_admin': False,
            }
        
        return self.get_response(request)
    
    def obtener_permisos(self, user):
        """
        Obtiene los permisos del usuario desde el modelo Mecanico
        """
        try:
            mecanico = user.mecanico
            return {
                'diagnosticos': mecanico.puede_ver_diagnosticos,
                'trabajos': mecanico.puede_ver_trabajos,
                'pos': mecanico.puede_ver_pos,
                'compras': mecanico.puede_ver_compras,
                'inventario': mecanico.puede_ver_inventario,
                'administracion': mecanico.puede_ver_administracion,
                'crear_clientes': mecanico.crear_clientes,
                'crear_vehiculos': mecanico.crear_vehiculos,
                'aprobar_diagnosticos': mecanico.aprobar_diagnosticos,
                'gestionar_usuarios': mecanico.gestionar_usuarios,
                'rol': mecanico.rol,
                'es_mecanico': mecanico.rol == 'mecanico',
                'es_vendedor': mecanico.rol == 'vendedor',
                'es_admin': mecanico.rol == 'admin',
            }
        except Exception as e:
            # Si no tiene perfil de mecánico, intentar crear uno por defecto
            from usuarios.models import Mecanico
            try:
                mecanico = Mecanico.objects.create(
                    user=user,
                    rol='mecanico'  # Rol por defecto
                )
                return {
                    'diagnosticos': True,
                    'trabajos': True,
                    'pos': True,
                    'compras': True,
                    'inventario': True,
                    'administracion': True,
                    'crear_clientes': True,
                    'crear_vehiculos': True,
                    'aprobar_diagnosticos': True,
                    'gestionar_usuarios': True,
                    'rol': 'mecanico',
                    'es_mecanico': True,
                    'es_vendedor': False,
                    'es_admin': False,
                }
            except:
                # Si falla la creación, retornar permisos mínimos
                return {
                    'diagnosticos': False,
                    'trabajos': False,
                    'pos': False,
                    'compras': False,
                    'inventario': False,
                    'administracion': False,
                    'crear_clientes': False,
                    'crear_vehiculos': False,
                    'aprobar_diagnosticos': False,
                    'gestionar_usuarios': False,
                    'rol': None,
                    'es_mecanico': False,
                    'es_vendedor': False,
                    'es_admin': False,
                }
