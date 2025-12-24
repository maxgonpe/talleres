#!/bin/bash
# Script para analizar la causa más probable de la pérdida de datos

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
echo -e "${BLUE}Análisis de Causa de Pérdida de Datos${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# 1. Recolectar evidencia
# =========================
echo -e "${YELLOW}[1/5] Recolectando evidencia...${NC}"
echo ""

# Estadísticas de borrados
TUPLAS_BORRADAS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT n_tup_del FROM pg_stat_user_tables WHERE relname = 'car_trabajo';" 2>/dev/null | tr -d '[:space:]' || echo "0")

# Trabajos en eventos vs trabajos en tabla
TRABAJOS_EN_EVENTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(DISTINCT trabajo_id) FROM car_registroevento WHERE trabajo_id IS NOT NULL;" 2>/dev/null | tr -d '[:space:]' || echo "0")

TRABAJOS_EN_TABLA=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")

# Fecha de creación de la BD
BD_CREATED=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c \
    "SELECT datname, pg_stat_file('base/'||oid||'/PG_VERSION', true) FROM pg_database WHERE datname = '${DB_NAME}';" 2>/dev/null || echo "N/A")

# Última modificación de tablas
LAST_MODIFIED=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT MAX(last_autoanalyze) FROM pg_stat_user_tables WHERE relname = 'car_trabajo';" 2>/dev/null | tr -d '[:space:]' || echo "N/A")

# Verificar si hay backups recientes
BACKUP_RECIENTE=$(find /home/max/backups -name "*${CLIENTE}*" -type f -mtime -30 2>/dev/null | head -1 || echo "")

echo -e "${GREEN}Evidencia recolectada:${NC}"
echo "  - Tuplas borradas: $TUPLAS_BORRADAS"
echo "  - Trabajos en eventos: $TRABAJOS_EN_EVENTOS"
echo "  - Trabajos en tabla: $TRABAJOS_EN_TABLA"
echo "  - Última modificación: $LAST_MODIFIED"
echo ""

# =========================
# 2. Analizar posibles causas
# =========================
echo -e "${YELLOW}[2/5] Analizando posibles causas...${NC}"
echo ""

CAUSAS=()

# Causa 1: DELETE masivo o accidental
if [[ "$TUPLAS_BORRADAS" != "0" && "$TUPLAS_BORRADAS" -gt 100 ]]; then
    CAUSAS+=("DELETE_MASIVO")
    echo -e "${RED}⚠️  CAUSA PROBABLE 1: DELETE masivo o accidental${NC}"
    echo "   - Se detectaron $TUPLAS_BORRADAS tuplas borradas"
    echo "   - Esto indica que se ejecutaron comandos DELETE"
    echo "   - Puede haber sido accidental o intencional"
    echo ""
fi

# Causa 2: BD creada desde semilla vacía
if [[ "$TRABAJOS_EN_EVENTOS" != "0" && "$TRABAJOS_EN_TABLA" == "0" ]]; then
    CAUSAS+=("SEMILLA_VACIA")
    echo -e "${YELLOW}⚠️  CAUSA PROBABLE 2: Base de datos creada desde semilla vacía${NC}"
    echo "   - Hay $TRABAJOS_EN_EVENTOS trabajos referenciados en eventos"
    echo "   - Pero 0 trabajos en la tabla car_trabajo"
    echo "   - Esto sugiere que la BD se creó sin copiar los datos correctamente"
    echo ""
fi

# Causa 3: Migración o actualización fallida
if [[ -n "$BACKUP_RECIENTE" ]]; then
    BACKUP_DATE=$(stat -c%y "$BACKUP_RECIENTE" 2>/dev/null | cut -d' ' -f1 || echo "N/A")
    CAUSAS+=("MIGRACION_FALLIDA")
    echo -e "${YELLOW}⚠️  CAUSA PROBABLE 3: Migración o actualización fallida${NC}"
    echo "   - Hay backups recientes (último: $BACKUP_DATE)"
    echo "   - Puede haber habido una migración que borró datos"
    echo "   - O una actualización del contenedor que no preservó datos"
    echo ""
