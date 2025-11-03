# 📋 PROPUESTA: Reorganización de ingreso.html con Pestañas e Insumos

## 🎯 OBJETIVOS

1. ✅ Agregar funcionalidad de **Insumos** (igual que en trabajo_detalle)
2. ✅ Reorganizar el template en **pestañas** para mejor UX móvil
3. ✅ Asegurar que **insumos se sumen con repuestos** en cálculos
4. ✅ Mantener toda la funcionalidad existente

---

## 📱 ESTRUCTURA DE PESTAÑAS PROPUESTA

### **Pestaña 1: Cliente y Vehículo** 🏠
- Datos del cliente (API de búsqueda)
- Selección de vehículo existente
- Datos del vehículo (API de placa)
- **Siempre visible, no requiere scroll largo**

### **Pestaña 2: Componentes** 🔧
- Acordeón de componentes (columna izquierda)
- Plano interactivo SVG (columna derecha)
- Lista de componentes seleccionados debajo
- **Función principal del diagnóstico**

### **Pestaña 3: Componentes Seleccionados** ✅
- Resumen de componentes elegidos
- Permite quitar componentes
- **Vista consolidada**

### **Pestaña 4: Acciones** ⚡
- Acciones aplicadas por componente
- Checkboxes de selección
- Cálculo de mano de obra total
- **Sin cambios en funcionalidad**

### **Pestaña 5: Repuestos** 📦
- Búsqueda en inventario propio
- Búsqueda en proveedores externos
- Lista de repuestos agregados
- Tabla de repuestos (igual que ahora)
- **Incluir insumos aquí también (lista combinada)**

### **Pestaña 6: Insumos** 🧰 **[NUEVA]**
- Búsqueda amplia (sin filtros de compatibilidad)
- Checkboxes para seleccionar insumos
- Campo de cantidad
- Lista de insumos disponibles
- Botón "Agregar Insumos"
- **Se guardan igual que repuestos, aparecen en pestaña Repuestos**

### **Pestaña 7: Observaciones** 📝
- Campo de descripción del problema
- Campo de notas adicionales
- **Formulario simple**

### **Fuera de Pestañas:**
- ✅ Botones "Guardar" y "Regresar" 
- ✅ Siempre visibles en la parte inferior
- ✅ Fijos en móvil (sticky)

---

## 🔄 FLUJO DE INSUMOS

1. Usuario va a pestaña **"Insumos"**
2. Busca insumos (ej: "aceite", "filtro")
3. Selecciona insumos con checkboxes
4. Ajusta cantidades
5. Hace clic en **"Agregar Insumos"**
6. Los insumos se **agregan como repuestos** en el diagnóstico
7. Aparecen en la pestaña **"Repuestos"** automáticamente
8. Se suman en los totales junto con repuestos

### **Diferencia entre Repuestos e Insumos:**

| Aspecto | Repuestos | Insumos |
|---------|-----------|---------|
| Búsqueda | Con filtros de compatibilidad | Sin filtros (amplia) |
| Uso | Específicos del vehículo | Cualquier repuesto del inventario |
| Almacenamiento | Tabla RepuestoDiagnostico | Tabla RepuestoDiagnostico (mismo lugar) |
| Visualización | Pestaña Repuestos | Pestaña Repuestos (combinados) |

**Nota:** En esencia, los insumos son repuestos, pero con búsqueda sin restricciones.

---

## 📐 DISEÑO RESPONSIVE

### **Móvil (< 768px):**
- Pestañas en scroll horizontal
- Cada pestaña ocupa 100% del ancho
- Botones fijos en la parte inferior
- Inputs grandes y fáciles de tocar
- Espaciado generoso

### **Tablet/Desktop (≥ 768px):**
- Pestañas en línea horizontal
- Más espacio para contenido
- Grid de 2 columnas donde sea apropiado

---

## 🎨 ESTRUCTURA HTML PROPUESTA

