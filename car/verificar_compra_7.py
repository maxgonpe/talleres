#!/usr/bin/env python3
"""
Script para verificar la compra 7 y sus items
"""

import sqlite3
from decimal import Decimal
import os

def verificar_compra_7():
    print("🔍 VERIFICANDO COMPRA 7 Y SUS ITEMS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 7
        print("📊 VERIFICANDO COMPRA 7...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            WHERE id = 7
        """)
        
        compra_7 = cursor.fetchone()
        if not compra_7:
            print("❌ No se encontró la compra ID 7")
            
            # Verificar todas las compras
            cursor.execute("""
                SELECT id, numero_compra, proveedor, estado, total
                FROM car_compra 
                ORDER BY id DESC
            """)
            
            compras = cursor.fetchall()
            print(f"\n  Compras disponibles:")
            for compra in compras:
                c_id, numero, proveedor, estado, total = compra
                print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}, Total: ${total}")
            
            return
        
        c_id, numero, proveedor, estado, total, fecha = compra_7
        
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha: {fecha}")
        
        # 2. VERIFICAR ITEMS DE LA COMPRA 7
        print("\n📦 VERIFICANDO ITEMS DE LA COMPRA 7...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido, ci.fecha_recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 7
            ORDER BY ci.id
        """)
        
        items_7 = cursor.fetchall()
        
        if items_7:
            print(f"  Items encontrados: {len(items_7)}")
            for item in items_7:
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
                    print(f"      Stock actual: {stock}")
                    print(f"      Precio costo actual: ${precio_costo}")
                    print(f"      Precio venta actual: ${precio_venta}")
                    print("      ---")
                else:
                    print(f"    Item ID: {item_id} - Repuesto no encontrado (ID: {repuesto_id})")
        else:
            print(f"  ❌ No hay items en la compra 7")
            
            # Verificar si hay items en otras compras
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
        
        # 3. VERIFICAR ACCIONES DISPONIBLES
        print(f"\n🎯 Acciones disponibles para {numero}:")
        
        if estado == 'borrador':
            print(f"    ✅ Confirmar Compra")
            print(f"    ✅ Cancelar Compra")
            print(f"    📝 Nota: Para confirmar, la compra debe tener items")
        elif estado == 'confirmada':
            if len(items_7) > 0:
                print(f"    ✅ Recibir Todos los Items")
            print(f"    ✅ Cancelar Compra")
        elif estado == 'recibida':
            print(f"    ❌ No hay acciones disponibles (ya recibida)")
        elif estado == 'cancelada':
            print(f"    ❌ No hay acciones disponibles (cancelada)")
        
        # Verificar si la compra tiene items para poder confirmar
        if estado == 'borrador' and len(items_7) > 0:
            print(f"\n  ✅ La compra puede ser confirmada (tiene {len(items_7)} items)")
        elif estado == 'borrador' and len(items_7) == 0:
            print(f"\n  ⚠️ La compra no puede ser confirmada (no tiene items)")
        
        # 4. CREAR ITEM SI NO EXISTE
        if len(items_7) == 0:
            print(f"\n📦 CREANDO ITEM PARA LA COMPRA 7...")
            
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
                precio_unitario = 40000
                subtotal = cantidad * precio_unitario
                
                cursor.execute("""
                    INSERT INTO car_compraitem 
                    (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                    VALUES (?, ?, ?, ?, ?, 0, NULL)
                """, (7, r_id, cantidad, precio_unitario, subtotal))
                
                print(f"  ✅ Item agregado:")
                print(f"    Cantidad: {cantidad}")
                print(f"    Precio unitario: ${precio_unitario}")
                print(f"    Subtotal: ${subtotal}")
                
                # Actualizar total de la compra
                cursor.execute("""
                    UPDATE car_compra 
                    SET total = ?
                    WHERE id = 7
                """, (subtotal,))
                
                print(f"  ✅ Total de la compra actualizado: ${subtotal}")
            else:
                print(f"  ❌ No se encontró el repuesto Aceite 10w-40")
        
        # 5. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 7
            ORDER BY ci.id
        """)
        
        items_final = cursor.fetchall()
        
        if items_final:
            print(f"  Items en la compra 7: {len(items_final)}")
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
            print(f"  ❌ No hay items en la compra 7")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡COMPRA 7 VERIFICADA Y CORREGIDA!")
        print("Ahora puedes:")
        print("  1. Ir al módulo de Compras")
        print("  2. Ver la compra 7")
        print("  3. Verificar que aparezcan los items en la lista")
        print("  4. Probar las acciones de confirmar o cancelar")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_compra_7()



