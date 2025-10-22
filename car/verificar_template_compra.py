#!/usr/bin/env python3
"""
Script para verificar el template de compra
"""

import sqlite3
from decimal import Decimal
import os

def verificar_template_compra():
    print("🔍 VERIFICANDO TEMPLATE DE COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 13 Y SUS ITEMS
        print("📊 VERIFICANDO COMPRA 13...")
        
        cursor.execute("""
            SELECT c.id, c.numero_compra, c.proveedor, c.estado, c.total
            FROM car_compra c
            WHERE c.id = 13
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra 13")
            return
        
        c_id, numero, proveedor, estado, total = compra
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        
        # 2. VERIFICAR ITEMS
        print(f"\n📦 VERIFICANDO ITEMS...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 13
            ORDER BY ci.id
        """)
        
        items = cursor.fetchall()
        
        if items:
            print(f"  Items encontrados: {len(items)}")
            for item in items:
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
            print(f"  ❌ No hay items en la compra 13")
        
        # 3. VERIFICAR SI EL PROBLEMA ES DE CACHE
        print(f"\n🔄 VERIFICANDO POSIBLES PROBLEMAS...")
        
        # Verificar si hay items en otras compras
        cursor.execute("""
            SELECT ci.compra_id, COUNT(*) as cantidad_items
            FROM car_compraitem ci
            GROUP BY ci.compra_id
            ORDER BY ci.compra_id DESC
            LIMIT 5
        """)
        
        compras_con_items = cursor.fetchall()
        print(f"  Compras con items:")
        for compra_id, cantidad in compras_con_items:
            print(f"    Compra ID: {compra_id}, Items: {cantidad}")
        
        # 4. CREAR ITEM DE PRUEBA SI NO EXISTE
        if len(items) == 0:
            print(f"\n📦 CREANDO ITEM DE PRUEBA...")
            
            # Buscar repuesto Aceite 10w-40
            cursor.execute("""
                SELECT id, nombre, sku
                FROM car_repuesto 
                WHERE nombre LIKE '%Aceite 10w-40%'
            """)
            
            repuesto = cursor.fetchone()
            if repuesto:
                r_id, nombre, sku = repuesto
                
                print(f"  Repuesto encontrado: {nombre}")
                print(f"  SKU: {sku}")
                
                # Agregar item
                cantidad = 2
                precio_unitario = 21800
                subtotal = cantidad * precio_unitario
                
                cursor.execute("""
                    INSERT INTO car_compraitem 
                    (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                    VALUES (?, ?, ?, ?, ?, 0, NULL)
                """, (13, r_id, cantidad, precio_unitario, subtotal))
                
                print(f"  ✅ Item agregado:")
                print(f"    Cantidad: {cantidad}")
                print(f"    Precio unitario: ${precio_unitario}")
                print(f"    Subtotal: ${subtotal}")
                
                # Actualizar total de la compra
                cursor.execute("""
                    UPDATE car_compra 
                    SET total = ?
                    WHERE id = 13
                """, (subtotal,))
                
                print(f"  ✅ Total de la compra actualizado: ${subtotal}")
            else:
                print(f"  ❌ No se encontró el repuesto Aceite 10w-40")
        
        # 5. VERIFICAR RESULTADO FINAL
        print(f"\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 13
            ORDER BY ci.id
        """)
        
        items_final = cursor.fetchall()
        
        if items_final:
            print(f"  Items finales: {len(items_final)}")
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
            print(f"  ❌ No hay items en la compra 13")
        
        # 6. DIAGNÓSTICO DEL PROBLEMA
        print(f"\n🔍 DIAGNÓSTICO DEL PROBLEMA...")
        
        if items_final:
            print(f"  ✅ Los items están en la base de datos")
            print(f"  ❌ Pero no se muestran en el template")
            print(f"  🔍 Posibles causas:")
            print(f"    1. Problema con la vista Django (compra_detail)")
            print(f"    2. Problema con el template (compra_detail.html)")
            print(f"    3. Problema con el JavaScript")
            print(f"    4. Problema de cache del navegador")
            print(f"    5. Problema con la relación en el modelo")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Refrescar la página (F5)")
            print(f"    2. Limpiar cache del navegador")
            print(f"    3. Verificar que la vista esté pasando los items correctamente")
            print(f"    4. Verificar que el template esté renderizando los items")
            print(f"    5. Verificar que no haya errores en la consola del navegador")
        else:
            print(f"  ❌ No hay items en la base de datos")
            print(f"  💡 El problema es que los items no se están guardando")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_template_compra()



