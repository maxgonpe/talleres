#!/usr/bin/env python3
"""
Script para crear una nueva compra de prueba
"""

import sqlite3
import os
from datetime import datetime

def crear_compra_nueva():
    print("🔧 CREANDO NUEVA COMPRA DE PRUEBA")
    print("=" * 60)
    
    # Conectar a la base de datos
    db_path = "db.sqlite3"
    if not os.path.exists(db_path):
        print(f"❌ Error: No se encontró la base de datos en {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. CREAR NUEVA COMPRA
        print("📊 CREANDO NUEVA COMPRA...")
        
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
            'Proveedor Prueba Final',
            '2025-10-22',
            'borrador',
            0,
            'Compra de prueba para verificar que todo funciona correctamente',
            1,  # Usuario ID 1
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        compra_id = cursor.lastrowid
        
        print(f"  ✅ Compra creada: {numero_compra} (ID: {compra_id})")
        print(f"  Proveedor: Proveedor Prueba Final")
        print(f"  Estado: borrador")
        print(f"  Total: $0")
        
        # 2. VERIFICAR QUE SE CREÓ CORRECTAMENTE
        print(f"\n🔍 VERIFICANDO COMPRA CREADA...")
        
        cursor.execute("""
            SELECT id, numero_compra, proveedor, estado, total
            FROM car_compra 
            WHERE id = ?
        """, (compra_id,))
        
        compra_verificada = cursor.fetchone()
        if compra_verificada:
            c_id, numero, proveedor, estado, total = compra_verificada
            print(f"  ✅ Compra verificada: {numero} (ID: {c_id})")
            print(f"  Proveedor: {proveedor}")
            print(f"  Estado: {estado}")
            print(f"  Total: ${total}")
        else:
            print(f"  ❌ Error: No se pudo verificar la compra")
            return
        
        # 3. INSTRUCCIONES PARA EL USUARIO
        print(f"\n🎯 INSTRUCCIONES PARA PROBAR:")
        print(f"  1. Ve al navegador")
        print(f"  2. Abre la compra {compra_id}")
        print(f"  3. Haz clic en 'Agregar Item'")
        print(f"  4. Busca y selecciona un repuesto")
        print(f"  5. Llena la cantidad y precio")
        print(f"  6. Haz clic en 'Agregar Item'")
        print(f"  7. Verifica que el item aparezca en la lista")
        print(f"  8. Verifica que los botones de acciones aparezcan")
        
        # 4. VERIFICAR BOTONES DE ACCIONES
        print(f"\n🔧 VERIFICANDO BOTONES DE ACCIONES...")
        
        # Verificar que la compra esté en estado 'borrador' para mostrar los botones
        if estado == 'borrador':
            print(f"  ✅ La compra está en estado 'borrador'")
            print(f"  ✅ Deberían aparecer los botones:")
            print(f"    - Confirmar Compra")
            print(f"    - Cancelar Compra")
            print(f"    - Agregar Item")
        else:
            print(f"  ❌ La compra está en estado '{estado}'")
            print(f"  ❌ Los botones pueden no aparecer correctamente")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 ¡COMPRA CREADA EXITOSAMENTE!")
        print("=" * 60)
        print("📋 RESUMEN:")
        print(f"  ✅ Compra {numero_compra} creada (ID: {compra_id})")
        print(f"  ✅ Estado: borrador")
        print(f"  ✅ Proveedor: Proveedor Prueba Final")
        print(f"  ✅ Total: $0")
        print(f"  💡 Ahora puedes probar agregar items en el navegador")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    crear_compra_nueva()



