#!/usr/bin/env python3
"""
Script para verificar qué templates están 100% alineados con el sistema centralizado
"""

import os
import re
from pathlib import Path

def check_template_compliance(template_path):
    """Verifica si un template está 100% alineado con el sistema centralizado"""
    issues = []
    warnings = []
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Verificar si usa el sistema centralizado
        if 'centralized-colors.css' not in content:
            issues.append("❌ No usa centralized-colors.css")
        else:
            warnings.append("✅ Usa centralized-colors.css")
        
        # 2. Verificar estilos inline problemáticos
        inline_styles = re.findall(r'style="[^"]*"', content)
        if inline_styles:
            for style in inline_styles:
                # Verificar si usa colores hardcodeados
                if re.search(r'#[0-9a-fA-F]{3,6}', style):
                    issues.append(f"❌ Color hardcodeado: {style[:50]}...")
                elif re.search(r'background-color:\s*white|color:\s*black', style):
                    issues.append(f"❌ Color básico hardcodeado: {style[:50]}...")
                elif re.search(r'padding:\s*\d+px|margin:\s*\d+px', style):
                    issues.append(f"❌ Espaciado hardcodeado: {style[:50]}...")
                else:
                    warnings.append(f"⚠️  Estilo inline: {style[:50]}...")
        
        # 3. Verificar uso de variables CSS
        css_vars = re.findall(r'var\(--[^)]+\)', content)
        if css_vars:
            warnings.append(f"✅ Usa {len(css_vars)} variables CSS")
        
        # 4. Verificar clases Bootstrap que podrían necesitar ajuste
        bootstrap_classes = re.findall(r'class="[^"]*"', content)
        problematic_classes = []
        for cls in bootstrap_classes:
            if 'bg-' in cls and 'bg-primary' not in cls and 'bg-secondary' not in cls:
                problematic_classes.append(cls)
            elif 'text-' in cls and 'text-primary' not in cls and 'text-secondary' not in cls:
                problematic_classes.append(cls)
        
        if problematic_classes:
            for cls in problematic_classes[:3]:  # Solo mostrar los primeros 3
                issues.append(f"❌ Clase Bootstrap problemática: {cls[:50]}...")
        
        # 5. Verificar si extiende base.html correctamente
        if '{% extends' in content:
            if 'base.html' in content or 'base_clean.html' in content:
                warnings.append("✅ Extiende template base correctamente")
            else:
                issues.append("❌ No extiende template base estándar")
        
        return issues, warnings
        
    except Exception as e:
        return [f"❌ Error al leer archivo: {e}"], []

def analyze_all_templates():
    """Analiza todos los templates operativos"""
    templates_dir = Path("/home/maxgonpe/talleres/car/car/templates")
    
    print("🔍 ANÁLISIS DE COMPLIANCE DE TEMPLATES")
    print("=" * 60)
    
    all_templates = []
    for html_file in templates_dir.rglob("*.html"):
        all_templates.append(html_file)
    
    compliant_templates = []
    non_compliant_templates = []
    partially_compliant_templates = []
    
    for template_path in sorted(all_templates):
        relative_path = template_path.relative_to(templates_dir)
        issues, warnings = check_template_compliance(template_path)
        
        print(f"\n📄 {relative_path}")
        print("-" * 40)
        
        if not issues:
            print("✅ 100% COMPLIANT - Perfecto!")
            compliant_templates.append(str(relative_path))
        elif len(issues) <= 2:
            print("⚠️  PARCIALMENTE COMPLIANT - Necesita ajustes menores")
            for issue in issues:
                print(f"  {issue}")
            for warning in warnings:
                print(f"  {warning}")
            partially_compliant_templates.append(str(relative_path))
        else:
            print("❌ NO COMPLIANT - Necesita trabajo significativo")
            for issue in issues:
                print(f"  {issue}")
            for warning in warnings:
                print(f"  {warning}")
            non_compliant_templates.append(str(relative_path))
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN FINAL:")
    print(f"✅ Templates 100% compliant: {len(compliant_templates)}")
    print(f"⚠️  Templates parcialmente compliant: {len(partially_compliant_templates)}")
    print(f"❌ Templates no compliant: {len(non_compliant_templates)}")
    print(f"📄 Total de templates: {len(all_templates)}")
    
    if compliant_templates:
        print(f"\n🎉 TEMPLATES PERFECTOS ({len(compliant_templates)}):")
        for template in compliant_templates:
            print(f"  ✅ {template}")
    
    if partially_compliant_templates:
        print(f"\n⚠️  TEMPLATES QUE NECESITAN AJUSTES MENORES ({len(partially_compliant_templates)}):")
        for template in partially_compliant_templates:
            print(f"  ⚠️  {template}")
    
    if non_compliant_templates:
        print(f"\n❌ TEMPLATES QUE NECESITAN TRABAJO ({len(non_compliant_templates)}):")
        for template in non_compliant_templates:
            print(f"  ❌ {template}")
    
    return compliant_templates, partially_compliant_templates, non_compliant_templates

def main():
    """Función principal"""
    compliant, partial, non_compliant = analyze_all_templates()
    
    print("\n" + "=" * 60)
    print("🎯 RECOMENDACIONES:")
    
    if non_compliant:
        print(f"1. Priorizar {len(non_compliant)} templates no compliant")
        print("2. Revisar estilos inline y colores hardcodeados")
        print("3. Asegurar uso de centralized-colors.css")
    
    if partial:
        print(f"4. Ajustar {len(partial)} templates parcialmente compliant")
        print("5. Reemplazar clases Bootstrap problemáticas")
    
    if compliant:
        print(f"6. ✅ {len(compliant)} templates están perfectos!")
    
    print("\n🚀 ¡Análisis completado!")

if __name__ == "__main__":
    main()






