"""Panel privado de administración del sistema de diseño. No se publica en menús."""
import hashlib
import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

START = "/* === ESTILOS: INICIO DE AJUSTES ADMINISTRADOS === */"
END = "/* === ESTILOS: FIN DE AJUSTES ADMINISTRADOS === */"
VAR_RE = re.compile(r"^--[a-zA-Z][a-zA-Z0-9-]*$")
THEMES = {"piedra": "html.theme-piedra, html.theme-oscuro, html.theme-dark",
          "sand": "html.theme-sand, html.theme-claro",
          "base": ":root"}
# Contrato CSS-005B2: solo estos 20 tokens controlan las cards jerárquicas.
CARD_TOKENS = {
    f"--surface-level-{level}{suffix}"
    for level in range(1, 6)
    for suffix in ("", "-text", "-border", "-hover")
}
CARD_COLOR_RE = re.compile(r"#[0-9a-fA-F]{6}\Z")

LABELS = {
    "--app-background": ("Fondo general del sistema", "Superficies"),
    "--floating-menu-bg": ("Menú flotante · Fondo", "Menús flotantes"),
    "--floating-menu-border": ("Menú flotante · Borde exterior", "Menús flotantes"),
    "--floating-menu-icon": ("Menú flotante · Color de iconos", "Menús flotantes"),
    "--floating-menu-hover-bg": ("Menú flotante · Fondo al pasar mouse", "Menús flotantes"),
    "--floating-menu-hover-icon": ("Menú flotante · Icono al pasar mouse", "Menús flotantes"),
    "--floating-menu-active-bg": ("Menú flotante · Fondo del botón activo", "Menús flotantes"),
    "--floating-menu-active-icon": ("Menú flotante · Icono del botón activo", "Menús flotantes"),
    "--floating-menu-separator": ("Menú flotante · Separador entre niveles", "Menús flotantes"),
    "--surface-level-1": ("Card · Nivel 1", "Superficies"),
    "--surface-level-2": ("Card · Nivel 2", "Superficies"),
    "--surface-level-3": ("Card · Nivel 3", "Superficies"),
    "--surface-level-4": ("Card · Nivel 4", "Superficies"),
    "--surface-level-5": ("Card · Nivel 5", "Superficies"),
    "--surface-level-1-text": ("Card · Nivel 1 · Texto", "Cards jerárquicas"),
    "--surface-level-1-border": ("Card · Nivel 1 · Borde", "Cards jerárquicas"),
    "--surface-level-1-hover": ("Card · Nivel 1 · Fondo hover", "Cards jerárquicas"),
    "--surface-level-2-text": ("Card · Nivel 2 · Texto", "Cards jerárquicas"),
    "--surface-level-2-border": ("Card · Nivel 2 · Borde", "Cards jerárquicas"),
    "--surface-level-2-hover": ("Card · Nivel 2 · Fondo hover", "Cards jerárquicas"),
    "--surface-level-3-text": ("Card · Nivel 3 · Texto", "Cards jerárquicas"),
    "--surface-level-3-border": ("Card · Nivel 3 · Borde", "Cards jerárquicas"),
    "--surface-level-3-hover": ("Card · Nivel 3 · Fondo hover", "Cards jerárquicas"),
    "--surface-level-4-text": ("Card · Nivel 4 · Texto", "Cards jerárquicas"),
    "--surface-level-4-border": ("Card · Nivel 4 · Borde", "Cards jerárquicas"),
    "--surface-level-4-hover": ("Card · Nivel 4 · Fondo hover", "Cards jerárquicas"),
    "--surface-level-5-text": ("Card · Nivel 5 · Texto", "Cards jerárquicas"),
    "--surface-level-5-border": ("Card · Nivel 5 · Borde", "Cards jerárquicas"),
    "--surface-level-5-hover": ("Card · Nivel 5 · Fondo hover", "Cards jerárquicas"),
    "--text-heading": ("Texto de títulos", "Textos"),
    "--text-body": ("Texto general", "Textos"),
    "--text-secondary": ("Texto secundario", "Textos"),
    "--text-tertiary": ("Texto auxiliar", "Textos"),
    "--text-on-accent": ("Texto sobre acentos", "Textos"),
    "--surface-level-3-text": ("Texto de cards nivel 3", "Textos"),
    "--border-subtle": ("Borde suave", "Bordes"),
    "--border-default": ("Borde normal", "Bordes"),
    "--border-strong": ("Borde destacado", "Bordes"),
    "--ui-accent": ("Acento principal", "Botones y acentos"),
    "--ui-accent-strong": ("Acento intenso", "Botones y acentos"),
    "--btn-primary-bg": ("Botón primario · Fondo", "Botones y acentos"),
    "--btn-primary-hover": ("Botón primario · Hover", "Botones y acentos"),
    "--btn-primary-text": ("Botón primario · Texto", "Botones y acentos"),
    "--btn-secondary-bg": ("Botón secundario · Fondo", "Botones y acentos"),
    "--btn-secondary-hover": ("Botón secundario · Hover", "Botones y acentos"),
    "--ui-radius-sm": ("Radio pequeño", "Dimensiones"),
    "--ui-radius-md": ("Radio mediano", "Dimensiones"),
    "--ui-radius-lg": ("Radio grande", "Dimensiones"),
    "--ui-space-1": ("Espaciado 1", "Dimensiones"),
    "--ui-space-2": ("Espaciado 2", "Dimensiones"),
    "--ui-space-3": ("Espaciado 3", "Dimensiones"),
    "--ui-space-4": ("Espaciado 4", "Dimensiones"),
    "--ui-space-5": ("Espaciado 5", "Dimensiones"),
    "--ui-space-6": ("Espaciado 6", "Dimensiones"),
    "--heading-1-size": ("Título H1 · Tamaño", "Tipografía"),
    "--heading-2-size": ("Título H2 · Tamaño", "Tipografía"),
    "--heading-3-size": ("Título H3 · Tamaño", "Tipografía"),
}


