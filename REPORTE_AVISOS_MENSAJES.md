# 📋 REPORTE DE REVISIÓN: Avisos y Mensajes Globalizados

**Fecha:** 14 de Diciembre, 2025  
**Sistema:** Taller Mecánico (car)  
**Variables Globales:** `ver_avisos` y `ver_mensajes`

---

## ✅ ESTADO GENERAL

### Variables Globales Implementadas
- ✅ `ver_avisos` y `ver_mensajes` disponibles en TODOS los templates (context processor)
- ✅ Context processor configurado en `settings.py`
- ✅ Variables accesibles como `{% if ver_avisos %}` en templates

---

## 📊 ESTADÍSTICAS

### Vistas con Mensajes
- **views.py**: 159 mensajes encontrados, 99 con `if config.ver_mensajes` ✅
- **views_compras.py**: 13 mensajes encontrados, 13 con `if config.ver_mensajes` ✅
- **views_pos.py**: 9 mensajes encontrados, 7 con `if config.ver_mensajes` ⚠️
- **views_bonos.py**: 15 mensajes encontrados, 11 con `if config.ver_mensajes` ⚠️
- **views_vehiculos.py**: 4 mensajes encontrados, 4 con `if config.ver_mensajes` ✅

### Templates con confirm()
- **Total archivos con confirm()**: 31 archivos
- **Con ver_avisos implementado**: ~28 archivos ✅
- **Sin ver_avisos**: ~3 archivos ⚠️

### Templates *_confirm_delete.html
- **Total**: 10 archivos
- **Con auto-submit implementado**: 10 archivos ✅

---

## ⚠️ PROBLEMAS ENCONTRADOS

### 1. VISTAS - Mensajes sin `ver_mensajes`

#### views.py (60 mensajes sin protección)
- **Línea 969**: `messages.success` - "Repuesto quitado del diagnóstico" ❌
- **Línea 988**: `messages.success` - "Cantidad actualizada" ❌
- **Línea 1003**: `messages.success` - "Acción quitada del diagnóstico" ❌
- **Línea 2242**: `messages.success` - "Observaciones guardadas" ✅ (tiene ver_mensajes)
- **Línea 2255**: `messages.success` - "Kilometraje guardado" ✅ (tiene ver_mensajes)
- **Línea 2263**: `messages.success` - "Kilometraje eliminado" ✅ (tiene ver_mensajes)
- **Línea 2298**: `messages.success` - "Mecánicos asignados" ✅ (tiene ver_mensajes)
- **Línea 2322**: `messages.success` - "Acción agregada al trabajo" ✅ (tiene ver_mensajes)
- **Línea 2392**: `messages.success` - "Acciones agregadas al trabajo" ✅ (tiene ver_mensajes)
- **Línea 2450**: `messages.success` - "Acción marcada como completada/pendiente" ✅ (tiene ver_mensajes)
- **Línea 2466**: `messages.success` - "Cantidad actualizada" ✅ (tiene ver_mensajes)
- **Línea 2484**: `messages.success` - "Precio actualizado" ✅ (tiene ver_mensajes)
- **Línea 2497**: `messages.success` - "Acción eliminada" (del trabajo) ❌
- **Línea 2524**: `messages.success` - "Repuesto agregado al trabajo" ❌
- **Línea 2556**: `messages.success` - "Repuesto externo agregado" ❌
- **Línea 2627-2647**: `messages.success` - "Repuestos agregados" (múltiples) ❌
- **Línea 2677**: `messages.success` - "Cantidad actualizada" (repuesto) ❌
- **Línea 2739**: `messages.success` - "Cantidad actualizada" (repuesto) ❌
- **Línea 2746**: `messages.success` - "Repuesto eliminado" ❌
- **Línea 2756**: `messages.success` - "Repuesto eliminado" ❌
- **Línea 2814**: `messages.success` - "Repuestos agregados al trabajo" ❌
- **Línea 2878**: `messages.success` - "Insumos agregados al trabajo" ❌
- Y muchos más...

**Total aproximado sin protección en views.py: ~60 mensajes**

#### views_pos.py (2 mensajes sin protección)
- **Línea 265**: `messages.error` - "No hay items en el carrito" ❌
- **Línea 584**: `messages.error` - "No hay items en el carrito" ❌

#### views_bonos.py (4 mensajes sin protección)
- **Línea 145**: `messages.error` - "Mecánico no encontrado" ❌
- **Línea 147**: `messages.error` - "Error al guardar configuración" ❌
- **Línea 261**: `messages.error` - "El monto debe ser mayor a cero" ❌
- **Línea 360**: `messages.error` - "Debe proporcionar un motivo" ❌
- **Línea 394**: `messages.error` - "No existe excepción" ❌

### 2. TEMPLATES - confirm() sin `ver_avisos`

#### Casos encontrados:

1. **ingreso-movil.html (línea 3703)**
   ```javascript
   if (confirm('¿Estás seguro de guardar el diagnóstico sin agregar repuestos ni insumos?...'))
   ```
   ❌ **PROBLEMA**: Tiene `{% if ver_avisos %}` duplicado, pero el confirm está mal estructurado

