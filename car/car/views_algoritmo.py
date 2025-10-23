from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .algoritmo_relacion import algoritmo_relacion_inteligente

@login_required
def relacionar_repuestos_componentes(request):
    """Vista principal para el algoritmo de relación inteligente"""
    if request.method == 'POST':
        umbral = float(request.POST.get('umbral', 0.6))
        ejecutar = request.POST.get('ejecutar') == 'true'
        
        if ejecutar:
            return ejecutar_algoritmo_relacion(request, umbral)
        else:
            return analizar_relaciones(request, umbral)
    
    # Vista inicial
    return render(request, 'car/relacionar_repuestos.html', {
        'umbral_default': 0.6
    })

def analizar_relaciones(request, umbral=0.6):
    """Analiza las relaciones posibles sin ejecutarlas"""
    resultados = algoritmo_relacion_inteligente(umbral, solo_analizar=True)
    
    return render(request, 'car/relacionar_repuestos.html', {
        'resultados': resultados,
        'umbral': umbral,
        'solo_analisis': True
    })

def ejecutar_algoritmo_relacion(request, umbral=0.6):
    """Ejecuta el algoritmo y crea las relaciones"""
    resultados = algoritmo_relacion_inteligente(umbral, ejecutar=True)
    
    return render(request, 'car/relacionar_repuestos.html', {
        'resultados': resultados,
        'umbral': umbral,
        'ejecutado': True
    })















