// Script para manejar la instalación de la PWA
// Muestra un banner cuando la PWA puede ser instalada

let deferredPrompt;
let installBannerShown = false;

// Detectar cuando el navegador puede instalar la PWA
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevenir el prompt automático
  e.preventDefault();
  
  // Guardar el evento para usarlo después
  deferredPrompt = e;
  
  // Mostrar banner personalizado
  showInstallBanner();
});

// Si no hay evento beforeinstallprompt después de cargar, mostrar instrucciones alternativas
window.addEventListener('load', function() {
  setTimeout(() => {
    if (!deferredPrompt && !isPWAInstalled()) {
      // Intentar mostrar banner de todas formas (algunos navegadores no disparan el evento)
      showInstallBanner();
    }
  }, 1000);
});

// Función para mostrar banner de instalación
function showInstallBanner() {
  // Solo mostrar si no se ha mostrado antes y el usuario no la ha instalado
  if (installBannerShown || isPWAInstalled()) {
    return;
  }
  
  // Verificar si el usuario ya cerró el banner antes (localStorage)
  const bannerDismissed = localStorage.getItem('pwa-banner-dismissed');
  if (bannerDismissed === 'true') {
    return;
  }
  
  installBannerShown = true;
  
  // Esperar un poco para que la página cargue
  setTimeout(() => {
    // Crear banner si no existe
    let banner = document.getElementById('pwa-install-banner');
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'pwa-install-banner';
      banner.className = 'alert alert-info alert-dismissible fade show position-fixed bottom-0 start-0 w-100 m-0 rounded-0 shadow-lg';
      banner.style.zIndex = '9999';
      banner.style.borderTop = '3px solid #0d6efd';
      banner.innerHTML = `
        <div class="container d-flex flex-column flex-md-row justify-content-between align-items-center py-2">
          <div class="mb-2 mb-md-0 text-center text-md-start flex-grow-1">
            <strong>📱 Instala la app</strong>
            <p class="mb-0 small">Acceso rápido y pantalla completa</p>
          </div>
          <div class="d-flex gap-2 align-items-center">
            <button id="pwa-install-btn" class="btn btn-primary btn-sm">
              <i class="fas fa-download me-1"></i>Instalar
            </button>
            <button id="pwa-dismiss-text-btn" class="btn btn-outline-secondary btn-sm">
              Ahora no
            </button>
            <button type="button" class="btn-close" id="pwa-dismiss-btn" aria-label="Cerrar" style="filter: brightness(0) invert(0); font-size: 1.2rem;"></button>
          </div>
        </div>
      `;
      document.body.appendChild(banner);
      
      // Event listener para el botón de instalar
      document.getElementById('pwa-install-btn').addEventListener('click', installPWA);
      
      // Función para cerrar el banner
      function closeBanner() {
        localStorage.setItem('pwa-banner-dismissed', 'true');
        banner.classList.remove('show');
        setTimeout(() => banner.remove(), 300);
      }
      
      // Event listeners para cerrar (ambos botones)
      document.getElementById('pwa-dismiss-btn').addEventListener('click', closeBanner);
      document.getElementById('pwa-dismiss-text-btn').addEventListener('click', closeBanner);
      
      // Auto-cerrar después de 15 segundos (más tiempo)
      setTimeout(() => {
        if (banner && banner.parentNode) {
          banner.classList.remove('show');
          setTimeout(() => banner.remove(), 300);
        }
      }, 15000);
    }
  }, 2000); // Esperar 2 segundos después de cargar
}

// Función para instalar la PWA
function installPWA() {
  // Si hay deferredPrompt, usarlo (instalación automática)
  if (deferredPrompt) {
    // Mostrar el prompt de instalación
    deferredPrompt.prompt();
    
    // Esperar la respuesta del usuario
    deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('Usuario aceptó instalar la PWA');
        // Ocultar banner
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
          banner.remove();
        }
      } else {
        console.log('Usuario rechazó instalar la PWA');
      }
      
      // Limpiar
      deferredPrompt = null;
    });
  } else {
    // No hay prompt automático - mostrar instrucciones manuales
    showManualInstallInstructions();
  }
}

