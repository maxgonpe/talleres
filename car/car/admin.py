from django.contrib import admin
from .models import (
    Cliente, Cliente_Taller, Vehiculo, Mecanico,
    Diagnostico, DiagnosticoComponenteAccion, DiagnosticoRepuesto,
    Trabajo, TrabajoAccion, TrabajoRepuesto,TrabajoFoto,
    Componente, Accion, ComponenteAccion,
    Repuesto, RepuestoEnStock, StockMovimiento,
    VehiculoVersion, ComponenteRepuesto, RepuestoAplicacion,
    Venta, VentaItem, PrefijoRepuesto,
    # Modelos POS
    SesionVenta, CarritoItem, VentaPOS, VentaPOSItem, ConfiguracionPOS,
    # Modelos Cotizaciones
    Cotizacion, CotizacionItem,
    # Modelos Administración
    AdministracionTaller,
    # Modelos Compras
    Compra, CompraItem
)

@admin.register(Mecanico)
class MecanicoAdmin(admin.ModelAdmin):
    list_display = ('id', 'especialidad', 'fecha_ingreso','activo')
    search_fields = ('especialidad', 'fecha_ingreso')

# ======================
# Clientes y Vehículos
# ======================
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'telefono')
    search_fields = ('nombre', 'telefono')


@admin.register(Cliente_Taller)
class ClienteTallerAdmin(admin.ModelAdmin):
    list_display = ('rut', 'nombre', 'telefono', 'email', 'fecha_registro', 'activo')
    search_fields = ('rut', 'nombre', 'telefono', 'email')
    list_filter = ('activo', 'fecha_registro')
    readonly_fields = ('fecha_registro',)
    fieldsets = (
        ('Información Básica', {
            'fields': ('rut', 'nombre', 'telefono', 'email')
        }),
        ('Información Adicional', {
            'fields': ('direccion', 'activo'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('fecha_registro',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('id', 'placa', 'marca', 'modelo', 'anio')
    search_fields = ('placa', 'marca', 'modelo')


# ======================
# Catálogo de Componentes y Acciones
# ======================
class ComponenteAccionInline(admin.TabularInline):
    model = ComponenteAccion
    extra = 1
    autocomplete_fields = ['accion']


@admin.register(Componente)
class ComponenteAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    inlines = [ComponenteAccionInline]


@admin.register(Accion)
class AccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)


@admin.register(ComponenteAccion)
class ComponenteAccionAdmin(admin.ModelAdmin):
    list_display = ('componente', 'accion', 'precio_mano_obra')
    list_filter = ('componente', 'accion')
    search_fields = ('componente__nombre', 'accion__nombre')


# ======================
# Diagnóstico
# ======================
class DiagnosticoComponenteAccionInline(admin.TabularInline):
    model = DiagnosticoComponenteAccion
    extra = 1
    autocomplete_fields = ['componente', 'accion']


class DiagnosticoRepuestoInline(admin.TabularInline):
    model = DiagnosticoRepuesto
    extra = 1
    autocomplete_fields = ['repuesto']


@admin.register(Diagnostico)
class DiagnosticoAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehiculo', 'descripcion_problema', 'estado', 'fecha')
    list_filter = ('estado', 'fecha')
    search_fields = ('vehiculo__placa', 'vehiculo__marca', 'componentes__nombre')
    inlines = [DiagnosticoComponenteAccionInline, DiagnosticoRepuestoInline]


# ======================
# Trabajo (clonado desde Diagnóstico aprobado)
# ======================
class TrabajoAccionInline(admin.TabularInline):
    model = TrabajoAccion
    extra = 1
    autocomplete_fields = ['componente', 'accion']


class TrabajoRepuestoInline(admin.TabularInline):
    model = TrabajoRepuesto
    extra = 1
    autocomplete_fields = ['repuesto']


@admin.register(Trabajo)
class TrabajoAdmin(admin.ModelAdmin):
    list_display = ('id', 'vehiculo', 'estado', 'fecha_inicio', 'fecha_fin')
    list_filter = ('estado', 'fecha_inicio', 'fecha_fin')
    search_fields = ('vehiculo__placa', 'vehiculo__marca')
    inlines = [TrabajoAccionInline, TrabajoRepuestoInline]


# ======================
# Repuestos y Stock
# ======================

@admin.register(PrefijoRepuesto)
class PrefijoRepuestoAdmin(admin.ModelAdmin):
    list_display = ("palabra", "abreviatura")
    search_fields = ("palabra", "abreviatura")


@admin.register(Repuesto)
class RepuestoAdmin(admin.ModelAdmin):
    list_display = ('id', 'sku', 'oem', 'referencia', 'nombre', 'precio_costo', 'precio_venta', 'stock', 'origen_repuesto', 'marca_veh')
    search_fields = ('nombre', 'oem', 'sku', 'codigo_barra', 'origen_repuesto', 'cod_prov', 'marca_veh', 'tipo_de_motor')
    list_filter = ("marca", "posicion", "origen_repuesto", "marca_veh")
    fieldsets = (
        ('Información Básica', {
            'fields': ('sku', 'oem', 'referencia', 'nombre', 'marca', 'descripcion')
        }),
        ('Especificaciones', {
            'fields': ('medida', 'posicion', 'unidad', 'codigo_barra')
        }),
        ('Precios y Stock', {
            'fields': ('precio_costo', 'precio_venta', 'stock')
        }),
        ('Información Adicional', {
            'fields': ('origen_repuesto', 'cod_prov', 'marca_veh', 'tipo_de_motor'),
            'classes': ('collapse',)
        }),
    )



@admin.register(ComponenteRepuesto)
class ComponenteRepuestoAdmin(admin.ModelAdmin):
    list_display = ('id', 'componente', 'repuesto', 'nota')

@admin.register(TrabajoAccion)
class TrabajoAccionAdmin(admin.ModelAdmin):
    list_display = ('id', 'trabajo','componente', 'accion', 'precio_mano_obra')


@admin.register(RepuestoAplicacion)
class RepuestoAplicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'repuesto', 'version', 'posicion', 'motor', 'carroceria')
    list_filter = ('repuesto__marca_veh', 'version__marca', 'version__modelo', 'motor', 'carroceria')
    search_fields = ('repuesto__nombre', 'repuesto__sku', 'version__marca', 'version__modelo', 'posicion', 'motor', 'carroceria')
    autocomplete_fields = ['repuesto', 'version']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('repuesto', 'version')
        }),
        ('Detalles de Aplicación', {
            'fields': ('posicion', 'motor', 'carroceria')
        }),
    )

