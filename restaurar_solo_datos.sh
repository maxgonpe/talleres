#!/bin/bash
# Script para restaurar SOLO los datos (INSERT) sin las estructuras
# Esto evita los errores de tablas existentes

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CLIENTE="solutioncar"
POSTGRES_CONTAINER="postgres_talleres"
DB_NAME="cliente_${CLIENTE}_db"
DB_OWNER="maxgonpe"
BACKUP_FILE="/home/max/myproject/cliente_solutioncar_db.sql"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Restauración SOLO de DATOS${NC}"
echo -e "${BLUE}Fecha backup: 11-12-2025${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar backup
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}❌ Backup no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backup encontrado${NC}"
echo ""

# Advertencia
echo -e "${YELLOW}⚠️  Este script:${NC}"
echo "  1. Limpiará las tablas car_trabajo y car_trabajorepuesto"
echo "  2. Restaurará SOLO los datos (INSERT) desde el backup"
echo "  3. NO afectará otras tablas"
echo ""
echo "¿Continuar? (escribe 'SI'):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo "Cancelado"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/4] Haciendo backup de seguridad...${NC}"
BACKUP_ANTES="/home/max/backups/antes_restore_datos_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /home/max/backups
docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${DB_OWNER}" -d "${DB_NAME}" -t car_trabajo -t car_trabajorepuesto > "${BACKUP_ANTES}" 2>/dev/null
echo -e "${GREEN}✅ Backup creado: ${BACKUP_ANTES}${NC}"
echo ""

echo -e "${YELLOW}[2/4] Limpiando tablas...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
TRUNCATE TABLE car_trabajorepuesto CASCADE;
TRUNCATE TABLE car_trabajo CASCADE;
COMMIT;
SQL
echo -e "${GREEN}✅ Tablas limpiadas${NC}"
echo ""

echo -e "${YELLOW}[3/4] Extrayendo y restaurando datos de trabajos...${NC}"
# Extraer solo los INSERT de car_trabajo
TRABAJO_INSERTS=$(grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | wc -l)
echo "  Encontrados: $TRABAJO_INSERTS registros"

if [[ $TRABAJO_INSERTS -gt 0 ]]; then
    grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" 2>&1 | grep -v "INSERT 0 1" | tail -5 || true
    echo -e "${GREEN}✅ Trabajos restaurados${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontraron trabajos en el backup${NC}"
fi
echo ""

echo -e "${YELLOW}[4/4] Extrayendo y restaurando datos de repuestos...${NC}"
# Extraer solo los INSERT de car_trabajorepuesto
REPUESTO_INSERTS=$(grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | wc -l)
echo "  Encontrados: $REPUESTO_INSERTS registros"

if [[ $REPUESTO_INSERTS -gt 0 ]]; then
    grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" 2>&1 | grep -v "INSERT 0 1" | tail -5 || true
    echo -e "${GREEN}✅ Repuestos restaurados${NC}"
else
    echo -e "${YELLOW}⚠️  No se encontraron repuestos en el backup${NC}"
fi
echo ""

echo -e "${YELLOW}[5/4] Verificando datos restaurados...${NC}"
TRABAJOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
REPUESTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo ""
echo -e "${GREEN}✅ Verificación:${NC}"
echo "  Trabajos: ${TRABAJOS} registros"
echo "  Repuestos: ${REPUESTOS} registros"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Restauración completada${NC}"
echo -e "${BLUE}========================================${NC}"


