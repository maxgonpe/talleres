from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from .models import Compra, CompraItem, Repuesto, RepuestoEnStock, StockMovimiento
from .forms import CompraForm, CompraItemForm


@login_required
def compra_list(request):
    """Lista todas las compras"""
    compras = Compra.objects.all().order_by('-fecha_compra', '-creado_en')
    
    # Filtros
    estado = request.GET.get('estado')
    proveedor = request.GET.get('proveedor')
    
    if estado:
        compras = compras.filter(estado=estado)
    if proveedor:
        compras = compras.filter(proveedor__icontains=proveedor)
    
    # Paginación
    paginator = Paginator(compras, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'estado': estado,
        'proveedor': proveedor,
        'estados_choices': Compra.ESTADOS,
    }
    return render(request, 'car/compras/compra_list.html', context)


@login_required
def compra_create(request):
    """Crear nueva compra"""
    if request.method == 'POST':
        form = CompraForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.creado_por = request.user
            compra.save()
            from .models import AdministracionTaller
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f'Compra #{compra.numero_compra} creada exitosamente.')
            return redirect('compra_detail', pk=compra.pk)
    else:
        form = CompraForm()
    
    return render(request, 'car/compras/compra_form.html', {
        'form': form,
        'title': 'Nueva Compra'
    })


@login_required
def compra_detail(request, pk):
    """Detalle de una compra"""
    compra = get_object_or_404(Compra, pk=pk)
    items = compra.items.all().order_by('repuesto__nombre')
    
    # DEBUG: Verificar items en la vista
    print(f"DEBUG VISTA - Compra ID: {compra.id}")
    print(f"DEBUG VISTA - Items count: {items.count()}")
    print(f"DEBUG VISTA - Items: {list(items)}")
    print(f"DEBUG VISTA - Items type: {type(items)}")
    print(f"DEBUG VISTA - Items empty: {items.exists()}")
    
    # DEBUG: Verificar la consulta directamente
    items_directos = CompraItem.objects.filter(compra=compra)
    print(f"DEBUG VISTA - Items directos count: {items_directos.count()}")
    print(f"DEBUG VISTA - Items directos: {list(items_directos)}")
    
    # DEBUG: Verificar si hay items en la base de datos
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM car_compraitem WHERE compra_id = %s", [compra.id])
        count_db = cursor.fetchone()[0]
        print(f"DEBUG VISTA - Items en DB: {count_db}")
    
    # Usar items directos en lugar de la relación
    items = items_directos.order_by('repuesto__nombre')
    
    # Formulario para agregar items
    if request.method == 'POST':
        print(f"DEBUG FORMULARIO - Método: {request.method}")
        print(f"DEBUG FORMULARIO - POST data: {request.POST}")
        form = CompraItemForm(request.POST)
        print(f"DEBUG FORMULARIO - Form válido: {form.is_valid()}")
        if not form.is_valid():
            print(f"DEBUG FORMULARIO - Errores: {form.errors}")
        if form.is_valid():
            repuesto = form.cleaned_data['repuesto']
            
            # Verificar si ya existe este repuesto en la compra
            item_existente = CompraItem.objects.filter(compra=compra, repuesto=repuesto).first()
            
            if item_existente:
                # Si ya existe, actualizar la cantidad y precio
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                item_existente.cantidad += form.cleaned_data['cantidad']
                item_existente.precio_unitario = form.cleaned_data['precio_unitario']
                item_existente.save()
                if config.ver_mensajes:
                    messages.success(request, f'Cantidad actualizada para {repuesto.nombre}.')
                return redirect(f'/car/compras/{compra.pk}/?item_agregado=true')
            else:
                # Si no existe, crear nuevo item
                item = form.save(commit=False)
                item.compra = compra
                item.save()
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f'Item "{repuesto.nombre}" agregado a la compra. Cantidad: {form.cleaned_data["cantidad"]}, Precio: ${form.cleaned_data["precio_unitario"]}')
                return redirect(f'/car/compras/{compra.pk}/?item_agregado=true')
    else:
        form = CompraItemForm()
    
    context = {
        'compra': compra,
        'items': items,
        'form': form,
    }
    return render(request, 'car/compras/compra_detail.html', context)


