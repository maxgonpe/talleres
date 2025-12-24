#!/bin/bash
# Script para verificar si hay datos en SQLite dentro del contenedor
# Esto verifica si el contenedor está usando SQLite en lugar de PostgreSQL

set -euo pipefail

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CLIENTE="solutioncar"
CONTAINER_NAME="cliente_${CLIENTE}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Verificando SQLite en contenedor${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Verificar contenedor
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ El contenedor ${CONTAINER_NAME} no está corriendo${NC}"
    exit 1
fi

echo -e "${YELLOW}Buscando archivos SQLite en el contenedor...${NC}"

# Buscar archivos .sqlite3 o .db
SQLITE_FILES=$(docker exec "${CONTAINER_NAME}" find /app -name "*.sqlite3" -o -name "*.db" 2>/dev/null | grep -v "__pycache__" || true)

if [[ -z "$SQLITE_FILES" ]]; then
    echo -e "${GREEN}✅ No se encontraron archivos SQLite en el contenedor${NC}"
    echo "Esto es correcto si estás usando PostgreSQL"
else
    echo -e "${YELLOW}⚠️  Se encontraron archivos SQLite:${NC}"
    echo "$SQLITE_FILES"
    echo ""
    
    for file in $SQLITE_FILES; do
        echo -e "${BLUE}Verificando: ${file}${NC}"
        
        # Verificar si el archivo tiene datos
        SIZE=$(docker exec "${CONTAINER_NAME}" stat -c%s "$file" 2>/dev/null || echo "0")
        
        if [[ "$SIZE" -gt 0 ]]; then
            echo -e "  Tamaño: ${SIZE} bytes"
            
            # Intentar contar registros en car_trabajo si existe
            COUNT=$(docker exec "${CONTAINER_NAME}" sqlite3 "$file" "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null || echo "N/A")
            
            if [[ "$COUNT" != "N/A" ]]; then
                echo -e "  Trabajos en SQLite: ${COUNT}"
                
                if [[ "$COUNT" != "0" ]]; then
                    echo -e "${RED}⚠️  ADVERTENCIA: Hay ${COUNT} trabajos en SQLite!${NC}"
                    echo -e "${RED}   El contenedor podría estar usando SQLite en lugar de PostgreSQL${NC}"
                fi
            fi
        else
            echo -e "  Tamaño: 0 bytes (vacío)"
        fi
        echo ""
    done
fi

echo ""
echo -e "${BLUE}Verificando configuración de BD desde Django...${NC}"
docker exec -it "${CONTAINER_NAME}" bash -lc "
python - <<'PY'
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','myproject.settings')
django.setup()
from django.conf import settings
from django.db import connection

db = settings.DATABASES['default']
engine = db.get('ENGINE', '')
name = db.get('NAME', '')

print('ENGINE:', engine)
print('NAME:', name)
print('HOST:', db.get('HOST', 'N/A'))

# Verificar conexión real
try:
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')
        print('✅ Conexión a BD exitosa')
        print('Base de datos REAL en uso:', connection.settings_dict['NAME'])
except Exception as e:
    print('❌ Error de conexión:', str(e))
PY
"

echo ""
echo -e "${BLUE}========================================${NC}"





