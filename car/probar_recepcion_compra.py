#!/usr/bin/env python3
"""
Script para probar la recepción de compras
Simula recibir el item de Aceite 10w-40 de la compra
"""

import sqlite3
from decimal import Decimal
import os
from datetime import datetime

def probar_recepcion_compra():
    print("📦 PROBANDO RECEPCIÓN DE COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. OBTENER COMPRA Y ITEM
        print("📊 OBTENIENDO COMPRA Y ITEM...")
        cursor.execute("""
            SELECT c.id, c.numero_compra, c.proveedor, c.estado
            FROM car_compra c
            WHERE c.id = 3
        """)
        
        compra = cursor.fetchone()
        if not compra:
            print("❌ No se encontró la compra ID 3")
            return
        
        compra_id, numero_compra, proveedor, estado = compra
        print(f"  Compra: {numero_compra} - {proveedor} - Estado: {estado}")
        
        # Obtener items de la compra
        cursor.execute("""
            SELECT ci.id, ci.repuesto_id, ci.cantidad, ci.precio_unitario, ci.recibido
            FROM car_compraitem ci
            WHERE ci.compra_id = ?
        """, (compra_id,))
        
        items = cursor.fetchall()
        if not items:
            print("❌ No se encontraron items en la compra")
            return
        
        print(f"  Items encontrados: {len(items)}")
        for item in items:
            item_id, repuesto_id, cantidad, precio, recibido = item
            print(f"    Item ID: {item_id}, Repuesto: {repuesto_id}, Cantidad: {cantidad}, Precio: ${precio}, Recibido: {recibido}")
        
        # 2. OBTENER ESTADO ACTUAL DEL REPUESTO
        print("\n📊 ESTADO ACTUAL DEL REPUESTO...")
        cursor.execute("""
            SELECT id, nombre, stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE id = ?
        """, (items[0][1],))  # Usar el primer item
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró el repuesto")
            return
        
        repuesto_id, nombre, stock_actual, precio_costo_actual, precio_venta_actual = repuesto
        
        print(f"  Repuesto: {nombre}")
        print(f"  Stock actual: {stock_actual}")
        print(f"  Precio costo: ${precio_costo_actual}")
        print(f"  Precio venta: ${precio_venta_actual}")
        
        # 3. SIMULAR RECEPCIÓN DEL ITEM
        print("\n📦 SIMULANDO RECEPCIÓN DEL ITEM...")
        
        item_id, repuesto_id, cantidad, precio_unitario, recibido = items[0]
        
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
            
            # 4. ACTUALIZAR STOCK Y PRECIOS
            print("\n💾 ACTUALIZANDO STOCK Y PRECIOS...")
            
            # Calcular nuevo stock y precios usando promedio ponderado
            stock_anterior = stock_actual
            precio_costo_anterior = precio_costo_actual
            precio_venta_anterior = precio_venta_actual
            
            # Cálculo del nuevo precio costo (promedio ponderado)
            valor_anterior = stock_anterior * precio_costo_anterior
            valor_nuevo = cantidad * precio_unitario
            nuevo_stock = stock_anterior + cantidad
            nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
            
            # Calcular factor de margen
            if precio_venta_anterior > 0 and precio_costo_anterior > 0:
                factor_margen = precio_venta_anterior / precio_costo_anterior
                nuevo_precio_venta = nuevo_precio_costo * factor_margen
            else:
                nuevo_precio_venta = nuevo_precio_costo * 1.3  # Margen del 30%
            
            print(f"  📈 Cálculos:")
            print(f"    Stock anterior: {stock_anterior}")
            print(f"    Compra: {cantidad} unidades a ${precio_unitario}")
            print(f"    Nuevo stock: {nuevo_stock}")
            print(f"    Valor anterior: {stock_anterior} × ${precio_costo_anterior} = ${valor_anterior}")
            print(f"    Valor nuevo: {cantidad} × ${precio_unitario} = ${valor_nuevo}")
            print(f"    Nuevo precio costo: ${nuevo_precio_costo:.2f}")
            print(f"    Factor margen: {factor_margen:.3f}")
            print(f"    Nuevo precio venta: ${nuevo_precio_venta:.2f}")
            
            # Actualizar tabla principal
            cursor.execute("""
                UPDATE car_repuesto 
                SET stock = ?, precio_costo = ?, precio_venta = ?
                WHERE id = ?
            """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
            
            print("  ✅ Tabla car_repuesto actualizada")
            
            # 5. SINCRONIZAR CON REPUESTOENSTOCK
            print("\n🔗 SINCRONIZANDO CON REPUESTOENSTOCK...")
            
            # Obtener o crear registro en RepuestoEnStock
            cursor.execute("""
                SELECT id FROM car_repuestoenstock 
                WHERE repuesto_id = ? AND deposito = 'bodega-principal'
            """, (repuesto_id,))
            
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
                """, (repuesto_id, nuevo_stock, nuevo_precio_costo, nuevo_precio_venta))
                print("  ✅ RepuestoEnStock creado")
            
            # 6. CREAR MOVIMIENTO DE STOCK
            print("\n📋 CREANDO MOVIMIENTO DE STOCK...")
            try:
                # Obtener el ID del repuesto_stock
                cursor.execute("""
                    SELECT id FROM car_repuestoenstock 
                    WHERE repuesto_id = ? AND deposito = 'bodega-principal'
                """, (repuesto_id,))
                
                repuesto_stock_id = cursor.fetchone()
                if repuesto_stock_id:
                    cursor.execute("""
                        INSERT INTO car_stockmovimiento 
                        (repuesto_stock_id, tipo, cantidad, motivo, referencia, usuario_id, fecha)
                        VALUES (?, 'entrada', ?, ?, ?, 1, datetime('now'))
                    """, (repuesto_stock_id[0], cantidad, f'Compra #{numero_compra}', f'COMPRA-{compra_id}'))
                    print("  ✅ Movimiento de stock creado")
                else:
                    print("  ⚠️ No se pudo crear movimiento de stock (repuesto_stock no encontrado)")
            except Exception as e:
                print(f"  ⚠️ No se pudo crear movimiento de stock: {e}")
            
            # 7. ACTUALIZAR ESTADO DE LA COMPRA
            print("\n🔄 ACTUALIZANDO ESTADO DE LA COMPRA...")
            cursor.execute("""
                UPDATE car_compra 
                SET estado = 'recibida', fecha_recibida = date('now')
                WHERE id = ?
            """, (compra_id,))
            
            print("  ✅ Compra marcada como recibida")
        
        # Confirmar todos los cambios
        conn.commit()
        
        # 8. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        
        # Verificar tabla principal
        cursor.execute("""
            SELECT stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE id = ?
        """, (repuesto_id,))
        
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
        """, (repuesto_id,))
        
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
        
        print("\n🎉 ¡RECEPCIÓN DE COMPRA SIMULADA EXITOSAMENTE!")
        print("Ahora puedes verificar en las pantallas del sistema:")
        print(f"  - Stock final: {stock_final} unidades")
        print(f"  - Precio costo: ${precio_costo_final}")
        print(f"  - Precio venta: ${precio_venta_final}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    probar_recepcion_compra()



