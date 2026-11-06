"""
Context processors para hacer disponibles variables globales en todos los templates
"""
from .models import AdministracionTaller
from django.urls import reverse


CONTEXT_MENUS = {
    "administracion": {
        "parent": ("panel_principal", "#administracion", "⚙️", "Administración"),
        "items": [
            ("configuracion_bonos", "💰", "Bonos"),
            ("administracion_taller", "🏢", "Taller"),
            ("gestion_usuarios", "👥", "Usuarios"),
        ],
    },
    "taller": {
        "parent": ("panel_principal", "#taller", "🔧", "Taller"),
        "items": [
            ("cliente_taller_list", "👥", "Clientes"),
            ("vehiculo_list", "🚗", "Vehículos"),
            ("componente_list", "⚙️", "Componentes"),
            ("accion_list", "🔨", "Acciones"),
            ("mecanico_list", "👷", "Mecánicos"),
        ],
    },
    "diagnostico": {
        "parent": ("panel_principal", "#taller", "📋", "Diagnóstico"),
        "items": [
            ("ingreso", "➕", "Nuevo"),
            ("ingreso_rapido", "⚡", "Rápido"),
            ("lista_diagnosticos", "📋", "Diagnósticos"),
            ("lista_trabajos", "🚗", "Trabajos"),
            ("historial_trabajos", "📜", "Historial"),
        ],
    },
    "inventario": {
        "parent": ("panel_principal", "#pos", "📦", "Inventario"),
        "items": [
            ("repuesto_list", "📦", "Repuestos"),
            ("repuesto_compatibilidad", "🚗", "Compatibilidad"),
            ("compra_dashboard", "📥", "Compras"),
        ],
    },
    "pos": {
        "parent": ("panel_principal", "#pos", "🛒", "POS"),
        "items": [
            ("pos_principal", "🛒", "Ventas"),
            ("ventas_historial", "📜", "Historial"),
            ("pos_historial_cotizaciones", "📋", "Cotizaciones"),
        ],
    },
    "compras": {
        "parent": ("panel_principal", "#pos", "📥", "Compras"),
        "items": [
            ("compra_dashboard", "📥", "Resumen"),
            ("compra_list", "📋", "Compras"),
            ("compra_create", "➕", "Nueva"),
        ],
    },
}


URL_MENU_GROUPS = {
    "pizarra_estado": "pizarra",
    "trabajo_detalle": "trabajo",
    "configuracion_bonos": "administracion",
    "editar_configuracion_bono": "administracion",
    "eliminar_configuracion_bono": "administracion",
    "lista_mecanicos_bonos": "administracion",
    "cuenta_mecanico": "administracion",
    "registrar_pago_mecanico": "administracion",
    "eliminar_pago": "administracion",
    "crear_cierre_periodo": "administracion",
    "lista_cierres_periodo": "administracion",
    "eliminar_cierre_periodo": "administracion",
    "excepcion_bono_trabajo": "administracion",
    "eliminar_excepcion_bono": "administracion",
    "eliminar_bono": "administracion",
    "pago_mecanico": "administracion",
    "administracion_taller": "administracion",
    "gestion_usuarios": "administracion",
    "cliente_taller_list": "taller",
    "vehiculo_list": "taller",
    "componente_list": "taller",
    "accion_list": "taller",
    "mecanico_list": "taller",
    "ingreso": "diagnostico",
    "ingreso_rapido": "diagnostico",
    "lista_diagnosticos": "diagnostico",
    "lista_trabajos": "diagnostico",
    "historial_trabajos": "diagnostico",
    "editar_diagnostico": "diagnostico",
    "eliminar_diagnostico": "diagnostico",
    "ingreso_exitoso": "diagnostico",
    "ingreso_voz": "diagnostico",
    "relacionar_repuestos_componentes": "diagnostico",
    "repuesto_list": "inventario",
    "repuesto_compatibilidad": "inventario",
    "repuesto_create": "inventario",
    "repuesto_detail": "inventario",
    "repuesto_update": "inventario",
    "repuesto_delete": "inventario",
    "vehiculo_compatibilidad_list": "inventario",
    "vehiculo_compatibilidad_create": "inventario",
    "vehiculo_compatibilidad_detail": "inventario",
    "vehiculo_compatibilidad_update": "inventario",
    "vehiculo_compatibilidad_delete": "inventario",
    "pos_principal": "pos",
    "ventas_historial": "pos",
    "pos_historial_cotizaciones": "pos",
    "pos_procesar_venta": "pos",
    "pos_venta_detalle": "pos",
    "pos_configuracion": "pos",
    "pos_procesar_cotizacion": "pos",
    "pos_cotizacion_detalle": "pos",
    "pos_convertir_cotizacion": "pos",
    "pos_dashboard": "pos",
    "compra_dashboard": "compras",
    "compra_list": "compras",
    "compra_create": "compras",
    "compra_detail": "compras",
    "compra_edit": "compras",
    "compra_confirmar": "compras",
    "compra_cancelar": "compras",
    "compra_recibir": "compras",
    "compra_item_edit": "compras",
    "compra_item_delete": "compras",
    "compra_item_recibir": "compras",
    "cliente_create": "taller",
    "cliente_update": "taller",
    "cliente_delete": "taller",
    "cliente_taller_create": "taller",
    "cliente_taller_update": "taller",
    "cliente_taller_delete": "taller",
    "vehiculo_create": "taller",
    "vehiculo_update": "taller",
    "vehiculo_delete": "taller",
    "mecanico_create": "taller",
    "mecanico_update": "taller",
    "mecanico_delete": "taller",
    "componente_create": "taller",
    "componente_update": "taller",
    "componente_delete": "taller",
    "accion_create": "taller",
    "accion_update": "taller",
    "accion_delete": "taller",
    "comp_accion_list": "taller",
    "comp_accion_create": "taller",
    "comp_accion_update": "taller",
    "comp_accion_delete": "taller",
}


