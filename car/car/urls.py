from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.utils.timezone import now
from django.shortcuts import redirect
from .import views
from .views_api import vehiculo_lookup
from .views import ClienteListView, ClienteTallerListView, ClienteTallerCreateView, ClienteTallerUpdateView, ClienteTallerDeleteView, cliente_taller_lookup, VehiculoListView,\
                   VehiculoCreateView,VehiculoUpdateView,\
                   VehiculoDeleteView,MecanicoListView,\
                   MecanicoDeleteView,MecanicoCreateView,\
                   MecanicoUpdateView,RepuestoCreateView,\
                   RepuestoUpdateView,RepuestoDeleteView,\
                   RepuestoListView
from . import views_pos 

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    # === Componentes ===
    path('componentes/', views.componente_list, name='componente_list'),
    path('componentes/nuevo/', views.componente_create, name='componente_create'),
    path('componentes/<int:pk>/editar/', views.componente_update, name='componente_update'),
    path('componentes/<int:pk>/eliminar/', views.componente_delete, name='componente_delete'),
    path('componentes-lookup/', views.componentes_lookup, name='componentes_lookup'),
    path('componentes/seleccionar/<str:codigo>/', views.seleccionar_componente, name='seleccionar_componente'),

    # === Ingreso / Diagnóstico ===
    path('ingreso/', views.ingreso_view, name='ingreso'),
    path('ingreso/exito/', views.ingreso_exitoso_view, name='ingreso_exitoso'),
    path('ingreso/editar/<int:pk>/', views.editar_diagnostico, name='editar_diagnostico'),
    path('ingreso/eliminar/<int:pk>/', views.eliminar_diagnostico, name='eliminar_diagnostico'),
    path('diagnosticos/', views.lista_diagnosticos, name='lista_diagnosticos'),

    # === Plano interactivo ===
    path('plano/', views.mostrar_plano, name='plano_interactivo'),

    # === Acciones ===
    path('acciones/', views.accion_list, name='accion_list'),
    path('acciones/nueva/', views.accion_create, name='accion_create'),
    path('acciones/<int:pk>/editar/', views.accion_update, name='accion_update'),
    path('acciones/<int:pk>/eliminar/', views.accion_delete, name='accion_delete'),
    path('car/acciones-lookup/<int:componente_id>/', views.acciones_por_componente, name='acciones_por_componente'),
    path("vehiculo_lookup/", vehiculo_lookup, name="vehiculo_lookup"),

    # === Componente + Acción (precios) ===
    path('componente-acciones/', views.comp_accion_list, name='comp_accion_list'),
    path('componente-acciones/nuevo/', views.comp_accion_create, name='comp_accion_create'),
    path('componente-acciones/<int:pk>/editar/', views.comp_accion_update, name='comp_accion_update'),
    path('componente-acciones/<int:pk>/eliminar/', views.comp_accion_delete, name='comp_accion_delete'),

    # === Repuestos sugeridos ===
    path('diagnostico/sugerir-repuestos/', views.sugerir_repuestos, name='sugerir_repuestos_preview'),
    path('diagnostico/<int:diagnostico_id>/sugerir-repuestos/', views.sugerir_repuestos, name='sugerir_repuestos'),
    path("diagnosticos/excel/", views.exportar_diagnosticos_excel, name="diagnosticos_excel"),
    path("diagnosticos/pdf/", views.exportar_diagnosticos_pdf, name="diagnosticos_pdf"),
    path("diagnosticos/<int:pk>/excel/", views.exportar_diagnostico_excel, name="diagnostico_excel"),
    path("diagnosticos/<int:pk>/pdf/", views.exportar_diagnostico_pdf, name="diagnostico_pdf"),
    path("diagnostico/<int:pk>/aprobar/", views.aprobar_diagnostico, name="aprobar_diagnostico"),
    # === CRUD de repuestos en diagnóstico ===
    path('diagnostico/<int:diagnostico_id>/agregar-repuesto/', views.agregar_repuesto, name='agregar_repuesto'),
    path('diagnostico/<int:diagnostico_id>/repuestos/', views.listar_repuestos_diagnostico, name='listar_repuestos_diagnostico'),
    # Mecanicos
    path("mecanicos/", MecanicoListView.as_view(), name="mecanico_list"),
    path("mecanicos/nuevo/", views.MecanicoCreateView.as_view(), name="mecanico_create"),
    path("mecanicos/<int:pk>/editar/", views.MecanicoUpdateView.as_view(), name="mecanico_update"),
    path("mecanicos/<int:pk>/eliminar/", views.MecanicoDeleteView.as_view(), name="mecanico_delete"),
    # Clientes (legacy)
    path("clientes/", ClienteListView.as_view(), name="cliente_list"),
    path("clientes/nuevo/", views.ClienteCreateView.as_view(), name="cliente_create"),
    path("clientes/<int:pk>/editar/", views.ClienteUpdateView.as_view(), name="cliente_update"),
    path("clientes/<int:pk>/eliminar/", views.ClienteDeleteView.as_view(), name="cliente_delete"),
    
    # Clientes del Taller (nuevo sistema)
    path("clientes-taller/", ClienteTallerListView.as_view(), name="cliente_taller_list"),
    path("clientes-taller/nuevo/", ClienteTallerCreateView.as_view(), name="cliente_taller_create"),
    path("clientes-taller/<str:pk>/editar/", ClienteTallerUpdateView.as_view(), name="cliente_taller_update"),
    path("clientes-taller/<str:pk>/eliminar/", ClienteTallerDeleteView.as_view(), name="cliente_taller_delete"),
    path("clientes-taller/lookup/", cliente_taller_lookup, name="cliente_taller_lookup"),
    # Vehículos
    path("vehiculos/", VehiculoListView.as_view(), name="vehiculo_list"),
    path("vehiculos/nuevo/", VehiculoCreateView.as_view(), name="vehiculo_create"),
    path("vehiculos/<int:pk>/editar/", VehiculoUpdateView.as_view(), name="vehiculo_update"),
    path("vehiculos/<int:pk>/eliminar/", VehiculoDeleteView.as_view(), name="vehiculo_delete"),
    # Trabajos
    path("trabajos/", views.lista_trabajos, name="lista_trabajos"),
    path("trabajos/<int:pk>/", views.trabajo_detalle, name="trabajo_detalle"),
    path("trabajos/<int:pk>/pdf/", views.trabajo_pdf, name="trabajo_pdf"),
    path("trabajos/<int:pk>/eliminar/", views.TrabajoDeleteView.as_view(), name="trabajo_delete"),
    # Pizarra
    path("pizarra/", views.pizarra_view, name="pizarra"),
    # Ventas
    path("crear/", views.venta_crear, name="venta_crear"),
    path("<int:pk>/", views.venta_detalle, name="venta_detalle"),
    path("historial/", views.ventas_historial, name="ventas_historial"),
    path("repuesto-lookup/", views.repuesto_lookup, name="repuesto_lookup"),
    # Repuestos
    path("repuestos/", RepuestoListView.as_view(), name="repuesto_list"),
    path("repuestos/nuevo/", RepuestoCreateView.as_view(), name="repuesto_create"),
    path("repuestos/<int:pk>/editar/", RepuestoUpdateView.as_view(), name="repuesto_update"),
    path("repuestos/<int:pk>/eliminar/", RepuestoDeleteView.as_view(), name="repuesto_delete"),
    # Seguimiento público por placa
    path("tracking/", views.tracking_publico, name="tracking_publico"),
    path("tracking/placa/", views.tracking_publico_preview, name="tracking_publico_preview"),

    # === MÓDULO POS (Point of Sale) ===
    path("pos/", views_pos.pos_principal, name="pos_principal"),
    path("pos/buscar/", views_pos.buscar_repuestos_pos, name="pos_buscar_repuestos"),
    path("pos/agregar-carrito/", views_pos.agregar_al_carrito, name="pos_agregar_carrito"),
    path("pos/actualizar-carrito/<int:item_id>/", views_pos.actualizar_carrito_item, name="pos_actualizar_carrito"),
    path("pos/eliminar-carrito/<int:item_id>/", views_pos.eliminar_carrito_item, name="pos_eliminar_carrito"),
    path("pos/limpiar-carrito/", views_pos.limpiar_carrito, name="pos_limpiar_carrito"),
    path("pos/procesar-venta/", views_pos.procesar_venta, name="pos_procesar_venta"),
    path("pos/venta/<int:venta_id>/", views_pos.pos_venta_detalle, name="pos_venta_detalle"),
    path("pos/historial/", views_pos.pos_historial_ventas, name="pos_historial_ventas"),
    path("pos/configuracion/", views_pos.pos_configuracion, name="pos_configuracion"),
    path("pos/crear-cliente/", views_pos.crear_cliente_rapido, name="pos_crear_cliente"),
    path("pos/cerrar-sesion/", views_pos.cerrar_sesion_pos, name="pos_cerrar_sesion"),
    path("pos/dashboard/", views_pos.pos_dashboard, name="pos_dashboard"),
    
    # === COTIZACIONES ===
    path("pos/procesar-cotizacion/", views_pos.procesar_cotizacion, name="pos_procesar_cotizacion"),
    path("pos/cotizacion/<int:cotizacion_id>/", views_pos.pos_cotizacion_detalle, name="pos_cotizacion_detalle"),
    path("pos/historial-cotizaciones/", views_pos.pos_historial_cotizaciones, name="pos_historial_cotizaciones"),
    path("pos/convertir-cotizacion/<int:cotizacion_id>/", views_pos.convertir_cotizacion_a_venta, name="convertir_cotizacion_a_venta"),
    
    # === ADMINISTRACIÓN DEL TALLER ===
    path("administracion/", views.administracion_taller, name="administracion_taller"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#if settings.DEBUG:
#    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


