#!/bin/bash
# ÚLTIMO INTENTO: Script más agresivo para restaurar todos los datos posibles

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
echo -e "${BLUE}ÚLTIMO INTENTO - Restauración Agresiva${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Este script:${NC}"
echo "  1. Deshabilitará TODAS las constraints temporalmente"
echo "  2. Limpiará y restaurará con máxima tolerancia a errores"
echo "  3. Intentará restaurar cada INSERT individualmente"
echo ""
echo "¿Continuar? (escribe 'SI'):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo "Cancelado"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/7] Deshabilitando TODAS las constraints...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
-- Deshabilitar triggers
SET session_replication_role = 'replica';

-- Deshabilitar foreign keys temporalmente
ALTER TABLE car_trabajo DISABLE TRIGGER ALL;
ALTER TABLE car_trabajorepuesto DISABLE TRIGGER ALL;
ALTER TABLE car_diagnostico DISABLE TRIGGER ALL;
COMMIT;
SQL
echo -e "${GREEN}✅ Constraints deshabilitadas${NC}"
echo ""

echo -e "${YELLOW}[2/7] Limpiando tablas...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
TRUNCATE TABLE car_trabajorepuesto CASCADE;
TRUNCATE TABLE car_trabajo CASCADE;
TRUNCATE TABLE car_diagnostico CASCADE;
COMMIT;
SQL
echo -e "${GREEN}✅ Tablas limpiadas${NC}"
echo ""

echo -e "${YELLOW}[3/7] Restaurando diagnósticos (INSERT por INSERT)...${NC}"
TEMP_DIAG="/tmp/diagnosticos_individuales_$$.sql"

# Extraer cada INSERT y limpiarlo individualmente
python3 <<'PYTHON'
import re
from pathlib import Path

backup_file = Path("/home/max/myproject/cliente_solutioncar_db.sql")
output_file = Path("/tmp/diagnosticos_individuales.sql")

