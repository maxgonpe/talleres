# 📐 Estructura del Proyecto ModTaller

## 🎯 Resumen

Este documento describe la estructura modular del proyecto ModTaller, una reestructuración completa del sistema de gestión de talleres mecánicos dividido en apps independientes pero integradas.

## 📦 Apps del Sistema

### 1. **core** - Modelos Base
**Ubicación**: `/core/`

**Responsabilidad**: Modelos compartidos entre todas las apps

**Modelos**:
- `Cliente_Taller`: Clientes del taller con RUT como PK
- `Vehiculo`: Vehículos de los clientes
- `Componente`: Componentes del vehículo (estructura jerárquica)
- `Accion`: Acciones que se pueden realizar sobre componentes
- `ComponenteAccion`: Precios de mano de obra por componente-acción
- `VehiculoVersion`: Versiones de vehículos para compatibilidad

**Dependencias**: Ninguna (app base)

---

### 2. **diagnosticos** - Diagnósticos
**Ubicación**: `/diagnosticos/`

**Responsabilidad**: Gestión de diagnósticos de vehículos

**Modelos**:
- `Diagnostico`: Diagnósticos de vehículos
- `DiagnosticoComponenteAccion`: Acciones en diagnósticos
- `DiagnosticoRepuesto`: Repuestos en diagnósticos

**Dependencias**: `core`, `inventario`

---

### 3. **trabajos** - Trabajos
**Ubicación**: `/trabajos/`

**Responsabilidad**: Gestión de trabajos realizados

**Modelos**:
- `Trabajo`: Trabajos realizados (clonados desde diagnósticos)
- `TrabajoAccion`: Acciones del trabajo
- `TrabajoRepuesto`: Repuestos del trabajo
- `TrabajoAbono`: Abonos/pagos parciales
- `TrabajoAdicional`: Conceptos adicionales o descuentos
- `TrabajoFoto`: Fotos del trabajo

**Dependencias**: `core`, `diagnosticos`, `inventario`, `usuarios`

---

### 4. **inventario** - Inventario
**Ubicación**: `/inventario/`

**Responsabilidad**: Gestión de inventario de repuestos

**Modelos**:
- `Repuesto`: Repuestos del inventario
- `RepuestoEnStock`: Stock detallado por depósito
- `StockMovimiento`: Movimientos de stock (auditoría)
- `RepuestoExterno`: Referencias de repuestos externos
- `ComponenteRepuesto`: Relación componente-repuesto
- `RepuestoAplicacion`: Compatibilidad de repuestos con vehículos

**Dependencias**: `core`

---

### 5. **punto_venta** - Punto de Venta (POS)
**Ubicación**: `/punto_venta/`

**Responsabilidad**: Sistema de punto de venta

**Modelos**:
- `SesionVenta`: Sesiones de venta
- `CarritoItem`: Items del carrito
- `VentaPOS`: Ventas realizadas
- `VentaPOSItem`: Items de venta
- `Cotizacion`: Cotizaciones
- `CotizacionItem`: Items de cotización
- `ConfiguracionPOS`: Configuración del POS

**Dependencias**: `core`, `inventario`, `usuarios`

---

### 6. **compras** - Compras
**Ubicación**: `/compras/`

**Responsabilidad**: Gestión de compras de repuestos

**Modelos**:
- `Compra`: Compras de repuestos
- `CompraItem`: Items de compra

**Dependencias**: `core`, `inventario`, `usuarios`

---

### 7. **usuarios** - Usuarios y Permisos
**Ubicación**: `/usuarios/`

**Responsabilidad**: Gestión de usuarios y permisos

**Modelos**:
- `Mecanico`: Mecánicos con roles y permisos

**Middleware**:
- `PermisosMiddleware`: Middleware de permisos

**Dependencias**: `core`

---

### 8. **bonos** - Bonos de Mecánicos
**Ubicación**: `/bonos/`

**Responsabilidad**: Sistema de bonos e incentivos

**Modelos**:
- `ConfiguracionBonoMecanico`: Configuración de bonos por mecánico
- `BonoGenerado`: Bonos generados
- `PagoMecanico`: Pagos a mecánicos
- `ExcepcionBonoTrabajo`: Excepciones de bonos

**Dependencias**: `usuarios`, `trabajos`

---

### 9. **configuracion** - Configuración del Taller
**Ubicación**: `/configuracion/`

**Responsabilidad**: Configuración general del taller

**Modelos**:
- `AdministracionTaller`: Configuración general del taller

**Context Processors**:
- `configuracion_taller`: Agrega configuración al contexto

**Dependencias**: `core`

---

### 10. **estadisticas** - Estadísticas
**Ubicación**: `/estadisticas/`

**Responsabilidad**: Estadísticas y análisis

**Modelos**:
- `RegistroEvento`: Registro de eventos para auditoría
- `ResumenTrabajo`: Resúmenes calculados de trabajos

**Dependencias**: `core`, `trabajos`, `diagnosticos`

---

## 🎨 Sistema CSS Modular

**Ubicación**: `/modtaller/static/css/`

**Archivos**:
- `variables-globales.css`: Variables globales y por tema
- `templates-especificos.css`: Estilos específicos por template

**Características**:
- Variables configurables por template
- Soporte para múltiples temas
- Fácil personalización

**Documentación**: Ver `modtaller/static/css/README.md`

---

## 🔗 Dependencias entre Apps

```
core (base)
  ├── diagnosticos
  │     └── trabajos
  ├── inventario
  │     ├── diagnosticos
  │     ├── trabajos
  │     ├── punto_venta
  │     └── compras
  ├── usuarios
  │     ├── trabajos
  │     ├── punto_venta
  │     ├── compras
  │     └── bonos
  ├── configuracion
  └── estadisticas
        ├── trabajos
        └── diagnosticos
```

---

## 📝 Notas Importantes

1. **Modelos compartidos**: Los modelos en `core` son compartidos y no deben tener dependencias de otras apps
2. **Importaciones circulares**: Evitar importaciones circulares entre apps
3. **URLs**: Cada app tiene su propio archivo `urls.py` que se incluye en `modtaller/urls.py`
4. **Templates**: Cada app tiene su carpeta `templates/app_name/`
5. **Static files**: Cada app puede tener su carpeta `static/app_name/`

---

## 🚀 Próximos Pasos

1. Completar modelos de todas las apps
2. Migrar vistas desde el proyecto anterior
3. Migrar templates
4. Configurar URLs
5. Probar funcionalidad completa



