# 📱 INSTALAR PWA - Instrucciones Manuales

## ⚠️ Situación: No aparece "Instalar app" en el menú

Esto es **normal** cuando:
- Estás en desarrollo local (HTTP, no HTTPS)
- El navegador no detecta la PWA como instalable
- Ya creaste un acceso directo antes

---

## ✅ SOLUCIÓN: "Agregar a la pantalla" SÍ funciona

**¡Buenas noticias!** El botón "Agregar a la pantalla de inicio" **SÍ instala la PWA** en la mayoría de navegadores modernos.

### **En Android (Chrome/Edge):**
1. Abre `http://192.168.1.104:8000`
2. Menú (⋮) → **"Agregar a pantalla de inicio"**
3. Confirma
4. ✅ Se instalará como PWA completa

### **En iPhone (Safari):**
1. Abre `http://192.168.1.104:8000`
2. Botón **Compartir** (📤)
3. **"Agregar a pantalla de inicio"**
4. ✅ Se instalará (esto es lo máximo en iOS)

---

## 🎯 CÓMO VERIFICAR SI SE INSTALÓ CORRECTAMENTE

Después de agregar a la pantalla:

1. **Abre el ícono desde la pantalla de inicio**
2. **Verifica:**
   - ✅ **NO ves la barra del navegador** (URL arriba) → ✅ Instalada correctamente
   - ❌ **SÍ ves la barra del navegador** → Solo acceso directo

### **Si NO ves la barra del navegador:**
- ✅ **¡Perfecto!** Está instalada como PWA
- Funciona en pantalla completa
- Tiene todas las características de PWA

### **Si SÍ ves la barra del navegador:**
- Puede que tu navegador no soporte PWA completa
- O necesitas hacerlo desde el menú del navegador de otra forma

---

## 🔧 FORZAR INSTALACIÓN COMPLETA

### **Opción 1: Desde el menú del navegador (recomendado)**

**Android Chrome:**
1. Abre el sitio
2. Menú (⋮) → "Agregar a pantalla de inicio"
3. O busca "Instalar app" si aparece

**Edge Android:**
1. Menú (⋮) → "Agregar a pantalla"
2. Funciona igual

### **Opción 2: Configuración del navegador**

**Chrome Android:**
1. Menú (⋮) → "Configuración"
2. Busca "Instalación de apps" o "Instalar apps"
3. Verifica que esté habilitado

---

## 📋 DIFERENCIAS VISUALES

### **PWA Instalada (correcto):**
- ❌ Sin barra de direcciones
- ❌ Sin botones del navegador
- ✅ Pantalla completa
- ✅ Se ve como app nativa

### **Acceso directo (no completo):**
- ✅ Con barra de direcciones
- ✅ Con botones del navegador
- ❌ Se ve como página web

---

## 🚀 EN PRODUCCIÓN (HTTPS)

Cuando subas a producción con HTTPS (`https://tallerx.netgogo.cl`):

- ✅ **Aparecerá automáticamente** la opción "Instalar app"
- ✅ **El banner funcionará mejor**
- ✅ **Mejor experiencia de instalación**

En desarrollo local, usar "Agregar a la pantalla" es **suficiente y funciona bien**.

---

## 💡 TIPS ADICIONALES

### **Limpiar e instalar de nuevo:**

Si quieres reinstalar:

1. Elimina el acceso directo actual
2. Limpia la caché del navegador
3. Vuelve a visitar el sitio
4. Usa "Agregar a la pantalla" de nuevo

### **Verificar Service Worker:**

1. Abre herramientas de desarrollador (F12 o menú → Más herramientas)
2. Pestaña "Application" (o "Aplicación")
3. Busca "Service Workers"
4. Debería aparecer: `service-worker.js` activo

---

## ✅ CONCLUSIÓN

**"Agregar a la pantalla de inicio" = Instalar PWA** en la mayoría de casos.

Si después de agregarlo:
- **NO ves barra del navegador** → ✅ Instalada correctamente
- **SÍ ves barra del navegador** → Acceso directo simple (pero igual funciona)

**Lo importante:** La optimización móvil (botones grandes, etc.) **funciona en ambos casos** ✅

