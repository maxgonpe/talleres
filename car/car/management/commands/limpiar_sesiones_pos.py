from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from car.models import SesionVenta, CarritoItem

class Command(BaseCommand):
    help = 'Limpiar todas las sesiones de POS y carritos antiguos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--todos',
            action='store_true',
            help='Limpiar TODAS las sesiones (incluso las activas)',
        )
        parser.add_argument(
            '--dias',
            type=int,
            default=1,
            help='Días de antigüedad para limpiar sesiones inactivas (default: 1)',
        )

    def handle(self, *args, **options):
        if options['todos']:
            # Limpiar TODAS las sesiones
            sesiones_totales = SesionVenta.objects.count()
            carritos_totales = CarritoItem.objects.count()
            
            # Cerrar todas las sesiones activas
            sesiones_activas = SesionVenta.objects.filter(activa=True)
            for sesion in sesiones_activas:
                sesion.activa = False
                sesion.fecha_fin = timezone.now()
                sesion.save()
            
            # Eliminar todos los carritos
            CarritoItem.objects.all().delete()
            
            # Eliminar todas las sesiones
            SesionVenta.objects.all().delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Limpieza completa realizada:\n'
                    f'   - {sesiones_totales} sesiones eliminadas\n'
                    f'   - {carritos_totales} carritos eliminados\n'
                    f'   - Sistema reiniciado desde cero'
                )
            )
        else:
            # Limpiar solo sesiones antiguas
            dias = options['dias']
            fecha_limite = timezone.now() - timedelta(days=dias)
            
            # Cerrar sesiones activas antiguas
            sesiones_activas_antiguas = SesionVenta.objects.filter(
                activa=True,
                fecha_inicio__lt=fecha_limite
            )
            
            for sesion in sesiones_activas_antiguas:
                sesion.activa = False
                sesion.fecha_fin = timezone.now()
                sesion.save()
            
            # Eliminar carritos de sesiones inactivas antiguas
            sesiones_antiguas = SesionVenta.objects.filter(
                activa=False,
                fecha_fin__lt=fecha_limite
            )
            
            carritos_eliminados = 0
            for sesion in sesiones_antiguas:
                carritos_eliminados += sesion.carrito_items.count()
                sesion.carrito_items.all().delete()
            
            # Eliminar las sesiones antiguas
            sesiones_eliminadas = sesiones_antiguas.count()
            sesiones_antiguas.delete()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Limpieza de sesiones antiguas realizada:\n'
                    f'   - {sesiones_eliminadas} sesiones eliminadas (más de {dias} días)\n'
                    f'   - {carritos_eliminados} carritos eliminados'
                )
            )
        
        # Mostrar estado actual
        sesiones_activas = SesionVenta.objects.filter(activa=True).count()
        sesiones_totales = SesionVenta.objects.count()
        carritos_totales = CarritoItem.objects.count()
        
        self.stdout.write(
            self.style.WARNING(
                f'\n📊 Estado actual:\n'
                f'   - Sesiones activas: {sesiones_activas}\n'
                f'   - Total sesiones: {sesiones_totales}\n'
                f'   - Total carritos: {carritos_totales}'
            )
        )














