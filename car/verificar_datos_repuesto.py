#!/usr/bin/env python3
"""
Script para verificar los datos del repuesto Aceite 10w-40
"""

import sqlite3
from decimal import Decimal
import os

def verificar_datos_repuesto():
    print("🔍 VERIFICANDO DATOS DEL REPUESTO ACEITE 10W-40")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. BUSCAR ACEITE 10W-40
        print("📊 BUSCANDO ACEITE 10W-40...")
        cursor.execute("""
            SELECT id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite%'
        """)
        
        repuestos = cursor.fetchall()
        
        if not repuestos:
            print("❌ No se encontraron repuestos con 'Aceite'")
            return
        
        print(f"  Encontrados {len(repuestos)} repuestos:")
        for repuesto in repuestos:
            r_id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock = repuesto
            print(f"    ID: {r_id}")
            print(f"    Nombre: {nombre}")
            print(f"    SKU: {sku}")
            print(f"    Marca: {marca}")
            print(f"    OEM: {oem}")
            print(f"    Referencia: {referencia}")
            print(f"    Precio costo: ${precio_costo}")
            print(f"    Precio venta: ${precio_venta}")
            print(f"    Stock: {stock}")
            print("    ---")
        
        # 2. BUSCAR ESPECÍFICAMENTE ACEITE 10W-40
        print("\n🔍 BUSCANDO ESPECÍFICAMENTE ACEITE 10W-40...")
        cursor.execute("""
            SELECT id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock
            FROM car_repuesto 
            WHERE nombre LIKE '%10w-40%'
        """)
        
        repuestos_10w40 = cursor.fetchall()
        
        if repuestos_10w40:
            print(f"  Encontrados {len(repuestos_10w40)} repuestos 10w-40:")
            for repuesto in repuestos_10w40:
                r_id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock = repuesto
                print(f"    ID: {r_id}")
                print(f"    Nombre: {nombre}")
                print(f"    SKU: {sku}")
                print(f"    Marca: {marca}")
                print(f"    OEM: {oem}")
                print(f"    Referencia: {referencia}")
                print(f"    Precio costo: ${precio_costo}")
                print(f"    Precio venta: ${precio_venta}")
                print(f"    Stock: {stock}")
                print("    ---")
        else:
            print("  ❌ No se encontraron repuestos 10w-40")
        
        # 3. VERIFICAR FILTROS DE EXCLUSIÓN
        print("\n🔍 VERIFICANDO FILTROS DE EXCLUSIÓN...")
        
        # Verificar OEM
        cursor.execute("""
            SELECT DISTINCT oem FROM car_repuesto 
            WHERE nombre LIKE '%Aceite%'
        """)
        oems = cursor.fetchall()
        print(f"  OEMs encontrados: {[oem[0] for oem in oems]}")
        
        # Verificar Referencias
        cursor.execute("""
            SELECT DISTINCT referencia FROM car_repuesto 
            WHERE nombre LIKE '%Aceite%'
        """)
        referencias = cursor.fetchall()
        print(f"  Referencias encontradas: {[ref[0] for ref in referencias]}")
        
        # Verificar Marcas
        cursor.execute("""
            SELECT DISTINCT marca FROM car_repuesto 
            WHERE nombre LIKE '%Aceite%'
        """)
        marcas = cursor.fetchall()
        print(f"  Marcas encontradas: {[marca[0] for marca in marcas]}")
        
        # 4. PROBAR BÚSQUEDA SIN FILTROS
        print("\n🔍 PROBANDO BÚSQUEDA SIN FILTROS...")
        cursor.execute("""
            SELECT id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock
            FROM car_repuesto 
            WHERE nombre LIKE '%Aceite%'
            ORDER BY nombre
        """)
        
        repuestos_sin_filtros = cursor.fetchall()
        
        if repuestos_sin_filtros:
            print(f"  Encontrados {len(repuestos_sin_filtros)} repuestos sin filtros:")
            for repuesto in repuestos_sin_filtros:
                r_id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock = repuesto
                print(f"    ID: {r_id}")
                print(f"    Nombre: {nombre}")
                print(f"    SKU: {sku}")
                print(f"    Marca: {marca}")
                print(f"    OEM: {oem}")
                print(f"    Referencia: {referencia}")
                print(f"    Precio costo: ${precio_costo}")
                print(f"    Precio venta: ${precio_venta}")
                print(f"    Stock: {stock}")
                print("    ---")
        
        # 5. PROBAR BÚSQUEDA CON FILTROS CORREGIDOS
        print("\n🔍 PROBANDO BÚSQUEDA CON FILTROS CORREGIDOS...")
        cursor.execute("""
            SELECT id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock
            FROM car_repuesto 
            WHERE (
                nombre LIKE '%Aceite%' OR
                sku LIKE '%Aceite%' OR
                codigo_barra LIKE '%Aceite%' OR
                oem LIKE '%Aceite%' OR
                referencia LIKE '%Aceite%'
            ) AND (
                (oem IS NULL OR oem = '' OR oem NOT IN ('oem', '')) AND
                (referencia IS NULL OR referencia = '' OR referencia NOT IN ('no-tiene', '')) AND
                (marca IS NULL OR marca = '' OR marca NOT IN ('general', ''))
            )
            ORDER BY nombre
        """)
        
        repuestos_con_filtros = cursor.fetchall()
        
        if repuestos_con_filtros:
            print(f"  Encontrados {len(repuestos_con_filtros)} repuestos con filtros corregidos:")
            for repuesto in repuestos_con_filtros:
                r_id, nombre, sku, marca, oem, referencia, precio_costo, precio_venta, stock = repuesto
                print(f"    ID: {r_id}")
                print(f"    Nombre: {nombre}")
                print(f"    SKU: {sku}")
                print(f"    Marca: {marca}")
                print(f"    OEM: {oem}")
                print(f"    Referencia: {referencia}")
                print(f"    Precio costo: ${precio_costo}")
                print(f"    Precio venta: ${precio_venta}")
                print(f"    Stock: {stock}")
                print("    ---")
        else:
            print("  ❌ No se encontraron repuestos con filtros corregidos")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_datos_repuesto()