@login_required
def compra_edit(request, pk):
    """Editar compra"""
    compra = get_object_or_404(Compra, pk=pk)
    
    if request.method == 'POST':
        form = CompraForm(request.POST, instance=compra)
        if form.is_valid():
            form.save()
            from .models import AdministracionTaller
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f'Compra #{compra.numero_compra} actualizada exitosamente.')
            return redirect('compra_detail', pk=compra.pk)
    else:
        form = CompraForm(instance=compra)
    
    return render(request, 'car/compras/compra_form.html', {
        'form': form,
        'compra': compra,
        'title': f'Editar Compra #{compra.numero_compra}'
    })


@login_required
def compra_item_delete(request, pk):
    """Eliminar item de compra"""
    from .models import AdministracionTaller
    
    item = get_object_or_404(CompraItem, pk=pk)
    compra = item.compra
    config = AdministracionTaller.get_configuracion_activa()
    
    # Si ver_avisos = False, eliminar directamente sin mostrar confirmación
    if not config.ver_avisos:
        item.delete()
        if config.ver_mensajes:
            messages.success(request, 'Item eliminado de la compra.')
        return redirect('compra_detail', pk=compra.pk)
    
    if request.method == 'POST':
        item.delete()
        if config.ver_mensajes:
            messages.success(request, 'Item eliminado de la compra.')
        return redirect('compra_detail', pk=compra.pk)
    
    return render(request, 'car/compras/compra_item_confirm_delete.html', {
        'item': item,
        'compra': compra,
        'config': config
    })


@login_required
def compra_item_edit(request, pk):
    """Editar item de compra"""
    item = get_object_or_404(CompraItem, pk=pk)
    compra = item.compra
    
    if request.method == 'POST':
        form = CompraItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            from .models import AdministracionTaller
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, 'Item actualizado exitosamente.')
            return redirect('compra_detail', pk=compra.pk)
    else:
        form = CompraItemForm(instance=item)
    
    return render(request, 'car/compras/compra_item_form.html', {
        'form': form,
        'item': item,
        'compra': compra,
        'title': 'Editar Item'
    })


@login_required
def compra_recibir(request, pk):
    """Recibir items de una compra"""
    compra = get_object_or_404(Compra, pk=pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            # Recibir todos los items pendientes
            items_pendientes = compra.items.filter(recibido=False)
            items_recibidos = 0
            
            for item in items_pendientes:
                item.recibir_item(usuario=request.user)
                items_recibidos += 1
            
            # Actualizar estado de la compra
            if items_recibidos > 0:
                compra.estado = 'recibida'
                compra.fecha_recibida = timezone.now().date()
                compra.save()
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f'{items_recibidos} items recibidos y stock actualizado.')
            else:
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.info(request, 'No hay items pendientes de recibir.')
        
        return redirect('compra_detail', pk=compra.pk)
    
    return render(request, 'car/compras/compra_recibir.html', {
        'compra': compra
    })


@login_required
def compra_item_recibir(request, pk):
    """Recibir un item específico"""
    item = get_object_or_404(CompraItem, pk=pk)
    compra = item.compra
    
    if request.method == 'POST':
        if not item.recibido:
            with transaction.atomic():
                item.recibir_item(usuario=request.user)
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f'Item "{item.repuesto.nombre}" recibido y stock actualizado.')
        else:
            from .models import AdministracionTaller
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.warning(request, 'Este item ya fue recibido.')
        
        return redirect('compra_detail', pk=compra.pk)
    
    return render(request, 'car/compras/compra_item_recibir.html', {
        'item': item,
        'compra': compra
    })


