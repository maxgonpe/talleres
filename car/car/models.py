from django.db import models
from django.db.models import Sum
from django.conf import settings
from decimal import Decimal
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
from django.db import transaction
from django.utils.timezone import now

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
        bonos_totales = BonoGenerado.objects.filter(
            mecanico=self
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        return bonos_totales
    
    @property
    def total_pagado(self):
        """
        Calcula el total pagado al mecánico.
        """
        pagos = PagoMecanico.objects.filter(
            mecanico=self
        ).aggregate(total=Sum('monto'))['total'] or Decimal('0')
        
        return pagos
    
    def tiene_bonos_activos(self):
        """
        Verifica si el mecánico tiene bonos activos configurados.
        """
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
class Cliente(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre


def normalizar_rut(rut: str) -> str:
    if not rut:
        return ""
    return (
        rut.replace(".", "")
           .replace("-", "")
           .replace(" ", "")
           .upper()
    )


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
    carroceria = models.CharField(max_length=100, blank=True, null=True, default='yyyyyy', verbose_name="Carrocería")
    cilindrada = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cilindrada")
    nro_valvulas = models.IntegerField(blank=True, null=True, verbose_name="Número de Válvulas")
    combustible = models.CharField(max_length=50, blank=True, null=True, verbose_name="Combustible")
    otro_especial = models.CharField(max_length=200, blank=True, null=True, verbose_name="Otro Especial")

    
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




class VehiculoVersion(models.Model):
    marca = models.CharField(max_length=80)
    modelo = models.CharField(max_length=120)
    anio_desde = models.IntegerField()
    anio_hasta = models.IntegerField()
    motor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Motor")
    carroceria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Carrocería")
    cilindrada = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cilindrada")
    nro_valvulas = models.IntegerField(blank=True, null=True, verbose_name="Número de Válvulas")
    combustible = models.CharField(max_length=50, blank=True, null=True, verbose_name="Combustible")
    otro_especial = models.CharField(max_length=200, blank=True, null=True, verbose_name="Otro Especial")
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
    motor = models.CharField(max_length=100, blank=True, null=True, verbose_name="Motor")
    carroceria = models.CharField(max_length=100, blank=True, null=True, verbose_name="Carrocería")
    cilindrada = models.CharField(max_length=50, blank=True, null=True, verbose_name="Cilindrada")
    nro_valvulas = models.IntegerField(blank=True, null=True, verbose_name="Número de Válvulas")
    combustible = models.CharField(max_length=50, blank=True, null=True, verbose_name="Combustible")
    otro_especial = models.CharField(max_length=200, blank=True, null=True, verbose_name="Otro Especial")

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
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT, null=True, blank=True)  # Ahora puede ser NULL
    repuesto_externo = models.ForeignKey('RepuestoExterno', on_delete=models.SET_NULL, null=True, blank=True, related_name='diagnosticos')  # NUEVO
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
    lectura_kilometraje_actual = models.IntegerField(null=True, blank=True, verbose_name="Kilometraje Actual", help_text="Lectura del kilometraje al ingresar el vehículo")
    mecanicos = models.ManyToManyField("Mecanico", related_name="trabajos", blank=True)
    visible = models.BooleanField(default=True, verbose_name="Visible", help_text="Indica si el trabajo debe mostrarse en las listas")

    # 🔹 Nuevo: relacionar con componentes (igual que Diagnostico)
    componentes = models.ManyToManyField("Componente", related_name="trabajos", blank=True)

    def __str__(self):
        return f"Trabajo #{self.id} - {self.vehiculo}"

    # ========================
    # TOTALES PRESUPUESTADOS (TODO)
    # ========================
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

    # ========================
    # TOTALES REALIZADOS (COMPLETADOS)
    # ========================
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

    # ========================
    # ABONOS Y SALDOS
    # ========================
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

    # ========================
    # PORCENTAJE DE AVANCE
    # ========================
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
    
    # ========================
    # DÍAS EN EL TALLER
    # ========================
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


class TrabajoRepuesto(models.Model):
    trabajo = models.ForeignKey(Trabajo, on_delete=models.CASCADE, related_name="repuestos")
    componente = models.ForeignKey(Componente, on_delete=models.CASCADE, null=True, blank=True)
    repuesto = models.ForeignKey("Repuesto", on_delete=models.PROTECT, null=True, blank=True)  # Ahora puede ser NULL
    repuesto_externo = models.ForeignKey('RepuestoExterno', on_delete=models.SET_NULL, null=True, blank=True, related_name='trabajos')  # NUEVO
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
        
        # 🔥 BÚSQUEDA CONSISTENTE: Buscar en bodega-principal
        stock_disponible = RepuestoEnStock.objects.filter(
            repuesto=item.repuesto,
            deposito='bodega-principal',
            stock__gte=item.cantidad
        ).first()
        
        if stock_disponible:
            # Descontar stock en RepuestoEnStock
            stock_disponible.stock -= item.cantidad
            stock_disponible.save()
            
            # 🔥 SINCRONIZAR: Descontar también en Repuesto.stock
            repuesto_obj = item.repuesto
            repuesto_obj.stock = (repuesto_obj.stock or 0) - item.cantidad
            repuesto_obj.save()
            
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
    ver_mensajes = models.BooleanField(
        default=True,
        help_text="Permitir visualización de mensajes"
    )
    ver_avisos = models.BooleanField(
        default=True,
        help_text="Permitir visualización de avisos"
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


# ========================
# SISTEMA DE COMPRAS
# ========================

class Compra(models.Model):
    """Modelo para registrar compras de repuestos"""
    ESTADOS = [
        ('borrador', 'Borrador'),
        ('confirmada', 'Confirmada'),
        ('recibida', 'Recibida'),
        ('cancelada', 'Cancelada'),
    ]
    
    numero_compra = models.CharField(max_length=20, unique=True, blank=True)
    proveedor = models.CharField(max_length=200, help_text="Nombre del proveedor")
    fecha_compra = models.DateField(default=now)
    fecha_recibida = models.DateField(null=True, blank=True, help_text="Fecha cuando se recibió la mercancía")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='borrador')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, help_text="Observaciones sobre la compra")
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_compra', '-creado_en']
        verbose_name = "Compra"
        verbose_name_plural = "Compras"
    
    def __str__(self):
        return f"Compra #{self.numero_compra} - {self.proveedor}"
    
    def save(self, *args, **kwargs):
        if not self.numero_compra:
            # Generar número de compra automático
            from django.db.models import Max
            
            # Obtener el último número de compra
            ultimo_numero = Compra.objects.aggregate(
                max_numero=Max('numero_compra')
            )['max_numero']
            
            if ultimo_numero:
                try:
                    # Extraer el número del formato COMP-0001
                    numero_actual = int(ultimo_numero.split('-')[-1])
                    nuevo_numero = numero_actual + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            
            # Generar el número de compra
            self.numero_compra = f"COMP-{nuevo_numero:04d}"
        
        super().save(*args, **kwargs)
    
    def calcular_total(self):
        """Calcula el total de la compra sumando todos los items"""
        total = self.items.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        )['total'] or 0
        self.total = total
        self.save(update_fields=['total'])
        return total


