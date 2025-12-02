"""
Modelos de inventario
"""

from django.db import models
from django.db.models import Sum
from django.conf import settings
from decimal import Decimal
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from core.models import Componente, VehiculoVersion


# Repuesto
class Repuesto(models.Model):
    sku = models.CharField(max_length=64, unique=True, blank=True, null=True)  # código interno
    oem = models.CharField(max_length=64, blank=True, null=True, default='oem')               # OEM / fabricante
    referencia = models.CharField(max_length=128, blank=True, null=True, default='no-tiene')       # ref proveedor
    nombre = models.CharField(max_length=250)
    marca = models.CharField(max_length=120, blank=True, default='general')
    descripcion = models.TextField(blank=True)
    medida = models.CharField(max_length=80, blank=True)   # ej. "258x22mm"
    posicion = models.CharField(max_length=80, blank=True) # ej. "freno delantero"
    unidad = models.CharField(max_length=20, default='pieza')
    precio_costo = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    codigo_barra = models.CharField(max_length=100, blank=True, null=True, unique=True)
    stock = models.IntegerField(default=0)  # Mantener para compatibilidad con datos existentes
    created = models.DateTimeField(auto_now_add=True)
    
    # Nuevos campos con nombres diferentes y valores por defecto
    origen_repuesto = models.CharField(max_length=100, blank=True, null=True, default='sin-origen', verbose_name="Origen del Repuesto")
    cod_prov = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código Proveedor")
    marca_veh = models.CharField(max_length=100, blank=True, null=True, default='xxx', verbose_name="Marca Vehículo")
    tipo_de_motor = models.TextField(blank=True, null=True, default='zzzzzz', verbose_name="Tipo de Motor")
    carroceria = models.CharField(max_length=100, blank=True, null=True, default='yyyyyy', verbose_name="Carrocería")

    
    def save(self, *args, **kwargs):
        # Generar SKU si no existe
        if not self.sku:
            self.sku = self.generate_sku()
        else:
            # Verificar si los campos relevantes han cambiado
            if self.pk:  # Solo para objetos existentes
                try:
                    old_instance = Repuesto.objects.get(pk=self.pk)
                    # Campos que afectan la generación del SKU
                    campos_relevantes = ['nombre', 'marca_veh', 'tipo_de_motor']
                    
                    # Verificar si algún campo relevante cambió
                    if any(getattr(self, campo) != getattr(old_instance, campo) for campo in campos_relevantes):
                        # Solo regenerar SKU automáticamente si el SKU actual parece generado automáticamente
                        # (contiene el patrón de generación automática)
                        if self._is_auto_generated_sku(self.sku):
                            self.sku = self.generate_sku()
                except Repuesto.DoesNotExist:
                    # Si no existe el objeto anterior, generar SKU
                    self.sku = self.generate_sku()
            else:
                # Para objetos nuevos, generar SKU
                self.sku = self.generate_sku()
        
        super().save(*args, **kwargs)
    
    def _is_auto_generated_sku(self, sku):
        """Verifica si un SKU fue generado automáticamente por el sistema"""
        if not sku:
            return False
        
        # Patrón: NOMBRE-MARCA-MOTOR-NUMERO (ej: ACEIT-XXXX-ZZZZZZ-1234)
        parts = sku.split('-')
        if len(parts) != 4:
            return False
        
        # Verificar que el último segmento sea numérico (4 dígitos)
        try:
            int(parts[3])
            return len(parts[3]) == 4
        except ValueError:
            return False

    def generate_sku(self):
        # 1. Primeros 5 caracteres del nombre
        nombre_part = (self.nombre[:5].upper() if self.nombre else "REPUE")
        
        # 2. Primeros 4 caracteres de marca_veh (mejorar detección de valores por defecto)
        marca_veh_part = "XXXX"  # Valor por defecto
        if self.marca_veh and self.marca_veh.lower() not in ['xxx', 'xxxx', '']:
            marca_veh_part = self.marca_veh[:4].upper()
        
        # 3. Primer grupo de tipo_de_motor (6-7 caracteres)
        tipo_motor_part = "ZZZZZZ"  # Valor por defecto
        
        if self.tipo_de_motor and self.tipo_de_motor.lower() not in ['zzzzzz', 'zzzz', '']:
            # Tomar el primer grupo antes del primer guión
            primer_grupo = self.tipo_de_motor.split(' - ')[0].strip()
            if primer_grupo and primer_grupo.lower() not in ['zzzzzz', 'zzzz']:
                # Limitar a 6-7 caracteres máximo
                tipo_motor_part = primer_grupo[:7].upper()
                # Si es muy corto, rellenar con 'Z'
                if len(tipo_motor_part) < 6:
                    tipo_motor_part = tipo_motor_part.ljust(6, 'Z')
        
        # 4. Número aleatorio de 4 dígitos
        numero_aleatorio = get_random_string(length=4, allowed_chars="0123456789")
        
        # Formato final: NOMBRE-MARCA-MOTOR-NUMERO
        return f"{nombre_part}-{marca_veh_part}-{tipo_motor_part}-{numero_aleatorio}"

    def __str__(self):
        return f"{self.nombre} ({self.sku or self.oem or 'sin-cod'})"
    
    @property
    def stock_total(self):
        """Obtiene el stock total - SIEMPRE desde la tabla maestra Repuesto"""
        return self.stock or 0
    
    @property
    def stock_disponible(self):
        """Obtiene el stock disponible (total - reservado)"""
        from django.db.models import Sum
        total_reservado = self.stocks.aggregate(total=Sum('reservado'))['total'] or 0
        return self.stock_total - total_reservado
    
    def tiene_stock_suficiente(self, cantidad):
        """Verifica si hay stock suficiente para la cantidad solicitada"""
        return self.stock_disponible >= cantidad
    
    def actualizar_stock_y_precio(self, cantidad_entrada, precio_compra, precio_venta_nuevo=None, proveedor=''):
        """
        Actualiza stock y precio usando promedio ponderado con factor de margen automático
        
        Args:
            cantidad_entrada: Cantidad que se está agregando
            precio_compra: Precio de compra de la nueva mercancía
            precio_venta_nuevo: Precio de venta nuevo (opcional, si no se proporciona se calcula automáticamente)
            proveedor: Nombre del proveedor (opcional)
        
        Returns:
            dict: Información del cambio realizado
        """
        from decimal import Decimal
        
        # Stock y precios actuales
        stock_anterior = self.stock or 0
        precio_venta_anterior = self.precio_venta or Decimal('0')
        precio_costo_anterior = self.precio_costo or Decimal('0')
        
        # Calcular nuevo stock
        nuevo_stock = stock_anterior + cantidad_entrada
        
        # El precio de compra es literal (no promedio ponderado)
        nuevo_precio_costo = precio_compra
        
        # Calcular precio de venta usando factor de margen
        if precio_venta_nuevo is not None:
            # Si se proporciona precio de venta específico, usarlo
            nuevo_precio_venta = precio_venta_nuevo
        elif stock_anterior > 0 and precio_venta_anterior > 0 and precio_costo_anterior > 0:
            # Calcular factor de margen del producto existente
            factor_margen = precio_venta_anterior / precio_costo_anterior
            
            # Aplicar el mismo factor al nuevo precio de costo
            nuevo_precio_venta = nuevo_precio_costo * factor_margen
        else:
            # Producto nuevo o sin datos anteriores: usar margen del 30% por defecto
            nuevo_precio_venta = nuevo_precio_costo * Decimal('1.3')
        
        # Actualizar el repuesto
        self.stock = nuevo_stock
        self.precio_costo = nuevo_precio_costo
        self.precio_venta = nuevo_precio_venta
        self.save()
        
        # Sincronizar con RepuestoEnStock
        self._sincronizar_con_stock_detallado(cantidad_entrada, precio_compra, proveedor)
        
        return {
            'stock_anterior': stock_anterior,
            'stock_nuevo': nuevo_stock,
            'precio_costo_anterior': float(precio_costo_anterior),
            'precio_costo_nuevo': float(nuevo_precio_costo),
            'precio_venta_anterior': float(precio_venta_anterior),
            'precio_venta_nuevo': float(nuevo_precio_venta),
            'cantidad_agregada': cantidad_entrada,
            'factor_margen_aplicado': float(nuevo_precio_venta / nuevo_precio_costo) if nuevo_precio_costo > 0 else 0
        }
    
    def _sincronizar_con_stock_detallado(self, cantidad_entrada, precio_compra, proveedor=''):
        """Sincroniza con RepuestoEnStock para mantener consistencia"""
        # 🔥 SIMPLIFICADO: Buscar SOLO por repuesto y depósito (sin proveedor como clave)
        # Esto evita crear múltiples registros por proveedor
        
        # Primero, eliminar cualquier registro duplicado existente
        registros_existentes = RepuestoEnStock.objects.filter(
            repuesto=self,
            deposito='bodega-principal'
        )
        
        if registros_existentes.count() > 1:
            print(f"⚠️ Encontrados {registros_existentes.count()} registros duplicados para {self.nombre}")
            # Mantener solo el más reciente y eliminar los duplicados
            registro_principal = registros_existentes.order_by('-id').first()
            registros_duplicados = registros_existentes.exclude(id=registro_principal.id)
            print(f"🗑️ Eliminando {registros_duplicados.count()} duplicados...")
            registros_duplicados.delete()
        
        # 🔥 CAMBIO CLAVE: get_or_create solo por repuesto y deposito (no incluir proveedor)
        stock_principal, created = RepuestoEnStock.objects.get_or_create(
            repuesto=self,
            deposito='bodega-principal',
            defaults={
                'stock': 0,
                'reservado': 0,
                'precio_compra': precio_compra,
                'precio_venta': self.precio_venta,
                'proveedor': proveedor  # Lo guardamos, pero no es clave de búsqueda
            }
        )
        
        if created:
            print(f"✅ Creado nuevo registro RepuestoEnStock para {self.nombre}")
        
        # Actualizar el stock detallado para que coincida con el stock maestro
        stock_principal.stock = self.stock
        stock_principal.precio_compra = self.precio_costo
        stock_principal.precio_venta = self.precio_venta
        # Actualizar proveedor si viene uno nuevo (pero sin crear registro duplicado)
        if proveedor:
            stock_principal.proveedor = proveedor
        stock_principal.save()
        
        print(f"🔄 Stock sincronizado: Repuesto.stock={self.stock} → RepuestoEnStock.stock={stock_principal.stock}")





