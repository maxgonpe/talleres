from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def lista(request):
    """Lista de usuarios"""
    return render(request, 'usuarios/lista.html', {
        'title': 'Usuarios'
    })

@login_required
def perfil(request):
    """Perfil del usuario"""
    return render(request, 'usuarios/perfil.html', {
        'title': 'Mi Perfil'
    })

