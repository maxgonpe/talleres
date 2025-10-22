#!/usr/bin/env python3
"""
Script para agregar un item a la compra ID 4
"""

import sqlite3
from decimal import Decimal
import os
from datetime import datetime

def agregar_item_compra():
    print("📦 AGREGANDO ITEM A COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA ID 4
        print("📊 VERIFICANDO COMPRA ID 4...")
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE id = 4
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra ID 4")
            return
        
        c_id, numero, proveedor, estado, total = compra
        print(f"  Compra: {numero}")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total actual: ${total}")
        
        # 2. VERIFICAR REPUESTO ACEITE 10W-40
        print("\n🔍 VERIFICANDO REPUESTO ACEITE 10W-40...")
        cursor.execute("""
            SELECT id, nombre, sku, stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite 10w-40%'
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró el repuesto Aceite 10w-40")
            return
        
        r_id, nombre, sku, stock, precio_costo, precio_venta = repuesto
        print(f"  Repuesto: {nombre}")
        print(f"  SKU: {sku}")
        print(f"  Stock: {stock}")
        print(f"  Precio costo: ${precio_costo}")
        print(f"  Precio venta: ${precio_venta}")
        
        # 3. AGREGAR ITEM A LA COMPRA
        print("\n📦 AGREGANDO ITEM A LA COMPRA...")
        
        cantidad = 2
        precio_unitario = 25000
        subtotal = cantidad * precio_unitario
        
        print(f"  Cantidad: {cantidad}")
        print(f"  Precio unitario: ${precio_unitario}")
        print(f"  Subtotal: ${subtotal}")
        
        # Verificar si ya existe el item
        cursor.execute("""
            SELECT id, cantidad, precio_unitario, subtotal
            FROM car_compraitem 
            WHERE compra_id = 4 AND repuesto_id = ?
        """, (r_id,))
        
        item_existente = cursor.fetchone()
        
        if item_existente:
            print(f"  ⚠️ Item ya existe, actualizando...")
            item_id, cant_actual, precio_actual, subtotal_actual = item_existente
            nueva_cantidad = cant_actual + cantidad
            nuevo_subtotal = nueva_cantidad * precio_unitario
            
            cursor.execute("""
                UPDATE car_compraitem 
                SET cantidad = ?, precio_unitario = ?, subtotal = ?
                WHERE id = ?
            """, (nueva_cantidad, precio_unitario, nuevo_subtotal, item_id))
            
            print(f"  ✅ Item actualizado:")
            print(f"    Cantidad anterior: {cant_actual}")
            print(f"    Cantidad final: {nueva_cantidad}")
            print(f"    Subtotal anterior: ${subtotal_actual}")
            print(f"    Subtotal final: ${nuevo_subtotal}")
        else:
            print(f"  ➕ Creando nuevo item...")
            cursor.execute("""
                INSERT INTO car_compraitem 
                (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                VALUES (?, ?, ?, ?, ?, 0, NULL)
            """, (4, r_id, cantidad, precio_unitario, subtotal))
            
            print(f"  ✅ Item creado exitosamente")
        
        # 4. ACTUALIZAR TOTAL DE LA COMPRA
        print("\n💰 ACTUALIZANDO TOTAL DE LA COMPRA...")
        
        cursor.execute("""
            SELECT SUM(subtotal) as total_calculado
            FROM car_compraitem 
            WHERE compra_id = 4
        """)
        
        total_calculado = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            UPDATE car_compra 
            SET total = ?
            WHERE id = 4
        """, (total_calculado,))
        
        print(f"  ✅ Total actualizado: ${total_calculado}")
        
        # 5. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 4
            ORDER BY ci.id
        """)
        
        items = cursor.fetchall()
        
        if items:
            print(f"  Items en compra 4: {len(items)}")
            for item in items:
                item_id, repuesto_id, cantidad, precio, subtotal, recibido = item
                
                # Obtener nombre del repuesto
                cursor.execute("""
                    SELECT nombre, sku
                    FROM car_repuesto 
                    WHERE id = ?
                """, (repuesto_id,))
                
                repuesto_info = cursor.fetchone()
                if repuesto_info:
                    nombre, sku = repuesto_info
                    print(f"    Item ID: {item_id}")
                    print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
                    print(f"      SKU: {sku}")
                    print(f"      Cantidad: {cantidad}")
                    print(f"      Precio unitario: ${precio}")
                    print(f"      Subtotal: ${subtotal}")
                    print(f"      Recibido: {recibido}")
                    print("      ---")
        else:
            print(f"  ❌ No hay items en la compra 4")
        
        # Verificar total final
        cursor.execute("""
            SELECT total FROM car_compra WHERE id = 4
        """)
        
        total_final = cursor.fetchone()[0]
        print(f"  Total final de la compra: ${total_final}")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡ITEM AGREGADO EXITOSAMENTE!")
        print("Ahora puedes verificar en la interfaz web que el item aparece en la lista.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    agregar_item_compra()