@admin.register(VehiculoVersion)
class VehiculoVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'marca', 'modelo', 'anio_desde', 'anio_hasta', 'motor', 'carroceria')
    list_filter = ('marca', 'anio_desde', 'anio_hasta', 'motor', 'carroceria')
    search_fields = ('marca', 'modelo', 'motor', 'carroceria')
    ordering = ('marca', 'modelo', 'anio_desde')
    
    fieldsets = (
        ('Información del Vehículo', {
            'fields': ('marca', 'modelo')
        }),
        ('Años de Aplicación', {
            'fields': ('anio_desde', 'anio_hasta')
        }),
        ('Especificaciones Técnicas', {
            'fields': ('motor', 'carroceria'),
            'classes': ('collapse',)
        }),
    )

@admin.register(RepuestoEnStock)
class RepuestoEnStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'repuesto', 'deposito', 'proveedor', 'stock', 'reservado', 'stock_disponible', 'precio_compra', 'precio_venta')
    list_filter = ('deposito', 'proveedor', 'repuesto__marca_veh')
    search_fields = ('repuesto__nombre', 'repuesto__sku', 'deposito', 'proveedor')
    autocomplete_fields = ['repuesto']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('repuesto', 'deposito', 'proveedor')
        }),
        ('Stock', {
            'fields': ('stock', 'reservado')
        }),
        ('Precios', {
            'fields': ('precio_compra', 'precio_venta')
        }),
    )
    
    def stock_disponible(self, obj):
        return obj.stock - obj.reservado
    stock_disponible.short_description = 'Stock Disponible'

admin.site.register(StockMovimiento)
#admin.site.register(TrabajoAccion)
admin.site.register(TrabajoFoto)
admin.site.register(TrabajoRepuesto)
admin.site.register(Venta)
admin.site.register(VentaItem)

