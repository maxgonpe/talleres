"""
Modelos de core
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


def normalizar_rut(rut: str) -> str:
    """Normaliza un RUT eliminando puntos, guiones y espacios"""
    if not rut:
        return ""
    return (
        rut.replace(".", "")
           .replace("-", "")
           .replace(" ", "")
           .upper()
    )


# Cliente_Taller
class Cliente_Taller(models.Model):
    """Nuevo modelo de cliente con RUT como clave primaria para evitar duplicados"""
    rut = models.CharField(max_length=12, primary_key=True, verbose_name="RUT")
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Cliente del Taller"
        verbose_name_plural = "Clientes del Taller"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rut})"

    def save(self, *args, **kwargs):
        self.rut = normalizar_rut(self.rut)
        super().save(*args, **kwargs)



# Vehiculo
class Vehiculo(models.Model):
    cliente = models.ForeignKey(Cliente_Taller, on_delete=models.CASCADE)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField()
    vin = models.CharField(max_length=50, blank=True, null=True)
    placa = models.CharField(max_length=10, unique=True)

    # Motor predefinido (opcional pero útil para IA)
    descripcion_motor = models.CharField(max_length=100, blank=True, null=True)
    
    
    #def __str__(self):
    #    return self.cliente.nombre

    #def __str__(self):
    #    # Acceder al anio
    #    return f"{self.marca} {self.modelo} {self.anio}"

    
    def __str__(self):
        return f"{self.placa} • {self.marca} {self.modelo} ({self.anio})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'placa'],
                name='unique_vehiculo_cliente_placa'
            ),
        ]



# Componente
class Componente(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=255, unique=True, editable=False)  # se autogenera
    activo = models.BooleanField(default=True)
    padre = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,            # <- PROTECT: Evita eliminación si tiene hijos
        null=True, blank=True,
        related_name='hijos'
    )

    class Meta:
        # evita duplicar el mismo nombre dentro del mismo padre
        constraints = [
            models.UniqueConstraint(
                fields=['padre', 'nombre'], name='unique_nombre_por_padre'
            )
        ]
        indexes = [
            models.Index(fields=['codigo']),
        ]

    def __str__(self):
        return self.nombre

    # ───────── helpers ─────────
    def build_codigo(self) -> str:
        """Construye el código jerárquico legible."""
        slug = slugify(self.nombre).replace('_', '-')
        if self.padre:
            return f"{self.padre.codigo}-{slug}"
        return slug

    def _update_descendant_codes(self):
        """Propaga el nuevo código a toda la descendencia."""
        for hijo in self.hijos.all():
            # recalcular usando el nuevo self.codigo como base
            hijo.codigo = f"{self.codigo}-{slugify(hijo.nombre).replace('_','-')}"
            super(Componente, hijo).save(update_fields=['codigo'])  # guarda sin recursión extra
            hijo._update_descendant_codes()

    def save(self, *args, **kwargs):
        # Detectar si cambia padre o nombre (para decidir si propagamos)
        old_nombre = None
        old_parent_id = None
        if self.pk:
            try:
                prev = type(self).objects.get(pk=self.pk)
                old_parent_id = prev.padre_id
                old_nombre = prev.nombre
            except type(self).DoesNotExist:
                # Si no existe el objeto anterior, es un objeto nuevo
                pass

        # Normalizar el nombre
        if self.nombre:
            self.nombre = self.nombre.lower()
        
        # Verificar restricción unique_together (padre, nombre)
        if self.pk:
            # Para objetos existentes, excluir el propio objeto
            existe_nombre = Componente.objects.filter(
                padre=self.padre, 
                nombre=self.nombre
            ).exclude(pk=self.pk).exists()
        else:
            # Para objetos nuevos, verificar si existe
            existe_nombre = Componente.objects.filter(
                padre=self.padre, 
                nombre=self.nombre
            ).exists()
        
        if existe_nombre:
            # Si el nombre ya existe bajo el mismo padre, agregar un sufijo numérico
            contador = 1
            nombre_base = self.nombre
            while Componente.objects.filter(
                padre=self.padre, 
                nombre=self.nombre
            ).exclude(pk=self.pk if self.pk else None).exists():
                self.nombre = f"{nombre_base}-{contador}"
                contador += 1

        # Siempre recalculamos el código antes de guardar
        nuevo_codigo = self.build_codigo()
        
        # Verificar si el nuevo código ya existe en otro componente
        if self.pk:
            # Para objetos existentes, excluir el propio objeto
            existe_codigo = Componente.objects.filter(codigo=nuevo_codigo).exclude(pk=self.pk).exists()
        else:
            # Para objetos nuevos, verificar si existe
            existe_codigo = Componente.objects.filter(codigo=nuevo_codigo).exists()
        
        if existe_codigo:
            # Si el código ya existe, agregar un sufijo numérico
            contador = 1
            codigo_base = nuevo_codigo
            while Componente.objects.filter(codigo=nuevo_codigo).exclude(pk=self.pk if self.pk else None).exists():
                nuevo_codigo = f"{codigo_base}-{contador}"
                contador += 1
        
        self.codigo = nuevo_codigo
        
        super().save(*args, **kwargs)

        # Si cambió el nombre o el padre, hay que propagar a los hijos
        if self.pk and old_parent_id is not None and (old_parent_id != self.padre_id or old_nombre != self.nombre):
            self._update_descendant_codes()
    
    def eliminar_seguro(self):
        """
        Elimina el componente de forma segura usando soft delete.
        Primero desactiva el componente y luego verifica si se puede eliminar.
        """
        # Verificar si tiene hijos activos
        hijos_activos = self.hijos.filter(activo=True).exists()
        if hijos_activos:
            raise ValueError(f"No se puede eliminar '{self.nombre}' porque tiene componentes hijos activos.")
        
        # Verificar si está siendo usado en diagnósticos o trabajos
        from django.db.models import Q
        en_uso = (
            self.diagnosticos.exists() or 
            self.trabajos.exists() or
            self.componenteaccion_set.exists() or
            self.diagnosticocomponenteaccion_set.exists() or
            self.trabajoaccion_set.exists() or
            self.componenterepuesto_set.exists() or
            self.trabajorepuesto_set.exists()
        )
        
        if en_uso:
            # Soft delete: solo desactivar
            self.activo = False
            self.save()
            return False  # No se eliminó físicamente
        else:
            # Hard delete: eliminar físicamente
            super().delete()
            return True  # Se eliminó físicamente



# Accion
class Accion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


# ComponenteAccion
class ComponenteAccion(models.Model):
    componente = models.ForeignKey("Componente", on_delete=models.CASCADE)
    accion = models.ForeignKey("Accion", on_delete=models.CASCADE)
    precio_mano_obra = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    class Meta:
        unique_together = ('componente','accion')

        def __str__(self):
            return f"{self.accion.nombre} {self.componente.nombre} - ${self.precio_mano_obra}"
            

# VehiculoVersion
class VehiculoVersion(models.Model):
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=120)
    anio_desde = models.IntegerField()
    anio_hasta = models.IntegerField()
    motor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Motor")
    carroceria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Carrocería")
    # opcionales: engine_code, trim, etc.

    class Meta:
        unique_together = ("marca", "modelo", "anio_desde", "anio_hasta")

    def __str__(self):
        return f"{self.marca} {self.modelo} {self.anio_desde}-{self.anio_hasta}"


# PrefijoRepuesto
class PrefijoRepuesto(models.Model):
    palabra = models.CharField(
        max_length=100, unique=True,
        help_text="Palabra clave a buscar en el nombre o posición (ej. 'freno')"
    )
    abreviatura = models.CharField(
        max_length=10,
        help_text="Abreviatura para el SKU (ej. 'FRE')"
    )

    def __str__(self):
        return f"{self.palabra} → {self.abreviatura}"