class CompraItem(models.Model):
    """Items de una compra"""
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='items')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(help_text="Cantidad comprada")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio por unidad")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, help_text="Cantidad × Precio unitario")
    recibido = models.BooleanField(default=False, help_text="¿Ya se recibió este item?")
    fecha_recibido = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Item de Compra"
        verbose_name_plural = "Items de Compra"
        unique_together = ['compra', 'repuesto']
    
    def __str__(self):
        return f"{self.repuesto.nombre} - {self.cantidad} unidades"
    
    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        
        # Actualizar total de la compra
        self.compra.calcular_total()
    
    def recibir_item(self, usuario=None):
        """Marca el item como recibido y actualiza el stock usando precio promedio ponderado"""
        if not self.recibido:
            print(f"\n{'='*80}")
            print(f"📦 RECIBIENDO COMPRA - Item: {self.repuesto.nombre} x{self.cantidad}")
            print(f"{'='*80}")
            
            self.recibido = True
            self.fecha_recibido = now()
            self.save()
            print(f"✅ Item marcado como recibido")
            
            # Actualizar stock del repuesto usando el nuevo sistema unificado
            repuesto = self.repuesto
            print(f"📊 Stock ANTES de actualizar:")
            print(f"   - Repuesto.stock: {repuesto.stock}")
            
            # Usar el nuevo método de actualización con precio promedio ponderado
            # Este método YA sincroniza con RepuestoEnStock internamente
            resultado = repuesto.actualizar_stock_y_precio(
                cantidad_entrada=self.cantidad,
                precio_compra=self.precio_unitario,
                proveedor=self.compra.proveedor
            )
            
            print(f"📊 Stock DESPUÉS de actualizar:")
            print(f"   - Stock anterior: {resultado['stock_anterior']}")
            print(f"   - Stock nuevo: {resultado['stock_nuevo']}")
            print(f"   - Precio costo: ${resultado['precio_costo_nuevo']}")
            print(f"   - Precio venta: ${resultado['precio_venta_nuevo']}")
            
            # Crear movimiento de stock para auditoría
            # 🔥 SIMPLIFICADO: Solo buscar por repuesto y deposito (ya sincronizado arriba)
            stock_principal = RepuestoEnStock.objects.filter(
                repuesto=self.repuesto,
                deposito='bodega-principal'
            ).first()
            
            if stock_principal:
                StockMovimiento.objects.create(
                    repuesto_stock=stock_principal,
                    tipo='entrada',
                    cantidad=self.cantidad,
                    motivo=f'Compra #{self.compra.numero_compra}',
                    referencia=f'COMPRA-{self.compra.id}',
                    usuario=usuario
                )
                print(f"📝 Movimiento de stock registrado")
            else:
                print(f"⚠️ No se encontró RepuestoEnStock para registrar movimiento")
            
            print(f"{'='*80}\n")


