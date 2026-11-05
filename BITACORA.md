# Bitacora Tecnica - Talleres

## 2026-11-04 - Linea base del sistema

### Objetivo del proyecto

Sistema Django para controlar la operacion de un taller mecanico: clientes,
vehiculos, diagnosticos, ordenes de trabajo, repuestos, stock, compras, ventas,
POS, bonos para mecanicos y seguimiento del trabajo.

El objetivo de la evolucion es conservar la logica de negocio validada,
simplificar la arquitectura, eliminar duplicaciones y mejorar la experiencia de
uso para que el sistema sea claro e intuitivo.

### Estado tecnico actual

- Django 5.2.5 sobre Python 3.11.
- Una aplicacion principal `car` con 44 modelos en un unico `models.py`.
- `views.py` supera las 5.000 lineas y convive con varios modulos de vistas.
- Existen servicios separados para diagnosticos, stock, compras, ventas y
  stock de trabajos, pero la logica aun esta repartida entre modelos, vistas y
  servicios.
- El desarrollo usa SQLite por defecto mediante `settings.py`.
- El proyecto ya tiene soporte parcial para PostgreSQL mediante variables de
  entorno y un `Dockerfile` con Gunicorn.
- `start.sh` ejecuta migraciones y `collectstatic` al iniciar el contenedor.
- Todavia no hay una composicion Docker versionada en este proyecto para la
  aplicacion y su base PostgreSQL persistente.
- El frontend combina Bootstrap, CSS propio, varias hojas de estilos historicas,
  JavaScript directo, PWA y versiones movil/escritorio de algunas pantallas.

### Funcionalidad identificada

- Autenticacion y perfiles de mecanico, vendedor y administrador.
- Clientes y vehiculos/equipos.
- Ingreso de diagnosticos con componentes, acciones y repuestos.
- Aprobacion de diagnosticos y creacion de trabajos.
- Seguimiento de estados, mecanicos, fotos, abonos y entrega.
- Inventario, compatibilidad de repuestos y movimientos de stock.
- Compras y recepcion de items.
- Venta legacy y POS moderno, incluyendo cotizaciones.
- Bonos, pagos y cierres de periodos para mecanicos.
- Exportaciones PDF/Excel, estadisticas y tracking publico.
- Panel configurable, temas visuales y funciones experimentales de IA.

### Hallazgos prioritarios

1. `DEBUG` y `ALLOWED_HOSTS` quedaron corregidos en
   `car/myproject/settings.py`: ahora dependen de `DJANGO_DEBUG` y
   `DJANGO_ALLOWED_HOSTS`, con valores locales seguros por defecto.
2. El middleware agrega permisos al request, pero la proteccion efectiva de
   cada operacion sensible debe revisarse vista por vista.
3. Hay dos modelos de cliente (`Cliente` y `Cliente_Taller`) y dos conceptos de
   vehiculo (`Vehiculo` y `VehiculoVersion`) coexistiendo.
4. Hay dos sistemas de ventas: `Venta`/`VentaItem` y `VentaPOS`/`VentaPOSItem`.
5. El stock se mantiene en `Repuesto.stock` y `RepuestoEnStock.stock`, con
   reglas repartidas y posibles inconsistencias por proveedor/deposito.
6. La logica de diagnosticos, stock y ventas esta distribuida entre modelos,
   vistas y servicios, lo que aumenta el riesgo de corregir un flujo y dejar
   otro con reglas diferentes.
7. Hay rutas, templates y flujos duplicados para ingreso, diagnosticos,
   vehiculos y pantallas movil/escritorio.
8. Existe una eliminacion de vehiculo por GET bajo una condicion de
   configuracion, lo que debe convertirse en una operacion POST protegida.
9. El repositorio no versiona las migraciones porque `.gitignore` excluye
   `car/car/migrations/`; se debe decidir una estrategia que no mezcle archivos
   locales del servidor con el codigo compartido.
