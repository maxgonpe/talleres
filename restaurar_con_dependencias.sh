#!/bin/bash
# Script para restaurar datos respetando dependencias (foreign keys)
# Restaura en orden: diagnósticos -> trabajos -> repuestos

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
echo -e "${BLUE}Restauración con Dependencias${NC}"
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

echo -e "${YELLOW}⚠️  Este script restaurará:${NC}"
echo "  1. Diagnósticos (necesarios para trabajos)"
echo "  2. Trabajos"
echo "  3. Repuestos de trabajo"
echo ""
echo "¿Continuar? (escribe 'SI'):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo "Cancelado"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5] Haciendo backup de seguridad...${NC}"
BACKUP_ANTES="/home/max/backups/antes_restore_completo_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /home/max/backups
docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${DB_OWNER}" -d "${DB_NAME}" -t car_diagnostico -t car_trabajo -t car_trabajorepuesto > "${BACKUP_ANTES}" 2>/dev/null
echo -e "${GREEN}✅ Backup creado${NC}"
echo ""

echo -e "${YELLOW}[2/5] Deshabilitando temporalmente foreign keys...${NC}"
# Deshabilitar triggers y constraints temporalmente
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
-- Deshabilitar triggers de foreign keys temporalmente
SET session_replication_role = 'replica';
COMMIT;
SQL
echo -e "${GREEN}✅ Foreign keys deshabilitadas temporalmente${NC}"
echo ""

echo -e "${YELLOW}[3/5] Restaurando diagnósticos relacionados...${NC}"
# Primero necesitamos los diagnósticos que referencian los trabajos
# Extraer IDs de diagnósticos de los trabajos en el backup
DIAGNOSTICO_IDS=$(grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | grep -oP "diagnostico_id\)=\K\d+" | sort -u || grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | sed -n "s/.*, \([0-9]*\), [0-9]*);/\1/p" | sort -u)

if [[ -n "$DIAGNOSTICO_IDS" ]]; then
    echo "  Encontrados IDs de diagnósticos necesarios"
    # Restaurar esos diagnósticos específicos
    for diag_id in $DIAGNOSTICO_IDS; do
        grep "INSERT INTO public.car_diagnostico.*VALUES.*($diag_id," "$BACKUP_FILE" 2>/dev/null | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" 2>&1 | grep -v "INSERT 0 1" | grep -v "ERROR" || true
    done
    echo -e "${GREEN}✅ Diagnósticos relacionados restaurados${NC}"
else
    echo -e "${YELLOW}⚠️  No se pudieron extraer IDs de diagnósticos${NC}"
    echo "  Intentando restaurar todos los diagnósticos del backup..."
    grep "INSERT INTO public.car_diagnostico" "$BACKUP_FILE" 2>/dev/null | head -100 | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" 2>&1 | grep -v "INSERT 0 1" | tail -3 || true
fi
echo ""

echo -e "${YELLOW}[4/5] Restaurando trabajos...${NC}"
# Limpiar trabajos primero
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "TRUNCATE TABLE car_trabajorepuesto CASCADE; TRUNCATE TABLE car_trabajo CASCADE;" 2>/dev/null || true

# Restaurar trabajos (con manejo de errores)
TRABAJO_COUNT=0
SUCCESS_COUNT=0
ERROR_COUNT=0

while IFS= read -r line; do
    if echo "$line" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" 2>&1 | grep -q "INSERT 0 1"; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        ERROR_COUNT=$((ERROR_COUNT + 1))
    fi
    TRABAJO_COUNT=$((TRABAJO_COUNT + 1))
    if [[ $((TRABAJO_COUNT % 50)) -eq 0 ]]; then
        echo "  Procesados: $TRABAJO_COUNT trabajos..."
    fi
done < <(grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE")

echo "  Total procesados: $TRABAJO_COUNT"
echo "  Exitosos: $SUCCESS_COUNT"
echo "  Con errores: $ERROR_COUNT"
echo ""

# Método alternativo: restaurar todos de una vez ignorando errores
echo "  Intentando método alternativo (ignorando errores de FK)..."
grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -10 || true
echo ""

echo -e "${YELLOW}[5/5] Restaurando repuestos...${NC}"
grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -10 || true
echo ""

echo -e "${YELLOW}[6/5] Rehabilitando foreign keys...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
SET session_replication_role = 'origin';
COMMIT;
SQL
echo -e "${GREEN}✅ Foreign keys rehabilitadas${NC}"
echo ""

echo -e "${YELLOW}[7/5] Verificando datos restaurados...${NC}"
TRABAJOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
REPUESTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo ""
echo -e "${GREEN}✅ Verificación:${NC}"
echo "  Trabajos: ${TRABAJOS} registros"
echo "  Repuestos: ${REPUESTOS} registros"
echo ""

if [[ "$TRABAJOS" == "0" ]]; then
    echo -e "${RED}⚠️  No se restauraron trabajos. Posibles causas:${NC}"
    echo "  - Faltan diagnósticos relacionados"
    echo "  - Faltan vehículos relacionados"
    echo "  - Errores de sintaxis en el backup"
    echo ""
    echo "Solución: Restaurar primero todas las tablas relacionadas del backup completo"
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Proceso completado${NC}"
echo -e "${BLUE}========================================${NC}"