def css_path():
    # Ruta de origen, no STATIC_ROOT, para mantener el archivo único.
    return Path(settings.BASE_DIR) / 'static' / 'css' / 'design-system.css'


def split_managed(source):
    if source.count(START) > 1 or source.count(END) > 1:
        raise ValueError('Se encontraron varias secciones administradas; no se guardará el CSS.')
    if START not in source and END not in source:
        return source.rstrip() + '\n', ''
    if START not in source or END not in source or source.index(END) < source.index(START):
        raise ValueError('Los delimitadores de estilos están incompletos.')
    before, rest = source.split(START, 1)
    managed, after = rest.split(END, 1)
    if after.strip():
        # No perder ajustes manuales posteriores; mantenerlos en la parte original.
        return (before.rstrip() + '\n' + after.lstrip()), managed
    return before.rstrip() + '\n', managed


def parse_blocks(css):
    """Lee las variables de selectores raíz/tema, sin dependencias externas."""
    from tinycss2 import parse_stylesheet, parse_declaration_list, serialize
    data = {theme: {} for theme in THEMES}
    for rule in parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if rule.type != 'qualified-rule':
            continue
        selector = serialize(rule.prelude).strip()
        # No leer selectores de componentes ni reglas anidadas; solo tokens de tema.
        selectors = {x.strip() for x in selector.split(',')}
        active = set()
        if ':root' in selectors:
            active.add('base')
        if selectors.intersection({'html.theme-piedra', 'html.theme-oscuro', 'html.theme-dark'}):
            active.add('piedra')
        if selectors.intersection({'html.theme-sand', 'html.theme-claro'}):
            active.add('sand')
        if not active:
            continue
        for declaration in parse_declaration_list(rule.content, skip_comments=True, skip_whitespace=True):
            if declaration.type == 'declaration' and declaration.name.startswith('--'):
                value = serialize(declaration.value).strip()
                for theme in active:
                    data[theme][declaration.name] = value
    return data


