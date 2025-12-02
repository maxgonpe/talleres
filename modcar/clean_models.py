#!/usr/bin/env python3
"""
Script para limpiar modelos duplicados y ajustar importaciones
"""
import re
from pathlib import Path

# Mapeo de apps y sus modelos
APPS_MODELS = {
    'core': ['Cliente_Taller', 'Vehiculo', 'Componente', 'Accion', 'ComponenteAccion', 'VehiculoVersion', 'PrefijoRepuesto'],
    'diagnosticos': ['Diagnostico', 'DiagnosticoComponenteAccion', 'DiagnosticoRepuesto', 'Reparacion'],
    'trabajos': ['Trabajo', 'TrabajoAccion', 'TrabajoRepuesto', 'TrabajoAbono', 'TrabajoAdicional', 'TrabajoFoto'],
    'inventario': ['Repuesto', 'RepuestoEnStock', 'StockMovimiento', 'RepuestoExterno', 'ComponenteRepuesto', 'RepuestoAplicacion'],
    'punto_venta': ['SesionVenta', 'CarritoItem', 'VentaPOS', 'VentaPOSItem', 'ConfiguracionPOS', 'Cotizacion', 'CotizacionItem', 'Venta', 'VentaItem'],
    'compras': ['Compra', 'CompraItem'],
    'usuarios': ['Mecanico'],
    'bonos': ['ConfiguracionBonoMecanico', 'ExcepcionBonoTrabajo', 'BonoGenerado', 'PagoMecanico'],
    'configuracion': ['AdministracionTaller'],
    'estadisticas': ['RegistroEvento', 'ResumenTrabajo'],
}

# Imports necesarios por app
IMPORTS_BY_APP = {
    'core': [
        "from django.db import models",
        "from django.contrib.auth.models import User",
        "from django.utils.text import slugify",
    ],
    'inventario': [
        "from django.db import models",
        "from django.db.models import Sum",
        "from django.conf import settings",
        "from decimal import Decimal",
        "from django.utils.crypto import get_random_string",
        "from django.contrib.auth.models import User",
        "from core.models import Componente, VehiculoVersion",
    ],
    'diagnosticos': [
        "from django.db import models",
        "from django.db.models import Sum",
        "from decimal import Decimal",
        "from django.db import transaction",
        "from core.models import Vehiculo, Componente",
        "from inventario.models import Repuesto, RepuestoExterno",
    ],
    'trabajos': [
        "from django.db import models",
        "from django.db.models import Sum",
        "from decimal import Decimal",
        "from django.conf import settings",
        "from core.models import Vehiculo, Componente",
        "from diagnosticos.models import Diagnostico",
        "from inventario.models import Repuesto, RepuestoExterno",
        "from usuarios.models import Mecanico",
    ],
    'punto_venta': [
        "from django.db import models",
        "from django.conf import settings",
        "from core.models import Cliente_Taller",
        "from inventario.models import Repuesto, RepuestoEnStock, StockMovimiento",
    ],
    'compras': [
        "from django.db import models",
        "from django.conf import settings",
        "from django.utils.timezone import now",
        "from inventario.models import Repuesto, RepuestoEnStock, StockMovimiento",
    ],
    'usuarios': [
        "from django.db import models",
        "from django.db.models import Sum",
        "from django.conf import settings",
        "from decimal import Decimal",
        "from django.contrib.auth.models import User",
        "from bonos.models import BonoGenerado, ConfiguracionBonoMecanico, PagoMecanico",
    ],
    'bonos': [
        "from django.db import models",
        "from django.db.models import Sum",
        "from decimal import Decimal",
        "from django.conf import settings",
        "from django.utils.timezone import now",
        "from django.contrib.auth.models import User",
        "from usuarios.models import Mecanico",
        "from trabajos.models import Trabajo",
    ],
    'configuracion': [
        "from django.db import models",
        "from django.contrib.auth.models import User",
    ],
    'estadisticas': [
        "from django.db import models",
        "from decimal import Decimal",
    ],
}

def clean_models_file(app_name, models_file):
    """Limpia y reorganiza un archivo de modelos"""
    if not models_file.exists():
        return
    
    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Separar en secciones
    lines = content.split('\n')
    
    # Encontrar la sección de modelos migrados
    migrados_start = None
    for i, line in enumerate(lines):
        if '# MODELOS MIGRADOS DESDE CAR' in line:
            migrados_start = i
            break
    
    if migrados_start is None:
        print(f"  ⚠️ No se encontró sección de modelos migrados en {app_name}")
        return
    
    # Extraer solo los modelos migrados
    migrados_content = '\n'.join(lines[migrados_start:])
    
    # Crear nuevo contenido con imports correctos
    new_content = f'"""\nModelos de {app_name}\n"""\n\n'
    
    # Agregar imports
    for imp in IMPORTS_BY_APP.get(app_name, []):
        new_content += imp + '\n'
    
    new_content += '\n'
    
    # Agregar modelos migrados (sin el comentario de sección)
    migrados_lines = migrados_content.split('\n')
    skip_until_model = False
    for line in migrados_lines:
        if '# MODELOS MIGRADOS DESDE CAR' in line or '# ========================' in line:
            continue
        if line.strip().startswith('#'):
            if 'class ' in line:
                skip_until_model = False
            elif skip_until_model:
                continue
        if re.match(r'^class \w+\(', line):
            skip_until_model = False
        new_content += line + '\n'
    
    # Escribir archivo limpio
    with open(models_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  ✓ Limpiado {app_name}/models.py")

def main():
    base_dir = Path('.')
    
    for app_name in APPS_MODELS.keys():
        models_file = base_dir / app_name / 'models.py'
        if models_file.exists():
            clean_models_file(app_name, models_file)
    
    print("\n✅ Limpieza completada!")

if __name__ == '__main__':
    main()



