from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from decimal import Decimal

from .models import (
    Mecanico, Trabajo, ConfiguracionBonoMecanico, 
    BonoGenerado, PagoMecanico, ExcepcionBonoTrabajo, CierrePeriodo
)
from .decorators import requiere_permiso


def generar_bonos_trabajo_entregado(trabajo):
    """
    Función para generar bonos automáticamente cuando se entrega un trabajo.
    Se llama desde la vista cuando el estado cambia a 'entregado'.
    
    Args:
        trabajo: Instancia de Trabajo que fue entregado
    
    Returns:
        Lista de bonos generados
    """
    bonos_generados = []
    
    # Verificar si el trabajo tiene excepción de bono
    try:
        excepcion = ExcepcionBonoTrabajo.objects.get(trabajo=trabajo)
        # Si hay excepción, no generar bonos
        return bonos_generados
    except ExcepcionBonoTrabajo.DoesNotExist:
        pass
    
    # Verificar si ya se generaron bonos para este trabajo
    bonos_existentes = BonoGenerado.objects.filter(trabajo=trabajo).exists()
    if bonos_existentes:
        # Ya se generaron bonos, no generar de nuevo
        return bonos_generados
    
    # Obtener mecánicos asignados al trabajo
    mecanicos = trabajo.mecanicos.filter(activo=True)
    
    if not mecanicos.exists():
        return bonos_generados
    
    # Calcular total de mano de obra del trabajo
    total_mano_obra = trabajo.total_mano_obra
    
    if total_mano_obra <= 0:
        return bonos_generados
    
    # Generar bonos para cada mecánico
    for mecanico in mecanicos:
        try:
            config = mecanico.configuracion_bono
        except ConfiguracionBonoMecanico.DoesNotExist:
            # No tiene configuración, saltar
            continue
        
        # Verificar si los bonos están activos para este mecánico
        if not config.activo:
            continue
        
        # Calcular el monto del bono
        monto_bono = config.calcular_bono(total_mano_obra)
        
        if monto_bono <= 0:
            continue
        
        # Obtener período actual (mes y año de la fecha de entrega)
        fecha_entrega = timezone.now()
        periodo_mes = fecha_entrega.month
        periodo_anio = fecha_entrega.year
        
        # Crear el bono generado con período automático
        bono = BonoGenerado.objects.create(
            mecanico=mecanico,
            trabajo=trabajo,
            monto=monto_bono,
            tipo_bono=config.tipo_bono,
            porcentaje_aplicado=config.porcentaje_mano_obra,
            total_mano_obra=total_mano_obra,
            periodo_mes=periodo_mes,
            periodo_anio=periodo_anio,
            notas=f"Bono generado automáticamente al entregar el trabajo #{trabajo.id}"
        )
        
        bonos_generados.append(bono)
    
    return bonos_generados


