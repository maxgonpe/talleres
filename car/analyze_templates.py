#!/usr/bin/env python3
"""
Script para analizar todos los templates del sistema y identificar cuáles están en uso
"""

import os
import re
from pathlib import Path

def extract_templates_from_views():
    """Extrae todos los templates usados en las vistas"""
    views_file = Path("/home/maxgonpe/talleres/car/car/views.py")
    templates_used = set()
    
    with open(views_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar patrones de render con templates
    patterns = [
        r'render\([^)]+,\s*["\']([^"\']+)["\']',
        r'return render\([^)]+,\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content)
        for match in matches:
            if match.endswith('.html'):
                templates_used.add(match)
    
    return templates_used

def extract_templates_from_views_pos():
    """Extrae templates de views_pos.py"""
    views_pos_file = Path("/home/maxgonpe/talleres/car/car/views_pos.py")
    templates_used = set()
    
    if views_pos_file.exists():
        with open(views_pos_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            r'render\([^)]+,\s*["\']([^"\']+)["\']',
            r'return render\([^)]+,\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.endswith('.html'):
                    templates_used.add(match)
    
    return templates_used

def extract_templates_from_views_compras():
    """Extrae templates de views_compras.py"""
    views_compras_file = Path("/home/maxgonpe/talleres/car/car/views_compras.py")
    templates_used = set()
    
    if views_compras_file.exists():
        with open(views_compras_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            r'render\([^)]+,\s*["\']([^"\']+)["\']',
            r'return render\([^)]+,\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.endswith('.html'):
                    templates_used.add(match)
    
    return templates_used

def extract_templates_from_views_vehiculos():
    """Extrae templates de views_vehiculos.py"""
    views_vehiculos_file = Path("/home/maxgonpe/talleres/car/car/views_vehiculos.py")
    templates_used = set()
    
    if views_vehiculos_file.exists():
        with open(views_vehiculos_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            r'render\([^)]+,\s*["\']([^"\']+)["\']',
            r'return render\([^)]+,\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.endswith('.html'):
                    templates_used.add(match)
    
    return templates_used

def extract_templates_from_views_algoritmo():
    """Extrae templates de views_algoritmo.py"""
    views_algoritmo_file = Path("/home/maxgonpe/talleres/car/car/views_algoritmo.py")
    templates_used = set()
    
    if views_algoritmo_file.exists():
        with open(views_algoritmo_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        patterns = [
            r'render\([^)]+,\s*["\']([^"\']+)["\']',
            r'return render\([^)]+,\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.endswith('.html'):
                    templates_used.add(match)
    
    return templates_used

def find_all_templates():
    """Encuentra todos los templates HTML en el sistema"""
    templates_dir = Path("/home/maxgonpe/talleres/car/car/templates")
    all_templates = set()
    
    for html_file in templates_dir.rglob("*.html"):
        # Convertir ruta absoluta a ruta relativa desde templates/
        relative_path = html_file.relative_to(templates_dir)
        all_templates.add(str(relative_path))
    
    return all_templates

def find_orphaned_templates():
    """Encuentra templates huérfanos"""
    print("🔍 Analizando templates del sistema...")
    
    # Obtener todos los templates usados
    templates_used = set()
    templates_used.update(extract_templates_from_views())
    templates_used.update(extract_templates_from_views_pos())
    templates_used.update(extract_templates_from_views_compras())
    templates_used.update(extract_templates_from_views_vehiculos())
    templates_used.update(extract_templates_from_views_algoritmo())
    
    # Obtener todos los templates existentes
    all_templates = find_all_templates()
    
    # Encontrar templates huérfanos
    orphaned = all_templates - templates_used
    
    print(f"📊 Total de templates encontrados: {len(all_templates)}")
    print(f"📊 Templates en uso: {len(templates_used)}")
    print(f"📊 Templates huérfanos: {len(orphaned)}")
    
    return orphaned, templates_used, all_templates

def move_orphaned_templates(orphaned_templates):
    """Mueve templates huérfanos a la carpeta de backup"""
    backup_dir = Path("/home/maxgonpe/talleres/otros/templates_antiguos/backup-templates-23-10-2025")
    templates_dir = Path("/home/maxgonpe/talleres/car/car/templates")
    
    moved_count = 0
    
    for template in orphaned_templates:
        source_path = templates_dir / template
        if source_path.exists():
            # Crear estructura de directorios en backup
            backup_path = backup_dir / template
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Mover archivo
            source_path.rename(backup_path)
            print(f"✅ Movido: {template}")
            moved_count += 1
        else:
            print(f"⚠️  No encontrado: {template}")
    
    return moved_count

def main():
    """Función principal"""
    print("🧹 LIMPIEZA DE TEMPLATES HUÉRFANOS")
    print("=" * 50)
    
    # Analizar templates
    orphaned, used, all_templates = find_orphaned_templates()
    
    print("\n📋 TEMPLATES EN USO:")
    for template in sorted(used):
        print(f"  ✅ {template}")
    
    print(f"\n🗑️  TEMPLATES HUÉRFANOS ({len(orphaned)}):")
    for template in sorted(orphaned):
        print(f"  ❌ {template}")
    
    if orphaned:
        print(f"\n🚚 Moviendo {len(orphaned)} templates huérfanos a backup...")
        moved = move_orphaned_templates(orphaned)
        print(f"\n✅ Movidos {moved} templates a backup")
        print(f"📁 Ubicación: /home/maxgonpe/talleres/otros/templates_antiguos/backup-templates-23-10-2025")
    else:
        print("\n🎉 ¡No hay templates huérfanos! El sistema está limpio.")
    
    print("\n" + "=" * 50)
    print("✅ Análisis completado!")

if __name__ == "__main__":
    main()






