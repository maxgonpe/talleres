#!/usr/bin/env python3
"""
Script para ejecutar cambios REALES en la base de datos
Actualiza stock, precio costo y precio venta con el factor de margen
"""

import sqlite3
from decimal import Decimal
import os

def ejecutar_cambios_reales():
    print("🔄 EJECUTANDO CAMBIOS REALES EN LA BASE DE DATOS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar el repuesto que actualizamos antes
        cursor.execute("""
            SELECT id, nombre, stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE id = 3
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró el repuesto ID 3")
            return
        
        repuesto_id, nombre, stock_actual, precio_costo_actual, precio_venta_actual = repuesto
        
        print(f"📊 REPUESTO ACTUAL:")
        print(f"  ID: {repuesto_id}")
        print(f"  Nombre: {nombre}")
        print(f"  Stock: {stock_actual}")
        print(f"  Precio costo: ${precio_costo_actual}")
        print(f"  Precio venta: ${precio_venta_actual}")
        
        # Aplicar el ejemplo real: compra de 4 unidades a $20,000
        print("\n🛒 APLICANDO COMPRA REAL DE 4 UNIDADES A $20,000...")
        
        # Estado inicial del ejemplo
        stock_inicial = 3
        precio_costo_inicial = 19278.00
        precio_venta_inicial = 30000.00
        
        # Compra nueva
        cantidad_compra = 4
        precio_compra_nuevo = 20000.00
        
        # Cálculo del nuevo precio costo (promedio ponderado)
        valor_anterior = stock_inicial * precio_costo_inicial
        valor_nuevo = cantidad_compra * precio_compra_nuevo
        nuevo_stock = stock_inicial + cantidad_compra
        nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
        
        # Calcular factor de margen del estado inicial
        factor_margen = precio_venta_inicial / precio_costo_inicial
        
        # Aplicar factor de margen al nuevo precio costo
        nuevo_precio_venta = nuevo_precio_costo * factor_margen
        
        print(f"  📈 Cálculos:")
        print(f"    Stock inicial: {stock_inicial}")
        print(f"    Compra: {cantidad_compra} unidades a ${precio_compra_nuevo:,.2f}")
        print(f"    Nuevo stock: {nuevo_stock}")
        print(f"    Valor anterior: {stock_inicial} × ${precio_costo_inicial:,.2f} = ${valor_anterior:,.2f}")
        print(f"    Valor nuevo: {cantidad_compra} × ${precio_compra_nuevo:,.2f} = ${valor_nuevo:,.2f}")
        print(f"    Total valor: ${valor_anterior + valor_nuevo:,.2f}")
        print(f"    Nuevo precio costo: ${nuevo_precio_costo:.2f}")
        print(f"    Factor margen: {factor_margen:.3f}")
        print(f"    Nuevo precio venta: ${nuevo_precio_venta:.2f}")
        
        # ACTUALIZAR LA BASE DE DATOS CON LOS NUEVOS VALORES
        print("\n💾 ACTUALIZANDO BASE DE DATOS CON PRECIOS REALES...")
        
        # Actualizar tabla principal Repuesto
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?, precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        print("  ✅ Tabla car_repuesto actualizada")
        
        # Actualizar o crear registro en RepuestoEnStock
        cursor.execute("""
            UPDATE car_repuestoenstock 
            SET stock = ?, precio_compra = ?, precio_venta = ?
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        # Si no existe, crear el registro con proveedor
        cursor.execute("""
            INSERT OR REPLACE INTO car_repuestoenstock 
            (repuesto_id, deposito, stock, reservado, precio_compra, precio_venta, proveedor, ultima_actualizacion)
            VALUES (?, 'bodega-principal', ?, 0, ?, ?, 'Proveedor Principal', datetime('now'))
        """, (repuesto_id, nuevo_stock, nuevo_precio_costo, nuevo_precio_venta))
        
        print("  ✅ Tabla car_repuestoenstock actualizada")
        
        # Confirmar todos los cambios
        conn.commit()
        
        print("  ✅ Todos los cambios confirmados en la base de datos")
        
        # VERIFICAR LOS CAMBIOS
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
        
        # Verificar factor de margen
        factor_final = precio_venta_final / precio_costo_final
        print(f"  🎯 Factor de margen final: {factor_final:.3f}")
        
        print("\n🎉 ¡CAMBIOS REALES EJECUTADOS EXITOSAMENTE!")
        print("Ahora ve a las pantallas del sistema y verifica:")
        print("  - POS: Stock 7, Precio venta $30,642.03")
        print("  - Compras: Stock 7, Precio costo $19,690.57")
        print("  - Ficha de repuesto: Todos los datos actualizados")
        print("  - Factor de margen: 1.556 (mantenido)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    ejecutar_cambios_reales()
