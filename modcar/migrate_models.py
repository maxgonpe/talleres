#!/usr/bin/env python3
"""
Script para migrar modelos del proyecto car a modcar
Extrae y organiza los modelos según la estructura modular
"""
import re
import os
from pathlib import Path

# Mapeo de modelos a apps
MODEL_TO_APP = {
    # Core
    'Cliente_Taller': 'core',
    'Vehiculo': 'core',
    'Componente': 'core',
    'Accion': 'core',
    'ComponenteAccion': 'core',
    'VehiculoVersion': 'core',
    'PrefijoRepuesto': 'core',
    
    # Diagnosticos
    'Diagnostico': 'diagnosticos',
    'DiagnosticoComponenteAccion': 'diagnosticos',
    'DiagnosticoRepuesto': 'diagnosticos',
    'Reparacion': 'diagnosticos',
    
    # Trabajos
    'Trabajo': 'trabajos',
    'TrabajoAccion': 'trabajos',
    'TrabajoRepuesto': 'trabajos',
    'TrabajoAbono': 'trabajos',
    'TrabajoAdicional': 'trabajos',
    'TrabajoFoto': 'trabajos',
    
    # Inventario
    'Repuesto': 'inventario',
    'RepuestoEnStock': 'inventario',
    'StockMovimiento': 'inventario',
    'RepuestoExterno': 'inventario',
    'ComponenteRepuesto': 'inventario',
    'RepuestoAplicacion': 'inventario',
    
    # Punto de Venta
    'SesionVenta': 'punto_venta',
    'CarritoItem': 'punto_venta',
    'VentaPOS': 'punto_venta',
    'VentaPOSItem': 'punto_venta',
    'ConfiguracionPOS': 'punto_venta',
    'Cotizacion': 'punto_venta',
    'CotizacionItem': 'punto_venta',
    'Venta': 'punto_venta',
    'VentaItem': 'punto_venta',
    
    # Compras
    'Compra': 'compras',
    'CompraItem': 'compras',
    
    # Usuarios
    'Mecanico': 'usuarios',
    
    # Bonos
    'ConfiguracionBonoMecanico': 'bonos',
    'ExcepcionBonoTrabajo': 'bonos',
    'BonoGenerado': 'bonos',
    'PagoMecanico': 'bonos',
    
    # Configuracion
    'AdministracionTaller': 'configuracion',
    
    # Estadisticas
    'RegistroEvento': 'estadisticas',
    'ResumenTrabajo': 'estadisticas',
}

# Funciones auxiliares que van en core
HELPER_FUNCTIONS = [
    'normalizar_rut',
    'actualizar_stock_venta',
    'actualizar_stock_venta_pos',
]

def extract_model_class(content, model_name):
    """Extrae una clase de modelo completa del contenido"""
    pattern = rf'^class {model_name}\(models\.Model\):'
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        return None
    
    start = match.start()
    lines = content[:start].count('\n')
    
    # Encontrar el final de la clase
    class_lines = content.split('\n')
    indent_level = len(class_lines[lines]) - len(class_lines[lines].lstrip())
    
    result_lines = [class_lines[lines]]
    i = lines + 1
    
    while i < len(class_lines):
        line = class_lines[i]
        if not line.strip():
            result_lines.append(line)
            i += 1
            continue
        
        current_indent = len(line) - len(line.lstrip())
        
        # Si encontramos otra clase o función al mismo nivel o menor, terminamos
        if current_indent <= indent_level:
            if re.match(r'^class \w+\(', line) or (re.match(r'^def \w+\(', line) and current_indent == 0):
                break
        
        result_lines.append(line)
        i += 1
    
    return '\n'.join(result_lines)

def extract_helper_function(content, func_name):
    """Extrae una función auxiliar"""
    pattern = rf'^def {func_name}\('
    match = re.search(pattern, content, re.MULTILINE)
    
    if not match:
        return None
    
    start = match.start()
    lines = content[:start].count('\n')
    
    class_lines = content.split('\n')
    result_lines = [class_lines[lines]]
    i = lines + 1
    
    while i < len(class_lines):
        line = class_lines[i]
        if not line.strip():
            result_lines.append(line)
            i += 1
            continue
        
        current_indent = len(line) - len(line.lstrip())
        
        # Si encontramos otra función o clase al mismo nivel, terminamos
        if current_indent == 0 and (re.match(r'^def \w+\(', line) or re.match(r'^class \w+\(', line)):
            break
        
        result_lines.append(line)
        i += 1
    
    return '\n'.join(result_lines)

def main():
    # Leer el archivo de modelos original
    original_file = Path('../car/car/models.py')
    if not original_file.exists():
        print(f"Error: No se encuentra {original_file}")
        return
    
    with open(original_file, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    # Extraer imports necesarios
    imports = []
    for line in original_content.split('\n')[:20]:
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            imports.append(line)
    
    # Organizar modelos por app
    models_by_app = {}
    for model_name, app_name in MODEL_TO_APP.items():
        if app_name not in models_by_app:
            models_by_app[app_name] = []
        
        model_code = extract_model_class(original_content, model_name)
        if model_code:
            models_by_app[app_name].append((model_name, model_code))
            print(f"✓ Extraído {model_name} -> {app_name}")
        else:
            print(f"✗ No se encontró {model_name}")
    
    # Extraer funciones auxiliares
    helpers = {}
    for func_name in HELPER_FUNCTIONS:
        func_code = extract_helper_function(original_content, func_name)
        if func_code:
            helpers[func_name] = func_code
            print(f"✓ Extraída función {func_name}")
    
    # Escribir modelos en cada app
    base_dir = Path('.')
    for app_name, models in models_by_app.items():
        app_dir = base_dir / app_name
        models_file = app_dir / 'models.py'
        
        if not models_file.exists():
            continue
        
        # Leer el contenido actual
        with open(models_file, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Preparar nuevo contenido
        new_content = current_content.rstrip() + '\n\n'
        new_content += f"# ========================\n"
        new_content += f"# MODELOS MIGRADOS DESDE CAR\n"
        new_content += f"# ========================\n\n"
        
        for model_name, model_code in models:
            new_content += f"# {model_name}\n"
            new_content += model_code + '\n\n'
        
        # Escribir
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ Actualizado {app_name}/models.py")
    
    print("\n✅ Migración de modelos completada!")

if __name__ == '__main__':
    main()



