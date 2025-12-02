"""
Modelos de compras
"""

from django.db import models
from django.conf import settings
from django.utils.timezone import now
from inventario.models import Repuesto, RepuestoEnStock, StockMovimiento


# Compra
class Compra(models.Model):
    """Modelo para registrar compras de repuestos"""
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_compra = models.CharField(max_length=20, unique=True, blank=True)
    proveedor = models.CharField(max_length=200, help_text="Nombre del proveedor")
    fecha_compra = models.DateField(default=now)
    fecha_recibida = models.DateField(null=True, blank=True, help_text="Fecha cuando se recibió la mercancía")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, help_text="Observaciones sobre la compra")
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_compra', '-creado_en']
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
    
    def __str__(self):
        return f"Compra #{self.numero_compra} - {self.proveedor}"
    
    def save(self, *args, **kwargs):
        if not self.numero_compra:
            # Generar número de compra automático
            from django.db.models import Max
            
            # Obtener el último número de compra
            ultimo_numero = Compra.objects.aggregate(
                max_numero=Max('numero_compra')
            )['max_numero']
            
            if ultimo_numero:
                try:
                    # Extraer el número del formato COMP-0001
                    numero_actual = int(ultimo_numero.split('-')[-1])
                    nuevo_numero = numero_actual + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            
            # Generar el número de compra
            self.numero_compra = f"COMP-{nuevo_numero:04d}"
        
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Calcula el total de la compra sumando todos los items"""
        total = self.items.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        )['total'] or 0
        self.total = total
        self.save(update_fields=['total'])
        return total



# CompraItem
class CompraItem(models.Model):
    """Items de una compra"""
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='items')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(help_text="Cantidad comprada")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio por unidad")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cantidad × Precio unitario")
    recibido = models.BooleanField(default=False, help_text="¿Ya se recibió este item?")
    fecha_recibido = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Item de Compra"
        verbose_name_plural = "Items de Compra"
        unique_together = ['compra', 'repuesto']
    
    def __str__(self):
        return f"{self.repuesto.nombre} - {self.cantidad} unidades"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar total de la compra
        self.compra.calcular_total()
    
    def recibir_item(self, usuario=None):
        """Marca el item como recibido y actualiza el stock usando precio promedio ponderado"""
        if not self.recibido:
            print(f"\n{'='*80}")
            print(f"📦 RECIBIENDO COMPRA - Item: {self.repuesto.nombre} x{self.cantidad}")
            print(f"{'='*80}")
            
            self.recibido = True
            self.fecha_recibido = now()
            self.save()
            print(f"✅ Item marcado como recibido")
            
            # Actualizar stock del repuesto usando el nuevo sistema unificado
            repuesto = self.repuesto
            print(f"📊 Stock ANTES de actualizar:")
            print(f"   - Repuesto.stock: {repuesto.stock}")
            
            # Usar el nuevo método de actualización con precio promedio ponderado
            # Este método YA sincroniza con RepuestoEnStock internamente
            resultado = repuesto.actualizar_stock_y_precio(
                cantidad_entrada=self.cantidad,
                precio_compra=self.precio_unitario,
                proveedor=self.compra.proveedor
            )
            
            print(f"📊 Stock DESPUÉS de actualizar:")
            print(f"   - Stock anterior: {resultado['stock_anterior']}")
            print(f"   - Stock nuevo: {resultado['stock_nuevo']}")
            print(f"   - Precio costo: ${resultado['precio_costo_nuevo']}")
            print(f"   - Precio venta: ${resultado['precio_venta_nuevo']}")
            
            # Crear movimiento de stock para auditoría
            # 🔥 SIMPLIFICADO: Solo buscar por repuesto y deposito (ya sincronizado arriba)
            stock_principal = RepuestoEnStock.objects.filter(
                repuesto=self.repuesto,
                deposito='bodega-principal'
            ).first()
            
            if stock_principal:
                StockMovimiento.objects.create(
                    repuesto_stock=stock_principal,
                    tipo='entrada',
                    cantidad=self.cantidad,
                    motivo=f'Compra #{self.compra.numero_compra}',
                    referencia=f'COMPRA-{self.compra.id}',
                    usuario=usuario
                )
                print(f"📝 Movimiento de stock registrado")
            else:
                print(f"⚠️ No se encontró RepuestoEnStock para registrar movimiento")
            
            print(f"{'='*80}\n")


# REPUESTOS EXTERNOS (REFERENCIAS)





