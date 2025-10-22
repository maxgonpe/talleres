#!/usr/bin/env python3
"""
Script para verificar el estado de la compra 25 después de agregar items
"""

import sqlite3
import os

def verificar_estado_compra_25():
    print("🔍 VERIFICANDO ESTADO DE LA COMPRA 25 DESPUÉS DE AGREGAR ITEMS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRA 25
        print("📊 VERIFICANDO COMPRA 25...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra, fecha_recibida
            FROM car_compra 
            WHERE id = 25
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra 25")
            return
        
        c_id, numero, proveedor, estado, total, fecha_compra, fecha_recibida = compra
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha compra: {fecha_compra}")
        print(f"  Fecha recibida: {fecha_recibida}")
        
        # 2. VERIFICAR ITEMS DE LA COMPRA 25
        print(f"\n📦 VERIFICANDO ITEMS DE LA COMPRA 25...")
        
        cursor.execute("""
            SELECT ci.id, ci.compra_id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            LEFT JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 25
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
        
        # 3. VERIFICAR SI HAY PROCESO AUTOMÁTICO
        print(f"\n🔍 VERIFICANDO SI HAY PROCESO AUTOMÁTICO...")
        
        if estado == 'recibida' and fecha_recibida:
            print(f"  ❌ La compra está en estado 'recibida'")
            print(f"  ❌ Fecha recibida: {fecha_recibida}")
            print(f"  💡 El sistema cambió automáticamente el estado")
            print(f"  💡 Esto no debería pasar al agregar items")
        elif estado == 'borrador':
            print(f"  ✅ La compra está en estado 'borrador'")
            print(f"  ✅ Los botones de acciones deberían aparecer")
        else:
            print(f"  ❌ Estado desconocido: {estado}")
        
        # 4. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        if estado == 'recibida':
            print(f"  ❌ PROBLEMA IDENTIFICADO:")
            print(f"    - La compra cambió automáticamente a estado 'recibida'")
            print(f"    - Esto no debería pasar al agregar items")
            print(f"    - Los botones desaparecen porque el estado cambió")
            print(f"    - El flujo lógico está roto")
            
            print(f"\n  💡 SOLUCIONES:")
            print(f"    1. Verificar si hay algún proceso automático")
            print(f"    2. Verificar si hay algún trigger en la base de datos")
            print(f"    3. Verificar si hay algún middleware que cambie el estado")
            print(f"    4. Verificar si hay algún JavaScript que cambie el estado")
        else:
            print(f"  ✅ El estado es correcto: {estado}")
            print(f"  ✅ Los botones deberían aparecer")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compra 25 encontrada")
        print(f"  ✅ Items en la compra 25: {len(items)}")
        print(f"  ✅ Estado: {estado}")
        if estado == 'recibida':
            print(f"  ❌ PROBLEMA: El estado cambió automáticamente")
            print(f"  💡 Necesitamos investigar por qué cambió el estado")
        else:
            print(f"  ✅ El estado es correcto")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_estado_compra_25()