with open(backup_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Buscar todos los INSERT de car_diagnostico
pattern = r'INSERT INTO public\.car_diagnostico[^;]*\);'
matches = re.findall(pattern, content, re.DOTALL)

# Limpiar cada INSERT (quitar saltos de línea múltiples, espacios extra)
cleaned = []
for match in matches:
    # Limpiar: reemplazar múltiples espacios/newlines por uno solo
    cleaned_line = ' '.join(match.split())
    # Asegurar que termine con );
    if not cleaned_line.rstrip().endswith(');'):
        cleaned_line = cleaned_line.rstrip().rstrip(';') + ');'
    cleaned.append(cleaned_line)

# Guardar
with open(output_file, 'w') as f:
    for line in cleaned:
        f.write(line + '\n')

print(f"✅ {len(cleaned)} INSERT de diagnósticos limpiados")
PYTHON

DIAG_COUNT=$(wc -l < /tmp/diagnosticos_individuales.sql 2>/dev/null || echo "0")
echo "  Total INSERT: $DIAG_COUNT"

# Restaurar uno por uno para ver cuáles fallan
SUCCESS=0
FAILED=0

while IFS= read -r line; do
    if [[ -n "$line" ]]; then
        if echo "$line" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | grep -q "INSERT 0 1"; then
            SUCCESS=$((SUCCESS + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    fi
done < /tmp/diagnosticos_individuales.sql

echo "  Exitosos: $SUCCESS"
echo "  Fallidos: $FAILED"

DIAG_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
echo -e "${GREEN}✅ Diagnósticos en BD: ${DIAG_FINAL}${NC}"
echo ""

echo -e "${YELLOW}[4/7] Restaurando trabajos (INSERT por INSERT)...${NC}"
python3 <<'PYTHON'
import re
from pathlib import Path

backup_file = Path("/home/max/myproject/cliente_solutioncar_db.sql")
output_file = Path("/tmp/trabajos_individuales.sql")

with open(backup_file, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

pattern = r'INSERT INTO public\.car_trabajo[^;]*\);'
matches = re.findall(pattern, content, re.DOTALL)

cleaned = []
for match in matches:
    cleaned_line = ' '.join(match.split())
    if not cleaned_line.rstrip().endswith(');'):
        cleaned_line = cleaned_line.rstrip().rstrip(';') + ');'
    cleaned.append(cleaned_line)

with open(output_file, 'w') as f:
    for line in cleaned:
        f.write(line + '\n')

print(f"✅ {len(cleaned)} INSERT de trabajos limpiados")
PYTHON

TRABAJO_COUNT=$(wc -l < /tmp/trabajos_individuales.sql 2>/dev/null || echo "0")
echo "  Total INSERT: $TRABAJO_COUNT"

SUCCESS=0
FAILED=0

while IFS= read -r line; do
    if [[ -n "$line" ]]; then
        if echo "$line" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | grep -q "INSERT 0 1"; then
            SUCCESS=$((SUCCESS + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    fi
done < /tmp/trabajos_individuales.sql

echo "  Exitosos: $SUCCESS"
echo "  Fallidos: $FAILED"

TRABAJO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
echo -e "${GREEN}✅ Trabajos en BD: ${TRABAJO_FINAL}${NC}"
echo ""

echo -e "${YELLOW}[5/7] Restaurando repuestos...${NC}"
grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -3 || true

REPUESTO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")
echo -e "${GREEN}✅ Repuestos en BD: ${REPUESTO_FINAL}${NC}"
echo ""

echo -e "${YELLOW}[6/7] Rehabilitando constraints...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
SET session_replication_role = 'origin';
ALTER TABLE car_trabajo ENABLE TRIGGER ALL;
ALTER TABLE car_trabajorepuesto ENABLE TRIGGER ALL;
ALTER TABLE car_diagnostico ENABLE TRIGGER ALL;
COMMIT;
SQL
echo -e "${GREEN}✅ Constraints rehabilitadas${NC}"
echo ""

echo -e "${YELLOW}[7/7] Verificación final...${NC}"
DIAG_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
TRABAJO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
REPUESTO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}RESULTADO FINAL:${NC}"
echo "  Diagnósticos: ${DIAG_FINAL} / 171 (${YELLOW}$((DIAG_FINAL * 100 / 171))%${NC})"
echo "  Trabajos: ${TRABAJO_FINAL} / 374 (${YELLOW}$((TRABAJO_FINAL * 100 / 374))%${NC})"
echo "  Repuestos: ${REPUESTO_FINAL} / 88 (${YELLOW}$((REPUESTO_FINAL * 100 / 88))%${NC})"
echo ""

if [[ "$DIAG_FINAL" -lt 100 || "$TRABAJO_FINAL" -lt 200 ]]; then
    echo -e "${RED}⚠️  No se restauraron suficientes datos${NC}"
    echo ""
    echo -e "${YELLOW}Recomendación: Restaurar backup completo${NC}"
    echo "Esto restaurará TODAS las tablas del 11-12-2025"
    echo ""
    echo "Comando:"
    echo "  docker exec postgres_talleres pg_dump -U maxgonpe -d cliente_solutioncar_db > /home/max/backups/backup_antes_restore_completo.sql"
    echo "  docker exec -i postgres_talleres psql -U maxgonpe -d postgres -c \"DROP DATABASE cliente_solutioncar_db; CREATE DATABASE cliente_solutioncar_db OWNER maxgonpe;\""
    echo "  docker exec -i postgres_talleres psql -U maxgonpe -d cliente_solutioncar_db < /home/max/myproject/cliente_solutioncar_db.sql"
else
    echo -e "${GREEN}✅ Restauración exitosa${NC}"
fi

echo -e "${BLUE}========================================${NC}"

# Limpiar archivos temporales
rm -f /tmp/diagnosticos_individuales.sql /tmp/trabajos_individuales.sql 2>/dev/null || true





