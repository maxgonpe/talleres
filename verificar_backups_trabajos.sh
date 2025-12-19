#!/bin/bash
# Script para verificar si los backups tienen los trabajos que faltan

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
echo -e "${BLUE}Verificando Backups para Trabajos${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Trabajos que sabemos que deberían existir (de los eventos)
TRABAJOS_ESPERADOS="54 59 61"

# =========================
# 1. Listar todos los backups disponibles
# =========================
echo -e "${YELLOW}[1/4] Buscando backups disponibles:${NC}"
echo "----------------------------------------"

BACKUP_FILES=(
    "/tmp/cliente_solutioncar_db.dump"
    "/home/max/backups/20251211_163708/cliente_solutioncar_db.sql"
    "/home/max/backups/20251211_163500/cliente_solutioncar_db.sql"
    "/home/max/backups/20251013_123012/cliente_solutioncar_db.sql"
)

VALID_BACKUPS=()

for backup in "${BACKUP_FILES[@]}"; do
    if [[ -f "$backup" ]]; then
        SIZE=$(stat -c%s "$backup" 2>/dev/null || echo "0")
        DATE=$(stat -c%y "$backup" 2>/dev/null | cut -d' ' -f1 || echo "N/A")
        echo -e "${GREEN}✅ ${backup}${NC}"
        echo "   Tamaño: $(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "${SIZE} bytes")"
        echo "   Fecha: $DATE"
        VALID_BACKUPS+=("$backup")
    else
        echo -e "${YELLOW}⚠️  ${backup} (no encontrado)${NC}"
    fi
done

echo ""

