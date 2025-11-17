# REVISIÓN DE TEMPLATES CON ESTILOS CSS LOCALES
## Sistema de Talleres Mecánicos

**Fecha de revisión:** 2025
**Estado:** Todos los templates heredan de `centralized-colors.css` pero tienen estilos locales específicos

---

## RESUMEN EJECUTIVO

**Total de templates con estilos locales:** 11

Todos los templates utilizan las variables CSS globales (`var(--*)`) del archivo `centralized-colors.css`, pero definen estilos locales adicionales para:
- Layouts específicos del template
- Componentes únicos (wizards, tabs, cards especiales)
- Comportamientos interactivos (animaciones, estados hover)
- Adaptaciones móviles específicas

---

## LISTADO DETALLADO

### 1. `panel_definitivo.html`
**Ubicación:** `car/car/templates/car/panel_definitivo.html`

**Razón del CSS local:**
Layout específico del panel principal con sistema de tabs, cards de estadísticas, grid de acciones y sección de pizarra completa.

**Estilos locales definidos:**
- `.panel-container` - Contenedor principal del panel
- `.panel-header` - Header con gradiente
- `.nav-tabs` - Sistema de navegación por tabs
- `.nav-tabs .nav-link` - Estilos de enlaces de tabs
- `.tab-content` - Contenido de las tabs
- `.stats-row` - Grid de estadísticas
- `.stat-card` - Cards de estadísticas con hover
- `.stat-number` - Números grandes en cards
- `.stat-label` - Etiquetas de estadísticas
- `.actions-grid` - Grid de acciones rápidas
- `.action-card` - Cards de acciones con hover
- `.action-icon` - Iconos de acciones
- `.action-title` - Títulos de acciones
- `.action-description` - Descripciones de acciones
- `.pizarra-section` - Sección completa de pizarra
- `.pizarra-header` - Header de pizarra
- `.pizarra-title` - Título de pizarra
- `.pizarra-grid` - Grid de celdas de pizarra
- `.pizarra-cell` - Celdas individuales de pizarra
- `.pizarra-cell-header` - Headers de celdas

**Notas:** Usa variables globales pero define layout específico del dashboard principal.

---

### 2. `ingreso_fusionado.html`
**Ubicación:** `car/car/templates/car/ingreso_fusionado.html`

**Razón del CSS local:**
Wizard de 3 pasos con barra de progreso visual, sistema fusionado de componentes/acciones y panel de resumen.

**Estilos locales definidos:**
- `.wizard-progress` - Contenedor de progreso del wizard
- `.wizard-steps` - Contenedor de pasos
- `.wizard-step` - Paso individual
- `.wizard-step-circle` - Círculo numerado del paso
- `.wizard-step.active .wizard-step-circle` - Estado activo
- `.wizard-step.done .wizard-step-circle` - Estado completado
- `.wizard-step.pending .wizard-step-circle` - Estado pendiente
- `.wizard-step-label` - Etiqueta del paso
- `.wizard-pane` - Panel de contenido del paso
- `.wizard-pane.active` - Panel activo
- `.componente-item` - Item de componente
- `.componente-item.active` - Componente seleccionado
- `.componente-header` - Header del componente
- `.acciones-panel` - Panel de acciones
- `.acciones-panel.show` - Panel visible
- `.accion-item` - Item de acción
- `.accion-item.seleccionada` - Acción seleccionada
- `.accion-item .accion-head` - Header de acción
- `.accion-item .accion-controls` - Controles de acción
- `.accion-item .accion-subtotal` - Subtotal de acción
- `.resumen-card` - Card de resumen
- `.total-mano-obra` - Total de mano de obra
- `.wizard-navigation` - Navegación del wizard (sticky)

**Notas:** Incluye media queries para responsive. Define todo el sistema visual del wizard fusionado.

---

### 3. `ingreso_movil_voz.html`
**Ubicación:** `car/car/templates/car/ingreso_movil_voz.html`

**Razón del CSS local:**
Mismo wizard que `ingreso_fusionado.html` + sistema completo de control por voz con botón flotante, banner de estado, toast de feedback y animaciones.

