# 📦 Archivos a Subir - Sistema de Repuestos Externos

## ✅ Sistema COMPLETO Implementado

Se implementó el sistema completo de referencias de repuestos externos, incluyendo:
- ✅ Búsqueda en proveedores chilenos (Mundo Repuestos, AutoPlanet)
- ✅ Extracción automática de datos desde URL
- ✅ Integración en Diagnóstico y Trabajo
- ✅ Visualización en PDFs y todas las vistas

---

## 📂 **ARCHIVOS A SUBIR AL SERVIDOR:**

### **1. Base de Datos y Modelos**
```
car/models.py
car/migrations/0034_agregar_repuesto_externo.py
car/migrations/0035_agregar_repuesto_externo_a_diagnostico.py
car/migrations/0036_agregar_repuesto_externo_a_trabajo.py
```

### **2. Administración**
```
car/admin.py
```

### **3. Vistas (Backend)**
```
car/views.py
```

### **4. URLs**
```
car/urls.py
```

### **5. Templates (Frontend)**
```
car/templates/car/ingreso.html
car/templates/car/trabajo_detalle_nuevo.html
car/templates/car/trabajo_pdf.html
car/templates/car/trabajo_lista.html
car/templates/car/busqueda_externa_repuestos.html
car/templates/car/bookmarklet_repuestos.html (NUEVO)
car/templates/car/agregar_repuesto_externo_rapido.html (NUEVO)
```

### **6. Documentación (Opcional)**
```
SISTEMA_REPUESTOS_EXTERNOS.md
ARCHIVOS_A_SUBIR_REPUESTOS_EXTERNOS.md (este archivo)
```

---

## 🚀 **PASOS PARA DESPLEGAR EN PRODUCCIÓN:**

### **Opción A: Usando Git (Recomendado)**

```bash
# 1. En tu máquina local (donde estás ahora)
cd /home/maxgonpe/talleres/car
git add .
git commit -m "Sistema de repuestos externos completo"
git push origin main

# 2. En el servidor de producción
cd /ruta/al/proyecto
git pull origin main

# 3. Activar entorno virtual
source env/bin/activate

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Reiniciar servidor
sudo systemctl restart gunicorn
# o si usas otro servidor:
# sudo systemctl restart uwsgi
# sudo service apache2 restart
```

### **Opción B: Subida Manual (FTP/SFTP)**

1. **Subir todos los archivos** listados arriba manteniendo la estructura de carpetas

2. **Conectar por SSH al servidor** y ejecutar:
```bash
cd /ruta/al/proyecto
source env/bin/activate
python manage.py migrate
sudo systemctl restart [tu-servidor]
```

---

## ⚙️ **COMANDOS IMPORTANTES EN EL SERVIDOR:**

```bash
# 1. Activar entorno virtual
source env/bin/activate

# 2. Aplicar migraciones (IMPORTANTE)
python manage.py migrate

# 3. Verificar que las migraciones se aplicaron
python manage.py showmigrations car

# 4. Reiniciar el servidor web
sudo systemctl restart gunicorn
# o
sudo systemctl restart uwsgi

# 5. (Opcional) Recolectar archivos estáticos
python manage.py collectstatic --noinput

# 6. (Opcional) Ver logs si hay errores
sudo tail -f /var/log/gunicorn/error.log
# o
sudo journalctl -u gunicorn -f
```

---

## 🎯 **NUEVAS FUNCIONALIDADES IMPLEMENTADAS:**

### **En Diagnóstico (Ingreso):**
1. Botón "🌐 Proveedores Externos"
2. Modal con 2 pestañas:
   - Buscar referencias guardadas
   - Guardar nueva referencia
3. Auto-extracción de datos desde URL
4. Búsqueda directa en proveedores
5. Agregado automático al diagnóstico

### **En Trabajo:**
1. Botón "🌐 Proveedores Externos" en pestaña Repuestos
2. Mismo modal con búsqueda y guardado
3. Agregado directo al trabajo
4. Visualización con icono 🌐

### **Visualización:**
- Lista de trabajos: Repuestos externos con 🌐
- Detalle del trabajo: Repuestos externos con 🌐
- PDF del trabajo: Repuestos externos con 🌐
- Todo completamente integrado

---

## 📱 **VERIFICACIÓN POST-DESPLIEGUE:**

Después de subir, verifica:

1. ✅ Las migraciones se ejecutaron correctamente
2. ✅ El botón "🌐 Proveedores Externos" aparece en Ingreso
3. ✅ El botón "🌐 Proveedores Externos" aparece en Trabajo
4. ✅ Puedes guardar referencias nuevas
5. ✅ Puedes buscar referencias guardadas
6. ✅ La extracción automática desde URL funciona
7. ✅ Los repuestos externos se muestran correctamente en PDFs
8. ✅ Los repuestos externos se copian al aprobar diagnósticos

---

## ⚠️ **IMPORTANTE - BACKUP:**

**Antes de aplicar las migraciones en producción:**

```bash
# Hacer backup de la base de datos
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json

# O si es SQLite:
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)

# O si es PostgreSQL:
pg_dump nombre_base_datos > backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## 🔧 **SOLUCIÓN DE PROBLEMAS:**

### Si hay error en las migraciones:
```bash
python manage.py showmigrations car
python manage.py migrate car --fake-initial
```

### Si los templates no se actualizan:
```bash
sudo systemctl restart gunicorn
# Limpiar caché del navegador (Ctrl+Shift+R)
```

### Si aparecen errores 500:
```bash
# Ver logs
sudo tail -f /var/log/gunicorn/error.log
# O
python manage.py runserver 0.0.0.0:8000 --settings=myproject.settings
```

---

## 📊 **CAMBIOS EN BASE DE DATOS:**

### Nuevas Tablas:
- `car_repuestoexterno` - Referencias de repuestos de proveedores externos

### Tablas Modificadas:
- `car_diagnosticorepuesto` - Nuevo campo `repuesto_externo_id` (nullable)
- `car_trabajorepuesto` - Nuevo campo `repuesto_externo_id` (nullable)
- Campos `repuesto_id` ahora son nullable en ambas tablas

---

## ✨ **TOTAL DE ARCHIVOS MODIFICADOS: 11**

- 1 modelo nuevo (RepuestoExterno)
- 3 migraciones nuevas
- 2 modelos modificados (DiagnosticoRepuesto, TrabajoRepuesto)
- 1 admin actualizado
- 1 views actualizado (con 3 nuevas vistas)
- 1 urls actualizado
- 5 templates actualizados/creados
- 2 documentación

---

**Fecha de implementación:** 27-28 de Octubre, 2025  
**Sistema:** Taller Automotriz - Gestión de Repuestos Externos  
**Estado:** ✅ COMPLETAMENTE FUNCIONAL Y PROBADO

