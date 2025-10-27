from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import Repuesto, RepuestoEnStock


class Command(BaseCommand):
    help = 'Sincroniza todos los repuestos con RepuestoEnStock creando clones faltantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué se sincronizaría sin hacer cambios reales',
        )
        parser.add_argument(
            '--deposito',
            type=str,
            default='bodega-principal',
            help='Depósito específico para crear clones (default: bodega-principal)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        deposito = options['deposito']
        
        self.stdout.write("🔄 INICIANDO SINCRONIZACIÓN DE REPUESTOS CON STOCK")
        self.stdout.write("=" * 60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN: Solo se mostrará qué se sincronizaría"))
        
        # Buscar repuestos que no tienen clon en RepuestoEnStock
        repuestos_sin_clon = self.identificar_repuestos_sin_clon(deposito)
        
        if not repuestos_sin_clon:
            self.stdout.write(self.style.SUCCESS("✅ Todos los repuestos ya tienen clon en RepuestoEnStock"))
            return
        
        # Mostrar resumen
        self.mostrar_resumen_sincronizacion(repuestos_sin_clon)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY-RUN: No se realizaron cambios"))
            return
        
        # Confirmar antes de sincronizar
        if not self.confirmar_sincronizacion():
            self.stdout.write(self.style.ERROR("❌ Operación cancelada"))
            return
        
        # Sincronizar repuestos
        sincronizados = self.sincronizar_repuestos(repuestos_sin_clon, deposito)
        
        # Mostrar resultado final
        self.mostrar_resultado_final(sincronizados)

    def identificar_repuestos_sin_clon(self, deposito):
        """Identifica repuestos que no tienen clon en RepuestoEnStock"""
        self.stdout.write(f"🔍 Buscando repuestos sin clon en depósito: {deposito}")
        
        # Obtener todos los repuestos
        todos_repuestos = Repuesto.objects.all()
        
        # Obtener repuestos que ya tienen clon
        repuestos_con_clon = RepuestoEnStock.objects.filter(
            deposito=deposito
        ).values_list('repuesto_id', flat=True)
        
        # Filtrar repuestos sin clon
        repuestos_sin_clon = todos_repuestos.exclude(id__in=repuestos_con_clon)
        
        return repuestos_sin_clon

    def mostrar_resumen_sincronizacion(self, repuestos_sin_clon):
        """Muestra un resumen de la sincronización"""
        total_repuestos = repuestos_sin_clon.count()
        
        self.stdout.write(f"\n📊 RESUMEN DE SINCRONIZACIÓN:")
        self.stdout.write(f"   • Repuestos sin clon: {total_repuestos}")
        
        # Mostrar algunos repuestos
        self.stdout.write(f"\n🔍 REPUESTOS A SINCRONIZAR:")
        for i, repuesto in enumerate(repuestos_sin_clon[:10]):
            self.stdout.write(f"   {i+1}. {repuesto.nombre} (ID: {repuesto.id})")
            self.stdout.write(f"      - SKU: {repuesto.sku or 'N/A'}")
            self.stdout.write(f"      - Stock: {repuesto.stock}")
            self.stdout.write(f"      - Precio costo: ${repuesto.precio_costo or 0}")
            self.stdout.write(f"      - Precio venta: ${repuesto.precio_venta or 0}")
        
        if total_repuestos > 10:
            self.stdout.write(f"   ... y {total_repuestos - 10} repuestos más")

    def confirmar_sincronizacion(self):
        """Solicita confirmación antes de sincronizar"""
        self.stdout.write(f"\n⚠️  ADVERTENCIA: Se crearán clones en RepuestoEnStock")
        self.stdout.write(f"   Esto sincronizará todos los repuestos faltantes")
        
        respuesta = input("\n¿Continuar con la sincronización? (s/N): ").strip().lower()
        return respuesta in ['s', 'si', 'sí', 'y', 'yes']

    @transaction.atomic
    def sincronizar_repuestos(self, repuestos_sin_clon, deposito):
        """Sincroniza repuestos creando clones en RepuestoEnStock"""
        sincronizados = []
        
        self.stdout.write(f"\n🔄 SINCRONIZANDO REPUESTOS...")
        
        for repuesto in repuestos_sin_clon:
            try:
                # Crear clon en RepuestoEnStock
                repstk = RepuestoEnStock.objects.create(
                    repuesto=repuesto,
                    deposito=deposito,
                    proveedor='',
                    stock=repuesto.stock or 0,
                    reservado=0,
                    precio_compra=repuesto.precio_costo or 0,
                    precio_venta=repuesto.precio_venta or 0
                )
                
                sincronizados.append({
                    'repuesto': repuesto.nombre,
                    'repuesto_id': repuesto.id,
                    'stock_id': repstk.id,
                    'stock': repstk.stock,
                    'precio_compra': repstk.precio_compra,
                    'precio_venta': repstk.precio_venta
                })
                
                self.stdout.write(f"   ✅ {repuesto.nombre} - Clon creado (ID: {repstk.id})")
                
            except Exception as e:
                self.stdout.write(f"   ❌ Error con {repuesto.nombre}: {e}")
        
        return sincronizados

    def mostrar_resultado_final(self, sincronizados):
        """Muestra el resultado final de la sincronización"""
        self.stdout.write(f"\n✅ SINCRONIZACIÓN COMPLETADA")
        self.stdout.write(f"   • Repuestos sincronizados: {len(sincronizados)}")
        
        # Mostrar algunos repuestos sincronizados
        if sincronizados:
            self.stdout.write(f"\n📋 REPUESTOS SINCRONIZADOS:")
            for i, repuesto in enumerate(sincronizados[:10]):
                self.stdout.write(f"   {i+1}. {repuesto['repuesto']} - "
                               f"Stock: {repuesto['stock']}, "
                               f"Precio: ${repuesto['precio_compra']}")
            
            if len(sincronizados) > 10:
                self.stdout.write(f"   ... y {len(sincronizados) - 10} repuestos más")
        
        self.stdout.write(f"\n🎉 ¡Sincronización completada exitosamente!")
        self.stdout.write(f"   Todos los repuestos ahora tienen clon en RepuestoEnStock")