```html
<form id="form-ingreso">
  <!-- Navegación de Pestañas -->
  <ul class="nav nav-tabs" id="ingresoTabs">
    <li><a href="#tab-cliente">Cliente</a></li>
    <li><a href="#tab-componentes">Componentes</a></li>
    <li><a href="#tab-seleccionados">Seleccionados</a></li>
    <li><a href="#tab-acciones">Acciones</a></li>
    <li><a href="#tab-repuestos">Repuestos</a></li>
    <li><a href="#tab-insumos">Insumos</a></li>
    <li><a href="#tab-observaciones">Observaciones</a></li>
  </ul>

  <!-- Contenido de Pestañas -->
  <div class="tab-content">
    <!-- Pestaña 1: Cliente y Vehículo -->
    <div id="tab-cliente" class="tab-pane active">...</div>
    
    <!-- Pestaña 2: Componentes -->
    <div id="tab-componentes" class="tab-pane">...</div>
    
    <!-- Pestaña 3: Componentes Seleccionados -->
    <div id="tab-seleccionados" class="tab-pane">...</div>
    
    <!-- Pestaña 4: Acciones -->
    <div id="tab-acciones" class="tab-pane">...</div>
    
    <!-- Pestaña 5: Repuestos -->
    <div id="tab-repuestos" class="tab-pane">...</div>
    
    <!-- Pestaña 6: Insumos (NUEVA) -->
    <div id="tab-insumos" class="tab-pane">...</div>
    
    <!-- Pestaña 7: Observaciones -->
    <div id="tab-observaciones" class="tab-pane">...</div>
  </div>

  <!-- Botones fuera de pestañas -->
  <div class="form-actions-sticky">
    <button type="submit" class="btn btn-primary">Guardar</button>
    <a href="javascript:history.back()" class="btn btn-secondary">Regresar</a>
  </div>
</form>
```

---

## 🔧 IMPLEMENTACIÓN TÉCNICA

### **JavaScript Necesario:**

1. **Sistema de pestañas** (Bootstrap 5 o custom)
2. **Búsqueda de insumos** (`buscarInsumos()` - ya existe)
3. **Agregar insumos** (`agregarInsumos()` - adaptar para diagnóstico)
4. **Sincronización:** Insumos agregados → aparecen en pestaña Repuestos

### **Backend:**

1. ✅ Endpoint `/car/repuestos/buscar-insumos/` ya existe
2. ✅ View `buscar_insumos` ya existe
3. ⚠️ **Modificar `ingreso_view`** para procesar `insumos_json`
4. ⚠️ **Guardar insumos como repuestos** en `RepuestoDiagnostico`

---

## ✅ VENTAJAS

- ✅ **Mejor UX móvil:** No hay scroll infinito
- ✅ **Organización clara:** Cada sección en su pestaña
- ✅ **Funcionalidad completa:** Insumos operativos
- ✅ **Integración:** Insumos = Repuestos (mismo modelo)
- ✅ **Mantenible:** Código organizado

---

## ⚠️ CONSIDERACIONES

1. **Validación:** Asegurar que al menos se complete Cliente + Vehículo antes de guardar
2. **Persistencia:** Mantener selecciones al cambiar de pestaña
3. **Cálculos:** Total repuestos = repuestos + insumos
4. **Estados:** Indicar pestañas completadas/por completar

---

## 🚀 PLAN DE IMPLEMENTACIÓN

1. ✅ Crear estructura de pestañas HTML
2. ✅ Mover contenido actual a pestañas
3. ✅ Agregar pestaña de Insumos con funcionalidad completa
4. ✅ Adaptar JavaScript de insumos para diagnóstico
5. ✅ Modificar view para procesar insumos_json
6. ✅ Asegurar que insumos se sumen con repuestos
7. ✅ Estilos responsive
8. ✅ Testing completo

---

## 📝 NOTAS FINALES

- Los insumos son **técnicamente repuestos** con búsqueda amplia
- Se almacenan en la **misma tabla** (`RepuestoDiagnostico`)
- Se **suman en totales** junto con repuestos
- La diferencia es solo en la **experiencia de búsqueda**

