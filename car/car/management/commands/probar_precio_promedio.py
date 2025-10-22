from django.core.management.base import BaseCommand
from car.models import Repuesto
from decimal import Decimal


class Command(BaseCommand):
    help = 'Prueba el sistema de precio promedio ponderado'

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
        
        self.stdout.write(f"Probando con repuesto: {repuesto.nombre}")
        self.stdout.write(f"Stock actual: {repuesto.stock}")
        self.stdout.write(f"Precio costo actual: ${repuesto.precio_costo or 0}")
        self.stdout.write(f"Precio venta actual: ${repuesto.precio_venta or 0}")
        self.stdout.write("")
        
        # Simular entrada de mercancía
        cantidad_entrada = 5
        precio_compra = Decimal('15.00')
        
        self.stdout.write(f"Simulando entrada de {cantidad_entrada} unidades a ${precio_compra} cada una")
        
        # Mostrar cálculo manual
        stock_anterior = repuesto.stock or 0
        precio_costo_anterior = repuesto.precio_costo or Decimal('0')
        precio_venta_anterior = repuesto.precio_venta or Decimal('0')
        
        if stock_anterior > 0 and precio_costo_anterior > 0:
            valor_anterior = stock_anterior * precio_costo_anterior
            valor_nuevo = cantidad_entrada * precio_compra
            nuevo_precio_costo = (valor_anterior + valor_nuevo) / (stock_anterior + cantidad_entrada)
            
            self.stdout.write("Cálculo manual:")
            self.stdout.write(f"  Valor anterior: {stock_anterior} × ${precio_costo_anterior} = ${valor_anterior}")
            self.stdout.write(f"  Valor nuevo: {cantidad_entrada} × ${precio_compra} = ${valor_nuevo}")
            self.stdout.write(f"  Nuevo precio costo: ${nuevo_precio_costo}")
            
            # Mostrar factor de margen
            if precio_venta_anterior > 0 and precio_costo_anterior > 0:
                factor_margen = precio_venta_anterior / precio_costo_anterior
                self.stdout.write(f"  Factor de margen actual: {factor_margen:.2f}")
                self.stdout.write(f"  Precio venta calculado: ${nuevo_precio_costo} × {factor_margen:.2f} = ${nuevo_precio_costo * factor_margen}")
        
        # Ejecutar actualización
        resultado = repuesto.actualizar_stock_y_precio(
            cantidad_entrada=cantidad_entrada,
            precio_compra=precio_compra,
            proveedor='Proveedor Test'
        )
        
        self.stdout.write("")
        self.stdout.write("Resultado de la actualización:")
        self.stdout.write(f"  Stock anterior: {resultado['stock_anterior']}")
        self.stdout.write(f"  Stock nuevo: {resultado['stock_nuevo']}")
        self.stdout.write(f"  Precio costo anterior: ${resultado['precio_costo_anterior']}")
        self.stdout.write(f"  Precio costo nuevo: ${resultado['precio_costo_nuevo']}")
        self.stdout.write(f"  Precio venta anterior: ${resultado['precio_venta_anterior']}")
        self.stdout.write(f"  Precio venta nuevo: ${resultado['precio_venta_nuevo']}")
        self.stdout.write(f"  Cantidad agregada: {resultado['cantidad_agregada']}")
        self.stdout.write(f"  Factor de margen aplicado: {resultado['factor_margen_aplicado']:.2f}")
        
        # Verificar sincronización
        repuesto.refresh_from_db()
        self.stdout.write("")
        self.stdout.write("Estado final del repuesto:")
        self.stdout.write(f"  Stock: {repuesto.stock}")
        self.stdout.write(f"  Precio costo: ${repuesto.precio_costo}")
        self.stdout.write(f"  Precio venta: ${repuesto.precio_venta}")
        
        # Verificar RepuestoEnStock
        stock_detallado = repuesto.stocks.filter(deposito='bodega-principal').first()
        if stock_detallado:
            self.stdout.write("")
            self.stdout.write("Estado de RepuestoEnStock:")
            self.stdout.write(f"  Stock: {stock_detallado.stock}")
            self.stdout.write(f"  Precio compra: ${stock_detallado.precio_compra}")
            self.stdout.write(f"  Precio venta: ${stock_detallado.precio_venta}")
        
        self.stdout.write(self.style.SUCCESS('Prueba completada exitosamente.'))
