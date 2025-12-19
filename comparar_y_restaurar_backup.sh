#!/bin/bash
# Script completo para comparar estructuras y restaurar datos del backup

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
echo -e "${BLUE}Comparación y Restauración desde Backup${NC}"
echo -e "${BLUE}Backup: 11-12-2025${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# ANÁLISIS DE ESTRUCTURAS
# =========================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}ANÁLISIS DE ESTRUCTURAS${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Estructura del backup - car_trabajo
echo -e "${YELLOW}📋 Tabla: car_trabajo${NC}"
echo "----------------------------------------"
echo -e "${BLUE}Estructura en BACKUP (11-12-2025):${NC}"
BACKUP_TRABAJO="id | fecha_inicio | fecha_fin | estado | observaciones | diagnostico_id | vehiculo_id | lectura_kilometraje_actual | visible"
echo "  Columnas: $BACKUP_TRABAJO"
echo ""

# Estructura actual en BD
echo -e "${BLUE}Estructura ACTUAL en base de datos:${NC}"
CURRENT_TRABAJO_COLS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'car_trabajo' 
AND table_schema = 'public'
ORDER BY ordinal_position;
" 2>/dev/null | tr '\n' '|' | sed 's/|$//' || echo "No disponible")

if [[ "$CURRENT_TRABAJO_COLS" != "No disponible" ]]; then
    echo "  Columnas: $CURRENT_TRABAJO_COLS"
    
    # Comparar
    BACKUP_COLS_ARRAY=($(echo "$BACKUP_TRABAJO" | tr '|' ' '))
    CURRENT_COLS_ARRAY=($(echo "$CURRENT_TRABAJO_COLS" | tr '|' ' '))
    
    echo ""
    echo -e "${GREEN}✅ Comparación:${NC}"
    MISSING_IN_CURRENT=""
    MISSING_IN_BACKUP=""
    
    for col in "${BACKUP_COLS_ARRAY[@]}"; do
        col=$(echo "$col" | xargs)  # trim
        if [[ ! " ${CURRENT_COLS_ARRAY[@]} " =~ " ${col} " ]]; then
            MISSING_IN_CURRENT="${MISSING_IN_CURRENT} ${col}"
        fi
    done
    
    for col in "${CURRENT_COLS_ARRAY[@]}"; do
        col=$(echo "$col" | xargs)  # trim
        if [[ ! " ${BACKUP_COLS_ARRAY[@]} " =~ " ${col} " ]]; then
            MISSING_IN_BACKUP="${MISSING_IN_BACKUP} ${col}"
        fi
    done
    
    if [[ -z "$MISSING_IN_CURRENT" && -z "$MISSING_IN_BACKUP" ]]; then
        echo -e "  ${GREEN}✅ Estructuras IDÉNTICAS - Compatible para restauración${NC}"
    else
        if [[ -n "$MISSING_IN_CURRENT" ]]; then
            echo -e "  ${YELLOW}⚠️  Columnas en backup que no están en BD actual:${MISSING_IN_CURRENT}${NC}"
        fi
        if [[ -n "$MISSING_IN_BACKUP" ]]; then
            echo -e "  ${YELLOW}⚠️  Columnas nuevas en BD actual (se llenarán con NULL o default):${MISSING_IN_BACKUP}${NC}"
        fi
    fi
else
    echo -e "  ${RED}❌ No se pudo obtener estructura actual${NC}"
fi

echo ""
echo ""

# Estructura del backup - car_trabajorepuesto
echo -e "${YELLOW}📋 Tabla: car_trabajorepuesto${NC}"
echo "----------------------------------------"
echo -e "${BLUE}Estructura en BACKUP (11-12-2025):${NC}"
BACKUP_REPUESTO="id | cantidad | precio_unitario | subtotal | repuesto_id | trabajo_id | componente_id | completado | fecha | repuesto_externo_id"
echo "  Columnas: $BACKUP_REPUESTO"
echo ""

