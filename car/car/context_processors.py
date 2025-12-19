"""
Context processors para hacer disponibles variables globales en todos los templates
"""
from .models import AdministracionTaller


def configuracion_taller(request):
    """
    Hace disponible la configuración del taller en todos los templates
    Incluye ver_avisos y ver_mensajes para controlar avisos y mensajes
    """
    config = AdministracionTaller.get_configuracion_activa()
    return {
        'config_taller': config,
        'ver_avisos': config.ver_avisos,
        'ver_mensajes': config.ver_mensajes,
    }











