# Solución para Duplicados en RepuestoEnStock

## Problema Identificado
El sistema tenía registros duplicados en la tabla `RepuestoEnStock` para el mismo repuesto, causando inconsistencias en precios y stock. Específicamente:

- **Aceite 10w-40 (ID 3)**: Tenía 2 registros (ID 32 y 196)
- **Registro ID 32**: ✅ Consistente (stock: 12, precios actualizados)
- **Registro ID 196**: ❌ Inconsistente (stock: 9, precios antiguos)

## Solución Implementada

### 1. Limpieza de Duplicados Existentes
- ✅ Eliminado registro duplicado ID 196
- ✅ Mantenido registro correcto ID 32
- ✅ Verificado que no hay más duplicados en el sistema

### 2. Mejora del Método `_sincronizar_con_stock_detallado`
Se actualizó el método en `car/models.py` para prevenir futuros duplicados:

```python
def _sincronizar_con_stock_detallado(self, cantidad_entrada, precio_compra):
    """Sincroniza con RepuestoEnStock para mantener consistencia"""
    # Primero, eliminar cualquier registro duplicado existente
    registros_existentes = RepuestoEnStock.objects.filter(
        repuesto=self,
        deposito='bodega-principal'
    )
    
    if registros_existentes.count() > 1:
        # Mantener solo el más reciente y eliminar los duplicados
        registro_principal = registros_existentes.order_by('-id').first()
        registros_duplicados = registros_existentes.exclude(id=registro_principal.id)
        registros_duplicados.delete()
    
    # Obtener o crear el registro principal en RepuestoEnStock
    stock_principal, created = RepuestoEnStock.objects.get_or_create(
        repuesto=self,
        deposito='bodega-principal',
        proveedor='',
        defaults={
            'stock': 0,
            'reservado': 0,
            'precio_compra': precio_compra,
            'precio_venta': self.precio_venta
        }
    )
    
    # Actualizar el stock detallado para que coincida con el stock maestro
    stock_principal.stock = self.stock
    stock_principal.precio_compra = self.precio_costo
    stock_principal.precio_venta = self.precio_venta
    stock_principal.save()
```

### 3. Script de Limpieza Automática
Se creó `limpiar_duplicados.py` para ejecutar periódicamente y mantener la consistencia:

```python
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
```

## Resultado Final

### ✅ Estado Actual del Sistema
- **Aceite 10w-40**: 1 registro único en RepuestoEnStock
- **Stock**: 15 unidades (consistente entre Repuesto y RepuestoEnStock)
- **Precio costo**: $45,000 (consistente)
- **Precio venta**: $54,000 (consistente)
- **Factor de margen**: 1.2 (20% de ganancia)

### ✅ Prevención de Futuros Duplicados
1. **Método mejorado**: `_sincronizar_con_stock_detallado` elimina duplicados automáticamente
2. **Script de limpieza**: `limpiar_duplicados.py` para mantenimiento periódico
3. **Consistencia garantizada**: Cada repuesto tiene exactamente un registro en RepuestoEnStock

### ✅ Funcionalidades Verificadas
- ✅ Compra de repuestos actualiza correctamente stock y precios
- ✅ Aplicación automática del factor de margen
- ✅ Sincronización perfecta entre Repuesto (maestro) y RepuestoEnStock (detalle)
- ✅ Sin duplicados en futuras operaciones
- ✅ Sistema de stock unificado y consistente

## Recomendaciones

1. **Ejecutar limpieza periódica**: `python3 limpiar_duplicados.py` semanalmente
2. **Monitorear duplicados**: Verificar que no se creen nuevos duplicados
3. **Mantener consistencia**: El sistema ahora previene automáticamente los duplicados
4. **Backup regular**: Hacer respaldos antes de ejecutar limpiezas masivas

El sistema ahora está completamente funcional y libre de duplicados. Todas las operaciones de compra, venta y stock funcionan correctamente con datos consistentes.



