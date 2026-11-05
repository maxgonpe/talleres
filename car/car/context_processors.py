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
    "repuesto_list": "inventario",
    "repuesto_compatibilidad": "inventario",
    "pos_principal": "pos",
    "ventas_historial": "pos",
    "pos_historial_cotizaciones": "pos",
    "compra_dashboard": "compras",
    "compra_list": "compras",
    "compra_create": "compras",
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
    if menu:
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











