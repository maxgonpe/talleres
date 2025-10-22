#!/usr/bin/env python3
"""
Script para crear una nueva compra de prueba final
"""

import sqlite3
import os
from datetime import datetime

def crear_compra_prueba_final():
    print("🔧 CREANDO NUEVA COMPRA DE PRUEBA FINAL")
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
            'Proveedor Prueba Final - Botones',
            '2025-10-22',
            'borrador',
            0,
            'Compra de prueba final para verificar botones de acciones',
            1,  # Usuario ID 1
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        compra_id = cursor.lastrowid
        
        print(f"  ✅ Compra creada: {numero_compra} (ID: {compra_id})")
        print(f"  Proveedor: Proveedor Prueba Final - Botones")
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
        
        # 3. INSTRUCCIONES PARA PROBAR BOTONES
        print(f"\n🎯 INSTRUCCIONES PARA PROBAR BOTONES:")
        print(f"  1. Ve al navegador")
        print(f"  2. Abre la compra {compra_id}")
        print(f"  3. Verifica que aparezcan los botones:")
        print(f"     - ✅ Confirmar Compra")
        print(f"     - ✅ Cancelar Compra")
        print(f"     - ✅ Agregar Item")
        print(f"  4. Haz clic en 'Agregar Item'")
        print(f"  5. Selecciona un repuesto de la lista")
        print(f"  6. Llena la cantidad y precio")
        print(f"  7. Haz clic en 'Agregar Item'")
        print(f"  8. Verifica que el item aparezca en la lista")
        print(f"  9. Haz clic en 'Confirmar Compra'")
        print(f"  10. Verifica que los botones cambien a 'Recibir'")
        
        # 4. VERIFICAR BOTONES SEGÚN ESTADO
        print(f"\n🔧 VERIFICANDO BOTONES SEGÚN ESTADO...")
        
        if estado == 'borrador':
            print(f"  ✅ La compra está en estado 'borrador'")
            print(f"  ✅ Deberían aparecer los botones:")
            print(f"    - Confirmar Compra (amarillo)")
            print(f"    - Cancelar Compra (rojo)")
            print(f"    - Agregar Item (azul)")
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
        print(f"  ✅ Proveedor: Proveedor Prueba Final - Botones")
        print(f"  ✅ Total: $0")
        print(f"  💡 Ahora puedes probar los botones de acciones en el navegador")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    crear_compra_prueba_final()