@login_required
@requiere_permiso('trabajos')
def configuracion_bonos(request):
    """
    Vista para configurar bonos por mecánico.
    Permite crear/editar configuraciones de bonos.
    """
    configuraciones = ConfiguracionBonoMecanico.objects.select_related('mecanico', 'mecanico__user').all()
    mecanicos_sin_config = Mecanico.objects.filter(
        activo=True,
        configuracion_bono__isnull=True
    )
    
    if request.method == 'POST':
        mecanico_id = request.POST.get('mecanico_id')
        tipo_bono = request.POST.get('tipo_bono')
        activo = request.POST.get('activo') == 'on'
        
        try:
            mecanico = Mecanico.objects.get(id=mecanico_id)
            
            porcentaje = None
            cantidad_fija = None
            
            if tipo_bono == 'porcentaje':
                porcentaje = Decimal(request.POST.get('porcentaje', 0))
            elif tipo_bono == 'fijo':
                cantidad_fija = Decimal(request.POST.get('cantidad_fija', 0))
            
            notas = request.POST.get('notas', '')
            
            config, created = ConfiguracionBonoMecanico.objects.update_or_create(
                mecanico=mecanico,
                defaults={
                    'tipo_bono': tipo_bono,
                    'porcentaje_mano_obra': porcentaje,
                    'cantidad_fija': cantidad_fija,
                    'activo': activo,
                    'notas': notas
                }
            )
            
            if created:
                from .models import AdministracionTaller
                config_taller = AdministracionTaller.get_configuracion_activa()
                if config_taller.ver_mensajes:
                    messages.success(request, f"Configuración de bono creada para {mecanico}")
            else:
                from .models import AdministracionTaller
                config_taller = AdministracionTaller.get_configuracion_activa()
                if config_taller.ver_mensajes:
                    messages.success(request, f"Configuración de bono actualizada para {mecanico}")
            
            return redirect('configuracion_bonos')
            
        except Mecanico.DoesNotExist:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.error(request, "Mecánico no encontrado")
        except Exception as e:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.error(request, f"Error al guardar configuración: {str(e)}")
    
    context = {
        'configuraciones': configuraciones,
        'mecanicos_sin_config': mecanicos_sin_config,
    }
    
    return render(request, 'car/bonos/configuracion_bonos.html', context)


@login_required
@requiere_permiso('trabajos')
def editar_configuracion_bono(request, pk):
    """
    Vista para editar una configuración de bono específica.
    """
    config = get_object_or_404(ConfiguracionBonoMecanico, pk=pk)
    
    if request.method == 'POST':
        config.tipo_bono = request.POST.get('tipo_bono')
        config.activo = request.POST.get('activo') == 'on'
        
        if config.tipo_bono == 'porcentaje':
            config.porcentaje_mano_obra = Decimal(request.POST.get('porcentaje', 0))
            config.cantidad_fija = None
        elif config.tipo_bono == 'fijo':
            config.cantidad_fija = Decimal(request.POST.get('cantidad_fija', 0))
            config.porcentaje_mano_obra = None
        
        config.notas = request.POST.get('notas', '')
        config.save()
        
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Configuración actualizada para {config.mecanico}")
        return redirect('configuracion_bonos')
    
    return render(request, 'car/bonos/editar_configuracion_bono.html', {'config': config})


