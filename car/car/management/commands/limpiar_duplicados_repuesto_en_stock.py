from django.core.management.base import BaseCommand
from django.db import transaction
from car.models import RepuestoEnStock, Repuesto
from collections import defaultdict


class Command(BaseCommand):
    help = 'Limpia registros duplicados en RepuestoEnStock manteniendo solo el más reciente por repuesto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo muestra qué se eliminaría sin hacer cambios reales',
        )
        parser.add_argument(
            '--deposito',
            type=str,
            default='bodega-principal',
            help='Depósito específico a limpiar (default: bodega-principal)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        deposito = options['deposito']
        
        self.stdout.write("🧹 INICIANDO LIMPIEZA DE DUPLICADOS EN REPUESTOENSTOCK")
        self.stdout.write("=" * 60)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 MODO DRY-RUN: Solo se mostrará qué se eliminaría"))
        
        # Buscar duplicados por repuesto y depósito
        duplicados = self.identificar_duplicados(deposito)
        
        if not duplicados:
            self.stdout.write(self.style.SUCCESS("✅ No se encontraron duplicados"))
            return
        
        # Mostrar resumen de duplicados encontrados
        self.mostrar_resumen_duplicados(duplicados)
        
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY-RUN: No se realizaron cambios"))
            return
        
        # Confirmar antes de eliminar
        if not self.confirmar_eliminacion():
            self.stdout.write(self.style.ERROR("❌ Operación cancelada"))
            return
        
        # Limpiar duplicados
        eliminados = self.limpiar_duplicados(duplicados)
        
        # Mostrar resultado final
        self.mostrar_resultado_final(eliminados)

    def identificar_duplicados(self, deposito):
        """Identifica registros duplicados por repuesto y depósito"""
        self.stdout.write(f"🔍 Buscando duplicados en depósito: {deposito}")
        
        # Obtener todos los registros del depósito
        registros = RepuestoEnStock.objects.filter(deposito=deposito).select_related('repuesto')
        
        # Agrupar por repuesto
        grupos = defaultdict(list)
        for registro in registros:
            grupos[registro.repuesto_id].append(registro)
        
        # Identificar grupos con duplicados
        duplicados = {}
        for repuesto_id, registros_grupo in grupos.items():
            if len(registros_grupo) > 1:
                duplicados[repuesto_id] = registros_grupo
        
        return duplicados

    def mostrar_resumen_duplicados(self, duplicados):
        """Muestra un resumen de los duplicados encontrados"""
        total_duplicados = sum(len(registros) - 1 for registros in duplicados.values())
        total_repuestos = len(duplicados)
        
        self.stdout.write(f"\n📊 RESUMEN DE DUPLICADOS ENCONTRADOS:")
        self.stdout.write(f"   • Repuestos con duplicados: {total_repuestos}")
        self.stdout.write(f"   • Registros duplicados a eliminar: {total_duplicados}")
        
        # Mostrar detalles de algunos duplicados
        self.stdout.write(f"\n🔍 DETALLES DE DUPLICADOS:")
        for i, (repuesto_id, registros) in enumerate(list(duplicados.items())[:5]):
            repuesto = registros[0].repuesto
            self.stdout.write(f"   • {repuesto.nombre} (ID: {repuesto_id})")
            self.stdout.write(f"     - Registros: {len(registros)}")
            for j, registro in enumerate(registros):
                self.stdout.write(f"       {j+1}. ID: {registro.id}, Stock: {registro.stock}, "
                               f"Precio: ${registro.precio_compra}, Proveedor: {registro.proveedor}")
        
        if len(duplicados) > 5:
            self.stdout.write(f"   ... y {len(duplicados) - 5} repuestos más")

    def confirmar_eliminacion(self):
        """Solicita confirmación antes de eliminar"""
        self.stdout.write(f"\n⚠️  ADVERTENCIA: Se eliminarán registros duplicados")
        self.stdout.write(f"   Se mantendrá el registro más reciente de cada repuesto")
        
        respuesta = input("\n¿Continuar con la eliminación? (s/N): ").strip().lower()
        return respuesta in ['s', 'si', 'sí', 'y', 'yes']

    @transaction.atomic
    def limpiar_duplicados(self, duplicados):
        """Elimina registros duplicados manteniendo el más reciente"""
        eliminados = []
        
        self.stdout.write(f"\n🧹 ELIMINANDO DUPLICADOS...")
        
        for repuesto_id, registros in duplicados.items():
            repuesto = registros[0].repuesto
            
            # Ordenar por ID (el más reciente es el de mayor ID)
            registros_ordenados = sorted(registros, key=lambda x: x.id)
            
            # Mantener el último (más reciente) y eliminar los anteriores
            registro_mantener = registros_ordenados[-1]
            registros_eliminar = registros_ordenados[:-1]
            
            self.stdout.write(f"   🔧 {repuesto.nombre}:")
            self.stdout.write(f"     - Manteniendo: ID {registro_mantener.id} (Stock: {registro_mantener.stock})")
            
            for registro in registros_eliminar:
                self.stdout.write(f"     - Eliminando: ID {registro.id} (Stock: {registro.stock})")
                eliminados.append({
                    'repuesto': repuesto.nombre,
                    'registro_id': registro.id,
                    'stock': registro.stock,
                    'precio': registro.precio_compra,
                    'proveedor': registro.proveedor
                })
                registro.delete()
        
        return eliminados

    def mostrar_resultado_final(self, eliminados):
        """Muestra el resultado final de la limpieza"""
        self.stdout.write(f"\n✅ LIMPIEZA COMPLETADA")
        self.stdout.write(f"   • Registros eliminados: {len(eliminados)}")
        
        # Mostrar algunos registros eliminados
        if eliminados:
            self.stdout.write(f"\n📋 REGISTROS ELIMINADOS:")
            for i, registro in enumerate(eliminados[:10]):
                self.stdout.write(f"   {i+1}. {registro['repuesto']} - "
                               f"ID: {registro['registro_id']}, "
                               f"Stock: {registro['stock']}, "
                               f"Precio: ${registro['precio']}, "
                               f"Proveedor: {registro['proveedor']}")
            
            if len(eliminados) > 10:
                self.stdout.write(f"   ... y {len(eliminados) - 10} registros más")
        
        self.stdout.write(f"\n🎉 ¡Limpieza completada exitosamente!")
        self.stdout.write(f"   Ahora cada repuesto tiene un solo registro en RepuestoEnStock")







