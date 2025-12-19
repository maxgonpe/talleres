#!/bin/bash
# Script para verificar base de datos de solutioncar
# Uso: ./verificar_bd_solutioncar.sh

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
CLIENTE="solutioncar"
CONTAINER_NAME="cliente_${CLIENTE}"
POSTGRES_CONTAINER="postgres_talleres"
DB_NAME="cliente_${CLIENTE}_db"
DB_OWNER="maxgonpe"
DB_PASSWORD="celsa1961"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verificación BD para: ${CLIENTE}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# 1. Verificar contenedor Django
# =========================
echo -e "${YELLOW}[1/6] Verificando contenedor Django...${NC}"
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ Error: El contenedor ${CONTAINER_NAME} no está corriendo${NC}"
    echo "Contenedores disponibles:"
    docker ps --format '{{.Names}}' | grep "cliente_"
    exit 1
fi
echo -e "${GREEN}✅ Contenedor ${CONTAINER_NAME} está corriendo${NC}"
echo ""

# =========================
# 2. Mostrar variables de entorno de BD
# =========================
echo -e "${YELLOW}[2/6] Variables de entorno de conexión a BD:${NC}"
echo "----------------------------------------"
docker exec "${CONTAINER_NAME}" env | grep -E "^DB_" | sort || echo "No se encontraron variables DB_*"
echo "----------------------------------------"
echo ""

# =========================
# 3. Verificar configuración de BD desde Django
# =========================
echo -e "${YELLOW}[3/6] Verificando configuración de BD desde Django:${NC}"
docker exec -it "${CONTAINER_NAME}" bash -lc "
python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','myproject.settings')
django.setup()
from django.conf import settings
db = settings.DATABASES['default']
print('ENGINE:', db.get('ENGINE'))
print('NAME:', db.get('NAME'))
print('HOST:', db.get('HOST'))
print('USER:', db.get('USER'))
print('PORT:', db.get('PORT'))
PY
"
echo ""

# =========================
# 4. Verificar BD en PostgreSQL
# =========================
echo -e "${YELLOW}[4/6] Verificando base de datos en PostgreSQL:${NC}"

# Verificar que el contenedor PostgreSQL existe
if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    echo -e "${RED}❌ Error: El contenedor PostgreSQL ${POSTGRES_CONTAINER} no está corriendo${NC}"
    exit 1
fi

# Verificar que la BD existe
echo "Verificando si la base de datos ${DB_NAME} existe..."
DB_EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c \
    "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}';" | tr -d '[:space:]' || echo "0")

if [[ "$DB_EXISTS" != "1" ]]; then
    echo -e "${RED}❌ Error: La base de datos ${DB_NAME} NO existe${NC}"
    echo "Bases de datos disponibles:"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -c "\l" | grep "cliente_"
    exit 1
fi

echo -e "${GREEN}✅ Base de datos ${DB_NAME} existe${NC}"

# Mostrar tamaño de la BD
echo "Tamaño de la base de datos:"
docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
SELECT pg_size_pretty(pg_database_size('${DB_NAME}')) AS size;
" || true
echo ""

# =========================
# 5. Verificar TODAS las tablas importantes y mostrar datos
# =========================
echo -e "${YELLOW}[5/6] Verificando tablas principales:${NC}"

# Lista de tablas importantes a verificar
TABLAS_IMPORTANTES=(
    "car_cliente"
    "car_vehiculo"
    "car_diagnostico"
    "car_trabajo"
    "car_trabajoaccion"
    "car_trabajorepuesto"
    "car_registroevento"
)

echo ""
echo -e "${BLUE}Resumen de datos en tablas principales:${NC}"
echo "----------------------------------------"

for tabla in "${TABLAS_IMPORTANTES[@]}"; do
    # Verificar si la tabla existe
    TABLE_EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = '${tabla}');" 2>/dev/null | tr -d '[:space:]' || echo "false")
    
    if [[ "$TABLE_EXISTS" == "t" ]]; then
        COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
            "SELECT COUNT(*) FROM ${tabla};" 2>/dev/null | tr -d '[:space:]' || echo "0")
        
        if [[ "$COUNT" == "0" ]]; then
            echo -e "  ${tabla}: ${YELLOW}${COUNT}${NC} registros"
        else
            echo -e "  ${tabla}: ${GREEN}${COUNT}${NC} registros"
        fi
    else
        echo -e "  ${tabla}: ${RED}NO EXISTE${NC}"
    fi
done

echo "----------------------------------------"
echo ""

# Verificar tabla car_trabajo específicamente
echo -e "${YELLOW}Detalle de tabla car_trabajo:${NC}"

TABLE_EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'car_trabajo');" | tr -d '[:space:]' || echo "false")

if [[ "$TABLE_EXISTS" != "t" ]]; then
    echo -e "${RED}❌ Error: La tabla car_trabajo NO existe${NC}"
    echo "Tablas disponibles en ${DB_NAME}:"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "\dt" | head -30
    exit 1
fi

echo -e "${GREEN}✅ La tabla car_trabajo existe${NC}"

# Contar registros
COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajo;" | tr -d '[:space:]' || echo "0")

echo -e "${BLUE}Total de trabajos: ${COUNT}${NC}"