10. El `.gitignore` excluye todos los Markdown y algunos archivos de codigo;
    la bitacora queda explicitamente permitida, pero las reglas deben
    normalizarse en una tarea posterior.

### Decisiones de trabajo

- `Cliente_Taller` es el modelo oficial de clientes. `Cliente` se considera
  legacy y se revisara para retiro cuando se confirme que no quedan flujos que
  lo utilicen.
- `Vehiculo` y `VehiculoVersion` forman parte intencional del diseno actual;
  no se trataran como duplicacion hasta entender su responsabilidad exacta.
- El middleware de permisos se mantiene sin cambios. Fue probado en produccion
  y su endurecimiento se evaluara despues de desplegar esta version y observar
  necesidades reales de seguridad.
- Los dos modelos de ventas/POS se revisaran como un posible arreglo historico
  que pudo haber duplicado el modelo para resolver una necesidad puntual.
- Las rutas y templates duplicados, junto con la eliminacion insegura por GET,
  quedan como trabajo de correccion posterior.
- El servidor de produccion y el entorno local pueden tener configuraciones,
  secretos, bases de datos, media y otros archivos propios. Esos elementos no
  deben entrar en Git ni bloquear los pull.
- Las migraciones Django son diferentes de la configuracion local: describen
  cambios de esquema y normalmente deben compartir la misma historia entre
  entornos. Antes de cambiar el `.gitignore`, se revisara si las migraciones
  excluidas son realmente locales o si contienen el historial necesario para
  migrar de SQLite a PostgreSQL.
- No se eliminaran modelos, rutas ni templates hasta identificar su uso y
  disponer de pruebas de regresion.
- La migracion a PostgreSQL se hara con una base persistente y variables de
  entorno fuera del repositorio.
- La configuracion Docker de STIHL y Condocdat se usara como referencia cuando
  sea necesario validar Traefik, redes externas, volumenes y despliegue.
- Cada cambio relevante se registrara en Git y en esta bitacora.
- La simplificacion priorizara primero seguridad, integridad de datos y claridad
  del flujo operativo; despues se abordara la renovacion visual.

### Orden de trabajo propuesto

1. Normalizar `.gitignore`, migraciones, secretos y archivos generados.
2. Crear una linea base reproducible del entorno local y pruebas.
3. Corregir configuracion segura de Django sin cambiar la logica funcional.
4. Definir los modelos canonicos de cliente, vehiculo, venta y stock.
5. Consolidar la logica de negocio en servicios claros y transaccionales.
6. Eliminar rutas, templates y codigo duplicado con pruebas de regresion.
7. Simplificar la interfaz y unificar la experiencia movil/escritorio.
8. Preparar Docker Compose con PostgreSQL persistente y despliegue Traefik.
9. Ejecutar migracion de datos, pruebas de aceptacion y documentar rollback.

### Registro de commits de referencia

- `ed16d1a` - borrado de archivos innecesarios.
- `0d5c2f5` - depuracion y refactorizacion general con pruebas principales.

La bitacora se actualizara despues de cada bloque funcional o decision tecnica.

### Cierre de jornada

- Se completo la primera auditoria tecnica y el inventario inicial de limpieza.
- Se corrigio la lectura de `DEBUG` y `ALLOWED_HOSTS` desde variables de entorno.
- Se movieron los candidatos confirmados a `otros/inventario_limpieza/`.
- `python manage.py check` fue correcto.
- Las 23 pruebas de `car` fueron correctas.
- No se hicieron cambios sobre middleware, modelos de negocio ni rutas activas.
- El proximo trabajo retomara desde la revision funcional y los cambios
  estructurales significativos, manteniendo esta linea base como referencia.

## 2026-11-05 - Primer refactor del flujo de diagnostico

- Se creo el commit de linea base `3fdd00e` antes de modificar la logica.
- Se comprobo que la aprobacion ya delegaba la creacion del trabajo al servicio
  `car/services/diagnostics.py`.
