#!/bin/bash
# Script para verificar historial y cambios en PostgreSQL para solutioncar
# Busca evidencia de actualizaciones, borrados o cambios en la base de datos

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

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verificando Historial PostgreSQL${NC}"
echo -e "${BLUE}Base de datos: ${DB_NAME}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar contenedor PostgreSQL
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${RED}❌ El contenedor PostgreSQL ${POSTGRES_CONTAINER} no está corriendo${NC}"
    exit 1
fi

# =========================
# 1. Verificar estadísticas de tablas (últimas actualizaciones)
# =========================
echo -e "${YELLOW}[1/6] Estadísticas de última modificación de tablas:${NC}"
echo "Esto muestra cuándo se modificaron las tablas por última vez"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    schemaname,
    relname AS tablename,
    n_tup_ins AS inserts,
    n_tup_upd AS updates,
    n_tup_del AS deletes,
    n_live_tup AS registros_actuales,
    n_dead_tup AS registros_muertos,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE relname LIKE 'car_%'
ORDER BY relname;
SQL

echo ""
echo -e "${CYAN}Nota:${NC} 'registros_muertos' son registros que fueron borrados pero aún no se han limpiado (vacuum)"
echo ""

# =========================
# 2. Verificar si hay tablas de auditoría o log
# =========================
echo -e "${YELLOW}[2/6] Buscando tablas de auditoría o log:${NC}"
echo "----------------------------------------"

AUDIT_TABLES=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT tablename 
FROM pg_tables 
WHERE schemaname = 'public' 
AND (tablename LIKE '%log%' OR tablename LIKE '%audit%' OR tablename LIKE '%historial%' OR tablename LIKE '%evento%')
ORDER BY tablename;
" 2>/dev/null | tr -d '[:space:]' | grep -v "^$" || echo "")

if [[ -n "$AUDIT_TABLES" ]]; then
    echo -e "${GREEN}✅ Se encontraron tablas de auditoría:${NC}"
    echo "$AUDIT_TABLES" | while read -r table; do
        if [[ -n "$table" ]]; then
            COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
                "SELECT COUNT(*) FROM ${table};" 2>/dev/null | tr -d '[:space:]' || echo "0")
            echo -e "  ${table}: ${COUNT} registros"
        fi
    done
else
    echo -e "${YELLOW}⚠️  No se encontraron tablas de auditoría específicas${NC}"
fi

# Verificar tabla car_registroevento específicamente
echo ""
echo "Verificando tabla car_registroevento (si existe):"
EVENT_COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_registroevento;" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [[ "$EVENT_COUNT" != "0" ]]; then
    echo -e "${GREEN}✅ car_registroevento tiene ${EVENT_COUNT} eventos${NC}"
    echo ""
    echo "Últimos 10 eventos registrados:"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
    SELECT 
        id,
        tipo_evento,
        fecha_evento,
        trabajo_id,
        vehiculo_id,
        descripcion
    FROM car_registroevento
    ORDER BY fecha_evento DESC
    LIMIT 10;
    " || echo "No se pudo consultar eventos"
else
    echo -e "${YELLOW}⚠️  car_registroevento está vacía o no existe${NC}"
fi
echo ""

# =========================
# 3. Verificar triggers de auditoría
# =========================
echo -e "${YELLOW}[3/6] Verificando triggers de auditoría:${NC}"
echo "----------------------------------------"

TRIGGERS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT 
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers
WHERE trigger_schema = 'public'
AND (trigger_name LIKE '%audit%' OR trigger_name LIKE '%log%' OR trigger_name LIKE '%historial%')
ORDER BY event_object_table, trigger_name;
" 2>/dev/null || echo "")

if [[ -n "$TRIGGERS" && "$TRIGGERS" != "" ]]; then
    echo -e "${GREEN}✅ Se encontraron triggers de auditoría:${NC}"
    echo "$TRIGGERS"
else
    echo -e "${YELLOW}⚠️  No se encontraron triggers de auditoría${NC}"
fi
echo ""

# =========================
# 4. Verificar logs de PostgreSQL (si están disponibles)
# =========================
echo -e "${YELLOW}[4/6] Verificando logs de PostgreSQL:${NC}"
echo "----------------------------------------"

# Intentar encontrar archivos de log
LOG_FILES=$(docker exec "${POSTGRES_CONTAINER}" find /var/log/postgresql -name "*.log" 2>/dev/null | head -5 || echo "")

if [[ -n "$LOG_FILES" ]]; then
    echo -e "${GREEN}✅ Se encontraron archivos de log:${NC}"
    for log_file in $LOG_FILES; do
        echo "  $log_file"
        # Buscar referencias a solutioncar o a la BD
        echo "  Buscando referencias a '${DB_NAME}' o '${CLIENTE}':"
        docker exec "${POSTGRES_CONTAINER}" grep -i "${DB_NAME}\|${CLIENTE}" "$log_file" 2>/dev/null | tail -5 || echo "    No se encontraron referencias"
    done
