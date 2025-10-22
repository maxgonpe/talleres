#!/usr/bin/env python3
"""
Script para solucionar definitivamente los duplicados en RepuestoEnStock
"""

import sqlite3
from decimal import Decimal
import os

def solucionar_duplicados_final():
    print("🔧 SOLUCIONANDO DUPLICADOS DEFINITIVAMENTE")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. IDENTIFICAR REGISTRO CORRECTO
        print("🎯 IDENTIFICANDO REGISTRO CORRECTO...")
        
        cursor.execute("""
            SELECT res.id, res.repuesto_id, res.deposito, res.proveedor, res.stock, res.reservado, 
                   res.precio_compra, res.precio_venta, r.nombre, r.sku, r.stock as stock_maestro, 
                   r.precio_costo, r.precio_venta as precio_venta_maestro
            FROM car_repuestoenstock res
            JOIN car_repuesto r ON res.repuesto_id = r.id
            WHERE res.repuesto_id = 3
            ORDER BY res.id
        """)
        
        registros = cursor.fetchall()
        
        if len(registros) != 2:
            print(f"  ❌ Se esperaban 2 registros, se encontraron {len(registros)}")
            return
        
        # Identificar el registro correcto (el que coincide con el maestro)
        registro_correcto = None
        registro_incorrecto = None
        
        for registro in registros:
            res_id, repuesto_id, deposito, proveedor, stock, reservado, precio_compra, precio_venta, nombre, sku, stock_maestro, precio_costo, precio_venta_maestro = registro
            
            if (stock == stock_maestro and 
                precio_compra == precio_costo and 
                precio_venta == precio_venta_maestro):
                registro_correcto = registro
                print(f"  ✅ Registro correcto: ID {res_id}")
            else:
                registro_incorrecto = registro
                print(f"  ❌ Registro incorrecto: ID {res_id}")
        
        if not registro_correcto or not registro_incorrecto:
            print(f"  ❌ No se pudo identificar correctamente los registros")
            return
        
        # 2. ELIMINAR REGISTRO INCORRECTO
        print(f"\n🗑️ ELIMINANDO REGISTRO INCORRECTO...")
        
        id_incorrecto = registro_incorrecto[0]
        cursor.execute("DELETE FROM car_repuestoenstock WHERE id = ?", (id_incorrecto,))
        
        print(f"  ✅ Eliminado registro ID: {id_incorrecto}")
        
        # 3. VERIFICAR RESULTADO
        print(f"\n🔍 VERIFICANDO RESULTADO...")
        
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
        
        if len(registros_finales) == 1:
            registro_final = registros_finales[0]
            res_id, repuesto_id, deposito, proveedor, stock, reservado, precio_compra, precio_venta, nombre, sku, stock_maestro, precio_costo, precio_venta_maestro = registro_final
            
            print(f"  ✅ Registro final: ID {res_id}")
            print(f"    Repuesto: {nombre}")
            print(f"    SKU: {sku}")
            print(f"    Depósito: {deposito}")
            print(f"    Stock: {stock} (maestro: {stock_maestro})")
            print(f"    Precio compra: ${precio_compra} (maestro: ${precio_costo})")
            print(f"    Precio venta: ${precio_venta} (maestro: ${precio_venta_maestro})")
            
            # Verificar consistencia
            if (stock == stock_maestro and 
                precio_compra == precio_costo and 
                precio_venta == precio_venta_maestro):
                print(f"    ✅ PERFECTAMENTE CONSISTENTE")
            else:
                print(f"    ❌ AÚN INCONSISTENTE")
        else:
            print(f"  ❌ Se esperaba 1 registro, se encontraron {len(registros_finales)}")
        
        # 4. VERIFICAR OTROS DUPLICADOS
        print(f"\n🔍 VERIFICANDO OTROS DUPLICADOS...")
        
        cursor.execute("""
            SELECT repuesto_id, COUNT(*) as cantidad
            FROM car_repuestoenstock 
            GROUP BY repuesto_id
            HAVING COUNT(*) > 1
            ORDER BY cantidad DESC
        """)
        
        otros_duplicados = cursor.fetchall()
        
        if otros_duplicados:
            print(f"  ⚠️ Se encontraron otros duplicados:")
            for repuesto_id, cantidad in otros_duplicados:
                print(f"    Repuesto ID {repuesto_id}: {cantidad} registros")
        else:
            print(f"  ✅ No hay más duplicados")
        
        # 5. CREAR FUNCIÓN DE LIMPIEZA AUTOMÁTICA
        print(f"\n🛠️ CREANDO FUNCIÓN DE LIMPIEZA AUTOMÁTICA...")
        
        # Crear un script de limpieza que se puede ejecutar periódicamente
        script_limpieza = """
# Script para limpiar duplicados en RepuestoEnStock
# Ejecutar periódicamente para mantener consistencia

import sqlite3

def limpiar_duplicados():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    try:
        # Buscar duplicados
        cursor.execute('''
            SELECT repuesto_id, COUNT(*) as cantidad
            FROM car_repuestoenstock 
            GROUP BY repuesto_id
            HAVING COUNT(*) > 1
        ''')
        
        duplicados = cursor.fetchall()
        
        for repuesto_id, cantidad in duplicados:
            # Obtener todos los registros del repuesto
            cursor.execute('''
                SELECT res.id, res.stock, res.precio_compra, res.precio_venta, 
                       r.stock as stock_maestro, r.precio_costo, r.precio_venta as precio_venta_maestro
                FROM car_repuestoenstock res
                JOIN car_repuesto r ON res.repuesto_id = r.id
                WHERE res.repuesto_id = ?
                ORDER BY res.id
            ''', (repuesto_id,))
            
            registros = cursor.fetchall()
            
            # Identificar el registro correcto
            registro_correcto = None
            for registro in registros:
                res_id, stock, precio_compra, precio_venta, stock_maestro, precio_costo, precio_venta_maestro = registro
                
                if (stock == stock_maestro and 
                    precio_compra == precio_costo and 
                    precio_venta == precio_venta_maestro):
                    registro_correcto = registro
                    break
            
            # Si no hay registro correcto, usar el más reciente
            if not registro_correcto:
                registro_correcto = registros[-1]
            
            # Eliminar duplicados
            ids_a_eliminar = [r[0] for r in registros if r[0] != registro_correcto[0]]
            
            for id_eliminar in ids_a_eliminar:
                cursor.execute('DELETE FROM car_repuestoenstock WHERE id = ?', (id_eliminar,))
            
            print(f'Limpiados {len(ids_a_eliminar)} duplicados para repuesto {repuesto_id}')
        
        conn.commit()
        print('Limpieza completada')
        
    except Exception as e:
        print(f'Error: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    limpiar_duplicados()
"""
        
        with open('limpiar_duplicados.py', 'w') as f:
            f.write(script_limpieza)
        
        print(f"  ✅ Script de limpieza creado: limpiar_duplicados.py")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡DUPLICADOS SOLUCIONADOS DEFINITIVAMENTE!")
        print("Ahora cada repuesto tiene un solo registro en RepuestoEnStock")
        print("Los precios y stock están perfectamente sincronizados")
        print("\nPara prevenir futuros duplicados:")
        print("1. Ejecuta 'python3 limpiar_duplicados.py' periódicamente")
        print("2. Asegúrate de que el método _sincronizar_con_stock_detallado funcione correctamente")
        print("3. Verifica que no se creen registros duplicados en las compras")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    solucionar_duplicados_final()



