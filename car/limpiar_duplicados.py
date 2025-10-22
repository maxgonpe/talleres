
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
