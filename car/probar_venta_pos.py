#!/usr/bin/env python3
"""
Script para probar la venta en POS y verificar actualización de stock
Simula una venta de 1 unidad del Aceite 10w-40
"""

import sqlite3
from decimal import Decimal
import os
from datetime import datetime

def probar_venta_pos():
    print("🛒 PROBANDO VENTA EN POS Y ACTUALIZACIÓN DE STOCK")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. OBTENER ESTADO ACTUAL DEL REPUESTO
        print("📊 ESTADO ACTUAL DEL REPUESTO...")
        cursor.execute("""
            SELECT id, nombre, sku, stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite 10w-40%'
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró el repuesto Aceite 10w-40")
            return
        
        repuesto_id, nombre, sku, stock_actual, precio_costo_actual, precio_venta_actual = repuesto
        
        print(f"  Repuesto: {nombre}")
        print(f"  SKU: {sku}")
        print(f"  Stock actual: {stock_actual}")
        print(f"  Precio costo: ${precio_costo_actual}")
        print(f"  Precio venta: ${precio_venta_actual}")
        
        # Verificar RepuestoEnStock
        cursor.execute("""
            SELECT stock, precio_compra, precio_venta 
            FROM car_repuestoenstock 
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (repuesto_id,))
        
        stock_detallado = cursor.fetchone()
        if stock_detallado:
            print(f"  RepuestoEnStock:")
            print(f"    Stock: {stock_detallado[0]}")
            print(f"    Precio compra: ${stock_detallado[1]}")
            print(f"    Precio venta: ${stock_detallado[2]}")
        
        # 2. SIMULAR VENTA DE 1 UNIDAD
        print("\n🛒 SIMULANDO VENTA DE 1 UNIDAD...")
        
        cantidad_vendida = 1
        nuevo_stock = stock_actual - cantidad_vendida
        
        print(f"  Cantidad a vender: {cantidad_vendida}")
        print(f"  Stock después de venta: {nuevo_stock}")
        
        # 3. ACTUALIZAR STOCK EN TABLA MAESTRA
        print("\n💾 ACTUALIZANDO STOCK EN TABLA MAESTRA...")
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?
            WHERE id = ?
        """, (nuevo_stock, repuesto_id))
        
        print("  ✅ Tabla car_repuesto actualizada")
        
        # 4. SINCRONIZAR CON REPUESTOENSTOCK
        print("\n🔗 SINCRONIZANDO CON REPUESTOENSTOCK...")
        cursor.execute("""
            UPDATE car_repuestoenstock 
            SET stock = ?
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (nuevo_stock, repuesto_id))
        
        print("  ✅ Tabla car_repuestoenstock sincronizada")
        
        # 5. CREAR REGISTRO DE VENTA
        print("\n📋 CREANDO REGISTRO DE VENTA...")
        
        # Obtener el próximo número de venta
        cursor.execute("SELECT MAX(id) FROM car_ventapos")
        max_venta_id = cursor.fetchone()[0] or 0
        nueva_venta_id = max_venta_id + 1
        
        # Crear venta
        cursor.execute("""
            INSERT INTO car_ventapos 
            (sesion_id, cliente_id, usuario_id, fecha, subtotal, descuento, total, metodo_pago, pagado, observaciones)
            VALUES (1, NULL, 1, datetime('now'), ?, 0, ?, 'efectivo', 1, 'Venta de prueba')
        """, (precio_venta_actual, precio_venta_actual))
        
        venta_id = cursor.lastrowid
        print(f"  ✅ Venta creada: ID {venta_id}")
        
        # 6. CREAR ITEM DE VENTA
        print("\n📦 CREANDO ITEM DE VENTA...")
        cursor.execute("""
            INSERT INTO car_ventapositem 
            (venta_id, repuesto_id, cantidad, precio_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?)
        """, (venta_id, repuesto_id, cantidad_vendida, precio_venta_actual, precio_venta_actual))
        
        print(f"  ✅ Item de venta creado")
        
        # 7. CREAR MOVIMIENTO DE STOCK (opcional)
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
                    VALUES (?, 'salida', ?, ?, ?, 1, datetime('now'))
                """, (repuesto_stock_id[0], cantidad_vendida, f'Venta POS #{venta_id}', str(venta_id)))
                print(f"  ✅ Movimiento de stock creado")
            else:
                print(f"  ⚠️ No se pudo crear movimiento de stock (repuesto_stock no encontrado)")
        except Exception as e:
            print(f"  ⚠️ No se pudo crear movimiento de stock: {e}")
        
        # Confirmar todos los cambios
        conn.commit()
        
        # 8. VERIFICAR CAMBIOS
        print("\n🔍 VERIFICANDO CAMBIOS APLICADOS...")
        
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
        
        stock_detallado_final = cursor.fetchone()
        if stock_detallado_final:
            print(f"  🔗 Tabla car_repuestoenstock:")
            print(f"    Stock: {stock_detallado_final[0]}")
            print(f"    Precio compra: ${stock_detallado_final[1]}")
            print(f"    Precio venta: ${stock_detallado_final[2]}")
        
        # Verificar venta creada
        cursor.execute("""
            SELECT id, total, metodo_pago, fecha 
            FROM car_ventapos 
            WHERE id = ?
        """, (venta_id,))
        
        venta_info = cursor.fetchone()
        if venta_info:
            print(f"  🛒 Venta creada:")
            print(f"    ID: {venta_info[0]}")
            print(f"    Total: ${venta_info[1]}")
            print(f"    Método pago: {venta_info[2]}")
            print(f"    Fecha: {venta_info[3]}")
        
        # Verificar consistencia
        if (stock_final == stock_detallado_final[0] and 
            precio_costo_final == stock_detallado_final[1] and
            precio_venta_final == stock_detallado_final[2]):
            print("\n✅ PERFECTO: Todas las tablas están sincronizadas")
        else:
            print("\n❌ ERROR: Hay inconsistencias entre las tablas")
        
        print("\n🎉 ¡VENTA SIMULADA Y STOCK ACTUALIZADO EXITOSAMENTE!")
        print("Ahora puedes verificar en las pantallas del sistema:")
        print(f"  - Stock final: {stock_final} unidades")
        print(f"  - Precio costo: ${precio_costo_final}")
        print(f"  - Precio venta: ${precio_venta_final}")
        print(f"  - Venta ID: {venta_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    probar_venta_pos()
