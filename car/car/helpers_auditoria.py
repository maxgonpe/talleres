"""
Funciones helper para registrar eventos en el sistema de auditoría.
Estas funciones deben ser llamadas cada vez que ocurre un evento importante
en el sistema para mantener un registro histórico completo.
"""

from django.utils import timezone
from .models import RegistroEvento, Trabajo, TrabajoAccion, TrabajoRepuesto, TrabajoAbono


def obtener_datos_vehiculo(trabajo):
    """Extrae datos del vehículo y cliente de un trabajo"""
    try:
        vehiculo = trabajo.vehiculo
        cliente = vehiculo.cliente if hasattr(vehiculo, 'cliente') else None
        
        return {
            'vehiculo_id': vehiculo.id,
            'vehiculo_placa': vehiculo.placa,
            'vehiculo_marca': vehiculo.marca if hasattr(vehiculo, 'marca') else None,
            'vehiculo_modelo': vehiculo.modelo if hasattr(vehiculo, 'modelo') else None,
            'cliente_nombre': cliente.nombre if cliente and hasattr(cliente, 'nombre') else None,
        }
    except Exception:
        return {
            'vehiculo_id': trabajo.vehiculo_id if hasattr(trabajo, 'vehiculo_id') else None,
            'vehiculo_placa': 'N/A',
            'vehiculo_marca': None,
            'vehiculo_modelo': None,
            'cliente_nombre': None,
        }


def obtener_totales_trabajo(trabajo):
    """Calcula los totales actuales de un trabajo"""
    try:
        return {
            'total_mano_obra': float(trabajo.total_mano_obra or 0),
            'total_repuestos': float(trabajo.total_repuestos or 0),
            'total_general': float(trabajo.total_general or 0),
        }
    except Exception:
        return {
            'total_mano_obra': 0,
            'total_repuestos': 0,
            'total_general': 0,
        }


def obtener_usuario_actual(request=None, user=None):
    """Obtiene información del usuario actual"""
    usuario = user or (request.user if request and hasattr(request, 'user') else None)
    if usuario and usuario.is_authenticated:
        return {
            'usuario_id': usuario.id,
            'usuario_nombre': usuario.username,
        }
    return {
        'usuario_id': None,
        'usuario_nombre': None,
    }


