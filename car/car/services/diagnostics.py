"""Casos de uso del módulo de diagnósticos."""

from decimal import Decimal
from django.db import transaction
from ..models import DiagnosticoComponenteAccion, DiagnosticoRepuesto, Repuesto, Accion, Componente


def aprobar_diagnostico(diagnostico):
    """Aprueba un diagnóstico y crea su orden de trabajo asociada."""
    if diagnostico.estado != "pendiente":
        raise ValueError("Solo se pueden aprobar diagnósticos pendientes")
    return diagnostico.aprobar_y_clonar()


@transaction.atomic
def agregar_repuesto(diagnostico, repuesto_id, cantidad, precio_unitario):
    """Agrega un repuesto al diagnóstico evitando duplicados."""
    repuesto = Repuesto.objects.get(pk=repuesto_id)
    cantidad = int(cantidad)
    precio_unitario = Decimal(str(precio_unitario or 0))
    if cantidad < 1 or precio_unitario < 0:
        raise ValueError("Cantidad o precio inválido")
    if DiagnosticoRepuesto.objects.filter(diagnostico=diagnostico, repuesto=repuesto).exists():
        return None
    return DiagnosticoRepuesto.objects.create(
        diagnostico=diagnostico,
        repuesto=repuesto,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        subtotal=cantidad * precio_unitario,
    )


@transaction.atomic
def agregar_accion(diagnostico, componente_id, accion_id, precio_mano_obra=0):
    """Agrega una acción al diagnóstico evitando combinaciones duplicadas."""
    componente = Componente.objects.get(pk=componente_id)
    accion = Accion.objects.get(pk=accion_id)
    precio = Decimal(str(precio_mano_obra or 0))
    if precio < 0:
        raise ValueError("El precio no puede ser negativo")
    if DiagnosticoComponenteAccion.objects.filter(
        diagnostico=diagnostico, componente=componente, accion=accion
    ).exists():
        return None
    return DiagnosticoComponenteAccion.objects.create(
        diagnostico=diagnostico,
        componente=componente,
        accion=accion,
        precio_mano_obra=precio,
    )
