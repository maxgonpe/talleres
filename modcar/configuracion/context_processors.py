"""
Context processors para configuración del taller
"""
from .models import AdministracionTaller


def configuracion_taller(request):
    """
    Agrega la configuración del taller al contexto de todos los templates
    """
    config = AdministracionTaller.get_configuracion_activa()
    return {
        'config': config
    }



