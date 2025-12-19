#!/bin/bash
# Script para recuperar datos de trabajos y repuestos desde el backup del 11-12-2025
# Compara estructuras y restaura datos compatibles

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

CLIENTE="solutioncar"
POSTGRES_CONTAINER="postgres_talleres"
DB_NAME="cliente_${CLIENTE}_db"
DB_OWNER="maxgonpe"
BACKUP_FILE="/home/max/myproject/cliente_solutioncar_db.sql"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Recuperación de Datos desde Backup${NC}"
echo -e "${BLUE}Fecha backup: 11-12-2025${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar que el backup existe
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}❌ Backup no encontrado: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backup encontrado: ${BACKUP_FILE}${NC}"
SIZE=$(stat -c%s "$BACKUP_FILE" 2>/dev/null || echo "0")
echo "   Tamaño: $(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "${SIZE} bytes")"
echo ""

# =========================
# 1. Analizar estructuras de tablas
# =========================
echo -e "${YELLOW}[1/5] Analizando estructuras de tablas...${NC}"
echo "----------------------------------------"

# Extraer estructura de car_trabajo del backup
echo "Estructura de car_trabajo en backup:"
BACKUP_TRABAJO_COLS=$(grep -A 15 "CREATE TABLE public.car_trabajo" "$BACKUP_FILE" | grep -E "^\s+[a-z_]+" | sed 's/^[[:space:]]*//' | cut -d' ' -f1 | grep -v "^$" || echo "")
echo "$BACKUP_TRABAJO_COLS" | while read -r col; do
    if [[ -n "$col" ]]; then
        echo "  - $col"
    fi
done

echo ""

# Extraer estructura de car_trabajorepuesto del backup
echo "Estructura de car_trabajorepuesto en backup:"
BACKUP_REPUESTO_COLS=$(grep -A 15 "CREATE TABLE public.car_trabajorepuesto" "$BACKUP_FILE" | grep -E "^\s+[a-z_]+" | sed 's/^[[:space:]]*//' | cut -d' ' -f1 | grep -v "^$" || echo "")
echo "$BACKUP_REPUESTO_COLS" | while read -r col; do
    if [[ -n "$col" ]]; then
        echo "  - $col"
    fi
done

echo ""

# Verificar estructura actual en BD
echo "Estructura actual en base de datos:"
echo "car_trabajo:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "\d car_trabajo" 2>/dev/null | grep -E "^\s+[a-z_]+" | head -15 || echo "  (no se pudo obtener)"

echo ""
echo "car_trabajorepuesto:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "\d car_trabajorepuesto" 2>/dev/null | grep -E "^\s+[a-z_]+" | head -15 || echo "  (no se pudo obtener)"

echo ""

# =========================
# 2. Verificar datos en backup
# =========================
echo -e "${YELLOW}[2/5] Verificando datos en backup...${NC}"
echo "----------------------------------------"

# Contar trabajos en backup
TRABAJOS_BACKUP=$(grep -c "^COPY public.car_trabajo" "$BACKUP_FILE" 2>/dev/null || echo "0")
if [[ "$TRABAJOS_BACKUP" == "0" ]]; then
    # Buscar formato INSERT
    TRABAJOS_BACKUP=$(grep -c "INSERT INTO.*car_trabajo" "$BACKUP_FILE" 2>/dev/null || echo "0")
fi

echo "Trabajos en backup: $TRABAJOS_BACKUP"

# Contar repuestos en backup
REPUESTOS_BACKUP=$(grep -c "^COPY public.car_trabajorepuesto" "$BACKUP_FILE" 2>/dev/null || echo "0")
if [[ "$REPUESTOS_BACKUP" == "0" ]]; then
    REPUESTOS_BACKUP=$(grep -c "INSERT INTO.*car_trabajorepuesto" "$BACKUP_FILE" 2>/dev/null || echo "0")
fi

echo "Repuestos de trabajo en backup: $REPUESTOS_BACKUP"
echo ""

# Mostrar algunos registros de ejemplo
if [[ "$TRABAJOS_BACKUP" != "0" ]]; then
    echo "Primeros registros de trabajos en backup:"
    # Buscar líneas COPY y mostrar algunas siguientes
    COPY_LINE=$(grep -n "^COPY public.car_trabajo" "$BACKUP_FILE" | head -1 | cut -d: -f1)
    if [[ -n "$COPY_LINE" ]]; then
        sed -n "${COPY_LINE},+10p" "$BACKUP_FILE" | head -10 | sed 's/^/  /'
    fi
fi

echo ""

# =========================
# 3. Comparar columnas y detectar diferencias
# =========================
echo -e "${YELLOW}[3/5] Comparando estructuras...${NC}"
echo "----------------------------------------"

# Columnas esperadas en models.py actual (basado en el modelo)
CURRENT_TRABAJO_COLS="id fecha_inicio fecha_fin estado observaciones diagnostico_id vehiculo_id lectura_kilometraje_actual visible"
CURRENT_REPUESTO_COLS="id trabajo_id componente_id repuesto_id repuesto_externo_id cantidad precio_unitario subtotal completado fecha"

echo "Columnas esperadas en models.py actual:"
echo "  car_trabajo: $CURRENT_TRABAJO_COLS"
echo "  car_trabajorepuesto: $CURRENT_REPUESTO_COLS"
echo ""

# Verificar compatibilidad
COMPATIBLE=true
DIFFERENCES=""

