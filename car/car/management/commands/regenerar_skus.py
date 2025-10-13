import re
from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import Repuesto
from django.utils.crypto import get_random_string


class Command(BaseCommand):
    help = 'Regenera todos los SKUs de repuestos con el nuevo algoritmo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar sin guardar cambios (solo mostrar qué se haría)',
        )
        parser.add_argument(
            '--id',
            type=int,
            help='Regenerar SKU solo para un repuesto específico por ID',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Límite de repuestos a procesar (default: 100)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        repuesto_id = options.get('id')
        limit = options['limit']

        # Obtener repuestos a procesar
        if repuesto_id:
            repuestos = Repuesto.objects.filter(id=repuesto_id)
        else:
            repuestos = Repuesto.objects.all()[:limit]

        total_repuestos = repuestos.count()
        self.stdout.write(f"Procesando {total_repuestos} repuestos...")

        if dry_run:
            self.stdout.write(self.style.WARNING("MODO DRY-RUN: No se guardarán cambios"))

        procesados = 0
        actualizados = 0

        for repuesto in repuestos:
            procesados += 1
            self.stdout.write(f"\n--- Procesando ID {repuesto.id}: {repuesto.nombre} ---")
            
            # Generar nuevo SKU
            nuevo_sku = self.generar_nuevo_sku(repuesto)
            sku_actual = repuesto.sku
            
            self.stdout.write(f"SKU actual: {sku_actual}")
            self.stdout.write(f"SKU nuevo:  {nuevo_sku}")
            
            if sku_actual != nuevo_sku:
                if not dry_run:
                    repuesto.sku = nuevo_sku
                    repuesto.save()
                    actualizados += 1
                    self.stdout.write(self.style.SUCCESS("  ✓ SKU actualizado"))
                else:
                    actualizados += 1
                    self.stdout.write(self.style.WARNING("  - SKU sería actualizado"))
            else:
                self.stdout.write("  - SKU sin cambios")

        self.stdout.write(f"\n{'='*50}")
        self.stdout.write(f"Resumen:")
        self.stdout.write(f"  Repuestos procesados: {procesados}")
        self.stdout.write(f"  SKUs actualizados: {actualizados}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("Ejecuta sin --dry-run para aplicar los cambios"))

    def generar_nuevo_sku(self, repuesto):
        """
        Genera un nuevo SKU usando el algoritmo actualizado
        """
        # 1. Primeros 5 caracteres del nombre
        nombre_part = (repuesto.nombre[:5].upper() if repuesto.nombre else "REPUE")
        
        # 2. Primeros 4 caracteres de marca_veh
        marca_veh_part = (repuesto.marca_veh[:4].upper() if repuesto.marca_veh and repuesto.marca_veh != 'xxx' else "XXXX")
        
        # 3. Primer grupo de tipo_de_motor (6-7 caracteres)
        tipo_motor_part = "ZZZZZZ"  # Valor por defecto
        
        if repuesto.tipo_de_motor and repuesto.tipo_de_motor != 'zzzzzz':
            # Tomar el primer grupo antes del primer guión
            primer_grupo = repuesto.tipo_de_motor.split(' - ')[0].strip()
            if primer_grupo:
                # Limitar a 6-7 caracteres máximo
                tipo_motor_part = primer_grupo[:7].upper()
                # Si es muy corto, rellenar con 'Z'
                if len(tipo_motor_part) < 6:
                    tipo_motor_part = tipo_motor_part.ljust(6, 'Z')
        
        # 4. Número aleatorio de 4 dígitos
        numero_aleatorio = get_random_string(length=4, allowed_chars="0123456789")
        
        # Formato final: NOMBRE-MARCA-MOTOR-NUMERO
        return f"{nombre_part}-{marca_veh_part}-{tipo_motor_part}-{numero_aleatorio}"
