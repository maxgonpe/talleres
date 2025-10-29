// ========================================
// PULL TO REFRESH - Recargar deslizando
// ========================================

(function() {
  'use strict';
  
  // Solo en móviles
  if (window.innerWidth > 768) {
    return;
  }
  
  let touchStartY = 0;
  let touchCurrentY = 0;
  let isPulling = false;
  let pullDistance = 0;
  let refreshIndicator = null;
  let maxPullDistance = 80;
  
  // Crear indicador visual
  function createRefreshIndicator() {
    if (refreshIndicator) return refreshIndicator;
    
    refreshIndicator = document.createElement('div');
    refreshIndicator.id = 'pull-to-refresh-indicator';
    refreshIndicator.style.cssText = `
      position: fixed;
      top: -60px;
      left: 50%;
      transform: translateX(-50%);
      width: 50px;
      height: 50px;
      background: var(--primary-600, #0d6efd);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 20px;
      z-index: 10000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
      transition: top 0.3s ease;
      pointer-events: none;
    `;
    refreshIndicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i>';
    document.body.appendChild(refreshIndicator);
    return refreshIndicator;
  }
  
  // Solo aplicar si estamos en la parte superior de la página
  function isAtTop() {
    return window.scrollY === 0 || window.pageYOffset === 0;
  }
  
  // Evento de inicio de toque
  function handleTouchStart(e) {
    if (!isAtTop() || e.touches.length !== 1) return;
    
    touchStartY = e.touches[0].clientY;
    isPulling = false;
  }
  
  // Evento de movimiento
  function handleTouchMove(e) {
    if (!isAtTop() || e.touches.length !== 1) return;
    
    touchCurrentY = e.touches[0].clientY;
    pullDistance = touchCurrentY - touchStartY;
    
    // Solo activar si deslizamos hacia abajo
    if (pullDistance > 0) {
      if (!isPulling) {
        isPulling = true;
        createRefreshIndicator();
      }
      
      // Limitar el pull
      pullDistance = Math.min(pullDistance, maxPullDistance);
      
      // Actualizar posición del indicador
      const progress = pullDistance / maxPullDistance;
      const topPosition = -60 + (pullDistance * 0.8);
      refreshIndicator.style.top = topPosition + 'px';
      refreshIndicator.style.transform = `translateX(-50%) scale(${0.8 + progress * 0.2})`;
      
      // Rotar icono
      if (refreshIndicator) {
        const icon = refreshIndicator.querySelector('i');
        if (icon) {
          icon.style.transform = `rotate(${pullDistance * 3}deg)`;
        }
      }
      
      // Prevenir scroll si estamos en el top
      if (pullDistance > 10) {
        e.preventDefault();
      }
    }
  }
  
  // Evento de fin de toque
  function handleTouchEnd(e) {
    if (!isPulling) return;
    
    const indicator = refreshIndicator;
    
    // Si llegó al límite, recargar
    if (pullDistance >= maxPullDistance * 0.8) {
      // Mostrar indicador completo
      if (indicator) {
        indicator.style.top = '20px';
        indicator.querySelector('i').classList.add('fa-spin');
      }
      
      // Recargar la página después de un pequeño delay
      setTimeout(() => {
        window.location.reload();
      }, 300);
    } else {
      // Volver a ocultar
      if (indicator) {
        indicator.style.top = '-60px';
        indicator.querySelector('i').classList.remove('fa-spin');
        indicator.querySelector('i').style.transform = 'rotate(0deg)';
      }
    }
    
    // Reset
    isPulling = false;
    pullDistance = 0;
    touchStartY = 0;
    touchCurrentY = 0;
  }
  
  // Agregar event listeners
  document.addEventListener('touchstart', handleTouchStart, { passive: true });
  document.addEventListener('touchmove', handleTouchMove, { passive: false });
  document.addEventListener('touchend', handleTouchEnd, { passive: true });
  
})();

