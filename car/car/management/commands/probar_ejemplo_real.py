from django.core.management.base import BaseCommand
from car.models import Repuesto
from decimal import Decimal


class Command(BaseCommand):
    help = 'Prueba el sistema con el ejemplo real del usuario'

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
        
        self.stdout.write("🧪 PRUEBA CON EJEMPLO REAL DEL USUARIO")
        self.stdout.write("=" * 60)
        
        # Estado inicial
        self.stdout.write("📊 ESTADO INICIAL:")
        self.stdout.write(f"  Repuesto: {repuesto.nombre}")
        self.stdout.write(f"  Stock: {repuesto.stock}")
        self.stdout.write(f"  Precio costo: ${repuesto.precio_costo or 0}")
        self.stdout.write(f"  Precio venta: ${repuesto.precio_venta or 0}")
        
        # Calcular factor de margen actual
        if repuesto.precio_costo and repuesto.precio_venta and repuesto.precio_costo > 0:
            factor_actual = repuesto.precio_venta / repuesto.precio_costo
            margen_porcentaje = (factor_actual - 1) * 100
            self.stdout.write(f"  Factor de margen: {factor_actual:.3f}")
            self.stdout.write(f"  Margen porcentual: {margen_porcentaje:.1f}%")
        else:
            self.stdout.write(self.style.WARNING("  ⚠️ No se puede calcular factor de margen (datos incompletos)"))
            return
        
        self.stdout.write("")
        
        # Simular el ejemplo del usuario
        # Estado inicial: 3 unidades a $19,278
        # Compra: 4 unidades a $20,000
        
        # Configurar el estado inicial si es necesario
        if repuesto.stock != 3 or repuesto.precio_costo != Decimal('19278'):
            self.stdout.write("🔧 Configurando estado inicial del ejemplo...")
            repuesto.stock = 3
            repuesto.precio_costo = Decimal('19278')
            repuesto.precio_venta = Decimal('30000')
            repuesto.save()
            self.stdout.write("  ✅ Estado inicial configurado")
        
        self.stdout.write("")
        self.stdout.write("🛒 SIMULANDO COMPRA:")
        self.stdout.write("  Entrada: 4 unidades a $20,000 cada una")
        
        # Mostrar cálculo manual esperado
        stock_anterior = 3
        precio_costo_anterior = Decimal('19278')
        precio_venta_anterior = Decimal('30000')
        cantidad_entrada = 4
        precio_compra_nuevo = Decimal('20000')
        
        # Cálculo manual
        valor_anterior = stock_anterior * precio_costo_anterior
        valor_nuevo = cantidad_entrada * precio_compra_nuevo
        nuevo_stock = stock_anterior + cantidad_entrada
        nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
        factor_margen = precio_venta_anterior / precio_costo_anterior
        nuevo_precio_venta = nuevo_precio_costo * factor_margen
        
        self.stdout.write("")
        self.stdout.write("📈 CÁLCULO MANUAL ESPERADO:")
        self.stdout.write(f"  Stock anterior: {stock_anterior}")
        self.stdout.write(f"  Valor anterior: {stock_anterior} × ${precio_costo_anterior} = ${valor_anterior}")
        self.stdout.write(f"  Valor nuevo: {cantidad_entrada} × ${precio_compra_nuevo} = ${valor_nuevo}")
        self.stdout.write(f"  Nuevo stock: {nuevo_stock}")
        self.stdout.write(f"  Nuevo precio costo: (${valor_anterior} + ${valor_nuevo}) ÷ {nuevo_stock} = ${nuevo_precio_costo:.2f}")
        self.stdout.write(f"  Factor margen: ${precio_venta_anterior} ÷ ${precio_costo_anterior} = {factor_margen:.3f}")
        self.stdout.write(f"  Nuevo precio venta: ${nuevo_precio_costo:.2f} × {factor_margen:.3f} = ${nuevo_precio_venta:.2f}")
        
        # Ejecutar actualización con el sistema
        self.stdout.write("")
        self.stdout.write("🔄 EJECUTANDO ACTUALIZACIÓN AUTOMÁTICA...")
        
        resultado = repuesto.actualizar_stock_y_precio(
            cantidad_entrada=cantidad_entrada,
            precio_compra=precio_compra_nuevo,
            proveedor='Proveedor Ejemplo'
        )
        
        self.stdout.write("")
        self.stdout.write("✅ RESULTADO DEL SISTEMA:")
        self.stdout.write(f"  Stock: {resultado['stock_anterior']} → {resultado['stock_nuevo']}")
        self.stdout.write(f"  Precio costo: ${resultado['precio_costo_anterior']} → ${resultado['precio_costo_nuevo']}")
        self.stdout.write(f"  Precio venta: ${resultado['precio_venta_anterior']} → ${resultado['precio_venta_nuevo']}")
        self.stdout.write(f"  Factor aplicado: {resultado['factor_margen_aplicado']:.3f}")
        
        # Verificar si coincide con el cálculo manual
        self.stdout.write("")
        self.stdout.write("🔍 VERIFICACIÓN:")
        diferencia_costo = abs(float(resultado['precio_costo_nuevo']) - float(nuevo_precio_costo))
        diferencia_venta = abs(float(resultado['precio_venta_nuevo']) - float(nuevo_precio_venta))
        
        if diferencia_costo < 0.01 and diferencia_venta < 0.01:
            self.stdout.write(self.style.SUCCESS("  ✅ PERFECTO: El sistema calculó correctamente"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ ERROR: Hay diferencias en el cálculo"))
            self.stdout.write(f"    Diferencia en precio costo: ${diferencia_costo:.2f}")
            self.stdout.write(f"    Diferencia en precio venta: ${diferencia_venta:.2f}")
        
        # Estado final
        repuesto.refresh_from_db()
        self.stdout.write("")
        self.stdout.write("📊 ESTADO FINAL DEL REPUESTO:")
        self.stdout.write(f"  Stock: {repuesto.stock}")
        self.stdout.write(f"  Precio costo: ${repuesto.precio_costo}")
        self.stdout.write(f"  Precio venta: ${repuesto.precio_venta}")
        
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS('🎉 Prueba del ejemplo real completada exitosamente.'))


