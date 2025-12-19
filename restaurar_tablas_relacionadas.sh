#!/bin/bash
# Script para restaurar todas las tablas relacionadas necesarias para trabajos
# Orden: Clientes -> Vehículos -> Diagnósticos -> Trabajos -> Repuestos

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
echo -e "${BLUE}Restauración de Tablas Relacionadas${NC}"
echo -e "${BLUE}Fecha backup: 11-12-2025${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}❌ Backup no encontrado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backup encontrado${NC}"
echo ""
echo -e "${YELLOW}Este script restaurará (en orden):${NC}"
echo "  1. Clientes (car_cliente_taller)"
echo "  2. Vehículos (car_vehiculo)"
echo "  3. Diagnósticos (car_diagnostico)"
echo "  4. Trabajos (car_trabajo)"
echo "  5. Repuestos de trabajo (car_trabajorepuesto)"
echo ""
echo "⚠️  Esto SOBRESCRIBIRÁ los datos actuales de estas tablas"
echo ""
echo "¿Continuar? (escribe 'SI'):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo "Cancelado"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/6] Backup de seguridad...${NC}"
BACKUP_ANTES="/home/max/backups/antes_restore_relacionadas_$(date +%Y%m%d_%H%M%S).sql"
mkdir -p /home/max/backups
docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${DB_OWNER}" -d "${DB_NAME}" \
    -t car_cliente_taller -t car_vehiculo -t car_diagnostico -t car_trabajo -t car_trabajorepuesto \
    > "${BACKUP_ANTES}" 2>/dev/null
echo -e "${GREEN}✅ Backup creado${NC}"
echo ""

echo -e "${YELLOW}[2/6] Deshabilitando foreign keys temporalmente...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SET session_replication_role = 'replica';
SQL
echo -e "${GREEN}✅ Foreign keys deshabilitadas${NC}"
echo ""

echo -e "${YELLOW}[3/6] Limpiando tablas (en orden inverso)...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
BEGIN;
TRUNCATE TABLE car_trabajorepuesto CASCADE;
TRUNCATE TABLE car_trabajo CASCADE;
TRUNCATE TABLE car_diagnostico CASCADE;
TRUNCATE TABLE car_vehiculo CASCADE;
TRUNCATE TABLE car_cliente_taller CASCADE;
COMMIT;
SQL
echo -e "${GREEN}✅ Tablas limpiadas${NC}"
echo ""

echo -e "${YELLOW}[4/6] Restaurando clientes...${NC}"
CLIENTES=$(grep -c "INSERT INTO public.car_cliente_taller" "$BACKUP_FILE" 2>/dev/null || echo "0")
echo "  Encontrados: $CLIENTES registros"
if [[ $CLIENTES -gt 0 ]]; then
    grep "INSERT INTO public.car_cliente_taller" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -3 || true
    echo -e "${GREEN}✅ Clientes restaurados${NC}"
fi
echo ""

echo -e "${YELLOW}[5/6] Restaurando vehículos...${NC}"
VEHICULOS=$(grep -c "INSERT INTO public.car_vehiculo" "$BACKUP_FILE" 2>/dev/null || echo "0")
echo "  Encontrados: $VEHICULOS registros"
if [[ $VEHICULOS -gt 0 ]]; then
    grep "INSERT INTO public.car_vehiculo" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -3 || true
    echo -e "${GREEN}✅ Vehículos restaurados${NC}"
fi
echo ""

echo -e "${YELLOW}[6/6] Restaurando diagnósticos...${NC}"
DIAGNOSTICOS=$(grep -c "INSERT INTO public.car_diagnostico" "$BACKUP_FILE" 2>/dev/null || echo "0")
echo "  Encontrados: $DIAGNOSTICOS registros"
if [[ $DIAGNOSTICOS -gt 0 ]]; then
    grep "INSERT INTO public.car_diagnostico" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -3 || true
    echo -e "${GREEN}✅ Diagnósticos restaurados${NC}"
fi
echo ""

echo -e "${YELLOW}[7/6] Restaurando trabajos...${NC}"
TRABAJOS=$(grep -c "INSERT INTO public.car_trabajo" "$BACKUP_FILE" 2>/dev/null || echo "0")
echo "  Encontrados: $TRABAJOS registros"
if [[ $TRABAJOS -gt 0 ]]; then
    # Limpiar líneas con saltos problemáticos
    grep "INSERT INTO public.car_trabajo" "$BACKUP_FILE" | tr -d '\n' | sed 's/);/);\n/g' | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -5 || true
    echo -e "${GREEN}✅ Trabajos restaurados${NC}"
fi
echo ""

echo -e "${YELLOW}[8/6] Restaurando repuestos...${NC}"
REPUESTOS=$(grep -c "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" 2>/dev/null || echo "0")
echo "  Encontrados: $REPUESTOS registros"
if [[ $REPUESTOS -gt 0 ]]; then
    grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | tail -3 || true
    echo -e "${GREEN}✅ Repuestos restaurados${NC}"
fi
echo ""

echo -e "${YELLOW}[9/6] Rehabilitando foreign keys...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SET session_replication_role = 'origin';
SQL
echo -e "${GREEN}✅ Foreign keys rehabilitadas${NC}"
echo ""

echo -e "${YELLOW}[10/6] Verificando...${NC}"
CLIENTES_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_cliente_taller;" 2>/dev/null | tr -d '[:space:]' || echo "0")
VEHICULOS_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_vehiculo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
DIAGNOSTICOS_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
TRABAJOS_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
REPUESTOS_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo ""
echo -e "${GREEN}✅ Resultados:${NC}"
echo "  Clientes: ${CLIENTES_FINAL}"
echo "  Vehículos: ${VEHICULOS_FINAL}"
echo "  Diagnósticos: ${DIAGNOSTICOS_FINAL}"
echo "  Trabajos: ${TRABAJOS_FINAL}"
echo "  Repuestos: ${REPUESTOS_FINAL}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Restauración completada${NC}"
echo -e "${BLUE}========================================${NC}"