# ========================
# REPUESTOS EXTERNOS (REFERENCIAS)
# ========================

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
    vehiculos_compatibles = models.ManyToManyField('Vehiculo', blank=True, related_name='repuestos_externos_compatibles')
    
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


# ========================
# SISTEMA DE AUDITORÍA Y REGISTRO DE EVENTOS
# ========================
# Este modelo registra todos los eventos importantes del sistema
# de forma independiente para análisis histórico, estadísticas
# y rastreo de movimientos, incluso si los registros originales
# son eliminados.

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
    
    # ========================
    # IDENTIFICACIÓN Y REFERENCIAS
    # ========================
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
    
    # ========================
    # TIPO Y FECHA DEL EVENTO
    # ========================
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
    
    # ========================
    # DATOS DEL VEHÍCULO (ALMACENADOS PARA HISTORIAL)
    # ========================
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
    
    # ========================
    # DATOS ESPECÍFICOS DEL EVENTO
    # ========================
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
    
    # ========================
    # METADATOS
    # ========================
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
    
    # ========================
    # CAMPOS PARA ESTADÍSTICAS Y ANÁLISIS
    # ========================
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
    
    # ========================
    # FECHA DE CREACIÓN DEL REGISTRO
    # ========================
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


# ========================
# RESUMEN DE TRABAJOS (VISTA MATERIALIZADA/VIRTUAL)
# ========================
# Este modelo puede ser usado para almacenar resúmenes calculados
# y mejorar el rendimiento de consultas frecuentes

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


# ========================
# SISTEMA DE BONOS E INCENTIVOS PARA MECÁNICOS
# ========================

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
    
    # Campos para cierre por período
    periodo_mes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Mes del Período",
        help_text="Mes del período (1-12)"
    )
    periodo_anio = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Año del Período",
        help_text="Año del período (ej: 2025)"
    )
    cerrado = models.BooleanField(
        default=False,
        verbose_name="Período Cerrado",
        help_text="Indica si este bono pertenece a un período cerrado"
    )
    
    class Meta:
        verbose_name = "Bono Generado"
        verbose_name_plural = "Bonos Generados"
        ordering = ['-fecha_generacion']
        indexes = [
            models.Index(fields=['mecanico', 'pagado']),
            models.Index(fields=['fecha_generacion']),
            models.Index(fields=['periodo_anio', 'periodo_mes']),
            models.Index(fields=['mecanico', 'periodo_anio', 'periodo_mes']),
        ]
    
    def __str__(self):
        estado = "Pagado" if self.pagado else "Pendiente"
        periodo = f" ({self.periodo_mes}/{self.periodo_anio})" if self.periodo_mes and self.periodo_anio else ""
        cerrado_texto = " [CERRADO]" if self.cerrado else ""
        return f"Bono {self.mecanico} - Trabajo #{self.trabajo.id} - ${self.monto} ({estado}){periodo}{cerrado_texto}"
    
    @property
    def periodo_texto(self):
        """Retorna el período en formato texto (ej: 'Enero 2025')"""
        if not self.periodo_mes or not self.periodo_anio:
            return "Sin período"
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[self.periodo_mes]} {self.periodo_anio}"


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
    
    # Campos para cierre por período
    periodo_mes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Mes del Período",
        help_text="Mes del período (1-12)"
    )
    periodo_anio = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Año del Período",
        help_text="Año del período (ej: 2025)"
    )
    
    class Meta:
        verbose_name = "Pago a Mecánico"
        verbose_name_plural = "Pagos a Mecánicos"
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['mecanico', 'fecha_pago']),
            models.Index(fields=['periodo_anio', 'periodo_mes']),
        ]
    
    def __str__(self):
        periodo = f" ({self.periodo_mes}/{self.periodo_anio})" if self.periodo_mes and self.periodo_anio else ""
        return f"Pago {self.mecanico} - ${self.monto} - {self.fecha_pago.strftime('%d/%m/%Y')}{periodo}"
    
    @property
    def periodo_texto(self):
        """Retorna el período en formato texto (ej: 'Enero 2025')"""
        if not self.periodo_mes or not self.periodo_anio:
            return "Sin período"
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[self.periodo_mes]} {self.periodo_anio}"
    
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
                # Sincronizar período del pago al bono si no tiene período
                if not bono.periodo_mes or not bono.periodo_anio:
                    if self.periodo_mes and self.periodo_anio:
                        bono.periodo_mes = self.periodo_mes
                        bono.periodo_anio = self.periodo_anio
                bono.save()