else
    echo -e "${YELLOW}⚠️  No se encontraron archivos de log en /var/log/postgresql${NC}"
    echo "Intentando buscar en otras ubicaciones..."
    
    # Buscar en ubicaciones comunes
    ALTERNATIVE_LOGS=$(docker exec "${POSTGRES_CONTAINER}" find /var/lib/postgresql -name "*.log" 2>/dev/null | head -3 || echo "")
    if [[ -n "$ALTERNATIVE_LOGS" ]]; then
        echo "Logs encontrados en:"
        echo "$ALTERNATIVE_LOGS"
    fi
fi
echo ""

# =========================
# 5. Verificar transacciones recientes (usando pg_stat_database)
# =========================
echo -e "${YELLOW}[5/6] Estadísticas de actividad de la base de datos:${NC}"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    datname,
    numbackends AS conexiones_activas,
    xact_commit AS transacciones_commit,
    xact_rollback AS transacciones_rollback,
    blks_read AS bloques_leidos,
    blks_hit AS bloques_en_cache,
    tup_returned AS tuplas_devueltas,
    tup_fetched AS tuplas_obtenidas,
    tup_inserted AS tuplas_insertadas,
    tup_updated AS tuplas_actualizadas,
    tup_deleted AS tuplas_borradas,
    stats_reset AS estadisticas_desde
FROM pg_stat_database
WHERE datname = current_database();
SQL

echo ""

# =========================
# 6. Verificar registros "muertos" (dead tuples) que indican borrados
# =========================
echo -e "${YELLOW}[6/6] Verificando registros muertos (dead tuples):${NC}"
echo "Esto indica registros que fueron borrados pero aún no se han limpiado"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    schemaname,
    relname AS tablename,
    n_live_tup AS registros_vivos,
    n_dead_tup AS registros_muertos,
    CASE 
        WHEN n_live_tup > 0 THEN 
            ROUND((n_dead_tup::numeric / n_live_tup::numeric) * 100, 2)
        ELSE 0
    END AS porcentaje_muertos,
    last_vacuum,
    last_autovacuum
FROM pg_stat_user_tables
WHERE relname LIKE 'car_%'
AND n_dead_tup > 0
ORDER BY n_dead_tup DESC;
SQL

echo ""
echo -e "${CYAN}Nota:${NC} Si hay muchos 'registros_muertos', puede indicar que se borraron datos recientemente."
echo "Ejecutar VACUUM puede limpiar estos registros, pero no recupera los datos."
echo ""

# =========================
# 7. Verificar si hay backups o snapshots recientes
# =========================
echo -e "${YELLOW}[7/6] Buscando backups o dumps recientes:${NC}"
echo "----------------------------------------"

# Buscar en el contenedor PostgreSQL
BACKUPS=$(docker exec "${POSTGRES_CONTAINER}" find /tmp /var/backups /backup -name "*${CLIENTE}*" -o -name "*${DB_NAME}*" 2>/dev/null | head -10 || echo "")

if [[ -n "$BACKUPS" ]]; then
    echo -e "${GREEN}✅ Se encontraron posibles backups:${NC}"
    echo "$BACKUPS"
else
    echo -e "${YELLOW}⚠️  No se encontraron backups dentro del contenedor${NC}"
fi

# Buscar en el host
echo ""
echo "Buscando backups en el servidor host:"
HOST_BACKUPS=$(find /home/max/myproject /home/max -name "*${CLIENTE}*" -o -name "*${DB_NAME}*" 2>/dev/null | head -10 || echo "")

if [[ -n "$HOST_BACKUPS" ]]; then
    echo -e "${GREEN}✅ Se encontraron posibles backups en el host:${NC}"
    echo "$HOST_BACKUPS"
else
    echo -e "${YELLOW}⚠️  No se encontraron backups en ubicaciones comunes${NC}"
fi
echo ""

# =========================
# 8. Resumen y recomendaciones
# =========================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resumen y Recomendaciones${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${CYAN}Para investigar más a fondo:${NC}"
echo "1. Revisa los logs de PostgreSQL si están habilitados"
echo "2. Verifica si hay backups recientes que puedan tener los datos"
echo "3. Revisa la tabla car_registroevento si tiene datos históricos"
echo "4. Compara con otras bases de datos cliente_* para ver si los datos están ahí"
echo ""
echo -e "${CYAN}Si los datos fueron borrados:${NC}"
echo "- Los 'dead tuples' indican borrados recientes"
echo "- Los logs de PostgreSQL pueden mostrar comandos DELETE"
echo "- Los backups pueden tener los datos antes del borrado"
echo ""

