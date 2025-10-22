#!/usr/bin/env python3
"""
Script para estandarizar números de compra
"""

import sqlite3
from decimal import Decimal
import os

def estandarizar_numeros_compra():
    print("🔧 ESTANDARIZANDO NÚMEROS DE COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR COMPRAS EXISTENTES
        print("📊 VERIFICANDO COMPRAS EXISTENTES...")
        cursor.execute("""
            SELECT id, numero_compra, proveedor, fecha_compra, estado
            FROM car_compra 
            ORDER BY id
        """)
        
        compras = cursor.fetchall()
        
        if not compras:
            print("  No hay compras en la base de datos")
            return
        
        print(f"  Encontradas {len(compras)} compras:")
        for compra in compras:
            c_id, numero, proveedor, fecha, estado = compra
            print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}")
        
        # 2. ESTANDARIZAR NÚMEROS
        print("\n🔧 ESTANDARIZANDO NÚMEROS DE COMPRA...")
        
        for compra in compras:
            c_id, numero_actual, proveedor, fecha, estado = compra
            
            # Generar nuevo número estándar
            nuevo_numero = f"COMP-{c_id:04d}"
            
            if numero_actual != nuevo_numero:
                print(f"  🔄 Corrigiendo ID {c_id}: {numero_actual} → {nuevo_numero}")
                cursor.execute("""
                    UPDATE car_compra 
                    SET numero_compra = ?
                    WHERE id = ?
                """, (nuevo_numero, c_id))
            else:
                print(f"  ✅ ID {c_id}: {numero_actual} (ya está correcto)")
        
        # 3. VERIFICAR RESULTADO FINAL
        print("\n🔍 VERIFICANDO RESULTADO FINAL...")
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado
            FROM car_compra 
            ORDER BY id
        """)
        
        compras_finales = cursor.fetchall()
        
        print(f"  📊 Estado final de las compras:")
        for compra in compras_finales:
            c_id, numero, proveedor, estado = compra
            print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}")
        
        # Verificar que no hay duplicados
        cursor.execute("""
            SELECT numero_compra, COUNT(*) as cantidad
            FROM car_compra 
            GROUP BY numero_compra
            HAVING COUNT(*) > 1
        """)
        
        duplicados_finales = cursor.fetchall()
        
        if duplicados_finales:
            print(f"  ❌ Aún hay {len(duplicados_finales)} números duplicados")
        else:
            print("  ✅ No hay números duplicados")
        
        # Confirmar cambios
        conn.commit()
        
        print("\n🎉 ¡NÚMEROS DE COMPRA ESTANDARIZADOS EXITOSAMENTE!")
        print("Ahora todas las compras tienen el formato estándar COMP-XXXX.")
        print("Puedes crear nuevas compras sin problemas.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    estandarizar_numeros_compra()



