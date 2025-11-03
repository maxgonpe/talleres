"""
Utilidades para registrar eventos en el sistema de auditoría.
Este módulo proporciona funciones helper para registrar automáticamente
todos los eventos importantes del sistema.
"""

from django.utils import timezone
from django.db import transaction
from .models import RegistroEvento, ResumenTrabajo, Trabajo, Diagnostico


def _obtener_datos_vehiculo(obj):
    """
    Extrae los datos del vehículo y cliente de un trabajo o diagnóstico.
    """
    vehiculo = obj.vehiculo
    cliente = vehiculo.cliente if hasattr(vehiculo, 'cliente') else None
    
    return {
        'vehiculo_id': vehiculo.id,
        'vehiculo_placa': vehiculo.placa,
        'vehiculo_marca': vehiculo.marca if hasattr(vehiculo, 'marca') else None,
        'vehiculo_modelo': vehiculo.modelo if hasattr(vehiculo, 'modelo') else None,
        'cliente_nombre': cliente.nombre if cliente else None,
    }


def _obtener_datos_trabajo(trabajo):
    """
    Extrae los totales y estadísticas actuales del trabajo.
    """
    return {
        'fecha_ingreso': trabajo.fecha_inicio,
        'fecha_entrega': trabajo.fecha_fin if trabajo.estado == 'entregado' else None,
        'dias_en_taller': trabajo.dias_en_taller,
        'total_mano_obra': trabajo.total_mano_obra or 0,
        'total_repuestos': trabajo.total_repuestos or 0,
        'total_general': trabajo.total_general or 0,
    }


def _obtener_datos_usuario(request):
    """
    Extrae los datos del usuario de la request.
    """
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        return {
            'usuario_id': request.user.id,
            'usuario_nombre': request.user.username,
        }
    return {
        'usuario_id': None,
        'usuario_nombre': None,
    }