// Verificar si la PWA ya está instalada
function isPWAInstalled() {
  // Verificar si se está ejecutando en modo standalone (instalada)
  return window.matchMedia('(display-mode: standalone)').matches ||
         window.navigator.standalone === true ||
         document.referrer.includes('android-app://');
}

// Mostrar instrucciones manuales cuando el botón de instalación no funciona
function showManualInstallInstructions() {
  // Ocultar el banner actual
  const banner = document.getElementById('pwa-install-banner');
  if (banner) {
    banner.style.display = 'none';
  }
  
  // Detectar el sistema operativo
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  const isAndroid = /Android/.test(navigator.userAgent);
  
  let instructionsText = '';
  if (isIOS) {
    instructionsText = `
      <strong>📱 Instalación en iPhone:</strong>
      <ol class="mb-2 small text-start">
        <li>Toca el botón <strong>Compartir</strong> (📤) en la barra inferior</li>
        <li>Desplázate y toca <strong>"Agregar a pantalla de inicio"</strong></li>
        <li>Toca <strong>"Agregar"</strong> para confirmar</li>
      </ol>
    `;
  } else if (isAndroid) {
    instructionsText = `
      <strong>📱 Instalación en Android:</strong>
      <ol class="mb-2 small text-start">
        <li>Toca el <strong>menú</strong> (⋮) en la esquina superior derecha</li>
        <li>Busca y toca <strong>"Agregar a pantalla de inicio"</strong> o <strong>"Instalar app"</strong></li>
        <li>Confirma la instalación</li>
      </ol>
    `;
  } else {
    instructionsText = `
      <strong>💡 Instalación manual:</strong>
      <p class="mb-2 small">
        Busca en el menú del navegador la opción <strong>"Agregar a pantalla de inicio"</strong> o <strong>"Instalar app"</strong>
      </p>
    `;
  }
  
  // Crear modal o alert con instrucciones
  const instructions = document.createElement('div');
  instructions.id = 'pwa-manual-instructions';
  instructions.className = 'alert alert-primary position-fixed top-50 start-50 translate-middle shadow-lg';
  instructions.style.zIndex = '10000';
  instructions.style.maxWidth = '90%';
  instructions.style.width = '400px';
  instructions.style.borderRadius = '12px';
  instructions.innerHTML = `
    <div class="d-flex justify-content-between align-items-start mb-2">
      <h5 class="mb-0">📱 Instalar App</h5>
      <button type="button" class="btn-close" id="pwa-instructions-close" aria-label="Cerrar"></button>
    </div>
    <div class="text-start">
      ${instructionsText}
      <div class="d-grid">
        <button class="btn btn-primary btn-sm" id="pwa-got-it-btn">Entendido</button>
      </div>
    </div>
  `;
  document.body.appendChild(instructions);
  
  // Event listeners para cerrar
  document.getElementById('pwa-instructions-close').addEventListener('click', () => {
    instructions.remove();
    if (banner) banner.style.display = 'flex';
  });
  
  document.getElementById('pwa-got-it-btn').addEventListener('click', () => {
    instructions.remove();
    if (banner) banner.remove();
    localStorage.setItem('pwa-banner-dismissed', 'true');
  });
  
  // Cerrar al hacer clic fuera (opcional)
  instructions.addEventListener('click', (e) => {
    if (e.target === instructions) {
      instructions.remove();
      if (banner) banner.style.display = 'flex';
    }
  });
}

// Detectar cuando la PWA se instala
window.addEventListener('appinstalled', () => {
  console.log('PWA instalada exitosamente');
  // Ocultar banner si existe
  const banner = document.getElementById('pwa-install-banner');
  if (banner) {
    banner.remove();
  }
  
  // Opcional: mostrar mensaje de éxito
  if ('Notification' in window && Notification.permission === 'granted') {
    new Notification('¡App instalada!', {
      body: 'Ahora puedes acceder rápidamente desde tu pantalla de inicio',
      icon: '/static/images/pwa-icon-192.png'
    });
  }
});

// Exponer función globalmente por si quieres un botón de instalación manual
window.installPWA = installPWA;

