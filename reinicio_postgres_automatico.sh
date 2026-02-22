#!/bin/bash
# Script para configurar reinicio automático de PostgreSQL
# Ejecutar en el servidor: /home/max/myproject

POSTGRES_CONTAINER="postgres_talleres"

echo "=========================================="
echo "Configurando Reinicio Automático"
echo "=========================================="
echo ""

# Ver política actual
echo "Política actual:"
CURRENT=$(docker inspect "${POSTGRES_CONTAINER}" --format '{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null)
echo "  ${CURRENT}"
echo ""

# Configurar nueva política
echo "Configurando política 'unless-stopped'..."
if docker update --restart=unless-stopped "${POSTGRES_CONTAINER}"; then
    echo "✅ Configuración exitosa"
else
    echo "❌ Error al configurar"
    exit 1
fi

echo ""

# Verificar
echo "Nueva política:"
NEW=$(docker inspect "${POSTGRES_CONTAINER}" --format '{{.HostConfig.RestartPolicy.Name}}' 2>/dev/null)
echo "  ${NEW}"

if [ "$NEW" = "unless-stopped" ]; then
    echo ""
    echo "✅ Reinicio automático configurado correctamente"
    echo ""
    echo "El contenedor se reiniciará automáticamente:"
    echo "  - Después de reinicio del servidor"
    echo "  - Después de reinicio de Docker"
    echo "  - Si el contenedor falla"
    echo ""
    echo "NO se reiniciará si lo detienes manualmente (docker stop)"
else
    echo "❌ Error: La política no se aplicó correctamente"
    exit 1
fi

echo "=========================================="