def registrar_evento(
    trabajo,
    tipo_evento,
    request=None,
    user=None,
    estado_anterior=None,
    estado_nuevo=None,
    accion=None,
    repuesto=None,
    mecanico=None,
    monto=None,
    descripcion=None,
    fecha_evento=None,
):
    """
    Función principal para registrar un evento en el sistema de auditoría.
    
    Args:
        trabajo: Instancia de Trabajo
        tipo_evento: Tipo de evento (ver TIPO_EVENTO_CHOICES en RegistroEvento)
        request: Request object (opcional, para obtener usuario)
        user: User object (opcional, alternativo a request)
        estado_anterior: Estado previo (para cambios de estado)
        estado_nuevo: Nuevo estado (para cambios de estado)
        accion: Instancia de TrabajoAccion (opcional)
        repuesto: Instancia de TrabajoRepuesto (opcional)
        mecanico: Instancia de Mecanico (opcional)
        monto: Decimal (opcional, para abonos, etc.)
        descripcion: Texto adicional (opcional)
        fecha_evento: DateTime (opcional, si no se proporciona usa timezone.now())
    """
    try:
        # Datos del vehículo
        datos_vehiculo = obtener_datos_vehiculo(trabajo)
        
        # Totales del trabajo
        totales = obtener_totales_trabajo(trabajo)
        
        # Usuario
        usuario_info = obtener_usuario_actual(request, user)
        
        # Fecha del evento
        if fecha_evento is None:
            fecha_evento = timezone.now()
        
        # Datos del evento
        evento_data = {
            'trabajo_id': trabajo.id,
            'diagnostico_id': trabajo.diagnostico_id if hasattr(trabajo, 'diagnostico_id') else None,
            'vehiculo_id': datos_vehiculo['vehiculo_id'],
            'tipo_evento': tipo_evento,
            'fecha_evento': fecha_evento,
            'vehiculo_placa': datos_vehiculo['vehiculo_placa'],
            'vehiculo_marca': datos_vehiculo['vehiculo_marca'],
            'vehiculo_modelo': datos_vehiculo['vehiculo_modelo'],
            'cliente_nombre': datos_vehiculo['cliente_nombre'],
            'estado_anterior': estado_anterior,
            'estado_nuevo': estado_nuevo,
            'usuario_id': usuario_info['usuario_id'],
            'usuario_nombre': usuario_info['usuario_nombre'],
            'monto': monto,
            'descripcion': descripcion,
            'fecha_ingreso': trabajo.fecha_inicio,
            'fecha_entrega': trabajo.fecha_fin if trabajo.estado == 'entregado' else None,
            'dias_en_taller': trabajo.dias_en_taller,
            'total_mano_obra': totales['total_mano_obra'],
            'total_repuestos': totales['total_repuestos'],
            'total_general': totales['total_general'],
        }
        
        # Datos específicos de acción
        if accion:
            evento_data.update({
                'accion_id': accion.id,
                'accion_nombre': accion.accion.nombre if hasattr(accion, 'accion') and accion.accion else None,
                'componente_nombre': accion.componente.nombre if hasattr(accion, 'componente') and accion.componente else None,
                'monto': accion.precio_mano_obra if hasattr(accion, 'precio_mano_obra') else monto,
            })
        
        # Datos específicos de repuesto
        if repuesto:
            evento_data.update({
                'repuesto_id': repuesto.id,
                'repuesto_nombre': repuesto.repuesto.nombre if hasattr(repuesto, 'repuesto') and repuesto.repuesto else (
                    repuesto.repuesto_externo.nombre if hasattr(repuesto, 'repuesto_externo') and repuesto.repuesto_externo else None
                ),
                'repuesto_cantidad': repuesto.cantidad if hasattr(repuesto, 'cantidad') else None,
                'monto': repuesto.subtotal if hasattr(repuesto, 'subtotal') else monto,
            })
        
        # Datos específicos de mecánico
        if mecanico:
            evento_data.update({
                'mecanico_id': mecanico.id if hasattr(mecanico, 'id') else mecanico,
                'mecanico_nombre': mecanico.user.username if hasattr(mecanico, 'user') and mecanico.user else (
                    str(mecanico) if hasattr(mecanico, '__str__') else None
                ),
            })
        
        # Crear el registro
        RegistroEvento.objects.create(**evento_data)
        
    except Exception as e:
        # No fallar silenciosamente en producción, pero no interrumpir el flujo principal
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al registrar evento de auditoría: {e}", exc_info=True)


# ========================
# FUNCIONES ESPECÍFICAS POR TIPO DE EVENTO
# ========================

def registrar_ingreso(trabajo, request=None, user=None):
    """Registra el ingreso de un vehículo al sistema"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='ingreso',
        request=request,
        user=user,
        estado_nuevo='iniciado',
        fecha_evento=trabajo.fecha_inicio,
    )


def registrar_cambio_estado(trabajo, estado_anterior, estado_nuevo, request=None, user=None):
    """Registra un cambio de estado de un trabajo"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='cambio_estado',
        request=request,
        user=user,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
    )


def registrar_accion_completada(trabajo, accion, request=None, user=None):
    """Registra cuando una acción se marca como completada"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='accion_completada',
        request=request,
        user=user,
        accion=accion,
    )


def registrar_accion_pendiente(trabajo, accion, request=None, user=None):
    """Registra cuando una acción se marca como pendiente"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='accion_pendiente',
        request=request,
        user=user,
        accion=accion,
    )