@login_required
@requiere_permiso('trabajos')
def cuenta_mecanico(request, mecanico_id):
    """
    Vista para ver la cuenta de un mecánico (bonos pendientes, pagos, etc.)
    Ahora incluye filtrado por período y gestión de cierres.
    """
    mecanico = get_object_or_404(Mecanico, id=mecanico_id)
    
    # Obtener filtros de período (opcional)
    periodo_mes = request.GET.get('mes')
    periodo_anio = request.GET.get('anio')
    
    # Base de consultas
    bonos_query = BonoGenerado.objects.filter(mecanico=mecanico)
    pagos_query = PagoMecanico.objects.filter(mecanico=mecanico)
    
    # Aplicar filtros de período si se proporcionan
    if periodo_mes and periodo_anio:
        try:
            periodo_mes = int(periodo_mes)
            periodo_anio = int(periodo_anio)
            bonos_query = bonos_query.filter(periodo_mes=periodo_mes, periodo_anio=periodo_anio)
            pagos_query = pagos_query.filter(periodo_mes=periodo_mes, periodo_anio=periodo_anio)
        except (ValueError, TypeError):
            periodo_mes = None
            periodo_anio = None
    
    # Bonos pendientes
    bonos_pendientes = bonos_query.filter(
        pagado=False
    ).select_related('trabajo', 'trabajo__vehiculo').order_by('-fecha_generacion')
    
    # Bonos pagados
    bonos_pagados = bonos_query.filter(
        pagado=True
    ).select_related('trabajo', 'trabajo__vehiculo').order_by('-fecha_generacion')[:20]
    
    # Pagos realizados
    pagos = pagos_query.prefetch_related('bonos_aplicados').order_by('-fecha_pago')
    
    # Estadísticas (totales si no hay filtro, del período si hay filtro)
    if periodo_mes and periodo_anio:
        saldo_pendiente = bonos_pendientes.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        total_generado = bonos_query.aggregate(total=Sum('monto'))['total'] or Decimal('0')
        # Total pagado debe ser la suma de los BONOS marcados como pagados, no de los pagos registrados
        # Esto es más preciso porque un pago puede ser parcial o cubrir múltiples bonos
        total_pagado = bonos_query.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    else:
        saldo_pendiente = mecanico.saldo_bonos_pendiente
        total_generado = mecanico.saldo_bonos_total
        # Total pagado: suma de los bonos marcados como pagados (no de los pagos registrados)
        total_pagado = BonoGenerado.objects.filter(mecanico=mecanico, pagado=True).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    
    # Cierres de períodos
    cierres = CierrePeriodo.objects.filter(
        mecanico=mecanico
    ).order_by('-periodo_anio', '-periodo_mes')[:12]  # Últimos 12 períodos
    
    # Obtener períodos disponibles (meses/años con bonos)
    periodos_disponibles = BonoGenerado.objects.filter(
        mecanico=mecanico
    ).values('periodo_mes', 'periodo_anio').distinct().order_by('-periodo_anio', '-periodo_mes')
    
    # Verificar si existe cierre para el período actual
    cierre_actual = None
    if periodo_mes and periodo_anio:
        cierre_actual = CierrePeriodo.objects.filter(
            mecanico=mecanico,
            periodo_mes=periodo_mes,
            periodo_anio=periodo_anio
        ).first()
    
    # Configuración de bono
    try:
        config_bono = mecanico.configuracion_bono
    except ConfiguracionBonoMecanico.DoesNotExist:
        config_bono = None
    
    meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    context = {
        'mecanico': mecanico,
        'bonos_pendientes': bonos_pendientes,
        'bonos_pagados': bonos_pagados,
        'pagos': pagos,
        'saldo_pendiente': saldo_pendiente,
        'total_generado': total_generado,
        'total_pagado': total_pagado,
        'config_bono': config_bono,
        'cierres': cierres,
        'periodos_disponibles': periodos_disponibles,
        'periodo_mes': periodo_mes,
        'periodo_anio': periodo_anio,
        'cierre_actual': cierre_actual,
        'meses': meses,
    }
    
    return render(request, 'car/bonos/cuenta_mecanico.html', context)


@login_required
@requiere_permiso('trabajos')
def registrar_pago_mecanico(request, mecanico_id):
    """
    Vista para registrar un pago a un mecánico.
    """
    mecanico = get_object_or_404(Mecanico, id=mecanico_id)
    
    # Bonos pendientes disponibles
    bonos_pendientes = BonoGenerado.objects.filter(
        mecanico=mecanico,
        pagado=False
    ).order_by('fecha_generacion')
    
    saldo_pendiente = mecanico.saldo_bonos_pendiente
    
    if request.method == 'POST':
        monto = Decimal(request.POST.get('monto', 0))
        metodo_pago = request.POST.get('metodo_pago')
        bonos_seleccionados = request.POST.getlist('bonos_seleccionados')
        notas = request.POST.get('notas', '')
        
        if monto <= 0:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.error(request, "El monto debe ser mayor a cero")
            return redirect('registrar_pago_mecanico', mecanico_id=mecanico_id)
        
        if monto > saldo_pendiente:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.warning(request, f"El monto excede el saldo pendiente (${saldo_pendiente})")
        
        # Obtener período actual (mes y año de la fecha de pago)
        fecha_pago = timezone.now()
        periodo_mes = fecha_pago.month
        periodo_anio = fecha_pago.year
        
        # Crear el pago con período automático
        pago = PagoMecanico.objects.create(
            mecanico=mecanico,
            monto=monto,
            metodo_pago=metodo_pago,
            notas=notas,
            registrado_por=request.user,
            periodo_mes=periodo_mes,
            periodo_anio=periodo_anio
        )
        
        # Asociar bonos seleccionados
        if bonos_seleccionados:
            bonos = BonoGenerado.objects.filter(
                id__in=bonos_seleccionados,
                mecanico=mecanico,
                pagado=False
            )
            pago.bonos_aplicados.set(bonos)
            
            # Marcar bonos como pagados
            for bono in bonos:
                bono.pagado = True
                bono.fecha_pago = pago.fecha_pago
                bono.save()
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Pago de ${monto} registrado para {mecanico}")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    context = {
        'mecanico': mecanico,
        'bonos_pendientes': bonos_pendientes,
        'saldo_pendiente': saldo_pendiente,
    }
    
    return render(request, 'car/bonos/registrar_pago_mecanico.html', context)


