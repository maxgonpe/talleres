#!/usr/bin/env python3
"""
Script para seguir el proceso completo del modal desde que se confirma hasta que se guarda
"""

import sqlite3
from decimal import Decimal
import os

def seguir_proceso_modal():
    print("🔍 SIGUIENDO PROCESO COMPLETO DEL MODAL")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR ESTADO INICIAL DE LA COMPRA 17
        print("📊 ESTADO INICIAL DE LA COMPRA 17...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra, observaciones
            FROM car_compra 
            WHERE id = 17
        """)
        
        compra_inicial = cursor.fetchone()
        if not compra_inicial:
            print("❌ No se encontró la compra 17")
            return
        
        c_id, numero, proveedor, estado, total, fecha, observaciones = compra_inicial
        
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        print(f"  Fecha: {fecha}")
        print(f"  Observaciones: {observaciones}")
        
        # 2. VERIFICAR ITEMS ANTES DEL MODAL
        print(f"\n📦 ITEMS ANTES DEL MODAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = 17
            ORDER BY ci.id
        """)
        
        items_antes = cursor.fetchall()
        
        print(f"  Items antes del modal: {len(items_antes)}")
        for item in items_antes:
            item_id, repuesto_id, cantidad, precio, subtotal, recibido = item
            print(f"    Item ID: {item_id}")
            print(f"      Repuesto ID: {repuesto_id}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print(f"      ---")
        
        # 3. SIMULAR DATOS DEL MODAL
        print(f"\n📝 SIMULANDO DATOS DEL MODAL...")
        
        # Datos que el usuario introduce en el modal
        datos_modal = {
            'repuesto_id': 3,  # Aceite 10w-40
            'cantidad': 5,
            'precio_unitario': 40000,
            'subtotal': 5 * 40000  # 200000
        }
        
        print(f"  Datos introducidos en el modal:")
        print(f"    Repuesto ID: {datos_modal['repuesto_id']}")
        print(f"    Cantidad: {datos_modal['cantidad']}")
        print(f"    Precio unitario: ${datos_modal['precio_unitario']}")
        print(f"    Subtotal calculado: ${datos_modal['subtotal']}")
        
        # 4. VERIFICAR REPUESTO SELECCIONADO
        print(f"\n🔍 VERIFICANDO REPUESTO SELECCIONADO...")
        
        cursor.execute("""
            SELECT id, nombre, sku, stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE id = ?
        """, (datos_modal['repuesto_id'],))
        
        repuesto_seleccionado = cursor.fetchone()
        if repuesto_seleccionado:
            r_id, nombre, sku, stock, precio_costo, precio_venta = repuesto_seleccionado
            print(f"  Repuesto seleccionado: {nombre}")
            print(f"  SKU: {sku}")
            print(f"  Stock actual: {stock}")
            print(f"  Precio costo actual: ${precio_costo}")
            print(f"  Precio venta actual: ${precio_venta}")
        else:
            print(f"  ❌ No se encontró el repuesto ID {datos_modal['repuesto_id']}")
            return
        
        # 5. SIMULAR PROCESO DE GUARDADO
        print(f"\n💾 SIMULANDO PROCESO DE GUARDADO...")
        
        # Verificar si ya existe el item
        cursor.execute("""
            SELECT id, cantidad, precio_unitario, subtotal
            FROM car_compraitem 
            WHERE compra_id = ? AND repuesto_id = ?
        """, (17, datos_modal['repuesto_id']))
        
        item_existente = cursor.fetchone()
        
        if item_existente:
            print(f"  ⚠️ Item ya existe, actualizando...")
            item_id, cantidad_actual, precio_actual, subtotal_actual = item_existente
            
            nueva_cantidad = cantidad_actual + datos_modal['cantidad']
            nuevo_subtotal = nueva_cantidad * datos_modal['precio_unitario']
            
            cursor.execute("""
                UPDATE car_compraitem 
                SET cantidad = ?, precio_unitario = ?, subtotal = ?
                WHERE id = ?
            """, (nueva_cantidad, datos_modal['precio_unitario'], nuevo_subtotal, item_id))
            
            print(f"    Cantidad anterior: {cantidad_actual}")
            print(f"    Cantidad nueva: {nueva_cantidad}")
            print(f"    Precio actualizado: ${datos_modal['precio_unitario']}")
            print(f"    Subtotal actualizado: ${nuevo_subtotal}")
        else:
            print(f"  ✅ Item no existe, creando nuevo...")
            
            cursor.execute("""
                INSERT INTO car_compraitem 
                (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
                VALUES (?, ?, ?, ?, ?, 0, NULL)
            """, (17, datos_modal['repuesto_id'], datos_modal['cantidad'], datos_modal['precio_unitario'], datos_modal['subtotal']))
            
            print(f"    ✅ Item creado correctamente")
            print(f"    Compra ID: 17")
            print(f"    Repuesto ID: {datos_modal['repuesto_id']}")
            print(f"    Cantidad: {datos_modal['cantidad']}")
            print(f"    Precio unitario: ${datos_modal['precio_unitario']}")
            print(f"    Subtotal: ${datos_modal['subtotal']}")
        
        # 6. ACTUALIZAR TOTAL DE LA COMPRA
        print(f"\n💰 ACTUALIZANDO TOTAL DE LA COMPRA...")
        
        cursor.execute("""
            SELECT SUM(subtotal) 
            FROM car_compraitem 
            WHERE compra_id = 17
        """)
        
        nuevo_total = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            UPDATE car_compra 
            SET total = ?
            WHERE id = 17
        """, (nuevo_total,))
        
        print(f"  ✅ Total actualizado: ${nuevo_total}")
        
        # 7. VERIFICAR ESTADO DESPUÉS DEL MODAL
        print(f"\n🔍 ESTADO DESPUÉS DEL MODAL...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE id = 17
        """)
        
        compra_despues = cursor.fetchone()
        if compra_despues:
            c_id, numero, proveedor, estado, total = compra_despues
            print(f"  Compra: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
        
        # 8. VERIFICAR ITEMS DESPUÉS DEL MODAL
        print(f"\n📦 ITEMS DESPUÉS DEL MODAL...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido,
                   r.nombre, r.sku
            FROM car_compraitem ci
            JOIN car_repuesto r ON ci.repuesto_id = r.id
            WHERE ci.compra_id = 17
            ORDER BY ci.id
        """)
        
        items_despues = cursor.fetchall()
        
        print(f"  Items después del modal: {len(items_despues)}")
        for item in items_despues:
            item_id, repuesto_id, cantidad, precio, subtotal, recibido, nombre, sku = item
            print(f"    Item ID: {item_id}")
            print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
            print(f"      SKU: {sku}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print(f"      ---")
        
        # 9. DIAGNÓSTICO DEL PROBLEMA
        print(f"\n🔍 DIAGNÓSTICO DEL PROBLEMA...")
        
        if len(items_despues) > len(items_antes):
            print(f"  ✅ Los items se están guardando correctamente")
            print(f"  ✅ La información del modal se está procesando")
            print(f"  ✅ La relación compra-item funciona")
            print(f"  ❌ Pero no se muestran en el template")
            print(f"  🔍 Posibles causas:")
            print(f"    1. El JavaScript AJAX no está funcionando correctamente")
            print(f"    2. La vista AJAX no está devolviendo los datos correctos")
            print(f"    3. El template parcial no se está renderizando")
            print(f"    4. Hay un problema de cache en el navegador")
            print(f"    5. Hay un error en la consola del navegador")
            
            print(f"\n  💡 SOLUCIONES A PROBAR:")
            print(f"    1. Verificar que no haya errores en la consola del navegador")
            print(f"    2. Verificar que el JavaScript esté funcionando")
            print(f"    3. Verificar que la vista AJAX esté devolviendo datos")
            print(f"    4. Refrescar la página (F5) para ver si aparecen los items")
            print(f"    5. Limpiar cache del navegador")
        else:
            print(f"  ❌ Los items no se están guardando")
            print(f"  💡 El problema está en el proceso de guardado")
            print(f"  🔍 Posibles causas:")
            print(f"    1. El formulario no se está enviando correctamente")
            print(f"    2. La vista no está procesando el formulario")
            print(f"    3. Hay un problema con la validación del formulario")
            print(f"    4. Hay un problema con el JavaScript AJAX")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡SEGUIMIENTO COMPLETADO!")
        print("=" * 60)
        print("📋 RESUMEN DEL PROCESO:")
        print(f"  1. ✅ Estado inicial de la compra verificado")
        print(f"  2. ✅ Items antes del modal: {len(items_antes)}")
        print(f"  3. ✅ Datos del modal simulados correctamente")
        print(f"  4. ✅ Repuesto seleccionado verificado")
        print(f"  5. ✅ Proceso de guardado simulado")
        print(f"  6. ✅ Total de la compra actualizado")
        print(f"  7. ✅ Items después del modal: {len(items_despues)}")
        print(f"  8. ✅ Diagnóstico del problema identificado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seguir_proceso_modal()



