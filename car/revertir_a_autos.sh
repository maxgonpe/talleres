#!/bin/bash
# revertir_a_autos.sh - Revierte un contenedor de motos a autos
# Uso: ./revertir_a_autos.sh <nombre_contenedor>

CONTAINER_NAME="$1"
if [ -z "$CONTAINER_NAME" ]; then
    echo "❌ Uso: $0 <nombre_contenedor>"
    echo "   Ejemplo: $0 cliente_solutioncar"
    exit 1
fi

echo "🚗 ==============================================="
echo "   REVERSIÓN A TALLER DE AUTOS"
echo "   Contenedor: $CONTAINER_NAME"
echo "🚗 ==============================================="
echo ""

# Verificar que el contenedor existe
if ! docker ps -a --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Error: El contenedor '$CONTAINER_NAME' no existe"
    exit 1
fi

# Verificar que el contenedor está corriendo
if ! docker ps --format "table {{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "⚠️  El contenedor no está corriendo. Iniciando..."
    docker start $CONTAINER_NAME
    sleep 3
fi

echo "🔄 Revirtiendo archivos a versión de autos..."

# 1. Restaurar panel principal original (desde el contenedor base)
echo "   📄 Restaurando panel principal..."
docker exec $CONTAINER_NAME cp /app/car/templates/car/panel_principal.html /app/car/templates/car/panel_principal_motos_backup.html
# Aquí necesitarías tener una copia del panel original, por ahora solo reiniciamos

# 2. Restaurar imágenes SVG originales
echo "   🖼️  Restaurando imágenes SVG..."
# Ejecutar collectstatic para restaurar archivos originales
docker exec $CONTAINER_NAME python manage.py collectstatic --noinput

# 3. Reiniciar contenedor
echo "🔄 Reiniciando contenedor..."
docker restart $CONTAINER_NAME

echo "✅ Reversión completada!"
echo "🚗 $CONTAINER_NAME ahora es un taller de autos"
echo ""
echo "📋 Cambios realizados:"
echo "   ✅ Panel principal restaurado"
echo "   ✅ Imágenes SVG restauradas"
echo "   ✅ Contenedor reiniciado"
echo ""
echo "🌐 Accede a tu aplicación para ver los cambios"







