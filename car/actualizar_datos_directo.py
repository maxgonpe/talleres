#!/usr/bin/env python3
"""
Script para actualizar datos directamente en la base de datos
Simula el ejemplo del usuario: 3 unidades a $19,278, compra 4 a $20,000
"""

import sqlite3
from decimal import Decimal
import os

def actualizar_repuesto_ejemplo():
    print("🔄 ACTUALIZANDO DATOS DIRECTAMENTE EN LA BASE DE DATOS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Buscar un repuesto con stock para actualizar
        cursor.execute("""
            SELECT id, nombre, stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE stock > 0 
            LIMIT 1
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontraron repuestos con stock")
            return
        
        repuesto_id, nombre, stock_actual, precio_costo_actual, precio_venta_actual = repuesto
        
        print(f"📊 REPUESTO ENCONTRADO:")
        print(f"  ID: {repuesto_id}")
        print(f"  Nombre: {nombre}")
        print(f"  Stock actual: {stock_actual}")
        print(f"  Precio costo: ${precio_costo_actual}")
        print(f"  Precio venta: ${precio_venta_actual}")
        
        # Configurar el estado inicial del ejemplo
        print("\n🔧 CONFIGURANDO ESTADO INICIAL DEL EJEMPLO...")
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = 3, precio_costo = 19278.00, precio_venta = 30000.00
            WHERE id = ?
        """, (repuesto_id,))
        
        print("  ✅ Estado inicial configurado:")
        print("    Stock: 3 unidades")
        print("    Precio costo: $19,278")
        print("    Precio venta: $30,000")
        
        # Calcular el factor de margen
        factor_margen = 30000.00 / 19278.00
        print(f"    Factor de margen: {factor_margen:.3f}")
        
        # Simular la compra de 4 unidades a $20,000
        print("\n🛒 SIMULANDO COMPRA DE 4 UNIDADES A $20,000...")
        
        # Cálculo del nuevo precio costo (promedio ponderado)
        valor_anterior = 3 * 19278.00
        valor_nuevo = 4 * 20000.00
        nuevo_stock = 3 + 4
        nuevo_precio_costo = (valor_anterior + valor_nuevo) / nuevo_stock
        
        # Cálculo del nuevo precio venta (aplicando factor de margen)
        nuevo_precio_venta = nuevo_precio_costo * factor_margen
        
        print(f"  📈 Cálculo:")
        print(f"    Valor anterior: 3 × $19,278 = ${valor_anterior:,.2f}")
        print(f"    Valor nuevo: 4 × $20,000 = ${valor_nuevo:,.2f}")
        print(f"    Total: ${valor_anterior + valor_nuevo:,.2f}")
        print(f"    Nuevo stock: {nuevo_stock}")
        print(f"    Nuevo precio costo: ${nuevo_precio_costo:.2f}")
        print(f"    Factor margen: {factor_margen:.3f}")
        print(f"    Nuevo precio venta: ${nuevo_precio_venta:.2f}")
        
        # Actualizar la base de datos
        print("\n💾 ACTUALIZANDO BASE DE DATOS...")
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?, precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        # Actualizar RepuestoEnStock si existe
        cursor.execute("""
            UPDATE car_repuestoenstock 
            SET stock = ?, precio_compra = ?, precio_venta = ?
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        # Si no existe registro en RepuestoEnStock, crear uno
        cursor.execute("""
            INSERT OR IGNORE INTO car_repuestoenstock 
            (repuesto_id, deposito, stock, reservado, precio_compra, precio_venta, ultima_actualizacion)
            VALUES (?, 'bodega-principal', ?, 0, ?, ?, datetime('now'))
        """, (repuesto_id, nuevo_stock, nuevo_precio_costo, nuevo_precio_venta))
        
        # Confirmar cambios
        conn.commit()
        
        print("  ✅ Base de datos actualizada exitosamente")
        
        # Verificar los cambios
        print("\n🔍 VERIFICANDO CAMBIOS...")
        cursor.execute("""
            SELECT stock, precio_costo, precio_venta 
            FROM car_repuesto 
            WHERE id = ?
        """, (repuesto_id,))
        
        stock_final, precio_costo_final, precio_venta_final = cursor.fetchone()
        
        print(f"  📊 Estado final:")
        print(f"    Stock: {stock_final}")
        print(f"    Precio costo: ${precio_costo_final}")
        print(f"    Precio venta: ${precio_venta_final}")
        
        # Verificar RepuestoEnStock
        cursor.execute("""
            SELECT stock, precio_compra, precio_venta 
            FROM car_repuestoenstock 
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (repuesto_id,))
        
        stock_detallado = cursor.fetchone()
        if stock_detallado:
            print(f"  🔗 RepuestoEnStock sincronizado:")
            print(f"    Stock: {stock_detallado[0]}")
            print(f"    Precio compra: ${stock_detallado[1]}")
            print(f"    Precio venta: ${stock_detallado[2]}")
        
        print("\n🎉 ¡DATOS ACTUALIZADOS EXITOSAMENTE!")
        print("Ahora puedes ver los cambios en las pantallas del sistema:")
        print("  - POS: Stock 7, Precio venta $30,642.03")
        print("  - Compras: Stock 7, Precio costo $19,690.57")
        print("  - Ficha de repuesto: Todos los datos actualizados")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    actualizar_repuesto_ejemplo()



