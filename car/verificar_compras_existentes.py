#!/usr/bin/env python3
"""
Script para verificar las compras existentes
"""

import sqlite3
import os

def verificar_compras_existentes():
    print("🔍 VERIFICANDO COMPRAS EXISTENTES")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. VERIFICAR TODAS LAS COMPRAS
        print("📊 VERIFICANDO TODAS LAS COMPRAS...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total, fecha_compra
            FROM car_compra 
            ORDER BY id DESC
            LIMIT 10
        """)
        
        compras = cursor.fetchall()
        
        print(f"  Últimas 10 compras:")
        for compra in compras:
            c_id, numero, proveedor, estado, total, fecha = compra
            print(f"    Compra {c_id}: {numero} - {proveedor} - {estado} - ${total}")
        
        # 2. BUSCAR COMPRAS EN ESTADO BORRADOR
        print(f"\n🔍 BUSCANDO COMPRAS EN ESTADO BORRADOR...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE estado = 'borrador'
            ORDER BY id DESC
        """)
        
        compras_borrador = cursor.fetchall()
        
        print(f"  Compras en estado 'borrador': {len(compras_borrador)}")
        for compra in compras_borrador:
            c_id, numero, proveedor, estado, total = compra
            print(f"    Compra {c_id}: {numero} - {proveedor} - {estado} - ${total}")
        
        # 3. CREAR NUEVA COMPRA SI NO HAY NINGUNA EN BORRADOR
        if len(compras_borrador) == 0:
            print(f"\n🔧 CREANDO NUEVA COMPRA EN ESTADO BORRADOR...")
            
            # Obtener el siguiente número de compra
            cursor.execute("SELECT MAX(id) FROM car_compra")
            ultimo_id = cursor.fetchone()[0] or 0
            nuevo_id = ultimo_id + 1
            
            # Obtener el siguiente número de compra
            cursor.execute("SELECT MAX(numero_compra) FROM car_compra")
            ultimo_numero = cursor.fetchone()[0]
            
            if ultimo_numero:
                try:
                    numero_actual = int(ultimo_numero.split('-')[-1])
                    nuevo_numero = numero_actual + 1
                except (ValueError, IndexError):
                    nuevo_numero = 1
            else:
                nuevo_numero = 1
            
            numero_compra = f"COMP-{nuevo_numero:04d}"
            
            # Crear la compra
            cursor.execute("""
                INSERT INTO car_compra 
                (numero_compra, proveedor, fecha_compra, estado, total, observaciones, 
                 creado_por_id, creado_en, actualizado_en)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                numero_compra,
                'Proveedor Prueba Botones',
                '2025-10-22',
                'borrador',
                0,
                'Compra de prueba para verificar botones de acciones',
                1,  # Usuario ID 1
                '2025-10-22 17:15:00',
                '2025-10-22 17:15:00'
            ))
            
            compra_id = cursor.lastrowid
            
            print(f"  ✅ Compra creada: {numero_compra} (ID: {compra_id})")
            print(f"  Proveedor: Proveedor Prueba Botones")
            print(f"  Estado: borrador")
            print(f"  Total: $0")
            
            # Confirmar cambios
            conn.commit()
            
            print(f"\n🎯 INSTRUCCIONES:")
            print(f"  1. Ve al navegador")
            print(f"  2. Abre la compra {compra_id}")
            print(f"  3. Verifica que aparezcan los botones de acciones")
        else:
            print(f"\n🎯 INSTRUCCIONES:")
            print(f"  1. Ve al navegador")
            print(f"  2. Abre la compra {compras_borrador[0][0]} (la primera en estado borrador)")
            print(f"  3. Verifica que aparezcan los botones de acciones")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compras encontradas: {len(compras)}")
        print(f"  ✅ Compras en borrador: {len(compras_borrador)}")
        if len(compras_borrador) == 0:
            print(f"  ✅ Nueva compra creada para probar botones")
        else:
            print(f"  ✅ Hay compras en borrador para probar botones")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    verificar_compras_existentes()



