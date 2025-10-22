#!/usr/bin/env python3
"""
Script para corregir números de compra duplicados
"""

import sqlite3
from decimal import Decimal
import os

def corregir_numeros_compra():
    print("🔧 CORRIGIENDO NÚMEROS DE COMPRA DUPLICADOS")
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
            SELECT id, numero_compra, proveedor, fecha_compra, estado, total
            FROM car_compra 
            ORDER BY id
        """)
        
        compras = cursor.fetchall()
        
        if not compras:
            print("  No hay compras en la base de datos")
            return
        
        print(f"  Encontradas {len(compras)} compras:")
        for compra in compras:
            c_id, numero, proveedor, fecha, estado, total = compra
            print(f"    ID: {c_id}, Número: {numero}, Proveedor: {proveedor}, Estado: {estado}")
        
        # 2. IDENTIFICAR DUPLICADOS
        print("\n🔍 IDENTIFICANDO NÚMEROS DUPLICADOS...")
        cursor.execute("""
            SELECT numero_compra, COUNT(*) as cantidad
            FROM car_compra 
            GROUP BY numero_compra
            HAVING COUNT(*) > 1
        """)
        
        duplicados = cursor.fetchall()
        
        if duplicados:
            print(f"  ❌ Encontrados {len(duplicados)} números duplicados:")
            for numero, cantidad in duplicados:
                print(f"    {numero}: {cantidad} veces")
        else:
            print("  ✅ No se encontraron números duplicados")
        
        # 3. CORREGIR NÚMEROS DUPLICADOS
        if duplicados:
            print("\n🔧 CORRIGIENDO NÚMEROS DUPLICADOS...")
            
            for numero_duplicado, cantidad in duplicados:
                print(f"  Corrigiendo {numero_duplicado}...")
                
                # Obtener todas las compras con este número
                cursor.execute("""
                    SELECT id, numero_compra, proveedor
                    FROM car_compra 
                    WHERE numero_compra = ?
                    ORDER BY id
                """, (numero_duplicado,))
                
                compras_duplicadas = cursor.fetchall()
                
                # Mantener la primera y corregir las demás
                for i, (c_id, numero, proveedor) in enumerate(compras_duplicadas):
                    if i == 0:
                        print(f"    ✅ Manteniendo ID {c_id} con número {numero}")
                    else:
                        # Generar nuevo número
                        nuevo_numero = f"COMP-{c_id:04d}"
                        cursor.execute("""
                            UPDATE car_compra 
                            SET numero_compra = ?
                            WHERE id = ?
                        """, (nuevo_numero, c_id))
                        print(f"    🔄 Corrigiendo ID {c_id}: {numero} → {nuevo_numero}")
        
        # 4. VERIFICAR NÚMEROS VACÍOS
        print("\n🔍 VERIFICANDO NÚMEROS VACÍOS...")
        cursor.execute("""
            SELECT id, numero_compra, proveedor
            FROM car_compra 
            WHERE numero_compra IS NULL OR numero_compra = ''
            ORDER BY id
        """)
        
        compras_sin_numero = cursor.fetchall()
        
        if compras_sin_numero:
            print(f"  ❌ Encontradas {len(compras_sin_numero)} compras sin número:")
            for c_id, numero, proveedor in compras_sin_numero:
                print(f"    ID: {c_id}, Proveedor: {proveedor}")
            
            print("  🔧 Asignando números a compras sin número...")
            for c_id, numero, proveedor in compras_sin_numero:
                nuevo_numero = f"COMP-{c_id:04d}"
                cursor.execute("""
                    UPDATE car_compra 
                    SET numero_compra = ?
                    WHERE id = ?
                """, (nuevo_numero, c_id))
                print(f"    ✅ ID {c_id}: {numero} → {nuevo_numero}")
        else:
            print("  ✅ No se encontraron compras sin número")
        
        # 5. VERIFICAR RESULTADO FINAL
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
        
        print("\n🎉 ¡NÚMEROS DE COMPRA CORREGIDOS EXITOSAMENTE!")
        print("Ahora puedes crear nuevas compras sin problemas de duplicados.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    corregir_numeros_compra()



