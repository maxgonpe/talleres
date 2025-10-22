#!/usr/bin/env python3
"""
Script para probar la nueva lógica de precios
Ejemplo: Producto con 3 unidades a $2000 costo y $2400 venta
Nueva compra: precio $2100
Resultado esperado: precio costo $2100, precio venta $2520 (20% de margen)
"""

import sqlite3
from decimal import Decimal
import os

def probar_nueva_logica_precios():
    print("💰 PROBANDO NUEVA LÓGICA DE PRECIOS")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. CREAR PRODUCTO DE PRUEBA
        print("📦 CREANDO PRODUCTO DE PRUEBA...")
        
        # Buscar un repuesto existente para modificar
        cursor.execute("""
            SELECT id, nombre, stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite%'
            LIMIT 1
        """)
        
        repuesto = cursor.fetchone()
        if not repuesto:
            print("❌ No se encontró un repuesto para probar")
            return
        
        repuesto_id, nombre, stock_actual, precio_costo_actual, precio_venta_actual = repuesto
        
        print(f"  Repuesto encontrado: {nombre}")
        print(f"  Stock actual: {stock_actual}")
        print(f"  Precio costo actual: ${precio_costo_actual}")
        print(f"  Precio venta actual: ${precio_venta_actual}")
        
        # 2. CONFIGURAR DATOS DE PRUEBA
        print("\n🔧 CONFIGURANDO DATOS DE PRUEBA...")
        
        # Establecer datos iniciales: 3 unidades a $2000 costo y $2400 venta
        stock_inicial = 3
        precio_costo_inicial = 2000
        precio_venta_inicial = 2400
        
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?, precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (stock_inicial, precio_costo_inicial, precio_venta_inicial, repuesto_id))
        
        print(f"  ✅ Datos iniciales configurados:")
        print(f"    Stock: {stock_inicial} unidades")
        print(f"    Precio costo: ${precio_costo_inicial}")
        print(f"    Precio venta: ${precio_venta_inicial}")
        
        # 3. CALCULAR FACTOR DE MARGEN
        print("\n📊 CALCULANDO FACTOR DE MARGEN...")
        
        factor_margen = precio_venta_inicial / precio_costo_inicial
        porcentaje_margen = (factor_margen - 1) * 100
        
        print(f"  Factor de margen: {factor_margen:.3f}")
        print(f"  Porcentaje de margen: {porcentaje_margen:.1f}%")
        
        # 4. SIMULAR NUEVA COMPRA
        print("\n🛒 SIMULANDO NUEVA COMPRA...")
        
        cantidad_compra = 2
        precio_compra_nuevo = 2100
        
        print(f"  Cantidad a comprar: {cantidad_compra} unidades")
        print(f"  Precio de compra nuevo: ${precio_compra_nuevo}")
        
        # 5. APLICAR NUEVA LÓGICA
        print("\n💾 APLICANDO NUEVA LÓGICA...")
        
        # Calcular nuevo stock
        nuevo_stock = stock_inicial + cantidad_compra
        
        # Precio de compra es literal (no promedio ponderado)
        nuevo_precio_costo = precio_compra_nuevo
        
        # Calcular nuevo precio de venta usando factor de margen
        nuevo_precio_venta = nuevo_precio_costo * factor_margen
        
        print(f"  📈 Cálculos:")
        print(f"    Stock anterior: {stock_inicial}")
        print(f"    Cantidad comprada: {cantidad_compra}")
        print(f"    Nuevo stock: {nuevo_stock}")
        print(f"    Precio costo anterior: ${precio_costo_inicial}")
        print(f"    Precio costo nuevo: ${nuevo_precio_costo} (literal)")
        print(f"    Factor de margen: {factor_margen:.3f}")
        print(f"    Precio venta nuevo: ${nuevo_precio_venta:.2f}")
        
        # 6. ACTUALIZAR BASE DE DATOS
        print("\n💾 ACTUALIZANDO BASE DE DATOS...")
        
        cursor.execute("""
            UPDATE car_repuesto 
            SET stock = ?, precio_costo = ?, precio_venta = ?
            WHERE id = ?
        """, (nuevo_stock, nuevo_precio_costo, nuevo_precio_venta, repuesto_id))
        
        print("  ✅ Base de datos actualizada")
        
        # 7. VERIFICAR RESULTADO
        print("\n🔍 VERIFICANDO RESULTADO...")
        
        cursor.execute("""
            SELECT stock, precio_costo, precio_venta
            FROM car_repuesto 
            WHERE id = ?
        """, (repuesto_id,))
        
        stock_final, precio_costo_final, precio_venta_final = cursor.fetchone()
        
        print(f"  📊 Resultado final:")
        print(f"    Stock: {stock_final} unidades")
        print(f"    Precio costo: ${precio_costo_final}")
        print(f"    Precio venta: ${precio_venta_final}")
        
        # 8. VERIFICAR CÁLCULOS
        print("\n✅ VERIFICANDO CÁLCULOS...")
        
        # Verificar stock
        if stock_final == nuevo_stock:
            print(f"  ✅ Stock correcto: {stock_final}")
        else:
            print(f"  ❌ Stock incorrecto: esperado {nuevo_stock}, obtenido {stock_final}")
        
        # Verificar precio de costo
        if precio_costo_final == nuevo_precio_costo:
            print(f"  ✅ Precio costo correcto: ${precio_costo_final}")
        else:
            print(f"  ❌ Precio costo incorrecto: esperado ${nuevo_precio_costo}, obtenido ${precio_costo_final}")
        
        # Verificar precio de venta
        if abs(precio_venta_final - nuevo_precio_venta) < 0.01:
            print(f"  ✅ Precio venta correcto: ${precio_venta_final}")
        else:
            print(f"  ❌ Precio venta incorrecto: esperado ${nuevo_precio_venta:.2f}, obtenido ${precio_venta_final}")
        
        # 9. MOSTRAR RESUMEN
        print("\n🎯 RESUMEN DE LA NUEVA LÓGICA:")
        print(f"  📦 Producto: {nombre}")
        print(f"  📊 Estado inicial:")
        print(f"    Stock: {stock_inicial} unidades")
        print(f"    Precio costo: ${precio_costo_inicial}")
        print(f"    Precio venta: ${precio_venta_inicial}")
        print(f"    Factor de margen: {factor_margen:.3f} ({porcentaje_margen:.1f}%)")
        print(f"  🛒 Nueva compra:")
        print(f"    Cantidad: {cantidad_compra} unidades")
        print(f"    Precio de compra: ${precio_compra_nuevo}")
        print(f"  📈 Estado final:")
        print(f"    Stock: {stock_final} unidades")
        print(f"    Precio costo: ${precio_costo_final} (literal)")
        print(f"    Precio venta: ${precio_venta_final} (factor aplicado)")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡NUEVA LÓGICA DE PRECIOS IMPLEMENTADA EXITOSAMENTE!")
        print("El precio de compra es literal y el precio de venta se calcula con el factor de margen.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    probar_nueva_logica_precios()



