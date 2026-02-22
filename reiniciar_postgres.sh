#!/bin/bash
# Script para reiniciar PostgreSQL y verificar conectividad
# Ejecutar en el servidor de producción: /home/max/myproject

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

POSTGRES_CONTAINER="postgres_talleres"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Reinicio de PostgreSQL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar si el contenedor existe
if ! docker ps -a --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${RED}❌ Error: El contenedor ${POSTGRES_CONTAINER} no existe${NC}"
    exit 1
fi

# Verificar estado actual
if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${GREEN}✅ El contenedor ya está corriendo${NC}"
    echo "Estado actual:"
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' | grep "${POSTGRES_CONTAINER}"
else
    echo -e "${YELLOW}El contenedor está detenido, intentando iniciar...${NC}"
    
    # Intentar iniciar
    if docker start "${POSTGRES_CONTAINER}"; then
        echo -e "${GREEN}✅ Contenedor iniciado${NC}"
    else
        echo -e "${RED}❌ Error al iniciar el contenedor${NC}"
        echo ""
        echo "Revisando logs de error:"
        docker logs --tail 20 "${POSTGRES_CONTAINER}" 2>&1
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Esperando a que PostgreSQL esté listo...${NC}"

# Esperar hasta 30 segundos para que PostgreSQL esté listo
MAX_WAIT=30
WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    if docker exec "${POSTGRES_CONTAINER}" pg_isready -U maxgonpe >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL está listo para conexiones${NC}"
        break
    fi
    echo -n "."
    sleep 2
    WAITED=$((WAITED + 2))
done

if [ $WAITED -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${RED}❌ PostgreSQL no respondió después de ${MAX_WAIT} segundos${NC}"
    echo "Revisando logs:"
    docker logs --tail 30 "${POSTGRES_CONTAINER}" 2>&1
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}PostgreSQL reiniciado exitosamente${NC}"
echo -e "${BLUE}========================================${NC}"