@login_required
@requiere_permiso('trabajos')
def lista_mecanicos_bonos(request):
    """
    Vista para listar todos los mecánicos con sus saldos de bonos.
    """
    mecanicos = Mecanico.objects.filter(activo=True).select_related('user')
    
    # Agregar información de saldos
    mecanicos_con_saldos = []
    for mecanico in mecanicos:
        mecanicos_con_saldos.append({
            'mecanico': mecanico,
            'saldo_pendiente': mecanico.saldo_bonos_pendiente,
            'total_generado': mecanico.saldo_bonos_total,
            'total_pagado': mecanico.total_pagado,
            'tiene_config': mecanico.tiene_bonos_activos(),
        })
    
    # Ordenar por saldo pendiente descendente
    mecanicos_con_saldos.sort(key=lambda x: x['saldo_pendiente'], reverse=True)
    
    context = {
        'mecanicos_con_saldos': mecanicos_con_saldos,
    }
    
    return render(request, 'car/bonos/lista_mecanicos_bonos.html', context)


@login_required
@requiere_permiso('trabajos')
def excepcion_bono_trabajo(request, trabajo_id):
    """
    Vista para crear una excepción de bono para un trabajo específico.
    """
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    
    # Verificar si ya existe excepción
    try:
        excepcion = ExcepcionBonoTrabajo.objects.get(trabajo=trabajo)
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.info(request, "Este trabajo ya tiene una excepción de bono")
        return redirect('trabajo_detalle', pk=trabajo.id)
    except ExcepcionBonoTrabajo.DoesNotExist:
        pass
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        if not motivo:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.error(request, "Debe proporcionar un motivo para la excepción")
            return redirect('excepcion_bono_trabajo', trabajo_id=trabajo_id)
        
        ExcepcionBonoTrabajo.objects.create(
            trabajo=trabajo,
            motivo=motivo,
            creado_por=request.user
        )
        
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Excepción de bono creada para el Trabajo #{trabajo.id}")
        return redirect('trabajo_detalle', pk=trabajo.id)
    
    return render(request, 'car/bonos/excepcion_bono_trabajo.html', {'trabajo': trabajo})


@login_required
@requiere_permiso('trabajos')
def eliminar_excepcion_bono(request, trabajo_id):
    """
    Vista para eliminar una excepción de bono de un trabajo.
    """
    trabajo = get_object_or_404(Trabajo, id=trabajo_id)
    
    try:
        excepcion = ExcepcionBonoTrabajo.objects.get(trabajo=trabajo)
        excepcion.delete()
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Excepción de bono eliminada para el Trabajo #{trabajo.id}")
    except ExcepcionBonoTrabajo.DoesNotExist:
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.error(request, "No existe excepción para este trabajo")
    
    return redirect('trabajo_detalle', pk=trabajo.id)


