#!/usr/bin/env python3
"""
Script para verificar la compra 13 y sus items
"""

import sqlite3
from decimal import Decimal
import os

def verificar_compra_13():
    print("🔍 VERIFICANDO COMPRA 13 Y SUS ITEMS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 13
        print("📊 VERIFICANDO COMPRA 13...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra, observaciones
            FROM car_compra 
            WHERE id = 13
        """)
        
        compra_13 = cursor.fetchone()
        if not compra_13:
            print("❌ No se encontró la compra ID 13")
            
            # Verificar todas las compras recientes
            cursor.execute("""
                SELECT id, numero_compra, proveedor, estado, total
                FROM car_compra 
                ORDER BY id DESC
                LIMIT 5
            """)
            
            compras = cursor.fetchall()
            print(f"\n  Compras recientes:")
            for compra in compras:
                c_id, numero, proveedor, estado, total = compra
                print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}, Total: ${total}")
            
            return
        
        c_id, numero, proveedor, estado, total, fecha, observaciones = compra_13
        
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha: {fecha}")
        print(f"  Observaciones: {observaciones}")
        
        # 2. VERIFICAR ITEMS DE LA COMPRA 13
        print("\n📦 VERIFICANDO ITEMS DE LA COMPRA 13...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido, ci.fecha_recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 13
            ORDER BY ci.id
        """)
        
        items_13 = cursor.fetchall()
        
        if items_13:
            print(f"  Items encontrados: {len(items_13)}")
            for item in items_13:
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
            print(f"  ❌ No hay items en la compra 13")
            
            # Verificar si hay items en otras compras recientes
            cursor.execute("""
                SELECT ci.id, ci.compra_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal
                FROM car_compraitem ci
                ORDER BY ci.id DESC
                LIMIT 5
            """)
            
            items_recientes = cursor.fetchall()
            if items_recientes:
                print(f"\n  Items recientes en otras compras:")
                for item in items_recientes:
                    item_id, compra_id, repuesto_id, cantidad, precio, subtotal = item
                    print(f"    Item ID: {item_id}, Compra ID: {compra_id}, Repuesto ID: {repuesto_id}, Cantidad: {cantidad}, Precio: ${precio}")
        
        # 3. VERIFICAR ACEITE 10W-40 ACTUAL
        print(f"\n🔍 VERIFICANDO ACEITE 10W-40 ACTUAL...")
        
        cursor.execute("""
            SELECT id, nombre, sku, stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE id = 3
        """)
        
        aceite = cursor.fetchone()
        if aceite:
            r_id, nombre, sku, stock, precio_costo, precio_venta = aceite
            print(f"  Repuesto: {nombre}")
            print(f"  SKU: {sku}")
            print(f"  Stock actual: {stock}")
            print(f"  Precio costo actual: ${precio_costo}")
            print(f"  Precio venta actual: ${precio_venta}")
            print(f"  Factor de margen: {float(precio_venta / precio_costo):.4f}")
        
        # 4. CREAR ITEM SI NO EXISTE
        if len(items_13) == 0:
            print(f"\n📦 CREANDO ITEM PARA LA COMPRA 13...")
            
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
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 13
            ORDER BY ci.id
        """)
        
        items_final = cursor.fetchall()
        
        if items_final:
            print(f"  Items en la compra 13: {len(items_final)}")
            for item in items_final:
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
            print(f"  ❌ No hay items en la compra 13")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡COMPRA 13 VERIFICADA!")
        print("Ahora puedes:")
        print("  1. Ir al módulo de Compras")
        print("  2. Ver la compra 13")
        print("  3. Verificar que aparezcan los items en la lista")
        print("  4. Probar las acciones de confirmar o cancelar")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_compra_13()