def validate_value(raw):
    """Valor CSS simple, sin posibilidad de insertar reglas, URLs ni código."""
    from tinycss2 import parse_component_value_list
    value = raw.strip()
    if not value or len(value) > 180 or any(c in value for c in '{};<>\\') or '/*' in value or '*/' in value:
        raise ValueError('Valor vacío o con caracteres no permitidos.')
    if '!' in value or re.search(r'(?i)(url\s*\(|@import|expression\s*\(|javascript:|data:)', value):
        raise ValueError('Este tipo de valor no está permitido.')
    tokens = parse_component_value_list(value)
    def check(items):
        for token in items:
            if token.type in {'error', 'url', 'bad-url', 'at-keyword'}:
                return False
            if token.type == 'function':
                if token.lower_name not in {'var', 'calc', 'min', 'max', 'clamp', 'rgb', 'rgba', 'hsl', 'hsla', 'color-mix'}:
                    return False
                if not check(token.arguments):
                    return False
            if token.type in {'() block', '[] block', '{} block'} and not check(token.content):
                return False
        return True
    if not check(tokens):
        raise ValueError('El valor contiene una función CSS no admitida.')
    return value


def render_section(changes):
    lines = [START, '/* Ajustes guardados desde /estilos/; no editar este bloque manualmente. */']
    for theme in ('base', 'piedra', 'sand'):
        values = changes.get(theme, {})
        if not values:
            continue
        lines.append(THEMES[theme] + ' {')
        for key in sorted(values):
            lines.append('  %s: %s;' % (key, values[key]))
        lines.append('}')
    lines.append(END)
    return '\n'.join(lines) + '\n'


def get_edition_state():
    path = css_path()
    source = path.read_text(encoding='utf-8')
    original, block = split_managed(source)
    base = parse_blocks(original)
    override = parse_blocks(block)
    for theme in THEMES:
        base[theme].update(override[theme])
    checksum = hashlib.sha256(source.encode('utf-8')).hexdigest()
    return source, original, override, base, checksum



def resolver_valor_visual(nombre, tema, datos, visitados=None):
    """Resuelve var(--token[, fallback]) desde el tema seleccionado.

    Mantiene la expresión original si la referencia no existe, es circular
    o necesita el motor CSS del navegador para calcularse.
    """
    import re
    valores = dict(datos.get('base', {}))
    if tema != 'base':
        valores.update(datos.get(tema, {}))
    visitados = set(visitados or ())
    if nombre in visitados:
        return valores.get(nombre, '')
    visitados.add(nombre)
    valor = valores.get(nombre, '')
    # Coincidencia de alias directo. No sustituimos arbitrariamente expresiones
    # complejas como color-mix(var(...)), calc(...) o fallbacks con paréntesis.
    patron = r'^var\(\s*(--[a-zA-Z][a-zA-Z0-9-]*)\s*(?:,\s*([^()]+))?\s*\)$'
    match = re.fullmatch(patron, valor.strip())
    if not match:
        return valor
    destino, alternativa = match.groups()
    if destino in visitados:
        return valor
    if destino not in valores:
        return alternativa.strip() if alternativa else valor
    resultado = resolver_valor_visual(destino, tema, datos, visitados)
    if resultado.strip().startswith('var('):
        return alternativa.strip() if alternativa else valor
    return resultado

def groups_for(theme, data):
    # Mostrar variables globales, incluso alias legacy: las dependientes son solo lectura.
    keys = sorted(set(data['base']) | set(data['piedra']) | set(data['sand']))
    ordered = {}
    for key in keys:
        current = data[theme].get(key, data['base'].get(key, ''))
        if not current:
            continue
        label, category = LABELS.get(key, (key[2:].replace('-', ' ').capitalize(), 'Otras variables'))
        if re.fullmatch(r'--surface-level-[1-5]', key):
            label, category = label + ' · Fondo', 'Cards jerárquicas'
        alias = current.strip().startswith('var(')
        resuelto = resolver_valor_visual(key, theme, data) if alias else current
        # Mostrar el resultado real resoluble como valor inicial editable.
        # Al guardar se crea un override del tema sin modificar el token de origen.
        editable = resuelto if resuelto and not resuelto.strip().startswith('var(') else current
        hexadecimal = bool(re.fullmatch(r'#[0-9a-fA-F]{6}', editable))
        # La fuente de cada valor se calcula exclusivamente para el tema elegido.
        # 'base' es un ámbito compartido, no sinónimo del tema visual de la página.
        source_scope = theme if key in data[theme] else 'base'
        info = {'key': key, 'label': label, 'value': editable,
                'source_value': current, 'alias': alias,
                'resolved': resuelto, 'color': hexadecimal, 'category': category,
                'source_scope': source_scope,
                'is_override': key in data[theme]}
        ordered.setdefault(category, []).append(info)
    priority = ['Cards jerárquicas', 'Superficies', 'Textos', 'Bordes', 'Botones y acentos', 'Menús flotantes', 'Dimensiones', 'Tipografía', 'Otras variables']
    return [{'name': cat, 'items': ordered[cat]} for cat in priority if cat in ordered]


