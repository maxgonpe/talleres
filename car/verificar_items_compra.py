#!/usr/bin/env python3
"""
Script para verificar los items de una compra
"""

import sqlite3
from decimal import Decimal
import os

def verificar_items_compra():
    print("📦 VERIFICANDO ITEMS DE COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRAS EXISTENTES
        print("📊 VERIFICANDO COMPRAS EXISTENTES...")
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            ORDER BY id DESC
        """)
        
        compras = cursor.fetchall()
        
        if not compras:
            print("❌ No hay compras en la base de datos")
            return
        
        print(f"  Encontradas {len(compras)} compras:")
        for compra in compras:
            c_id, numero, proveedor, estado, total = compra
            print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}, Total: ${total}")
        
        # 2. VERIFICAR ITEMS DE CADA COMPRA
        print("\n📦 VERIFICANDO ITEMS DE CADA COMPRA...")
        
        for compra in compras:
            c_id, numero, proveedor, estado, total = compra
            
            print(f"\n  🔍 Compra {numero} (ID: {c_id}):")
            
            cursor.execute("""
                SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido, ci.fecha_recibido
                FROM car_compraitem ci
                WHERE ci.compra_id = ?
                ORDER BY ci.id
            """, (c_id,))
            
            items = cursor.fetchall()
            
            if items:
                print(f"    Items encontrados: {len(items)}")
                for item in items:
                    item_id, repuesto_id, cantidad, precio, subtotal, recibido, fecha_recibido = item
                    
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
                        if fecha_recibido:
                            print(f"        Fecha recibido: {fecha_recibido}")
                        print(f"        Stock actual: {stock}")
                        print(f"        Precio venta actual: ${precio_venta}")
                        print("        ---")
                    else:
                        print(f"      Item ID: {item_id} - Repuesto no encontrado (ID: {repuesto_id})")
            else:
                print(f"    ❌ No hay items en esta compra")
        
        # 3. VERIFICAR COMPRA ESPECÍFICA (ID 3)
        print("\n🔍 VERIFICANDO COMPRA ESPECÍFICA (ID 3)...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            WHERE id = 3
        """)
        
        compra_3 = cursor.fetchone()
        if compra_3:
            c_id, numero, proveedor, estado, total, fecha = compra_3
            print(f"  Compra: {numero}")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
            print(f"  Fecha: {fecha}")
            
            # Items de la compra 3
            cursor.execute("""
                SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
                FROM car_compraitem ci
                WHERE ci.compra_id = 3
                ORDER BY ci.id
            """)
            
            items_3 = cursor.fetchall()
            
            if items_3:
                print(f"  Items en compra 3: {len(items_3)}")
                for item in items_3:
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
                        print(f"    Item ID: {item_id}")
                        print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
                        print(f"      SKU: {sku}")
                        print(f"      Cantidad: {cantidad}")
                        print(f"      Precio unitario: ${precio}")
                        print(f"      Subtotal: ${subtotal}")
                        print(f"      Recibido: {recibido}")
                        print(f"      Stock actual: {stock}")
                        print(f"      Precio venta actual: ${precio_venta}")
                        print("      ---")
            else:
                print(f"  ❌ No hay items en la compra 3")
        else:
            print(f"  ❌ No se encontró la compra ID 3")
        
        # 4. VERIFICAR TOTALES
        print("\n💰 VERIFICANDO TOTALES...")
        
        for compra in compras:
            c_id, numero, proveedor, estado, total = compra
            
            # Calcular total de items
            cursor.execute("""
                SELECT SUM(subtotal) as total_calculado
                FROM car_compraitem 
                WHERE compra_id = ?
            """, (c_id,))
            
            total_calculado = cursor.fetchone()[0] or 0
            
            print(f"  Compra {numero}:")
            print(f"    Total en BD: ${total}")
            print(f"    Total calculado: ${total_calculado}")
            if total == total_calculado:
                print(f"    ✅ Totales coinciden")
            else:
                print(f"    ❌ Totales NO coinciden")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_items_compra()



