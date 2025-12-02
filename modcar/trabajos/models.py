"""
Modelos de trabajos
"""

from django.db import models
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings
from core.models import Vehiculo, Componente
from diagnosticos.models import Diagnostico
from inventario.models import Repuesto, RepuestoExterno
from usuarios.models import Mecanico


# Trabajo
class Trabajo(models.Model):
    ESTADOS = [
        ("iniciado", "Iniciado"),
        ("trabajando", "Trabajando"),
        ("completado", "Completado"),
        ("entregado", "Entregado"),
    ]

    diagnostico = models.OneToOneField(Diagnostico, on_delete=models.CASCADE, related_name="trabajo")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="iniciado")
    observaciones = models.TextField(blank=True, null=True)
    lectura_kilometraje_actual = models.IntegerField(null=True, blank=True, verbose_name="Kilometraje Actual", help_text="Lectura del kilometraje al ingresar el vehículo")
    mecanicos = models.ManyToManyField("usuarios.Mecanico", related_name="trabajos", blank=True)
    visible = models.BooleanField(default=True, verbose_name="Visible", help_text="Indica si el trabajo debe mostrarse en las listas")

    # 🔹 Nuevo: relacionar con componentes (igual que Diagnostico)
    componentes = models.ManyToManyField("core.Componente", related_name="trabajos", blank=True)

    def __str__(self):
        return f"Trabajo #{self.id} - {self.vehiculo}"

    # TOTALES PRESUPUESTADOS (TODO)
    @property
    def total_mano_obra(self):
        """Total de mano de obra presupuestada (TODAS las acciones, considerando cantidad)"""
        return sum(a.subtotal for a in self.acciones.all())

    @property
    def total_repuestos(self):
        """Total de repuestos presupuestados (TODOS los repuestos)"""
        return sum(r.subtotal or 0 for r in self.repuestos.all())

    @property
    def total_adicionales(self):
        """Total de conceptos adicionales agregados al trabajo (solo los que NO son descuentos)"""
        return sum(ad.monto for ad in self.adicionales.filter(descuento=False))

    @property
    def total_descuentos(self):
        """Total de descuentos aplicados al trabajo"""
        return sum(ad.monto for ad in self.adicionales.filter(descuento=True))

    @property
    def total_general(self):
        """Total presupuestado completo (TODO el trabajo) - descuentos"""
        return self.total_mano_obra + self.total_repuestos + self.total_adicionales - self.total_descuentos
    
    # Alias para mayor claridad
    @property
    def total_presupuesto(self):
        """Alias de total_general - Total presupuestado"""
        return self.total_general

    # TOTALES REALIZADOS (COMPLETADOS)
    @property
    def total_realizado_mano_obra(self):
        """Total de mano de obra REALIZADA (solo acciones completadas, considerando cantidad)"""
        return sum(
            a.subtotal 
            for a in self.acciones.filter(completado=True)
        )
    
    @property
    def total_realizado_repuestos(self):
        """Total de repuestos INSTALADOS (solo repuestos completados)"""
        return sum(
            r.subtotal or 0 
            for r in self.repuestos.filter(completado=True)
        )
    
    @property
    def total_realizado_adicionales(self):
        """Total de conceptos adicionales realizados (solo los que NO son descuentos)"""
        return sum(ad.monto for ad in self.adicionales.filter(descuento=False))
    
    @property
    def total_realizado_descuentos(self):
        """Total de descuentos aplicados (siempre se consideran realizados)"""
        return sum(ad.monto for ad in self.adicionales.filter(descuento=True))
    
    @property
    def total_realizado(self):
        """Total de trabajo REALIZADO hasta el momento - descuentos"""
        return self.total_realizado_mano_obra + self.total_realizado_repuestos + self.total_realizado_adicionales - self.total_realizado_descuentos

    # ABONOS Y SALDOS
    @property
    def total_abonos(self):
        """Total de abonos/pagos parciales recibidos"""
        return sum(abono.monto for abono in self.abonos.all())
    
    @property
    def saldo_pendiente(self):
        """Saldo que falta por cobrar (Total Realizado - Abonos)"""
        return self.total_realizado - self.total_abonos
    
    @property
    def saldo_presupuesto(self):
        """Diferencia entre lo presupuestado y lo realizado"""
        return self.total_presupuesto - self.total_realizado

    # PORCENTAJE DE AVANCE
    @property
    def porcentaje_avance(self):
        """Porcentaje de avance basado en items completados"""
        acciones_total = self.acciones.count()
        repuestos_total = self.repuestos.count()
        total_items = acciones_total + repuestos_total

        if total_items == 0:
            return 0  # nada registrado

        acciones_completadas = self.acciones.filter(completado=True).count()
        repuestos_instalados = self.repuestos.filter(completado=True).count()
        completados = acciones_completadas + repuestos_instalados

        return int((completados / total_items) * 100)
    
    @property
    def porcentaje_cobrado(self):
        """Porcentaje cobrado del total realizado"""
        if self.total_realizado == 0:
            return 0
        return int((self.total_abonos / self.total_realizado) * 100)
    
    # DÍAS EN EL TALLER
    @property
    def dias_en_taller(self):
        """
        Calcula cuántos días ha estado el vehículo en el taller.
        Si está entregado, cuenta hasta fecha_fin.
        Si no está entregado, cuenta hasta hoy.
        """
        from django.utils import timezone
        from datetime import datetime
        
        if not self.fecha_inicio:
            return 0
        
        # Si está entregado, usar fecha_fin
        if self.estado == 'entregado' and self.fecha_fin:
            fecha_final = self.fecha_fin
        else:
            # Si no está entregado, usar fecha actual
            fecha_final = timezone.now()
        
        # Calcular diferencia en días
        diferencia = fecha_final - self.fecha_inicio
        return diferencia.days
    
    @property
    def dias_en_taller_texto(self):
        """
        Retorna el texto formateado de días en taller con su clase CSS
        """
        dias = self.dias_en_taller
        
        # Determinar el texto
        if dias == 0:
            texto = "Hoy"
        elif dias == 1:
            texto = "1 día"
        else:
            texto = f"{dias} días"
        
        # Determinar la clase CSS según el rango de días
        if self.estado == 'entregado':
            css_class = "entregado"
        elif dias <= 3:
            css_class = "pocos"
        elif dias <= 7:
            css_class = "medios"
        else:
            css_class = "muchos"
        
        return {
            'texto': texto,
            'css_class': css_class
        }