**Estilos locales definidos:**
- **Todos los estilos de `ingreso_fusionado.html`** (wizard completo)
- `.voice-control-container` - Contenedor del control de voz (fixed)
- `.voice-btn` - Botón de micrófono flotante
- `.voice-btn.listening` - Estado escuchando (rojo con animación)
- `.voice-btn.processing` - Estado procesando (amarillo con rotación)
- `.voice-status-banner` - Banner de estado (fixed top)
- `.voice-feedback-toast` - Toast de feedback
- `.voice-help-card` - Card de ayuda con comandos
- `@keyframes pulse` - Animación de pulso para micrófono
- `@keyframes spin` - Animación de rotación para procesamiento

**Notas:** Extiende `ingreso_fusionado.html` con funcionalidad de voz. Incluye animaciones CSS personalizadas.

---

### 4. `trabajo_detalle_nuevo.html`
**Ubicación:** `car/car/templates/car/trabajo_detalle_nuevo.html`

**Razón del CSS local:**
Página de detalle de trabajo con sistema de tabs personalizado, badges de estado, cards de información y botones de acción estilizados.

**Estilos locales definidos:**
- `.trabajo-container` - Contenedor principal
- `.trabajo-header` - Header con gradiente
- `.estado-badge` - Badge de estado base
- `.estado-iniciado` - Estado iniciado (amarillo)
- `.estado-trabajando` - Estado trabajando (azul)
- `.estado-completado` - Estado completado (verde)
- `.estado-entregado` - Estado entregado (gris)
- `.tab-container` - Contenedor de tabs
- `.tab-nav` - Navegación de tabs
- `.tab-btn` - Botón de tab
- `.tab-btn.active` - Tab activo
- `.tab-content` - Contenido de tab
- `.tab-content.active` - Contenido activo
- `.info-card` - Card de información
- `.info-row` - Fila de información
- `.info-label` - Etiqueta de información
- `.info-value` - Valor de información
- `.btn-action` - Botón de acción
- `.btn-mobile` - Botón móvil (full width)

**Notas:** Define sistema completo de tabs y estados visuales del trabajo.

---

### 5. `trabajo_detalle_movil.html`
**Ubicación:** `car/car/templates/car/trabajo_detalle_movil.html`

**Razón del CSS local:**
Versión móvil optimizada del detalle de trabajo con header fijo sticky, barra de progreso visual, tabs adaptados y botones grandes para uso táctil.

**Estilos locales definidos:**
- `.trabajo-movil-container` - Contenedor móvil
- `.trabajo-header-movil` - Header móvil (sticky)
- `.trabajo-header-movil h3` - Título del header
- `.trabajo-header-movil p` - Texto del header
- `.estado-badge-movil` - Badge de estado móvil
- `.estado-iniciado` - Estado iniciado
- `.estado-trabajando` - Estado trabajando
- `.estado-completado` - Estado completado
- `.estado-entregado` - Estado entregado
- `.progress-movil` - Barra de progreso móvil
- `.progress-fill-movil` - Relleno de progreso
- Estilos responsive específicos para móvil

**Notas:** Versión completamente adaptada para móvil con elementos sticky y tamaños aumentados.

---

### 6. `pos/pos_principal.html`
**Ubicación:** `car/car/templates/car/pos/pos_principal.html`

**Razón del CSS local:**
Punto de venta completo con sistema de búsqueda, resultados desplegables, carrito de compras y totales. Incluye estilos específicos para tema oscuro.

**Estilos locales definidos:**
- `.pos-container` - Contenedor del POS
- `.pos-header` - Header sticky del POS
- `.search-container` - Contenedor de búsqueda
- `.search-results` - Resultados de búsqueda (absolute)
- `body.theme-oscuro .search-results` - Resultados en tema oscuro
- `.search-item` - Item de resultado
- `body.theme-oscuro .search-item` - Item en tema oscuro
- `.search-item .fw-bold` - Texto en negrita
- `body.theme-oscuro .search-item .fw-bold` - Negrita en tema oscuro
- `.search-item .text-secondary` - Texto secundario
- `body.theme-oscuro .search-item .text-secondary` - Secundario en tema oscuro
- `.search-item:hover` - Hover de item
- `body.theme-oscuro .search-item:hover` - Hover en tema oscuro
- `.carrito-container` - Contenedor del carrito
- `.carrito-item` - Item del carrito
- `.item-info` - Información del item
- `.item-controls` - Controles del item
- `.quantity-input` - Input de cantidad
- `.price-input` - Input de precio
- `.total-container` - Contenedor de total (verde)
- `.btn-pos` - Botón del POS

