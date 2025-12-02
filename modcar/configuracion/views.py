from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def administracion(request):
    """Administración del taller"""
    return render(request, 'configuracion/administracion.html', {
        'title': 'Configuración del Taller'
    })



