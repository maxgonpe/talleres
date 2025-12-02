"""
Modelos de punto_venta
"""

from django.db import models
from django.conf import settings
from core.models import Cliente_Taller
from inventario.models import Repuesto, RepuestoEnStock, StockMovimiento


# SesionVenta
class SesionVenta(models.Model):
    """Representa una sesión de venta en el POS"""
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    total_ventas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    numero_ventas = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"Sesión {self.id} - {self.usuario.username} ({self.fecha_inicio.strftime('%d/%m/%Y %H:%M')})"


# CarritoItem
class CarritoItem(models.Model):
    """Items en el carrito de compras del POS"""
    sesion = models.ForeignKey(SesionVenta, on_delete=models.CASCADE, related_name='carrito_items')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    agregado_en = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.repuesto.nombre} x{self.cantidad}"


# VentaPOS
class VentaPOS(models.Model):
    """Ventas realizadas desde el POS"""
    sesion = models.ForeignKey(SesionVenta, on_delete=models.CASCADE, related_name='ventas')
    cliente = models.ForeignKey(Cliente_Taller, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    metodo_pago = models.CharField(max_length=20, choices=(
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("transferencia", "Transferencia"),
        ("mixto", "Mixto"),
    ), default="efectivo")
    pagado = models.BooleanField(default=True)  # En POS siempre se paga al momento
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Venta POS #{self.id} - ${self.total} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"


# VentaPOSItem
class VentaPOSItem(models.Model):
    """Items de una venta POS"""
    venta = models.ForeignKey(VentaPOS, on_delete=models.CASCADE, related_name='items')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # NOTA: El stock se actualiza en la vista POS usando actualizar_stock_venta_pos()
        # para evitar race conditions y problemas de transacciones



# ConfiguracionPOS
class ConfiguracionPOS(models.Model):
    """Configuraciones del sistema POS"""
    nombre_empresa = models.CharField(max_length=100, default="Taller Mecánico")
    direccion = models.TextField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    ruc = models.CharField(max_length=20, blank=True)
    imprimir_ticket = models.BooleanField(default=True)
    mostrar_descuentos = models.BooleanField(default=True)
    permitir_venta_sin_stock = models.BooleanField(default=False)
    margen_ganancia_default = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    
    class Meta:
        verbose_name = "Configuración POS"
        verbose_name_plural = "Configuraciones POS"
    
    def __str__(self):
        return f"Configuración POS - {self.nombre_empresa}"

# SISTEMA DE COTIZACIONES


# Cotizacion
class Cotizacion(models.Model):
    """Cotizaciones del POS (no afectan stock)"""
    sesion = models.ForeignKey(SesionVenta, on_delete=models.CASCADE, related_name='cotizaciones')
    cliente = models.ForeignKey(Cliente_Taller, on_delete=models.SET_NULL, null=True, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True)
    valida_hasta = models.DateField(help_text="Fecha de vencimiento de la cotización")
    estado = models.CharField(max_length=20, choices=(
        ("activa", "Activa"),
        ("vencida", "Vencida"),
        ("convertida", "Convertida a Venta"),
        ("cancelada", "Cancelada"),
    ), default="activa")
    
    def __str__(self):
        return f"Cotización #{self.id} - ${self.total} ({self.fecha.strftime('%d/%m/%Y')})"


# CotizacionItem
class CotizacionItem(models.Model):
    """Items de una cotización"""
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name='items')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        # NO actualiza stock - es solo una cotización
    
    def __str__(self):
        return f"{self.repuesto.nombre} x{self.cantidad}"



# Venta
class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    cliente = models.ForeignKey(Cliente_Taller, null=True, blank=True, on_delete=models.SET_NULL)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pagado = models.BooleanField(default=False)
    metodo_pago = models.CharField(max_length=20, choices=(
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("transferencia", "Transferencia"),
    ), default="efectivo")

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"



# VentaItem
class VentaItem(models.Model):
    venta = models.ForeignKey(Venta, related_name="items", on_delete=models.CASCADE)
    repuesto_stock = models.ForeignKey(RepuestoEnStock, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario)
        super().save(*args, **kwargs)
        
        # NOTA: El stock se actualiza en la vista de venta usando actualizar_stock_venta()
        # para evitar race conditions y problemas de transacciones






