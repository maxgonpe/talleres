#!/usr/bin/env python3
"""
Script agresivo para corregir los templates restantes
"""

import os
import re
from pathlib import Path

def fix_aggressive_template(file_path):
    """Corrige agresivamente un template"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Forzar centralized-colors.css
        if 'centralized-colors.css' not in content:
            if '{% load static %}' not in content:
                content = content.replace('{% extends', '{% load static %}\n{% extends')
            if '{% block extra_css %}' in content:
                content = content.replace(
                    '{% block extra_css %}',
                    '{% block extra_css %}\n  <link rel="stylesheet" href="{% static \'css/centralized-colors.css\' %}">'
                )
            else:
                content = content.replace(
                    '{% block title %}',
                    '{% block extra_css %}\n  <link rel="stylesheet" href="{% static \'css/centralized-colors.css\' %}">\n{% endblock %}\n\n{% block title %}'
                )
            changes_made.append("Forzado centralized-colors.css")
        
        # 2. Reemplazar TODAS las clases Bootstrap problemáticas
        bootstrap_fixes = {
            r'class="text-muted"': 'class="text-secondary"',
            r'class="small text-muted"': 'class="small text-secondary"',
            r'class="text-muted text-center"': 'class="text-secondary text-center"',
            r'class="text-muted small"': 'class="text-secondary small"',
            r'class="text-center text-muted py-4"': 'class="text-center text-secondary py-4"',
            r'class="search-item text-muted"': 'class="search-item text-secondary"',
            r'class="text-center text-muted"': 'class="text-center text-secondary"',
            r'class="card bg-light border-success"': 'class="card bg-secondary border-success"',
            r'class="badge bg-info text-dark"': 'class="badge bg-info text-primary"',
            r'class="progress-bar bg-dark"': 'class="progress-bar bg-primary"',
        }
        
        for pattern, replacement in bootstrap_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Bootstrap: {pattern}")
        
        # 3. Limpiar estilos inline problemáticos
        inline_fixes = {
            r'style="display:none;"': 'style="display: none;"',
            r'style="max-width:80px;"': 'style="max-width: 80px;"',
            r'style="width:50%"': 'style="width: 50%;"',
            r'style="width:10%"': 'style="width: 10%;"',
            r'style="width:15%"': 'style="width: 15%;"',
            r'style="width:90px"': 'style="width: 90px;"',
            r'style="width:120px"': 'style="width: 120px;"',
            r'style="height:40px"': 'style="height: 40px;"',
        }
        
        for pattern, replacement in inline_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Estilo inline: {pattern}")
        
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
    
    print("🔧 CORRECCIÓN AGRESIVA DE TEMPLATES RESTANTES")
    print("=" * 50)
    
    # Lista de templates que aún necesitan corrección
    remaining_templates = [
        "car/administracion_taller.html",
        "car/compras/compra_dashboard.html",
        "car/compras/compra_detail.html",
        "car/compras/compra_items_table.html",
        "car/compras/compra_list.html",
        "car/diagnostico_lista.html",
        "car/pos/cotizacion_detalle.html",
        "car/pos/venta_detalle.html",
        "car/relacionar_repuestos.html",
        "car/trabajo_lista.html",
        "vehiculos/vehiculo_form.html"
    ]
    
    fixed_count = 0
    
    for template_path in remaining_templates:
        full_path = templates_dir / template_path
        if full_path.exists():
            fixed, changes = fix_aggressive_template(full_path)
            
            if fixed:
                print(f"✅ Corregido: {template_path}")
                for change in changes[:3]:
                    print(f"   - {change}")
                if len(changes) > 3:
                    print(f"   - ... y {len(changes) - 3} cambios más")
                fixed_count += 1
            else:
                print(f"⏭️  Sin cambios: {template_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen:")
    print(f"   Archivos corregidos: {fixed_count}")
    print("✅ Corrección agresiva completada!")

if __name__ == "__main__":
    main()