@login_required
def compra_confirmar(request, pk):
    """Confirmar compra"""
    compra = get_object_or_404(Compra, pk=pk)
    
    if request.method == 'POST':
        from .models import AdministracionTaller
        config = AdministracionTaller.get_configuracion_activa()
        compra.estado = 'confirmada'
        compra.save()
        if config.ver_mensajes:
            messages.success(request, f'Compra #{compra.numero_compra} confirmada.')
        return redirect('compra_detail', pk=compra.pk)
    
    return render(request, 'car/compras/compra_confirmar.html', {
        'compra': compra
    })


@login_required
def compra_cancelar(request, pk):
    """Cancelar compra"""
    compra = get_object_or_404(Compra, pk=pk)
    
    if request.method == 'POST':
        compra.estado = 'cancelada'
        compra.save()
        from .models import AdministracionTaller
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.success(request, f'Compra #{compra.numero_compra} cancelada.')
        return redirect('compra_detail', pk=compra.pk)
    
    return render(request, 'car/compras/compra_cancelar.html', {
        'compra': compra
    })


@login_required
def buscar_repuestos_compra(request):
    """API para buscar repuestos al agregar a compra"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'repuestos': []})
    
    repuestos = Repuesto.objects.filter(
        Q(nombre__icontains=query) |
        Q(sku__icontains=query) |
        Q(codigo_barra__icontains=query) |
        Q(oem__icontains=query) |
        Q(referencia__icontains=query) |
        Q(marca__icontains=query) |
        Q(marca_veh__icontains=query) |
        Q(tipo_de_motor__icontains=query) |
        Q(carroceria__icontains=query)
    ).order_by('nombre')[:10]
    
    resultados = []
    for repuesto in repuestos:
        resultados.append({
            'id': repuesto.id,
            'nombre': repuesto.nombre,
            'sku': repuesto.sku or '',
            'marca': repuesto.marca or '',
            'oem': repuesto.oem or '',
            'precio_costo': float(repuesto.precio_costo or 0),
            'precio_venta': float(repuesto.precio_venta or 0),
            'stock': repuesto.stock_total,  # Usar stock unificado
            'stock_actual': repuesto.stock_total,  # Alias para compatibilidad
            'marca_veh': repuesto.marca_veh or '',
            'tipo_motor': repuesto.tipo_de_motor or '',
            'carroceria': repuesto.carroceria or '',
        })
    return JsonResponse({'repuestos': resultados})


@login_required
def compra_dashboard(request):
    """Dashboard de compras"""
    # Obtener configuración del taller
    from .models import AdministracionTaller
    config = AdministracionTaller.get_configuracion_activa()
    
    # Estadísticas básicas
    total_compras = Compra.objects.count()
    compras_pendientes = Compra.objects.filter(estado__in=['borrador', 'confirmada']).count()
    compras_recibidas = Compra.objects.filter(estado='recibida').count()
    
    # Compras recientes
    compras_recientes = Compra.objects.all().order_by('-creado_en')[:5]
    
    # Total gastado este mes
    from datetime import datetime, timedelta
    inicio_mes = datetime.now().replace(day=1)
    total_mes = Compra.objects.filter(
        fecha_compra__gte=inicio_mes,
        estado='recibida'
    ).aggregate(total=Sum('total'))['total'] or 0
    
    context = {
        'total_compras': total_compras,
        'compras_pendientes': compras_pendientes,
        'compras_recibidas': compras_recibidas,
        'compras_recientes': compras_recientes,
        'total_mes': total_mes,
        'config': config,
    }
    return render(request, 'car/compras/compra_dashboard.html', context)


@login_required
def compra_items_ajax(request, pk):
    """Vista AJAX para obtener solo la tabla de items de una compra"""
    compra = get_object_or_404(Compra, pk=pk)
    items = compra.items.all().order_by('repuesto__nombre')
    
    context = {
        'compra': compra,
        'items': items,
    }
    return render(request, 'car/compras/compra_items_table.html', context)
