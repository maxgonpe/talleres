"""Operaciones atomicas de inventario basadas exclusivamente en Repuesto."""

from django.db import transaction


def _audit(repuesto, tipo, cantidad, motivo, referencia, usuario=None):
    from ..models import StockMovimiento
    if referencia and StockMovimiento.objects.filter(referencia=referencia).exists():
        return False
    StockMovimiento.objects.create(
        repuesto=repuesto, tipo=tipo, cantidad=cantidad,
        motivo=motivo, referencia=referencia, usuario=usuario,
    )
    return True


@transaction.atomic
def mover_stock(repuesto_id, cantidad, tipo, motivo, referencia, usuario=None):
    """Aplica un movimiento una sola vez y bloquea la fila de Repuesto."""
    from ..models import Repuesto
    if cantidad < 1 or tipo not in {"entrada", "salida", "liberacion"}:
        raise ValueError("Movimiento de inventario invalido")
    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto_id)
    if referencia and _movement_exists(referencia):
        return repuesto
    if tipo == "salida" and repuesto.stock_disponible < cantidad:
        raise ValueError(f"Stock insuficiente para {repuesto.nombre}")
    repuesto.stock += cantidad if tipo in {"entrada", "liberacion"} else -cantidad
    repuesto.save(update_fields=["stock"])
    _audit(repuesto, tipo, cantidad, motivo, referencia, usuario)
    return repuesto


def _movement_exists(referencia):
    from ..models import StockMovimiento
    return StockMovimiento.objects.filter(referencia=referencia).exists()


@transaction.atomic
def reservar(repuesto_id, cantidad, referencia, motivo="Reserva", usuario=None):
    from ..models import Repuesto
    repuesto = Repuesto.objects.select_for_update().get(pk=repuesto_id)
    if _movement_exists(referencia):
        return repuesto
    if cantidad < 1 or repuesto.stock_disponible < cantidad:
        raise ValueError("Stock insuficiente para reservar")
    repuesto.stock_reservado += cantidad
    repuesto.save(update_fields=["stock_reservado"])
    _audit(repuesto, "reserva", cantidad, motivo, referencia, usuario)
    return repuesto
