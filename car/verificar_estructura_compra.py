#!/usr/bin/env python3
"""
Script para verificar la estructura de la tabla car_compra
"""

import sqlite3
import os

def verificar_estructura_compra():
    print("🔍 VERIFICANDO ESTRUCTURA DE CAR_COMPRA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Obtener información de la tabla
        cursor.execute("PRAGMA table_info(car_compra)")
        columnas = cursor.fetchall()
        
        print("📊 ESTRUCTURA DE CAR_COMPRA:")
        print("  Columnas:")
        for columna in columnas:
            cid, nombre, tipo, notnull, default, pk = columna
            print(f"    {nombre}: {tipo} {'NOT NULL' if notnull else 'NULL'} {'PRIMARY KEY' if pk else ''} {'DEFAULT: ' + str(default) if default else ''}")
        
        # Verificar una compra existente
        cursor.execute("""
            SELECT * FROM car_compra LIMIT 1
        """)
        
        compra_ejemplo = cursor.fetchone()
        if compra_ejemplo:
            print(f"\n📋 EJEMPLO DE COMPRA EXISTENTE:")
            for i, valor in enumerate(compra_ejemplo):
                nombre_columna = columnas[i][1]
                print(f"    {nombre_columna}: {valor}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_estructura_compra()



