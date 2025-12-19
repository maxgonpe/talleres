#!/bin/bash
# Script que limpia los INSERT problemáticos (saltos de línea) y restaura correctamente

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
echo -e "${BLUE}Restauración con Limpieza de SQL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}❌ Backup no encontrado${NC}"
    exit 1
fi

echo -e "${YELLOW}Este script:${NC}"
echo "  1. Limpiará INSERT con saltos de línea problemáticos"
echo "  2. Restaurará diagnósticos correctamente"
echo "  3. Luego trabajos y repuestos"
echo ""
echo "¿Continuar? (escribe 'SI'):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo "Cancelado"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5] Limpiando tablas...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SET session_replication_role = 'replica';
BEGIN;
TRUNCATE TABLE car_trabajorepuesto CASCADE;
TRUNCATE TABLE car_trabajo CASCADE;
TRUNCATE TABLE car_diagnostico CASCADE;
COMMIT;
SQL
echo -e "${GREEN}✅ Tablas limpiadas${NC}"
echo ""

echo -e "${YELLOW}[2/5] Extrayendo y limpiando INSERT de diagnósticos...${NC}"
TEMP_DIAG="/tmp/diagnosticos_limpios_$$.sql"

# Extraer INSERT de diagnósticos y limpiar saltos de línea problemáticos
# Buscar desde INSERT hasta el siguiente INSERT o fin de línea
awk '
/^INSERT INTO public\.car_diagnostico/ {
    line = $0
    while (getline > 0) {
        if (/^INSERT INTO/ || /^COPY/ || /^\\\./) {
            print line ";"
            line = $0
            break
        }
        line = line " " $0
        if (line ~ /\);$/) {
            print line
            line = ""
            break
        }
    }
    if (line) print line ";"
}
' "$BACKUP_FILE" | grep "INSERT INTO public.car_diagnostico" > "$TEMP_DIAG" 2>/dev/null || {
    # Método alternativo: buscar líneas que contengan INSERT y unir hasta encontrar );
    grep -A 10 "INSERT INTO public.car_diagnostico" "$BACKUP_FILE" | \
    awk '/INSERT INTO/ {line=$0; next} {line=line" "$0} /\);$/ {print line; line=""}' > "$TEMP_DIAG" 2>/dev/null || true
}

DIAG_COUNT=$(wc -l < "$TEMP_DIAG" 2>/dev/null || echo "0")
echo "  INSERT limpios: $DIAG_COUNT"

if [[ $DIAG_COUNT -gt 0 ]]; then
    echo "  Restaurando diagnósticos..."
    cat "$TEMP_DIAG" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | grep -E "INSERT|ERROR" | tail -10 || true
    
    DIAG_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    echo -e "${GREEN}✅ Diagnósticos restaurados: ${DIAG_FINAL}${NC}"
else
    echo -e "${RED}❌ No se pudieron extraer diagnósticos${NC}"
fi
echo ""

echo -e "${YELLOW}[3/5] Limpiando y restaurando trabajos...${NC}"
TEMP_TRABAJO="/tmp/trabajos_limpios_$$.sql"

# Limpiar INSERT de trabajos
awk '
/^INSERT INTO public\.car_trabajo/ {
    line = $0
    while (getline > 0) {
        if (/^INSERT INTO/ || /^COPY/ || /^\\\./) {
            print line ";"
            line = $0
            break
        }
        line = line " " $0
        if (line ~ /\);$/) {
            print line
            line = ""
            break
        }
    }
    if (line) print line ";"
}
' "$BACKUP_FILE" | grep "INSERT INTO public.car_trabajo" > "$TEMP_TRABAJO" 2>/dev/null || {
    # Método alternativo
    grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | sed 's/\n/ /g' | sed 's/);/);\n/g' > "$TEMP_TRABAJO" 2>/dev/null || true
}

TRABAJO_COUNT=$(wc -l < "$TEMP_TRABAJO" 2>/dev/null || echo "0")
echo "  INSERT limpios: $TRABAJO_COUNT"

if [[ $TRABAJO_COUNT -gt 0 ]]; then
    echo "  Restaurando trabajos..."
    cat "$TEMP_TRABAJO" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | grep -E "INSERT|ERROR" | tail -10 || true
    
    TRABAJO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    echo -e "${GREEN}✅ Trabajos restaurados: ${TRABAJO_FINAL}${NC}"
else
    echo -e "${RED}❌ No se pudieron extraer trabajos${NC}"
fi
echo ""

echo -e "${YELLOW}[4/5] Restaurando repuestos...${NC}"
grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | grep -E "INSERT|ERROR" | tail -5 || true

REPUESTO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")
echo -e "${GREEN}✅ Repuestos restaurados: ${REPUESTO_FINAL}${NC}"
echo ""

echo -e "${YELLOW}[5/5] Rehabilitando foreign keys...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SET session_replication_role = 'origin';
SQL
echo -e "${GREEN}✅ Foreign keys rehabilitadas${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Resumen Final:${NC}"
echo "  Diagnósticos: ${DIAG_FINAL:-0}"
echo "  Trabajos: ${TRABAJO_FINAL:-0}"
echo "  Repuestos: ${REPUESTO_FINAL:-0}"
echo -e "${BLUE}========================================${NC}"

# Limpiar archivos temporales
rm -f "$TEMP_DIAG" "$TEMP_TRABAJO" 2>/dev/null || true


