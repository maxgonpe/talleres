#!/usr/bin/env python3
"""
Script para crear una nueva compra en estado borrador
"""

import sqlite3
from decimal import Decimal
import os
from datetime import datetime

def crear_compra_borrador():
    print("📦 CREANDO NUEVA COMPRA EN BORRADOR")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. CREAR NUEVA COMPRA EN BORRADOR
        print("📦 CREANDO NUEVA COMPRA EN BORRADOR...")
        
        # Obtener el próximo número de compra
        cursor.execute("""
            SELECT MAX(id) FROM car_compra
        """)
        
        max_id = cursor.fetchone()[0] or 0
        nuevo_id = max_id + 1
        nuevo_numero = f"COMP-{nuevo_id:04d}"
        
        cursor.execute("""
            INSERT INTO car_compra 
            (numero_compra, proveedor, fecha_compra, estado, total, observaciones, creado_por_id, creado_en, actualizado_en)
            VALUES (?, ?, date('now'), 'borrador', 0, 'Compra de prueba para verificar acciones', 1, datetime('now'), datetime('now'))
        """, (nuevo_numero, 'Proveedor Test'))
        
        nueva_compra_id = cursor.lastrowid
        print(f"  ✅ Nueva compra creada: {nuevo_numero} (ID: {nueva_compra_id})")
        
        # 2. AGREGAR ITEM A LA COMPRA
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
        cantidad = 3
        precio_unitario = 30000
        subtotal = cantidad * precio_unitario
        
        cursor.execute("""
            INSERT INTO car_compraitem 
            (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
            VALUES (?, ?, ?, ?, ?, 0, NULL)
        """, (nueva_compra_id, r_id, cantidad, precio_unitario, subtotal))
        
        print(f"  ✅ Item agregado:")
        print(f"    Cantidad: {cantidad}")
        print(f"    Precio unitario: ${precio_unitario}")
        print(f"    Subtotal: ${subtotal}")
        
        # Actualizar total de la compra
        cursor.execute("""
            UPDATE car_compra 
            SET total = ?
            WHERE id = ?
        """, (subtotal, nueva_compra_id))
        
        print(f"  ✅ Total de la compra actualizado: ${subtotal}")
        
        # 3. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            WHERE id = ?
        """, (nueva_compra_id,))
        
        compra_final = cursor.fetchone()
        if compra_final:
            c_id, numero, proveedor, estado, total, fecha = compra_final
            
            print(f"  Compra final: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
            print(f"  Fecha: {fecha}")
            
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
            
            # 4. VERIFICAR ACCIONES DISPONIBLES
            print(f"\n🎯 Acciones disponibles para {numero}:")
            
            if estado == 'borrador':
                print(f"    ✅ Confirmar Compra")
                print(f"    ✅ Cancelar Compra")
                print(f"    📝 Nota: Para confirmar, la compra debe tener items")
            elif estado == 'confirmada':
                if len(items_final) > 0:
                    print(f"    ✅ Recibir Todos los Items")
                print(f"    ✅ Cancelar Compra")
            elif estado == 'recibida':
                print(f"    ❌ No hay acciones disponibles (ya recibida)")
            elif estado == 'cancelada':
                print(f"    ❌ No hay acciones disponibles (cancelada)")
            
            # Verificar si la compra tiene items para poder confirmar
            if estado == 'borrador' and len(items_final) > 0:
                print(f"\n  ✅ La compra puede ser confirmada (tiene {len(items_final)} items)")
            elif estado == 'borrador' and len(items_final) == 0:
                print(f"\n  ⚠️ La compra no puede ser confirmada (no tiene items)")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡NUEVA COMPRA EN BORRADOR CREADA EXITOSAMENTE!")
        print("Ahora puedes:")
        print("  1. Ir al módulo de Compras")
        print("  2. Ver la compra en borrador")
        print("  3. Verificar que aparezcan las acciones: Confirmar y Cancelar")
        print("  4. Probar el flujo completo de compras")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    crear_compra_borrador()



