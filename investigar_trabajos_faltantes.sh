#!/bin/bash
# Script para investigar por qué los trabajos no aparecen aunque hay eventos que los referencian

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
echo -e "${BLUE}Investigando Trabajos Faltantes${NC}"
echo -e "${BLUE}Base de datos: ${DB_NAME}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# 1. Verificar trabajos que están referenciados en eventos pero no existen
# =========================
echo -e "${YELLOW}[1/5] Trabajos referenciados en eventos:${NC}"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
-- Trabajos referenciados en eventos
SELECT DISTINCT
    trabajo_id,
    COUNT(*) as num_eventos,
    MIN(fecha_evento) as primer_evento,
    MAX(fecha_evento) as ultimo_evento
FROM car_registroevento
WHERE trabajo_id IS NOT NULL
GROUP BY trabajo_id
ORDER BY trabajo_id;
SQL

echo ""

# =========================
# 2. Verificar si esos trabajos existen en car_trabajo
# =========================
echo -e "${YELLOW}[2/5] Verificando si esos trabajos existen en car_trabajo:${NC}"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
-- Trabajos que están en eventos pero NO en car_trabajo
SELECT 
    e.trabajo_id,
    COUNT(e.id) as num_eventos,
    MIN(e.fecha_evento) as primer_evento,
    MAX(e.fecha_evento) as ultimo_evento,
    CASE WHEN t.id IS NULL THEN 'NO EXISTE' ELSE 'EXISTE' END as estado_en_tabla
FROM car_registroevento e
LEFT JOIN car_trabajo t ON e.trabajo_id = t.id
WHERE e.trabajo_id IS NOT NULL
GROUP BY e.trabajo_id, t.id
ORDER BY e.trabajo_id;
SQL

echo ""

# =========================
# 3. Contar trabajos reales en car_trabajo
# =========================
echo -e "${YELLOW}[3/5] Estado actual de car_trabajo:${NC}"
echo "----------------------------------------"

docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
-- Contar trabajos por estado
SELECT 
    estado,
    COUNT(*) as cantidad,
    COUNT(CASE WHEN visible = true THEN 1 END) as visibles,
    COUNT(CASE WHEN visible = false THEN 1 END) as ocultos
FROM car_trabajo
GROUP BY estado
ORDER BY estado;
SQL

echo ""

# Verificar si hay trabajos ocultos (visible = false)
OCULTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajo WHERE visible = false;" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [[ "$OCULTOS" != "0" ]]; then
    echo -e "${YELLOW}⚠️  Se encontraron ${OCULTOS} trabajos ocultos (visible = false)${NC}"
    echo ""
    echo "Trabajos ocultos:"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
    SELECT id, estado, fecha_inicio, visible
    FROM car_trabajo
    WHERE visible = false
    ORDER BY id;
    " || true
    echo ""
fi

# =========================
# 4. Verificar trabajos con IDs específicos mencionados en eventos
# =========================
echo -e "${YELLOW}[4/5] Verificando trabajos específicos mencionados en eventos:${NC}"
echo "----------------------------------------"

# Obtener IDs de trabajos de eventos
TRABAJO_IDS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT DISTINCT trabajo_id FROM car_registroevento WHERE trabajo_id IS NOT NULL ORDER BY trabajo_id;" 2>/dev/null | grep -v "^$" | head -10)

