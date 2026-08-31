from django.db import transaction


def descontar_stock(stock, cantidad, usuario=None, referencia=""):
    """Descuenta una existencia y su total maestro en una sola transacción."""
    from ..models import StockMovimiento
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero")
    with transaction.atomic():
        stock = type(stock).objects.select_for_update().select_related("repuesto").get(pk=stock.pk)
        repuesto = stock.repuesto
        if stock.disponible < cantidad or (repuesto.stock or 0) < cantidad:
            raise ValueError(f"Stock insuficiente para {repuesto.nombre}")
        stock.stock -= cantidad
        repuesto.stock -= cantidad
        stock.save(update_fields=["stock", "ultima_actualizacion"])
        repuesto.save(update_fields=["stock"])
        StockMovimiento.objects.create(
            repuesto_stock=stock, tipo="salida", cantidad=cantidad,
            motivo=referencia or "Salida de inventario", referencia=referencia,
            usuario=usuario,
        )
    return stock


def ajustar_stock(stock, cantidad, tipo, motivo, referencia="", usuario=None):
    """Aplica una entrada o salida auditada a una existencia."""
    from ..models import StockMovimiento
    if cantidad < 1 or tipo not in {"entrada", "salida", "liberacion", "reserva"}:
        raise ValueError("Movimiento de stock inválido")
    with transaction.atomic():
        stock = type(stock).objects.select_for_update().select_related("repuesto").get(pk=stock.pk)
        if tipo == "salida" and (stock.disponible < cantidad or (stock.repuesto.stock or 0) < cantidad):
            raise ValueError(f"Stock insuficiente para {stock.repuesto.nombre}")
        factor = -1 if tipo == "salida" else 1
        stock.stock += factor * cantidad
        stock.repuesto.stock = (stock.repuesto.stock or 0) + factor * cantidad
        stock.save(update_fields=["stock", "ultima_actualizacion"])
        stock.repuesto.save(update_fields=["stock"])
        StockMovimiento.objects.create(
            repuesto_stock=stock, tipo=tipo, cantidad=cantidad,
            motivo=motivo, referencia=referencia, usuario=usuario,
        )
    return stock


def reservar_stock(stock, cantidad, motivo, referencia="", usuario=None):
    """Reserva existencias disponibles sin modificar el stock físico."""
    from ..models import StockMovimiento
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero")
    with transaction.atomic():
        stock = type(stock).objects.select_for_update().get(pk=stock.pk)
        if stock.disponible < cantidad:
            raise ValueError("Stock insuficiente")
        stock.reservado += cantidad
        stock.save(update_fields=["reservado", "ultima_actualizacion"])
        StockMovimiento.objects.create(
            repuesto_stock=stock, tipo="reserva", cantidad=cantidad,
            motivo=motivo, referencia=referencia, usuario=usuario,
        )
    return stock


def liberar_reserva(stock, cantidad, motivo, referencia="", usuario=None):
    """Libera una reserva sin alterar las existencias físicas."""
    from ..models import StockMovimiento
    if cantidad < 1:
        raise ValueError("La cantidad debe ser mayor que cero")
    with transaction.atomic():
        stock = type(stock).objects.select_for_update().get(pk=stock.pk)
        if stock.reservado < cantidad:
            raise ValueError("La reserva excede la cantidad reservada")
        stock.reservado -= cantidad
        stock.save(update_fields=["reservado", "ultima_actualizacion"])
        StockMovimiento.objects.create(
            repuesto_stock=stock, tipo="liberacion", cantidad=cantidad,
            motivo=motivo, referencia=referencia, usuario=usuario,
        )
    return stock


def descontar_stock_venta_pos(venta_pos):
    """Descuenta el stock de una venta POS de forma idempotente y atómica."""
    from ..models import Repuesto, RepuestoEnStock, StockMovimiento

    if not venta_pos.pagado:
        return

    with transaction.atomic():
        for item in venta_pos.items.all():
            movimiento_ref = f"VENTA-POS-{venta_pos.pk}-ITEM-{item.pk}"
            if StockMovimiento.objects.filter(referencia=movimiento_ref).exists():
                continue

            stock = RepuestoEnStock.objects.select_for_update().filter(
                repuesto_id=item.repuesto_id,
                deposito="bodega-principal",
            ).first()
            repuesto = Repuesto.objects.select_for_update().get(pk=item.repuesto_id)

            if not stock or stock.stock < item.cantidad:
                raise ValueError(f"No hay stock disponible para {repuesto.nombre}")
            if (repuesto.stock or 0) < item.cantidad:
                raise ValueError(f"Stock insuficiente para {repuesto.nombre}")

            stock.stock -= item.cantidad
            stock.save(update_fields=["stock", "ultima_actualizacion"])
            repuesto.stock -= item.cantidad
            repuesto.save(update_fields=["stock"])
            StockMovimiento.objects.create(
                repuesto_stock=stock,
                tipo="salida",
                cantidad=item.cantidad,
                motivo=f"Venta POS #{venta_pos.id}",
                referencia=movimiento_ref,
                usuario=venta_pos.usuario,
            )
