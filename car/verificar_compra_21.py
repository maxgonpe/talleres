#!/usr/bin/env python3
"""
Script para verificar la compra 21 y sus items
"""

import sqlite3
import os

def verificar_compra_21():
    print("🔍 VERIFICANDO COMPRA 21 Y SUS ITEMS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 21
        print("📊 VERIFICANDO COMPRA 21...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            WHERE id = 21
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra 21")
            return
        
        c_id, numero, proveedor, estado, total, fecha = compra
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha: {fecha}")
        
        # 2. VERIFICAR ITEMS DE LA COMPRA 21
        print(f"\n📦 VERIFICANDO ITEMS DE LA COMPRA 21...")
        
        cursor.execute("""
            SELECT ci.id, ci.compra_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            LEFT JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 21
            ORDER BY ci.id
        """)
        
        items = cursor.fetchall()
        
        print(f"  Items encontrados: {len(items)}")
        for item in items:
            item_id, compra_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = item
            print(f"    Item ID: {item_id}")
            print(f"      Compra ID: {compra_id}")
            print(f"      Repuesto ID: {repuesto_id}")
            print(f"      Repuesto: {nombre or 'N/A'}")
            print(f"      SKU: {sku or 'N/A'}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print(f"      ---")
        
        # 3. VERIFICAR TODAS LAS COMPRAS
        print(f"\n📊 VERIFICANDO TODAS LAS COMPRAS...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            ORDER BY id DESC
            LIMIT 10
        """)
        
        compras = cursor.fetchall()
        
        print(f"  Últimas 10 compras:")
        for compra in compras:
            c_id, numero, proveedor, estado, total = compra
            print(f"    Compra {c_id}: {numero} - {proveedor} - {estado} - ${total}")
        
        # 4. VERIFICAR TODOS LOS ITEMS
        print(f"\n📦 VERIFICANDO TODOS LOS ITEMS...")
        
        cursor.execute("""
            SELECT ci.id, ci.compra_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            LEFT JOIN car_repuesto r ON ci.repuesto_id = r.id
            ORDER BY ci.id DESC
            LIMIT 10
        """)
        
        items_todos = cursor.fetchall()
        
        print(f"  Últimos 10 items:")
        for item in items_todos:
            item_id, compra_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = item
            print(f"    Item {item_id}: Compra {compra_id} - {nombre or 'N/A'} - Cantidad: {cantidad} - Precio: ${precio}")
        
        # 5. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        if len(items) > 0:
            print(f"  ✅ Hay {len(items)} items en la compra 21")
            print(f"  ✅ Los items se están guardando correctamente")
            print(f"  ❌ Pero no se muestran en el template")
            print(f"  💡 El problema está en el template o en la vista")
        else:
            print(f"  ❌ No hay items en la compra 21")
            print(f"  💡 El problema está en el proceso de guardado")
            print(f"  🔍 Posibles causas:")
            print(f"    1. El formulario no se está enviando correctamente")
            print(f"    2. La vista no está procesando el formulario")
            print(f"    3. Hay un problema con la validación del formulario")
            print(f"    4. Hay un problema con el JavaScript AJAX")
            print(f"    5. Los items se están guardando en otra compra")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compra 21 encontrada")
        print(f"  ✅ Items en la compra 21: {len(items)}")
        print(f"  ✅ Items totales en la base de datos: {len(items_todos)}")
        if len(items) == 0:
            print(f"  ❌ No hay items en la compra 21")
            print(f"  💡 El problema está en el proceso de guardado")
        else:
            print(f"  ✅ Hay items en la compra 21")
            print(f"  💡 El problema está en el template o en la vista")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_compra_21()



