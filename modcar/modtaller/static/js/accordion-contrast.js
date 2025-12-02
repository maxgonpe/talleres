/**
 * Accordion Contrast Fix
 * Soluciona problemas de contraste en acordeones para temas oscuros
 */

(function() {
    'use strict';
    
    // Función para aplicar contraste forzado
    function applyAccordionContrast() {
        // Verificar si estamos en un tema oscuro
        const isDarkTheme = document.body.classList.contains('theme-piedra') ||
                           document.body.classList.contains('theme-charcoal') ||
                           document.body.classList.contains('theme-forest') ||
                           document.body.classList.contains('theme-plum');
        
        if (!isDarkTheme) {
            return; // No hacer nada en temas claros
        }
        
        // Buscar el acordeón de componentes
        const accordion = document.getElementById('componentesAccordion');
        if (!accordion) {
            return;
        }
        
        // Aplicar clase de contraste forzado
        accordion.classList.add('accordion-force-contrast');
        
        // Aplicar estilos directamente a los elementos
        const buttons = accordion.querySelectorAll('.accordion-button');
        const bodies = accordion.querySelectorAll('.accordion-body');
        const items = accordion.querySelectorAll('.accordion-item');
        const labels = accordion.querySelectorAll('.form-check-label');
        const inputs = accordion.querySelectorAll('.form-check-input');
        
        // Estilos para botones
        buttons.forEach(button => {
            button.style.setProperty('background-color', '#ffffff', 'important');
            button.style.setProperty('color', '#212529', 'important');
            button.style.setProperty('border-color', '#dee2e6', 'important');
            button.style.setProperty('font-weight', '600', 'important');
            button.style.setProperty('text-shadow', 'none', 'important');
            button.style.setProperty('opacity', '1', 'important');
            button.style.setProperty('visibility', 'visible', 'important');
        });
        
        // Estilos para cuerpos
        bodies.forEach(body => {
            body.style.setProperty('background-color', '#ffffff', 'important');
            body.style.setProperty('color', '#212529', 'important');
            body.style.setProperty('border-color', '#dee2e6', 'important');
            body.style.setProperty('text-shadow', 'none', 'important');
            body.style.setProperty('opacity', '1', 'important');
            body.style.setProperty('visibility', 'visible', 'important');
        });
        
        // Estilos para items
        items.forEach(item => {
            item.style.setProperty('background-color', '#ffffff', 'important');
            item.style.setProperty('border-color', '#dee2e6', 'important');
            item.style.setProperty('text-shadow', 'none', 'important');
            item.style.setProperty('opacity', '1', 'important');
            item.style.setProperty('visibility', 'visible', 'important');
        });
        
        // Estilos para labels
        labels.forEach(label => {
            label.style.setProperty('color', '#212529', 'important');
            label.style.setProperty('font-weight', '500', 'important');
            label.style.setProperty('text-shadow', 'none', 'important');
            label.style.setProperty('opacity', '1', 'important');
            label.style.setProperty('visibility', 'visible', 'important');
        });
        
        // Estilos para inputs
        inputs.forEach(input => {
            input.style.setProperty('background-color', '#ffffff', 'important');
            input.style.setProperty('border-color', '#dee2e6', 'important');
            input.style.setProperty('text-shadow', 'none', 'important');
            input.style.setProperty('opacity', '1', 'important');
            input.style.setProperty('visibility', 'visible', 'important');
        });
    }
    
    // Función para remover contraste forzado
    function removeAccordionContrast() {
        const accordion = document.getElementById('componentesAccordion');
        if (accordion) {
            accordion.classList.remove('accordion-force-contrast');
        }
    }
    
    // Aplicar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAccordionContrast);
    } else {
        applyAccordionContrast();
    }
    
    // Aplicar cuando cambie el tema
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target === document.body) {
                    // Verificar si cambió el tema
                    const hasThemeClass = target.className.includes('theme-');
                    if (hasThemeClass) {
                        setTimeout(applyAccordionContrast, 100);
                    }
                }
            }
        });
    });
    
    observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['class']
    });
    
    // Aplicar cuando se abra/cierre un acordeón
    document.addEventListener('shown.bs.collapse', function(event) {
        if (event.target.closest('#componentesAccordion')) {
            setTimeout(applyAccordionContrast, 50);
        }
    });
    
    document.addEventListener('hidden.bs.collapse', function(event) {
        if (event.target.closest('#componentesAccordion')) {
            setTimeout(applyAccordionContrast, 50);
        }
    });
    
    // Aplicar periódicamente para asegurar que se mantenga
    setInterval(applyAccordionContrast, 2000);
    
    // Función para mejorar contraste de elementos small.text-muted
    function enhanceSmallTextContrast() {
        const isDarkTheme = document.body.classList.contains('theme-piedra') ||
                           document.body.classList.contains('theme-charcoal') ||
                           document.body.classList.contains('theme-forest') ||
                           document.body.classList.contains('theme-plum');
        
        if (!isDarkTheme) {
            return;
        }
        
        // Buscar todos los elementos small.text-muted
        const smallElements = document.querySelectorAll('small.text-muted');
        smallElements.forEach(element => {
            // Aplicar estilos inline para máximo contraste
            element.style.setProperty('color', '#ecf0f1', 'important');
            element.style.setProperty('font-weight', '600', 'important');
            element.style.setProperty('background-color', 'rgba(44, 62, 80, 0.9)', 'important');
            element.style.setProperty('padding', '3px 8px', 'important');
            element.style.setProperty('border-radius', '6px', 'important');
            element.style.setProperty('display', 'inline-block', 'important');
            element.style.setProperty('border', '1px solid #34495e', 'important');
        });
    }
    
    // Función para mejorar contraste de nombres de productos
    function enhanceProductNameContrast() {
        const isDarkTheme = document.body.classList.contains('theme-piedra') ||
                           document.body.classList.contains('theme-charcoal') ||
                           document.body.classList.contains('theme-forest') ||
                           document.body.classList.contains('theme-plum');
        
        if (!isDarkTheme) {
            return;
        }
        
        // Buscar todos los elementos .fw-bold (nombres de productos)
        const boldElements = document.querySelectorAll('.fw-bold');
        boldElements.forEach(element => {
            // Aplicar estilos inline para máximo contraste
            element.style.setProperty('color', '#ffffff', 'important');
            element.style.setProperty('font-weight', '700', 'important');
            element.style.setProperty('background-color', 'rgba(41, 128, 185, 0.9)', 'important');
            element.style.setProperty('padding', '5px 12px', 'important');
            element.style.setProperty('border-radius', '8px', 'important');
            element.style.setProperty('display', 'inline-block', 'important');
            element.style.setProperty('border', '2px solid #3498db', 'important');
            element.style.setProperty('text-shadow', '1px 1px 2px rgba(0, 0, 0, 0.5)', 'important');
            element.style.setProperty('margin-bottom', '4px', 'important');
        });
    }
    
    // Función para mejorar contraste de números de compra
    function enhancePurchaseNumberContrast() {
        const isDarkTheme = document.body.classList.contains('theme-piedra') ||
                           document.body.classList.contains('theme-charcoal') ||
                           document.body.classList.contains('theme-forest') ||
                           document.body.classList.contains('theme-plum');
        
        if (!isDarkTheme) {
            return;
        }
        
        // Buscar todos los elementos strong dentro de tablas (números de compra)
        const tableStrongElements = document.querySelectorAll('.table tbody tr td strong');
        tableStrongElements.forEach(element => {
            // Verificar si parece un número de compra (contiene COMP-)
            const text = element.textContent.trim();
            if (text.includes('COMP-') || text.includes('COMP') || /^[A-Z]+-\d+/.test(text)) {
                // Aplicar estilos específicos para números de compra
                element.style.setProperty('color', '#ffffff', 'important');
                element.style.setProperty('font-weight', '700', 'important');
                element.style.setProperty('background-color', 'rgba(231, 76, 60, 0.9)', 'important');
                element.style.setProperty('padding', '4px 10px', 'important');
                element.style.setProperty('border-radius', '6px', 'important');
                element.style.setProperty('display', 'inline-block', 'important');
                element.style.setProperty('border', '2px solid #e74c3c', 'important');
                element.style.setProperty('text-shadow', '1px 1px 2px rgba(0, 0, 0, 0.5)', 'important');
                element.style.setProperty('font-family', 'Courier New, monospace', 'important');
                element.style.setProperty('letter-spacing', '0.5px', 'important');
            }
        });
    }
    
    // Aplicar mejora de contraste cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            enhanceSmallTextContrast();
            enhanceProductNameContrast();
            enhancePurchaseNumberContrast();
        });
    } else {
        enhanceSmallTextContrast();
        enhanceProductNameContrast();
        enhancePurchaseNumberContrast();
    }
    
    // Aplicar cuando cambie el tema
    const observer2 = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target === document.body) {
                    const hasThemeClass = target.className.includes('theme-');
                    if (hasThemeClass) {
                        setTimeout(function() {
                            enhanceSmallTextContrast();
                            enhanceProductNameContrast();
                            enhancePurchaseNumberContrast();
                        }, 100);
                    }
                }
            }
        });
    });
    
    observer2.observe(document.body, {
        attributes: true,
        attributeFilter: ['class']
    });
    
    // Aplicar periódicamente para elementos dinámicos
    setInterval(function() {
        enhanceSmallTextContrast();
        enhanceProductNameContrast();
        enhancePurchaseNumberContrast();
    }, 3000);
    
})();
