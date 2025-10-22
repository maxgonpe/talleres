#!/usr/bin/env python3
"""
Script para analizar duplicados en RepuestoEnStock
"""

import sqlite3
from decimal import Decimal
import os

def analizar_duplicados_stock():
    print("🔍 ANALIZANDO DUPLICADOS EN REPUESTOENSTOCK")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. BUSCAR DUPLICADOS POR REPUESTO
        print("📊 BUSCANDO DUPLICADOS POR REPUESTO...")
        
        cursor.execute("""
            SELECT repuesto_id, COUNT(*) as cantidad
            FROM car_repuestoenstock 
            GROUP BY repuesto_id
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
        """)
        
        duplicados = cursor.fetchall()
        
        if duplicados:
            print(f"  Se encontraron {len(duplicados)} repuestos con duplicados:")
            for repuesto_id, cantidad in duplicados:
                print(f"    Repuesto ID {repuesto_id}: {cantidad} registros")
        else:
            print("  ✅ No se encontraron duplicados por repuesto")
        
        # 2. ANALIZAR ESPECÍFICAMENTE EL ACEITE 10W-40
        print("\n🔍 ANALIZANDO ACEITE 10W-40 (ID 3)...")
        
        cursor.execute("""
            SELECT res.id, res.repuesto_id, res.deposito, res.proveedor, res.stock, res.reservado, 
                   res.precio_compra, res.precio_venta, r.nombre, r.sku, r.stock as stock_maestro, 
                   r.precio_costo, r.precio_venta as precio_venta_maestro
            FROM car_repuestoenstock res
            JOIN car_repuesto r ON res.repuesto_id = r.id
            WHERE res.repuesto_id = 3
            ORDER BY res.id
        """)
        
        registros_aceite = cursor.fetchall()
        
        if registros_aceite:
            print(f"  Registros encontrados: {len(registros_aceite)}")
            for registro in registros_aceite:
                res_id, repuesto_id, deposito, proveedor, stock, reservado, precio_compra, precio_venta, nombre, sku, stock_maestro, precio_costo, precio_venta_maestro = registro
                
                print(f"    Registro ID: {res_id}")
                print(f"      Repuesto: {nombre} (ID: {repuesto_id})")
                print(f"      SKU: {sku}")
                print(f"      Depósito: {deposito}")
                print(f"      Proveedor: {proveedor}")
                print(f"      Stock: {stock}")
                print(f"      Reservado: {reservado}")
                print(f"      Precio compra: ${precio_compra}")
                print(f"      Precio venta: ${precio_venta}")
                print(f"      ---")
                print(f"      Stock maestro: {stock_maestro}")
                print(f"      Precio costo maestro: ${precio_costo}")
                print(f"      Precio venta maestro: ${precio_venta_maestro}")
                print(f"      ---")
        else:
            print("  ❌ No se encontraron registros para el Aceite 10w-40")
        
        # 3. IDENTIFICAR EL REGISTRO CORRECTO
        print("\n🎯 IDENTIFICANDO REGISTRO CORRECTO...")
        
        if len(registros_aceite) > 1:
            # Buscar el registro con depósito 'bodega-principal'
            registro_principal = None
            otros_registros = []
            
            for registro in registros_aceite:
                res_id, repuesto_id, deposito, proveedor, stock, reservado, precio_compra, precio_venta, nombre, sku, stock_maestro, precio_costo, precio_venta_maestro = registro
                
                if deposito == 'bodega-principal':
                    registro_principal = registro
                else:
                    otros_registros.append(registro)
            
            if registro_principal:
                print(f"  ✅ Registro principal encontrado (ID: {registro_principal[0]})")
                print(f"    Depósito: {registro_principal[2]}")
                print(f"    Stock: {registro_principal[4]}")
                print(f"    Precio compra: ${registro_principal[6]}")
                print(f"    Precio venta: ${registro_principal[7]}")
            else:
                print(f"  ⚠️ No se encontró registro principal (bodega-principal)")
                # Usar el más reciente
                registro_principal = registros_aceite[-1]
                print(f"  Usando el más reciente (ID: {registro_principal[0]})")
            
            print(f"\n  Registros duplicados a eliminar:")
            for registro in otros_registros:
                print(f"    ID: {registro[0]}, Depósito: {registro[2]}, Stock: {registro[4]}")
        
        # 4. SOLUCIONAR DUPLICADOS
        print("\n🔧 SOLUCIONANDO DUPLICADOS...")
        
        if len(registros_aceite) > 1:
            # Eliminar registros duplicados, mantener solo el principal
            ids_a_eliminar = []
            for registro in otros_registros:
                ids_a_eliminar.append(registro[0])
            
            if ids_a_eliminar:
                print(f"  Eliminando registros duplicados: {ids_a_eliminar}")
                
                for id_eliminar in ids_a_eliminar:
                    cursor.execute("DELETE FROM car_repuestoenstock WHERE id = ?", (id_eliminar,))
                    print(f"    ✅ Eliminado registro ID: {id_eliminar}")
                
                # Actualizar el registro principal con datos del maestro
                if registro_principal:
                    cursor.execute("""
                        UPDATE car_repuestoenstock 
                        SET stock = ?, precio_compra = ?, precio_venta = ?
                        WHERE id = ?
                    """, (stock_maestro, precio_costo, precio_venta_maestro, registro_principal[0]))
                    
                    print(f"    ✅ Actualizado registro principal (ID: {registro_principal[0]})")
                    print(f"      Stock: {stock_maestro}")
                    print(f"      Precio compra: ${precio_costo}")
                    print(f"      Precio venta: ${precio_venta_maestro}")
        
        # 5. VERIFICAR RESULTADO
        print("\n🔍 VERIFICANDO RESULTADO...")
        
        cursor.execute("""
            SELECT res.id, res.repuesto_id, res.deposito, res.proveedor, res.stock, res.reservado, 
                   res.precio_compra, res.precio_venta, r.nombre, r.sku, r.stock as stock_maestro, 
                   r.precio_costo, r.precio_venta as precio_venta_maestro
            FROM car_repuestoenstock res
            JOIN car_repuesto r ON res.repuesto_id = r.id
            WHERE res.repuesto_id = 3
            ORDER BY res.id
        """)
        
        registros_finales = cursor.fetchall()
        
        if registros_finales:
            print(f"  Registros finales: {len(registros_finales)}")
            for registro in registros_finales:
                res_id, repuesto_id, deposito, proveedor, stock, reservado, precio_compra, precio_venta, nombre, sku, stock_maestro, precio_costo, precio_venta_maestro = registro
                
                print(f"    Registro ID: {res_id}")
                print(f"      Depósito: {deposito}")
                print(f"      Stock: {stock} (maestro: {stock_maestro})")
                print(f"      Precio compra: ${precio_compra} (maestro: ${precio_costo})")
                print(f"      Precio venta: ${precio_venta} (maestro: ${precio_venta_maestro})")
                
                # Verificar consistencia
                if stock == stock_maestro and precio_compra == precio_costo and precio_venta == precio_venta_maestro:
                    print(f"      ✅ CONSISTENTE")
                else:
                    print(f"      ❌ INCONSISTENTE")
        else:
            print("  ❌ No se encontraron registros finales")
        
        # 6. CREAR REGISTRO SI NO EXISTE
        if len(registros_finales) == 0:
            print("\n📦 CREANDO REGISTRO PRINCIPAL...")
            
            cursor.execute("""
                INSERT INTO car_repuestoenstock 
                (repuesto_id, deposito, proveedor, stock, reservado, precio_compra, precio_venta)
                VALUES (3, 'bodega-principal', '', ?, 0, ?, ?)
            """, (stock_maestro, precio_costo, precio_venta_maestro))
            
            print(f"  ✅ Registro creado para Aceite 10w-40")
            print(f"    Stock: {stock_maestro}")
            print(f"    Precio compra: ${precio_costo}")
            print(f"    Precio venta: ${precio_venta_maestro}")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡DUPLICADOS SOLUCIONADOS!")
        print("Ahora cada repuesto tiene un solo registro en RepuestoEnStock")
        print("Los precios y stock están sincronizados con la tabla maestra")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    analizar_duplicados_stock()



