#!/usr/bin/env python3
"""
Script para revisar la compra 16 y su proceso de agregar items
"""

import sqlite3
from decimal import Decimal
import os

def revisar_compra_16():
    print("🔍 REVISANDO COMPRA 16 Y PROCESO DE AGREGAR ITEMS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 16
        print("📊 VERIFICANDO COMPRA 16...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra, observaciones
            FROM car_compra 
            WHERE id = 16
        """)
        
        compra_16 = cursor.fetchone()
        if not compra_16:
            print("❌ No se encontró la compra ID 16")
            
            # Verificar todas las compras recientes
            cursor.execute("""
                SELECT id, numero_compra, proveedor, estado, total
                FROM car_compra 
                ORDER BY id DESC
                LIMIT 10
            """)
            
            compras = cursor.fetchall()
            print(f"\n  Compras recientes:")
            for compra in compras:
                c_id, numero, proveedor, estado, total = compra
                print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}, Total: ${total}")
            
            return
        
        c_id, numero, proveedor, estado, total, fecha, observaciones = compra_16
        
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha: {fecha}")
        print(f"  Observaciones: {observaciones}")
        
        # 2. VERIFICAR ITEMS DE LA COMPRA 16
        print("\n📦 VERIFICANDO ITEMS DE LA COMPRA 16...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido, ci.fecha_recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 16
            ORDER BY ci.id
        """)
        
        items_16 = cursor.fetchall()
        
        if items_16:
            print(f"  Items encontrados: {len(items_16)}")
            for item in items_16:
                item_id, repuesto_id, cantidad, precio, subtotal, recibido, fecha_recibido = item
                
                # Obtener nombre del repuesto
                cursor.execute("""
                    SELECT nombre, sku, stock, precio_costo, precio_venta
                    FROM car_repuesto 
                    WHERE id = ?
                """, (repuesto_id,))
                
                repuesto_info = cursor.fetchone()
                if repuesto_info:
                    nombre, sku, stock, precio_costo, precio_venta = repuesto_info
                    print(f"    Item ID: {item_id}")
                    print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
                    print(f"      SKU: {sku}")
                    print(f"      Cantidad: {cantidad}")
                    print(f"      Precio unitario: ${precio}")
                    print(f"      Subtotal: ${subtotal}")
                    print(f"      Recibido: {recibido}")
                    if fecha_recibido:
                        print(f"      Fecha recibido: {fecha_recibido}")
                    print(f"      ---")
                    print(f"      Stock actual del repuesto: {stock}")
                    print(f"      Precio costo actual: ${precio_costo}")
                    print(f"      Precio venta actual: ${precio_venta}")
                    print(f"      ---")
                else:
                    print(f"    Item ID: {item_id} - Repuesto no encontrado (ID: {repuesto_id})")
        else:
            print(f"  ❌ No hay items en la compra 16")
            
            # Verificar si hay items en otras compras recientes
            cursor.execute("""
                SELECT ci.id, ci.compra_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal
                FROM car_compraitem ci
                ORDER BY ci.id DESC
                LIMIT 10
            """)
            
            items_recientes = cursor.fetchall()
            if items_recientes:
                print(f"\n  Items recientes en otras compras:")
                for item in items_recientes:
                    item_id, compra_id, repuesto_id, cantidad, precio, subtotal = item
                    print(f"    Item ID: {item_id}, Compra ID: {compra_id}, Repuesto ID: {repuesto_id}, Cantidad: {cantidad}, Precio: ${precio}")
        
        # 3. VERIFICAR ESTRUCTURA DE LA TABLA COMPRAITEM
        print(f"\n🔍 VERIFICANDO ESTRUCTURA DE CAR_COMPRAITEM...")
        
        cursor.execute("PRAGMA table_info(car_compraitem)")
        columnas = cursor.fetchall()
        
        print(f"  Estructura de car_compraitem:")
        for columna in columnas:
            cid, nombre, tipo, notnull, default, pk = columna
            print(f"    {nombre}: {tipo} {'NOT NULL' if notnull else 'NULL'} {'PRIMARY KEY' if pk else ''} {'DEFAULT: ' + str(default) if default else ''}")
        
        # 4. VERIFICAR SI HAY PROBLEMA CON LA RELACIÓN
        print(f"\n🔗 VERIFICANDO RELACIÓN...")
        
        # Verificar que la compra existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM car_compra 
            WHERE id = 16
        """)
        
        count_compra = cursor.fetchone()[0]
        print(f"  Compras con ID 16: {count_compra}")
        
        # Verificar items por compra_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM car_compraitem 
            WHERE compra_id = 16
        """)
        
        count_items = cursor.fetchone()[0]
        print(f"  Items con compra_id = 16: {count_items}")
        
        # 5. CREAR ITEM DE PRUEBA SI NO EXISTE
        if len(items_16) == 0:
            print(f"\n📦 CREANDO ITEM DE PRUEBA PARA LA COMPRA 16...")
            
            # Buscar repuesto Aceite 10w-40
            cursor.execute("""
                SELECT id, nombre, sku, stock, precio_costo, precio_venta
                FROM car_repuesto 
                WHERE nombre LIKE '%Aceite 10w-40%'
            """)
            
            repuesto = cursor.fetchone()
            if repuesto:
                r_id, nombre, sku, stock, precio_costo, precio_venta = repuesto
                
                print(f"  Repuesto encontrado: {nombre}")
                print(f"  SKU: {sku}")
                print(f"  Stock actual: {stock}")
                print(f"  Precio costo actual: ${precio_costo}")
                print(f"  Precio venta actual: ${precio_venta}")
                
                # Agregar item a la compra
                cantidad = 3
                precio_unitario = 30000
                subtotal = cantidad * precio_unitario
                
                cursor.execute("""
                    INSERT INTO car_compraitem 
                    (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                    VALUES (?, ?, ?, ?, ?, 0, NULL)
                """, (16, r_id, cantidad, precio_unitario, subtotal))
                
                print(f"  ✅ Item agregado:")
                print(f"    Cantidad: {cantidad}")
                print(f"    Precio unitario: ${precio_unitario}")
                print(f"    Subtotal: ${subtotal}")
                
                # Actualizar total de la compra
                cursor.execute("""
                    UPDATE car_compra 
                    SET total = ?
                    WHERE id = 16
                """, (subtotal,))
                
                print(f"  ✅ Total de la compra actualizado: ${subtotal}")
            else:
                print(f"  ❌ No se encontró el repuesto Aceite 10w-40")
        
        # 6. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 16
            ORDER BY ci.id
        """)
        
        items_final = cursor.fetchall()
        
        if items_final:
            print(f"  Items finales en la compra 16: {len(items_final)}")
            for item in items_final:
                item_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = item
                print(f"    Item ID: {item_id}")
                print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
                print(f"      SKU: {sku}")
                print(f"      Cantidad: {cantidad}")
                print(f"      Precio unitario: ${precio}")
                print(f"      Subtotal: ${subtotal}")
                print(f"      Recibido: {recibido}")
                print(f"      ---")
        else:
            print(f"  ❌ No hay items en la compra 16")
        
        # 7. DIAGNÓSTICO DEL PROBLEMA
        print(f"\n🔍 DIAGNÓSTICO DEL PROBLEMA...")
        
        if items_final:
            print(f"  ✅ Los items están en la base de datos")
            print(f"  ✅ La relación compra-item funciona")
            print(f"  ❌ Pero no se muestran en el template")
            print(f"  🔍 Posibles causas:")
            print(f"    1. La vista Django no está pasando los items al template")
            print(f"    2. El template no está renderizando los items correctamente")
            print(f"    3. Hay un problema con el JavaScript AJAX")
            print(f"    4. Hay un problema de cache en el navegador")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Verificar que la vista esté pasando 'items' al contexto")
            print(f"    2. Verificar que el template esté usando 'for item in items'")
            print(f"    3. Refrescar la página (F5) en el navegador")
            print(f"    4. Limpiar cache del navegador")
            print(f"    5. Verificar que no haya errores en la consola del navegador")
            print(f"    6. Verificar que el JavaScript AJAX esté funcionando")
        else:
            print(f"  ❌ No hay items en la base de datos")
            print(f"  💡 El problema es que los items no se están guardando")
            print(f"  🔍 Posibles causas:")
            print(f"    1. El formulario no se está enviando correctamente")
            print(f"    2. La vista no está procesando el formulario")
            print(f"    3. Hay un problema con la validación del formulario")
            print(f"    4. Hay un problema con el JavaScript AJAX")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡REVISIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        if items_final:
            print("  ✅ Los items están en la base de datos")
            print("  ✅ La relación compra-item funciona")
            print("  ❌ Pero no se muestran en el template")
            print("  🔍 El problema está en el template o en la vista Django")
        else:
            print("  ❌ No hay items en la base de datos")
            print("  💡 El problema es que los items no se están guardando")
            print("  🔍 El problema está en el proceso de agregar items")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    revisar_compra_16()