# Estructura actual en BD
echo -e "${BLUE}Estructura ACTUAL en base de datos:${NC}"
CURRENT_REPUESTO_COLS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'car_trabajorepuesto' 
AND table_schema = 'public'
ORDER BY ordinal_position;
" 2>/dev/null | tr '\n' '|' | sed 's/|$//' || echo "No disponible")

if [[ "$CURRENT_REPUESTO_COLS" != "No disponible" ]]; then
    echo "  Columnas: $CURRENT_REPUESTO_COLS"
    
    # Comparar
    BACKUP_COLS_ARRAY=($(echo "$BACKUP_REPUESTO" | tr '|' ' '))
    CURRENT_COLS_ARRAY=($(echo "$CURRENT_REPUESTO_COLS" | tr '|' ' '))
    
    echo ""
    echo -e "${GREEN}✅ Comparación:${NC}"
    MISSING_IN_CURRENT=""
    MISSING_IN_BACKUP=""
    
    for col in "${BACKUP_COLS_ARRAY[@]}"; do
        col=$(echo "$col" | xargs)  # trim
        if [[ ! " ${CURRENT_COLS_ARRAY[@]} " =~ " ${col} " ]]; then
            MISSING_IN_CURRENT="${MISSING_IN_CURRENT} ${col}"
        fi
    done
    
    for col in "${CURRENT_COLS_ARRAY[@]}"; do
        col=$(echo "$col" | xargs)  # trim
        if [[ ! " ${BACKUP_COLS_ARRAY[@]} " =~ " ${col} " ]]; then
            MISSING_IN_BACKUP="${MISSING_IN_BACKUP} ${col}"
        fi
    done
    
    if [[ -z "$MISSING_IN_CURRENT" && -z "$MISSING_IN_BACKUP" ]]; then
        echo -e "  ${GREEN}✅ Estructuras IDÉNTICAS - Compatible para restauración${NC}"
    else
        if [[ -n "$MISSING_IN_CURRENT" ]]; then
            echo -e "  ${YELLOW}⚠️  Columnas en backup que no están en BD actual:${MISSING_IN_CURRENT}${NC}"
        fi
        if [[ -n "$MISSING_IN_BACKUP" ]]; then
            echo -e "  ${YELLOW}⚠️  Columnas nuevas en BD actual (se llenarán con NULL o default):${MISSING_IN_BACKUP}${NC}"
        fi
    fi
else
    echo -e "  ${RED}❌ No se pudo obtener estructura actual${NC}"
fi

echo ""
echo ""

# =========================
# VERIFICAR DATOS EN BACKUP
# =========================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}VERIFICACIÓN DE DATOS EN BACKUP${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Buscar datos de trabajos
COPY_TRABAJO_LINE=$(grep -n "^COPY public.car_trabajo" "$BACKUP_FILE" | head -1 | cut -d: -f1)
if [[ -n "$COPY_TRABAJO_LINE" ]]; then
    # Contar líneas de datos (hasta \.)
    DATA_END=$(sed -n "${COPY_TRABAJO_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$DATA_END" ]]; then
        DATA_LINES=$((DATA_END - 1))
        echo -e "${GREEN}✅ Trabajos encontrados en backup:${NC}"
        echo "  Formato: COPY (PostgreSQL)"
        echo "  Líneas de datos: $DATA_LINES"
        
        # Mostrar primeros registros
        echo ""
        echo "  Primeros 3 registros:"
        sed -n "$((COPY_TRABAJO_LINE + 1)),$((COPY_TRABAJO_LINE + 3))p" "$BACKUP_FILE" | sed 's/^/    /'
    fi
else
    echo -e "${YELLOW}⚠️  No se encontraron datos en formato COPY${NC}"
    # Buscar INSERT
    INSERT_COUNT=$(grep -c "INSERT INTO.*car_trabajo" "$BACKUP_FILE" 2>/dev/null || echo "0")
    if [[ "$INSERT_COUNT" != "0" ]]; then
        echo "  Formato: INSERT"
        echo "  Registros: $INSERT_COUNT"
    fi
fi

echo ""

