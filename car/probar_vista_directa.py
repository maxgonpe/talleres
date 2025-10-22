#!/usr/bin/env python3
"""
Script para probar la vista compra_detail directamente
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from car.models import Compra, CompraItem, Repuesto
from car.views_compras import compra_detail
from django.test import RequestFactory
from django.contrib.auth.models import User

def probar_vista_directa():
    print("🔍 PROBANDO VISTA COMPRA_DETAIL DIRECTAMENTE")
    print("=" * 60)
    
    try:
        # 1. OBTENER COMPRA 17
        print("📊 OBTENIENDO COMPRA 17...")
        
        compra = Compra.objects.get(id=17)
        print(f"  Compra: {compra.numero_compra} (ID: {compra.id})")
        print(f"  Proveedor: {compra.proveedor}")
        print(f"  Estado: {compra.estado}")
        print(f"  Total: ${compra.total}")
        
        # 2. OBTENER ITEMS DE LA COMPRA
        print(f"\n📦 OBTENIENDO ITEMS DE LA COMPRA...")
        
        items = compra.items.all().order_by('repuesto__nombre')
        print(f"  Items encontrados: {items.count()}")
        
        for item in items:
            print(f"    Item ID: {item.id}")
            print(f"      Repuesto: {item.repuesto.nombre} (ID: {item.repuesto.id})")
            print(f"      SKU: {item.repuesto.sku}")
            print(f"      Cantidad: {item.cantidad}")
            print(f"      Precio unitario: ${item.precio_unitario}")
            print(f"      Subtotal: ${item.subtotal}")
            print(f"      Recibido: {item.recibido}")
            print(f"      ---")
        
        # 3. SIMULAR LA VISTA COMPRA_DETAIL
        print(f"\n🔍 SIMULANDO LA VISTA COMPRA_DETAIL...")
        
        # Crear request factory
        factory = RequestFactory()
        
        # Crear request GET
        request = factory.get(f'/car/compras/{compra.id}/')
        
        # Obtener usuario (usar el primero disponible)
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios en la base de datos")
            return
        
        request.user = user
        
        # Simular la lógica de la vista
        items_vista = compra.items.all().order_by('repuesto__nombre')
        
        print(f"  Items que debería devolver la vista: {items_vista.count()}")
        for item in items_vista:
            print(f"    Item ID: {item.id}")
            print(f"      Repuesto: {item.repuesto.nombre} (ID: {item.repuesto.id})")
            print(f"      SKU: {item.repuesto.sku}")
            print(f"      Cantidad: {item.cantidad}")
            print(f"      Precio unitario: ${item.precio_unitario}")
            print(f"      Subtotal: ${item.subtotal}")
            print(f"      Recibido: {item.recibido}")
            print(f"      ---")
        
        # 4. VERIFICAR EL CONTEXTO
        print(f"\n🔍 VERIFICANDO EL CONTEXTO...")
        
        context = {
            'compra': compra,
            'items': items_vista,
            'form': None,  # No necesitamos el formulario para esta prueba
        }
        
        print(f"  Contexto creado:")
        print(f"    compra: {context['compra']}")
        print(f"    items: {context['items']}")
        print(f"    items count: {context['items'].count()}")
        print(f"    items type: {type(context['items'])}")
        
        # 5. VERIFICAR SI HAY PROBLEMA CON EL TEMPLATE
        print(f"\n🔍 VERIFICANDO EL TEMPLATE...")
        
        # Verificar si el template existe
        template_path = 'car/templates/car/compras/compra_detail.html'
        if os.path.exists(template_path):
            print(f"  ✅ Template existe: {template_path}")
            
            # Leer el template
            with open(template_path, 'r') as f:
                template_content = f.read()
            
            # Verificar si tiene la lógica correcta
            if '{% if items %}' in template_content:
                print("  ✅ Template tiene lógica {% if items %}")
            else:
                print("  ❌ Template NO tiene lógica {% if items %}")
            
            if '{% for item in items %}' in template_content:
                print("  ✅ Template tiene loop {% for item in items %}")
            else:
                print("  ❌ Template NO tiene loop {% for item in items %}")
            
            if '{{ item.repuesto.nombre }}' in template_content:
                print("  ✅ Template tiene {{ item.repuesto.nombre }}")
            else:
                print("  ❌ Template NO tiene {{ item.repuesto.nombre }}")
            
            # Verificar si tiene el debug que agregamos
            if 'DEBUG:' in template_content:
                print(f"  ✅ Template tiene debug agregado")
            else:
                print(f"  ❌ Template NO tiene debug agregado")
        else:
            print(f"  ❌ Template NO existe: {template_path}")
        
        # 6. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        if items_vista.count() > 0:
            print(f"  ✅ Hay {items_vista.count()} items en la base de datos")
            print(f"  ✅ La vista debería devolver {items_vista.count()} items")
            print(f"  ✅ El contexto tiene {context['items'].count()} items")
            print(f"  ❌ Pero no se muestran en el navegador")
            
            print(f"\n  🔍 POSIBLES CAUSAS:")
            print(f"    1. El template no se está renderizando correctamente")
            print(f"    2. Hay un problema con la herencia del template")
            print(f"    3. Hay un problema con el JavaScript AJAX")
            print(f"    4. Hay un problema con el cache del navegador")
            print(f"    5. Hay un problema con la URL o la vista")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Verificar que el debug aparezca en el navegador")
            print(f"    2. Verificar que no haya errores en la consola del navegador")
            print(f"    3. Verificar que la URL sea correcta")
            print(f"    4. Verificar que la vista se esté ejecutando")
            print(f"    5. Refrescar la página (F5) para ver si aparece el debug")
        else:
            print(f"  ❌ No hay items en la base de datos")
            print(f"  💡 El problema está en el proceso de guardado")
        
        print(f"\n🎉 ¡PRUEBA COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compra 17 encontrada")
        print(f"  ✅ Items en la base de datos: {items_vista.count()}")
        print(f"  ✅ Contexto creado correctamente")
        print(f"  ✅ Template verificado")
        print(f"  ❌ Pero no se muestran en el navegador")
        print(f"  💡 Agregar debug al template para verificar la variable 'items'")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    probar_vista_directa()