**Notas:** Incluye muchos estilos específicos para tema oscuro con `body.theme-oscuro`. Sistema complejo de búsqueda y carrito.

---

### 7. `pos/dashboard.html`
**Ubicación:** `car/car/templates/car/pos/dashboard.html`

**Razón del CSS local:**
Dashboard del POS con grid de estadísticas, cards con bordes de color diferenciados y acciones rápidas con iconos.

**Estilos locales definidos:**
- `.dashboard-container` - Contenedor del dashboard
- `.dashboard-header` - Header con gradiente
- `.stats-grid` - Grid de estadísticas
- `.stat-card` - Card de estadística base
- `.stat-card:hover` - Hover de card
- `.stat-card.primary` - Card primaria (borde azul)
- `.stat-card.success` - Card éxito (borde verde)
- `.stat-card.warning` - Card advertencia (borde amarillo)
- `.stat-card.info` - Card información (borde azul claro)
- `.stat-card.danger` - Card peligro (borde rojo)
- `.stat-number` - Número grande de estadística
- `.stat-label` - Etiqueta de estadística
- `.quick-actions` - Acciones rápidas
- `.action-grid` - Grid de acciones
- `.action-btn` - Botón de acción
- `.action-btn:hover` - Hover de botón
- `.action-icon` - Icono de acción
- `.action-text` - Texto de acción

**Notas:** Sistema de cards con variantes de color por tipo. Grid responsive.

---

### 8. `pos/configuracion.html`
**Ubicación:** `car/car/templates/car/pos/configuracion.html`

**Razón del CSS local:**
Formulario de configuración con secciones separadas, inputs con focus personalizado y botones con gradientes hardcodeados.

**Estilos locales definidos:**
- `.config-container` - Contenedor de configuración
- `.config-header` - Header con gradiente gris
- `.config-form` - Formulario de configuración
- `.form-section` - Sección del formulario
- `.form-section:last-child` - Última sección
- `.section-title` - Título de sección
- `.form-label` - Etiqueta de formulario
- `.form-control` - Input de formulario
- `.form-select` - Select de formulario
- `.form-control:focus` - Focus de input
- `.form-select:focus` - Focus de select
- `.form-check-input` - Checkbox personalizado
- `.form-check-label` - Label de checkbox
- `.btn-save` - Botón guardar (gradiente verde hardcodeado)
- `.btn-save:hover` - Hover de guardar
- `.btn-cancel` - Botón cancelar (gradiente gris hardcodeado)
- `.btn-cancel:hover` - Hover de cancelar

**Notas:** **IMPORTANTE:** Usa gradientes hardcodeados (`#28a745`, `#6c757d`) en lugar de variables. Debería migrarse a variables globales.

---

### 9. `ingreso-pc.html`
**Ubicación:** `car/car/templates/car/ingreso-pc.html`

**Razón del CSS local:**
Formulario de ingreso para PC con secciones estilizadas, inputs con estados y botones personalizados.

**Estilos locales definidos:**
- `.ingreso-container` - Contenedor de ingreso
- `.ingreso-header` - Header con gradiente
- `.ingreso-header h2` - Título del header
- `.form-section` - Sección del formulario
- `.form-section h3` - Título de sección
- `.form-label` - Etiqueta de formulario
- `.form-control` - Input de formulario
- `.form-select` - Select de formulario
- `.form-control:focus` - Focus de input
- `.form-select:focus` - Focus de select
- `.form-control::placeholder` - Placeholder
- `.btn` - Botón base
- `.btn-primary` - Botón primario
- `.btn-primary:hover` - Hover primario
- `.btn-outline-primary` - Botón outline primario
- `.btn-outline-primary:hover` - Hover outline
- `.btn-success` - Botón éxito

