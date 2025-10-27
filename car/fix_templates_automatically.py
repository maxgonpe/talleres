#!/usr/bin/env python3
"""
Script para corregir automáticamente problemas comunes en templates
"""

import os
import re
from pathlib import Path

def fix_template_automatically(file_path):
    """Corrige automáticamente problemas comunes en un template"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Reemplazar clases Bootstrap problemáticas
        bootstrap_fixes = {
            r'class="text-muted"': 'class="text-secondary"',
            r'class="bg-primary"': 'class="bg-primary"',  # Mantener pero asegurar que use variables
            r'class="bg-success"': 'class="bg-success"',  # Mantener pero asegurar que use variables
            r'class="bg-warning"': 'class="bg-warning"',  # Mantener pero asegurar que use variables
            r'class="bg-danger"': 'class="bg-danger"',  # Mantener pero asegurar que use variables
            r'class="bg-info"': 'class="bg-info"',  # Mantener pero asegurar que use variables
            r'class="text-white"': 'class="text-inverse"',
            r'class="text-dark"': 'class="text-primary"',
        }
        
        for pattern, replacement in bootstrap_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Reemplazado: {pattern}")
        
        # 2. Reemplazar colores hardcodeados comunes
        color_fixes = {
            r'color:\s*#28a745': 'color: var(--success-600)',
            r'color:\s*#6c757d': 'color: var(--text-muted)',
            r'color:\s*#dc3545': 'color: var(--danger-600)',
            r'color:\s*#ffc107': 'color: var(--warning-600)',
            r'color:\s*#0d6efd': 'color: var(--primary-600)',
            r'color:\s*#17a2b8': 'color: var(--info-600)',
            r'background-color:\s*#28a745': 'background-color: var(--success-600)',
            r'background-color:\s*#6c757d': 'background-color: var(--neutral-600)',
            r'background-color:\s*#dc3545': 'background-color: var(--danger-600)',
            r'background-color:\s*#ffc107': 'background-color: var(--warning-500)',
            r'background-color:\s*#0d6efd': 'background-color: var(--primary-600)',
            r'background-color:\s*#17a2b8': 'background-color: var(--info-600)',
        }
        
        for pattern, replacement in color_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Color corregido: {pattern}")
        
        # 3. Reemplazar espaciado hardcodeado
        spacing_fixes = {
            r'padding:\s*5px': 'padding: var(--spacing-xs)',
            r'padding:\s*10px': 'padding: var(--spacing-sm)',
            r'padding:\s*15px': 'padding: var(--spacing-md)',
            r'padding:\s*20px': 'padding: var(--spacing-lg)',
            r'margin:\s*5px': 'margin: var(--spacing-xs)',
            r'margin:\s*10px': 'margin: var(--spacing-sm)',
            r'margin:\s*15px': 'margin: var(--spacing-md)',
            r'margin:\s*20px': 'margin: var(--spacing-lg)',
        }
        
        for pattern, replacement in spacing_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Espaciado corregido: {pattern}")
        
        # 4. Reemplazar border-radius hardcodeado
        radius_fixes = {
            r'border-radius:\s*5px': 'border-radius: var(--border-radius-sm)',
            r'border-radius:\s*8px': 'border-radius: var(--border-radius-md)',
            r'border-radius:\s*10px': 'border-radius: var(--border-radius-lg)',
            r'border-radius:\s*15px': 'border-radius: var(--border-radius-xl)',
            r'border-radius:\s*25px': 'border-radius: var(--border-radius-full)',
        }
        
        for pattern, replacement in radius_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Border-radius corregido: {pattern}")
        
        # 5. Reemplazar box-shadow hardcodeado
        shadow_fixes = {
            r'box-shadow:\s*0 2px 10px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-md)',
            r'box-shadow:\s*0 4px 15px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-lg)',
            r'box-shadow:\s*0 2px 6px rgba\(0,0,0,0\.05\)': 'box-shadow: var(--shadow-sm)',
        }
        
        for pattern, replacement in shadow_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Box-shadow corregido: {pattern}")
        
        # Si hubo cambios, escribir el archivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        else:
            return False, []
            
    except Exception as e:
        return False, [f"Error: {e}"]

def main():
    """Función principal"""
    templates_dir = Path("/home/maxgonpe/talleres/car/car/templates")
    
    print("🔧 CORRECCIÓN AUTOMÁTICA DE TEMPLATES")
    print("=" * 50)
    
    fixed_count = 0
    total_count = 0
    
    # Buscar todos los archivos HTML
    for html_file in templates_dir.rglob("*.html"):
        total_count += 1
        relative_path = html_file.relative_to(templates_dir)
        
        fixed, changes = fix_template_automatically(html_file)
        
        if fixed:
            print(f"✅ Corregido: {relative_path}")
            for change in changes[:3]:  # Mostrar solo los primeros 3 cambios
                print(f"   - {change}")
            if len(changes) > 3:
                print(f"   - ... y {len(changes) - 3} cambios más")
            fixed_count += 1
        else:
            print(f"⏭️  Sin cambios: {relative_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen:")
    print(f"   Total de archivos: {total_count}")
    print(f"   Archivos corregidos: {fixed_count}")
    print(f"   Archivos sin cambios: {total_count - fixed_count}")
    print("✅ Corrección automática completada!")

if __name__ == "__main__":
    main()






