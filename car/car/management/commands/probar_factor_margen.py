from django.core.management.base import BaseCommand
from car.models import Repuesto
from decimal import Decimal


class Command(BaseCommand):
    help = 'Prueba el sistema de factor de margen automático'

    def add_arguments(self, parser):
        parser.add_argument(
            '--repuesto-id',
            type=int,
            help='ID del repuesto a probar',
        )

    def handle(self, *args, **options):
        repuesto_id = options.get('repuesto_id')
        
        if repuesto_id:
            try:
                repuesto = Repuesto.objects.get(id=repuesto_id)
            except Repuesto.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Repuesto con ID {repuesto_id} no encontrado'))
                return
        else:
            # Buscar un repuesto con stock para probar
            repuesto = Repuesto.objects.filter(stock__gt=0).first()
            if not repuesto:
                self.stdout.write(self.style.ERROR('No se encontraron repuestos con stock para probar'))
                return
        
        self.stdout.write(f"🧪 Probando Factor de Margen Automático")
        self.stdout.write(f"Repuesto: {repuesto.nombre}")
        self.stdout.write("=" * 60)
        
        # Estado inicial
        self.stdout.write("📊 ESTADO INICIAL:")
        self.stdout.write(f"  Stock: {repuesto.stock}")
        self.stdout.write(f"  Precio costo: ${repuesto.precio_costo or 0}")
        self.stdout.write(f"  Precio venta: ${repuesto.precio_venta or 0}")
        
        if repuesto.precio_costo and repuesto.precio_venta and repuesto.precio_costo > 0:
            factor_actual = repuesto.precio_venta / repuesto.precio_costo
            self.stdout.write(f"  Factor de margen actual: {factor_actual:.2f}")
        else:
            self.stdout.write(f"  Factor de margen actual: No calculable")
        
        self.stdout.write("")
        
        # Simular diferentes escenarios
        escenarios = [
            {"cantidad": 3, "precio": Decimal('12.00'), "descripcion": "Compra más barata"},
            {"cantidad": 2, "precio": Decimal('18.00'), "descripcion": "Compra más cara"},
            {"cantidad": 1, "precio": Decimal('15.00'), "descripcion": "Compra precio medio"},
        ]
        
        for i, escenario in enumerate(escenarios, 1):
            self.stdout.write(f"🔄 ESCENARIO {i}: {escenario['descripcion']}")
            self.stdout.write(f"  Entrada: {escenario['cantidad']} unidades a ${escenario['precio']}")
            
            # Mostrar cálculo esperado
            stock_anterior = repuesto.stock or 0
            precio_costo_anterior = repuesto.precio_costo or Decimal('0')
            precio_venta_anterior = repuesto.precio_venta or Decimal('0')
            
            if stock_anterior > 0 and precio_costo_anterior > 0:
                # Cálculo esperado
                valor_anterior = stock_anterior * precio_costo_anterior
                valor_nuevo = escenario['cantidad'] * escenario['precio']
                nuevo_stock = stock_anterior + escenario['cantidad']
                nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
                
                if precio_venta_anterior > 0 and precio_costo_anterior > 0:
                    factor_margen = precio_venta_anterior / precio_costo_anterior
                    nuevo_precio_venta = nuevo_precio_costo * factor_margen
                    
                    self.stdout.write(f"  📈 Cálculo esperado:")
                    self.stdout.write(f"    Stock: {stock_anterior} + {escenario['cantidad']} = {nuevo_stock}")
                    self.stdout.write(f"    Precio costo: (${valor_anterior} + ${valor_nuevo}) ÷ {nuevo_stock} = ${nuevo_precio_costo:.2f}")
                    self.stdout.write(f"    Factor margen: {factor_margen:.2f}")
                    self.stdout.write(f"    Precio venta: ${nuevo_precio_costo:.2f} × {factor_margen:.2f} = ${nuevo_precio_venta:.2f}")
            
            # Ejecutar actualización
            resultado = repuesto.actualizar_stock_y_precio(
                cantidad_entrada=escenario['cantidad'],
                precio_compra=escenario['precio'],
                proveedor='Proveedor Test'
            )
            
            self.stdout.write(f"  ✅ Resultado real:")
            self.stdout.write(f"    Stock: {resultado['stock_anterior']} → {resultado['stock_nuevo']}")
            self.stdout.write(f"    Precio costo: ${resultado['precio_costo_anterior']} → ${resultado['precio_costo_nuevo']}")
            self.stdout.write(f"    Precio venta: ${resultado['precio_venta_anterior']} → ${resultado['precio_venta_nuevo']}")
            self.stdout.write(f"    Factor aplicado: {resultado['factor_margen_aplicado']:.2f}")
            self.stdout.write("")
        
        # Estado final
        repuesto.refresh_from_db()
        self.stdout.write("📊 ESTADO FINAL:")
        self.stdout.write(f"  Stock: {repuesto.stock}")
        self.stdout.write(f"  Precio costo: ${repuesto.precio_costo}")
        self.stdout.write(f"  Precio venta: ${repuesto.precio_venta}")
        
        if repuesto.precio_costo and repuesto.precio_venta and repuesto.precio_costo > 0:
            factor_final = repuesto.precio_venta / repuesto.precio_costo
            self.stdout.write(f"  Factor de margen final: {factor_final:.2f}")
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS('🎉 Prueba del factor de margen completada exitosamente.'))


