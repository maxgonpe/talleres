#!/bin/bash
# Script para verificar logs de contenedores Django
# Ejecutar en el servidor de producción: /home/max/myproject

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verificación de Logs Django${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Listar contenedores de clientes
CLIENTE_CONTAINERS=$(docker ps --format '{{.Names}}' | grep "^cliente_")
if [ -z "$CLIENTE_CONTAINERS" ]; then
    echo -e "${RED}❌ No se encontraron contenedores de clientes corriendo${NC}"
    exit 1
fi

# Verificar logs de cada contenedor
echo "$CLIENTE_CONTAINERS" | while read -r container; do
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}Logs de ${container}${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    # Mostrar últimas 30 líneas de logs
    echo -e "${YELLOW}Últimas 30 líneas de logs:${NC}"
    docker logs --tail 30 "$container" 2>&1 | sed 's/^/  /'
    
    echo ""
    
    # Buscar errores relacionados con base de datos
    echo -e "${YELLOW}Buscando errores de base de datos:${NC}"
    DB_ERRORS=$(docker logs "$container" 2>&1 | grep -iE "database|postgres|connection|operationalerror|could not connect" | tail -10)
    if [ -n "$DB_ERRORS" ]; then
        echo -e "${RED}⚠️  Se encontraron errores relacionados con BD:${NC}"
        echo "$DB_ERRORS" | sed 's/^/  /'
    else
        echo -e "${GREEN}✅ No se encontraron errores de base de datos recientes${NC}"
    fi
    
    echo ""
    
    # Verificar si hay errores de Bad Gateway o 502
    echo -e "${YELLOW}Buscando errores de Bad Gateway:${NC}"
    GATEWAY_ERRORS=$(docker logs "$container" 2>&1 | grep -iE "bad gateway|502|gateway" | tail -5)
    if [ -n "$GATEWAY_ERRORS" ]; then
        echo -e "${RED}⚠️  Se encontraron errores de Bad Gateway:${NC}"
        echo "$GATEWAY_ERRORS" | sed 's/^/  /'
    else
        echo -e "${GREEN}✅ No se encontraron errores de Bad Gateway${NC}"
    fi
    
    echo ""
    echo ""
done

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Verificación de logs completada${NC}"
echo -e "${BLUE}========================================${NC}"
