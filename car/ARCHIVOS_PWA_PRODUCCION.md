# 📤 ARCHIVOS PARA SUBIR A PRODUCCIÓN - PWA y Optimización Móvil

## ✅ LISTA DE ARCHIVOS NUEVOS A SUBIR

### **1. Archivos PWA (obligatorios)**
```
static/
├── manifest.json                    ← Configuración PWA
├── js/
│   ├── service-worker.js            ← Funcionalidad offline
│   └── pwa-install.js               ← Banner de instalación
└── images/
    ├── pwa-icon-192.png             ← Icono 192x192
    └── pwa-icon-512.png             ← Icono 512x512
```

### **2. Archivos de optimización móvil (obligatorios)**
```
static/
└── css/
    ├── mobile-optimized.css         ← Optimización móvil principal
    └── mobile-bottom-nav.css        ← Menú inferior (opcional)
```

### **3. Templates modificados (obligatorios)**
```
car/templates/
├── base.html                        ← Modificado (meta tags PWA + CSS móvil)
└── base_clean.html                  ← Modificado (meta tags PWA + CSS móvil)
```

---

## 📋 PASOS PARA SUBIR A PRODUCCIÓN

### **Paso 1: Preparar archivos**

```bash
cd /home/maxgonpe/talleres/car
```

### **Paso 2: Copiar archivos nuevos**

Copia estos archivos a tu servidor de producción:

#### **Archivos estáticos:**
- `static/manifest.json`
- `static/js/service-worker.js`
- `static/js/pwa-install.js`
- `static/css/mobile-optimized.css`
- `static/images/pwa-icon-192.png`
- `static/images/pwa-icon-512.png`

#### **Templates:**
- `car/templates/base.html`
- `car/templates/base_clean.html`

### **Paso 3: En el servidor de producción**

```bash
# Entrar al directorio del proyecto
cd /ruta/a/tu/proyecto

# Si usas collectstatic (recomendado)
python manage.py collectstatic --noinput

# O simplemente asegúrate de que los archivos estén en:
# - static/ (o STATICFILES_DIRS)
# - car/templates/
```

---

## 🗂️ ESTRUCTURA COMPLETA EN PRODUCCIÓN

Tu servidor debe tener:

```
proyecto/
├── static/
│   ├── manifest.json                ✅ NUEVO
│   ├── js/
│   │   ├── service-worker.js        ✅ NUEVO
│   │   └── pwa-install.js           ✅ NUEVO
│   ├── css/
│   │   ├── mobile-optimized.css     ✅ NUEVO
│   │   └── mobile-bottom-nav.css    ✅ NUEVO (opcional)
│   └── images/
│       ├── pwa-icon-192.png         ✅ NUEVO
│       └── pwa-icon-512.png         ✅ NUEVO
│
└── car/
    └── templates/
        ├── base.html                ✅ MODIFICADO
        └── base_clean.html          ✅ MODIFICADO
```

---

## 🚀 COMANDO RÁPIDO (si usas rsync/scp)

```bash
# Desde tu máquina local
cd /home/maxgonpe/talleres/car

# Copiar archivos estáticos nuevos
scp static/manifest.json usuario@servidor:/ruta/proyecto/static/
scp static/js/service-worker.js usuario@servidor:/ruta/proyecto/static/js/
scp static/js/pwa-install.js usuario@servidor:/ruta/proyecto/static/js/
scp static/css/mobile-optimized.css usuario@servidor:/ruta/proyecto/static/css/
scp static/images/pwa-icon-*.png usuario@servidor:/ruta/proyecto/static/images/

# Copiar templates modificados
scp car/templates/base.html usuario@servidor:/ruta/proyecto/car/templates/
scp car/templates/base_clean.html usuario@servidor:/ruta/proyecto/car/templates/
```

---

## ✅ VERIFICAR EN PRODUCCIÓN

Después de subir, verifica:

### **1. Archivos accesibles:**
- `https://tallerx.netgogo.cl/static/manifest.json` → Debe mostrar el JSON
- `https://tallerx.netgogo.cl/static/js/service-worker.js` → Debe mostrar el código
- `https://tallerx.netgogo.cl/static/images/pwa-icon-192.png` → Debe mostrar el icono

### **2. En el navegador (F12 → Application):**
- **Manifest**: Debe aparecer correctamente
- **Service Workers**: Debe estar registrado
- **Sin errores** en la consola

### **3. Probar en móvil:**
- Abrir en teléfono con HTTPS
- Verificar que aparezca el banner
- Instalar la PWA
- Verificar que funcione sin barra del navegador

---

## 📝 NOTA IMPORTANTE: HTTPS

**La PWA requiere HTTPS en producción** (excepto localhost).

Tu dominio `tallerx.netgogo.cl` debe tener:
- ✅ Certificado SSL activo
- ✅ Redirección de HTTP a HTTPS

Si ya tienes HTTPS configurado, no hay problema. Si no, necesitas configurarlo primero.

---

## 🎯 RESUMEN RÁPIDO

**Archivos a subir:**
1. ✅ `static/manifest.json`
2. ✅ `static/js/service-worker.js`
3. ✅ `static/js/pwa-install.js`
4. ✅ `static/css/mobile-optimized.css`
5. ✅ `static/images/pwa-icon-192.png`
6. ✅ `static/images/pwa-icon-512.png`
7. ✅ `car/templates/base.html` (modificado)
8. ✅ `car/templates/base_clean.html` (modificado)

**En producción:**
- Ejecutar `collectstatic` si es necesario
- Verificar que HTTPS esté activo
- Probar en móvil

---

## ✨ ¡LISTO!

Una vez subidos estos archivos, la PWA y optimización móvil estarán disponibles en producción.

¡Solo sube los 8 archivos y listo! 🚀



