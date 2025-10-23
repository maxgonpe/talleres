#!/usr/bin/env python3
"""
Script para corregir los problemas restantes en templates
"""

import os
import re
from pathlib import Path

def fix_remaining_issues(file_path):
    """Corrige los problemas restantes en un template"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes_made = []
        
        # 1. Agregar centralized-colors.css si no lo tiene
        if 'centralized-colors.css' not in content and '{% extends' in content:
            if '{% load static %}' not in content:
                content = content.replace('{% extends', '{% load static %}\n{% extends')
            content = content.replace(
                '{% block title %}',
                '{% block extra_css %}\n  <link rel="stylesheet" href="{% static \'css/centralized-colors.css\' %}">\n{% endblock %}\n\n{% block title %}'
            )
            changes_made.append("Agregado centralized-colors.css")
        
        # 2. Reemplazar clases Bootstrap problemáticas restantes
        bootstrap_fixes = {
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
            r'class="card-header bg-primary text-inverse"': 'class="card-header bg-primary text-inverse"',  # Mantener
            r'class="card-header bg-success text-inverse"': 'class="card-header bg-success text-inverse"',  # Mantener
            r'class="card-header bg-warning text-primary"': 'class="card-header bg-warning text-primary"',  # Mantener
            r'class="card-header bg-info text-inverse"': 'class="card-header bg-info text-inverse"',  # Mantener
            r'class="card bg-primary text-white"': 'class="card bg-primary text-inverse"',
            r'class="card bg-warning text-white"': 'class="card bg-warning text-inverse"',
            r'class="card bg-success text-white"': 'class="card bg-success text-inverse"',
            r'class="card bg-light border-success"': 'class="card bg-secondary border-success"',
            r'class="badge bg-info text-dark"': 'class="badge bg-info text-primary"',
            r'class="badge {% if acc.completado %}bg-success{% else %}bg-warning{% endif %}"': 'class="badge {% if acc.completado %}bg-success{% else %}bg-warning{% endif %}"',  # Mantener
            r'class="progress-bar bg-warning"': 'class="progress-bar bg-warning"',  # Mantener
            r'class="progress-bar bg-success"': 'class="progress-bar bg-success"',  # Mantener
            r'class="progress-bar bg-primary"': 'class="progress-bar bg-primary"',  # Mantener
            r'class="progress-bar bg-dark"': 'class="progress-bar bg-primary"',
            r'class="badge bg-warning"': 'class="badge bg-warning"',  # Mantener
            r'class="badge bg-success"': 'class="badge bg-success"',  # Mantener
            r'class="badge bg-danger"': 'class="badge bg-danger"',  # Mantener
            r'class="text-danger mt-1"': 'class="text-danger mt-1"',  # Mantener para errores
            r'class="mt-3 text-end"': 'class="mt-3 text-end"',  # Mantener
            r'class="row text-center mt-3"': 'class="row text-center mt-3"',  # Mantener
            r'class="text-center py-4"': 'class="text-center py-4"',  # Mantener
            r'class="info-card text-center"': 'class="info-card text-center"',  # Mantener
        }
        
        for pattern, replacement in bootstrap_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Bootstrap: {pattern}")
        
        # 3. Reemplazar colores hardcodeados restantes
        color_fixes = {
            r'style="[^"]*--bs-accordion-bg: #ff[^"]*"': 'style="--bs-accordion-bg: var(--bg-card);"',
            r'style="[^"]*border: 1px solid #ccc[^"]*"': 'style="border: 1px solid var(--border-color);"',
        }
        
        for pattern, replacement in color_fixes.items():
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made.append(f"Color: {pattern}")
        
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
    
    print("🔧 CORRECCIÓN DE PROBLEMAS RESTANTES")
    print("=" * 50)
    
    # Lista de templates que necesitan corrección
    problematic_templates = [
        "car/accion_confirm_delete.html",
        "car/comp_accion_confirm_delete.html", 
        "car/componentes_confirm_delete.html",
        "car/diagnostico_eliminar.html",
        "car/editar_diagnostico.html",
        "car/ingreso_exitoso.html",
        "car/pizarra_page.html",
        "car/plano_interactivo.html",
        "car/administracion_taller.html",
        "car/compras/compra_dashboard.html",
        "car/compras/compra_detail.html",
        "car/compras/compra_items_table.html",
        "car/compras/compra_list.html",
        "car/diagnostico_lista.html",
        "car/panel_definitivo.html",
        "car/pizarra_partial.html",
        "car/pos/cotizacion_detalle.html",
        "car/pos/pos_principal.html",
        "car/pos/venta_detalle.html",
        "car/relacionar_repuestos.html",
        "car/trabajo_detalle_nuevo.html",
        "car/trabajo_lista.html",
        "vehiculos/vehiculo_form.html",
        "ventas/venta_crear.html",
        "ventas/venta_detalle.html",
        "ventas/ventas_historial.html"
    ]
    
    fixed_count = 0
    
    for template_path in problematic_templates:
        full_path = templates_dir / template_path
        if full_path.exists():
            fixed, changes = fix_remaining_issues(full_path)
            
            if fixed:
                print(f"✅ Corregido: {template_path}")
                for change in changes[:3]:  # Mostrar solo los primeros 3 cambios
                    print(f"   - {change}")
                if len(changes) > 3:
                    print(f"   - ... y {len(changes) - 3} cambios más")
                fixed_count += 1
            else:
                print(f"⏭️  Sin cambios: {template_path}")
    
    print("\n" + "=" * 50)
    print(f"📊 Resumen:")
    print(f"   Archivos corregidos: {fixed_count}")
    print("✅ Corrección de problemas restantes finalizada!")

if __name__ == "__main__":
    main()
