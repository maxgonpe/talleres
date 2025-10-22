#!/usr/bin/env python3
"""
Script para simular la vista de compra
"""

import sqlite3
from decimal import Decimal
import os

def simular_vista_compra():
    print("🔍 SIMULANDO VISTA DE COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. SIMULAR LA VISTA COMPRA_DETAIL
        print("📊 SIMULANDO VISTA COMPRA_DETAIL...")
        
        # Obtener compra
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra, observaciones
            FROM car_compra 
            WHERE id = 13
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra 13")
            return
        
        c_id, numero, proveedor, estado, total, fecha, observaciones = compra
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        
        # 2. SIMULAR LA CONSULTA DE ITEMS (como en la vista)
        print(f"\n📦 SIMULANDO CONSULTA DE ITEMS...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido, ci.fecha_recibido,
                   r.nombre, r.sku, r.stock, r.precio_costo, r.precio_venta
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 13
            ORDER BY r.nombre
        """)
        
        items = cursor.fetchall()
        
        print(f"  Items encontrados: {len(items)}")
        
        if items:
            print(f"  ✅ Los items están en la base de datos")
            print(f"  ✅ La consulta los encuentra correctamente")
            print(f"  ✅ El problema está en el template o en la vista Django")
            
            for item in items:
                item_id, repuesto_id, cantidad, precio, subtotal, recibido, fecha_recibido, nombre, sku, stock, precio_costo, precio_venta = item
                print(f"    Item ID: {item_id}")
                print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
                print(f"      SKU: {sku}")
                print(f"      Cantidad: {cantidad}")
                print(f"      Precio unitario: ${precio}")
                print(f"      Subtotal: ${subtotal}")
                print(f"      Recibido: {recibido}")
                print(f"      ---")
                print(f"      Stock actual: {stock}")
                print(f"      Precio costo actual: ${precio_costo}")
                print(f"      Precio venta actual: ${precio_venta}")
                print(f"      ---")
        else:
            print(f"  ❌ No hay items en la compra 13")
        
        # 3. VERIFICAR SI HAY PROBLEMA CON LA RELACIÓN
        print(f"\n🔗 VERIFICANDO RELACIÓN...")
        
        # Verificar que la relación funcione
        cursor.execute("""
            SELECT COUNT(*) 
            FROM car_compraitem 
            WHERE compra_id = 13
        """)
        
        count_items = cursor.fetchone()[0]
        print(f"  Items en car_compraitem: {count_items}")
        
        # Verificar que la compra existe
        cursor.execute("""
            SELECT COUNT(*) 
            FROM car_compra 
            WHERE id = 13
        """)
        
        count_compra = cursor.fetchone()[0]
        print(f"  Compras con ID 13: {count_compra}")
        
        # 4. DIAGNÓSTICO FINAL
        print(f"\n🔍 DIAGNÓSTICO FINAL...")
        
        if items:
            print(f"  ✅ Los items están en la base de datos")
            print(f"  ✅ La consulta SQL los encuentra")
            print(f"  ❌ Pero no se muestran en el template")
            print(f"  🔍 Posibles causas:")
            print(f"    1. La vista Django no está pasando los items al template")
            print(f"    2. El template no está renderizando los items correctamente")
            print(f"    3. Hay un problema con la relación en el modelo Django")
            print(f"    4. Hay un problema de cache en el navegador")
            
            print(f"\n  💡 SOLUCIONES:")
            print(f"    1. Verificar que la vista esté pasando 'items' al contexto")
            print(f"    2. Verificar que el template esté usando 'for item in items'")
            print(f"    3. Refrescar la página (F5) en el navegador")
            print(f"    4. Limpiar cache del navegador")
            print(f"    5. Verificar que no haya errores en la consola del navegador")
        else:
            print(f"  ❌ No hay items en la base de datos")
            print(f"  💡 El problema es que los items no se están guardando")
        
        # 5. CREAR SCRIPT DE PRUEBA PARA EL NAVEGADOR
        print(f"\n🧪 CREANDO SCRIPT DE PRUEBA...")
        
        script_prueba = """
// Script para probar en la consola del navegador
console.log('🔍 Verificando items en la compra 13...');

// Verificar si hay items en el DOM
const itemsTable = document.querySelector('.table-responsive table tbody');
if (itemsTable) {
    const rows = itemsTable.querySelectorAll('tr');
    console.log('📊 Filas en la tabla:', rows.length);
    
    if (rows.length > 0) {
        console.log('✅ Items encontrados en el DOM');
        rows.forEach((row, index) => {
            console.log(`  Fila ${index + 1}:`, row.textContent);
        });
    } else {
        console.log('❌ No hay filas en la tabla');
    }
} else {
    console.log('❌ No se encontró la tabla de items');
}

// Verificar si hay mensaje de "No hay items"
const noItemsMessage = document.querySelector('.text-center.py-4');
if (noItemsMessage) {
    console.log('❌ Mensaje "No hay items" encontrado:', noItemsMessage.textContent);
} else {
    console.log('✅ No hay mensaje "No hay items"');
}

// Verificar debug info
const debugInfo = document.querySelector('.alert-info');
if (debugInfo) {
    console.log('🔍 Debug info:', debugInfo.textContent);
} else {
    console.log('❌ No se encontró debug info');
}
"""
        
        with open('debug_compra.js', 'w') as f:
            f.write(script_prueba)
        
        print(f"  ✅ Script de debug creado: debug_compra.js")
        print(f"  💡 Copia y pega este script en la consola del navegador para debuggear")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡SIMULACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print("  ✅ Los items están en la base de datos")
        print("  ✅ La consulta SQL los encuentra")
        print("  ❌ Pero no se muestran en el template")
        print("  🔍 El problema está en el template o en la vista Django")
        print("  💡 Prueba refrescar la página (F5) en el navegador")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    simular_vista_compra()
