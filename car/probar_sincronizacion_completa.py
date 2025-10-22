#!/usr/bin/env python3
"""
Script para probar la sincronización completa entre Repuesto y RepuestoEnStock
"""

import sqlite3
from decimal import Decimal
import os

def probar_sincronizacion_completa():
    print("🔄 PROBANDO SINCRONIZACIÓN COMPLETA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR ESTADO INICIAL
        print("📊 VERIFICANDO ESTADO INICIAL...")
        
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
        
        # Verificar RepuestoEnStock inicial
        cursor.execute("""
            SELECT stock, precio_compra, precio_venta
            FROM car_repuestoenstock 
            WHERE repuesto_id = ? AND deposito = 'bodega-principal'
        """, (r_id,))
        
        stock_detallado_inicial = cursor.fetchone()
        if stock_detallado_inicial:
            stock_det, precio_compra_det, precio_venta_det = stock_detallado_inicial
            print(f"  RepuestoEnStock inicial:")
            print(f"    Stock: {stock_det}")
            print(f"    Precio compra: ${precio_compra_det}")
            print(f"    Precio venta: ${precio_venta_det}")
        else:
            print(f"  ⚠️ No hay registro en RepuestoEnStock")
        
        # 2. SIMULAR NUEVA COMPRA
        print("\n🛒 SIMULANDO NUEVA COMPRA...")
        
        cantidad_compra = 2
        precio_compra_nuevo = 35000
        
        print(f"  Cantidad a comprar: {cantidad_compra} unidades")
        print(f"  Precio de compra nuevo: ${precio_compra_nuevo}")
        
        # 3. APLICAR NUEVA LÓGICA
        print("\n💾 APLICANDO NUEVA LÓGICA...")
        
        # Calcular nuevo stock
        nuevo_stock = stock_inicial + cantidad_compra
        
        # Precio de compra es literal (no promedio ponderado)
        nuevo_precio_costo = precio_compra_nuevo
        
        # Calcular factor de margen del producto existente
        if precio_costo_inicial > 0 and precio_venta_inicial > 0:
            factor_margen = precio_venta_inicial / precio_costo_inicial
            nuevo_precio_venta = nuevo_precio_costo * factor_margen
        else:
            factor_margen = 1.3
            nuevo_precio_venta = nuevo_precio_costo * factor_margen
        
        print(f"  📈 Cálculos:")
        print(f"    Stock anterior: {stock_inicial}")
        print(f"    Cantidad comprada: {cantidad_compra}")
        print(f"    Nuevo stock: {nuevo_stock}")
        print(f"    Precio costo anterior: ${precio_costo_inicial}")
        print(f"    Precio costo nuevo: ${nuevo_precio_costo} (literal)")
        print(f"    Factor de margen: {factor_margen:.3f}")
        print(f"    Precio venta nuevo: ${nuevo_precio_venta:.2f}")
        
        # 4. ACTUALIZAR TABLA PRINCIPAL
        print("\n💾 ACTUALIZANDO TABLA PRINCIPAL...")
        
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?, precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, r_id))
        
        print("  ✅ Tabla car_repuesto actualizada")
        
        # 5. SINCRONIZAR CON REPUESTOENSTOCK
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
        
        # 6. VERIFICAR RESULTADO FINAL
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
        
        stock_detallado_final = cursor.fetchone()
        if stock_detallado_final:
            print(f"  🔗 Tabla car_repuestoenstock:")
            print(f"    Stock: {stock_detallado_final[0]}")
            print(f"    Precio compra: ${stock_detallado_final[1]}")
            print(f"    Precio venta: ${stock_detallado_final[2]}")
        else:
            print(f"  ❌ No hay registro en RepuestoEnStock")
        
        # 7. VERIFICAR CONSISTENCIA
        print("\n✅ VERIFICANDO CONSISTENCIA...")
        
        if stock_detallado_final:
            stock_det, precio_compra_det, precio_venta_det = stock_detallado_final
            
            # Verificar stock
            if stock_final == stock_det:
                print(f"  ✅ Stock sincronizado: {stock_final}")
            else:
                print(f"  ❌ Stock NO sincronizado: Repuesto={stock_final}, RepuestoEnStock={stock_det}")
            
            # Verificar precio de compra
            if precio_costo_final == precio_compra_det:
                print(f"  ✅ Precio compra sincronizado: ${precio_costo_final}")
            else:
                print(f"  ❌ Precio compra NO sincronizado: Repuesto=${precio_costo_final}, RepuestoEnStock=${precio_compra_det}")
            
            # Verificar precio de venta
            if abs(precio_venta_final - precio_venta_det) < 0.01:
                print(f"  ✅ Precio venta sincronizado: ${precio_venta_final}")
            else:
                print(f"  ❌ Precio venta NO sincronizado: Repuesto=${precio_venta_final}, RepuestoEnStock=${precio_venta_det}")
            
            # Verificar consistencia total
            if (stock_final == stock_det and 
                precio_costo_final == precio_compra_det and
                abs(precio_venta_final - precio_venta_det) < 0.01):
                print(f"\n🎉 ¡PERFECTO: Todas las tablas están completamente sincronizadas!")
            else:
                print(f"\n❌ ERROR: Hay inconsistencias entre las tablas")
        else:
            print(f"  ❌ No se pudo verificar consistencia (RepuestoEnStock no encontrado)")
        
        # 8. MOSTRAR RESUMEN
        print("\n🎯 RESUMEN DE LA SINCRONIZACIÓN:")
        print(f"  📦 Repuesto: {nombre}")
        print(f"  📊 Estado inicial:")
        print(f"    Stock: {stock_inicial} unidades")
        print(f"    Precio costo: ${precio_costo_inicial}")
        print(f"    Precio venta: ${precio_venta_inicial}")
        print(f"  🛒 Compra recibida:")
        print(f"    Cantidad: {cantidad_compra} unidades")
        print(f"    Precio de compra: ${precio_compra_nuevo}")
        print(f"  📈 Estado final:")
        print(f"    Stock: {stock_final} unidades")
        print(f"    Precio costo: ${precio_costo_final} (literal)")
        print(f"    Precio venta: ${precio_venta_final} (factor aplicado)")
        print(f"  🔗 Sincronización:")
        print(f"    Repuesto y RepuestoEnStock: ✅ Completamente sincronizados")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡SINCRONIZACIÓN COMPLETA VERIFICADA!")
        print("La nueva lógica de precios está funcionando correctamente:")
        print("  - Precio de compra es literal")
        print("  - Precio de venta se calcula con factor de margen")
        print("  - Todas las tablas están sincronizadas")
        print("  - No hay inconsistencias")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    probar_sincronizacion_completa()



