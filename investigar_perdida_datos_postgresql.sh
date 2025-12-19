#!/bin/bash
# Script para investigar qué pasó con los datos perdidos usando capacidades de PostgreSQL

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
echo -e "${BLUE}Investigación de Pérdida de Datos${NC}"
echo -e "${BLUE}Usando capacidades de PostgreSQL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# 1. Verificar configuración de logging
# =========================
echo -e "${YELLOW}[1/7] Verificando configuración de logging de PostgreSQL...${NC}"
echo "----------------------------------------"

# Verificar si log_statement está habilitado
LOG_STATEMENT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c "
SHOW log_statement;
" 2>/dev/null | tr -d '[:space:]' || echo "none")

echo "log_statement: $LOG_STATEMENT"

if [[ "$LOG_STATEMENT" == "none" ]]; then
    echo -e "${YELLOW}⚠️  log_statement está en 'none' - no se registran comandos SQL${NC}"
    echo "   Esto significa que PostgreSQL NO tiene registro de comandos DELETE/TRUNCATE"
elif [[ "$LOG_STATEMENT" == "all" || "$LOG_STATEMENT" == "ddl" || "$LOG_STATEMENT" == "mod" ]]; then
    echo -e "${GREEN}✅ log_statement está en '${LOG_STATEMENT}' - algunos comandos se registran${NC}"
    echo "   Los logs pueden tener información sobre borrados"
else
    echo -e "${YELLOW}⚠️  log_statement: ${LOG_STATEMENT}${NC}"
fi

# Verificar ubicación de logs
LOG_DESTINATION=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c "
SHOW logging_collector;
" 2>/dev/null | tr -d '[:space:]' || echo "off")

echo "logging_collector: $LOG_DESTINATION"

LOG_DIR=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c "
SHOW log_directory;
" 2>/dev/null | tr -d '[:space:]' || echo "log")

echo "log_directory: $LOG_DIR"
echo ""

# =========================
# 2. Buscar logs de PostgreSQL
# =========================
echo -e "${YELLOW}[2/7] Buscando logs de PostgreSQL...${NC}"
echo "----------------------------------------"

# Buscar logs en ubicaciones comunes
LOG_FILES=$(docker exec "${POSTGRES_CONTAINER}" find /var/log/postgresql /var/lib/postgresql/data/log -name "*.log" -type f -mtime -7 2>/dev/null | head -10 || echo "")

if [[ -n "$LOG_FILES" ]]; then
    echo -e "${GREEN}✅ Se encontraron logs recientes:${NC}"
    for log_file in $LOG_FILES; do
        echo "  - $log_file"
        
        # Buscar DELETE o TRUNCATE en los últimos días
        echo "    Buscando DELETE/TRUNCATE en últimos 7 días:"
        docker exec "${POSTGRES_CONTAINER}" grep -i "DELETE\|TRUNCATE" "$log_file" 2>/dev/null | grep -i "car_trabajo\|car_diagnostico" | tail -5 | sed 's/^/      /' || echo "      No se encontraron referencias"
    done
else
    echo -e "${YELLOW}⚠️  No se encontraron logs recientes${NC}"
    echo "   Los logs pueden estar deshabilitados o en otra ubicación"
fi
echo ""

# =========================
# 3. Verificar WAL (Write-Ahead Logging)
# =========================
echo -e "${YELLOW}[3/7] Verificando WAL (Write-Ahead Logging)...${NC}"
echo "----------------------------------------"

WAL_LEVEL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c "
SHOW wal_level;
" 2>/dev/null | tr -d '[:space:]' || echo "replica")

echo "wal_level: $WAL_LEVEL"

if [[ "$WAL_LEVEL" == "logical" ]]; then
    echo -e "${GREEN}✅ WAL está en modo 'logical' - puede tener información detallada${NC}"
    echo "   (Aunque WAL normalmente no se usa para auditoría de datos)"
elif [[ "$WAL_LEVEL" == "replica" ]]; then
    echo -e "${YELLOW}⚠️  WAL está en modo 'replica' - solo para replicación${NC}"
    echo "   No contiene información de auditoría de datos"
else
    echo -e "${YELLOW}⚠️  WAL está en modo '${WAL_LEVEL}'${NC}"
fi
echo ""

# =========================
# 4. Verificar estadísticas de actividad (pg_stat_*)
# =========================
echo -e "${YELLOW}[4/7] Analizando estadísticas de actividad...${NC}"
echo "----------------------------------------"

echo "Estadísticas de car_trabajo:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    schemaname,
    relname AS tabla,
    n_tup_ins AS total_insertados,
    n_tup_upd AS total_actualizados,
    n_tup_del AS total_borrados,
    n_live_tup AS registros_actuales,
    n_dead_tup AS registros_muertos,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE relname = 'car_trabajo';
SQL

echo ""
echo "Cuándo se reiniciaron las estadísticas:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    stats_reset
FROM pg_stat_database
WHERE datname = current_database();
SQL

