# 🔧 Solución: Extracción de Datos en Producción

## ❌ Problema

La extracción automática de datos funciona en **local** pero falla en **producción** con el error:
```
❌ Error: Unexpected token '<', "<!DOCTYPE "... is not valid JSON
```

---

## 🔍 Causa

Tu **servidor de producción no puede hacer peticiones HTTP salientes** a sitios externos (Mundo Repuestos, AutoPlanet). Esto puede ser por:

1. **Firewall del servidor** bloqueando peticiones salientes
2. **Política de seguridad** del hosting
3. **Proxy/VPN** interceptando las conexiones
4. **Los sitios externos bloquean** peticiones desde servidores (anti-scraping)

---

## ✅ Soluciones

### **Opción 1: Permitir peticiones salientes en el servidor (Recomendado)**

Si tienes acceso al servidor, ejecuta:

```bash
# Verificar si puede hacer peticiones salientes
curl -I https://mundorepuestos.com
curl -I https://www.autoplanet.cl

# Si falla, revisar firewall (ejemplo para UFW):
sudo ufw allow out 80/tcp
sudo ufw allow out 443/tcp
sudo ufw reload

# O si usas iptables:
sudo iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
```

### **Opción 2: Instalar librerías faltantes**

Verifica que estén instaladas en producción:

```bash
source env/bin/activate
pip install requests beautifulsoup4
```

### **Opción 3: Usar proxy/servicio externo**

Si el servidor está muy restringido, podrías usar un servicio de scraping como:
- ScraperAPI
- Bright Data
- ProxyCrawl

Pero esto tiene costo mensual.

### **Opción 4: Deshabilitar auto-extracción en producción (Temporal)**

Si no puedes solucionar lo anterior, simplemente:
- ✅ **Mantén la funcionalidad de búsqueda** (funciona perfecto)
- ✅ **Mantén la funcionalidad de guardar referencias** (funciona perfecto)
- ❌ **La extracción automática no funcionará** (tendrán que copiar manualmente)

**Esto NO afecta al resto del sistema** - solo la función "🔍 Extraer Datos" no funcionará. Todo lo demás sigue funcionando:
- Buscar en referencias guardadas ✅
- Buscar directamente en proveedores ✅
- Guardar referencias manualmente ✅
- Agregar a diagnósticos/trabajos ✅
- PDFs con repuestos externos ✅

---

## 🎯 Flujo Alternativo (sin auto-extracción)

Si la extracción automática no funciona en producción:

1. Click en "🛒 Buscar en Mundo Repuestos" → Abre pestaña
2. Encuentras: "Filtro Aceite Toyota Corolla - $18,500"
3. **Copias manualmente** a una nota o pantalla dividida
4. Vuelves a la pestaña "💾 Guardar Nueva Referencia"
5. **Llenas el formulario a mano:**
   - Nombre: Filtro Aceite Toyota Corolla
   - Proveedor: Mundo Repuestos
   - Precio: 18500
   - (URL opcional)
6. Guardas
7. ✅ Listo

**Sigue siendo más rápido que antes** porque:
- Ya tienes los botones directos a proveedores
- El formulario es simple
- Una vez guardado, queda para siempre

---

## 🔧 Debug en Producción

Para verificar qué está pasando exactamente:

```bash
# SSH al servidor
cd /ruta/al/proyecto
source env/bin/activate

# Probar si puede hacer requests
python manage.py shell
>>> import requests
>>> r = requests.get('https://mundorepuestos.com/', timeout=5)
>>> print(r.status_code)
>>> exit()

# Ver logs del servidor
sudo tail -f /var/log/gunicorn/error.log
# O
sudo journalctl -u gunicorn -f
```

Si el `requests.get()` funciona en el shell pero no desde la vista, puede ser un problema de timeout o headers.

---

## 💡 Recomendación Final

**Implementa la Opción 4** (desactivar auto-extracción en producción) porque:
- ✅ **90% del sistema funciona perfecto** sin ella
- ✅ **No depende de scraping** (que es frágil)
- ✅ **Copiar manualmente** 4 campos toma solo 30 segundos
- ✅ **Una vez guardado**, se reutiliza para siempre

El valor real del sistema es:
1. **Base de datos propia** de repuestos externos
2. **Búsqueda rápida** en referencias
3. **Integración con diagnósticos/trabajos**
4. **Visualización en PDFs**

La auto-extracción es un **bonus**, no crítica.

---

**Fecha:** 28 de Octubre, 2025  
**Estado:** Sistema funcional, auto-extracción puede fallar en producción por restricciones del servidor