# RepuestoEnStock
class RepuestoEnStock(models.Model):
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name='stocks')
    deposito = models.CharField(max_length=80, default='bodega-principal')  # o FK a un modelo Deposito
    proveedor = models.CharField(max_length=120, blank=True)  # info del proveedor
    stock = models.IntegerField(default=0)
    reservado = models.IntegerField(default=0)  # cantidad reservada por diagnósticos pendientes
    precio_compra = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # en este sitio
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("repuesto", "deposito", "proveedor")

    @property
    def disponible(self):
        return self.stock - (self.reservado or 0)

    def __str__(self):
        return f"{self.repuesto.nombre} (Stock: {self.stock})" 


# StockMovimiento
class StockMovimiento(models.Model):
    repuesto_stock = models.ForeignKey(RepuestoEnStock, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=(('ingreso','ingreso'),('salida','salida'),('reserva','reserva'),('liberacion','liberacion')))
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=200, blank=True)
    referencia = models.CharField(max_length=120, blank=True)  # ej ODT/DIAG id
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateTimeField(auto_now_add=True)


# RepuestoExterno
class RepuestoExterno(models.Model):
    """
    Referencias de repuestos de proveedores externos.
    No están en inventario, pero se pueden referenciar en diagnósticos y trabajos.
    """
    PROVEEDOR_CHOICES = [
        ('mundo_repuestos', '🛒 Mundo Repuestos'),
        ('autoplanet', '🚗 AutoPlanet'),
        ('otro', '📦 Otro Proveedor'),
    ]
    
    # Información básica
    nombre = models.CharField(max_length=255, help_text="Nombre del repuesto")
    proveedor = models.CharField(max_length=50, choices=PROVEEDOR_CHOICES, default='otro')
    proveedor_nombre = models.CharField(max_length=100, blank=True, null=True, help_text="Si es 'otro', especificar nombre")
    codigo_proveedor = models.CharField(max_length=100, blank=True, null=True, help_text="SKU o código del proveedor")
    
    # Precio y disponibilidad
    precio_referencial = models.DecimalField(max_digits=10, decimal_places=0, help_text="Precio de referencia en pesos")
    url_producto = models.URLField(max_length=500, blank=True, null=True, help_text="Link directo al producto")
    
    # Información adicional
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción o notas adicionales")
    marca = models.CharField(max_length=100, blank=True, null=True)
    
    # Compatibilidad
    vehiculos_compatibles = models.ManyToManyField('core.Vehiculo', blank=True, related_name='repuestos_externos_compatibles')
    
    # Metadata
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='repuestos_externos_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True, help_text="Desactivar si ya no está disponible")
    
    # Estadísticas de uso
    veces_usado = models.IntegerField(default=0, help_text="Contador de veces que se ha referenciado")
    
    class Meta:
        verbose_name = "Repuesto Externo"
        verbose_name_plural = "Repuestos Externos"
        ordering = ['-veces_usado', '-fecha_creacion']
    
    def __str__(self):
        proveedor_display = self.get_proveedor_display() if self.proveedor != 'otro' else self.proveedor_nombre
        return f"{self.nombre} - {proveedor_display}"
    
    def incrementar_uso(self):
        """Incrementa el contador de uso"""
        self.veces_usado += 1
        self.save(update_fields=['veces_usado'])
    
    def get_url_busqueda(self):
        """Genera URL de búsqueda en el proveedor si no hay URL directa"""
        if self.url_producto:
            return self.url_producto
        
        termino = self.nombre
        
        if self.proveedor == 'mundo_repuestos':
            termino_formateado = termino.replace(' ', '--')
            return f"https://mundorepuestos.com/busqueda/{termino_formateado}"
        elif self.proveedor == 'autoplanet':
            from urllib.parse import quote
            return f"https://www.autoplanet.cl/busqueda/{quote(termino)}"
        
        return "#"


# SISTEMA DE AUDITORÍA Y REGISTRO DE EVENTOS
# Este modelo registra todos los eventos importantes del sistema
# de forma independiente para análisis histórico, estadísticas
# y rastreo de movimientos, incluso si los registros originales
# son eliminados.


# ComponenteRepuesto
class ComponenteRepuesto(models.Model):
    componente = models.ForeignKey('core.Componente', on_delete=models.CASCADE)  # tu modelo de componente
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    nota = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("componente", "repuesto")


# RepuestoAplicacion
class RepuestoAplicacion(models.Model):
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name="aplicaciones")
    version = models.ForeignKey(VehiculoVersion, on_delete=models.CASCADE)
    posicion = models.CharField(max_length=80, blank=True)  # opcional, sinon usar repuesto.posicion
    motor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Motor")
    carroceria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Carrocería")

    class Meta:
        unique_together = ("repuesto", "version")