2. **ingreso.html (línea 3703)**
   ```javascript
   if (confirm('¿Estás seguro de guardar el diagnóstico sin agregar repuestos ni insumos?...'))
   ```
   ❌ **PROBLEMA**: Mismo problema que ingreso-movil.html

3. **trabajo_detalle_nuevo.html (líneas 1623, 3008)**
   ```javascript
   if (confirm('¿Eliminar esta foto?')) {  // línea 1623
   if (!confirm(`¿Agregar "${nombre}" al trabajo?`)) {  // línea 3008
   ```
   ❌ **PROBLEMA**: Línea 1623 tiene ver_avisos pero está mal estructurado (ya corregido antes)
   ❌ **PROBLEMA**: Línea 3008 NO tiene ver_avisos

4. **netgogo_console.html (línea 391)**
   ```javascript
   if (confirm('¿Deseas limpiar el chat y comenzar una nueva sesión?')) {
   ```
   ❌ **PROBLEMA**: NO tiene ver_avisos (pero es un caso especial de consola IA)

5. **busqueda_externa_repuestos.html (línea 395)**
   ```javascript
   if (confirm('¿Estás seguro de que quieres limpiar el historial?')) {
   ```
   ✅ **CORRECTO**: Tiene `{% if ver_avisos %}` implementado

6. **pos/procesar_venta.html (línea 267)**
   ```javascript
   if (!confirm('¿Confirmar esta venta?')) {
   ```
   ✅ **CORRECTO**: Tiene `{% if ver_avisos %}` implementado

7. **pos/procesar_cotizacion.html (línea 329)**
   ```javascript
   if (!confirm('¿Generar esta cotización?')) {
   ```
   ✅ **CORRECTO**: Tiene `{% if ver_avisos %}` implementado

8. **pos/configuracion.html (línea 337)**
   ```javascript
   if (!confirm('¿Guardar la configuración?')) {
   ```
   ✅ **CORRECTO**: Tiene `{% if ver_avisos %}` implementado

### 3. TEMPLATES *_confirm_delete.html

✅ **TODOS CORRECTOS**: Los 10 archivos tienen:
- `id="deleteForm"` en el formulario
- Script de auto-submit si `ver_avisos = False`

### 4. DeleteView (Class-Based Views)

✅ **TODOS CORRECTOS**: Los 6 DeleteView tienen:
- Override de `get()` para ver_avisos
- Override de `delete()` para ver_mensajes

### 5. JavaScript Externo

✅ **plano-interactivo.js**: 
- Usa `window.ver_avisos` correctamente
- Variable declarada en templates antes de cargar el script

---

## 📝 RESUMEN DE PROBLEMAS

### 🔴 CRÍTICOS (Deben corregirse)

1. **views.py**: ~60 mensajes sin `if config.ver_mensajes:`
   - Principalmente en acciones de trabajo (agregar, modificar, eliminar repuestos/acciones)
   - Mensajes de error también deberían respetar ver_mensajes

2. **views_pos.py**: 2 mensajes de error sin protección

3. **views_bonos.py**: 5 mensajes de error sin protección

4. **trabajo_detalle_nuevo.html**: 
   - Línea 3008: confirm sin ver_avisos para "Agregar al trabajo"

5. **ingreso-movil.html / ingreso.html**: 
   - Línea 3703: confirm mal estructurado (duplicado `{% if ver_avisos %}`)

### 🟡 MENORES (Opcionales)

1. **netgogo_console.html**: confirm sin ver_avisos (pero es consola IA, puede ser intencional)

---

## ✅ LO QUE ESTÁ BIEN

1. ✅ Context processor funcionando
2. ✅ Templates *_confirm_delete.html todos correctos
3. ✅ DeleteView todos correctos
4. ✅ La mayoría de templates con confirm() tienen ver_avisos
5. ✅ La mayoría de mensajes en vistas principales tienen ver_mensajes
6. ✅ JavaScript externo (plano-interactivo.js) correcto

---

## 🎯 RECOMENDACIONES

### Prioridad ALTA
1. Envolver los ~60 mensajes restantes en views.py con `if config.ver_mensajes:`
2. Corregir los 2 mensajes en views_pos.py
3. Corregir los 5 mensajes en views_bonos.py
4. Corregir trabajo_detalle_nuevo.html línea 3008
5. Corregir ingreso-movil.html e ingreso.html línea 3703

### Prioridad BAJA
1. Considerar si netgogo_console.html necesita ver_avisos (consola IA)

---

## 📈 COBERTURA ACTUAL

- **Templates con confirm()**: ~90% implementado ✅
- **Vistas con messages**: ~75% implementado ⚠️
- **DeleteView**: 100% implementado ✅
- **Templates confirm_delete**: 100% implementado ✅

---

**Total de problemas encontrados**: ~67 casos que necesitan corrección






