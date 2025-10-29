# 📱 GUÍA DE USO - PWA (Progressive Web App)

## ✅ ¿Qué se implementó?

Tu sistema ahora es una **Progressive Web App (PWA)** completa. Esto significa que:

- ✅ Se puede **instalar en el teléfono** como una app nativa
- ✅ Funciona **sin conexión** (offline básico)
- ✅ Se ve y se siente como una **app nativa**
- ✅ Es más **rápida** gracias al caché inteligente
- ✅ Compatible con **todos los dispositivos** (teléfono, tablet, PC)

---

## 🚀 CÓMO PROBAR EN TU TELÉFONO

### **Método 1: Mismo Wi-Fi (Recomendado)**

1. **En tu PC:**
   ```bash
   cd /home/maxgonpe/talleres/car
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Averiguar tu IP local:**
   ```bash
   hostname -I
   ```
   O:
   ```bash
   ip addr show | grep "inet " | grep -v 127.0.0.1
   ```
   Ejemplo de resultado: `192.168.1.100`

3. **En tu teléfono:**
   - Asegúrate de estar conectado al **mismo Wi-Fi** que tu PC
   - Abre el navegador (Chrome, Safari, Firefox)
   - Ve a: `http://TU-IP:8000`
   - Ejemplo: `http://192.168.1.100:8000`

4. **Instalar la PWA:**
   - **Android (Chrome):** Verás un banner "Instala la app" o en el menú → "Instalar app"
   - **iPhone (Safari):** Botón "Compartir" (📤) → "Agregar a pantalla de inicio"

---

### **Método 2: Localhost (PC/Tablet)**

Si solo quieres probar en tu PC/Tablet en el mismo equipo:

1. Inicia el servidor normalmente:
   ```bash
   python manage.py runserver
   ```

2. Abre en el navegador:
   ```
   http://localhost:8000
   ```

3. **Instalar:**
   - **Chrome/Edge:** Click en el ícono de "Instalar" en la barra de direcciones
   - **Firefox:** Menú → "Instalar"

---

## 📋 VERIFICAR QUE FUNCIONA

### **1. Verificar Service Worker**

1. Abre las **Herramientas de Desarrollador** (F12)
2. Ve a la pestaña **"Application"** (o "Aplicación")
3. En el menú izquierdo, busca **"Service Workers"**
4. Deberías ver: `service-worker.js` con estado **"activated and is running"**

### **2. Verificar Manifest**

1. En las herramientas de desarrollador, pestaña **"Application"**
2. Busca **"Manifest"** en el menú izquierdo
3. Deberías ver los datos de la PWA (nombre, iconos, etc.)

### **3. Probar Modo Offline**

1. En las herramientas de desarrollador, pestaña **"Network"** (Red)
2. Marca **"Offline"** (también en Chrome: F12 → Network → Throttling → Offline)
3. Recarga la página
4. Debería seguir funcionando (desde caché)

### **4. Verificar Instalación**

Después de instalar:
- La app aparecerá en tu pantalla de inicio (como un ícono)
- Al abrirla, se verá **sin la barra del navegador** (pantalla completa)
- Funciona como una app nativa

---

## 🔧 TROUBLESHOOTING

### **No aparece el banner de instalación:**

- ✅ Asegúrate de estar usando **HTTPS** o **localhost** (no funciona en IPs normales sin HTTPS)
- ✅ En desarrollo local, `localhost:8000` funciona perfectamente
- ✅ Si usas IP, necesitas HTTPS para producción

### **El Service Worker no se registra:**

1. Verifica en la consola del navegador si hay errores
2. Asegúrate de que el archivo existe: `/static/js/service-worker.js`
3. Verifica que el servidor esté sirviendo archivos estáticos correctamente

### **Los iconos no aparecen:**

1. Verifica que existan:
   ```bash
   ls -la static/images/pwa-icon-*.png
   ```
2. Si no existen, créalos desde el logo:
   ```bash
   python3 -c "from PIL import Image; img = Image.open('static/images/Logo2.png'); img.resize((192, 192)).save('static/images/pwa-icon-192.png'); img.resize((512, 512)).save('static/images/pwa-icon-512.png')"
   ```

### **PWA instalada pero parece web normal:**

- ✅ Verifica que estés abriendo la **versión instalada** (desde el ícono de la pantalla de inicio)
- ✅ No desde el navegador normal

---

## 📁 ARCHIVOS CREADOS

```
static/
├── manifest.json           ← Configuración de la PWA
├── js/
│   ├── service-worker.js   ← Funcionalidad offline
│   └── pwa-install.js      ← Banner de instalación
└── images/
    ├── pwa-icon-192.png    ← Icono 192x192
    └── pwa-icon-512.png    ← Icono 512x512

car/templates/
└── base.html               ← Modificado (meta tags PWA)
```

---

## 🎯 PRÓXIMOS PASOS

### **Para Producción:**

1. **Asegúrate de usar HTTPS:**
   - Las PWA requieren HTTPS (excepto localhost)
   - Tu servidor ya tiene HTTPS configurado

2. **Subir archivos al servidor:**
   ```bash
   # Los archivos PWA ya están en tu proyecto
   # Solo sube como siempre
   ```

3. **Ejecutar collectstatic (si es necesario):**
   ```bash
   python manage.py collectstatic --noinput
   ```

---

## ✨ FUNCIONALIDADES ACTIVAS

- ✅ **Instalación:** Los usuarios pueden instalar la app en su teléfono
- ✅ **Pantalla completa:** Se ve como app nativa cuando está instalada
- ✅ **Offline básico:** Funciona sin internet (usando caché)
- ✅ **Caché inteligente:** Archivos estáticos se cachean automáticamente
- ✅ **Actualizaciones:** El Service Worker se actualiza automáticamente cada hora
- ✅ **Banner de instalación:** Aparece automáticamente cuando es posible instalar

---

## 🎉 ¡LISTO PARA USAR!

Tu sistema ahora es una PWA completa. Pruébalo en tu teléfono siguiendo los pasos de arriba.

**El banner de instalación aparecerá automáticamente cuando sea posible instalarla.**

