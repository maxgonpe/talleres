"""
Modelos de usuarios
"""

from django.db import models
from django.db.models import Sum
from django.conf import settings
from decimal import Decimal
from django.contrib.auth.models import User
# Importación lazy para evitar dependencia circular
# from bonos.models import BonoGenerado, ConfiguracionBonoMecanico, PagoMecanico


# Mecanico
class Mecanico(models.Model):
    ROLES_CHOICES = [
        ('mecanico', 'Mecánico'),
        ('vendedor', 'Vendedor'),
        ('admin', 'Administrador'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mecanico")
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    # NUEVOS CAMPOS PARA ROLES Y PERMISOS
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, default='mecanico')
    
    # PERMISOS POR MÓDULO
    puede_ver_diagnosticos = models.BooleanField(default=True)
    puede_ver_trabajos = models.BooleanField(default=True)
    puede_ver_pos = models.BooleanField(default=True)  # ← CAMBIADO
    puede_ver_compras = models.BooleanField(default=True)  # ← CAMBIADO
    puede_ver_inventario = models.BooleanField(default=True)  # ← CAMBIADO
    puede_ver_administracion = models.BooleanField(default=True)  # ← CAMBIADO
    
    # PERMISOS ESPECÍFICOS
    crear_clientes = models.BooleanField(default=True)
    crear_vehiculos = models.BooleanField(default=True)
    aprobar_diagnosticos = models.BooleanField(default=False)
    gestionar_usuarios = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_rol_display()})"
    
    @property
    def saldo_bonos_pendiente(self):
        """
        Calcula el saldo total de bonos pendientes de pago.
        """
        from bonos.models import BonoGenerado
        bonos_pendientes = BonoGenerado.objects.filter(
            mecanico=self,
            pagado=False
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        return bonos_pendientes
    
    @property
    def saldo_bonos_total(self):
        """
        Calcula el total de bonos generados (incluyendo pagados).
        """
        from bonos.models import BonoGenerado
        bonos_totales = BonoGenerado.objects.filter(
            mecanico=self
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        return bonos_totales
    
    @property
    def total_pagado(self):
        """
        Calcula el total pagado al mecánico.
        """
        from bonos.models import PagoMecanico
        pagos = PagoMecanico.objects.filter(
            mecanico=self
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        return pagos
    
    def tiene_bonos_activos(self):
        """
        Verifica si el mecánico tiene bonos activos configurados.
        """
        from bonos.models import ConfiguracionBonoMecanico
        try:
            config = self.configuracion_bono
            return config.activo
        except ConfiguracionBonoMecanico.DoesNotExist:
            return False
    
    def save(self, *args, **kwargs):
        # Auto-configurar permisos según el rol
        if self.rol == 'mecanico':
            self.puede_ver_diagnosticos = True
            self.puede_ver_trabajos = True
            self.puede_ver_pos = False
            self.puede_ver_compras = False
            self.puede_ver_inventario = False
            self.puede_ver_administracion = False
            self.crear_clientes = True
            self.crear_vehiculos = True
            self.aprobar_diagnosticos = False
            self.gestionar_usuarios = False
        elif self.rol == 'vendedor':
            self.puede_ver_diagnosticos = False
            self.puede_ver_trabajos = False
            self.puede_ver_pos = True
            self.puede_ver_compras = False
            self.puede_ver_inventario = True
            self.puede_ver_administracion = False
            self.crear_clientes = True
            self.crear_vehiculos = False
            self.aprobar_diagnosticos = False
            self.gestionar_usuarios = False
        elif self.rol == 'admin':
            self.puede_ver_diagnosticos = True
            self.puede_ver_trabajos = True
            self.puede_ver_pos = True
            self.puede_ver_compras = True
            self.puede_ver_inventario = True
            self.puede_ver_administracion = True
            self.crear_clientes = True
            self.crear_vehiculos = True
            self.aprobar_diagnosticos = True
            self.gestionar_usuarios = True
        
        super().save(*args, **kwargs)



# Create your models here.