# Verificar si hay columnas nuevas en el modelo actual que no están en el backup
echo "Verificando compatibilidad..."
for col in $CURRENT_TRABAJO_COLS; do
    if ! echo "$BACKUP_TRABAJO_COLS" | grep -q "$col"; then
        if [[ "$col" != "id" ]]; then  # id siempre existe
            echo -e "  ${YELLOW}⚠️  Columna nueva en modelo actual: ${col}${NC}"
            DIFFERENCES="${DIFFERENCES}Nueva columna: ${col}\n"
        fi
    fi
done

echo ""

# =========================
# 4. Crear script de restauración
# =========================
echo -e "${YELLOW}[4/5] Preparando restauración...${NC}"
echo "----------------------------------------"

RESTORE_SCRIPT="/tmp/restore_${CLIENTE}_$$.sql"

cat > "$RESTORE_SCRIPT" <<'RESTORE_SQL'
-- Script de restauración de datos desde backup
-- Generado automáticamente

BEGIN;

-- Deshabilitar triggers temporalmente para evitar validaciones
SET session_replication_role = 'replica';

-- Restaurar trabajos (solo si la tabla está vacía)
DO $$
DECLARE
    trabajo_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO trabajo_count FROM car_trabajo;
    
    IF trabajo_count = 0 THEN
        RAISE NOTICE 'Tabla car_trabajo está vacía, restaurando datos...';
    ELSE
        RAISE NOTICE 'Tabla car_trabajo tiene % registros. No se restaurarán datos automáticamente.', trabajo_count;
    END IF;
END $$;

-- Aquí se insertarán los datos del backup
-- (se extraerán en el siguiente paso)

COMMIT;

-- Rehabilitar triggers
SET session_replication_role = 'origin';
RESTORE_SQL

echo -e "${GREEN}✅ Script de restauración creado: ${RESTORE_SCRIPT}${NC}"
echo ""

# =========================
# 5. Extraer datos del backup
# =========================
echo -e "${YELLOW}[5/5] Extrayendo datos del backup...${NC}"
echo "----------------------------------------"

# Extraer datos de car_trabajo
echo "Extrayendo datos de car_trabajo..."
TRABAJO_DATA_FILE="/tmp/trabajos_backup_$$.sql"

# Buscar sección COPY de car_trabajo
COPY_START=$(grep -n "^COPY public.car_trabajo" "$BACKUP_FILE" | head -1 | cut -d: -f1)
if [[ -n "$COPY_START" ]]; then
    # Buscar el final (línea con \.)
    COPY_END=$(sed -n "${COPY_START},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$COPY_END" ]]; then
        ACTUAL_END=$((COPY_START + COPY_END - 1))
        sed -n "${COPY_START},${ACTUAL_END}p" "$BACKUP_FILE" > "$TRABAJO_DATA_FILE"
        echo -e "${GREEN}✅ Datos de trabajos extraídos: $(wc -l < "$TRABAJO_DATA_FILE") líneas${NC}"
    fi
fi

# Extraer datos de car_trabajorepuesto
echo "Extrayendo datos de car_trabajorepuesto..."
REPUESTO_DATA_FILE="/tmp/repuestos_backup_$$.sql"

COPY_START=$(grep -n "^COPY public.car_trabajorepuesto" "$BACKUP_FILE" | head -1 | cut -d: -f1)
if [[ -n "$COPY_START" ]]; then
    COPY_END=$(sed -n "${COPY_START},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$COPY_END" ]]; then
        ACTUAL_END=$((COPY_START + COPY_END - 1))
        sed -n "${COPY_START},${ACTUAL_END}p" "$BACKUP_FILE" > "$REPUESTO_DATA_FILE"
        echo -e "${GREEN}✅ Datos de repuestos extraídos: $(wc -l < "$REPUESTO_DATA_FILE") líneas${NC}"
    fi
fi

echo ""

# =========================
# Resumen y opciones
# =========================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resumen${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Backup analizado: ${BACKUP_FILE}"
echo -e "Trabajos en backup: ${TRABAJOS_BACKUP}"
echo -e "Repuestos en backup: ${REPUESTOS_BACKUP}"
echo ""
echo -e "${CYAN}Archivos generados:${NC}"
echo "  - Script de restauración: ${RESTORE_SCRIPT}"
if [[ -f "$TRABAJO_DATA_FILE" ]]; then
    echo "  - Datos de trabajos: ${TRABAJO_DATA_FILE}"
fi
if [[ -f "$REPUESTO_DATA_FILE" ]]; then
    echo "  - Datos de repuestos: ${REPUESTO_DATA_FILE}"
fi
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE:${NC}"
echo "  1. Revisa las diferencias de estructura antes de restaurar"
echo "  2. Haz un backup de la BD actual antes de restaurar"
echo "  3. Si hay columnas nuevas, necesitarás ajustar los datos"
echo ""
echo -e "${CYAN}Para restaurar los datos:${NC}"
echo "  1. Haz backup de la BD actual:"
echo "     docker exec ${POSTGRES_CONTAINER} pg_dump -U ${DB_OWNER} -d ${DB_NAME} > backup_antes_restore.sql"
echo ""
echo "  2. Restaura los datos:"
if [[ -f "$TRABAJO_DATA_FILE" ]]; then
    echo "     docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} < ${TRABAJO_DATA_FILE}"
fi
if [[ -f "$REPUESTO_DATA_FILE" ]]; then
    echo "     docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} < ${REPUESTO_DATA_FILE}"
fi
echo ""
echo -e "${BLUE}========================================${NC}"