def registrar_repuesto_instalado(trabajo, repuesto, request=None, user=None):
    """Registra cuando un repuesto se marca como instalado"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='repuesto_instalado',
        request=request,
        user=user,
        repuesto=repuesto,
    )


def registrar_repuesto_pendiente(trabajo, repuesto, request=None, user=None):
    """Registra cuando un repuesto se marca como pendiente"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='repuesto_pendiente',
        request=request,
        user=user,
        repuesto=repuesto,
    )


def registrar_entrega(trabajo, request=None, user=None):
    """Registra la entrega de un vehículo"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='entrega',
        request=request,
        user=user,
        estado_nuevo='entregado',
        fecha_evento=trabajo.fecha_fin or timezone.now(),
    )


def registrar_abono(trabajo, abono, request=None, user=None):
    """Registra un abono/pago recibido"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='abono',
        request=request,
        user=user,
        monto=abono.monto if hasattr(abono, 'monto') else None,
        descripcion=f"Abono: {abono.metodo_pago if hasattr(abono, 'metodo_pago') else 'N/A'}" if hasattr(abono, 'metodo_pago') else None,
        fecha_evento=abono.fecha if hasattr(abono, 'fecha') else None,
    )


def registrar_mecanico_asignado(trabajo, mecanico, request=None, user=None):
    """Registra cuando se asigna un mecánico a un trabajo"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='mecanico_asignado',
        request=request,
        user=user,
        mecanico=mecanico,
    )


def registrar_mecanico_removido(trabajo, mecanico, request=None, user=None):
    """Registra cuando se remueve un mecánico de un trabajo"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='mecanico_removido',
        request=request,
        user=user,
        mecanico=mecanico,
    )


def registrar_foto_agregada(trabajo, request=None, user=None, descripcion=None):
    """Registra cuando se agrega una foto a un trabajo"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='foto_agregada',
        request=request,
        user=user,
        descripcion=descripcion or "Foto agregada al trabajo",
    )


def registrar_observacion(trabajo, request=None, user=None, descripcion=None):
    """Registra cuando se agrega una observación a un trabajo"""
    registrar_evento(
        trabajo=trabajo,
        tipo_evento='observacion_agregada',
        request=request,
        user=user,
        descripcion=descripcion or trabajo.observaciones if hasattr(trabajo, 'observaciones') else None,
    )


# ========================
# FUNCIONES PARA CONSULTAS Y FILTROS
# ========================

def filtrar_trabajos_entregados_por_dias(trabajos_queryset, dias_desde_entrega=3):
    """
    Filtra trabajos entregados que tienen más de X días desde la entrega.
    Útil para ocultar trabajos entregados en pizarras después de cierto tiempo.
    
    Args:
        trabajos_queryset: QuerySet de Trabajo
        dias_desde_entrega: Número de días después de los cuales ocultar (default: 3)
    
    Returns:
        QuerySet filtrado sin trabajos entregados antiguos
    """
    from django.utils import timezone
    from datetime import timedelta
    
    fecha_limite = timezone.now() - timedelta(days=dias_desde_entrega)
    
    # Filtrar trabajos entregados que tienen más de X días desde fecha_fin
    return trabajos_queryset.exclude(
        estado='entregado',
        fecha_fin__lt=fecha_limite
    )


def obtener_trabajos_para_pizarra(dias_desde_entrega=3):
    """
    Obtiene trabajos filtrados para mostrar en pizarra.
    Excluye trabajos entregados que tienen más de X días desde la entrega.
    
    Args:
        dias_desde_entrega: Número de días después de los cuales ocultar (default: 3)
    
    Returns:
        QuerySet de Trabajo filtrado
    """
    from .models import Trabajo
    
    trabajos = Trabajo.objects.select_related("vehiculo", "vehiculo__cliente")
    return filtrar_trabajos_entregados_por_dias(trabajos, dias_desde_entrega)

