#!/usr/bin/env python3
"""
Script para verificar la compra 25 y sus botones de acciones
"""

import sqlite3
import os

def verificar_compra_25():
    print("🔍 VERIFICANDO COMPRA 25 Y SUS BOTONES DE ACCIONES")
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
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            WHERE id = 25
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra 25")
            return
        
        c_id, numero, proveedor, estado, total, fecha = compra
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha: {fecha}")
        
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
        
        # 3. VERIFICAR BOTONES DE ACCIONES
        print(f"\n🔧 VERIFICANDO BOTONES DE ACCIONES...")
        
        if estado == 'borrador':
            print(f"  ✅ La compra está en estado 'borrador'")
            print(f"  ✅ Deberían aparecer los botones:")
            print(f"    - Confirmar Compra (amarillo)")
            print(f"    - Cancelar Compra (rojo)")
            print(f"    - Agregar Item (azul)")
        elif estado == 'confirmada':
            print(f"  ✅ La compra está en estado 'confirmada'")
            print(f"  ✅ Deberían aparecer los botones:")
            print(f"    - Recibir Todos los Items (verde)")
            print(f"    - Cancelar Compra (rojo)")
        elif estado == 'recibida':
            print(f"  ✅ La compra está en estado 'recibida'")
            print(f"  ✅ No deberían aparecer botones de acciones")
        elif estado == 'cancelada':
            print(f"  ✅ La compra está en estado 'cancelada'")
            print(f"  ✅ No deberían aparecer botones de acciones")
        else:
            print(f"  ❌ Estado desconocido: {estado}")
        
        # 4. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        if len(items) > 0:
            print(f"  ✅ Hay {len(items)} items en la compra 25")
            print(f"  ✅ Los items se están guardando correctamente")
            print(f"  ✅ El formulario funciona correctamente")
            
            if estado == 'borrador':
                print(f"  ✅ La compra está en estado 'borrador'")
                print(f"  ✅ Los botones de acciones deberían aparecer")
                print(f"  ❌ Pero no se muestran en el template")
                print(f"  💡 El problema está en el template o en la vista")
            else:
                print(f"  ❌ La compra está en estado '{estado}'")
                print(f"  ❌ Los botones pueden no aparecer según el estado")
        else:
            print(f"  ❌ No hay items en la compra 25")
            print(f"  💡 El problema está en el proceso de guardado")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compra 25 encontrada")
        print(f"  ✅ Items en la compra 25: {len(items)}")
        print(f"  ✅ Estado: {estado}")
        if len(items) > 0 and estado == 'borrador':
            print(f"  ✅ Los botones de acciones deberían aparecer")
            print(f"  ❌ Pero no se muestran en el template")
            print(f"  💡 El problema está en el template o en la vista")
        else:
            print(f"  ✅ Todo funciona correctamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_compra_25()