class CierrePeriodo(models.Model):
    """
    Representa un cierre de período de bonos (mes/año).
    Permite agrupar y cerrar bonos de un período específico.
    """
    mecanico = models.ForeignKey(
        Mecanico,
        on_delete=models.CASCADE,
        related_name='cierres_periodo',
        verbose_name="Mecánico"
    )
    periodo_mes = models.PositiveIntegerField(
        verbose_name="Mes",
        help_text="Mes del período (1-12)"
    )
    periodo_anio = models.PositiveIntegerField(
        verbose_name="Año",
        help_text="Año del período (ej: 2025)"
    )
    fecha_cierre = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Cierre"
    )
    cerrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Cerrado por"
    )
    total_bonos = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Bonos del Período"
    )
    total_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Total Pagado del Período"
    )
    saldo_pendiente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Pendiente"
    )
    notas = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notas",
        help_text="Notas sobre el cierre del período"
    )
    
    class Meta:
        verbose_name = "Cierre de Período"
        verbose_name_plural = "Cierres de Períodos"
        ordering = ['-periodo_anio', '-periodo_mes']
        unique_together = ['mecanico', 'periodo_mes', 'periodo_anio']
        indexes = [
            models.Index(fields=['mecanico', 'periodo_anio', 'periodo_mes']),
            models.Index(fields=['periodo_anio', 'periodo_mes']),
        ]
    
    def __str__(self):
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"Cierre {self.mecanico} - {meses[self.periodo_mes]} {self.periodo_anio}"
    
    @property
    def periodo_texto(self):
        """Retorna el período en formato texto (ej: 'Enero 2025')"""
        meses = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return f"{meses[self.periodo_mes]} {self.periodo_anio}"
    
    def calcular_totales(self):
        """
        Calcula los totales del período basándose en los bonos.
        Total pagado se calcula como suma de bonos marcados como pagados (no de pagos registrados).
        """
        # Bonos del período
        bonos_periodo = BonoGenerado.objects.filter(
            mecanico=self.mecanico,
            periodo_mes=self.periodo_mes,
            periodo_anio=self.periodo_anio
        )
        
        self.total_bonos = bonos_periodo.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        # Total pagado: suma de bonos marcados como pagados (no de pagos registrados)
        # Esto es consistente con el cálculo en la vista cuenta_mecanico
        bonos_pagados = bonos_periodo.filter(pagado=True)
        self.total_pagado = bonos_pagados.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        # Saldo pendiente
        bonos_pendientes = bonos_periodo.filter(pagado=False)
        self.saldo_pendiente = bonos_pendientes.aggregate(
            total=Sum('monto')
        )['total'] or Decimal('0')
        
        self.save()
    
    def cerrar_periodo(self, usuario=None):
        """
        Cierra el período marcando todos los bonos como cerrados.
        """
        bonos_periodo = BonoGenerado.objects.filter(
            mecanico=self.mecanico,
            periodo_mes=self.periodo_mes,
            periodo_anio=self.periodo_anio
        )
        
        bonos_periodo.update(cerrado=True)
        
        if usuario:
            self.cerrado_por = usuario
            self.save()
        
        self.calcular_totales()

