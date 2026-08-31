from django.db import transaction


@transaction.atomic
def agregar_repuesto_trabajo(trabajo, repuesto=None, repuesto_externo=None,
                             cantidad=1, precio_unitario=0, componente=None):
    """Crea un repuesto de trabajo con cantidades y subtotal normalizados."""
    from ..models import TrabajoRepuesto
    cantidad = int(cantidad)
    precio_unitario = precio_unitario or 0
    if cantidad < 1 or precio_unitario < 0:
        raise ValueError("Cantidad o precio inválido")
    return TrabajoRepuesto.objects.create(
        trabajo=trabajo,
        componente=componente,
        repuesto=repuesto,
        repuesto_externo=repuesto_externo,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        subtotal=cantidad * precio_unitario,
    )


@transaction.atomic
def agregar_accion_trabajo(trabajo, componente, accion, precio_mano_obra=0, cantidad=1):
    """Crea una acción de trabajo con datos normalizados."""
    from ..models import TrabajoAccion
    cantidad = int(cantidad)
    if cantidad < 1 or precio_mano_obra < 0:
        raise ValueError("Cantidad o precio inválido")
    return TrabajoAccion.objects.create(
        trabajo=trabajo,
        componente=componente,
        accion=accion,
        precio_mano_obra=precio_mano_obra or 0,
        cantidad=cantidad,
    )


def descontar_repuesto_trabajo(repuesto_trabajo):
    """Descuenta el stock correspondiente a un repuesto instalado."""
    return ajustar_stock_repuesto_trabajo(repuesto_trabajo, delta=-1)


def devolver_repuesto_trabajo(repuesto_trabajo):
    """Devuelve el stock correspondiente a un repuesto instalado."""
    return ajustar_stock_repuesto_trabajo(repuesto_trabajo, delta=1)


def ajustar_stock_repuesto_trabajo(repuesto_trabajo, delta):
    """Ajusta stock por instalación o devolución de un repuesto de trabajo."""
    if not repuesto_trabajo.repuesto:
        return False
    from ..models import RepuestoEnStock
    from .stock import ajustar_stock

    cantidad = repuesto_trabajo.cantidad or 0
    if cantidad < 1:
        return False
    with transaction.atomic():
        stock = RepuestoEnStock.objects.filter(
            repuesto_id=repuesto_trabajo.repuesto_id,
            deposito='bodega-principal',
        ).first()
        if not stock:
            return False
        try:
            ajustar_stock(
                stock,
                cantidad,
                'salida' if delta < 0 else 'liberacion',
                f"{'Instalación' if delta < 0 else 'Devolución'} de repuesto en trabajo #{repuesto_trabajo.trabajo_id}",
                f"TRABAJO-{repuesto_trabajo.trabajo_id}-REPUESTO-{repuesto_trabajo.pk}",
            )
        except ValueError:
            return False
    return True
