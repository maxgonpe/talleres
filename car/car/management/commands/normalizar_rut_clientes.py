from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from car.models import (
    Cliente_Taller,
    Vehiculo,
    Venta,
    VentaPOS,
    Cotizacion,
)


def normalizar_rut(valor: str) -> str:
    if not valor:
        return ""
    return (
        valor.replace('.', '')
             .replace('-', '')
             .replace(' ', '')
             .upper()
    )


class Command(BaseCommand):
    help = (
        "Normaliza los RUT de Cliente_Taller removiendo guiones/puntos. "
        "Primero fusiona duplicados para evitar choques y luego actualiza el RUT final."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica los cambios (por defecto solo muestra lo que haría).'
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']

        clientes = list(Cliente_Taller.objects.all())
        grupos = defaultdict(list)

        for cliente in clientes:
            rut_normalizado = normalizar_rut(cliente.rut)
            grupos[rut_normalizado].append(cliente)

        total_grupos = len(grupos)
        grupos_con_duplicados = [g for g in grupos.values() if len(g) > 1]

        self.stdout.write(self.style.NOTICE(
            f"Total clientes: {len(clientes)} | Grupos únicos (rut normalizado): {total_grupos}"
        ))
        self.stdout.write(self.style.NOTICE(
            f"Grupos con duplicados (mismo rut sin guion): {len(grupos_con_duplicados)}"
        ))

        if not grupos_con_duplicados and not apply_changes:
            self.stdout.write(self.style.SUCCESS("No hay duplicados que fusionar."))

        for grupo in grupos_con_duplicados:
            grupo_ordenado = sorted(grupo, key=lambda c: (0 if '-' in c.rut else 1, c.rut))
            principal = grupo_ordenado[0]
            duplicados = grupo_ordenado[1:]

            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f"Normalizado {normalizar_rut(principal.rut)} → mantendré {principal.rut}"
            ))

            if not apply_changes:
                for dup in duplicados:
                    self.stdout.write(f"  - Fusionar {dup.rut} dentro de {principal.rut}")
                continue

            with transaction.atomic():
                for dup in duplicados:
                    vehiculos_actualizados = Vehiculo.objects.filter(cliente=dup).update(cliente=principal)
                    ventas_actualizadas = Venta.objects.filter(cliente=dup).update(cliente=principal)
                    ventas_pos_actualizadas = VentaPOS.objects.filter(cliente=dup).update(cliente=principal)
                    cotizaciones_actualizadas = Cotizacion.objects.filter(cliente=dup).update(cliente=principal)

                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f"  → {dup.rut}: vehiculos={vehiculos_actualizados}, "
                            f"ventas={ventas_actualizadas}, pos={ventas_pos_actualizadas}, "
                            f"cotizaciones={cotizaciones_actualizadas}"
                        )
                    )

                    dup.delete()
                    self.stdout.write(self.style.SUCCESS(f"    Eliminado duplicado {dup.rut}"))

        # Segunda fase: actualizar el RUT de los clientes restantes
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE("Normalizando RUT restantes (removiendo guiones/puntos)..."))

        pendientes = list(Cliente_Taller.objects.all())

        for cliente in pendientes:
            rut_normalizado = normalizar_rut(cliente.rut)
            if cliente.rut == rut_normalizado:
                continue

            self.stdout.write(f"  {cliente.rut} → {rut_normalizado}")

            if not apply_changes:
                continue

            with transaction.atomic():
                existente = Cliente_Taller.objects.filter(rut=rut_normalizado).first()

                if existente and existente != cliente:
                    principal = existente
                else:
                    principal = Cliente_Taller.objects.create(
                        rut=rut_normalizado,
                        nombre=cliente.nombre,
                        telefono=cliente.telefono,
                        email=cliente.email,
                        direccion=cliente.direccion,
                        activo=cliente.activo,
                    )
                    principal.fecha_registro = cliente.fecha_registro
                    principal.save(update_fields=['fecha_registro'])

                vehiculos_actualizados = Vehiculo.objects.filter(cliente=cliente).update(cliente=principal)
                ventas_actualizadas = Venta.objects.filter(cliente=cliente).update(cliente=principal)
                ventas_pos_actualizadas = VentaPOS.objects.filter(cliente=cliente).update(cliente=principal)
                cotizaciones_actualizadas = Cotizacion.objects.filter(cliente=cliente).update(cliente=principal)

                self.stdout.write(
                    self.style.HTTP_INFO(
                        f"    → Reasignados: vehiculos={vehiculos_actualizados}, "
                        f"ventas={ventas_actualizadas}, pos={ventas_pos_actualizadas}, "
                        f"cotizaciones={cotizaciones_actualizadas}"
                    )
                )

                if existente and existente != cliente:
                    cliente.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    Eliminado duplicado original {cliente.rut}, se conserva {principal.rut}"
                        )
                    )
                else:
                    cliente.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    Cliente {cliente.rut} reemplazado por {principal.rut}"
                        )
                    )

        if apply_changes:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS("Proceso completado: RUT normalizados."))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING("Modo simulación: use --apply para ejecutar los cambios."))