@login_required
@requiere_permiso('trabajos')
def eliminar_configuracion_bono(request, pk):
    """
    Vista para eliminar una configuración de bono.
    No afecta los bonos ya generados, solo elimina la configuración.
    """
    config = get_object_or_404(ConfiguracionBonoMecanico, pk=pk)
    mecanico_nombre = str(config.mecanico)
    
    if request.method == 'POST':
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        
        # Verificar si hay bonos pendientes (opcional, solo informativo)
        bonos_pendientes = BonoGenerado.objects.filter(
            mecanico=config.mecanico,
            pagado=False
        ).count()
        
        # Eliminar la configuración
        config.delete()
        
        if config_taller.ver_mensajes:
            if bonos_pendientes > 0:
                if config_taller.ver_mensajes:
                    messages.success(
                        request, 
                        f"Configuración de bono eliminada para {mecanico_nombre}. "
                        f"Nota: Este mecánico tiene {bonos_pendientes} bono(s) pendiente(s) que no se verán afectados."
                    )
            else:
                if config_taller.ver_mensajes:
                    messages.success(request, f"Configuración de bono eliminada para {mecanico_nombre}")
        
        return redirect('configuracion_bonos')
    
    # Si es GET, mostrar confirmación
    bonos_pendientes = BonoGenerado.objects.filter(
        mecanico=config.mecanico,
        pagado=False
    ).count()
    bonos_total = BonoGenerado.objects.filter(
        mecanico=config.mecanico
    ).count()
    
    context = {
        'config': config,
        'bonos_pendientes': bonos_pendientes,
        'bonos_total': bonos_total,
    }
    
    return render(request, 'car/bonos/confirmar_eliminar_configuracion.html', context)


@login_required
@requiere_permiso('trabajos')
def lista_cierres_periodo(request, mecanico_id=None):
    """
    Vista para listar todos los cierres de períodos.
    Si se proporciona mecanico_id, filtra por ese mecánico.
    """
    cierres = CierrePeriodo.objects.select_related('mecanico', 'mecanico__user', 'cerrado_por').all()
    
    if mecanico_id:
        mecanico = get_object_or_404(Mecanico, id=mecanico_id)
        cierres = cierres.filter(mecanico=mecanico)
    else:
        mecanico = None
    
    # Ordenar por año y mes descendente
    cierres = cierres.order_by('-periodo_anio', '-periodo_mes')
    
    context = {
        'cierres': cierres,
        'mecanico': mecanico,
    }
    
    return render(request, 'car/bonos/lista_cierres_periodo.html', context)


@login_required
@requiere_permiso('trabajos')
def crear_cierre_periodo(request, mecanico_id, mes, anio):
    """
    Vista para crear un cierre de período para un mecánico específico.
    """
    mecanico = get_object_or_404(Mecanico, id=mecanico_id)
    
    # Validar mes y año
    try:
        mes = int(mes)
        anio = int(anio)
        if mes < 1 or mes > 12:
            raise ValueError("Mes inválido")
    except (ValueError, TypeError):
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.error(request, "Período inválido")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    # Verificar si ya existe un cierre para este período
    cierre_existente = CierrePeriodo.objects.filter(
        mecanico=mecanico,
        periodo_mes=mes,
        periodo_anio=anio
    ).first()
    
    if cierre_existente:
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.warning(request, f"Ya existe un cierre para {cierre_existente.periodo_texto}")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    if request.method == 'POST':
        notas = request.POST.get('notas', '')
        
        # Crear el cierre
        cierre = CierrePeriodo.objects.create(
            mecanico=mecanico,
            periodo_mes=mes,
            periodo_anio=anio,
            cerrado_por=request.user,
            notas=notas
        )
        
        # Calcular totales y cerrar período
        cierre.calcular_totales()
        cierre.cerrar_periodo(usuario=request.user)
        
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Cierre de período {cierre.periodo_texto} creado exitosamente")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    # Obtener estadísticas del período antes de cerrar
    bonos_periodo = BonoGenerado.objects.filter(
        mecanico=mecanico,
        periodo_mes=mes,
        periodo_anio=anio
    )
    
    total_bonos = bonos_periodo.aggregate(total=Sum('monto'))['total'] or Decimal('0')
    total_pagado = bonos_periodo.filter(pagado=True).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    saldo_pendiente = bonos_periodo.filter(pagado=False).aggregate(total=Sum('monto'))['total'] or Decimal('0')
    cantidad_bonos = bonos_periodo.count()
    
    meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    context = {
        'mecanico': mecanico,
        'mes': mes,
        'anio': anio,
        'periodo_texto': f"{meses[mes]} {anio}",
        'total_bonos': total_bonos,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'cantidad_bonos': cantidad_bonos,
    }
    
    return render(request, 'car/bonos/crear_cierre_periodo.html', context)


