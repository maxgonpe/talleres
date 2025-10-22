#!/usr/bin/env python3
"""
Script para verificar la consulta de items en la compra
"""

import sqlite3
import os

def verificar_consulta_items():
    print("🔍 VERIFICANDO CONSULTA DE ITEMS EN LA COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 17
        print("📊 VERIFICANDO COMPRA 17...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE id = 17
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra 17")
            return
        
        c_id, numero, proveedor, estado, total = compra
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        
        # 2. VERIFICAR ITEMS DE LA COMPRA
        print(f"\n📦 VERIFICANDO ITEMS DE LA COMPRA...")
        
        cursor.execute("""
            SELECT ci.id, ci.compra_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 17
            ORDER BY r.nombre
        """)
        
        items = cursor.fetchall()
        
        print(f"  Items encontrados: {len(items)}")
        for item in items:
            item_id, compra_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = item
            print(f"    Item ID: {item_id}")
            print(f"      Compra ID: {compra_id}")
            print(f"      Repuesto ID: {repuesto_id}")
            print(f"      Repuesto: {nombre}")
            print(f"      SKU: {sku}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print(f"      ---")
        
        # 3. VERIFICAR RELACIÓN COMPRA-ITEMS
        print(f"\n🔍 VERIFICANDO RELACIÓN COMPRA-ITEMS...")
        
        # Verificar si hay items en car_compraitem para la compra 17
        cursor.execute("""
            SELECT COUNT(*) 
            FROM car_compraitem 
            WHERE compra_id = 17
        """)
        
        count_items = cursor.fetchone()[0]
        print(f"  Items en car_compraitem para compra 17: {count_items}")
        
        if count_items > 0:
            print("  ✅ Hay items en la tabla car_compraitem")
            
            # Verificar la estructura de la tabla
            cursor.execute("PRAGMA table_info(car_compraitem)")
            columns = cursor.fetchall()
            
            print(f"  Estructura de car_compraitem:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                print(f"    {col_name}: {col_type} {'NOT NULL' if not_null else 'NULL'}")
            
            # Verificar datos específicos
            cursor.execute("""
                SELECT * 
                FROM car_compraitem 
                WHERE compra_id = 17
            """)
            
            items_raw = cursor.fetchall()
            print(f"  Datos raw de car_compraitem:")
            for item in items_raw:
                print(f"    {item}")
        else:
            print("  ❌ No hay items en la tabla car_compraitem")
        
        # 4. VERIFICAR SI HAY PROBLEMA CON LA CONSULTA
        print(f"\n🔍 VERIFICANDO CONSULTA...")
        
        # Simular la consulta que hace la vista
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 17
            ORDER BY r.nombre
        """)
        
        items_consulta = cursor.fetchall()
        
        print(f"  Items que debería devolver la consulta: {len(items_consulta)}")
        for item in items_consulta:
            item_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = item
            print(f"    Item ID: {item_id}")
            print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
            print(f"      SKU: {sku}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print(f"      ---")
        
        # 5. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        if len(items_consulta) > 0:
            print(f"  ✅ Hay {len(items_consulta)} items en la base de datos")
            print(f"  ✅ La consulta debería devolver {len(items_consulta)} items")
            print(f"  ❌ Pero la vista devuelve 0 items")
            
            print(f"\n  🔍 POSIBLES CAUSAS:")
            print(f"    1. La vista no está ejecutando la consulta correctamente")
            print(f"    2. Hay un problema con el ORM de Django")
            print(f"    3. Hay un problema con la relación compra-items")
            print(f"    4. Hay un problema con el contexto del template")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Verificar que la vista esté ejecutando la consulta")
            print(f"    2. Verificar que no haya errores en la consola del navegador")
            print(f"    3. Verificar que la URL sea correcta")
            print(f"    4. Verificar que la vista se esté ejecutando")
            print(f"    5. Agregar debug a la vista para verificar la consulta")
        else:
            print(f"  ❌ No hay items en la base de datos")
            print(f"  💡 El problema está en que no se están guardando los items")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compra 17 encontrada")
        print(f"  ✅ Items en la base de datos: {len(items_consulta)}")
        print(f"  ✅ Consulta verificada")
        print(f"  ❌ Pero la vista devuelve 0 items")
        print(f"  💡 El problema está en la vista o en el ORM")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_consulta_items()



