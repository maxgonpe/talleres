from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from decimal import Decimal

# NUEVOS IMPORTS PARA PERMISOS
from .decorators import (
    requiere_permiso, requiere_rol, solo_administradores, 
    solo_mecanicos_y_admin, solo_vendedores_y_admin
)

from .models import (
    Repuesto, RepuestoEnStock, Cliente, SesionVenta, 
    CarritoItem, VentaPOS, VentaPOSItem, ConfiguracionPOS,
    Cotizacion, CotizacionItem, StockMovimiento
)
from .forms import (
    BuscarRepuestoForm, CarritoItemForm, VentaPOSForm, 
    ConfiguracionPOSForm, ClienteRapidoForm, CotizacionForm
)

# ========================
# VISTAS PRINCIPALES POS
# ========================

@login_required
@requiere_permiso('pos')
def pos_principal(request):
    """Vista principal del sistema POS"""
    # Obtener o crear sesión activa
    sesion_activa = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    ).first()
    
    if not sesion_activa:
        sesion_activa = SesionVenta.objects.create(
            usuario=request.user,
            activa=True
        )
    
    # Obtener items del carrito
    carrito_items = sesion_activa.carrito_items.all().order_by('-agregado_en')
    
    # Calcular totales
    subtotal = sum(item.subtotal for item in carrito_items)
    
    # Obtener configuración del taller
    from .models import AdministracionTaller
    config_taller = AdministracionTaller.get_configuracion_activa()
    
    # Obtener configuración POS
    config = ConfiguracionPOS.objects.first()
    if not config:
        config = ConfiguracionPOS.objects.create()
    
    context = {
        'sesion': sesion_activa,
        'carrito_items': carrito_items,
        'subtotal': subtotal,
        'config': config_taller,
        'config_pos': config,
        'buscar_form': BuscarRepuestoForm(),
    }
    
    return render(request, 'car/pos/pos_principal.html', context)

