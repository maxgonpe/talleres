"""Casos de uso para el flujo de ventas legacy."""

from decimal import Decimal, InvalidOperation
from django.db import transaction


@transaction.atomic
def crear_venta(form, cart, usuario):
    """Crea una venta pagada y descuenta su inventario de forma centralizada."""
    from ..models import VentaItem
    from .inventory import mover_stock

    venta = form.save(commit=False)
    venta.usuario = usuario
    venta.total = Decimal("0")
    venta.save()
    total = Decimal("0")
    for idx, item in enumerate(cart):
        try:
            repuesto_id = int(item.get("repuesto_id"))
            cantidad = int(item.get("cantidad", 1))
            precio = Decimal(str(item.get("precio_unitario", "0")))
        except (ValueError, TypeError, InvalidOperation) as exc:
            raise ValueError(f"Datos inválidos en item #{idx + 1}: {exc}") from exc
        if cantidad < 1 or precio < 0:
            raise ValueError(f"Cantidad o precio inválido en item #{idx + 1}")
        from ..models import Repuesto
        repuesto = Repuesto.objects.get(pk=repuesto_id)
        subtotal = precio * cantidad
        venta_item = VentaItem.objects.create(
            venta=venta, repuesto=repuesto, cantidad=cantidad,
            precio_unitario=precio, subtotal=subtotal,
        )
        mover_stock(repuesto.pk, cantidad, "salida", f"Venta #{venta.pk}",
                    f"VENTA-{venta.pk}-ITEM-{venta_item.pk}", usuario)
        total += subtotal
    venta.total = total
    venta.pagado = True
    venta.save(update_fields=["total", "pagado"])
    return venta


@transaction.atomic
def convertir_cotizacion(cotizacion, usuario):
    """Convierte una cotización activa en venta POS y actualiza su sesión."""
    from ..models import VentaPOS, VentaPOSItem
    from .stock import descontar_stock_venta_pos
    venta = VentaPOS.objects.create(
        sesion=cotizacion.sesion,
        cliente=cotizacion.cliente,
        usuario=usuario,
        subtotal=cotizacion.subtotal,
        descuento=cotizacion.descuento,
        total=cotizacion.total,
        observaciones=f"Convertida desde cotización #{cotizacion.id}",
        metodo_pago='efectivo',
    )
    for item in cotizacion.items.all():
        VentaPOSItem.objects.create(
            venta=venta, repuesto=item.repuesto, cantidad=item.cantidad,
            precio_unitario=item.precio_unitario, subtotal=item.subtotal,
        )
    descontar_stock_venta_pos(venta)
    cotizacion.estado = 'convertida'
    cotizacion.save(update_fields=['estado'])
    sesion = cotizacion.sesion
    sesion.total_ventas += venta.total
    sesion.numero_ventas += 1
    sesion.save(update_fields=['total_ventas', 'numero_ventas'])
    return venta