# TrabajoAccion
class TrabajoAccion(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="acciones")
    componente = models.ForeignKey("core.Componente", on_delete=models.CASCADE)
    accion = models.ForeignKey("core.Accion", on_delete=models.CASCADE)
    precio_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Unitario")
    cantidad = models.IntegerField(default=1, verbose_name="Cantidad", help_text="Número de veces que se realizará esta acción (ej: cambiar 4 bujías)")
    completado = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True, blank=True)

    @property
    def subtotal(self):
        """Calcula el subtotal: precio unitario * cantidad"""
        return self.precio_mano_obra * self.cantidad

    #def __str__(self):
    #    return f"{self.trabajo} - {self.accion.nombre} {self.componente.nombre}"
    @property
    def costo(self):
        return self.accion.costo if self.completado else 0

    def __str__(self):
        if self.cantidad > 1:
            return f"{self.accion} (x{self.cantidad}) ({'✔️' if self.completado else 'pendiente'})"
        return f"{self.accion} ({'✔️' if self.completado else 'pendiente'})"



# TrabajoRepuesto
class TrabajoRepuesto(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="repuestos")
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, null=True, blank=True)
    repuesto = models.ForeignKey("inventario.Repuesto", on_delete=models.PROTECT, null=True, blank=True)  # Ahora puede ser NULL
    repuesto_externo = models.ForeignKey('inventario.RepuestoExterno', on_delete=models.SET_NULL, null=True, blank=True, related_name='trabajos')  # NUEVO
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    completado = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.repuesto_externo:
            return f"🌐 {self.repuesto_externo.nombre} (x{self.cantidad})"
        elif self.repuesto:
            return f"{self.repuesto} (x{self.cantidad})"
        return f"Repuesto (x{self.cantidad})"



# TrabajoAbono
class TrabajoAbono(models.Model):
    """
    Modelo para registrar abonos/pagos parciales del cliente
    mientras el vehículo está en el taller
    """
    METODOS_PAGO = [
        ("efectivo", "Efectivo"),
        ("tarjeta", "Tarjeta"),
        ("transferencia", "Transferencia"),
        ("cheque", "Cheque"),
        ("otro", "Otro"),
    ]
    
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="abonos")
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo_pago = models.CharField(max_length=20, choices=METODOS_PAGO, default="efectivo")
    descripcion = models.TextField(blank=True, null=True, help_text="Descripción o nota del abono")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que registró el abono"
    )
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Abono de Trabajo"
        verbose_name_plural = "Abonos de Trabajos"
    
    def __str__(self):
        return f"Abono ${self.monto} - {self.get_metodo_pago_display()} - {self.fecha.strftime('%d/%m/%Y')}"



# TrabajoAdicional
class TrabajoAdicional(models.Model):
    """
    Modelo para registrar conceptos adicionales al trabajo
    (servicios extra, materiales adicionales, etc.)
    que se suman al total del trabajo.
    Si descuento=True, el monto se resta en lugar de sumar.
    """
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="adicionales")
    concepto = models.TextField(verbose_name="Concepto", help_text="Descripción del concepto adicional")
    monto = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    descuento = models.BooleanField(default=False, verbose_name="Es Descuento", help_text="Si está marcado, este monto se restará del total en lugar de sumarlo")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True,
        verbose_name="Usuario",
        help_text="Usuario que registró el concepto adicional"
    )
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Concepto Adicional"
        verbose_name_plural = "Conceptos Adicionales"
    
    def __str__(self):
        tipo = "Descuento" if self.descuento else "Adicional"
        return f"{tipo}: {self.concepto[:50]} - ${self.monto} - {self.fecha.strftime('%d/%m/%Y')}"


# ventas/models.py  (puedes ponerlo en la app extintores o crear app nueva "ventas")


# TrabajoFoto
class TrabajoFoto(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="trabajos/fotos/%Y/%m/%d")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto {self.id} de {self.trabajo}"