@login_required
def buscar_repuestos_pos(request):
    """Búsqueda de repuestos para POS (AJAX) - Unificada con módulo de repuestos"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'repuestos': []})
    
    # Usar la misma lógica de búsqueda que funciona en el módulo de repuestos
    repuestos = Repuesto.objects.filter(
        Q(nombre__icontains=query) |
        Q(sku__icontains=query) |
        Q(codigo_barra__icontains=query) |
        Q(oem__icontains=query) |
        Q(referencia__icontains=query) |
        Q(marca__icontains=query) |
        Q(descripcion__icontains=query) |
        Q(marca_veh__icontains=query) |
        Q(tipo_de_motor__icontains=query) |
        Q(cod_prov__icontains=query) |
        Q(origen_repuesto__icontains=query) |
        Q(carroceria__icontains=query)
    )
    
    # Si no hay resultados y el término contiene guiones, buscar por partes del SKU
    if not repuestos.exists() and '-' in query:
        partes = query.split('-')
        if len(partes) > 1:
            # Buscar SKUs que contengan todas las partes
            sku_filter = Q()
            for parte in partes:
                if parte.strip():  # Ignorar partes vacías
                    sku_filter &= Q(sku__icontains=parte.strip())
            
            if sku_filter:
                repuestos = Repuesto.objects.filter(sku_filter)
    
    # Ordenar por nombre y limitar resultados
    repuestos = repuestos.order_by('nombre')[:20]
    
    resultados = []
    for repuesto in repuestos:
        # Usar el stock unificado desde la tabla maestra
        stock_total = repuesto.stock_total
        
        # Precio de venta
        precio_venta = repuesto.precio_venta or 0
        
        # Solo incluir repuestos con stock disponible
        if stock_total > 0:
            resultados.append({
                'id': repuesto.id,
                'nombre': repuesto.nombre,
                'sku': repuesto.sku or '',
                'marca': repuesto.marca or '',
                'precio_venta': float(precio_venta),
                'stock': stock_total,
                'codigo_barra': repuesto.codigo_barra or '',
                'unidad': repuesto.unidad,
                'oem': repuesto.oem or '',
                'referencia': repuesto.referencia or '',
                'marca_veh': repuesto.marca_veh or '',
                'tipo_motor': repuesto.tipo_de_motor or '',
                'carroceria': repuesto.carroceria or '',
            })
    
    return JsonResponse({'repuestos': resultados})

@login_required
def agregar_al_carrito(request):
    """Agregar repuesto al carrito (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    repuesto_id = request.POST.get('repuesto_id')
    cantidad = int(request.POST.get('cantidad', 1))
    precio_unitario = round(Decimal(request.POST.get('precio_unitario', 0)))
    
    try:
        repuesto = Repuesto.objects.get(id=repuesto_id)
        
        # Obtener sesión activa
        sesion = SesionVenta.objects.filter(
            usuario=request.user, 
            activa=True
        ).first()
        
        if not sesion:
            return JsonResponse({'error': 'No hay sesión activa'}, status=400)
        
        # Verificar si ya existe en el carrito
        carrito_item = CarritoItem.objects.filter(
            sesion=sesion,
            repuesto=repuesto
        ).first()
        
        if carrito_item:
            # Actualizar cantidad
            carrito_item.cantidad += cantidad
            carrito_item.save()
        else:
            # Crear nuevo item
            CarritoItem.objects.create(
                sesion=sesion,
                repuesto=repuesto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )
        
        return JsonResponse({'success': True})
        
    except Repuesto.DoesNotExist:
        return JsonResponse({'error': 'Repuesto no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def actualizar_carrito_item(request, item_id):
    """Actualizar cantidad o precio de un item del carrito (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        item = CarritoItem.objects.get(
            id=item_id,
            sesion__usuario=request.user,
            sesion__activa=True
        )
        
        cantidad = request.POST.get('cantidad')
        precio_unitario = request.POST.get('precio_unitario')
        
        if cantidad:
            item.cantidad = int(cantidad)
        if precio_unitario:
            item.precio_unitario = round(Decimal(precio_unitario))
        
        item.save()
        
        return JsonResponse({
            'success': True,
            'subtotal': float(item.subtotal)
        })
        
    except CarritoItem.DoesNotExist:
        return JsonResponse({'error': 'Item no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def eliminar_carrito_item(request, item_id):
    """Eliminar item del carrito (AJAX)"""
    try:
        item = CarritoItem.objects.get(
            id=item_id,
            sesion__usuario=request.user,
            sesion__activa=True
        )
        item.delete()
        
        return JsonResponse({'success': True})
        
    except CarritoItem.DoesNotExist:
        return JsonResponse({'error': 'Item no encontrado'}, status=404)

@login_required
def limpiar_carrito(request):
    """Limpiar todo el carrito"""
    sesion = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    ).first()
    
    from .models import AdministracionTaller
    config = AdministracionTaller.get_configuracion_activa()
    
    if sesion:
        sesion.carrito_items.all().delete()
        if config.ver_mensajes:
            messages.success(request, 'Carrito limpiado')
    
    return redirect('pos_principal')

@login_required
def procesar_venta(request):
    """Procesar la venta del carrito"""
    sesion = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    ).first()
    
    if not sesion or not sesion.carrito_items.exists():
        messages.error(request, 'No hay items en el carrito')
        return redirect('pos_principal')
    
    if request.method == 'POST':
        form = VentaPOSForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                # Crear la venta
                venta = form.save(commit=False)
                venta.sesion = sesion
                venta.usuario = request.user
                
                # Calcular totales
                subtotal = sum(item.subtotal for item in sesion.carrito_items.all())
                descuento = venta.descuento or 0
                venta.subtotal = subtotal
                venta.total = subtotal - descuento
                venta.save()
                
                # Crear items de la venta y actualizar stock
                for carrito_item in sesion.carrito_items.all():
                    VentaPOSItem.objects.create(
                        venta=venta,
                        repuesto=carrito_item.repuesto,
                        cantidad=carrito_item.cantidad,
                        precio_unitario=carrito_item.precio_unitario,
                        subtotal=carrito_item.subtotal
                    )
                    
                    # Actualizar stock usando el sistema unificado
                    repuesto = carrito_item.repuesto
                    
                    # Verificar stock suficiente
                    if repuesto.stock_total < carrito_item.cantidad:
                        raise ValueError(f"Stock insuficiente para {repuesto.nombre}. Disponible: {repuesto.stock_total}, Solicitado: {carrito_item.cantidad}")
                    
                    # Actualizar stock en la tabla maestra
                    repuesto.stock -= carrito_item.cantidad
                    repuesto.save()
                    
                    # Sincronizar con RepuestoEnStock
                    stock_disponible = RepuestoEnStock.objects.filter(
                        repuesto=repuesto,
                        deposito='bodega-principal'
                    ).first()
                    
                    if stock_disponible:
                        # Actualizar stock detallado para que coincida con el stock maestro
                        stock_disponible.stock = repuesto.stock
                        stock_disponible.save()
                    else:
                        # Crear registro si no existe
                        RepuestoEnStock.objects.create(
                            repuesto=repuesto,
                            deposito='bodega-principal',
                            stock=repuesto.stock,
                            reservado=0,
                            precio_compra=repuesto.precio_costo,
                            precio_venta=repuesto.precio_venta,
                            proveedor=''
                        )
                    
                    # Registrar movimiento de stock
                    StockMovimiento.objects.create(
                        repuesto_stock=stock_disponible,
                        tipo="salida",
                        cantidad=carrito_item.cantidad,
                        motivo=f"Venta POS #{venta.id}",
                        referencia=str(venta.id),
                        usuario=request.user
                    )
                
                # Limpiar carrito
                sesion.carrito_items.all().delete()
                
                # Actualizar estadísticas de la sesión
                sesion.total_ventas += venta.total
                sesion.numero_ventas += 1
                sesion.save()
                
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f'Venta procesada exitosamente. Total: ${venta.total}')
                
                # Redirigir a detalle de venta o imprimir ticket
                return redirect('pos_venta_detalle', venta_id=venta.id)
    else:
        form = VentaPOSForm()
    
    # Calcular totales para mostrar
    carrito_items = sesion.carrito_items.all()
    subtotal = sum(item.subtotal for item in carrito_items)
    
    context = {
        'form': form,
        'carrito_items': carrito_items,
        'subtotal': subtotal,
        'sesion': sesion,
    }
    
    return render(request, 'car/pos/procesar_venta.html', context)

@login_required
def pos_venta_detalle(request, venta_id):
    """Detalle de una venta POS"""
    venta = get_object_or_404(
        VentaPOS, 
        id=venta_id,
        usuario=request.user
    )
    
    # Obtener configuración del taller para el logo (igual que en cotización)
    from .models import AdministracionTaller
    
    config = AdministracionTaller.get_configuracion_activa()
    
    # Generar URL absoluta para el logo (igual que en cotizacion_detalle)
    logo_url = None
    if config.logo_principal_png:
        logo_url = request.build_absolute_uri(config.logo_principal_png.url)
    elif config.logo_principal_svg:
        logo_url = request.build_absolute_uri(config.logo_principal_svg.url)
    else:
        logo_url = request.build_absolute_uri('/static/images/Logo1.svg')
    
    context = {
        'venta': venta,
        'items': venta.items.all(),
        'config': config,
        'logo_url': logo_url,
    }
    
    return render(request, 'car/pos/venta_detalle.html', context)

@login_required
def pos_historial_ventas(request):
    """Historial de ventas del POS"""
    ventas = VentaPOS.objects.filter(
        usuario=request.user
    ).order_by('-fecha')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        ventas = ventas.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta)
    
    paginator = Paginator(ventas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
    }
    
    return render(request, 'car/pos/historial_ventas.html', context)

@login_required
def pos_configuracion(request):
    """Configuración del sistema POS"""
    config = ConfiguracionPOS.objects.first()
    
    if not config:
        config = ConfiguracionPOS.objects.create()
    
    if request.method == 'POST':
        form = ConfiguracionPOSForm(request.POST, instance=config)
        from .models import AdministracionTaller
        config = AdministracionTaller.get_configuracion_activa()
        if form.is_valid():
            form.save()
            if config.ver_mensajes:
                messages.success(request, 'Configuración actualizada')
            return redirect('pos_configuracion')
    else:
        form = ConfiguracionPOSForm(instance=config)
    
    context = {
        'form': form,
        'config': config,
    }
    
    return render(request, 'car/pos/configuracion.html', context)

@login_required
def crear_cliente_rapido(request):
    """Crear cliente rápidamente desde POS (AJAX)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    form = ClienteRapidoForm(request.POST)
    
    if form.is_valid():
        cliente = form.save(commit=False)
        cliente.activo = True  # Asegurar que el cliente esté activo
        cliente.save()
        return JsonResponse({
            'success': True,
            'cliente': {
                'id': cliente.rut,
                'nombre': cliente.nombre,
                'telefono': cliente.telefono or ''
            }
        })
    else:
        return JsonResponse({
            'error': 'Datos inválidos',
            'errors': form.errors
        }, status=400)

@login_required
def cerrar_sesion_pos(request):
    """Cerrar sesión de venta actual"""
    sesion = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    ).first()
    
    if sesion:
        sesion.activa = False
        sesion.fecha_fin = timezone.now()
        sesion.save()
        
        from .models import AdministracionTaller
        config = AdministracionTaller.get_configuracion_activa()
        if config.ver_mensajes:
            messages.success(request, 'Sesión de venta cerrada')
    
    return redirect('pos_principal')

@login_required
def limpiar_sesiones_pos(request):
    """Limpiar todas las sesiones inactivas y crear una nueva sesión limpia"""
    # Cerrar todas las sesiones activas del usuario
    sesiones_activas = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    )
    
    for sesion in sesiones_activas:
        sesion.activa = False
        sesion.fecha_fin = timezone.now()
        sesion.save()
    
    # Limpiar carritos de sesiones inactivas (más de 1 día)
    from datetime import timedelta
    fecha_limite = timezone.now() - timedelta(days=1)
    
    sesiones_antiguas = SesionVenta.objects.filter(
        usuario=request.user,
        activa=False,
        fecha_fin__lt=fecha_limite
    )
    
    for sesion in sesiones_antiguas:
        sesion.carrito_items.all().delete()
    
    from .models import AdministracionTaller
    config = AdministracionTaller.get_configuracion_activa()
    
    if config.ver_mensajes:
        messages.success(request, 'Sesiones limpiadas. Nueva sesión iniciada.')
    return redirect('pos_principal')

@login_required
def pos_dashboard(request):
    """Dashboard con estadísticas del POS"""
    # Estadísticas del día
    hoy = timezone.now().date()
    ventas_hoy = VentaPOS.objects.filter(
        usuario=request.user,
        fecha__date=hoy
    )
    
    total_hoy = ventas_hoy.aggregate(total=Sum('total'))['total'] or 0
    cantidad_ventas_hoy = ventas_hoy.count()
    
    # Calcular promedio de venta
    promedio_venta = 0
    if cantidad_ventas_hoy > 0:
        promedio_venta = total_hoy / cantidad_ventas_hoy
    
    # Top repuestos vendidos
    top_repuestos = VentaPOSItem.objects.filter(
        venta__usuario=request.user,
        venta__fecha__date=hoy
    ).values('repuesto__nombre').annotate(
        cantidad_vendida=Sum('cantidad')
    ).order_by('-cantidad_vendida')[:5]
    
    context = {
        'total_hoy': total_hoy,
        'cantidad_ventas_hoy': cantidad_ventas_hoy,
        'promedio_venta': promedio_venta,
        'top_repuestos': top_repuestos,
    }
    
    return render(request, 'car/pos/dashboard.html', context)

# ========================
# VISTAS PARA COTIZACIONES
# ========================

@login_required
def procesar_cotizacion(request):
    """Procesar una cotización desde el carrito"""
    sesion = SesionVenta.objects.filter(
        usuario=request.user, 
        activa=True
    ).first()
    
    if not sesion or not sesion.carrito_items.exists():
        messages.error(request, 'No hay items en el carrito')
        return redirect('pos_principal')
    
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                # Crear la cotización
                cotizacion = form.save(commit=False)
                cotizacion.sesion = sesion
                cotizacion.usuario = request.user
                
                # Calcular totales
                subtotal = sum(item.subtotal for item in sesion.carrito_items.all())
                descuento = cotizacion.descuento or 0
                cotizacion.subtotal = subtotal
                cotizacion.total = subtotal - descuento
                cotizacion.save()
                
                # Crear items de la cotización
                for carrito_item in sesion.carrito_items.all():
                    CotizacionItem.objects.create(
                        cotizacion=cotizacion,
                        repuesto=carrito_item.repuesto,
                        cantidad=carrito_item.cantidad,
                        precio_unitario=carrito_item.precio_unitario,
                        subtotal=carrito_item.subtotal
                    )
                
                # Limpiar carrito
                sesion.carrito_items.all().delete()
                from .models import AdministracionTaller
                config = AdministracionTaller.get_configuracion_activa()
                if config.ver_mensajes:
                    messages.success(request, f'Cotización generada exitosamente. Total: ${cotizacion.total}')
                
                # Redirigir a detalle de cotización
                return redirect('pos_cotizacion_detalle', cotizacion_id=cotizacion.id)
    else:
        # Establecer fecha de vencimiento por defecto (7 días)
        from datetime import date, timedelta
        fecha_default = date.today() + timedelta(days=7)
        form = CotizacionForm(initial={'valida_hasta': fecha_default})
    
    # Calcular totales para mostrar
    carrito_items = sesion.carrito_items.all()
    subtotal = sum(item.subtotal for item in carrito_items)
    
    context = {
        'form': form,
        'carrito_items': carrito_items,
        'subtotal': subtotal,
        'sesion': sesion,
    }
    
    return render(request, 'car/pos/procesar_cotizacion.html', context)

@login_required
def pos_cotizacion_detalle(request, cotizacion_id):
    """Detalle de una cotización"""
    cotizacion = get_object_or_404(
        Cotizacion, 
        id=cotizacion_id,
        usuario=request.user
    )
    
    # Obtener configuración del taller para el logo
    from .models import AdministracionTaller
    
    config = AdministracionTaller.get_configuracion_activa()
    
    # Generar URL absoluta para el logo (igual que en trabajo_pdf)
    logo_url = None
    if config.logo_principal_png:
        logo_url = request.build_absolute_uri(config.logo_principal_png.url)
    elif config.logo_principal_svg:
        logo_url = request.build_absolute_uri(config.logo_principal_svg.url)
    else:
        logo_url = request.build_absolute_uri('/static/images/Logo1.svg')
    
    # Debug para verificar el nombre del taller
    print(f"🔧 DEBUG COTIZACIÓN - Nombre del taller: '{config.nombre_taller}'")
    print(f"🔧 DEBUG COTIZACIÓN - Logo URL: {logo_url}")
    
    context = {
        'cotizacion': cotizacion,
        'items': cotizacion.items.all(),
        'config': config,
        'logo_url': logo_url,
    }
    
    return render(request, 'car/pos/cotizacion_detalle.html', context)

@login_required
def pos_historial_cotizaciones(request):
    """Historial de cotizaciones"""
    cotizaciones = Cotizacion.objects.filter(
        usuario=request.user
    ).order_by('-fecha')
    
    # Filtros
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado')
    
    if fecha_desde:
        cotizaciones = cotizaciones.filter(fecha__date__gte=fecha_desde)
    if fecha_hasta:
        cotizaciones = cotizaciones.filter(fecha__date__lte=fecha_hasta)
    if estado:
        cotizaciones = cotizaciones.filter(estado=estado)
    
    paginator = Paginator(cotizaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'estado': estado,
    }
    
    return render(request, 'car/pos/historial_cotizaciones.html', context)

@login_required
def convertir_cotizacion_a_venta(request, cotizacion_id):
    """Convertir una cotización en venta"""
    cotizacion = get_object_or_404(
        Cotizacion, 
        id=cotizacion_id,
        usuario=request.user,
        estado='activa'
    )
    
    if request.method == 'POST':
        with transaction.atomic():
            # Crear la venta
            venta = VentaPOS.objects.create(
                sesion=cotizacion.sesion,
                cliente=cotizacion.cliente,
                usuario=request.user,
                subtotal=cotizacion.subtotal,
                descuento=cotizacion.descuento,
                total=cotizacion.total,
                observaciones=f"Convertida desde cotización #{cotizacion.id}",
                metodo_pago='efectivo'  # Por defecto, se puede cambiar
            )
            
            # Crear items de la venta y actualizar stock
            for item in cotizacion.items.all():
                VentaPOSItem.objects.create(
                    venta=venta,
                    repuesto=item.repuesto,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    subtotal=item.subtotal
                )
                
                # Actualizar stock usando el sistema unificado
                repuesto = item.repuesto
                
                # Verificar stock suficiente
                if repuesto.stock_total < item.cantidad:
                    raise ValueError(f"Stock insuficiente para {repuesto.nombre}. Disponible: {repuesto.stock_total}, Solicitado: {item.cantidad}")
                
                # Actualizar stock en la tabla maestra
                repuesto.stock -= item.cantidad
                repuesto.save()
                
                # Sincronizar con RepuestoEnStock
                stock_disponible = RepuestoEnStock.objects.filter(
                    repuesto=repuesto,
                    deposito='bodega-principal'
                ).first()
                
                if stock_disponible:
                    # Actualizar stock detallado para que coincida con el stock maestro
                    stock_disponible.stock = repuesto.stock
                    stock_disponible.save()
                else:
                    # Crear registro si no existe
                    RepuestoEnStock.objects.create(
                        repuesto=repuesto,
                        deposito='bodega-principal',
                        stock=repuesto.stock,
                        reservado=0,
                        precio_compra=repuesto.precio_costo,
                        precio_venta=repuesto.precio_venta,
                        proveedor=''
                    )
                
                # Registrar movimiento de stock
                StockMovimiento.objects.create(
                    repuesto_stock=stock_disponible,
                    tipo="salida",
                    cantidad=item.cantidad,
                    motivo=f"Venta POS #{venta.id} (desde cotización #{cotizacion.id})",
                    referencia=str(venta.id),
                    usuario=request.user
                )
            
            # Actualizar estado de la cotización
            cotizacion.estado = 'convertida'
            cotizacion.save()
            
            # Actualizar estadísticas de la sesión
            sesion = cotizacion.sesion
            sesion.total_ventas += venta.total
            sesion.numero_ventas += 1
            sesion.save()
            
            from .models import AdministracionTaller
            config = AdministracionTaller.get_configuracion_activa()
            if config.ver_mensajes:
                messages.success(request, f'Cotización convertida a venta exitosamente. Venta #{venta.id}')
            return redirect('pos_venta_detalle', venta_id=venta.id)
    
    context = {
        'cotizacion': cotizacion,
        'items': cotizacion.items.all(),
    }
    
    return render(request, 'car/pos/convertir_cotizacion.html', context)
