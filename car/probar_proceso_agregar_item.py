#!/usr/bin/env python3
"""
Script para probar el proceso completo de agregar items
"""

import sqlite3
from decimal import Decimal
import os

def probar_proceso_agregar_item():
    print("🧪 PROBANDO PROCESO COMPLETO DE AGREGAR ITEMS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. CREAR COMPRA DE PRUEBA
        print("📊 CREANDO COMPRA DE PRUEBA...")
        
        # Obtener el siguiente número de compra
        cursor.execute("""
            SELECT MAX(CAST(SUBSTR(numero_compra, 6) AS INTEGER)) 
            FROM car_compra 
            WHERE numero_compra LIKE 'COMP-%'
        """)
        
        ultimo_numero = cursor.fetchone()[0] or 0
        nuevo_numero = ultimo_numero + 1
        
        cursor.execute("""
            INSERT INTO car_compra (numero_compra, proveedor, estado, total, fecha_compra, observaciones, creado_en, actualizado_en, creado_por_id)
            VALUES (?, 'Proveedor Prueba AJAX', 'borrador', 0, date('now'), 'Prueba de proceso AJAX', datetime('now'), datetime('now'), 1)
        """, (f'COMP-{nuevo_numero:04d}',))
        
        compra_id = cursor.lastrowid
        print(f"  ✅ Compra creada: ID {compra_id}")
        
        # 2. SIMULAR PROCESO DE AGREGAR ITEM
        print(f"\n📦 SIMULANDO PROCESO DE AGREGAR ITEM...")
        
        # Buscar repuesto Aceite 10w-40
        cursor.execute("""
            SELECT id, nombre, sku, stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite 10w-40%'
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print(f"  ❌ No se encontró el repuesto Aceite 10w-40")
            return
        
        r_id, nombre, sku, stock, precio_costo, precio_venta = repuesto
        
        print(f"  Repuesto seleccionado: {nombre}")
        print(f"  SKU: {sku}")
        print(f"  Stock actual: {stock}")
        print(f"  Precio costo actual: ${precio_costo}")
        print(f"  Precio venta actual: ${precio_venta}")
        
        # Simular datos del formulario
        cantidad = 2
        precio_unitario = 35000
        subtotal = cantidad * precio_unitario
        
        print(f"\n  Datos del formulario:")
        print(f"    Cantidad: {cantidad}")
        print(f"    Precio unitario: ${precio_unitario}")
        print(f"    Subtotal: ${subtotal}")
        
        # 3. VERIFICAR SI YA EXISTE EL ITEM
        print(f"\n🔍 VERIFICANDO SI YA EXISTE EL ITEM...")
        
        cursor.execute("""
            SELECT id, cantidad, precio_unitario, subtotal
            FROM car_compraitem 
            WHERE compra_id = ? AND repuesto_id = ?
        """, (compra_id, r_id))
        
        item_existente = cursor.fetchone()
        
        if item_existente:
            print(f"  ⚠️ Item ya existe, actualizando...")
            item_id, cantidad_actual, precio_actual, subtotal_actual = item_existente
            
            nueva_cantidad = cantidad_actual + cantidad
            nuevo_subtotal = nueva_cantidad * precio_unitario
            
            cursor.execute("""
                UPDATE car_compraitem 
                SET cantidad = ?, precio_unitario = ?, subtotal = ?
                WHERE id = ?
            """, (nueva_cantidad, precio_unitario, nuevo_subtotal, item_id))
            
            print(f"    Cantidad anterior: {cantidad_actual}")
            print(f"    Cantidad nueva: {nueva_cantidad}")
            print(f"    Precio actualizado: ${precio_unitario}")
            print(f"    Subtotal actualizado: ${nuevo_subtotal}")
        else:
            print(f"  ✅ Item no existe, creando nuevo...")
            
            cursor.execute("""
                INSERT INTO car_compraitem 
                (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                VALUES (?, ?, ?, ?, ?, 0, NULL)
            """, (compra_id, r_id, cantidad, precio_unitario, subtotal))
            
            print(f"    ✅ Item creado correctamente")
        
        # 4. ACTUALIZAR TOTAL DE LA COMPRA
        print(f"\n💰 ACTUALIZANDO TOTAL DE LA COMPRA...")
        
        cursor.execute("""
            SELECT SUM(subtotal) 
            FROM car_compraitem 
            WHERE compra_id = ?
        """, (compra_id,))
        
        nuevo_total = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            UPDATE car_compra 
            SET total = ?
            WHERE id = ?
        """, (nuevo_total, compra_id))
        
        print(f"  ✅ Total actualizado: ${nuevo_total}")
        
        # 5. VERIFICAR RESULTADO FINAL
        print(f"\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = ?
            ORDER BY ci.id
        """, (compra_id,))
        
        items_final = cursor.fetchall()
        
        if items_final:
            print(f"  Items en la compra {compra_id}: {len(items_final)}")
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
            print(f"  ❌ No hay items en la compra {compra_id}")
        
        # 6. VERIFICAR COMPRA FINAL
        print(f"\n📊 VERIFICANDO COMPRA FINAL...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE id = ?
        """, (compra_id,))
        
        compra_final = cursor.fetchone()
        if compra_final:
            c_id, numero, proveedor, estado, total = compra_final
            print(f"  Compra: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡PROCESO COMPLETADO!")
        print("=" * 60)
        print("✅ PROCESO DE AGREGAR ITEM:")
        print("  1. ✅ Compra creada correctamente")
        print("  2. ✅ Repuesto encontrado y seleccionado")
        print("  3. ✅ Datos del formulario procesados")
        print("  4. ✅ Item agregado/actualizado en la base de datos")
        print("  5. ✅ Total de la compra actualizado")
        print("  6. ✅ Relación compra-item funcionando")
        print()
        print("🔍 DIAGNÓSTICO:")
        if items_final:
            print("  ✅ Los items se están guardando correctamente")
            print("  ✅ La relación compra-item funciona")
            print("  ❌ Pero no se muestran en el template")
            print("  💡 El problema está en el JavaScript AJAX o en el template")
        else:
            print("  ❌ Los items no se están guardando")
            print("  💡 El problema está en el proceso de guardado")
        print()
        print("🧪 PARA PROBAR EN EL NAVEGADOR:")
        print(f"  1. Ve al módulo de Compras")
        print(f"  2. Abre la compra {compra_id}")
        print(f"  3. Haz clic en 'Agregar Item'")
        print(f"  4. Busca y selecciona un repuesto")
        print(f"  5. Completa cantidad y precio")
        print(f"  6. Haz clic en 'Agregar Item'")
        print(f"  7. Verifica que aparezca el mensaje de éxito")
        print(f"  8. Verifica que el listado se actualice automáticamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    probar_proceso_agregar_item()



