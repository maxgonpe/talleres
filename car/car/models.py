from django.db import models
from django.db import models
from django.conf import settings
from decimal import Decimal
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.timezone import now

class Mecanico(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="mecanico")
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    fecha_ingreso = models.DateField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}"



# Create your models here.
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


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


class Vehiculo(models.Model):
    cliente = models.ForeignKey(Cliente_Taller, on_delete=models.CASCADE)
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    anio = models.PositiveIntegerField()
    vin = models.CharField(max_length=50, blank=True, null=True)
    placa = models.CharField(max_length=10)

    # Motor predefinido (opcional pero útil para IA)
    descripcion_motor = models.CharField(max_length=100, blank=True, null=True)
    
    
    #def __str__(self):
    #    return self.cliente.nombre

    #def __str__(self):
    #    # Acceder al anio
    #    return f"{self.marca} {self.modelo} {self.anio}"

    
    def __str__(self):
        return f"{self.placa} • {self.marca} {self.modelo} ({self.anio})"


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
        old_parent_id = None
        old_nombre = None
        if self.pk:
            prev = type(self).objects.get(pk=self.pk)
            old_parent_id = prev.padre_id
            old_nombre = prev.nombre

        # Siempre recalculamos el código antes de guardar
        self.codigo = self.build_codigo()
        if self.nombre:
            self.nombre = self.nombre.lower()
        super().save(*args, **kwargs)

        # Si cambió el nombre o el padre, hay que propagar a los hijos
        if self.pk and (old_parent_id != self.padre_id or old_nombre != self.nombre):
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

    def __str__(self):
        return self.vehiculo.marca
    

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
                    completado=False  # arranca pendiente
                )

            # 🔹 Clonar Repuestos asociados
            for dr in self.repuestos.all():
                TrabajoRepuesto.objects.create(
                    trabajo=trabajo,
                    #componente=dr.componente if hasattr(dr, "componente") else None,
                    componente=getattr(dr, "componente", None),  # si no existe, queda None
                    repuesto=dr.repuesto,
                    #repuesto_stock=dr.repuesto_stock,
                    cantidad=dr.cantidad,
                    precio_unitario=dr.precio_unitario or 0,
                    subtotal=dr.subtotal or 0,
                    #estado="pendiente",  # nuevo campo sugerido en TrabajoRepuesto
                    #componente=dr.componente if hasattr(dr, "componente") else None
                )

            # Cambiar estado del diagnóstico
            self.estado = "aprobado"
            self.save()

        return trabajo


    
class Reparacion(models.Model):
    diagnostico = models.ForeignKey(Diagnostico, on_delete=models.CASCADE)
    subcomponente = models.CharField(max_length=100)
    accion = models.CharField(max_length=200)
    tiempo_estimado_minutos = models.PositiveIntegerField()



class Accion(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class ComponenteAccion(models.Model):
    componente = models.ForeignKey("Componente", on_delete=models.CASCADE)
    accion = models.ForeignKey("Accion", on_delete=models.CASCADE)
    precio_mano_obra = models.DecimalField(max_digits=10,decimal_places=2,default=0)

    class Meta:
        unique_together = ('componente','accion')

        def __str__(self):
            return f"{self.accion.nombre} {self.componente.nombre} - ${self.precio_mano_obra}"
            
class DiagnosticoComponenteAccion(models.Model):
    diagnostico = models.ForeignKey("Diagnostico", on_delete=models.CASCADE, related_name="acciones_componentes")
    componente = models.ForeignKey("Componente", on_delete=models.CASCADE)
    accion = models.ForeignKey("Accion", on_delete=models.CASCADE)
    precio_mano_obra = models.DecimalField(max_digits=10, decimal_places=2,default=0)

    def __str__(self):
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
                        # Regenerar SKU si cambió algún campo relevante
                        self.sku = self.generate_sku()
                except Repuesto.DoesNotExist:
                    # Si no existe el objeto anterior, generar SKU
                    self.sku = self.generate_sku()
            else:
                # Para objetos nuevos, generar SKU
                self.sku = self.generate_sku()
        
        super().save(*args, **kwargs)

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
        """Obtiene el stock total de todos los depósitos"""
        from django.db.models import Sum
        total = self.stocks.aggregate(total=Sum('stock'))['total']
        return total or 0
    
    @property
    def stock_disponible(self):
        """Obtiene el stock disponible (total - reservado)"""
        from django.db.models import Sum
        total_stock = self.stocks.aggregate(total=Sum('stock'))['total'] or 0
        total_reservado = self.stocks.aggregate(total=Sum('reservado'))['total'] or 0
        return total_stock - total_reservado
    
    def tiene_stock_suficiente(self, cantidad):
        """Verifica si hay stock suficiente para la cantidad solicitada"""
        return self.stock_disponible >= cantidad




class VehiculoVersion(models.Model):
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=120)
    anio_desde = models.IntegerField()
    anio_hasta = models.IntegerField()
    # opcionales: engine_code, trim, etc.

    class Meta:
        unique_together = ("marca", "modelo", "anio_desde", "anio_hasta")

    def __str__(self):
        return f"{self.marca} {self.modelo} {self.anio_desde}-{self.anio_hasta}"

class ComponenteRepuesto(models.Model):
    componente = models.ForeignKey('Componente', on_delete=models.CASCADE)  # tu modelo de componente
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE)
    nota = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("componente", "repuesto")

class RepuestoAplicacion(models.Model):
    repuesto = models.ForeignKey(Repuesto, on_delete=models.CASCADE, related_name="aplicaciones")
    version = models.ForeignKey(VehiculoVersion, on_delete=models.CASCADE)
    posicion = models.CharField(max_length=80, blank=True)  # opcional, sinon usar repuesto.posicion

    class Meta:
        unique_together = ("repuesto", "version")

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