@transaction.atomic
def registrar_evento(
    trabajo=None,
    diagnostico=None,
    tipo_evento=None,
    fecha_evento=None,
    estado_anterior=None,
    estado_nuevo=None,
    accion=None,
    componente=None,
    repuesto=None,
    repuesto_cantidad=None,
    monto=None,
    mecanico=None,
    descripcion=None,
    request=None,
):
    """
    Registra un evento en el sistema de auditoría.
    
    Args:
        trabajo: Instancia de Trabajo (opcional si es diagnóstico)
        diagnostico: Instancia de Diagnostico (opcional si es trabajo)
        tipo_evento: Tipo de evento (ver RegistroEvento.TIPO_EVENTO_CHOICES)
        fecha_evento: Fecha del evento (default: ahora)
        estado_anterior: Estado anterior (para cambios de estado)
        estado_nuevo: Estado nuevo (para cambios de estado)
        accion: Instancia de TrabajoAccion (opcional)
        componente: Instancia de Componente o nombre (opcional)
        repuesto: Instancia de TrabajoRepuesto (opcional)
        repuesto_cantidad: Cantidad de repuesto (opcional)
        monto: Monto relacionado (opcional)
        mecanico: Instancia de Mecanico (opcional)
        descripcion: Descripción adicional (opcional)
        request: Request object para obtener usuario (opcional)
    
    Returns:
        RegistroEvento: El registro creado
    """
    if fecha_evento is None:
        fecha_evento = timezone.now()
    
    # Determinar si es trabajo o diagnóstico
    if trabajo:
        obj = trabajo
        diagnostico_obj = trabajo.diagnostico if hasattr(trabajo, 'diagnostico') else None
        trabajo_id = trabajo.id
    elif diagnostico:
        obj = diagnostico
        diagnostico_obj = diagnostico
        trabajo_id = None
    else:
        raise ValueError("Debe proporcionar 'trabajo' o 'diagnostico'")
    
    # Obtener datos del vehículo
    datos_vehiculo = _obtener_datos_vehiculo(obj)
    
    # Obtener datos del trabajo (si existe)
    if trabajo:
        datos_trabajo = _obtener_datos_trabajo(trabajo)
    else:
        # Para diagnósticos, no tenemos datos de trabajo
        datos_trabajo = {
            'fecha_ingreso': None,
            'fecha_entrega': None,
            'dias_en_taller': None,
            'total_mano_obra': 0,
            'total_repuestos': 0,
            'total_general': 0,
        }
    
    # Obtener datos del usuario
    datos_usuario = _obtener_datos_usuario(request)
    
    # Estado actual (del trabajo o diagnóstico)
    estado_actual = None
    if trabajo:
        estado_actual = estado_nuevo or trabajo.estado
    elif diagnostico:
        estado_actual = estado_nuevo or diagnostico.estado
    
    # Preparar datos del evento
    evento_data = {
        'trabajo_id': trabajo_id,
        'diagnostico_id': diagnostico_obj.id if diagnostico_obj else None,
        'vehiculo_id': datos_vehiculo['vehiculo_id'],
        'tipo_evento': tipo_evento,
        'fecha_evento': fecha_evento,
        'vehiculo_placa': datos_vehiculo['vehiculo_placa'],
        'vehiculo_marca': datos_vehiculo['vehiculo_marca'],
        'vehiculo_modelo': datos_vehiculo['vehiculo_modelo'],
        'cliente_nombre': datos_vehiculo['cliente_nombre'],
        'estado_anterior': estado_anterior,
        'estado_nuevo': estado_actual,
        'fecha_ingreso': datos_trabajo['fecha_ingreso'],
        'fecha_entrega': datos_trabajo['fecha_entrega'],
        'dias_en_taller': datos_trabajo['dias_en_taller'],
        'total_mano_obra': datos_trabajo['total_mano_obra'],
        'total_repuestos': datos_trabajo['total_repuestos'],
        'total_general': datos_trabajo['total_general'],
        'usuario_id': datos_usuario['usuario_id'],
        'usuario_nombre': datos_usuario['usuario_nombre'],
        'descripcion': descripcion,
    }
    
    # Datos de acción
    if accion:
        evento_data['accion_id'] = accion.id if hasattr(accion, 'id') else None
        evento_data['accion_nombre'] = (
            accion.accion.nombre if hasattr(accion, 'accion') else 
            str(accion) if accion else None
        )
        if hasattr(accion, 'componente') and accion.componente:
            evento_data['componente_nombre'] = accion.componente.nombre
        if hasattr(accion, 'precio_mano_obra'):
            evento_data['monto'] = accion.precio_mano_obra
    
    # Datos de componente (si se pasa directamente)
    if componente:
        if hasattr(componente, 'nombre'):
            evento_data['componente_nombre'] = componente.nombre
        else:
            evento_data['componente_nombre'] = str(componente)
    
    # Datos de repuesto
    if repuesto:
        evento_data['repuesto_id'] = (
            repuesto.repuesto.id if hasattr(repuesto, 'repuesto') and repuesto.repuesto else
            repuesto.repuesto_externo.id if hasattr(repuesto, 'repuesto_externo') and repuesto.repuesto_externo else
            None
        )
        evento_data['repuesto_nombre'] = (
            repuesto.repuesto.nombre if hasattr(repuesto, 'repuesto') and repuesto.repuesto else
            repuesto.repuesto_externo.nombre if hasattr(repuesto, 'repuesto_externo') and repuesto.repuesto_externo else
            None
        )
        if hasattr(repuesto, 'cantidad'):
            evento_data['repuesto_cantidad'] = repuesto.cantidad
        if hasattr(repuesto, 'subtotal'):
            evento_data['monto'] = repuesto.subtotal
        if hasattr(repuesto, 'componente') and repuesto.componente:
            evento_data['componente_nombre'] = repuesto.componente.nombre
    
    if repuesto_cantidad:
        evento_data['repuesto_cantidad'] = repuesto_cantidad
    
    if monto:
        evento_data['monto'] = monto
    
    # Datos de mecánico
    if mecanico:
        evento_data['mecanico_id'] = mecanico.id if hasattr(mecanico, 'id') else None
        if hasattr(mecanico, 'user'):
            evento_data['mecanico_nombre'] = mecanico.user.get_full_name() or mecanico.user.username
        else:
            evento_data['mecanico_nombre'] = str(mecanico)
    
    # Crear el registro
    registro = RegistroEvento.objects.create(**evento_data)
    
    # Actualizar el resumen del trabajo (solo si existe trabajo)
    if trabajo:
        actualizar_resumen_trabajo(trabajo)
    
    return registro


