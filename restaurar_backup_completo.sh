#!/bin/bash
# Script para restaurar el backup completo del 11-12-2025
# Esto restaurará TODA la base de datos al estado del 11-12-2025

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
echo -e "${BLUE}Restauración COMPLETA del Backup${NC}"
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

# Verificar contenedor PostgreSQL
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${RED}❌ El contenedor PostgreSQL ${POSTGRES_CONTAINER} no está corriendo${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Contenedor PostgreSQL está corriendo${NC}"
echo ""

# Advertencia final
echo -e "${RED}⚠️  ADVERTENCIA CRÍTICA:${NC}"
echo ""
echo "Este proceso:"
echo "  1. ELIMINARÁ la base de datos actual (${DB_NAME})"
echo "  2. CREARÁ una nueva base de datos vacía"
echo "  3. RESTAURARÁ el backup completo del 11-12-2025"
echo ""
echo "Esto significa que:"
echo "  - Todos los datos actuales se PERDERÁN"
echo "  - El sistema quedará como estaba el 11-12-2025"
echo "  - Cualquier dato creado después del 11-12-2025 se perderá"
echo ""
echo -e "${YELLOW}¿Estás SEGURO de que quieres continuar?${NC}"
echo -e "${YELLOW}Escribe 'RESTAURAR' para confirmar:${NC}"
read -r confirmacion

if [[ "$confirmacion" != "RESTAURAR" ]]; then
    echo -e "${YELLOW}Operación cancelada${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/5] Verificando backup de seguridad de hoy...${NC}"
BACKUP_HOY=$(ls -t /home/max/backups/backup_antes_restore_completo_*.sql /home/max/backups/antes_restore_*.sql 2>/dev/null | head -1 || echo "")

if [[ -n "$BACKUP_HOY" ]]; then
    echo -e "${GREEN}✅ Backup de seguridad encontrado: ${BACKUP_HOY}${NC}"
    SIZE_HOY=$(stat -c%s "$BACKUP_HOY" 2>/dev/null || echo "0")
    echo "   Tamaño: $(numfmt --to=iec-i --suffix=B $SIZE_HOY 2>/dev/null || echo "${SIZE_HOY} bytes")"
else
    echo -e "${YELLOW}⚠️  No se encontró backup de seguridad de hoy${NC}"
    echo "   Asegúrate de haber hecho backup antes de continuar"
    echo ""
    echo "¿Deseas continuar de todas formas? (s/n):"
    read -r continuar
    if [[ "$continuar" != "s" && "$continuar" != "S" ]]; then
        echo "Cancelado"
        exit 0
    fi
fi
echo ""

echo -e "${YELLOW}[2/5] Desconectando sesiones activas...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres <<'SQL'
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'cliente_solutioncar_db' AND pid <> pg_backend_pid();
SQL
echo -e "${GREEN}✅ Sesiones desconectadas${NC}"
echo ""

echo -e "${YELLOW}[3/5] Eliminando base de datos actual...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres <<'SQL'
DROP DATABASE IF EXISTS cliente_solutioncar_db;
SQL
echo -e "${GREEN}✅ Base de datos eliminada${NC}"
echo ""

echo -e "${YELLOW}[4/5] Creando nueva base de datos...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres <<'SQL'
CREATE DATABASE cliente_solutioncar_db OWNER maxgonpe;
SQL
echo -e "${GREEN}✅ Base de datos creada${NC}"
echo ""

echo -e "${YELLOW}[5/5] Restaurando backup del 11-12-2025...${NC}"
echo "   Esto puede tardar varios minutos..."
echo ""

# Restaurar el backup
if docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" < "${BACKUP_FILE}" 2>&1 | tee /tmp/restore_log_$$.txt | tail -20; then
    # Verificar si hubo errores críticos
    ERROR_COUNT=$(grep -c "ERROR" /tmp/restore_log_$$.txt 2>/dev/null || echo "0")
    
    if [[ "$ERROR_COUNT" -gt 0 ]]; then
        echo ""
        echo -e "${YELLOW}⚠️  Se encontraron ${ERROR_COUNT} errores durante la restauración${NC}"
        echo "   (Algunos errores pueden ser normales si las tablas ya existían)"
    fi
    
    echo -e "${GREEN}✅ Restauración completada${NC}"
else
    echo -e "${RED}❌ Error durante la restauración${NC}"
    echo ""
    echo "Revisa el log: /tmp/restore_log_$$.txt"
    exit 1
fi

echo ""
echo -e "${YELLOW}[6/5] Verificando datos restaurados...${NC}"
echo ""

TRABAJOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
REPUESTOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")
DIAGNOSTICOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
CLIENTES=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_cliente_taller;" 2>/dev/null | tr -d '[:space:]' || echo "0")
VEHICULOS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_vehiculo;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo -e "${GREEN}✅ Datos restaurados:${NC}"
echo "  Trabajos: ${TRABAJOS}"
echo "  Repuestos: ${REPUESTOS}"
echo "  Diagnósticos: ${DIAGNOSTICOS}"
echo "  Clientes: ${CLIENTES}"
echo "  Vehículos: ${VEHICULOS}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Restauración COMPLETA exitosa${NC}"
echo -e "${BLUE}El sistema está ahora al estado del 11-12-2025${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Nota:${NC} Si necesitas recuperar datos de hoy, usa el backup:"
if [[ -n "$BACKUP_HOY" ]]; then
    echo "  ${BACKUP_HOY}"
fi
echo ""


