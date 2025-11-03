/* ========================================
   GESTOR DE TEMAS AUTOMÁTICO
   ======================================== */

class ThemeManager {
    constructor() {
        this.themes = {
            piedra: { name: 'Piedra', type: 'dark' },
            charcoal: { name: 'Charcoal', type: 'dark' },
            forest: { name: 'Forest', type: 'dark' },
            plum: { name: 'Plum', type: 'dark' },
            cyan: { name: 'Cyan', type: 'light' },
            sand: { name: 'Sand', type: 'light' },
            sage: { name: 'Sage', type: 'light' },
            sky: { name: 'Sky', type: 'light' }
        };
        
        this.currentTheme = this.getStoredTheme();
        this.init();
    }
    
    init() {
        this.applyTheme(this.currentTheme);
        this.setupThemeSwitcher();
        this.setupAutoContrast();
        this.setupAccessibility();
    }
    
    getStoredTheme() {
        return localStorage.getItem('theme') || 'piedra';
    }
    
    setStoredTheme(theme) {
        localStorage.setItem('theme', theme);
    }
    
    applyTheme(theme) {
        // Remover tema anterior
        document.body.className = document.body.className.replace(/theme-\w+/g, '');
        
        // Aplicar nuevo tema
        document.body.classList.add(`theme-${theme}`);
        
        // Guardar tema
        this.setStoredTheme(theme);
        this.currentTheme = theme;
        
        // Disparar evento personalizado
        document.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme, type: this.themes[theme].type }
        }));
        
        // Aplicar contraste automático
        this.applyAutoContrast();
    }
    
    setupThemeSwitcher() {
        // Buscar selector de tema
        const themeSelector = document.querySelector('[data-theme-selector]');
        if (themeSelector) {
            themeSelector.addEventListener('change', (e) => {
                this.applyTheme(e.target.value);
            });
        }
        
        // Buscar botones de tema
        document.querySelectorAll('[data-theme]').forEach(button => {
            button.addEventListener('click', (e) => {
                const theme = e.target.dataset.theme;
                this.applyTheme(theme);
            });
        });
    }
    
    setupAutoContrast() {
        // Aplicar contraste automático a elementos problemáticos
        this.applyAutoContrast();
        
        // Observar cambios en el DOM
        const observer = new MutationObserver(() => {
            this.applyAutoContrast();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    applyAutoContrast() {
        // Aplicar clases de contraste automático
        const elements = document.querySelectorAll(`
            .card:not(.auto-contrast),
            .modal-content:not(.auto-contrast),
            .form-control:not(.auto-contrast),
            .btn:not(.auto-contrast),
            .alert:not(.auto-contrast),
            .table:not(.auto-contrast),
            .navbar:not(.auto-contrast)
        `);
        
        elements.forEach(element => {
            if (!element.classList.contains('auto-contrast')) {
                element.classList.add('auto-contrast');
            }
        });
        
        // Aplicar contraste a texto
        const textElements = document.querySelectorAll(`
            .text-muted:not(.auto-contrast-text),
            .text-secondary:not(.auto-contrast-text),
            .text-primary:not(.auto-contrast-text)
        `);
        
        textElements.forEach(element => {
            if (element.classList.contains('text-muted') && !element.classList.contains('auto-contrast-text-muted')) {
                element.classList.add('auto-contrast-text-muted');
            } else if (element.classList.contains('text-secondary') && !element.classList.contains('auto-contrast-text-secondary')) {
                element.classList.add('auto-contrast-text-secondary');
            } else if (element.classList.contains('text-primary') && !element.classList.contains('auto-contrast-text')) {
                element.classList.add('auto-contrast-text');
            }
        });
    }
    
    setupAccessibility() {
        // Detectar preferencias de accesibilidad
        if (window.matchMedia) {
            // Preferencia de movimiento reducido
            const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
            reducedMotion.addEventListener('change', (e) => {
                if (e.matches) {
                    document.body.classList.add('reduced-motion');
                } else {
                    document.body.classList.remove('reduced-motion');
                }
            });
            
            // Preferencia de contraste alto
            const highContrast = window.matchMedia('(prefers-contrast: high)');
            highContrast.addEventListener('change', (e) => {
                if (e.matches) {
                    document.body.classList.add('high-contrast');
                } else {
                    document.body.classList.remove('high-contrast');
                }
            });
            
            // Preferencia de color scheme
            const darkMode = window.matchMedia('(prefers-color-scheme: dark)');
            darkMode.addEventListener('change', (e) => {
                if (e.matches && this.themes[this.currentTheme].type === 'light') {
                    // Sugerir cambio a tema oscuro
                    this.suggestThemeChange('dark');
                } else if (!e.matches && this.themes[this.currentTheme].type === 'dark') {
                    // Sugerir cambio a tema claro
                    this.suggestThemeChange('light');
                }
            });
        }
    }
    
    suggestThemeChange(type) {
        // Crear notificación de sugerencia
        const notification = document.createElement('div');
        notification.className = 'theme-suggestion alert alert-info position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>💡 Sugerencia de tema</strong><br>
                    <small>Tu sistema prefiere temas ${type === 'dark' ? 'oscuros' : 'claros'}</small>
                </div>
                <button type="button" class="btn btn-sm btn-outline-primary ms-2" onclick="this.parentElement.parentElement.remove()">
                    ✕
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }
    
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    getThemeType() {
        return this.themes[this.currentTheme].type;
    }
    
    getAllThemes() {
        return this.themes;
    }
    
    isDarkTheme() {
        return this.getThemeType() === 'dark';
    }
    
    isLightTheme() {
        return this.getThemeType() === 'light';
    }
}

/* ========================================
   FUNCIONES UTILITARIAS
   ======================================== */

// Función para cambiar tema desde JavaScript
function changeTheme(theme) {
    if (window.themeManager) {
        window.themeManager.applyTheme(theme);
    }
}

// Función para obtener tema actual
function getCurrentTheme() {
    return window.themeManager ? window.themeManager.getCurrentTheme() : 'piedra';
}

// Función para verificar si es tema oscuro
function isDarkTheme() {
    return window.themeManager ? window.themeManager.isDarkTheme() : false;
}

// Función para verificar si es tema claro
function isLightTheme() {
    return window.themeManager ? window.themeManager.isLightTheme() : false;
}

// Función para aplicar contraste automático
function applyAutoContrast() {
    if (window.themeManager) {
        window.themeManager.applyAutoContrast();
    }
}

/* ========================================
   INICIALIZACIÓN AUTOMÁTICA
   ======================================== */

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.themeManager = new ThemeManager();
    
    // Aplicar contraste automático después de un breve delay
    setTimeout(() => {
        applyAutoContrast();
    }, 100);
});

