from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import Vehiculo, Diagnostico, Trabajo


class Command(BaseCommand):
    help = 'Identifica y corrige placas duplicadas en la tabla Vehiculo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra los duplicados sin hacer cambios',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Aplica los cambios (elimina duplicados)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        apply = options['apply']

        if not dry_run and not apply:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Este comando requiere --dry-run o --apply'
                )
            )
            self.stdout.write('   Ejemplo: python manage.py fix_placas_duplicadas --dry-run')
            return

        # Buscar placas duplicadas
        from django.db.models import Count
        
        duplicados = (
            Vehiculo.objects.values('placa')
            .annotate(count=Count('placa'))
            .filter(count__gt=1)
            .order_by('-count')
        )

        if not duplicados:
            self.stdout.write(self.style.SUCCESS('✅ No hay placas duplicadas'))
            return

        self.stdout.write(
            self.style.WARNING(
                f'⚠️  Se encontraron {len(duplicados)} placas duplicadas:\n'
            )
        )

        total_eliminados = 0

        for dup in duplicados:
            placa = dup['placa']
            count = dup['count']
            
            vehiculos = Vehiculo.objects.filter(placa=placa).order_by('id')
            
            self.stdout.write(f'\n📋 Placa: {placa} ({count} vehículos)')
            
            # Analizar cada vehículo
            vehiculos_data = []
            for v in vehiculos:
                diagnosticos_count = Diagnostico.objects.filter(vehiculo=v).count()
                trabajos_count = Trabajo.objects.filter(vehiculo=v).count()
                
                vehiculos_data.append({
                    'vehiculo': v,
                    'id': v.id,
                    'cliente': v.cliente,
                    'diagnosticos': diagnosticos_count,
                    'trabajos': trabajos_count,
                    'total_relaciones': diagnosticos_count + trabajos_count,
                })
                
                self.stdout.write(
                    f'   - ID {v.id}: Cliente={v.cliente}, '
                    f'Diagnósticos={diagnosticos_count}, Trabajos={trabajos_count}'
                )

            # Determinar cuál mantener (el que tenga más relaciones o el más reciente)
            vehiculos_data.sort(
                key=lambda x: (x['total_relaciones'], x['id']), 
                reverse=True
            )
            
            mantener = vehiculos_data[0]
            eliminar = vehiculos_data[1:]

            self.stdout.write(
                self.style.SUCCESS(
                    f'   ✅ Mantener: ID {mantener["id"]} '
                    f'(relaciones: {mantener["total_relaciones"]})'
                )
            )

            for elim in eliminar:
                self.stdout.write(
                    self.style.WARNING(
                        f'   🗑️  Eliminar: ID {elim["id"]} '
                        f'(relaciones: {elim["total_relaciones"]})'
                    )
                )

            if apply:
                with transaction.atomic():
                    for elim in eliminar:
                        # Verificar que no tenga relaciones importantes
                        if elim['total_relaciones'] > 0:
                            self.stdout.write(
                                self.style.ERROR(
                                    f'   ⚠️  ADVERTENCIA: El vehículo ID {elim["id"]} '
                                    f'tiene {elim["total_relaciones"]} relaciones. '
                                    f'Se eliminará de todas formas.'
                                )
                            )
                        
                        elim['vehiculo'].delete()
                        total_eliminados += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'   ✅ Eliminado ID {elim["id"]}')
                        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  MODO DRY-RUN: No se realizaron cambios.\n'
                    f'   Ejecuta con --apply para aplicar los cambios.'
                )
            )
        elif apply:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Proceso completado. Se eliminaron {total_eliminados} vehículos duplicados.'
                )
            )
            self.stdout.write(
                self.style.SUCCESS(
                    '   Ahora puedes ejecutar: python manage.py migrate'
                )
            )

