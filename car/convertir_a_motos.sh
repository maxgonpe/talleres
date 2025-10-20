#!/bin/bash
# convertir_a_motos.sh - Script completo para convertir talleres a motos
# Uso: ./convertir_a_motos.sh <nombre_contenedor>

CONTAINER_NAME="$1"
if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Uso: $0 <nombre_contenedor>"
    echo "   Ejemplo: $0 cliente_solutioncar"
    echo ""
    echo "📋 Contenedores disponibles:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    exit 1
fi

echo "🏍️ ==============================================="
echo "   CONVERSIÓN A TALLER DE MOTOS"
echo "   Contenedor: $CONTAINER_NAME"
echo "🏍️ ==============================================="
echo ""

# Verificar que el contenedor existe
if ! docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Error: El contenedor '$CONTAINER_NAME' no existe"
    echo ""
    echo "📋 Contenedores disponibles:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "⚠️  El contenedor no está corriendo. Iniciando..."
    docker start $CONTAINER_NAME
    sleep 3
fi

echo "📁 Verificando archivos de motos..."

# Verificar que existen los archivos necesarios
if [ ! -f "otros/archivos_motos/panel_principal.html" ]; then
    echo "❌ Error: No se encuentra panel_principal.html"
    exit 1
fi

if [ ! -f "otros/archivos_motos/vehiculo-desde-abajo.svg" ]; then
    echo "❌ Error: No se encuentra vehiculo-desde-abajo.svg"
    exit 1
fi

if [ ! -f "otros/archivos_motos/motor.svg" ]; then
    echo "❌ Error: No se encuentra motor.svg"
    exit 1
fi

echo "✅ Archivos de motos encontrados"
echo ""

# Ejecutar la inyección
echo "🚀 Ejecutando inyección de archivos..."
./inject_motos.sh $CONTAINER_NAME

echo ""
echo "🎉 ¡CONVERSIÓN COMPLETADA!"
echo ""
echo "📋 Resumen de cambios:"
echo "   ✅ Panel principal actualizado con iconos de motos 🏍️"
echo "   ✅ Plano interactivo cambiado a moto"
echo "   ✅ Motor actualizado para moto"
echo "   ✅ Contenedor reiniciado"
echo ""
echo "🌐 Tu aplicación ahora es un taller de motos"
echo "   Accede a tu dominio para ver los cambios"
echo ""
echo "💡 Para revertir a autos, ejecuta:"
echo "   ./revertir_a_autos.sh $CONTAINER_NAME"
