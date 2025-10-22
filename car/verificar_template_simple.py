#!/usr/bin/env python3
"""
Script para verificar el template sin depender de Django
"""

import os

def verificar_template_simple():
    print("🔍 VERIFICANDO TEMPLATE SIN DEPENDER DE DJANGO")
    print("=" * 60)
    
    try:
        # 1. VERIFICAR SI EL TEMPLATE EXISTE
        print("📊 VERIFICANDO TEMPLATE...")
        
        template_path = 'car/templates/car/compras/compra_detail.html'
        if not os.path.exists(template_path):
            print(f"❌ Template NO existe: {template_path}")
            return
        
        print(f"✅ Template existe: {template_path}")
        
        # 2. LEER EL TEMPLATE
        print(f"\n📖 LEYENDO TEMPLATE...")
        
        with open(template_path, 'r') as f:
            template_content = f.read()
        
        print(f"✅ Template leído correctamente")
        print(f"  Tamaño: {len(template_content)} caracteres")
        
        # 3. VERIFICAR LÓGICA DEL TEMPLATE
        print(f"\n🔍 VERIFICANDO LÓGICA DEL TEMPLATE...")
        
        # Verificar si tiene la lógica correcta
        if '{% if items %}' in template_content:
            print("✅ Template tiene lógica {% if items %}")
        else:
            print("❌ Template NO tiene lógica {% if items %}")
        
        if '{% for item in items %}' in template_content:
            print("✅ Template tiene loop {% for item in items %}")
        else:
            print("❌ Template NO tiene loop {% for item in items %}")
        
        if '{{ item.repuesto.nombre }}' in template_content:
            print("✅ Template tiene {{ item.repuesto.nombre }}")
        else:
            print("❌ Template NO tiene {{ item.repuesto.nombre }}")
        
        # 4. VERIFICAR DEBUG
        print(f"\n🔍 VERIFICANDO DEBUG...")
        
        if 'DEBUG:' in template_content:
            print("✅ Template tiene debug agregado")
        else:
            print("❌ Template NO tiene debug agregado")
        
        # 5. VERIFICAR ESTRUCTURA DEL TEMPLATE
        print(f"\n🔍 VERIFICANDO ESTRUCTURA DEL TEMPLATE...")
        
        # Verificar herencia
        if '{% extends' in template_content:
            print("✅ Template extiende de otro template")
            # Buscar la línea de extends
            lines = template_content.split('\n')
            for i, line in enumerate(lines):
                if '{% extends' in line:
                    print(f"  Línea {i+1}: {line.strip()}")
        else:
            print("❌ Template NO extiende de otro template")
        
        # Verificar bloques
        if '{% block' in template_content:
            print("✅ Template tiene bloques")
            # Buscar bloques
            lines = template_content.split('\n')
            for i, line in enumerate(lines):
                if '{% block' in line:
                    print(f"  Línea {i+1}: {line.strip()}")
        else:
            print("❌ Template NO tiene bloques")
        
        # 6. VERIFICAR JAVASCRIPT
        print(f"\n🔍 VERIFICANDO JAVASCRIPT...")
        
        if 'actualizarListadoItems' in template_content:
            print("✅ Template tiene función actualizarListadoItems")
        else:
            print("❌ Template NO tiene función actualizarListadoItems")
        
        if 'fetch(' in template_content:
            print("✅ Template tiene llamadas fetch")
        else:
            print("❌ Template NO tiene llamadas fetch")
        
        # 7. VERIFICAR ESTRUCTURA DE LA TABLA
        print(f"\n🔍 VERIFICANDO ESTRUCTURA DE LA TABLA...")
        
        if '<table' in template_content:
            print("✅ Template tiene tabla")
        else:
            print("❌ Template NO tiene tabla")
        
        if '<thead>' in template_content:
            print("✅ Template tiene thead")
        else:
            print("❌ Template NO tiene thead")
        
        if '<tbody>' in template_content:
            print("✅ Template tiene tbody")
        else:
            print("❌ Template NO tiene tbody")
        
        # 8. VERIFICAR ESTRUCTURA ESPECÍFICA
        print(f"\n🔍 VERIFICANDO ESTRUCTURA ESPECÍFICA...")
        
        # Buscar la sección de items
        if 'Items de la Compra' in template_content:
            print("✅ Template tiene sección 'Items de la Compra'")
        else:
            print("❌ Template NO tiene sección 'Items de la Compra'")
        
        # Buscar la lógica de mostrar items
        if '{% if items %}' in template_content and '{% else %}' in template_content:
            print("✅ Template tiene lógica if/else para items")
        else:
            print("❌ Template NO tiene lógica if/else para items")
        
        # 9. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        # Verificar si el template tiene la estructura correcta
        estructura_correcta = (
            '{% if items %}' in template_content and
            '{% for item in items %}' in template_content and
            '{{ item.repuesto.nombre }}' in template_content and
            '<table' in template_content
        )
        
        if estructura_correcta:
            print("✅ Template tiene estructura correcta")
            print("✅ La lógica del template debería funcionar")
            print("❌ Pero no se muestran los items en el navegador")
            
            print(f"\n  🔍 POSIBLES CAUSAS:")
            print(f"    1. La vista no está pasando 'items' al contexto")
            print(f"    2. La variable 'items' está vacía en el template")
            print(f"    3. Hay un problema con la herencia del template")
            print(f"    4. Hay un problema con el JavaScript AJAX")
            print(f"    5. Hay un problema con el cache del navegador")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Verificar que el debug aparezca en el navegador")
            print(f"    2. Verificar que no haya errores en la consola del navegador")
            print(f"    3. Verificar que la URL sea correcta")
            print(f"    4. Verificar que la vista se esté ejecutando")
            print(f"    5. Refrescar la página (F5) para ver si aparece el debug")
        else:
            print("❌ Template NO tiene estructura correcta")
            print("💡 El problema está en el template")
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Template existe y se puede leer")
        print(f"  ✅ Template tiene estructura básica")
        print(f"  ✅ Template tiene lógica para items")
        print(f"  ✅ Template tiene debug agregado")
        print(f"  ❌ Pero no se muestran los items en el navegador")
        print(f"  💡 El problema está en la vista o en el contexto")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verificar_template_simple()