def version_context(request):
    """Cache busting de CSS con mtime: cada guardado se refleja en otras pantallas."""
    try:
        version = str(css_path().stat().st_mtime_ns)
    except OSError:
        version = '0'
    return {'design_css_version': version}


@user_passes_test(lambda u: u.is_active and u.is_superuser, login_url='/admin/login/')
@require_http_methods(['GET', 'POST'])
def estilos(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden('Acceso reservado al superusuario.')
    try:
        source, original, overrides, data, checksum = get_edition_state()
    except (OSError, ValueError) as exc:
        logger.exception('Error leyendo CSS global')
        return render(request, 'car/estilos.html', {'error': str(exc), 'groups': [], 'theme': 'piedra'}, status=500)

    theme = request.POST.get('theme', request.GET.get('theme', 'piedra'))
    if theme not in THEMES:
        theme = 'piedra'

    if request.method == 'POST':
        name = request.POST.get('variable', '')
        raw_value = request.POST.get('value', '')
        if request.POST.get('checksum') != checksum:
            messages.error(request, 'El CSS cambió desde que abriste el editor. Recarga antes de guardar.')
        elif not VAR_RE.fullmatch(name) or name not in set().union(*[set(d) for d in data.values()]):
            messages.error(request, 'Variable inexistente o no autorizada.')
        else:
            try:
                value = validate_value(raw_value)
                if name in CARD_TOKENS and not CARD_COLOR_RE.fullmatch(value):
                    raise ValueError('Las variables de cards requieren un color hexadecimal de seis dígitos (#RRGGBB).')
                # Un alias puede adquirir un valor propio en el tema actual.
                # La variable de origen y el resto de temas permanecen intactos.
                overrides[theme][name] = value
                new_css = original.rstrip() + '\n\n' + render_section(overrides)
                path = css_path()
                if not os.access(path, os.W_OK):
                    raise PermissionError('El proceso Django no tiene permisos para escribir el CSS original.')
                # Backups fuera de static, para que no sean públicos.
                backup_dir = Path(settings.BASE_DIR) / 'estilos_backups'
                backup_dir.mkdir(mode=0o700, exist_ok=True)
                filename = 'design-system-' + datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.css.bak'
                shutil.copy2(path, backup_dir / filename)
                fd, tmpname = tempfile.mkstemp(prefix='.design-system-', suffix='.tmp', dir=path.parent)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        f.write(new_css)
                        f.flush()
                        os.fsync(f.fileno())
                    os.chmod(tmpname, path.stat().st_mode & 0o777)
                    os.replace(tmpname, path)
                finally:
                    if os.path.exists(tmpname):
                        os.unlink(tmpname)
                messages.success(request, 'Variable guardada. Se creó un respaldo automático.')
                return redirect(request.path + '?theme=' + theme)
            except (ValueError, OSError, PermissionError) as exc:
                messages.error(request, str(exc))
    return render(request, 'car/estilos.html', {
        'theme': theme, 'groups': groups_for(theme, data), 'checksum': checksum,
        'css_location': str(css_path()), 'total': sum(len(g['items']) for g in groups_for(theme, data)),
        'preview_variables': dict(data['base'], **data[theme]),
    })
