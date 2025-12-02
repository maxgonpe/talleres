# 🎨 Sistema de Temas Centralizado

## 📋 Descripción

Sistema completo de gestión de temas para el taller mecánico que centraliza todos los colores, contrastes y estilos en variables CSS reutilizables.

## 🗂️ Estructura de Archivos

```
static/css/
├── variables.css          # Variables centralizadas para todos los temas
├── contrast.css           # Clases de contraste garantizado
├── themes.css             # Sistema de temas automático
├── theme-integration.css  # Integración completa del sistema
└── README.md              # Esta documentación

static/js/
└── theme-manager.js       # Gestor automático de temas
```

## 🎯 Características

### ✅ **8 Temas Completos**
- **Oscuros**: Piedra, Charcoal, Forest, Plum
- **Claros**: Cyan, Sand, Sage, Sky

### ✅ **Contraste Garantizado**
- Texto legible en cualquier tema
- Fondos con contraste adecuado
- Bordes y sombras consistentes

### ✅ **Aplicación Automática**
- Se aplica automáticamente a todos los elementos
- No requiere clases manuales
- Herencia automática de estilos

### ✅ **Accesibilidad**
- Soporte para `prefers-reduced-motion`
- Soporte para `prefers-contrast: high`
- Soporte para `prefers-color-scheme`

## 🚀 Uso

### 1. **Incluir en el Template Base**

```html
<!-- En base.html -->
<link rel="stylesheet" href="{% static 'css/theme-integration.css' %}">
<script src="{% static 'js/theme-manager.js' %}"></script>
```

### 2. **Aplicar Clases de Integración**

```html
<!-- Aplicar a contenedores principales -->
<div class="pos-integration">
  <!-- Contenido del POS -->
</div>

<div class="dashboard-integration">
  <!-- Contenido del Dashboard -->
</div>

<div class="compras-integration">
  <!-- Contenido de Compras -->
</div>
```

### 3. **Usar Clases de Contraste**

```html
<!-- Para elementos específicos -->
<div class="card-contrast">
  <!-- Card con contraste garantizado -->
</div>

<div class="modal-contrast">
  <!-- Modal con contraste garantizado -->
</div>

<form class="form-contrast">
  <!-- Formulario con contraste garantizado -->
</form>
```

## 🎨 Variables Disponibles

### **Colores Principales**
```css
--bg-primary          /* Fondo principal */
--bg-secondary        /* Fondo secundario */
--bg-card             /* Fondo de cards */
--text-primary        /* Texto principal */
--text-secondary      /* Texto secundario */
--text-muted          /* Texto atenuado */
--border-color        /* Color de bordes */
--accent              /* Color de acento */
```

### **Colores de Estado**
```css
--success-bg          /* Fondo de éxito */
--success-text        /* Texto de éxito */
--warning-bg          /* Fondo de advertencia */
--warning-text        /* Texto de advertencia */
--danger-bg           /* Fondo de peligro */
--danger-text         /* Texto de peligro */
--info-bg             /* Fondo de información */
--info-text           /* Texto de información */
```

### **Transiciones y Sombras**
```css
--transition          /* Transición estándar */
--transition-fast     /* Transición rápida */
--transition-slow     /* Transición lenta */
--shadow-sm           /* Sombra pequeña */
--shadow-md           /* Sombra media */
--shadow-lg           /* Sombra grande */
--shadow-xl           /* Sombra extra grande */
```

## 🔧 Clases Disponibles

### **Clases de Integración**
- `.pos-integration` - Para el POS
- `.dashboard-integration` - Para el Dashboard
- `.compras-integration` - Para Compras
- `.repuestos-integration` - Para Repuestos

### **Clases de Contraste**
- `.card-contrast` - Cards con contraste garantizado
- `.modal-contrast` - Modales con contraste garantizado
- `.form-contrast` - Formularios con contraste garantizado
- `.btn-contrast` - Botones con contraste garantizado

