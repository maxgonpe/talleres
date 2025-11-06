// Service Worker para PWA - Taller Mecánico
const CACHE_NAME = 'taller-mecanico-v2';
const STATIC_CACHE_NAME = 'taller-static-v2';
const DYNAMIC_CACHE_NAME = 'taller-dynamic-v2';

// Archivos esenciales que se cachean inmediatamente
const STATIC_FILES = [
  '/',
  '/static/css/centralized-colors.css',
  '/static/images/Logo2.png',
];

// Estrategia: Cache First para archivos estáticos
// Network First para páginas HTML

self.addEventListener('install', (event) => {
  console.log('[Service Worker] Instalando...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME).then((cache) => {
      console.log('[Service Worker] Cacheando archivos estáticos');
      return cache.addAll(STATIC_FILES);
    })
  );
  
  // Activar el service worker inmediatamente
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activando...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Eliminar caches antiguos
          if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
            console.log('[Service Worker] Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Tomar control de todas las páginas inmediatamente
  return self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Ignorar requests que no son GET
  if (request.method !== 'GET') {
    return;
  }
  
  // Ignorar requests al admin (siempre online)
  if (url.pathname.startsWith('/admin/')) {
    return;
  }
  
  // Estrategia para archivos estáticos: Cache First
  if (
    url.pathname.startsWith('/static/') ||
    url.pathname.startsWith('/media/')
  ) {
    event.respondWith(
      caches.match(request).then((response) => {
        return response || fetch(request).then((fetchResponse) => {
          // Cachear para próximas veces
          if (fetchResponse && fetchResponse.status === 200) {
            const responseToCache = fetchResponse.clone();
            caches.open(STATIC_CACHE_NAME).then((cache) => {
              cache.put(request, responseToCache);
            });
          }
          return fetchResponse;
        });
      })
    );
    return;
  }
  
  // Estrategia para páginas HTML: Network First
  // Si no hay conexión, usar cache
  event.respondWith(
    fetch(request)
      .then((response) => {
        // Si la respuesta es válida, cachearla
        if (response && response.status === 200) {
          const responseToCache = response.clone();
          caches.open(DYNAMIC_CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
        }
        return response;
      })
      .catch(() => {
        // Si no hay conexión, intentar desde cache
        return caches.match(request).then((response) => {
          if (response) {
            return response;
          }
          // Si no hay en cache, mostrar página offline
          if (request.mode === 'navigate') {
            return caches.match('/');
          }
        });
      })
  );
});

// Notificaciones (opcional, para futuras funcionalidades)
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});


