"""Catálogo controlado de iconos visuales para menús contextuales."""
from django.utils.text import slugify

SPECIALTIES = [
    ('auto', 'Automóviles'), ('moto', 'Motocicletas'),
    ('bici', 'Bicicletas'), ('maquinaria', 'Maquinaria y equipos'),
]

ICONS = [
    ('fa-house', 'Inicio'), ('fa-chart-line', 'Pizarra'), ('fa-screwdriver-wrench', 'Taller'),
    ('fa-gears', 'Administración'), ('fa-car-side', 'Automóvil'), ('fa-motorcycle', 'Motocicleta'),
    ('fa-bicycle', 'Bicicleta'), ('fa-tractor', 'Maquinaria'), ('fa-users', 'Clientes'),
    ('fa-user-gear', 'Mecánicos'), ('fa-toolbox', 'Herramientas'), ('fa-wrench', 'Reparación'),
    ('fa-clipboard-check', 'Diagnóstico'), ('fa-clipboard-list', 'Trabajos'),
    ('fa-list-check', 'Acciones'), ('fa-bolt', 'Rápido'), ('fa-plus', 'Nuevo'),
    ('fa-box-open', 'Repuestos'), ('fa-boxes-stacked', 'Inventario'),
    ('fa-cart-shopping', 'Ventas'), ('fa-cash-register', 'POS'), ('fa-receipt', 'Cotizaciones'),
    ('fa-truck-ramp-box', 'Recepción'), ('fa-basket-shopping', 'Compras'),
    ('fa-file-invoice-dollar', 'Bonos'), ('fa-money-bill-wave', 'Abonos'),
    ('fa-clock-rotate-left', 'Historial'), ('fa-camera', 'Fotos'),
    ('fa-circle-info', 'Información'), ('fa-gauge-high', 'Estado'),
    ('fa-circle-check', 'Completados'), ('fa-person-biking', 'En progreso'),
    ('fa-hourglass-start', 'Iniciados'), ('fa-flag-checkered', 'Entregados'),
    ('fa-warehouse', 'Insumos'), ('fa-puzzle-piece', 'Componentes'),
    ('fa-shield-halved', 'Usuarios'), ('fa-scale-balanced', 'Compatibilidad'),
    ('fa-chart-pie', 'Resumen'), ('fa-clipboard', 'Otros'),
]
ALLOWED_ICONS = {name for name, _ in ICONS}

MENU_SECTIONS = [
    ('panel', ['Pizarra', 'Inicio', 'Taller', 'POS', 'Administración']),
    ('pizarra', ['Pizarra', 'Iniciados', 'En progreso', 'Completados', 'Entregados']),
    ('trabajo', ['Pizarra', 'Información', 'Acciones', 'Repuestos', 'Insumos', 'Adicionales', 'Fotos', 'Abonos', 'Estado']),
    ('administracion', ['Administración', 'Bonos', 'Taller', 'Usuarios']),
    ('taller', ['Taller', 'Clientes', 'Vehículos', 'Componentes', 'Acciones', 'Mecánicos']),
    ('diagnostico', ['Diagnóstico', 'Nuevo', 'Rápido', 'Diagnósticos', 'Trabajos', 'Historial']),
    ('inventario', ['Inventario', 'Repuestos', 'Compatibilidad', 'Compras']),
    ('pos', ['POS', 'Ventas', 'Historial', 'Cotizaciones']),
    ('compras', ['Compras', 'Resumen', 'Nueva']),
]

DEFAULTS = {
    'Pizarra': 'fa-chart-line', 'Inicio': 'fa-house', 'Taller': 'fa-screwdriver-wrench',
    'Administración': 'fa-gears', 'Bonos': 'fa-file-invoice-dollar',
    'Usuarios': 'fa-shield-halved', 'Clientes': 'fa-users', 'Vehículos': 'fa-car-side',
    'Componentes': 'fa-puzzle-piece', 'Acciones': 'fa-list-check', 'Mecánicos': 'fa-user-gear',
    'Diagnóstico': 'fa-clipboard-check', 'Nuevo': 'fa-plus', 'Rápido': 'fa-bolt',
    'Diagnósticos': 'fa-clipboard-check', 'Trabajos': 'fa-clipboard-list',
    'Historial': 'fa-clock-rotate-left', 'Inventario': 'fa-boxes-stacked',
    'Repuestos': 'fa-box-open', 'Compatibilidad': 'fa-scale-balanced',
    'Compras': 'fa-basket-shopping', 'POS': 'fa-cash-register',
    'Ventas': 'fa-cart-shopping', 'Cotizaciones': 'fa-receipt',
    'Resumen': 'fa-chart-pie', 'Nueva': 'fa-plus', 'Información': 'fa-circle-info',
    'Insumos': 'fa-warehouse', 'Adicionales': 'fa-plus', 'Fotos': 'fa-camera',
    'Abonos': 'fa-money-bill-wave', 'Estado': 'fa-gauge-high',
    'Iniciados': 'fa-hourglass-start', 'En progreso': 'fa-person-biking',
    'Completados': 'fa-circle-check', 'Entregados': 'fa-flag-checkered',
}


def menu_key(group, label):
    return f'{group}.{slugify(label)}'


def default_icon(group, label, specialty='auto'):
    if label in ('Vehículos', 'Compatibilidad'):
        return {'auto': 'fa-car-side', 'moto': 'fa-motorcycle',
                'bici': 'fa-bicycle', 'maquinaria': 'fa-tractor'}.get(specialty, 'fa-car-side')
    return DEFAULTS.get(label, 'fa-clipboard')


def menu_icon(group, label, specialty='auto', overrides=None):
    candidate = (overrides or {}).get(menu_key(group, label))
    if isinstance(candidate, str) and candidate in ALLOWED_ICONS:
        return candidate
    return default_icon(group, label, specialty)


def editable_menu_items(config):
    overrides = config.iconos_menu if isinstance(config.iconos_menu, dict) else {}
    out = []
    for group, labels in MENU_SECTIONS:
        for label in labels:
            key = menu_key(group, label)
            out.append({'key': key, 'group': group.title(), 'label': label,
                        'selected': overrides.get(key, default_icon(group, label, config.tipo_taller))})
    return out
