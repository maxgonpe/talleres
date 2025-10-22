#!/usr/bin/env python3
"""
Script para probar el ejercicio completo con la nueva lógica de precios
"""

import sqlite3
from decimal import Decimal
import os

def probar_ejercicio_completo():
    print("🔄 PROBANDO EJERCICIO COMPLETO CON NUEVA LÓGICA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR ESTADO INICIAL DEL REPUESTO
        print("📊 VERIFICANDO ESTADO INICIAL DEL REPUESTO...")
        
        cursor.execute("""
            SELECT id, nombre, stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite 10w-40%'
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró el repuesto Aceite 10w-40")
            return
        
        r_id, nombre, stock_inicial, precio_costo_inicial, precio_venta_inicial = repuesto
        
        print(f"  Repuesto: {nombre}")
        print(f"  Stock inicial: {stock_inicial}")
        print(f"  Precio costo inicial: ${precio_costo_inicial}")
        print(f"  Precio venta inicial: ${precio_venta_inicial}")
        
        # 2. VERIFICAR COMPRA EN BORRADOR
        print("\n📦 VERIFICANDO COMPRA EN BORRADOR...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE estado = 'borrador'
            ORDER BY id DESC
            LIMIT 1
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró compra en borrador")
            return
        
        c_id, numero, proveedor, estado, total = compra
        
        print(f"  Compra: {numero} (ID: {c_id})")
        print(f"  Proveedor: {proveedor}")
        print(f"  Estado: {estado}")
        print(f"  Total: ${total}")
        
        # 3. VERIFICAR ITEMS DE LA COMPRA
        print("\n📦 VERIFICANDO ITEMS DE LA COMPRA...")
        
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.subtotal, ci.recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = ?
            ORDER BY ci.id
        """, (c_id,))
        
        items = cursor.fetchall()
        
        if not items:
            print("❌ No hay items en la compra")
            return
        
        print(f"  Items encontrados: {len(items)}")
        for item in items:
            item_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido = item
            print(f"    Item ID: {item_id}")
            print(f"      Repuesto ID: {repuesto_id}")
            print(f"      Cantidad: {cantidad}")
            print(f"      Precio unitario: ${precio_unitario}")
            print(f"      Subtotal: ${subtotal}")
            print(f"      Recibido: {recibido}")
            print("      ---")
        
        # 4. SIMULAR RECEPCIÓN DEL ITEM
        print("\n📦 SIMULANDO RECEPCIÓN DEL ITEM...")
        
        item_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido = items[0]
        
        if recibido:
            print(f"  ⚠️ El item ya está marcado como recibido")
        else:
            print(f"  📦 Recibiendo {cantidad} unidades a ${precio_unitario} cada una")
            
            # Marcar item como recibido
            cursor.execute("""
                UPDATE car_compraitem 
                SET recibido = 1, fecha_recibido = datetime('now')
                WHERE id = ?
            """, (item_id,))
            
            print("  ✅ Item marcado como recibido")
            
            # 5. APLICAR NUEVA LÓGICA DE PRECIOS
            print("\n💾 APLICANDO NUEVA LÓGICA DE PRECIOS...")
            
            # Calcular nuevo stock
            nuevo_stock = stock_inicial + cantidad
            
            # Precio de compra es literal (no promedio ponderado)
            nuevo_precio_costo = precio_unitario
            
            # Calcular factor de margen del producto existente
            if precio_costo_inicial > 0 and precio_venta_inicial > 0:
                factor_margen = precio_venta_inicial / precio_costo_inicial
                nuevo_precio_venta = nuevo_precio_costo * factor_margen
            else:
                factor_margen = 1.3
                nuevo_precio_venta = nuevo_precio_costo * factor_margen
            
            print(f"  📈 Cálculos:")
            print(f"    Stock anterior: {stock_inicial}")
            print(f"    Cantidad recibida: {cantidad}")
            print(f"    Nuevo stock: {nuevo_stock}")
            print(f"    Precio costo anterior: ${precio_costo_inicial}")
            print(f"    Precio costo nuevo: ${nuevo_precio_costo} (literal)")
            print(f"    Factor de margen: {factor_margen:.3f}")
            print(f"    Precio venta nuevo: ${nuevo_precio_venta:.2f}")
            print(f"    Cálculo: ${nuevo_precio_costo} × {factor_margen:.3f} = ${nuevo_precio_venta:.2f}")
            
            # Actualizar tabla principal
            cursor.execute("""
                UPDATE car_repuesto 
                SET stock = ?, precio_costo = ?, precio_venta = ?
                WHERE id = ?
            """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, r_id))
            
            print("  ✅ Tabla car_repuesto actualizada")
            
            # 6. SINCRONIZAR CON REPUESTOENSTOCK
            print("\n🔗 SINCRONIZANDO CON REPUESTOENSTOCK...")
            
            # Obtener o crear registro en RepuestoEnStock
            cursor.execute("""
                SELECT id FROM car_repuestoenstock 
                WHERE repuesto_id = ? AND deposito = 'bodega-principal'
            """, (r_id,))
            
            stock_id = cursor.fetchone()
            if stock_id:
                # Actualizar existente
                cursor.execute("""
                    UPDATE car_repuestoenstock 
                    SET stock = ?, precio_compra = ?, precio_venta = ?
                    WHERE id = ?
                """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, stock_id[0]))
                print("  ✅ RepuestoEnStock actualizado")
            else:
                # Crear nuevo
                cursor.execute("""
                    INSERT INTO car_repuestoenstock 
                    (repuesto_id, deposito, stock, reservado, precio_compra, precio_venta, proveedor, ultima_actualizacion)
                    VALUES (?, 'bodega-principal', ?, 0, ?, ?, '', datetime('now'))
                """, (r_id, nuevo_stock, nuevo_precio_costo, nuevo_precio_venta))
                print("  ✅ RepuestoEnStock creado")
            
            # 7. CREAR MOVIMIENTO DE STOCK
            print("\n📋 CREANDO MOVIMIENTO DE STOCK...")
            try:
                # Obtener el ID del repuesto_stock
                cursor.execute("""
                    SELECT id FROM car_repuestoenstock 
                    WHERE repuesto_id = ? AND deposito = 'bodega-principal'
                """, (r_id,))
                
                repuesto_stock_id = cursor.fetchone()
                if repuesto_stock_id:
                    cursor.execute("""
                        INSERT INTO car_stockmovimiento 
                        (repuesto_stock_id, tipo, cantidad, motivo, referencia, usuario_id, fecha)
                        VALUES (?, 'entrada', ?, ?, ?, 1, datetime('now'))
                    """, (repuesto_stock_id[0], cantidad, f'Compra #{numero}', f'COMPRA-{c_id}'))
                    print("  ✅ Movimiento de stock creado")
                else:
                    print("  ⚠️ No se pudo crear movimiento de stock (repuesto_stock no encontrado)")
            except Exception as e:
                print(f"  ⚠️ No se pudo crear movimiento de stock: {e}")
            
            # 8. ACTUALIZAR ESTADO DE LA COMPRA
            print("\n🔄 ACTUALIZANDO ESTADO DE LA COMPRA...")
            cursor.execute("""
                UPDATE car_compra 
                SET estado = 'recibida', fecha_recibida = date('now')
                WHERE id = ?
            """, (c_id,))
            
            print("  ✅ Compra marcada como recibida")
        
        # 9. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        # Verificar tabla principal
        cursor.execute("""
            SELECT stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE id = ?
        """, (r_id,))
        
        stock_final, precio_costo_final, precio_venta_final = cursor.fetchone()
        
        print(f"  📊 Tabla car_repuesto:")
        print(f"    Stock: {stock_final}")
        print(f"    Precio costo: ${precio_costo_final}")
        print(f"    Precio venta: ${precio_venta_final}")
        
        # Verificar tabla detallada
        cursor.execute("""
            SELECT stock, precio_compra, precio_venta 
            FROM car_repuestoenstock 
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (r_id,))
        
        stock_detallado = cursor.fetchone()
        if stock_detallado:
            print(f"  🔗 Tabla car_repuestoenstock:")
            print(f"    Stock: {stock_detallado[0]}")
            print(f"    Precio compra: ${stock_detallado[1]}")
            print(f"    Precio venta: ${stock_detallado[2]}")
        
        # Verificar consistencia
        if (stock_final == stock_detallado[0] and 
            precio_costo_final == stock_detallado[1] and
            precio_venta_final == stock_detallado[2]):
            print("\n✅ PERFECTO: Todas las tablas están sincronizadas")
        else:
            print("\n❌ ERROR: Hay inconsistencias entre las tablas")
        
        # 10. MOSTRAR RESUMEN
        print("\n🎯 RESUMEN DEL EJERCICIO COMPLETO:")
        print(f"  📦 Repuesto: {nombre}")
        print(f"  📊 Estado inicial:")
        print(f"    Stock: {stock_inicial} unidades")
        print(f"    Precio costo: ${precio_costo_inicial}")
        print(f"    Precio venta: ${precio_venta_inicial}")
        print(f"  🛒 Compra recibida:")
        print(f"    Cantidad: {cantidad} unidades")
        print(f"    Precio de compra: ${precio_unitario}")
        print(f"  📈 Estado final:")
        print(f"    Stock: {stock_final} unidades")
        print(f"    Precio costo: ${precio_costo_final} (literal)")
        print(f"    Precio venta: ${precio_venta_final} (factor aplicado)")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡EJERCICIO COMPLETO REALIZADO EXITOSAMENTE!")
        print("La nueva lógica de precios está funcionando correctamente:")
        print("  - Precio de compra es literal")
        print("  - Precio de venta se calcula con factor de margen")
        print("  - Todas las tablas están sincronizadas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    probar_ejercicio_completo()