// Aplicar contraste automático cuando se cargan nuevos elementos
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar contraste automático a elementos existentes
    applyAutoContrast();
    
    // Aplicar contraste automático a elementos que se cargan dinámicamente
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Aplicar contraste automático a elementos nuevos
                        const elements = node.querySelectorAll ? 
                            node.querySelectorAll('.card, .modal-content, .form-control, .btn, .alert, .table, .navbar') :
                            (node.classList && node.classList.contains('card') || 
                             node.classList && node.classList.contains('modal-content') ||
                             node.classList && node.classList.contains('form-control') ||
                             node.classList && node.classList.contains('btn') ||
                             node.classList && node.classList.contains('alert') ||
                             node.classList && node.classList.contains('table') ||
                             node.classList && node.classList.contains('navbar')) ? [node] : [];
                        
                        elements.forEach(element => {
                            if (!element.classList.contains('auto-contrast')) {
                                element.classList.add('auto-contrast');
                            }
                        });
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

/* ========================================
   EXPORTAR PARA USO GLOBAL
   ======================================== */

// Hacer disponible globalmente
window.ThemeManager = ThemeManager;
window.changeTheme = changeTheme;
window.getCurrentTheme = getCurrentTheme;
window.isDarkTheme = isDarkTheme;
window.isLightTheme = isLightTheme;
window.applyAutoContrast = applyAutoContrast;