- Se elimino la duplicacion de eventos y aprobacion entre
  `guardar_aprobar_y_crear_ot` y `aprobar_diagnostico` mediante el helper privado
  `_aprobar_diagnostico_y_registrar` en `car/views.py`.
- No se modificaron middleware, modelos, rutas ni reglas de negocio.
- `python manage.py check`: correcto.
- `python manage.py test car`: 23 pruebas correctas.

## 2026-11-04 - Inventario inicial de rutas y limpieza

### Rutas revisadas

Se reviso `car/car/urls.py` y `car/myproject/urls.py`. Las rutas estan
organizadas en estos grupos:

- Entrada: login, logout, ingreso de diagnostico, ingreso rapido, voz y pruebas.
- Componentes, acciones y precios de mano de obra.
- Diagnosticos, sugerencia de repuestos, aprobacion y exportaciones.
- Clientes legacy y clientes oficiales del taller.
- Vehiculos operativos y catalogo de compatibilidad (`VehiculoVersion`).
- Trabajos, historial, PDF y pizarra.
- Repuestos, compatibilidad e inventario.
- POS, carrito, ventas, cotizaciones y anulaciones.
- Compras, recepcion e items AJAX.
- Bonos, pagos, excepciones y cierres de periodo.
- Administracion, usuarios, permisos y estadisticas.
- Tracking publico.
- APIs de vehiculos, compras, compatibilidad, repuestos externos y OpenAI.
- Consolas experimentales `netgogo` y `netgogo2`.

### Archivos Python con camino activo

No se identificaron archivos `.py` claramente solitarios para mover:

- `agent.py` es usado por `views_ia.py`.
- `algoritmo_relacion.py` es usado por `views_algoritmo.py` y su URL.
- `views_api.py`, `views_ia.py`, `views_vehiculos.py`, `views_compras.py`,
  `views_estadisticas.py` y `views_bonos.py` estan conectados desde URLs.
- `services/*.py` son usados por vistas, modelos o servicios relacionados.
- `management/commands/*.py` son comandos Django invocables aunque no tengan
  imports directos.
- `scripts/backup.sh` y `scripts/verify_backup.sh` son herramientas operativas,
  no archivos abandonados.
- `start.sh`, `Dockerfile`, WSGI y ASGI son parte del arranque o despliegue.

### Archivos movidos a `otros/`

Se movieron, conservando una estructura separada en
`otros/inventario_limpieza/`:

- Templates sin referencia activa: `diagnostico2_pdf.html`, `ingreso.html` e
  `ingreso-movil.html`.
- Documentacion: `car/OPERACIONES.md` y `car/car/static/css/README.md`.
- Recursos experimentales o intermedios: `static/images/no/`,
  `static/images/transforma/` y `static/images/pruebas.svg`.
- Variantes graficas no referenciadas: `Logo1 (copia 1).svg`, `Logo21.png`,
  `Logo22.png` y `Logo31.svg`.

El movimiento es reversible desde `otros/inventario_limpieza/` si el check o
una prueba funcional demuestra que alguno aun era necesario.

### Archivos que no deben moverse ahora

- `db.sqlite3`: es la base local ignorada; moverla romperia el desarrollo local
  mientras SQLite siga siendo el valor por defecto.
- `__pycache__/` y `*.pyc`: deben ignorarse y limpiarse, no formar parte de
  `otros/`.
- `media/` y `trabajos/fotos/`: son datos de usuario o de prueba; requieren una
  politica de datos separada, no una mudanza manual sin respaldo.
- Templates referenciados desde vistas, URLs o includes.
- Comandos de gestion con nombres `probar`, `limpiar`, `verificar` o `auditar`:
  pueden ser herramientas de mantenimiento validas aunque no se ejecuten en
  cada arranque.

### Proximo paso de limpieza

Antes de mover candidatos se hara una segunda comprobacion: buscar referencias
en codigo, templates, JavaScript y configuracion, ejecutar las pruebas y revisar
el arbol en el navegador cuando el archivo sea visual. Los movimientos se
haran en un cambio separado y reversible, registrando cada ruta original y
nueva.
