"""
Modelos de configuracion
"""

from django.db import models
from django.contrib.auth.models import User


# AdministracionTaller
class AdministracionTaller(models.Model):
    """Configuración y administración del taller"""
    
    # Información básica del taller
    nombre_taller = models.CharField(max_length=200, default="Mi Taller Mecánico")
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    rut = models.CharField(max_length=20, blank=True, null=True, help_text="RUT del taller")
    
    # Logos personalizables
    logo_principal_png = models.ImageField(
        upload_to='logos/', 
        blank=True, 
        null=True,
        help_text="Logo principal en formato PNG (recomendado: 200x80px)"
    )
    logo_principal_svg = models.FileField(
        upload_to='logos/', 
        blank=True, 
        null=True,
        help_text="Logo principal en formato SVG (vectorial, mejor calidad)"
    )
    logo_secundario_png = models.ImageField(
        upload_to='logos/', 
        blank=True, 
        null=True,
        help_text="Logo secundario en formato PNG (recomendado: 150x60px)"
    )
    
    # Fondo personalizable
    imagen_fondo = models.ImageField(
        upload_to='fondos/', 
        blank=True, 
        null=True,
        help_text="Imagen de fondo para el panel principal (recomendado: 1920x1080px)"
    )
    
    # Políticas de seguridad
    sesion_timeout_minutos = models.PositiveIntegerField(
        default=30,
        help_text="Tiempo de inactividad antes de cerrar sesión (minutos)"
    )
    intentos_login_maximos = models.PositiveIntegerField(
        default=5,
        help_text="Máximo número de intentos de login fallidos"
    )
    bloqueo_temporal_horas = models.PositiveIntegerField(
        default=1,
        help_text="Horas de bloqueo después de exceder intentos máximos"
    )
    requiere_cambio_password = models.BooleanField(
        default=False,
        help_text="Forzar cambio de contraseña en próximo login"
    )
    dias_validez_password = models.PositiveIntegerField(
        default=90,
        help_text="Días de validez de la contraseña (0 = sin expiración)"
    )
    
    # Configuraciones adicionales
    tema_por_defecto = models.CharField(
        max_length=20,
        choices=[
            ('piedra', 'Piedra (Oscuro)'),
            ('plum', 'Plum (Oscuro)'),
            ('cyan', 'Cyan (Claro)'),
            ('sand', 'Sand (Claro)'),
            ('sage', 'Sage (Claro)'),
            ('sky', 'Sky (Claro)'),
        ],
        default='piedra',
        help_text="Tema de color por defecto para nuevos usuarios"
    )
    
    # Configuraciones del sistema
    mostrar_estadisticas_publicas = models.BooleanField(
        default=True,
        help_text="Mostrar estadísticas en el panel principal"
    )
    permitir_registro_usuarios = models.BooleanField(
        default=False,
        help_text="Permitir que nuevos usuarios se registren automáticamente"
    )
    notificaciones_email = models.BooleanField(
        default=True,
        help_text="Enviar notificaciones por email"
    )
    
    # Metadatos
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='configuraciones_creadas'
    )
    
    class Meta:
        verbose_name = "Administración del Taller"
        verbose_name_plural = "Administraciones de Taller"
        ordering = ['-fecha_actualizacion']
    
    def __str__(self):
        return f"Configuración - {self.nombre_taller}"
    
    @property
    def logo_principal_url(self):
        """Retorna la URL del logo principal (PNG o SVG)"""
        if self.logo_principal_svg:
            return self.logo_principal_svg.url
        elif self.logo_principal_png:
            return self.logo_principal_png.url
        else:
            return '/static/images/Logo1.svg'  # Logo por defecto
    
    @property
    def logo_secundario_url(self):
        """Retorna la URL del logo secundario"""
        if self.logo_secundario_png:
            return self.logo_secundario_png.url
        else:
            return '/static/images/Logo2.png'  # Logo por defecto
    
    @property
    def imagen_fondo_url(self):
        """Retorna la URL de la imagen de fondo"""
        if self.imagen_fondo:
            return self.imagen_fondo.url
        else:
            return None  # Sin fondo personalizado
    
    @classmethod
    def get_configuracion_activa(cls):
        """Obtiene la configuración activa del taller"""
        config = cls.objects.first()
        if not config:
            # Crear configuración por defecto si no existe
            config = cls.objects.create(
                nombre_taller="Mi Taller Mecánico",
                creado_por=None
            )
        return config


# SISTEMA DE COMPRAS





