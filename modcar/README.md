# ModTaller - Sistema Modular de Gestión de Talleres Mecánicos

## 📋 Descripción

ModTaller es una reestructuración modular del sistema de gestión de talleres mecánicos, dividido en apps independientes pero integradas que facilitan el mantenimiento, escalabilidad y personalización del sistema.

## 🗂️ Estructura del Proyecto

```
modcar/
├── manage.py
├── modtaller/
│   ├── __init__.py
│   ├── settings.py          # Configuración principal del proyecto
│   ├── urls.py              # URLs principales
│   ├── wsgi.py
│   ├── asgi.py
│   ├── static/
│   │   └── css/
│   │       ├── variables-globales.css      # Variables CSS globales
│   │       ├── templates-especificos.css   # Estilos por template
│   │       └── README.md                    # Documentación CSS
│   └── templates/
│       └── base.html                        # Template base
│
├── core/                    # App principal - Modelos base
│   ├── models.py            # Cliente_Taller, Vehiculo, Componente, Accion
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── diagnosticos/            # App de diagnósticos
│   ├── models.py           # Diagnostico, DiagnosticoComponenteAccion, DiagnosticoRepuesto
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── trabajos/               # App de trabajos
│   ├── models.py           # Trabajo, TrabajoAccion, TrabajoRepuesto, TrabajoAbono, TrabajoAdicional
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── inventario/              # App de inventario
│   ├── models.py           # Repuesto, RepuestoEnStock, StockMovimiento, RepuestoExterno
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── punto_venta/            # App de punto de venta (POS)
│   ├── models.py           # SesionVenta, CarritoItem, VentaPOS, Cotizacion
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── compras/                 # App de compras
│   ├── models.py           # Compra, CompraItem
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── usuarios/                # App de usuarios y permisos
│   ├── models.py           # Mecanico
│   ├── views.py
│   ├── urls.py
│   ├── middleware.py       # PermisosMiddleware
│   └── ...
│
├── bonos/                   # App de bonos de mecánicos
│   ├── models.py           # ConfiguracionBonoMecanico, BonoGenerado, PagoMecanico
│   ├── views.py
│   ├── urls.py
│   └── ...
│
├── configuracion/           # App de configuración del taller
│   ├── models.py           # AdministracionTaller
│   ├── views.py
│   ├── urls.py
│   ├── context_processors.py
│   └── ...
│
└── estadisticas/            # App de estadísticas
    ├── models.py           # RegistroEvento, ResumenTrabajo
    ├── views.py
    ├── urls.py
    └── ...
```

## 🎯 Apps del Sistema

### 1. **core** - Modelos Base
Modelos compartidos entre todas las apps:
- `Cliente_Taller`: Clientes del taller
- `Vehiculo`: Vehículos
- `Componente`: Componentes del vehículo (estructura jerárquica)
- `Accion`: Acciones que se pueden realizar
- `ComponenteAccion`: Precios de mano de obra
- `VehiculoVersion`: Versiones de vehículos para compatibilidad

### 2. **diagnosticos** - Diagnósticos
- `Diagnostico`: Diagnósticos de vehículos
- `DiagnosticoComponenteAccion`: Acciones en diagnósticos
- `DiagnosticoRepuesto`: Repuestos en diagnósticos

### 3. **trabajos** - Trabajos
- `Trabajo`: Trabajos realizados
- `TrabajoAccion`: Acciones del trabajo
- `TrabajoRepuesto`: Repuestos del trabajo
- `TrabajoAbono`: Abonos/pagos parciales
- `TrabajoAdicional`: Conceptos adicionales
- `TrabajoFoto`: Fotos del trabajo

### 4. **inventario** - Inventario
- `Repuesto`: Repuestos del inventario
- `RepuestoEnStock`: Stock detallado por depósito
- `StockMovimiento`: Movimientos de stock
- `RepuestoExterno`: Referencias de repuestos externos
- `ComponenteRepuesto`: Relación componente-repuesto
- `RepuestoAplicacion`: Compatibilidad de repuestos

### 5. **punto_venta** - Punto de Venta (POS)
- `SesionVenta`: Sesiones de venta
- `CarritoItem`: Items del carrito
- `VentaPOS`: Ventas realizadas
- `VentaPOSItem`: Items de venta
- `Cotizacion`: Cotizaciones
- `CotizacionItem`: Items de cotización
- `ConfiguracionPOS`: Configuración del POS

### 6. **compras** - Compras
- `Compra`: Compras de repuestos
- `CompraItem`: Items de compra

### 7. **usuarios** - Usuarios y Permisos
- `Mecanico`: Mecánicos con roles y permisos
- Middleware de permisos

### 8. **bonos** - Bonos de Mecánicos
- `ConfiguracionBonoMecanico`: Configuración de bonos
- `BonoGenerado`: Bonos generados
- `PagoMecanico`: Pagos a mecánicos
- `ExcepcionBonoTrabajo`: Excepciones de bonos

### 9. **configuracion** - Configuración del Taller
- `AdministracionTaller`: Configuración general del taller
- Context processor para configuración

### 10. **estadisticas** - Estadísticas
- `RegistroEvento`: Registro de eventos para auditoría
- `ResumenTrabajo`: Resúmenes calculados de trabajos

## 🎨 Sistema CSS Modular

El proyecto incluye un sistema CSS modular con variables globales configurables de forma específica para cada template.

### Archivos CSS:
- `variables-globales.css`: Variables globales y por tema
- `templates-especificos.css`: Estilos específicos por template

### Características:
- Variables configurables por template
- Soporte para múltiples temas (Piedra, Sand, Plum, Cyan, Sage, Sky)
- Fácil personalización de colores y estilos
- Documentación completa en `modtaller/static/css/README.md`

## 🚀 Instalación y Configuración

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Crear superusuario

```bash
python manage.py createsuperuser
```

### 4. Ejecutar servidor

```bash
python manage.py runserver
```

## 📝 Migración desde el Proyecto Anterior

Para migrar datos desde el proyecto anterior (`car`):

1. Copiar la base de datos SQLite si es necesario
2. Ejecutar las migraciones
3. Verificar que todos los modelos estén correctamente migrados

## 🔧 Desarrollo

### Agregar una nueva app

1. Crear la estructura de la app:
```bash
python manage.py startapp nueva_app
```

2. Agregar a `INSTALLED_APPS` en `settings.py`

3. Crear modelos, vistas y URLs

4. Incluir URLs en `modtaller/urls.py`

### Personalizar CSS

Ver documentación en `modtaller/static/css/README.md`

## 📚 Documentación Adicional

- **CSS Modular**: `modtaller/static/css/README.md`
- **Estructura de Apps**: Ver README de cada app (si existe)

## 🎯 Ventajas de la Estructura Modular

1. **Separación de responsabilidades**: Cada app tiene su propia funcionalidad
2. **Mantenibilidad**: Fácil de mantener y actualizar
3. **Escalabilidad**: Fácil agregar nuevas funcionalidades
4. **Reutilización**: Modelos y vistas pueden reutilizarse
5. **Testing**: Más fácil de testear cada módulo por separado
6. **CSS Modular**: Sistema de estilos centralizado y configurable

## 📞 Soporte

Para más información sobre el sistema, consultar la documentación de cada app o el código fuente.



