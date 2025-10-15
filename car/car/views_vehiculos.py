from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import VehiculoVersion
from .forms import VehiculoVersionForm

@login_required
def vehiculo_list(request):
    """Lista todos los vehículos con búsqueda y paginación"""
    search_query = request.GET.get('search', '')
    
    # Obtener todos los vehículos
    vehiculos = VehiculoVersion.objects.all().order_by('marca', 'modelo', 'anio_desde')
    
    # Aplicar filtro de búsqueda si existe
    if search_query:
        vehiculos = vehiculos.filter(
            Q(marca__icontains=search_query) |
            Q(modelo__icontains=search_query) |
            Q(anio_desde__icontains=search_query) |
            Q(anio_hasta__icontains=search_query)
        )
    
    # Paginación
    paginator = Paginator(vehiculos, 20)  # 20 vehículos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'vehiculos': page_obj,
        'search_query': search_query,
        'total_vehiculos': vehiculos.count(),
    }
    
    return render(request, 'vehiculos/vehiculo_list.html', context)

@login_required
def vehiculo_create(request):
    """Crear un nuevo vehículo"""
    if request.method == 'POST':
        form = VehiculoVersionForm(request.POST)
        if form.is_valid():
            vehiculo = form.save()
            messages.success(request, f'✅ Vehículo "{vehiculo.marca} {vehiculo.modelo}" creado exitosamente.')
            return redirect('vehiculo_compatibilidad_list')
    else:
        form = VehiculoVersionForm()
    
    context = {
        'form': form,
        'title': 'Crear Nuevo Vehículo',
        'action': 'Crear',
    }
    
    return render(request, 'vehiculos/vehiculo_form.html', context)

@login_required
def vehiculo_update(request, pk):
    """Editar un vehículo existente"""
    vehiculo = get_object_or_404(VehiculoVersion, pk=pk)
    
    if request.method == 'POST':
        form = VehiculoVersionForm(request.POST, instance=vehiculo)
        if form.is_valid():
            vehiculo = form.save()
            messages.success(request, f'✅ Vehículo "{vehiculo.marca} {vehiculo.modelo}" actualizado exitosamente.')
            return redirect('vehiculo_compatibilidad_list')
    else:
        form = VehiculoVersionForm(instance=vehiculo)
    
    context = {
        'form': form,
        'vehiculo': vehiculo,
        'title': f'Editar Vehículo: {vehiculo.marca} {vehiculo.modelo}',
        'action': 'Actualizar',
    }
    
    return render(request, 'vehiculos/vehiculo_form.html', context)

@login_required
def vehiculo_delete(request, pk):
    """Eliminar un vehículo"""
    vehiculo = get_object_or_404(VehiculoVersion, pk=pk)
    
    if request.method == 'POST':
        marca_modelo = f"{vehiculo.marca} {vehiculo.modelo}"
        vehiculo.delete()
        messages.success(request, f'✅ Vehículo "{marca_modelo}" eliminado exitosamente.')
        return redirect('vehiculo_list')
    
    context = {
        'vehiculo': vehiculo,
    }
    
    return render(request, 'vehiculos/vehiculo_confirm_delete.html', context)

@login_required
def vehiculo_detail(request, pk):
    """Ver detalles de un vehículo"""
    vehiculo = get_object_or_404(VehiculoVersion, pk=pk)
    
    # Obtener repuestos compatibles con este vehículo
    from .models import RepuestoAplicacion
    repuestos_compatibles = RepuestoAplicacion.objects.filter(version=vehiculo).select_related('repuesto')
    
    context = {
        'vehiculo': vehiculo,
        'repuestos_compatibles': repuestos_compatibles,
    }
    
    return render(request, 'vehiculos/vehiculo_detail.html', context)
