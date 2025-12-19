#!/usr/bin/env python3
"""
Script para comparar estructuras de tablas entre backup y models.py actual
y generar script de recuperación de datos
"""

import re
import sys
from pathlib import Path

BACKUP_FILE = Path("/home/max/myproject/cliente_solutioncar_db.sql")
MODELS_FILE = Path("/home/max/myproject/car/car/models.py")

def extract_table_structure_from_backup(table_name):
    """Extrae la estructura CREATE TABLE del backup"""
    if not BACKUP_FILE.exists():
        print(f"❌ Backup no encontrado: {BACKUP_FILE}")
        return None
    
    with open(BACKUP_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Buscar CREATE TABLE
    pattern = rf'CREATE TABLE.*?{table_name}.*?\((.*?)\);'
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        table_def = match.group(0)
        # Extraer columnas
        columns = []
        for line in table_def.split('\n'):
            line = line.strip()
            if line and not line.startswith('CREATE TABLE') and not line.startswith('CONSTRAINT'):
                if line.startswith('PRIMARY KEY') or line.startswith('FOREIGN KEY'):
                    continue
                # Limpiar comentarios y espacios
                col_line = re.sub(r'--.*$', '', line).strip()
                if col_line and not col_line.startswith(')'):
                    columns.append(col_line.rstrip(','))
        return {
            'full_definition': table_def,
            'columns': columns
        }
    return None

def extract_model_fields_from_py(model_name):
    """Extrae los campos del modelo desde models.py"""
    if not MODELS_FILE.exists():
        print(f"❌ Models.py no encontrado: {MODELS_FILE}")
        return None
    
    with open(MODELS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar la clase del modelo
    pattern = rf'class {model_name}\(models\.Model\):.*?(?=\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        class_content = match.group(0)
        # Extraer campos (líneas que tienen models.)
        fields = []
        for line in class_content.split('\n'):
            if 'models.' in line and '=' in line:
                # Extraer nombre del campo y tipo
                field_match = re.search(r'(\w+)\s*=\s*models\.(\w+)', line)
                if field_match:
                    field_name = field_match.group(1)
                    field_type = field_match.group(2)
                    # Extraer opciones adicionales
                    options = {}
                    if 'null=True' in line:
                        options['null'] = True
                    if 'blank=True' in line:
                        options['blank'] = True
                    if 'default=' in line:
                        default_match = re.search(r"default=([^,)]+)", line)
                        if default_match:
                            options['default'] = default_match.group(1).strip('"\'')
                    
                    fields.append({
                        'name': field_name,
                        'type': field_type,
                        'options': options
                    })
        return fields
    return None

def main():
    print("=" * 60)
    print("Comparación de Estructuras: Backup vs Models.py")
    print("=" * 60)
    print()
    
    # Analizar car_trabajo
    print("📋 Analizando tabla: car_trabajo")
    print("-" * 60)
    
    backup_trabajo = extract_table_structure_from_backup('car_trabajo')
    model_trabajo = extract_model_fields_from_py('Trabajo')
    
    if backup_trabajo:
        print(f"✅ Estructura encontrada en backup")
        print(f"   Columnas: {len(backup_trabajo['columns'])}")
        print("\n   Columnas del backup:")
        for i, col in enumerate(backup_trabajo['columns'][:10], 1):
            print(f"   {i}. {col[:80]}")
        if len(backup_trabajo['columns']) > 10:
            print(f"   ... y {len(backup_trabajo['columns']) - 10} más")
    else:
        print("❌ No se encontró estructura en backup")
    
    print()
    
    if model_trabajo:
        print(f"✅ Modelo encontrado en models.py")
        print(f"   Campos: {len(model_trabajo)}")
        print("\n   Campos del modelo:")
        for i, field in enumerate(model_trabajo[:10], 1):
            opts = ', '.join([f"{k}={v}" for k, v in field['options'].items()])
            opts_str = f" ({opts})" if opts else ""
            print(f"   {i}. {field['name']}: {field['type']}{opts_str}")
        if len(model_trabajo) > 10:
            print(f"   ... y {len(model_trabajo) - 10} más")
    else:
        print("❌ No se encontró modelo en models.py")
    
    print()
    print("=" * 60)
    
    # Analizar car_trabajorepuesto
    print("\n📋 Analizando tabla: car_trabajorepuesto")
    print("-" * 60)
    
    backup_repuesto = extract_table_structure_from_backup('car_trabajorepuesto')
    model_repuesto = extract_model_fields_from_py('TrabajoRepuesto')
    
    if backup_repuesto:
        print(f"✅ Estructura encontrada en backup")
        print(f"   Columnas: {len(backup_repuesto['columns'])}")
        print("\n   Columnas del backup:")
        for i, col in enumerate(backup_repuesto['columns'][:10], 1):
            print(f"   {i}. {col[:80]}")
    else:
        print("❌ No se encontró estructura en backup")
    
    print()
    
    if model_repuesto:
        print(f"✅ Modelo encontrado en models.py")
        print(f"   Campos: {len(model_repuesto)}")
        print("\n   Campos del modelo:")
        for i, field in enumerate(model_repuesto[:10], 1):
            opts = ', '.join([f"{k}={v}" for k, v in field['options'].items()])
            opts_str = f" ({opts})" if opts else ""
            print(f"   {i}. {field['name']}: {field['type']}{opts_str}")
    else:
        print("❌ No se encontró modelo en models.py")
    
    print()
    print("=" * 60)
    print("\n💡 Para ver diferencias detalladas, ejecuta el script de recuperación")
    print("=" * 60)

if __name__ == "__main__":
    main()