def registrar_diagnostico_creado(diagnostico, request=None):
    """Registra la creación de un diagnóstico."""
    return registrar_evento(
        diagnostico=diagnostico,
        tipo_evento='diagnostico_creado',
        fecha_evento=diagnostico.fecha if hasattr(diagnostico, 'fecha') else timezone.now(),
        estado_nuevo=diagnostico.estado if hasattr(diagnostico, 'estado') else 'pendiente',
        request=request,
        descripcion=f'Diagnóstico creado para vehículo {diagnostico.vehiculo.placa}'
    )


def registrar_diagnostico_aprobado(diagnostico, trabajo, request=None):
    """
    Registra cuando un diagnóstico se aprueba y se convierte en trabajo.
    Calcula los días entre creación y aprobación.
    """
    # Calcular días entre creación y aprobación
    dias_entre_creacion_y_aprobacion = None
    if hasattr(diagnostico, 'fecha') and diagnostico.fecha:
        delta = timezone.now() - diagnostico.fecha
        dias_entre_creacion_y_aprobacion = delta.days
    
    descripcion = f'Diagnóstico aprobado y convertido en trabajo #{trabajo.id}'
    if dias_entre_creacion_y_aprobacion is not None:
        descripcion += f' (aprobado {dias_entre_creacion_y_aprobacion} día(s) después de su creación)'
    
    return registrar_evento(
        diagnostico=diagnostico,
        trabajo=trabajo,
        tipo_evento='diagnostico_aprobado',
        fecha_evento=timezone.now(),
        estado_anterior=diagnostico.estado if hasattr(diagnostico, 'estado') else 'pendiente',
        estado_nuevo='iniciado',
        request=request,
        descripcion=descripcion
    )


def registrar_ingreso(trabajo, request=None):
    """Registra el ingreso de un vehículo al sistema."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='ingreso',
        fecha_evento=trabajo.fecha_inicio,
        estado_nuevo='iniciado',
        request=request,
        descripcion=f'Vehículo ingresado al sistema'
    )


def registrar_cambio_estado(trabajo, estado_anterior, estado_nuevo, request=None):
    """Registra un cambio de estado de un trabajo."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='cambio_estado',
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        request=request,
        descripcion=f'Estado cambiado de {estado_anterior} a {estado_nuevo}'
    )


def registrar_accion_completada(trabajo, accion, request=None):
    """Registra cuando una acción se marca como completada."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='accion_completada',
        accion=accion,
        request=request,
        descripcion=f'Acción completada: {accion.accion.nombre if hasattr(accion, "accion") else str(accion)}'
    )


def registrar_accion_pendiente(trabajo, accion, request=None):
    """Registra cuando una acción se marca como pendiente."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='accion_pendiente',
        accion=accion,
        request=request,
        descripcion=f'Acción marcada como pendiente: {accion.accion.nombre if hasattr(accion, "accion") else str(accion)}'
    )


def registrar_repuesto_instalado(trabajo, repuesto, request=None):
    """Registra cuando un repuesto se marca como instalado."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='repuesto_instalado',
        repuesto=repuesto,
        request=request,
        descripcion=f'Repuesto instalado: {repuesto.repuesto.nombre if hasattr(repuesto, "repuesto") and repuesto.repuesto else repuesto.repuesto_externo.nombre if hasattr(repuesto, "repuesto_externo") and repuesto.repuesto_externo else "N/A"}'
    )


def registrar_repuesto_pendiente(trabajo, repuesto, request=None):
    """Registra cuando un repuesto se marca como pendiente."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='repuesto_pendiente',
        repuesto=repuesto,
        request=request,
        descripcion=f'Repuesto marcado como pendiente'
    )


