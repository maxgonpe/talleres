# 📅 CONTADOR DE DÍAS EN EL TALLER - Pizarra

## ✅ IMPLEMENTACIÓN COMPLETADA

Se ha agregado un **contador visual de días** en la pizarra de trabajos para saber cuánto tiempo lleva cada vehículo en el taller.

---

## 🎯 Funcionalidad

### **Cálculo Automático:**

```python
Si estado != 'entregado':
    días = HOY - fecha_inicio
    
Si estado == 'entregado':
    días = fecha_fin - fecha_inicio
    (deja de contar, muestra días totales que estuvo)
```

### **Visualización:**

El badge muestra:
- "Hoy" (si es 0 días)
- "1 día" (si es 1 día)
- "X días" (si es más de 1)

---

## 🎨 Colores Semánticos

El badge cambia de color según los días:

```
🟢 Verde (0-2 días)    = Reciente, normal
🟡 Amarillo (3-5 días) = Atención, tiempo medio
🔴 Rojo (6+ días)      = Alerta, mucho tiempo
⚫ Gris (Entregado)    = Ya no cuenta, trabajo terminado
```

### **Animación:**
- ✅ Los badges activos (no entregados) tienen efecto **pulse**
- ✅ Los badges entregados NO tienen animación (estáticos)

---

## 📊 Ejemplo Visual

### **Pizarra:**
```
┌────────────────────────────────────────┐
│           🟡 INICIADO                  │
├────────────────────────────────────────┤
│ 🚗 ABC-123 - Juan Pérez                │
│    📅 2 días  [████░░░░] 25%           │
├────────────────────────────────────────┤
│ 🚗 XYZ-789 - María López               │
│    📅 7 días  [██░░░░░░] 15%           │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│           🔵 TRABAJANDO                │
├────────────────────────────────────────┤
│ 🚙 DEF-456 - Pedro González            │
│    📅 4 días  [██████░░] 75%           │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│           🟢 COMPLETADO                │
├────────────────────────────────────────┤
│ 🚕 GHI-789 - Ana Martínez              │
│    📅 3 días  [████████] 100%          │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│           ⚫ ENTREGADO                 │
├────────────────────────────────────────┤
│ 🚐 JKL-012 - Carlos Rojas              │
│    📅 5 días  [████████] 100%          │
│    (contador detenido)                 │
└────────────────────────────────────────┘
```

---

## 🔧 Implementación Técnica

### **1. Modelo (models.py):**

```python
@property
def dias_en_taller(self):
    """Calcula días desde inicio hasta hoy (o hasta fin si entregado)"""
    if estado == 'entregado' and fecha_fin:
        return (fecha_fin - fecha_inicio).days
    else:
        return (hoy - fecha_inicio).days

@property
def dias_en_taller_texto(self):
    """Retorna texto formateado"""
    if dias == 0: return "Hoy"
    elif dias == 1: return "1 día"
    else: return "X días"
```

### **2. Template (pizarra_partial.html):**

HTML de cada card:
```html
<span class="placa-chile">ABC-123</span>
<strong>Juan Pérez</strong>
<span class="dias-taller pocos/medios/muchos/entregado">
    📅 2 días
</span>
```

CSS con colores:
```css
.dias-taller.pocos    → Verde (0-2 días)
.dias-taller.medios   → Amarillo (3-5 días)  
.dias-taller.muchos   → Rojo (6+ días)
.dias-taller.entregado → Gris (sin animación)
```

---

## 💡 Beneficios

### **Para el Taller:**
- ✅ **Control visual inmediato** de tiempos
- ✅ **Identificar trabajos retrasados** (badge rojo)
- ✅ **Priorizar atención** a vehículos con más días
- ✅ **Métricas de eficiencia** (cuánto se tarda en promedio)

### **Para el Cliente:**
- ✅ **Transparencia** sobre tiempo de servicio
- ✅ **Expectativas claras** al ver días transcurridos

---

## 📍 Ubicación

**URL:** `http://localhost:8000/car/pizarra/`

O desde el panel principal/menú: "📋 Pizarra"

---

## 🎯 Casos de Uso

### **Caso 1: Identificar trabajos urgentes**
- Mirar la pizarra
- Buscar badges rojos (6+ días)
- Priorizar esos trabajos

### **Caso 2: Informar al cliente**
- Cliente pregunta: "¿Cuánto lleva mi auto?"
- Ver pizarra
- Responder con exactitud: "Lleva 4 días"

### **Caso 3: Métricas**
- Revisar trabajos entregados
- Ver cuántos días tardaron en promedio
- Mejorar procesos

---

## 🎨 Semáforo Visual

```
┌─────────────────────────────────┐
│ 0-2 días:  🟢 Verde  (Normal)   │
│ 3-5 días:  🟡 Amarillo (Medio)  │
│ 6+ días:   🔴 Rojo (Alerta)     │
│ Entregado: ⚫ Gris (Finalizado) │
└─────────────────────────────────┘
```

---

## 📁 Archivos Modificados

```
✏️ car/models.py
   - Agregadas propiedades: dias_en_taller, dias_en_taller_texto

✏️ car/templates/car/pizarra_partial.html
   - CSS para badges de días
   - Badges en los 4 estados
   - Colores semánticos
   - Animación pulse
```

---

## 🧪 Cómo Probar

1. **Ir a la pizarra**: `http://localhost:8000/car/pizarra/`
2. **Verificar** que cada vehículo muestre:
   - Placa
   - Cliente
   - **Badge de días** (📅 X días)
   - Barra de progreso

3. **Verificar colores**:
   - Verde si lleva 0-2 días
   - Amarillo si lleva 3-5 días
   - Rojo si lleva 6+ días
   - Gris si está entregado

4. **Verificar animación**:
   - Badges deben tener efecto pulse
   - Excepto los entregados (estáticos)

---

## ✅ Características

- ✅ **Automático** - Se calcula en tiempo real
- ✅ **Visual** - Colores semánticos
- ✅ **Preciso** - Cuenta días exactos
- ✅ **Inteligente** - Se detiene al entregar
- ✅ **Animado** - Efecto pulse llamativo
- ✅ **Responsive** - Se ve bien en móvil

---

## 🔄 Actualización Automática

El contador se actualiza:
- ✅ **Cada vez que se recarga** la pizarra
- ✅ **Automáticamente** (no necesita configuración)
- ✅ **Para todos los trabajos** en todas las columnas

---

## 📊 Métricas Posibles

Con esta información puedes:
- Ver promedio de días por trabajo
- Identificar cuellos de botella
- Mejorar tiempos de entrega
- Establecer SLAs (ej: máximo 5 días)

---

**¡Implementado y listo para usar!** 🎉

**Fecha:** Octubre 27, 2025  
**Estado:** ✅ COMPLETADO

