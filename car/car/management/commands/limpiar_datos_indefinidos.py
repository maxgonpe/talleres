from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import Repuesto


class Command(BaseCommand):
    help = 'Limpia datos indefinidos en el modelo Repuesto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin ejecutar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('MODO DRY-RUN: No se realizarán cambios'))
        
        # Contar registros problemáticos
        problemas = {
            'oem_vacio': Repuesto.objects.filter(oem__in=['oem', '']).count(),
            'referencia_vacia': Repuesto.objects.filter(referencia__in=['no-tiene', '']).count(),
            'origen_vacio': Repuesto.objects.filter(origen_repuesto__in=['sin-origen', '']).count(),
            'marca_veh_vacia': Repuesto.objects.filter(marca_veh__in=['xxx', 'xxxx', '']).count(),
            'tipo_motor_vacio': Repuesto.objects.filter(tipo_de_motor__in=['zzzzzz', 'zzzz', '']).count(),
            'marca_general': Repuesto.objects.filter(marca__in=['general', '']).count(),
        }
        
        total_problemas = sum(problemas.values())
        
        self.stdout.write(f"Registros con datos indefinidos encontrados:")
        for campo, cantidad in problemas.items():
            if cantidad > 0:
                self.stdout.write(f"  - {campo}: {cantidad}")
        
        self.stdout.write(f"Total de registros problemáticos: {total_problemas}")
        
        if total_problemas == 0:
            self.stdout.write(self.style.SUCCESS('No se encontraron datos indefinidos.'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Para ejecutar la limpieza, ejecuta sin --dry-run'))
            return
        
        # Confirmar antes de proceder
        confirm = input(f"¿Deseas limpiar {total_problemas} registros problemáticos? (y/N): ")
        if confirm.lower() != 'y':
            self.stdout.write('Operación cancelada.')
            return
        
        # Limpiar datos
        with transaction.atomic():
            # Limpiar campos con valores por defecto problemáticos
            Repuesto.objects.filter(oem__in=['oem', '']).update(oem=None)
            Repuesto.objects.filter(referencia__in=['no-tiene', '']).update(referencia=None)
            Repuesto.objects.filter(origen_repuesto__in=['sin-origen', '']).update(origen_repuesto=None)
            Repuesto.objects.filter(marca_veh__in=['xxx', 'xxxx', '']).update(marca_veh=None)
            Repuesto.objects.filter(tipo_de_motor__in=['zzzzzz', 'zzzz', '']).update(tipo_de_motor=None)
            Repuesto.objects.filter(marca__in=['general', '']).update(marca=None)
            
            # Sincronizar stock con RepuestoEnStock
            self.stdout.write("Sincronizando stock...")
            repuestos_sin_stock_detallado = Repuesto.objects.filter(
                stocks__isnull=True
            ).exclude(stock=0)
            
            for repuesto in repuestos_sin_stock_detallado:
                repuesto._sincronizar_con_stock_detallado(0, repuesto.precio_costo or 0)
        
        self.stdout.write(self.style.SUCCESS('Limpieza completada exitosamente.'))