def configuracion_taller(request):
    """
    Hace disponible la configuración del taller en todos los templates
    Incluye ver_avisos y ver_mensajes para controlar avisos y mensajes
    """
    config = AdministracionTaller.get_configuracion_activa()
    url_name = request.resolver_match.url_name if request.resolver_match else None
    menu_group = URL_MENU_GROUPS.get(url_name)
    menu = CONTEXT_MENUS.get(menu_group)
    context_menu = None
    if url_name == "panel_principal":
        context_menu = {
            "group": "panel",
            "parent": None,
            "items": [
                {"target": "#pizarra", "icon": "📊", "label": "Pizarra", "active": True},
                {"target": "#inicio", "icon": "🏠", "label": "Inicio", "active": False},
                {"target": "#taller", "icon": "🔧", "label": "Taller", "active": False},
                {"target": "#pos", "icon": "🛒", "label": "POS", "active": False},
                {"target": "#administracion", "icon": "⚙️", "label": "Administración", "active": False},
            ],
        }
    elif url_name == "trabajo_detalle":
        trabajo_id = request.resolver_match.kwargs.get("pk")
        base_url = reverse("trabajo_detalle", kwargs={"pk": trabajo_id})
        tabs = [("info", "📋", "Información"), ("acciones", "🛠️", "Acciones"),
                ("repuestos", "🔧", "Repuestos"), ("insumos", "📦", "Insumos"),
                ("adicionales", "➕", "Adicionales"), ("fotos", "📷", "Fotos"),
                ("abonos", "💵", "Abonos"), ("estado", "⚡", "Estado")]
        active_tab = request.GET.get("tab", "info")
        # Volver al último tablero de estado visitado, incluso al cambiar de pestaña.
        estado_origen = request.session.get("pizarra_estado_origen")
        if estado_origen in ("iniciados", "progreso", "completados", "entregados"):
            url_retorno = reverse("pizarra_estado", kwargs={"estado": estado_origen})
        else:
            url_retorno = f"{reverse('panel_principal')}#pizarra"
        context_menu = {
            "group": "trabajo",
            "parent": {"url": url_retorno, "icon": "📊", "label": "Pizarra"},
            "items": [
                {"url": f"{base_url}?tab={tab}", "icon": icon, "label": label, "active": tab == active_tab}
                for tab, icon, label in tabs
            ],
        }
    elif url_name == "pizarra_estado":
        estado = request.resolver_match.kwargs.get("estado", "")
        estados = {
            "iniciados": ("🟡", "Iniciados"),
            "progreso": ("🔵", "En progreso"),
            "completados": ("🟢", "Completados"),
            "entregados": ("⚫", "Entregados"),
        }
        # Conservar el nivel de pizarra desde el que se abrirá un trabajo.
        if estado in estados:
            request.session["pizarra_estado_origen"] = estado
        context_menu = {
            "group": "pizarra",
            "parent": {"url": f"{reverse('panel_principal')}#pizarra", "icon": "📊", "label": "Pizarra"},
            "items": [
                {"url": reverse("pizarra_estado", kwargs={"estado": slug}), "icon": icon,
                 "label": label, "active": slug == estado}
                for slug, (icon, label) in estados.items()
            ],
        }
    elif menu:
        parent_name, parent_fragment, parent_icon, parent_label = menu["parent"]
        context_menu = {
            "group": menu_group,
            "parent": {
                "url": f"{reverse(parent_name)}{parent_fragment}",
                "icon": parent_icon,
                "label": parent_label,
            },
            "items": [
                {"url": reverse(name), "icon": icon, "label": label, "active": name == url_name}
                for name, icon, label in menu["items"]
            ],
        }

    return {
        'config_taller': config,
        'ver_avisos': config.ver_avisos,
        'ver_mensajes': config.ver_mensajes,
        'context_menu': context_menu,
    }






