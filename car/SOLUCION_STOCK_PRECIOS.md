# 🛠️ Solución: Sistema Unificado de Stock y Precios

## 📋 **Problemas Identificados y Solucionados**

### **1. Problemas de Indefinición en Datos**
- ✅ **Campos con valores por defecto problemáticos eliminados de búsquedas**
- ✅ **Filtros mejorados para excluir registros con datos indefinidos**

### **2. Sistema de Stock Unificado**
- ✅ **Tabla maestra `Repuesto` como fuente única de verdad para stock**
- ✅ **Sincronización automática con `RepuestoEnStock`**
- ✅ **Eliminación de inconsistencias entre tablas**

### **3. Sistema de Precios con Factor de Margen Automático**
- ✅ **Cálculo automático de precios usando promedio ponderado**
- ✅ **Factor de margen automático basado en historial del producto**
- ✅ **Manejo inteligente de productos nuevos (30% margen por defecto)**
- ✅ **Actualización automática sin intervención manual**

## 🔧 **Cambios Implementados**

### **Modelo Repuesto (`car/models.py`)**

#### **Nuevos Métodos:**
```python
def actualizar_stock_y_precio(self, cantidad_entrada, precio_compra, precio_venta_nuevo=None):
    """
    Actualiza stock y precio usando promedio ponderado con factor de margen automático
    
    Fórmulas:
    - Precio Costo: (Stock_Anterior × Precio_Anterior + Cantidad_Nueva × Precio_Nuevo) / Stock_Total
    - Factor Margen: Precio_Venta_Anterior / Precio_Costo_Anterior
    - Precio Venta: Nuevo_Precio_Costo × Factor_Margen
    """
```

#### **Propiedades Unificadas:**
```python
@property
def stock_total(self):
    """Obtiene el stock total - SIEMPRE desde la tabla maestra Repuesto"""
    return self.stock or 0

@property
def stock_disponible(self):
    """Obtiene el stock disponible (total - reservado)"""
    return self.stock_total - total_reservado
```

### **Búsquedas Mejoradas**

#### **POS (`car/views_pos.py`):**
```python
repuestos = Repuesto.objects.filter(
    # ... criterios de búsqueda ...
).exclude(
    # Excluir registros con valores por defecto problemáticos
    Q(oem__in=['oem', '']) |
    Q(referencia__in=['no-tiene', '']) |
    Q(origen_repuesto__in=['sin-origen', '']) |
    Q(marca_veh__in=['xxx', 'xxxx', '']) |
    Q(tipo_de_motor__in=['zzzzzz', 'zzzz', '']) |
    Q(marca__in=['general', ''])
)
```

#### **Compras (`car/views_compras.py`):**
```python
repuestos = Repuesto.objects.filter(
    # ... criterios de búsqueda ...
).exclude(
    Q(oem__in=['oem', '']) |
    Q(referencia__in=['no-tiene', '']) |
    Q(marca__in=['general', ''])
)
```

### **Sistema de Compras Actualizado**

#### **CompraItem.recibir_item():**
```python
def recibir_item(self, usuario=None):
    """Marca el item como recibido y actualiza el stock usando precio promedio ponderado"""
    # Usar el nuevo método de actualización
    resultado = repuesto.actualizar_stock_y_precio(
        cantidad_entrada=self.cantidad,
        precio_compra=self.precio_unitario
    )
```

## 🎯 **Ejemplo de Funcionamiento**

### **Escenario:**
- Producto X: Stock = 2, Precio costo = $10, Precio venta = $13
- Compra nueva: +3 unidades a $15 c/u

### **Cálculo Automático:**
1. **Factor de margen actual:** $13 ÷ $10 = 1.3 (30% margen)
2. **Nuevo precio costo:** (2×$10 + 3×$15) ÷ 5 = $13
3. **Nuevo precio venta:** $13 × 1.3 = $16.9

### **Resultado:**
- ✅ Stock final = 5 unidades
- ✅ Precio costo = $13 (promedio ponderado)
- ✅ Precio venta = $16.9 (factor de margen aplicado)
- ✅ **Sin intervención manual necesaria**

## 🚀 **Scripts de Utilidad**

### **1. Limpiar Datos Indefinidos:**
```bash
python manage.py limpiar_datos_indefinidos --dry-run  # Ver qué se limpiaría
python manage.py limpiar_datos_indefinidos           # Ejecutar limpieza
```

### **2. Probar Sistema de Precios:**
```bash
python manage.py probar_precio_promedio --repuesto-id 123
```

### **3. Probar Factor de Margen:**
```bash
python manage.py probar_factor_margen --repuesto-id 123
```

## 📊 **Beneficios de la Solución**

1. **✅ Consistencia de Datos:** Una sola fuente de verdad para stock
2. **✅ Precios Inteligentes:** Factor de margen automático
3. **✅ Búsquedas Limpias:** Sin resultados con datos indefinidos
4. **✅ Sincronización Automática:** RepuestoEnStock siempre actualizado
5. **✅ Auditoría Completa:** Movimientos de stock registrados
6. **✅ Cero Intervención Manual:** Todo automático

## 🔄 **Flujo de Trabajo Actualizado**

1. **Compra de Repuestos:**
   - Se crea CompraItem con cantidad y precio
   - Al marcar como "recibido" → actualiza stock y precios automáticamente

2. **Búsqueda en POS:**
   - Solo muestra repuestos con datos válidos
   - Stock y precios consistentes desde tabla maestra

3. **Ventas:**
   - Stock se reduce desde tabla maestra
   - Precios actualizados automáticamente

## ⚠️ **Consideraciones Importantes**

- **Migración de Datos:** Ejecutar script de limpieza antes de usar
- **Backup:** Hacer respaldo antes de ejecutar cambios masivos
- **Pruebas:** Probar con datos de prueba antes de producción

## 🎉 **Resultado Final**

- ✅ **Stock unificado y consistente**
- ✅ **Precios calculados automáticamente**
- ✅ **Búsquedas sin datos indefinidos**
- ✅ **Sistema robusto y escalable**
