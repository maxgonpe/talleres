from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import VentaPOS, SesionVenta


class Command(BaseCommand):
    help = 'Limpia datos huérfanos que impiden las migraciones'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué se eliminaría sin hacer cambios reales',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🧹 LIMPIANDO DATOS HUÉRFANOS")
        self.stdout.write("=" * 50)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN: Solo se mostrará qué se eliminaría"))
        
        # Buscar sesiones existentes
        sesiones_existentes = set(SesionVenta.objects.values_list('id', flat=True))
        self.stdout.write(f"📊 Sesiones existentes: {len(sesiones_existentes)}")
        
        # Buscar ventas con sesiones huérfanas
        ventas_huerfanas = VentaPOS.objects.exclude(sesion_id__in=sesiones_existentes)
        total_huerfanas = ventas_huerfanas.count()
        
        if total_huerfanas == 0:
            self.stdout.write(self.style.SUCCESS("✅ No se encontraron datos huérfanos"))
            return
        
        self.stdout.write(f"🚨 Ventas huérfanas encontradas: {total_huerfanas}")
        
        # Mostrar detalles
        for venta in ventas_huerfanas[:10]:
            self.stdout.write(f"   - Venta ID: {venta.id}, Sesión ID: {venta.sesion_id}")
        
        if total_huerfanas > 10:
            self.stdout.write(f"   ... y {total_huerfanas - 10} ventas más")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY-RUN: No se realizaron cambios"))
            return
        
        # Confirmar eliminación
        respuesta = input(f"\n¿Eliminar {total_huerfanas} ventas huérfanas? (s/N): ").strip().lower()
        if respuesta not in ['s', 'si', 'sí', 'y', 'yes']:
            self.stdout.write(self.style.ERROR("❌ Operación cancelada"))
            return
        
        # Eliminar ventas huérfanas
        with transaction.atomic():
            eliminadas = ventas_huerfanas.delete()
            self.stdout.write(f"✅ Eliminadas {eliminadas[0]} ventas huérfanas")
        
        self.stdout.write(self.style.SUCCESS("🎉 Limpieza completada exitosamente"))

