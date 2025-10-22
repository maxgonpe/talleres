#!/bin/bash
# inject_motos.sh - Convierte un contenedor de talleres a motos
# Uso: ./inject_motos.sh <nombre_contenedor>

CONTAINER_NAME="$1"
if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Uso: $0 <nombre_contenedor>"
    echo "   Ejemplo: $0 cliente_solutioncar"
    exit 1
fi

echo "🏍️ Convirtiendo $CONTAINER_NAME a taller de motos..."

# Verificar que el contenedor existe
if ! docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Error: El contenedor '$CONTAINER_NAME' no existe"
    echo "   Contenedores disponibles:"
    docker ps -a --format "table {{.Names}}\t{{.Status}}"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "⚠️  El contenedor no está corriendo. Iniciando..."
    docker start $CONTAINER_NAME
    sleep 3
fi

echo "📁 Inyectando archivos de motos..."

# 1. Inyectar panel principal de motos (con permisos)
echo "   📄 Panel principal..."
docker cp otros/archivos_motos/panel_definitivo_motos.html $CONTAINER_NAME:/app/car/templates/car/panel_definitivo.html

# 2. Inyectar imágenes SVG de motos (mismo nombre, contenido diferente)
echo "   🖼️  Imágenes SVG..."
if [ -f "otros/archivos_motos/vehiculo-desde-abajo.svg" ]; then
    docker cp otros/archivos_motos/vehiculo-desde-abajo.svg $CONTAINER_NAME:/app/static/images/vehiculo-desde-abajo.svg
    echo "     ✅ vehiculo-desde-abajo.svg (moto)"
else
    echo "     ⚠️  vehiculo-desde-abajo.svg no encontrado en otros/archivos_motos/"
fi

if [ -f "otros/archivos_motos/motor.svg" ]; then
    docker cp otros/archivos_motos/motor.svg $CONTAINER_NAME:/app/static/images/motor.svg
    echo "     ✅ motor.svg (moto)"
else
    echo "     ⚠️  motor.svg no encontrado en otros/archivos_motos/"
fi

# 3. Copiar otros archivos SVG de motos si existen
echo "   🔧 Otros archivos SVG..."
for svg_file in otros/archivos_motos/*.svg; do
    if [ -f "$svg_file" ]; then
        filename=$(basename "$svg_file")
        if [ "$filename" != "vehiculo-desde-abajo.svg" ] && [ "$filename" != "motor.svg" ]; then
            docker cp "$svg_file" $CONTAINER_NAME:/app/static/images/
            echo "     ✅ $filename"
        fi
    fi
done

# 4. Reiniciar contenedor para aplicar cambios
echo "🔄 Reiniciando contenedor..."
docker restart $CONTAINER_NAME

echo "✅ Conversión completada!"
echo "🏍️ $CONTAINER_NAME ahora es un taller de motos"
echo ""
echo "📋 Archivos inyectados:"
echo "   - Panel principal con iconos de motos 🏍️"
echo "   - Plano interactivo de moto"
echo "   - Motor de moto"
echo "   - Otros archivos SVG específicos de motos"
echo ""
echo "🌐 Accede a tu aplicación para ver los cambios"
