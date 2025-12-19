#!/bin/bash
# Script para investigar cuándo y quién borró los datos

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
CONTAINER_NAME="cliente_${CLIENTE}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Investigación: Fecha y Usuario${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# 1. Cuándo se reiniciaron las estadísticas
# =========================
echo -e "${YELLOW}[1/5] Cuándo se reiniciaron las estadísticas...${NC}"
echo "----------------------------------------"

STATS_RESET=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT stats_reset::text 
FROM pg_stat_database 
WHERE datname = current_database();
" 2>/dev/null | tr -d '[:space:]' || echo "N/A")

echo "Estadísticas reiniciadas desde: $STATS_RESET"
echo ""

# Calcular días desde el reset
if [[ "$STATS_RESET" != "N/A" && "$STATS_RESET" != "" ]]; then
    echo "Esto significa que las estadísticas de borrados son desde esta fecha"
    echo "Los 6 registros borrados fueron DESPUÉS de esta fecha"
fi
echo ""

# =========================
# 2. Verificar tabla car_registroevento para fechas
# =========================
echo -e "${YELLOW}[2/5] Analizando eventos para determinar fechas...${NC}"
echo "----------------------------------------"

# Último evento registrado
ULTIMO_EVENTO=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "
SELECT MAX(fecha_evento)::text 
FROM car_registroevento;
" 2>/dev/null | tr -d '[:space:]' || echo "N/A")

echo "Último evento registrado: $ULTIMO_EVENTO"
echo ""

# Eventos de los últimos 7 días
echo "Eventos de los últimos 7 días:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    DATE(fecha_evento) as fecha,
    COUNT(*) as total_eventos,
    COUNT(DISTINCT trabajo_id) as trabajos_afectados
FROM car_registroevento
WHERE fecha_evento >= NOW() - INTERVAL '7 days'
GROUP BY DATE(fecha_evento)
ORDER BY fecha DESC;
SQL

echo ""

# =========================
# 3. Verificar logs de Django (si existen)
# =========================
echo -e "${YELLOW}[3/5] Buscando logs de la aplicación Django...${NC}"
echo "----------------------------------------"

# Buscar logs dentro del contenedor
DJANGO_LOGS=$(docker exec "${CONTAINER_NAME}" find /app -name "*.log" -type f -mtime -7 2>/dev/null | head -5 || echo "")

if [[ -n "$DJANGO_LOGS" ]]; then
    echo -e "${GREEN}✅ Se encontraron logs de Django:${NC}"
    for log_file in $DJANGO_LOGS; do
        echo "  - $log_file"
        
        # Buscar referencias a DELETE o borrados
        if docker exec "${CONTAINER_NAME}" grep -qi "delete\|truncate\|borrar" "$log_file" 2>/dev/null; then
            echo -e "    ${YELLOW}⚠️  Contiene referencias a DELETE/borrar${NC}"
            docker exec "${CONTAINER_NAME}" grep -i "delete\|truncate\|borrar" "$log_file" 2>/dev/null | tail -3 | sed 's/^/      /' || true
        fi
    done
else
    echo -e "${YELLOW}⚠️  No se encontraron logs de Django recientes${NC}"
fi
echo ""

# =========================
# 4. Verificar usuarios activos recientemente
# =========================
echo -e "${YELLOW}[4/5] Verificando usuarios activos recientemente...${NC}"
echo "----------------------------------------"

# Últimos logins desde la tabla de sesiones
echo "Últimos accesos al sistema (desde sesiones):"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    user_id,
    (SELECT username FROM auth_user WHERE id = user_id) as usuario,
    MAX(expire_date) as ultimo_acceso
FROM django_session
WHERE expire_date >= NOW() - INTERVAL '7 days'
GROUP BY user_id
ORDER BY ultimo_acceso DESC
LIMIT 10;
SQL

echo ""

# Verificar tabla de admin log para acciones recientes
echo "Acciones recientes en admin (últimos 7 días):"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    action_time,
    (SELECT username FROM auth_user WHERE id = user_id) as usuario,
    content_type_id,
    object_id,
    object_repr,
    action_flag,
    change_message
FROM django_admin_log
WHERE action_time >= NOW() - INTERVAL '7 days'
ORDER BY action_time DESC
LIMIT 20;
SQL

echo ""

# =========================
# 5. Analizar estadísticas detalladas por tabla
# =========================
echo -e "${YELLOW}[5/5] Estadísticas detalladas por tabla...${NC}"
echo "----------------------------------------"

echo "Resumen de actividad en tablas principales:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SELECT 
    relname AS tabla,
    n_tup_ins AS insertados,
    n_tup_upd AS actualizados,
    n_tup_del AS borrados,
    n_live_tup AS actuales,
    n_dead_tup AS muertos,
    last_autoanalyze AS ultimo_analisis
FROM pg_stat_user_tables
WHERE relname IN ('car_trabajo', 'car_diagnostico', 'car_trabajorepuesto', 'car_vehiculo', 'car_cliente_taller')
ORDER BY n_tup_del DESC, relname;
SQL

echo ""

# =========================
# CONCLUSIÓN
# =========================
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}ANÁLISIS${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${CYAN}Respecto a los 397 registros:${NC}"
echo "  - Estos son 'tuplas_actualizadas' (UPDATE), NO borrados"
echo "  - Los borrados reales son: 6 tuplas"
echo "  - Pero esto es desde que se reiniciaron las estadísticas"
echo ""

echo -e "${CYAN}¿Cuándo se borraron los datos?${NC}"
if [[ "$STATS_RESET" != "N/A" && "$STATS_RESET" != "" ]]; then
    echo "  Las estadísticas se reiniciaron: $STATS_RESET"
    echo "  Los 6 borrados fueron DESPUÉS de esta fecha"
    echo "  Pero NO sabemos la fecha exacta (solo que fue después del reset)"
else
    echo "  No se pudo determinar cuándo se reiniciaron las estadísticas"
fi
echo ""

echo -e "${CYAN}¿Quién borró los datos?${NC}"
echo "  ${RED}❌ NO se puede saber con la configuración actual${NC}"
echo ""
echo "  Razones:"
echo "  1. log_statement está en 'none' - no registra comandos SQL"
echo "  2. No hay triggers de auditoría en las tablas"
echo "  3. No hay extensión pgaudit habilitada"
echo ""
echo "  Lo que SÍ podemos ver:"
echo "  - Usuarios que accedieron al sistema recientemente (arriba)"
echo "  - Acciones en el admin de Django (arriba)"
echo "  - Pero NO quién ejecutó comandos DELETE/TRUNCATE directamente en la BD"
echo ""

echo -e "${CYAN}Recomendación:${NC}"
echo "  Los datos probablemente se borraron entre:"
echo "  - La fecha del último evento en car_registroevento"
echo "  - Y la fecha en que restauraste el backup (hoy)"
echo ""
echo "  Revisa los usuarios activos mostrados arriba"
echo "  y las acciones en django_admin_log para ver quién estaba trabajando"
echo ""

echo -e "${BLUE}========================================${NC}"