fi

# Causa 4: Problema con script alta_cliente.sh
SCRIPT_ALTA_CLIENTE="/home/max/myproject/otros/base-docker/alta_cliente.sh"
if [[ -f "$SCRIPT_ALTA_CLIENTE" ]]; then
    # Verificar si el script copia desde una semilla
    if grep -q "SEED_DB" "$SCRIPT_ALTA_CLIENTE"; then
        SEED_DB=$(grep "SEED_DB=" "$SCRIPT_ALTA_CLIENTE" | head -1 | cut -d'"' -f2 || echo "")
        if [[ -n "$SEED_DB" ]]; then
            SEED_HAS_DATA=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${SEED_DB}" -tA -c \
                "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
            
            if [[ "$SEED_HAS_DATA" == "0" ]]; then
                CAUSAS+=("SEMILLA_VACIA")
                echo -e "${RED}⚠️  CAUSA PROBABLE 4: Semilla vacía${NC}"
                echo "   - El script alta_cliente.sh copia desde: $SEED_DB"
                echo "   - La semilla tiene 0 trabajos"
                echo "   - Si solutioncar se creó desde esta semilla, no tendría datos"
                echo ""
            fi
        fi
    fi
fi

# Causa 5: VACUUM o limpieza agresiva
DEAD_TUPLES=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = 'car_trabajo';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [[ "$DEAD_TUPLES" != "0" && "$DEAD_TUPLES" -gt 100 ]]; then
    CAUSAS+=("VACUUM_AGRESIVO")
    echo -e "${YELLOW}⚠️  CAUSA PROBABLE 5: VACUUM o limpieza agresiva${NC}"
    echo "   - Hay $DEAD_TUPLES dead tuples (registros marcados para borrar)"
    echo "   - Un VACUUM FULL puede haber limpiado datos"
    echo ""
fi

# =========================
# 3. Determinar causa más probable
# =========================
echo -e "${YELLOW}[3/5] Determinando causa más probable...${NC}"
echo ""

CAUSA_MAS_PROBABLE=""

if [[ " ${CAUSAS[@]} " =~ " DELETE_MASIVO " ]]; then
    CAUSA_MAS_PROBABLE="DELETE_MASIVO"
    echo -e "${RED}🔴 CAUSA MÁS PROBABLE: DELETE masivo o accidental${NC}"
    echo ""
    echo "   Razones:"
    echo "   - Las estadísticas muestran $TUPLAS_BORRADAS tuplas borradas"
    echo "   - Hay eventos que referencian trabajos que ya no existen"
    echo "   - Esto indica que se ejecutó un DELETE (accidental o intencional)"
    echo ""
    echo "   Posibles escenarios:"
    echo "   1. DELETE FROM car_trabajo WHERE ... (condición incorrecta)"
    echo "   2. TRUNCATE TABLE car_trabajo (accidental)"
    echo "   3. Script de limpieza o mantenimiento mal ejecutado"
    echo "   4. Error en una migración que borró datos"
    
elif [[ " ${CAUSAS[@]} " =~ " SEMILLA_VACIA " ]]; then
    CAUSA_MAS_PROBABLE="SEMILLA_VACIA"
    echo -e "${YELLOW}🟡 CAUSA MÁS PROBABLE: Base de datos creada desde semilla vacía${NC}"
    echo ""
    echo "   Razones:"
    echo "   - Hay eventos históricos pero no trabajos en la tabla"
    echo "   - La BD puede haberse creado desde una semilla sin datos"
    echo "   - O se recreó el contenedor sin preservar los datos"
    echo ""
    echo "   Posibles escenarios:"
    echo "   1. Se ejecutó alta_cliente.sh con una semilla vacía"
    echo "   2. Se recreó el contenedor sin hacer backup primero"
    echo "   3. Se copió el esquema pero no los datos"
    
elif [[ " ${CAUSAS[@]} " =~ " MIGRACION_FALLIDA " ]]; then
    CAUSA_MAS_PROBABLE="MIGRACION_FALLIDA"
    echo -e "${YELLOW}🟡 CAUSA PROBABLE: Migración o actualización fallida${NC}"
    echo ""
    echo "   Razones:"
    echo "   - Hay backups recientes que sugieren actividad"
    echo "   - Puede haber habido una migración que falló"
    echo ""