# ======================
# ADMIN PARA SISTEMA POS
# ======================

@admin.register(SesionVenta)
class SesionVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'fecha_inicio', 'fecha_fin', 'activa', 'total_ventas', 'numero_ventas')
    list_filter = ('activa', 'fecha_inicio', 'usuario')
    search_fields = ('usuario__username',)
    readonly_fields = ('fecha_inicio', 'fecha_fin', 'total_ventas', 'numero_ventas')
    actions = ['cerrar_sesiones_activas', 'limpiar_sesiones_antiguas', 'limpiar_todas_las_sesiones']
    
    def cerrar_sesiones_activas(self, request, queryset):
        """Cerrar todas las sesiones activas"""
        from django.utils import timezone
        sesiones_cerradas = 0
        for sesion in SesionVenta.objects.filter(activa=True):
            sesion.activa = False
            sesion.fecha_fin = timezone.now()
            sesion.save()
            sesiones_cerradas += 1
        
        self.message_user(request, f'{sesiones_cerradas} sesiones activas cerradas.')
    cerrar_sesiones_activas.short_description = "Cerrar sesiones activas"
    
    def limpiar_sesiones_antiguas(self, request, queryset):
        """Limpiar sesiones inactivas de más de 1 día"""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_limite = timezone.now() - timedelta(days=1)
        sesiones_antiguas = SesionVenta.objects.filter(
            activa=False,
            fecha_fin__lt=fecha_limite
        )
        
        carritos_eliminados = 0
        for sesion in sesiones_antiguas:
            carritos_eliminados += sesion.carrito_items.count()
            sesion.carrito_items.all().delete()
        
        sesiones_eliminadas = sesiones_antiguas.count()
        sesiones_antiguas.delete()
        
        self.message_user(request, f'{sesiones_eliminadas} sesiones antiguas eliminadas y {carritos_eliminados} carritos limpiados.')
    limpiar_sesiones_antiguas.short_description = "Limpiar sesiones antiguas (más de 1 día)"
    
    def limpiar_todas_las_sesiones(self, request, queryset):
        """Limpiar TODAS las sesiones y carritos"""
        from django.utils import timezone
        
        # Cerrar sesiones activas
        sesiones_activas = SesionVenta.objects.filter(activa=True)
        for sesion in sesiones_activas:
            sesion.activa = False
            sesion.fecha_fin = timezone.now()
            sesion.save()
        
        # Contar antes de eliminar
        carritos_totales = CarritoItem.objects.count()
        sesiones_totales = SesionVenta.objects.count()
        
        # Eliminar todo
        CarritoItem.objects.all().delete()
        SesionVenta.objects.all().delete()
        
        self.message_user(request, f'Limpieza completa: {sesiones_totales} sesiones y {carritos_totales} carritos eliminados.')
    limpiar_todas_las_sesiones.short_description = "⚠️ LIMPIAR TODO (sesiones + carritos)"

@admin.register(CarritoItem)
class CarritoItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'sesion', 'repuesto', 'cantidad', 'precio_unitario', 'subtotal', 'agregado_en')
    list_filter = ('sesion__usuario', 'agregado_en')
    search_fields = ('repuesto__nombre', 'repuesto__sku')

class VentaPOSItemInline(admin.TabularInline):
    model = VentaPOSItem
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(VentaPOS)
class VentaPOSAdmin(admin.ModelAdmin):
    list_display = ('id', 'sesion', 'cliente', 'fecha', 'total', 'metodo_pago', 'pagado')
    list_filter = ('metodo_pago', 'pagado', 'fecha', 'sesion__usuario')
    search_fields = ('cliente__nombre', 'id')
    readonly_fields = ('fecha', 'subtotal', 'total')
    inlines = [VentaPOSItemInline]

@admin.register(VentaPOSItem)
class VentaPOSItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'venta', 'repuesto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('venta__fecha', 'venta__sesion__usuario')
    search_fields = ('repuesto__nombre', 'repuesto__sku')