class StockMovimiento(models.Model):
    repuesto_stock = models.ForeignKey(RepuestoEnStock, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=20, choices=(('ingreso','ingreso'),('salida','salida'),('reserva','reserva'),('liberacion','liberacion')))
    cantidad = models.IntegerField()
    motivo = models.CharField(max_length=200, blank=True)
    referencia = models.CharField(max_length=120, blank=True)  # ej ODT/DIAG id
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    fecha = models.DateTimeField(auto_now_add=True)

class DiagnosticoRepuesto(models.Model):
    diagnostico = models.ForeignKey('Diagnostico', on_delete=models.CASCADE, related_name='repuestos')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    repuesto_stock = models.ForeignKey(RepuestoEnStock, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    reservado = models.BooleanField(default=False)  # si fue reservado en stock
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.repuesto} (x{self.cantidad})"

# ========================
# Trabajo (clonado desde Diagnóstico aprobado)
# ========================

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
    mecanicos = models.ManyToManyField("Mecanico", related_name="trabajos", blank=True)

    # 🔹 Nuevo: relacionar con componentes (igual que Diagnostico)
    componentes = models.ManyToManyField("Componente", related_name="trabajos", blank=True)

    def __str__(self):
        return f"Trabajo #{self.id} - {self.vehiculo}"

    @property
    def total_mano_obra(self):
        return sum(a.precio_mano_obra for a in self.acciones.all())

    @property
    def total_repuestos(self):
        return sum(r.subtotal or 0 for r in self.repuestos.all())

    @property
    def total_general(self):
        return self.total_mano_obra + self.total_repuestos

    @property
    def porcentaje_avance(self):
        acciones_total = self.acciones.count()
        repuestos_total = self.repuestos.count()
        total_items = acciones_total + repuestos_total

        if total_items == 0:
            return 0  # nada registrado

        acciones_completadas = self.acciones.filter(completado=True).count()
        repuestos_instalados = self.repuestos.filter(completado=True).count()
        completados = acciones_completadas + repuestos_instalados

        return int((completados / total_items) * 100)

class TrabajoFoto(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="trabajos/fotos/%Y/%m/%d")
    descripcion = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto {self.id} de {self.trabajo}"


class TrabajoAccion(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="acciones")
    componente = models.ForeignKey("Componente", on_delete=models.CASCADE)
    accion = models.ForeignKey("Accion", on_delete=models.CASCADE)
    precio_mano_obra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    completado = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True, blank=True)

    #def __str__(self):
    #    return f"{self.trabajo} - {self.accion.nombre} {self.componente.nombre}"
    @property
    def costo(self):
        return self.accion.costo if self.completado else 0

    def __str__(self):
        return f"{self.accion} ({'✔️' if self.completado else 'pendiente'})"


class TrabajoRepuesto(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="repuestos")
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, null=True, blank=True)
    repuesto = models.ForeignKey("Repuesto", on_delete=models.PROTECT)
    cantidad = models.IntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    completado = models.BooleanField(default=False)
    fecha = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.repuesto} (x{self.cantidad})"

# ventas/models.py  (puedes ponerlo en la app extintores o crear app nueva "ventas")

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


def actualizar_stock_venta(venta):
    """
    Actualiza el stock de forma segura después de confirmar una venta.
    Debe llamarse dentro de una transacción atómica.
    """
    if not venta.pagado:
        return  # Solo actualizar stock si la venta está pagada
    
    for item in venta.items.all():
        # Verificar stock disponible antes de descontar
        if not item.repuesto_stock.repuesto.tiene_stock_suficiente(item.cantidad):
            raise ValueError(f"Stock insuficiente para {item.repuesto_stock.repuesto.nombre}")
        
        # Descontar stock
        item.repuesto_stock.stock -= item.cantidad
        item.repuesto_stock.save()
        
        # Registrar movimiento
        StockMovimiento.objects.create(
            repuesto_stock=item.repuesto_stock,
            tipo="salida",
            cantidad=item.cantidad,
            motivo=f"Venta #{venta.id}",
            usuario=venta.usuario
        )

# ========================
# MÓDULO POS (Point of Sale)
# ========================

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


def actualizar_stock_venta_pos(venta_pos):
    """
    Actualiza el stock de forma segura después de confirmar una venta POS.
    Debe llamarse dentro de una transacción atómica.
    """
    if not venta_pos.pagado:
        return  # Solo actualizar stock si la venta está pagada
    
    for item in venta_pos.items.all():
        # Verificar stock disponible antes de descontar
        if not item.repuesto.tiene_stock_suficiente(item.cantidad):
            raise ValueError(f"Stock insuficiente para {item.repuesto.nombre}")
        
        # Buscar el stock disponible
        stock_disponible = RepuestoEnStock.objects.filter(
            repuesto=item.repuesto,
            stock__gte=item.cantidad
        ).first()
        
        if stock_disponible:
            # Descontar stock
            stock_disponible.stock -= item.cantidad
            stock_disponible.save()
            
            # Registrar movimiento
            StockMovimiento.objects.create(
                repuesto_stock=stock_disponible,
                tipo="salida",
                cantidad=item.cantidad,
                motivo=f"Venta POS #{venta_pos.id}",
                usuario=venta_pos.usuario
            )
        else:
            raise ValueError(f"No hay stock disponible para {item.repuesto.nombre}")


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

# ========================
# SISTEMA DE COTIZACIONES
# ========================

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

