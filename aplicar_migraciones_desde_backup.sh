#!/bin/bash
# Script para aplicar migraciones después de restaurar un backup antiguo
# Esto agregará las columnas faltantes sin perder los datos restaurados

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CLIENTE="solutioncar"
CONTAINER_NAME="cliente_${CLIENTE}"
POSTGRES_CONTAINER="postgres_talleres"
DB_NAME="cliente_${CLIENTE}_db"
DB_OWNER="maxgonpe"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Aplicar Migraciones después de Restore${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar contenedor Django
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ El contenedor ${CONTAINER_NAME} no está corriendo${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Contenedor ${CONTAINER_NAME} está corriendo${NC}"
echo ""

echo -e "${YELLOW}[1/4] Verificando estado de migraciones...${NC}"
echo "----------------------------------------"

# Ver migraciones aplicadas
docker exec -it "${CONTAINER_NAME}" bash -lc "
cd /app
python manage.py showmigrations --plan | head -20
" || echo "No se pudo ver migraciones"

echo ""
echo ""

echo -e "${YELLOW}[2/4] Verificando migraciones pendientes...${NC}"
echo "----------------------------------------"

PENDING=$(docker exec -it "${CONTAINER_NAME}" bash -lc "
cd /app
python manage.py showmigrations 2>&1 | grep '\[ \]' | head -10
" || echo "")

if [[ -n "$PENDING" ]]; then
    echo -e "${YELLOW}⚠️  Migraciones pendientes encontradas:${NC}"
    echo "$PENDING"
else
    echo -e "${GREEN}✅ No se encontraron migraciones pendientes (o todas están aplicadas)${NC}"
fi
echo ""

echo -e "${YELLOW}[3/4] Aplicando migraciones...${NC}"
echo "----------------------------------------"
echo "Esto agregará las columnas faltantes sin perder datos"
echo ""

# Aplicar migraciones
docker exec -it "${CONTAINER_NAME}" bash -lc "
cd /app
python manage.py migrate --noinput
" 2>&1 | tee /tmp/migrate_log_$$.txt

MIGRATE_EXIT=${PIPESTATUS[0]}

if [[ $MIGRATE_EXIT -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}✅ Migraciones aplicadas exitosamente${NC}"
else
    echo ""
    echo -e "${RED}⚠️  Hubo algunos errores durante las migraciones${NC}"
    echo "   Revisa el log: /tmp/migrate_log_$$.txt"
fi
echo ""

echo -e "${YELLOW}[4/4] Verificando columnas faltantes...${NC}"
echo "----------------------------------------"

# Verificar si la columna ver_mensajes existe ahora
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
else
    echo -e "${RED}❌ Columna ver_mensajes NO existe${NC}"
    echo ""
    echo "Intentando agregarla manualmente..."
    
    # Intentar agregar la columna manualmente
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
ALTER TABLE car_administraciontaller 
ADD COLUMN IF NOT EXISTS ver_mensajes boolean DEFAULT true;
SQL
    
    echo -e "${GREEN}✅ Columna agregada manualmente${NC}"
fi

echo ""

# Verificar otras columnas comunes que podrían faltar
echo "Verificando otras columnas importantes..."
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'car_administraciontaller'
AND column_name IN ('ver_mensajes', 'notificaciones_email', 'notificaciones_sms')
ORDER BY column_name;
" 2>/dev/null || true

echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Proceso completado${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Próximos pasos:${NC}"
echo "  1. Reinicia el contenedor Django si es necesario:"
echo "     docker restart ${CONTAINER_NAME}"
echo ""
echo "  2. Verifica que la aplicación funcione correctamente"
echo ""





