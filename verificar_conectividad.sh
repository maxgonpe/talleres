#!/bin/bash
# Script para verificar conectividad desde contenedores de clientes
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
echo -e "${BLUE}Verificación de Conectividad${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que PostgreSQL esté corriendo
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${RED}❌ Error: El contenedor ${POSTGRES_CONTAINER} no está corriendo${NC}"
    exit 1
fi

# Verificar que PostgreSQL esté listo
echo -e "${YELLOW}[1/4] Verificando que PostgreSQL esté listo...${NC}"
if docker exec "${POSTGRES_CONTAINER}" pg_isready -U maxgonpe >/dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL está listo${NC}"
else
    echo -e "${RED}❌ PostgreSQL no está respondiendo${NC}"
    exit 1
fi

echo ""

# Listar contenedores de clientes
echo -e "${YELLOW}[2/4] Contenedores de clientes encontrados:${NC}"
CLIENTE_CONTAINERS=$(docker ps --format '{{.Names}}' | grep "^cliente_")
if [ -z "$CLIENTE_CONTAINERS" ]; then
    echo -e "${RED}❌ No se encontraron contenedores de clientes corriendo${NC}"
    exit 1
fi

echo "$CLIENTE_CONTAINERS" | while read -r container; do
    echo "  - $container"
done

echo ""

# Verificar conectividad desde cada contenedor
echo -e "${YELLOW}[3/4] Verificando conectividad desde contenedores Django...${NC}"
echo "$CLIENTE_CONTAINERS" | while read -r container; do
    echo ""
    echo -e "${BLUE}Verificando ${container}...${NC}"
    
    # Verificar variables de entorno de BD
    echo "  Variables de entorno de BD:"
    docker exec "$container" env 2>/dev/null | grep -E "^DB_|^DATABASE" | sed 's/^/    /' || echo "    No se encontraron variables DB_*"
    
    # Intentar verificar conexión con Django
    echo "  Verificando conexión Django:"
    if docker exec "$container" python manage.py check --database default 2>&1 | head -5 | sed 's/^/    /'; then
        echo -e "    ${GREEN}✅ Conexión exitosa${NC}"
    else
        echo -e "    ${RED}❌ Error en la conexión${NC}"
        echo "    Últimos logs del contenedor:"
        docker logs --tail 10 "$container" 2>&1 | sed 's/^/      /' | head -5
    fi
done

echo ""

# Verificar bases de datos disponibles
echo -e "${YELLOW}[4/4] Bases de datos disponibles en PostgreSQL:${NC}"
docker exec "${POSTGRES_CONTAINER}" psql -U maxgonpe -d postgres -c "\l" 2>/dev/null | grep "cliente_" || echo "No se encontraron bases de datos de clientes"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Verificación completada${NC}"
echo -e "${BLUE}========================================${NC}"