if [[ "$COUNT" == "0" ]]; then
    echo -e "${RED}⚠️  ADVERTENCIA: La tabla car_trabajo está VACÍA${NC}"
    
    # Verificar si hay diagnósticos (que podrían convertirse en trabajos)
    COUNT_DIAG=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
        "SELECT COUNT(*) FROM car_diagnostico;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    
    if [[ "$COUNT_DIAG" != "0" ]]; then
        echo -e "${YELLOW}ℹ️  Pero hay ${COUNT_DIAG} diagnósticos (algunos podrían no estar aprobados aún)${NC}"
    fi
    
    # Verificar si hay vehículos
    COUNT_VEH=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
        "SELECT COUNT(*) FROM car_vehiculo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
    
    if [[ "$COUNT_VEH" != "0" ]]; then
        echo -e "${YELLOW}ℹ️  Y hay ${COUNT_VEH} vehículos registrados${NC}"
    fi
else
    echo -e "${GREEN}✅ La tabla tiene ${COUNT} registros${NC}"
fi

# Mostrar algunos registros de ejemplo
if [[ "$COUNT" != "0" ]]; then
    echo ""
    echo "Primeros 5 registros de car_trabajo:"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
    SELECT 
        id,
        estado,
        fecha_inicio,
        fecha_fin,
        lectura_kilometraje_actual,
        visible
    FROM car_trabajo 
    ORDER BY id 
    LIMIT 5;
    "
    echo ""
    
    # Mostrar trabajos con vehículos (join)
    echo "Trabajos con información de vehículos (últimos 3):"
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -c "
    SELECT 
        t.id AS trabajo_id,
        t.estado,
        t.fecha_inicio,
        v.placa,
        v.marca,
        v.modelo
    FROM car_trabajo t
    LEFT JOIN car_vehiculo v ON t.vehiculo_id = v.id
    ORDER BY t.id DESC
    LIMIT 3;
    " || echo "No se pudo hacer el join (puede que falte la tabla car_vehiculo)"
    echo ""
fi

# =========================
# 6. Verificar si hay datos en otras bases de datos
# =========================
echo -e "${YELLOW}[6/6] Verificando otras bases de datos cliente_*:${NC}"
echo "Buscando bases de datos que puedan tener datos de ${CLIENTE}..."
echo ""

ALL_DBS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c \
    "SELECT datname FROM pg_database WHERE datname LIKE 'cliente_%' ORDER BY datname;" | tr -d '[:space:]' | grep -v "^$")

echo "Bases de datos cliente encontradas:"
for db in $ALL_DBS; do
    if [[ "$db" == "$DB_NAME" ]]; then
        echo -e "  ${db}: ${BLUE}(esta es la BD actual)${NC}"
    else
        # Contar trabajos en esta BD
        COUNT_OTHER=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -tA -c \
            "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "N/A")
        echo -e "  ${db}: ${COUNT_OTHER} trabajos"
    fi
done
echo ""

# =========================
# 7. Comparación detallada con otro cliente (opcional)
# =========================
echo -e "${YELLOW}[BONUS] Comparación detallada con otro cliente:${NC}"
echo "¿Deseas comparar con otro cliente? (s/n)"
read -r respuesta || respuesta="n"

if [[ "$respuesta" == "s" || "$respuesta" == "S" ]]; then
    echo "Ingresa el nombre del cliente para comparar (ej: theskynet):"
    read -r otro_cliente || otro_cliente="theskynet"
    
    OTRO_DB_NAME="cliente_${otro_cliente}_db"
    
    echo ""
    echo -e "${BLUE}Comparando ${CLIENTE} vs ${otro_cliente}:${NC}"
    echo "----------------------------------------"
    
    for tabla in "${TABLAS_IMPORTANTES[@]}"; do
        COUNT_ACTUAL=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
            "SELECT COUNT(*) FROM ${tabla};" 2>/dev/null | tr -d '[:space:]' || echo "0")
        COUNT_OTRO=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${OTRO_DB_NAME}" -tA -c \
            "SELECT COUNT(*) FROM ${tabla};" 2>/dev/null | tr -d '[:space:]' || echo "N/A")
        
        echo "  ${tabla}:"
        echo -e "    ${CLIENTE}: ${COUNT_ACTUAL}"
        echo -e "    ${otro_cliente}: ${COUNT_OTRO}"
    done
    
    echo "----------------------------------------"
    
    COUNT_OTRO=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${OTRO_DB_NAME}" -tA -c \
        "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "N/A")
    
    if [[ "$COUNT" == "0" && "$COUNT_OTRO" != "0" && "$COUNT_OTRO" != "N/A" ]]; then
        echo -e "${RED}⚠️  ${CLIENTE} tiene 0 trabajos mientras que ${otro_cliente} tiene ${COUNT_OTRO}${NC}"
        echo ""
        echo -e "${YELLOW}💡 Posibles causas:${NC}"
        echo "  1. Los datos nunca se migraron a esta BD"
        echo "  2. Los datos están en otra base de datos"
        echo "  3. Hubo un problema durante la creación/copia de la BD"
        echo "  4. La BD se creó desde una semilla vacía"
    fi
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Verificación completada${NC}"
echo -e "${BLUE}========================================${NC}"

