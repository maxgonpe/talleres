from django.db import transaction
from django.utils.timezone import now


def recibir_item_compra(item, usuario=None):
    """Recibe un item de compra y registra una única entrada de stock."""
    from .inventory import mover_stock

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
        repuesto.precio_costo = locked.precio_unitario
        repuesto.save(update_fields=["precio_costo"])
        mover_stock(repuesto.pk, locked.cantidad, "entrada",
                    f"Compra #{locked.compra.numero_compra}",
                    f"COMPRA-{locked.compra_id}-ITEM-{locked.pk}", usuario)
        return locked
