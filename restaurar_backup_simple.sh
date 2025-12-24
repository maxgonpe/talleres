#!/bin/bash
# Script simple para restaurar el backup completo

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
echo -e "${BLUE}Restauración de Backup Completo${NC}"
echo -e "${BLUE}Fecha backup: 11-12-2025${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que el backup existe
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}❌ Backup no encontrado: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backup encontrado${NC}"
echo ""

# Verificar contenedor PostgreSQL
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${RED}❌ El contenedor PostgreSQL ${POSTGRES_CONTAINER} no está corriendo${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Contenedor PostgreSQL está corriendo${NC}"
echo ""

# Advertencia importante
echo -e "${RED}⚠️  ADVERTENCIA IMPORTANTE:${NC}"
echo "Este script restaurará TODA la base de datos desde el backup."
echo "Esto SOBRESCRIBIRÁ todos los datos actuales."
echo ""
echo "¿Deseas continuar? (escribe 'SI' para confirmar):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo -e "${YELLOW}Operación cancelada${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/3] Haciendo backup de la BD actual antes de restaurar...${NC}"
BACKUP_ANTES="/home/max/backups/antes_restore_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /home/max/backups
docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${DB_OWNER}" -d "${DB_NAME}" > "${BACKUP_ANTES}" 2>/dev/null

if [[ -f "$BACKUP_ANTES" ]]; then
    SIZE=$(stat -c%s "$BACKUP_ANTES" 2>/dev/null || echo "0")
    echo -e "${GREEN}✅ Backup de seguridad creado: ${BACKUP_ANTES}${NC}"
    echo "   Tamaño: $(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "${SIZE} bytes")"
else
    echo -e "${YELLOW}⚠️  No se pudo crear backup de seguridad, pero continuamos...${NC}"
fi

echo ""
echo -e "${YELLOW}[2/3] Restaurando backup del 11-12-2025...${NC}"

# Restaurar el backup
if docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" < "${BACKUP_FILE}" 2>&1; then
    echo -e "${GREEN}✅ Backup restaurado exitosamente${NC}"
else
    echo -e "${RED}❌ Error al restaurar backup${NC}"
    echo ""
    echo "Si hubo errores, puedes restaurar el backup de seguridad con:"
    echo "docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} < ${BACKUP_ANTES}"
    exit 1
fi

echo ""
echo -e "${YELLOW}[3/3] Verificando datos restaurados...${NC}"

# Verificar trabajos
TRABAJOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")

# Verificar repuestos
REPUESTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo ""
echo -e "${GREEN}✅ Verificación completada:${NC}"
echo "  Trabajos: ${TRABAJOS} registros"
echo "  Repuestos: ${REPUESTOS} registros"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Restauración completada${NC}"
echo -e "${BLUE}========================================${NC}"





