"""
Modelos de estadisticas
"""

from django.db import models
from decimal import Decimal


# RegistroEvento
class RegistroEvento(models.Model):
    """
    Registro inmutable de eventos del sistema para auditoría y análisis.
    Captura todos los movimientos importantes: ingresos, cambios de estado,
    acciones completadas, repuestos instalados, entregas, etc.
    """
    
    TIPO_EVENTO_CHOICES = [
        ('diagnostico_creado', 'Diagnóstico Creado'),
        ('diagnostico_aprobado', 'Diagnóstico Aprobado'),
        ('ingreso', 'Ingreso de Vehículo'),
        ('cambio_estado', 'Cambio de Estado'),
        ('accion_completada', 'Acción Completada'),
        ('accion_pendiente', 'Acción Marcada como Pendiente'),
        ('repuesto_instalado', 'Repuesto Instalado'),
        ('repuesto_pendiente', 'Repuesto Marcado como Pendiente'),
        ('entrega', 'Vehículo Entregado'),
        ('abono', 'Abono/Pago Recibido'),
        ('mecanico_asignado', 'Mecánico Asignado'),
        ('mecanico_removido', 'Mecánico Removido'),
        ('foto_agregada', 'Foto Agregada'),
        ('observacion_agregada', 'Observación Agregada'),
    ]
    
    # IDENTIFICACIÓN Y REFERENCIAS
    # Usar IntegerField en lugar de FK para que persistan aunque se eliminen los originales
    trabajo_id = models.IntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID del Trabajo",
        help_text="ID del trabajo relacionado (null si es solo diagnóstico, puede no existir si fue eliminado)"
    )
    diagnostico_id = models.IntegerField(
        null=True, 
        blank=True,
        db_index=True,
        verbose_name="ID del Diagnóstico",
        help_text="ID del diagnóstico relacionado"
    )
    vehiculo_id = models.IntegerField(
        db_index=True,
        verbose_name="ID del Vehículo",
        help_text="ID del vehículo relacionado"
    )
    
    # TIPO Y FECHA DEL EVENTO
    tipo_evento = models.CharField(
        max_length=30,
        choices=TIPO_EVENTO_CHOICES,
        db_index=True,
        verbose_name="Tipo de Evento"
    )
    fecha_evento = models.DateTimeField(
        db_index=True,
        verbose_name="Fecha del Evento",
        help_text="Fecha y hora exacta en que ocurrió el evento"
    )
    
    # DATOS DEL VEHÍCULO (ALMACENADOS PARA HISTORIAL)
    # Almacenar datos importantes como texto para que persistan
    vehiculo_placa = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="Placa del Vehículo",
        help_text="Placa almacenada al momento del evento"
    )
    vehiculo_marca = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Marca del Vehículo"
    )
    vehiculo_modelo = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Modelo del Vehículo"
    )
    cliente_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre del Cliente",
        help_text="Nombre del cliente al momento del evento"
    )
    
    # DATOS ESPECÍFICOS DEL EVENTO
    estado_anterior = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Estado Anterior",
        help_text="Estado previo (para cambios de estado)"
    )
    estado_nuevo = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="Estado Nuevo",
        help_text="Nuevo estado (para cambios de estado)"
    )
    accion_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="ID de Acción",
        help_text="ID de la acción relacionada (si aplica)"
    )
    accion_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre de Acción",
        help_text="Nombre de la acción al momento del evento"
    )
    componente_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre de Componente",
        help_text="Componente relacionado (si aplica)"
    )
    repuesto_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="ID de Repuesto",
        help_text="ID del repuesto relacionado (si aplica)"
    )
    repuesto_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre de Repuesto",
        help_text="Nombre del repuesto al momento del evento"
    )
    repuesto_cantidad = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad de Repuesto"
    )
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Monto",
        help_text="Monto relacionado (abonos, acciones, repuestos)"
    )
    
    # METADATOS
    usuario_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="ID del Usuario",
        help_text="Usuario que realizó la acción"
    )
    usuario_nombre = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name="Nombre del Usuario",
        help_text="Nombre del usuario al momento del evento"
    )
    mecanico_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="ID del Mecánico",
        help_text="Mecánico relacionado (si aplica)"
    )
    mecanico_nombre = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Nombre del Mecánico"
    )
    descripcion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción",
        help_text="Descripción adicional del evento"
    )
    
    # CAMPOS PARA ESTADÍSTICAS Y ANÁLISIS
    fecha_ingreso = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Fecha de Ingreso",
        help_text="Fecha en que ingresó el vehículo al sistema"
    )
    fecha_entrega = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Fecha de Entrega",
        help_text="Fecha en que se entregó el vehículo (si aplica)"
    )
    dias_en_taller = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="Días en Taller",
        help_text="Días que estuvo en el taller al momento del evento"
    )
    total_mano_obra = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total Mano de Obra",
        help_text="Total de mano de obra al momento del evento"
    )
    total_repuestos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total Repuestos",
        help_text="Total de repuestos al momento del evento"
    )
    total_general = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Total General",
        help_text="Total general al momento del evento"
    )
    
    # FECHA DE CREACIÓN DEL REGISTRO
    creado_en = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha de Creación del Registro"
    )
    
    class Meta:
        verbose_name = "Registro de Evento"
        verbose_name_plural = "Registros de Eventos"
        ordering = ['-fecha_evento', '-creado_en']
        indexes = [
            models.Index(fields=['trabajo_id', 'tipo_evento', 'fecha_evento']),
            models.Index(fields=['vehiculo_id', 'fecha_evento']),
            models.Index(fields=['fecha_ingreso', 'fecha_entrega']),
            models.Index(fields=['tipo_evento', 'fecha_evento']),
            models.Index(fields=['vehiculo_placa', 'fecha_evento']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_evento_display()} - Trabajo #{self.trabajo_id} - {self.vehiculo_placa} - {self.fecha_evento.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def es_entrega(self):
        """Indica si este evento es una entrega"""
        return self.tipo_evento == 'entrega'
    
    @property
    def es_cambio_estado(self):
        """Indica si este evento es un cambio de estado"""
        return self.tipo_evento == 'cambio_estado'
    
    @property
    def dias_desde_entrega(self):
        """Calcula cuántos días han pasado desde la entrega"""
        if not self.fecha_entrega:
            return None
        from django.utils import timezone
        delta = timezone.now() - self.fecha_entrega
        return delta.days


# RESUMEN DE TRABAJOS (VISTA MATERIALIZADA/VIRTUAL)
# Este modelo puede ser usado para almacenar resúmenes calculados
# y mejorar el rendimiento de consultas frecuentes


# ResumenTrabajo
class ResumenTrabajo(models.Model):
    """
    Resumen calculado de un trabajo para análisis rápido.
    Se actualiza cada vez que hay un evento relacionado.
    """
    
    trabajo_id = models.IntegerField(
        unique=True,
        db_index=True,
        verbose_name="ID del Trabajo"
    )
    
    # Datos del vehículo (snapshot)
    vehiculo_placa = models.CharField(max_length=20, db_index=True)
    vehiculo_marca = models.CharField(max_length=100, blank=True, null=True)
    vehiculo_modelo = models.CharField(max_length=100, blank=True, null=True)
    cliente_nombre = models.CharField(max_length=200, blank=True, null=True)
    
    # Fechas importantes
    fecha_ingreso = models.DateTimeField(db_index=True)
    fecha_ultimo_estado = models.DateTimeField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # Estado actual
    estado_actual = models.CharField(max_length=20, db_index=True)
    
    # Contadores
    total_acciones = models.IntegerField(default=0)
    acciones_completadas = models.IntegerField(default=0)
    cantidad_repuestos = models.IntegerField(default=0, verbose_name="Cantidad de Repuestos")
    repuestos_instalados = models.IntegerField(default=0)
    
    # Totales financieros
    total_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_repuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Total Repuestos (Monto)")
    total_general = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_abonos = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Calculados
    porcentaje_avance = models.IntegerField(default=0)
    porcentaje_cobrado = models.IntegerField(default=0)
    dias_en_taller = models.IntegerField(default=0)
    dias_desde_entrega = models.IntegerField(null=True, blank=True)
    
    # Mecánicos asignados (almacenado como texto separado por comas)
    mecanicos_asignados = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="IDs de mecánicos separados por comas"
    )
    
    # Última actualización
    ultima_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Resumen de Trabajo"
        verbose_name_plural = "Resúmenes de Trabajos"
        ordering = ['-fecha_ingreso']
        indexes = [
            models.Index(fields=['estado_actual', 'fecha_ingreso']),
            models.Index(fields=['fecha_entrega', 'dias_desde_entrega']),
            models.Index(fields=['vehiculo_placa', 'fecha_ingreso']),
        ]
    
    def __str__(self):
        estado_texto = "Entregado" if self.fecha_entrega else self.estado_actual
        return f"Trabajo #{self.trabajo_id} - {self.vehiculo_placa} - {estado_texto}"


# SISTEMA DE BONOS E INCENTIVOS PARA MECÁNICOS





