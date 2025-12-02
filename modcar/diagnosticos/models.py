"""
Modelos de diagnosticos
"""

from django.db import models
from django.db.models import Sum
from decimal import Decimal
from django.db import transaction
from core.models import Vehiculo, Componente
from inventario.models import Repuesto, RepuestoExterno, RepuestoEnStock


# Diagnostico
class Diagnostico(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("aprobado", "Aprobado"),
        ("rechazado", "Rechazado"),
    ]

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    componentes = models.ManyToManyField(Componente, related_name='diagnosticos')
    descripcion_problema = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    subcomponentes_sugeridos = models.JSONField(blank=True, null=True)
    aceptado_por = models.CharField(max_length=100, blank=True, null=True)
    fecha_aceptacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    visible = models.BooleanField(default=True, verbose_name="Visible", help_text="Indica si el diagnóstico debe mostrarse en las listas")

    def __str__(self):
        return self.vehiculo.marca
    
    @property
    def total_mano_obra(self):
        """Calcular el total de mano de obra sumando todas las acciones (considerando cantidad)"""
        from decimal import Decimal
        total = Decimal('0')
        for dca in self.acciones_componentes.all():
            total += dca.subtotal or Decimal('0')
        return total
    
    @property
    def total_repuestos(self):
        """Calcular el total de repuestos sumando todos los subtotales"""
        from decimal import Decimal
        total = Decimal('0')
        for dr in self.repuestos.all():
            total += dr.subtotal or Decimal('0')
        return total
    
    @property
    def total_presupuesto(self):
        """Calcular el total del presupuesto (mano de obra + repuestos)"""
        return self.total_mano_obra + self.total_repuestos

    def aprobar_y_clonar(self):
        """
        Convierte un diagnóstico en un trabajo, clonando también
        sus acciones y repuestos asociados.
        """
        with transaction.atomic():
            # 🚗 Crear el trabajo
            trabajo = Trabajo.objects.create(
                diagnostico=self,
                vehiculo=self.vehiculo,
                estado="iniciado",
                observaciones=self.descripcion_problema,
            )

            # 🔹 Clonar componentes (M2M)
            trabajo.componentes.set(self.componentes.all())

            # 🔹 Clonar Acciones asociadas
            for dca in self.acciones_componentes.all():
                TrabajoAccion.objects.create(
                    trabajo=trabajo,
                    componente=dca.componente,
                    accion=dca.accion,
                    precio_mano_obra=dca.precio_mano_obra,
                    cantidad=dca.cantidad,  # Clonar cantidad también
                    completado=False  # arranca pendiente
                )

            # 🔹 Clonar Repuestos asociados (incluyendo externos)
            for dr in self.repuestos.all():
                TrabajoRepuesto.objects.create(
                    trabajo=trabajo,
                    componente=getattr(dr, "componente", None),  # si no existe, queda None
                    repuesto=dr.repuesto,  # Puede ser None si es externo
                    repuesto_externo=dr.repuesto_externo,  # NUEVO: copiar repuesto externo
                    cantidad=dr.cantidad,
                    precio_unitario=dr.precio_unitario or 0,
                    subtotal=dr.subtotal or 0,
                )

            # Cambiar estado del diagnóstico
            self.estado = "aprobado"
            self.save()

        return trabajo


    

# DiagnosticoComponenteAccion
class DiagnosticoComponenteAccion(models.Model):
    diagnostico = models.ForeignKey("Diagnostico", on_delete=models.CASCADE, related_name="acciones_componentes")
    componente = models.ForeignKey("core.Componente", on_delete=models.CASCADE)
    accion = models.ForeignKey("core.Accion", on_delete=models.CASCADE)
    precio_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio Unitario")
    cantidad = models.IntegerField(default=1, verbose_name="Cantidad", help_text="Número de veces que se realizará esta acción (ej: cambiar 4 bujías)")

    @property
    def subtotal(self):
        """Calcula el subtotal: precio unitario * cantidad"""
        return self.precio_mano_obra * self.cantidad

    def __str__(self):
        if self.cantidad > 1:
            return f"{self.diagnostico.vehiculo} - {self.accion.nombre} {self.componente.nombre} (x{self.cantidad})"
        return f"{self.diagnostico.vehiculo} - {self.accion.nombre} {self.componente.nombre}"


    # --- Solo para mostrar en el admin como referencia ---
    def precio_base_sugerido(self):
        try:
            base = ComponenteAccion.objects.get(componente=self.componente, accion=self.accion)
            return base.precio_mano_obra
        except ComponenteAccion.DoesNotExist:
            return None
    precio_base_sugerido.short_description = "Precio base (catálogo)"

    # --- Validación opcional: exigir que exista el precio base en catálogo ---
    def clean(self):
        # si quieres forzar que exista esa combinación en el catálogo, descomenta:
        # if not ComponenteAccion.objects.filter(componente=self.componente, accion=self.accion).exists():
        #     raise ValidationError("No existe precio base en el catálogo para esta combinación Componente + Acción.")

        super().clean()

    # --- Autocompletar si no se ingresó precio explícito ---
    def save(self, *args, **kwargs):
        if (self.precio_mano_obra is None or self.precio_mano_obra == 0) and self.componente_id and self.accion_id:
            try:
                base = ComponenteAccion.objects.get(componente=self.componente, accion=self.accion)
                self.precio_mano_obra = base.precio_mano_obra
            except ComponenteAccion.DoesNotExist:
                # Si no existe en catálogo, lo dejamos en 0 para que el admin lo note
                pass
        super().save(*args, **kwargs)



# DiagnosticoRepuesto
class DiagnosticoRepuesto(models.Model):
    diagnostico = models.ForeignKey('Diagnostico', on_delete=models.CASCADE, related_name='repuestos')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT, null=True, blank=True)  # Ahora puede ser NULL
    repuesto_externo = models.ForeignKey('inventario.RepuestoExterno', on_delete=models.SET_NULL, null=True, blank=True, related_name='diagnosticos')  # NUEVO
    repuesto_stock = models.ForeignKey(RepuestoEnStock, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    reservado = models.BooleanField(default=False)  # si fue reservado en stock
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.repuesto_externo:
            return f"🌐 {self.repuesto_externo.nombre} (x{self.cantidad})"
        elif self.repuesto:
            return f"{self.repuesto} (x{self.cantidad})"
        return f"Repuesto (x{self.cantidad})"

# Trabajo (clonado desde Diagnóstico aprobado)


# Reparacion
class Reparacion(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE)
    subcomponente = models.CharField(max_length=100)
    accion = models.CharField(max_length=200)
    tiempo_estimado_minutos = models.PositiveIntegerField()





