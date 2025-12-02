"""
Modelos de bonos
"""

from django.db import models
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings
from django.utils.timezone import now
from django.contrib.auth.models import User
from usuarios.models import Mecanico
from trabajos.models import Trabajo


# ConfiguracionBonoMecanico
class ConfiguracionBonoMecanico(models.Model):
    """
    Configuración de bonos por mecánico.
    Permite definir bonos por porcentaje o cantidad fija.
    El administrador puede activar/desactivar bonos por mecánico.
    """
    TIPO_BONO_CHOICES = [
        ('porcentaje', 'Porcentaje de Mano de Obra'),
        ('fijo', 'Cantidad Fija'),
    ]
    
    mecanico = models.OneToOneField(
        Mecanico, 
        on_delete=models.CASCADE, 
        related_name='configuracion_bono',
        verbose_name="Mecánico"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Bonos Activos",
        help_text="Si está desactivado, este mecánico no recibirá bonos automáticos"
    )
    tipo_bono = models.CharField(
        max_length=20,
        choices=TIPO_BONO_CHOICES,
        default='porcentaje',
        verbose_name="Tipo de Bono"
    )
    porcentaje_mano_obra = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name="Porcentaje (%)",
        help_text="Porcentaje de la mano de obra del trabajo (ej: 10.00 = 10%)",
        null=True,
        blank=True
    )
    cantidad_fija = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Cantidad Fija",
        help_text="Cantidad fija a pagar por cada trabajo entregado",
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre esta configuración"
    )
    
    class Meta:
        verbose_name = "Configuración de Bono por Mecánico"
        verbose_name_plural = "Configuraciones de Bonos por Mecánico"
        ordering = ['mecanico__user__first_name', 'mecanico__user__last_name']
    
    def __str__(self):
        tipo = "Porcentaje" if self.tipo_bono == 'porcentaje' else "Fijo"
        estado = "Activo" if self.activo else "Inactivo"
        return f"{self.mecanico} - {tipo} ({estado})"
    
    def calcular_bono(self, total_mano_obra):
        """
        Calcula el bono basado en la configuración y el total de mano de obra.
        """
        if not self.activo:
            return Decimal('0')
        
        if self.tipo_bono == 'porcentaje':
            if self.porcentaje_mano_obra:
                return (total_mano_obra * self.porcentaje_mano_obra) / Decimal('100')
        elif self.tipo_bono == 'fijo':
            return self.cantidad_fija or Decimal('0')
        
        return Decimal('0')



# ExcepcionBonoTrabajo
class ExcepcionBonoTrabajo(models.Model):
    """
    Permite excluir trabajos específicos del sistema de bonos.
    Útil cuando el administrador decide que un trabajo no debe generar bonos.
    """
    trabajo = models.OneToOneField(
        Trabajo,
        on_delete=models.CASCADE,
        related_name='excepcion_bono',
        verbose_name="Trabajo"
    )
    motivo = models.TextField(
        verbose_name="Motivo de la Excepción",
        help_text="Razón por la cual este trabajo no genera bonos"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Creado por"
    )
    
    class Meta:
        verbose_name = "Excepción de Bono por Trabajo"
        verbose_name_plural = "Excepciones de Bonos por Trabajo"
        ordering = ['-fecha_creacion']
    
    def __str__(self):
        return f"Excepción - Trabajo #{self.trabajo.id}"



# BonoGenerado
class BonoGenerado(models.Model):
    """
    Historial de bonos generados cuando se entrega un trabajo.
    Representa el saldo a favor del mecánico.
    """
    mecanico = models.ForeignKey(
        Mecanico,
        on_delete=models.CASCADE,
        related_name='bonos_generados',
        verbose_name="Mecánico"
    )
    trabajo = models.ForeignKey(
        Trabajo,
        on_delete=models.CASCADE,
        related_name='bonos_generados',
        verbose_name="Trabajo"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto del Bono"
    )
    tipo_bono = models.CharField(
        max_length=20,
        choices=ConfiguracionBonoMecanico.TIPO_BONO_CHOICES,
        verbose_name="Tipo de Bono"
    )
    porcentaje_aplicado = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Porcentaje Aplicado (%)"
    )
    total_mano_obra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Total Mano de Obra del Trabajo"
    )
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    pagado = models.BooleanField(
        default=False,
        verbose_name="Pagado",
        help_text="Indica si este bono ya fue pagado"
    )
    fecha_pago = models.DateTimeField(null=True, blank=True)
    notas = models.TextField(blank=True, null=True, verbose_name="Notas")
    
    class Meta:
        verbose_name = "Bono Generado"
        verbose_name_plural = "Bonos Generados"
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['mecanico', 'pagado']),
            models.Index(fields=['fecha_generacion']),
        ]
    
    def __str__(self):
        estado = "Pagado" if self.pagado else "Pendiente"
        return f"Bono {self.mecanico} - Trabajo #{self.trabajo.id} - ${self.monto} ({estado})"



# PagoMecanico
class PagoMecanico(models.Model):
    """
    Registro de pagos realizados a mecánicos.
    Estos pagos descuentan del saldo pendiente del mecánico.
    """
    METODOS_PAGO = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('cheque', 'Cheque'),
        ('otro', 'Otro'),
    ]
    
    mecanico = models.ForeignKey(
        Mecanico,
        on_delete=models.CASCADE,
        related_name='pagos',
        verbose_name="Mecánico"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Monto Pagado"
    )
    metodo_pago = models.CharField(
        max_length=20,
        choices=METODOS_PAGO,
        default='efectivo',
        verbose_name="Método de Pago"
    )
    fecha_pago = models.DateTimeField(
        default=now,
        verbose_name="Fecha de Pago"
    )
    bonos_aplicados = models.ManyToManyField(
        BonoGenerado,
        related_name='pagos',
        verbose_name="Bonos Aplicados",
        help_text="Bonos que se están pagando con este pago"
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas adicionales sobre este pago"
    )
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Registrado por"
    )
    
    class Meta:
        verbose_name = "Pago a Mecánico"
        verbose_name_plural = "Pagos a Mecánicos"
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['mecanico', 'fecha_pago']),
        ]
    
    def __str__(self):
        return f"Pago {self.mecanico} - ${self.monto} - {self.fecha_pago.strftime('%d/%m/%Y')}"
    
    def save(self, *args, **kwargs):
        """
        Al guardar un pago, marca los bonos aplicados como pagados.
        """
        super().save(*args, **kwargs)
        
        # Marcar bonos como pagados
        if self.pk:
            bonos = self.bonos_aplicados.all()
            for bono in bonos:
                bono.pagado = True
                bono.fecha_pago = self.fecha_pago
                bono.save()






