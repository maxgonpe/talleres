#!/bin/bash
# Script final que usa Python para limpiar INSERT y restaurar correctamente

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
PYTHON_SCRIPT="/home/max/myproject/restaurar_fix_sql.py"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Restauración Final con Python${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo -e "${RED}❌ Backup no encontrado${NC}"
    exit 1
fi

echo -e "${YELLOW}Este script:${NC}"
echo "  1. Usará Python para limpiar INSERT problemáticos"
echo "  2. Restaurará diagnósticos, trabajos y repuestos"
echo ""
echo "¿Continuar? (escribe 'SI'):"
read -r confirmacion

if [[ "$confirmacion" != "SI" ]]; then
    echo "Cancelado"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/6] Ejecutando script Python para limpiar INSERT...${NC}"

# Verificar si Python está disponible
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no está instalado${NC}"
    echo "Instalando método alternativo..."
    # Crear script bash alternativo más robusto
    python3 "$PYTHON_SCRIPT" 2>/dev/null || {
        echo -e "${YELLOW}⚠️  Python no disponible, usando método alternativo...${NC}"
        # Método alternativo: usar sed/awk más robusto
        echo "  Limpiando INSERT con método alternativo..."
        
        # Para diagnósticos: buscar INSERT y unir líneas hasta encontrar );
        grep -A 20 "INSERT INTO public.car_diagnostico" "$BACKUP_FILE" | \
        awk 'BEGIN{RS="INSERT INTO"; ORS="\n"} /car_diagnostico/ {line=$0; while(getline > 0 && !/\);$/) {line=line" "$0}; if(/\);$/) print "INSERT INTO"line}' | \
        sed 's/INSERT INTO INSERT INTO/INSERT INTO/g' > /tmp/diagnosticos_limpios.sql 2>/dev/null || true
    }
else
    python3 "$PYTHON_SCRIPT"
fi

echo ""

# Verificar que se crearon los archivos
if [[ ! -f "/tmp/diagnosticos_limpios.sql" ]]; then
    echo -e "${RED}❌ No se crearon archivos limpios. Creando manualmente...${NC}"
    
    # Método manual más simple: extraer INSERT completos
    echo "  Extrayendo diagnósticos..."
    awk '/INSERT INTO public\.car_diagnostico/,/\);$/' "$BACKUP_FILE" | \
    tr -d '\n' | sed 's/);/);\n/g' | grep "INSERT INTO public.car_diagnostico" > /tmp/diagnosticos_limpios.sql
    
    echo "  Extrayendo trabajos..."
    awk '/INSERT INTO public\.car_trabajo/,/\);$/' "$BACKUP_FILE" | \
    tr -d '\n' | sed 's/);/);\n/g' | grep "INSERT INTO public.car_trabajo" > /tmp/trabajos_limpios.sql
    
    echo "  Extrayendo repuestos..."
    grep "INSERT INTO public.car_trabajorepuesto" "$BACKUP_FILE" > /tmp/repuestos_limpios.sql
fi

DIAG_COUNT=$(wc -l < /tmp/diagnosticos_limpios.sql 2>/dev/null || echo "0")
TRABAJO_COUNT=$(wc -l < /tmp/trabajos_limpios.sql 2>/dev/null || echo "0")
REPUESTO_COUNT=$(wc -l < /tmp/repuestos_limpios.sql 2>/dev/null || echo "0")

echo -e "${GREEN}✅ Archivos limpios creados:${NC}"
echo "  Diagnósticos: $DIAG_COUNT INSERT"
echo "  Trabajos: $TRABAJO_COUNT INSERT"
echo "  Repuestos: $REPUESTO_COUNT INSERT"
echo ""

echo -e "${YELLOW}[2/6] Limpiando tablas...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SET session_replication_role = 'replica';
BEGIN;
TRUNCATE TABLE car_trabajorepuesto CASCADE;
TRUNCATE TABLE car_trabajo CASCADE;
TRUNCATE TABLE car_diagnostico CASCADE;
COMMIT;
SQL
echo -e "${GREEN}✅ Tablas limpiadas${NC}"
echo ""

echo -e "${YELLOW}[3/6] Restaurando diagnósticos...${NC}"
if [[ $DIAG_COUNT -gt 0 ]]; then
    cat /tmp/diagnosticos_limpios.sql | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | \
    grep -E "INSERT|ERROR" | tail -5 || true
    
    DIAG_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    echo -e "${GREEN}✅ Diagnósticos restaurados: ${DIAG_FINAL}${NC}"
else
    echo -e "${RED}❌ No hay diagnósticos para restaurar${NC}"
fi
echo ""

echo -e "${YELLOW}[4/6] Restaurando trabajos...${NC}"
if [[ $TRABAJO_COUNT -gt 0 ]]; then
    cat /tmp/trabajos_limpios.sql | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | \
    grep -E "INSERT|ERROR" | tail -5 || true
    
    TRABAJO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    echo -e "${GREEN}✅ Trabajos restaurados: ${TRABAJO_FINAL}${NC}"
else
    echo -e "${RED}❌ No hay trabajos para restaurar${NC}"
fi
echo ""

echo -e "${YELLOW}[5/6] Restaurando repuestos...${NC}"
if [[ $REPUESTO_COUNT -gt 0 ]]; then
    cat /tmp/repuestos_limpios.sql | docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -v ON_ERROR_STOP=0 2>&1 | \
    grep -E "INSERT|ERROR" | tail -3 || true
    
    REPUESTO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    echo -e "${GREEN}✅ Repuestos restaurados: ${REPUESTO_FINAL}${NC}"
else
    echo -e "${RED}❌ No hay repuestos para restaurar${NC}"
fi
echo ""

echo -e "${YELLOW}[6/6] Rehabilitando foreign keys...${NC}"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" <<'SQL'
SET session_replication_role = 'origin';
SQL
echo -e "${GREEN}✅ Foreign keys rehabilitadas${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Resumen Final:${NC}"
DIAG_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
TRABAJO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
REPUESTO_FINAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c "SELECT COUNT(*) FROM car_trabajorepuesto;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo "  Diagnósticos: ${DIAG_FINAL} (esperados: 171)"
echo "  Trabajos: ${TRABAJO_FINAL} (esperados: 374)"
echo "  Repuestos: ${REPUESTO_FINAL} (esperados: 88)"
echo ""

if [[ "$DIAG_FINAL" -lt 50 || "$TRABAJO_FINAL" -lt 50 ]]; then
    echo -e "${RED}⚠️  ADVERTENCIA: Se restauraron muy pocos registros${NC}"
    echo ""
    echo "El problema puede ser:"
    echo "  1. Saltos de línea en el backup que no se están limpiando bien"
    echo "  2. Errores de sintaxis en los INSERT"
    echo ""
    echo "Solución alternativa: Restaurar el backup completo con pg_restore"
    echo "  (pero esto sobrescribirá TODAS las tablas)"
else
    echo -e "${GREEN}✅ Restauración exitosa${NC}"
fi

echo -e "${BLUE}========================================${NC}"


