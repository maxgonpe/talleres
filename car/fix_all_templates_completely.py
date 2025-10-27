#!/usr/bin/env python3
"""
Script para corregir COMPLETAMENTE todos los templates y hacerlos 100% uniformes
"""

import os
import re
from pathlib import Path

def fix_template_completely(file_path):
    """Corrige completamente un template para que sea 100% uniforme"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Asegurar que use centralized-colors.css (solo si extiende base.html)
        if '{% extends' in content and 'centralized-colors.css' not in content:
            if '{% block extra_css %}' in content:
                # Si ya tiene block extra_css, agregar el CSS ahí
                content = content.replace(
                    '{% block extra_css %}',
                    '{% block extra_css %}\n  <link rel="stylesheet" href="{% static \'css/centralized-colors.css\' %}">'
                )
                changes_made.append("Agregado centralized-colors.css")
            else:
                # Si no tiene block extra_css, agregarlo después del extends
                if '{% load static %}' not in content:
                    content = content.replace(
                        '{% extends',
                        '{% load static %}\n{% extends'
                    )
                content = content.replace(
                    '{% block title %}',
                    '{% block extra_css %}\n  <link rel="stylesheet" href="{% static \'css/centralized-colors.css\' %}">\n{% endblock %}\n\n{% block title %}'
                )
                changes_made.append("Agregado centralized-colors.css y load static")
        
        # 2. Reemplazar TODAS las clases Bootstrap problemáticas
        bootstrap_fixes = {
            # Clases de texto
            r'class="text-muted"': 'class="text-secondary"',
            r'class="text-white"': 'class="text-inverse"',
            r'class="text-dark"': 'class="text-primary"',
            r'class="text-center"': 'class="text-center"',  # Mantener pero asegurar consistencia
            r'class="text-end"': 'class="text-end"',  # Mantener pero asegurar consistencia
            r'class="text-start"': 'class="text-start"',  # Mantener pero asegurar consistencia
            
            # Clases de fondo
            r'class="bg-primary"': 'class="bg-primary"',  # Mantener pero usar variables
            r'class="bg-success"': 'class="bg-success"',  # Mantener pero usar variables
            r'class="bg-warning"': 'class="bg-warning"',  # Mantener pero usar variables
            r'class="bg-danger"': 'class="bg-danger"',  # Mantener pero usar variables
            r'class="bg-info"': 'class="bg-info"',  # Mantener pero usar variables
            r'class="bg-light"': 'class="bg-secondary"',
            r'class="bg-dark"': 'class="bg-primary"',
            
            # Clases de badge
            r'class="badge bg-primary"': 'class="badge bg-primary"',
            r'class="badge bg-success"': 'class="badge bg-success"',
            r'class="badge bg-warning"': 'class="badge bg-warning"',
            r'class="badge bg-danger"': 'class="badge bg-danger"',
            r'class="badge bg-info"': 'class="badge bg-info"',
            r'class="badge bg-dark"': 'class="badge bg-primary"',
            r'class="badge bg-light"': 'class="badge bg-secondary"',
            
            # Clases de card
            r'class="card-header bg-primary text-white"': 'class="card-header bg-primary text-inverse"',
            r'class="card-header bg-success text-white"': 'class="card-header bg-success text-inverse"',
            r'class="card-header bg-warning text-dark"': 'class="card-header bg-warning text-primary"',
            r'class="card-header bg-danger text-white"': 'class="card-header bg-danger text-inverse"',
            r'class="card-header bg-info text-white"': 'class="card-header bg-info text-inverse"',
            
            # Clases de progress
            r'class="progress-bar bg-warning"': 'class="progress-bar bg-warning"',
            r'class="progress-bar bg-success"': 'class="progress-bar bg-success"',
            r'class="progress-bar bg-danger"': 'class="progress-bar bg-danger"',
            r'class="progress-bar bg-info"': 'class="progress-bar bg-info"',
            r'class="progress-bar bg-primary"': 'class="progress-bar bg-primary"',
            r'class="progress-bar bg-dark"': 'class="progress-bar bg-primary"',
            
            # Clases de alert
            r'class="alert alert-success"': 'class="alert alert-success"',
            r'class="alert alert-warning"': 'class="alert alert-warning"',
            r'class="alert alert-danger"': 'class="alert alert-danger"',
            r'class="alert alert-info"': 'class="alert alert-info"',
            r'class="alert alert-primary"': 'class="alert alert-primary"',
            
            # Clases de button
            r'class="btn btn-primary"': 'class="btn btn-primary"',
            r'class="btn btn-success"': 'class="btn btn-success"',
            r'class="btn btn-warning"': 'class="btn btn-warning"',
            r'class="btn btn-danger"': 'class="btn btn-danger"',
            r'class="btn btn-info"': 'class="btn btn-info"',
            r'class="btn btn-secondary"': 'class="btn btn-secondary"',
            
            # Clases de form
            r'class="form-text text-muted"': 'class="form-text text-secondary"',
            r'class="text-danger mt-1"': 'class="text-danger mt-1"',  # Mantener para errores
            r'class="text-success"': 'class="text-success"',
            r'class="text-warning"': 'class="text-warning"',
            r'class="text-info"': 'class="text-info"',
        }
        
        for pattern, replacement in bootstrap_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Bootstrap: {pattern}")
        
        # 3. Reemplazar TODOS los colores hardcodeados
        color_fixes = {
            # Colores principales
            r'color:\s*#28a745': 'color: var(--success-600)',
            r'color:\s*#6c757d': 'color: var(--text-muted)',
            r'color:\s*#dc3545': 'color: var(--danger-600)',
            r'color:\s*#ffc107': 'color: var(--warning-600)',
            r'color:\s*#0d6efd': 'color: var(--primary-600)',
            r'color:\s*#17a2b8': 'color: var(--info-600)',
            r'color:\s*#6f42c1': 'color: var(--accent-600)',
            r'color:\s*#fd7e14': 'color: var(--secondary-600)',
            r'color:\s*#20c997': 'color: var(--success-500)',
            r'color:\s*#e83e8c': 'color: var(--accent-500)',
            r'color:\s*#198754': 'color: var(--success-700)',
            r'color:\s*#0dcaf0': 'color: var(--info-500)',
            r'color:\s*#6610f2': 'color: var(--accent-700)',
            r'color:\s*#212529': 'color: var(--text-primary)',
            r'color:\s*#495057': 'color: var(--text-secondary)',
            r'color:\s*#6c757d': 'color: var(--text-muted)',
            r'color:\s*#adb5bd': 'color: var(--text-muted)',
            r'color:\s*#dee2e6': 'color: var(--border-color)',
            r'color:\s*#e9ecef': 'color: var(--border-color-light)',
            r'color:\s*#f8f9fa': 'color: var(--bg-secondary)',
            r'color:\s*#ffffff': 'color: var(--text-inverse)',
            r'color:\s*#000000': 'color: var(--text-primary)',
            r'color:\s*red': 'color: var(--danger-600)',
            r'color:\s*green': 'color: var(--success-600)',
            r'color:\s*blue': 'color: var(--primary-600)',
            r'color:\s*yellow': 'color: var(--warning-600)',
            r'color:\s*orange': 'color: var(--secondary-600)',
            r'color:\s*purple': 'color: var(--accent-600)',
            r'color:\s*black': 'color: var(--text-primary)',
            r'color:\s*white': 'color: var(--text-inverse)',
            r'color:\s*gray': 'color: var(--text-muted)',
            r'color:\s*grey': 'color: var(--text-muted)',
            
            # Background colors
            r'background-color:\s*#28a745': 'background-color: var(--success-600)',
            r'background-color:\s*#6c757d': 'background-color: var(--neutral-600)',
            r'background-color:\s*#dc3545': 'background-color: var(--danger-600)',
            r'background-color:\s*#ffc107': 'background-color: var(--warning-500)',
            r'background-color:\s*#0d6efd': 'background-color: var(--primary-600)',
            r'background-color:\s*#17a2b8': 'background-color: var(--info-600)',
            r'background-color:\s*#6f42c1': 'background-color: var(--accent-600)',
            r'background-color:\s*#fd7e14': 'background-color: var(--secondary-600)',
            r'background-color:\s*#20c997': 'background-color: var(--success-500)',
            r'background-color:\s*#e83e8c': 'background-color: var(--accent-500)',
            r'background-color:\s*#198754': 'background-color: var(--success-700)',
            r'background-color:\s*#0dcaf0': 'background-color: var(--info-500)',
            r'background-color:\s*#6610f2': 'background-color: var(--accent-700)',
            r'background-color:\s*#212529': 'background-color: var(--text-primary)',
            r'background-color:\s*#495057': 'background-color: var(--text-secondary)',
            r'background-color:\s*#6c757d': 'background-color: var(--text-muted)',
            r'background-color:\s*#adb5bd': 'background-color: var(--text-muted)',
            r'background-color:\s*#dee2e6': 'background-color: var(--border-color)',
            r'background-color:\s*#e9ecef': 'background-color: var(--border-color-light)',
            r'background-color:\s*#f8f9fa': 'background-color: var(--bg-secondary)',
            r'background-color:\s*#ffffff': 'background-color: var(--bg-card)',
            r'background-color:\s*#000000': 'background-color: var(--text-primary)',
            r'background-color:\s*red': 'background-color: var(--danger-600)',
            r'background-color:\s*green': 'background-color: var(--success-600)',
            r'background-color:\s*blue': 'background-color: var(--primary-600)',
            r'background-color:\s*yellow': 'background-color: var(--warning-500)',
            r'background-color:\s*orange': 'background-color: var(--secondary-600)',
            r'background-color:\s*purple': 'background-color: var(--accent-600)',
            r'background-color:\s*black': 'background-color: var(--text-primary)',
            r'background-color:\s*white': 'background-color: var(--bg-card)',
            r'background-color:\s*gray': 'background-color: var(--text-muted)',
            r'background-color:\s*grey': 'background-color: var(--text-muted)',
        }
        
        for pattern, replacement in color_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Color: {pattern}")
        
        # 4. Reemplazar TODOS los espaciados hardcodeados
        spacing_fixes = {
            r'padding:\s*1px': 'padding: var(--spacing-xs)',
            r'padding:\s*2px': 'padding: var(--spacing-xs)',
            r'padding:\s*3px': 'padding: var(--spacing-xs)',
            r'padding:\s*4px': 'padding: var(--spacing-xs)',
            r'padding:\s*5px': 'padding: var(--spacing-xs)',
            r'padding:\s*6px': 'padding: var(--spacing-sm)',
            r'padding:\s*7px': 'padding: var(--spacing-sm)',
            r'padding:\s*8px': 'padding: var(--spacing-sm)',
            r'padding:\s*9px': 'padding: var(--spacing-sm)',
            r'padding:\s*10px': 'padding: var(--spacing-sm)',
            r'padding:\s*11px': 'padding: var(--spacing-sm)',
            r'padding:\s*12px': 'padding: var(--spacing-sm)',
            r'padding:\s*13px': 'padding: var(--spacing-sm)',
            r'padding:\s*14px': 'padding: var(--spacing-sm)',
            r'padding:\s*15px': 'padding: var(--spacing-md)',
            r'padding:\s*16px': 'padding: var(--spacing-md)',
            r'padding:\s*17px': 'padding: var(--spacing-md)',
            r'padding:\s*18px': 'padding: var(--spacing-md)',
            r'padding:\s*19px': 'padding: var(--spacing-md)',
            r'padding:\s*20px': 'padding: var(--spacing-lg)',
            r'padding:\s*25px': 'padding: var(--spacing-lg)',
            r'padding:\s*30px': 'padding: var(--spacing-xl)',
            r'padding:\s*40px': 'padding: var(--spacing-2xl)',
            r'padding:\s*50px': 'padding: var(--spacing-2xl)',
            
            r'margin:\s*1px': 'margin: var(--spacing-xs)',
            r'margin:\s*2px': 'margin: var(--spacing-xs)',
            r'margin:\s*3px': 'margin: var(--spacing-xs)',
            r'margin:\s*4px': 'margin: var(--spacing-xs)',
            r'margin:\s*5px': 'margin: var(--spacing-xs)',
            r'margin:\s*6px': 'margin: var(--spacing-sm)',
            r'margin:\s*7px': 'margin: var(--spacing-sm)',
            r'margin:\s*8px': 'margin: var(--spacing-sm)',
            r'margin:\s*9px': 'margin: var(--spacing-sm)',
            r'margin:\s*10px': 'margin: var(--spacing-sm)',
            r'margin:\s*11px': 'margin: var(--spacing-sm)',
            r'margin:\s*12px': 'margin: var(--spacing-sm)',
            r'margin:\s*13px': 'margin: var(--spacing-sm)',
            r'margin:\s*14px': 'margin: var(--spacing-sm)',
            r'margin:\s*15px': 'margin: var(--spacing-md)',
            r'margin:\s*16px': 'margin: var(--spacing-md)',
            r'margin:\s*17px': 'margin: var(--spacing-md)',
            r'margin:\s*18px': 'margin: var(--spacing-md)',
            r'margin:\s*19px': 'margin: var(--spacing-md)',
            r'margin:\s*20px': 'margin: var(--spacing-lg)',
            r'margin:\s*25px': 'margin: var(--spacing-lg)',
            r'margin:\s*30px': 'margin: var(--spacing-xl)',
            r'margin:\s*40px': 'margin: var(--spacing-2xl)',
            r'margin:\s*50px': 'margin: var(--spacing-2xl)',
        }
        
        for pattern, replacement in spacing_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Espaciado: {pattern}")
        
        # 5. Reemplazar TODOS los border-radius hardcodeados
        radius_fixes = {
            r'border-radius:\s*1px': 'border-radius: var(--border-radius-sm)',
            r'border-radius:\s*2px': 'border-radius: var(--border-radius-sm)',
            r'border-radius:\s*3px': 'border-radius: var(--border-radius-sm)',
            r'border-radius:\s*4px': 'border-radius: var(--border-radius-sm)',
            r'border-radius:\s*5px': 'border-radius: var(--border-radius-sm)',
            r'border-radius:\s*6px': 'border-radius: var(--border-radius-md)',
            r'border-radius:\s*7px': 'border-radius: var(--border-radius-md)',
            r'border-radius:\s*8px': 'border-radius: var(--border-radius-md)',
            r'border-radius:\s*9px': 'border-radius: var(--border-radius-md)',
            r'border-radius:\s*10px': 'border-radius: var(--border-radius-lg)',
            r'border-radius:\s*12px': 'border-radius: var(--border-radius-lg)',
            r'border-radius:\s*15px': 'border-radius: var(--border-radius-xl)',
            r'border-radius:\s*20px': 'border-radius: var(--border-radius-xl)',
            r'border-radius:\s*25px': 'border-radius: var(--border-radius-full)',
            r'border-radius:\s*30px': 'border-radius: var(--border-radius-full)',
            r'border-radius:\s*50px': 'border-radius: var(--border-radius-full)',
            r'border-radius:\s*100px': 'border-radius: var(--border-radius-full)',
        }
        
        for pattern, replacement in radius_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Border-radius: {pattern}")
        
        # 6. Reemplazar TODOS los box-shadow hardcodeados
        shadow_fixes = {
            r'box-shadow:\s*0 1px 2px rgba\(0,0,0,0\.05\)': 'box-shadow: var(--shadow-sm)',
            r'box-shadow:\s*0 2px 4px rgba\(0,0,0,0\.05\)': 'box-shadow: var(--shadow-sm)',
            r'box-shadow:\s*0 2px 6px rgba\(0,0,0,0\.05\)': 'box-shadow: var(--shadow-sm)',
            r'box-shadow:\s*0 2px 8px rgba\(0,0,0,0\.05\)': 'box-shadow: var(--shadow-sm)',
            r'box-shadow:\s*0 2px 10px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-md)',
            r'box-shadow:\s*0 4px 6px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-md)',
            r'box-shadow:\s*0 4px 8px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-md)',
            r'box-shadow:\s*0 4px 10px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-md)',
            r'box-shadow:\s*0 4px 15px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-lg)',
            r'box-shadow:\s*0 6px 10px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-lg)',
            r'box-shadow:\s*0 8px 15px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-lg)',
            r'box-shadow:\s*0 10px 15px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-lg)',
            r'box-shadow:\s*0 10px 20px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-xl)',
            r'box-shadow:\s*0 15px 25px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-xl)',
            r'box-shadow:\s*0 20px 25px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-xl)',
        }
        
        for pattern, replacement in shadow_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Box-shadow: {pattern}")
        
        # 7. Reemplazar transiciones hardcodeadas
        transition_fixes = {
            r'transition:\s*all 0\.2s': 'transition: var(--transition-fast)',
            r'transition:\s*all 0\.3s': 'transition: var(--transition)',
            r'transition:\s*all 0\.5s': 'transition: var(--transition-slow)',
            r'transition:\s*background-color 0\.2s': 'transition: var(--transition-fast)',
            r'transition:\s*background-color 0\.3s': 'transition: var(--transition)',
            r'transition:\s*color 0\.2s': 'transition: var(--transition-fast)',
            r'transition:\s*color 0\.3s': 'transition: var(--transition)',
            r'transition:\s*border 0\.2s': 'transition: var(--transition-fast)',
            r'transition:\s*border 0\.3s': 'transition: var(--transition)',
        }
        
        for pattern, replacement in transition_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Transición: {pattern}")
        
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
    
    print("🔧 CORRECCIÓN COMPLETA DE TODOS LOS TEMPLATES")
    print("=" * 60)
    
    fixed_count = 0
    total_count = 0
    
    # Buscar todos los archivos HTML
    for html_file in templates_dir.rglob("*.html"):
        total_count += 1
        relative_path = html_file.relative_to(templates_dir)
        
        fixed, changes = fix_template_completely(html_file)
        
        if fixed:
            print(f"✅ Corregido: {relative_path}")
            for change in changes[:5]:  # Mostrar solo los primeros 5 cambios
                print(f"   - {change}")
            if len(changes) > 5:
                print(f"   - ... y {len(changes) - 5} cambios más")
            fixed_count += 1
        else:
            print(f"⏭️  Sin cambios: {relative_path}")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen:")
    print(f"   Total de archivos: {total_count}")
    print(f"   Archivos corregidos: {fixed_count}")
    print(f"   Archivos sin cambios: {total_count - fixed_count}")
    print("✅ Corrección completa finalizada!")

if __name__ == "__main__":
    main()






