#!/usr/bin/env python3
"""
Script para crear una compra REAL y actualizar datos según el factor de margen
Producto: Aceite 10w-40 (ACEIT-XXXX-ZZZZZZ-4706)
Estado actual: Stock 7, Precio costo $19,690.57, Precio venta $30,642.03
Compra: 3 unidades a $20,000
Resultado esperado: Stock 10, Precio costo $19,690.57, Precio venta $30,642.03
"""

import sqlite3
from decimal import Decimal
import os
from datetime import datetime

def crear_compra_real():
    print("🛒 CREANDO COMPRA REAL Y ACTUALIZANDO DATOS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. OBTENER DATOS ACTUALES DEL REPUESTO
        print("📊 OBTENIENDO DATOS ACTUALES...")
        cursor.execute("""
            SELECT id, nombre, sku, stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite 10w-40%' OR sku LIKE '%ACEIT%'
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró el repuesto Aceite 10w-40")
            return
        
        repuesto_id, nombre, sku, stock_actual, precio_costo_actual, precio_venta_actual = repuesto
        
        print(f"  Repuesto encontrado:")
        print(f"    ID: {repuesto_id}")
        print(f"    Nombre: {nombre}")
        print(f"    SKU: {sku}")
        print(f"    Stock actual: {stock_actual}")
        print(f"    Precio costo: ${precio_costo_actual}")
        print(f"    Precio venta: ${precio_venta_actual}")
        
        # Calcular factor de margen actual
        if precio_costo_actual and precio_venta_actual and precio_costo_actual > 0:
            factor_margen = precio_venta_actual / precio_costo_actual
            print(f"    Factor de margen: {factor_margen:.3f}")
        else:
            print("❌ No se puede calcular factor de margen")
            return
        
        # 2. CREAR REGISTRO DE COMPRA
        print("\n🛒 CREANDO REGISTRO DE COMPRA...")
        
        # Obtener el próximo número de compra
        cursor.execute("SELECT MAX(CAST(SUBSTR(numero_compra, 2) AS INTEGER)) FROM car_compra WHERE numero_compra LIKE 'C%'")
        max_num = cursor.fetchone()[0] or 0
        nuevo_numero = f"C{max_num + 1:04d}"
        
        # Crear la compra
        cursor.execute("""
            INSERT INTO car_compra 
            (numero_compra, proveedor, fecha_compra, estado, total, observaciones, creado_por_id, creado_en, actualizado_en)
            VALUES (?, 'Proveedor Test', date('now'), 'recibida', ?, 'Compra de prueba - Aceite 10w-40', 1, datetime('now'), datetime('now'))
        """, (nuevo_numero, 0))  # Total se calculará después
        
        compra_id = cursor.lastrowid
        print(f"  ✅ Compra creada: #{nuevo_numero} (ID: {compra_id})")
        
        # 3. CREAR ITEM DE COMPRA
        print("\n📦 CREANDO ITEM DE COMPRA...")
        
        cantidad_compra = 3
        precio_compra_nuevo = 20000.00
        subtotal_item = cantidad_compra * precio_compra_nuevo
        
        cursor.execute("""
            INSERT INTO car_compraitem 
            (compra_id, repuesto_id, cantidad, precio_unitario, subtotal, recibido, fecha_recibido)
            VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
        """, (compra_id, repuesto_id, cantidad_compra, precio_compra_nuevo, subtotal_item))
        
        item_id = cursor.lastrowid
        print(f"  ✅ Item creado:")
        print(f"    Cantidad: {cantidad_compra}")
        print(f"    Precio unitario: ${precio_compra_nuevo:,.2f}")
        print(f"    Subtotal: ${subtotal_item:,.2f}")
        print(f"    Estado: Recibido")
        
        # 4. ACTUALIZAR TOTAL DE LA COMPRA
        cursor.execute("""
            UPDATE car_compra 
            SET total = ?
            WHERE id = ?
        """, (subtotal_item, compra_id))
        
        print(f"  ✅ Total de compra actualizado: ${subtotal_item:,.2f}")
        
        # 5. CALCULAR NUEVOS PRECIOS CON FACTOR DE MARGEN
        print("\n🧮 CALCULANDO NUEVOS PRECIOS...")
        
        # Estado actual
        stock_anterior = stock_actual
        precio_costo_anterior = precio_costo_actual
        precio_venta_anterior = precio_venta_actual
        
        # Compra nueva
        cantidad_entrada = cantidad_compra
        precio_compra_entrada = precio_compra_nuevo
        
        # Cálculo del nuevo precio costo (promedio ponderado)
        valor_anterior = stock_anterior * precio_costo_anterior
        valor_nuevo = cantidad_entrada * precio_compra_entrada
        nuevo_stock = stock_anterior + cantidad_entrada
        nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
        
        # Aplicar factor de margen al nuevo precio costo
        nuevo_precio_venta = nuevo_precio_costo * factor_margen
        
        print(f"  📈 Cálculos:")
        print(f"    Stock anterior: {stock_anterior}")
        print(f"    Compra: {cantidad_entrada} unidades a ${precio_compra_entrada:,.2f}")
        print(f"    Nuevo stock: {nuevo_stock}")
        print(f"    Valor anterior: {stock_anterior} × ${precio_costo_anterior:,.2f} = ${valor_anterior:,.2f}")
        print(f"    Valor nuevo: {cantidad_entrada} × ${precio_compra_entrada:,.2f} = ${valor_nuevo:,.2f}")
        print(f"    Total valor: ${valor_anterior + valor_nuevo:,.2f}")
        print(f"    Nuevo precio costo: ${nuevo_precio_costo:.2f}")
        print(f"    Factor margen: {factor_margen:.3f}")
        print(f"    Nuevo precio venta: ${nuevo_precio_venta:.2f}")
        
        # 6. ACTUALIZAR TABLA REPUESTO
        print("\n💾 ACTUALIZANDO TABLA REPUESTO...")
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?, precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        print("  ✅ Tabla car_repuesto actualizada")
        
        # 7. ACTUALIZAR TABLA REPUESTOENSTOCK
        print("\n🔗 ACTUALIZANDO TABLA REPUESTOENSTOCK...")
        cursor.execute("""
            UPDATE car_repuestoenstock 
            SET stock = ?, precio_compra = ?, precio_venta = ?
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        print("  ✅ Tabla car_repuestoenstock actualizada")
        
        # 8. CREAR MOVIMIENTO DE STOCK (opcional, puede fallar)
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
                    VALUES (?, 'entrada', ?, 'Compra recibida', ?, 1, datetime('now'))
                """, (repuesto_stock_id[0], cantidad_entrada, f'COMPRA-{compra_id}'))
                print("  ✅ Movimiento de stock creado")
            else:
                print("  ⚠️ No se pudo crear movimiento de stock (repuesto_stock no encontrado)")
        except Exception as e:
            print(f"  ⚠️ No se pudo crear movimiento de stock: {e}")
        
        # Confirmar todos los cambios
        conn.commit()
        
        # 9. VERIFICAR CAMBIOS
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
        print(f"    Precio costo: ${precio_costo_final:.2f}")
        print(f"    Precio venta: ${precio_venta_final:.2f}")
        
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
            print(f"    Precio compra: ${stock_detallado[1]:.2f}")
            print(f"    Precio venta: ${stock_detallado[2]:.2f}")
        
        # Verificar compra creada
        cursor.execute("""
            SELECT numero_compra, proveedor, total, estado 
            FROM car_compra 
            WHERE id = ?
        """, (compra_id,))
        
        compra_info = cursor.fetchone()
        if compra_info:
            print(f"  🛒 Compra creada:")
            print(f"    Número: {compra_info[0]}")
            print(f"    Proveedor: {compra_info[1]}")
            print(f"    Total: ${compra_info[2]:,.2f}")
            print(f"    Estado: {compra_info[3]}")
        
        # Verificar factor de margen final
        factor_final = precio_venta_final / precio_costo_final
        print(f"  🎯 Factor de margen final: {factor_final:.3f}")
        
        print("\n🎉 ¡COMPRA REAL CREADA Y DATOS ACTUALIZADOS EXITOSAMENTE!")
        print("Ahora puedes verificar en las pantallas del sistema:")
        print(f"  - Compra #{compra_info[0]} creada con 3 unidades a $20,000")
        print(f"  - Stock final: {stock_final} unidades")
        print(f"  - Precio costo final: ${precio_costo_final:.2f}")
        print(f"  - Precio venta final: ${precio_venta_final:.2f}")
        print(f"  - Factor de margen: {factor_final:.3f} (mantenido)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    crear_compra_real()