@login_required
@requiere_permiso('trabajos')
def eliminar_cierre_periodo(request, cierre_id):
    """
    Vista para eliminar un cierre de período.
    Esto desmarcará los bonos como cerrados.
    """
    cierre = get_object_or_404(CierrePeriodo, id=cierre_id)
    mecanico_id = cierre.mecanico.id
    
    if request.method == 'POST':
        # Desmarcar bonos como cerrados
        BonoGenerado.objects.filter(
            mecanico=cierre.mecanico,
            periodo_mes=cierre.periodo_mes,
            periodo_anio=cierre.periodo_anio
        ).update(cerrado=False)
        
        # Eliminar el cierre
        periodo_texto = cierre.periodo_texto
        cierre.delete()
        
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Cierre de período {periodo_texto} eliminado. Los bonos ya no están marcados como cerrados.")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    context = {
        'cierre': cierre,
    }
    
    return render(request, 'car/bonos/confirmar_eliminar_cierre.html', context)


@login_required
@requiere_permiso('trabajos')
def eliminar_bono(request, bono_id):
    """
    Vista para eliminar un bono individual.
    Solo se puede eliminar si no está pagado y no pertenece a un período cerrado.
    """
    bono = get_object_or_404(BonoGenerado, id=bono_id)
    mecanico_id = bono.mecanico.id
    
    if request.method == 'POST':
        # Verificar si está pagado
        if bono.pagado:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.error(request, "No se puede eliminar un bono que ya está pagado")
            return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
        
        # Verificar si pertenece a un período cerrado
        if bono.cerrado:
            from .models import AdministracionTaller
            config_taller = AdministracionTaller.get_configuracion_activa()
            if config_taller.ver_mensajes:
                messages.error(request, "No se puede eliminar un bono de un período cerrado. Primero elimine el cierre del período.")
            return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
        
        # Eliminar el bono
        trabajo_id = bono.trabajo.id
        bono.delete()
        
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Bono del Trabajo #{trabajo_id} eliminado exitosamente")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    context = {
        'bono': bono,
    }
    
    return render(request, 'car/bonos/confirmar_eliminar_bono.html', context)


@login_required
@requiere_permiso('trabajos')
def eliminar_pago(request, pago_id):
    """
    Vista para eliminar un pago individual.
    Esto desmarcará los bonos asociados como no pagados.
    """
    pago = get_object_or_404(PagoMecanico, id=pago_id)
    mecanico_id = pago.mecanico.id
    
    if request.method == 'POST':
        # Desmarcar bonos como no pagados
        bonos_aplicados = pago.bonos_aplicados.all()
        for bono in bonos_aplicados:
            bono.pagado = False
            bono.fecha_pago = None
            bono.save()
        
        # Eliminar el pago
        monto = pago.monto
        pago.delete()
        
        from .models import AdministracionTaller
        config_taller = AdministracionTaller.get_configuracion_activa()
        if config_taller.ver_mensajes:
            messages.success(request, f"Pago de ${monto} eliminado. Los bonos asociados ahora están marcados como pendientes.")
        return redirect('cuenta_mecanico', mecanico_id=mecanico_id)
    
    context = {
        'pago': pago,
    }
    
    return render(request, 'car/bonos/confirmar_eliminar_pago.html', context)

