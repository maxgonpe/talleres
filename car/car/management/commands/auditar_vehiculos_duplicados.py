import itertools

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from car.models import Cliente_Taller, Vehiculo, Diagnostico, Trabajo


class Command(BaseCommand):
    help = (
        "Audita vehículos duplicados por cliente y placa. "
        "Con --fix unifica las referencias de diagnóstico/trabajo y elimina duplicados."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Aplica la corrección: reasigna relaciones y elimina duplicados.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Procesa solo los primeros N grupos duplicados (para pruebas).",
        )

    def handle(self, *args, **options):
        apply_fix = options["fix"]
        limit = options.get("limit")

        duplicates = (
            Vehiculo.objects.values("cliente_id", "placa")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
            .order_by("placa", "cliente_id")
        )

        total_groups = duplicates.count()
        if limit is not None:
            duplicates = list(itertools.islice(duplicates.iterator(), limit))
        else:
            duplicates = list(duplicates)

        if not duplicates:
            self.stdout.write(self.style.SUCCESS("No se encontraron vehículos duplicados."))
            return

        self.stdout.write(
            self.style.WARNING(
                f"Se detectaron {total_groups} combinaciones cliente+placa con duplicados."
            )
        )
        if apply_fix:
            self.stdout.write(self.style.WARNING("Modo corrección ACTIVADO (--fix)."))
        else:
            self.stdout.write(
                self.style.NOTICE(
                    "Modo solo lectura: usa --fix para aplicar la unificación."
                )
            )

        for index, entry in enumerate(duplicates, start=1):
            cliente_id = entry["cliente_id"]
            placa = entry["placa"] or "(sin placa)"

            vehiculos = (
                Vehiculo.objects.select_related("cliente")
                .filter(cliente_id=cliente_id, placa=entry["placa"])
                .order_by("id")
            )

            if not vehiculos:
                continue

            cliente = vehiculos[0].cliente
            principal = vehiculos[0]
            duplicados = list(vehiculos[1:])

            diag_por_vehiculo = {
                item["vehiculo_id"]: item["total"]
                for item in Diagnostico.objects.filter(vehiculo__in=vehiculos)
                .values("vehiculo_id")
                .annotate(total=Count("id"))
            }
            trabajos_por_vehiculo = {
                item["vehiculo_id"]: item["total"]
                for item in Trabajo.objects.filter(vehiculo__in=vehiculos)
                .values("vehiculo_id")
                .annotate(total=Count("id"))
            }

            self.stdout.write("")
            self.stdout.write(self.style.MIGRATE_HEADING(f"[{index}] Cliente {cliente.rut} - {cliente.nombre}"))
            self.stdout.write(self.style.HTTP_INFO(f"  Placa: {placa} | Vehículos: {len(vehiculos)}"))
            self.stdout.write(self.style.HTTP_INFO(f"  Principal sugerido: ID {principal.id}"))

            for veh in vehiculos:
                diag_count = diag_por_vehiculo.get(veh.id, 0)
                trabajo_count = trabajos_por_vehiculo.get(veh.id, 0)
                marcador = "*" if veh == principal else "-"
                self.stdout.write(
                    f"    {marcador} Vehículo ID={veh.id} | Marca/Modelo={veh.marca} {veh.modelo} {veh.anio or ''} "
                    f"| Diagnósticos={diag_count} | Trabajos={trabajo_count}"
                )

            if not apply_fix:
                continue

            with transaction.atomic():
                for vehiculo_dup in duplicados:
                    diag_actualizados = Diagnostico.objects.filter(vehiculo=vehiculo_dup).update(
                        vehiculo=principal
                    )
                    trabajos_actualizados = Trabajo.objects.filter(vehiculo=vehiculo_dup).update(
                        vehiculo=principal
                    )

                    self.stdout.write(
                        self.style.HTTP_INFO(
                            f"    → Reasignado ID {vehiculo_dup.id}: {diag_actualizados} diagnósticos, "
                            f"{trabajos_actualizados} trabajos."
                        )
                    )

                    vehiculo_dup.delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    → Vehículo duplicado ID {vehiculo_dup.id} eliminado."
                        )
                    )

            self.stdout.write(
                self.style.SUCCESS(
                    f"  Grupo cliente={cliente.rut} placa={placa} unificado correctamente."
                )
            )

        if apply_fix:
            self.stdout.write(self.style.SUCCESS("Proceso de unificación finalizado."))
        else:
            self.stdout.write(self.style.SUCCESS("Revisión completada (sin cambios)."))