if [[ ${#VALID_BACKUPS[@]} -eq 0 ]]; then
    echo -e "${RED}❌ No se encontraron backups válidos${NC}"
    exit 1
fi

# =========================
# 2. Verificar backups SQL (texto plano)
# =========================
echo -e "${YELLOW}[2/4] Verificando backups SQL (texto plano):${NC}"
echo "----------------------------------------"

for backup in "${VALID_BACKUPS[@]}"; do
    if [[ "$backup" == *.sql ]]; then
        echo ""
        echo -e "${CYAN}Analizando: ${backup}${NC}"
        
        # Contar trabajos en el backup
        if [[ -r "$backup" ]]; then
            # Buscar INSERT INTO car_trabajo
            TRABAJOS_COUNT=$(grep -c "INSERT INTO.*car_trabajo" "$backup" 2>/dev/null || echo "0")
            echo "  Trabajos encontrados (INSERT): $TRABAJOS_COUNT"
            
            # Buscar los trabajos específicos
            for trabajo_id in $TRABAJOS_ESPERADOS; do
                if grep -q "car_trabajo.*${trabajo_id}" "$backup" 2>/dev/null; then
                    echo -e "  ${GREEN}✅ Trabajo ${trabajo_id} encontrado${NC}"
                    
                    # Mostrar información del trabajo
                    echo "    Información del trabajo:"
                    grep -A 5 "car_trabajo.*${trabajo_id}" "$backup" | head -10 | sed 's/^/    /' || true
                else
                    echo -e "  ${RED}❌ Trabajo ${trabajo_id} NO encontrado${NC}"
                fi
            done
            
            # Buscar COPY car_trabajo (formato COPY de PostgreSQL)
            if grep -q "^COPY.*car_trabajo" "$backup" 2>/dev/null; then
                echo "  Formato: COPY (PostgreSQL)"
                # Contar líneas después de COPY
                COPY_START=$(grep -n "^COPY.*car_trabajo" "$backup" | cut -d: -f1 | head -1)
                if [[ -n "$COPY_START" ]]; then
                    # Buscar el final del COPY (línea con \.)
                    COPY_END=$(sed -n "${COPY_START},\$p" "$backup" | grep -n "^\\\\\." | head -1 | cut -d: -f1)
                    if [[ -n "$COPY_END" ]]; then
                        LINES_COUNT=$((COPY_END - 1))
                        echo "  Registros en formato COPY: ~$LINES_COUNT"
                    fi
                fi
            fi
        else
            echo -e "  ${RED}❌ No se puede leer el archivo${NC}"
        fi
    fi
done

echo ""

# =========================
# 3. Verificar backups en formato dump (binario)
# =========================
echo -e "${YELLOW}[3/4] Verificando backups en formato dump (binario):${NC}"
echo "----------------------------------------"

for backup in "${VALID_BACKUPS[@]}"; do
    if [[ "$backup" == *.dump ]]; then
        echo ""
        echo -e "${CYAN}Analizando: ${backup}${NC}"
        
        # Intentar restaurar a una BD temporal para verificar
        TEMP_DB="temp_verify_${CLIENTE}_$$"
        
        echo "  Creando base de datos temporal: $TEMP_DB"
        docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -c \
            "CREATE DATABASE ${TEMP_DB};" 2>/dev/null || echo "  (puede que ya exista)"
        
        echo "  Restaurando backup..."
        if docker exec -i "${POSTGRES_CONTAINER}" pg_restore -U "${DB_OWNER}" -d "${TEMP_DB}" < "$backup" 2>/dev/null; then
            echo -e "  ${GREEN}✅ Backup restaurado exitosamente${NC}"
            
            # Contar trabajos
            TRABAJOS_COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${TEMP_DB}" -tA -c \
                "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")
            echo "  Trabajos en backup: $TRABAJOS_COUNT"
            
            # Verificar trabajos específicos
            for trabajo_id in $TRABAJOS_ESPERADOS; do
                EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${TEMP_DB}" -tA -c \
                    "SELECT EXISTS(SELECT 1 FROM car_trabajo WHERE id = ${trabajo_id});" 2>/dev/null | tr -d '[:space:]' || echo "false")
                
                if [[ "$EXISTS" == "t" ]]; then
                    echo -e "  ${GREEN}✅ Trabajo ${trabajo_id} encontrado${NC}"
                    
                    # Mostrar información
                    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${TEMP_DB}" -c "
                    SELECT id, estado, fecha_inicio, visible
                    FROM car_trabajo
                    WHERE id = ${trabajo_id};
                    " 2>/dev/null | head -10 || true
                else
                    echo -e "  ${RED}❌ Trabajo ${trabajo_id} NO encontrado${NC}"
                fi
            done
            
            # Limpiar BD temporal
            echo "  Eliminando base de datos temporal..."
            docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -c \
                "DROP DATABASE IF EXISTS ${TEMP_DB};" 2>/dev/null || true
        else
            echo -e "  ${RED}❌ Error al restaurar backup${NC}"
            # Limpiar en caso de error
            docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d postgres -c \
                "DROP DATABASE IF EXISTS ${TEMP_DB};" 2>/dev/null || true
        fi
    fi
done

echo ""

# =========================
# 4. Comparar con la BD actual
# =========================
echo -e "${YELLOW}[4/4] Comparación con base de datos actual:${NC}"
echo "----------------------------------------"

CURRENT_COUNT=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
    "SELECT COUNT(*) FROM car_trabajo;" 2>/dev/null | tr -d '[:space:]' || echo "0")

echo "Trabajos en BD actual: $CURRENT_COUNT"
echo ""

for trabajo_id in $TRABAJOS_ESPERADOS; do
    EXISTS=$(docker exec -i "${POSTGRES_CONTAINER}" psql -U "${DB_OWNER}" -d "${DB_NAME}" -tA -c \
        "SELECT EXISTS(SELECT 1 FROM car_trabajo WHERE id = ${trabajo_id});" 2>/dev/null | tr -d '[:space:]' || echo "false")
    
    if [[ "$EXISTS" == "t" ]]; then
        echo -e "${GREEN}✅ Trabajo ${trabajo_id}: EXISTE en BD actual${NC}"
    else
        echo -e "${RED}❌ Trabajo ${trabajo_id}: NO EXISTE en BD actual${NC}"
    fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Verificación completada${NC}"
echo -e "${BLUE}========================================${NC}"