@admin.register(ConfiguracionPOS)
class ConfiguracionPOSAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_empresa', 'telefono', 'imprimir_ticket', 'mostrar_descuentos')
    fieldsets = (
        ('Información de la Empresa', {
            'fields': ('nombre_empresa', 'direccion', 'telefono', 'ruc')
        }),
        ('Configuración de Ventas', {
            'fields': ('imprimir_ticket', 'mostrar_descuentos', 'permitir_venta_sin_stock', 'margen_ganancia_default')
        }),
    )

# ======================
# ADMIN PARA COTIZACIONES
# ======================

class CotizacionItemInline(admin.TabularInline):
    model = CotizacionItem
    extra = 0
    readonly_fields = ('subtotal',)

@admin.register(Cotizacion)
class CotizacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'sesion', 'cliente', 'fecha', 'total', 'estado', 'valida_hasta')
    list_filter = ('estado', 'fecha', 'valida_hasta', 'sesion__usuario')
    search_fields = ('cliente__nombre', 'id')
    readonly_fields = ('fecha', 'subtotal', 'total')
    inlines = [CotizacionItemInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('sesion', 'cliente', 'fecha', 'estado')
        }),
        ('Detalles Financieros', {
            'fields': ('subtotal', 'descuento', 'total')
        }),
        ('Vigencia', {
            'fields': ('valida_hasta',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
    )

@admin.register(CotizacionItem)
class CotizacionItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cotizacion', 'repuesto', 'cantidad', 'precio_unitario', 'subtotal')
    list_filter = ('cotizacion__fecha', 'cotizacion__sesion__usuario')
    search_fields = ('repuesto__nombre', 'repuesto__sku')


@admin.register(AdministracionTaller)
class AdministracionTallerAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_taller', 'telefono', 'email', 'fecha_actualizacion')
    list_filter = ('fecha_creacion', 'fecha_actualizacion', 'tema_por_defecto')
    search_fields = ('nombre_taller', 'email', 'telefono')
    readonly_fields = ('fecha_creacion', 'fecha_actualizacion')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_taller', 'direccion', 'telefono', 'email', 'rut')
        }),
        ('Logos y Personalización', {
            'fields': ('logo_principal_png', 'logo_principal_svg', 'logo_secundario_png', 'imagen_fondo')
        }),
        ('Políticas de Seguridad', {
            'fields': ('sesion_timeout_minutos', 'intentos_login_maximos', 'bloqueo_temporal_horas', 
                      'requiere_cambio_password', 'dias_validez_password')
        }),
        ('Configuraciones del Sistema', {
            'fields': ('tema_por_defecto', 'mostrar_estadisticas_publicas', 
                      'permitir_registro_usuarios', 'notificaciones_email')
        }),
        ('Metadatos', {
            'fields': ('fecha_creacion', 'fecha_actualizacion', 'creado_por'),
            'classes': ('collapse',)
        }),
    )


# ======================
# ADMIN PARA COMPRAS
# ======================

class CompraItemInline(admin.TabularInline):
    model = CompraItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('repuesto', 'cantidad', 'precio_unitario', 'subtotal', 'recibido')

@admin.register(Compra)
class CompraAdmin(admin.ModelAdmin):
    list_display = ('numero_compra', 'proveedor', 'fecha_compra', 'estado', 'total', 'creado_por')
    list_filter = ('estado', 'fecha_compra', 'fecha_recibida', 'creado_por')
    search_fields = ('numero_compra', 'proveedor', 'observaciones')
    readonly_fields = ('numero_compra', 'creado_en', 'actualizado_en', 'total')
    inlines = [CompraItemInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('numero_compra', 'proveedor', 'fecha_compra', 'estado')
        }),
        ('Detalles Financieros', {
            'fields': ('total',)
        }),
        ('Recepción', {
            'fields': ('fecha_recibida',)
        }),
        ('Observaciones', {
            'fields': ('observaciones',)
        }),
        ('Metadatos', {
            'fields': ('creado_por', 'creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CompraItem)
class CompraItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'compra', 'repuesto', 'cantidad', 'precio_unitario', 'subtotal', 'recibido', 'fecha_recibido')
    list_filter = ('recibido', 'compra__estado', 'compra__fecha_compra')
    search_fields = ('repuesto__nombre', 'repuesto__sku', 'compra__numero_compra')
    readonly_fields = ('subtotal', 'fecha_recibido')