### **Clases de Texto**
- `.text-contrast-high` - Texto de alto contraste
- `.text-contrast-medium` - Texto de contraste medio
- `.text-contrast-low` - Texto de bajo contraste

### **Clases de Fondo**
- `.bg-contrast-high` - Fondo de alto contraste
- `.bg-contrast-medium` - Fondo de contraste medio
- `.bg-contrast-low` - Fondo de bajo contraste

## 🎯 JavaScript API

### **Cambiar Tema**
```javascript
// Cambiar tema desde JavaScript
changeTheme('piedra');
changeTheme('cyan');
changeTheme('forest');
```

### **Obtener Tema Actual**
```javascript
// Obtener tema actual
const currentTheme = getCurrentTheme();

// Verificar tipo de tema
const isDark = isDarkTheme();
const isLight = isLightTheme();
```

### **Aplicar Contraste Automático**
```javascript
// Aplicar contraste automático
applyAutoContrast();
```

## 🔍 Debugging

### **Activar Modo Debug**
```html
<!-- Agregar clase debug al body -->
<body class="debug-integration">
```

### **Verificar Variables**
```javascript
// Verificar variables CSS
console.log(getComputedStyle(document.documentElement).getPropertyValue('--bg-primary'));
```

## 📱 Responsive

### **Breakpoints**
- Mobile: `< 768px`
- Tablet: `768px - 1024px`
- Desktop: `> 1024px`

### **Accesibilidad**
- `prefers-reduced-motion: reduce` - Reduce animaciones
- `prefers-contrast: high` - Aumenta contraste
- `prefers-color-scheme: dark` - Sugiere temas oscuros

## 🚀 Implementación

### **Paso 1: Incluir Archivos**
```html
<link rel="stylesheet" href="{% static 'css/theme-integration.css' %}">
<script src="{% static 'js/theme-manager.js' %}"></script>
```

### **Paso 2: Aplicar Clases**
```html
<div class="pos-integration">
  <!-- Contenido -->
</div>
```

### **Paso 3: Verificar Funcionamiento**
```javascript
// Verificar que el sistema funciona
console.log('Tema actual:', getCurrentTheme());
console.log('Es tema oscuro:', isDarkTheme());
```

## 🎨 Personalización

### **Agregar Nuevo Tema**
1. Agregar variables en `variables.css`
2. Crear clase `.theme-nuevo`
3. Agregar al objeto `themes` en `theme-manager.js`

### **Modificar Colores**
1. Cambiar variables en `variables.css`
2. Los cambios se aplican automáticamente

### **Agregar Clases Personalizadas**
1. Crear en `contrast.css`
2. Usar variables del sistema
3. Aplicar automáticamente

## 🔧 Mantenimiento

### **Verificar Contraste**
- Usar herramientas de accesibilidad
- Verificar en todos los temas
- Probar con `prefers-contrast: high`

### **Actualizar Temas**
- Modificar variables en `variables.css`
- Verificar en todos los temas
- Probar transiciones

### **Optimizar Rendimiento**
- Minificar CSS en producción
- Usar `prefers-reduced-motion`
- Evitar transiciones innecesarias

## 📚 Recursos

- [MDN CSS Variables](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [WCAG Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [CSS Custom Properties](https://css-tricks.com/a-complete-guide-to-custom-properties/)

## 🐛 Problemas Comunes

### **Contraste Insuficiente**
- Verificar variables de tema
- Aplicar clases de contraste
- Usar `prefers-contrast: high`

### **Transiciones Lentas**
- Verificar `prefers-reduced-motion`
- Optimizar transiciones
- Usar `transition-duration`

### **Temas No Aplican**
- Verificar orden de CSS
- Verificar JavaScript
- Verificar localStorage

## 📞 Soporte

Para problemas o preguntas:
1. Verificar documentación
2. Revisar console de errores
3. Verificar variables CSS
4. Contactar al desarrollador









