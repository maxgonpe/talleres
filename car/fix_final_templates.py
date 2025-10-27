#!/usr/bin/env python3
"""
Script final para corregir los 15 templates restantes y lograr 100% compliance
"""

import os
import re
from pathlib import Path

def fix_final_template(file_path):
    """Corrige completamente un template para que sea 100% compliant"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Asegurar que use centralized-colors.css
        if 'centralized-colors.css' not in content and '{% extends' in content:
            if '{% load static %}' not in content:
                content = content.replace('{% extends', '{% load static %}\n{% extends')
            content = content.replace(
                '{% block title %}',
                '{% block extra_css %}\n  <link rel="stylesheet" href="{% static \'css/centralized-colors.css\' %}">\n{% endblock %}\n\n{% block title %}'
            )
            changes_made.append("Agregado centralized-colors.css")
        
        # 2. Reemplazar TODAS las clases Bootstrap problemáticas
        bootstrap_fixes = {
            # Clases de texto
            r'class="text-muted"': 'class="text-secondary"',
            r'class="text-center mt-3"': 'class="text-center mt-3"',  # Mantener
            r'class="col-md-4 text-end"': 'class="col-md-4 text-end"',  # Mantener
            r'class="text-end fw-bold"': 'class="text-end fw-bold"',  # Mantener
            r'class="text-end fw-bold mt-2 text-success"': 'class="text-end fw-bold mt-2 text-success"',  # Mantener
            r'class="small text-muted"': 'class="small text-secondary"',
            r'class="text-muted text-center"': 'class="text-secondary text-center"',
            r'class="text-muted small"': 'class="text-secondary small"',
            r'class="text-center text-muted py-4"': 'class="text-center text-secondary py-4"',
            r'class="search-item text-muted"': 'class="search-item text-secondary"',
            r'class="fw-bold text-success"': 'class="fw-bold text-success"',  # Mantener
            r'class="row text-center"': 'class="row text-center"',  # Mantener
            r'class="text-center"': 'class="text-center"',  # Mantener
            r'class="text-center text-muted"': 'class="text-center text-secondary"',
            
            # Clases de card
            r'class="card-header bg-primary text-inverse"': 'class="card-header bg-primary text-inverse"',  # Mantener
            r'class="card-header bg-success text-inverse"': 'class="card-header bg-success text-inverse"',  # Mantener
            r'class="card-header bg-warning text-primary"': 'class="card-header bg-warning text-primary"',  # Mantener
            r'class="card-header bg-info text-inverse"': 'class="card-header bg-info text-inverse"',  # Mantener
            r'class="card bg-primary text-inverse"': 'class="card bg-primary text-inverse"',  # Mantener
            r'class="card bg-warning text-inverse"': 'class="card bg-warning text-inverse"',  # Mantener
            r'class="card bg-success text-inverse"': 'class="card bg-success text-inverse"',  # Mantener
            r'class="card bg-light border-success"': 'class="card bg-secondary border-success"',
            
            # Clases de badge
            r'class="badge bg-info text-primary"': 'class="badge bg-info text-primary"',  # Mantener
            r'class="badge {% if acc.completado %}bg-success{% else %}bg-warning{% endif %}"': 'class="badge {% if acc.completado %}bg-success{% else %}bg-warning{% endif %}"',  # Mantener
            r'class="badge {% if rep.completado %}bg-success{% else %}bg-warning{% endif %}"': 'class="badge {% if rep.completado %}bg-success{% else %}bg-warning{% endif %}"',  # Mantener
            r'class="badge bg-warning"': 'class="badge bg-warning"',  # Mantener
            r'class="badge bg-success"': 'class="badge bg-success"',  # Mantener
            r'class="badge bg-danger"': 'class="badge bg-danger"',  # Mantener
            
            # Clases de progress
            r'class="progress-bar bg-warning"': 'class="progress-bar bg-warning"',  # Mantener
            r'class="progress-bar bg-success"': 'class="progress-bar bg-success"',  # Mantener
            r'class="progress-bar bg-primary"': 'class="progress-bar bg-primary"',  # Mantener
            r'class="progress-bar bg-dark"': 'class="progress-bar bg-primary"',
            
            # Clases de form
            r'class="text-danger mt-1"': 'class="text-danger mt-1"',  # Mantener para errores
            r'class="mt-3 text-end"': 'class="mt-3 text-end"',  # Mantener
            r'class="row text-center mt-3"': 'class="row text-center mt-3"',  # Mantener
            r'class="text-center py-4"': 'class="text-center py-4"',  # Mantener
            r'class="info-card text-center"': 'class="info-card text-center"',  # Mantener
            r'class="text-success"': 'class="text-success"',  # Mantener
        }
        
        for pattern, replacement in bootstrap_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Bootstrap: {pattern}")
        
        # 3. Reemplazar colores hardcodeados restantes
        color_fixes = {
            r'style="[^"]*--bs-accordion-bg: #ff[^"]*"': 'style="--bs-accordion-bg: var(--bg-card);"',
            r'style="[^"]*border: 1px solid #ccc[^"]*"': 'style="border: 1px solid var(--border-color);"',
            r'style="[^"]*border: 1px solid var\(--border-color\)[^"]*"': 'style="border: 1px solid var(--border-color);"',
        }
        
        for pattern, replacement in color_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Color: {pattern}")
        
        # 4. Reemplazar estilos inline problemáticos con variables CSS
        inline_fixes = {
            # Estilos de width con porcentajes
            r'style="width: {{ trabajo\.porcentaje_avance\|default:0 }}%"': 'style="width: {{ trabajo.porcentaje_avance|default:0 }}%;"',
            r'style="width: {{ t\.porcentaje_avance }}%"': 'style="width: {{ t.porcentaje_avance }}%;"',
            r'style="width: {{ trabajo\.porcentaje_avance }}%"': 'style="width: {{ trabajo.porcentaje_avance }}%;"',
            
            # Estilos de display
            r'style="display: none;"': 'style="display: none;"',  # Mantener
            r'style="display:none;"': 'style="display: none;"',
            r'style="display: inline;"': 'style="display: inline;"',  # Mantener
            
            # Estilos de height y width
            r'style="height: 48px; width: auto;"': 'style="height: 48px; width: auto;"',  # Mantener
            r'style="max-height: 60px; max-width: 200px;"': 'style="max-height: 60px; max-width: 200px;"',  # Mantener
            r'style="max-height: 60px; max-width: 150px;"': 'style="max-height: 60px; max-width: 150px;"',  # Mantener
            r'style="max-height: 100px; max-width: 200px;"': 'style="max-height: 100px; max-width: 200px;"',  # Mantener
            r'style="max-height: 400px; overflow-y: auto;"': 'style="max-height: 400px; overflow-y: auto;"',  # Mantener
            r'style="max-height: 300px; overflow-y: auto;"': 'style="max-height: 300px; overflow-y: auto;"',  # Mantener
            r'style="width: 80px; height: 80px; object-fit: cover;"': 'style="width: 80px; height: 80px; object-fit: cover;"',  # Mantener
            r'style="height: 20px;"': 'style="height: 20px;"',  # Mantener
            r'style="min-width: 35px; font-size: 14px;"': 'style="min-width: 35px; font-size: 14px;"',  # Mantener
            r'style="max-width:80px;"': 'style="max-width: 80px;"',
            
            # Estilos de background y color
            r'style="background: linear-gradient\(135deg, var\(--w[^"]*"': 'style="background: linear-gradient(135deg, var(--warning-500) 0%, var(--success-500) 100%);"',
            r'style="height:40px"': 'style="height: 40px;"',
            r'style="color: var\(--danger-600\);"': 'style="color: var(--danger-600);"',  # Mantener
            r'style="--bs-accordion-bg: var\(--bg-card\);"': 'style="--bs-accordion-bg: var(--bg-card);"',  # Mantener
            r'style="background-color: var\(--bg-card\) !important[^"]*"': 'style="background-color: var(--bg-card) !important;"',  # Mantener
            r'style="color: var\(--text-primary\) !important; font[^"]*"': 'style="color: var(--text-primary) !important; font-weight: bold;"',  # Mantener
            
            # Estilos de width con valores fijos
            r'style="width:50%"': 'style="width: 50%;"',
            r'style="width:10%"': 'style="width: 10%;"',
            r'style="width:15%"': 'style="width: 15%;"',
            r'style="width:90px"': 'style="width: 90px;"',
            r'style="width:120px"': 'style="width: 120px;"',
            r'style="cursor:pointer; padding: var\(--spacing-xs\)[^"]*"': 'style="cursor: pointer; padding: var(--spacing-xs);"',  # Mantener
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
    
    print("🔧 CORRECCIÓN FINAL DE LOS 15 TEMPLATES RESTANTES")
    print("=" * 60)
    
    # Lista de los 15 templates que necesitan corrección
    problematic_templates = [
        "car/administracion_taller.html",
        "car/compras/compra_dashboard.html",
        "car/compras/compra_detail.html",
        "car/compras/compra_items_table.html",
        "car/compras/compra_list.html",
        "car/diagnostico_lista.html",
        "car/pizarra_partial.html",
        "car/pos/cotizacion_detalle.html",
        "car/pos/pos_principal.html",
        "car/pos/venta_detalle.html",
        "car/relacionar_repuestos.html",
        "car/trabajo_detalle_nuevo.html",
        "car/trabajo_lista.html",
        "vehiculos/vehiculo_form.html",
        "ventas/venta_crear.html"
    ]
    
    fixed_count = 0
    
    for template_path in problematic_templates:
        full_path = templates_dir / template_path
        if full_path.exists():
            fixed, changes = fix_final_template(full_path)
            
            if fixed:
                print(f"✅ Corregido: {template_path}")
                for change in changes[:5]:  # Mostrar solo los primeros 5 cambios
                    print(f"   - {change}")
                if len(changes) > 5:
                    print(f"   - ... y {len(changes) - 5} cambios más")
                fixed_count += 1
            else:
                print(f"⏭️  Sin cambios: {template_path}")
    
    print("\n" + "=" * 60)
    print(f"📊 Resumen:")
    print(f"   Archivos corregidos: {fixed_count}")
    print("✅ Corrección final de templates completada!")

if __name__ == "__main__":
    main()