echo ""
echo -e "${CYAN}Interpretación:${NC}"
echo "  - 'total_borrados': Cuántas tuplas se borraron desde stats_reset"
echo "  - 'registros_muertos': Registros borrados pero aún no limpiados"
echo "  - 'estadisticas_desde': Cuándo se reiniciaron las estadísticas"
echo ""

# =========================
# 5. Verificar dead tuples (registros borrados)
# =========================
echo -e "${YELLOW}[5/7] Verificando dead tuples (registros borrados)...${NC}"
echo "----------------------------------------"

DEAD_TUPLES=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = 'car_trabajo';
" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [[ "$DEAD_TUPLES" != "0" && "$DEAD_TUPLES" -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Se encontraron ${DEAD_TUPLES} dead tuples en car_trabajo${NC}"
    echo "   Esto indica que se borraron registros recientemente"
    echo ""
    echo "   Los dead tuples son registros que fueron marcados para borrar"
    echo "   pero aún no se han limpiado físicamente del disco"
    echo ""
    echo "   Para ver más detalles:"
    echo "   docker exec -i ${POSTGRES_CONTAINER} psql -U ${DB_OWNER} -d ${DB_NAME} -c \"VACUUM VERBOSE car_trabajo;\""
else
    echo -e "${GREEN}✅ No hay dead tuples significativos${NC}"
    echo "   (O ya se limpiaron con VACUUM)"
fi
echo ""

# =========================
# 6. Verificar si hay extensiones de auditoría
# =========================
echo -e "${YELLOW}[6/7] Verificando extensiones de auditoría...${NC}"
echo "----------------------------------------"

EXTENSIONS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT extname FROM pg_extension WHERE extname IN ('pg_audit', 'pgaudit', 'log_fdw');
" 2>/dev/null || echo "")

if [[ -n "$EXTENSIONS" ]]; then
    echo -e "${GREEN}✅ Extensiones de auditoría encontradas:${NC}"
    echo "$EXTENSIONS"
    echo "   Estas pueden tener información sobre cambios"
else
    echo -e "${YELLOW}⚠️  No se encontraron extensiones de auditoría${NC}"
    echo "   PostgreSQL no tiene auditoría avanzada habilitada"
fi
echo ""

# =========================
# 7. Verificar transacciones recientes
# =========================
echo -e "${YELLOW}[7/7] Analizando actividad reciente de la base de datos...${NC}"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    datname,
    xact_commit AS transacciones_commit,
    xact_rollback AS transacciones_rollback,
    tup_inserted AS tuplas_insertadas,
    tup_updated AS tuplas_actualizadas,
    tup_deleted AS tuplas_borradas,
    stats_reset AS estadisticas_desde
FROM pg_stat_database
WHERE datname = current_database();
SQL

echo ""
echo -e "${CYAN}Interpretación:${NC}"
echo "  - 'tuplas_borradas': Total de registros borrados desde stats_reset"
echo "  - 'estadisticas_desde': Cuándo se reiniciaron estas estadísticas"
echo ""

# =========================
# CONCLUSIÓN
# =========================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CONCLUSIÓN${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${CYAN}¿PostgreSQL sabe qué pasó?${NC}"
echo ""

if [[ "$LOG_STATEMENT" == "all" || "$LOG_STATEMENT" == "mod" ]]; then
    echo -e "${GREEN}✅ SÍ - PostgreSQL tiene logging habilitado${NC}"
    echo "   Los logs pueden contener información sobre comandos DELETE/TRUNCATE"
    echo "   Revisa los logs encontrados arriba"
elif [[ -n "$LOG_FILES" ]]; then
    echo -e "${YELLOW}⚠️  PARCIALMENTE - Hay logs pero pueden no tener todos los detalles${NC}"
    echo "   Revisa los logs encontrados"
else
    echo -e "${RED}❌ NO - PostgreSQL NO tiene suficiente información${NC}"
    echo ""
    echo "   Razones:"
    echo "   1. log_statement está en 'none' - no registra comandos SQL"
    echo "   2. No hay extensiones de auditoría habilitadas"
    echo "   3. WAL no se usa para auditoría de datos"
    echo ""
    echo "   Lo que SÍ sabemos:"
    echo "   - Las estadísticas muestran cuántas tuplas se borraron"
    echo "   - Los dead tuples indican borrados recientes"
    echo "   - Pero NO sabemos QUIÉN, CUÁNDO exactamente, o QUÉ comando se ejecutó"
fi

echo ""
echo -e "${CYAN}Recomendaciones para el futuro:${NC}"
echo "  1. Habilitar logging de PostgreSQL:"
echo "     ALTER SYSTEM SET log_statement = 'mod';"
echo "     ALTER SYSTEM SET logging_collector = 'on';"
echo ""
echo "  2. Instalar extensión de auditoría (pgaudit):"
echo "     CREATE EXTENSION IF NOT EXISTS pgaudit;"
echo ""
echo "  3. Implementar triggers de auditoría en tablas críticas"
echo ""
echo "  4. Configurar backups automáticos diarios"
echo ""

echo -e "${BLUE}========================================${NC}"

