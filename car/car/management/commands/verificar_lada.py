from django.core.management.base import BaseCommand
from car.models import VehiculoVersion


class Command(BaseCommand):
    help = 'Verifica específicamente los datos de vehículos Lada'

    def handle(self, *args, **options):
        self.stdout.write("🔍 VERIFICANDO DATOS DE LADA")
        self.stdout.write("=" * 40)
        
        # Buscar vehículos Lada
        vehiculos_lada = VehiculoVersion.objects.filter(marca__icontains='lada')
        
        if not vehiculos_lada.exists():
            self.stdout.write("❌ No se encontraron vehículos Lada")
            return
        
        self.stdout.write(f"📊 Vehículos Lada encontrados: {vehiculos_lada.count()}")
        
        # Mostrar todos los vehículos Lada
        for vehiculo in vehiculos_lada:
            self.stdout.write(f"\n🚗 {vehiculo.marca} {vehiculo.modelo}")
            self.stdout.write(f"   ID: {vehiculo.id}")
            self.stdout.write(f"   Años: {vehiculo.anio_desde}-{vehiculo.anio_hasta}")
            self.stdout.write(f"   Motor: {vehiculo.motor or 'N/A'}")
            self.stdout.write(f"   Carrocería: {vehiculo.carroceria or 'N/A'}")
            
            # Verificar si los años son problemáticos
            if vehiculo.anio_desde > 2030 or vehiculo.anio_hasta > 2030:
                self.stdout.write(f"   ⚠️  PROBLEMA: Años fuera de rango normal")
            elif vehiculo.anio_desde < 1900 or vehiculo.anio_hasta < 1900:
                self.stdout.write(f"   ⚠️  PROBLEMA: Años muy antiguos")
            else:
                self.stdout.write(f"   ✅ Años normales")
        
        # Buscar vehículos con años problemáticos específicamente
        vehiculos_problematicos = vehiculos_lada.filter(
            anio_desde__gt=2030
        ) | vehiculos_lada.filter(
            anio_hasta__gt=2030
        )
        
        if vehiculos_problematicos.exists():
            self.stdout.write(f"\n🚨 Vehículos Lada con años problemáticos: {vehiculos_problematicos.count()}")
            for vehiculo in vehiculos_problematicos:
                self.stdout.write(f"   - {vehiculo.marca} {vehiculo.modelo}: {vehiculo.anio_desde}-{vehiculo.anio_hasta}")
        else:
            self.stdout.write(f"\n✅ Todos los vehículos Lada tienen años normales")


