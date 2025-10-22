#!/usr/bin/env python3
"""
Script para verificar la vista y el template paso a paso
"""

import sqlite3
from decimal import Decimal
import os

def verificar_vista_template():
    print("🔍 VERIFICANDO VISTA Y TEMPLATE PASO A PASO")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 17 Y SUS ITEMS
        print("📊 VERIFICANDO COMPRA 17 Y SUS ITEMS...")
        
        cursor.execute("""
            SELECT c.id, c.numero_compra, c.proveedor, c.estado, c.total,
                   ci.id as item_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compra c
            LEFT JOIN car_compraitem ci ON c.id = ci.compra_id
            LEFT JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE c.id = 17
            ORDER BY ci.id
        """)
        
        resultados = cursor.fetchall()
        
        if resultados:
            compra = resultados[0]
            c_id, numero, proveedor, estado, total = compra[:5]
            
            print(f"  Compra: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
            
            # Verificar items
            items = []
            for resultado in resultados:
                if resultado[5] is not None:  # Si hay item_id
                    item_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = resultado[5:]
                    items.append({
                        'id': item_id,
                        'repuesto_id': repuesto_id,
                        'cantidad': cantidad,
                        'precio_unitario': precio,
                        'subtotal': subtotal,
                        'recibido': recibido,
                        'nombre': nombre,
                        'sku': sku
                    })
            
            print(f"\n  Items encontrados: {len(items)}")
            for item in items:
                print(f"    Item ID: {item['id']}")
                print(f"      Repuesto: {item['nombre']} (ID: {item['repuesto_id']})")
                print(f"      SKU: {item['sku']}")
                print(f"      Cantidad: {item['cantidad']}")
                print(f"      Precio unitario: ${item['precio_unitario']}")
                print(f"      Subtotal: ${item['subtotal']}")
                print(f"      Recibido: {item['recibido']}")
                print(f"      ---")
        else:
            print("❌ No se encontró la compra 17")
            return
        
        # 2. SIMULAR LA VISTA COMPRA_DETAIL
        print(f"\n🔍 SIMULANDO LA VISTA COMPRA_DETAIL...")
        
        # Simular la consulta que hace la vista
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku, r.stock, r.precio_costo, r.precio_venta
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 17
            ORDER BY r.nombre
        """)
        
        items_vista = cursor.fetchall()
        
        print(f"  Items que debería devolver la vista: {len(items_vista)}")
        for item in items_vista:
            item_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku, stock, precio_costo, precio_venta = item
            print(f"    Item ID: {item_id}")
            print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
            print(f"      SKU: {sku}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print(f"      Stock actual: {stock}")
            print(f"      Precio costo: ${precio_costo}")
            print(f"      Precio venta: ${precio_venta}")
            print(f"      ---")
        
        # 3. VERIFICAR LA LÓGICA DEL TEMPLATE
        print(f"\n🔍 VERIFICANDO LA LÓGICA DEL TEMPLATE...")
        
        if items_vista:
            print(f"  ✅ Hay {len(items_vista)} items en la base de datos")
            print(f"  ✅ La consulta de la vista debería devolver {len(items_vista)} items")
            print(f"  ✅ El template debería mostrar la tabla con {len(items_vista)} filas")
            print(f"  ❌ Pero no se está mostrando en el navegador")
            
            print(f"\n  🔍 POSIBLES CAUSAS:")
            print(f"    1. La vista no está pasando 'items' al contexto")
            print(f"    2. La variable 'items' está vacía en el template")
            print(f"    3. Hay un problema con el JavaScript AJAX")
            print(f"    4. El template no se está renderizando correctamente")
            print(f"    5. Hay un problema con la herencia del template")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Agregar debug al template para verificar la variable 'items'")
            print(f"    2. Verificar que la vista esté pasando 'items' al contexto")
            print(f"    3. Verificar que no haya errores en el template")
            print(f"    4. Verificar que el JavaScript no esté interfiriendo")
        else:
            print(f"  ❌ No hay items en la base de datos")
            print(f"  💡 El problema está en que no se están guardando los items")
        
        # 4. CREAR DEBUG PARA EL TEMPLATE
        print(f"\n🛠️ CREANDO DEBUG PARA EL TEMPLATE...")
        
        debug_template = """
<!-- DEBUG: Verificar items -->
<div class="alert alert-info">
    <strong>DEBUG:</strong> 
    <br>Items count: {{ items|length }}
    <br>Items: {{ items }}
    <br>Items type: {{ items|default:"No items" }}
    <br>Items empty: {{ items|yesno:"No,Yes" }}
</div>
"""
        
        print(f"  ✅ Debug template creado")
        print(f"  💡 Agregar este debug al template para verificar la variable 'items'")
        
        # 5. VERIFICAR SI HAY PROBLEMA CON LA HERENCIA
        print(f"\n🔍 VERIFICANDO HERENCIA DEL TEMPLATE...")
        
        # Leer el template base
        try:
            with open('car/templates/car/compras/compra_detail.html', 'r') as f:
                template_content = f.read()
            
            if '{% extends' in template_content:
                print(f"  ✅ El template extiende de otro template")
                # Buscar la línea de extends
                lines = template_content.split('\n')
                for i, line in enumerate(lines):
                    if '{% extends' in line:
                        print(f"    Línea {i+1}: {line.strip()}")
            else:
                print(f"  ❌ El template no extiende de otro template")
            
            if '{% block' in template_content:
                print(f"  ✅ El template tiene bloques")
                # Buscar bloques
                lines = template_content.split('\n')
                for i, line in enumerate(lines):
                    if '{% block' in line:
                        print(f"    Línea {i+1}: {line.strip()}")
            else:
                print(f"  ❌ El template no tiene bloques")
                
        except Exception as e:
            print(f"  ❌ Error al leer el template: {e}")
        
        # 6. VERIFICAR SI HAY PROBLEMA CON EL JAVASCRIPT
        print(f"\n🔍 VERIFICANDO JAVASCRIPT...")
        
        if 'actualizarListadoItems' in template_content:
            print(f"  ✅ La función actualizarListadoItems está en el template")
        else:
            print(f"  ❌ La función actualizarListadoItems NO está en el template")
        
        if 'fetch(' in template_content:
            print(f"  ✅ Hay llamadas fetch en el template")
        else:
            print(f"  ❌ No hay llamadas fetch en el template")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        if items_vista:
            print("  ✅ Los items están en la base de datos")
            print("  ✅ La consulta de la vista debería funcionar")
            print("  ❌ Pero no se muestran en el template")
            print("  🔍 El problema está en el template o en la vista")
            print("  💡 Agregar debug al template para verificar la variable 'items'")
        else:
            print("  ❌ No hay items en la base de datos")
            print("  💡 El problema está en el proceso de guardado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_vista_template()



