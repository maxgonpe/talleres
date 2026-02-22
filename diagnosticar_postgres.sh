#!/bin/bash
# Script para diagnosticar y resolver el problema de PostgreSQL
# Ejecutar en el servidor de producción: /home/max/myproject

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

POSTGRES_CONTAINER="postgres_talleres"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Diagnóstico de PostgreSQL${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# =========================
# 1. Verificar estado del contenedor
# =========================
echo -e "${YELLOW}[1/5] Verificando estado del contenedor PostgreSQL...${NC}"
echo "----------------------------------------"

if docker ps -a --format '{{.Names}}\t{{.Status}}' | grep -q "^${POSTGRES_CONTAINER}"; then
    STATUS=$(docker ps -a --format '{{.Names}}\t{{.Status}}' | grep "^${POSTGRES_CONTAINER}" | awk '{print $2" "$3" "$4" "$5" "$6}')
    echo -e "Estado: ${STATUS}"
    
    if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
        echo -e "${GREEN}✅ Contenedor está corriendo${NC}"
        IS_RUNNING=true
    else
        echo -e "${RED}❌ Contenedor está detenido${NC}"
        IS_RUNNING=false
    fi
else
    echo -e "${RED}❌ Contenedor ${POSTGRES_CONTAINER} no existe${NC}"
    exit 1
fi

echo ""

# =========================
# 2. Ver logs del contenedor
# =========================
echo -e "${YELLOW}[2/5] Revisando logs del contenedor (últimas 50 líneas)...${NC}"
echo "----------------------------------------"
docker logs --tail 50 "${POSTGRES_CONTAINER}" 2>&1 || echo "No se pudieron obtener logs"
echo ""

# =========================
# 3. Verificar información del contenedor
# =========================
echo -e "${YELLOW}[3/5] Información del contenedor...${NC}"
echo "----------------------------------------"
echo "Puertos mapeados:"
docker port "${POSTGRES_CONTAINER}" 2>/dev/null || echo "Sin puertos mapeados"
echo ""

echo "Volúmenes montados:"
docker inspect "${POSTGRES_CONTAINER}" --format '{{range .Mounts}}{{.Source}} -> {{.Destination}} ({{.Type}}){{"\n"}}{{end}}' 2>/dev/null || echo "No se pudieron obtener volúmenes"
echo ""

# =========================
# 4. Intentar reiniciar si está detenido
# =========================
if [ "$IS_RUNNING" = false ]; then
    echo -e "${YELLOW}[4/5] Intentando reiniciar el contenedor...${NC}"
    echo "----------------------------------------"
    
    if docker start "${POSTGRES_CONTAINER}"; then
        echo -e "${GREEN}✅ Contenedor iniciado exitosamente${NC}"
        echo "Esperando 5 segundos para que PostgreSQL se inicie..."
        sleep 5
    else
        echo -e "${RED}❌ Error al iniciar el contenedor${NC}"
        echo ""
        echo "Revisando detalles del error..."
        docker inspect "${POSTGRES_CONTAINER}" --format '{{.State.Error}}' 2>/dev/null || echo "Sin información de error disponible"
        exit 1
    fi
else
    echo -e "${GREEN}[4/5] Contenedor ya está corriendo, saltando reinicio${NC}"
fi

echo ""

# =========================
# 5. Verificar conectividad
# =========================
echo -e "${YELLOW}[5/5] Verificando conectividad de PostgreSQL...${NC}"
echo "----------------------------------------"

# Verificar que PostgreSQL esté listo
if docker exec "${POSTGRES_CONTAINER}" pg_isready -U maxgonpe 2>/dev/null; then
    echo -e "${GREEN}✅ PostgreSQL está listo para conexiones${NC}"
else
    echo -e "${RED}❌ PostgreSQL no está respondiendo${NC}"
    echo "Esperando 10 segundos más..."
    sleep 10
    if docker exec "${POSTGRES_CONTAINER}" pg_isready -U maxgonpe 2>/dev/null; then
        echo -e "${GREEN}✅ PostgreSQL está listo ahora${NC}"
    else
        echo -e "${RED}❌ PostgreSQL aún no responde${NC}"
        exit 1
    fi
fi

echo ""

# Verificar desde un contenedor de cliente
echo -e "${YELLOW}Verificando conectividad desde contenedor de cliente...${NC}"
CLIENTE_CONTAINER="cliente_solutioncar"

if docker ps --format '{{.Names}}' | grep -q "^${CLIENTE_CONTAINER}$"; then
    echo "Probando conexión desde ${CLIENTE_CONTAINER}..."
    if docker exec "${CLIENTE_CONTAINER}" python manage.py check --database default 2>&1 | head -20; then
        echo -e "${GREEN}✅ Conexión desde Django exitosa${NC}"
    else
        echo -e "${YELLOW}⚠️  Hubo problemas con la conexión desde Django${NC}"
        echo "Revisando variables de entorno de BD:"
        docker exec "${CLIENTE_CONTAINER}" env | grep -E "^DB_|^DATABASE" | head -10 || echo "No se encontraron variables DB_*"
    fi
else
    echo -e "${YELLOW}⚠️  Contenedor ${CLIENTE_CONTAINER} no está corriendo, saltando verificación${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Diagnóstico completado${NC}"
echo -e "${BLUE}========================================${NC}"
