#!/usr/bin/env python3
"""
Script para verificar el estado actual de la compra y restaurar items
"""

import sqlite3
from decimal import Decimal
import os

def verificar_estado_compra():
    print("📦 VERIFICANDO ESTADO ACTUAL DE COMPRAS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR TODAS LAS COMPRAS
        print("📊 VERIFICANDO TODAS LAS COMPRAS...")
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            ORDER BY id DESC
        """)
        
        compras = cursor.fetchall()
        
        print(f"  Encontradas {len(compras)} compras:")
        for compra in compras:
            c_id, numero, proveedor, estado, total, fecha = compra
            print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}, Total: ${total}")
        
        # 2. VERIFICAR ITEMS DE CADA COMPRA
        print("\n📦 VERIFICANDO ITEMS DE CADA COMPRA...")
        
        for compra in compras:
            c_id, numero, proveedor, estado, total, fecha = compra
            
            print(f"\n  🔍 Compra {numero} (ID: {c_id}):")
            
            cursor.execute("""
                SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
                FROM car_compraitem ci
                WHERE ci.compra_id = ?
                ORDER BY ci.id
            """, (c_id,))
            
            items = cursor.fetchall()
            
            if items:
                print(f"    Items encontrados: {len(items)}")
                for item in items:
                    item_id, repuesto_id, cantidad, precio, subtotal, recibido = item
                    
                    # Obtener nombre del repuesto
                    cursor.execute("""
                        SELECT nombre, sku, stock, precio_venta
                        FROM car_repuesto 
                        WHERE id = ?
                    """, (repuesto_id,))
                    
                    repuesto_info = cursor.fetchone()
                    if repuesto_info:
                        nombre, sku, stock, precio_venta = repuesto_info
                        print(f"      Item ID: {item_id}")
                        print(f"        Repuesto: {nombre} (ID: {repuesto_id})")
                        print(f"        SKU: {sku}")
                        print(f"        Cantidad: {cantidad}")
                        print(f"        Precio unitario: ${precio}")
                        print(f"        Subtotal: ${subtotal}")
                        print(f"        Recibido: {recibido}")
                        print(f"        Stock actual: {stock}")
                        print(f"        Precio venta actual: ${precio_venta}")
                        print("        ---")
            else:
                print(f"    ❌ No hay items en esta compra")
        
        # 3. IDENTIFICAR COMPRA PARA RESTAURAR
        print("\n🔍 IDENTIFICANDO COMPRA PARA RESTAURAR...")
        
        # Buscar compra con estado borrador
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE estado = 'borrador'
            ORDER BY id DESC
            LIMIT 1
        """)
        
        compra_borrador = cursor.fetchone()
        
        if compra_borrador:
            c_id, numero, proveedor, estado, total = compra_borrador
            print(f"  Compra en borrador encontrada: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Total: ${total}")
            
            # Verificar si tiene items
            cursor.execute("""
                SELECT COUNT(*) FROM car_compraitem WHERE compra_id = ?
            """, (c_id,))
            
            cantidad_items = cursor.fetchone()[0]
            print(f"  Items actuales: {cantidad_items}")
            
            if cantidad_items == 0:
                print(f"  ⚠️ La compra no tiene items, vamos a agregar uno")
                
                # 4. AGREGAR ITEM A LA COMPRA
                print("\n📦 AGREGANDO ITEM A LA COMPRA...")
                
                # Buscar repuesto Aceite 10w-40
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
                
                print(f"  Repuesto encontrado: {nombre}")
                print(f"  SKU: {sku}")
                print(f"  Stock actual: {stock}")
                print(f"  Precio costo actual: ${precio_costo}")
                print(f"  Precio venta actual: ${precio_venta}")
                
                # Agregar item a la compra
                cantidad = 2
                precio_unitario = 25000
                subtotal = cantidad * precio_unitario
                
                cursor.execute("""
                    INSERT INTO car_compraitem 
                    (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                    VALUES (?, ?, ?, ?, ?, 0, NULL)
                """, (c_id, r_id, cantidad, precio_unitario, subtotal))
                
                print(f"  ✅ Item agregado:")
                print(f"    Cantidad: {cantidad}")
                print(f"    Precio unitario: ${precio_unitario}")
                print(f"    Subtotal: ${subtotal}")
                
                # Actualizar total de la compra
                cursor.execute("""
                    UPDATE car_compra 
                    SET total = ?
                    WHERE id = ?
                """, (subtotal, c_id))
                
                print(f"  ✅ Total de la compra actualizado: ${subtotal}")
                
            else:
                print(f"  ✅ La compra ya tiene {cantidad_items} items")
        else:
            print(f"  ❌ No se encontró compra en borrador")
            
            # Crear nueva compra en borrador
            print(f"\n📦 CREANDO NUEVA COMPRA EN BORRADOR...")
            
            cursor.execute("""
                INSERT INTO car_compra 
                (numero_compra, proveedor, fecha_compra, estado, total, observaciones, creado_por_id, creado_en, actualizado_en)
                VALUES ('COMP-0005', 'Proveedor Test', date('now'), 'borrador', 0, 'Compra de prueba', 1, datetime('now'), datetime('now'))
            """)
            
            nueva_compra_id = cursor.lastrowid
            print(f"  ✅ Nueva compra creada: ID {nueva_compra_id}")
            
            # Agregar item a la nueva compra
            cursor.execute("""
                SELECT id, nombre, sku, stock, precio_costo, precio_venta
                FROM car_repuesto 
                WHERE nombre LIKE '%Aceite 10w-40%'
            """)
            
            repuesto = cursor.fetchone()
            if repuesto:
                r_id, nombre, sku, stock, precio_costo, precio_venta = repuesto
                
                cantidad = 2
                precio_unitario = 25000
                subtotal = cantidad * precio_unitario
                
                cursor.execute("""
                    INSERT INTO car_compraitem 
                    (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                    VALUES (?, ?, ?, ?, ?, 0, NULL)
                """, (nueva_compra_id, r_id, cantidad, precio_unitario, subtotal))
                
                # Actualizar total de la compra
                cursor.execute("""
                    UPDATE car_compra 
                    SET total = ?
                    WHERE id = ?
                """, (subtotal, nueva_compra_id))
                
                print(f"  ✅ Item agregado a la nueva compra:")
                print(f"    Repuesto: {nombre}")
                print(f"    Cantidad: {cantidad}")
                print(f"    Precio unitario: ${precio_unitario}")
                print(f"    Subtotal: ${subtotal}")
        
        # 5. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE estado = 'borrador'
            ORDER BY id DESC
            LIMIT 1
        """)
        
        compra_final = cursor.fetchone()
        if compra_final:
            c_id, numero, proveedor, estado, total = compra_final
            
            print(f"  Compra final: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
            
            # Verificar items
            cursor.execute("""
                SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
                FROM car_compraitem ci
                WHERE ci.compra_id = ?
                ORDER BY ci.id
            """, (c_id,))
            
            items_final = cursor.fetchall()
            
            if items_final:
                print(f"  Items en la compra: {len(items_final)}")
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
                print(f"  ❌ No hay items en la compra final")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡COMPRA RESTAURADA EXITOSAMENTE!")
        print("Ahora puedes hacer el ejercicio completo:")
        print("  1. Ir al módulo de Compras")
        print("  2. Ver la compra en borrador")
        print("  3. Verificar que aparezcan los items en la lista")
        print("  4. Probar recibir los items para actualizar stock y precios")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_estado_compra()



