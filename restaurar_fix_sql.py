#!/usr/bin/env python3
"""
Script Python para limpiar y restaurar INSERT problemáticos del backup
"""

import re
import sys
from pathlib import Path

BACKUP_FILE = Path("/home/max/myproject/cliente_solutioncar_db.sql")

def clean_inserts(table_name, backup_file):
    """Extrae y limpia INSERT de una tabla específica"""
    inserts = []
    current_insert = None
    
    with open(backup_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            
            # Detectar inicio de INSERT
            if f"INSERT INTO public.{table_name}" in line:
                if current_insert:
                    inserts.append(current_insert)
                current_insert = line
            # Continuar INSERT en múltiples líneas
            elif current_insert:
                current_insert += " " + line
                # Si termina con );, cerrar el INSERT
                if current_insert.rstrip().endswith(');'):
                    inserts.append(current_insert)
                    current_insert = None
            # Si encontramos otro INSERT o COPY, cerrar el anterior
            elif current_insert and (line.startswith('INSERT INTO') or line.startswith('COPY') or line == '\\.'):
                inserts.append(current_insert.rstrip().rstrip(';') + ';')
                current_insert = None
    
    # Agregar el último si existe
    if current_insert:
        inserts.append(current_insert.rstrip().rstrip(';') + ';')
    
    return inserts

def main():
    print("=" * 60)
    print("Limpieza de INSERT del backup")
    print("=" * 60)
    print()
    
    # Limpiar diagnósticos
    print("📋 Limpiando INSERT de car_diagnostico...")
    diagnosticos = clean_inserts("car_diagnostico", BACKUP_FILE)
    print(f"   Encontrados: {len(diagnosticos)} INSERT")
    
    if diagnosticos:
        output_file = Path("/tmp/diagnosticos_limpios.sql")
        with open(output_file, 'w') as f:
            for insert in diagnosticos:
                f.write(insert + '\n')
        print(f"   ✅ Guardados en: {output_file}")
        print(f"   Primeros 3 INSERT:")
        for i, ins in enumerate(diagnosticos[:3], 1):
            print(f"   {i}. {ins[:80]}...")
    print()
    
    # Limpiar trabajos
    print("📋 Limpiando INSERT de car_trabajo...")
    trabajos = clean_inserts("car_trabajo", BACKUP_FILE)
    print(f"   Encontrados: {len(trabajos)} INSERT")
    
    if trabajos:
        output_file = Path("/tmp/trabajos_limpios.sql")
        with open(output_file, 'w') as f:
            for insert in trabajos:
                f.write(insert + '\n')
        print(f"   ✅ Guardados en: {output_file}")
        print(f"   Primeros 3 INSERT:")
        for i, ins in enumerate(trabajos[:3], 1):
            print(f"   {i}. {ins[:80]}...")
    print()
    
    # Limpiar repuestos
    print("📋 Limpiando INSERT de car_trabajorepuesto...")
    repuestos = clean_inserts("car_trabajorepuesto", BACKUP_FILE)
    print(f"   Encontrados: {len(repuestos)} INSERT")
    
    if repuestos:
        output_file = Path("/tmp/repuestos_limpios.sql")
        with open(output_file, 'w') as f:
            for insert in repuestos:
                f.write(insert + '\n')
        print(f"   ✅ Guardados en: {output_file}")
    print()
    
    print("=" * 60)
    print("✅ Archivos limpios creados en /tmp/")
    print("=" * 60)
    print()
    print("Para restaurar, ejecuta:")
    print("  docker exec -i postgres_talleres psql -U maxgonpe -d cliente_solutioncar_db < /tmp/diagnosticos_limpios.sql")
    print("  docker exec -i postgres_talleres psql -U maxgonpe -d cliente_solutioncar_db < /tmp/trabajos_limpios.sql")
    print("  docker exec -i postgres_talleres psql -U maxgonpe -d cliente_solutioncar_db < /tmp/repuestos_limpios.sql")

if __name__ == "__main__":
    main()





