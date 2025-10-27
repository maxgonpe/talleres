from django.core.management.base import BaseCommand
from car.models import VehiculoVersion


class Command(BaseCommand):
    help = 'Verifica y corrige los años de los vehículos que tienen valores incorrectos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Corregir automáticamente los años incorrectos',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        
        self.stdout.write("🔍 VERIFICANDO AÑOS DE VEHÍCULOS")
        self.stdout.write("=" * 50)
        
        # Buscar vehículos con años problemáticos
        vehiculos_problematicos = VehiculoVersion.objects.filter(
            anio_desde__gt=2030  # Años futuros sospechosos
        ) | VehiculoVersion.objects.filter(
            anio_hasta__gt=2030  # Años futuros sospechosos
        ) | VehiculoVersion.objects.filter(
            anio_desde__lt=1900  # Años muy antiguos
        ) | VehiculoVersion.objects.filter(
            anio_hasta__lt=1900  # Años muy antiguos
        )
        
        total_problematicos = vehiculos_problematicos.count()
        
        if total_problematicos == 0:
            self.stdout.write(self.style.SUCCESS("✅ No se encontraron vehículos con años problemáticos"))
            return
        
        self.stdout.write(f"🚨 Vehículos con años problemáticos: {total_problematicos}")
        
        # Mostrar algunos ejemplos
        for i, vehiculo in enumerate(vehiculos_problematicos[:10]):
            self.stdout.write(f"   {i+1}. {vehiculo.marca} {vehiculo.modelo} - "
                           f"Años: {vehiculo.anio_desde}-{vehiculo.anio_hasta} (ID: {vehiculo.id})")
        
        if total_problematicos > 10:
            self.stdout.write(f"   ... y {total_problematicos - 10} vehículos más")
        
        if not fix:
            self.stdout.write(f"\n💡 Para corregir automáticamente, ejecuta con --fix")
            return
        
        # Corregir años problemáticos
        self.stdout.write(f"\n🔧 CORRIGIENDO AÑOS PROBLEMÁTICOS...")
        
        corregidos = 0
        for vehiculo in vehiculos_problematicos:
            # Si el año es muy grande (como 4024), probablemente es un error de formato
            if vehiculo.anio_desde > 2030:
                # Intentar extraer el año correcto
                if vehiculo.anio_desde > 4000:
                    # Podría ser un error de formato, intentar dividir por 100
                    nuevo_anio = vehiculo.anio_desde // 100
                    if 1900 <= nuevo_anio <= 2030:
                        vehiculo.anio_desde = nuevo_anio
                        self.stdout.write(f"   ✅ {vehiculo.marca} {vehiculo.modelo}: {vehiculo.anio_desde} → {nuevo_anio}")
                    else:
                        # Si no funciona, usar un año por defecto
                        vehiculo.anio_desde = 2000
                        self.stdout.write(f"   ⚠️  {vehiculo.marca} {vehiculo.modelo}: {vehiculo.anio_desde} → 2000 (por defecto)")
                
            if vehiculo.anio_hasta > 2030:
                if vehiculo.anio_hasta > 4000:
                    nuevo_anio = vehiculo.anio_hasta // 100
                    if 1900 <= nuevo_anio <= 2030:
                        vehiculo.anio_hasta = nuevo_anio
                        self.stdout.write(f"   ✅ {vehiculo.marca} {vehiculo.modelo}: {vehiculo.anio_hasta} → {nuevo_anio}")
                    else:
                        vehiculo.anio_hasta = 2020
                        self.stdout.write(f"   ⚠️  {vehiculo.marca} {vehiculo.modelo}: {vehiculo.anio_hasta} → 2020 (por defecto)")
            
            # Asegurar que anio_desde <= anio_hasta
            if vehiculo.anio_desde > vehiculo.anio_hasta:
                vehiculo.anio_hasta = vehiculo.anio_desde
                self.stdout.write(f"   🔄 {vehiculo.marca} {vehiculo.modelo}: Ajustado anio_hasta a {vehiculo.anio_hasta}")
            
            vehiculo.save()
            corregidos += 1
        
        self.stdout.write(f"\n✅ Corregidos {corregidos} vehículos")
        self.stdout.write(self.style.SUCCESS("🎉 Verificación completada"))