**Notas:** Estilos estándar de formulario. Usa variables globales correctamente.

---

### 10. `ingreso-movil.html`
**Ubicación:** `car/car/templates/car/ingreso-movil.html`

**Razón del CSS local:**
Mismo formulario que `ingreso-pc.html` pero con tamaños de fuente aumentados para mejor legibilidad en móvil.

**Estilos locales definidos:**
- **Todos los estilos de `ingreso-pc.html`** (formulario completo)
- Ajustes adicionales:
  - `.form-label` - `font-size: 1.05rem` (aumentado de 1rem)
  - `.form-control` - `font-size: 1.05rem` (aumentado de 1rem)

**Notas:** Versión móvil con fuentes más grandes. Mismo layout que PC pero optimizado para pantallas táctiles.

---

### 11. `diagnostico_lista.html`
**Ubicación:** `car/car/templates/car/diagnostico_lista.html`

**Razón del CSS local:**
Lista de diagnósticos con sistema de tabs temporales (Hoy, Esta semana, Este mes, etc.) para filtrar por período.

**Estilos locales definidos:**
- `.tiempo-tabs` - Contenedor de tabs temporales
- `.tiempo-tab` - Tab temporal individual
- `.tiempo-tab:hover` - Hover de tab
- `.tiempo-tab.active` - Tab activo
- `.tiempo-tab .count` - Contador dentro del tab

**Notas:** Sistema simple de tabs para filtrado temporal. Usa variables globales correctamente.

---

## RESUMEN POR CATEGORÍA

### Layouts Específicos (2)
- `panel_definitivo.html` - Dashboard principal
- `pos/dashboard.html` - Dashboard POS

### Wizards/Progreso (2)
- `ingreso_fusionado.html` - Wizard fusionado
- `ingreso_movil_voz.html` - Wizard con voz

### Detalle con Tabs (2)
- `trabajo_detalle_nuevo.html` - Detalle desktop
- `trabajo_detalle_movil.html` - Detalle móvil

### Punto de Venta (2)
- `pos/pos_principal.html` - POS principal
- `pos/configuracion.html` - Configuración POS

### Formularios (2)
- `ingreso-pc.html` - Ingreso desktop
- `ingreso-movil.html` - Ingreso móvil

### Listas con Filtros (1)
- `diagnostico_lista.html` - Lista con tabs temporales

---

## OBSERVACIONES IMPORTANTES

### ✅ Buenas Prácticas
- Todos los templates usan variables CSS globales (`var(--*)`)
- Los estilos locales son específicos y justificados
- Se mantiene consistencia en nombres de clases
- Media queries se usan cuando es necesario

### ⚠️ Puntos de Atención

1. **`pos/configuracion.html`**
   - Usa gradientes hardcodeados (`#28a745`, `#6c757d`, `#667eea`) en lugar de variables
   - **Recomendación:** Migrar a variables globales para mantener consistencia

2. **`pos/pos_principal.html`**
   - Muchos estilos específicos para tema oscuro con `body.theme-oscuro`
   - **Recomendación:** Considerar mover estos estilos a `centralized-colors.css` si se usan en otros templates

3. **Duplicación de Estilos**
   - `ingreso-pc.html` e `ingreso-movil.html` tienen estilos casi idénticos
   - `ingreso_fusionado.html` e `ingreso_movil_voz.html` comparten el wizard
   - **Recomendación:** Considerar extraer estilos comunes a un archivo CSS compartido

---

## CONCLUSIÓN

Todos los templates están correctamente integrados con el sistema de variables CSS globales. Los estilos locales son necesarios y específicos para cada template, justificados por:
- Layouts únicos
- Componentes específicos
- Comportamientos interactivos
- Adaptaciones móviles

**Estado general:** ✅ Bueno - Los estilos locales son apropiados y no violan la arquitectura global.

---

**Documento generado automáticamente**
**Última actualización:** 2025



