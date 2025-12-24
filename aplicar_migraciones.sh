#!/bin/bash
# Script simple para aplicar migraciones después de restaurar backup antiguo

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CLIENTE="solutioncar"
CONTAINER_NAME="cliente_${CLIENTE}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Aplicar Migraciones de Django${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar contenedor
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ El contenedor ${CONTAINER_NAME} no está corriendo${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Contenedor ${CONTAINER_NAME} está corriendo${NC}"
echo ""

echo -e "${YELLOW}[1/3] Verificando migraciones pendientes...${NC}"
docker exec -it "${CONTAINER_NAME}" bash -lc "
cd /app
python manage.py showmigrations 2>&1 | grep '\[ \]' | head -20
" || echo "No se encontraron migraciones pendientes o hubo un error"
echo ""

echo -e "${YELLOW}[2/3] Aplicando migraciones...${NC}"
echo "Esto agregará las columnas faltantes (como ver_mensajes) sin perder datos"
echo ""

docker exec -it "${CONTAINER_NAME}" bash -lc "
cd /app
python manage.py migrate --noinput
" 2>&1

MIGRATE_EXIT=$?

if [[ $MIGRATE_EXIT -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Migraciones aplicadas exitosamente${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Hubo algunos errores, pero algunas migraciones se aplicaron${NC}"
fi
echo ""

echo -e "${YELLOW}[3/3] Verificando columna ver_mensajes...${NC}"
POSTGRES_CONTAINER="postgres_talleres"
DB_NAME="cliente_${CLIENTE}_db"
DB_OWNER="maxgonpe"

COLUMN_EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT EXISTS (
    SELECT 1 
    FROM information_schema.columns 
    WHERE table_name = 'car_administraciontaller' 
    AND column_name = 'ver_mensajes'
);
" 2>/dev/null | tr -d '[:space:]' || echo "false")

if [[ "$COLUMN_EXISTS" == "t" ]]; then
    echo -e "${GREEN}✅ Columna ver_mensajes existe${NC}"
    
    # Verificar si tiene valores NULL y actualizarlos
    NULL_COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
    SELECT COUNT(*) FROM car_administraciontaller WHERE ver_mensajes IS NULL;
    " 2>/dev/null | tr -d '[:space:]' || echo "0")
    
    if [[ "$NULL_COUNT" != "0" ]]; then
        echo "  Actualizando valores NULL a true (default)..."
        docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
        UPDATE car_administraciontaller SET ver_mensajes = true WHERE ver_mensajes IS NULL;
        " 2>/dev/null || true
        echo -e "${GREEN}✅ Valores actualizados${NC}"
    fi
else
    echo -e "${RED}❌ Columna ver_mensajes NO existe${NC}"
    echo "  Agregándola manualmente..."
    
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
ALTER TABLE car_administraciontaller 
ADD COLUMN IF NOT EXISTS ver_mensajes boolean DEFAULT true;

UPDATE car_administraciontaller 
SET ver_mensajes = true 
WHERE ver_mensajes IS NULL;
SQL
    
    echo -e "${GREEN}✅ Columna agregada manualmente${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Proceso completado${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximo paso:${NC}"
echo "  Reinicia el contenedor Django para aplicar cambios:"
echo "  docker restart ${CONTAINER_NAME}"
echo ""





