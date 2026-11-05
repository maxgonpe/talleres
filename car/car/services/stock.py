from django.db import transaction


def descontar_stock(repuesto, cantidad, usuario=None, referencia=""):
    """Descuenta stock del repuesto maestro en una sola transacción."""
    from ..models import StockMovimiento
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero")
    with transaction.atomic():
        repuesto = type(repuesto).objects.select_for_update().get(pk=repuesto.pk)
        if repuesto.stock_disponible < cantidad:
            raise ValueError(f"Stock insuficiente para {repuesto.nombre}")
        repuesto.stock -= cantidad
        repuesto.save(update_fields=["stock"])
        StockMovimiento.objects.create(
            repuesto=repuesto, tipo="salida", cantidad=cantidad,
            motivo=referencia or "Salida de inventario", referencia=referencia,
            usuario=usuario,
        )
    return repuesto


def ajustar_stock(repuesto, cantidad, tipo, motivo, referencia="", usuario=None):
    """Aplica una entrada o salida auditada a una existencia."""
    from ..models import StockMovimiento
    if cantidad < 1 or tipo not in {"entrada", "salida", "liberacion", "reserva"}:
        raise ValueError("Movimiento de stock inválido")
    with transaction.atomic():
        repuesto = type(repuesto).objects.select_for_update().get(pk=repuesto.pk)
        if tipo == "salida" and repuesto.stock_disponible < cantidad:
            raise ValueError(f"Stock insuficiente para {repuesto.nombre}")
        factor = -1 if tipo == "salida" else 1
        repuesto.stock = (repuesto.stock or 0) + factor * cantidad
        repuesto.save(update_fields=["stock"])
        StockMovimiento.objects.create(
            repuesto=repuesto, tipo=tipo, cantidad=cantidad,
            motivo=motivo, referencia=referencia, usuario=usuario,
        )
    return repuesto


def reservar_stock(repuesto, cantidad, motivo, referencia="", usuario=None):
    """Reserva existencias disponibles sin modificar el stock físico."""
    from ..models import StockMovimiento
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero")
    with transaction.atomic():
        repuesto = type(repuesto).objects.select_for_update().get(pk=repuesto.pk)
        if repuesto.stock_disponible < cantidad:
            raise ValueError("Stock insuficiente")
        repuesto.stock_reservado += cantidad
        repuesto.save(update_fields=["stock_reservado"])
        StockMovimiento.objects.create(
            repuesto=repuesto, tipo="reserva", cantidad=cantidad,
            motivo=motivo, referencia=referencia, usuario=usuario,
        )
    return repuesto


def liberar_reserva(repuesto, cantidad, motivo, referencia="", usuario=None):
    """Libera una reserva sin alterar las existencias físicas."""
    from ..models import StockMovimiento
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero")
    with transaction.atomic():
        repuesto = type(repuesto).objects.select_for_update().get(pk=repuesto.pk)
        if repuesto.stock_reservado < cantidad:
            raise ValueError("La reserva excede la cantidad reservada")
        repuesto.stock_reservado -= cantidad
        repuesto.save(update_fields=["stock_reservado"])
        StockMovimiento.objects.create(
            repuesto=repuesto, tipo="liberacion", cantidad=cantidad,
            motivo=motivo, referencia=referencia, usuario=usuario,
        )
    return repuesto


def descontar_stock_venta_pos(venta_pos):
    """Descuenta el stock de una venta POS de forma idempotente y atómica."""
    from .inventory import mover_stock

    if not venta_pos.pagado:
        return

    with transaction.atomic():
        for item in venta_pos.items.all():
            movimiento_ref = f"VENTA-POS-{venta_pos.pk}-ITEM-{item.pk}"
            mover_stock(item.repuesto_id, item.cantidad, "salida",
                        f"Venta POS #{venta_pos.id}", movimiento_ref,
                        venta_pos.usuario)
