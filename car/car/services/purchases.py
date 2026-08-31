from django.db import transaction
from django.utils.timezone import now


def recibir_item_compra(item, usuario=None):
    """Recibe un item de compra y registra una única entrada de stock."""
    from ..models import RepuestoEnStock, StockMovimiento

    with transaction.atomic():
        locked = type(item).objects.select_for_update().select_related(
            "compra", "repuesto"
        ).get(pk=item.pk)
        if locked.recibido:
            return locked
        locked.recibido = True
        locked.fecha_recibido = now()
        locked.save()
        repuesto = locked.repuesto
        repuesto.actualizar_stock_y_precio(
            cantidad_entrada=locked.cantidad,
            precio_compra=locked.precio_unitario,
            proveedor=locked.compra.proveedor,
        )
        stock = RepuestoEnStock.objects.filter(
            repuesto=repuesto, deposito="bodega-principal"
        ).first()
        if stock:
            StockMovimiento.objects.create(
                repuesto_stock=stock,
                tipo="entrada",
                cantidad=locked.cantidad,
                motivo=f"Compra #{locked.compra.numero_compra}",
                referencia=f"COMPRA-{locked.compra_id}-ITEM-{locked.pk}",
                usuario=usuario,
            )
        return locked