# Buscar datos de repuestos
COPY_REPUESTO_LINE=$(grep -n "^COPY public.car_trabajorepuesto" "$BACKUP_FILE" | head -1 | cut -d: -f1)
if [[ -n "$COPY_REPUESTO_LINE" ]]; then
    DATA_END=$(sed -n "${COPY_REPUESTO_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$DATA_END" ]]; then
        DATA_LINES=$((DATA_END - 1))
        echo -e "${GREEN}✅ Repuestos de trabajo encontrados en backup:${NC}"
        echo "  Formato: COPY (PostgreSQL)"
        echo "  Líneas de datos: $DATA_LINES"
        
        # Mostrar primeros registros
        echo ""
        echo "  Primeros 3 registros:"
        sed -n "$((COPY_REPUESTO_LINE + 1)),$((COPY_REPUESTO_LINE + 3))p" "$BACKUP_FILE" | sed 's/^/    /'
    fi
else
    echo -e "${YELLOW}⚠️  No se encontraron datos en formato COPY${NC}"
    INSERT_COUNT=$(grep -c "INSERT INTO.*car_trabajorepuesto" "$BACKUP_FILE" 2>/dev/null || echo "0")
    if [[ "$INSERT_COUNT" != "0" ]]; then
        echo "  Formato: INSERT"
        echo "  Registros: $INSERT_COUNT"
    fi
fi

echo ""
echo ""

# =========================
# INSTRUCCIONES DE RESTAURACIÓN
# =========================
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}INSTRUCCIONES DE RESTAURACIÓN${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}⚠️  IMPORTANTE - Lee esto antes de restaurar:${NC}"
echo ""
echo "1. ${RED}Haz un backup de la BD actual ANTES de restaurar:${NC}"
echo "   docker exec ${POSTGRES_CONTAINER} pg_dump -U ${DB_OWNER} -d ${DB_NAME} > /home/max/backups/antes_restore_$(date +%Y%m%d_%H%M%S).sql"
echo ""
echo "2. Verifica que la tabla car_trabajo esté vacía:"
echo "   docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} -c \"SELECT COUNT(*) FROM car_trabajo;\""
echo ""
echo "3. ${GREEN}Para restaurar los datos:${NC}"
echo ""

# Extraer y crear archivos de datos
TEMP_DIR="/tmp/restore_${CLIENTE}_$$"
mkdir -p "$TEMP_DIR"

if [[ -n "$COPY_TRABAJO_LINE" ]]; then
    DATA_END=$(sed -n "${COPY_TRABAJO_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$DATA_END" ]]; then
        ACTUAL_END=$((COPY_TRABAJO_LINE + DATA_END - 1))
        sed -n "${COPY_TRABAJO_LINE},${ACTUAL_END}p" "$BACKUP_FILE" > "${TEMP_DIR}/trabajos.sql"
        echo "   Trabajos extraídos a: ${TEMP_DIR}/trabajos.sql"
        echo "   Restaurar con:"
        echo "   docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} < ${TEMP_DIR}/trabajos.sql"
    fi
fi

echo ""

if [[ -n "$COPY_REPUESTO_LINE" ]]; then
    DATA_END=$(sed -n "${COPY_REPUESTO_LINE},\$p" "$BACKUP_FILE" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
    if [[ -n "$DATA_END" ]]; then
        ACTUAL_END=$((COPY_REPUESTO_LINE + DATA_END - 1))
        sed -n "${COPY_REPUESTO_LINE},${ACTUAL_END}p" "$BACKUP_FILE" > "${TEMP_DIR}/repuestos.sql"
        echo "   Repuestos extraídos a: ${TEMP_DIR}/repuestos.sql"
        echo "   Restaurar con:"
        echo "   docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} < ${TEMP_DIR}/repuestos.sql"
    fi
fi

echo ""
echo -e "${CYAN}Nota:${NC} Los archivos están en ${TEMP_DIR} y se pueden usar para restaurar."
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Análisis completado${NC}"
echo -e "${BLUE}========================================${NC}"

