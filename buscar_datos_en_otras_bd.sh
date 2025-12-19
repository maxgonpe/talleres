#!/bin/bash
# Script para buscar datos de solutioncar en otras bases de datos
# Útil si los datos están en otra BD o fueron movidos

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
DB_OWNER="maxgonpe"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Buscando datos de ${CLIENTE} en todas las BD${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Obtener todas las bases de datos cliente_*
mapfile -t ALL_DBS < <(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -tA -c \
    "SELECT datname FROM pg_database WHERE datname LIKE 'cliente_%' OR datname LIKE 'netgogo%' ORDER BY datname;" 2>/dev/null | grep -v "^$" || true)

if [[ -z "$ALL_DBS" ]]; then
    echo -e "${RED}❌ No se encontraron bases de datos${NC}"
    exit 1
fi

echo -e "${YELLOW}Buscando datos relacionados con '${CLIENTE}' en todas las bases de datos...${NC}"
echo ""

# Buscar en cada base de datos
for db in "${ALL_DBS[@]}"; do
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}Base de datos: ${db}${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Verificar si la tabla car_trabajo existe
    TABLE_EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -tA -c \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'car_trabajo');" 2>/dev/null | tr -d '[:space:]' || echo "false")
    
    if [[ "$TABLE_EXISTS" == "t" ]]; then
        # Contar trabajos
        COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -tA -c \
            "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
        
        echo -e "Trabajos: ${COUNT}"
        
        # Si hay trabajos, buscar información de vehículos
        if [[ "$COUNT" != "0" ]]; then
            echo ""
            echo "Vehículos relacionados con trabajos:"
            docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -c "
            SELECT DISTINCT
                v.placa,
                v.marca,
                v.modelo,
                COUNT(t.id) as num_trabajos
            FROM car_trabajo t
            JOIN car_vehiculo v ON t.vehiculo_id = v.id
            GROUP BY v.placa, v.marca, v.modelo
            ORDER BY num_trabajos DESC
            LIMIT 10;
            " 2>/dev/null || echo "No se pudo consultar vehículos"
        fi
        
        # Buscar en car_cliente si existe
        CLIENT_TABLE_EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -tA -c \
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'car_cliente');" 2>/dev/null | tr -d '[:space:]' || echo "false")
        
        if [[ "$CLIENT_TABLE_EXISTS" == "t" ]]; then
            # Buscar clientes que contengan "solution" en el nombre
            CLIENT_MATCHES=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -tA -c \
                "SELECT COUNT(*) FROM car_cliente WHERE LOWER(nombre) LIKE '%solution%' OR LOWER(nombre) LIKE '%${CLIENTE}%';" 2>/dev/null | tr -d '[:space:]' || echo "0")
            
            if [[ "$CLIENT_MATCHES" != "0" ]]; then
                echo ""
                echo -e "${YELLOW}⚠️  Se encontraron clientes relacionados:${NC}"
                docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${db}" -c "
                SELECT id, nombre, rut, telefono
                FROM car_cliente
                WHERE LOWER(nombre) LIKE '%solution%' OR LOWER(nombre) LIKE '%${CLIENTE}%'
                LIMIT 5;
                " 2>/dev/null || true
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  La tabla car_trabajo no existe en esta BD${NC}"
    fi
    
    echo ""
done

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Búsqueda completada${NC}"
echo -e "${BLUE}========================================${NC}"