if [[ -n "$TRABAJO_IDS" ]]; then
    echo "Buscando trabajos con IDs: $(echo $TRABAJO_IDS | tr '\n' ' ')"
    echo ""
    
    for trabajo_id in $TRABAJO_IDS; do
        if [[ -n "$trabajo_id" ]]; then
            EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
                "SELECT EXISTS(SELECT 1 FROM car_trabajo WHERE id = ${trabajo_id});" 2>/dev/null | tr -d '[:space:]' || echo "false")
            
            if [[ "$EXISTS" == "t" ]]; then
                echo -e "${GREEN}✅ Trabajo ${trabajo_id}: EXISTE${NC}"
                docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
                SELECT id, estado, fecha_inicio, visible, vehiculo_id
                FROM car_trabajo
                WHERE id = ${trabajo_id};
                " 2>/dev/null || true
            else
                echo -e "${RED}❌ Trabajo ${trabajo_id}: NO EXISTE (pero tiene eventos)${NC}"
                
                # Mostrar eventos de este trabajo
                echo "  Eventos relacionados:"
                docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
                SELECT id, tipo_evento, fecha_evento, descripcion
                FROM car_registroevento
                WHERE trabajo_id = ${trabajo_id}
                ORDER BY fecha_evento
                LIMIT 5;
                " 2>/dev/null || true
            fi
            echo ""
        fi
    done
fi

# =========================
# 5. Verificar si hay trabajos eliminados (soft delete o hard delete)
# =========================
echo -e "${YELLOW}[5/5] Verificando trabajos eliminados:${NC}"
echo "----------------------------------------"

# Verificar dead tuples (registros borrados físicamente)
DEAD_TUPLES=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname = 'car_trabajo';" 2>/dev/null | tr -d '[:space:]' || echo "0")

if [[ "$DEAD_TUPLES" != "0" ]]; then
    echo -e "${YELLOW}⚠️  Se encontraron ${DEAD_TUPLES} dead tuples en car_trabajo${NC}"
    echo "Esto indica que se borraron registros físicamente pero aún no se han limpiado."
    echo ""
    echo "Ejecutando VACUUM para limpiar (esto no recupera datos, solo limpia):"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "VACUUM ANALYZE car_trabajo;" 2>/dev/null || true
    echo ""
fi

# Verificar estadísticas de borrados
echo "Estadísticas de borrados en car_trabajo:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
SELECT 
    n_tup_ins AS total_insertados,
    n_tup_upd AS total_actualizados,
    n_tup_del AS total_borrados,
    n_live_tup AS registros_actuales,
    n_dead_tup AS registros_muertos
FROM pg_stat_user_tables
WHERE relname = 'car_trabajo';
" || true

echo ""

# =========================
# Resumen y conclusiones
# =========================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resumen${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

TOTAL_TRABAJOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")

TOTAL_EVENTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_registroevento WHERE trabajo_id IS NOT NULL;" 2>/dev/null | tr -d '[:space:]' || echo "0")

TRABAJOS_UNICOS_EVENTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(DISTINCT trabajo_id) FROM car_registroevento WHERE trabajo_id IS NOT NULL;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo -e "Trabajos en car_trabajo: ${TOTAL_TRABAJOS}"
echo -e "Eventos con trabajo_id: ${TOTAL_EVENTOS}"
echo -e "Trabajos únicos en eventos: ${TRABAJOS_UNICOS_EVENTOS}"
echo ""

if [[ "$TOTAL_TRABAJOS" == "0" && "$TRABAJOS_UNICOS_EVENTOS" != "0" ]]; then
    echo -e "${RED}⚠️  PROBLEMA DETECTADO:${NC}"
    echo -e "   Hay ${TRABAJOS_UNICOS_EVENTOS} trabajos referenciados en eventos,"
    echo -e "   pero 0 trabajos en la tabla car_trabajo."
    echo ""
    echo -e "${CYAN}Posibles causas:${NC}"
    echo "   1. Los trabajos fueron borrados físicamente (DELETE)"
    echo "   2. Los trabajos están en otra base de datos"
    echo "   3. Hubo un problema durante una migración o actualización"
    echo "   4. Los trabajos están ocultos (visible = false) - ya verificado arriba"
    echo ""
    echo -e "${CYAN}Recomendaciones:${NC}"
    echo "   1. Revisar los backups encontrados anteriormente"
    echo "   2. Verificar si los datos están en otra BD"
    echo "   3. Revisar logs de la aplicación para ver si hubo borrados"
fi

echo ""