def registrar_entrega(trabajo, request=None):
    """Registra la entrega de un vehículo."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='entrega',
        fecha_evento=trabajo.fecha_fin,
        estado_anterior=trabajo.estado,
        estado_nuevo='entregado',
        request=request,
        descripcion='Vehículo entregado al cliente'
    )


def registrar_abono(trabajo, abono, request=None):
    """Registra un abono/pago recibido."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='abono',
        monto=abono.monto,
        fecha_evento=abono.fecha,
        request=request,
        descripcion=f'Abono recibido: ${abono.monto} - {abono.get_metodo_pago_display() if hasattr(abono, "get_metodo_pago_display") else ""}'
    )


def registrar_mecanico_asignado(trabajo, mecanico, request=None):
    """Registra la asignación de un mecánico."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='mecanico_asignado',
        mecanico=mecanico,
        request=request,
        descripcion=f'Mecánico asignado: {mecanico.user.get_full_name() if hasattr(mecanico, "user") else str(mecanico)}'
    )


def registrar_mecanico_removido(trabajo, mecanico, request=None):
    """Registra la remoción de un mecánico."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='mecanico_removido',
        mecanico=mecanico,
        request=request,
        descripcion=f'Mecánico removido: {mecanico.user.get_full_name() if hasattr(mecanico, "user") else str(mecanico)}'
    )


def registrar_foto_agregada(trabajo, request=None, descripcion=None):
    """Registra cuando se agrega una foto."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='foto_agregada',
        request=request,
        descripcion=descripcion or 'Foto agregada al trabajo'
    )


def registrar_observacion(trabajo, observacion, request=None):
    """Registra cuando se agrega una observación."""
    return registrar_evento(
        trabajo=trabajo,
        tipo_evento='observacion_agregada',
        request=request,
        descripcion=f'Observación agregada: {observacion[:200]}'  # Limitar a 200 caracteres
    )


@transaction.atomic
def actualizar_resumen_trabajo(trabajo):
    """
    Actualiza o crea el resumen de un trabajo.
    """
    datos_vehiculo = _obtener_datos_vehiculo(trabajo)
    datos_trabajo = _obtener_datos_trabajo(trabajo)
    
    # Obtener mecánicos asignados
    mecanicos_ids = list(trabajo.mecanicos.values_list('id', flat=True))
    mecanicos_str = ','.join(map(str, mecanicos_ids)) if mecanicos_ids else None
    
    # Calcular días desde entrega
    dias_desde_entrega = None
    if trabajo.estado == 'entregado' and trabajo.fecha_fin:
        delta = timezone.now() - trabajo.fecha_fin
        dias_desde_entrega = delta.days
    
    resumen, created = ResumenTrabajo.objects.update_or_create(
        trabajo_id=trabajo.id,
        defaults={
            'vehiculo_placa': datos_vehiculo['vehiculo_placa'],
            'vehiculo_marca': datos_vehiculo['vehiculo_marca'],
            'vehiculo_modelo': datos_vehiculo['vehiculo_modelo'],
            'cliente_nombre': datos_vehiculo['cliente_nombre'],
            'fecha_ingreso': datos_trabajo['fecha_ingreso'],
            'fecha_ultimo_estado': timezone.now(),
            'fecha_entrega': datos_trabajo['fecha_entrega'],
            'estado_actual': trabajo.estado,
            'total_acciones': trabajo.acciones.count(),
            'acciones_completadas': trabajo.acciones.filter(completado=True).count(),
            'cantidad_repuestos': trabajo.repuestos.count(),
            'repuestos_instalados': trabajo.repuestos.filter(completado=True).count(),
            'total_mano_obra': datos_trabajo['total_mano_obra'],
            'total_repuestos': datos_trabajo['total_repuestos'],
            'total_general': datos_trabajo['total_general'],
            'total_abonos': trabajo.total_abonos,
            'porcentaje_avance': trabajo.porcentaje_avance,
            'porcentaje_cobrado': trabajo.porcentaje_cobrado,
            'dias_en_taller': datos_trabajo['dias_en_taller'],
            'dias_desde_entrega': dias_desde_entrega,
            'mecanicos_asignados': mecanicos_str,
        }
    )
    
    return resumen

