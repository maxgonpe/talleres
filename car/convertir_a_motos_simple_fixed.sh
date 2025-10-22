#!/bin/bash
# convertir_a_motos_simple.sh - Convierte un contenedor a motos (solo 3 archivos)
# Uso: ./convertir_a_motos_simple.sh <nombre_contenedor>

CONTAINER_NAME="$1"
if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Uso: $0 <nombre_contenedor>"
    echo "   Ejemplo: $0 cliente_solutioncar"
    exit 1
fi

echo "🏍️ Convirtiendo $CONTAINER_NAME a motos..."

# Verificar que el contenedor existe
if ! docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Error: El contenedor '$CONTAINER_NAME' no existe"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "⚠️  Iniciando contenedor..."
    docker start $CONTAINER_NAME
    sleep 3
fi

echo "📁 Inyectando archivos de motos..."

# 1. Panel definitivo con iconos de motos (CORREGIDO)
echo "   📄 Panel definitivo..."
docker cp otros/archivos_motos/panel_definitivo_motos.html $CONTAINER_NAME:/app/car/templates/car/panel_definitivo.html

# 2. Plano interactivo de moto
echo "   🖼️  Plano interactivo..."
docker cp otros/archivos_motos/vehiculo-desde-abajo.svg $CONTAINER_NAME:/app/static/images/vehiculo-desde-abajo.svg

# 3. Motor de moto
echo "   🔧 Motor..."
docker cp otros/archivos_motos/motor.svg $CONTAINER_NAME:/app/static/images/motor.svg

# 4. Reiniciar contenedor
echo "🔄 Reiniciando contenedor..."
docker restart $CONTAINER_NAME

echo "✅ ¡Conversión completada!"
echo "🏍️ $CONTAINER_NAME ahora es un taller de motos"
echo ""
echo "📋 Archivos cambiados:"
echo "   ✅ panel_definitivo.html (iconos 🏍️ + permisos)"
echo "   ✅ vehiculo-desde-abajo.svg (plano de moto)"
echo "   ✅ motor.svg (motor de moto)"
echo ""
echo "🌐 Accede a tu aplicación para ver los cambios"






