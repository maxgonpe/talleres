#!/usr/bin/env python3
"""
Script para transformar templates HTML y reemplazar estilos inline con variables centralizadas
"""

import os
import re
from pathlib import Path

# Mapeo de estilos inline comunes a variables CSS
STYLE_MAPPINGS = {
    # Colores de fondo
    r'background-color:\s*#ffffff': 'background-color: var(--bg-card)',
    r'background-color:\s*#f8f9fa': 'background-color: var(--bg-secondary)',
    r'background-color:\s*#f5f5f5': 'background-color: var(--bg-secondary)',
    r'background:\s*#ffffff': 'background-color: var(--bg-card)',
    r'background:\s*#f8f9fa': 'background-color: var(--bg-secondary)',
    r'background:\s*white': 'background-color: var(--bg-card)',
    
    # Colores de texto
    r'color:\s*#000000': 'color: var(--text-primary)',
    r'color:\s*#333333': 'color: var(--text-primary)',
    r'color:\s*#666666': 'color: var(--text-secondary)',
    r'color:\s*#999999': 'color: var(--text-muted)',
    r'color:\s*black': 'color: var(--text-primary)',
    r'color:\s*white': 'color: var(--text-inverse)',
    
    # Bordes
    r'border:\s*1px solid #ddd': 'border: 1px solid var(--border-color)',
    r'border:\s*1px solid #eee': 'border: 1px solid var(--border-color)',
    r'border:\s*2px solid #ddd': 'border: 2px solid var(--border-color)',
    r'border-bottom:\s*1px solid #eee': 'border-bottom: 1px solid var(--border-color)',
    r'border-bottom:\s*1px solid #ddd': 'border-bottom: 1px solid var(--border-color)',
    
    # Padding y margin
    r'padding:\s*1rem': 'padding: var(--spacing-md)',
    r'padding:\s*0\.5rem': 'padding: var(--spacing-sm)',
    r'padding:\s*0\.25rem': 'padding: var(--spacing-xs)',
    r'padding:\s*1\.5rem': 'padding: var(--spacing-lg)',
    r'padding:\s*2rem': 'padding: var(--spacing-xl)',
    r'margin:\s*1rem': 'margin: var(--spacing-md)',
    r'margin:\s*0\.5rem': 'margin: var(--spacing-sm)',
    r'margin:\s*0\.25rem': 'margin: var(--spacing-xs)',
    r'margin:\s*1\.5rem': 'margin: var(--spacing-lg)',
    r'margin:\s*2rem': 'margin: var(--spacing-xl)',
    
    # Border radius
    r'border-radius:\s*8px': 'border-radius: var(--border-radius-md)',
    r'border-radius:\s*10px': 'border-radius: var(--border-radius-lg)',
    r'border-radius:\s*5px': 'border-radius: var(--border-radius-sm)',
    r'border-radius:\s*15px': 'border-radius: var(--border-radius-xl)',
    r'border-radius:\s*25px': 'border-radius: var(--border-radius-full)',
    
    # Box shadow
    r'box-shadow:\s*0 2px 10px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-md)',
    r'box-shadow:\s*0 4px 15px rgba\(0,0,0,0\.1\)': 'box-shadow: var(--shadow-lg)',
    r'box-shadow:\s*0 2px 6px rgba\(0,0,0,0\.05\)': 'box-shadow: var(--shadow-sm)',
    
    # Transiciones
    r'transition:\s*all 0\.3s ease': 'transition: var(--transition)',
    r'transition:\s*background-color 0\.2s': 'transition: var(--transition-fast)',
    r'transition:\s*all 0\.5s ease': 'transition: var(--transition-slow)',
}

def transform_template(file_path):
    """Transforma un template HTML reemplazando estilos inline"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Aplicar mapeos de estilos
        for pattern, replacement in STYLE_MAPPINGS.items():
            content = re.sub(pattern, replacement, content)
        
        # Si hubo cambios, escribir el archivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Transformado: {file_path}")
            return True
        else:
            print(f"⏭️  Sin cambios: {file_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error en {file_path}: {e}")
        return False

def main():
    """Función principal"""
    templates_dir = Path("/home/maxgonpe/talleres/car/car/templates")
    
    if not templates_dir.exists():
        print(f"❌ Directorio no encontrado: {templates_dir}")
        return
    
    print("🎨 Iniciando transformación de templates...")
    print("=" * 50)
    
    transformed_count = 0
    total_count = 0
    
    # Buscar todos los archivos HTML
    for html_file in templates_dir.rglob("*.html"):
        total_count += 1
        if transform_template(html_file):
            transformed_count += 1
    
    print("=" * 50)
    print(f"📊 Resumen:")
    print(f"   Total de archivos: {total_count}")
    print(f"   Archivos transformados: {transformed_count}")
    print(f"   Archivos sin cambios: {total_count - transformed_count}")
    print("✅ Transformación completada!")

if __name__ == "__main__":
    main()