else
    CAUSA_MAS_PROBABLE="DESCONOCIDA"
    echo -e "${CYAN}⚠️  Causa no determinada con certeza${NC}"
    echo "   Se necesita más investigación"
fi

# =========================
# 4. Verificar evidencia adicional
# =========================
echo -e "${YELLOW}[4/5] Verificando evidencia adicional...${NC}"
echo ""

# Verificar si hay logs de la aplicación
echo "Buscando logs de la aplicación..."
APP_LOGS=$(find /home/max/myproject -name "*.log" -type f -mtime -30 2>/dev/null | head -5 || echo "")

if [[ -n "$APP_LOGS" ]]; then
    echo -e "${GREEN}✅ Se encontraron logs de aplicación${NC}"
    for log in $APP_LOGS; do
        echo "  - $log"
        # Buscar referencias a DELETE o borrados
        if grep -qi "delete\|truncate\|drop" "$log" 2>/dev/null; then
            echo -e "    ${RED}⚠️  Contiene referencias a DELETE/TRUNCATE${NC}"
            grep -i "delete\|truncate" "$log" 2>/dev/null | tail -3 | sed 's/^/      /' || true
        fi
    done
else
    echo -e "${YELLOW}⚠️  No se encontraron logs recientes${NC}"
fi

echo ""

# Verificar historial de comandos Docker
echo "Verificando contenedores Docker relacionados..."
DOCKER_HISTORY=$(docker ps -a --filter "name=cliente_${CLIENTE}" --format "{{.CreatedAt}} {{.Status}}" 2>/dev/null || echo "")

if [[ -n "$DOCKER_HISTORY" ]]; then
    echo "Historial del contenedor:"
    echo "$DOCKER_HISTORY" | sed 's/^/  /'
fi

echo ""

# =========================
# 5. Recomendaciones
# =========================
echo -e "${YELLOW}[5/5] Recomendaciones:${NC}"
echo ""

if [[ "$CAUSA_MAS_PROBABLE" == "DELETE_MASIVO" ]]; then
    echo -e "${CYAN}Para recuperar los datos:${NC}"
    echo "  1. Verificar backups recientes (ejecutar verificar_backups_trabajos.sh)"
    echo "  2. Si los backups tienen los datos, restaurar desde backup"
    echo "  3. Revisar logs de PostgreSQL para ver comandos DELETE ejecutados"
    echo ""
    echo -e "${CYAN}Para prevenir en el futuro:${NC}"
    echo "  1. Implementar backups automáticos diarios"
    echo "  2. Agregar confirmación antes de DELETE masivos"
    echo "  3. Usar transacciones con rollback para operaciones críticas"
    echo "  4. Implementar auditoría de cambios (triggers)"
    
elif [[ "$CAUSA_MAS_PROBABLE" == "SEMILLA_VACIA" ]]; then
    echo -e "${CYAN}Para recuperar los datos:${NC}"
    echo "  1. Buscar backups anteriores a la creación de la BD"
    echo "  2. Verificar si los datos están en otra base de datos"
    echo "  3. Restaurar desde un backup que tenga los datos"
    echo ""
    echo -e "${CYAN}Para prevenir en el futuro:${NC}"
    echo "  1. Asegurar que la semilla tenga datos antes de crear clientes"
    echo "  2. Verificar que alta_cliente.sh copie datos, no solo esquema"
    echo "  3. Hacer backup antes de recrear contenedores"
    
else
    echo -e "${CYAN}Recomendaciones generales:${NC}"
    echo "  1. Ejecutar verificar_backups_trabajos.sh para verificar backups"
    echo "  2. Revisar logs de PostgreSQL si están habilitados"
    echo "  3. Verificar si hay datos en otras bases de datos"
    echo "  4. Implementar sistema de auditoría para rastrear cambios"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Análisis completado${NC}"
echo -e "${BLUE}========================================${NC}"





