
// Script para probar en la consola del navegador
console.log('🔍 Verificando items en la compra 13...');

// Verificar si hay items en el DOM
const itemsTable = document.querySelector('.table-responsive table tbody');
if (itemsTable) {
    const rows = itemsTable.querySelectorAll('tr');
    console.log('📊 Filas en la tabla:', rows.length);
    
    if (rows.length > 0) {
        console.log('✅ Items encontrados en el DOM');
        rows.forEach((row, index) => {
            console.log(`  Fila ${index + 1}:`, row.textContent);
        });
    } else {
        console.log('❌ No hay filas en la tabla');
    }
} else {
    console.log('❌ No se encontró la tabla de items');
}

// Verificar si hay mensaje de "No hay items"
const noItemsMessage = document.querySelector('.text-center.py-4');
if (noItemsMessage) {
    console.log('❌ Mensaje "No hay items" encontrado:', noItemsMessage.textContent);
} else {
    console.log('✅ No hay mensaje "No hay items"');
}

// Verificar debug info
const debugInfo = document.querySelector('.alert-info');
if (debugInfo) {
    console.log('🔍 Debug info:', debugInfo.textContent);
} else {
    console.log('❌ No se encontró debug info');
}
